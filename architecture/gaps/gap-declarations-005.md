---
id: GAP-DECLARATIONS-005
title: "`derivable` is a property only std aspects have, and the derivations are written by the compiler"
summary: "`derives A` is legal only for an aspect whose declaration says `derivable`, which only `std::core` can say, and the compiler writes the impl itself; a user cannot make an aspect derivable or register a deriver."
scope: "reference/spec/declarations.md#spec.declarations.aspects.declaration-clauses.legality-3"
owner: language
discovered_by: "language owner review of the v0.16.0 Declarations and derivation milestone, 2026-11-13; metel-core#1829"
disposition: planned
tracked_by: metel-core#799
rfc: RFC-0093
review: null
---

## Gap

The `derivable` property (RFC-0212) makes `derives A` legal, and the specification restricts it to the standard library
(`Aspect Declaration Properties`). `derives A` is legal exactly when `A` has a derivation (`declaration-clauses.legality-3`), and in the
current language only `Clone` and `Copy` do: the compiler writes both impls after name resolution, field by field. A correct
implementation of the current spec has the same limit: there is no syntax for a user to mark an aspect `derivable`, and no mechanism to
supply a deriver. `struct P derives Eq` is `T0046` ("`Eq` has no derivation"), and so is `derives` of any aspect a user declares.

## Impact

Every impl of an aspect other than `Copy` and `Clone` is written by hand, for std and user aspects alike. The planned std derivables
(`Eq`, `Ord`, `Hash`, `Display`; RFC-0093 section 2) cannot be added as ordinary aspects, and a library cannot ship a derivable aspect.
The workaround is a hand-written `extend`.

## Affects

- `spec.declarations.aspects.declaration-clauses.legality-3`
- `spec.declarations.aspects.aspect-declaration-properties.legality-2`
- `RFC-0093`
- `RFC-0207`
- `RFC-0212`
- `RFC-0227`

## Resolution

Planned: RFC-0093 (derive registration, under review, tracked as metel-core#799) proposes the registration half, a comptime function
that implements an aspect's derivation, and waits on the comptime core and execution model (RFC-0092, RFC-0132). RFC-0222 (draft) is the
template-derivation case (`derives Builder`) the same mechanism has to account for. The compiler-written `Clone` derivation is to be
replaced by the comptime derive (metel-core#1829). The gap closes when a user aspect can be declared derivable and the spec text of the
property table changes.
