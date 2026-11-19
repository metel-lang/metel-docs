---
id: adr-0070
title: "Limits Are Spec Prose, Markers and Issues, Not a Record Kind"
date: '2026-11-19'
status: proposed
relates: adr-0055, adr-0057
---

## Context

The architecture corpus keeps two record kinds for what the language or the implementation does not do. A `LIMIT-*`
record describes a shortfall of the implementation against the Language Spec (ADR-0055 section 4). A `GAP-*` record
describes the Language Spec's own boundary, something a fully correct implementation would still not do (ADR-0057,
which is still `proposed`). Each has a disposition (`known`, `accepted`, `mitigated`, `planned`, `resolved`,
`superseded`), an owner and a review date, and `check_architecture.py` enforces a set of rules over them. The spec
shows the live ones as `> **Gap**` and `> **Limitation**` marker lines.

Four things went wrong, and an audit of all 76 records (33 gaps, 43 limitations) shows how often.

- **A language boundary reads as a bug.** 30 markers appear in the spec chapters: 14 `known`, 12 `planned` and 4
  `accepted`. The four accepted ones (`GAP-MODULES-002`, `GAP-TYPES-010`, `-011`, `-012`) are decisions of the
  language, yet they carry the same marker as a feature that is not built.
- **The names read backwards.** A `GAP-*` is the language's own boundary and a `LIMIT-*` is a gap between the spec and
  the implementation. "Limit" reads as a language limit and "gap" as a spec/implementation gap.
- **Records go stale and nothing says so.** Nine `known` records have every tracking issue closed. Running each
  record's own reproduction against the current interpreter shows `LIMIT-TYPE-INFERENCE-003` is wrong (a `..` in an
  anonymous record pattern now compiles and runs) and `-002` and `LIMIT-COHERENCE-001` record error codes the
  compiler no longer produces. Only 18 of the 76 records contain a runnable reproduction at all.
- **Records overlap and can disagree.** Four spec rules have more than one active record. Nothing forces anyone to
  reconcile them.

The audit also asked, for every record, whether it is something that could not be expressed another way. None
was. Each has a cheaper home that already exists: spec prose, a marker, an issue, an RFC, an ADR, a `blocked`
exemption or a skipped fixture. The records add an index over those pieces, an owner and a review date, and a body of
checks that exist only because the records do.

## Decision

### 1. The record kinds are retired

`GAP-*` and `LIMIT-*`, the `architecture/gaps` and `architecture/limitations` directories, and the `Gap` and
`Limitation` markers go away. No new record of either kind is filed. This supersedes ADR-0057 and the limitation
parts of ADR-0055 section 4 once it is accepted. Nothing is renamed: the audit found nothing that needs a kind.

### 2. What replaces a record

Every limit is one of the following, and each has a home that carries it without a record.

| What it is | Where it lives |
|---|---|
| **A boundary of the language, by design.** No plan, nothing to track. | A plain statement in the spec ("Metel does not …"), written as a Legality Rule when it is checkable, with the reproduction as an expect-fail fixture. The RFC or ADR that decided it is reachable from the generated backlinks. No marker. |
| **Planned or in flight.** An RFC and an issue exist. | `> **Planned for vX.Y.Z (RFC-NNNN).**` when it has an RFC and a milestone, or `> **Pending** metel-core#N` when it lands within the milestone. The issue holds the plan. |
| **Open or undecided.** The spec is silent and nothing is scheduled. | An issue labelled `needs-design`. No inline marker: the spec states what it specifies, and a reader is not told about every thing it does not. A generated page of open questions lists the labelled issues. |
| **A deviation in the current release.** The spec promises it and the code does not deliver it. | The `blocked` exemption on the rule, citing the issue, and a `skip = "pending: #N"` fixture. The existing validity checks apply to both. |
| **A property of the implementation.** Not a property of the language. | The consequences of the ADR that chose it, or a note on the architecture requirement it qualifies. |
| **Resolved or superseded.** | Nothing: git, the issue, the RFC and the changelog hold the history. |

