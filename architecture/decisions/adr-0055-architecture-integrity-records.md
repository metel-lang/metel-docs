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

An `ARCH-*` record is stored inline: a stable anchor at the point in its
defining Architecture Spec section where the claim is made, not a separate
file. This follows the Language Spec's own proven pattern for Formal Rules
— stable `{#id}` anchors inside shared prose, not one file per rule — rather
than the ADR/RFC convention of a standalone file per record. The reasons
carry over directly: a claim is meant to be read in the context of the
prose explaining it, not as an isolated file, and the Language Spec's
~350 Formal Rules already demonstrate the pattern holds at a scale `ARCH-*`
is unlikely to approach for a long time. `rfc.py`'s existing anchor/backlink/
coverage machinery (`metel-docs/rfcs/tools/rfc.py`) is the template to
generalize for this checker, not a system to discard and reinvent as
file-per-record.

An Architecture Spec section links to its `ARCH-*` records, and each record
links back to exactly one defining section. Code and fixtures cite the
atomic record rather than broad Spec prose or an ADR. This makes the normal
path explicit:

```
Architecture Spec section ──defines──► ARCH-* ──verified by──► fixture/code
                                          │
                                          └──related to──► ADR/RFC
```

`ARCH-*` records and Formal Rules now share both a role and a storage shape
— the atomic, inline-anchored, checkable claim — across two domains. They
remain separate ID spaces (architecture records govern internal system
constraints; Formal Rules govern language semantics), and the tooling that
reads them (§6) treats the two prefixes as distinct namespaces over one
shared anchor-and-backlink mechanism, not two unrelated systems.

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

Unlike `ARCH-*` (§2), a debt record is its own file, one per record —
matching the ADR/RFC convention rather than the inline, Formal-Rule one.
The reason is the record's own shape, not its domain: a debt record carries
a standalone lifecycle (discovery, disposition, ownership, review,
resolution) closer to a decision than to a terse rule clause, and that
shape is what earns it a file — not that it happens to describe
architecture. §6 depends on keeping that distinction shape-based rather
than domain-based.

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

### 5. Reserved for later: a language-level debt sibling

`DEBT-*` as specified here is scoped to architecture — a known limitation
in how the compiler implements something. A parallel concept for the
language itself (a known, accepted gap in what the Language Spec currently
specifies or guarantees, not in one implementation's fidelity to it) is a
real future need, not an architecture concern, and chartering it is out of
scope here.

If and when it is chartered, it takes a separate sibling prefix,
`LDEBT-<AREA>-<NNN>`, reserved now to avoid a collision: reusing `DEBT-*`
for both domains would make an entry like `DEBT-RESOLUTION-001` ambiguous
between a compiler limitation and a language-semantics one for the same
subsystem name, the same way `ARCH-*` and `PROC-*` stay sibling prefixes
rather than one shared one. The record-shape argument in §4 — separate
file, standalone lifecycle — carries over as a starting point, not a
decision to re-litigate; it was never about architecture specifically.
Nothing here charters the work or its schema in full; this only reserves
the name so a future ADR solves its own actual scope instead of also
solving a naming collision this one could prevent for free.

### 6. Integrity tooling verifies references and reconciliation

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

**Store `ARCH-*` records as separate files, matching ADR/RFC.** Considered
in an earlier draft of this ADR, then reversed — see §2. `rfc.py` already
proves the inline-anchor pattern at ~350 Formal Rules, a scale `ARCH-*` is
unlikely to reach for a long time, and a separate-file convention would
fragment the Architecture Spec's own prose with no reassembly mechanism to
undo that, the same cost that pattern would impose on the Language Spec if
applied there.

**Give a future language-debt concept the bare `DEBT-*` prefix, distinguished
only by `AREA`.** Rejected — see §5. `DEBT-RESOLUTION-001` would be
ambiguous between a compiler limitation and a language-semantics one for
the same subsystem name; a distinguishing prefix (`LDEBT-*`) avoids that
for free and matches how `ARCH-*`/`PROC-*` already stay sibling prefixes
rather than one shared one.

## Consequences

- `#1155` authors stable Architecture Spec sections and the initial
  `ARCH-*` and `DEBT-*` records.
- `#1154` and `#1157` provide the marker, fixture-sidecar, and integrity
  checking support described here, generalizing `rfc.py`'s existing
  anchor/backlink/coverage pattern rather than building a parallel
  file-per-record system for `ARCH-*`.
- The initial review surface is the Spec (with its inline `ARCH-*`
  anchors), individual debt-record files, fixtures, and checker output. It
  is sufficient to trace a claim to evidence and keep known system
  limitations visible without a full Atlas UI.
- A future data-model registry or reader must consume these records as its
  source. It cannot become a second architecture authority.
- `LDEBT-*` is reserved (§5) but not chartered — a future language-debt ADR
  inherits the name and the record-shape rationale, and doesn't need to
  solve either from scratch.
