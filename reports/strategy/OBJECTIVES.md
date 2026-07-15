---
id: strategic-objectives
title: "Strategic Objectives, Priorities, and Watch List"
type: report
status: active
last_reviewed: '2026-07-15'
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

A systems language whose public face is **allocator-aware storage and resource control**, but
whose real semantic substrate is lower-level: **structural shape**, **per-field multiplicity**,
**brand identity/provenance**, and **binding-named lifetime validity**. Allocators remain
central to the language's identity, but they are the first major *synthesis* of that substrate,
not the substrate itself. The ordinary modern surface (aspects, exhaustive enums,
`Perhaps`/`Result`, generics, pattern matching) still matters, but it is not the differentiator.

The differentiation claim is therefore slightly sharper than the earlier allocator-first
framing: the bet is not merely "allocators as first-class values," but **fine-grained resource
semantics over structured values** — row-shaped products with per-field ownership discipline,
identity where plain structure is not enough, and concrete lifetime diagnostics named after real
bindings rather than abstract `'a`. Allocator semantics remain the flagship integrative use
case that justifies this machinery, rather than the only low-level concept the language is
"about."

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
migration below — a mechanical link update, not a status or design change. **All six are still
`impl_status: not-started` as of 2026-07-11** — fully specified, ratified, worked-example-checked,
and zero engineering has started on any of them. Unlike Priority 3, this needs no scoping, only
building — see Trigger 12 and `strategic-overview-2026-07-11.md`'s "Design/Implementation Gap"
section, which named this explicitly after an earlier draft of that snapshot missed it.

**Resolved 2026-07-15.** All five still-tracked RFCs (RFC-0067a/#236, RFC-0072/#243,
RFC-0078/#234, RFC-0081/#264, RFC-0082/#242 — RFC-0083 was superseded rather than
implemented, reconciled elsewhere) are now `4-implemented`. Trigger 12 fired and is
resolved — see `strategic-overview-2026-07-15.md`. This priority's follow-through is
done; watch instead whether the *next* `3-integrated` batch (currently empty — 0 RFCs
at that stage as of 07-15) repeats the same not-started stall before being fully
built, per the new Trigger 13 below.

### Priority 2 — The substrate for fine-grained resource semantics

**This is now the main medium-term design priority.** The project should stop treating the
allocator cluster as the deepest layer. The lower-level work that needs the most clarity is:

- **Structural types / records** as the carrier for non-coarse resource reasoning.
- **Per-field multiplicity** so ownership is not only a whole-value property.
- **Brand semantics** for identity/provenance wherever plain structure is insufficient.
- **Lifetime validity** in its narrower but essential role: borrow scope, exclusivity, and
  concrete diagnostics.

This framing demotes the old typestate question from "central fork in the roadmap" to a
secondary stylistic consequence unless implementation pressure proves otherwise. The core design
question is not "rows vs brands for typestate"; it is whether the language has a coherent
substrate for structured, fine-grained resource semantics at all.

**Concrete consequence:** RFC-0089 (Linear Types) and RFC-0090 (Structural Records — Rows and
Tiers) are not just optional future polish. They sit directly in this substrate, as does the
still-unwritten brand-unification work. The unresolved issue is not merely that RFC-0089 now
depends on RFC-0090's `ToRecord`/`FromRecord` mechanism — it's that this dependency is exactly
where the project must decide whether the "narrow floor" story from
`integrated-language-overview-2026-07-07.md` still holds or has been deliberately revised.
That remains Trigger 6 below, but it now matters as a substrate-shaping decision, not just as a
local RFC dependency question.

### Priority 3 — Allocator semantics as the flagship synthesis

Allocator semantics remain central to the language's identity, but they are **not** currently
the most primitive thing to prioritize directly. They should be treated as the first major
integration target that proves the substrate above is coherent: allocators exercise structure,
multiplicity, identity/provenance, and borrowing all at once. In that sense they stay more
important strategically than the current implementation order alone would suggest.

**What changes here is sequencing, not importance.** If allocator values are ultimately
structured, branded resources with borrowing rules and storage-transparency ergonomics on top,
then parts of the allocator cluster are downstream presentation and synthesis work rather than
foundational semantics. That does **not** reduce their importance to the language's public
identity. It does mean the medium-term planning question is "what substrate do allocator
semantics need?" before "which allocator-facing RFC lands next?"

### Priority 4 — Active adjacent design, and deferred frontier work

Comptime/derive remains active design work with real internal motion (RFC-0092–0095), but it is
not the same priority shape as the substrate above. It should continue, but not be conflated
with the structural/brand/lifetime foundation or with allocator semantics.

