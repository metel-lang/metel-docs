---
id: rfc-0120
title: "Named Records"
date: '2026-07-24'
status: under-review
tracking: 'https://github.com/metel-lang/metel-core/issues/791'
target:
updated: '2026-08-23'
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

| Tier | Declaration | Row access | Impl-eligible |
|---|---|---|---|
| 1 | `struct` | none | — |
| 2 | `struct` + `#derive(ToRecord, FromRecord)` | explicit, temporary, per-call | no |
| 3 | `record` | intrinsic, permanent | yes |

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
`(brand, row)` under the hood, with the row degrading on partial move — is a live
exploration in `reports/substructural-types/nominal-types-as-branded-rows.md` and is
**deliberately not folded in here.** It is a genuinely different architecture: it would make
row-shapedness the default rather than a tier, which contradicts §1's entire framing. Kept
separate so this RFC can be accepted or refused on its own terms.

That document also raises a real problem this RFC inherits the moment narrowing is extended
to nominal types: **how does custom `Drop` dispatch against a narrowed residual?** Its §4
gives a concrete leak under the naive reading. RFC-0116 §3 forbids custom `Drop` on
anonymous records, so the question does not arise there — it arises here, and is not
answered.

---

## Open Questions

1. **`Drop` dispatch against a narrowed named record** (§4). A custom destructor plus a
   residual missing the fields it reads is a leak under the obvious rule.
   `nominal-types-as-branded-rows.md` §4.1–4.3 proposes body-inferred, row-bounded dispatch
   and argues it needs a fixed field-set plus a subset check rather than general row
   machinery — plausible, not adopted here.
2. **Brand-versus-row coherence priority.** An ordinary `extend Point: Display` is
   brand-keyed; a row-conditional impl is row-keyed. If a value matches both, which wins?
   More-specific-wins is the obvious default and is written down nowhere.
   *(From RFC-0090 OQ6; RFC-0118 OQ4 is the same question seen from bound position.)*
3. **Does RFC-0116 §3's allocator-type restriction transfer to tier 3?** That restriction
   assumed structural interchangeability, which a fixed brand arguably removes — a named
   record has per-instance identity in a way an anonymous one does not. Unresolved.
   *(From RFC-0090 OQ9.)*
4. **Is the brand here the same kind as RFC-0076's?** §3 asserts implementer economy by
   reusing `brand-kind-unification.md`'s single identity kind. Whether a
   declaration-minted, compile-time-only, one-introduction tag really is a degenerate case
   of that kind — rather than something that merely resembles it — is argued in that
   document's §8 and not proven. Note this RFC does **not** depend on RFC-0076's runtime
   checking machinery.
5. **Does a narrowed named record keep its brand?** Presumably yes — that is the point of
   §1's third bullet — but the rule is unstated, and it decides whether
   `Handle.{ fd }` is still a `Handle` for impl-resolution purposes.

---

## References

- `public/rfcs/5-superseded/rfc-0090-structural-records.md` §8 (tier 3, the tier table,
  the upgrade path) and §9 (identity-tag reuse) — the source
- RFC-0116 (Anonymous Record Types) — the anonymous former this is the nominal counterpart
  to; §5 there declined the records-as-foundation reframing this RFC's §3 narrows
- RFC-0119 (Record Conversions) — tier 2, which this is defined against; **not a
  dependency** (2026-08-23 correction, see header)
- RFC-0121 (Open Rows) — row-conditional impls, the capability §1 says tier 3 exists for
- `reports/substructural-types/brand-kind-unification.md` §8 — the single-identity-kind
  proposal §3 reuses
- `reports/substructural-types/nominal-types-as-branded-rows.md` — the stronger thesis §4
  deliberately does not adopt, and §4's `Drop`-dispatch leak
- RFC-0076 (Brand Types) — related but **not a dependency**; see OQ4

---

## Decision

**Outcome:** *(pending)*
**Target:** *(set when accepted)*
