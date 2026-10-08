---
id: LIMIT-TYPE-CONSTRUCTION-004
title: "Generic closure reconstruction omitted captured types"
summary: "Runtime construction lacked the captured bindings' creation-time types when rebuilding a polymorphic closure body."
scope: "architecture/spec/type-construction.md#type-construction"
owner: metel-frontend
discovered_by: "v0.14.0 sensitive release-matrix probe; metel-core#1411"
disposition: known
review: null
---

## Limitation

Generic closure reconstruction previously omitted the static types of captured
bindings. A closure over a partially moved nominal record could therefore fail
with I0010 at its call site; the move checker also could not analyze the body.
Generic closures now carry those creation-time capture types into construction
and ownership analysis. The issue-backed regression
`evaluator/records/release_matrix_generic_residual_capture.mtl` now passes with
move checking enabled, covering partial and empty residual captures and field
restoration. A negative typechecking regression confirms that a moved field
does not become accessible again inside the captured body. The fixes are local
and metel-core#1411 remains open pending integration.

## Impact

Previously, generic closure checking could not reliably reconstruct the
captured value's narrowed nominal type.

## Affects

- `spec.types.generics.rigid-type-parameters.legality-1`
- `spec.functions.closures.dynamics-5`

## Resolution

Implementation is present locally and covered by passing positive and negative
regressions; tracked by metel-core#1411 pending integration.
