---
id: strategic-objectives
title: "Strategic Objectives, Priorities, and Watch List"
type: report
status: active
last_reviewed: '2026-08-01'
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

**How to use this document, each strategic-overview cycle:** see `PROCESS.md` (this
directory) for the full methodology — verification discipline, trigger append-only
lifecycle and closure bar, and the dated overview's structural template. Summary:
0. **Steering checkpoint, before anything else** — state what's changed and where §2
   seems to stand as a result, and ask whether the operator wants to redirect before
   proceeding. Runs every cycle, quiet ones included. See `PROCESS.md` §5.
1. Check §3's open triggers against real progress since `last_reviewed`. Mark any that fired,
   with a one-line resolution note, or that got closed for other reasons.
2. Update §2's priorities in place — not "restated unchanged," actually re-verified against
   current RFC/`REGISTRY.md` state **and against the issue tracker**, which is where the
   claim "this is a priority" either is or isn't cashed out. **Note the two parts of §2 are
   updated differently**: the priorities *table* is overwritten each cycle (current state
   only); the prose subsections beneath it are append-only, like §3's triggers — see
   `PROCESS.md` §1.
3. Add any new triggers this cycle surfaced.
4. Append one line to §4's review log.
5. Update `last_reviewed` above.
6. *Then* write the dated narrative snapshot, if one is warranted — this document changing
   is not itself always enough to justify a new dated file; see `internal/rfcs/PROCESS.md`'s
   note on event-based rather than calendar-based triggers for that, and this directory's
   own `PROCESS.md` §5 for how triggering decisions stay human-prompted.

---

## 0. At a glance

*Added 2026-08-01, in response to the operator naming this document's own scalability
problem: no single place answered "what are we doing and why" without reading the full
history below. This section is **overwritten each cycle** — current state only, no
history — unlike everything below it. For history, read §§1–4 and the dated overviews.*

**Top priorities right now:** (1) Records/views — 3 of the 6-way RFC-0090 split
(RFC-0115/0116/0118) shipped `4-implemented`; RFC-0117/0119/0120/0121 untouched,
`0-draft`. (2) Ownership/borrow-checking — RFC-0071 `3-integrated`, substantially built
and enforced opt-in via `--move-check`; RFC-0122 (borrow checking) still `0-draft`.
(3) Brands/context parameters and (4) allocators: untouched, as designed.
**RFC-0122 (Borrow Checking) was accepted and reverted to `1-under-review` on
2026-08-01** — six gaps found immediately after acceptance, three blocking (§2b). Third
such reversion in the corpus; Trigger 14 fired. **Its liveness model then changed from
lexical to NLL** (§2.2, superseding the same day), which dissolves one of the three
blockers outright; Polonius considered and recorded as a named future option (§2c),
gated on Metel acquiring a CFG/MIR it does not have.

