---
id: rfc-0122
title: "Borrow Checking"
date: '2026-07-24'
status: accepted
target:
updated: '2026-08-02'
---

> **Opened 2026-07-24** against `OBJECTIVES.md` Trigger 19, which has tracked the borrow
> checker as "carrying more architectural weight than any other undocumented thing in the
> project." Written as the design half of v0.12.0, running alongside RFC-0071's
> implementation rather than gating it — move checking and borrow checking are separable,
> and only the former is specified today.
>
> **Trigger 19's framing needs one correction, made here rather than left standing.** It
> records that "the borrow checker has no RFC at all — the only match for 'borrow' across
> 112 RFCs is RFC-0086, which is `6-refused`." That is true of the *title* search but
> understates what exists: **RFC-0067 (Lifetime Anchors) is `2-accepted`** and specifies a
> surface for naming borrow validity — `&r T` carries anchor `r`, a binding whose scope
> bounds the borrow — having itself superseded RFC-0052 (Lifetime System).
>
> **What is missing is the checking rules**, and that is this RFC's scope.
>
> **This RFC does not depend on RFC-0067, and an earlier draft said it did.** *(Corrected
> 2026-07-24.)* The dependency runs the other way:
>
> - **The rules need only `&T` and `&var T`** (RFC-0067a, `4-implemented`). Shared XOR
>   exclusive is a question about which borrows coexist at a program point — it never needs
>   a borrow's validity scope to be *named*. Local outlives checking is scope-based for the
>   same reason.
> - **Anchors are a disambiguator for the cross-function minority case.** RFC-0067's own
>   §-on-declaration says so: `fun longest<&r>(&r Str, &r Str) -> &r Str`, with "elision
>   rules (RFC-0065 §2) cover the common cases; `<&r>` declarations appear only when the
>   relationship is ambiguous."
> - **So anchors presuppose a checker, not the reverse.** `&r T` denotes nothing without
>   rules that enforce it; rules without anchors still check every local borrow and every
>   elided signature.
>
> The practical consequence is the point: **this RFC is buildable without RFC-0067**, which
> is `2-accepted`, unimplemented, and itself carrying stale syntax (ten `&var` occurrences
> predating RFC-0098, whose last update was 2026-07-10, four days before RFC-0098 shipped).
> *(Count corrected 2026-08-01: the original said nine.)*
> RFC-0067 should be treated as a dependent extension, and its acceptance re-examined
> against these rules rather than assumed to constrain them.

> **Status — accepted (2026-08-02).** All five design questions resolved: granularity and move-relationship (07-24), lexical-first, observability, and diagnostics (08-01 joint review). RFC-0071 SS9b's standalone place abstraction — this RFC's only structural blocker — discharged by #291.

## Summary

**The headline rule, which is stated nowhere in the corpus today:**

> **Shared XOR exclusive.** For any given place, a program may hold *any number* of `&T`
> borrows, or *exactly one* `&var T` borrow, and never both at once.

Everything else here is machinery for enforcing that, plus the second rule that a borrow must
not outlive its referent. This RFC specifies what the compiler computes, what it rejects, and
what diagnostics it produces — against the anchor notation RFC-0067 already accepted, and on
top of the move/partial-move tracking RFC-0071 specifies.

**This RFC adds no syntax.** `&T`, `&var T` (RFC-0067a) and `&r T` (RFC-0067) already
exist. It supplies the rules those spellings are currently checked by — which today is
nothing at all.

### Why this is the headline rather than one item among several

**`&var T` is called "exclusive" by both the spec and RFC-0067a, and nothing defines or
enforces that.** RFC-0067a is `4-implemented`; the spec's References section lists `&var T`
as "exclusive mutable reference to `T`" and never says what exclusive *means*. The word is
doing load-bearing work as a bare adjective.

**RFC-0071 cannot supply it, and a nearby resolution makes that easy to miss.** It resolved
(2026-07-24) that `&var T` is not `Copy`, which stops an exclusive reference being
*duplicated* — but not two being created independently:

```metel
let a = &var x;
let b = a;         // rejected: !Copy, so `a` was moved
let c = &var x;
let d = &var x;    // nothing in RFC-0071 forbids this
```

Ownership answers "how many owners". `Copy` answers "may this be duplicated". Neither answers
"what is borrowed right now", which is the only question that yields exclusivity. **So
`&var` ships today on a promise no document makes and no pass checks.**

**Three programs, all accepted today under `--move-check`** *(verified against the built
interpreter, 2026-08-01, not reasoned about)*. The first shows two exclusive borrows
coexisting; the second and third show the aliasing actually being observed, which is what
makes this a soundness rule rather than a hygiene one:

