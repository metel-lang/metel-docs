---
id: rfc-index
title: "RFC Index"
type: index
last_updated: '2026-07-15'
---

# RFC Index

This file is the **curated thematic map** of the RFC corpus. It groups RFCs by design
cluster, points out meaningful cross-RFC relationships, and records non-derivable
judgment about why certain RFCs matter together.

It is **not** the authoritative source for mutable state such as counts, stage totals,
paths, or "what changed most recently." Those facts live in the generated
[`REGISTRY.md`](REGISTRY.md), rebuilt by `rfcs/tools/rfc.py`.

Use the two files differently:

- `REGISTRY.md`: exact state inventory, generated, trusted for counts/stages/paths.
- `INDEX.md`: curated reading map, trusted for grouping and cross-reference guidance.

Grouped by theme, not by number, because number order tells you nothing about what's
related. See `PROCESS.md` for the lifecycle rules that govern how RFCs move.

---

## ✅ RFC-0055 overlap — reconciled 2026-07-09

Found while building this index, resolved the same day: RFC-0055 ("Comptime," draft
since 2026-06-05) had gone undiscovered through this session's entire RFC-0092/0093/
0094 drafting, because no index existed to check against. Its foundational execution
model (`comptime let`, `comptime fun`'s restrictions, `comptime if`) was real and
missing from RFC-0092 — folded into RFC-0092 §0. Its recursion/allocation/error-message
open questions are now RFC-0092 Open Questions 6-8. Its aspect-inspection question
(OQ-4) is answered more precisely by RFC-0093's `#derive(Aspect)` registration. Its
`#cfg`-collapses-into-`comptime if` observation independently corroborates RFC-0095's
Open Question 4 rather than needing merging into it. RFC-0055 is now superseded
(`5-superseded/rfc-0055-comptime.md`) — kept as the first concrete proof that
`INDEX.md` and the check-before-opening-a-new-RFC rule (`PROCESS.md`) earn their keep.

---

## ✅ RFC-0083 folded into RFC-0092 — 2026-07-12

RFC-0083 (Public Value Exports, `pub let`) had reached `3-integrated` requiring `pub
let` initializers to be "constant expressions," a concept it never specified itself —
it deferred that definition to RFC-0092, while RFC-0092 only carried the connection as
a pending open question ("added 2026-07-11"). Neither RFC actually owned the
restriction it depended on. Surfaced while deciding whether to implement Codeberg issue
#539 (RFC-0083's tracking issue): implementing `pub let` as drafted would have meant
building a bespoke restricted evaluator now, then reconciling it against `comptime let`
later once RFC-0092 lands. Resolved instead by folding RFC-0083 into RFC-0092 §0a:
public value exports are `pub` applied to `comptime let`, not a parallel mechanism.
Issue #539 closed unimplemented. RFC-0083 is now superseded
(`5-superseded/rfc-0083-public-value-exports.md`); `reference/spec/modules.md`'s
`pub let` section (added when RFC-0083 integrated) was reverted to its pre-integration
wording ("public value exports are not supported in the current version"), since the
feature is no longer backed by a settled RFC — the mechanism now lives in draft-stage
RFC-0092 instead, gated on that RFC's own v0.5+ timeline (a real cost, noted in
RFC-0092's own Timing Recommendation).

---

## Comptime / Derive cluster (draft — the newest, least settled cluster)

All v0.5+, none implemented, none accepted. This is where the RFC-0055 overlap (above)
was found and reconciled, and where this session did most of its work.

> **Moved to under review, 2026-07-21.** RFC-0089, RFC-0090, RFC-0091 and RFC-0109 — the
> records/views substrate — were swept from draft to `1-under-review` together, along with
> the new **RFC-0113 (Context Parameters)**. This is `OBJECTIVES.md` Priority 2, the
> declared main medium-term design priority, and the blog's stated short-term commitment
> (`ToRecord`/`FromRecord` working in the interpreter). It also answers Trigger 17, which
> asked whether the next cycle would move a higher-ranked item or keep substituting
> reference/deref ergonomics work for it. The cluster is reviewed as a unit because
> RFC-0091 extends the RFC-0089/RFC-0090 floor and RFC-0109 depends on both — Trigger 6's
> 0089↔0090 dependency direction is the question review has to settle.
>
> **Restructured 2026-07-24 — Trigger 6 settled, and the cluster decomposed.** Trigger 6's
> question resolved by finding the dependency was **accidental**: RFC-0089's floor was
> rewritten from "Option B" to `ToRecord` by a same-day revision on 2026-07-09, which is
> why neither RFC ever stated it as a design position. Per-field multiplicity was always
> meant to wait until records were implemented.
>
> Consequently: **RFC-0090 is superseded by six RFCs** — RFC-0116 (Anonymous Record
> Types), RFC-0117 (Row Narrowing), RFC-0118 (Row Bounds), RFC-0119 (Record Conversions),
> RFC-0120 (Named Records), RFC-0121 (Open Rows) — re-housed by dependency depth rather
> than by topic, so the one piece that depends on nothing can be accepted and built
> independently. **RFC-0089, RFC-0091 and RFC-0109 return to `0-draft`**, deferred until
> records ship. No feature was dropped and no design decision was reversed; this is a
> re-partition.
>
> **The largest single consequence, after two corrections:** the records cluster has **no
> dependency on RFC-0076 (Brand Types, `0-draft`)**. That claim was first made when
> fiat-linearity was deferred, **withdrawn** hours later as overstated (it held only for
> by-value conversion; the by-reference mode looked likely to reinstate a brand through
> reassembly provenance), and then **restored on different grounds** when RFC-0119 dropped
> its by-reference mode outright. Tier 2 is now brand-free because it never touches a
> borrow — a structural property of what it does — rather than because a dependency
> happened to be deferred. The sequence is kept visible in RFC-0119 §5 because the first
> version was used as evidence the decomposition had simplified the design, and that
> evidence only became sound after a second, independent decision.
>
> **RFC-0116 was unaffected throughout** — no conversions, no borrows, no provenance. The
> one external dependency that is certain is RFC-0071 (`3-integrated`, 0% implemented), and
> it gates RFC-0117 onward, not RFC-0116, which is why the split is six-way rather than
> three-way.

- **RFC-0113** *(under review, opened 2026-07-21)* — Context Parameters — a value a call
  tree needs, declared on the callee and resolved *by type* from the caller's scope, with
  ambiguity always a compile error. Fills what `OBJECTIVES.md` Priority 2 calls "the largest
  unwritten hole on the allocator critical path" — the one substrate primitive with no RFC
  of any kind. Generalizes RFC-0065's four separate elision rules (§1/§1a/§1b/§2 all restate
  the same "elide only when the unique answer is determinable" invariant) and adopts its
  reverted-depth-shadowing lesson as §3.1's type-directed filtering. Also retires the
  invented `given` keyword in RFC-0076's capability-token sketch. Deliberately scoped to
  the *threading* only: allocated values stay owned/affine/move-tracked, which is the
  box+brand+borrow-checker column, untouched.

### The records cluster after the 2026-07-24 six-way split

Listed in dependency order. Each can be reviewed and accepted independently once the ones
above it are.

