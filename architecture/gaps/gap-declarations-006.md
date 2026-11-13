---
id: GAP-DECLARATIONS-006
title: "`via` states a flow for `Copy` only"
summary: "A derived impl can state which type parameters it depends on only for `Copy` (`derives Copy via T`); `via` on any other entry is an error, so a derived `Clone` has only a computed flow and a public type cannot pin it."
scope: "reference/spec/declarations.md#spec.declarations.aspects.declaration-clauses.legality-11"
owner: language
discovered_by: "language owner review of the v0.16.0 Declarations and derivation milestone, 2026-11-13; metel-core#1941"
disposition: planned
tracked_by: metel-core#2002
rfc: RFC-0227
review: null
---

## Gap

`declaration-clauses.legality-11` accepts `via` on a `Copy` entry of a `derives` clause and makes it an error on any other entry,
because RFC-0224 stated the flow for `Copy` and deferred the other markers. Nothing in the mechanism is specific to `Copy`: a derived
impl bounds each type parameter a field holds by value by the derived aspect itself, and `via` replaces the computed set with a stated
one. A correct implementation of the current spec still rejects `derives Clone via T`.

## Impact

A derived `Clone` carries a computed flow only, so a `pub` generic type's `Clone` interface moves with its fields, and the `pub` rule of
`declaration-clauses.legality-13` (a public generic type states a non-empty flow) applies to `Copy` alone. The same holds for any
field-wise derivation added later. The workaround is a hand-written `Clone` impl with the bounds written out.

## Affects

- `spec.declarations.aspects.declaration-clauses.legality-11`
- `spec.declarations.aspects.declaration-clauses.legality-13`
- `RFC-0224`
- `RFC-0227`

## Resolution

Planned: RFC-0227 (stated flow for every derived impl, tracked as metel-core#2002) generalises `via` to every field-wise
derivation, widens the `pub` statement to every derived impl, and defines `derivable` as field-wise. The gap closes when the spec text of
legality-11 and legality-13 changes and the `Copy`-only guard in the clause expansion is lifted.
