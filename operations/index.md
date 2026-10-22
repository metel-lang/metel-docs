---
title: "Operations Specification"
---

# Operations Specification

This specification states the durable contracts of the Metel project's own processes: how a
change becomes a checked, versioned, released, deployed and documented artifact. It is the sibling
of the Architecture Specification, which does the same for the implementation. Workflow files,
scripts and commands implement these contracts; the checks and the evidence named in each
requirement show that they hold. It describes what the project does now, and says so where a
process is partial, planned or still manual.

The specification was written while the processes it describes were being changed (metel-core
v0.14.1), so each change landed with its requirement. It has 44 requirements in five areas:

| Area | Page | Covers |
|---|---|---|
| `RELEASE` | [Release](spec/release.md) | the tag, the release chain, the GitHub Release, the release gate |
| `DEPLOY` | [Deployment](spec/deploy.md) | staging, promotion, the unreleased view |
| `DOCS` | [Documentation](spec/docs.md) | the source of truth, pins, generated artifacts, reviews, lifecycles |
| `CI` | [Continuous integration](spec/ci.md) | what each repository's CI guarantees, hooks, conventions |
| `WORK` | [Work management](spec/work.md) | issues and branches, verification tiers, milestones and themes, bugs, the milestone gates |

[Inventory](inventory.md) maps every workflow, script, hook and command to the requirements it
implements.
[Flows](flows.md) draws the implementation flow and the release flow, and is checked against the
repositories and the requirements (PROC-CI-008).

## How to read a requirement

A requirement has a stable identifier `PROC-<AREA>-<NNN>`, one statement of the contract, and a
table:

| Field | Meaning |
|---|---|
| `status` | `implemented`, `partial` (some of it is automated or enforced) or `planned` (not built; a tracking issue is named) |
| `owner` | the process or role responsible |
| `trigger` | what starts it |
| `produces` | the artifact or decision it yields |
| `implemented by` | the workflow, script, command or document that carries it out |
| `verified by` | what shows it holds: a CI job, a test, or "none automated" stated plainly |
| `related` | other requirements |

Identifiers are never reused. A requirement that stops being true is marked rather than deleted,
and the change that makes it untrue updates it.

## The repositories

| Repository | Role | CI |
|---|---|---|
| `metel-core` | the language implementation, the issue tracker and milestones, release automation. Integrates on `develop`; `main` moves only at a release | yes |
| `metel-docs` | the single public documentation source: language reference, RFCs, ADRs, the Architecture and Operations Specifications, tutorials, blog, release notes. Trunk-based `main` | yes |
| `metel-website` | the Docusaurus site and its deployment | yes |
| `metel-docs-internal` | private reports, strategy material, the versioning rule | no |

`metel-core` pins `metel-docs` through its `docs` gitlink, and `metel-website` through its own
`docs` pointer (PROC-DOCS-002). A release is the only moment the two are made to agree.

## Rules that run through the requirements

1. **Derived text is generated, a judgment is written by hand.** The implementation and
   verification inventories are derived from markers in code; whether a claim still holds is a
   hand-typed review that tools only audit (PROC-DOCS-004, PROC-DOCS-006).
2. **Generation is explicit and checking is automatic.** CI checks that committed output equals a
   fresh run; it does not rewrite content (PROC-DOCS-005).
3. **A pull request is failed by what is wrong with the change; the release is failed by what has
   gone stale.** Freshness signals are warnings on a pull request and failures at release
   (PROC-CI-005, PROC-RELEASE-008).
4. **Nothing names a version that has not been cut.** Planned work is a theme; the version is
   chosen at the cut (`ROADMAP.md` in `metel-core`).
5. **Each automated step writes to one repository with a credential scoped to it**
   (PROC-RELEASE-009). Secrets appear in this specification only by class, never by value.

## Not enforced, and known gaps

These are stated so that nobody assumes a guarantee that does not exist.

- That a requirement marked `implemented` is still true is not checked. Code, workflows and
  scripts with no requirement are caught by the discovery of `check_operations.py` (PROC-CI-008),
  but only for the repositories it can reach: `metel-website` and `metel-docs-internal` assets are
  checked when those repositories sit next to the others, locally and at release.
- The MDX check cannot see what the website's plugins create or rewrite, `sidebars.ts`, or the footer links, so a docs change that passes it can still fail the staging deploy (PROC-DOCS-011).
- Nothing sends the event that rebuilds the unreleased view (PROC-DEPLOY-005).
- The spec fixture viewer embeds fixture source in every published version (PROC-DOCS-012).
- The 60-run measurement of core CI after ADR-0064 is pending (PROC-CI-002).

## Vocabulary

- **Gate**: a check that must pass before an action, run by a person (`/cut-release`) or by a
  workflow.
- **Pin**: an exact commit recorded by a submodule pointer.
- **Snapshot**: a frozen copy of the documentation for a released minor version.
- **Staging / production**: the preview and live deployments of the site.
- **Placeholder**: `_Generated at publish._`, what `metel-docs` stores where the evidence links are
  produced at publish time.
- **Pending marker**: `> **Pending** metel-core#N`, spec text that runs ahead of the code.

## When documents disagree

The specification wins. A document that states a process contract differently is wrong and is fixed
to cite the requirement (metel-core#1528).

## Sources

`metel-core/RELEASING.md`, `metel-core/PROCESSES.md`, `metel-core/AGENTS.md`,
`metel-website/WORKFLOW.md`, the workflows of the three repositories, ADR-0051, ADR-0055,
ADR-0057, ADR-0064, `architecture/PROCESS.md` and `rfcs/PROCESS.md`. Those documents describe
operation in detail; this one states the contracts and links to them rather than restating them.
