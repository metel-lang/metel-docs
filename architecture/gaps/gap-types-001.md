---
id: GAP-TYPES-001
title: "No higher-rank polymorphism"
scope: "reference/spec/types.md#type-inference"
owner: language
discovered_by: "metel-core#1218 limitation analysis; fixture `typechecking/generics/limit_01_rank1_fn_arg.mtl`; `reference/spec/functions.md` First-Class Functions"
disposition: known
review: null
---

## Gap

Inference is Hindley-Milner, which is rank-1: a quantifier appears only at
the outermost level of a type. Two consequences follow, and the Language Spec
states the second:

- A function parameter is a monotype. An unannotated `f` in
  `fun apply_both(f, x: i64, y: boolean)` cannot be applied to both an `i64`
  and a `boolean`; the second use is rejected (`T0001`).
- A generic function may not be referenced where the receiving position is
  itself still generic in the callee (rank-2), nor where nothing pins down a
  concrete instantiation; both are `T0003`.

## Impact

A Metel programmer cannot write a function that takes a polymorphic function
argument and uses it at more than one type. Each use needs its own
instantiation, or the argument must be a concrete function type.

## Affects

- `spec.functions.first-class-functions.legality-2`
- `RFC-0138`

## Resolution

None recorded: no RFC or issue plans higher-rank polymorphism. RFC-0138 (implemented) defines
the current boundary.
