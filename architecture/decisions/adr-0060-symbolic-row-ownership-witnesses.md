---
id: adr-0060
title: "Symbolic Row Witnesses for Ownership Checking"
date: '2026-10-08'
status: accepted
relates: RFC-0121, RFC-0123, RFC-0173, RFC-0178
implements: metel-core#1405
---

## Context

The optional move checker reconstructs generic bodies using resolved placeholder
types. Nominal placeholders preserve ordinary generic aspect assumptions, but
cannot represent an open-row remainder. Reconstruction of a valid row-forwarding
closure consequently failed with `T0002` and skipped ownership checking.

Sampling an empty record would eliminate that failure but falsely make an unknown
row `Copy`. The definition must be checked against its declared facts, not against
one convenient concrete instantiation.

## Decision

Resolved types include ownership-only `SymbolicRow` witnesses and `OpenRecord`
heads with such tails. A witness has opaque identity and retains proven field-wise
aspect bounds, absent labels, and typed negative field requirements. It contains
no inference variables. Runtime specializations continue to use concrete records;
the witness is not a new user-facing type or runtime value kind.

Row equations share a tail witness and retain known surviving fields in both
directions. A closed row bound, unlike an unconstrained tail, proves the tail empty.
Declared remainder equations are replayed during generic specialization before
unresolved scalar variables receive the existing bottom-type fallback.

Construction consumes these resolved facts without changing its context's solved
substitution. Structural conversions, spreads and rest patterns preserve the tail
rather than erasing it. Bound checks require evidence: an unknown label is not
absent, an unknown tail is not an exact closed row, and field-wise assumptions do
not grant an arbitrary whole-record aspect. Structural `Copy` requires `Copy` for
each known field and the tail; an empty concrete record remains vacuously `Copy`.

Closure capture completeness remains a separate definition-time check. The same
free-use traversal is shared by inference and construction, with global bindings
excluded and shadowing locals included. A missing explicit capture reports
`T0026`, rather than becoming an internal reconstruction disagreement.

## Alternatives Considered

**Empty-record samples.** Rejected because they erase unknown ownership and
absence obligations.

**Nominal row samples.** Rejected because a nominal placeholder cannot participate
in open-record construction and remainder forwarding without losing row identity.

**Ignore reconstruction errors.** Rejected as a solution: a warning is an honest
fallback, but not evidence that a generic definition was ownership-checked.

## Consequences

Regressions must assert the absence of move-check skip warnings, not merely that a
program runs. A paired negative regression reuses an unconstrained row after
forwarding it and requires a move violation. Empty and nonempty runtime arguments
exercise the forwarding closure. Closed-row and known-head tests distinguish
declared closure from unknown tails.

Move checking remains opt-in. Rest-destructuring double consumption tracked by
metel-core#1407 is independent and is not changed by this decision.
