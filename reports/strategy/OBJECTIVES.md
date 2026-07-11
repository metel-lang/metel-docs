---
id: strategic-objectives
title: "Strategic Objectives, Priorities, and Watch List"
type: report
status: active
last_reviewed: '2026-07-11'
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

Originally, from `integrated-language-overview-2026-07-07.md` §5/§7:

> The design is roughly two major threads ahead of the implementation. The interpreter still
> deep-clones values and has no borrow checker, no allocator, no move-semantics enforcement.
> If each planning cycle keeps extending the design instead of freezing and building, the
> overreach risk compounds. The discipline to stop designing is itself the most important
> planning decision here.

**Sharpened 2026-07-09**, prompted directly by introducing `3-integrated` — a lifecycle stage
whose entire purpose is *more* pre-implementation design work (worked examples, spec
integration). Does that institutionalize the exact overreach this risk warns against? The flat
framing above doesn't distinguish two cases that need different answers.

- **For L3 (comptime/derive, brands, structural records) — genuinely still forming — letting
  design run ahead of implementation is the right call, not overreach, for a specific reason:**
  `comptime`/`emit`/derive registration (RFC-0092–0095) have zero footprint in
  `reports/implementation/roadmap-2026-07-07.md` — nothing exists yet to rebuild, so settling
  the mechanism's shape before writing it is not paying a build-then-rebuild cost, it's simply
  sequencing design before the only implementation that would use it.
  **Correction, 2026-07-10:** this section originally cited RFC-0092's Open Question 4 (whether
  `<T>` generics should be reinterpreted as sugar over comptime type parameters) as that
  evidence, framed as "implementing generics naively now, then unifying with comptime later,
  would likely require rebuilding the specialization mechanism's internals." That's wrong as
  stated — per the roadmap (`reports/implementation/roadmap-2026-07-07.md` L0 row), generics via
  monomorphization are **already implemented and mature**, not a future action being weighed.
  OQ4 itself says the unification is "not load-bearing for derive itself" — recommended, not
  required — precisely because it's optional, no forced rebuild follows regardless of when it's
  settled. That example actually shows the opposite pattern from the one it was cited for:
  implementation (L0 generics) already ran ahead of a later L3 design question, harmlessly,
  because the later question was scoped not to be load-bearing on the earlier build. The
  general L3 argument (above) doesn't depend on that example and still holds on its own — but
  the specific citation was wrong and is corrected rather than quietly dropped.
  `3-integrated`'s cross-checking (catching an RFC-0063/RFC-0066-style conflict before something
  is built against it) is aligned with the general argument, not opposed to it — done narrowly.
- **For L2 (the allocator/lifetime cluster, Priority 1) — already accepted, stable, and not
  entangled with L3 — the same argument does not apply, and leaving it un-actioned *is* the
  actual overreach.** Per `integrated-language-overview-2026-07-07.md`'s own dependency table,
  L2 does not depend on L3 at all. Nothing about comptime/derive's still-forming state touches
  allocator/lifetime semantics. Priority 1 has sat unactioned through five strategic-overview
  cycles (07-01 through 07-08) and still is as of this document's creation — that is the
  concrete instance of the meta-risk, not the L3 design work happening alongside it.

**Practical consequence: scope `3-integrated` narrowly** — to genuinely-coupled, still-forming
clusters (comptime/derive now; brand-kind-unification later, once it has real RFCs) — not
applied uniformly across the whole 14-RFC accepted backlog. Most of that backlog (the
aspect-system core) isn't part of active churn and doesn't need the full
worked-examples-against-siblings treatment before implementation; running it there would be
more process delaying implementation with no real conflict to catch.

**Honest note, unchanged in substance:** the session that produced this sharpening is still
evidence bearing on the risk, not against it. It spent its effort on L3/process work — seven
new RFCs, a new lifecycle stage, tooling, this document — and never once triggered Priority 1's
ratification sweep, despite nothing blocking it. That's the pattern to watch: not whether L3
design kept happening, but whether the unblocked, already-settled layer kept not getting built.

