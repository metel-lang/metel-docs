---
id: LIMIT-TYPE-INFERENCE-009
title: "A partial nominal residual cannot be coerced to a row-conditional dyn aspect"
summary: "Row-conditional dispatch works on a partial nominal residual, but coercion of that receiver to dyn Aspect fails."
scope: "architecture/spec/type-inference.md#type-inference"
owner: metel-frontend
discovered_by: "v0.14.0 sensitive release-matrix probe; metel-core#1413"
disposition: resolved
review: null
---

## Limitation

Row-conditional method dispatch succeeded on a partial nominal residual, but
coercing that receiver to `dyn Aspect` failed with `T0012`; runtime coercion also
assumed every value had a nominal type id, rejecting anonymous records. Dyn
values now retain an optional nominal id and the concrete structural receiver
type, and runtime dispatch routes structural values through record/pattern
impl lookup. `evaluator/records/release_matrix_residual_dyn_alias.mtl` passes
without a skip. The fix merged in metel-core PR #1422.

## Impact

Previously, an otherwise available row-conditional implementation could not be
used through the corresponding existential aspect type after record narrowing.

## Affects

- `spec.types.generics.row-conditional-impls.legality-1`
- `spec.declarations.aspects.dyn-aspect.legality-6`

## Resolution

Implemented in metel-core commit `5f038b189cb67c5ec40e51d16a3e11a831a4535e`
(PR #1422). The executable fixture above covers nominal residuals, anonymous
rows, a transparent dyn alias, and captured dynamic dispatch; tracked by
metel-core#1413.
