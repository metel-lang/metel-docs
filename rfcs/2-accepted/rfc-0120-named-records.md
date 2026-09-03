---
id: rfc-0120
title: "Named Records"
date: '2026-07-24'
status: accepted
tracking: 'https://github.com/metel-lang/metel-core/issues/791'
target: v0.13.0
updated: '2026-08-30'
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
> **Open-question sweep, 2026-08-30** (and tightened the same day after an adversarial
> review). RFC-0137 (Nominal Types as Branded Rows) is now `3-integrated`, and it resolves
> or absorbs the three open questions that were still live:
>
> - **OQ1** (`Drop` dispatch against a narrowed named record) — the *design* is settled by
>   RFC-0137 §5's row-bounded dispatch, the same rule that closed RFC-0117's identical
>   question, now spec text. But the narrowed `drop`-receiver *spelling* it relies on
>   (RFC-0109/0147/0148) is not integrated, so §2 makes a v0.13 scoping decision: a
>   `record` with custom `Drop` uses a whole-row `&var self` receiver — no narrowed
>   receiver, no partial move of it — until that syntax lands. Not an open design
>   question; a recorded restriction.
> - **OQ3** — a `record` brand *is* the per-instance declaration identity RFC-0116 §3
>   said an anonymous record lacks, so that specific objection does not transfer; a named
>   record has the same allocator-type eligibility as a `struct`, subject to the allocator
>   cluster's own not-yet-specified custom-`Alloc` story (RFC-0063).
> - **OQ4** — "same brand kind as RFC-0076's" is now RFC-0137's committed model for every
>   struct brand, which a `record` brand simply is.
>
> **No blocking open question remains.** §1's table was already restated against RFC-0137
> (2026-08-25); §4's "deliberately not folded in" note is likewise now historical. §5
> (field visibility, numeric labels) and §6 (generic named records) were added the same
> day to close gaps the review found.

> **Status — accepted (2026-08-30).** Named records: the declared row is structurally visible for row bounds and row-conditional impl resolution where a plain struct's is not (Summary). All open questions resolved (OQ1 design settled by RFC-0137 §5 with a recorded v0.13 whole-row-receiver restriction; OQ2/4/5 via RFC-0121/RFC-0137; OQ3 = same eligibility as struct). §1 guardrail reviewed and holds: tier 1 and tier 3 are opposite capability commitments, tier 2 is a scoped lossy bridge. Spec-rule pass deferred to integration.

## Summary

A third declaration kind alongside `struct`, `enum` and `aspect`:

```metel
record Handle { fd: i32, alloc: @a Buffer }
```

A named record carries a `(row, brand)` representation **intrinsically**, not convertibly.
That is the one capability RFC-0119's conversions cannot supply at any cost: row-conditional
impls are resolved by the type system matching a type's own declared row at
impl-resolution time, and there is no call site for a derived conversion to intercept.

**Normatively: `record X { … }` is identical to `struct X { … }` in every respect —
name, brand, identity, construction, field access, coherence — except one: a `record`'s
declaration brand is *structurally visible*, so its own declared row satisfies row bounds
(RFC-0118) and is matched by row-conditional impl resolution (RFC-0121). A plain
`struct`'s brand is not (RFC-0137 §3).** Everything else in this RFC follows from that one
bit.

`record` is now the keyword's only job — RFC-0116 dropped it from the anonymous former.

---

## Motivation

RFC-0119 lets a struct convert to a record on demand. That covers the local
drain-and-restore pattern, but the converted value is a *different* value with a different
type, brand-stripped, alive only while it is held.

**After RFC-0137, `record`'s job is precisely one capability: the declared row is visible
to impl resolution.** That is the Summary's one bit, and it takes two forms that RFC-0118
OQ4 already notes are the same question from two positions:

- **Row-conditional impls** (`extend<row R: { token: Token, .. }> Session<..R>`) —
  resolution matches the type's *own* declared row, so `Session` gains or loses methods as
  its row narrows. Tier 2 cannot express this at all: an impl on the converted anonymous
  value is brandless and matches every same-shaped value, not `Session`.
- **Direct row-bound satisfaction** — a `Session` value itself satisfies
  `<record T: { token, .. }>`, brand intact, rather than a caller having to pass
  `session.to_record()` and lose the identity.

*(The third motivation this section once listed — "a residual that keeps its identity" —
is now universal, not tier-3-only: RFC-0137 preserves the brand through narrowing for
every `struct`. It is no longer a reason to reach for `record`; §4 records the change.)*

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
would otherwise have to publish the whole row as public API (§2, §5 — every `record` field
is public) and accept the coherence-priority rules that only matter for types with
row-conditional impls — paying for machinery never asked for. Tier 2 grants the row
*operation* while keeping the layout private.

**The guardrail this depends on:** each tier must correspond to a distinct *capability
requirement* — "no row access" / "temporary, explicit, non-impl-eligible" / "permanent,
impl-eligible" — never offered as interchangeable ways to do the same thing.

