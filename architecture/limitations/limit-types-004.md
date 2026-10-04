---
id: LIMIT-TYPES-004
title: "RFC-0173 generic-body checking was incomplete"
summary: "Resolved: generic bodies retain declared bounds and row facts, and report rigidity failures at the causal expression."
scope: "architecture/spec/type-inference.md#type-inference"
owner: metel-frontend
discovered_by: "RFC-0173 entering 3-integrated with no implementation yet; metel-core#1320, #1323"
disposition: resolved
review: null
---

## Limitation

RFC-0173 makes the definition-time check the contract for a generic body: each declared
parameter is rigid, and a use is allowed only if the declared bounds entail it. The completed
implementation (metel-core#1364) keeps row decompositions as symbolic facts through generic
calls and generalized schemes; checks direct and `where all` bound forwarding; makes
conditional-impl visibility depend on declared entailment; and records solver provenance so a
rigidity mismatch (`T0001`) points at the causal expression. A construction disagreement is
`I0010`, never a call-site type error. Operators on bare parameters remain the separate
language-level gap `GAP-TYPES-005`.

## Impact

At the time, a generic function could over-constrain its parameters or use an entitlement
that only a concrete caller supplied. Row-polymorphic code was affected most because a
remainder could collapse into its source row. The completed implementation enforces the
RFC-0173 contract at the definition.

## Affects

- `spec.types.generics.rigid-type-parameters.legality-1`
- `spec.types.generics.rigid-type-parameters.legality-2`
- `spec.types.generics.rigid-type-parameters.dynamics-1`

## Resolution

Resolved by metel-core#1364 and ADR-0058. `LIMIT-EVALUATION-001` (the per-call
reconstruction) remains a separate implementation boundary; its failure mode is guarded by
`I0010` and the differential fixture sweep specified in ADR-0058.
