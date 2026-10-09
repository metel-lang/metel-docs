---
id: LIMIT-TYPE-INFERENCE-008
title: "Field-wise Clone is not entailed for a borrowed open row"
summary: "A where all R: Clone grant on a borrowed open-row parameter is rejected before its body can be checked."
scope: "architecture/spec/type-inference.md#type-inference"
owner: metel-frontend
discovered_by: "v0.14.0 sensitive release-matrix probe; metel-core#1412"
disposition: resolved
review: null
---

## Limitation

A function accepting `&{ ..R }` with `where all R: Clone` was rejected with
`T0012` before the body was checked. The parameter lowering now preserves the
reference while collecting its open-row bound, and borrowed rows no longer get
the by-value `Copy` width check. The regression
`evaluator/records/release_matrix_borrowed_all_clone.mtl` passes without a skip.
The fix merged in metel-core PR #1422.

## Impact

Previously, generic code could not express this borrowed-row cloning operation
with the field-wise bound that worked for owned open rows.

## Affects

- `spec.types.generics.field-wise-row-constraints.legality-1`
- `spec.types.generics.open-rows.legality-4`

## Resolution

Implemented in metel-core commit `5f038b189cb67c5ec40e51d16a3e11a831a4535e`
(PR #1422), with empty/nonempty borrowed-row cloning and retained source
ownership covered by the executable fixture above; tracked by metel-core#1412.
Diagnostics for unused row constraints now state the required row context
without referring to the closed implementation tracker metel-core#1302.
