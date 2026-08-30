---
id: rfc-0120
title: "Named Records"
date: '2026-07-24'
status: under-review
tracking: 'https://github.com/metel-lang/metel-core/issues/791'
target: v0.13.0
updated: '2026-08-25'
---

> **Extracted from RFC-0090 §8 (tier 3) and §9 on 2026-07-24** (superseded; see RFC-0116's
> header for the split rationale). Depends on RFC-0116 (Anonymous Record Types).

> **Correction, 2026-08-23: RFC-0119 removed from the dependency list above.** It was
> inherited from the original six-way split's dependency-*ordering* (RFC-0116 through
> RFC-0121, numbered by review convenience), not a real technical requirement — this
> RFC's own §1 says so directly: *"A tier-3 type gets tier 2's conversions for free:
> `to_record`/`from_record` on a type that already **is** `(row, brand)` are the
> identity coercion, nothing to derive separately."* Tier 2 (RFC-0119) and tier 3 (this
> RFC) are parallel paths for different commitments, not a sequence — see §2's framing.
> RFC-0119 also carries a real, open-ended blocker of its own (its derive convenience
> depends on RFC-0093, `0-draft`, no target) that this RFC has no reason to inherit.

> **Status — under review (2026-08-23).** Committed to v0.13.0, tracking issue #791 filed 2026-08-22
>
> **Open-question sweep, 2026-08-30.** RFC-0137 (Nominal Types as Branded Rows) is now
> `3-integrated`, and it resolves or absorbs the three open questions that were still
> live: OQ1 (`Drop` dispatch against a narrowed named record) is answered by RFC-0137 §5's
> row-bounded dispatch, the same rule that closed RFC-0117's identical question and is now
> spec text (`spec.ownership.drop-dispatch-against-a-narrowed-residual`); OQ3's
> "does the anonymous-record allocator restriction transfer" loses its premise, because a
> `record` brand *is* the per-instance declaration identity RFC-0116 §3 said an anonymous
> record lacks; OQ4's "same brand kind as RFC-0076's" is now RFC-0137's committed model
> for every struct brand, which a `record` brand simply is. **No blocking open question
> remains** — see each item below. §1's table was already restated against RFC-0137
> (2026-08-25); §4's "deliberately not folded in" note is likewise now historical.

## Summary

A third declaration kind alongside `struct`, `enum` and `aspect`:

```metel
record Handle { fd: i32, alloc: @a Buffer }
```

A named record carries a `(row, brand)` representation **intrinsically**, not convertibly.
That is the one capability RFC-0119's conversions cannot supply at any cost: row-conditional
impls are resolved by the type system matching a type's own declared row at
impl-resolution time, and there is no call site for a derived conversion to intercept.

`record` is now the keyword's only job — RFC-0116 dropped it from the anonymous former, so
it does exactly one thing: mint a nominal type that is row-shaped.

---

## Motivation

RFC-0119 lets a struct convert to a record on demand. That covers the local
drain-and-restore pattern, but the converted value is a *different* value with a different
type, alive only while it is held. Three things need the row to be part of the type itself:

- **Row-conditional impls** (`extend<row R: { token: Token, .. }> Session<..R>`) — resolution
  matches the type's own row, with nothing to intercept.
- **Direct row-bound satisfaction at impl-resolution time**, as opposed to a generic
  function accepting a converted value.
- **A residual that keeps its identity.** A narrowed `Handle` that is still recognisably a
  `Handle`, rather than a bare row that any same-shaped value would also inhabit.

---

## 1. Three tiers, and why the boundary sits here

**Restated 2026-08-25 against RFC-0137 (Nominal Types as Branded Rows, then accepted;
reverted to `1-under-review` the same day — see caveat below Open Question 5).**
RFC-0137 established that *every* struct carries `(brand, row)` unconditionally, not
only tier 3 — so tier 1's "row access: none" cell below is no longer accurate as
originally worded. What actually distinguishes the tiers, per RFC-0137 §3, is never
"having a row" (universal) but *whether that row is visible to structural matching* —
the table's substance is unchanged, only the tier-1 cell's wording:

