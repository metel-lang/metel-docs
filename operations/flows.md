---
title: "Operations flows"
---

# Operations flows

Two pictures of the pipeline: how a change becomes part of `develop`, and how `develop` becomes a
release on the site. They are drawings of the requirements, not a second source: every node names
the requirement it depicts (`PROC-…`) and the workflow, script or command that performs it, and
`check_operations.py` fails or warns when a picture goes stale (PROC-CI-008):

- a node that cites a requirement or an asset that no longer exists;
- a workflow or slash command that no node mentions, unless it is listed under [Not drawn](#not-drawn);
- an implemented requirement that no node cites, unless it is listed under Not drawn;
- a node that says `manual` for a workflow that also runs on events, or the reverse.

Solid arrows are automated. A dotted arrow is a step a person takes.

## Implementation flow

```mermaid
flowchart TD
    issue["Issue with acceptance criteria<br/>PROC-WORK-001"]
    start["/start-issue: branch from develop<br/>PROC-WORK-001, PROC-CI-007"]
    local["pre-commit and pre-push hooks<br/>PROC-CI-006"]
    docsPr["metel-docs pull request<br/>only if the change cites a new claim, spec rule or tool<br/>PROC-CI-002, PROC-WORK-003"]
    docsCi["architecture-check.yml, check-examples.yml,<br/>check-mdx.yml, rfc-check.yml<br/>PROC-CI-003, PROC-CI-004, PROC-DOCS-010, PROC-DOCS-011"]
    docsMain["metel-docs main<br/>PROC-DOCS-001"]
    bump["bump-docs.sh moves the docs gitlink<br/>PROC-DOCS-003"]
    ship["/ship-issue: core pull request<br/>PROC-CI-007"]
    coreCi["ci.yml: test, clippy, fmt and the policy checks<br/>PROC-CI-001, PROC-CI-005, PROC-CI-008"]
    develop["rebase-merge into develop<br/>PROC-CI-007"]
    rolling["ci.yml publishes develop-latest<br/>PROC-CI-004"]
    siteCi["check-showcases.yml, plugin-tests.yml<br/>on metel-website pull requests<br/>PROC-DEPLOY-007"]
    next["next.yml rebuilds /docs/next<br/>every six hours, off by default<br/>PROC-DEPLOY-004, PROC-DEPLOY-005"]

    issue --> start --> local
    local --> ship
    local -.-> docsPr
    docsPr --> docsCi --> docsMain
    docsMain -.-> bump --> ship
    ship --> coreCi --> develop --> rolling
    rolling -. "fetched by" .-> docsCi
    rolling -. "fetched by" .-> siteCi
    docsMain --> next
```

## Release flow

```mermaid
flowchart TD
    gap["/gap-analysis on entry<br/>PROC-WORK-007"]
    work["issues of the milestone are implemented<br/>PROC-WORK-004, PROC-WORK-005"]
    integ["/milestone-integration-test<br/>PROC-WORK-007"]
    gate["/cut-release: release gate with --strict<br/>PROC-RELEASE-008, PROC-CI-005"]
    tag["fast-forward main, tag vX.Y.Z<br/>by the maintainer<br/>PROC-RELEASE-001"]
    validate["release.yml: validate-release<br/>PROC-RELEASE-002"]
    chain["release.yml: release-chain<br/>bumps the website to core's pinned docs commit,<br/>cuts the snapshot and renders the evidence on a minor<br/>PROC-RELEASE-003, PROC-RELEASE-004, PROC-RELEASE-005, PROC-RELEASE-006"]
    ghrel["release.yml: github-release<br/>PROC-RELEASE-007"]
    deploy["deploy.yml: build and deploy to staging<br/>PROC-DEPLOY-001, PROC-DEPLOY-002"]
    promote["promote.yml: manual promotion to production<br/>PROC-DEPLOY-003"]
    prod(["metel-lang.org"])
    docsOnly["publish-docs.yml: manual, a docs-only change between releases<br/>bumps the docs pointer, builds, deploys to staging<br/>PROC-DEPLOY-006"]

    gap --> work --> integ --> gate
    gate -.-> tag
    tag --> validate
    validate --> chain
    validate --> ghrel
    chain --> deploy
    deploy -. "reviewed by a person" .-> promote
    promote --> prod
    docsOnly -.-> promote
```

## Not drawn

Requirements that state a rule rather than a step, and assets that are aids, with the reason.

| Item | Reason |
|---|---|
| `/new-rfc` | starts a draft RFC; part of the RFC lifecycle, not of the delivery pipeline (PROC-DOCS-008) |
| `/review-typechecker` | a review aid with no contract (marked `local` in the inventory) |
| `PROC-RELEASE-009` | a rule about credentials that every step above obeys |
| `PROC-DOCS-002` | a rule about who pins which commit; the pins are the gitlink and website bumps drawn above |
| `PROC-DOCS-004` | generation at publish time; its release-time instance is drawn in `release-chain` (PROC-RELEASE-005) and `next.yml` |
| `PROC-DOCS-005` | a rule about generated output; its checks run inside the CI nodes |
| `PROC-DOCS-006` | hand-typed review commits; audited by the CI checks and enforced at the gate |
| `PROC-DOCS-007` | the Pending marker; checked by the CI nodes and enforced at the gate |
| `PROC-DOCS-008` | the RFC lifecycle, a flow of its own run by `rfc.py` |
| `PROC-DOCS-009` | the lifecycle of gap and limitation records, run inside the CI nodes |
| `PROC-DOCS-012` | what the spec fixture viewer embeds, a build-time property |
| `PROC-WORK-002` | which tier of verification a change gets, a rule that applies to every node |
| `PROC-WORK-003` | pairing a change with its documentation and changelog, a rule applied at the pull request |
| `PROC-WORK-006` | where bugs are scheduled, a rule about milestones rather than a step |
| `PROC-WORK-008` | when work stops and asks, a rule about the agent |
