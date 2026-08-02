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

## Release checklist

*Added 2026-08-02, from the v0.12.0 pre-release review. This document previously defined
the release **model** — tags, annotation style, changelog format — but not the **steps**,
so every release re-derived them. Three of the five items below were genuinely undone at
the point v0.12.0 was declared ready, and were found only because someone ran a review by
hand.*

Run in order. Everything before the tag happens on `develop`; the tag is applied to
`main` after the release-prep commit merges.

**1. Verify the tree.**
- [ ] `cargo test --release` — all suites green
- [ ] `cargo clippy --release --lib -- -W clippy::pedantic` — clean
- [ ] `cargo fmt --check` — clean
- [ ] `rfc.py check` — clean (also confirms `REGISTRY.md` is not stale)

**2. Verify the release is actually complete.**
- [ ] The version milestone has **zero open issues**
- [ ] No RFC targeting this version is short of `4-implemented`, or the changelog says
      explicitly which parts shipped and which did not
- [ ] Any **release gate** recorded in an RFC (e.g. RFC-0071 §9c's "#290 must not ship
      without #292") is discharged, and the discharge is written down in the RFC itself
- [ ] `git ls-tree <ref> docs` resolves to a commit reachable from `metel-docs` `main`

**3. Bump the version in every place it is written.** These are separate files and
nothing cross-checks them:
- [ ] `metel-interpreter/Cargo.toml` — `version = "X.Y.Z"`
- [ ] `docs/public/reference/spec.md` — frontmatter `version: vX.Y.Z` (a `vX.Y.0` tag
      means *spec + interpreter*, so the spec version is part of what is tagged)

**4. Close out the changelog entry.**
- [ ] Replace the in-progress line with the released form used by every prior entry:
      `**Released YYYY-MM-DD.** The spec's `Since vX.Y.Z` / `Changed in vX.Y.Z` markers
      refer to this entry.`
- [ ] Confirm the entry names the RFCs implemented, features, and breaking changes

**5. Normalise version markers *before* tagging — a tagged spec version is immutable.**
- [ ] Every marker for this version uses the mandated `Since vX.Y.Z` form (see
      "Annotation style" above), not ad-hoc wording. v0.12.0 shipped its review with
      seven `Available in v0.12.0` sites against three `Since v0.12.0`; after a tag, the
      only remedy is errata in the next version.

**6. Tag.**
- [ ] Release-prep commit merged to `develop`, then `develop` → `main`
- [ ] Single tag `vX.Y.Z` on `main`

**Also worth a look each time, though not gating:** stale "known issues" notes in
`AGENTS.md` or elsewhere that describe problems since fixed. v0.12.0's review found
`AGENTS.md` still warning that `spec.md` claimed `v0.7.0` and a reference-counting memory
model, both corrected releases earlier. A warning that points at a non-problem trains
readers to skip warnings.

---

## Changelog

Version entries live in `docs/public/release-notes/changelog.md`. Each entry lists features added, breaking changes (if any), and whether it includes spec changes.

**No process artifacts in the changelog.** *(Rule added 2026-08-02; the changelog was swept the same day.)* The "public/spec vs. internal/process boundary" above scoped only to `docs/public/reference/spec/`, so the changelog was never covered and had accumulated RFC ids, issue numbers, ADR ids, old task ids (`METEL-NNN`), and sprint branch names across nearly every entry. None of these mean anything to a language user, and **RFC numbers in particular are not public** — the RFC corpus is internal, so citing one points at nothing a reader can follow.

The changelog answers three questions and nothing else:

1. **What changed** in the language or standard library?
2. **Does it break my code**, and what do I write instead?
3. **What is the known limitation** I should plan around?

Concretely, the changelog does **not** contain: RFC ids, issue or PR numbers, ADR ids, task-tracker ids, sprint or branch names, or a "RFCs implemented" header. Design rationale belongs in the RFC; migration guidance belongs here.

**Keep entries proportionate.** A release entry describing user-visible change should read closer to 100–200 lines than 350. The v0.12.0 entry reached 358 lines largely by importing RFC-voice rationale ("rejecting rather than accepting is deliberate throughout") and internal archaeology about which error code a bug used to report. Cut both; keep the behaviour, the breaking change, and the workaround.

Patch releases (`vX.Y.Z` with Z > 0) get a short entry listing only the interpreter changes — no spec section needed.

---

## References

- Project vision and dual-mode commitment: `docs/internal/vision.md`
- Language spec: `docs/public/reference/spec.md`
- Changelog: `docs/public/release-notes/changelog.md`
- RFC lifecycle (authoritative, not this document): `internal/rfcs/PROCESS.md`
- Long-term objectives and priorities: `reports/strategy/OBJECTIVES.md`
