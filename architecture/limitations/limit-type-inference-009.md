---
id: LIMIT-TYPE-INFERENCE-009
title: "Nominal residual coercion misses a row-conditional aspect impl"
summary: "A partial nominal row can dispatch an aspect method but fail coercion to the same dyn aspect."
scope: "architecture/spec/type-inference.md#type-inference"
owner: metel-frontend
discovered_by: "v0.14.0 sensitive release-matrix probe; metel-core#1413"
disposition: known
review: null
---

## Limitation

A partial nominal record whose current row satisfies a row-conditional aspect impl accepts ordinary method dispatch, but its coercion to that object-safe `dyn Aspect` is rejected with `T0012`. This loses the current-row implementation at the erasure boundary; it is not an object-safety failure. Transparent dyn aliases exhibit the same failure.

Reproduced against core `784eb8f96f598122b4cacbd2f8e099b42f3f31e2`.
The expected-success fixture is skipped with a link to this record, rather than
asserting the compiler's incorrect rejection as intended behavior.

## Impact

The corresponding sensitive release-matrix boundary is blocked. Passing neighboring
concrete cases is not proof that this interaction works.

## Affects

- `spec.declarations.aspects.dyn-aspect.legality-6`
- `metel-interpreter/tests/integration/sources/evaluator/records/release_matrix_residual_dyn_alias`

## Resolution

Open: [metel-core#1413](https://github.com/metel-lang/metel-core/issues/1413).
The fixture must become executable when the fix lands; no fix or release deferral
is claimed by recording this limitation.
