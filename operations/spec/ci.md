---
title: "Continuous integration"
---

# Continuous integration

What each repository's CI guarantees, in the state after ADR-0064. Source: the workflows, and `.githooks`.

### PROC-CI-001 — Core CI runs a fixed set of checks on every push and pull request to develop and main {#proc-ci-001}

Jobs: `test / clippy / fmt` (format, clippy with pedantic lints, tests); `rfc.py check`; `Architecture evidence` (meaning of the architecture markers, then `check_architecture.py` over skipped and pending fixtures); `grammar.md up to date`; `runtime.md matches stdlib declarations`; `doc examples`; `tools self-tests`; `clippy-allow ratchet`; `no post-freeze semantic name lookup`; `no flat module file beside its own directory`. On a push to `develop` only, `publish rolling develop binary` rebuilds the `develop-latest` pre-release.

| Field | Value |
|---|---|
| `status` | `implemented` |
| `owner` | continuous integration |
| `trigger` | push or pull request to `develop` or `main` of `metel-core` |
| `produces` | one job per check named in the statement; the first failure marks the run failed |
| `implemented by` | `metel-core/.github/workflows/ci.yml` |
| `verified by` | the jobs themselves |
| `related` | PROC-DOCS-004, PROC-DOCS-005, PROC-DOCS-010, PROC-CI-006 |

### PROC-CI-002 — A core pull request needs no docs pull request unless it cites a new claim id {#proc-ci-002}

The check compares what is cited, not how a link renders. A pull request that cites a claim id the pinned docs do not define needs that requirement written in metel-docs first; that is the one cross-repository step left.

