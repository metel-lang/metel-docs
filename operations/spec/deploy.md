---
title: "Deployment"
---

# Deployment

How built documentation reaches staging and production, and how the unreleased view is published. Source: `metel-website/.github/workflows`, `metel-website/WORKFLOW.md`.

### PROC-DEPLOY-001 — A tag pushed to metel-website builds and deploys to staging, never to production {#proc-deploy-001}

The job typechecks, builds the site with the tag's docs, and deploys the prebuilt output to the hosting project's preview environment. It prints the exact command to promote the result.

| Field | Value |
|---|---|
| `status` | `implemented` |
| `owner` | website |
| `trigger` | push of a tag `vX.Y.Z` to `metel-website` (normally made by PROC-RELEASE-006; a tag pushed there by hand triggers the same pipeline) |
| `produces` | a staging deployment URL in the job summary |
| `implemented by` | `metel-website/.github/workflows/deploy.yml` |
| `verified by` | the job: typecheck and build must pass before anything is deployed |
| `related` | PROC-RELEASE-006, PROC-DEPLOY-003 |

### PROC-DEPLOY-002 — A tag is deployed only if its version is among the snapshots {#proc-deploy-002}

A minor tag must be listed. A patch tag passes if it or the minor version it patches is listed, since a patch cuts no snapshot of its own.

| Field | Value |
|---|---|
| `status` | `implemented` |
| `owner` | website |
| `trigger` | step "Confirm this release's version is in versions.json" |
| `produces` | a pass or a failed run |
| `implemented by` | `metel-website/.github/workflows/deploy.yml` |
| `verified by` | the step itself |
| `related` | PROC-RELEASE-004 |

### PROC-DEPLOY-003 — Production changes only by promoting a reviewed staging build, without a rebuild {#proc-deploy-003}

Running the workflow is the approval step, since the hosting plan has no environment protection. The artifact promoted is the one that was reviewed; it is not rebuilt from a later commit.

| Field | Value |
|---|---|
| `status` | `implemented` |
| `owner` | website |
| `trigger` | manual: `workflow_dispatch` of `promote.yml` with the staging `deployment_url` and the `tag` |
| `produces` | the staging deployment aliased to production |
| `implemented by` | `metel-website/.github/workflows/promote.yml` |
| `verified by` | the workflow requests the production domain after promoting and fails if it does not answer |
| `related` | PROC-DEPLOY-001 |

### PROC-DEPLOY-004 — Unreleased documentation is published under /docs/next, off by default {#proc-deploy-004}

It deploys only when the repository variable `NEXT_DEPLOY_ENABLED` is `true`; a manual run defaults to a dry run. It renders the architecture evidence itself, pinned to the `develop` commit it checked out, and rebuilds when docs, website or core changes. Skipping a pair already deployed is keyed on all three commits.

| Field | Value |
|---|---|
| `status` | `implemented` |
| `owner` | website |
| `trigger` | `metel-website/.github/workflows/next.yml`: every six hours, `workflow_dispatch`, `repository_dispatch` of type `docs-updated` |
| `produces` | the unreleased view, built from metel-docs `main` and metel-core `develop`, marked noindex and labelled with the commits it was built from |
| `implemented by` | `metel-website/.github/workflows/next.yml`, `metel-website/scripts/prepare-next-docs.mjs` |
| `verified by` | a unit test of the preparation script (`prepare-next-docs.test.mjs`) runs in the workflow and in PROC-DEPLOY-007 |
| `related` | PROC-DOCS-004, PROC-DEPLOY-005 |

### PROC-DEPLOY-005 — A push to metel-docs main rebuilds the unreleased documentation {#proc-deploy-005}

The receiving side exists. Nothing sends the event, so the six-hour schedule is what keeps the unreleased view current. Tracked in metel-core#1294.

| Field | Value |
|---|---|
| `status` | `partial` |
| `owner` | website |
| `trigger` | `repository_dispatch` of type `docs-updated`, sent from `metel-docs` |
| `produces` | a rebuild of PROC-DEPLOY-004 without waiting for the schedule |
| `implemented by` | receiver: `metel-website/.github/workflows/next.yml`. Sender: none yet |
| `verified by` | none |
| `related` | PROC-DEPLOY-004 |

### PROC-DEPLOY-006 — Corrected documentation reaches production without a release {#proc-deploy-006}

There is no automated path for a docs-only change (a typo, a rewritten section, a blog post) short of a version tag. Today the maintainer bumps the website's docs pointer by pull request, moves a release tag to redeploy, or builds and deploys with the hosting CLI. Tracked in metel-core#692.

The manual procedure used today, run from a machine with the hosting CLI linked to the project:

1. Merge the `metel-docs` pull request to its `main`.
2. In `metel-website`, bump the `docs` submodule pointer to that commit, run `npm run typecheck && npm run build`, and push to `main`. No docs snapshot is cut; that happens only for a minor release (PROC-RELEASE-004).
3. `npx vercel pull --environment=preview && npx vercel build && npx vercel deploy --prebuilt` produces a staging deployment, the same commands `deploy.yml` runs.
4. Read the build output under `.vercel/output/static/` to confirm the fix is in it: the hosting provider's deployment protection redirects a plain request to the staging URL to a sign-in page.
5. `npx vercel pull --environment=production && npx vercel promote <staging-url> --yes`, the promotion `promote.yml` performs.
6. Request the production site directly, which has no deployment protection, to confirm the change is live.

| Field | Value |
|---|---|
| `status` | `planned` |
| `owner` | website |
| `trigger` | manual today |
| `produces` | documentation changes published between releases |
| `implemented by` | none |
| `verified by` | none |
| `related` | PROC-DEPLOY-003, PROC-DOCS-002 |

### PROC-DEPLOY-007 — Changes to the site's own code are checked on every pull request {#proc-deploy-007}

The showcase snippets are checked by the same checker the documentation uses. The plugin tests use Node's built-in runner over `src/remark` and `scripts`.

| Field | Value |
|---|---|
| `status` | `implemented` |
| `owner` | website |
| `trigger` | pull request or push to `main` of `metel-website` |
| `produces` | a pass or fail |
| `implemented by` | `metel-website/.github/workflows/check-showcases.yml`, `metel-website/.github/workflows/plugin-tests.yml` |
| `verified by` | the workflows: the landing page snippets are real `.mtl` files run against core's rolling binary; the build-time plugins and scripts have unit tests |
| `related` | PROC-DOCS-011 |
