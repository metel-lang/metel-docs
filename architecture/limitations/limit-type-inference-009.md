---
id: LIMIT-TYPE-INFERENCE-009
title: "A partial nominal residual cannot be coerced to a row-conditional dyn aspect"
summary: "Row-conditional dispatch works on a partial nominal residual, but coercion of that receiver to dyn Aspect fails."
scope: "architecture/spec/type-inference.md#type-inference"
owner: metel-frontend
discovered_by: "v0.14.0 sensitive release-matrix probe; metel-core#1413"
disposition: known
review: null
---

## Limitation

Row-conditional method dispatch succeeded on a partial nominal residual, but
coercing that receiver to `dyn Aspect` failed with `T0012`; runtime coercion also
assumed every value had a nominal type id, rejecting anonymous records. Dyn
values now retain an optional nominal id and the concrete structural receiver
type, and runtime dispatch routes structural values through record/pattern
impl lookup. `evaluator/records/release_matrix_residual_dyn_alias.mtl` now passes
locally without a skip; see metel-core#1413, which remains open pending
integration.

## Impact

An otherwise available row-conditional implementation cannot be used through
the corresponding existential aspect type after record narrowing.

## Affects

- `spec.types.generics.row-conditional-impls.legality-1`
- `spec.declarations.aspects.dyn-aspect.legality-6`

## Resolution

Implementation is present locally and covered by the unskipped regression;
tracked by metel-core#1413 pending integration.
