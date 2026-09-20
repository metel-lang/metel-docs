---
id: adr-0057
title: "GAP-* Records for Language-Level Gaps"
date: '2026-09-20'
status: proposed
relates: adr-0055
implements: metel-core#1179
updated: '2026-09-20'
---

## Context

ADR-0055 §4 created `LIMIT-*` records for known limitations of the
architecture: how the compiler or interpreter is built. §5 reserved a
separate `GAP-<AREA>-<NNN>` prefix for a language-level counterpart and left
its charter for a later ADR.

The per-stage limitation analysis (metel-core#1209-#1218) makes that later
ADR necessary. Its triage found that the candidate limitations are of two
kinds, and that filing all of them as `LIMIT-*` would blur them: some are
boundaries of the implementation (a fallback, a skipped analysis, a
placeholder value), while others are boundaries of what the language
currently specifies or guarantees (rank-1 polymorphism, no borrow checking,
no first-class generic values). The reader, the owner and the way out
differ: an implementation limitation is closed by changing code; a language
gap is closed by an RFC that changes what the Language Spec says.

The three `LIMIT-*` records that already exist and are language-visible
(cross-module mutual recursion, `?` needing an explicit `From` impl, overload
sets not exportable) show the pressure: they sit in the architecture
inventory but describe behaviour a Metel programmer observes.

## Decision

### 1. What a `GAP-*` record is

A `GAP-<AREA>-<NNN>` record describes a known, accepted gap in what the
Language Spec specifies or guarantees. It is a fact about the language as
currently defined, not about one implementation's fidelity to it.

`<AREA>` is a Language Spec chapter: `TYPES`, `EXPRESSIONS`, `FUNCTIONS`,
`DECLARATIONS`, `MODULES`, `OWNERSHIP`, `RUNTIME`, `LEXICAL`.

### 2. The sorting test

To decide between the two record kinds, ask:

> Would a fully correct implementation of the *current* Language Spec still
> have this behaviour?

- **Yes**: the spec itself does not cover it, or covers it with a limitation.
  This is a `GAP-*`. Example: function parameters are monotypes, and the spec
  says so.
- **No**: the spec promises (or an accepted RFC will promise) something the
  implementation does not yet deliver. This is a `LIMIT-*`. It may be
  user-visible; its `impact` says so. Example: destructors are specified but
  not yet invoked.
- **Both**: a user-visible spec gap whose current behaviour also depends on an
  implementation shortcut gets a `GAP-*` for the spec side and a `LIMIT-*` for
  the implementation side, each linking the other under `affects`.

A behaviour that is a bug (the spec is clear and the implementation is wrong)
is neither: it is filed as an issue.

### 3. Shape

A `GAP-*` record follows §4's record shape (its own file, standalone
lifecycle) with these differences:

| Field | Difference |
|---|---|
| `scope` | a Language Spec section anchor, not an Architecture Spec section |
| `affects` | Language Spec rules (`spec.*` IDs), RFCs, and any related `LIMIT-*` records |
| `disposition` | the same values as `LIMIT-*` |
| `resolution` | normally an RFC (draft, under review or accepted) or an issue; a gap closes when the spec text changes and its rules gain evidence |

Records live in `reference/spec/gaps/gap-<area>-<nnn>.md`, next to the spec
they qualify. Unlike `LIMIT-*`, they are part of the published Language Spec
material, because the reader they serve is a Metel programmer.

### 4. Tooling

`check_architecture.py` validates `GAP-*` records with the same rules as
`LIMIT-*`: ID shape and uniqueness, required fields, disposition rules, typed
links, and review dates for accepted gaps. Additionally, a `GAP-*` that lists
a related `LIMIT-*` must be linked back from that record. The Language Spec's
own tooling is unchanged. Implementation is tracked separately; this ADR only
charters the record kind.

### 5. Relationship to existing records

Existing `LIMIT-*` records are re-sorted by the test in §2 during the per-stage
analysis, not en masse. A record that is really a spec gap is re-filed as a
`GAP-*` and its `LIMIT-*` is marked `superseded` with a pointer, rather than
renumbered.

## Alternatives Considered

**One namespace with a `kind` field.** Rejected. ADR-0055 §5 already weighed a
shared word with a domain marker and reversed it: two distinct words read
better and never collide. A `kind` field reintroduces the same shared-word
problem at the field level, and would hide which records belong in the
Language Spec's material.

**Document language gaps only in the Language Spec prose.** Rejected as the
sole mechanism. Prose has no owner, disposition, review date or checker, which
are what §4 says make a limitation durable. Prose remains the place a gap is
*stated to a reader*; the record is the inventory behind it.

## Consequences

- ADR-0055 §5 changes from "reserved" to "chartered by ADR-0057".
- The per-stage analysis issues sort each candidate by §2 before records are
  written.
- The Atlas limitations section (metel-core#1179) shows `LIMIT-*` records and
  links `GAP-*` records rather than duplicating them.
- A checker extension and a first batch of `GAP-*` records are follow-up work.
