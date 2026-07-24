---
id: strategic-objectives
title: "Strategic Objectives, Priorities, and Watch List"
type: report
status: active
last_reviewed: '2026-07-24'
---

# Strategic Objectives, Priorities, and Watch List

*Living document — updated in place, not a point-in-time snapshot, matching the convention
already used for `reports/substructural-types/*.md`. Dated strategic-overview reports
(`strategic-overview-YYYY-MM-DD.md`) remain the periodic narrative record of what was found
and decided each cycle. What this document adds: a single place each cycle reads from and
writes back to, so "what are the current priorities" and "what are we watching for" don't
have to be reconstructed by finding whichever dated file happens to be most recent and
reading its prose. Created 2026-07-09; **§1/§2 rewritten and the priorities reordered
2026-07-22** — see the review log for what changed and why.*

**How to use this document, each strategic-overview cycle:**
1. Check §3's open triggers against real progress since `last_reviewed`. Mark any that fired,
   with a one-line resolution note, or that got closed for other reasons.
2. Update §2's priorities in place — not "restated unchanged," actually re-verified against
   current RFC/`REGISTRY.md` state **and against the issue tracker**, which is where the
   claim "this is a priority" either is or isn't cashed out.
3. Add any new triggers this cycle surfaced.
4. Append one line to §4's review log.
5. Update `last_reviewed` above.
6. *Then* write the dated narrative snapshot, if one is warranted — this document changing
   is not itself always enough to justify a new dated file; see `PROCESS.md`'s note on
   event-based rather than calendar-based triggers for that.

---

## 1. Long-term objectives

A systems language whose public face is **allocator-aware storage and resource control**, but
whose real semantic substrate is lower-level: **structural shape**, **per-field multiplicity**,
**brand identity/provenance**, and **binding-named lifetime validity**. Allocators remain
central to the language's identity, but they are the first major *synthesis* of that substrate,
not the substrate itself. The ordinary modern surface (aspects, exhaustive enums,
`Perhaps`/`Result`, generics, pattern matching) still matters, but it is not the differentiator.

The differentiation claim is therefore sharper than the earlier allocator-first framing: the
bet is not merely "allocators as first-class values," but **fine-grained resource semantics
over structured values** — row-shaped products with per-field ownership discipline, identity
where plain structure is not enough, and concrete lifetime diagnostics named after real
bindings rather than abstract `'a`.

This is restated near-verbatim in the public blog post ("Introducing Metel", 07-15), which is
the external commitment this document is accountable to. Its sequencing sentence is the one to
measure §2 against:

> **short term**, the records post and `ToRecord`/`FromRecord` working in the interpreter.
> **Medium term**, the borrow checker, linear types, and brands as real primitives.
> **Then allocators**, on top of all of it.

§2's order below is that sentence, with one addition the blog doesn't have a slot for (the
interpreter-as-instrument track, Priority 5) because pretending it isn't consuming effort
would make this document less honest, not more focused.

**One qualification the blog sentence needs, added 2026-07-22.** "`ToRecord`/`FromRecord`
working in the interpreter" is the short-term *goal*, but it is not the short-term *task*, and
reading it as one produces an unbuildable first step: those conversions are tier 2 of
RFC-0090's three tiers and convert *into* a record type-former that does not exist yet. The
record/row semantics have to be defined first. Priority 1 states the resulting order. This
qualification is recorded here rather than only in §2 because §2's ordering is measured
against this sentence, so a misreading of it propagates into the priorities themselves — as it
did in this document's first draft of the reorder.

### The standing meta-risk

Originally, from `integrated-language-overview-2026-07-07.md` §5/§7:

> The design is roughly two major threads ahead of the implementation. The interpreter still
> deep-clones values and has no borrow checker, no allocator, no move-semantics enforcement.
> If each planning cycle keeps extending the design instead of freezing and building, the
> overreach risk compounds. The discipline to stop designing is itself the most important
> planning decision here.

**Still literally true fifteen days later**, word for word: the interpreter still deep-clones,
still has no borrow checker, still has no move-semantics enforcement. That sentence has now
survived seven strategic-overview cycles unchanged. It is not a warning about a possible
future; it is a description of the present.

**Sharpened 2026-07-09** (prompted by introducing `3-integrated`, a stage whose entire purpose
is *more* pre-implementation design work) into a two-case rule that still holds:

- **For genuinely still-forming clusters** — comptime/derive, brand-kind unification — letting
  design run ahead of implementation is correct, not overreach: nothing exists yet to rebuild,
  so settling the mechanism's shape first isn't paying a build-then-rebuild cost.
- **For already-accepted, unentangled clusters, leaving them un-actioned *is* the overreach.**
  This is where the risk actually lives.

  *Historical correction, 2026-07-10, kept rather than dropped:* this section originally cited
  RFC-0092's Open Question 4 (reinterpreting `<T>` generics as sugar over comptime type
  parameters) as evidence for the first case. That was wrong — generics via monomorphization
  were already implemented, and OQ4 explicitly says the unification is "not load-bearing." The
  example in fact showed the opposite pattern (implementation running safely ahead of a later
  design question). The general argument doesn't depend on it and still holds.

**Practical consequence: scope `3-integrated` narrowly**, to genuinely-coupled, still-forming
clusters — not uniformly across the whole accepted backlog. Most of that backlog isn't in
active churn and doesn't need worked-examples-against-siblings before implementation.

### Corollary: the interpreter is a temporary feedback mechanism, not the target structure

*Added 2026-07-10; unchanged in substance, and now load-bearing for Priority 5.*

The current interpreter's job is to produce real-program feedback the design can't get any
other way — not to be, or to become through careful internal refactoring, the eventual
compiler. Interpreter-internals work falls into one of two budgets, and only the first is
worth spending on now:

- **Feedback-trustworthiness budget** — work needed so the interpreter's behavior is a
  reliable signal about the *design*, not an artifact of how the interpreter happens to be
  built. A real dispatch bug, a wrong diagnostic, a construct that can't be written at all.
  Worth doing regardless of whether this interpreter's structure survives.
- **Forward-structure budget** — work that only pays off if these internals persist into
  whatever comes after the compiler-direction decision: consolidating a scattered
  monomorphization pass, clean IR shape, ABI groundwork. Not worth spending on now.

**The failure mode this filter is most often used to excuse is the opposite one** — skipping
trustworthiness work because "it's all throwaway anyway." That is a misuse of the corollary,
never an instance of it (Trigger 9).

---

## 2. Current priorities

**Reordered 2026-07-22.** The previous ordering had a *completed* item (ratifying the
allocator cluster, done 07-10) occupying the Priority 1 slot, which made the document read as
though the top priority were finished when the actual top priority sat at number 2. The order
below is the blog's own sequencing sentence, made checkable.

