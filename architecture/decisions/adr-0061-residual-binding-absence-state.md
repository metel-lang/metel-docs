---
id: adr-0061
title: "Residual Bindings Retain Initial Absence State"
date: '2026-10-08'
status: accepted
relates: RFC-0137
implements: metel-core#1406
---

## Context

Local partial moves seed the typechecker's flow state with missing fields. A
parameter or new binding whose initial type is already a residual did not carry
those absences into the flow state. Reinitializing its fields therefore could
not widen it, even though the brand supplies their declared types.

## Decision

For a non-generic nominal residual, both typechecker passes register the brand's
whole type as the binding's underlying declaration and seed missing depth-one
field projections in their existing flow state. Ordinary narrowed reads still
produce exactly the supplied residual. Field assignments clear those projections,
and only restoration of every missing field recovers the whole brand.

These seeded absences are type-level facts, not user move events. They are private
to the typechecker flows; the independent ownership checker continues to consume
typed expressions and report actual source moves. Existing shadowing, branch
joins and loop fixed points therefore govern restoration without a second
widening-state lattice. Capture inference uses the current narrowed type when
binding an owned capture, rather than its underlying nominal declaration.

Residual types do not currently retain a generic brand's type arguments. Such
bindings keep their surviving concrete field types unchanged: normalization must
not substitute raw declaration variables or invent erased arguments. This
decision does not extend generic residual restoration beyond the representation's
existing capabilities.

## Alternatives Considered

**Track restored labels separately.** Rejected because assignment, shadowing and
control-flow joins already share the missing-field lattice.

**Change only the final result type.** Rejected because it would hide unavailable
fields and could accept a partially restored value as whole.

## Consequences

Fixtures cover parameter rebinding, transparent callback aliases and written
closure types, along with missing-field reads, incomplete restoration and wrong
field types. A paired generic-brand regression keeps distinct instantiations'
field types independent. Ordinary ownership checking remains opt-in; brand and
narrowed-row legality remain unconditional typechecking rules.
