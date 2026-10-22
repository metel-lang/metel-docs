---
title: "Release"
---

# Release

The path from a version tag in `metel-core` to published, versioned documentation and a GitHub Release. Source: `metel-core/RELEASING.md`, `release.yml`, `/cut-release`.

### PROC-RELEASE-001 — A release is cut by the maintainer, never by automation {#proc-release-001}

The version number is chosen when a release is cut, by the versioning rule (a spec change needs at least a minor bump; a patch never changes the language). Nothing names a version that has not been cut (`ROADMAP.md`). Pushing the tag is the only step that starts automation.

| Field | Value |
|---|---|
| `status` | `implemented` |
| `owner` | release process |
| `trigger` | manual: `/cut-release vX.Y.Z` after `/gap-analysis` and `/milestone-integration-test` |
| `produces` | a `vX.Y.Z` tag on `metel-core` `main` once every gate in PROC-RELEASE-008 passes |
| `implemented by` | `metel-core/.claude/commands/cut-release.md`, `metel-core/RELEASING.md` |
| `verified by` | none automated: the command is a procedure the maintainer follows; the tag push is then checked by PROC-RELEASE-002 |
| `related` | PROC-RELEASE-002, PROC-RELEASE-008, PROC-RELEASE-003 |

### PROC-RELEASE-002 — A tag whose changelog section is not finalized releases nothing {#proc-release-002}

The job extracts the `## vX.Y.Z` section of `release-notes/changelog.md` from the pinned docs and fails when it is missing or still begins with `**In progress`. Until it passes, nothing writes to another repository and nothing is built.

| Field | Value |
|---|---|
| `status` | `implemented` |
| `owner` | release process |
| `trigger` | push of a tag `vX.Y.Z` to `metel-core` |
| `produces` | a pass or fail that gates both PROC-RELEASE-003 and PROC-RELEASE-007 |
| `implemented by` | `metel-core/.github/workflows/release.yml` job `validate-release` |
| `verified by` | the job itself: it fails the run and the two jobs that need it do not start |
| `related` | PROC-RELEASE-001, PROC-RELEASE-007 |

### PROC-RELEASE-003 — The chain bumps the website to the docs commit metel-core pins, not to metel-docs main {#proc-release-003}

Reading metel-core's own pin, rather than resolving metel-docs `main` again, guarantees that the spec the release tests ran against and the spec the website shows for it are the same commit (ADR-0051).

| Field | Value |
|---|---|
| `status` | `implemented` |
| `owner` | release process |
| `trigger` | job `release-chain` after `validate-release` |
| `produces` | a `release: vX.Y.Z` commit on `metel-website` `main` that moves its `docs` pointer to the commit `metel-core` itself pins |
| `implemented by` | `metel-core/.github/workflows/release.yml` job `release-chain`, steps "Read the pinned docs submodule commit" and "Bump the docs submodule pointer" |
| `verified by` | none automated beyond the job; the pinned commit is the one the release gate ran against |
| `related` | PROC-DOCS-002, PROC-RELEASE-004, PROC-RELEASE-009 |

### PROC-RELEASE-004 — Only a minor release freezes a docs snapshot {#proc-release-004}

A patch release changes no language-visible behaviour, so its documentation is the minor version it patches. It still gets its docs pointer bumped and the site redeployed; it does not get a snapshot of its own.

| Field | Value |
|---|---|
| `status` | `implemented` |
| `owner` | release process |
| `trigger` | step "Cut a new docs version" in `release-chain` |
| `produces` | `versioned_docs/version-X.Y.0`, `versioned_sidebars` and `versions.json` for a release whose patch component is `0` |
| `implemented by` | `metel-core/.github/workflows/release.yml` (`is_minor`) |
| `verified by` | the website deploy confirms the version is present: PROC-DEPLOY-002 |
| `related` | PROC-DEPLOY-002, PROC-RELEASE-003 |

### PROC-RELEASE-005 — The architecture evidence is rendered into the snapshot, pinned to the release tag {#proc-release-005}

The step runs before the snapshot is frozen and needs no git history. A failure stops the chain before the website is tagged, so a broken generator blocks a release and never publishes empty evidence.