| Field | Value |
|---|---|
| `status` | `implemented` |
| `owner` | continuous integration |
| `trigger` | a core pull request that adds, moves or removes `arch-implements`, `arch-verifies` or `// limit:` markers for an existing requirement or record |
| `produces` | a green `Architecture evidence` job with no change to metel-docs and no gitlink bump |
| `implemented by` | `generate_architecture_evidence.py --check` (meaning only); ADR-0064 |
| `verified by` | core CI over the last runs: the job failed in 15 of 17 failed runs before the migration and in none of the 12 runs after it. The 60-run measurement is pending (metel-core#1509) |
| `related` | PROC-DOCS-004, PROC-DOCS-003 |

### PROC-CI-003 — Docs CI runs four checks and does not read metel-core's code {#proc-ci-003}

`architecture-check` runs the two tools' regression tests and `check_architecture.py --check` (structure, cross-references, pending markers). `check-examples` runs the examples against core's binary. `check-mdx` builds the MDX. `rfc-check` runs the RFC tool's tests and `rfc.py check`. None checks out metel-core, so a core pull request in flight cannot fail a docs pull request, except through the binary of PROC-CI-004.

| Field | Value |
|---|---|
| `status` | `implemented` |
| `owner` | continuous integration |
| `trigger` | pull request or push to `main` of `metel-docs` |
| `produces` | one job per workflow |
| `implemented by` | `metel-docs/.github/workflows/architecture-check.yml`, `metel-docs/.github/workflows/check-examples.yml`, `metel-docs/.github/workflows/check-mdx.yml`, `metel-docs/.github/workflows/rfc-check.yml` |
| `verified by` | the workflows |
| `related` | PROC-DOCS-001, PROC-CI-004 |

### PROC-CI-004 — Docs example checks wait for a core binary that includes what the change needs {#proc-ci-004}

The binary must include core `develop` as it is, or, for each `Depends-on: metel-lang/metel-core#N` line in the pull request description, that pull request's merge commit. An unmerged dependency fails at once and names it. Otherwise it polls up to 30 minutes and then names the binary's commit and the one it needs.

| Field | Value |
|---|---|
| `status` | `implemented` |
| `owner` | continuous integration |
| `trigger` | step "Wait for a metel-core binary…" of `check-examples` |
| `produces` | the binary's commit, recorded in the job summary |
| `implemented by` | `metel-docs/.github/scripts/wait-for-core-binary.sh` |
| `verified by` | `.github/scripts/test_wait_for_core_binary.sh`, which runs first in the job |
| `related` | PROC-DOCS-010 |

### PROC-CI-005 — Checks separate problems from freshness warnings, and a release is strict {#proc-ci-005}

A problem is a property of the change under review. A warning depends on time or on code outside the change: a review that came due, an unreachable recorded commit, a scheduled RFC that is still a draft. A pull request that only moves a cited fixture is not failed by it; the release enforces it.

| Field | Value |
|---|---|
| `status` | `implemented` |
| `owner` | continuous integration |
| `trigger` | every run of `rfc.py check` and `generate_architecture_evidence.py --check` |
| `produces` | problems (fail) and warnings (printed, exit 0); with `--strict` warnings fail |
| `implemented by` | `rfc.py check --strict`, `generate_architecture_evidence.py --check --strict` |
| `verified by` | the tools' tests (`test_rfc.py`, `test_generate_architecture_evidence.py`) |
| `related` | PROC-DOCS-006, PROC-RELEASE-008 |

### PROC-CI-006 — Local hooks run the fast checks before a commit and the heavy ones before a push {#proc-ci-006}

The hooks can be bypassed locally; CI is the enforcement. `metel-docs` has its own hooks: `pre-commit` runs the tooling tests, `pre-push` runs `rfc.py check`, `commit-msg` rejects attribution trailers.

| Field | Value |
|---|---|
| `status` | `implemented` |
| `owner` | continuous integration |
| `trigger` | git hooks of `metel-core`, installed through `core.hooksPath` |
| `produces` | a refused commit or push |
| `implemented by` | `metel-core/.githooks/pre-commit` (format, `clippy-allow ratchet`, no post-freeze name lookup), `pre-push` (clippy with pedantic lints, the workspace tests, no flat module beside its directory, no merge commit in a push to `develop`), `commit-msg` (rejects attribution trailers) |
| `verified by` | the same checks run again in CI, so skipping a hook is caught there |
| `related` | PROC-CI-001, PROC-CI-007 |

### PROC-CI-007 — Branches, merges and commit messages follow one convention {#proc-ci-007}

Core integrates on `develop` and `main` moves only at a release; pull requests target `develop`. A core pull request is merged with the hosting service's **rebase merge** (`gh pr merge --rebase`), so `develop` stays linear, `main` is a prefix of it at every release, and no merge commit lands on it. The commits get new hashes, so nothing cites a branch commit; a recorded `last_reviewed` that named one stops resolving and is re-recorded at the next review (a warning, PROC-CI-005). `metel-docs` and `metel-website` take pull requests with a merge commit.

| Field | Value |
|---|---|
| `status` | `implemented` |
| `owner` | continuous integration |
| `trigger` | every change |
| `produces` | one issue, one branch `<type>/<issue>-<slug>`, one pull request, one linear history on `develop` |
| `implemented by` | `metel-core/AGENTS.md` (§ GitHub and branch workflow), `.claude/commands/ship-issue.md`; the `commit-msg` and `pre-push` hooks |
| `verified by` | the `commit-msg` hook (no attribution trailers) and the `pre-push` hook (no merge commit in a push to `develop`); the merge method itself is a maintainer step, not checked |
| `related` | PROC-CI-006, PROC-CI-005 |

### PROC-CI-008 — The Operations Specification is checked against the repositories {#proc-ci-008}

`check_operations.py` validates the specification's structure (ids, anchors, statuses, the field table, cross-references, tracking issues of planned requirements) and the paths a requirement says implement it, and discovers every workflow, script, hook, slash command and cargo bin in the repositories it can reach, requiring each to appear in `operations/inventory.md` (or be marked `local`) and every inventory row to name something that exists. Structural findings, and assets of `metel-docs` itself, fail the check. An asset of another repository that the inventory does not list is a warning on a pull request and fails under `--strict`, because requiring `metel-docs` to change before a `metel-core` pull request could pass is the circularity of PROC-CI-002. A `# Process: PROC-…` marker in a workflow or script must name an existing requirement.

The flow diagrams of [`flows.md`](../flows.md) are checked for staleness by the same tool. A node that cites a requirement that does not exist, or a workflow, script or command that does not exist, is a finding when every repository is readable (otherwise the asset may live in one that is not, and nothing is said). A workflow or slash command that no node mentions, and an implemented or partial requirement that no node cites, is a warning (a finding for `metel-docs`' own workflows, and under `--strict`) unless the page lists it under `## Not drawn` with a reason. A node that says `manual` for a workflow that also runs on events, or omits it for one that only runs when dispatched, is a warning.

| Field | Value |
|---|---|
| `status` | `partial` |
| `owner` | continuous integration |
| `trigger` | `architecture-check` on `metel-docs` (docs assets only); core CI (core and the pinned docs; website skipped; warnings only); `/cut-release` (all reachable repositories, `--strict`) |
| `produces` | findings, and warnings for unlisted assets of other repositories |
| `implemented by` | `metel-docs/architecture/tools/check_operations.py`, `metel-docs/architecture/tools/check_flows.py` |
| `verified by` | `test_check_operations.py`; the real tree is clean |
| `related` | PROC-CI-002, PROC-DOCS-009, PROC-RELEASE-008 |

Partial because the assets of `metel-website` and `metel-docs-internal` are checked only where those repositories are checked out next to the others: locally and at release, not on every pull request.
