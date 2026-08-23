---
id: adr-0051
title: "Retire the metel-docs-internal → metel-docs Sync: One Public Source, Two Direct Submodules"
date: '2026-08-22'
status: proposed
relates: adr-0050
implements: issue #809
updated: '2026-08-23'
---

> **Implementation tracking issue filed 2026-08-23** — metel-core#809, an 8-item
> checklist mirroring this ADR's own Sequencing section directly, one item per step.
> Filed after the ADR (the reverse of `implements:`'s more common direction elsewhere in
> this corpus, where the issue predates and motivates the ADR) — recorded here for the
> same reason ADR-0049 needed its own status caught up: an ADR with real follow-through
> steps and no tracking issue is exactly how work like this goes untracked. Status stays
> `proposed`; filing a tracking issue is not acceptance.

> **Gap found and fixed 2026-08-23, mid-implementation (after step 1 landed) — the
> original 8 steps never mentioned CI.** `metel-docs-internal` has three real workflow
> files that check `public/` content directly — `check-examples.yml` (runs
> `check_doc_examples.py` against `public/getting-started`, `public/blog`,
> `public/reference`), `check-mdx.yml` (builds `tools/mdx-check-site/` against the same
> content), and `rfc-check.yml` (`rfc.py check`) — verified by reading all three
> directly, not assumed. `metel-docs` has none. Left as originally written, step 4
> (`git rm -r public/`) would delete the content these three jobs check while leaving
> them configured to check it, and nothing in `metel-docs` would replace that coverage —
> a real regression, not a cosmetic gap. Fixed by extending step 3 and step 4 below
> rather than adding a new numbered step, since it's the same underlying move (the
> tooling that verifies this content moves with the content, on the same schedule).

