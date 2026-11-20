---
id: GAP-DECLARATIONS-006
title: "`via` stated a flow for `Copy` only"
summary: "RESOLVED: RFC-0227 (Derivation Arguments) replaces `via` with an argument list on a `derives` entry, accepted for `Clone` as well as `Copy`, and the `pub` rule applies to both."
scope: "reference/spec/declarations/aspects/declaration-clauses.md#spec.declarations.aspects.declaration-clauses.legality-11"
owner: language
discovered_by: "language owner review of the v0.16.0 Declarations and derivation milestone, 2026-11-13; metel-core#1941"
disposition: resolved
review: null
---

## Gap

**Resolved.** A derived impl could state which type parameters it depends on only for `Copy` (`derives Copy via T`); `via` on any other
entry was an error, so a derived `Clone` had only a computed flow and a `pub` generic type's `Clone` interface moved with its fields.
RFC-0227 (Derivation Arguments, `4-implemented`) replaces `via` with an argument list on the entry, `derives Clone(T), Copy(T)`,
accepted for every field-wise derivation, and widens the `pub` rule of `declaration-clauses.legality-13` to `Clone`.

## Impact

None remaining: `derives Clone(T)` states the `Clone` flow, and a `pub` generic type that omits a non-empty one is an error with a
fix-it.

## Affects

- `RFC-0227`

## Resolution

Resolved 2026-11-16: RFC-0227 reached `3-integrated` (spec text in
`reference/spec/declarations/aspects/declaration-clauses.md#spec.declarations.aspects.declaration-clauses.legality-11` to `legality-13`) and then
`4-implemented`, landed in metel-core#2069 (tracked by metel-core#2067).