By contrast, the lower-level unsafe/custom-allocator layer remains **demand-gated frontier
work**, not a neglected near-term priority. Both
`integrated-language-overview-2026-07-07.md` and `reports/implementation/roadmap-2026-07-07.md`
still classify it that way: it gates user-authored custom allocators, not the four stdlib
allocators or the allocator/lifetime MVP, and RFC-0026 still predates the split model and
needs a rewrite before it is actionable. Promotion signal unchanged: a concrete need that
host-implemented stdlib allocators cannot satisfy.

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
   hoped → the emerging substrate story weakens at exactly the point where it wants brands to
   carry cross-cutting identity/provenance. Still untouched.
3. ⬜ **Open.** If real allocator/resource implementation shows partial-consumption and
   drain/restore patterns are needed constantly, not exceptionally → that is evidence the
   substrate priority above is correct, and that structural/per-field machinery belongs closer
   to the implementation path rather than parked as a later tower. No implementation has
   happened yet to produce this evidence.
4. ⬜ **Open, carried from 07-06.** Implementation pressure on Option B/C; a comparable
   language shipping a similar structural-plus-linear combination first (the one external risk
   to the "worth pursuing" verdict); RFC-0039's independent prioritization; a concrete
   user-authored-allocator need that would promote the unsafe/custom-allocator frontier. None
   resolved or superseded this session.
5. ✅ **Fired and resolved, 2026-07-10.** Priority 1 (L2, unblocked by L3) moved — see
   above. This trigger did its job: it named exactly the pattern that was actually
   happening (L3 activity masking L2 inaction) and it's what caused the check that led to
   ratification, rather than this being noticed by accident.
