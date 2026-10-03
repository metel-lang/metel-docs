---
id: GAP-DECLARATIONS-001
title: "Tuples cannot implement an aspect"
summary: "A tuple cannot implement an aspect; use a named struct. An anonymous record can, for a local aspect, through a record-target `extend`."
scope: "reference/spec/declarations.md#spec.declarations.structural-aspect-bounds.legality-6"
owner: language
discovered_by: "metel-core#1217 limitation analysis; `reference/spec/types.md` (Planned for v0.14.0 note)"
disposition: planned
planned_for: v0.14.0
rfc: RFC-0061
review: null
---

## Gap

Tuple types have no standard blanket aspect implementations, and a local
aspect cannot be implemented for a tuple target (`extend (i64, i64): MyAspect { … }`
does not work). Arrays are the exception, through the orphan-rule carve-out for
structural type constructors, and anonymous records now are too: a local aspect
can be implemented for a record target, closed or row-tailed (`extend { w: i64 }: MyAspect`,
`extend<row R: { w: i64, .. }> { ..R }: MyAspect`; RFC-0121 §3, metel-core#1306 item 8).
The Language Spec defers tuples pending a decision between per-arity boilerplate
and variadic generics.

## Impact

A tuple satisfies no aspect that requires an implementation, so it cannot be
printed, compared or passed where such a bound is required. `extend (i64, i64): Show { … }`
is rejected with `T0001` ("cannot `extend` a tuple type"), and the diagnostic hints at
using a named struct instead. Auto-derived aspects are unaffected.

## Affects

- `spec.declarations.structural-aspect-bounds.legality-6`
- `RFC-0061`

## Resolution

Records: resolved by metel-core#1306 item 8. Tuples: planned for v0.14.0, tracked as
metel-core#239.