| Tier | Declaration | Row visible to structural matching | Impl-eligible |
|---|---|---|---|
| 1 | `struct` | no — has a row (RFC-0137), never exposed to matching | — |
| 2 | `struct` + `#derive(ToRecord, FromRecord)` | no — `.to_record()`'s output is brand-stripped and bare, a separate value, not the struct's own row becoming visible | no |
| 3 | `record` | yes — intrinsic, permanent | yes |

**Why not collapse 2 into 3.** Anyone wanting a single local drain/restore in one function
would otherwise have to accept the coherence-priority and private-field-leakage exposure
(§3) that only matters for types with row-conditional impls — paying for machinery never
asked for.

**The guardrail this depends on:** each tier must correspond to a distinct *capability
requirement* — "no row access" / "temporary, explicit, non-impl-eligible" / "permanent,
impl-eligible" — never offered as interchangeable ways to do the same thing.

A tier-3 type gets tier 2's conversions for free: `to_record`/`from_record` on a type that
already *is* `(row, brand)` are the identity coercion, nothing to derive separately.

## 2. The upgrade path

`struct` → `record` should require touching no existing caller, provided:

- The nominal name and identity are unchanged — aspect impls, orphan-rule coherence and
  generic instantiation all key off the same identity as before.
- Construction and field-access syntax are unchanged.
- Whole-value use sites keep typechecking exactly as before, against the record's full row.
- Row tracking costs nothing at runtime for whole-value-only callers.

**One honest caveat: "non-breaking" means "doesn't break existing callers," not "changes
nothing observable."** The conversion does newly make row-conditional generic functions and
drain/restore-style APIs legal against the type. That is the point of upgrading, not a side
effect to apologize for.

**A second caveat, added 2026-07-24, and this one is a real cost rather than a clarification:
the upgrade is a one-way door.** Declaring `record X` publishes the type's field names and
types as public interface — a nominal type's API is what it declares, a record's API is what
it contains (RFC-0118 §3). Two consequences the framing above misses:

- **Reverting is breaking, and you cannot find who it breaks.** Going back to `struct` breaks
  every caller who wrote a row bound naming your fields. The forward direction is additive
  for callers; the reverse is not, and unlike an ordinary API break there is no declaration
  site to grep for — satisfaction is structural, so the dependency is invisible from your
  module.
- **Field renames stop being internal.** After the upgrade, renaming a field is a breaking
  change to anyone bounded on it. Before it, it was refactoring.

So `struct` → `record` should be read as *publishing a contract*, not as *enabling a
feature*. Tier 2 (`#derive(ToRecord, FromRecord)`, RFC-0119) exists precisely for the author
who wants row operations **locally** without making that commitment: it grants conversion and
withholds bound satisfaction, so the layout stays private. **That is what the tier 2 / tier 3
boundary is actually for** — §1 above describes it in terms of impl-resolution mechanics,
which is the mechanism rather than the reason.

## 3. Reusing the identity tag rather than inventing one

Representing a named type as `(row, brand)` — a structural shape plus an identity tag — has
real precedent: TypeScript labels a structural descriptor; OCaml's object system treats a
class name as a constructor convenience over a structural object type.

**This is not a re-litigation of RFC-0116 §5**, which declined "nominal types as pure sugar
over records" because nominal identity is load-bearing and the sugar would have to
reintroduce a real tag anyway. What survives is narrower: not *elimination* of the tag, but
*reuse* of it.

**And the tag need not be a fourth mechanism.** `brand-kind-unification.md` already proposes
that `@a` (allocator tags), `&r` (lifetime anchors) and `'c` (brands) are one underlying
identity kind under three sigils. A named record's tag is a plausible fourth surface use of
that same kind — implementer economy, one freshness/rigidity/erasure checker, not a new
concept for users.

**Scope is unchanged from RFC-0116 §5.** This is a representation-sharing move for
record-shaped nominal types specifically. It says nothing new about enums (the sum-type
objection stands) or primitives.

## 4. What this RFC does not claim

The strong thesis — that **every** nominal type, not just an opt-in `record`, is
`(brand, row)` under the hood, with the row degrading on partial move — was a live
exploration in `reports/substructural-types/nominal-types-as-branded-rows.md` when this
section was written, deliberately not folded in so this RFC could be accepted on its own
terms.