6. ⬜ **New, 2026-07-09; reframed 2026-07-15.** Does the substrate for fine-grained resource
   semantics genuinely require RFC-0090's record machinery for RFC-0089's floor, or does that
   dependency need removing to preserve the "narrow, no row kind" property
   `integrated-language-overview-07-07` wanted? Neither RFC currently states the conflict;
   resolve or explicitly accept that the earlier framing has changed.
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
   **Update, 2026-07-15: emphatically un-stalled.** RFC-0060 and RFC-0061 both moved
   through and shipped as `4-implemented` (issues #238/#245 respectively); RFC-0071 and
   RFC-0037/0036 (already implemented per the 07-13 entry above) are also done.
   RFC-0008 remains the one genuinely open item in this original list, still gated on
   `dyn Aspect` having no consumer.
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
11. ✅ **Re-evaluated and closed, 2026-07-15.** The analogy this trigger drew to Priority 1
    does not hold. Priority 3 is explicitly Stage C / demand-gated in both the integrated
    overview and the implementation roadmap: it blocks user-authored custom allocators, not
    the MVP allocator/lifetime path, and RFC-0026 still predates the split model and needs a
    rewrite before it is actionable anyway. No concrete custom-allocator demand has appeared.
    Keep the signal, but in the form those source docs already named: re-promote this work if
    a real user-authored allocator need emerges that host-implemented stdlib allocators cannot
    cover.
12. ✅ **Fired and resolved, 2026-07-15.** The six RFCs that reached `3-integrated`
    (RFC-0067a/0072/0078/0081/0082/0083) all moved to `4-implemented` in the four days
    since 07-11 — the fastest resolution any trigger in this document has had. Five have
    real tracking issues (#236/#243/#234/#264/#242); RFC-0083 was superseded rather than
    implemented. This is the single cleanest piece of evidence yet that naming a stall
    explicitly (rather than letting "unchanged again" accumulate silently) is what gets
    it moved — the same shape as Trigger 5's resolution for Priority 1 itself.

13. ⬜ **New, 2026-07-15.** With Trigger 12 resolved, `3-integrated` is now empty (0 RFCs)
    for the first time since the stage was created — the batch that just shipped went
    straight from accepted/draft to implemented without sitting at `3-integrated` first
    in most cases (RFC-0098/0102/0103/0106), unlike the RFC-0067a-cluster's own path.
    Watch whether that's the new normal (worked-examples-then-immediate-build, collapsing
    the stall this document exists to catch) or whether the next batch of accepted RFCs
    sits at `3-integrated` again with no engineering following — the condition Trigger 12
    was originally watching for.

14. ⬜ **New, 2026-07-15.** RFC-0099 (Dot-Separated Module Paths) and RFC-0100
    (Constructor-Call Construction) both reverted `2-accepted` → `1-under-review` during
    integration, on grounds neither this document's 07-11 snapshot nor the review that
    accepted them had surfaced (RFC-0099: readability cost of `.` everywhere; RFC-0100:
    whether general keyword arguments belong in the spec at all, not just the
    ascription-collision fix already found). Watch whether either resolves cleanly next
    cycle or whether RFC-0100 in particular gets scoped down or refused — "does this
    belong at all" is a design-level reopening, not an engineering gap, and the pattern
    of accepted-then-reopened is new; if it recurs with a third RFC, that's evidence
    `2-accepted`'s own bar ("no more open questions block it") is being called too early
    somewhere in this project's actual practice, not just in this one pair.

15. ⬜ **New, 2026-07-15.** `metel-core` PR #270 (issue #245's own WIP branch) was found,
    while pulling both repos this cycle, to be fully superseded by direct commits on
    `sprint/26` (`a9b49a5`/`20c81a3`) that independently reimplemented the same feature
    using the newer RFC-0098 `extend` syntax. Neither PR #270 nor issues #245/#269 have
    been closed yet. Watch whether this gets cleaned up next cycle, and — more
    importantly for process — whether a cheap, repeatable check ("does an open PR's
    branch still contain work not already on the target branch") gets added anywhere,
    since this instance was only caught by an explicit pull-and-compare, not by any
    standing mechanism.

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
| 2026-07-11 | Correction to the same-day snapshot above: it originally said the design/implementation gap was untouched this cycle, missing that the six RFCs integrated into the spec (RFC-0067a/0072/0078/0081/0082/0083) are all still `impl_status: not-started` — a real, itemized widening of the gap, and the cheapest available implementation work in this document since none of it needs further design. Trigger 12 opened; Priority 1's follow-through note and the dated snapshot's "Design/Implementation Gap" and "Honest Assessment" sections amended. | `strategic-overview-2026-07-11.md` (amended) |
| 2026-07-15 | Both repos pulled to current tips (`metel-docs` main, `metel-core` sprint/26 + submodule). Eleven RFCs shipped `4-implemented` since 07-11 (RFC-0067a/0072/0078/0081/0082 + RFC-0060/0061/0097/0098/0102/0103/0106 — RFC-0083 superseded instead); Trigger 12 fired and resolved, Trigger 8 un-stalled. RFC-0103 split again: bodyless-declaration half implemented, struct/enum-embedded-list half (this session's own prior obligation-model/auto-impl-registry-injection work) deferred into new draft RFC-0105 with that reasoning preserved. RFC-0099/0100 reverted accepted → under-review post-integration over design questions review hadn't surfaced (Trigger 14, new). Found `metel-core` PR #270/issues #245/#269 fully superseded by direct `sprint/26` commits, not yet closed (Trigger 15, new) — flagged, not acted on. Found and named, not yet fixed: a dangling `3-integrated` path reference in `public/reference/error-codes.md` and stale RFC-count header in `INDEX.md` (real drift `rfc.py index --check-drift`'s date-only comparison doesn't catch). | `strategic-overview-2026-07-15.md` |
| 2026-07-15 | Fixed the dangling RFC-0060 path references in `public/reference/error-codes.md` and the dated 07-15 strategic overview; `rfc.py check` is clean again. Re-evaluated Priority 3 against the integrated overview and implementation roadmap: closed Trigger 11 as a false analogy to Priority 1, and reframed unsafe/custom-allocator work as demand-gated frontier scope rather than neglected near-term work. | *(none yet)* |
| 2026-07-15 | Split RFC indexing into two roles: generated `internal/rfcs/REGISTRY.md` is now the authoritative state inventory, while `internal/rfcs/INDEX.md` is explicitly curated/thematic only. `rfc.py check` and `rfc.py index --check-drift` now enforce that split mechanically instead of relying on `INDEX.md`'s old date-only drift check. | *(none yet)* |
| 2026-07-15 | Rewrote the medium-term priority narrative around a substrate-first model: structural types, per-field multiplicity, brand semantics, and lifetime validity are now the main low-level design priority; allocator semantics are kept central to language identity but reframed as the flagship synthesis built on that substrate; typestate is explicitly demoted to a secondary stylistic consequence unless implementation pressure proves otherwise. | *(none yet)* |

---

## References

- `strategic-overview-2026-07-08.md` — priorities and triggers this document was seeded from
- `strategic-overview-2026-07-11.md`, `strategic-overview-2026-07-15.md` — dated narrative
  snapshots, most recent last
- `integrated-language-overview-2026-07-07.md` — long-term objectives, the meta-risk framing,
  and the "narrow, no row kind" floor property Trigger 6 checks against
- `internal/rfcs/PROCESS.md` — the RFC lifecycle this document's priorities reference
- `internal/rfcs/REGISTRY.md` — exact current RFC state by stage/path/status
- `internal/rfcs/INDEX.md` — curated thematic grouping and cross-reference map
- `metel-core/AGENTS.md` — Codeberg Issues task-tracking design (Trigger 10)
