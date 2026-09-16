---
id: adr-0055
title: "Architecture Integrity Records and Verification"
date: '2026-09-15'
status: proposed
relates: adr-0054
implements: metel-core#1141, metel-core#1154, metel-core#1155, metel-core#1157
---

## Context

The Architecture Spec needs to remain a trustworthy description of the
current system. Today a maintainer cannot reliably answer which code and
fixtures prove an architectural claim, which claims are knowingly incomplete,
or whether a source, test, or cited decision has gone stale.

The prior Atlas proposal combined that problem with a large reader: C4-style
views, stage drill-ins, a data-model registry, Decisions, Debt, and Health.
Those are useful possible projections, but they are not prerequisites for
authoring and verifying the architecture. Requiring the reader first blocks
the design work and risks committing to a UI before real records establish
what maintainers need to navigate.

This ADR establishes the first, durable slice: the Architecture Spec,
atomic architecture requirements, debt records, fixture evidence, and the
tooling that verifies their integrity. A separate ADR defers the reader.

## Decision

### 1. The Architecture Spec is authoritative

The Architecture Spec is the current, versioned description of architecture.
Its stable sections and anchors describe boundaries, ownership, invariants,
and implementation mappings in prose. The records below link to that prose;
they do not replace or duplicate it.

### 2. `ARCH-*` records make architectural claims checkable

Each checkable architecture claim has a stable ID of the form
`ARCH-<AREA>-<NNN>`. An `ARCH-*` record contains at least:

| Field | Purpose |
|---|---|
| `status` | `implemented`, `partial`, `planned`, `superseded`, or `retired` |
| `owner` | accountable architectural area or maintainer |
| `specified by` | one defining Architecture Spec section anchor |
| `implements` | code path or other concrete implementation binding |
| `verified by` | fixture, test, or check that proves the claim |
| `related` | relevant ADRs or RFCs |

An Architecture Spec section links to its `ARCH-*` records, and each record
links back to exactly one defining section. Code and fixtures cite the
atomic record rather than broad Spec prose or an ADR. This makes the normal
path explicit:

```
Architecture Spec section ──defines──► ARCH-* ──verified by──► fixture/code
                                          │
                                          └──related to──► ADR/RFC
```

`ARCH-*` records and Formal Rules serve parallel roles in different domains.
They remain separate ID spaces: architecture records govern internal system
constraints; Formal Rules govern language semantics.

### 3. Fixtures provide architecture evidence

Fixture sidecars gain an `arch = [...]` array, parallel to the existing
`spec = [...]` array. A fixture may prove both a Formal Rule and an
architecture requirement. The checker validates that every cited ID exists
and that the fixture's inline citation, when present, agrees with its
sidecar.

Evidence is not inferred merely from a passing test. An `ARCH-*` record
names the fixture or check and explains the aspect of the claim it verifies.

### 4. `DEBT-*` records persist known system limitations

A requirement status and a failing Health finding cannot preserve a known
system limitation: what does not work, where its boundary lies, who owns the
knowledge, and whether it is being accepted, mitigated, or resolved.
`DEBT-<AREA>-<NNN>` records are the durable inventory of those limitations.

A debt record may describe a known unsupported case, an incomplete capability,
a performance or scalability boundary, an operational constraint, or a
deliberate architectural compromise. It does not need to be an exception to
an existing `ARCH-*` requirement. A related requirement is recorded when one
exists; the absence of one is useful information, not a reason to omit the
limitation.

Each debt record contains:

| Field | Purpose |
|---|---|
| `scope` | affected Architecture Spec section |
| `limitation` | precise description of the known boundary or shortfall |
| `impact` | affected behavior, users, maintainers, or system area |
| `affects` | zero or more related `ARCH-*` records and relevant code paths |
| `owner` | person or area responsible for maintaining the record and its disposition |
| `discovered by` | check, audit, incident, issue, or reader observation when known |
| `disposition` | `known`, `accepted`, `mitigated`, `planned`, `resolved`, or `superseded` |
| `review` | next review date or event when the limitation remains active |
| `resolution` | optional issue, successor requirement, exit condition, and verifying evidence |

An accepted temporary limitation requires rationale, an accepting ADR or
issue, and a review-by date. A limitation may remain `known` without a
resolution plan; recording it accurately is still valuable. When a record
does claim resolution, it names the exit condition and verifying evidence. A
closed issue is never sufficient resolution evidence by itself.

Code and fixtures cite `ARCH-*` records or Formal Rules, never debt records.
Debt records document limitations and their disposition; they are not a
contract that the implementation satisfies.

### 5. Integrity tooling verifies references and reconciliation

The initial checker validates:

- Architecture Spec anchors, `ARCH-*` and `DEBT-*` IDs, and all typed links;
- every `ARCH-*` record's owner, defining Spec section, implementation
  binding, and evidence reference;
- fixture-sidecar `arch` references and inline/sidecar agreement;
- every debt record's scope, limitation, impact, owner, disposition, and
  typed links;
- an acceptance rationale and review date when a limitation is temporarily
  accepted;
- exit evidence and reconciliation with linked work only when a record claims
  resolution.

It reports findings rather than silently changing a debt disposition. A human
triages a finding, records a limitation, or updates the relevant requirement
or debt record.

The first implementation does not establish a general `DATA-*` registry,
data-model extraction, signature-shape matching, or unmapped-code discovery.
An `ARCH-*` record may describe the data boundary necessary to state its
claim. A standalone data-model record is deferred until repeated, independent
invariants demonstrate that it needs its own lifecycle.

## Alternatives Considered

**Build the complete Atlas first.** Rejected. A reader is a projection over
records; it should not determine their schema or block authoring, fixtures,
and verification.

**Represent debt only through requirement status or issue labels.** Rejected.
Neither persistently records a known system limitation, its impact, ownership,
and disposition.

**Use Architecture Spec prose as the evidence unit.** Rejected. Prose is
needed for explanation, but its sections are too broad to serve as stable,
individually testable code and fixture citations.

**Introduce a generic data-model registry now.** Deferred. It would begin a
second authoring effort before actual architecture records demonstrate which
data concepts need independent identity and lifecycle.

## Consequences

- `#1155` authors stable Architecture Spec sections and the initial
  `ARCH-*` and `DEBT-*` records.
- `#1154` and `#1157` provide the marker, fixture-sidecar, and integrity
  checking support described here.
- The initial review surface is the Spec, individual record files, fixtures,
  and checker output. It is sufficient to trace a claim to evidence and keep
  known system limitations visible without a full Atlas UI.
- A future data-model registry or reader must consume these records as its
  source. It cannot become a second architecture authority.
