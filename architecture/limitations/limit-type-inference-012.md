---
id: LIMIT-TYPE-INFERENCE-012
title: "Field-wise Clone is unavailable for records imported from another module"
summary: "A public nominal record imported from another module has no visible field-wise Clone method, even when every field is Clone."
scope: "architecture/spec/type-inference.md#type-inference"
owner: metel-frontend
discovered_by: "v0.14.0 release-matrix probe; metel-core#1421"
disposition: known
review: null
---

## Limitation

A public `Packet` record declared in one module with `Clone` fields was not
recognized as Clone in a consumer module because the registry merge omitted its
record-kind identity. The merge now carries that identity, and
`module_semantics/release_matrix_record_clone_cross_module` passes locally
without a skip; metel-core#1421 remains open pending integration.

## Impact

Field-wise record Clone cannot be relied on across module boundaries, despite
the public record and its Clone aspect being available to the consumer.

## Affects

- `spec.declarations.records.legality-1`
- `spec.modules.imports.legality-2`

## Resolution

Implementation is present locally and covered by the unskipped regression;
tracked by metel-core#1421 pending merge.