**Acceptance review of the guardrail, 2026-08-30.** It holds. There are two *fundamental*
capabilities, and they are opposite commitments:

- **Tier 1 (`struct`) — a private row.** Layout is encapsulated; field renames are
  refactoring; nothing outside the module is structurally coupled to the shape.
- **Tier 3 (`record`) — a published structural row.** The declared row participates in
  impl resolution (Motivation), which is *unavailable* at tier 1 by any amount of extra
  code — the resolver does not look at a `struct`'s row, deliberately (RFC-0137 §3, to
  keep structural eligibility from going ambient). And it is a one-way door: §2's cost.

  Tier 1 → tier 3 is not "the same thing done differently"; it is choosing the opposite
  side of an encapsulation trade.

**Tier 2 is a scoped bridge, not a co-equal third capability.** `#derive(ToRecord,
FromRecord)` grants a *local, explicit, lossy* row view (a brand-stripped copy) without
moving the type off tier 1. It is genuinely distinct from tier 3 for the use case that
matters — a row-conditional impl on the *nominal* type is impossible via tier 2, because
the converted value has no brand — so it is not an interchangeable way to get what
`record` gets. It is best read as tier 1 plus an escape hatch, priced (a copy, brand
loss, non-impl-eligible), for the author who needs a row operation once and not a
contract.

So the guardrail's three points are real: tier 1 and tier 3 are distinct *and opposite*
capability requirements; tier 2 is distinct-by-limitation from tier 3 and additive over
tier 1. No two are interchangeable.

A tier-3 type gets tier 2's conversions for free: `to_record`/`from_record` on a type that
already *is* `(row, brand)` are the identity coercion, nothing to derive separately.

## 2. The upgrade path

`struct` → `record` should require touching no existing caller, provided:

- The nominal name and identity are unchanged — aspect impls, orphan-rule coherence and
  generic instantiation all key off the same identity as before.
- Construction and field-access syntax are unchanged. `record X { … }` construction is
  ordinary nominal (struct-literal) construction — this RFC introduces **no**
  anonymous-row-to-`X` coercion and does not make "a row becomes `Self`" a privileged
  operation. If RFC-0114 (`Construct`) later routes *all* nominal construction through a
  constructor, `record` follows that change uniformly with `struct`; it is not singled
  out.
- Whole-value use sites keep typechecking exactly as before, against the record's full row.
- Row tracking costs nothing at runtime for whole-value-only callers.
- **Custom `Drop` on the upgraded type keeps a whole-row `&var self` receiver.** The
  narrowed-receiver forms (RFC-0109/0147/0148) that would let a destructor read a strict
  subset are not integrated yet (Open Question 1), so until they are, a `record` with
  custom `Drop` may not partially-move `self`, exactly as RFC-0071 §7 already requires for
  any `Drop` type.

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
carries `(brand, row)`, and the row narrows on partial move (RFC-0117, implemented).
This does **not** collapse §1's tiers — RFC-0137's row is never visible to structural
matching (that is exactly its §1 restriction), so a plain `struct` stays impl-ineligible.
What `record` still adds on top of RFC-0137 is precisely §1's tier-3 cell: the row is
**visible to structural matching and impl-eligible** for row-conditional impls. That
capability is not in RFC-0137 and is why this RFC still has a job; §1's table already
carries the "Restated 2026-08-25 against RFC-0137" note reconciling the wording.

The `Drop`-dispatch problem this section flagged — *how does custom `Drop` dispatch
against a narrowed residual?* — is answered: Open Question 1 above, via RFC-0137 §5's
row-bounded dispatch, now spec text.

## 5. Field visibility, and numeric labels

