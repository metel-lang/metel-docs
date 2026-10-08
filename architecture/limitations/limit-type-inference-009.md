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

Row-conditional method dispatch succeeds on a partial nominal residual, but
coercing the same receiver to `dyn Aspect` fails with `T0012`. The skipped
regression is `evaluator/records/release_matrix_residual_dyn_alias.mtl`; see
metel-core#1413.

## Impact

An otherwise available row-conditional implementation cannot be used through
the corresponding existential aspect type after record narrowing.

## Affects

- `spec.types.generics.row-conditional-impls.legality-1`
- `spec.declarations.aspects.dyn-aspect.legality-6`

## Resolution

Open; tracked by metel-core#1413.
