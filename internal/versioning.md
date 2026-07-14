---
id: versioning
title: "Versioning Model"
type: guide
created_date: '2026-05-21'
updated: '2026-07-10'
---

# Metel Versioning Model

This document is the authority on version numbering and documentation conventions.
**It is not the authority on the RFC lifecycle** — see the note in place of the old
"RFC Lifecycle" section below. All other guides defer to this document on version
numbering and doc conventions specifically.

---

## Version Numbering

All Metel releases — language spec and interpreter — share a single three-digit version number: `v<major>.<minor>.<patch>`.

| Segment | When to increment | Examples |
|---|---|---|
| **major** | Breaking changes to existing programs | `v0.x → v1.0` |
| **minor** | New language features; spec changes implemented from accepted RFCs | `v0.4.0 → v0.5.0` |
| **patch** | Interpreter-only changes — bug fixes, refactors, performance — with **no spec changes** | `v0.4.0 → v0.4.1` |

**Rule:** `patch > 0` always means the spec is unchanged from the `.0` release of that minor version. A patch release never adds, removes, or alters any language-visible behaviour.

### Pre-1.0 era

Versions before `v1.0` cover the active development period. Minor versions may introduce significant new capabilities (generics, aspects, concurrency, the memory model). Breaking changes before `v1.0` are possible but must be called out explicitly in the CHANGELOG.

### Historical note

Versions v0.1 through v0.4 were tagged with two-digit identifiers (`v0.3`, `v0.4`) before this scheme was adopted. They are treated as equivalent to `v0.1.0`–`v0.4.0`. New releases use three digits.

---

## The Spec as a Living Document

`docs/public/reference/spec.md` is the entry point for the language specification. It links to focused sub-files in `docs/public/reference/spec/`. The public docs are split into `getting-started/`, `reference/`, and `release-notes/` so the published site can stay navigable without flattening everything into one directory. The spec describes the full language, including features planned for future versions, but **availability is expressed only in terms of versions**. Version snapshots are captured as **git tags**, not separate document files.

**Public/spec vs. internal/process boundary.** The public spec is for language users. It may say that a feature is available since `vX.Y.Z`, changed in `vX.Y.Z`, or planned for `vX.Y.Z`. As a narrow exception, a future-facing availability note may also include the RFC id in parentheses, so not-yet-implemented spec text can still be tied back to its design source during implementation. Issue numbers, `impl_tracking` links, and other tracking artifacts still do not belong in `docs/public/reference/spec/`.

### Version tags

When a version is released, a single git tag is applied:

| Tag | Meaning |
|---|---|
| `vX.Y.0` | First release of spec version X.Y (spec + interpreter) |
| `vX.Y.Z` (Z > 0) | Patch release — interpreter only, spec unchanged |

**A tagged spec version is immutable.** If a spec error is discovered after tagging, it is documented as errata in the next version's CHANGELOG. Tags are never amended.

### Annotation style

Spec sections are annotated to indicate which version introduced or changed a feature:

| Situation | Annotation |
|---|---|
| Feature added in a specific version | `> *Since vX.Y.Z.*` |
| Existing feature changed in a version | `> *Changed in vX.Y.Z: description.*` |
| Feature planned for a future version | `> *Planned for vX.Y.Z (RFC-0123).*` |

**Availability rule.** Prefer these annotations over prose like "not yet implemented." The public question is "in which version is this language behavior available?"; for future-facing text only, the RFC id may appear as the stable design reference, but issue numbers and tracking links stay out.

---

## RFC Lifecycle

**Superseded 2026-07-10 by `internal/rfcs/PROCESS.md` — that document is now the sole
authority on the RFC lifecycle, frontmatter requirements, and tooling.** This section
previously duplicated that content (6 stages, no `3-integrated`; a `spec_status:
pending/done` frontmatter field tracking spec-sync separately from lifecycle state) and
was never reconciled when PROCESS.md was written, leaving two documents disagreeing
about the same thing. `spec_status` is retired outright: `3-integrated` is now a real
lifecycle *stage* (spec merged, worked examples checked) rather than a side field on
`2-accepted`, and `impl_status`/`impl_tracking` (also on RFC frontmatter, from
`3-integrated` onward) track implementation progress the same way `spec_status` tried
to. See `PROCESS.md` for the current 7-stage lifecycle, the tooling (`rfc.py`), and the
working rules.

Two things below are unaffected by this and remain accurate:

**Target version.** Still not stored in RFC frontmatter — it lives in exactly one
place, the project milestone (a Codeberg milestone; see `metel-core/AGENTS.md`'s Task
Tracking section). The RFC's own `## Decision` section may record it in prose
(`**Target:** vX.Y.0`) as a human-readable note, but the milestone is authoritative.

**Decision section format:**

```markdown
## Decision

**Outcome:** Accepted / Implemented / Superseded / Refused  
**Target:** vX.Y.0 *(if accepted)*

Brief rationale — why this design was chosen (or not), what alternatives were considered, and any constraints that drove the decision.
```

---

## Milestone Structure

| Milestone type | Examples | Purpose |
|---|---|---|
| **Version** | `v0.4.0`, `v0.5.0`, `v1.0.0` | Release planning — what ships in which version |

Implementation issues are assigned to the **version milestone** they target (see
`metel-core/AGENTS.md`'s Task Tracking section). RFCs are not separately tracked by a
milestone-adjacent custom field — the RFC file's own directory and frontmatter is the
complete lifecycle record; see `PROCESS.md`.

---

## Changelog

Version entries live in `docs/public/release-notes/changelog.md`. Each entry lists RFCs implemented, features added, breaking changes (if any), and whether it includes spec changes.

Patch releases (`vX.Y.Z` with Z > 0) get a short entry listing only the interpreter changes — no spec section needed.

---

## References

- Project vision and dual-mode commitment: `docs/internal/vision.md`
- Language spec: `docs/public/reference/spec.md`
- Changelog: `docs/public/release-notes/changelog.md`
- RFC lifecycle (authoritative, not this document): `internal/rfcs/PROCESS.md`
- Long-term objectives and priorities: `reports/strategy/OBJECTIVES.md`