| # | Priority | Design state | Engineering state |
|---|---|---|---|
| 1 | Records / views as the structural carrier | RFC-0089/0090/0091/0109 `1-under-review` | not started, **no issue** |
| 2 | Ownership enforcement and the borrow checker | RFC-0071 `2-accepted`; borrow checker **has no RFC at all** | not started, **no issue** |
| 3 | Brands and context parameters | RFC-0076 `0-draft`; RFC-0113 `1-under-review` | not started, **no issue** |
| 4 | Allocators — emergent synthesis, built last | RFC-0063/65/66/67/68/73/77 `2-accepted`, complete | deliberately not started |
| 5 | The interpreter as a feedback instrument | n/a | **all 19 open issues** |
| 6 | Adjacent design and demand-gated frontier | RFC-0092–0095 `0-draft`; RFC-0026 stale | not started |

**Read that table's last two columns together — that is this cycle's central finding.**
Priorities 1–4 hold every RFC the project calls foundational and, between them, zero open
issues. Priority 5, which this document had never ranked at all until today, holds all of
them. This is not the same claim as 07-20's Trigger 17 ("ergonomics churn substituted for the
stated priority"); it is structural. The stated priorities and the tracker do not intersect.

### Priority 1 — Records / views as the structural carrier

**Restructured 2026-07-24.** Trigger 6 is settled and the cluster is decomposed. The four
RFCs swept to review on 07-21 are gone as a unit: **RFC-0090 is superseded by six RFCs
ordered by dependency depth** — RFC-0116 (Anonymous Record Types), RFC-0117 (Row
Narrowing), RFC-0118 (Row Bounds), RFC-0119 (Record Conversions), RFC-0120 (Named
Records), RFC-0121 (Open Rows) — and **RFC-0089/0091/0109 return to `0-draft`**, deferred
until records are implemented.

Trigger 6 resolved by finding the dependency it tracked was **accidental**: RFC-0089's floor
was rewritten from "Option B" to `ToRecord` by its own same-day revision on 2026-07-09, which
is why neither RFC ever stated the conflict — neither chose it. Per-field multiplicity was
always meant to wait for records. The largest consequence was unplanned: removing
fiat-linearity from the records path drops the brand-carrying `ToRecord` exception and with
it **the cluster's only dependency on RFC-0076 (`0-draft`)**.

**The entry point is now RFC-0116, and it is unblocked.** Anonymous record types: the closed
`{ x: f64 }` type-former, `{ x = 1.0 }` values, projection, structural identity, usability
rules. No narrowing, no bounds, no conversions — and therefore no dependency on RFC-0071
(`2-accepted`, 0% implemented), on RFC-0076, or on any row kind. That is the whole point of
splitting six ways rather than three: everything else in the cluster sits behind one of
those, and RFC-0116 sits behind nothing. **Trigger 24 is its falsifier.**

**The first deliverable is the record/row semantics themselves, not `ToRecord`/`FromRecord`.**
The blog names the latter as the short-term goal, and this document's first draft of §2
repeated that as the recommended first tracked issue. That was wrong, and RFC-0090 already
says so in two places:

- **§3's own recommended build order** puts *closed `record` types + `HasField`
  auto-derivation* at step 1, explicitly deferring `<row R>` open generics to a separate
  decision with its own timeline. `ToRecord`/`FromRecord` is nowhere in that step.
- **§8 makes it tier 2 of three.** Its whole content is a conversion *into* the record
  type-former — `h.to_record()` has type `record { fd: i32, alloc: @a Buffer }`. Until that
  type exists as a real type-former, the conversion has no codomain and cannot be built. The
  derive half depends further on RFC-0093's comptime mechanism, still `0-draft`.

So the sequence inside this priority is now the RFC numbering itself: **RFC-0116 → RFC-0117
→ RFC-0118 → RFC-0119 → RFC-0120 → RFC-0121**, with tier 2's conversions (RFC-0119) as the
visible acceptance test the blog names rather than the entry point, and open rows (RFC-0121)
last because that is where the row kind and row unification live. Each is independently
acceptable once its predecessors are, which is what the decomposition bought.

**Per-field multiplicity moves out of this priority** — RFC-0089/0091, now `0-draft`. It is
still the half of the substrate that makes records more than a structural-typing convenience,
and it is still unwritten in its final form, but it was never meant to be built alongside
records. Its floor gets respecified once there is an implemented records substrate to build
against; RFC-0089 §3 is marked as not-the-specified-floor in the meantime. RFC-0089 §1–2 (the
`Linear` aspect and multiplicity lattice) and §4–5 are independent of all of the above and
could be taken up separately at any point — they were only ever blocked by sharing a document
with §3.

