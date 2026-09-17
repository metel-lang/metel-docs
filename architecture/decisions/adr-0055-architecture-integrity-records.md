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
views, stage drill-ins, a data-model registry, Decisions, Limitations, and
Health. Those are useful possible projections, but they are not
prerequisites for authoring and verifying the architecture. Requiring the
reader first blocks the design work and risks committing to a UI before
real records establish what maintainers need to navigate.

This ADR establishes the first, durable slice: the Architecture Spec,
atomic architecture requirements, limitation records, fixture evidence,
and the tooling that verifies their integrity. A separate ADR defers the
reader.

## Decision

### 1. The Architecture Spec is authoritative

The Architecture Spec is the current, versioned description of architecture.
Its stable sections and anchors describe boundaries, ownership, invariants,
and implementation mappings in prose. The records below link to that prose;
they do not replace or duplicate it.

### 2. `arch-*` records make architectural claims checkable

Each checkable architecture claim has a stable ID of the form
`arch.<dotted-section-path>.requirement-<N>` — `arch` naming a domain, a
dotted path mirroring the defining Architecture Spec section's own heading
hierarchy, and a local sequential number under that path, e.g. (once
`#1155` writes the real section) `arch.resolution.requirement-1`. This
matches Formal Rules' own convention exactly in shape —
`spec.declarations.variables.immutable-bindings.legality-1` — rather than
the flat `ARCH-<AREA>-<NNN>` `#1154` originally specified: now that an
`arch-*` record is inline-anchored (below), a flat area-plus-number no
longer describes where the record actually lives the way a dotted path
does, and a mismatch between ID shape and storage shape is a real cost, not
a cosmetic one — the ID is what a citation or a checker's backlink actually
carries. The prefix goes lowercase too, matching `spec`: an earlier
revision of this section kept `ARCH` uppercase deliberately, reasoning that
only punctuation and structure were in scope — but the prefix's role is
addressing a location in the Architecture Spec the same way `spec.*`
addresses one in the Language Spec, and a differently-cased prefix signals
a difference in kind that doesn't exist. `PROC-*` (`#1142`) keeps its
original uppercase, flat scheme untouched: it isn't inline-anchored and
mirrors no section path, so nothing here pulls it toward the Formal Rules
convention — an Operations requirement isn't always anchored at one point
in one hierarchical document — `PROC-RELEASE-001` spans two repositories —
so it has no section path to mirror, and a dotted, lowercase form here
would only look aligned, not be aligned. An `arch-*` record contains at
least:

| Field | Purpose |
|---|---|
| `status` | `implemented`, `partial`, `planned`, `superseded`, or `retired` |
| `owner` | accountable architectural area or maintainer |
| `specified by` | one defining Architecture Spec section anchor |
| `implements` | code path or other concrete implementation binding |
| `verified by` | fixture, test, or check that proves the claim |
| `related` | relevant ADRs or RFCs |

`specified by` stays an explicit field even though the ID's own path
already names the section — the path is for addressing; `specified by` is
what the checker reads without re-parsing an ID string, the same reason a
Formal Rule's backlink data isn't inferred from its ID alone either.

An `arch-*` record is stored inline: a stable anchor at the point in its
defining Architecture Spec section where the claim is made, not a separate
file. This follows the Language Spec's own proven pattern for Formal Rules
— stable `{#id}` anchors inside shared prose, not one file per rule — rather
than the ADR/RFC convention of a standalone file per record. The reasons
carry over directly: a claim is meant to be read in the context of the
prose explaining it, not as an isolated file, and the Language Spec's
~350 Formal Rules already demonstrate the pattern holds at a scale `arch-*`
is unlikely to approach for a long time. `rfc.py`'s existing anchor/backlink/
coverage machinery (`metel-docs/rfcs/tools/rfc.py`) is the template to
generalize for this checker, not a system to discard and reinvent as
file-per-record.

An Architecture Spec section links to its `arch-*` records, and each record
links back to exactly one defining section. Code and fixtures cite the
atomic record rather than broad Spec prose or an ADR. This makes the normal
path explicit:

```
Architecture Spec section ──defines──► arch-* ──verified by──► fixture/code
                                          │
                                          └──related to──► ADR/RFC
```

`arch-*` records and Formal Rules now share a role, a storage shape, and an
ID shape — the atomic, inline-anchored, path-addressed, checkable claim —
across two domains. They remain separate ID spaces (architecture records
govern internal system constraints; Formal Rules govern language
semantics), and the tooling that reads them (§6) treats the two prefixes as
distinct namespaces over one shared anchor-and-backlink mechanism, not two
unrelated systems.

### 3. Fixtures provide architecture evidence

Fixture sidecars gain an `arch = [...]` array, parallel to the existing
`spec = [...]` array. A fixture may prove both a Formal Rule and an
architecture requirement. The checker validates that every cited ID exists
and that the fixture's inline citation, when present, agrees with its
sidecar.

