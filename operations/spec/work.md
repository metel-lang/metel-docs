---
title: "Work management"
---

# Work management

How work is planned, started, verified and released in `metel-core`, before it reaches the release chain. Source: `metel-core/AGENTS.md`, `metel-core/ROADMAP.md`, the slash commands.

### PROC-WORK-001 — Work is an issue, a branch and a pull request, and nothing else {#proc-work-001}

GitHub issues are the task source of truth. A second concern found during the work gets its own issue and is not folded into the pull request. An issue with an unmet dependency is not started: a closed dependency whose code does not provide the contract the issue assumes counts as unmet. Work starts narrowly: read the issue, the governing spec or RFC sections, reproduce the bug or establish the missing behaviour, state the intended change and the regression test, and stop and report when there is no causal hypothesis after fifteen minutes.

| Field | Value |
|---|---|
| `status` | `implemented` |
| `owner` | engineering |
| `trigger` | any change to a repository |
| `produces` | one issue, one branch `<type>/<issue>-<slug>` from current `develop`, one pull request |
| `implemented by` | `metel-core/AGENTS.md` (Task workflow, GitHub and branch workflow), `.claude/commands/start-issue.md`, `ship-issue.md` |
| `verified by` | none automated for the shape; the `commit-msg` hook checks the message, CI checks the content (PROC-CI-001) |
| `related` | PROC-CI-007, PROC-WORK-002 |

### PROC-WORK-002 — A change is verified at the cheapest tier that can falsify it, and once at the strictest before merge {#proc-work-002}

Tier 1, after each meaningful edit: `cargo check` for the crate touched and the one new test. Tier 2, at handoff: the workspace tests and format check. Tier 3, once on the final tree: the release-mode workspace tests, clippy with warnings denied and the pedantic lints, and the format check. A defect found at Tier 3 is fixed by rerunning the focused regression first, then only the failed gate, then one complete Tier 3. A suppressed lint carries a `// clippy-allow:` reason; a bare or module-level allow is rejected by the ratchet.

| Field | Value |
|---|---|
| `status` | `implemented` |
| `owner` | engineering |
| `trigger` | edits while the work is in progress; handoff for review; the final tree before merge |
| `produces` | a regression fixture that fails without the change, and a final pass at Tier 3 |
| `implemented by` | `metel-core/AGENTS.md` (Verification tiers); CI (`test / clippy / fmt`) |
| `verified by` | CI runs the release-level gate on every pull request (PROC-CI-001); the tiers themselves are followed by the author |
| `related` | PROC-CI-001, PROC-CI-006, PROC-WORK-003 |

### PROC-WORK-003 — A language-visible change is paired with its documentation and changelog {#proc-work-003}

The specification holds current rules, not rationale or issue history; rationale lives in RFCs and ADRs. The changelog is written when the change lands, not at the end of the release. Because the changelog is a commit in another repository, a feature commit cannot contain its own entry, which is why the check is a report and not a gate.

| Field | Value |
|---|---|
| `status` | `partial` |
| `owner` | engineering |
| `trigger` | a change that alters syntax, type checking, move checking or runtime behaviour |
| `produces` | the spec and changelog entries in `metel-docs`, landed with the change |
| `implemented by` | `metel-core/AGENTS.md` (Documentation and RFC workflow); `tools/changelog-status.sh` reports unlogged commits |
| `verified by` | none enforced: the script reports and a person reads it at the release gate (PROC-RELEASE-008) |
| `related` | PROC-RELEASE-008, PROC-DOCS-001 |

### PROC-WORK-004 — Work is planned in themes, and at most one patch and the next minor release carry version numbers {#proc-work-004}

The numbered milestone with the lowest version (`vX.Y.Z`) is the release in progress: it is what the next tag will contain. While it is a patch, one further numbered milestone may exist for the next minor release (`vX.(Y+1).0`), so that the minor is planned, analysed and prepared before the patch ships. There are never two patch milestones or two minor milestones, and never a numbered milestone further out than the next minor. Every other milestone is a theme with no version number. A numbered milestone is made by renaming a theme once the version is chosen by the versioning rule; renaming keeps its issues. Issues, RFC `target` fields, spec notes, blog and release notes say planned or name the theme, and never name a version that has not been cut.

**The minor milestone does not merge ahead of the patch.** A patch never changes the language (PROC-RELEASE-001) and is tagged from `develop`, so while a patch milestone is open nothing language-visible from the minor milestone merges to `develop`, and no `metel-docs` change that only the minor needs reaches the docs commit `metel-core` pins. Allowed meanwhile: `/gap-analysis` on the minor, rewriting its issues, RFC lifecycle changes, and branches and pull requests kept open (draft) against it. When the patch tag is pushed the minor becomes the release in progress and its held pull requests merge. A bug goes to the patch milestone only if fixing it changes no accepted program (`ROADMAP.md`, Release type); otherwise it goes to the minor.