### Corollary, 2026-07-10: the interpreter is a temporary feedback mechanism, not the target structure

Follows from the meta-risk framing above and a sequencing decision already visible in the
ClickUp tracker (the METEL-123/METEL-171 split), made explicit rather than re-derived each
time it matters. The current interpreter's job is to produce real-program feedback the design
can't get any other way — not to be, or to become through careful internal refactoring, the
eventual compiler. METEL-171 already defers monomorphization strategy, ABI/calling-convention
design, MIR/CFG lowering, and closure-codegen metadata until after "the v0.8.1 elaboration
pipeline lands and the interpreter boundary is stable" — a real compiler-direction decision
this interpreter is a precursor to, not an instance of.

**The filter this gives:** interpreter-internals work falls into one of two budgets, and only
the first is worth spending on now:

- **Feedback-trustworthiness budget** — work needed so the interpreter's behavior is a
  reliable signal about the *design*, not an artifact of how the interpreter happens to be
  built. Sprint 25's SymbolId/coherence-pipeline work is this: it exists because the prior
  string-keyed dispatch was producing real bugs (METEL-185's string-fallback notes), and a
  buggy interpreter can't tell you whether a language-design question is wrong or just
  mis-executed. Worth doing regardless of whether this interpreter's structure survives.
- **Forward-structure budget** — work that only pays off if this interpreter's internals
  persist into whatever comes after METEL-171's compiler-direction decision: consolidating a
  scattered monomorphization pass, clean IR shape, ABI/calling-convention groundwork. Not
  worth spending on now — the tracker already made this call once, by scoping it into
  METEL-171 specifically to hold it out of the current sprint.

**Applied to the concrete case that raised this:** the monomorphization pass being scattered
across the codebase is real, but consolidating it belongs to the forward-structure budget
unless the scattering is itself producing incorrect programs — in which case it moves to the
trustworthiness budget and the calculus flips. Nothing surfaced so far indicates the latter.

---

## 2. Current priorities

Seeded from `strategic-overview-2026-07-08.md`, corrected for what's actually happened since.

### Priority 1 — Ratify the allocator/lifetime cluster's design

**Done 2026-07-10**, after six strategic-overview cycles unactioned (07-01 through 07-09) —
the concrete instance of the meta-risk this section warned about while it sat idle. Ratified
by amending RFC-0063 directly rather than creating RFC-0088 (the vehicle question the roadmap
left open): RFC-0063/0065/0066/0067/0068/0073/0077 are now `2-accepted`. This was not a pure
formality — a consistency pass first found RFC-0063 §9 items 1/2/5 still written up as
open/blocking, three days after `reports/implementation/roadmap-2026-07-07.md`'s Phase 0 had
already resolved them in a separate document with no sync back to the RFC itself (exactly the
drift `PROCESS.md`'s ratification/consistency step exists to catch), plus stale
"Region..." titles on RFC-0066/0068 that never got renamed when the rest of the cluster moved
to "Allocator" terminology. Both fixed before sweeping. RFC-0080 is now the only RFC left
under review, unchanged since — no movement this cycle.

**Follow-through, 2026-07-10/11:** six of this cluster's RFCs (RFC-0067a/0072/0078/0081/0082/0083)
went the rest of the way through `3-integrated`, each surfacing a real spec-vs-design gap while
writing worked examples (Trigger 8). Their `impl_tracking` fields were later repointed from
ClickUp to Codeberg Issues (#236/#243/#234/#264/#242/#235) as a side effect of the task-tracker
migration below — a mechanical link update, not a status or design change.

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

**Re-verified 2026-07-11, unchanged:** no commits touched `reports/substructural-types/`,
RFC-0089, or RFC-0090 since 07-09 (checked directly against `git log`). Trigger 6's tension
is exactly as unresolved as when it was opened.

### Priority 3 — Lower-level memory API and unsafe blocks

**Unchanged again — now flagged, see Trigger 11.** Nothing has touched this priority's
reasoning or ranking across every cycle in this document's review log (07-01 through
07-11). That's the same shape Priority 1 sat in for six cycles before the meta-risk
section (§1) named it explicitly as the concrete instance of the risk it warns about.
This document owes Priority 3 the same scrutiny, not a seventh consecutive "unchanged."

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
5. ✅ **Fired and resolved, 2026-07-10.** Priority 1 (L2, unblocked by L3) moved — see
   above. This trigger did its job: it named exactly the pattern that was actually
   happening (L3 activity masking L2 inaction) and it's what caused the check that led to
   ratification, rather than this being noticed by accident.
6. ⬜ **New, 2026-07-09.** Priority 2a's tension: does RFC-0089's floor genuinely need
   RFC-0090's record machinery to satisfy RFC-0063 §9 item 5, or does that dependency need
   removing to preserve the "narrow, no row kind" property `integrated-language-overview-07-07`
   wanted? Neither RFC currently states the conflict; resolve or explicitly accept it.
7. ⬜ **Open, still untested as of 2026-07-11.** Does `INDEX.md` + `rfc.py`'s overlap check
   actually prevent a second RFC-0055-shaped silent duplication going forward, or does it
   quietly fall out of use the way the undocumented process before it did? Still can't be
   checked — zero new RFCs were created this cycle (confirmed via `git log`), so `rfc.py new`
   has had no opportunity to be run or skipped. Keep watching at the next RFC creation.
8. 🟡 **Fired twice the same day, 2026-07-10 — now a real trend, not just one cycle.**
   First RFC-0067a/0078/0083, then RFC-0072/0081/0082, moved from accepted through
   integrated, merged into `public/reference/spec/`. Every single one of these six
   surfaced a real problem while writing the worked examples this stage requires — not
   formalities: RFC-0067a's missing value-extraction rule, RFC-0083's obsolete
   motivating example, a pre-existing `types.md`/`expressions.md` contradiction over
   `&mut` field paths, RFC-0072's stale bracket-channel examples, RFC-0081's dangling
   `#[derive]`/RFC-0012 reference, RFC-0082 amending a since-retracted RFC's dead
   concept and mislabeling the allocator aspect. The pattern holding across two
   consecutive batches is itself evidence this stage is doing its job, not a fluke.
   Still open: 6 RFCs remain in the backlog (RFC-0008, 0036, 0037, 0060, 0061, 0071).
   RFC-0079/0084 left the backlog by refusal, not integration — worth noting that path
   exists too. Keep watching whether the remaining 6 keep moving or the pace stalls.
   **Update, 2026-07-11: the pace stalled this cycle** — none of the remaining 6 moved, and
   RFC-0080 (the sole under-review RFC) didn't either. Not neglect: the cycle's effort went
   into closing a gap the *previous* integration batch exposed (the spec's "Not yet
   implemented" callouts had no enforced removal step — now fixed, see review log). Still,
   a stall is a stall; if the next cycle also produces no movement on the remaining 6 with
   no comparably concrete reason, that's the pattern worth calling out, not this one alone.
9. ⬜ **New, 2026-07-10.** Watch for the "interpreter is temporary" corollary (§1) being
   misapplied to justify skipping *feedback-trustworthiness* work under cover of "it's all
   throwaway anyway" — e.g. a real dispatch bug shrugged off instead of fixed. That's a
   misuse of the corollary, not an instance of it; the corollary only excuses
   forward-structure work (§1), never correctness.
10. ⬜ **New, 2026-07-11.** Task tracking moved from ClickUp to Codeberg Issues, explicitly to
    avoid vendor lock-in and eventually enable outside contributors. Neither payoff is
    verified yet — the migration only proves the mechanics work. Watch for: any issue or PR
    filed by a non-maintainer; whether `tea-paced.sh` and the RFC-tooling enforcement added
    this cycle actually get reused next time rather than being one-off tooling nobody revisits
    (the same question Trigger 7 already asks about `rfc.py new` — this is that question's
    sibling for the tracker migration).
11. ⬜ **New, 2026-07-11.** Priority 3 (lower-level memory API and unsafe blocks) has now gone
    unactioned across every cycle in this document's review log (07-01 through 07-11) — the
    same shape Priority 1 sat in for six cycles before §1's meta-risk section named it
    explicitly. Unlike Priority 1, nothing currently blocks Priority 3 from being picked up
    either. If the next cycle again produces no movement here with no L3-shaped reason (the
    way this cycle's stall on Trigger 8 had one), that's the concrete recurrence of the
    meta-risk this document exists to catch.

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
| 2026-07-10 | Corrected the RFC-0092/generics citation in the meta-risk section (generics were already implemented, not a future action); RFC-0084 reversed to keep `[T; N]`/`[expr; N]`; added the "interpreter as temporary feedback mechanism" corollary (§1, Trigger 9) after a ClickUp check found no sprint task consolidating the scattered monomorphization pass | *(none yet)* |
| 2026-07-10 | Priority 1 done: allocator/lifetime cluster (RFC-0063/0065/0066/0067/0068/0073/0077) ratified to accepted after a consistency pass fixed real drift (RFC-0063 §9 items 1/2/5 out of sync with the roadmap's Phase 0 decision; stale "Region..." titles on RFC-0066/0068). Trigger 5 fired and resolved. | *(none yet)* |
| 2026-07-10 | RFC-0067a/0078/0083 became the first RFCs to reach `3-integrated`, merged into `public/reference/spec/`; each surfaced a real problem while writing worked examples (Trigger 8 partially fired) | *(none yet)* |
| 2026-07-10 | RFC-0072/0081/0082 followed the same day, merged into `declarations.md`; RFC-0067/0079/0084 also handled (renamed, refused, refused respectively). Trigger 8 fired again — 6 RFCs left in the `3-integrated` backlog (was 14) | *(none yet)* |
| 2026-07-10/11 | RFC-0082's associated-type disambiguation hardened further: a second candidate syntax (`<T:Aspect>::AssocType`) considered and rejected against `grammar.md`, recorded in the RFC only (not the spec) per explicit direction. `metel-core/AGENTS.md` and `metel-docs/internal/versioning.md` reconciled (both had stale, contradictory task-tracker/RFC-lifecycle docs); `AGENTS.md`'s repo-slug typo (`metel-lang/metel` → `metel-lang/metel-core`) fixed. Task tracking fully migrated from ClickUp to Codeberg Issues: 49 pre-existing stale/duplicate Codeberg issues reconciled (closed with explanatory comments or reused instead of duplicated), 34 active tasks migrated, 10 labels + 1 milestone created, 6 integrated RFCs' `impl_tracking` repointed to the new issue URLs. Self-hosting a Forgejo instance assessed as feasible (this environment's own Hetzner box could run it) but explicitly deferred — Codeberg's discoverability for future outside contributors outweighs full control, for now. `internal/rfcs/tools/rfc.py` gained enforcement for the spec's "Not yet implemented" callouts: required to be one-liners, `transition --to implemented` now refuses to run while one still exists for that RFC, `check` flags any that survive anyway — closing a real gap the previous integration batch left open. Triggers 7/8 updated (both still open, for different reasons); Triggers 10/11 opened. | `strategic-overview-2026-07-11.md` |

---

## References

- `strategic-overview-2026-07-08.md` — priorities and triggers this document was seeded from
- `strategic-overview-2026-07-11.md` — this cycle's dated narrative snapshot
- `integrated-language-overview-2026-07-07.md` — long-term objectives, the meta-risk framing,
  and the "narrow, no row kind" floor property Trigger 6 checks against
- `internal/rfcs/PROCESS.md` — the RFC lifecycle this document's priorities reference
- `internal/rfcs/INDEX.md` — current RFC state by number and cluster
- `metel-core/AGENTS.md` — Codeberg Issues task-tracking design (Trigger 10)
