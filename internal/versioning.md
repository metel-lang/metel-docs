---
id: versioning
title: "Versioning Model"
type: guide
created_date: '2026-05-21'
---

# Metel Versioning Model

This document is the authority on version numbering, the RFC lifecycle, and documentation conventions. All other guides defer to it on these topics.

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

`docs/public/reference/spec.md` is the entry point for the language specification. It links to focused sub-files in `docs/public/reference/spec/`. The public docs are split into `getting-started/`, `reference/`, and `release-notes/` so the published site can stay navigable without flattening everything into one directory. The spec describes the full language including features planned for future versions. Version snapshots are captured as **git tags**, not separate document files.

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
| Feature planned for a future version | `> **vX.Y.Z feature.** description...` |

---

## RFC Lifecycle

RFCs are the mechanism for proposing language changes. An RFC must be accepted and assigned a target version before implementation begins.

### States

The main representation of an RFC's lifecycle state is the directory containing the RFC file. The RFC frontmatter and the Plane RFC item must mirror that directory exactly.

| Directory | State | Meaning |
|---|---|---|
| `docs/internal/rfcs/0-draft/` | `draft` | Being written; not yet ready for review |
| `docs/internal/rfcs/1-under-review/` | `under-review` | Ready for evaluation; set manually by the author |
| `docs/internal/rfcs/2-accepted/` | `accepted` | Design decided; target version milestone assigned; **spec must be updated before implementation begins** |
| `docs/internal/rfcs/3-implemented/` | `implemented` | Implemented and shipped in the target version |
| `docs/internal/rfcs/4-superseded/` | `superseded` | Replaced by a later RFC; successor recorded in frontmatter or `## Decision` |
| `docs/internal/rfcs/5-refused/` | `refused` | Will not be implemented; reason recorded in `## Decision` |

### Frontmatter fields

```yaml
---
id: rfc-NNNN
title: "..."
date: 'YYYY-MM-DD'
status: draft          # one of the states above
spec_status: pending   # pending | done — tracks whether the relevant spec/docs reflect the RFC decisions
---
```

`spec_status` is required for all `accepted` RFCs. It is independent of `status`:
- `pending` — RFC is accepted but the relevant spec or architecture docs have not yet been updated to reflect its decisions. **Implementation is blocked until this is `done`.**
- `done` — The spec (for language-visible RFCs: `docs/public/reference/spec/`) or internal architecture docs (for implementation RFCs: `metel-interpreter/docs/`) have been updated. Implementation may proceed.

The target version is **not** stored in the RFC frontmatter. It lives in exactly one place: the project milestone. The `## Decision` section records it in prose (`**Target:** vX.Y.0`) as a human-readable audit trail, but the milestone is the authoritative field.

### Acceptance process

1. Author moves the RFC to `1-under-review/` and sets `status: under-review` when the RFC is ready for evaluation.
2. Discussion happens in the linked Plane RFC item.
3. The project owner records the outcome in a `## Decision` section at the bottom of the RFC file.
4. **If accepted**:
   - Move the RFC to `2-accepted/`, set `status: accepted`, and set `spec_status: pending`.
   - Assign the Plane RFC item to the target version milestone and set its state to `accepted`.
   - Record `**Target:** vX.Y.0` in `## Decision`.
   - **Immediately** update the relevant spec or docs to reflect the RFC's decisions and set `spec_status: done`. This may be a single commit. Implementation items must not be created or started until `spec_status: done`.
5. **If refused**: move the RFC to `5-refused/`, set `status: refused`, set the Plane RFC item to `refused`, and record the reason in `## Decision`.
6. **If superseded**: move the RFC to `4-superseded/`, set `status: superseded`, set the Plane RFC item to `superseded`, and record the successor in frontmatter or `## Decision`.

Once the RFC's target version ships (git tag applied), move it to `3-implemented/`, set `status: implemented`, and set the Plane RFC item to `implemented`. This is a required step of the release process — every accepted RFC whose target version matches the tag must be updated before the tag is pushed. The sprint-end quality gate enforces this with a full RFC staleness sweep.

### Decision section format

```markdown
## Decision

**Outcome:** Accepted / Implemented / Superseded / Refused  
**Target:** vX.Y.0 *(if accepted)*

Brief rationale — why this design was chosen (or not), what alternatives were considered, and any constraints that drove the decision.
```

---

## Plane Milestone Structure

| Milestone type | Examples | Purpose |
|---|---|---|
| **Version** | `v0.4.0`, `v0.5.0`, `v1.0.0` | Release planning — what ships in which version |

Implementation work items are assigned to the **version milestone** they target. Plane RFC work items must use the exact lifecycle state represented by their RFC directory: `draft`, `under-review`, `accepted`, `implemented`, `superseded`, or `refused`.

---

## Changelog

Version entries live in `docs/public/release-notes/changelog.md`. Each entry lists RFCs implemented, features added, breaking changes (if any), and whether it includes spec changes.

Patch releases (`vX.Y.Z` with Z > 0) get a short entry listing only the interpreter changes — no spec section needed.

---

## References

- Project vision and dual-mode commitment: `docs/internal/vision.md`
- Language spec: `docs/public/reference/spec.md`
- Changelog: `docs/public/release-notes/changelog.md`
