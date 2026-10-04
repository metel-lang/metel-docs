---
id: adr-0058
title: "Generic Bodies Retain Their Definition-Time Entitlements"
date: '2026-10-04'
status: accepted
relates: RFC-0173, LIMIT-TYPES-004
implements: metel-core#1364
updated: '2026-10-04'
---

## Context

Generic bodies were reconstructed at concrete calls, while the initial check did not retain
every fact expressed by the declaration. This allowed a body to rely on a concrete caller to
settle a declared parameter, a row remainder, or a callee bound. It also meant the final
rigidity check could identify a collapse only after solving and reported the declaration rather
than the expression that caused it.

## Decision

The definition-time checker is authoritative. Declared parameters are tracked through solving,
and each parameter records the constraint span that last changed its resolved type. A rigidity
failure uses that span.

Row decompositions are represented as symbolic `Rest = R minus labels` facts. A generic call
adds the fact while both rows are abstract; generalizing an enclosing free function or method
retains unresolved facts in its scheme. Instantiation replays the fact, deriving a concrete
remainder once its source row is concrete. The excluded labels, row bound, and symbolic fact are
therefore one declaration-time contract rather than a call-time-only derivation.

Declared bounds travel with local schemes. Direct aspect-bound forwarding and field-wise
`where all R: A` forwarding are checked against the caller's declared entitlements. Conditional
impl selection uses the same entailment judgment. A bare parameter is not callable; the existing
definition-time `T0001` remains the diagnostic until callable aspects are specified.

Construction may reconstruct a generic body for runtime representation, but a `TypeError` from
that reconstruction is converted to `I0010`. The integration differential sweep is the generic
fixture cluster: every success fixture that constructs a generic body is run through the full
pipeline, while all typecheck-only generic fixtures exercise the authoritative definition check.
Any disagreement is therefore an internal invariant failure, not a programmer-facing error at a
call site.

## Alternatives Considered

**Treat row remainders as call-time metadata only.** Rejected: an enclosing generic could lose
the relationship learned from an inner generic call.

**Report the declaration span.** Rejected: the solver has each causal constraint span, and
reporting the declaration obscures the use that over-constrained the parameter.

**Remove reconstruction.** Rejected: runtime bodies still require concrete typed ASTs. The
definition check remains the contract, with `I0010` guarding reconstruction.

## Consequences

- RFC-0173 definition errors are stable across callers and point at the causal expression.
- Generic schemes retain symbolic row facts and field-wise entitlements.
- The differential fixture sweep is a required regression gate for changes to generic
  construction or inference.
