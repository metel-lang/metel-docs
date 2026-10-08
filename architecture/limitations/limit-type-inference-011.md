---
id: LIMIT-TYPE-INFERENCE-011
title: "A field-wise Clone grant does not entail Clone for an open-row record"
summary: "An owned generic row with `where all R: Clone` cannot clone the entire open-row value inside its body."
scope: "architecture/spec/type-inference.md#type-inference"
owner: metel-frontend
discovered_by: "v0.14.0 sensitive release-matrix probe; metel-core#1420"
disposition: known
review: null
---

## Limitation

A generic function with an owned parameter `{ id: i64, ..R }` and
`where all R: Clone` is rejected with `T0035` when its body calls `value.clone()`.
The fixed field type is Clone and the declared field-wise grant covers the open
tail, so this call should be available from the definition. The issue-backed
regression is `evaluator/records/release_matrix_bounded_clone_residual_callback.mtl`;
see metel-core#1420. This differs from #1412, which is rejected earlier at the
where clause for a borrowed open-row parameter.

## Impact

Generic code cannot use field-wise Clone to duplicate an owned anonymous row,
even when every field is known to satisfy Clone.

## Affects

- `spec.types.generics.field-wise-row-constraints.legality-1`
- `spec.types.generics.rigid-type-parameters.legality-1`

## Resolution

Open; tracked by metel-core#1420.
