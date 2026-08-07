---
id: rfc-0122
title: "Borrow Checking"
date: '2026-07-24'
status: under-review
target: v0.14.0
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
> is `1-under-review` and unimplemented.
> *(Corrected 2026-08-02. This sentence previously added "and itself carrying stale syntax
> (nine — later 'corrected' to ten — `&var` occurrences predating RFC-0098)". **The claim
> was false**: RFC-0098 renamed `mut`→`var`, so `&var` is the current spelling, and
> metel-core#604's docs sweep had already converted RFC-0067's occurrences — it carries
> zero `&mut`. Worth recording how the error survived: a reader re-verified the **count**
> and shipped a correction to it without ever checking the **assertion** the count was
> attached to. RFC-0067 did have real stale syntax — a `null` literal Metel has never had,
> a bare `mut` in prose, and two retired `:` field separators — just not this.)*
> RFC-0067 should be treated as a dependent extension, and its acceptance re-examined
> against these rules rather than assumed to constrain them.

> **Status — accepted (2026-08-02).** All five design questions resolved: granularity and move-relationship (07-24), lexical-first, observability, and diagnostics (08-01 joint review). RFC-0071 SS9b's standalone place abstraction — this RFC's only structural blocker — discharged by #579.

> **Status — under review (2026-08-02).** Acceptance 2026-08-01 was premature. An adversarial pass the same day found six gaps, three blocking: the outlives rule is named but unspecified; reference-typed struct fields defeat the anchors-are-a-dependent claim; and the lexical rule as written rejects sequential &var method calls. Third accepted-to-under-review reversion in the corpus (Trigger 14).