```metel
struct P { v: i64 }

fun both(a: &var P, b: &var P) { a.v = 10; b.v = 20; }

// (1) two exclusive borrows of one place — accepted
var x = P { v = 1 };
let c = &var x;
let d = &var x;

// (2) the same, aliased across a call boundary — accepted, prints 20
both(&var x, &var x);

// (3) the owner writes through an outstanding exclusive borrow — accepted, prints 99
let r = &var x;
x.v = 99;
println(r.v.to_string());
```

Case (2) is the one worth dwelling on: a compiler entitled to assume `a` and `b` do not
alias would be entitled to reorder those two writes. Nothing today earns that entitlement,
and nothing rejects the program that violates it.

---

## Motivation

Three things depend on borrow checking and none of them can be finished without it:

- **`OBJECTIVES.md` §1's differentiation claim** rests on "concrete lifetime diagnostics
  named after real bindings rather than abstract `'a`." That is a claim about *diagnostics
  from a checker*, and there is no checker.
- **`allocators-as-emergent-synthesis.md`** decomposes `@a T` as "an owned box type + the
  borrow checker checking it outlives `a`." The borrow checker is a load-bearing term in
  the decomposition that justifies Priority 4's entire structure.
- **RFC-0117 (Row Narrowing) and RFC-0109 (Self-View Narrowing)** both reason about
  borrowed sub-rows. RFC-0109 is explicitly "paper-only territory" pending this.

Meanwhile the interpreter deep-clones every value, so no reference rule of any kind is
enforced at runtime today. Every borrow-related guarantee in the corpus is currently
aspirational.

**Why now, and why as design only.** RFC-0071's move checking is fully specified and
unimplemented; this is unspecified. Doing the design here while the implementation work
happens there means v0.13.0 can consider building it, rather than discovering at that
point that a month of design is still needed. It also means the design gets written
*against* a real move checker rather than against a guess — the sequencing argument for
deferring it entirely, which was considered and rejected on the grounds that the two
concerns are separable in the specification even where they interact in the implementation.

---

## 1. Scope

**In scope:**

- When a borrow is valid with respect to the scope of what it borrows. Naming that scope
  explicitly (`&r T`, RFC-0067) is a separate, later concern.
- **Enforcing shared-XOR-exclusive** — which borrow pairs conflict (shared/shared never;
  shared/exclusive and exclusive/exclusive always) and over what granularity: whole value,
  field, or index.
- **Call-site argument aliasing** — `both(&var x, &var x)` creates two exclusive borrows
  of one place and passes them to one call. *(Stated explicitly 2026-08-01: an earlier
  draft's scope section deferred "naming that scope explicitly" to RFC-0067 in a way that
  left this case ambiguous.* **It is in scope, and it is not a naming question.** Nothing
  about it requires a borrow's validity scope to be *named*: the two borrows are created
  in the same expression, in the caller's own frame, and conflict there by the same
  shared-XOR-exclusive rule as any other pair. The callee's signature is irrelevant to
  detecting it. Deferring this to anchors would leave the single most direct violation of
  the headline rule unchecked by the RFC that states the rule.)
- Interaction with RFC-0071's move and partial-move tracking: a moved-from place cannot be
  borrowed; a borrowed place cannot be moved from.
- Reborrowing, already surfaced by v0.11.0's `&*p` and by RFC-0067's coercions.
- Diagnostics, which §1's differentiation claim makes a first-class deliverable rather than
  a quality-of-implementation detail.

**Out of scope:**

- Any new surface syntax. RFC-0067/0067a own the spellings.
- Allocator interaction beyond what RFC-0067 already specifies for `@a T` coercion.
- Row/view-specific borrowing — RFC-0109 and RFC-0119's dropped by-reference mode both
  raise questions (notably provenance: whether several borrows are known to come from one
  object) that this RFC should make *answerable* but should not answer for them.

---

## 2. Design questions this RFC exists to settle

**All five are resolved as of 2026-08-01** — questions 1 and 3 on 07-24, questions 2, 4
and 5 in a joint review on 08-01. They are kept in question form, with their resolutions
appended rather than rewritten into flat prose, because the reasoning that settled each
one is the substance of this RFC; a reader who disagrees with a rule should be able to
see exactly what argument produced it and attack that.

*Numbered §2.1–§2.5 for citation.*

