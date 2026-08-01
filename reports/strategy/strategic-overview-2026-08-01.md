---
id: strategic-overview-2026-08-01
title: "Language Design — Strategic Overview"
type: report
created_date: '2026-08-01'
---

# Language Design — Strategic Overview

*This document supersedes `strategic-overview-2026-07-23.md` as the dated narrative
record. For the living priorities/triggers document both this and every prior cycle
write back to, see `OBJECTIVES.md`.*

*Eight days since the last review (07-24), the longest gap between cycles this document
has recorded. Every prior cycle in this series was a design-and-prose week measured
against a standing complaint that engineering wasn't following it. This one inverts
that shape almost completely: the gap was almost entirely spent building, on exactly
the two priorities this document has spent seven cycles saying were undermanned. The
right question this time is not "did depth constitute progress" (07-23's question) but
"does a week of real building change what the standing risk actually says" — and the
honest answer is: partially, precisely, and not as cleanly as the raw numbers suggest.*

---

## What actually happened, 07-24 → 08-01

Verified directly against RFC frontmatter, `REGISTRY.md`, and the issue tracker, not
reconstructed from memory:

1. **RFC-0071 (Ownership and Move Semantics) moved from `2-accepted`, one guard clause,
   to `3-integrated`, `impl_status: in-progress`, and substantially built.** A `v0.12.0`
   milestone of **23 issues, all now closed**: four are the direct RFC deliverables
   (#287 RFC-0115, #288 RFC-0116, #289 RFC-0118, #290/#291 RFC-0071 parts 1–2 of 4 —
   `Copy`/`Drop` aspects and move checking). The other **nineteen** are correctness bugs
   found and fixed *while building those four* — loop-body fixed-point analysis and
   lifting the `place` abstraction to RFC-0071 §9b's standalone-reusable bar (#291
   itself), a binding-shadow bug that erased moved state permanently (#343), `&var self`
   and by-value `self` rejected through a reference in every receiver shape (#347,
   #348), structural `extend` targets that silently accepted-and-did-nothing (#296),
   a `Drop`-body rejection discharging the RFC-0071 §9c release gate that fired mid-cycle
   when #292 slipped to v0.13.0 (#345), aspect-method resolution through a bounded
   generic reference (#334), array-intrinsic and auto-deref internal errors (#313, #314),
   an evaluator panic on nested `return`/`break`/`continue` (#321), and more.
2. **Two more records-cluster RFCs reached `4-implemented`, not just `3-integrated`.**
   RFC-0116 (Anonymous Record Types, #288) and RFC-0118 (Row Bounds, #289) are real,
   shipped code now, alongside RFC-0115 (#287). Three of the six-way RFC-0090 split are
   built; RFC-0117/0119/0120/0121 are untouched, still `0-draft`.
3. **RFC-0122 (Borrow Checking) got real content on 07-24 — granularity and
   move-vs-borrow questions answered, shared-XOR-exclusive promoted to its headline, a
   dependency direction inverted — then nothing since.** It did not reach `2-accepted`,
   the bar this document itself set for v0.12.0 on 07-24. `git log` on the RFC file shows
   four substantive commits on 07-24 and none since (the one 08-01 touch is the
   corpus-wide `mut`→`var` prose sweep, mechanical, not content).
4. **Priority 3 (brands, context parameters) is exactly where it was on 07-24.**
   RFC-0076 still `0-draft`, RFC-0113 still `1-under-review`. Zero movement.
5. **One new draft, unrelated to Priorities 1–4: RFC-0127** (Associated Functions on
   Generic Types), opened today, closing a real gap found while investigating whether
   concrete-array structural impls made sense (`Counter::new()` works for non-generic
   types; the identical construct fails `T0003` for user-defined generic ones, with
   `List::new()` only working because it is hardcoded into the scheme table). Priority-6
   flavored — genuine language-surface work, not tied to any of the four ranked clusters.
6. **v0.13.0 already has 11 open issues, and nine of them are RFC-0071/move-checker
   completions, not new backlog:** #292/#293 (RFC-0071 parts 3–4, drop order and partial
   moves), #310/#328/#330/#338/#341/#342 (migrating the fixture corpus and hardening the
   checker toward being enabled by default), #324 (a `break`/`continue`-outside-a-loop
   internal error). #353 (structural impls on tuples/records, deliberately deferred off
   v0.12.0 this cycle) is the one genuinely new item.
7. **The pre-existing Priority-5 backlog is untouched.** LSP MVP (#246–#250), operator
   aspects (#149), concurrency (#253), parser/recursion performance (#260, #261),
   overload sets (#262), `Ord`/`Eq` (#263), stdlib breadth (#258, #335), the native-
   compiler epic (#155) — same items, same count, neither shrinking nor growing.
8. **`develop` is 134 commits ahead of `origin/main`; no `v0.12.0` tag exists yet**, even
   though the milestone's own issue list is fully closed. The release-cut decision is
   administrative at this point, not blocked on outstanding work.
9. `REGISTRY.md` (regenerated today): **126 RFCs — 40 draft, 4 under-review, 8 accepted,
   1 integrated, 46 implemented, 13 superseded, 14 refused.** The "1 integrated" is
   RFC-0071, and it is the first time this document's tally has had a non-zero entry in
   that stage since Trigger 13 started asking whether `3-integrated` would stall.

---

## Honest assessment

**This is the first cycle in this document's life where Priority 1/2 engineering, not
Priority 5 engineering or pure design prose, consumed nearly all of a review period's
effort.** Every prior cycle since Trigger 20 was written (07-22) recorded the same
complaint in different words: the stated priorities and the tracker did not intersect.
For one full milestone, they did — completely. That is worth stating plainly rather than
undercutting it with a reflexive "but."

**The more precise reading, though, is not "the priority ranking worked."** Priority 5's
own backlog — LSP, performance, stdlib breadth, the operator-aspect refactor — is exactly
the same size it was on 07-22. Nothing in it was closed, and nothing in it was skipped in
favor of it. The nineteen non-RFC issues that shipped this week were not drawn from that
backlog at all; they were **found by the act of building RFC-0071**, not chosen from a
priority-ordered list. #334 (aspect dispatch through a bounded generic reference), #331
(`impl Aspect` lowering only at the top level of an annotation), #321 (an evaluator panic
on nested control flow), #313/#314 (auto-deref internal errors) — every one of these
surfaced because move-checking or the reference rules it depends on touched that code
path for the first time. **The ranking did not pull effort toward Priority 2; building
Priority 2 pulled the bug fixes along with it.** That is a better outcome than the
ranking working as designed, not a worse one — it means the two priorities are load-
bearing for each other in practice, not just in the document's stated order — but it is
a different mechanism than "we followed the list," and the next cycle should describe it
that way rather than crediting the ranking for something necessity did.

**The standing meta-risk sentence, unchanged for seven cycles and quoted verbatim every
time, is now partially false for the first time — and the imprecise version of that
correction is a real risk in itself.** The original: *"the interpreter still deep-clones
values and has no borrow checker, no allocator, no move-semantics enforcement."* As of
this week: move-semantics enforcement **exists** — real, tested, opt-in via
`--move-check`. But the interpreter's runtime **still deep-clones every value
regardless of what the checker concludes** — move checking is a static analysis layered
on top of an evaluator whose actual execution semantics haven't changed at all. Writing
next cycle's version of this sentence carelessly ("move semantics: done") would be a
false claim of exactly the kind Trigger 22 was watching for on the design side, now
showing up as a risk on the engineering side instead. The precise version is: **the
compile-time discipline exists and is enforced; the runtime discipline it describes does
not yet exist to be enforced against.** No allocator, no borrow checker: both still
completely true.

**RFC-0122 has not missed the bar this document set for it — `v0.12.0` has no tag cut
yet — but it is behind the pace that bar implied, and that should be named rather than
left to quietly not-recur.** "Reach `2-accepted` in v0.12.0, not merely accumulate prose"
was written in this same document on 07-24. It accumulated prose — real prose, with two
open questions answered — and nothing substantive since. This is not a crisis; RFC-0122
was explicitly scoped as design-only for v0.12.0, with no borrow checking shipping this
release, and the bar remains reachable before the release is actually cut. But
ten-plus days of no movement on a design-only deliverable, this close to a release
whose milestone issues are otherwise fully closed, is exactly the kind of drift this
document exists to catch when other documents show it (Trigger 16's RFC-0097
frontmatter drift, Trigger 14's RFC-0099/0100 reversions) — it should hold itself to
the same standard rather than assume there's ample runway left. **Correction, same
day:** the first draft of this paragraph said the bar was "missed." It was not — that
conflated the issue tracker's closed milestone with an actual release, which
`git log origin/main..origin/develop` and the absence of a `v0.12.0` tag would have
shown directly. Caught by the operator, not by this cycle's own verification pass,
which is itself the more important fact to record.

**A genuinely new data point for the "how vibecoded is this" question raised mid-week
outside this document's own scope, but relevant to it:** the final PR of the week
(#348's by-value-self-through-reference fix) needed a full second pass after adversarial
review found three real defects in its first commit — a silent bypass for non-place
receivers, an under-counted multi-layer-reference diagnostic, and a missing `Copy` gate
that would have wrongly rejected legal code the RFC itself already permits. None of the
three were cosmetic; all three were caught before merge, none by the author's own
first-pass verification. That is exactly the kind of implementation-quality signal worth
weighing against the trigger condition discussed for going deeper into the
implementation personally (before RFC-0122 moves from design to code) — not alarming on
its own, but a data point, and this document is where such data points should
accumulate rather than evaporate at the end of the conversation that produced them.

---

## Verified findings worth carrying forward

- **`3-integrated` does not stall, on a second and larger data point.** RFC-0071,
  RFC-0116, and RFC-0118 all passed through it and out the other side within the same
  week, matching the 07-15 cohort's pattern rather than the empty-stage worry Trigger 13
  was written to watch for.
- **The nineteen non-deliverable issues closed this week are a byproduct of building,
  not a selection from the Priority-5 backlog.** Checked by cross-referencing each
  issue's content against what it touches: every one names a code path move-checking, the
  reference rules, or the records work newly exercised. None overlaps with the untouched
  LSP/performance/stdlib backlog.
- **RFC-0122's four 07-24 commits are its last substantive ones** — verified via
  `git log` on the file directly, not inferred from its frontmatter alone.
- **v0.13.0's backlog is, by issue count, mostly Priority 2** (nine of eleven items are
  RFC-0071/move-checker completion work), which means the intersection this cycle found
  between stated priorities and the tracker is not a one-milestone artifact — the next
  milestone is already shaped the same way, before this review even asked it to be.

---

## New and updated triggers (§3 of `OBJECTIVES.md`)

1. **Trigger 20, closed — not by one issue, by an entire milestone.** The falsifier
   asked for "one tracked issue against any of Priorities 1–3." What actually happened
   is 23, all closed, mapping almost entirely to Priorities 1–2. This is the strongest
   possible resolution available to this trigger; no stronger evidence could exist
   short of a full release.
2. **Trigger 21, refuted for this cycle.** Priority 5 did not expand to fill available
   effort — its backlog is unchanged in size. But see the honest assessment above:
   the correct causal story is not "ranking constrained it," it's "necessity pulled
   effort toward Priority 2 instead, and Priority 5 was simply not visited." Watch
   whether a future cycle without an RFC-0071-shaped forcing function behaves the
   same way, or whether this week's result depended on having one.
3. **Trigger 22, closed — yes, unambiguously.** Its discriminating question was "does
   any of this RFC-text work ever produce a change the interpreter would have to
   implement to be conformant?" RFC-0071, RFC-0116, RFC-0118, and RFC-0115 all did.
   The middle state it was watching for was a real waypoint, not a comfortable
   substitute for building, at least in this instance.
4. **Trigger 24, closed — the strongest possible resolution, faster than its own
   falsifier's deadline.** "If a month passes with RFC-0116 still `0-draft` and no
   issue filed, the decomposition was a more sophisticated form of not starting." It
   reached `4-implemented` within the same week it was drafted. Decisive.
5. **New — the meta-risk sentence (§1) needs a precise rewrite, not a checkbox.**
   It has been quoted unchanged for seven cycles specifically because it stayed
   entirely true. It is now partially false (move-semantics enforcement exists) and
   partially still true (the runtime still deep-clones regardless of what the checker
   concludes). Watch whether the next cycle states that distinction precisely or lets
   an imprecise "move semantics: done" stand in its place — which would be the
   engineering-side version of exactly what Trigger 22 watches for on the design side.
6. **New — RFC-0122 is behind the pace of its self-imposed 07-24 bar ("reach
   `2-accepted` in v0.12.0"), though not yet past it since `v0.12.0` has no tag cut —
   and the drift has not been named anywhere until this entry.** Not urgent — the
   release always scoped it as design-only — but this document should hold its own
   stated bars to the same standard it applies to RFC frontmatter drift elsewhere.
   Watch whether it reaches `2-accepted` before the tag is cut, whether v0.13.0 restates
   the bar explicitly instead, or whether it drifts further unaddressed. (Corrected
   same day: originally stated as "missed"; it was not — caught by the operator.)
7. **New — a calibration data point for the (separately tracked, outside this
   document) question of implementation trust.** #348's fix needed three real
   corrections after adversarial review, none caught by the author's own first pass.
   Not itself a trigger this document owns, but worth a standing line here so the
   evidence persists across cycles rather than living only in the conversation that
   produced it.

---

## Priorities table — engineering-state column, updated

| # | Priority | Design state | Engineering state |
|---|---|---|---|
| 1 | Records / views as the structural carrier | RFC-0115/0116/0118 **`4-implemented`**; RFC-0117/0119/0120/0121 `0-draft`, untouched | **v0.12.0: #287/#288/#289 shipped** |
| 2 | Ownership enforcement and the borrow checker | RFC-0071 **`3-integrated`**, `impl_status: in-progress`; RFC-0122 `0-draft`, behind the pace of its 07-24 `2-accepted` bar but not yet missed (`v0.12.0` unshipped) | **v0.12.0: #290/#291 shipped + 19 hardening fixes; v0.13.0: #292/#293 + 6 more queued** |
| 3 | Brands and context parameters | RFC-0076 `0-draft`, RFC-0113 `1-under-review` — unchanged | not started, no issue |
| 4 | Allocators — emergent synthesis, built last | 8 RFCs `2-accepted`, complete, unchanged | deliberately not started |
| 5 | The interpreter as a feedback instrument | n/a | backlog unchanged in size (~15 open) |
| 6 | Adjacent design and demand-gated frontier | RFC-0092–0095 `0-draft` unchanged; **new draft RFC-0127** | not started |

---

## References

- `strategic-overview-2026-07-23.md` — previous dated snapshot
- `OBJECTIVES.md` — Priorities 1/2, Triggers 13/19/20/21/22/24, and the standing
  meta-risk (§1) this cycle's assessment is measured against
- `internal/rfcs/3-integrated/rfc-0071-ownership-and-move-semantics.md` — the sole
  `3-integrated` RFC, and this cycle's central engineering result
- `internal/rfcs/0-draft/rfc-0122-borrow-checking.md` — the 07-24 bar it is behind, not missed
- `internal/rfcs/REGISTRY.md` — regenerated 2026-08-01, this cycle's corpus tally
- `internal/rfcs/4-implemented/rfc-0116-anonymous-record-types.md`,
  `rfc-0118-row-bounds.md` — Priority 1's two new implemented RFCs
- `internal/rfcs/0-draft/rfc-0127-associated-functions-on-generic-types.md` — this
  cycle's one new, unranked draft
- Codeberg milestone `v0.12.0` (23/23 closed) and `v0.13.0` (0/11 closed, 9 of 11
  already RFC-0071/move-checker work)
