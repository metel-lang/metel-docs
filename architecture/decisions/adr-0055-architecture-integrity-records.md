---
id: adr-0055
title: "Architecture Integrity Records and Verification"
date: '2026-09-15'
status: accepted
relates: adr-0054
implements: metel-core#1141, metel-core#1154, metel-core#1155, metel-core#1157
updated: '2026-09-17'
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
a difference in kind that doesn't exist. `PROC-*` (`#1142`) is unaffected:
its own ID scheme is Operations' decision, not this one's, and this ADR
takes no position on it. An `arch-*` record contains at least:

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

### 4. `LIMIT-*` records persist known system limitations

A requirement status and a failing Health finding cannot preserve a known
system limitation: what does not work, where its boundary lies, who owns the
knowledge, and whether it is being accepted, mitigated, or resolved.
`LIMIT-<AREA>-<NNN>` records are the durable inventory of those
limitations — renamed from an earlier `DEBT-*`. The record described below
already covered a performance or scalability boundary, an operational
constraint, and a deliberate architectural compromise alongside an
unsupported case or incomplete capability, and only the latter two are
debt in the strict sense of a shortcut taken now with intent to pay it
down. A boundary accepted indefinitely, with no repayment plan, was never
debt to begin with; `limitation` names what the whole set actually shares
without implying a repayment story that doesn't hold for most of it. The
language-domain counterpart reserved in §5 uses a different word entirely
rather than a letter-prefixed variant of this one — see there for why.

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

### 5. Language-level gap sibling (chartered by ADR-0057)

> Chartered by [ADR-0057](adr-0057-language-gap-records.md). The text below records
> why the prefix is `GAP-*`; the charter (definition, sorting test, shape,
> location) is in ADR-0057.

`LIMIT-*` as specified here is scoped to architecture — a known limitation
in how the compiler implements something. A parallel concept for the
language itself (a known, accepted gap in what the Language Spec currently
specifies or guarantees, not in one implementation's fidelity to it) is a
real future need, not an architecture concern, and chartering it is out of
scope here.

If and when it is chartered, it takes a separate prefix, `GAP-<AREA>-<NNN>`
— a distinct word, not a letter-prefixed variant of `LIMIT-*`. An earlier
revision of this ADR used `ALIMIT-*`/`LLIMIT-*`, a shared base word with a
domain letter (`A`/`L`) attached to keep the two forms unambiguous; that
was reversed. `GAP` fits the language-domain concept precisely — the
paragraph above already describes it as "a known, accepted gap" without
needing an invented word for it — while `LIMIT` fits architecture's
broader set (a boundary, a constraint, a deliberate compromise, not only
something missing). Forcing one shared word to cover both was a
readability cost (`ALIMIT`/`LLIMIT` read less naturally than either plain
word) for no real gain: once each domain has the word that actually fits
it, the two prefixes already don't collide, so no domain-letter mechanism
is needed to keep `GAP-RESOLUTION-001` from being read as an architecture
record the way a bare, reused `LIMIT-RESOLUTION-001` might have been for
both. The record-shape argument in §4 — separate file, standalone
lifecycle — carries over as a starting point, not a decision to
re-litigate; it was never about architecture specifically. Nothing here
charters the work or its schema in full; this only reserves the name so a
future ADR solves its own actual scope instead of also solving a naming
collision this one could prevent for free.

### 6. Integrity tooling verifies references and reconciliation

The initial checker validates:

- Architecture Spec anchors, `arch-*` and `LIMIT-*` IDs, and all typed links;
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

The checks above split into two different kinds of work: baseline
referential integrity (do cited IDs and typed links resolve, are required
fields populated, does a fixture sidecar's `arch` array agree with its
inline citation) and conditional policy over relationships (a temporarily
accepted limitation needs a rationale and review date; a resolved one
needs exit evidence that reconciles with the linked work). The prior-art
survey's own recommended composition (`architecture-atlas-prior-art-survey.html`
§7) argues for relational-schema-plus-foreign-key validation for the first
kind and a declarative rule engine such as Soufflé Datalog for the second,
naming reconciliation logic like this section's last two checks directly
as a poor fit for "Python control flow." That composition is not adopted
here. `rfc.py`'s anchor/backlink/coverage machinery (§2) already covers
the referential-integrity shape of the first four checks at a proven
~350-rule scale, and the two conditional checks are, right now, a pair of
field-presence rules — not yet numerous or interdependent enough to need a
rule engine's own runtime and schema. Introducing Datalog and a separate
relational-validation layer ahead of that need would be the same
premature-machinery mistake this section already avoids for `DATA-*`:
real reconciliation-rule volume and complexity, not this ADR's own
preference, should decide when a declarative rule engine earns its keep.

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

