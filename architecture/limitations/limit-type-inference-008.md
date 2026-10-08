---
id: LIMIT-TYPE-INFERENCE-008
title: "Field-wise Clone is not entailed for a borrowed open row"
summary: "A where all R: Clone grant on a borrowed open-row parameter is rejected before its body can be checked."
scope: "architecture/spec/type-inference.md#type-inference"
owner: metel-frontend
discovered_by: "v0.14.0 sensitive release-matrix probe; metel-core#1412"
disposition: known
review: null
---

## Limitation

A function accepting `&{ ..R }` with `where all R: Clone` was rejected with
`T0012` before the body was checked. The parameter lowering now preserves the
reference while collecting its open-row bound, and borrowed rows no longer get
the by-value `Copy` width check. The regression
`evaluator/records/release_matrix_borrowed_all_clone.mtl` passes locally without
a skip; see metel-core#1412, which remains open pending integration.

## Impact

Generic code cannot express this borrowed-row cloning operation with the
field-wise bound that works for owned open rows.

## Affects

- `spec.types.generics.field-wise-row-constraints.legality-1`
- `spec.types.generics.open-rows.legality-4`

## Resolution

Implementation is present locally and covered by the unskipped regression;
tracked by metel-core#1412 pending merge.
