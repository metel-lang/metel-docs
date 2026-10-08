---
id: LIMIT-TYPE-CONSTRUCTION-004
title: "Generic row reconstruction can hide an invalid capture"
summary: "A generic function can capture a record remainder whose reconstructed type is not established by its declared bounds."
scope: "architecture/spec/type-construction.md#type-construction"
owner: metel-frontend
discovered_by: "v0.14.0 sensitive release-matrix probe; metel-core#1411"
disposition: known
review: null
---

## Limitation

With ownership checking enabled, a generic function can destructure a nominal
record, capture its residual in a closure, and reconstruct the nominal value
without a declared field-wise bound that justifies the capture. The regression
is `evaluator/records/release_matrix_generic_residual_capture.mtl` and is
tracked by metel-core#1411. The fixture is skipped until the checker rejects
the unsupported construction at the generic definition.

## Impact

Generic ownership checking may accept a closure capture whose concrete
remainder is unavailable from the declared row facts.

## Affects

- `spec.types.generics.rigid-type-parameters.legality-1`
- `spec.functions.closures.dynamics-5`

## Resolution

Open; tracked by metel-core#1411.
