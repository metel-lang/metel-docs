---
id: LIMIT-TYPE-CONSTRUCTION-004
title: "Let-polymorphic closure over a nominal residual fails at call time"
summary: "A generic closure capturing a partial nominal residual can raise I0010 when instantiated."
scope: "architecture/spec/type-construction.md#type-construction"
owner: metel-frontend
discovered_by: "v0.14.0 sensitive release-matrix probe; metel-core#1411"
disposition: known
review: null
---

## Limitation

The definition is accepted, but calling the inferred generic closure that owns a partial nominal residual raises `I0010` in both modes. The surviving field is available; this is not a legitimate missing-field error. The concrete capture-entry ownership fix does not repair reconstruction of the let-polymorphic body.

Reproduced against core `784eb8f96f598122b4cacbd2f8e099b42f3f31e2`.
The expected-success fixture is skipped with a link to this record, rather than
asserting the compiler's incorrect rejection as intended behavior.

## Impact

The corresponding sensitive release-matrix boundary is blocked. Passing neighboring
concrete cases is not proof that this interaction works.

## Affects

- `spec.functions.closures.dynamics-5`
- `metel-interpreter/tests/integration/sources/evaluator/records/release_matrix_generic_residual_capture`

## Resolution

Open: [metel-core#1411](https://github.com/metel-lang/metel-core/issues/1411).
The fixture must become executable when the fix lands; no fix or release deferral
is claimed by recording this limitation.