1. ~~What granularity does conflict detection use?~~ **Resolved 2026-07-24: per-field for
   statically-named fields; whole-value for anything reached through a dynamic index.**
   Three constraints converge and leave no other option:
   - **RFC-0071 §7 already tracks partial moves "at field granularity."** Whole-value borrow
     granularity would disagree with it: you could move `x.a` out but not borrow `x.b`
     without conflicting on `x`. The two analyses must agree about places (see question 3),
     so borrow granularity is fixed by a decision already taken.
   - **RFC-0109 §3 requires it.** Its reference-destructuring pattern "splits one `&var`
     borrow into disjoint per-field sub-borrows." Whole-value granularity makes that
     construct unimplementable.
   - **Per-index is not statically decidable, and RFC-0071 §9a already ruled on the same
     question.** It bans moving out of an array element because the index may be dynamic, so
     *which* element left is not a static fact. Borrows inherit the reasoning: a borrow
     through an index borrows the whole container. Rust lands in the same place — indexing
     borrows the container, and disjoint element access needs an explicit split.

   **Named tuple and record fields are per-field too**, by the same rule: RFC-0071 §9a
   resolved tuple partial moves as identical to struct fields because positional fields are
   statically named, and RFC-0117's record narrowing is per-field.

   **One asymmetry worth stating, because it is easy to get backwards: a `Drop` type may be
   partially *borrowed* even though it may not be partially *moved*.** RFC-0071 §7 bans the
   latter because the destructor needs the whole value. A borrow ends and returns the value
   intact, so the destructor still sees everything. Nothing about `Drop` restricts borrow
   granularity.
2. ~~Lexical or non-lexical?~~ **Resolved 2026-08-01: lexical first.** A borrow is live
   from its creation to the end of the enclosing scope; non-lexical liveness (ending a
   borrow at its last use) is a later, separately-decided tightening.

   **The argument is asymmetric reversibility, and it is the whole reason to decide it
   this way rather than by preference.** Lexical → non-lexical accepts *strictly more*
   programs: every program a lexical checker admits, an NLL checker also admits. So the
   later move is backward-compatible, needs no corpus migration, and breaks nothing.
   The reverse — shipping NLL and later restricting to lexical — would reject
   already-valid programs, which is a breaking change no release could absorb quietly.
   Given genuine uncertainty about which is right, the option that can be changed later
   for free is the one to take first.

   ```metel
   let r = &var x;
   r.v = 1;
   // r is never used again, but under lexical rules it stays live
   let s = &var x;   // REJECTED under lexical; would be ACCEPTED under NLL
   ```

   **This will reject ordinary code, and that cost is accepted knowingly, not
   overlooked.** Rust shipped lexical borrows for years and moved to NLL precisely
   because the false-rejection rate was a real ergonomic problem. Metel is choosing the
   same starting point with the benefit of knowing where it leads — the escape hatch in
   the interim is the one Rust users used, an explicit block to bound the borrow's
   scope:

   ```metel
   { let r = &var x; r.v = 1; }   // borrow ends with the block
   let s = &var x;                // now fine under lexical rules
   ```

   **RFC-0067's anchors are consistent with this and do not force it.** `&r T` names a
   binding whose scope bounds the borrow, which reads lexically — but as the header
   note establishes, anchors presuppose these rules rather than supplying them, so this
   decision is not inherited from RFC-0067; it merely happens not to conflict with it.

   *Operator decision, recorded in `reports/strategy/OBJECTIVES.md` §0.*
3. ~~What is the relationship to RFC-0071's move tracking — one analysis or two?~~
   **Resolved 2026-07-24: two analyses over one shared place abstraction.** Rust's borrow
   checker is the precedent — initialization/move tracking and borrow tracking run as
   *separate* dataflow analyses over a *shared* place representation (MIR places and move
   paths), in the same pass. Not one monolithic analysis, and not two passes with
   independent notions of what a place is.

   **The useful part of this answer is what it implies for sequencing, because the question
   as posed was slightly the wrong one.** The risk was never "one or two" — it is *whether
   RFC-0071's implementation builds a move-only place representation that a later borrow
   checker cannot reuse.* If the place abstraction is a separate, reusable component, move
   checking can ship in v0.12.0 and borrow checking can add a second analysis over the same
   places later, with no rework. If places are folded into move-specific state, the borrow
   checker has to rebuild them.

   **So this converts into one requirement on RFC-0071's implementation**, recorded there
   and to be carried into its tracking issue: *the place abstraction must be a standalone
   component with no move-specific assumptions.* Given that, splitting the two across
   releases is safe, and the argument for pulling this RFC into v0.12.0 falls away.

   **✅ Discharged 2026-08-01 by #291, verified directly against the interpreter.** The
   place abstraction lives at `metel-interpreter/src/place.rs` — crate root, not inside
   `move_check` — is 203 lines, and carries no move-specific state: every mention of
   "move" in the file is module documentation explaining *why* it is analysis-neutral
   (its own doc comment: *"Policy lives with each analysis, not here"*), and
   `move_check/mod.rs` is its only importer. `Place`, `Projection::{Field, TupleIndex,
   OpaqueIndex, Deref}`, `is_prefix_of`, and `from_expr`/`from_typed_place` are all
   available to a second analysis unchanged. See `metel-interpreter/docs/decisions/
   adr-0045` and RFC-0071 §9b.

   **This is the whole of what stood structurally between this RFC and implementation.**
   With it discharged, borrow checking is a second dataflow analysis over an existing,
   already-tested representation — not a rebuild.
