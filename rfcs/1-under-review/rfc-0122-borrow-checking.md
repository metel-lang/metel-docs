---
id: rfc-0122
title: "Borrow Checking"
date: '2026-07-24'
status: under-review
target: v0.16.0
updated: '2026-09-01'
tracking: 'https://github.com/metel-lang/metel-core/issues/847'
---

> **Tracking corrected 2026-08-27.** metel-core#847 now owns this RFC's design and
> opt-in implementation. metel-core#274 owns only the temporary stored-reference
> restriction and its removal after RFC-0067; it is not the borrow-checker umbrella.

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

> **Amendment 2026-09-01 — interim-rule catalogue (§2e) + closure clause (§2f).** The
> closure cluster (RFC-0050, RFC-0153) and RFC-0071 §9 each shipped or specified a narrow,
> sound borrow-shaped rule as a stopgap "until RFC-0122." **§2e catalogues all of them**
> — what each permits, enforcement status, fixtures constrained, teardown when
> `--borrow-check` lands (including two whose owner is RFC-0096 / RFC-0067, not this RFC).
> **§2f (new, 2026-09-01, pass 4)** carries this RFC's matching clause for the closure
> cases the cluster delegates to — `[&x]`/`[&var x]` capture-as-borrow and the `&var
> self`-shaped `mutating` call — closing §2b.4 for those cases. No change to the rules in
> §2/§2b; §2f is a consolidation so the closure cluster does not delegate to unwritten
> spec.

> ## Targeted at v0.16.0
>
> *Corrected 2026-08-27 after the open/variadic and cleanup milestones shifted the
> sequence.* v0.16.0 contains this RFC alone as a language feature: borrow checking
> ships opt-in before **v0.17.0 (ownership completion and RFC-0067 Lifetime Anchors)**.
> The ordering is forced: anchors cannot settle what they bound until this RFC defines
> validity and outlives, while local borrowing does not require stored-reference anchors.
>
> **What must close first**, all in §2b: the outlives rule specified (§2b.2), the
> stored-reference restriction implemented (§2b.3 / metel-core#274), closures (§2b.4 —
> **now covered for the v0.13.0 cluster's cases by §2f**), reborrowing (§2b.5), and the
> `T[]` `Copy`-view interaction (§2b.6). §2b.1 is already dissolved by §2.2's move to NLL.
> **On implementation, §2e's interim rules (RFC-0071 §9 Q5, RFC-0050 RQ1/RQ3, RFC-0153
> §3's static half) are torn down and their deferred fixtures added; RFC-0153's runtime
> in-call flag is kept.**
>
> **Tracking and implementation ownership:** metel-core#847 carries design settlement
> and the opt-in implementation checklist. Reaching acceptance/integration remains a
> prerequisite to claiming the implementation is complete.
>
> **§3's rollout constraint still binds and interacts with the schedule:** borrow checking
> ships opt-in behind `--borrow-check` and must **not** go default-on in the same release
> as #267 (enable move checking by default, currently v0.17.0). With this RFC at v0.16.0
> and #267 at v0.17.0 those are in different releases, which satisfies the
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
let a := &var x;
let b := a;         // rejected: !Copy, so `a` was moved
let c := &var x;
let d := &var x;    // nothing in RFC-0071 forbids this
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

fun both(a: &var P, b: &var P) { a.v := 10; b.v := 20; }

// (1) two exclusive borrows of one place — accepted
var x := P { v = 1 };
let c := &var x;
let d := &var x;

// (2) the same, aliased across a call boundary — accepted, prints 20
both(&var x, &var x);

// (3) the owner writes through an outstanding exclusive borrow — accepted, prints 99
let r := &var x;
x.v := 99;
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
    let local := P { v = 1 };
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
    let local := P { v = 42 };
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
var c := C { v = 0 };
let r := &var c;
let f := || -> i64 { c.v };   // captures c while r borrows it exclusively
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

## 2e. Interim rules elsewhere in the corpus, pending this RFC

*Added 2026-09-01. Several RFCs shipped or specified a narrow borrow-shaped rule as a
deliberate stopgap "until RFC-0122." Each is catalogued here so the implementation of
this RFC has **one checklist** of what to delete, what to widen, and which fixtures to
revisit — instead of each stopgap being discoverable only from the RFC that introduced
it. This section is normative about the teardown: landing `--borrow-check` **must** remove
each stopgap's own front-end check and let the general rule take over.*

**Common shape.** Every entry is **weaker than** the full shared-XOR-exclusive rule — it
rejects a *subset* of what the full checker rejects. Two consequences, and the second is
the one earlier drafts of this section stated backwards:

- **(a) No false positives.** The stopgap never rejects a program the full checker
  accepts, so nothing written against a stopgap is stranded when `--borrow-check` lands.
- **(b) It *does* accept programs the full checker rejects.** Those become `T0020` on
  landing. That is the "accepted but ill-formed" gap — expected, not a contradiction —
  and the fixture-corpus constraint on each entry is what keeps it from mattering (no
  expected-behaviour fixture may exercise it).

Enforcement in v0.13.0 varies: most entries are unenforced at runtime (the evaluator
still deep-clones, §2 question 4); one — **same-closure-value** reentrancy, item 3 — is
enforced by a runtime flag and is *not* in the gap. Landing `--borrow-check` **must**
remove each stopgap's own front-end check and let the general rule take over (the runtime
flag stays as defence-in-depth).