| Field | Value |
|---|---|
| `status` | `implemented` |
| `owner` | release process |
| `trigger` | step "Render the architecture evidence for the snapshot" in `release-chain`, minor releases only |
| `produces` | the `implements` and `verified by` cells and the limitation records' code links in the snapshot, each link `blob/<tag>/<path>#L<line>` |
| `implemented by` | `metel-core/.github/workflows/release.yml`, `metel-docs/architecture/tools/generate_architecture_evidence.py --publish` (ADR-0064) |
| `verified by` | the generator's tests; a dry run against the v0.14.0 tag reproduced the stored v0.14.0 snapshot exactly (110 evidence rows, 65 records). The step itself is first exercised by the next minor release |
| `related` | PROC-DOCS-004, PROC-RELEASE-006 |

### PROC-RELEASE-006 — The website is tagged only after its version commit is pushed, and a tag is not recreated {#proc-release-006}

A retry of a failed run is safe: an existing tag is reported and not re-created, and a commit with no content changes is not made.

| Field | Value |
|---|---|
| `status` | `implemented` |
| `owner` | release process |
| `trigger` | step "Tag the website release" in `release-chain` |
| `produces` | the tag `vX.Y.Z` on `metel-website`, which triggers PROC-DEPLOY-001 |
| `implemented by` | `metel-core/.github/workflows/release.yml` |
| `verified by` | none automated; a retry of the chain finds the tag and leaves it |
| `related` | PROC-DEPLOY-001 |

### PROC-RELEASE-007 — A GitHub Release is built from the changelog section and the release binary {#proc-release-007}

It needs only the repository's own token and writes to no other repository. A failure of this job does not block the website chain, and the reverse.

| Field | Value |
|---|---|
| `status` | `implemented` |
| `owner` | release process |
| `trigger` | job `github-release` after `validate-release`, independent of `release-chain` |
| `produces` | a GitHub Release on `metel-core` whose body is the changelog section, with the `metel` binary |
| `implemented by` | `metel-core/.github/workflows/release.yml` job `github-release` |
| `verified by` | the job itself |
| `related` | PROC-RELEASE-002 |

### PROC-RELEASE-008 — A tag is cut only when the release gate passes {#proc-release-008}

`develop` is frozen from the start of the gate until the tag. The gate asks, in order: the milestone is complete or its open issues are re-milestoned (a deferred bug returns to Backlog); the integration report exists, passes, and is newer than the freeze; the version follows the rule; the changelog is finalized; RFC state is clean with no warnings; no architecture review is stale; no pending part is open in the release milestone; the spec, internal documents and decision records reflect the release; the full suite and the doc examples pass on the release commit. Warnings that a pull request only shows are enforced here.

| Field | Value |
|---|---|
| `status` | `implemented` |
| `owner` | release process |
| `trigger` | manual: the steps of `/cut-release` |
| `produces` | a go or no-go for the tag |
| `implemented by` | `metel-core/.claude/commands/cut-release.md`; the checks it runs are `rfc.py check --strict`, `generate_architecture_evidence.py --check --strict` and `check_architecture.py --release-gate` |
| `verified by` | the checks are automated tools with their own tests (PROC-DOCS-006, PROC-DOCS-007, PROC-DOCS-008); running them is a manual step |
| `related` | PROC-RELEASE-001, PROC-DOCS-006, PROC-DOCS-007, PROC-DOCS-008 |

### PROC-RELEASE-009 — Each step of the chain writes to one repository with a token scoped to it {#proc-release-009}

Secrets appear only by class: a write token for `metel-website` lives in `metel-core`; deploy credentials for the hosting project live in `metel-website`. No secret value appears in this specification.

| Secret | Lives in | Scope |
|---|---|---|
| `WEBSITE_TOKEN` | `metel-core` | write to `metel-website` only |
| `VERCEL_TOKEN`, `VERCEL_ORG_ID`, `VERCEL_PROJECT_ID` | `metel-website` | deploy access for the hosting project |
| built-in `GITHUB_TOKEN` | each repository | same-repository writes (`develop-latest`, the GitHub release) and public reads (checker, rolling binary); no cross-repository credential is needed for them |

The tokens that once authenticated the private documentation submodule and the old sync into `metel-docs` are retired (ADR-0051); they should be removed from the repository settings, not left provisioned. `metel-core/RELEASING.md` lists how each remaining secret is provisioned.

| Field | Value |
|---|---|
| `status` | `implemented` |
| `owner` | release process |
| `trigger` | the release workflow |
| `produces` | no credential that spans repositories |
| `implemented by` | `metel-core/.github/workflows/release.yml` (`WEBSITE_TOKEN`: write to `metel-website` only; `github-release` uses the built-in token) |
| `verified by` | none automated; by construction of the workflow |
| `related` | PROC-RELEASE-003 |