- **RFC-0125** *(draft, opened 2026-07-25)* — Variadic Generics — a type-parameter pack
  (`<..Ts>`) so one impl covers tuples of every arity: `extend<..Ts> (..Ts): Copy where all
  Ts: Copy;`. Supplies the design RFC-0061 §6 deferred as "no design exists", which
  RFC-0096 §7 then inherited and #263 is now blocked on. **Bounds reuse RFC-0123's `all`
  quantifier** rather than inventing a second one — `all Ts: A` over an ordered pack is the
  same construct as `all R: A` over a row's fields, which makes RFC-0123 a likely dependency
  or a candidate for lifting the quantifier out. Proposes a **two-stage** design: packs plus
  `all` bounds first (enough for `Copy`/`Send`/`Sync`, which are marker aspects and need no
  body), deferring body-level expansion (`Display`, `Eq`, `Clone`) where C++ and Swift both
  accumulated their complexity. Records comptime (RFC-0092, Zig's answer) and per-arity
  boilerplate (Rust's answer, twelve blocks × seven aspects) as the two real competitors —
  noting Rust sustains that choice only because macros generate the copies, which Metel has
  no way to do. §1.1 analyses Rust's four drafts (EddyB, Cramertj, Fredpointzero, Bertholet)
  from the lang-team design note and draws five lessons, two of which change the design:
  head-tail recursion is **rejected** because it inherits Rust's tuple-layout blocker, and
  Bertholet's `static for` is recognised as comptime, making RFC-0092 the likely
  *implementation* of stage 2 rather than a rival to it.

- **RFC-0127** *(draft, opened 2026-08-01)* — Associated Functions on Generic Types —
  a no-receiver `fun` in an `extend` block is already declarable, checked, and callable as
  `Counter::new()` on a **non-generic** type; the same declaration on a generic type
  resolves to `T0003 unresolved path`. Opened because the gap is invisible from the design
  side: **140 call sites across 31 files** assume it (`Rc::new` ×18, `BumpAlloc::scoped`
  ×13, `List::new` ×6), and `stdlib/core.mtl` declares `List::new`/`List::from` which work
  only because `List` is a builtin seeded directly into the scheme table — so the standard
  library models an idiom user code cannot write. Cause is narrow: path resolution consults
  `method_scheme_for`, a single-scheme table generic methods are not in, ten lines above an
  enum-variant arm that already mints fresh type arguments the way this needs. The real
  work is **OQ4**, selecting among several bounded impls (RFC-0036) with no receiver to
  select on, which is why this is an RFC and not a bug report. Also carries the two
  turbofish positions (`Tok::make::<i64>` names the function's parameters,
  `Tok<i64>::make` the type's — only the first parses today) and notes `Aspect::method()`
  as out of scope but not to be foreclosed. Related but non-overlapping: RFC-0044 settles
  the three *receiver* forms and never names their absence; RFC-0114's `Construct` aspect
  and RFC-0100's call-shaped construction both give construction without giving a *named*
  alternative constructor.
- **RFC-0126** *(implemented 2026-07-27, #593, split from RFC-0124)* — T[] as a Copy
  Borrowed View — extracts the one part of RFC-0124 that was already settled rather than
  leaving it waiting on RFC-0124's harder open questions. RFC-0054 (`4-implemented`) already
  declared `T[]` "the immutable/read-only array type"; this RFC takes that at face value:
  `T[]` is a non-owning, immutable, unconditionally-`Copy` view produced only by borrowing,
  and array literals retype to `[T; N]`. **Opened because #578 and #579 were blocked on
  exactly this question** — #579's move checker had no rule for `T[]` beyond "not `Copy`",
  which is why six of #267's fixture-migration corpus were stuck on nothing but this.
  Adversarial review (per PROCESS.md) checked both named attack vectors directly against
  the codebase — neither landed — and surfaced a third: literal retyping would break every
  corpus-wide call site passing an unannotated array to a `T[]`-parameterized function (92
  of them), unless `[T; N]` coerces to `T[]` implicitly. Already solved, live, by RFC-0053.
  Implementation (#593) surfaced two more real findings beyond the RFC text itself: forcing
  index-assignment to actually validate exposed a pre-existing bug where generic-struct
  field assignment discarded its type arguments and anonymous records had no arm at all
  (both fixed); and `int_01_statistics.mtl`'s bubble sort needed a real algorithm change,
  not just a retype, since an in-place sort mutating a borrowed slice is impossible once
  `T[]` is immutable and `List<T>` has no index-assignment method either — concrete evidence
  for RFC-0124's still-open "is there a mutable slice" question (Open Question 1), not just
  a theoretical one.

- **RFC-0124** *(draft, opened 2026-07-25, narrowed 2026-07-27, OQ6 split out 2026-08-13)*
  — Sequence Types: Fixed Arrays, Slices, and the Growable List — **now the slice half
  only.** Covers: whether a mutable slice exists and how it is spelled (OQ1), and the exact
  dependency on RFC-0067's lifetime anchors (OQ2 — a stated precondition for this RFC's own
  acceptance). Its other three questions have all left: OQ3 (does `[T; N]`'s `Copy` rule
  need const generics) is **answered by citation** to RFC-0128 §3; OQ4 (`Value::Array`'s
  representation) is being decided in `metel-core#277`, which owns the change; OQ6 (can
  `List<T>` be written in Metel source) moved to **RFC-0133**. What is left has a *known*
  unblock point — RFC-0067 settling, ~v0.15.0 — where before it had none, which is the
  whole point of the split. Title's "and the Growable List" retained as history.

- **RFC-0133** *(draft, opened 2026-08-13, split from RFC-0124 OQ6)* — From-Metel List: the
  Runtime-Sized Buffer Gap — can `List<T>` ever be implemented in Metel source, or is
  native/Rust backing structurally permanent? **Proposes no design, deliberately.** Records
  the five prerequisites in dependency order, and its load-bearing finding is an *absence*:
  two of the five — a runtime-sized buffer-allocation primitive in the design, and one in
  the evaluator — **have no owning RFC at all.** That is what makes this indefinite rather
  than distant: no document to wait on, no milestone that could contain it. RFC-0063 is
  routinely cited as where `List`'s buffer comes from and, checked directly, is not (single-
  value allocation only; its own §9 calls `Alloc.alloc`'s signature "undecided and
  unspecified"). Two mutually exclusive things would close it: an RFC specifying batch/
  buffer allocation, or an explicit decision that native backing is permanent rather than
  default — the latter being cheaper, legitimate, and currently unstated anywhere. Tracked
  by `metel-core#276` (retargeted from RFC-0124, and unmilestoned to match its own body).
  Its OQ1 asks the question nothing else does: whether a from-Metel `List` is actually
  *wanted*.

- **RFC-0123** *(draft, opened 2026-07-24)* — Field-Wise Row Constraints — a constraint
  applying an aspect to **every field of a row** rather than to the row's type
  (`extend<row R> { ..R }: Display where all R: Display`). Opened after noticing that two
  questions the corpus tracked separately are one missing construct: RFC-0121's
  width-subtyping rule needs "every field in `R` is `Copy`", and RFC-0116 needs "every field
  in `R` is `Display`" before an anonymous record can be printed at all. **Without it no
  record can satisfy any stdlib aspect**, since they are all non-local and the orphan rule
  correctly bans per-shape impls. Depends on RFC-0121, so neither is in v0.12.0 — the gap is
  a stated limit of records as first shipped. Prior art is PureScript's `RowToList` plus
  instance induction, and Haskell `row-types`' `Forall r c`; both derive it rather than
  making it primitive, which is open question 2.

- **RFC-0122** *(under review — accepted and reverted 2026-08-01; opened 2026-07-24)* — Borrow Checking — **headline rule: shared XOR
  exclusive** (any number of `&T` to a place, or exactly one `&var T`, never both), plus the
  outlives rule. Neither is stated anywhere in the corpus today, and `&var T` is called
  "exclusive" by the spec and RFC-0067a with nothing defining or enforcing it. **Depends only
  on RFC-0067a (`4-implemented`); RFC-0067's anchors are a dependent, not a dependency** —
  they name a validity scope for the cross-function cases elision cannot infer, and denote
  nothing without these rules. **Adds no syntax**; `&T`/`&var T` (RFC-0067a) and `&r T` (RFC-0067)
  exist, and this supplies the rules they are currently checked by, which is nothing.
  Opened against Trigger 19 — **and correcting it**: that trigger records "the borrow
  checker has no RFC at all," true of a title search but understating RFC-0067, which is
  `2-accepted`, specifies anchors, and superseded RFC-0052. The missing piece is the
  checking rules, not the notation. Scheduled as **design-only** for v0.12.0, running
  alongside RFC-0071's implementation rather than gating it. **Accepted 2026-08-01** with
  all five design questions resolved: per-field granularity, two analyses over one shared
  place abstraction (07-24), and **lexical borrows first** — chosen for asymmetric
  reversibility, since lexical→NLL accepts strictly more and needs no migration while the
  reverse breaks valid programs — plus observability and a specified `T0020` diagnostic
  format (08-01). **Its only structural blocker is discharged:** RFC-0071 §9b's standalone
  place abstraction shipped in #579 (`src/place.rs`, crate root, analysis-neutral), so
  this is now a second analysis over an existing representation rather than a rebuild.
  §3 requires it ship opt-in behind `--borrow-check` and **not** default-on in the same
  release as #267, to keep two corpus migrations out of one blast radius.
  **Reverted to `1-under-review` the same day.** Six gaps found immediately after
  acceptance, three blocking: the outlives rule — half the RFC's own stated scope — is
  named in its Summary and specified nowhere (`return &local;` is accepted today);
  reference-typed struct fields (`struct Holder { r: &P }`, constructible and able to
  outlive their referent today) defeat the "anchors are a dependent, not a dependency"
  claim; and §2.2's lexical rule as written rejects sequential `&var` method calls.
  Closures, reborrowing, and RFC-0126's `Copy` `T[]` view are unaddressed. Recorded as
  §2b. **Third `2-accepted`→`1-under-review` reversion in the corpus (Trigger 14 fired).**
  **Liveness model changed lexical → NLL the same day (§2.2)**, after the operator asked
  about Polonius: Polonius is Datalog over program points and presupposes a CFG Metel has
  no form of, whereas NLL needs none — structured control flow makes the AST a reducible
  CFG (`move_check` is the precedent). NLL also dissolves the lexical blocker outright.
  §2c records Polonius as a named future option gated on Metel acquiring a CFG/MIR.

- **RFC-0116** *(implemented in v0.12.0, was #576)* — Anonymous Record Types — the closed `{ x: f64 }` type-former,
  `{ x = 1.0 }` values, `Handle.{ fd }` projection, structural identity, and where records
  are usable (no inherent impls, no non-local aspect impls, no custom `Drop`, not an
  allocator). Also carries RFC-0090 §6's declined "records as the universal foundation"
  reframing. **Depends on nothing** — the only piece of the cluster buildable today, and
  the reason the split is six-way.
- **RFC-0137** *(under review, opened 2026-08-24)* — Nominal Types as Branded Rows — formalizes
  `reports/substructural-types/nominal-types-as-branded-rows.md`'s central thesis, left
  deliberately unfolded by that document's own Open Question 7 so it would not gate this
  cluster's nearer review. Proposes that **every** `struct`, not only RFC-0120's opt-in
  `record` kind, is represented as `(brand, row)`: narrowing via partial move produces a
  residual of the *same brand* (`Handle` → `Handle.{ fd }`), and a struct's own field
  projection (RFC-0116 §4) is recognizably still that struct for impl-resolution
  purposes — closing the gap where `Self.{ fd }`/`Handle.{ fd }` today accepts an
  unrelated anonymous record of the same shape exactly as readily as a value actually
  derived from the struct. Keeps RFC-0116/RFC-0090's non-ambient-structural-matching
  guarantee by separating "has a row" (universal under this RFC) from "row is visible to
  structural matching" (stays exactly as opt-in as RFC-0120 already gates it — a
  restatement of the existing three tiers, not a fourth one). Supersedes RFC-0071 §7's
  blanket partial-move-with-`Drop` ban with row-bounded dispatch instead of narrowing it
  by exception; depends on RFC-0114 landing before automatic widening is safe to enable.
  **Discharges RFC-0117 §3's own stated dependency** ("narrowing a nominal type…
  depends on nominal types carrying rows at all") and answers **RFC-0120's Open Question
  5** ("does a narrowed named record keep its brand") for the general case. Its own
  zero-runtime-cost claim for narrowing and `Drop` dispatch is a design argument, not a
  demonstrated property — contingent on RFC-0071 actually being built, which it is not
  today (`3-integrated`, partial-move tracking confirmed absent from the interpreter).
- **RFC-0117** *(draft)* — Row Narrowing — moving a field out narrows the record's type;
  the closed 2^*N* subset lattice, no row variables and no unification. Depends on
  RFC-0116 and on **RFC-0071** (`3-integrated`, 0% implemented), which is why it is separate
  from RFC-0116 rather than bundled with it. **Its own §3 nominal-type exclusion is now
  addressed by RFC-0137**, which should be folded in as its supplying dependency once
  reviewed.
- **RFC-0118** *(implemented in v0.12.0, was #577)* — Row Bounds — `<record T: { x: f64, .. }>` and `!{ token }`,
  replacing the `HasField`/`Lacks` family that never parsed. The trailing `..` is an
  anonymous row variable and is what makes a bound *open*; without it the bound is closed,
  a reading that previously could not be written at all. Explains why implicit structural
  satisfaction is safe here specifically (a bound grants no capability over the type
  itself). Depends on RFC-0116.
- **RFC-0119** *(draft)* — Record Conversions — tier 2 `ToRecord`/`FromRecord`, kept as
  separate aspects for the serde reason. **By value only**: RFC-0090 §8's
  `to_record_mut`/`from_record_mut` are dropped as superseded by RFC-0109's named views
  (added 2026-07-08 to "resolve tier 2's borrow gap", ten days before RFC-0109 built that
  mechanism properly). Also drops §8's brand-carrying fiat-linear exception. Between them
  those leave tier 2 with **no RFC-0076 dependency for a structural reason** — it never
  handles a borrow, so it never needs to establish which object one came from — and put
  the tier boundary on a clean line: *by-value conversion is bare; borrowed access is
  branded because it must be.* Depends on RFC-0116, RFC-0117.
- **RFC-0120** *(draft)* — Named Records — tier 3 `record X { }` carrying `(row, brand)`
  intrinsically; the tier table, the non-breaking upgrade path, and RFC-0090 §9's
  identity-tag reuse. Depends on RFC-0116, RFC-0119. **Its own Open Question 5** (does a
  narrowed named record keep its brand) **is answered by RFC-0137** for the general case
  — every struct's brand is preserved through narrowing, not only tier-3's.
- **RFC-0121** *(draft)* — Open Rows — `<row R>` / `..R`, row algebra (extension is a
  literal, removal is a where-clause decomposition), row-conditional typestate, and the
  width-subtyping-versus-ownership problem. **The expensive half**, and the only piece
  introducing a row kind or row unification. Depends on RFC-0118, RFC-0120.

**Deferred until records are implemented** — returned to `0-draft` 2026-07-24:

- **RFC-0089** — Linear Types — multiplicity lattice, `Linear` auto-impl aspect. Depends
  on RFC-0071 (integrated). Its §3 floor was rewritten on 2026-07-09 to route partial
  consumption through `ToRecord`; **that coupling was accidental** and is what Trigger 6
  was tracking. `Linear`'s auto-impl categorization depends on RFC-0096 for the shared
  mechanism it's an instance of.
- **RFC-0090** *(superseded 2026-07-24 by RFC-0116–0121)* — Structural Records — Rows and Tiers — bare-row bounds (`HasField`/
  `Lacks` retired 2026-07-23, replaced by `T: { x: f64 }` / `T: !{ tag: _ }`), `record`
  type-former, three-tier capability model. No dependency on comptime. §1 calls the
  row-bound mechanism an extension of RFC-0080's auto-impl pattern; RFC-0096 §7
  (2026-07-11) works out that it's a family with existential satisfaction, not the same
  mechanism as `Send`/`Sync`/`Linear` — still open. The other 2026-07-11 gap
  (`HasField`'s string-literal bound argument not covered by the grammar) is fixed by
  the 2026-07-23 revision: it never actually parsed, and the bare-row form has no
  string literal to fail on. That revision also folds back two findings from
  `reports/substructural-types/nominal-types-as-branded-rows.md` — tier 3's declaration
  syntax (OQ8, resolved to `record X { ... }`) and a pointer to RFC-0114 for OQ10
  (`FromRecord`/constructor invariants) — while deliberately *not* folding in that
  document's own central, still-exploratory thesis (every struct, not just tier-3,
  carrying `(brand, row)`), which stays a separate track so it doesn't gate this
  cluster's review.
- **RFC-0091** — Linear Records — per-field multiplicity, automatic-downgrade partial
  consumption, the `uses(fd)` Drop mechanism. Depends on RFC-0089 + RFC-0090.
- **RFC-0109** *(draft, opened 2026-07-18, revised same day)* — Self-View Narrowing and
  Reference-Destructuring Patterns — closes the gap found comparing RFC-0090's records
  against Rust's (unshipped) view-types proposal. Canonical mechanism (as of the
  revision): named **views** — `view TicketView for Ticketing { golden_tickets }` — are
  *branded* records, reusing RFC-0090 §9 / RFC-0091 §2.2's `(row, brand)` representation
  rather than an anonymous one. `self: &TicketView` lets an inherent method declare
  which sub-row it touches with zero call-site syntax (unlike `to_record_mut()`); brand
  equality is what stops a view from ever satisfying a bound RFC-0090 §8 didn't intend
  it to (no reopening of "no implicit coercion"). Framed as a second instance of
  RFC-0089 §3.1's existing bare-vs-branded tier-2 exception, not a new carve-out, and
  deliberately kept out of coherence/impl-resolution so it never becomes tier 3 "for
  free." `self` may also be a tuple of independently-moded views (`self: (&mut
  BarsView, &TicketView)`, unpacked via ordinary `Pattern::Tuple`) for Rust's mixed
  shared/exclusive `&{bars, mut golden_tickets} self` case, with addressability
  following the tightest slot. Plus `let &var { a, b } = h;` for the ad hoc, one-off
  splits a named view isn't worth declaring for. Amends RFC-0044. Paper-only pending
  RFC-0071 (0% implemented,
  confirmed by source search) — inherits RFC-0091 §2.1's open aliasing question only for
  the already-partially-consumed-residual case, not the common intact-struct case. Also
  defines the minimal by-value struct-destructuring pattern Metel currently lacks
  entirely (`Pattern` in `src/ast/mod.rs` has no `Struct` variant), since the reference
  form needs one to exist.
- **RFC-0114** *(draft, opened 2026-07-23)* — Constructor Aspect and Canonical
  Construction — split out of `reports/substructural-types/nominal-types-as-branded-rows.md`
  §6, which found that automatic row-narrowing/widening reopens RFC-0090's open question
  10 (`FromRecord` bypassing constructor invariants) as a general risk reachable through
  ordinary field reassignment, not one scoped to the `FromRecord` conversion alone.
  Proposes a `Construct` aspect (`construct(row) -> Result<Self, Self::Error>`) as the
  one path any value of a nominal type is ever produced through — fresh construction and
  post-narrowing reconstruction collapse into the same operation. **Syntax-independent
  since 2026-07-24:** the RFC-0100 dependency was found not to be real — a brace literal
  that *desugars* to `construct` is not a bypass, so `Point { x = 1.0 }` and
  `Point(x = 1.0)` both work and neither is required. Only §1.1's rule matters, that
  row-to-`Self` is admitted inside `construct`/`construct_unchecked` and nowhere else. A struct with no invariant gets a
  compiler-synthesized identity default (`Error = !`). Collapses RFC-0090's `FromRecord`
  into the same mechanism without amending RFC-0090's own text. A separate, opt-in
  `ConstructUnchecked` aspect (depends on RFC-0026, `unsafe` blocks) gives an explicit
  escape hatch, mirroring Rust's `new`/`new_unchecked`. **Fallibility resolved same day:**
  `Self::Error = !` collapses `Result<Self, !>` to bare `Self` via RFC-0078's
  already-implemented uninhabited-variant exhaustiveness and inhabited-singleton
  coercion rules — provably, not by convention — while a real error type loses the
  automatic-firing sugar in exchange, decided by the same rule rather than a special
  case. Open question remaining: whether `Construct`'s default-impl derivation fits
  RFC-0096's auto-impl pattern, RFC-0093's comptime derive, or needs its own mechanism —
  RFC-0082 explicitly declined general default associated types, for reasons that may or
  may not transfer to this narrower, whole-impl case.
- **RFC-0132** — Comptime Execution Model — `comptime let`/`fun`/`if`, `pub comptime let`
  (public value exports), and **comptime-known non-type generic parameters**
  (`comptime N: u64`) — i.e. the const generics RFC-0053 deferred to "a future RFC," now
  with an actual home. Split out of RFC-0092 §0/§0a on 2026-08-13, acting on an escape
  hatch RFC-0092's own Timing Recommendation had written down 35 days earlier and nobody
  could act on because §0 had no independently schedulable identity. **This is now the
  dependency root of the whole cluster** — RFC-0092 depends on it, not the reverse.
  Unblocks three things that were all waiting on the same content without anyone
  connecting them: `metel-core#263`'s hardcoded `[T; N]: Copy` arm, RFC-0124's Open
  Question 3 (now answered by citation), and RFC-0083's public value exports (waiting
  since 2026-07-12). Its OQ1/OQ2 (comptime recursion, comptime allocation) are inherited
  from RFC-0092 OQ6/OQ7 but are **blocking here where they were not there** — you cannot
  ship `comptime fun`/`comptime let` without answering them. §3.1 deliberately spells the
  parameter `comptime N: u64` rather than RFC-0053's guessed `<const N: u64>`; §3.4
  excludes computed arities (`[T; N + 1]`) as a *named* deferral rather than another
  unnamed future RFC.
- **RFC-0092** — Comptime Core — `type`-as-value, `typeinfo`, single-declaration
  `emit`. **§0/§0a (the base execution model and `pub comptime let`) split out to
  RFC-0128 on 2026-08-13** — retained in place, marked non-normative, because the
  RFC-0055/RFC-0083 reconciliation history recorded in them is part of how this RFC
  reached its shape. Still the dependency root of 0093/0094; now itself depends on
  RFC-0128.
- **RFC-0093** — Derive Registration — `#derive(Aspect)` as request + registration.
  Depends on RFC-0092. RFC-0080's `Clone` derive depends on this. Answers RFC-0055's
  aspect-inspection open question. Deliberately excludes auto-impl aspects
  (`Send`/`Sync`/`Linear`) from its scope — see RFC-0096.
- **RFC-0096** — Auto-Impl Aspects — owns the auto-impl mechanism: formalizes the
  recognition rule (closed,
  compiler-intrinsic list, not a declaration-level marker) and the shared
  structural-composition algorithm that RFC-0080 §3.2/§4.2 and RFC-0089 §2 each
  independently invoke as "the auto-impl pattern" without either owning it. Opened
  2026-07-11 while implementing issue #542 (Aspect Impl Coherence pipeline), which
  confirmed `AspectDecl` carries no such marker today. Fleshed out same day: §3
  covers generic types (an auto-impl on a generic struct/enum is an implicit
  RFC-0036 conditional impl, never evaluated eagerly); §4 corrects a plausible
  misreading of RFC-0061 §5's heading — `Drop`'s array-only propagation is not a
  fourth instance of this mechanism, since RFC-0071 §3 already makes `Drop` opt-in
  for structs/enums. Also found, in passing, that RFC-0050 independently derived
  the same closure-capture `Send` rule without citing a shared source — a fourth
  uncited instance of the pattern this RFC names. **Corrected later 2026-07-11:** §1's
  "closed list of three" claim was itself wrong — RFC-0090 §1 independently calls
  `HasField`/`Lacks` an extension of this same pattern, missed on the first pass
  (different INDEX.md cluster). New §7 explains why it's related but not a fourth
  fixed-marker instance (a parameterized family with existential, not universal,
  satisfaction — possibly outside the impl/coherence system entirely). 6 Unresolved
  Questions recorded (unit variants, raw pointers, `Linear`'s missing reference rule,
  the RFC-0061 §5 heading fix, whether the fixed-marker category is expected to grow,
  whether `HasField` goes through coherence at all). No behavior change to
  `Send`/`Sync`/`Linear` themselves.
- **RFC-0094** — Comptime Metaprogramming — generalized `emit`, comptime-callable
  parsing, diagnostics, body-reflection scoping. Depends on RFC-0092 only; independent
  of RFC-0093.
- **RFC-0095** — Attributes and Metadata — `@` syntax, attributes as comptime-visible
  metadata. Mostly independent; only §2 depends on RFC-0092.
- **RFC-0062** — Ord/Eq Comparison Aspects — `Eq`/`Ord`/`Ordering` in `std::core`.
  RFC-0093's Derivable Aspects table assumes these exist; not cross-checked against
  RFC-0062's actual signatures.
- **RFC-0011** — Operator Overloading Aspects — operator desugaring. RFC-0093 notes
  derived `Eq`/`Ord` depend on this.
- **RFC-0039** — `aspect` Alias Syntax — vehicle for RFC-0089's `Affine` alias
  (`!Copy + !Linear`). Small, standalone.

## Region / Allocator / Lifetime cluster (accepted 2026-07-10 — ratified, Phase 3's dependency now clear)

The cluster the roadmap tried to get to "accepted, ready to implement" for weeks. Ratified
2026-07-10 via a consistency pass before sweeping: RFC-0063 §9 items 1/2/5 (allocator
teardown discipline, `drop` interaction, partial consumption) were still written up as
open/blocking, even though `reports/implementation/roadmap-2026-07-07.md`'s Phase 0 had
already resolved them in a separate document three days earlier and never synced back —
now fixed in RFC-0063 itself. RFC-0066 and RFC-0068's frontmatter titles/filenames also
still said "Region ..." after the rest of the cluster renamed region → allocator; renamed
to match (`rfc-0066-allocated-value-extraction.md`, `rfc-0068-struct-owned-allocators.md`),
plus a few stale cross-reference bugs (a self-contradictory syntax note, a wrong section
number, a backwards RFC-0067a split direction).

- **RFC-0063** *(accepted)* — Allocator Handles — the allocator half of the old "region
  handles" premise. Central to the whole cluster.
- **RFC-0065** *(accepted, amended 2026-07-20)* — Allocator and Lifetime Ergonomics —
  elision rules for both channels. Depends on RFC-0063 + RFC-0067. §1b added
  2026-07-20: call-site allocator-*argument* elision (`wrap(@a, 42_u64)` →
  `wrap(42_u64)` when exactly one allocator is in scope and the callee's signature
  declares exactly one) — closes the gap §1/§1a never covered (every worked example
  in the cluster, e.g. RFC-0077 §3.3, wrote the argument out in full even when
  unambiguous), the concrete substance behind a real "elision is still too verbose"
  critique. Surveyed against Zig (no such mechanism, by design), Odin (ambient
  `context.allocator`, rejected for the same reason RFC-0075's inter-function
  inference was — invisible at the call site), and Kotlin (context parameters,
  stable as of 2.4 — the closest precedent, since it independently arrived at the
  same "ambiguity is a compile error" invariant this RFC already commits to). Second
  fix the same day, revised once during discussion: an allocator declared two scopes
  out (e.g. `Heap` as an *outer function's* own parameter, with an inner
  `BumpAlloc::scoped((@a) -> {...})` closure) had no stated resolution — a first
  draft proposed silent depth-based shadowing (innermost declared allocator always
  wins), reverted as too close to overload resolution and a silent-refactor hazard
  (adding an unrelated inner allocator would silently change what existing elided
  code means, no diagnostic). Replaced with **type-directed candidate filtering**:
  "in scope" now means in scope *and of the required concrete type*, whenever one is
  known — which resolves `Heap`-vs-`BumpAlloc` for free at any concretely-typed
  position (a call, or an annotation against a non-generic signature), with no
  shadowing rule needed, since the two never share a type. The one residual case — a
  bare allocation expression with no concrete type to filter by — stays a hard
  compile error, matching how Kotlin's own context parameters resolve a genuine
  same-type collision (loudly, not by nesting depth), not a new silent tiebreak.
- **RFC-0066** *(accepted)* — Allocated Value Extraction — individual drop/move-out; the
  RFC that triggered the whole cluster-wide split. Renamed from "Region Pointer
  Extraction" 2026-07-10 to match how every other RFC already referred to it.
- **RFC-0067** *(under review — reverted from accepted 2026-08-02)* — Lifetime Anchors — the narrowed remainder after RFC-0067a
  was split out and accepted separately. Renamed 2026-07-10 from "Lifetime Anchors and
  Allocator-Pointer References" (`rfc-0067-lifetime-anchors.md`) — the dropped half of
  the title duplicated RFC-0063/RFC-0066's own naming.
  **Reverted 2026-08-02.** Accepted 2026-06-28 before any borrow checker was specified —
  "designed against an absence" by its own header — and never re-examined in the nine days
  since that risk was recorded. RFC-0122 has since specified NLL liveness, per-field
  granularity, `T0020` diagnostics, and a stored-reference ban whose removal this RFC
  triggers (#274), none checked against §1. "Unresolved questions: None" replaced with
  five real ones, load-bearing being whether §1's lexical "valid for exactly as long as
  `r` is in scope" survives NLL. Staleness fixed in the same pass: a `null` literal Metel
  has never had, a bare `mut` in prose, two retired `:` separators, and a self-staleness
  note that was itself obsolete. See `OBJECTIVES.md` Trigger 29 (staleness in place —
  distinct from Trigger 14's premature acceptance).
- **RFC-0067a** *(implemented 2026-07-11)* — Reference Types — plain `&T`/`&var T`,
  auto-deref. No allocator/borrow-checker dependency; already sequenced into Cluster A.
  Integrated into `reference/spec/types.md` and `expressions.md`; gained a new
  §3a (type-directed value-copy-out) resolving a gap found writing the worked examples.
  Implemented in `metel-core` (issue #540); §3a amended the same day to state that
  read-copy fires at `return`/`break`/tail-expression positions too (not just `let`/
  ascription) and that read-copy, write-through, and auto-deref all chain through
  multiple reference layers — both found only once the implementation's own regression
  tests exercised a `&&T`-shaped case.
- **RFC-0068** *(accepted)* — Struct-Owned Allocators — primary-constructor syntax
  (`struct Foo(@a: BumpAlloc)`). Renamed from "Struct-Owned Regions" 2026-07-10.
- **RFC-0073** *(accepted)* — AutoAlloc — renamed from AutoRegion; SubRegion interaction
  dropped.
- **RFC-0077** *(accepted)* — Allocator Generics — `<A: Alloc>` impl headers, variance
  for `@a T`.
- **RFC-0074** *(draft)* — Shared Pointers (Rc/Arc) — blocked on RFC-0076 (brand
  introduction mechanism unresolved).
- **RFC-0075** *(draft, parked)* — Region Inference — deliberately deferred until
  real annotation-burden data exists.
- **RFC-0076** *(draft)* — Brand Types — phantom identity parameters; RFC-0074 and
  RFC-0090's tier-3 `(row, brand)` idea both depend on this.

## Aspect system core (accepted — the stable foundation)

The load-bearing accepted RFCs everything else cites. One open item as of 2026-07-11
(RFC-0097, below) — a narrow gap found by scrutiny, not a design problem with the
cluster itself. **Resolved 2026-07-13**: RFC-0097 integrated (issue #555 tracks
implementation).

- **RFC-0129** *(draft, opened 2026-08-05)* — Aspect Method Generic Constraint
  Conformance — defines the substitutability relation between an aspect method's generic
  constraints and its implementation: an implementation may accept a wider domain but
  cannot narrow it. Covers record kind, aspect and row bounds, and associated-type
  equality bindings; open questions delimit the entailment engine rather than assuming
  constraint spelling equality is semantic equality. Distinct from RFC-0036's
  conditional-impl selection and RFC-0118's row-bound satisfaction.

- **RFC-0130** *(draft, opened 2026-08-06)* — extends Aspect: Renaming `impl
  Aspect` for Consistency with `extend` — renames the anonymous-type-parameter
  (RFC-0035) and return-position (RFC-0037) `impl Aspect` keyword to `extends
  Aspect`, closing the one spot RFC-0098's own Rust-tell sweep (`impl`→`extend`,
  `pub`→`public`, `mut`→`var`) left untouched: the block form already reads
  `extend Type: Aspect { ... }`, but the anonymous/opaque-type form still says
  `impl Aspect`, spelling the same underlying claim two unrelated ways depending
  on grammatical position. Pure lexical rename — RFC-0035/0037's desugaring,
  independence, and opacity rules are unchanged, as is the T0022 restriction
  (metel-core#240/#622, landed the same day) on where `impl Aspect` is legal at
  all. Explicitly does not touch RFC-0038's still-reserved `dyn Aspect`.
- **RFC-0008** — Aspect Objects — `dyn Aspect`, vtable dispatch.
- **RFC-0061** *(implemented 2026-07-14, was integrated 2026-07-13)* — Structural
  Aspect Bounds — `T[]`/tuples/function-type bounds. Depends on RFC-0060 and
  RFC-0036; both were in place before implementation. Integrated into
  `reference/spec/declarations.md` as a new "Structural Aspect Bounds" section
  right after Aspect Implementation Coherence. Integration also surfaced three real
  groundwork bugs in the interpreter's structural-impl path (non-named impl-target
  crashes, array method-dispatch gating, and structural-target registration being
  skipped entirely), all fixed as part of issue #549 rather than left implicit. The
  initial integrated draft had carried array auto-impl propagation as §5, but that
  dependency has now been rehomed to RFC-0096, leaving RFC-0061 to own structural
  impl lookup/bounds and explicit `std::core` structural impls only.
- **RFC-0071** — Ownership and Move Semantics — affine-by-default foundation.
- **RFC-0036** *(implemented 2026-07-13, was integrated 2026-07-13)* — Conditional Impl
  Blocks — `extend Type<T>: Aspect where T: Bound`, both inline and `where`-clause
  forms. Integrated into `reference/spec/declarations.md` right after the basic
  `extend Type: Aspect` example. Fixed a stale error-code collision while integrating:
  the RFC's own §4 example used `T0013`, already claimed (ambiguous aspect
  method/associated-type resolution) by the time this integrated — corrected to reuse
  `T0012` instead, per RFC-0072's own precedent for the negative-bound direction.
  Explicitly defers bare-parameter blanket impls (`extend<T: Bound> T: Aspect`) to
  RFC-0097 (now implemented) — every example in this RFC targets a
  genuinely named type. Worked
  example checks composition with RFC-0082's equality-constrained bounds (both are the
  same `Bound` structure, so no new machinery needed). Implemented (issue #545):
  registry/inference/construction bound-gated impl support, coherence disjointness
  detection (including syntactic negation, §3.1), use-site bound enforcement at every
  point the aspect is required. Independent review found and fixed a real gap the
  implementation's own self-report missed: conditional-impl satisfaction was only
  consulted for direct method dispatch on the receiver, not when the conditionally-
  implementing type was passed through an *unrelated* generic function's own bound —
  such calls were unconditionally rejected regardless of whether the bound actually
  held. Also restored two coherence-negation fixtures (this RFC's own §3.1 examples)
  that the implementation had skipped on a mistaken belief the parser didn't support
  `!Aspect` bounds — it does, at every level (inline, `where`-clause, and impl-level
  polarity). This resolves the "priority over blanket impls"/"blanket-impl-aware
  discharge" blockers noted in RFC-0060, RFC-0072, and RFC-0081's own entries below —
  #548 (2026-07-13) landed that remaining work; see those RFCs' own entries.
- **RFC-0037** *(implemented 2026-07-13, was integrated 2026-07-13)* — Return-Position
  `impl Aspect` — opaque, monomorphised-per-function return types. Integrated into
  `reference/spec/declarations.md` right after the parameter-position `impl
  Aspect` shorthand. Worked example checks composition with RFC-0082 (Associated
  Types): a function returning `impl Container` still resolves `Container::Item`
  correctly through the caller's method calls, since the opaque type is a real
  concrete type internally, erased only from the caller's naming surface. Implemented
  (issue #544): per-quantified-var opaque metadata, linked/unlinked discrimination,
  definition-time bound checking, and real opacity enforcement (T0018) checked
  incrementally per-constraint rather than once at the end of solving (the
  end-of-solve version can't tell a legitimate `impl Aspect`-to-`impl Aspect`
  pass-through apart from an actual violation). Independent review found and fixed a
  real `TypeVar`-generator bug that aliased independent opaque-returning calls once
  three or more appeared in one scope, and that the opacity check itself had been
  left entirely disconnected (never called) despite existing in the source.
- **RFC-0060** *(implemented 2026-07-14, was integrated 2026-07-11)* — Aspect Impl
  Coherence — orphan rule, overlap detection, closed-world assumption, auto-impl
  coherence participation, negative-impl priority. Integrated into
  `reference/spec/declarations.md` as a new section; also surfaced a real,
  unrelated docs bug while integrating (RFC-0033's recommended error code T0014 was
  already claimed by this RFC's own orphan-rule error, so RFC-0033 was corrected
  rather than silently colliding). Implemented across issues #542, #547, #552, and
  #548: orphan-rule enforcement, concrete and blanket-aware overlap detection,
  blanket-impl-aware closed-world negative-bound discharge, and negative-impl
  priority over blanket positives. RFC-0096 still owns the separate auto-impl
  mechanism itself, but that is no longer part of RFC-0060's unimplemented surface.
- **RFC-0097** *(implemented, confirmed 2026-07-20)* — Orphan Rule for
  Bare-Parameter Blanket Impls. RFC-0060 §1's orphan rule assumes every impl target
  has an outermost type constructor to check — but a bare-parameter blanket
  (`extend<T: Bound> T: Aspect`, the exact form RFC-0060 §3/§5 and RFC-0080 §1.2 all
  use as their own running example) has none. Formalizes that target-locality is
  vacuously unsatisfiable for this shape, so such an impl is permitted only via the
  aspect side; no new syntax, no new error code (reuses T0014), no new
  overlap-detection machinery (the orphan-rule fix alone confines any one aspect's
  bare-parameter blanket to a single module). Opened 2026-07-11, same review pass as
  RFC-0096. Integrated into `reference/spec/declarations.md`, expanding the
  existing "not covered by this section" deferral note (added while integrating
  RFC-0036) into full spec content with its three worked examples. **Fixed
  2026-07-20:** the frontmatter had claimed `implemented` since integration, but
  `coherence.rs`'s `outermost_id` had no explicit case for "target is the impl's own
  generic parameter" — it happened to return `None` for one by incidental
  name-resolution failure (a bare generic parameter name is never registered in
  `names.symbols`), not by a deliberate check, the same fragile-by-accident pattern
  #545 and #549 each had to fix for their own target shapes. Landed the real check:
  `outermost_id` now takes the enclosing impl's own generic parameter names and
  explicitly returns `None` for a bare `Named(name, [])` matching one of them,
  before ever falling through to name resolution — same observable behavior, now
  deliberate and immune to `resolve_id` someday changing underneath it. Verified
  against both existing fixtures
  (`bare_parameter_blanket_foreign_aspect_is_orphan`,
  `bare_parameter_blanket_local_aspect_permitted`) plus the full suite (546
  integration + 119 unit tests, `cargo clippy --release --lib -- -W
  clippy::pedantic` clean) — zero regressions, since the change only narrows an
  already-`None`-producing path to be explicit rather than changing any outcome.
- **RFC-0072** *(implemented 2026-07-12, was integrated 2026-07-10)* — Negative Bounds
  — `T: !Aspect`. Integrated into `reference/spec/declarations.md`; its own
  stale bracket-channel allocator examples (`@[r] T`) fixed first. Implemented (issue
  #547): enforcement at all four function-call-expression branches plus generic
  struct/enum literal construction, by inverting the same lookup the positive-bound
  check already uses (this also means negative impls, RFC-0081/#552, are correctly
  consulted for free). §2.3 Copy-implies-!Drop implemented as a narrow, name-literal
  override, per the RFC's own "do not generalize" wording. **Update 2026-07-13:**
  that shared lookup was `impl_aspect_env_has` at the time #547 landed — since
  corrected, while implementing RFC-0036/#545, to `type_satisfies_aspect`, which also
  consults conditional impls (`impl_aspect_env_has` alone can't see those, so a
  negative bound against a conditionally-implementing type was being evaluated
  incorrectly until this fix). Blanket-impl-aware discharge (RFC-0060 §3's fuller
  closed-world form) was blocked on RFC-0036/#545; that dependency has now landed,
  unblocking it. **Update 2026-07-13 (later):** #548 landed the discharge/priority
  logic itself — the `TODO(#545)` comments at each check site are resolved.
- **RFC-0078** *(implemented 2026-07-12)* — Bottom Type `!` — subtyping, coercion, match
  exhaustiveness, inhabited-singleton coercion, `-> !` returns. Integrated into
  `reference/spec/types.md`; §4.2's stale pre-split allocator syntax fixed first.
  Implemented in metel-core sprint/25 (issue #538): `!` surface syntax (grammar),
  `panic(msg)` native, general uninhabited-variant exhaustiveness (subsuming
  `Result<T, !>` as the general rule's special case rather than a hardcoded one),
  inhabited-singleton coercion, and `-> !` divergence checking. §4.2 (allocator
  collapse) intentionally out of scope — depends on RFC-0063's allocator syntax,
  not yet implemented.
- **RFC-0081** *(implemented 2026-07-12, was integrated 2026-07-10)* — Negative
  Impls — `extend Type: !Aspect;`. Syntax, finality (conflict with a concrete
  positive impl), and the orphan rule are implemented and tested (issue #552).
  Negative-bound consultation (SS2.3) is now implemented too (issue #547,
  RFC-0072/2026-07-12): `T: !Aspect` checking inverts the same
  `impl_aspect_env_has` lookup (since corrected to `type_satisfies_aspect`, see
  RFC-0072's entry above), which already excludes negative impls, so this
  composes correctly with no extra work. Priority over blanket impls (SS2.1) was
  a property of RFC-0036 (issue #545) — that RFC is now implemented (2026-07-13),
  and `register_aspect_impl` already refuses to register a negative impl as
  positive, so this composes correctly. **Update 2026-07-13 (later):** #548 landed
  the dedicated priority check itself (a `neg_impl_env` registry table consulted by
  `type_satisfies_aspect` before either positive path) — a concrete negative impl now
  overrides a blanket positive impl for its exact instantiation, without disturbing
  the existing negative-vs-concrete-positive conflict rule (§2.2/#552, confirmed by
  a regression this fix initially introduced and then corrected).
- **RFC-0082** *(implemented 2026-07-13, was integrated 2026-07-10)* — Associated
  Types. Integrated into `reference/spec/declarations.md`; stale
  `Region`/`@[r]` naming corrected to `Alloc`/`@a`, and §7 (amending retracted
  RFC-0069's `SubRegion`) marked historical-only rather than integrated. Implemented
  (issue #546): §1/§1.1/§1.2 declaration + bound enforcement + bare-name sugar
  (in both directions — explicit `T::AssocType` and an aspect's own bare-name
  method signatures, for concrete impls and generic dispatch alike), §2 impl
  completeness (new error code T0017), §3/§3a real projection resolution with
  ambiguity detection (T0013), §4 equality constraints
  (`Aspect<AssocType = Concrete>`). §6 object safety remains unimplemented —
  blocked on RFC-0008 (`dyn Aspect`), which has no consumer yet.
- **RFC-0083** *(superseded 2026-07-12, was integrated 2026-07-10)* — Public Value
  Exports (`pub let`). Reached `3-integrated` requiring "constant expression"
  initializers, a concept it never specified — deferred to RFC-0092, which only had it
  as an open question. Folded into RFC-0092 §0a instead of implementing as drafted; see
  the RFC-0083 fold note above. `modules.md`'s `pub let` section reverted to
  pre-integration wording. Codeberg issue #539 (tracking) closed unimplemented.

## Linear closures / concurrency

- **RFC-0049** *(draft)* — `linear fun` Type System — unconsumed-scope-exit, `Drop`
  interaction, subtyping vs. plain `fun`.
- **RFC-0050** *(draft)* — Closure Capture Lists — `&var`/`move`/clone/`&` specifiers.
  `&var`/clone/`&` buildable now; `move` waits on a split-model successor to refused
  RFC-0046 — RFC-0134 is a candidate, scoped narrower (affine, not linear).
- **RFC-0134** *(under-review as of 2026-08-14, opened 2026-08-13)* — Closure Call
  Capability — the type-level
  distinction `metel-core#269` needs (does calling a closure consume a non-`Copy`
  capture) to make move checking sound for closures, blocking `metel-core#267`
  (enable move checking by default). Scoped as an affine question, deliberately not
  waiting on RFC-0028's linear-types tower the way RFC-0050's `move` half does — affine
  is now a recorded decision with a stated reopening condition, not an open question.
  Carries **two** multiplicity fields on `Type::Fun` (call, and by-value-use — the
  latter is §1's `Copy` rule, which has nowhere else to live since captures aren't in
  the type). §3 specifies exact-match multiplicity unification, with subtyping deferred
  as a strict later widening. **Not proposed for acceptance yet:** the by-value-use
  field's interaction with the two name-literal `Copy` implications — RFC-0072 §2.3's
  `Copy` ⟹ `!Drop` and RFC-0080's `Copy` ⟹ `Clone` — is unspecified.
- **RFC-0135** *(draft, opened 2026-08-13)* — Multiplicity for Ordinary Types — companion
  to RFC-0134, not a dependency of it. Reframes `Copy` as `many` applied to a type's
  by-value-use operation rather than a closure's call operation — same axis RFC-0134
  already uses, named there (§5) but designed here. For named types (`struct`/`enum`)
  this replaces `extend TypeName: Copy;` with a declaration-site `once`/`many` qualifier;
  for structural types there is no single mechanism to rename — records can never be
  `Copy` today (RFC-0071/RFC-0123), tuples have no impls at all (RFC-0061 §6), and only
  function pointers have a working one (RFC-0061 §7.2). Interacts with **RFC-0071**
  (Ownership and Move Semantics, affine-by-default foundation — see Aspect system core,
  below) more than with RFC-0134 itself.
- **RFC-0003** *(draft)* — Concurrency Model — fiber handles, channels, `select`,
  `Send`.

## Small, mostly standalone syntax/ergonomics items

- **RFC-0004** — `main()` return type — should it return `Result`?
- **RFC-0005** — Warn on unreachable match arms — **empty stub, no content written.**
- **RFC-0014** — Panic Recovery.
- **RFC-0015** — Unwrap Syntax — `.yolo()` vs. a keyword (resolved in practice: `.yolo()`
  is already implemented as a method, though as an interpreter special case rather than
  real dispatch — RFC-0079, which formalized this, was refused 2026-07-10 as redundant
  with already-shipped behavior; the dispatch fix is tracked at
  https://app.clickup.com/t/86cap1wzb, not by this RFC).
- **RFC-0017** — Language Edition System.
- **RFC-0026** — Unsafe Blocks — deferred, depends on a stable memory-safety model
  (RFC-0028, refused — needs re-pointing at whatever supersedes it).
- **RFC-0027** — C FFI.
- **RFC-0033** — Field-Level Mutability — additive `let` field annotation.
- **RFC-0038** — `impl Aspect` in Struct Fields / Existential Types.
- **RFC-0131** *(draft, opened 2026-08-09)* — Hoist `let`/`var` Bindings to the Top of
  Their Containing Block — `fun` declarations are already hoisted (visible regardless of
  declaration order); `let`/`var` are explicitly sequential-only, an asymmetry that
  became a real constraint fixing metel-core#656/#658 (a nested `fun`'s eager,
  order-independent build had to be restricted to blocks with no `let`/`var` at all, to
  avoid the eager build serving a stale, pre-execution snapshot of one). Sketches three
  designs — TDZ-style hoisting with same-block redeclaration banned, full dynamic
  hoisting needing resolve-by-declaration-identity, or narrowing `fun` hoisting further
  via a free-variable check instead — without yet choosing one; the current shadowing
  example (`let x=1; fun get_x(){x}; let x=2;` — `get_x` must still see the first `x`)
  is the concrete case any design has to survive.
- **RFC-0128** *(draft, opened 2026-08-04)* — Exportable Overload Sets and
  Shadow-versus-Extend Semantics — same-name module functions form one overload set;
  exports/imports preserve whole sets; lexical bindings shadow whole sets; and `extend`
  methods remain aspect dispatch rather than free-function overloads.
- **RFC-0138** *(draft, opened 2026-08-24)* — Generic Functions as First-Class Values —
  `functions.md`'s unqualified first-class-functions claim doesn't hold for a
  `<T>`-declared named function today: no value form at all, in any position, fully
  instantiated or not (metel-core#736). Proposes extending the existing closure
  let-polymorphism mechanism (deferred `scheme_env` instantiation, currently gated on
  the RHS being a syntactic closure literal) to also recognize a bare reference to an
  already-declared generic function. Traces the actual failure to the construction pass
  specifically (`ConstructCtx::lookup` deliberately excludes generic schemes from its
  own env, by the same design the closure case already uses) — inference itself already
  resolves a bare reference via `poly_env` auto-instantiation, it just doesn't
  re-generalize the alias binding, a latent gap this RFC also closes. #736 itself is
  being resolved in the interim by scoping `functions.md`'s claim down with an explicit
  carve-out, pending this RFC's acceptance.
- **RFC-0107** *(implemented 2026-07-21 — issue #559)* — Unqualified Enum Variants in Match
  Patterns — `Red` instead of `Colour::Red` in a match arm, resolved type-directed
  against the scrutinee's known enum (not a lexical-scope import, so no cross-enum
  collision risk). Generalizes the existing `Perhaps::None`-only special case
  (`Pattern::None`) into a real mechanism; answers RFC-0101's Unresolved Question 1.
- **RFC-0108** *(implemented 2026-07-21 — issue #559)* — Reference-Transparent Match Scrutinees —
  matching a `&T`/`&var T` value directly (`match c { Colour::Red => .., .. }` for
  `c: &Colour`) instead of the current `T0001 cannot unify &Colour with Colour`, with
  no workaround available today (`*expr` doesn't parse — Metel has no general deref
  expression). Extends RFC-0067a's field-access/method-dispatch auto-deref-chain
  principle to match scrutinees, the one place it's currently missing — `self` inside
  method bodies and `for`-loop element bindings already get this transparency via their
  own separate, narrower mechanisms. Sibling to RFC-0107 (§2 there), not overlapping.
- **RFC-0111** *(implemented 2026-07-21 — issue #572)* — Unqualified Enum Variants in Expression
  Position — the expression-position half of RFC-0107, and the follow-up RFC-0107 §5
  explicitly left open. Bare `Red` / `Some { value: 5 }` / `None` resolved type-directed
  against the *expected* type (`let c: Colour = Red;`, return position, monomorphic call
  arguments), which is what finally lets `Literal::None` retire and makes `None` an
  ordinary variant rather than a privileged builtin. Deliberately declines the reverse
  variant→enum index RFC-0107 §1.4 anticipated as the resolution mechanism (action at a
  distance — an unrelated new enum would break distant code); the index survives only as
  a gate on Pass 1 deferral, never to pick an enum. Notes that the Rust analogy the
  request came from actually points at scope import (`use Colour::*`), weighed and
  declined in §2.1 for consistency with RFC-0107's already-shipped choice. Real work is
  in Pass 1, which has no expected-type parameter at all.
- **RFC-0110** *(implemented 2026-07-21 — issue #559)* —
  Explicit Dereference Operator — **the Go half** of what was one RFC. Unary `*expr` for
  reads and for writing through (`*p = v`); auto-deref kept at *selectors only* (field
  access, field assign, method dispatch); bare assignment to a reference-typed identifier
  changed to mean rebind, which is what unlocks repointing — verified unrepresentable
  today (`p = &var b` fails with `cannot unify i64 with &var ?t18`). Demoted from
  `3-integrated` and its spec text backed out when the design changed to the Go model;
  read-side extensions split into RFC-0112. Also corrects its own earlier claim that
  index-path write-through was "kept unchanged" — it does not work through a reference
  today, so it is an addition with real cost.
- **RFC-0112** *(draft, opened 2026-07-21)* — Auto-Deref Scope and Expected-Type
  Provenance — **the auto-deref half.** Where implicit read-copy fires, and how that
  boundary is *enforced* rather than emergent. Rule: it fires only when the expected type
  was authored in the declaration the expression is lexically inside — not a callee's
  parameter list, a struct's field declaration, another operand, or compiler bookkeeping.
  Enforced by tagging every expected type with its origin, because RFC-0111 wants hints
  widened and RFC-0110 wants auto-deref narrowed *through the same parameter*, so without
  the tag the enum-variant work would silently re-add call-argument auto-deref. Verified to
  be a zero-behavior-change formalization; also documents that RFC-0067a §3a's text claims
  two positions (struct fields, match arms) it does not actually cover. Its §4.2 records
  where RFC-0110's "what does `&i64 == &i64` do?" open question actually led: nowhere near
  auto-deref — `==` has no operand check at all, so it typechecks and then aborts at runtime
  for references, structs, enums (including `Perhaps`), arrays, tuples and unit. Filed as
  issue #561; aspect-dispatch design fix at #259 / RFC-0062.
- **RFC-0098** *(implemented)* — Surface Keyword Renames — `extend Type` /
  `extend Type: Aspect` (reordered target-first, Swift precedent — not `impl X with Y`
  as first drafted), `pub` → `public`, `mut` → `var` (bindings, reference types, and
  reference expressions together). Three independent, purely lexical renames with no
  semantic change. Amends RFC-0032/0042/0044/0067A's surface syntax only — each
  already-implemented RFC's actual semantics (field-visibility enforcement, binding
  mutability, reference/auto-deref behavior, receiver dispatch) are untouched. Opened
  2026-07-13, accepted and integrated 2026-07-14.
- **RFC-0099** *(under review again, reopened 2026-07-14)* — Dot-Separated Module Paths — `::` → `.` for import/export,
  static/module, and enum-variant paths, and `::<` → `.<` for turbofish. Not a pure
  rename: `.` already means field/method access (RFC-0045), so this RFC has to settle a
  real disambiguation rule before the grammar change is well-formed. Capitalization-
  based disambiguation (Option A) was reviewed and rejected — it fails on real fixture
  code (`std::core::Perhaps::Some`, and the RFC's own worked example) since module path
  segments are lowercase, same as values; resolved at name-resolution time instead
  (Option B), reusing the existing `Expr::ResolvedPath` pattern already in the codebase.
  Turbofish (RFC-0023), found as a third, separate use of `::` this RFC also addresses,
  is respelled `.<` rather than left as `::<` (a "same disambiguation guarantee, just
  spelled to match" token substitution, not a new ambiguity). Amends RFC-0030's path
  grammar, reserved path roots (`root::`/`std::`/`self::`/`super::` → `.`-spelled), and
  RFC-0023's turbofish syntax. Reopened after acceptance to compare the full-dot design
  against a narrower context-limited dotted-path alternative before any integration.
- **RFC-0100** *(under review again, reopened 2026-07-14; split 2026-07-24)* — Constructor-Call Construction — `Type { field: value }` struct
  literals → `Type(field = value)` call-shaped construction. Real deliverable is general
  keyword arguments for function calls, not a struct-only rename — struct construction
  is just the first consumer. Like RFC-0099, not a pure addition: keyword arguments
  occupy a grammar position already spoken for. **Revised 2026-07-24 to spell them
  `name = value`, which dissolves the reason the RFC was reopened** — the ascription
  collision (`Foo(bar: Baz)` ambiguous between a keyword argument and an ascribed
  positional argument) was specific to the `:` spelling, not to keyword arguments as a
  feature. Under `=` the collision is with `assign_expr` instead, fixed by the same
  `arg_list` reordering at a much smaller cost: a bare assignment can no longer be a
  positional argument (the C `if (x = 5)` footgun), and type ascription is untouched in
  every position. Pattern-matching destructuring explicitly keeps its current
  `{ field }` syntax (deliberate asymmetry, not an oversight — see the RFC's own §4);
  patterns have no separator to change either way. Old literal syntax retired outright
  rather than kept as a second spelling, following RFC-0042's precedent — **though that
  case is weaker since the split**, which moved the invariant argument to RFC-0115.
  Opened 2026-07-13, accepted 2026-07-14.
- **RFC-0115** *(implemented 2026-07-24 in `develop`, ships v0.12.0, #575)* — Field Initializer Separator — `field_init` changes from
  `ident ":" expr` to `ident "=" expr`, so `Point { x = 1.0, y = 2.0 }`. **Split out of
  RFC-0100 on 2026-07-24**, which had bundled this with call-shaped construction; that
  made a settled, dependency-free question hostage to a contested one, with "the
  invariant gets a permanent exception" as the downside if RFC-0100 never landed.
  `field_init` is the *only* site in the grammar where `:` introduces a value, so this
  one-token change completes the `:` classifies / `=` defines invariant
  (`reports/syntax/colon-classifies-equals-labels-walrus-binds.md`) with no exceptions left. Braces,
  punning (`Point { x }`), and pattern destructuring all unchanged. Carries no grammar
  risk, unlike both of RFC-0100's separator proposals — `field_init` matches
  `ident ~ "="` directly, so the label never routes through `expr` and nothing can shadow
  it. Second motivation, and the stronger one: it aligns nominal struct literals with
  RFC-0090's settled anonymous record values, making `Point { x = 1.0 }` literally
  `{ x = 1.0 }` plus a brand — the relationship RFC-0090 tier 3 claims holds
  semantically, now visible in the syntax.
- **RFC-0136** *(under review, opened 2026-08-23)* — Walrus for Kept Bindings — extends
  the classify/define invariant with a third token: `let`/`var` declarations, plain
  reassignment, and `type X = Concrete` all currently spell "define" with `=`, the same
  token `field_init`, `assoc_binding`, and RFC-0100's not-yet-live keyword arguments use
  for a value or type consumed once at the site and not kept as a name. Splits on
  whether the introduced name is *kept* (referenceable after the statement — moves to
  `:=`) or *not kept* (a label — stays `=`). Four grammar rules change: `let_decl`,
  `let_mut_decl`, `assign_op` (plain `=` only), `assoc_type_def`; resolves RFC-0100's
  `f(x = 1)`/`assign_expr` collision as a side effect, since plain `=` can no longer
  parse as assignment inside an argument position at all. Largest syntax-migration
  surface proposed to date — every `let` and plain reassignment in the corpus. Open:
  whether compound assignment operators (`+=` etc.) move too; coordination with
  RFC-0132's `comptime let`. Declaration-side default parameter values explicitly out of
  scope. See `reports/syntax/colon-classifies-equals-labels-walrus-binds.md`.
- **RFC-0101** *(draft)* — Grammar-Enforced Naming Case Conventions — PascalCase for type
  declarations (struct/enum/aspect/generic params) and enum variants, camelCase for
  `fun` declarations (free functions, methods, associated functions), SCREAMING_CASE for
  constants (module-level, immutable `let` bindings — no dedicated `const` keyword
  needed, since the grammar already distinguishes `let` from `var`), snake_case for
  everything else that introduces a name (function-local `let` bindings, parameters,
  struct fields) — enforced as a real compile-time check (a post-parse AST pass, not
  literally embedded in `grammar.pest`), not just a style convention. PascalCase-types,
  snake_case-bindings, and the (currently unused) constants row all need zero renames
  across `stdlib/` and the test suite; camelCase-for-`fun` is the one real, active
  change, requiring a full rename pass across every existing function and method.
  Surfaced from reviewing RFC-0100's keyword-argument/ascription collision, but
  deliberately scoped as its own RFC rather than folded into that one — it's a general
  readability property, and does *not* rescue RFC-0099's own disambiguation question
  (module path segments share casing with
  values, an orthogonal problem). Opened 2026-07-14.
- **RFC-0102** *(integrated 2026-07-14)* — Bodyless Extend Blocks for Marker Aspects and
  Negative Impls — `extend Type: Aspect;` / `extend Type: !Aspect;` (no braces) as
  sugar for an empty-bodied `extend` block, valid in exactly the situations an empty
  body is already accepted today (positive impls, when every method has a default
  body or the aspect declares none, the true marker-aspect case). Pure desugaring, no
  new semantic category — mirrors `fun_decl`'s existing `(block | ";")` alternative.
  **For negative impls, the bodyless form isn't optional sugar — the old
  `extend Type: !Aspect { }` braces spelling is retired outright**, since a negative
  impl's body is never meaningfully non-empty (nothing `{ }` could say that `;`
  doesn't), matching this project's own precedent (RFC-0100, RFC-0042) for retiring a
  strictly-superseded spelling rather than keeping two. §5 extends the aspect clause
  to a comma-separated, per-item-polarity list for the same bodyless case
  (`extend Type: A, B, !C;`, desugaring to N independent single-aspect blocks; any
  negative item forces the whole list bodyless), reusing RFC-0036's existing `bound`
  grammar directly — strictly scoped to bodyless/empty-bodied extends, since a shared
  non-empty body across multiple aspects has no principled disambiguation and isn't
  attempted. Depends on RFC-0098's `extend Type: Aspect` grammar shape. Opened
  2026-07-14, accepted and integrated 2026-07-14.
- **RFC-0103** *(integrated 2026-07-14)* — Bodyless Aspect Declarations — a bodyless
  spelling for the aspect *declaration* itself (`aspect Copy2;` — pure sugar for
  `aspect Copy2 { }`, legal whenever the braced form already would be, no permanence
  guarantee attached, unlike an earlier draft's dropped `marker` keyword). This is
  the aspect-declaration analogue of RFC-0102's bodyless `extend`-block sugar, and
  nothing more.
- **RFC-0105** *(draft, split from RFC-0103 on 2026-07-14)* — Struct-Embedded Aspect
  Lists — the deferred `struct Token: Copy2, Serializable, !Send { value: String }`
  / `enum ... : ...` proposal. Reuses RFC-0102 §5's `extend_aspect_list`, where
  struct/enum bodies stay fields-only: negative items are fully satisfied by the list
  itself, while every positive item declares a checked, module-wide *obligation*
  discharged by an ordinary, separately-editable `extend` block elsewhere. Split out
  so the larger declaration-surface and coherence/auto-impl questions can be judged
  separately from RFC-0103's smaller bodyless-declaration feature. A still-earlier
  `marker` keyword (permanently gating which positive items
  the list alone could satisfy) was dropped outright once every positive item became
  an obligation uniformly — the permanence guarantee it offered stopped being
  load-bearing. Its last two open questions are now resolved: the obligation check
  runs inside the same already-existing whole-graph coherence pass (`coherence.rs`,
  RFC-0060) rather than a new stage, since that pass already collects every
  `Decl::Impl` across every loaded module before checking orphan/overlap rules —
  confirmed directly against the actual implementation, not assumed; and a real
  interaction with RFC-0096 (Auto-Impl Aspects, draft) was found and fixed by placing
  a requirement on RFC-0096's own implementation instead of special-casing it here —
  `Send`/`Sync`/`Linear` must be injected into the same aspect-implementation
  registry an ordinary `extend` block populates (RFC-0096 §5 already half-commits to
  this: "an auto-impl is an ordinary positive impl for coherence purposes"), so this
  RFC's obligation check needs a single, mechanism-agnostic registry lookup with zero
  special-casing, rather than querying a separate `satisfies` predicate keyed to
  three specific aspect names (an initial draft of §4, reversed once it was clear
  that coupled this RFC to RFC-0096's internals unnecessarily). Depends on RFC-0102
  and (for §4) places a new implementation requirement on RFC-0096. Opened
  2026-07-14, accepted 2026-07-14.
- **RFC-0106** *(implemented 2026-07-14)* — Optional Braces for Empty Constructors —
  zero-field structs may be written as either `Empty` or `Empty {}`, and zero-field
  enum variants as either `Type::Variant` or `Type::Variant {}`. Implemented as a
  narrow parser/typechecker change only: non-empty constructors are unchanged, and
  empty enum-pattern braces were not added as part of this RFC. Opened 2026-07-14,
  implemented 2026-07-14.
- **RFC-0104** *(draft)* — Multi-Aspect Extend Blocks with Shared Bodies — split out
  of an earlier draft of RFC-0103's own struct/enum-embedding section, since it's a
  separate feature that doesn't depend on anything there. Lifts RFC-0102 §5's
  bodyless-only restriction for `extend` blocks specifically: `extend A: Aspect3,
  Aspect4 { ... }` with a real, shared, non-empty body. Disambiguation reuses a
  tolerance that already exists in today's single-aspect impl checking (extra methods
  beyond what an aspect requires already become ordinary inherent methods,
  uncontested) — generalized to multiple aspects by checking each one's own
  required-method coverage independently against the same shared pool. The one new
  rule: if two named aspects in the same list declare a method with the identical
  name, the whole combination is rejected outright rather than guessing or
  introducing a qualified-declaration syntax. Depends on RFC-0102. Opened 2026-07-14.

---

## Settled (reference only — not part of active tracking)

**Implemented:** RFC-0006, RFC-0007, RFC-0010, RFC-0018, RFC-0019, RFC-0020, RFC-0021,
RFC-0022, RFC-0023, RFC-0030, RFC-0031, RFC-0032, RFC-0034, RFC-0035, RFC-0040,
RFC-0041, RFC-0042, RFC-0044, RFC-0045, RFC-0053, RFC-0054, RFC-0057,
RFC-0058, RFC-0059, RFC-0060, RFC-0061, RFC-0098, RFC-0106.

Also implemented but not yet folded into this list (Cluster A, landed
2026-07-15/17 — see `REGISTRY.md` for the exact, generated set): RFC-0036,
RFC-0037, RFC-0067A, RFC-0072, RFC-0078, RFC-0081, RFC-0082, RFC-0097,
RFC-0102, RFC-0103.

**Superseded:** RFC-0001 (→ later pointer work), RFC-0002 (aspect bound syntax),
RFC-0043 (Regular Pointers, `*T`/`*mut T` → RFC-0067a's `&T`/`&var T`; file was never
moved out of `4-implemented/` despite RFC-0067a's own text saying so since
2026-06-28 — caught and fixed 2026-07-20 while drafting RFC-0110),
RFC-0009 (module system → RFC-0030), RFC-0012 (→ RFC-0092/0093/0094/0095), RFC-0013
(integer overflow), RFC-0016 (stdlib foundation), RFC-0024 (linear types → RFC-0028,
which was then refused — RFC-0089 re-homes this), RFC-0029 (module system gaps),
RFC-0052 (lifetime system → RFC-0067; predates the 2026-07-02 allocator/anchor split
and depended entirely on refused prerequisites RFC-0025/0028/0051), RFC-0055 (comptime
→ RFC-0092/0093/0095, reconciled 2026-07-09 — see above), RFC-0083 (public value
exports → RFC-0092 §0a; see fold note above).

**Refused:** RFC-0025, RFC-0028, RFC-0046, RFC-0047, RFC-0048, RFC-0051, RFC-0056,
RFC-0064, RFC-0069, RFC-0079, RFC-0084, RFC-0085, RFC-0086, RFC-0087 —
mostly the earlier region/lifetime model iterations that didn't survive the 2026-07-05
split, plus RFC-0046 (linear closure capture, blocking RFC-0050's `move` half), plus
RFC-0064 (structured fork-join `||`, retracted 2026-07-07 — its one guarantee, a fiber
cannot be silently abandoned, relocated onto `JoinHandle<T>` from `spawn`), plus
RFC-0084 (refused 2026-07-10 — reverted in place to reaffirm RFC-0053's
`[T; N]`/`[expr; N]` exactly, with nothing left of its own to propose), plus RFC-0079
(refused 2026-07-10 — most of `Perhaps<T>`/`Result<T, E>` was already implemented and
spec'd by the time it was written, and its `?`-operator section was factually wrong
relative to already-shipped `From`-based coercion; real remaining gaps tracked at
https://app.clickup.com/t/86cap1wzb).

---

## Maintenance note

This file is intentionally **manual and curated**. Update it when a current RFC needs
thematic placement, a cluster description changes, or a relationship note becomes
misleading. Do **not** duplicate stage counts, generated status summaries, or other
derivable facts here — those belong in `REGISTRY.md`, and `rfc.py check` treats that
generated file as the exact source of truth.
