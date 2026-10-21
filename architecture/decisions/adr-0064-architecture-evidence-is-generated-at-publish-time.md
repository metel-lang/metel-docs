---
id: adr-0064
title: "Architecture Evidence Is Generated at Publish Time, Not Checked In"
date: '2026-10-21'
status: accepted
relates: adr-0051, adr-0055, adr-0056
implements: metel-core#1508, metel-core#1416
---

## Context

The Architecture Spec states each requirement with two evidence cells, `implements` and
`verified by`, plus limitation records whose `## Affects` carries generated code links. ADR-0055
made these cells **generated**: a tool in `metel-docs` reads `arch-implements` / `arch-verifies`
markers in `metel-core` and writes commit-pinned GitHub links into the Markdown. The generated
text is committed to `metel-docs` and verified in two places:

- **metel-core CI** (`Architecture evidence`) runs the generator against its own commit, using the
  `docs` submodule's pinned commit for the tool and the cells.
- **metel-docs CI** (`architecture-check`) checks out metel-core `develop` and runs the same
  generator.

A cell holds a line number and the cited item's last-touch commit SHA. Both are derived from core
code that changes in the very pull request being checked, and the SHA exists only once the core
commit does. So a core PR that moves a cited function, or merely changes a cited file, cannot
contain the correct docs text. The author lands a metel-docs PR, then a second core commit that
bumps the gitlink, then re-runs CI. Core must then merge in a way that keeps its SHAs, and the
docs `architecture-check` is re-run after. Over the last 60 core `CI` runs 17 failed (28%), and the
`Architecture evidence` job was in 16 of those 17.

metel-core#1417 removed the part of this that was **spurious**: `--check` now compares what is
cited (the set of `path::item` labels per requirement and side), not how a link renders, so a line
shift or a newer commit no longer fails it. What remains is **structural**. As long as the cells are
committed, any change to which items are cited still needs a docs PR and a gitlink bump in the
same breath, and the docs repo's own check still has to look at a moving core branch.

The cells are also read in one place only: the website. Each versioned snapshot
(`versioned_docs/version-X/architecture/`) already stores the rendered evidence of its release, so
published history does not depend on the committed cells.

## Decision

### 1. Evidence is derived, so it is published, not committed

The `implements` and `verified by` cells and the limitation records' generated `// limit:` blocks
are **publish-time artifacts**. In `metel-docs` they are placeholders. They are generated from
`metel-core` and the spec when documentation is published, and never stored in the repository that
authors the spec.

- A requirement's `implements` / `verified by` cell holds `_Generated at publish._` (or the existing
  `_Exempt; see exemption below._` when an exemption is declared).
- Hand-authored content stays in `metel-docs`: the requirement text, the exemptions, and
  `last_reviewed`.
- A limitation record keeps its hand-written `## Affects` bullets (`path::symbol`, unlinked).
  The generated `// limit:` block is absent from the repository.

### 2. Where it runs

The generator runs in the two workflows that publish documentation, each of which already has the
code it cites:

| Publish path | Step | Core ref |
|---|---|---|
| **Release** (`release.yml` in metel-core) | Before the website's `docs:version`, run the generator in write mode on the docs working copy that is about to be versioned. | The release tag. |
| **Unreleased docs** (`next.yml` in metel-website) | Check out metel-core `develop` and run the same step before the build. | The `develop` commit SHA it built from, shown on the page as the unreleased view already is. |

The website build itself (`deploy.yml`, `promote.yml`) is unchanged: it builds the tag, which now
contains the generated evidence in `versioned_docs`. If the generator fails, the release job fails
before the website is tagged, because the step sits in the `release-chain` job ahead of the website
tag, so a broken generator stops the chain and never publishes empty evidence.

The step uses the existing write mode with `--core-ref <ref>`; the working copy is discarded or
committed only to the versioned snapshot.

### 3. Links are pinned to the release tag

A published link has the form `blob/<ref>/<path>#L<line>`, where `<ref>` is the release tag (for
`next`, the `develop` SHA) and `<line>` is the cited item's line in that tree. A tag is immutable, so
the link is a permanent permalink and is readable (`blob/v0.14.1/…`). It replaces the per-citation
last-touch SHA, which exists only so that a link survives an unrelated later commit; a tag does
that without a `git log -L` per citation.

Past releases keep the evidence already stored in their `versioned_docs` snapshots. Nothing is
regenerated for them; if one is ever needed, `--core-ref <old tag>` reproduces it.

### 4. What a pull request checks

Checks that a PR author can act on stay, and none of them reads a rendered link:

- **metel-core CI** runs the generator in `--check` mode against its own tree, using the pinned
  `docs` for the requirement list and exemptions. It validates the meaning: every cited claim id
  exists, every cited item or rule exists in its file, a cited test is not `#[ignore]`d, a cited
  fixture is not skipped, exemptions are valid and unexpired, every requirement has evidence or an
  exemption, and every `// limit:` marker names an existing active record. A cell that is still a
  committed rendering (legacy) is compared by label as today (metel-core#1417); a placeholder is
  not compared.
- **metel-docs CI** `architecture-check` runs the tool's tests and `check_architecture.py`
  (structure, cross-references, required fields). It no longer checks out metel-core, so a core PR
  in flight cannot make a docs PR fail.
- A core PR that adds a marker for an **existing** requirement needs no docs change and no gitlink
  bump. A core PR that cites a **new** claim id still needs the requirement written in `metel-docs`
  first. That cross-repository step is real, and rare.

### 5. `last_reviewed` is unchanged

`last_reviewed` stays a hand-typed commit SHA in the spec, audited against the cited code's last
change, a warning on a PR and an error at release under `--strict` (metel-core#1417). Because core
merges by rebase, a recorded SHA can stop resolving; that is reported as a warning too, and
re-reviewing the claim records the new SHA. Publishing does not run the audit.

### What a reader sees

- **Published site:** full evidence with links, for every released version and for `next` when it is
  enabled (`next.yml` ships switched off).
- **`metel-docs` `main` on GitHub:** requirements with a placeholder instead of links. The prose,
  exemptions and `last_reviewed` are all visible; the links are on the site.
- **Local `npm start`:** placeholders, unless the generator is run by hand.

## Consequences

**Good**

- A Rust-only core PR, or one that moves or adds a citation for an existing requirement, needs no
  metel-docs PR and no gitlink commit to pass CI. This is the target of metel-core#1416.
- The docs `architecture-check` has no dependency on a moving core branch.
- There is no committed text that can go stale, so there is nothing for CI to compare except what is
  cited.
- Links are stable tag permalinks.

**Bad**

- A docs PR cannot show the evidence for a changed requirement in its diff; reviewers read the
  site or run the generator.
- `release.yml` and `next.yml` gain a step and depend on the generator. A generator bug blocks a
  release until fixed; the previous design instead failed every PR.
- While `next.yml` stays disabled, there is no rendered evidence for unreleased docs.
- Unlinked bullets in a record's `## Affects` stay unlinked until publish.

**Neutral**

- The `--check` label comparison stays for any cell that is still a committed rendering, so
  migration can proceed requirement by requirement.

## Alternatives considered

- **A post-merge bot opens or updates the metel-docs PR.** Rejected. It automates the churn rather
  than removing it, adds a bot with write access to `metel-docs`, and leaves a window in which the
  committed text is wrong and docs `main` is red.
- **Move `architecture/` into metel-core**, so code and evidence change in one PR. Rejected. ADR-0051
  made `metel-docs` the single public documentation source; splitting the Architecture Spec away
  from it brings back a second source and a second path to the website for one section.
- **Keep the committed cells and rely on the semantic check (#1417 alone).** Rejected as the end
  state. The spurious failures are gone, but every change to which items are cited still needs a
  matching docs commit and gitlink bump, and the docs check still reads a moving core branch.
- **Committed `path::item` labels without links.** Rejected. It would keep a readable evidence list
  in docs diffs, but a docs PR would be needed whenever a citation changes, which is the
  circularity this ADR removes.
- **Generate during the website build.** Rejected. The website build has no metel-core checkout and
  would need a second credential and a way to choose the core ref for each docs version.
- **Pin links to commit SHAs.** Rejected in favour of the tag: equally immutable, readable, and it
  needs no history lookup per citation.

## Migration

1. **#1417 (done).** `--check` compares citations, not link rendering; `last_reviewed` warns on a PR
   and fails under `--strict` at release.
2. **#1509.** Make write mode a publish step: it must not need history, must not run the
   `last_reviewed` audit, and must write links as `blob/<ref>/…` for a given ref. Add the step to
   `release.yml` (before `docs:version`) and to `next.yml` (core `develop` checkout). Dry-run both
   against the last release tag.
3. **#1509.** Replace the committed cells and the committed `// limit:` blocks with placeholders in
   one metel-docs change, with a check-mode rule that a placeholder is not compared. Remove the
   `Architecture evidence is current` comparison from core CI's job, keeping the meaning checks, and
   remove the core checkout from the docs `architecture-check`.
4. **#1509.** Re-measure the core `CI` failure rate on the same 60-run window; the target is well
   under 10%, the remainder being real test or lint failures.
5. **#1506.** Record the resulting `PROC-*` requirements (below) in the Operations Spec.

## Operations Spec requirements affected (metel-core#1506)

- **PROC-DOCS: Architecture evidence is generated at publish time.** Derived evidence cells and
  `// limit:` blocks are placeholders in `metel-docs` and rendered at publish.
- **PROC-RELEASE: A release publishes evidence pinned to its tag.** `release.yml` generates it
  before the website versions the docs; a generator failure fails the release before the website is
  tagged.
- **PROC-DOCS: Unreleased docs render evidence pinned to the `develop` commit they were built from.**
  `next.yml`, when enabled.
- **PROC-CI: A core pull request needs no docs pull request to pass architecture checks** unless it
  cites a new claim id.
- **PROC-CI: The docs `architecture-check` does not read metel-core.**
- **PROC-RELEASE: A release runs the architecture check with `--strict`** (already in
  `/cut-release`, metel-core#1417).