**Updated 2026-08-30: that thesis is now RFC-0137 (`3-integrated`).** Every `struct`
carries `(brand, row)`, and the row narrows on partial move (RFC-0117, also integrated).
This does **not** collapse §1's tiers — RFC-0137's row is never visible to structural
matching (that is exactly its §1 restriction), so a plain `struct` stays impl-ineligible.
What `record` still adds on top of RFC-0137 is precisely §1's tier-3 cell: the row is
**visible to structural matching and impl-eligible** for row-conditional impls. That
capability is not in RFC-0137 and is why this RFC still has a job; §1's table already
carries the "Restated 2026-08-25 against RFC-0137" note reconciling the wording.

The `Drop`-dispatch problem this section flagged — *how does custom `Drop` dispatch
against a narrowed residual?* — is answered: Open Question 1 above, via RFC-0137 §5's
row-bounded dispatch, now spec text.

---

## Open Questions

1. ~~**`Drop` dispatch against a narrowed named record** (§4). A custom destructor plus a
   residual missing the fields it reads is a leak under the obvious rule.
   `nominal-types-as-branded-rows.md` §4.1–4.3 proposes body-inferred, row-bounded dispatch
   and argues it needs a fixed field-set plus a subset check rather than general row
   machinery — plausible, not adopted here.~~ **Resolved 2026-08-30 — RFC-0137 §5
   (`3-integrated`).** Dispatch is row-bounded: a `Drop` impl's required field set is the
   residual row its `drop` receiver is *declared* as (RFC-0137 §5 as amended 2026-08-28 —
   declared, not body-inferred), and the destructor fires against any residual of that
   brand whose current row is a superset of it. A `record` with custom `Drop` is a nominal
   type, so this applies to it directly — it is the identical question RFC-0117 carried as
   *its* OQ1, closed the same way, and now spec text at
   `spec.ownership.drop-dispatch-against-a-narrowed-residual`. The leak
   `nominal-types-as-branded-rows.md` §4 describes cannot occur: a partial move that would
   leave the residual below the declared required set is rejected at that point
   (spec `…legality-1`), so the destructor is never reached with a field it reads already
   gone. Implementation is gated on metel-core#858 (row-bounded Drop dispatch), the same
   gate RFC-0117's rule sits behind.
2. ~~**Brand-versus-row coherence priority.** An ordinary `extend Point: Display` is
   brand-keyed; a row-conditional impl is row-keyed. If a value matches both, which wins?
   More-specific-wins is the obvious default and is written down nowhere.
   *(From RFC-0090 OQ6; RFC-0118 OQ4 is the same question seen from bound position.)*~~
   **Resolved, 2026-08-25 — RFC-0121 §3 (under review).** The brand-keyed impl wins:
   brand-exact dispatch is checked before row-conditional resolution is attempted, so a
   match there short-circuits it rather than conflicting with it under RFC-0060 §2. For
   tier 3 specifically: a `record` with its own nominal impl of an aspect dispatches to
   that impl over any row-conditional impl its row also satisfies. Owning implementation
   issue: metel-core#833.
3. **Does RFC-0116 §3's allocator-type restriction transfer to tier 3?** That restriction
   assumed structural interchangeability, which a fixed brand arguably removes — a named
   record has per-instance identity in a way an anonymous one does not. ~~Unresolved.~~
   *(From RFC-0090 OQ9.)* **Premise removed 2026-08-30 — RFC-0137 (`3-integrated`).**
   RFC-0116 §3's own stated reason an anonymous record cannot be an allocator is that
   *"allocator identity is per-instance (RFC-0063 §2)"* and an anonymous record has no
   such identity. A `record` brand **is** exactly that per-instance declaration identity
   (RFC-0137 §2/§3; OQ5), so the restriction's rationale does not carry to tier 3 — a
   named record is, on this axis, a `struct`. Whether a `record` may then *actually* serve
   as an allocator type is a question for the allocator cluster (RFC-0063 disjointness,
   RFC-0143), not for this RFC's acceptance; it is no longer an open design gap here, just
   a deferral to where allocator identity is specified.