Evidence is not inferred merely from a passing test. An `arch-*` record
names the fixture or check and explains the aspect of the claim it verifies.

### 4. `ALIMIT-*` records persist known system limitations

A requirement status and a failing Health finding cannot preserve a known
system limitation: what does not work, where its boundary lies, who owns the
knowledge, and whether it is being accepted, mitigated, or resolved.
`ALIMIT-<AREA>-<NNN>` records are the durable inventory of those
limitations — renamed from an earlier `DEBT-*`. The record described below
already covered a performance or scalability boundary, an operational
constraint, and a deliberate architectural compromise alongside an
unsupported case or incomplete capability, and only the latter two are
debt in the strict sense of a shortcut taken now with intent to pay it
down. A boundary accepted indefinitely, with no repayment plan, was never
debt to begin with; `limitation` names what the whole set actually shares
without implying a repayment story that doesn't hold for most of it. The
prefix itself carries an explicit domain letter, `A` for architecture,
rather than staying bare — see §5, which reserves the language-domain
counterpart `LLIMIT-*` and needs the two to read as siblings rather than
one plain form plus one prefixed exception.

Unlike `arch-*` (§2), a limitation record is its own file, one per record —
matching the ADR/RFC convention rather than the inline, Formal-Rule one.
The reason is the record's own shape, not its domain: a limitation record
carries a standalone lifecycle (discovery, disposition, ownership, review,
resolution) closer to a decision than to a terse rule clause, and that
shape is what earns it a file — not that it happens to describe
architecture. §6 depends on keeping that distinction shape-based rather
than domain-based.

A limitation record may describe a known unsupported case, an incomplete
capability, a performance or scalability boundary, an operational
constraint, or a deliberate architectural compromise. It does not need to
be an exception to an existing `arch-*` requirement. A related requirement
is recorded when one exists; the absence of one is useful information, not
a reason to omit the limitation.

Each limitation record contains:

| Field | Purpose |
|---|---|
| `scope` | affected Architecture Spec section |
| `limitation` | precise description of the known boundary or shortfall |
| `impact` | affected behavior, users, maintainers, or system area |
| `affects` | zero or more related `arch-*` records and relevant code paths |
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

Code and fixtures cite `arch-*` records or Formal Rules, never limitation
records. Limitation records document limitations and their disposition;
they are not a contract that the implementation satisfies.

### 5. Reserved for later: a language-level limitation sibling

