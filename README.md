# metel-docs

Shared Metel documentation repository.

This repository is intended to be used as a submodule in:

- `metel`
- `metel-website`

Authoritative layout:

- `public/getting-started/`: intro, quickstart, and guided tutorials
- `public/reference/`: the language reference, error codes, and spec sub-sections
- `public/release-notes/`: versioned change logs and release history
- `internal/`: implementation-facing internal docs and RFCs
- `reports/`: design reports and longer-form research notes

The old flat public-docs layout has been split into these buckets so the website can keep the public surface readable without duplicating content.

Migration safety:

- `migration/website-pre-submodule/` preserves the pre-submodule `metel-wiki/docs` working tree snapshot so no in-flight website docs edits are lost during the split.

## Branching

This repository is trunk-based: commit directly to `main`. There is no `develop`
or long-lived feature branch tier here, unlike `metel-core`.

This is a deliberate difference from `metel-core`'s branching, not an
inconsistency — the two repos carry different risk. Code merged prematurely can
break a build for everyone; a doc merged prematurely cannot, because its own
location already carries its trust level. An RFC's lifecycle stage
(`internal/rfcs/0-draft/` through `4-implemented/`, see `internal/rfcs/PROCESS.md`)
is a directory, not a flag or a branch — an unfinished RFC sitting in `0-draft/`
on `main` isn't misleading anyone; that's exactly what `0-draft` means. There is
nothing here that needs a branch to stay hidden until it's "done."

Use a short-lived branch only for a same-session, multi-file restructuring where
an easy rollback point is genuinely useful (a big RFC-cluster reorg, a directory
split) — and merge it back into `main` before ending that session, not days
later. A branch that outlives the session it was created in has already gone
stale relative to this rule: reconcile it and merge, don't let it accumulate.
This matters beyond just this repo's own history — `metel-core` bumps its `docs`
submodule pointer only from `metel-docs main` (never a feature branch, per
`metel-core/AGENTS.md`'s Release Workflow), so a doc change that isn't on `main`
is invisible to every consumer of the submodule until someone remembers to go
reconcile it.