**Every field of a `record` is public.** A field-visibility modifier (`private`, or a
non-`public` field where the module default is private) on a `record` declaration is a
compile error. This is not a restriction so much as what the declaration *means*: §2
already establishes that `record X` publishes its row as the type's interface — "a
record's API is what it contains" (RFC-0118 §3). A partially-private row would make a
bound like `<record T: { token, .. }>` either a privacy oracle (it reveals whether a
field the caller can't name exists) or a bound over a label the caller cannot access;
neither is coherent. An author who wants a private field wants a `struct` (tier 1) or
tier 2's local, brand-stripped conversion.

**Numeric field labels are deferred to RFC-0151.** If `(A, B)` becomes the numeric-label
row `{ 0: A, 1: B }` (RFC-0151, `0-draft`), whether `record R { 0: i64 }` is a legal
declaration is that RFC's call, to be made before it is accepted. Either way it does not
threaten `record`: a `record` always carries a brand, so even `record R { 0: i64, 1:
String }` and the brandless tuple `(i64, String)` of the same shape stay distinct types —
the tuple never satisfies a `record`-kinded bound and `R` never matches a bound written
for a bare tuple.

## 6. Generic named records

`record` composes with type parameters exactly as `struct` does: `record Session<T> {
token: T, log: List<String> }` declares the row `{ token: T, log: List<String> }` with
`T` symbolic, and each instantiation substitutes as for a struct's fields — `Session<Api>`
has the row `{ token: Api, .. }`.

Row-conditional impl resolution is checked **under the impl's own substitution**, against
the instantiated row. An `extend<row R: { token: Api, .. }> Session<..R>` matches
`Session<Api>` and not `Session<i64>`; an `extend<T> ...` impl written over an unbound
`token: T` matches every instantiation. This is the same rule RFC-0137 applies to a
generic brand's symbolic field types (including a `Drop` impl's required set), so `record`
introduces no new generic behavior — only the visibility bit of §Summary, applied to the
parameterized row.

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
   gone.

   **v0.13 scope, not an open design question.** The spec's own `…legality-3` records that
   the *narrowed* `drop`-receiver spelling this relies on — `&var self: Self.{ a, b }` or
   a row-parameter receiver — depends on RFC-0109/0147/0148, none of which is integrated;
   *"until then a drop receiver is always the whole value and the required set is always
   the whole row."* So for v0.13, a `record` with custom `Drop` takes a whole-row
   `&var self` and may not partially-move it (§2), which is exactly RFC-0071 §7's existing
   rule for every `Drop` type. The narrowed case — a destructor that reads only a subset,
   run against a residual — is fully specified in the design and becomes reachable for
   `record` the moment the receiver syntax lands, with no further decision needed here.
   Implementation is gated on metel-core#858 (row-bounded Drop dispatch), the same gate
   RFC-0117's rule sits behind.
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
   *(From RFC-0090 OQ9.)* **Answered 2026-08-30 — same eligibility as `struct`.**
   RFC-0116 §3's stated reason an anonymous record cannot be an allocator is that
   *"allocator identity is per-instance (RFC-0063 §2)"* and an anonymous record has no
   such identity. A `record` brand **is** that per-instance declaration identity
   (RFC-0137 §2/§3; OQ5), so that specific objection does not transfer: **a named record's
   allocator-type eligibility is exactly a `struct`'s** — no better, no worse. What that
   eligibility actually *is* — whether any nominal type may implement `Alloc`, how the
   disjointness rules apply — is unspecified in the allocator cluster itself (RFC-0063
   defers custom-`Alloc` authoring; RFC-0143 is unwritten), and `record` neither needs nor
   pre-empts that answer. So: not an open design gap for *this* RFC, and not a special
   restriction on `record`; it inherits `struct`'s answer whenever the allocator cluster
   gives one.
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
- `reports/substructural-types/nominal-types-as-branded-rows.md` — the exploration whose
  strong thesis §4 kept separate at the time; that thesis is now RFC-0137 (`3-integrated`)
  and §4 is updated to say so. Its §4.1–4.3 `Drop`-dispatch leak analysis is what RFC-0137
  §5's row-bounded dispatch answers (Open Question 1)
- RFC-0137 (Nominal Types as Branded Rows, `3-integrated`) — the exploration above,
  formalized and merged into `reference/spec/ownership.md`: adopts the stronger thesis for
  every struct, and its §2/§3/§5 resolve Open Questions 5, 1, and the premise of 3; §1's
  table above is restated against it. `record` still adds tier-3's row-visibility and
  impl-eligibility on top (§4)
- RFC-0117 (Row Narrowing, `4-implemented`) — the narrowing rule a `record` residual
  follows; carried the identical `Drop`-dispatch question (its OQ1) closed the same way
- RFC-0076 (RC Brands, `1-under-review`) — related but **not a dependency**; OQ4's
  "same identity kind" concern is now RFC-0137's, not this RFC's

---

## Decision

**Outcome:** **Ready for acceptance, 2026-08-30.** No blocking open question remains after
the adversarial review pass: OQ2 / OQ5 resolved earlier (RFC-0121 §3, RFC-0137 §2/§3);
OQ1's design is settled by RFC-0137 §5 with a recorded v0.13 whole-row-receiver
restriction (§2, OQ1); OQ3 answered as "same allocator eligibility as `struct`"; OQ4
inherited from RFC-0137. §5 fixes field visibility (all fields public) and defers numeric
labels to RFC-0151; §6 states the generic rule. **The §1 guardrail was reviewed and
holds** — tier 1 (private row) and tier 3 (published structural row) are distinct and
opposite capability requirements, and tier 2 is distinct-by-limitation from tier 3 and
additive over tier 1; none is an interchangeable way to do another's job. The only work
left is the spec-rule pass (coverage frontmatter + Legality Rule blocks for declaration
grammar, structural-visibility eligibility, row-bound/impl dispatch, upgrade behaviour)
done at the `3-integrated` transition, as for RFC-0117 and RFC-0129.
**Target:** v0.13.0, via metel-core#791.