### 3. Claims about behaviour are executable

A statement that the compiler accepts or rejects something is a runnable block, not prose. A spec or ADR passage that
documents a limit or a boundary carries a `metel` block with its expected outcome (an `expect-fail` marker naming
the diagnostic code), which `check_doc_examples.py` already runs. When the behaviour changes, the block fails, and the
passage is stale by construction. This replaces the "does the record still make sense" judgement with a result.

### 4. The checks that carry over

No new apparatus is needed. The staleness and contradiction problems fall to checks that exist:

- `Pending` and `Planned for` markers fail while their issue is closed or has no milestone, or their version has passed.
- A `blocked` exemption fails when its issue is closed, and a `skip = "pending: #N"` fixture fails on the same rule.
- Contradiction between a limit and a spec rule becomes a spec rule contradicting its own exemption or marker, which
  those checks already see. The overlap of two records on one rule disappears with the records.

Two additions are made. The doc-example check also runs the blocks of ADRs and the architecture spec, so a limit
documented there is held to section 3. And a `blocked` exemption on a rule that a fixture now cites is a finding,
because it means the deviation may be gone and the exemption is the stale half.

### 5. Migration

The records are removed in one ordered pass. The audit assigns each record a destination:

1. Delete the 29 records that are `resolved` or `superseded`.
2. Convert the 6 language boundaries to spec statements with an expect-fail fixture each: `GAP-MODULES-001`, `-002`,
   `GAP-TYPES-001`, `-010`, `-011`, `-012`.
3. Turn the 14 planned records into `Planned for` or `Pending` markers with their existing issue and RFC.
4. File an issue labelled `needs-design` for each of the 11 open questions.
5. For each of the 9 records whose tracking issues are all closed, decide: fixed (delete), a real bug (a new issue),
   or an unscheduled design question (a `needs-design` issue).
6. Move the 7 implementation notes into the consequences of their ADRs.
7. Retire the machinery: the record checks in `check_architecture.py`, the `<!-- records:gaps -->` and
   `<!-- records:limitations -->` listings, the `// limit:` markers in `metel-core` source (13) and the `GAP-` and
   `LIMIT-` references in fixtures (36 lines), and the two directories. A check then rejects a new `GAP-*` or `LIMIT-*`
   id anywhere.

The full table is in [the audit](../reports/gap-limit-record-audit.md) that supports this decision. Until step 7 the existing checks stay on, so the corpus is
valid at every step.

## Consequences

- A reader of the spec sees only what is true, plus a marker where something is coming. An accepted boundary is a
  sentence of the language, not a defect.
- Several fields disappear: `owner`, `review`, `discovered_by` and `affects`. Ownership and review move to the issue
  (assignee, labels) and to the spec's own `last_reviewed` on the rule that states a boundary. The cross-cutting query
  "which rules have known deviations" becomes the set of `blocked` exemptions.
- The architecture evidence pages lose their generated record listings. The open-questions page replaces the gap list.
- The record schema, its disposition vocabulary, and the record checks in `check_architecture.py` with their tests are removed.
- A limit with no issue and no spec statement is invisible. That is intended: if it matters to a reader it is a spec
  sentence or a marker, and if it matters to the project it is an issue.

## Alternatives considered

- **Keep both kinds and rename them** (for example `OPEN-*` and `DEV-*`). Fixes the names and nothing else: the audit
  found no record that needs a kind, so the rename keeps all the machinery for no distinct content.
- **Keep the records and add checks** for staleness and contradiction. Most of those checks would have to be built
  around the records' own fields, and the signals they need (issue state, milestone, RFC status, a reproduction) are
  already available on the markers, exemptions and fixtures.
- **Keep only `accepted` boundaries as records.** An accepted boundary is a statement about the language, and the
  spec is where that is read.
