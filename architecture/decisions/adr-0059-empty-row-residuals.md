---
id: adr-0059
title: "Empty Rows Remain Residual Values"
date: '2026-10-07'
status: accepted
relates: RFC-0117, RFC-0137
implements: metel-core#1398
---

## Context

Both typechecker passes discarded narrowing when no fields remained. A binding
therefore recovered its declared type after its last field move, and only the
optional move checker rejected a subsequent removed-field read. This differed
from the ordinary type error after a partial field move.

## Decision

Inference and construction retain an empty `Record` or branded `Residual` when
field moves empty a non-empty row. No new type variant or evaluator entry point
is required. Full-width normalization still applies to genuinely zero-field
nominal declarations. Empty nominal residuals are named by `Name.{}` in type
position; no new expression-projection form is introduced.

Anonymous-record field writes resolve a removed label against the binding's
original declared row before the existing flow-state reinitialization widens it.
Reads continue to use the narrowed row. Nominal writes use the existing declared
brand-field lookup.

The move checker's narrowed-whole-value exemption is conditional on the root not
having been moved as a whole. Field disjointness alone is insufficient: an empty
row satisfies that test vacuously, even after a subsequent whole-binding move.
Existing `Copy` rules still decide whether consuming a residual actually moves it.

Symbolic move-analysis placeholders remain abstract for construction narrowing,
matching inference's treatment of unresolved field types. The registry explicitly
marks generic, unknown row-field, and associated-type witnesses, including those
with no positive aspect bounds. Fields containing these witnesses are held in
the row until concrete; the move checker still analyzes their ownership and can
report `T0019`. This avoids a reconstruction failure hiding a generic-body move
violation, without disabling narrowing of known concrete fields or treating
arbitrary reconstruction failures as source errors.

## Alternatives Considered

**Leave the final field move to the optional move checker.** Rejected: narrowing
would cease to be monotone and removed-field diagnostics would depend on row width.

**Treat an empty residual as a wholly moved binding.** Rejected: residuals are
ordinary values, and field consumption is distinct from consuming their binding.

## Consequences

The inference/construction boundary is unchanged. Fixtures run in both ownership
modes to verify diagnostics, empty-value transfer, brand preservation, copied
fields, widening, and zero-field full-width normalization. A move-check-enabled
negative fixture protects subsequent whole-binding moves from the exemption.
