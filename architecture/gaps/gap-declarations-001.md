---
id: GAP-DECLARATIONS-001
title: "Tuples and anonymous records cannot implement an aspect"
summary: "A tuple or anonymous record cannot implement an aspect; use a named struct."
scope: "reference/spec/declarations.md#spec.declarations.structural-aspect-bounds.legality-6"
owner: language
discovered_by: "metel-core#1217 limitation analysis; `reference/spec/types.md` (Planned for v0.14.0 note)"
disposition: planned
review: null
---

## Gap

Tuple types have no standard blanket aspect implementations, and a local
aspect cannot be implemented for a tuple or an anonymous record target
(`extend { w: i64 }: MyAspect { … }` does not work). Arrays are the exception,
through the orphan-rule carve-out for structural type constructors. The
Language Spec defers tuples pending a decision between per-arity boilerplate
and variadic generics.

## Impact

A tuple or anonymous record satisfies no aspect that requires an
implementation, so it cannot be printed, compared or passed where such a
bound is required. `extend (i64, i64): Show { … }` is rejected with `T0001`
("cannot `extend` a tuple type"), and the diagnostic hints at using a named struct instead.
Auto-derived aspects are unaffected.

## Affects

- `spec.declarations.structural-aspect-bounds.legality-6`
- `RFC-0061`

## Resolution

Planned for v0.14.0, tracked as metel-core#239.
