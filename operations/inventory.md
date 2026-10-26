---
title: "Operations inventory"
---

# Operations inventory

Every workflow, script, hook and command in the four repositories, and the requirement each one
implements. An entry marked `local` is a manual aid with no contract. The requirement cells are
judgment and are written by hand; `check_operations.py` (PROC-CI-008) discovers the assets and fails
or warns when one is missing from this table or a row names something that no longer exists.

| Repository | Asset | Requirements |
|---|---|---|
| `metel-core` | `.github/workflows/ci.yml` | PROC-CI-001, PROC-CI-002, PROC-DOCS-005 |
| `metel-core` | `.github/workflows/release.yml` | PROC-RELEASE-002 to PROC-RELEASE-007, PROC-RELEASE-009 |
| `metel-core` | `.githooks/pre-commit`, `pre-push`, `commit-msg` | PROC-CI-006 |
| `metel-core` | `.claude/commands/cut-release.md` | PROC-RELEASE-001, PROC-RELEASE-008 |
| `metel-core` | `.claude/commands/gap-analysis.md`, `milestone-integration-test.md` | PROC-WORK-007, PROC-WORK-005, PROC-WORK-006 |
| `metel-core` | `.claude/commands/start-issue.md`, `ship-issue.md` | PROC-WORK-001, PROC-CI-007 |
| `metel-core` | `.claude/commands/new-rfc.md` | PROC-DOCS-008 |
| `metel-core` | `.claude/commands/review-typechecker.md` | local: a review aid, no contract |
| `metel-core` | `tools/check_doc_examples.py` | PROC-DOCS-010 |
| `metel-core` | `tools/bump-docs.sh`, `tools/test_bump_docs.sh` | PROC-DOCS-003 |
| `metel-core` | `tools/changelog-status.sh` | PROC-WORK-003, PROC-RELEASE-008 |
| `metel-core` | `tools/clippy_allow_ratchet.py`, `check_no_semantic_name_lookup.py`, `check_no_flat_module_dir_collision.py` | PROC-CI-001, PROC-CI-006 |
| `metel-core` | `metel-frontend/src/bin/gen_grammar.rs`, `check_stdlib_docs.rs` | PROC-DOCS-005 |
| `metel-core` | `metel-interpreter/src/bin/move-check-count.rs` | local: a measurement `/milestone-integration-test` runs (PROC-WORK-007), no contract of its own |
| `metel-core` | `AGENTS.md` | process document: PROC-WORK-001, PROC-WORK-002, PROC-WORK-003, PROC-WORK-008, PROC-CI-007 |
| `metel-core` | `ROADMAP.md` | process document: PROC-WORK-004, PROC-WORK-005, PROC-WORK-006 |
| `metel-core` | `RELEASING.md`, `PROCESSES.md` | process documents; they link here (PROC-RELEASE-001). `PROCESSES.md` is a pointer to this specification |
| `metel-docs` | `.github/workflows/architecture-check.yml`, `rfc-check.yml` | PROC-CI-003, PROC-DOCS-008, PROC-DOCS-009 |
| `metel-docs` | `.github/workflows/check-examples.yml`, `.github/scripts/wait-for-core-binary.sh`, `test_wait_for_core_binary.sh` | PROC-CI-004, PROC-DOCS-010 |
| `metel-docs` | `.github/workflows/check-mdx.yml`, `tools/mdx-check-site` | PROC-DOCS-011 |
| `metel-docs` | `architecture/tools/generate_architecture_evidence.py` | PROC-DOCS-004, PROC-DOCS-006, PROC-CI-002, PROC-CI-005 |
| `metel-docs` | `architecture/tools/check_architecture.py` | PROC-DOCS-007, PROC-DOCS-009 |
| `metel-docs` | `architecture/tools/check_operations.py`, `check_flows.py` (+ tests) | PROC-CI-008 |
| `metel-docs` | `rfcs/tools/rfc.py` | PROC-DOCS-005, PROC-DOCS-006, PROC-DOCS-008, PROC-DOCS-012, PROC-CI-005 |
| `metel-docs` | `.githooks/pre-commit`, `pre-push`, `commit-msg` | PROC-CI-006 |
| `metel-website` | `.github/workflows/deploy.yml` | PROC-DEPLOY-001, PROC-DEPLOY-002 |
| `metel-website` | `.github/workflows/promote.yml` | PROC-DEPLOY-003 |
| `metel-website` | `.github/workflows/publish-docs.yml` | PROC-DEPLOY-006 |
| `metel-website` | `.github/workflows/next.yml`, `scripts/prepare-next-docs.mjs` | PROC-DEPLOY-004, PROC-DEPLOY-005 |
| `metel-website` | `.github/workflows/check-showcases.yml`, `plugin-tests.yml` | PROC-DEPLOY-007 |
| `metel-website` | `scripts/build-rfc-index.mjs`, `build-spec-index.mjs` (the `prebuild` step) | PROC-DOCS-005 (search data computed at build) |
| `metel-website` | `scripts/check-mdx-site-drift.mjs` | PROC-DOCS-011 |
| `metel-website` | `src/remark/*.mjs` | PROC-DOCS-005 (views computed at build), PROC-DOCS-007 |
| `metel-website` | `WORKFLOW.md` | process document; links here |
| `metel-docs-internal` | `reports/strategy/tools/strategy.py`, `rfc_cycle_prep.py` | local: manual strategy tooling, no CI, not part of any pipeline |
| `metel-docs-internal` | `internal/versioning.md` | the authority for the versioning rule (PROC-RELEASE-001) |