| Field | Value |
|---|---|
| `status` | `implemented` |
| `owner` | engineering |
| `trigger` | planning, and the cut of a release |
| `produces` | milestones named for capabilities, carrying a horizon (`now`, `next`, `later`, `parallel`), an outcome, an exit test and what they come after |
| `implemented by` | `metel-core/ROADMAP.md`; the GitHub milestones |
| `verified by` | none automated: `rfc.py milestones` prints the report ordered by horizon (numbered milestones first, lowest version first), and the order list is in `ROADMAP.md` |
| `related` | PROC-WORK-005, PROC-RELEASE-001 |

### PROC-WORK-005 — A theme milestone is coherent {#proc-work-005}

A theme states one outcome in a sentence, an exit test, and what it must come after. An issue that is not a necessary step goes to its nearest theme, to Backlog if it is a bug, or stays without a milestone with `needs-design` or `rfc-tracking` until it has a home. Design-settlement issues belong in decision-only themes, not mixed with implementation.

| Field | Value |
|---|---|
| `status` | `implemented` |
| `owner` | engineering |
| `trigger` | creating or editing a theme milestone, and `/gap-analysis` on entry |
| `produces` | a theme whose issues are all necessary steps to one outcome |
| `implemented by` | `metel-core/ROADMAP.md`; `.claude/commands/gap-analysis.md` |
| `verified by` | none automated |
| `related` | PROC-WORK-004, PROC-WORK-006 |

### PROC-WORK-006 — Bugs are not scheduled into themes {#proc-work-006}

A bug is observable behaviour that contradicts the spec or a documented guarantee; a known limitation or a not-yet-built feature is a feature. Severity is `soundness` (accepts a program that breaks a language guarantee; blocks the next release wherever it is found), `incorrect` (wrong result, crash, internal error, spurious rejection) or `diagnostic` (a misleading message only). A regression also carries `regression` and is fixed ahead of other bugs of its severity. A bug enters the numbered milestone only when the fix is committed for that release; a soundness bug or a regression since the last tag is committed by default. A deferred bug returns to Backlog, never to a theme. Integration findings go to Backlog, except soundness bugs and regressions, which go to the numbered milestone. A fix that changes only diagnostics or internals can ship in a patch; one that changes which programs are accepted is language-visible.

| Field | Value |
|---|---|
| `status` | `implemented` |
| `owner` | engineering |
| `trigger` | a defect is found, or an integration finding is filed |
| `produces` | an issue labelled `bug` and one `severity:*` label in the Backlog milestone |
| `implemented by` | `metel-core/ROADMAP.md` (Bugs), `.claude/commands/cut-release.md`, `gap-analysis.md`, `milestone-integration-test.md` |
| `verified by` | `/cut-release` lists the open `severity:soundness` and `regression` issues; a person reads the list |
| `related` | PROC-RELEASE-008, PROC-WORK-004 |

### PROC-WORK-007 — A milestone is analysed on entry and tested in combination before release {#proc-work-007}

Every question is batched into one report and answered before any issue is rewritten. The integration session builds the matrix of pairs of features the milestone shipped, fills the high-risk gaps with fixtures that exercise both features in one program, and files one issue per finding. Run order for a release: gap analysis, the issues, the integration session, the release gate.

| Field | Value |
|---|---|
| `status` | `implemented` |
| `owner` | engineering |
| `trigger` | `/gap-analysis <milestone>` on entry; `/milestone-integration-test <version>` after the issues are done |
| `produces` | issues that can be executed without further questions; a committed report `release-notes/integration/<version>.md` |
| `implemented by` | `metel-core/.claude/commands/gap-analysis.md`, `milestone-integration-test.md` |
| `verified by` | `/cut-release` refuses a tag without a passing report newer than the freeze (PROC-RELEASE-008) |
| `related` | PROC-RELEASE-008 |

### PROC-WORK-008 — Work stops and asks when the ground is unclear {#proc-work-008}

No destructive git command is used to obtain a clean tree, no shared history is rewritten, no merge commit is created locally, no RFC lifecycle state is changed silently, and no behaviour absent from the spec is implemented. A substantial type-system or architecture change gets an adversarial review whose job is to produce runnable counterexamples, kept separate from the implementation.

| Field | Value |
|---|---|
| `status` | `implemented` |
| `owner` | engineering |
| `trigger` | the spec is ambiguous in a way that changes behaviour; a required RFC is below integrated; a closed dependency's code does not provide the assumed contract; several architectural choices differ materially; the task needs destructive cleanup or broader authority |
| `produces` | a question to the maintainer instead of a guess |
| `implemented by` | `metel-core/AGENTS.md` (Stop conditions, Review discipline) |
| `verified by` | none automated |
| `related` | PROC-DOCS-008 |
