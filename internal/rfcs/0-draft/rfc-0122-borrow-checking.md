---
id: rfc-0122
title: "Borrow Checking"
date: '2026-07-24'
status: draft
target:
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
> is `2-accepted`, unimplemented, and itself carrying stale syntax (nine `&var` occurrences
> predating RFC-0098, whose last update was 2026-07-10, four days before RFC-0098 shipped).
> RFC-0067 should be treated as a dependent extension, and its acceptance re-examined
> against these rules rather than assumed to constrain them.

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

## 2. Open design questions this RFC exists to settle

Deliberately listed rather than answered — this is a draft opened to hold the design, not a
finished proposal.

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
2. **Lexical or non-lexical?** RFC-0067's anchors are bindings with scopes, which reads
   lexical. Rust moved from lexical to NLL because the lexical version rejected too much
   ordinary code. Adopting the lexical version first and tightening later is cheap; the
   reverse is not.
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
4. **Does the interpreter's deep-cloning evaluator make any of this observable?** A checker
   that rejects programs is meaningful even if the runtime would not have misbehaved — but
   the *value* of the checker before the evaluator stops cloning is worth being honest
   about, per `OBJECTIVES.md`'s feedback-trustworthiness budget.
5. **What does a diagnostic look like?** §1's claim is "named after real bindings rather
   than abstract `'a`." That is a promise about wording, and it should be specified with
   examples, not left to implementation.

---

## References

- RFC-0067a (Reference Types), `4-implemented` — `&T` / `&var T`, **this RFC's only
  reference-side dependency**
- RFC-0067 (Lifetime Anchors), `2-accepted` — **a dependent, not a dependency.** Its `&r T`
  anchors name a validity scope for the cross-function cases elision cannot infer; they
  presuppose the rules here rather than supplying them. Supersedes RFC-0052 (Lifetime
  System). Carries pre-RFC-0098 `&var` spelling
- RFC-0071 (Ownership and Move Semantics), `2-accepted` — move and partial-move tracking,
  which this must agree with about places; scheduled for implementation in v0.12.0
- RFC-0086 (Outlives-of-Bindings Sugar), `6-refused` — the only prior "borrow"-titled RFC;
  refused, and its refusal is not evidence against this one
- `reports/strategy/OBJECTIVES.md` — Trigger 19, and §1's diagnostics claim
- `reports/substructural-types/allocators-as-emergent-synthesis.md` — the decomposition
  that makes this load-bearing for Priority 4
- `internal/rfcs/0-draft/rfc-0109-self-view-narrowing-and-reference-destructuring-patterns.md`
  — deferred; its borrowed-view questions depend on the outcome here

---

## Decision

**Outcome:** *(pending)*
**Target:** *(set when accepted)*
