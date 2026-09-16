---
id: adr-0056
title: "Architecture Atlas Reader Is a Deferred Projection"
date: '2026-09-16'
status: proposed
relates: adr-0055
implements: metel-core#1156, metel-core#1159
---

## Context

An Architecture Atlas can make the Architecture Spec and its evidence easier
to browse. The prototype explored Context, Container, Component, Data model,
Architecture entries, Health, Decisions, and Debt views. That work exposed
useful questions about hierarchy and scope, but it also demonstrated that a
reader designed before sufficient records exist is speculative.

The immediate need is trustworthy architecture content and verification,
defined by ADR-0055. A production reader must follow the relationships that
real records establish rather than impose a fixed container hierarchy,
data-model taxonomy, or navigation model on them.

## Decision

The Atlas reader is deferred until ADR-0055 has produced a useful body of
Architecture Spec sections, `ARCH-*` records, `DEBT-*` records, fixture
evidence, and integrity-check output.

When scoped, the first reader increment will render the authoritative
Architecture Spec and provide navigation from an `ARCH-*` record to its
defining section, implementation binding, evidence, related decision, and
open debt. Health is a derived view over records and checker findings, not a
second record system.

The reader is a projection only. It cannot own architecture prose, infer
records from code as authority, or require a generic data-model registry.
Container, Component, data-model, ADR, and Debt views remain candidates to
evaluate against actual maintainer tasks after the integrity system is in
use. Their final hierarchy, filters, and drill-ins are deliberately not
decided here.

The existing static prototype remains a research artifact. It may inform a
future design, but does not set a committed information architecture or
implementation scope.

## Alternatives Considered

**Ship the prototype as the first implementation.** Rejected. Its views and
navigation were designed around a small, hand-authored sample and would make
the display model a prerequisite for the source records.

**Delete all reader work.** Rejected. The prototype is valuable evidence of
questions the later design must answer; it simply is not on the critical path.

## Consequences

- `#1159` is reduced to research and design validation rather than blocking
  the Architecture Spec and integrity work.
- `#1156` is deferred and must be re-scoped from actual records and
  maintainer workflows before implementation.
- No container, component, or data-model presentation is required for the
  first architecture-integrity release.
