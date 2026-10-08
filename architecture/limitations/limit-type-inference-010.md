---
id: LIMIT-TYPE-INFERENCE-010
title: "A transparent public alias omitted its nominal type dependency"
summary: "Alias expansion erased module context for nominal declarations referenced in the alias target."
scope: "architecture/spec/type-inference.md#type-inference"
owner: metel-frontend
discovered_by: "v0.14.0 sensitive release-matrix probe; metel-core#1414"
disposition: known
review: null
---

## Limitation

Importing `public type EmptyPacket := Packet<{}>` without separately importing
`Packet` previously reported `unknown type Packet` in the consuming module.
Alias expansion now materializes a synthetic import for nominal dependencies
from the defining module. The two-module regression
`module_semantics/release_matrix_row_callback/` now passes locally without a
skip; see metel-core#1414, which remains open pending integration.

## Impact

Public aliases to specialized nominal types are not self-contained across
module boundaries.

## Affects

- `spec.declarations.type-aliases.legality-3`
- `spec.types.generics.open-rows.legality-1`

## Resolution

Implementation is present locally and covered by the unskipped regression;
tracked by metel-core#1414 pending integration.
