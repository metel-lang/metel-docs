---
id: strategic-objectives
title: "Strategic Objectives, Priorities, and Watch List"
type: report
status: active
last_reviewed: '2026-07-09'
---

# Strategic Objectives, Priorities, and Watch List

*Living document — updated in place, not a point-in-time snapshot, matching the convention
already used for `reports/substructural-types/*.md`. Dated strategic-overview reports
(`strategic-overview-YYYY-MM-DD.md`) remain the periodic narrative record of what was found
and decided each cycle — that value doesn't go away. What changes: this document is what
each cycle reads from and writes back to, so "what are the current priorities" and "what are
we watching for" don't have to be reconstructed by finding whichever dated file happens to be
most recent and reading its prose. Created 2026-07-09 because nothing like it existed —
`README.md` is repo layout only, and every other planning document
(`integrated-language-overview-2026-07-07.md`, `reports/implementation/roadmap-2026-07-07.md`,
the strategic-overview series itself) is a dated, point-in-time snapshot with no persistent
counterpart.*

**How to use this document, each strategic-overview cycle:**
1. Check §3's open triggers against real progress since `last_reviewed`. Mark any that fired,
   with a one-line resolution note, or that got closed for other reasons.
2. Update §2's priorities in place — not "restated unchanged," actually re-verified against
   current RFC/INDEX.md state.
3. Add any new triggers this cycle surfaced.
4. Append one line to §4's review log.
5. Update `last_reviewed` above.
6. *Then* write the dated narrative snapshot, if one is warranted — this document changing
   is not itself always enough to justify a new dated file; see `PROCESS.md`'s note on
   event-based rather than calendar-based triggers for that.

---

## 1. Long-term objectives

Seeded from `integrated-language-overview-2026-07-07.md` §1 — restate or correct this, don't
treat it as fixed by virtue of being written down first.

A systems language organized around two axes most languages fuse or omit: **where a value
lives** (allocators as first-class values) and **how a value may be used** (an affine-by-
default substructural discipline, with `Linear` at the strict end and `Copy` opt-in), with an
ordinary modern surface on top (aspects, exhaustive enums, `Perhaps`/`Result`, generics,
pattern matching), governed by **Storage Transparency**: code that doesn't allocate or borrow
carries no storage annotation, so the annotation budget concentrates exactly where a real
storage or resource decision is made.

The differentiation claim: linear-types-plus-regions is a proven neighborhood (Austral),
structural typing is proven (TypeScript) — the combination, row-polymorphic products with a
per-field ownership discipline plus concrete binding-named lifetime errors instead of abstract
`'a`, is the actual bet.

### The standing meta-risk

Stated once, here, persistently, rather than buried in whichever dated file happened to name
it — from `integrated-language-overview-2026-07-07.md` §5/§7:

> The design is roughly two major threads ahead of the implementation. The interpreter still
> deep-clones values and has no borrow checker, no allocator, no move-semantics enforcement.
> If each planning cycle keeps extending the design instead of freezing and building, the
> overreach risk compounds. The discipline to stop designing is itself the most important
> planning decision here.

**Honest note, written the same day this document was created:** the session that created
this document, `INDEX.md`, `PROCESS.md`, and the `rfc.py` tool is itself evidence bearing on
this risk, not evidence against it. It produced seven new RFCs (0089–0095), a new lifecycle
stage, and process tooling — zero lines of interpreter code changed. That work was arguably
worth doing (RFC-0055's silent duplication was real; the RFC-0063 precedent for undetected
cross-RFC conflict was real), but it is still design-and-process extension, not building, and
should be weighed as such at the next review rather than quietly exempted because it felt like
infrastructure rather than feature design.

---

## 2. Current priorities

Seeded from `strategic-overview-2026-07-08.md`, corrected for what's actually happened since.

### Priority 1 — Ratify the allocator/lifetime cluster's design

Unchanged. RFC-0067a is accepted; the rest of the sweep (RFC-0088 or amending RFC-0063
directly, retracting RFC-0069/0085/0087 — already done, see `INDEX.md` — and returning
RFC-0063/0065/0066/0067/0068/0073/0077 to accepted) is still unactioned. This remains the one
item integrated-language-overview-07-07 §3 calls genuinely critical-path: Phase 2–4
implementation needs settled text to build against.

### Priority 2a — The floor, plus tiers 1/2

**Materially changed since 07-08, not just restated.** The floor and tiers 1/2 are no longer
report-only content — they're RFC-0089 (Linear Types) and RFC-0090 (Structural Records — Rows
and Tiers), both draft. But the floor mechanism itself changed underneath them: RFC-0089 §3
now routes partial consumption through `ToRecord`/`FromRecord` (RFC-0090), not through a
bespoke struct-level mechanism.

**This creates a real, unreconciled tension worth surfacing rather than smoothing over.**
`integrated-language-overview-2026-07-07.md` §3 describes the critical-path floor as "already
satisfied by a narrow mechanism (explicit residual extraction over a closed field list — no
row kind, no unification), and must stay scoped that narrowly on purpose." The 2026-07-09
decision routes that same floor through RFC-0090's record/row machinery instead — meaning
RFC-0063 §9 item 5's deadline may now depend on RFC-0090 reaching a workable state, which is
exactly the "no row kind" independence the 07-07 framing wanted to preserve. Neither RFC-0089
nor RFC-0090 currently states this conflict explicitly. Tracked as Open Trigger 6 below.

