---
id: strategic-overview-2026-07-11
title: "Language Design — Strategic Overview"
type: report
created_date: '2026-07-11'
---

# Language Design — Strategic Overview

*This document supersedes `strategic-overview-2026-07-08.md` as the dated narrative
record. For the living priorities/triggers document both this and 07-08 write back to,
see `OBJECTIVES.md` — it now carries more of the ongoing state than any single dated
file, per its own convention.*

*Updated 2026-07-11: unlike every prior cycle in this series, nothing in this pass
touched language design at all. The entire cycle since 07-09 went into process and
tooling — migrating task tracking off ClickUp, closing a real enforcement gap in the
RFC lifecycle tooling, and reconciling stale cross-repo documentation. See "What
Changed" for what happened and "Honest Assessment" for whether that was the right
thing to spend a cycle on.*

---

## What Changed

Everything this cycle is process and tooling. No RFC advanced in design terms; the six
RFCs that moved did so mechanically, finishing a sweep already recorded as in-progress
by 07-10's own review-log entries.

**Task tracking fully migrated from ClickUp to Codeberg Issues.** This was scoped and
executed in one pass: inventoried the active ClickUp backlog (~37 tasks), decided to
migrate active work only (not the ~130 already-shipped/cancelled historical tasks —
their value already lives in git history), and built the migration as a script the
user runs with their own token rather than one this session could run unsupervised.
Two things emerged during execution that weren't anticipated at scoping time. First,
Codeberg's issue tracker wasn't a blank slate — it was the project's *original*
tracker (Sprint 10-15 era), abandoned mid-stream for Plane and then ClickUp, and still
held ~49 leftover issues, several of which exactly duplicated tasks about to be
migrated (including METEL-1, METEL-12, and METEL-13). All 49 were individually
checked against current RFC/ClickUp status and either closed with an explanatory
comment (stale, superseded, already-shipped, or premature-for-a-still-draft-RFC) or
reused instead of creating a duplicate. Second, Codeberg enforces a tight, undocumented
anti-spam limit on issue/comment creation — roughly 5 issue creates or 15 comment posts
per 5 minutes — which is not the general API rate limit and not something a paid tier
lifts (Codeberg is a nonprofit, donation- and membership-funded, with no premium tier
at all). The migration itself had to be run in paced batches with retry/backoff to get
through it. The six integrated RFCs' `impl_tracking` fields were then repointed from
ClickUp URLs to the new Codeberg issue URLs as a mechanical follow-up.

**The rate limit turned into a standing tool, not a one-off workaround.** Since it will
bite any future bulk operation (splitting a task into subissues, another migration),
the retry/backoff logic was generalized into `tools/tea-paced.sh` in metel-core — a
thin wrapper around any `tea` subcommand that retries specifically on a rate-limit
response and fails fast on everything else — and documented in `AGENTS.md` so it
doesn't get silently rediscovered next time.