### 1. `&var T` reborrow-in-argument-position — RFC-0071 §9 question 5 *(shipped v0.12.0)*

> Passing a `&var T` value to a `&var T` parameter **reborrows** it (the binding is usable
> after the call); every other use — `let q := p;`, returning it, storing it in a struct,
> capturing it in a closure — **moves** it.

Introduced because `&var T: !Copy` (#578) plus move checking (#579) otherwise made every
exclusive reference single-use. It tracks no reborrow *duration* — that is §2b.5.
**On landing:** §2b.5's reborrow rule replaces it; the "every other use moves" half
remains true as a consequence of `!Copy`, not as a special case. RFC-0071 is
`3-integrated`; the rule already states it is "a strict subset of what RFC-0122 will
specify, so it is subsumed rather than contradicted."

### 2. `[&var x]` / `[&x]` capture borrow-freeze — RFC-0050 Resolved Questions 1 & 3 *(v0.13.0)*

RFC-0050's rule: a `[&var x]` / `[&x]` capture takes the borrow at closure creation and
**holds it for the closure value's whole lifetime**. While a `[&var x]` closure is live,
any other read or write of `x`, another `[&var x]` / `[&x]` capture of it, or a bare `&x`,
is a conflict; while a `[&x]` closure is live, `x` may be read but not written or
`&var`-borrowed. This is shared-XOR-exclusive applied to the capture aggregate — nothing
closure-specific (**§2f** carries this RFC's matching clause; RFC-0050 RQ1 states the same
rule in full).

**Enforcement in v0.13.0: none.** RFC-0050's heap-backed capture storage means a
`[&var x]` closure outliving `x` is not memory-unsafe, so the interpreter runs these
programs; a violation is **accepted but ill-formed**.

**Fixture-corpus constraint** (RFC-0050 "Migration", normative): the v0.13.0 corpus must
**not** add, as expected-behaviour fixtures, programs that rely on the unenforced freeze —
two live `[&var x]` closures over one binding, a write to `x` while a `[&var x]` closure
is live, a bare `&x` alongside one. Those are valid only as `expected-error` fixtures once
this RFC lands. **On landing:** the checker enforces the rule; such programs become
`T0020`; the corpus additions deferred here are made then.

### 3. `mutating`-closure-callee eligibility — RFC-0153 §3 *(v0.13.0)*

A `mutating` closure's synthesized `call` takes `&var self`; the full callee-eligibility
rule is stated in RFC-0153 §3 and matched by §2f below. Two v0.13.0 stopgaps:

- **Interim static rule:** the front-end enforces the statically-checkable half — reject a
  **shared-`&` callee** (`&Self` receiver, `(&b).handler()`, an `&`-captured closure);
  accept an owned binding, an owned temporary (`make_counter()()`), an exclusive
  projection whose visible steps are owning/`&var`, or a `&var` parameter. What it cannot
  check — that no *other* borrow of the place is live across the call, that a projection's
  dynamic base is unaliased — is deferred to this RFC; a program violating only those
  parts is accepted-but-ill-formed (fixture-corpus caution as in item 2). Per the
  "Common shape" above: the interim rule never rejects what §2f accepts (no false
  positives), but it *does* accept some programs §2f rejects — those become `T0020` on
  landing. Deleted on landing.
- **Runtime in-call flag (not a stopgap — permanent).** Every `mutating` closure value
  carries a one-bit "in-call" flag, set on entry to a `mutating` call, checked on entry,
  cleared on exit/unwind; a reentrant call panics. It enforces **same-closure-value**
  reentrancy only — that case is **not** in the "accepted-but-ill-formed" gap. It does
  **not** catch *aliased-capture* reentrancy (two distinct `mutating` closures, or a
  `Copy` closure and its copy, each holding `[&var x]` to one `x`, one calling the other
  mid-call) — that is **in the gap**, the same unenforced `[&var x]` freeze as item 2,
  and this RFC closes it statically (§2f). The flag is **kept** after this RFC lands as
  defence-in-depth.

### 4. `mutating` closure is `!Sync` — RFC-0153 §3 *(rule owned by RFC-0153 now; migrates to RFC-0096)*

A `mutating` closure value is not `Sync` (two fibers each needing the exclusive per-call
borrow). RFC-0153 defers all *other* closure `Send`/`Sync` to the aggregate rule over
captures + RFC-0080's reference rules; this one fact is closure-specific. **RFC-0153 §3 is
its normative source today** — RFC-0096 does not yet model closure mutation. When RFC-0096
grows a closure-mutation hook the rule migrates there; listed here so the migration is
tracked, not to assert RFC-0096 already owns it. Not a `--borrow-check` teardown.

### 5. Returned closure capturing a method receiver — RFC-0050 *(teardown owner: RFC-0067)*

RFC-0050's `self`-capture rule rejects a closure that captures a method's `&self` / `&var
self` receiver and then escapes the method (is returned), because the captured borrow
cannot outlive the call without a lifetime anchor. That rejection is lifted when **RFC-0067
(Lifetime Anchors)** lets the method tie the closure's region to `self` — same teardown
owner as §2d, not this RFC.

### Not on this list

**§2d's reference-typed-struct-field ban** is a scaffold *this RFC imposes*, waiting on
**RFC-0067** (Lifetime Anchors), not on itself. Shipping `--borrow-check` does not lift
it; implementing anchors does. See §2d.

---

## 2f. Closure borrow rules — resolves §2b.4

*Added 2026-09-01. §2b.4 flagged "closures are absent entirely." The v0.13.0 closure
cluster (RFC-0050, RFC-0153) states the rules it needs in its own text and cites this RFC
for enforcement; this section carries the matching clauses so the two do not drift, and
closes §2b.4 for the cases the cluster exercises. General closure borrow checking beyond
these — a borrow that flows *through* a returned closure (needs anchors, §2d bars the
struct-field route anyway), and **an inner closure that borrows (`[&x]` / `[&var x]`) a
by-value capture of an enclosing closure** — remains future work. That last case is a
**local reborrow into the enclosing closure's environment aggregate**: sound iff the inner
closure is strictly local to one activation and dies before the outer body touches the
capture again (an NLL judgement), unsound if it escapes. RFC-0050 **rejects it outright in
the v0.13.0 interim** (its "Nested closures" rules); this RFC's implementation replaces
that rejection with the NLL local-reborrow check.*

1. **A by-value capture is a move at closure creation** (RFC-0157 D5 / RFC-0050). The
   move checker (RFC-0071) already treats a captured non-`Copy` free root as moved at the
   closure literal; borrow checking adds nothing for the by-value case — the value now
   lives in the closure's environment aggregate and is checked there like any owned place.

2. **A `[&x]` / `[&var x]` capture is a borrow of `x` held for the closure value's
   lifetime.** From the closure literal to the closure value's last use / drop, `x` is
   borrowed exactly as `let r := &x;` / `let r := &var x;` would borrow it, under
   shared-XOR-exclusive (§2 question 1 granularity): a live `[&var x]` closure conflicts
   with any other read, write, `&`, or `&var` of `x`; a live `[&x]` closure permits other
   `&x` and reads but not writes or `&var x`. Two `[&var x]` closures over one `x` is the
   two-exclusive-borrows conflict of the Summary. Diagnostic: `T0020`, naming the closure
   binding as the borrow holder and the closure's last use as what keeps it live (§2.5).

3. **A `mutating` call is a `&var self`-shaped exclusive borrow of the callee place** for
   the call's dynamic extent (RFC-0153 §3). Callee eligibility is the ordinary `&var self`
   receiver rule: an owned binding, an owned temporary, an exclusive (`&var` / owning)
   projection off one, or a `&var` parameter — **not** a shared-`&` callee. Across the
   call no other read, write, `&`, or `&var` of the place may be live, and two `mutating`
   calls on one place cannot overlap. A reentrant `mutating` call re-enters the borrow and
   is rejected (`T0020` "already borrowed exclusively") — this covers **both** the
   same-closure-value case and the aliased-`[&var x]`-capture case that v0.13.0's runtime
   in-call flag (§2e item 3) can only catch for the former.

4. **A `once` call consumes the callee place** at the call expression (RFC-0134 §2); it is
   a move, checked by the move checker, and composes with (3) for `once mut` — the move
   happens first, the exclusive borrow is then moot.

These are first-order and place-based — no anchor needed — so they fit this RFC's
"buildable without RFC-0067" claim. They do **not** cover a borrow escaping *through* a
returned closure (that needs anchors — RFC-0050's `self`-capture rule rejects it in the
interim, §2e item 5).

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
- RFC-0050 (Closure Capture Lists), `2-accepted` (v0.13.0) — its Resolved Questions
  1 & 3 state the `[&var x]` / `[&x]` capture borrow-freeze rule and defer enforcement
  here; catalogued in §2e
- RFC-0153 (Closure Mutation Axis), `2-accepted` (v0.13.0) — its §3 defers
  `mutating`-callee eligibility to this RFC's `&var self` receiver rule and carries an
  interim check for the v0.13.0 window; catalogued in §2e
- `reports/strategy/OBJECTIVES.md` — Trigger 19, and §1's diagnostics claim
- `reports/substructural-types/allocators-as-emergent-synthesis.md` — the decomposition
  that makes this load-bearing for Priority 4
- `rfcs/1-under-review/rfc-0109-self-view-narrowing-and-reference-destructuring-patterns.md` (RFC-0109, `1-under-review`)
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