4. **Is the brand here the same kind as RFC-0076's?** §3 asserts implementer economy by
   reusing `brand-kind-unification.md`'s single identity kind. Whether a
   declaration-minted, compile-time-only, one-introduction tag really is a degenerate case
   of that kind — rather than something that merely resembles it — is argued in that
   document's §8 and not proven. Note this RFC does **not** depend on RFC-0076's runtime
   checking machinery. ~~Unresolved.~~ **Resolved by inheritance 2026-08-30 — RFC-0137
   (`3-integrated`).** RFC-0137 §1 commits the language to treating *every* struct's
   declaration brand as "a fourth surface use of `brand-kind-unification.md` §8's single
   identity kind, not a new concept." A `record` brand is a `struct` brand — §2's upgrade
   path keeps "the nominal name and identity … unchanged" — so this is no longer a
   question this RFC settles or is blocked on: it rides on RFC-0137's integrated model.
   The residual "argued, not proven" concern belongs to `brand-kind-unification.md` /
   RFC-0076, not to accepting `record`.
5. ~~Does a narrowed named record keep its brand? Presumably yes — that is the point of
   §1's third bullet — but the rule is unstated, and it decides whether
   `Handle.{ fd }` is still a `Handle` for impl-resolution purposes.~~ **Answered,
   2026-08-25 — RFC-0137 §2/§3 (then accepted).** Yes, for the general case, not just
   tier 3: narrowing preserves the brand unconditionally for every struct, and
   visibility to structural matching (§1's restated table above) is scoped to the
   brand, fixed at declaration, inherited unchanged by every narrowing. A narrowed
   `record` stays impl-eligible for exactly the same reason a narrowed plain `struct`
   stays ineligible — the row content changed, the brand's own eligibility flag did
   not. **Caveat, 2026-08-25 same day: RFC-0137 was reverted to `1-under-review` the
   same day it was accepted** (its own Open Questions 5-6, opened on reversion, don't
   touch §2/§3's brand-preservation claim directly). **RFC-0137 was re-accepted
   2026-08-27**, all four Open Questions closed. **Checked 2026-08-27: the table
   restatement itself was already made the same day as this answer (§1 above,
   "Restated 2026-08-25") — the previous close of this note was wrong to say it was
   still pending.** Nothing further needed here.

---

## References

- `public/rfcs/5-superseded/rfc-0090-structural-records.md` §8 (tier 3, the tier table,
  the upgrade path) and §9 (identity-tag reuse) — the source
- RFC-0116 (Anonymous Record Types) — the anonymous former this is the nominal counterpart
  to; §5 there declined the records-as-foundation reframing this RFC's §3 narrows
- RFC-0119 (Record Conversions) — tier 2, which this is defined against; **not a
  dependency** (2026-08-23 correction, see header)
- RFC-0121 (Open Rows) — row-conditional impls, the capability §1 says tier 3 exists for;
  §3 there resolves Open Question 2 above (2026-08-25)
- `reports/substructural-types/brand-kind-unification.md` §8 — the single-identity-kind
  proposal §3 reuses
- `reports/substructural-types/nominal-types-as-branded-rows.md` — the stronger thesis §4
  deliberately does not adopt, and §4's `Drop`-dispatch leak
- RFC-0137 (Nominal Types as Branded Rows, `3-integrated`) — the exploration above,
  formalized and merged into `reference/spec/ownership.md`: adopts the stronger thesis for
  every struct, and its §2/§3/§5 resolve Open Questions 5, 1, and the premise of 3; §1's
  table above is restated against it. `record` still adds tier-3's row-visibility and
  impl-eligibility on top (§4)
- RFC-0117 (Row Narrowing, `3-integrated`) — the narrowing rule a `record` residual
  follows; carried the identical `Drop`-dispatch question (its OQ1) closed the same way
- RFC-0076 (RC Brands, `1-under-review`) — related but **not a dependency**; OQ4's
  "same identity kind" concern is now RFC-0137's, not this RFC's

---

## Decision

**Outcome:** *(pending — but no blocking open question remains as of 2026-08-30. OQ2 and
OQ5 were resolved earlier (RFC-0121 §3, RFC-0137 §2/§3); OQ1, OQ3, and OQ4 are resolved
or reduced to a non-blocking deferral by RFC-0137 reaching `3-integrated` — see the
open-question sweep in the header. The remaining gate is an acceptance review confirming
tier 3 is a distinct capability requirement (§1's guardrail) and that `record` still
earns its place on top of RFC-0137's every-struct-is-branded-row model — §4.)*
**Target:** *(set when accepted; committed to v0.13.0 via metel-core#791.)*
