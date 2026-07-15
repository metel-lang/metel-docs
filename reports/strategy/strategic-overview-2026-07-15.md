---
id: strategic-overview-2026-07-15
title: "Language Design — Strategic Overview"
type: report
created_date: '2026-07-15'
---

# Language Design — Strategic Overview

*This document supersedes `strategic-overview-2026-07-11.md` as the dated narrative
record. For the living priorities/triggers document both this and 07-11 write back to,
see `OBJECTIVES.md`.*

*Written after pulling both repos (`metel-docs` main, `metel-core` sprint/26 +
submodule) to their current tips. Unlike 07-11, this cycle is almost entirely
**implementation**, not process — the opposite mix from the previous four cycles
combined, and a direct, welcome answer to Trigger 12 below.*

---

## What Changed

**The design/implementation gap Trigger 12 was watching just closed, hard.** All six
RFCs that reached `3-integrated` in the 07-10 cycle and sat at `impl_status:
not-started` through 07-11 are now `4-implemented`, each with a real Codeberg tracking
issue: RFC-0067a/#236, RFC-0072/#243, RFC-0078/#234, RFC-0081/#264, RFC-0082/#242 (the
sixth, RFC-0083, was superseded rather than implemented — reconciled into the
`public_value_exports` decision elsewhere, not left dangling). Alongside them, a second
cluster shipped in the same window: RFC-0060 (Aspect Impl Coherence, #238), RFC-0061
(Structural Aspect Bounds, #245), RFC-0097 (Orphan Rule for Bare-Parameter Blanket
Impls, #269), RFC-0098 (Surface Keyword Renames — `impl`→`extend`, `pub`→`public`,
`mut`→`var`), RFC-0102 (Bodyless Extend Blocks), RFC-0103 (Bodyless Aspect
Declarations, narrowed — see below), and a brand-new RFC-0106 (Optional Braces for
Empty Constructors) — accepted and implemented same-day. That is eleven RFCs moved to
`4-implemented` in roughly four days, against a backlog that sat still for the five
prior cycles this document's review log covers.

**RFC-0103 was split again, and the harder half deferred rather than rushed.** This
session's own previous work narrowed RFC-0103 to two features (bodyless aspect
declarations; struct/enum-embedded aspect lists with an obligation model) and resolved
its interaction with RFC-0096's auto-impl aspects by requiring RFC-0096 to inject
determinations into the shared aspect-implementation registry rather than exposing a
bespoke `satisfies()` query. On integration, the struct/enum-embedded list half was
judged a materially larger surface-language commitment than the bodyless-declaration
sugar — it couples type-declaration syntax to whole-graph obligation checking,
coherence, and the still-unresolved RFC-0096 interaction — and was split out into a new
RFC-0105 (Struct-Embedded Aspect Lists), left `0-draft`/deferred. **The reasoning from
this session's own registry-injection fix survived the split intact**, cited verbatim
in RFC-0105 §4 and listed as its own Unresolved Question ("is the auto-impl
registry-injection requirement on RFC-0096 the right design, or a sign this syntax is
reaching too far into implementation structure?") rather than lost or re-litigated from
scratch. RFC-0103 itself, narrowed to just the bodyless-declaration sugar, shipped as
`4-implemented` (issue #278).

**Two accepted RFCs were pulled back to under-review after integration exposed real
problems with them — the exact mechanism `3-integrated` exists for, working as
designed.** RFC-0099 (Dot-Separated Module Paths) and RFC-0100 (Constructor-Call
Construction) both moved `2-accepted` → `1-under-review` days after this session's own
review had resolved their previously-known open questions:

- **RFC-0099**: reopened specifically over "the readability cost of using `.`
  everywhere" — a concern the original design discussion never weighed once the
  disambiguation question (Option A vs. B) was settled. A narrower, context-limited
  dotted-path alternative has been added alongside the original fully-dotted proposal
  for direct comparison before any further integration work proceeds.
- **RFC-0100**: reopened over something more fundamental than a syntax detail —
  "whether general keyword arguments belong in the spec at all," given the collision
  with type ascription at call sites that this session's own review found and patched
  with a grammar-ordering fix. The reopening suggests that fix was judged a patch over
  a deeper tension rather than a real resolution.

Neither reversal is a failure of the review this session did — both are evidence the
`3-integrated` stage is catching exactly the class of problem it was built for (Trigger
8's pattern, now recurring a third time: RFC-0067a's missing value-extraction rule,
RFC-0081's dangling reference, and now these two). It does mean the surface-syntax
cluster (RFC-0098/0099/0100/0101/0102/0103/0104/0105/0106) is less settled as a whole
than it looked at the end of the 07-14 review — RFC-0098/0102/0103/0106 shipped, but the
two RFCs carrying the most semantic weight (paths, call syntax) did not.

**A real, previously-uncalled-out redundancy: issue #245 was independently reimplemented
directly on `sprint/26`, separately from this branch's own PR #270.** This branch
(`worktree-issue-245-structural-aspect-bounds`) diverged from `sprint/26` at `dc948ee`
and, earlier this session, fixed eight real bugs blocking structural aspect bounds from
working at all, opening draft PR #270. Independently, `sprint/26` itself moved forward
with a full implementation of the same RFC-0061 feature (commits `a9b49a5`/`20c81a3`,
"Implement integrated surface syntax RFCs" / "Implement integrated RFCs and bump docs
pointer") — confirmed by direct inspection: `sprint/26`'s own `stdlib/core.mtl` already
has `extend<T: Display> T[]: Display { ... }` (the array `Display`/`Clone`/`Eq` impls
this branch's own PR added, but spelled in RFC-0098's new `extend` syntax, which
post-dates this branch's fork point). **PR #270 is now very likely fully superseded**
— its fixes target the same bugs, using the now-superseded `impl` keyword spelling, and
`sprint/26`'s own version is strictly ahead of it. This wasn't visible until pulling
both repos just now; issues #245 and #269 both still show `open` in the tracker despite
their corresponding work having shipped through a different path. **Recommend closing
PR #270 and issue #245/#269 with a pointer to the commits that actually shipped the
work**, rather than continuing to rebase a now-redundant branch — flagged here rather
than acted on unilaterally, since closing a PR and abandoning a branch are exactly the
kind of visible, hard-to-reverse actions this project's own norms ask to be confirmed
first.

**A real documentation-drift instance, caught by `rfc.py check`, not yet fixed.**
`public/reference/error-codes.md` still references
`internal/rfcs/3-integrated/rfc-0060-aspect-impl-coherence.md` — a path that stopped
existing the moment RFC-0060 moved to `4-implemented` in this same batch. Separately,
`INDEX.md`'s own header counts (`103 RFCs total... 3 integrated... 32 implemented`)
were not updated alongside the batch that just landed — actual on-disk counts are 31
draft, 3 under-review (RFC-0099/0100's reversal accounts for the rise from 1),
9 accepted, 0 integrated, 39 implemented, 10 superseded, 13 refused (105 total).
`rfc.py index --check-drift` doesn't catch this specific kind of drift (it only compares
dates, not counts), which is itself worth noting — the tool's blind spot let this
particular staleness through even though the mechanism exists and is otherwise working.

---

## Design/Implementation Gap — resolved, then partially reopened

07-11 closed on: "six RFCs integrated, worked-example-checked, needing no further
design, only engineering... still `not-started`." That is no longer true — all six
implemented, tracked, done. That's the single cleanest resolution to a named trigger
this review-log has recorded. But the gap didn't stay closed at zero: RFC-0105 (deferred
mid-split) and RFC-0099/0100 (reopened) are now the gap's new occupants — smaller in
count, but RFC-0100 in particular is a bigger *design* question than an engineering one
("does this belong in the spec at all"), which is a different, arguably harder kind of
unresolved than "specified but not yet built."

---

## Honest Assessment

The four-day burst from 07-11 to now is the single largest implementation velocity
this review-log has recorded — eleven RFCs shipped against five prior cycles' combined
near-zero engineering movement on the already-ratified backlog. That's a genuine,
material answer to the meta-risk this document exists to track (design running ahead of
build). It came with two costs worth stating plainly rather than folding into the
celebration: first, the pace outran this session's own local state — the redundant
PR #270 work only surfaced because pulling both repos was the explicit ask this cycle,
not something the prior workflow was set up to catch on its own. Second, two RFCs
(0099/0100) that this session spent real review effort resolving got reopened days
later on grounds that review didn't surface — not a failure of that review (the
questions raised now are different in kind from the ones then), but a reminder that
"no open questions block it" is a snapshot, not a guarantee, and the gap between one
session's acceptance and another's integration is exactly where that kind of thing has
room to happen.

---

## References

- `strategic-overview-2026-07-11.md` — previous cycle's snapshot, the "six RFCs stuck at
  not-started" gap this cycle resolves
- `OBJECTIVES.md` — living priorities/triggers document, updated alongside this snapshot
- `internal/rfcs/INDEX.md` — current RFC state by number and cluster (header counts
  currently stale relative to disk — see "What Changed")
- `internal/rfcs/0-draft/rfc-0105-struct-embedded-aspect-lists.md` — the deferred split
  of this session's own struct/enum-embedded aspect-list work
- `internal/rfcs/1-under-review/rfc-0099-dot-separated-module-paths.md`,
  `rfc-0100-constructor-call-construction.md` — the two reopened RFCs
- `metel-core` PR #270, issues #245/#269 — likely-superseded branch/issues flagged for
  closure, not yet acted on
