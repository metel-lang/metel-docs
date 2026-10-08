---
id: LIMIT-TYPE-INFERENCE-010
title: "Imported nominal row alias loses definition-site type lookup"
summary: "Using a public imported alias for Packet<{}> can report unknown type Packet in the consumer."
scope: "architecture/spec/type-inference.md#type-inference"
owner: metel-frontend
discovered_by: "v0.14.0 sensitive release-matrix probe; metel-core#1414"
disposition: known
review: null
---

## Limitation

Importing a public alias whose RHS is a nominal row instantiation can leave the RHS nominal name resolved in the consuming module. A minimal two-file control reports `T0003: unknown type Packet` at the alias use unless the underlying nominal name is also brought into scope. The alias should preserve definition-site nominal identity; importing it should not require or expose that original bare constructor name.

Reproduced against core `784eb8f96f598122b4cacbd2f8e099b42f3f31e2`.
The expected-success fixture is skipped with a link to this record, rather than
asserting the compiler's incorrect rejection as intended behavior.

## Impact

The corresponding sensitive release-matrix boundary is blocked. Passing neighboring
concrete cases is not proof that this interaction works.

## Affects

- `spec.declarations.type-aliases.legality-3`
- `metel-interpreter/tests/integration/sources/module_semantics/release_matrix_row_callback`

## Resolution

Open: [metel-core#1414](https://github.com/metel-lang/metel-core/issues/1414).
The fixture must become executable when the fix lands; no fix or release deferral
is claimed by recording this limitation.
