---
id: LIMIT-TYPE-INFERENCE-010
title: "A public alias loses its defining module's nominal type import"
summary: "Importing a public alias to a row-specialized nominal type does not make its defining nominal type available to the alias."
scope: "architecture/spec/type-inference.md#type-inference"
owner: metel-frontend
discovered_by: "v0.14.0 sensitive release-matrix probe; metel-core#1414"
disposition: known
review: null
---

## Limitation

Importing `public type EmptyPacket := Packet<{}>` without separately importing
`Packet` reports `unknown type Packet` in the consuming module. A minimal
two-module regression is `module_semantics/release_matrix_row_callback/`;
see metel-core#1414.

## Impact

Public aliases to specialized nominal types are not self-contained across
module boundaries.

## Affects

- `spec.declarations.type-aliases.legality-3`
- `spec.types.generics.open-rows.legality-1`

## Resolution

Open; tracked by metel-core#1414.