**Needs a decision from the operator, not just the agent:** whether RFC-0122 can
realistically still clear `2-accepted` before the `v0.12.0` tag, given §2b.2 (specify the
outlives rule) is genuine design work. *(The stored-reference restriction is no longer
open — reasoned, scoped, migration-checked, and tracked as #364 with its exit condition
fixed to RFC-0067's implementation.)*

**Latest dated overview:** `strategic-overview-2026-08-01.md`. **Latest review:**
2026-08-01 (see `last_reviewed` above).

### Operator directives

*Append-only, most-recent-first. Distinct from §2's derived priorities: this is where
you state an explicit priority call or redirect directly, rather than it being
reconstructed later from a decision made mid-conversation about something else (as
happened, e.g., with the RFC-0090/RFC-0100 splits — real steering moments, only
recorded after the fact by whichever cycle's writer noticed them). Every cycle checks
§2 against this section and must flag, not silently resolve, any place they disagree.
Logged proactively — any time an explicit steering call is made, in any conversation,
not only during a strategic-overview cycle — per `PROCESS.md` §1.*

**2026-08-01 — RFC-0122 specifies NLL (borrow dies at last use), superseding the
earlier lexical-first decision.** The operator revisited the lexical call after the
reversion, asking whether a Polonius-style checker was feasible from the start. It is
not, cheaply: Polonius is Datalog over **program points** and presupposes a CFG, which
Metel has no form of — the pipeline has no MIR/IR and `move_check` walks the typed AST.
**NLL, however, is reachable without one**, because Metel's control flow is fully
structured (zero `goto`/labels in the grammar), so the AST is a reducible CFG and
AST-directed dataflow has equivalent power — `move_check`'s own 4357-line loop
fixed-point is the in-repo proof. NLL also *dissolves* §2b.1's bug rather than patching
it: under last-use liveness, `c.bump(); c.bump();` needs no temporary-vs-`let`-bound
exception. **The earlier reversibility argument for lexical is withdrawn as weak** — it
protects against breaking downstream users, and Metel has one operator and a 732-fixture
corpus, while lexical's cost (rejecting idiomatic code, migrating the corpus, then
un-migrating) is paid immediately.

**2026-08-01 — Polonius is to be recorded in RFC-0122 as a named future option, not
adopted.** What it would buy (NLL problem case #3, conditional reference returns), what
it costs (a CFG/MIR — a compiler-architecture commitment §1's corollary currently defers
as forward-structure budget), and the condition that would justify revisiting. Documented
rather than silently foreclosed.

**2026-08-01 — RFC-0122 reverts to `1-under-review`; its acceptance was premature.**
Decided immediately after acceptance, when a follow-up adversarial pass found six gaps,
three of them blocking-grade: the second headline rule (a borrow must not outlive its
referent) is named in the Summary but specified nowhere and is demonstrably unenforced;
reference-typed struct fields defeat the RFC's central claim that RFC-0067's anchors are
"a dependent, not a dependency"; and the lexical rule as written rejects `c.bump();
c.bump();`, a shape already passing in the test suite. **This is the third
accepted→under-review reversion (after RFC-0099 and RFC-0100) — Trigger 14's falsifier,
which asked exactly for a third.**

**2026-08-01 — reference-typed struct fields (`struct Holder { r: &P }`) are banned as
an explicitly temporary scaffold, with a defined exit.** Not a language design position:
Metel does not intend to forbid structs holding references. The ban exists so borrow
checking can be built without first designing and implementing lifetime anchors —
rejecting a stored reference that outlives its referent requires relating two independent
lifetimes, which no scope-based rule can do and which is precisely what an anchor is. Its
removal is triggered by **one event and no other: RFC-0067 (Lifetime Anchors) being
implemented.** Tracked end-to-end as **#364**, which owns both halves so the exit cannot
be lost across releases; RFC-0067 carries the reciprocal pointer so implementing anchors
surfaces the obligation. Reasoning in RFC-0122 §2d. **Migration cost verified as zero** —
no reference-typed field exists anywhere in the corpus or stdlib.

**2026-08-01 — RFC-0122 adopts lexical borrows first, not NLL.** Decided during a
joint review of the RFC. Adopts the RFC's own standing lean rather than overriding it:
tightening lexical → non-lexical later is backward-compatible (it accepts strictly
more), the reverse is not, so the cheap-to-reverse option goes first. Settles the one
genuinely blocking question in RFC-0122 §2.

**2026-08-01 — RFC-0122 is to reach `2-accepted` before the `v0.12.0` tag cuts**, not
deferred to v0.13.0. Reaffirms the original 07-24 bar rather than letting it slip, on
the basis that its only structural blocker (a standalone place abstraction, RFC-0071
§9b) was discharged by #291 this week, so what remains is a session of work rather
than the month the bar was originally sized against. Resolves the open question §0
raised for the operator; Trigger 27 tracks whether it lands.

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
| 1 | Records / views as the structural carrier | RFC-0115/0116/0118 **`4-implemented`** (#287/#288/#289), RFC-0117/0119/0120/0121 `0-draft`, untouched since the 07-24 split | **v0.12.0: #287/#288/#289 shipped** |
| 2 | Ownership enforcement and the borrow checker | RFC-0071 **`3-integrated`**, `impl_status: in-progress`; RFC-0122 **`1-under-review`** — accepted and reverted 2026-08-01 on six gaps (§2b); liveness model now **NLL** not lexical (§2.2), dissolving one blocker; §9b blocker *is* discharged by #291 | **v0.12.0: #290/#291 shipped + 19 hardening fixes; v0.13.0: #292/#293 + 6 more queued** |
| 3 | Brands and context parameters | RFC-0076 `0-draft`; RFC-0113 `1-under-review` | not started, **no issue** |
| 4 | Allocators — emergent synthesis, built last | RFC-0063/65/66/67/68/73/77 `2-accepted`, complete | deliberately not started |
| 5 | The interpreter as a feedback instrument | n/a | **all 19 open issues** |
| 6 | Adjacent design and demand-gated frontier | RFC-0092–0095 `0-draft`; RFC-0026 stale | not started |

**Read that table's last two columns together — that is this cycle's central finding.**
Priorities 1–4 hold every RFC the project calls foundational and, between them, zero open
issues. Priority 5, which this document had never ranked at all until today, holds all of
them. This is not the same claim as 07-20's Trigger 17 ("ergonomics churn substituted for the
stated priority"); it is structural. The stated priorities and the tracker do not intersect.

**Update, 2026-08-01: the gap this finding named has closed, for one milestone.**
`v0.12.0` shipped 23 issues, all now closed, almost all against Priorities 1–2 — RFC-0071
reached `3-integrated` and is substantially built (move checking, `Copy`/`Drop`, the
reference-through-a-borrow rules), and RFC-0115/0116/0118 all reached `4-implemented`.
`v0.13.0` already queues nine more Priority-2 items. Priority 5's own backlog is
unchanged in size — the correct reading is not "the ranking pulled effort toward
Priorities 1–2," it is "building RFC-0071 forced nineteen correctness fixes as a
byproduct, and Priority 5 was simply not visited." See
`strategic-overview-2026-08-01.md` for the full account, including where this reading
needs to stay precise (the interpreter still deep-clones every value at runtime; only
the static check is new) and where it fell short (RFC-0122 did not reach the
`2-accepted` bar set for it the same day this finding was written).

### Release plan — v0.12.0 *(added 2026-07-24, after v0.11.0 shipped)*

**Scope decided:** RFC-0116 (Anonymous Record Types) + RFC-0118 (Row Bounds) + RFC-0071
(Ownership and Move Semantics) + RFC-0115 (Field Initializer Separator), with RFC-0122
(Borrow Checking) drafted in parallel as design only.

**RFC-0115 was pulled in on 2026-07-24, and RFC-0116 is what makes it close to mandatory
rather than merely convenient.** RFC-0116 ships `{ x = 1.0 }` as the anonymous record
value form. Shipping that *without* RFC-0115 would release this into a tagged version:

```metel
{ x = 1.0 }         // anonymous record — RFC-0116, v0.12.0
Point { x: 1.0 }    // nominal struct   — unchanged, differs by separator for no reason
```

— i.e. it would ship the exact mismatch RFC-0115 exists to remove, as a user-visible
inconsistency, and then break it again later. Either both ship or neither does. Batching it
here is also cheap in breakage terms: v0.12.0 already carries RFC-0071, by far the most
breaking change the language will take.

**Its migration is larger than its own §3 first claimed** — corrected there the same day.
573 literal sites change; **382 declaration lines must not**; and declarations, patterns and
literals share brace syntax and co-occur on single lines (`stdlib/core.mtl:42` has a pattern
and a literal in one expression). A regex sweep will corrupt declarations; this wants a
parser-driven rewrite over `FieldInit` spans, which is cheap because the parser already
tells the three apart.

**One accepted risk:** RFC-0100 (`1-under-review`) proposes retiring brace literals
entirely. If it later lands, these 573 sites migrate twice. Judged acceptable — RFC-0115 was
split out of RFC-0100 precisely so a settled question would stop being hostage to a
contested one, and reversing that to avoid a second mechanical pass would undo the split's
whole point.

**The reasoning, which turns on one fact.** The blog's short-term commitment is
"`ToRecord`/`FromRecord` working in the interpreter" — that is RFC-0119, and its chain is
`RFC-0119 → RFC-0117 → RFC-0071`. **No release delivers that commitment until RFC-0071 is
implemented.** Including it in v0.12.0 is therefore not ambition, it is the shortest path
to the stated goal; v0.13.0 then delivers RFC-0117 + RFC-0119 and the commitment is met.
RFC-0116 and RFC-0118 ride along because they depend on nothing at all and give the
release a visible records deliverable rather than a purely internal one.

**RFC-0071 is the risk, and it is larger than "accepted since June" suggests.** Checked
section by section against the interpreter on 2026-07-24:

| RFC-0071 § | State |
|---|---|
| §1 move by default | not started — 91 `.clone()` calls in `evaluator/mod.rs`, no move tracking anywhere |
| §2 `Copy` aspect | not started — zero declarations in `stdlib/` |
| §3 `Drop` aspect | not started — zero declarations in `stdlib/`, no drop tests |
| §4 `Copy`/`Drop` exclusive | **done** — one guard at `construction.rs:3661`, the only implemented part |
| §5 drop order | not started |
| §6 explicit `drop` | not started |
| §7 partial moves | not started — **this is what RFC-0117 needs**, so it cannot be descoped |

So RFC-0071 is essentially entirely unbuilt except a single guard clause, and §7 is
non-negotiable if v0.13.0 is to follow. It should be split into several tracked issues
rather than one, and it is plausibly larger than all of v0.11.0.

**Lifecycle prerequisites before any code.** `AGENTS.md` states an RFC gets a tracked issue
"only once it reaches `3-integrated`." Nothing is at `3-integrated` today — the stage is
empty. So: RFC-0116/0118 need `1-under-review → 2-accepted → 3-integrated`, and **RFC-0071
needs `3-integrated` too**, which it has never had despite being accepted for four weeks.
That integration step — spec merged, worked examples checked — is the gate, and it is where
Trigger 24's tracked issue finally becomes creatable.

**RFC-0122's completion bar, set 2026-07-24: reach `2-accepted` in v0.12.0, not merely accumulate prose.** Its two implementation-shaping questions are answered — granularity is per-field for statically-named fields and whole-value through a dynamic index; move and borrow checking are two analyses over one shared place abstraction. That converted the only real argument for pulling it forward into a single requirement on RFC-0071: **the place abstraction must be a standalone reusable component.** Given that, splitting the two across releases costs no rework.

**Out of scope, deliberately:** RFC-0008 (Aspect Objects, `2-accepted` since 07-01) stays
deferred as Phase 4; the seven accepted allocator RFCs stay Priority 4 ("built last"); and
RFC-0122 ships as a design document only, with no borrow checking in v0.12.0.

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
it the brand dependency *that came from fiat-linearity*. **That claim went through a
correction and a re-resolution the same day, and the sequence is worth keeping:** it was
first written as "the cluster's only dependency on RFC-0076", withdrawn as overstated once
reassembly provenance surfaced (RFC-0119 OQ8), then restored on different grounds when
RFC-0119 dropped its by-reference mode outright. Tier 2 is brand-free because it never
touches a borrow — structural, not incidental. RFC-0116 was unaffected throughout.

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

**2026-08-01: RFC-0116 and RFC-0118 both reached `4-implemented`** (#288, #289),
alongside RFC-0115 (#287) — real shipped code, not merely `3-integrated`. RFC-0116 in
particular closes Trigger 24 in the strongest way available to it: drafted and shipped
within the same week, well inside its own one-month falsifier. RFC-0117/0119/0120/0121
are untouched, still `0-draft`; the entry point built cleanly, the rest of the
decomposition has not yet been picked up. See `strategic-overview-2026-08-01.md`.

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

**2026-08-01: the first half moved, substantially.** RFC-0071 reached `3-integrated`,
`impl_status: in-progress`, tracked at #291. `v0.12.0` shipped `Copy`/`Drop` aspects
(#290) and move checking (#291) — loop-body fixed-point analysis, the `place`
abstraction lifted to satisfy RFC-0071 §9b's standalone-reusable requirement, and the
reference-through-a-borrow rules for both `&var self` (#347) and by-value `self`
(#348) — plus nineteen correctness fixes found while building it. It remains opt-in
(`--move-check`) and does not change the evaluator's own runtime semantics, which still
deep-clone every value regardless of what the checker concludes; enabling it by default
is itself queued (#310) in v0.13.0, alongside RFC-0071 parts 3–4 (#292 drop order,
#293 partial moves). **The second half is behind the pace this document's own 07-24 bar implied, though
not yet past it:** RFC-0122 gained real content that day (granularity and
move-vs-borrow questions answered, a dependency direction inverted) and nothing
substantive since. "Reach `2-accepted` in v0.12.0" is **still reachable, not missed** —
`v0.12.0` has no tag cut yet — but ten-plus days with no movement on a design-only
deliverable, this close to a release whose milestone issues are otherwise fully closed,
is worth naming as a live risk rather than assuming there's ample time left. See
`strategic-overview-2026-08-01.md`.

**Resolved same day, 2026-08-01: RFC-0122 reached `2-accepted`, clearing its bar before
the tag cut.** A joint operator review resolved the three remaining design questions —
**lexical borrows first** (chosen for asymmetric reversibility: lexical→NLL accepts
strictly more and needs no migration, the reverse breaks valid programs), observability
under a deep-cloning evaluator, and a specified `T0020` diagnostic format naming
bindings and scope ends rather than abstract lifetimes. It also brought call-site
argument aliasing (`both(&var x, &var x)`) explicitly into scope, and added a migration-
cost section requiring opt-in rollout behind `--borrow-check` rather than default-on
alongside #310. **The reason it moved in a session rather than a month is worth
recording:** its sole structural blocker, RFC-0071 §9b's standalone place abstraction,
had already been discharged by #291 — the stall was a stale premise, not a resourcing
problem. **Reverted hours later, the same day.** An adversarial pass found six gaps, three
blocking — the outlives rule (half the RFC's own stated scope) named in its Summary and
specified nowhere; reference-typed struct fields defeating its central claim that
RFC-0067's anchors are a dependent rather than a dependency; and the lexical rule as
written rejecting `c.bump(); c.bump();`, a shape already passing in the test suite.
RFC-0122 is back at `1-under-review` with those recorded as §2b. **Third
`2-accepted`→`1-under-review` reversion in the corpus, firing Trigger 14.** Move
checking's half of this priority is genuinely specified and built; the borrow half is
not, and the day's net movement on it was zero plus a better-documented gap list.

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
of what was watched for and what actually happened is part of the point. **Once a
trigger has been closed for at least two review cycles and isn't the subject of an
active priority's own narrative section, it moves to `triggers-archive.md`** (verbatim,
never renumbered) with a one-line stub left in its place here — see `PROCESS.md`. This
keeps the active list scannable without losing the record.

1. ✅ **[Archived — see `triggers-archive.md`]** Fired 2026-07-09; caused the
   RFC-0012 → RFC-0092/0093/0094/0095 split.
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
5. ✅ **[Archived — see `triggers-archive.md`]** Fired and resolved 2026-07-10; caused
   the former Priority 1 (allocator/lifetime cluster) to ratify.
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
8. 🟡 **[Archived — see `triggers-archive.md`]** Fired repeatedly through 07-15; the
   `3-integrated` worked-examples mechanism works. Superseded as a watch item by Trigger 13.
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
11. ✅ **[Archived — see `triggers-archive.md`]** Re-evaluated and closed 2026-07-15;
    the former-Priority-1 analogy did not hold. Signal retained in Priority 6's form.
12. ✅ **[Archived — see `triggers-archive.md`]** Fired and resolved 2026-07-15; six
    RFCs at `3-integrated` reached `4-implemented` within four days.
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
    **🟡 FIRED 2026-08-01 — RFC-0122 is the third.** This trigger's falsifier was
    explicit: *"If a third RFC follows the same path, that's evidence `2-accepted`'s own
    bar is being called too early in practice."* RFC-0122 was accepted and reverted to
    `1-under-review` the same day, on six gaps (three blocking) found by an adversarial
    pass immediately after acceptance. **The evidence the trigger asked for now exists,
    and it points at a specific mechanism rather than at carelessness in general:** in
    all three cases the accepting review checked the questions *the RFC itself had
    listed* and treated that list as complete. RFC-0122 makes this unusually legible
    because its §2 was an explicit five-item checklist, every item genuinely resolved —
    and the RFC was still missing half of its own stated scope (the outlives rule,
    promised in its Summary, specified nowhere).
    **The concrete change this suggests, for whoever acts on it:** `2-accepted`'s bar
    should be read as *"no open question blocks it"*, not *"every question the RFC asked
    is answered"* — and the cheap check that would have caught all three is to re-read
    the RFC's own Summary/Scope against its resolutions and ask what is promised there
    but specified nowhere. That check takes minutes and is not currently written down in
    `internal/rfcs/PROCESS.md`.
    **One distinguishing feature worth not flattening:** RFC-0099/0100 were reverted
    during *integration*, by problems the accepting review could not easily have seen.
    RFC-0122 was reverted minutes later, by a question anyone could have asked of the
    same document — a cheaper failure to catch, and a worse one to have made.
15. ⬜ **Open, 2026-07-15.** `metel-core` PR #270 was found fully superseded by direct commits
    on `sprint/26` that reimplemented the same feature with the newer `extend` syntax. Watch
    whether a cheap repeatable check ("does an open PR's branch still contain work not already
    on the target branch") gets added anywhere — this instance was only caught by an explicit
    pull-and-compare.
16. ✅ **[Archived — see `triggers-archive.md`]** Fired and resolved same day, 07-20:
    RFC-0097 frontmatter/reality drift fixed by landing the real check.
17. ✅ **[Archived — see `triggers-archive.md`]** Opened and answered 2026-07-20/21: both
    ergonomics churn *and* a same-cycle self-correction happened. Superseded by Trigger 20.
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
    **Partially addressed, 2026-07-24: RFC-0122 (Borrow Checking) was opened.** Its two
    implementation-shaping questions were answered the same day. **Update, 2026-08-01:
    it did not reach `2-accepted`**, the bar this document set for it in v0.12.0 — no
    substantive change to the file since 07-24. Still open; the RFC exists now, but the
    trigger's underlying worry (borrow checking cited as a known quantity without being
    specified enough to build) is only partially retired. Watch whether v0.13.0 restates
    a completion bar or lets it lapse a second time.
    **Substantially resolved, 2026-08-01: RFC-0122 reached `2-accepted`.** The borrow
    checker now has a specified, accepted rule set — headline rule, granularity,
    liveness model, diagnostics, and rollout constraint — rather than being cited as a
    known quantity by documents that had never specified it, which is exactly what this
    trigger was opened against. **Kept open, narrowed:** acceptance is not
    implementation, and nothing enforces any of it yet. The trigger's remaining question
    is whether the accepted rules actually get built, or whether "RFC-0122 is accepted"
    becomes the new way of citing borrow checking as settled while the interpreter still
    enforces nothing.
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
    **✅ Closed, 2026-08-01 — not by one issue, by an entire milestone.** `v0.12.0`
    shipped 23 issues, all now closed, almost all against Priorities 1–2: RFC-0071
    reached `3-integrated` (#290/#291 plus nineteen hardening fixes found while building
    them), RFC-0115/0116/0118 all reached `4-implemented` (#287/#288/#289). `v0.13.0`
    already queues nine more Priority-2 items. This is the strongest resolution this
    trigger's falsifier could have received — no stronger evidence exists short of a
    full release. See `strategic-overview-2026-08-01.md` for the precise reading:
    Priority 5's own backlog did not shrink either, so the mechanism was necessity
    (bugs found while building), not the ranking pulling effort toward Priority 2.
21. ⬜ **New, 2026-07-22.** Priority 5 is new and is the priority most likely to expand to fill
    the available effort, because its work is the most immediately satisfying — every issue in
    it is well-scoped, verifiable, and finishable in a session, which is precisely what the
    substrate work is not. Watch whether ranking it fifth actually constrains it, or whether
    naming it legitimises it and the ratio gets worse. If the next cycle closes several
    Priority 5 issues and opens none against 1–3, ranking it did nothing and the ordering
    should be treated as descriptive rather than directive.
    **Refuted for this cycle, 2026-08-01 — but check the mechanism, not just the
    count.** Priority 5's backlog is unchanged in size; nothing in it was closed this
    week. But that is not evidence the ranking constrained anything — it is evidence
    that this week's effort was pulled toward Priority 2 by necessity (nineteen
    correctness bugs found while building RFC-0071), not chosen from a priority-ordered
    list. Watch whether a future cycle without an RFC-0071-shaped forcing function
    produces the same result, or whether this one only held because there was
    something urgent enough to hold it.
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
    **✅ Closed, 2026-08-01 — yes, unambiguously.** RFC-0071, RFC-0116, RFC-0118, and
    RFC-0115 all produced real interpreter changes this week, not further RFC-text-only
    findings. The middle state this trigger was watching for turned out to be a real
    waypoint on the way to building, at least in this instance — not a comfortable
    substitute for it. See `strategic-overview-2026-08-01.md`.
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
24. ✅ **Fired 2026-07-24, the same day it was opened — by RFC-0115, not RFC-0116.**
    Issue **#287** exists: the first tracked issue against any of Priorities 1–4, ending a
    run this document had counted at eight days. A `v0.12.0` milestone was also created,
    re-establishing a convention dormant since v0.7.0 — v0.8 through v0.11 all shipped
    without one.
    **Counted honestly, this is a partial trip, not a clean one.** The falsifier named
    RFC-0116 specifically, and RFC-0116 is still `1-under-review` with no issue; what
    actually cleared the gate first was RFC-0115, a one-grammar-line change that was not
    even in the plan until it was pulled in. The mechanism that forced it is worth naming
    because it was not willpower: `rfc.py transition --to integrated` **refuses to run
    without `--tracking`**, so reaching `3-integrated` made the issue mandatory rather than
    virtuous. That is a tooling constraint doing what eight days of intent did not, and it
    suggests the useful lever is the gate, not the resolve.
    **Closed later the same day: RFC-0116 reached `3-integrated` and is tracked as #288** —
    the RFC this falsifier actually named. Its integration did what integration is for: the
    grammar-feasibility question was settled by *building* the change (a `record_lit`
    alternative added to `primary_expr`, 755 tests green, then reverted), which also found
    a better reason for the answer than the RFC had — Metel's parenthesised conditions make
    Rust's struct-literal ambiguity structurally impossible — and turned up one real sharp
    edge (`block` is tried before `expr` in an if-branch, so a bare `{ x }` there is a block
    with tail `x`, never a punned record).
    **RFC-0118 and RFC-0071 remain short of `3-integrated` and un-issued**, so v0.12.0 is
    two of four. The lesson recorded above stands unchanged and is the durable part: the
    tooling gate, not intent, is what produced all three artifacts.
    **Update, 2026-08-01: all four caught up.** RFC-0118 and RFC-0071 both reached
    `3-integrated` and beyond — RFC-0071 is now `impl_status: in-progress`
    (tracked #291), and RFC-0116/0118 both reached `4-implemented` (#288, #289) the
    same week. `v0.12.0` closed all 23 of its issues. The falsifier this trigger
    named is now moot in the strongest possible way: not just tracked, but shipped.
25. ⬜ **New, 2026-07-24. The split's whole promise is that RFC-0116 is buildable today —
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
    **✅ Closed, 2026-08-01 — RFC-0116 reached `4-implemented` within the same week
    it was drafted**, weeks inside its own one-month falsifier. The decomposition's
    promise held for its entry point; RFC-0117/0119/0120/0121 remain `0-draft` and
    untouched, so the rest of the six-way split has not yet been tested the same way.
26. ⬜ **New, 2026-08-01.** The standing meta-risk sentence (§1), quoted unchanged for
    seven cycles specifically because it stayed entirely true, is now partially false:
    "no move-semantics enforcement" no longer holds — `--move-check` is real and
    tested. "The interpreter still deep-clones" still holds, exactly as before; the
    checker is a static analysis layered on an evaluator whose runtime semantics have
    not changed at all. Watch whether the next cycle rewrites that sentence with this
    precision or lets an imprecise "move semantics: done" stand in for it — the
    engineering-side version of exactly what Trigger 22 watched for on the design side.
27. ⬜ **New, 2026-08-01.** RFC-0122 missed its own stated bar: "reach `2-accepted` in
    v0.12.0, not merely accumulate prose" (written 2026-07-24, this document). It
    accumulated real prose that day and nothing substantive since, and did not reach
    `2-accepted`. Not urgent — the release always scoped it design-only — but a
    self-imposed bar lapsing without comment is the pattern this document exists to
    catch elsewhere (Triggers 14, 16). Watch whether v0.13.0 restates a bar for it
    explicitly or lets it drift a second time.
    **Corrected same day, 2026-08-01 — this trigger overstated its own claim, caught by
    the operator.** RFC-0122 has **not** missed the bar: `v0.12.0` has no tag cut on
    `main` yet (the milestone's issues being closed is a tracker convenience, not a
    release), so "reach `2-accepted` in v0.12.0" remains reachable, not lapsed. What is
    actually true and worth keeping the trigger open for: RFC-0122 has had no
    substantive change since 07-24, which is behind the pace the bar implied, and stays
    a live risk to whether it clears `2-accepted` before the tag is actually cut. This
    is exactly the verification-discipline failure `PROCESS.md` §2 warns about —
    "the RFC hasn't shipped" was inferred from the issue tracker's closed milestone
    rather than checked against `git log origin/main..origin/develop` and the absence
    of a `v0.12.0` tag, which was sitting right there the whole time.
    **✅ Closed, 2026-08-01 — the bar was met, before the tag cut.** RFC-0122 reached
    `2-accepted` in a joint operator review the same day: questions 2, 4 and 5 resolved
    (lexical-first, observability, a specified `T0020` diagnostic format), staleness
    corrected, call-site argument aliasing brought explicitly in scope, and a migration-
    cost section added requiring it ship opt-in behind `--borrow-check` rather than
    default-on alongside #310. **What actually unblocked it was not effort but a fact
    nobody had checked:** RFC-0122's sole structural blocker — RFC-0071 §9b's
    standalone place abstraction — had already been discharged by #291 days earlier, so
    the bar this trigger was worrying about was a session's work, not the month it had
    been sized against. Worth keeping as the lesson: the trigger correctly flagged a
    stall, and the stall turned out to be a stale premise rather than a resourcing
    problem. See Trigger 19, which this partially resolves.
    **⬜ Reopened hours later, 2026-08-01 — the acceptance was reverted.** An adversarial
    pass found six gaps (three blocking) and RFC-0122 returned to `1-under-review`. So
    the bar was *not* met: this trigger's closure above was premature in exactly the way
    the RFC's acceptance was, and for the same reason — it took "all five §2 questions
    resolved" as equivalent to "nothing blocks it." **Kept open with its falsifier
    unchanged** (reach `2-accepted` before the `v0.12.0` tag cuts), now with §2b's six
    gaps as the concrete remaining work. Whether that is still achievable pre-tag is a
    real question and not a rhetorical one: §2b.2 (specify the outlives rule) and §2b.3
    (ban reference-typed struct fields, per the operator directive in §0) are both
    genuine design work, not editing.
28. ⬜ **New, 2026-08-01.** A calibration data point, tracked here because it belongs
    somewhere durable rather than only in the conversation that produced it: the
    week's final PR (#348, by-value-`self`-through-a-reference) needed a full second
    pass after adversarial review found three real defects in its first commit — a
    silent bypass for non-place receivers, an under-counted multi-layer-reference
    diagnostic, and a missing `Copy` gate that would have wrongly rejected legal code.
    None cosmetic; none caught by the author's own first-pass verification. Not itself
    a trigger about design/tracker alignment like the others here, but worth watching
    whether this rate (three real defects per adversarially-reviewed PR) is typical or
    was one unusually dense instance, since it bears on when a deeper personal
    implementation review becomes warranted.

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
| 2026-07-24 | **RFC-0114 and RFC-0100 revised together, and the pairing was the point.** RFC-0114 carried stale syntax in three independent ways — freestanding `.{ … }` rows (superseded by `access-and-presence-rows.md` §3.5's receiver-based split the day before), and two *pre-RFC-0098* spellings (`extend Type: Aspect`, `&var`) despite the RFC post-dating that RFC's implementation by nine days. Correcting the examples exposed a real hole the stale syntax had hidden: **`construct`'s own body had no way to build a `Self`** — the first draft used the bare literal §2 abolishes, and the synthesized default `Ok(row)` did not typecheck as written. New §1.1 confines row-to-`Self` to `construct`/`construct_unchecked` and nowhere else, which also **resolved that RFC's open question 5** (hand-written `new` needs no separate enforcement, because no primitive remains available to it) and raised a new one (8: `extend` blocks have no visibility modifier, so canonical construction may hand every struct a public constructor unless private field labels are unwritable from outside — RFC-0090's question, not RFC-0114's). RFC-0100 adopted `=` for keyword arguments per the separator invariant, which **dissolves the collision it was reopened over** rather than answering it; §3 rewritten around the smaller `assign_expr` collision `=` trades into, with the superseded ascription analysis kept behind a fold. Trigger 14 updated — and deliberately *not* as a vindication: review surfaced a real problem and mis-diagnosed its cause, which is a different failure from accepting too early. **Second consecutive day that findings reached RFC text with no tracked issue filed** — exactly the middle state Trigger 22 was opened to watch, now recurring rather than isolated, and Trigger 20's falsifier is untripped for an eighth day. **Later the same day, on the user's decision, RFC-0090 dropped the `record` keyword from the anonymous type-former** (`{ x: f64 }` as a type, `{ x = 1.0 }` as a value), completing the adoption of `access-and-presence-rows.md` §3.5 — the keyword now does exactly one job, minting nominal identity at `record X { ... }`, which also let open question 8 be folded into §8's prose instead of contradicting it. The change has a real cost, recorded as new open question 13 rather than glossed: closed record types and row bounds are now spelled identically and told apart by grammatical position alone, and one bullet in §2 that asserted the old distinction was wrong the moment the keyword went and had to be corrected. ~141 uses of the old spelling remain across RFC-0091/0109/0089 and the design reports — deliberately not swept, and named in RFC-0090's own revision note so the gap is visible rather than discovered later. **Then, on the user's call, RFC-0100 was split** — the separator fix (`field_init`'s `:` → `=`, braces kept) extracted as new draft **RFC-0115**, leaving call-shaped construction and general keyword arguments in RFC-0100. The trigger for the split was the user's observation that construction could keep its brackets and change only the separator; working it through found that version stronger than what was in RFC-0100 on four independent counts (it aligns nominal literals with RFC-0090's just-settled `{ x = 1.0 }` anonymous records, making `Point { x = 1.0 }` literally a row plus a brand; it restores the construction/destructuring symmetry RFC-0100 §4 had apologized for; it carries **zero** grammar risk where both prior proposals carried a real collision; and it frees the invariant from an under-review RFC). **RFC-0100 is honestly weaker for the split and now says so** — it lost the invariant argument to RFC-0115. **RFC-0114 gained the most:** reworking §2 showed its RFC-0100 dependency was never real — a literal that desugars to `construct` is not a bypass — so it now has no blocking dependency on any under-review RFC, and its open question 2 resolved by dissolving its premise. Still no tracked issue filed; Trigger 20's falsifier untripped for an eighth day, now against a *larger* body of RFC text. **Finally, a notation change that fixed a real ambiguity rather than a preference:** inside projection braces a bare identifier could be either a field label or a row variable (`Handle.{ fd }` vs `Handle.{ R }`), separated only by case convention — and RFC-0101, which would make that convention normative, is `0-draft`. So the design was leaning on an unratified RFC to disambiguate something it never acknowledged as ambiguous. Fixed by adopting **`row` declares, `..` marks every use**: a row variable is `..R` at every use site, a bare identifier in type position is always a *type* variable. The same mechanism with the variable left unnamed (`T: { x: f64, .. }` = "at least x") **resolved open question 13 the same day it was opened** — the closed/open bound distinction now turns on a token instead of on grammatical position, and the closed *bound* reading, previously inexpressible, became writable. Propagated through RFC-0090/0091/0109 and both exploration docs; RFC-0109 checked and found already conformant. New open question 14 opened for row *operations* (`R without "token"`, `R + "auth"`), which still use the string-literal-in-type-position form retired for bounds on 07-23 and now have no specified precedence, arity, or grammar — **and resolved the same day, in new RFC-0090 §2.1, by deleting the operators rather than fixing them.** A prior-art pass (PureScript, Ur/Web, Haskell `row-types`, OCaml, Koka, TypeScript, Elm) found that **extension needs no syntax at all** — every row-typed language writes the new label *inside the row literal*, which for Metel is the spread tail it already has (`{ ..R, auth: String }`), and the string literal was only present because an infix operator had nowhere else to put the name. Only **removal** lacked a form, and it becomes a where-clause decomposition (`where R = { token: Token, ..Rest }`), following PureScript's `Prim.Row.Cons` rather than Ur/Web's `--`. Cost: one grammar addition, no label literal, no label kind, no operators; the equation also subsumes the bound it replaces, and `=` is the invariant-correct separator (it equates), matching the `assoc_binding` equation already in that channel. Elm — the one language that shipped row extension/restriction and then **withdrew both** — is recorded as the standing caution. **The pass also found a third unbacked construct nobody had noticed:** `drain_field<row R, name: Symbol, T>` invents a `Symbol` *kind* that exists nowhere (the corpus's only `Symbol` is RFC-0059's compiler-internal `SymbolId`), spells it in bound position where the grammar reads it as an aspect bound on a *type* variable — inconsistent with `<row R>`'s prefix-keyword pattern sitting in the same parameter list — and indexes with `s.[name]`, which `postfix` does not accept. Opened as RFC-0091 open question 4, deliberately **not** folded into the §2.1 resolution: that retires the label *literal*, but `drain_field` needs label *polymorphism*, a strictly stronger capability (a label kind, a label literal, an index-by-label form, and rules for all three). Named explicitly because if it resolves to "no", RFC-0109's Motivation needs editing — it cites the generic `drain_field` as the reusable half records give and Rust's view types cannot. **The cycle then ended by settling Trigger 6 and decomposing the cluster on that basis.** The question resolved not as yes-or-no but as *the dependency was accidental*: RFC-0089's floor was rewritten from Option B to `ToRecord` by its own same-day revision on 2026-07-09, which is exactly why the trigger could observe that "neither RFC states the conflict" — neither chose it. Per-field multiplicity was always meant to wait for records. **RFC-0090 superseded by six RFCs partitioned by dependency depth** (RFC-0116 Anonymous Record Types, 0117 Row Narrowing, 0118 Row Bounds, 0119 Record Conversions, 0120 Named Records, 0121 Open Rows); **RFC-0089/0091/0109 returned to `0-draft`**; RFC-0089 §3 marked as not the specified floor, with §1–2/§4–5 noted as the half that was independently acceptable all along and blocked only by sharing a document. No feature dropped, no design decision reversed — a re-partition, and PROCESS.md's own named pathology (RFC-0012's 18 open questions before its split; RFC-0090 had 14). **The largest consequence was unplanned:** dropping fiat-linearity from the records path removes the brand-carrying `ToRecord` exception and with it the brand dependency that came from fiat-linearity — the coupling's removal made the design simpler, which is the strongest evidence it was accidental. **Corrected hours later, in the same cycle:** this was first recorded as removing the cluster's *only* RFC-0076 dependency, which overstated it. A follow-on conversation about `FromRecord`'s relationship to `Construct` surfaced that **reassembly through a `&var` view needs provenance, not shape** — the compiler must know all the borrows belong to one struct instance — and that whether this is free depends on a question the corpus answers two ways: a view as a *borrow of a record* (RFC-0119 §2's own signature, one pointer, sound by construction) versus a *record of borrows* (`access-and-presence-rows.md` §3, which argues that reading is better, and under which `from_record_mut` is unsound without an identity check). An identity check means a brand, which means RFC-0076 returns and collides with tier 2's bare-ness. Recorded as RFC-0119 OQ8 with three ways out, the most promising being to drop by-reference conversion from tier 2 entirely and let RFC-0109's branded views own the borrowed case. Three further questions opened alongside it (RFC-0119 OQ5–7, OQ9; RFC-0114 OQ9–10), including a **direct contradiction between RFC-0114 §3 and RFC-0119 §2** that neither document had noticed. **RFC-0116 is untouched by all of it**, which is the one thing that matters for Trigger 24. **Then, on the user's call, `to_record_mut`/`from_record_mut` were dropped from tier 2 outright** — the third of RFC-0119 OQ8's own three options. The chronology carried the argument: `to_record_mut` was added 2026-07-08 with the commit message *"resolving tier 2's borrow gap"*, ten days before RFC-0109 built that mechanism properly as branded named views. It was what the design reached for before the right tool existed. **This dissolved three open questions at once** (OQ6's by-value/by-reference asymmetry, OQ7's direct contradiction with RFC-0114 §3, OQ8's provenance hole) rather than answering any of them, and put the tier boundary on a clean line: *by-value conversion is bare because it is by-value; borrowed access is branded because it must be.* Recorded honestly as **not pure redundancy removal** — the dropped construct also permitted moving a field *out* through a borrow, which views do not replace and nothing else in the cluster provides; Rust forbids it too, so it is defensible, but it is a capability lost rather than relocated, and RFC-0109 now carries the note. RFC-0114 §3 stands unamended and is now the only story for row completion. RFC-0071 (`2-accepted`, 0% implemented) remains, gating RFC-0117 onward but **not RFC-0116**, which is why the split is six-way. Trigger 24 opened as the falsifier: RFC-0116 is now the small, genuinely unblocked entry point, and if a month passes with no issue filed against it, the decomposition was a more sophisticated form of not starting. **One correction to record against this session's own work:** the `FromRecord` proposal was written up as *collapsing* it into `Construct` — one aspect instead of two — and a fatal-looking objection raised against that (universal `Construct` synthesis would make every struct tier 2, collapsing the tier boundary). **That was not the proposal.** The actual one keeps `FromRecord` a separate opt-in aspect and reuses only the constructor *call syntax* (`Handle({row})`) and `construct` as its *default logic* — capability and logic separated, tier gate untouched, objection inapplicable. RFC-0119 OQ5 and RFC-0114 OQ9 rewritten. A further claim built on the misreading is withdrawn with it: that the tier gate could become *visibility*, making RFC-0114 OQ8 and RFC-0116 OQ3 "the same question asked three ways." They are not; the visibility question stands on its own. Logged because the failure was in restating a proposal rather than in evaluating one, and the evaluation that followed was confident. **Both ideas were then deferred, on the user's call and correctly:** working them through showed each depends on something unsettled — the call-syntax proposal on RFC-0100 (`1-under-review`, reopened once) for what `Handle(r)` means positionally, and the marker/destructuring proposal on a struct pattern that does not exist in the grammar plus RFC-0109, itself now deferred. Neither is refused and neither gates RFC-0119, which is complete and reviewable without them; they would change the spelling and the derivation default, not the capability. Revisit once records are implemented, when there will be real usage to judge them against. **Net effect of the last four exchanges on the critical path: nil, by design** — every finding landed in RFC-0114/0119, and RFC-0116 was untouched throughout. | *(none)* |
| 2026-08-01 | **The first cycle where Priority 1/2 engineering, not design prose or Priority 5, consumed nearly all of a review period.** `v0.12.0` shipped 23 issues (all closed): RFC-0071 reached `3-integrated`/`impl_status: in-progress` (#290 `Copy`/`Drop`, #291 move checking — loop fixed-point analysis, the `place` abstraction lifted to RFC-0071 §9b's standalone bar, reference-through-a-borrow rules for `&var self` and by-value `self`), plus nineteen correctness fixes found while building it (#296, #313, #314, #321, #334, #343, #345, #347, #348, among others). RFC-0115/0116/0118 all reached `4-implemented`. Triggers 20, 22, and 24 closed — not by a token issue each, but by the milestone itself; Trigger 24 in particular resolved inside its own one-month falsifier. Trigger 21 refuted for this cycle but with a caveat recorded precisely: Priority 5's backlog didn't shrink, which means the mechanism was necessity (bugs found while building), not the ranking pulling effort — worth re-testing without an RFC-0071-shaped forcing function present. Trigger 19 partially addressed (RFC-0122 exists, two real questions answered) but not resolved: it is behind the pace of its own 07-24 bar of reaching `2-accepted` in v0.12.0, newly named as Trigger 27 rather than left silent — **corrected same day: not actually missed, since `v0.12.0` has no tag cut yet; caught by the operator, not by the cycle's own verification.** New Trigger 26 flags that the seven-cycle-old meta-risk sentence (§1) is now partially false and needs a precise rewrite, not a checkbox — move-semantics enforcement exists, but the interpreter's runtime still deep-clones every value regardless. New Trigger 28 records a calibration data point outside this document's usual scope: the week's final PR needed three real post-review corrections, none caught by the author's own first pass, relevant to a separately-tracked question about when a deeper implementation review is warranted. Priority 3 (brands, context parameters) untouched. One new, unranked draft (RFC-0127, associated functions on generic types) opened the same day, closing a gap found while investigating an adjacent question. `develop` sits 134 commits ahead of `main`/v0.11.0 with `v0.12.0`'s milestone fully closed but no tag cut yet. | `strategic-overview-2026-08-01.md` |
| 2026-08-01 (2nd) | **RFC-0122 (Borrow Checking) reviewed jointly with the operator and accepted**, clearing the v0.12.0 bar Trigger 27 had flagged, before the tag cut. Three remaining design questions resolved: **lexical borrows first** (asymmetric reversibility — lexical→NLL accepts strictly more and needs no migration; the reverse breaks valid programs), observability under a deep-cloning evaluator (answered by precedent: move checking found six real defects over the same runtime this release), and a specified `T0020` diagnostic format naming bindings and scope ends. Call-site argument aliasing (`both(&var x, &var x)`, verified accepted today) brought explicitly in scope — it is a checking question, not the naming question §1 had deferred to RFC-0067. New §3 costs corpus migration and requires opt-in rollout behind `--borrow-check`, not default-on alongside #310. **The unblocking fact was a stale premise, not effort:** RFC-0122's sole structural blocker (RFC-0071 §9b's standalone place abstraction) had already been discharged by #291 — verified directly at `src/place.rs`, 203 lines, crate root, every "move" mention doc-comment only. Staleness corrected (RFC-0071 cited as `2-accepted`, actually `3-integrated`; `&var` count nine→ten). Triggers 27 closed, 19 narrowed to "accepted is not implemented." **First cycle exercising §0's new Operator Directives log** — both decisions recorded there as they were made, not reconstructed afterward. | *(none — no dated snapshot; this is an artifact-level change, not a review cycle)* |
| 2026-08-01 (3rd) | **RFC-0122's acceptance reverted the same day; Trigger 14 fired.** An adversarial pass immediately after acceptance found six gaps, three blocking, all verified against the built interpreter: the **outlives rule** — half the RFC's own stated scope, promised in its Summary — is specified nowhere and unenforced (`fun leak() -> &P { let local = …; return &local; }` is accepted); **reference-typed struct fields** (`struct Holder { r: &P }`) are constructible and can outlive their referent today, which defeats the RFC's central claim that RFC-0067's anchors are "a dependent, not a dependency," since no scope-based rule can relate two independent lifetimes; and **§2.2's lexical rule as written** ("live from creation to end of enclosing scope") rejects `c.bump(); c.bump();`, a shape already passing in `move_check`'s own suite — the temporary-vs-`let`-bound distinction Rust had pre-NLL was omitted. Also unaddressed: closures (zero mentions), reborrowing (listed in scope, specified nowhere), and RFC-0126's `Copy` `T[]` borrowed view (zero mentions, and already shipped in v0.12.0). Recorded as RFC-0122 §2b; RFC returned to `1-under-review`; Trigger 27 reopened with its falsifier unchanged. **Trigger 14's falsifier — "if a third RFC follows the same path" — is met (after RFC-0099, RFC-0100), and the shared mechanism is now identifiable:** all three accepting reviews checked the questions the RFC itself listed and treated that list as complete. `internal/rfcs/PROCESS.md` gains the cheap counter-check (re-read the Summary and Scope against the resolutions; anything promised but unpointable is an open question the RFC did not know it had). Operator directive: **ban reference-typed struct fields for now**, keeping the outlives rule scope-based — a real language restriction, not yet tracked. | *(none — same-day correction, not a review cycle)* |
| 2026-08-01 (4th) | **RFC-0122's liveness model changed from lexical to NLL**, after the operator asked whether a Polonius-style checker was feasible from the start. It is not, cheaply, and the reason is structural rather than a preference: Polonius is Datalog indexed by **program points** and presupposes a CFG, which Metel has in no form — verified, the pipeline carries no MIR or IR and `move_check` walks the typed AST. **But NLL needs no CFG either**, because Metel's control flow is fully structured (zero `goto`/labels in `grammar.pest`), making the AST a reducible CFG over which AST-directed dataflow is equally powerful; `move_check`'s own 4357-line loop fixed-point is the in-repo proof. NLL additionally **dissolves §2b.1** (lexical's rejection of `c.bump(); c.bump();`) rather than patching it — no temporary-vs-`let`-bound exception needed, and needing an exception was evidence about the rule. **The earlier reversibility argument for lexical is withdrawn as weak**: it protects against breaking code you do not control, and Metel has one operator and a 732-fixture corpus, while lexical's cost is paid immediately and twice. §2.5's diagnostic format revised with it — the earlier version claimed a scope-end was expressible *only* under lexical and that NLL's "last use" was "materially harder to point at"; that was backwards and is corrected, since the extending use is a single span the analysis must compute anyway and it explains *why* the borrow lasted rather than merely where it stops. New §2c records Polonius as a named future option with an explicit revisit condition (Metel acquires a CFG/MIR for an unrelated reason — #259 is the live candidate — or problem case #3 becomes a recurring rejection), noting that its advantage concentrates in exactly the surface §2b.3's stored-reference ban narrows. | *(none — same-day, not a review cycle)* |

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
- `strategic-overview-2026-08-01.md` — most recent dated snapshot, the first cycle
  where Priority 1/2 engineering (not design prose) dominated the review period,
  behind Triggers 20/21/22/24's closures and 26/27/28's openings
