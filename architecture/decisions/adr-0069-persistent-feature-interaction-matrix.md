---
id: adr-0069
title: "The Feature-Interaction Matrix Is Persistent and Computed From Fixtures"
date: '2026-11-19'
status: accepted
implements: metel-core#2082
---

## Context

`/milestone-integration-test` built an N×N interaction matrix from scratch for each milestone, from only the
features that milestone shipped, and judged each cell by hand. Two things went wrong with that.

- **New-versus-old pairs went unchecked.** A new rule meeting a v0.13 closure rule or a v0.14 narrowing rule was
  exercised only when a new fixture happened to include the old feature. That is where regressions hide.
- **The risk table was hand-maintained and incomplete.** The subsystem table that marked a pair "high-risk" missed the
  derivation and flow features of v0.16.0. Nothing recorded partial coverage, so a pair was either filled or forgotten.

The v0.16.0 session computed a 24-feature, 276-pair matrix with a throwaway script (117 pairs covered, 41 high-risk
gaps). It also showed that spec rule ids already link features to fixtures: every integration fixture cites the rules it
exercises in `spec = [...]`.

## Decision

### 1. A committed feature registry

`tools/feature-matrix/registry.toml` in metel-core lists one entry per language-visible capability: an id, a name, the
release that introduced it, subsystem tags, the spec rule ids it owns, and its sources (RFCs, issues, changelog
entries). It is seeded from implemented-RFC coverage and the release changelog, and each release adds only its own
rows. It lives in metel-core because coverage is computed from the fixtures and the gate belongs to `/cut-release`.

### 2. Coverage is computed, not judged

A pair (A, B) has evidence when some fixture cites a rule of A and a rule of B. The cell score is the share of the two
features' rules that such fixtures cite. A cell with no such fixture is `open`, a cell with a partial score is
`partial`, and a full score is `covered`. A fixture that is removed or retagged reopens its cells with no further
action, because the grid is recomputed on every run. The criterion is the fixture's spec tags and not a per-pair
annotation, so a fixture needs no extra metadata to count.

### 3. Four cell states

`covered`, `partial` and `open` are computed. `n/a` (with a reason) and `deferred` (with a reason and a GitHub issue
URL) are set by hand in `tools/feature-matrix/states.toml`, and a hand-set state is stable when fixture evidence
changes. Partial coverage is therefore explicit, and an uncovered pair is either covered, deliberately excluded, or
tracked.

A third hand-set form, the **bulk deferral**, exists for the bootstrap: an entry in `states.toml` defers every
still-`open` cell of one tier for one release to a single tracking issue, with a reason. It applies only to cells that
are still open, so fixture evidence always wins and a cell leaves the deferral as soon as a fixture covers it. It is
reported separately ("bulk-deferred") and its issue is required, so the backlog stays visible and countable.

### 4. Risk tiers

A pair is **Tier A** when its features share a subsystem tag, **Tier B** when their subsystems are adjacent (the
adjacency list is in the registry), and **Tier C** otherwise.

### 5. The gate

The gate is scoped to the release under test: its new features against the whole registry, which is O(N) per
release and not O(N²). Old-by-old cells stay out of scope. It fails when any of these holds, and its thresholds
are the registry's `[gate]` table, which a release may raise and never lower:

- **open-tier-a** — a Tier A cell in a new feature's row is `open`. A bulk deferral excuses this rule, only for
  the release it names.
- **joint-fixtures** — a Tier A pair among the release's own features has fewer than `min_joint_fixtures` (2)
  joint fixtures. One fixture can be a coincidence.
- **tier-b-evidence** — a Tier B pair among the release's own features is `open` (`tier_b_open_fails`). Tier B
  pairs in the rest of the registry, and Tier C, are reported and never gate.
- **feature-floor** — a new feature has evidence in fewer than `feature_tier_a_floor` (50%) of its Tier A pairs.
  `n/a` pairs do not count against it, and a bulk deferral is not evidence.
- **expired-bulk** — a `[[bulk]]` deferral of an earlier minor release still has open cells. Without this a
  deferral outlives its release and the debt silently leaves the gate.

`partial` cells are reported and never block: complete rule coverage of every pair is not a reasonable bar.
A rule-coverage floor per pair was considered and left out for now; it rewards citing more rules, which the
script cannot check, and its combined denominator penalises features that own many rules.

### 6. Tooling and commands

`tools/feature_matrix.py <release>` prints the baseline, the gate scope and the verdict, and `--details` and
`--blockers` list cells. Its self-test (`tools/test_feature_matrix.py`) runs in the "tools self-tests" CI job.
`/milestone-integration-test` reads the registry and the script, adds the milestone's features to the registry, and
reports the delta in `integration/<version>.md`. `/cut-release` Step 1b runs the gate verdict.

### 7. Published metrics

Each release publishes its coverage. `feature_matrix.py <release> --json` is saved next to the integration report
as `<version>.metrics.json`, the baseline a later release diffs against. `--table` produces the markdown table
(tiers for the release's own features and against older ones, rule coverage, gate verdict). The report carries it
with per-feature rows, and the changelog's `## <version>` section carries the compact one between
`feature-matrix` markers. The GitHub Release body is sourced from that section. `/cut-release` runs
`--check-table`, which fails on a missing or stale table.

## Consequences

- The first release to use the registry inherits every open Tier A cell of its new features. v0.16.0 was held to
  the full gate: its own pairs were closed with fixtures (19 first, then 40 more violations of the stricter rules),
  and 82 new-versus-old Tier A pairs are bulk-deferred to metel-core#2086. The deferral expires at v0.17.0 and is
  removed when it is swept.
- A fixture's rule tags are claims the script cannot verify. The gate counts them, so a threshold makes over-tagging
  more tempting, and re-reviewing the tags of new fixtures is part of the integration session.
- A feature without spec rule ids has no computable coverage. The script reports such features. A registry seed entry
  that cites no rule is a defect to fix, not an exemption.
- Spec rule ids become the join key between features and fixtures. Renaming or retiring a rule id breaks coverage
  for the features that own it, and the script rejects unknown ids.
- The matrix measures fixtures that cite rules of both features. It does not measure the quality of the fixture.

## Alternatives considered

- **Keep the per-milestone matrix.** Cheapest, and it keeps the old-versus-new blind spot.
- **A full N×N gate.** Quadratic work per release and mostly old-by-old cells; rejected for O(N) gating.
- **Per-pair annotations instead of spec-tag inference.** More precise, and every fixture would carry extra
  metadata that goes stale; rejected.
- **Block on `partial` cells.** Rejected in section 5: it makes the gate unusable and ignores the recorded state.