**Adopt the prior-art survey's recommended relational-schema-plus-Datalog
composition for the checker now.** Deferred — see §6. The survey itself
frames this as the target composition once the Atlas has real content;
right now `arch-*`/`LIMIT-*` records don't exist yet (`#1155` hasn't
written the first Architecture Spec section), so there is no reconciliation-
rule volume to justify a declarative rule engine over generalizing
`rfc.py`, which already does the referential-integrity half of the job at
a proven scale. Revisit once the two conditional checks in §6 have grown
into something a human can no longer track as a short, fixed list.

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

**Keep `arch-*`'s original flat, uppercase form (`ARCH-<AREA>-<NNN>`, e.g.
`ARCH-RESOLUTION-001`, `#1154`'s original schema).** Rejected — see §2.
That form was shaped for file-per-record storage, where a short unique
label was enough and case carried no meaning. Once a record is
inline-anchored inside a hierarchical document instead, an ID that doesn't
mirror that hierarchy is a real mismatch between how a record is named and
how it's actually found, not a cosmetic difference from Formal Rules'
dotted-path convention — and the same logic extends to case: `spec.*`'s
lowercase signals that inline-anchored role directly, so `arch.*` matches
it rather than keeping the flat form's uppercase for no remaining reason.

**Any `LIMIT-*`/`GAP-*` alternative other than the final naming in §4 and
§5.** Considered and rejected along the way: keeping the original
`DEBT-*` name (the record covers more than technical debt — a boundary
accepted indefinitely with no repayment plan was never debt to begin
with); reusing one prefix unmodified for both domains, e.g.
`LIMIT-RESOLUTION-001` for both a compiler limitation and a
language-semantics one (ambiguous for the same subsystem name); and a
shared base word with a domain letter on each side, `ALIMIT-*`/`LLIMIT-*`
(disambiguating, but forcing one word to describe two not-quite-identical
concepts, and reading less naturally than either domain's own accurate
word). `LIMIT-*`/`GAP-*` — two distinct words, each fitted to its own
domain's actual content — resolves all three at once: no ambiguity, no
shared-word compromise, no domain-letter mechanism to explain.

## Consequences

- `#1155` authors stable Architecture Spec sections and the initial
  `arch-*` and `LIMIT-*` records.
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
- `GAP-*` is reserved (§5) but not chartered — a future language-gap ADR
  inherits the record-shape rationale (separate file, standalone
  lifecycle), not the name, which was chosen to fit its own domain rather
  than to match `LIMIT-*`.
- `DEBT-*`/`LDEBT-*` (this ADR's own earlier names) are retired in favor of
  `LIMIT-*` (architecture) and `GAP-*` (the reserved language sibling).
  ADR-0056 and the prior-art survey cited the intermediate
  `ALIMIT-*`/`LLIMIT-*` names and are updated alongside this ADR in the
  same change.
- `#1154`'s own generic schema note (`<PREFIX>-<AREA>-<NNN>`, e.g.
  `ARCH-RESOLUTION-001`) is amended for the `arch-*` case only, by §2.
  `#1154` should cite this ADR for the `arch-*` ID shape rather than
  restate its own, now-superseded example. `PROC-*`'s own schema is
  unaffected and out of scope here.
- The prior-art survey's relational-schema-plus-Datalog checker composition
  (§7 of `architecture-atlas-prior-art-survey.html`) is knowingly not
  adopted yet — see §6 and Alternatives Considered. `#1154`/`#1157`
  implement the `rfc.py`-generalization checker described here; whoever
  revisits it once reconciliation rules grow past a short fixed list
  should start from the survey's Soufflé/Frictionless recommendation
  rather than re-deriving it.