> ## Targeted at v0.14.0
>
> *Set 2026-08-02 by operator decision, giving this RFC a concrete release for the first
> time.* v0.14.0 sits between v0.13.0 (RFC-0071's remaining parts and move-checker
> hardening) and **v0.15.0 (RFC-0067, Lifetime Anchors)** — an ordering that is forced,
> not chosen: RFC-0067's own open questions cannot be answered until this RFC settles what
> a validity scope is, and its §1 anchor model was written before any checker existed.
>
> **What must close first**, all in §2b: the outlives rule specified (§2b.2), the
> stored-reference restriction implemented (§2b.3 / metel-core#274), closures (§2b.4),
> reborrowing (§2b.5), and the `T[]` `Copy`-view interaction (§2b.6). §2b.1 is already
> dissolved by §2.2's move to NLL.
>
> **No implementation issue exists for this RFC yet, deliberately** —
> `public/rfcs/PROCESS.md` allows one only from `3-integrated`, and this is
> `1-under-review`. The v0.14.0 milestone therefore carries no work for this RFC today;
> that is the expected state, not an oversight, and it changes the moment §2b closes and
> this reaches `2-accepted` → `3-integrated`.
>
> **§3's rollout constraint still binds and interacts with the schedule:** borrow checking
> ships opt-in behind `--borrow-check` and must **not** go default-on in the same release
> as #267 (enable move checking by default, currently v0.13.0). With this RFC at v0.14.0
> and #267 at v0.13.0 those are already in different releases, which satisfies the
> constraint — worth stating so a later reshuffle does not silently break it.

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
and 5 in a joint review on 08-01. **This was mistaken for completeness and it is not:
see §2b for six further gaps that reverted this RFC's acceptance the same day.** §2.2's
resolution in particular is *incomplete as written*, not merely joined by others — read
§2b.1 alongside it. They are kept in question form, with their resolutions
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
2. ~~Lexical or non-lexical?~~ **Resolved 2026-08-01: non-lexical (NLL) — a borrow is
   live from its creation to its last use, not to the end of its scope.** *(This
   supersedes a same-day resolution of "lexical first", withdrawn after the operator
   asked whether a Polonius-style checker was feasible instead; the reasoning that
   replaced it is below and the superseded argument is preserved at the end of this
   item.)*

   ```metel
   let r = &var x;
   r.v = 1;          // r's last use — the borrow ends here
   let s = &var x;   // accepted: nothing of r is live
   ```

   **Three reasons, in order of weight.**

   **(a) It is reachable without building a CFG, which is the constraint that actually
   decides this.** Metel's pipeline has no MIR and no IR of any kind; `move_check` walks
   the typed AST. But Metel's control flow is **fully structured** — no `goto`, no
   arbitrary labeled jumps (verified against `grammar.pest`) — so the AST is a reducible
   CFG, and an AST-directed dataflow analysis has the same power as a CFG-based one over
   it. `move_check` is the in-repo proof: 4357 lines, loop fixed-point analysis with
   `LoopFrame`/`unwound_to`, entirely AST-directed. Last-use liveness is computable the
   same way.

   **(b) It dissolves the failure §2b.1 records instead of patching it.** Under a lexical
   rule, two sequential `&var self` method calls are two coexisting exclusive borrows —
   and rescuing that requires importing Rust's pre-NLL temporary-vs-`let`-bound
   distinction as an extra rule. Under last-use liveness the case never arises: the first
   borrow's last use is inside the first call. **A rule needing no exception is better
   evidence of being right than one needing an exception.**

   **(c) It is what Rust actually ships.** Not a research position — the deployed default
   since the 2018 edition, with a decade of evidence that lexical rejected too much
   ordinary code to live with.

   > **The superseded argument, kept because withdrawing it is part of the record.** The
   > earlier resolution chose lexical on *asymmetric reversibility*: lexical → NLL accepts
   > strictly more programs, so the later tightening is backward-compatible, while the
   > reverse would reject already-valid code. That reasoning is sound in general and weak
   > **here**. Reversibility buys protection against breaking code you do not control;
   > Metel has one operator and a 732-fixture corpus. Meanwhile lexical's cost is paid
   > immediately and twice — reject idiomatic code, migrate the corpus around the
   > rejection, then un-migrate on the way to NLL. Rust's own lexical → NLL transition
   > took years and an edition boundary; that is the cost the argument was treating as
   > free.

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

   **✅ Discharged 2026-08-01 by #579, verified directly against the interpreter.** The
   place abstraction lives at `metel-interpreter/src/place.rs` — crate root, not inside
   `move_check` — is 203 lines, and carries no move-specific state: every mention of
   "move" in the file is module documentation explaining *why* it is analysis-neutral
   (its own doc comment: *"Policy lives with each analysis, not here"*), and
   `move_check/mod.rs` is its only importer. `Place`, `Projection::{Field, TupleIndex,
   OpaqueIndex, Deref}`, `is_prefix_of`, and `from_expr`/`from_typed_place` are all
   available to a second analysis unchanged. See `architecture/decisions/
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
   masking (#581, #591, #598, #600, #347, #602). A static checker over a
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
     that borrow is still live because `c` is used again at main.mtl:9:20
     help: the borrow ends after its last use — move that use before line 6, or
           stop using `c` if it is no longer needed
   ```

   ```text
   [T0020] type error in main.mtl:7:5: cannot borrow `x` as exclusive while it is
   borrowed as shared
     `x` is borrowed as shared by `r`, created at main.mtl:6:13
     that borrow is still live because `r` is used again at main.mtl:10:17
   ```

   ```text
   [T0020] type error in main.mtl:7:17: cannot move out of `b` while it is borrowed
     `b` is borrowed by `r`, created at main.mtl:6:13
     moving `b` would leave `r` referring to a value that no longer exists
   ```

Three properties are load-bearing and should be treated as normative, not as sample
   prose: **(a)** the conflicting borrow is always attributed to *the binding that holds
   it* (`c`, `r`), never to an anonymous region; **(b)** the reason a borrow is still live
   is always stated as **the later use that keeps it alive, with a line number** — under
   §2.2's NLL model that use is exactly what extends the borrow, so pointing at it is both
   honest and directly actionable; **(c)** the `help:` line names the concrete edit, which
   under NLL is moving or removing the extending use rather than adding a scope.

   *(Revised 2026-08-01 with §2.2's move from lexical to NLL. The earlier version stated
   liveness as a **scope end**, and argued that was only expressible because the model was
   lexical — under NLL "its last use" was called "a materially harder thing to point at."
   That was backwards: the extending use is a single concrete span the analysis must
   already compute to decide liveness at all, whereas a scope end tells the reader where
   the borrow stops without telling them why it lasted that long. NLL's diagnostic is the
   better one, not the harder one — recorded because the earlier claim was stated
   confidently and was wrong.)*

   **A new error code is required: `T0020`.** T0019 is RFC-0071's move-checking code and
   covers seven distinct situations already; borrow conflicts are a different analysis
   with a different opt-in flag, and folding them into T0019 would make the code
   meaningless as a triage signal. To be registered in `public/reference/error-codes.md`
   at integration, not before — a code that no pass emits should not appear in the
   reference.

---

## 2b. Blocking gaps found after the premature acceptance

*Added 2026-08-01, immediately after this RFC was accepted and reverted the same day.
All six were found by an adversarial pass asking "what does a borrow checker need that
this does not have," and all six are verified against the built interpreter rather than
reasoned about. They are numbered separately from §2 because §2's five questions were
**the questions this RFC had asked itself**, and the lesson of the reversion is that that
was not the same set as the questions it needed to answer.*

**1. §2.2's lexical rule, as written, rejects ordinary code.** It says a borrow is live
"from its creation to the end of the enclosing scope." Applied literally, each method
call taking `&var self` creates a borrow that never ends:

```metel
c.bump();   // &var borrow of c, live to end of scope
c.bump();   // second exclusive borrow of c → rejected
```

That program is accepted today, and the identical shape is a **currently-passing case in
`move_check`'s own test suite**. Rust's pre-NLL rule distinguished *temporary* borrows
(ending at the end of the enclosing statement) from `let`-bound borrows (end of scope);
§2.2 omitted that distinction entirely.

> **✅ Dissolved 2026-08-01, not fixed — §2.2 now specifies NLL.** The proposed fix was
> to import Rust's pre-NLL temporary-vs-`let`-bound rule as an extra clause. Moving to
> last-use liveness removes the need for it: the first `c.bump()`'s borrow has its last
> use inside that call, so it is dead before the second begins, with no special case for
> temporaries anywhere. **That this gap existed at all is the strongest single argument
> for NLL in this RFC** — the lexical model required an exception to describe ordinary
> code correctly, and needing an exception is evidence about the rule.

**2. The second headline rule is named and never specified.** The Summary promises two
rules: shared-XOR-exclusive, *and* "a borrow must not outlive its referent." All five of
§2's questions are about the first. The outlives rule has no granularity decision, no
liveness model, no diagnostic, and no worked example. It is also unenforced:

```metel
fun leak() -> &P {
    let local = P { v = 1 };
    return &local;          // accepted today; prints 1
}
```

**This is the larger half of the RFC's own stated scope, missing.** §1 lists "when a
borrow is valid with respect to the scope of what it borrows" first among in-scope items.

**3. Reference-typed struct fields defeat this RFC's central architectural claim.** The
header argues at length that RFC-0067's anchors are "a dependent, not a dependency,"
because shared-XOR-exclusive never needs a validity scope *named* and local outlives
checking is scope-based. Both halves of that argument are about **local** borrows. Neither
survives a stored reference:

```metel
struct Holder { r: &P }
fun make() -> Holder {
    let local = P { v = 42 };
    return Holder { r = &local };   // accepted today; prints 42
}
```

No scope-based rule can check this: the question is whether `Holder`'s referent outlives
`Holder`, which relates two independent lifetimes and is exactly what an anchor
expresses. **Either reference-typed fields are banned, or RFC-0067 is a dependency for
the outlives rule after all.**

> **Operator decision, 2026-08-01: ban reference-typed struct fields — as an explicitly
> temporary measure.** Full reasoning, scope, and the condition that lifts it are in
> **§2d**, which also records the migration check this note originally said was missing.
> Recorded in `reports/strategy/OBJECTIVES.md` §0.

**4. Closures are absent entirely — zero mentions.** RFC-0071 specifies closure capture
for moves (a free non-`Copy` root is treated as moved at closure creation). Borrow
checking needs the analogue: a closure capturing a place while a borrow of it is live.
Accepted today:

```metel
var c = C { v = 0 };
let r = &var c;
let f = () -> i64 { c.v };   // captures c while r borrows it exclusively
```

**5. Reborrowing is listed in scope and specified nowhere.** §1 names it ("already
surfaced by v0.11.0's `&*p` and by RFC-0067's coercions") and no other line in the RFC
mentions it. Whether a reborrow suspends the original borrow, and for how long, is core
machinery rather than a detail — it is what makes `&var` usable at all in practice.

**6. RFC-0126's `T[]` Copy borrowed view is unaddressed — zero mentions — and it
shipped.** v0.12.0 made `T[]` a `Copy` borrowed view (#593). A borrow that is *freely
copyable* sits awkwardly against a rule whose whole content is how many borrows may
coexist: unlimited copies of a shared view are presumably fine, but the interaction with
an exclusive borrow of the same backing storage is undefined here. This is the one gap
that concerns already-implemented, already-shipped behaviour rather than future work.

---

## 2d. The reference-typed struct field restriction — temporary, and what lifts it

*Added 2026-08-01, expanding §2b.3's one-line operator decision into a real
justification with a tracked exit.*

> **This is a temporary scaffold, not a language design position.** Metel does not
> intend to forbid structs that hold references. The restriction exists for exactly one
> reason — to let borrow checking be built and shipped without first designing and
> implementing lifetime anchors — and **it is lifted the moment RFC-0067 (Lifetime
> Anchors) is implemented.** Nothing else needs to happen for it to go.

### The rule

A `struct` or `enum` field may not have a reference type (`&T`, `&var T`), directly or
nested inside a generic argument. Rejected at typechecking, not at borrow checking, so
the restriction applies whether or not `--borrow-check` is on.

```metel
struct Holder { r: &P }        // rejected while this restriction stands
struct Pair   { xs: List<&P> } // likewise — nesting does not evade it
```

### Why it exists

**Because the alternative is that RFC-0122 cannot be built without RFC-0067 first.** The
chain is short and each link is forced:

1. §2b.3 showed a stored reference can outlive its referent today, silently
   (`fun make() -> Holder { let local = …; return Holder { r = &local }; }` is accepted
   and prints 42).
2. Rejecting that requires relating **two independent lifetimes** — the struct's and its
   referent's. No scope-based rule can do it: there is no enclosing scope that contains
   both, which is precisely why local borrows are checkable without anchors and stored
   ones are not.
3. Relating two independent lifetimes is what an anchor *is*. So admitting stored
   references makes RFC-0067 a hard dependency of the outlives rule.
4. RFC-0067 is `2-accepted`, unimplemented, and carries pre-RFC-0098 syntax. Making it a
   dependency means **no borrow checking of any kind ships until anchors are designed
   through, implemented, and stabilised** — trading the ~90% of value that local borrow
   checking delivers for a much larger, later deliverable.

The restriction buys that ~90% now. It is the same trade RFC-0067's own text already
implies when it says anchors "appear only when the relationship is ambiguous" — the
ambiguous cases are the ones being deferred, not the common ones.

### What it costs

**Zero migration cost, verified rather than assumed** *(2026-08-01)*: an exhaustive scan
of every `struct`/`enum` declaration body across `tests/integration/sources/**` and
`stdlib/**` found **no** reference-typed field, in any shape — no direct `&T`, no
`&var T`, none nested in a generic argument. Nothing in the corpus or the standard
library has to change to adopt this.

**Real expressive cost, deferred not denied.** Borrowed wrappers, view structs,
reference-holding iterators, and anything shaped like Rust's `struct Iter<'a>` are
unwritable while this stands. Two RFCs already want them and are already deferred for
adjacent reasons — **RFC-0109** (Self-View Narrowing, `0-draft`) and **RFC-0119**'s
dropped by-reference conversion mode. Neither is blocked *further* by this restriction,
but both are downstream of the same missing capability, and whoever lifts it should check
both.

### What lifts it

> **The restriction is removed when RFC-0067 (Lifetime Anchors) is implemented.** That is
> the whole condition. It is not "when someone asks for it," not "when the borrow checker
> is mature," and not subject to re-litigation on other grounds: anchors supply exactly
> the missing capability (naming a validity scope so two independent lifetimes can be
> related), and once they exist the justification above evaporates in full.

**Tracked as metel-core#274**, which owns both halves — imposing the restriction and
removing it — so the exit cannot be lost if the two land in different releases.
RFC-0067's own text carries the reciprocal pointer, so that implementing anchors surfaces
this obligation rather than depending on someone remembering it.

**A caution for whoever lifts it.** Deleting the check is the easy half. The real work is
that the outlives rule (§2b.2) was *specified* scope-based on the assumption stored
references do not exist; admitting them means revisiting that specification, not merely
relaxing an error. Treat §2b.2 and this section as a pair.

---

## 2c. Polonius, and why it is not the starting point

*Added 2026-08-01, when the operator asked whether a Polonius-style checker could be
built from the start rather than evolving into one. Recorded rather than left implicit so
the choice is documented instead of silently foreclosed.*

**What Polonius is.** A reformulation of borrow checking as Datalog over *loans* rather
than as liveness over *lifetimes*. Where NLL asks "at this point, is this reference
live," Polonius asks "at this point, which loans are in scope," deriving conflicts from
relations like `loan_issued_at(Loan, Point)`, `loan_killed_at`, `origin_live_on_entry`,
and `subset`. It is Rust's intended successor to NLL.

**What it would buy.** Chiefly **NLL problem case #3**: a reference conditionally returned
out of a `match`, where the borrow appears live on a path that never actually uses it.
NLL rejects; Polonius accepts. Secondarily, a declarative rule set is easier to argue
about and to test than hand-written dataflow.

**Why it is not the starting point — the constraint is structural, not a preference.**
Every Polonius relation is indexed by a **program point**, so the formulation presupposes
a CFG. Metel has none: the pipeline runs parser → resolver → typechecker → `move_check` →
elaborator → evaluator, with no MIR and no IR of any kind. **"Implement Polonius" is
therefore not a borrow-checking decision — it is "build a MIR-like IR first,"** which is
a compiler-architecture commitment. `OBJECTIVES.md` §1's corollary classifies exactly
this ("clean IR shape") as *forward-structure budget* — work that pays off only if the
current interpreter's internals persist past the compiler-direction decision, which that
document explicitly defers.

Two further facts weigh the same way:

- **NLL is reachable without any of that**, because Metel's control flow is fully
  structured (no `goto`, no arbitrary labeled jumps), making the AST a reducible CFG over
  which AST-directed dataflow is equally powerful — see §2.2(a).
- **Polonius's advantage concentrates in a surface this RFC is narrowing.** Problem case
  #280 is about references flowing outward through conditional returns; §2b.3's operator
  decision bans reference-typed struct fields, and the outlives rule (§2b.2) is
  deliberately scope-based. The cases where Polonius beats NLL are exactly the ones being
  deferred.

**The condition that would justify revisiting**, stated so this is a decision with a
falsifier rather than a permanent no:

> Revisit Polonius when **either** (a) Metel grows a CFG or MIR for an unrelated reason —
> #255's compiler-facing HIR is the live candidate — so the prerequisite is already paid
> for, **or** (b) NLL problem case #3 shows up as a *recurring* rejection of code the
> language wants to accept, rather than as a known theoretical limit. Absent both,
> adopting Polonius means paying for an IR to buy a case Metel cannot currently write.

**One caution on timing, recorded honestly.** Rust has worked on Polonius since 2018 and
still has not made it the default, largely on performance. That is a strong signal about
cost for a project whose interpreter `OBJECTIVES.md` describes as a temporary feedback
instrument — but it is a signal about *Rust's* constraints (an enormous ecosystem, hard
compile-time budgets), not proof it would be expensive here, and it should not be
mistaken for a technical objection to the formulation itself.

---

## 3. Migration cost, and why it is a sequencing constraint

*Added 2026-08-01. Nothing in the earlier draft costed this, and it is the largest
practical risk to implementing the rules above.*

**Shared-XOR-exclusive will invalidate existing Metel programs, including this
project's own fixture corpus.** The evidence is direct and recent: RFC-0071's #602 added
*one* narrow rule — a by-value `self` method may not be called through a reference — and
that alone required migrating five corpus fixtures that had been relying on the gap. A
rule as broad as "at most one `&var` per place, and never alongside a `&`" touches far
more surface, and the three programs in the Summary above are all currently-passing
shapes that would stop compiling.

**The constraint this creates: do not enable borrow checking by default in the same
release as #267.** #267 (enable move checking by default) is already queued for
v0.13.0, and it carries its own corpus migration. Landing both defaults together would
make a failing fixture ambiguous between two new analyses, and would put two unrelated
migrations in one release's blast radius.

**Recommended sequencing, following the precedent RFC-0071 set and which worked:**

1. Borrow checking ships **opt-in behind its own flag** (`--borrow-check`), exactly as
   move checking shipped behind `--move-check` — no corpus migration required to land
   it, and the analysis becomes testable against real programs immediately.
2. The corpus migrates incrementally, under that flag, as its own tracked work.
3. Only then does enabling-by-default become a separate, independently-schedulable
   decision — and in a different release from #267's.

This is not a concession to expedience. Opt-in is what allowed #579's move checker to be
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
  1–2 shipped in v0.12.0 as #578/#579, and **§9b's place-abstraction requirement — the
  only thing this RFC asked of it — is discharged**, see §2 question 3. Parts 3–4 (#261
  drop order, #262 partial moves) are queued for v0.13.0.)*
- RFC-0086 (Outlives-of-Bindings Sugar), `6-refused` — the only prior "borrow"-titled RFC;
  refused, and its refusal is not evidence against this one
- `reports/strategy/OBJECTIVES.md` — Trigger 19, and §1's diagnostics claim
- `reports/substructural-types/allocators-as-emergent-synthesis.md` — the decomposition
  that makes this load-bearing for Priority 4
- `public/rfcs/0-draft/rfc-0109-self-view-narrowing-and-reference-destructuring-patterns.md`
  — deferred; its borrowed-view questions depend on the outcome here

---

## Decision

**Outcome:** **Reverted to `1-under-review`, 2026-08-01, the same day it was accepted.**
The acceptance below was premature: an adversarial pass immediately afterward found six
gaps (§2b), three of them blocking — an unspecified outlives rule, reference-typed struct
fields defeating the anchors-are-a-dependent claim, and a lexical rule that as written
rejects sequential `&var` method calls. `PROCESS.md`'s bar for `2-accepted` is "no open
questions block it"; that was true of the five questions §2 asked and not of the RFC.

**This is the corpus's third `2-accepted` → `1-under-review` reversion** (after RFC-0099
and RFC-0100), which is precisely what `OBJECTIVES.md` Trigger 14 named as its falsifier:
*"If a third RFC follows the same path, that's evidence `2-accepted`'s own bar is being
called too early in practice."* It fired. Recorded there rather than only here.

**The distinguishing feature of this instance, worth keeping:** RFC-0099 and RFC-0100
were reverted during *integration*, by problems the accepting review had not surfaced.
This one was reverted minutes after acceptance, by an adversarial pass on the same
document in the same session — which is a cheaper failure, but a more embarrassing one,
because nothing about the gaps required new information. §2b.2's dangling-reference repro
is four lines.

**Superseded acceptance rationale, kept for the record:** *Accepted 2026-08-01.* All five design questions in §2 are resolved and
none blocks implementation. The headline rule (shared XOR exclusive), its granularity
(per-field for statically-named fields, whole-value through a dynamic index), its
liveness model (lexical), its relationship to move checking (two analyses, one shared
place abstraction), its diagnostic format (`T0020`, naming bindings and scope ends), and
its rollout constraint (§3: opt-in behind `--borrow-check`, not default-on alongside
#267) are all settled.

**What acceptance does *not* claim.** No borrow checking ships in v0.12.0 — this RFC was
always scoped design-only for that release, and its acceptance changes nothing about
what the interpreter enforces today. The three programs in the Summary still compile.
Integration (`3-integrated`) additionally requires merging these rules into
`public/reference/spec/` with worked examples checked against everything already
integrated, and — per `PROCESS.md` — a tracked implementation issue, neither of which
exists yet.

**Target:** implementation not yet scheduled. RFC-0071's remaining parts (#261 drop
order, #262 partial moves) are v0.13.0 and share this RFC's place abstraction; whether
borrow checking lands alongside them or after is a scheduling decision for the release
that picks it up, constrained only by §3's requirement that it not go default-on in
the same release as #267.