4. ~~Does the interpreter's deep-cloning evaluator make any of this observable?~~
   **Resolved 2026-08-01: yes, and the cloning is what makes the checker necessary
   rather than redundant.** The question assumed the runtime's cloning might make a
   rejected program harmless. The opposite is true — it makes the bug *silent*:

   ```metel
   struct B { v: String }
   let b = B { v = "owned" };
   let r = &b;          // borrow outstanding
   let taken = b;       // value moved out from under it
   println(r.v);        // prints "owned" — accepted today
   ```

   *(Verified against the built interpreter, 2026-08-01.)* `r` should be dangling. It
   isn't, because the evaluator deep-cloned — so the program produces a plausible answer
   instead of crashing, and nothing signals that the source is wrong. A runtime that
   faulted here would at least be self-reporting; one that silently papers over the
   error is exactly the case where a static checker carries the whole diagnostic burden.

   **There is now empirical precedent, which did not exist when this question was
   written.** RFC-0071's move checking shipped in v0.12.0 as an opt-in analysis over
   this same cloning evaluator, and found six real defects the runtime had been
   masking (#296, #313, #334, #343, #347, #348). A static checker over a
   value-semantics runtime is not a theoretical exercise here; it has already paid.

   **The honest limit, per `OBJECTIVES.md`'s feedback-trustworthiness budget:** this
   buys *design* feedback (does the rule reject what it should, accept what it should)
   and not *runtime* guarantees, which arrive only when the evaluator stops cloning.
   `evaluator/mod.rs` carries 93 `.clone()` calls as of 2026-08-01 — up from the 91
   RFC-0071's own 07-24 audit recorded, so that day is not approaching on its own.
5. ~~What does a diagnostic look like?~~ **Resolved 2026-08-01 by specification, since
   §1's differentiation claim makes wording a deliverable rather than an implementation
   detail.** Every borrow diagnostic names **two program points and one binding**: where
   the conflicting borrow was created, where the conflict occurs, and the binding whose
   scope keeps the first borrow live. No abstract lifetime variable appears in any of
   them.

   ```text
   [T0020] type error in main.mtl:6:13: cannot borrow `x` as exclusive more than once
     `x` is already borrowed exclusively by `c`, created at main.mtl:5:13
     that borrow stays live until the end of the enclosing scope (main.mtl:9:1)
     help: end the first borrow sooner by scoping it — `{ let c = &var x; … }`
   ```

   ```text
   [T0020] type error in main.mtl:7:5: cannot borrow `x` as exclusive while it is
   borrowed as shared
     `x` is borrowed as shared by `r`, created at main.mtl:6:13
     that borrow stays live until the end of the enclosing scope (main.mtl:10:1)
   ```

   ```text
   [T0020] type error in main.mtl:7:17: cannot move out of `b` while it is borrowed
     `b` is borrowed by `r`, created at main.mtl:6:13
     moving `b` would leave `r` referring to a value that no longer exists
   ```

   Three properties are load-bearing and should be treated as normative, not as sample
   prose: **(a)** the conflicting borrow is always attributed to *the binding that holds
   it* (`c`, `r`), never to an anonymous region; **(b)** the reason a borrow is still
   live is always stated as a **scope end with a line number**, which is only expressible
   *because* §2.2 chose lexical — under NLL the honest answer is "its last use," a
   materially harder thing to point at; **(c)** the `help:` line names the scoping escape
   hatch, since under lexical rules that is the fix in the large majority of cases.

   **A new error code is required: `T0020`.** T0019 is RFC-0071's move-checking code and
   covers seven distinct situations already; borrow conflicts are a different analysis
   with a different opt-in flag, and folding them into T0019 would make the code
   meaningless as a triage signal. To be registered in `public/reference/error-codes.md`
   at integration, not before — a code that no pass emits should not appear in the
   reference.

---

## 3. Migration cost, and why it is a sequencing constraint

*Added 2026-08-01. Nothing in the earlier draft costed this, and it is the largest
practical risk to implementing the rules above.*

**Shared-XOR-exclusive will invalidate existing Metel programs, including this
project's own fixture corpus.** The evidence is direct and recent: RFC-0071's #348 added
*one* narrow rule — a by-value `self` method may not be called through a reference — and
that alone required migrating five corpus fixtures that had been relying on the gap. A
rule as broad as "at most one `&var` per place, and never alongside a `&`" touches far
more surface, and the three programs in the Summary above are all currently-passing
shapes that would stop compiling.

**The constraint this creates: do not enable borrow checking by default in the same
release as #310.** #310 (enable move checking by default) is already queued for
v0.13.0, and it carries its own corpus migration. Landing both defaults together would
make a failing fixture ambiguous between two new analyses, and would put two unrelated
migrations in one release's blast radius.

**Recommended sequencing, following the precedent RFC-0071 set and which worked:**

1. Borrow checking ships **opt-in behind its own flag** (`--borrow-check`), exactly as
   move checking shipped behind `--move-check` — no corpus migration required to land
   it, and the analysis becomes testable against real programs immediately.
2. The corpus migrates incrementally, under that flag, as its own tracked work.
3. Only then does enabling-by-default become a separate, independently-schedulable
   decision — and in a different release from #310's.

This is not a concession to expedience. Opt-in is what allowed #291's move checker to be
built, reviewed, and hardened against six real defects across v0.12.0 without ever
blocking an unrelated release.

---

## References

- RFC-0067a (Reference Types), `4-implemented` — `&T` / `&var T`, **this RFC's only
  reference-side dependency**
- RFC-0067 (Lifetime Anchors), `2-accepted` — **a dependent, not a dependency.** Its `&r T`
  anchors name a validity scope for the cross-function cases elision cannot infer; they
  presuppose the rules here rather than supplying them. Supersedes RFC-0052 (Lifetime
  System). Carries pre-RFC-0098 `&var` spelling (ten occurrences, verified 2026-08-01)
- RFC-0071 (Ownership and Move Semantics), **`3-integrated`, `impl_status: in-progress`**
  — move and partial-move tracking, which this must agree with about places. *(Updated
  2026-08-01: was cited as `2-accepted`/"scheduled for implementation in v0.12.0"; parts
  1–2 shipped in v0.12.0 as #290/#291, and **§9b's place-abstraction requirement — the
  only thing this RFC asked of it — is discharged**, see §2 question 3. Parts 3–4 (#292
  drop order, #293 partial moves) are queued for v0.13.0.)*
- RFC-0086 (Outlives-of-Bindings Sugar), `6-refused` — the only prior "borrow"-titled RFC;
  refused, and its refusal is not evidence against this one
- `reports/strategy/OBJECTIVES.md` — Trigger 19, and §1's diagnostics claim
- `reports/substructural-types/allocators-as-emergent-synthesis.md` — the decomposition
  that makes this load-bearing for Priority 4
- `internal/rfcs/0-draft/rfc-0109-self-view-narrowing-and-reference-destructuring-patterns.md`
  — deferred; its borrowed-view questions depend on the outcome here

---

## Decision

**Outcome:** **Accepted 2026-08-01.** All five design questions in §2 are resolved and
none blocks implementation. The headline rule (shared XOR exclusive), its granularity
(per-field for statically-named fields, whole-value through a dynamic index), its
liveness model (lexical), its relationship to move checking (two analyses, one shared
place abstraction), its diagnostic format (`T0020`, naming bindings and scope ends), and
its rollout constraint (§3: opt-in behind `--borrow-check`, not default-on alongside
#310) are all settled.

**What acceptance does *not* claim.** No borrow checking ships in v0.12.0 — this RFC was
always scoped design-only for that release, and its acceptance changes nothing about
what the interpreter enforces today. The three programs in the Summary still compile.
Integration (`3-integrated`) additionally requires merging these rules into
`public/reference/spec/` with worked examples checked against everything already
integrated, and — per `PROCESS.md` — a tracked implementation issue, neither of which
exists yet.

**Target:** implementation not yet scheduled. RFC-0071's remaining parts (#292 drop
order, #293 partial moves) are v0.13.0 and share this RFC's place abstraction; whether
borrow checking lands alongside them or after is a scheduling decision for the release
that picks it up, constrained only by §3's requirement that it not go default-on in
the same release as #310.