### Priority 2b — The fuller vision

**Very unevenly developed since 07-08, not uniformly "paced" anymore.** Comptime/derive
graduated from "newly-discovered gap" to seven draft RFCs (0089–0095) with a working
registration mechanism, reconciled against a five-week-old sibling (RFC-0055) that predated
all of it. Brand-kind-unification and the row-vs-brand typestate fork have not moved at all —
still exploration-only, no RFC, exactly where `integrated-language-overview-2026-07-07.md`
§2's L3 table left them. If 2b is still meant to be one paced track, it currently isn't one —
worth deciding at the next review whether to split it the way Priority 2 itself was already
split from Priority 1.

### Priority 3 — Lower-level memory API and unsafe blocks

Unchanged. Nothing this session touched this priority's reasoning or ranking.

---

## 3. Open triggers (watch list)

Living checklist. Fired/resolved items stay listed with resolution, not deleted — the record
of what was watched for and what actually happened is part of the point.

1. ✅ **Fired, 2026-07-09.** If re-reading RFC-0080 showed it did not naturally extend to
   derive-as-codegen (only auto-trait-style structural composition) → confirmed: `Clone`'s
   derive was one hardcoded example, and RFC-0080's own Unresolved Questions section never
   mentioned a general mechanism. This directly caused the RFC-0012 → RFC-0092/0093/0094/0095
   split.
2. ⬜ **Open.** If a real scenario forces the brand-kind-unification role-crossing matrix to
   resolve and reveals identity brands and allocator/lifetime brands are more separate than
   hoped → tier 3's core premise (reusing the same tag) weakens. Untouched this session.
3. ⬜ **Open.** If Phase 3 implementation experience shows tier 1/2's drain/restore patterns
   are needed constantly in real allocator/resource code → concrete evidence for pulling
   tier 1/2 into Cluster A's sequencing sooner. No implementation has happened yet to produce
   this evidence.
4. ⬜ **Open, carried from 07-06.** Implementation pressure on Option B/C; a comparable
   language shipping a similar structural-plus-linear combination first (the one external risk
   to the "worth pursuing" verdict); RFC-0039's independent prioritization; a concrete
   user-authored-allocator need. None resolved or superseded this session.
5. ⬜ **Open, standing.** The meta-risk itself (§1): is design continuing to outpace
   implementation, cycle over cycle? Check this explicitly at every review, not just when
   something else prompts concern — it's the one risk `integrated-language-overview-07-07`
   ranked highest, and the easiest one to quietly stop tracking.
6. ⬜ **New, 2026-07-09.** Priority 2a's tension: does RFC-0089's floor genuinely need
   RFC-0090's record machinery to satisfy RFC-0063 §9 item 5, or does that dependency need
   removing to preserve the "narrow, no row kind" property `integrated-language-overview-07-07`
   wanted? Neither RFC currently states the conflict; resolve or explicitly accept it.
7. ⬜ **New, 2026-07-09.** Does `INDEX.md` + `rfc.py`'s overlap check actually prevent a
   second RFC-0055-shaped silent duplication going forward, or does it quietly fall out of use
   the way the undocumented process before it did? Check at the next review whether `rfc.py
   new` was actually run before any RFC created since.
8. ⬜ **New, 2026-07-09.** The `3-integrated` backlog (14 RFCs — see `PROCESS.md`) — does it
   start shrinking, or does it just grow alongside the draft/under-review pile? A backlog that
   only grows is a sign the new stage isn't actually being used, not just that it's early.

---

## 4. Review log

| Date | What changed | Dated snapshot |
|---|---|---|
| 2026-07-01 | (predates this document) | `strategic-overview-2026-07-01.md` |
| 2026-07-05 | (predates this document) | `strategic-overview-2026-07-05.md` |
| 2026-07-06 | (predates this document) | `strategic-overview-2026-07-06.md` |
| 2026-07-07 | (predates this document) | `integrated-language-overview-2026-07-07.md`, `reports/implementation/roadmap-2026-07-07.md` |
| 2026-07-08 | (predates this document) | `strategic-overview-2026-07-08.md` |
| 2026-07-09 | This document created, seeded from 07-08 and 07-07; RFC-0012 split into RFC-0089–0095; RFC-0055 reconciled; `INDEX.md`/`PROCESS.md`/`rfc.py` created; Priority 2a's ToRecord-floor tension surfaced (Trigger 6) | *(none yet — no dated overview written this cycle)* |

---

## References

- `strategic-overview-2026-07-08.md` — priorities and triggers this document was seeded from
- `integrated-language-overview-2026-07-07.md` — long-term objectives, the meta-risk framing,
  and the "narrow, no row kind" floor property Trigger 6 checks against
- `internal/rfcs/PROCESS.md` — the RFC lifecycle this document's priorities reference
- `internal/rfcs/INDEX.md` — current RFC state by number and cluster
