---
id: LIMIT-TYPE-INFERENCE-010
title: "A transparent public alias omitted its nominal type dependency"
summary: "Alias expansion erased module context for nominal declarations referenced in the alias target."
scope: "architecture/spec/type-inference.md#type-inference"
owner: metel-frontend
discovered_by: "v0.14.0 sensitive release-matrix probe; metel-core#1414"
disposition: resolved
review: null
---

## Limitation

Importing `public type EmptyPacket := Packet<{}>` without separately importing
`Packet` previously reported `unknown type Packet` in the consuming module.
Alias expansion now materializes a synthetic import for nominal dependencies
from the defining module. The two-module regression
`module_semantics/release_matrix_row_callback/` passes without a skip after
metel-core PR #1422. Written constructor lookup also requires either a resolved
import identity or a name in the current module's scope: the synthetic alias
dependency does not expose the original bare constructor name.

## Impact

Previously, public aliases to specialized nominal types were not self-contained
across module boundaries.

## Affects

- `spec.declarations.type-aliases.legality-3`
- `spec.types.generics.open-rows.legality-1`

## Resolution

Alias dependency preservation was implemented in metel-core commit
`5f038b189cb67c5ec40e51d16a3e11a831a4535e` (PR #1422). Exit evidence for
metel-core#1414 includes `module_semantics/release_matrix_row_callback`,
`module_semantics/imported_nominal_alias_definition_scope` (renames, re-exports,
row and ordinary generic aliases, consumer name collisions), and
`module_semantics/alias_rhs_constructor_not_imported` (the original constructor
remains unavailable).