**2026-07-23: a full session of design work landed here, with one real artifact-level
result and Trigger 6 still not settled.** `HasField`'s bound syntax — checked directly
against `grammar.pest` — never actually parsed; it is fixed, as a direct amendment to
RFC-0090 itself, not just in a parallel exploration document (`HasField<"x", f64>` →
`{ x: f64 }`, `Lacks<"tag">` → `!{ tag: _ }`). Two of RFC-0090's own open questions got
resolutions folded in the same pass (tier-3's declaration syntax; a pointer to new draft
RFC-0114 for `FromRecord`'s constructor-invariant risk). A separate, more radical
exploration (`nominal-types-as-branded-rows.md` — every nominal type as `(brand, row)`,
not just tier-3's opt-in named record) was pressure-tested at length and deliberately
**unbundled**: parts that didn't need its central thesis were folded back now; the
central thesis itself was kept a live, separate exploration, explicitly not gating this
priority's own path to acceptance. **Trigger 6 itself — the actual dependency-direction
question review is gated on — was not touched.** See
`strategic-overview-2026-07-23.md` for the full account and the honest assessment of
what this kind of session does and doesn't count as.

### Priority 2 — Ownership enforcement and the borrow checker

Promoted to its own slot 2026-07-22. Previously this was one bullet inside the substrate list
("lifetime validity in its narrower but essential role"), which understated two things:

**RFC-0071 (Ownership and Move Semantics) has been `2-accepted` since 2026-06-28 and is 0%
implemented, with no tracking issue.** It is the most-depended-on document in the corpus —
RFC-0063 and every downstream allocator RFC take affine ownership as a given, RFC-0066's
`T: !Drop` scoped move-out assumes it, RFC-0068's struct-owned arenas assume its drop order —
and the interpreter still deep-clones, so none of it is enforced. Nearly a month accepted,
nothing built.

**The borrow checker has no RFC at all.** Verified against `REGISTRY.md`: the only match for
"borrow" across 112 RFCs is RFC-0086 (Outlives-of-Bindings Sugar), which is `6-refused`. The
blog commits to it as a medium-term primitive; `allocators-as-emergent-synthesis.md` makes it
a load-bearing term in the decomposition ("`@a T` being owned/affine/extractable is an owned
box type + the borrow checker checking it outlives `a`"); Priority 4 is gated on it. It is
carrying more architectural weight than any other undocumented thing in the project. This is a
larger unwritten hole than context parameters were before RFC-0113, and it is now Trigger 19.

The two halves sequence naturally: move checking makes ownership real and is specified
already; borrowing needs a design document before it can be built.

### Priority 3 — Brands and context parameters

The two primitives that carry identity and threading, both needed before Priority 4's
decomposition can even be tested.

- **Brands** (RFC-0076, `0-draft`) — identity/provenance where plain structure is
  insufficient. `brand-kind-unification.md` already established that the allocator handle
  `@a` is a brand role. Still unsettled, and Trigger 2's role-crossing matrix is the thing
  that would settle it. *Carried caveat:* RFC-0076's argument for why regions don't need
  brands rests on RFC-0063's abandoned triple-duty premise and needs re-deriving.
- **Context parameters** (RFC-0113, `1-under-review`, written 2026-07-21) — a general
  mechanism for a value a call tree needs, resolved by type from scope with ambiguity an
  error, of which the allocator handle `(@a: A)` is one instance. Written deliberately
  without allocator syntax in its core, and scoped narrowly: it replaces the *threading*
  only. Five open questions, chiefly syntax and whether contexts propagate through
  intermediate frames.

This priority is where the coupling risk in Trigger 18 concentrates: brands are unsettled,
and Priority 4 is bet on them.

**2026-07-23: `brand-kind-unification.md`'s own OQ6 (open since 2026-07-07, sixteen
days) got a candidate answer** — checked property by property against that document's
own definition of the unified kind, not re-asserted — and Priority 1's exploration was
checked for whether it deepens this priority's dependency on RFC-0076: it does not.
Nominal type identity, the thing Priority 1's exploration needs, turns out to be a
degenerate case of the freshness/rigidity properties (one introduction, at declaration,
compile-time only), needing none of RFC-0076's actual runtime checking machinery. The
real RFC-0076 dependency in this cluster (the allocator-instance brand, RFC-0090 §9's
fiat-linear exception) predates this session and is unchanged either way.

### Priority 4 — Allocators as an emergent synthesis and acceptance test, built last

*Unchanged in substance from the 2026-07-20 reframe; renumbered from 3.*

Allocator semantics remain central to the language's public identity, but they are **not** a
primitive, and almost certainly not a standalone feature either. They are the **last** major
subsystem and the **acceptance test** proving the primitives beneath them are sufficient.

**The design is essentially complete and deliberately unimplemented, and it stays that way
until the primitives it synthesizes are all built.** This is intentional, not neglect, and it
matches what the blog already tells readers. Implementation is gated on all of: the borrow
checker, records/views, linear types, lifetime anchors, and brands. Allocators are not being
*delayed* past those — they are *downstream of* those by construction, because they are
largely built *out of* them.

**The decomposition** (worked out in full in
`reports/substructural-types/allocators-as-emergent-synthesis.md`):

- `(@a: A)` handle-threading (RFC-0065 §1/§1b) is a special case of **context parameters**
  (now RFC-0113);
- the `@a T` instance-level tag, disjointness, and sendability are a special case of
  **brands** — `@a T` is `Box<T, instance-brand>` precisely, with *brand* rather than *type*
  (unlike Rust's `Box<T, A>`) carrying the load;
- `@a T` being owned/affine/extractable is an owned **box** type plus the **borrow checker**
  checking it outlives `a`;
- `@a expr` / `Alloc` is `@`-sugar over an ordinary aspect and library code.

What remains irreducibly allocator-specific is strikingly small: the sugar and the library.
The strategic risk this exposes is real — the cluster was specified *before* any of those
primitives existed, so some of its machinery (the `@` value-channel parameter; the tag-only
`<@a>` form, a brand re-invented under an allocator name without anyone noticing) is
general-purpose primitives wearing allocator-specific clothing.

**What does not change: the allocator RFCs stay intact.** Reframed from "accepted design
awaiting implementation" to "the acceptance test the primitives must reconstruct" — but not
refused, gutted, or superseded. The paper-complete standalone design is what keeps the
general-primitive work honest ("does this rebuild `BumpAlloc`?" is checkable at every step).
Dissolving it into abstractions before the primitives can reconstruct it would lose exactly
that check. This is Trigger 18.

### Priority 5 — The interpreter as a feedback instrument

**New slot, 2026-07-22.** This document has never ranked this work, while every open issue
has been in it. Naming it is not a promotion — it is ranked fifth deliberately — but leaving
it unlisted meant the tracker and the priorities described two unrelated projects, and the
gap could never be measured because one side of it wasn't written down.

The §1 corollary supplies the filter, and it is the whole content of this priority:
**trustworthiness work qualifies; forward-structure work does not.** Applied to what's
currently open:

- **Qualifies** — diagnostics and correctness that make interpreter behaviour a reliable
  signal about the design: the operator-aspect work (#149, #263 / RFC-0062), stack-safety
  where recursion depth silently changes what programs can be written (#261), missing
  language surface that blocks writing realistic test programs at all.
- **Instrument-quality, qualifies conditionally** — the LSP MVP (#246–#250). It doesn't make
  the interpreter more *correct*, but it does make feedback cheaper to obtain, which is the
  same argument one level up. Worth it if it stays an MVP; not worth it as a product.
- **Does not qualify while Priorities 1–3 have no issues at all** — parser performance
  (#260), the System F HIR follow-up (#259), stdlib breadth (#258). These are forward-
  structure or product work on an interpreter explicitly described as temporary.

**The honest reading of the tracker:** it currently holds a well-run interpreter project. That
is worth something — the last several cycles genuinely improved diagnostics, fixed eight real
bugs, and shipped four RFCs. It is just not the project §1 describes, and the two have not
been distinguishable from this document until now.

### Priority 6 — Adjacent design and demand-gated frontier

Two unrelated things, previously conflated in one section:

- **Comptime / derive** (RFC-0092–0095) remains active design work with real internal
  motion. It should continue, but not be conflated with the substrate or with allocators. It
  is the clearest legitimate instance of §1's "still-forming, nothing to rebuild" case.
- **The unsafe / custom-allocator layer** remains **demand-gated frontier work**, not a
  neglected near-term priority. It gates user-authored custom allocators, not the four stdlib
  allocators or the allocator MVP, and RFC-0026 still predates the split model and needs a
  rewrite before it is actionable. Promotion signal unchanged: a concrete need that
  host-implemented stdlib allocators cannot satisfy.

### Closed: ratifying the allocator/lifetime cluster (former Priority 1)

Kept as a record, no longer a priority. **Done 2026-07-10** after six cycles unactioned — the
concrete instance of the meta-risk while it sat idle. Ratified by amending RFC-0063 directly
rather than creating RFC-0088. Not a formality: a consistency pass first found RFC-0063 §9
items 1/2/5 still written as open/blocking three days after the roadmap's Phase 0 had resolved
them elsewhere with no sync back, plus stale "Region…" titles on RFC-0066/0068. **Follow-through
resolved 2026-07-15** — RFC-0067a/0072/0078/0081/0082 all reached `4-implemented` (RFC-0083
superseded). Triggers 5 and 12 fired and resolved here.

---

## 3. Open triggers (watch list)

Living checklist. Fired/resolved items stay listed with resolution, not deleted — the record
of what was watched for and what actually happened is part of the point.

1. ✅ **Fired, 2026-07-09.** Re-reading RFC-0080 confirmed it did not naturally extend to
   derive-as-codegen — `Clone`'s derive was one hardcoded example, and its Unresolved
   Questions never mentioned a general mechanism. Directly caused the RFC-0012 →
   RFC-0092/0093/0094/0095 split.
2. ⬜ **Open.** If a real scenario forces the brand-kind-unification role-crossing matrix to
   resolve and reveals identity brands and allocator/lifetime brands are more separate than
   hoped → the substrate story weakens at exactly the point where it wants brands to carry
   cross-cutting identity/provenance. Still untouched. **Now Priority 3's gating question,
   and Trigger 18's first term.**
3. ⬜ **Open.** If real allocator/resource implementation shows partial-consumption and
   drain/restore patterns are needed constantly, not exceptionally → evidence that the
   substrate priority is correct and that per-field machinery belongs closer to the
   implementation path. No implementation has happened yet to produce this evidence.
4. ⬜ **Open, carried from 07-06.** Implementation pressure on Option B/C; a comparable
   language shipping a similar structural-plus-linear combination first (the one external
   risk to the "worth pursuing" verdict); RFC-0039's independent prioritization; a concrete
   user-authored-allocator need that would promote the frontier layer. None resolved.
5. ✅ **Fired and resolved, 2026-07-10.** The former Priority 1 moved. This trigger did its
   job: it named the pattern that was actually happening (L3 activity masking L2 inaction)
   and caused the check that led to ratification.
6. ✅ **Settled 2026-07-24 — the dependency was accidental, and the cluster is decomposed.**
   Working the question through produced a cleaner answer than "yes" or "no": the
   RFC-0089→RFC-0090 dependency was introduced by RFC-0089's *own same-day revision* on
   2026-07-09, which rewrote its §3 floor from "Option B" (field access on a nominal
   struct) to `ToRecord`. **Neither RFC stated the conflict because neither RFC chose it** —
   that absence was the tell, and this trigger was right to treat it as a signal rather
   than an oversight. Per-field multiplicity was always meant to wait until records were
   implemented.
   Three findings from settling it, in ascending order of consequence:
   - **The technical answer, had the coupling been deliberate:** RFC-0089's floor needs
     only RFC-0090 §3 *step 1* — a closed type-former plus narrowing over a 2^*N* subset
     lattice, all concrete — and no row variables or unification anywhere. So it never
     threatened the "narrow, no row kind" property, because everything it touched was
     inside the half of RFC-0090 defined by not having a row kind.
   - **It was a diamond, not a cycle.** RFC-0090's step-1 core and RFC-0089 §1–2 are
     mutually independent; the two interaction points (§5's `Linear`-over-records join,
     §3's floor) both sit *above* both cores. Nothing was circular, and the build order
     was forced all along.
   - **Deferring linear removed the cluster's only unratified dependency.** RFC-0090 §8's
     brand-carrying `ToRecord` exception existed solely to serve RFC-0089 §2.1's
     fiat-linearity. Dropping it means nothing in RFC-0116–0121 depends on **RFC-0076
     (Brand Types, `0-draft`)**. The strongest corroboration that the coupling was
     accidental: removing it made the design *simpler*, not merely differently-shaped.
   **Action taken:** RFC-0090 superseded by six RFCs partitioned by dependency depth
   (RFC-0116–0121); RFC-0089/0091/0109 returned to `0-draft`; RFC-0089 §3 marked as not
   the specified floor, with §1–2 and §4–5 noted as the half that was independently
   acceptable all along and blocked only by sharing a document. See Trigger 24 for what
   this now hands to the next cycle.
   *Original wording, kept because the trigger's value was in how it was posed:* "Does the
   substrate genuinely require RFC-0090's record machinery for RFC-0089's floor, or does
   that dependency need removing to preserve the 'narrow, no row kind' property? **Neither
   RFC states the conflict.** Review of the under-review cluster must settle this, and it
   is the reason the four RFCs were swept as a unit rather than individually. *2026-07-23:
   a full session of depth on Priority 1 went around this question, not through it* — real
   fixes landed without ever addressing the dependency direction itself."
7. ⬜ **Open, still untested.** Does `INDEX.md` + `rfc.py`'s overlap check actually prevent a
   second RFC-0055-shaped silent duplication, or does it quietly fall out of use the way the
   undocumented process before it did? **Partially exercised 2026-07-21:** RFC-0111 and
   RFC-0113 were both created this window, and `INDEX.md` was checked first in both cases.
   Two data points, both by the same operator who wrote the rule — keep watching.
8. 🟡 **Fired repeatedly; the mechanism works.** Twelve RFCs moved through `3-integrated` and
   each surfaced a real problem while writing worked examples — RFC-0067a's missing
   value-extraction rule, RFC-0083's obsolete motivating example, a pre-existing
   `types.md`/`expressions.md` contradiction over `&mut` field paths, RFC-0072's stale
   bracket-channel examples, RFC-0081's dangling `#[derive]` reference, RFC-0082 amending a
   retracted RFC's dead concept. Of the original backlog only RFC-0008 remains, still gated on
   `dyn Aspect` having no consumer. Superseded as a watch item by Trigger 13.
9. ⬜ **Open.** Watch for the "interpreter is temporary" corollary (§1) being misapplied to
   justify skipping *feedback-trustworthiness* work under cover of "it's all throwaway
   anyway" — e.g. a real dispatch bug shrugged off instead of fixed. **Now directly operative:
   Priority 5 turns this corollary into a triage rule, which makes it much easier to misuse
   in both directions.** Watch for both: trustworthiness work skipped as throwaway, and
   forward-structure work admitted by relabelling it trustworthiness.
10. ⬜ **Open, 2026-07-11.** Task tracking moved from ClickUp to Codeberg Issues, to avoid
    vendor lock-in and eventually enable outside contributors. Neither payoff is verified —
    the migration only proves the mechanics work. Watch for any issue or PR filed by a
    non-maintainer, and whether the tooling added then gets reused rather than being a one-off.
    The blog's "open parts of the process to outside contributions" makes this a stated goal
    now, not just an internal hope.
11. ✅ **Re-evaluated and closed, 2026-07-15.** The analogy to the former Priority 1 does not
    hold: the frontier layer is demand-gated in both source documents, blocks only
    user-authored custom allocators, and RFC-0026 needs a rewrite anyway. Signal retained in
    Priority 6's form.
12. ✅ **Fired and resolved, 2026-07-15.** The six RFCs at `3-integrated` all reached
    `4-implemented` within four days — the fastest resolution any trigger here has had.
    Cleanest evidence yet that naming a stall explicitly is what gets it moved.
13. ⬜ **Open, 2026-07-15.** `3-integrated` has been empty since Trigger 12 resolved; recent
    RFCs (0098/0102/0103/0106/0111) went straight from accepted to implemented. Watch whether
    that's the new normal (worked-examples-then-immediate-build, collapsing the stall this
    document exists to catch) or whether the next accepted batch sits there again with no
    engineering following.
14. ⬜ **Open, 2026-07-15; half of it addressed 2026-07-24.** RFC-0099 and RFC-0100 both
    reverted `2-accepted` → `1-under-review` during integration, on grounds the review that
    accepted them hadn't surfaced. Both are still under review nine days later. If a third
    RFC follows the same path, that's evidence `2-accepted`'s own bar ("no more open
    questions block it") is being called too early in practice.
    **Update, 2026-07-24: RFC-0100's grounds for reversion turned out to be
    separator-specific, not fundamental.** The ascription collision that reopened it arises
    only from spelling keyword arguments `name: value`; under `=` (the separator invariant
    in `reports/syntax/colon-classifies-equals-defines.md`) it cannot occur, and RFC-0100
    was revised to adopt `=` rather than to answer the question it was reopened over. **This
    cuts both ways for the trigger and should not be read as a clean vindication.** It is
    mild evidence *for* the trigger's worry — the reversion was called on an analysis that
    was itself incomplete, meaning review surfaced a real problem but mis-diagnosed its
    cause, which is a different failure from accepting too early and arguably a worse one.
    What it does show is that a reopened RFC can be closed out by a finding from elsewhere
    in the corpus rather than by re-litigating its own question. RFC-0099 is untouched and
    still open on its own grounds.
15. ⬜ **Open, 2026-07-15.** `metel-core` PR #270 was found fully superseded by direct commits
    on `sprint/26` that reimplemented the same feature with the newer `extend` syntax. Watch
    whether a cheap repeatable check ("does an open PR's branch still contain work not already
    on the target branch") gets added anywhere — this instance was only caught by an explicit
    pull-and-compare.
16. ✅ **Fired and resolved same day, 2026-07-20.** RFC-0097's frontmatter claimed
    `implemented` while `coherence.rs::outermost_id` had no deliberate branch for a bare
    blanket-impl target. Resolved by landing the real check rather than downgrading the
    frontmatter; zero regressions, since the fix only made an already-correct outcome
    deliberate.
17. ✅ **Opened 2026-07-20; answered 2026-07-21 — both, in that order.** Would the next cycle
    move a higher-ranked priority, or would reference/deref ergonomics churn keep substituting
    for it? It did both: RFC-0107/0108/0110 were implemented and RFC-0111 was opened *and*
    implemented — all ergonomics, with records and allocators untouched — and then the cluster
    was named and corrected within the same cycle, sweeping RFC-0089/0090/0091/0109 to review
    and writing RFC-0113 from nothing. Recorded honestly rather than as a clean win: **the
    correction happened because the trigger was read back, not because the priority was
    followed.** Superseded going forward by Trigger 20, which measures the same thing without
    depending on someone remembering to re-read this file.
18. ⬜ **Open, 2026-07-20.** The allocator-decomposition hypothesis (Priority 4): can the
    cluster be rebuilt as (context parameter) + (allocator-instance brand) + (owned box) +
    (borrow-checked lifetime), leaving only the `Alloc` aspect and `@`-sugar as residue?
    Untestable until brands and context parameters are real. Watch for: (a) the decomposition
    proving true (the language gets smaller) or false (the resisting part is the genuinely
    allocator-specific remainder worth keeping); (b) the coupling risk — allocators are now
    bet on a two-deep chain of unsettled-on-unsettled, and the mitigation (keep the allocator
    RFCs intact as the acceptance test, never gutted) has to actually hold. **One of its three
    original clauses is discharged:** the context-parameter RFC that didn't exist is now
    RFC-0113.
19. ⬜ **New, 2026-07-22. The borrow checker has no RFC.** Verified against `REGISTRY.md`: the
    only "borrow" match across 112 RFCs is RFC-0086, `6-refused`. Meanwhile the blog commits to
    it as a medium-term primitive, `allocators-as-emergent-synthesis.md` makes it a load-bearing
    term in the decomposition, Priority 4 is gated on it, and RFC-0071 — accepted since 06-28,
    0% implemented — assumes it. It is carrying more architectural weight than anything else
    undocumented in the project. Watch whether an RFC gets written, or whether the borrow
    checker keeps being cited as a known quantity by documents that have never specified it.
    This is the same shape as the context-parameter hole Trigger 18(b) tracked, one layer down
    and load-bearing for more.
20. ⬜ **New, 2026-07-22. Priorities 1–4 hold zero open issues; Priority 5 holds all nineteen.**
    Verified directly against the tracker: no issue references RFC-0071, 0076, 0089, 0090,
    0091, 0109, or 0113, and none of those RFCs carries an `impl_tracking` field. This is the
    structural version of Trigger 17 — not "attention went elsewhere this cycle" but "the
    stated priorities have never been represented in the system that schedules work." Watch
    for the specific, cheap thing that would falsify it: **one tracked issue against any of
    Priorities 1–3.**

    *Corrected 2026-07-22, same day:* this trigger originally recommended
    `ToRecord`/`FromRecord` as that first issue, on the strength of the blog calling it the
    short-term commitment. It cannot be first — it is tier 2 of RFC-0090 §8 and converts into
    a record type-former that has to be specified and built before the conversion has a
    meaning, which RFC-0090 §3's own build order already states. The recommended first issue
    is instead **the closed `record` type-former plus `HasField`** (§3 step 1), and the
    honest version of this trigger is that even the "cheap falsifier" was mis-sized on first
    attempt — the substrate has no genuinely small entry point, which is itself part of why
    it keeps not being started.

    **Update, 2026-07-23: still not tripped, for the seventh day running — but a real
    middle state showed up that this trigger's binary framing didn't anticipate.** A
    full session's findings became a direct amendment to RFC-0090 itself (the bound
    syntax fix), reaching the artifact under review without ever touching the issue
    tracker. That is not the falsifier — no tracked issue exists — but it is not
    identical to another day of pure `reports/`-only exploration either. See Trigger 22.
21. ⬜ **New, 2026-07-22.** Priority 5 is new and is the priority most likely to expand to fill
    the available effort, because its work is the most immediately satisfying — every issue in
    it is well-scoped, verifiable, and finishable in a session, which is precisely what the
    substrate work is not. Watch whether ranking it fifth actually constrains it, or whether
    naming it legitimises it and the ratio gets worse. If the next cycle closes several
    Priority 5 issues and opens none against 1–3, ranking it did nothing and the ordering
    should be treated as descriptive rather than directive.
22. ⬜ **New, 2026-07-23. A middle state between "pure exploration" and "a tracked issue"
    showed up, which Trigger 20's binary framing didn't anticipate.** A full session's
    findings on Priority 1 became a direct amendment to RFC-0090 itself (a real bound-
    syntax bug, fixed in the RFC under review, not just in a parallel document) —
    reaching the artifact that governs implementation without ever touching the issue
    tracker. Not the falsifier; not identical to another day of `reports/`-only churn
    either. Watch whether this recurs as a reliable leading indicator that a cluster is
    converging, or whether it can also repeat indefinitely without ever producing a
    tracked issue.
    **Recurred immediately, 2026-07-24 — one day later, not eventually.** RFC-0114 and
    RFC-0100 were both revised directly, with real findings (a construction hole in
    RFC-0114 that its stale syntax had hidden; RFC-0100's reopening reason dissolved),
    and again no issue was filed. **One data point each way is now available and they
    point in opposite directions:** it is not merely occasional, which is mild support for
    the "leading indicator" reading — but the second instance was *cheaper* than the first
    (correcting stale syntax, not discovering a bug), which is mild support for the "can
    repeat indefinitely" reading, since low-cost RFC edits are always available and never
    force a build. The discriminating question, worth stating now so the next cycle can
    answer it rather than re-observe it: **does any of this RFC-text work ever produce a
    change that the interpreter would have to implement to be conformant?** If yes, the
    middle state is a real waypoint. If the corpus can absorb every finding without that
    ever becoming true, it is a comfortable substitute for building.
23. ⬜ **New, 2026-07-23. An explicit unbundling decision, worth watching whether it
    holds.** A session's deepest exploration (`nominal-types-as-branded-rows.md` —
    every nominal type as `(brand, row)`, not just tier-3) turned out to bundle several
    claims at different levels of dependency on its own central thesis. Rather than one
    fate for the whole document, the independent parts were folded back now (into
    RFC-0090, into `brand-kind-unification.md`) and the central, more speculative thesis
    was deliberately kept separate, explicitly not gating Priority 1's own path to
    acceptance. Watch whether the next cycle actually acts on that split — moving
    RFC-0089/0090/0091/0109 toward acceptance without waiting on the broader idea — or
    whether the split was itself just a well-reasoned form of deferral.
    **A second, cleaner instance the next day, 2026-07-24 — and this one produced an
    artifact rather than a decision about one.** RFC-0100 was split: its separator half
    became **RFC-0115** (a new, small, dependency-free draft), its call-shaped-construction
    and keyword-argument half stayed put and stayed contested. The test this trigger asks
    for is met more convincingly here than by the 07-23 instance, on two counts. First,
    the split was made **against** the splitter's interest — RFC-0100 is materially weaker
    for it, having lost the "we complete a grammar-wide invariant" argument to RFC-0115,
    and its own text now says so. Second, it **removed** a dependency rather than deferring
    one: reworking RFC-0114 against the split showed its RFC-0100 dependency had never been
    real (a literal that desugars to `construct` is not a bypass), so RFC-0114 went from
    blocked-on-an-under-review-RFC to blocked on nothing. Two unbundlings in two days is a
    pattern, not a coincidence; the open part of this trigger is unchanged and unaffected —
    none of it moved RFC-0089/0090/0091/0109 toward acceptance.
    **Third instance, hours later, and this one *did* move them — by dissolving the
    cluster.** RFC-0090 superseded into six dependency-ordered RFCs, RFC-0089/0091/0109
    deferred to draft. Three unbundlings in two days is now the dominant activity of this
    cycle, which is worth naming as its own risk: a corpus can be re-partitioned
    indefinitely, and each split feels like progress because it genuinely removes a
    dependency. **The test this trigger should now apply is no longer "does the split
    hold?" but "did any of them end in a build?"** So far: no.
24. ⬜ **New, 2026-07-24. The split's whole promise is that RFC-0116 is buildable today —
    and that promise is now falsifiable in a way its predecessors were not.** Trigger 20's
    original recommended first issue ("the closed `record` type-former plus `HasField`")
    was stale twice over by 07-24: `HasField` retired, and the type-former's grammar
    surface grew three times in one day. RFC-0116 is the re-scoped version — anonymous
    record types, no narrowing, no bounds, no conversions, **no dependency on RFC-0071,
    RFC-0076, or any row kind**. If it is genuinely the small, unblocked entry point the
    split claims, a tracked issue against it should be cheap to file and cheap to close.
    **If a month passes with RFC-0116 still `0-draft` and no issue filed, the decomposition
    was a more sophisticated form of not starting**, and this document should say so
    plainly rather than crediting the improved structure. That is the falsifier; it is
    narrower and harder to evade than Trigger 20's, because the excuse of "blocked on
    something unratified" has been deliberately engineered away.

---

## 4. Review log

| Date | What changed | Dated snapshot |
|---|---|---|
| 2026-07-01 | (predates this document) | `strategic-overview-2026-07-01.md` |
| 2026-07-05 | (predates this document) | `strategic-overview-2026-07-05.md` |
| 2026-07-06 | (predates this document) | `strategic-overview-2026-07-06.md` |
| 2026-07-07 | (predates this document) | `integrated-language-overview-2026-07-07.md`, `reports/implementation/roadmap-2026-07-07.md` |
| 2026-07-08 | (predates this document) | `strategic-overview-2026-07-08.md` |
| 2026-07-09 | This document created, seeded from 07-08 and 07-07; RFC-0012 split into RFC-0089–0095; RFC-0055 reconciled; `INDEX.md`/`PROCESS.md`/`rfc.py` created; the ToRecord-floor tension surfaced (Trigger 6) | *(none)* |
| 2026-07-10 | Corrected the RFC-0092/generics citation in the meta-risk section; RFC-0084 reversed to keep `[T; N]`/`[expr; N]`; added the "interpreter as temporary feedback mechanism" corollary (§1, Trigger 9) | *(none)* |
| 2026-07-10 | Former Priority 1 done: allocator/lifetime cluster ratified to accepted after a consistency pass fixed real drift (RFC-0063 §9 items 1/2/5 out of sync with the roadmap; stale "Region…" titles on RFC-0066/0068). Trigger 5 fired and resolved. | *(none)* |
| 2026-07-10 | RFC-0067a/0078/0083 became the first RFCs to reach `3-integrated`; RFC-0072/0081/0082 followed the same day. Trigger 8 fired twice. | *(none)* |
| 2026-07-10/11 | RFC-0082's associated-type disambiguation hardened. `AGENTS.md` and `internal/versioning.md` reconciled. Task tracking fully migrated from ClickUp to Codeberg Issues: 49 stale/duplicate issues reconciled, 34 tasks migrated, 10 labels + 1 milestone created, 6 RFCs' `impl_tracking` repointed. Self-hosting Forgejo assessed as feasible but deferred. `rfc.py` gained enforcement for the spec's "Not yet implemented" callouts. Triggers 10/11 opened. | `strategic-overview-2026-07-11.md` |
| 2026-07-11 | Correction to the same-day snapshot: it had missed that all six newly-integrated RFCs were still `impl_status: not-started` — a real widening of the design/implementation gap. Trigger 12 opened. | `strategic-overview-2026-07-11.md` (amended) |
| 2026-07-15 | Eleven RFCs shipped `4-implemented`; Trigger 12 fired and resolved, Trigger 8 un-stalled. RFC-0103 split, deferred half became RFC-0105. RFC-0099/0100 reverted accepted → under-review (Trigger 14). PR #270 found superseded (Trigger 15). Dangling `3-integrated` path in `error-codes.md` and stale `INDEX.md` counts found. | `strategic-overview-2026-07-15.md` |
| 2026-07-15 | Fixed the dangling RFC-0060 path references; closed Trigger 11 as a false analogy. Split RFC indexing into generated `REGISTRY.md` (authoritative) vs curated `INDEX.md` (thematic), enforced mechanically. Rewrote the medium-term narrative around a substrate-first model, and refined it to a minimal low-level allocation model narrower than the full allocator family. | *(none)* |
| 2026-07-20 | First cycle to cross-reference the public blog post against this document as real strategic intent. Found strong alignment (substrate reframing and records' priority near-verbatim) and two divergences: the blog's Foundation section shows 0%-implemented syntax with no "design sketch" disclaimer, and the cycle's RFC output went to neither higher-declared priority. RFC-0097 frontmatter/reality drift found. Triggers 16/17 opened. | `strategic-overview-2026-07-20.md` |
| 2026-07-20 | Trigger 16 fixed the same day: landed the real `outermost_id` check for bare-parameter blanket-impl targets rather than downgrading the frontmatter. Zero regressions. Trigger 16 closed. | *(none — code fix)* |
| 2026-07-20 | Reframed allocators from "flagship synthesis" to "emergent synthesis + acceptance test, built last." New exploration doc `allocators-as-emergent-synthesis.md`. Context parameters added to the substrate as a primitive with no RFC yet; allocator RFCs kept intact as the acceptance test; Trigger 18 opened. | *(none)* |
| 2026-07-21 | RFC-0113 (Context Parameters) written from nothing, closing the "largest unwritten hole" this document named — deliberately without allocator syntax in its core, and scoped to replace the threading only. RFC-0089/0090/0091/0109 swept to `1-under-review` as one records/views cluster, with Trigger 6 named as the question review must settle. Twelve status-citation drift problems fixed. Trigger 17 answered honestly ("both, in that order"). | *(none)* |
| 2026-07-22 | **§1 and §2 rewritten; priorities reordered from four slots to six.** The old ordering had a completed item (allocator ratification, done 07-10) in the Priority 1 slot, so the document read as though the top priority were finished — moved to a "Closed" subsection at the end of §2, preserved as a record. New order follows the blog's own sequencing sentence: records/views (1), ownership + borrow checker (2), brands + context parameters (3), allocators (4). Two structural findings drove it, both verified directly rather than inferred: **the borrow checker has no RFC at all** (only "borrow" match across 112 RFCs is the refused RFC-0086) despite three documents treating it as a known quantity, and **RFC-0071 has been accepted since 06-28, 0% implemented, untracked** — together promoted to Priority 2 and Trigger 19. **Priorities 1–4 hold zero open issues while all nineteen sit in interpreter work that this document had never ranked**; that work is now Priority 5, ranked explicitly fifth with the §1 budget filter as its triage rule, because leaving it unlisted meant the tracker and the priorities described two unrelated projects and the gap could not be measured. Triggers 19/20/21 opened; 8 and 17 marked superseded by later triggers rather than deleted. | *(this entry; a dated snapshot may follow)* |
| 2026-07-22 | **Corrected the same day, on review:** the reorder below had recommended `ToRecord`/`FromRecord` as Priority 1's first tracked issue, following the blog's "short term" phrasing. It cannot be first. RFC-0090 §8 makes it tier 2 of three, converting *into* a `record { … }` type-former that does not exist yet — the conversion has no codomain until the record/row semantics are defined — and RFC-0090 §3's own recommended build order already puts the closed `record` type-former plus `HasField` at step 1, with `<row R>` open generics deferred to a separate decision. The derive half depends further on RFC-0093, still `0-draft`. Priority 1 now states the real order; §1 records the qualification the blog sentence needs, since §2 is measured against that sentence and a misreading of it propagated straight into the priorities; Trigger 20's recommended first issue corrected, keeping the note that even the "cheap falsifier" was mis-sized on first attempt — the substrate has no genuinely small entry point, which is part of why it keeps not being started. The five under-review RFCs' status notes were carrying the same wrong framing plus a stale Priority number; both fixed. | *(none)* |
| 2026-07-23 | A full session of design work on Priority 1's records/views substrate, not a corpus-wide sweep. Real, verified findings throughout — `HasField`'s bound syntax never actually parsed (confirmed against `grammar.pest`) and is fixed as a direct amendment to RFC-0090 itself; `brand-kind-unification.md`'s OQ6 (open sixteen days) got a candidate answer; a new draft RFC (RFC-0114) closed RFC-0090's OQ10 using only already-implemented machinery; two of the session's own errors were caught and corrected within the same conversation. A more radical exploration (every nominal type as `(brand, row)`, not just tier-3) was pressure-tested and then deliberately **unbundled**: parts independent of its central thesis folded back now, the central thesis itself kept separate and explicitly not gating this priority's own review. Honest assessment, matching Trigger 17's precedent for recording process outcomes plainly: on-topic depth is not the same failure Trigger 17 caught, but it is still design extension rather than building, per §1's own standing risk — and **Trigger 6, the actual question review is gated on, was not touched**. Trigger 20's tracked-issue falsifier was still not tripped, for the seventh day running, though a real middle state (a direct RFC amendment with no tracked issue) showed up that its binary framing hadn't anticipated. Triggers 22/23 opened for that middle state and for whether the unbundling decision actually holds next cycle. | `strategic-overview-2026-07-23.md` |
| 2026-07-24 | **RFC-0114 and RFC-0100 revised together, and the pairing was the point.** RFC-0114 carried stale syntax in three independent ways — freestanding `.{ … }` rows (superseded by `access-and-presence-rows.md` §3.5's receiver-based split the day before), and two *pre-RFC-0098* spellings (`impl Aspect for Type`, `&mut`) despite the RFC post-dating that RFC's implementation by nine days. Correcting the examples exposed a real hole the stale syntax had hidden: **`construct`'s own body had no way to build a `Self`** — the first draft used the bare literal §2 abolishes, and the synthesized default `Ok(row)` did not typecheck as written. New §1.1 confines row-to-`Self` to `construct`/`construct_unchecked` and nowhere else, which also **resolved that RFC's open question 5** (hand-written `new` needs no separate enforcement, because no primitive remains available to it) and raised a new one (8: `extend` blocks have no visibility modifier, so canonical construction may hand every struct a public constructor unless private field labels are unwritable from outside — RFC-0090's question, not RFC-0114's). RFC-0100 adopted `=` for keyword arguments per the separator invariant, which **dissolves the collision it was reopened over** rather than answering it; §3 rewritten around the smaller `assign_expr` collision `=` trades into, with the superseded ascription analysis kept behind a fold. Trigger 14 updated — and deliberately *not* as a vindication: review surfaced a real problem and mis-diagnosed its cause, which is a different failure from accepting too early. **Second consecutive day that findings reached RFC text with no tracked issue filed** — exactly the middle state Trigger 22 was opened to watch, now recurring rather than isolated, and Trigger 20's falsifier is untripped for an eighth day. **Later the same day, on the user's decision, RFC-0090 dropped the `record` keyword from the anonymous type-former** (`{ x: f64 }` as a type, `{ x = 1.0 }` as a value), completing the adoption of `access-and-presence-rows.md` §3.5 — the keyword now does exactly one job, minting nominal identity at `record X { ... }`, which also let open question 8 be folded into §8's prose instead of contradicting it. The change has a real cost, recorded as new open question 13 rather than glossed: closed record types and row bounds are now spelled identically and told apart by grammatical position alone, and one bullet in §2 that asserted the old distinction was wrong the moment the keyword went and had to be corrected. ~141 uses of the old spelling remain across RFC-0091/0109/0089 and the design reports — deliberately not swept, and named in RFC-0090's own revision note so the gap is visible rather than discovered later. **Then, on the user's call, RFC-0100 was split** — the separator fix (`field_init`'s `:` → `=`, braces kept) extracted as new draft **RFC-0115**, leaving call-shaped construction and general keyword arguments in RFC-0100. The trigger for the split was the user's observation that construction could keep its brackets and change only the separator; working it through found that version stronger than what was in RFC-0100 on four independent counts (it aligns nominal literals with RFC-0090's just-settled `{ x = 1.0 }` anonymous records, making `Point { x = 1.0 }` literally a row plus a brand; it restores the construction/destructuring symmetry RFC-0100 §4 had apologized for; it carries **zero** grammar risk where both prior proposals carried a real collision; and it frees the invariant from an under-review RFC). **RFC-0100 is honestly weaker for the split and now says so** — it lost the invariant argument to RFC-0115. **RFC-0114 gained the most:** reworking §2 showed its RFC-0100 dependency was never real — a literal that desugars to `construct` is not a bypass — so it now has no blocking dependency on any under-review RFC, and its open question 2 resolved by dissolving its premise. Still no tracked issue filed; Trigger 20's falsifier untripped for an eighth day, now against a *larger* body of RFC text. **Finally, a notation change that fixed a real ambiguity rather than a preference:** inside projection braces a bare identifier could be either a field label or a row variable (`Handle.{ fd }` vs `Handle.{ R }`), separated only by case convention — and RFC-0101, which would make that convention normative, is `0-draft`. So the design was leaning on an unratified RFC to disambiguate something it never acknowledged as ambiguous. Fixed by adopting **`row` declares, `..` marks every use**: a row variable is `..R` at every use site, a bare identifier in type position is always a *type* variable. The same mechanism with the variable left unnamed (`T: { x: f64, .. }` = "at least x") **resolved open question 13 the same day it was opened** — the closed/open bound distinction now turns on a token instead of on grammatical position, and the closed *bound* reading, previously inexpressible, became writable. Propagated through RFC-0090/0091/0109 and both exploration docs; RFC-0109 checked and found already conformant. New open question 14 opened for row *operations* (`R without "token"`, `R + "auth"`), which still use the string-literal-in-type-position form retired for bounds on 07-23 and now have no specified precedence, arity, or grammar — **and resolved the same day, in new RFC-0090 §2.1, by deleting the operators rather than fixing them.** A prior-art pass (PureScript, Ur/Web, Haskell `row-types`, OCaml, Koka, TypeScript, Elm) found that **extension needs no syntax at all** — every row-typed language writes the new label *inside the row literal*, which for Metel is the spread tail it already has (`{ ..R, auth: String }`), and the string literal was only present because an infix operator had nowhere else to put the name. Only **removal** lacked a form, and it becomes a where-clause decomposition (`where R = { token: Token, ..Rest }`), following PureScript's `Prim.Row.Cons` rather than Ur/Web's `--`. Cost: one grammar addition, no label literal, no label kind, no operators; the equation also subsumes the bound it replaces, and `=` is the invariant-correct separator (it equates), matching the `assoc_binding` equation already in that channel. Elm — the one language that shipped row extension/restriction and then **withdrew both** — is recorded as the standing caution. **The pass also found a third unbacked construct nobody had noticed:** `drain_field<row R, name: Symbol, T>` invents a `Symbol` *kind* that exists nowhere (the corpus's only `Symbol` is RFC-0059's compiler-internal `SymbolId`), spells it in bound position where the grammar reads it as an aspect bound on a *type* variable — inconsistent with `<row R>`'s prefix-keyword pattern sitting in the same parameter list — and indexes with `s.[name]`, which `postfix` does not accept. Opened as RFC-0091 open question 4, deliberately **not** folded into the §2.1 resolution: that retires the label *literal*, but `drain_field` needs label *polymorphism*, a strictly stronger capability (a label kind, a label literal, an index-by-label form, and rules for all three). Named explicitly because if it resolves to "no", RFC-0109's Motivation needs editing — it cites the generic `drain_field` as the reusable half records give and Rust's view types cannot. **The cycle then ended by settling Trigger 6 and decomposing the cluster on that basis.** The question resolved not as yes-or-no but as *the dependency was accidental*: RFC-0089's floor was rewritten from Option B to `ToRecord` by its own same-day revision on 2026-07-09, which is exactly why the trigger could observe that "neither RFC states the conflict" — neither chose it. Per-field multiplicity was always meant to wait for records. **RFC-0090 superseded by six RFCs partitioned by dependency depth** (RFC-0116 Anonymous Record Types, 0117 Row Narrowing, 0118 Row Bounds, 0119 Record Conversions, 0120 Named Records, 0121 Open Rows); **RFC-0089/0091/0109 returned to `0-draft`**; RFC-0089 §3 marked as not the specified floor, with §1–2/§4–5 noted as the half that was independently acceptable all along and blocked only by sharing a document. No feature dropped, no design decision reversed — a re-partition, and PROCESS.md's own named pathology (RFC-0012's 18 open questions before its split; RFC-0090 had 14). **The largest consequence was unplanned:** dropping fiat-linearity from the records path removes the brand-carrying `ToRecord` exception and with it the cluster's *only* dependency on RFC-0076 (`0-draft`) — the coupling's removal made the design simpler, which is the strongest evidence it was accidental. RFC-0071 (`2-accepted`, 0% implemented) remains, gating RFC-0117 onward but **not RFC-0116**, which is why the split is six-way. Trigger 24 opened as the falsifier: RFC-0116 is now the small, genuinely unblocked entry point, and if a month passes with no issue filed against it, the decomposition was a more sophisticated form of not starting. | *(none)* |

---

## References

- `public/blog/introducing-metel-2026-07-15.md` — the external commitment §2's ordering is
  measured against, especially its "What Now?" sequencing sentence
- `strategic-overview-2026-07-20.md` — most recent dated snapshot; `…-07-11`/`…-07-15`
  precede it, `…-07-08` is what this document was seeded from
- `integrated-language-overview-2026-07-07.md` — long-term objectives, the meta-risk framing,
  and the "narrow, no row kind" floor property Trigger 6 checks against
- `reports/substructural-types/allocators-as-emergent-synthesis.md` — Priority 4's
  decomposition argument and Trigger 18
- `reports/substructural-types/brand-kind-unification.md` — Priority 3's brand half, Trigger 2
- `internal/rfcs/PROCESS.md` — the RFC lifecycle this document's priorities reference
- `internal/rfcs/REGISTRY.md` — authoritative RFC state; the source for Trigger 19's
  "no borrow-checker RFC" finding
- `internal/rfcs/INDEX.md` — curated thematic grouping and cross-reference map
- `metel-core/AGENTS.md` — Codeberg Issues task-tracking design (Triggers 10, 20)
- `strategic-overview-2026-07-23.md` — most recent dated snapshot, the single-priority,
  deep-session cycle behind Triggers 22/23 and Priority 1/3's 2026-07-23 updates