**A real, previously-unenforced gap in the RFC lifecycle tooling closed.** The spec's
inline "Not yet implemented" callouts (added when an RFC reaches `3-integrated`, per
07-09/07-10's own additions to `PROCESS.md`) had no enforced removal step once the RFC
reached `4-implemented` — a forgettable manual edit, the same failure shape as every
other stale-doc bug this project has already caught this session (the `versioning.md`/
`PROCESS.md` lifecycle conflict, `AGENTS.md`'s wrong repo slug, RFC-0082's dead
RFC-0069 reference). Fixed two ways: the six existing callouts were normalized to
exactly one line each (previously some spanned 3-4 lines of blockquote prose), and
`rfc.py transition --to implemented` now refuses to run while a callout for that RFC
still exists, with `rfc.py check` flagging any that survive anyway. Verified end to end
in a sandbox: refuses with the exact file:line to delete, succeeds cleanly once that
single line is gone.

**Cross-repo documentation reconciled.** `metel-core/AGENTS.md` and
`metel-docs/internal/versioning.md` both carried stale, mutually contradictory
task-tracker and RFC-lifecycle descriptions (Plane-based, six-stage, a `spec_status`
field nothing else used) that predated this session's actual process and had never
been checked against each other. `AGENTS.md` was rewritten around the Codeberg Issues
design and the current seven-stage lifecycle; `versioning.md`'s conflicting section was
retired in favor of deferring to `PROCESS.md`. A repo-slug typo in `AGENTS.md`
(`metel-lang/metel` instead of `metel-lang/metel-core`) was found and fixed only after
the rewrite, during the Codeberg migration work — a small reminder that even a
same-session rewrite doesn't guarantee every fact in it gets checked.

**Self-hosting Forgejo assessed, explicitly deferred.** Raised as a way to escape the
rate limit and avoid depending on Codeberg specifically. Genuinely feasible — this very
environment runs on the kind of small VPS Forgejo needs, and Gitea/Forgejo's own
repo-migration feature would make the move a supported import rather than another
hand-rolled script. Not pursued: the reason for moving to Codeberg in the first place
was partly to eventually let outside contributors participate, and a self-hosted
instance nobody's heard of works against that goal more than the rate limit works
against it. Recorded as a real option to revisit, not closed off.

**RFC-0082's associated-type disambiguation hardened once more.** A second candidate
syntax, `<T:Aspect>::AssocType`, was proposed as a cleaner-looking alternative to the
already-rejected `<T as Aspect>::AssocType`. Checked against `grammar.md` directly
rather than by feel: `<T: Aspect>` already has exactly one meaning everywhere in Metel
(declaring a fresh generic parameter), with zero precedent for it meaning "select"
instead of "declare" — a stronger collision than the `as` spelling's two prior,
unrelated uses. Rejected, and recorded in the RFC only, not the spec, per explicit
direction to keep `declarations.md` stating only the settled design.

---

## RFC State

No lifecycle-stage transitions this cycle beyond what was already recorded in 07-10's
own review-log entries (RFC-0067a/0072/0078/0081/0082/0083 into `3-integrated`;
RFC-0067 renamed; RFC-0079/0084 refused). RFC-0080 remains the sole RFC in
`1-under-review`, unchanged. The `2-accepted` backlog remains at 6 (RFC-0008, 0036,
0037, 0060, 0061, 0071) — no further movement this cycle.

---

## The Design/Implementation Gap — unchanged, and untouched

Identical to every prior report: no borrow checker, no allocator, no move-semantics
enforcement in the interpreter. Nothing this cycle bears on it either way — this is the
first cycle in the series where that sentence is trivially true because nothing
design- or implementation-facing happened at all, not because the gap moved.

---

## Honest Assessment — was this cycle worth spending on process instead of design?

Every prior cycle in this series has had to weigh design threads against each other.
This one is different in kind: it's the first cycle to spend its entire budget on
process and tooling, touching zero design threads. That's worth assessing directly
rather than folding into the usual per-thread analysis, because it's exactly the shape
of question `OBJECTIVES.md`'s meta-risk section (§1) was written to catch.

**This wasn't the failure mode the meta-risk section warns about, but it rhymes with
it.** The specific risk named there is L3 design work piling up while L2 (already-
settled, unblocked) work sits idle — more design on top of design, while something
ready to ship doesn't. This cycle didn't add design at all, on any layer; it closed
operational debt that was actively causing problems (a task tracker in a third-party
SaaS product, contradicting the stated goal of avoiding vendor lock-in; an unenforced
manual step that had already produced a real, if minor, doc-staleness bug pattern all
session). That's a legitimate category of work, not idle process theater — but it still
means Priority 2a's Trigger 6 tension, Priority 2b's comptime scope, and Priority 3
are exactly where they were on 07-09, and RFC-0080 hasn't moved.

**Priority 3 is now the more pointed version of this question than any single thread.**
It has gone unactioned across every cycle this document's review log covers — the same
number of cycles Priority 1 sat idle before the meta-risk section named it explicitly as
the concrete instance of the risk. Nothing currently blocks Priority 3 the way L3's
still-forming state arguably justified not touching L2 early on. If the next cycle
produces a seventh consecutive "unchanged" here with no comparably concrete reason (the
way this cycle at least has one for its own stall on the RFC backlog), that would be the
real recurrence to flag — not this cycle.

**The task-tracker migration's actual payoff is still unverified.** It was justified by
two goals — avoid vendor lock-in, eventually enable outside contributors — and the
migration only proves the mechanics work, not that either goal materializes. Tracked as
Trigger 10, deliberately paired with Trigger 7's identical shape of question about
`rfc.py new`: a tool or process only pays off if it's actually used going forward, and
that's never verified at the moment it's built.

---

## Priorities

No re-ranking. Priority 1 is done (with a mechanical `impl_tracking`-URL update this
cycle). Priorities 2a/2b are re-verified unchanged, not just restated — checked directly
against `git log` rather than assumed. Priority 3's staleness is now named as its own
watch item (Trigger 11) rather than left as a silent, uncommented-on line.

See `OBJECTIVES.md` §2 for the current text of each — this section intentionally does
not duplicate it verbatim, to avoid the two documents drifting the way `versioning.md`
and `PROCESS.md` already did once this session.

---

## What Would Change This Assessment

**If the next cycle also produces zero movement on Priority 3 with no concrete reason**,
that's the pattern worth calling out explicitly, the way Priority 1's six-cycle stall
eventually was.

**If a non-maintainer files an issue or PR on Codeberg**, or if `tea-paced.sh`/the new
RFC-tooling enforcement get reused without needing to be rediscovered, that's real
evidence the migration and this cycle's tooling investment paid off — Trigger 10.

**Everything in prior cycles' "What Would Change This Assessment" sections still
applies unchanged** — none of it was resolved or superseded by a cycle that didn't
touch design at all.
