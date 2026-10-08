---
id: LIMIT-TYPE-INFERENCE-008
title: "Borrowed open-row parameters do not consume field-wise bounds"
summary: "where all R: Aspect is rejected when its parameter's open-row tail is under a reference."
scope: "architecture/spec/type-inference.md#type-inference"
owner: metel-frontend
discovered_by: "v0.14.0 sensitive release-matrix probe; metel-core#1412"
disposition: known
review: null
---

## Limitation

A signature `value: &{ ..R }` with `where all R: Clone` is rejected with `T0012` before body checking. The diagnostic claims the constraint names no parameter tail and refers to the already closed tracker #1302. The signature does contain that tail under the reference; the expected field-wise entitlement is not carried into this borrowed-row context.

Reproduced against core `784eb8f96f598122b4cacbd2f8e099b42f3f31e2`.
The expected-success fixture is skipped with a link to this record, rather than
asserting the compiler's incorrect rejection as intended behavior.

## Impact

The corresponding sensitive release-matrix boundary is blocked. Passing neighboring
concrete cases is not proof that this interaction works.

## Affects

- `spec.types.generics.field-wise-row-constraints.legality-1`
- `metel-interpreter/tests/integration/sources/evaluator/records/release_matrix_borrowed_all_clone`

## Resolution

Open: [metel-core#1412](https://github.com/metel-lang/metel-core/issues/1412).
The fixture must become executable when the fix lands; no fix or release deferral
is claimed by recording this limitation.
