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
`where all R: Clone` was rejected with `T0035` when its body called
`value.clone()`. Generic method entailment now accounts for the fixed row fields
and carries the declared field-wise requirement to the open tail. The regression
`evaluator/records/release_matrix_bounded_clone_residual_callback.mtl` now passes
locally without a skip; metel-core#1420 remains open pending integration.

## Impact

Generic code cannot use field-wise Clone to duplicate an owned anonymous row,
even when every field is known to satisfy Clone.

## Affects

- `spec.types.generics.field-wise-row-constraints.legality-1`
- `spec.types.generics.rigid-type-parameters.legality-1`

## Resolution

Implementation is present locally and covered by the unskipped regression;
tracked by metel-core#1420 pending merge.