`ALIMIT-*` as specified here is scoped to architecture — a known limitation
in how the compiler implements something. A parallel concept for the
language itself (a known, accepted gap in what the Language Spec currently
specifies or guarantees, not in one implementation's fidelity to it) is a
real future need, not an architecture concern, and chartering it is out of
scope here.

If and when it is chartered, it takes a separate sibling prefix,
`LLIMIT-<AREA>-<NNN>`: a single domain letter — `A` for architecture, `L`
for language — prepended to the shared base word `LIMIT`, the same way
`ALIMIT-*` itself is formed. The apparent doubled `L` in `LLIMIT` is
coincidental, not a special rule: `LIMIT` happens to start with `L`, so
the language-domain letter and the base word's own first letter collide;
it is still just one prefix letter, formed the same mechanical way as
`ALIMIT-*`. It is reserved now to avoid a collision: leaving the
architecture form bare and unprefixed while giving language a letter would
also have worked to disambiguate the two, but it would read as
architecture being the default and language the exception, when neither
domain is more entitled to the plain form than the other. Explicit letters
on both sides say what's actually true instead. Reusing a single `LIMIT-*`
for both domains would otherwise make an entry like `LIMIT-RESOLUTION-001`
ambiguous between a compiler limitation and a language-semantics one for
the same subsystem name, the same way `arch-*` and `PROC-*` stay sibling
prefixes rather than one shared one. The record-shape argument in §4 —
separate file, standalone lifecycle — carries over as a starting point,
not a decision to re-litigate; it was never about architecture
specifically. Nothing here charters the work or its schema in full; this
only reserves the name so a future ADR solves its own actual scope instead
of also solving a naming collision this one could prevent for free.

### 6. Integrity tooling verifies references and reconciliation

The initial checker validates:

- Architecture Spec anchors, `arch-*` and `ALIMIT-*` IDs, and all typed links;
- every `arch-*` record's owner, defining Spec section, implementation
  binding, and evidence reference;
- fixture-sidecar `arch` references and inline/sidecar agreement;
- every limitation record's scope, limitation, impact, owner, disposition,
  and typed links;
- an acceptance rationale and review date when a limitation is temporarily
  accepted;
- exit evidence and reconciliation with linked work only when a record claims
  resolution.

It reports findings rather than silently changing a limitation's
disposition. A human triages a finding, records a limitation, or updates
the relevant requirement or limitation record.

The first implementation does not establish a general `DATA-*` registry,
data-model extraction, signature-shape matching, or unmapped-code discovery.
An `arch-*` record may describe the data boundary necessary to state its
claim. A standalone data-model record is deferred until repeated, independent
invariants demonstrate that it needs its own lifecycle.

## Alternatives Considered

**Build the complete Atlas first.** Rejected. A reader is a projection over
records; it should not determine their schema or block authoring, fixtures,
and verification.

**Represent a limitation only through requirement status or issue labels.**
Rejected. Neither persistently records a known system limitation, its
impact, ownership, and disposition.

**Use Architecture Spec prose as the evidence unit.** Rejected. Prose is
needed for explanation, but its sections are too broad to serve as stable,
individually testable code and fixture citations.

**Introduce a generic data-model registry now.** Deferred. It would begin a
second authoring effort before actual architecture records demonstrate which
data concepts need independent identity and lifecycle.

**Store `arch-*` records as separate files, matching ADR/RFC.** Considered
in an earlier draft of this ADR, then reversed — see §2. `rfc.py` already
proves the inline-anchor pattern at ~350 Formal Rules, a scale `arch-*` is
unlikely to reach for a long time, and a separate-file convention would
fragment the Architecture Spec's own prose with no reassembly mechanism to
undo that, the same cost that pattern would impose on the Language Spec if
applied there.

**Give a future language-limitation concept the same `ALIMIT-*` prefix
unmodified, distinguished only by `AREA`.** Rejected — see §5.
`ALIMIT-RESOLUTION-001` would be ambiguous between a compiler limitation
and a language-semantics one for the same subsystem name; a distinguishing
prefix (`LLIMIT-*`) avoids that for free and matches how `arch-*`/`PROC-*`
already stay sibling prefixes rather than one shared one.

**Leave the architecture-domain prefix bare (`LIMIT-*`) and give only the
language domain a letter (`LLIMIT-*`).** Rejected — see §4 and §5. This is
what an earlier revision of this ADR did. Disambiguation only requires the
two forms to differ, and a bare-plus-prefixed pair achieves that, but it
also reads as architecture being the default domain and language the
exception, which isn't true — neither domain owns the concept more than
the other. `ALIMIT-*`/`LLIMIT-*` says so directly: the same single-letter
scheme applied to both sides, not one side spelled out and one left
implicit.

**Keep the `DEBT-*` name now that the record covers more than technical
debt.** Rejected — see §4. The record already included a performance
boundary, an operational constraint, and a deliberate architectural
compromise alongside cases that are debt in the strict sense; `debt`
implies a shortcut taken now with intent to repay, which doesn't describe
a boundary accepted indefinitely with no repayment plan. `limitation` is
the term this ADR's own prose already used throughout to describe the
concept; the ID prefix and the reserved sibling (`LDEBT-*` → `LLIMIT-*`)
now match it.

**Keep `ARCH-<AREA>-<NNN>` (`#1154`'s original flat schema) now that
storage is inline.** Rejected — see §2. The flat form was shaped around
file-per-record, where a short unique label was enough; once a record is
addressed by an anchor inside a hierarchical document instead, an ID that
doesn't mirror that hierarchy is a real mismatch between how a record is
named and how it's actually found, not a cosmetic difference from Formal
Rules' dotted-path convention.

**Keep `ARCH` uppercase after adopting the dotted path.** An earlier
revision of this ADR made exactly this call, reasoning that only the
punctuation and hierarchy were in scope. Reversed — see §2. The dotted
form's whole point is that the ID mirrors how the record is addressed, the
same way `spec.*` does; keeping the prefix's case different from `spec`
after matching everything else about its shape would be an arbitrary
holdout, not a meaningful distinction.

## Consequences

- `#1155` authors stable Architecture Spec sections and the initial
  `arch-*` and `ALIMIT-*` records.
- `#1154` and `#1157` provide the marker, fixture-sidecar, and integrity
  checking support described here, generalizing `rfc.py`'s existing
  anchor/backlink/coverage pattern rather than building a parallel
  file-per-record system for `arch-*`.
- The initial review surface is the Spec (with its inline `arch-*`
  anchors), individual limitation-record files, fixtures, and checker
  output. It is sufficient to trace a claim to evidence and keep known
  system limitations visible without a full Atlas UI.
- A future data-model registry or reader must consume these records as its
  source. It cannot become a second architecture authority.
- `LLIMIT-*` is reserved (§5) but not chartered — a future
  language-limitation ADR inherits the name and the record-shape
  rationale, and doesn't need to solve either from scratch.
- `DEBT-*`/`LDEBT-*` (this ADR's own earlier names) are retired in favor of
  `ALIMIT-*`/`LLIMIT-*`; ADR-0056 and the prior-art survey cited the old
  names and are updated alongside this ADR in the same change.
- `#1154`'s own generic schema note (`<PREFIX>-<AREA>-<NNN>`, e.g.
  `ARCH-RESOLUTION-001`) is amended for the `arch-*` case by §2 — `PROC-*`
  keeps the original flat form for the reason stated there. `#1154` should
  cite this ADR for the `arch-*` ID shape rather than restate its own,
  now-superseded example.