> **Amended 2026-08-23, after step 7 landed — `architecture/decisions/` (ADRs) also
> moves to `metel-docs`, reversing part of the Decision below.** The original Decision
> said `metel-docs-internal` keeps `internal/` and `reports/` as "the only two
> directories its own tooling or its own contributors ever needed private" — that
> sentence never accounted for `architecture/` at all (a real, if harmless, gap in the
> original Context's own directory enumeration, which named `internal/`, `public/`, and
> `reports/` but not `architecture/`). Step 7's own audit surfaced the practical cost of
> leaving it out: ADRs are ordinary engineering documentation, read and written during
> regular `metel-core` work, and `metel-core` deliberately has no second submodule to
> reach them — every process doc touched in step 7 had to say "this now means a separate
> clone" for something that used to just be a local path. Architecture decisions are not
> privacy-sensitive the way `internal/`'s versioning notes or `reports/`'s planning
> corpus are (checked directly: no ADR references credentials, private roadmap
> reasoning, or anything else that needed the private-repo boundary) — RFCs already
> established the precedent that this project's design record is public at every stage.
> Moved: 51 files, `architecture/decisions/*.md`, to `metel-docs`'s own
> `architecture/decisions/`. Kept private: `architecture/architecture.md` (interpreter
> pipeline/component-boundary notes) — not itself a decision record, and not raised as
> a problem the way the ADRs were. Every reference across all four repos updated in the
> same change (`metel-core`'s `AGENTS.md`/`README.md`/`cut-release.md`,
> `metel-docs-internal`'s own `README.md`/`architecture/architecture.md`).

> **Amended 2026-08-23, closing the loop on the previous amendment —
> `architecture/architecture.md` also moves to `metel-docs`, so `architecture/` no
> longer exists in `metel-docs-internal` at all.** The previous amendment kept this one
> file private on the reasoning that it "wasn't raised as a problem the way the ADRs
> were" — asked directly whether that was still defensible, and it wasn't: the same two
> facts that moved the ADRs apply to it unchanged. Checked directly, again: no
> credentials, no private roadmap reasoning, and (new check this pass) no links into
> `internal/` or `reports/` from within the file itself, so nothing about the move
> creates a public→private dangling reference. `metel-docs-internal` now holds exactly
> `internal/` and `reports/` — what the original Decision below said before the
> `architecture/` gap was ever found, reached for real this time rather than asserted.
> Found and fixed in the same pass, unrelated to the move itself: the file's own
> `typechecker.md`/`evaluator.md`/`testing.md` table links were bare relative paths that
> never resolved to anything in this repo (those files live in `metel-core`, under
> `metel-frontend/docs/` and `metel-interpreter/docs/`) — now absolute links to
> `metel-core`. Every reference updated in the same change (`metel-core`'s
> `AGENTS.md`/`README.md`/`cut-release.md`/`start-issue.md`, `metel-docs-internal`'s own
> `README.md`).

## Context

Today's chain: `metel-docs-internal` (private) holds `internal/`, `public/`, and
`reports/`. `metel-core` submodules `metel-docs-internal` directly, for `rfc.py` and
fixture-citation tooling — even though that tooling only ever touches `public/`
(spec citation IDs, `rfc.py`, `INDEX.md`, `COVERAGE-BASELINE.json` all live there; nothing
under `internal/` or `reports/` is read by it). On release, `metel-core`'s `release.yml`
rsyncs `metel-docs-internal/public/` into a second repo, `metel-docs` (public) —
committing only if content changed — then bumps `metel-website`'s `docs` submodule to
that new commit. `metel-website` submodules `metel-docs`, never `metel-docs-internal`.

Two copies of the same content, kept in sync by a one-way mirror step, running on a
release cadence rather than on every change.

This session hit the cost of that directly, not hypothetically. A spec-content sweep
landed real changes in `metel-docs-internal/public/` — merged, verified, done. Separately
asked to fix a website build failure, the first three reproduction attempts (plain
`npm run build`, before and after manually rsyncing the pending sync content into a
scratch clone of `metel-docs`) all reported success, because `metel-website`'s
`includeCurrentVersion: false` means only a *versioned* snapshot is ever served, and no
version had been cut against the new content yet. Reproducing the real failure required
fabricating a throwaway `docusaurus docs:version` cut by hand, in a scratch checkout,
against a sync commit that only existed unpushed on this machine — because the
push to `metel-docs` itself is still sitting blocked pending explicit sign-off (a separate,
correct guard against pushing to a public repo, but one that left the mirror stale for the
entire investigation). None of that reproduction difficulty was about the actual bug
(`rfcs/**` excluded from the site while spec pages had grown real backlinks into it — see
the companion fix, metel-website#16); all of it was about figuring out which of two copies
of the docs tree the build was even looking at.

## Decision

Keep `metel-docs-internal` and `metel-docs` as two separate repos — the hard repo
boundary is the actual privacy guarantee for `internal/`/`reports/` content, and
collapsing it into one private repo with a path-filtered checkout would trade a boundary
GitHub enforces for one a script has to keep enforcing correctly forever. But stop
duplicating the public content across that boundary:

- `metel-docs-internal` drops `public/` entirely. **Amended 2026-08-23: it also drops
  `architecture/` in full** — first `architecture/decisions/` (the ADRs), then
  `architecture/architecture.md` too (see both amendment notes above); the directory no
  longer exists in `metel-docs-internal` at all. What's left, `internal/` and
  `reports/`, really is the whole of what its own tooling or contributors need private
  — this time checked directly against the actual top-level directory listing, not
  just asserted. `metel-docs-internal` is not renamed; the name has been accurate the
  whole time, it just stops being half-true.
- `metel-docs` becomes the sole, directly-edited source for everything currently under
  `public/`. Its structure doesn't change — it already mirrors `public/` 1:1 at its own
  root — only how it gets written to does: commits land there directly, not via a mirror
  step from somewhere else.
- `metel-core`'s `docs` submodule repoints from `metel-docs-internal` to `metel-docs`.
  `metel-website`'s `docs` submodule keeps pointing at `metel-docs`, unchanged. Total
  submodule count doesn't grow: still exactly one in `metel-core`, one in `metel-website`,
  both now aimed at the same repo instead of two different ones. `metel-docs-internal`
  gains no submodule of its own — if `internal/` notes ever need to reference public spec
  content, that's a plain cross-repo link in prose, not a new dependency edge.

### `rfc.py` has to move, and it has a `reports/` dependency to untangle first

`rfc.py` currently lives at `public/rfcs/tools/rfc.py` — inside the tree that's moving.
`REPO_ROOT = Path(__file__).resolve().parents[3]` and every path it builds is
`REPO_ROOT / "public" / ...` (`RFCS_DIR`, `SPEC_DIR`, the `PATH_REF_RE` regex, and
dozens of user-facing strings in docstrings/help text/error messages). Once `rfc.py`
lives at the root of `metel-docs` instead of three levels under `metel-docs-internal`,
every one of those needs the `public` segment dropped, not just `REPO_ROOT`'s arithmetic
— this is a real find-and-rewrite pass through the script, not a one-line path change.

It also has one dependency that *doesn't* move with it: the `cycle-prep` subcommand
(`cmd_cycle_prep`, `build_cycle_state`, `diff_cycle_state`, plus the `STRATEGY_DIR =
REPO_ROOT / "reports" / "strategy"` / `SNAPSHOT_PATH` constants) writes
`reports/strategy/.cycle-snapshot.json`. `reports/` is staying in `metel-docs-internal`.

**Decided: `cycle-prep` moves out of `rfc.py` entirely**, into a small separate script
kept in `metel-docs-internal` near `reports/strategy/`. Its *inputs* are all public —
read `cmd_cycle_prep`'s body to confirm rather than assume: RFC records via
`collect_rfc_records()`, `REGISTRY.md` drift, retired-host links, RFC-vs-git-log
staleness, and `metel-core`'s open GitHub milestones are all public data or a public API
call. Only the snapshot it *writes* is private planning output — the feature was never
privileged input reaching over the repo boundary, just a public computation with a
private destination for its result. It moves as a strict subtraction from `rfc.py`,
adding no coupling back to it beyond a path argument: it needs read access to wherever a
`metel-docs` checkout lives locally to compute `records` from (its own local clone, or —
if run on a machine that already has one — `metel-core`'s `docs` submodule checkout), via
an explicit CLI argument, not a new submodule of `metel-docs-internal`'s own (consistent
with minimizing submodules — this repo gains none). Whoever implements the move decides
whether it reuses `rfc.py`'s parsing helpers by importing the module from that path, or
carries its own small duplicate of the handful of functions it needs
(`collect_rfc_records`, `registry_drift_problem`, `retired_host_references`,
`rfc_git_staleness`) — not decided here, since it doesn't affect anything outside this one
script.

### Release flow loses a step instead of gaining one

`release.yml`'s sync-then-bump becomes just bump: no more rsync-and-conditionally-commit
into `metel-docs`, since there's nothing to sync from anymore — `metel-docs` main *is*
the current public docs state. `metel-website`'s `docs` submodule pointer bump should
target the exact commit SHA `metel-core`'s own `docs` submodule is pinned to at release
time, not just "whatever's at `metel-docs` main right now" — that's a small, free
correctness improvement this consolidation makes available: it guarantees the spec
content the release's own tests ran against and the spec content the website shows for
that release are the literal same commit, not two independently-resolved reads of a
moving target.

### Public docs authoring becomes always-public, not staged

Today, editing `public/getting-started/`, `public/reference/`, `public/release-notes/`
inside the private `metel-docs-internal` repo is invisible until the next sync. After
this change, a commit to `metel-docs` is visible on GitHub the moment it's pushed —
whether or not the website has cut a version that serves it yet (the website's own
`includeCurrentVersion: false` and versioning already gate *site* visibility
independently of repo visibility). This matches the philosophy `public/rfcs/`
already operates under — RFCs at any lifecycle stage, including `0-draft`, live in the
open, per `PROCESS.md`'s "there is nothing here that needs a branch to stay hidden until
it's done" — just extended to the rest of `public/`. Named here as a deliberate
consequence, not a side effect to discover later.

## Consequences

- The exact class of bug this ADR exists to close — "which copy is the build actually
  looking at" — becomes structurally impossible, not just better-tested. There is one
  copy.
- `metel-core` drops its dependency on a private repo entirely. Its CI no longer needs
  any credential scoped to `metel-docs-internal`, and the fixture-citation tooling ends up
  pointed at exactly what it always actually used (`public/`'s content), nothing more.
- `release.yml` loses a job (the sync), not gains one — this is a net simplification of
  the release path, not a wash.
- One real one-time migration cost, spanning four repos (`metel-docs-internal`,
  `metel-docs`, `metel-core`, `metel-website`) plus `rfc.py`'s path rewrite and the
  `reports/strategy` untangling above. Sequencing below lands it in an order that
  doesn't require a synchronized flag-day across all four.
- `metel-docs-internal`'s git history for `public/` doesn't move with the content —
  it stays browsable there up to the cutover commit, but new history for that content
  continues in `metel-docs` from a fresh point, not a preserved one. Accepted: matches
  how the original `public/` → separate-repo split already treated history the first
  time (per this session's own read of `metel-docs`'s existing commit history, which
  already starts from a single "initial sync" rather than an imported history).
- Public docs content (`getting-started/`, `reference/`, `release-notes/`, not just
  `rfcs/`) becomes visible on GitHub at commit time, not release time. Accepted per the
  "authoring becomes always-public" section above — already true for RFCs, now
  consistent across all of `public/`.

## Alternatives considered

- **Merge `metel-docs-internal` and `metel-docs` into one repo**, with `metel-website`
  consuming a path-filtered/sparse checkout of just the public subtree. Rejected: this
  was the first shape proposed here, and it does eliminate the sync step too — but it
  turns "internal notes never leak" from a guarantee GitHub enforces (a private repo
  literally cannot serve content it was never pushed to) into one a checkout script has
  to keep getting right forever, and it gives `metel-website`'s CI a credential to a
  private repo it doesn't otherwise need. The user explicitly asked to keep the two
  repos separate for this reason.
- **Keep the sync, make it run on every push instead of on release** (closes the drift
  window without restructuring anything). Rejected: still two copies, still a class of
  "which one am I looking at" bug possible mid-flight, and doesn't reduce the submodule
  the user asked to minimize — it just narrows the window this session happened to fall
  into.

## Sequencing

1. Push the already-prepared, already-verified sync commit (`00ecce7` in the working
   scratch clone as of this ADR — sitting unpushed pending sign-off) to `metel-docs`
   first, so `metel-docs` main is genuinely caught up before anything is deleted upstream
   of it. This is the *last* sync `metel-docs` ever receives via the mirror mechanism.
2. Extract `cycle-prep` out of `rfc.py` into its own script kept in
   `metel-docs-internal` near `reports/strategy/`, per the decision above.
3. Move `rfc.py` (and any other `public/rfcs/tools/` scripts) to `metel-docs`'s root
   layout, rewriting every `public/`-prefixed path, regex, and user-facing string found
   during the Context section's grep pass. Verify against `metel-docs`'s own checkout,
   not `metel-docs-internal`'s. `public/rfcs/PROCESS.md` (12 occurrences) and
   `public/rfcs/INDEX.md` (11) move in the same tree and carry the same `public/`-prefixed
   references in their own prose — fix them in this same pass, not a separate one, since
   it's the same mechanical class of edit in files that move together.
   `public/rfcs/REGISTRY.md` doesn't need hand-editing: it's `rfc.py index
   --rebuild-registry` output (136 occurrences, all generated) — regenerating it with the
   fixed tool is the verification that step 3 worked, not additional work.

   **Added 2026-08-23 — the same step also moves CI, not just the tool:** create
   `metel-docs/.github/workflows/rfc-check.yml`, `check-examples.yml`, and
   `check-mdx.yml` (plus `tools/mdx-check-site/`, `check-mdx.yml`'s own dependency),
   ported from `metel-docs-internal`'s current copies with the same `public/`-prefixed
   path rewrite applied to their `run:` steps and path filters. Verify each actually
   runs green against `metel-docs`'s post-rewrite content — a workflow file that merely
   exists but has never fired is not verification. Do this *before* step 4 deletes
   `metel-docs-internal`'s content, so there is no window where the content exists
   nowhere with working CI.
4. `git rm -r public/` in `metel-docs-internal`; update its own `README.md` (already
   flagged elsewhere this session as stale/pre-rename) to describe the new two-directory
   shape. **Added 2026-08-23:** also `git rm` the three workflow files this step's
   content used to justify (`rfc-check.yml`, `check-examples.yml`, `check-mdx.yml`) and
   `tools/mdx-check-site/` — dead configuration once `public/` is gone, not something to
   leave behind failing (or worse, silently no-op-ing) on every future PR.
5. Repoint `metel-core`'s `docs` submodule at `metel-docs`; update every tooling
   reference to `docs/public/...` paths to drop the `public` segment.
6. Rewrite `metel-core`'s `release.yml`: delete the sync step, change the
   `metel-website` submodule-bump step to use `metel-core`'s own current `docs` submodule
   SHA as the target instead of resolving `metel-docs` main independently.
7. Update every process/agent-facing document across all four repos to describe the new
   layout — these are load-bearing for whoever (human or agent) works in these repos next,
   not incidental, and stale ones are exactly how this session ended up needing to
   rediscover the real chain from source instead of being told it directly. Concretely, by
   file (grep-verified during this ADR, not assumed):
   - `metel-core/AGENTS.md`: describes `docs/` as "the private `metel-docs-internal`
     submodule" and has ~20 `docs/public/...` path references across its file-location
     table and body prose (spec entry point, RFC directories, changelog, `rfc.py`
     invocation) — all need the `public` segment dropped and the private-submodule
     framing corrected to describe `metel-docs` directly.
   - `metel-core/RELEASING.md`: its own prose describes the sync step independently of
     `release.yml`'s code (¶9, ¶19-21) and documents two secrets whose scope changes —
     `DOCS_REPO_TOKEN` (read-only access to `metel-docs-internal`) is no longer needed by
     `metel-core` at all once its submodule points at `metel-docs`; `DOCS_PUBLIC_TOKEN`'s
     description ("write, `metel-docs` only") stays accurate but its purpose changes from
     "sync target" to "the only docs repo `metel-core` touches." Update the prose and the
     secrets table together, in step 6's PR, not after.
   - `metel-website/WORKFLOW.md`: remove the sync step from the documented release chain
     (the repository-split section's bullet list and the numbered release-model steps
     both describe it).
   - `metel-docs-internal/README.md`: covered by step 4 above — listed here too so this
     step's file list is complete, not to redo it.
   - `metel-docs` (public) currently has no root `README.md` or agent-instructions file at
     all. Adding one isn't required by this ADR (nothing existing needs fixing), but once
     it's the directly-edited source rather than a mirror target, it's worth a maintainer
     picking up separately — flagged here, not decided.
   - `CLAUDE.md` in each repo that has one is a one-line pointer to that repo's own
     `AGENTS.md`/equivalent (verified this session) — no separate edit needed once the
     file it points to is fixed.
8. Confirm end to end: a real fixture-citation PR pair against `metel-core` +
   `metel-docs` (replacing the `metel-core` + `metel-docs-internal` pattern used all of
   this session), and one real `docusaurus docs:version` + build in `metel-website`
   against it, the way metel-website#16's fix was verified.
