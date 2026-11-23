---
title: "Multi-Shot Continuations for Metel: A Design Exploration"
date: '2026-11-23'
status: report
relates: rfc-0014, rfc-0050, rfc-0089, rfc-0140, rfc-0194, rfc-0232, rfc-0245
---

# Multi-Shot Continuations for Metel: A Design Exploration

An exploration of whether and how a handler could resume a continuation more than once in Metel, written from a planning
discussion on 2026-11-23. It records what duplicating a continuation means under Metel's ownership model, four design points,
a proposal that did not survive (explicit capture lists at suspension points), the rules that did, and a stress test. It
does not decide. Whether Metel needs multi-shot at all is open (section 12).

## 1. Status and scope

- **Not scheduled.** Handlers and resumption are not in v0.17.0. The effect rows and markers slice (RFC-0245) is the first
  step; algebraic effect handlers follow in a later release.
- **Illustrative syntax.** The control class `ctl multi`, the handler clauses and any marker on a call are invented for this
  note. RFC-0140's `^` notation is replaced by `effects` in RFC-0245, and both RFCs are not accepted.
- **Nothing was implemented or prototyped.** Claims about the evaluator and typechecker were not checked against the code, and
  are marked where they matter.
- **Sources.** Prior art in section 10 is marked as sourced from a search or as general knowledge to check.

## 2. What exists today

- **RFC-0140 section 2** makes a continuation an affine `@Heap` value. One-shot resumption "falls out of the general ownership
  model", multi-shot is "not expressible", and a continuation over only `Copy` or `Clone` data "could support
  `k.clone().resume(v)` explicitly". Syntax for that is "deliberately out of scope". The `@Heap` and allocator-tag basis of that
  RFC predates the memory-model decision (metel-core#2116), which amends or supersedes RFC-0063, so it cannot be taken as given.
- **RFC-0245 (draft)** classifies an operation as `fun` (resumes exactly once, in tail position), `ctl` (zero or one time) or
  `final ctl` (never). A handler cannot strengthen the declared class. A fourth class would be the place for multi-shot.
- **Copy on an erased callable** was answered on 2026-11-22 (metel-core#2135): a `dyn` callable that lists `Copy` is copyable
  through a vtable copy entry, and copying it allocates. The same mechanism would give an erased continuation `Clone`.
- **RFC-0050** gives closures explicit capture lists: `x` copies or moves, `&x` and `&var x` borrow, `x.clone()` makes an
  independent copy at capture time while the original stays in scope. Once present the list is exhaustive.
- **RFC-0089** treats an early `return` or `?` as an implicit drop that needs `Discard`, so a `Linear` value live at such a site
  is rejected. The Linear types stage extends the rule to handler abandonment and panic recovery. Generic bodies are checked
  once, at the definition, against their declared bounds.

## 3. Why one might want it, and what else would do

Multi-shot continuations are the mechanism behind nondeterminism and backtracking: choose, search, N-queens and Pythagorean
triple benchmarks (Koka uses both in its evidence-passing benchmarks, per the sources), parser backtracking, and, from general
knowledge, probabilistic programming and re-entrant generators. Three alternatives cover part of the ground without it:

- **Replay.** A handler re-runs a callable that can be called many times (`CallMany`) with a log of recorded choices. It needs no
  language support and only works for deterministic computations, at exponential cost.
- **Explicit continuation-passing.** The continuation is a user-written closure, `once` or `many`, with an ordinary capture
  list. It works with today's closures, and loses direct style, which is most of the appeal of handlers.
- **One-shot plus restart.** Resume once, and restart the computation for the next alternative.

How many of Metel's intended uses these cover is not known.

## 4. What resuming twice duplicates

A continuation captures the frames between the `handle` and the point that performs the operation. Resuming it twice
duplicates every value live in those frames.

| Captured value | Resumed twice |
|---|---|
| `Copy` | fine |
| `Clone` | cloned per resume |
| Affine, not `Clone` | not allowed |
| Resource with `Drop` | released twice, unless `Clone` gives each copy its own |
| `Linear` | forbidden: it would be duplicated |
| Shared or exclusive borrow | aliasing, and a pointer into a frame that may be dropped |
| Handler state | moved into the resume gives backtracking; shared gives global state |

The `Linear` row is a documented hazard. Tang, Hillerstrom, Lindley and Morris ("Soundly Handling Linearity", POPL 2024) show that
multi-shot handlers can duplicate a linear session channel, and that Links had a soundness bug of this kind. Their fix, control-flow
linearity, makes a continuation obey the linearity of what it captures.

## 5. Four design points

- **A. Implicit capture, clone derived from the frames.** A continuation's type derives `Clone` from its captured values, as a
  closure's environment type does (RFC-0232 rule 4). An erased continuation is `dyn Continuation + Clone` through a vtable copy
  entry. It needs a whole-stack property to propagate through effect rows: values live at an effect site must be `Clone`.
- **B. A control class `ctl multi`.** The operation declares it, and only those operations pay for copying. GHC and Scala Native
  copy defensively even for one-shot use, and OCaml avoids the cost by staying one-shot, so a class keeps one-shot operations
  cheap. This is A with the obligation attached to a declaration.
- **C. Replay in a library.** Section 3.
- **D. Unrestricted multi-shot, as in Scheme.** It conflicts with ownership and with linear types. Dropped.

The rest of this note explores B.

## 6. Explicit capture lists

The proposal was to treat a call whose callee row contains a `ctl multi` operation as a **suspension point**, and to require a
capture list there in the style of RFC-0050, with the same four entry forms, exhaustive once present.

```metel
// illustrative: a capture list on a call is not RFC-0050 syntax
fun pick_pair(xs: List<i64>) -> (i64, i64) effects .{ .amb: Amb } {
    let base := xs.len();
    let label := String::from("pair");
    let a := [base, label] choose(xs);    // label is live after the call, so it is listed, and must be Clone
    let b := [base] choose(xs);
    (a, b)
}
```

**The analogy breaks.** A closure chooses how to capture: move, borrow or clone. A continuation is the frame itself, so there is
no original left in scope. Values are moved in, borrows are not allowed (section 7), and cloning happens per resume where the
handler writes `k.clone()`. The `x.clone()` form of RFC-0050 clones at capture time and leaves the original running, which has no
meaning here. An early draft of this exploration used it and was wrong. In this design the list carries no decision: liveness
determines it, so the compiler can compute it.

**Where a list would carry meaning.** With reference origins (not yet designed), an `&outer` entry could share data owned outside
the `handle` among all clones, a real choice between sharing and cloning. Until then the list is an assertion.

**Conclusion.** Mark the suspension point (as `.await` does, to show where) and check the rules in section 7 at every suspension
frame. Reserve the list for the sharing case.

## 7. Rules at a suspension frame

A suspension frame is a call, inside a function or closure body, whose callee's row contains a `ctl multi` operation.

1. **Live values are owned and `Clone` or `Copy`.** A tail call has nothing live and needs nothing.
2. **No `Linear` value, and no `Drop` resource unless `Clone`.** It must be consumed or closed before the call.
3. **A pending observable drop counts as live.** An in-scope `File` never used again still drops at scope end, so it must be
   closed first. A value with no `Drop` impl and no later use may be dropped early, since that is unobservable.
4. **A borrow is allowed only if its referent is a local of the suspending frame, passed directly.** Both ends are then inside the
   captured region, so a clone can relocate the pointer. A reference parameter is rejected, because whether its referent is inside
   or outside the region depends on where the `handle` sits, which a frame cannot know. That needs reference origins.
5. **Row parameters default to "no multi-shot operation".** A combinator that must accept one opts in with `E: multi`, and then
   writes the `Clone` bounds on its own live values, because generic bodies are checked at the definition.
6. **Operations are always declared, even by an unrestricted function.** RFC-0245's rule 4 makes a function with no row
   unrestricted; if that top row included operations, every call to such a function would be a suspension point and every existing
   program would be affected.

## 8. Stress test

Two examples, then the results.

```metel
effect Amb { ctl multi fun choose(n: i64) -> i64; fun fail() -> !; }

fun triple(limit: i64) -> (i64, i64, i64) effects .{ .amb: Amb } {
    let a := choose(limit);           // live values are Copy: no list, no annotation
    let b := choose(limit);
    let c := choose(limit);
    if a*a + b*b == c*c { (a, b, c) } else { fail() }
}
// handler, illustrative: for i in 0..n { out.append(resume(k.clone(), i)) }
```

A graph walk with `g: &Graph` as a parameter fails rule 4: the reference's origin is unknown, and a clone's callee pointer would
refer to the original frame. The workaround is an owned shared handle, and std has none today (no `Arc` or `Rc`; RFC-0074 is only
a design).

| Case | Result |
|---|---|
| Backtracking parser, non-tail recursion | Passes if the syntax tree is `Clone`. Breaks on the input: a `&Tokens` parameter fails rule 4, and an owned vector is cloned per frame per resume, quadratic with depth. Needs a sharing type or origins. |
| Effect-polymorphic `map` with `E: multi` | Passes, with explicit `T: Clone` and `U: Clone` bounds. The default leaves existing combinators untouched. |
| Calls to a `many` closure or a `&self` or `&var self` method | Breaks under a blanket "no references" rule, since the callee frame holds a borrow of the receiver. Passes with rule 4 when the receiver is a local of the suspending frame. A `&var self` parameter recursing through itself still fails; state passing by value works. |
| Loop with a suspension inside | Passes. Loop locals are ordinary live values. Not checked: whether `for x in xs` borrows or consumes `xs`, and std has no lazy iterator layer. |
| A `File` live across the call | Rejected as designed (rule 3). |
| Nested handlers | Passes. The inner handler frame is part of the captured region, so its state must be `Clone`; a `&var` handler state is rejected. |

## 9. Implementation coupling

- **The tree-walking evaluator runs on the host stack,** which cannot be cloned. Multi-shot needs reified frames (a machine in the
  style of CEK or CPS). That ties it to the reference evaluator of the Core design (RFC-0241), where exceptional exits are reserved
  and not modelled. Not verified against the evaluator code.
- **Frame-internal borrows need relocatable references.** Cloning a frame chain must retarget a pointer from one captured frame to
  another, so references into frames are addressed by frame and slot, not by raw address.
- **Cost.** Each resume clones every captured frame, so deep recursion over owned lists is quadratic in depth. Persistent or
  shared structures are the real answer.
- **A one-shot continuation needs none of this,** which is why the class keeps one-shot operations on the cheap path.

## 10. Prior art

Sourced from searches on 2026-11-23:

- **OCaml 5** forbids multi-shot, enforced at run time. Secondary sources give performance (a one-shot continuation resumes
  without copying) and soundness with mutable state (compiler and runtime assumptions fail). The Affect paper (POPL 2025) proposes
  an affine effect system that distinguishes one-shot from multi-shot, and the `multicont` library provides multi-shot on top of
  linear continuations, with a warning about the compiler assumptions.
- **Koka** supports multi-shot, and its benchmarks (nqueens, triple) use it.
- **Stack-based implementations** copy the stack per resume, and a mutable reference captured in a stack frame is shared by both
  resumptions. GHC and Scala Native copy defensively even for one-shot use. A 2025 Tubingen paper avoids copying while keeping
  multi-shot.
- **Links** had a soundness bug combining session channels, exceptions and multi-shot handlers (see section 4).

From general knowledge, to check before relying on it: Koka compiles to C with evidence passing, and a resumed continuation's captured
values need reference-count handling when copied.

## 11. Dependencies and costs

- **A shared-ownership type or reference origins**, for any multi-shot search over non-trivial data. Without one, examples copy large
  data per resume or are limited to small `Copy` state.
- **A new control class and a row-parameter bound** in RFC-0245, and `Clone` bounds on generic code that opts in.
- **A refinement of RFC-0245 rule 4** (section 7, rule 6), which is relevant even without multi-shot.
- **The memory-model settlement** (metel-core#2116), for how a continuation is allocated.
- **The Linear types stage**, for the rule on linear values at handler abandonment, which multi-shot only sharpens.
- **A reified-frame evaluator** (section 9).

## 12. Open questions

1. Does Metel need multi-shot, or do replay, explicit continuation-passing and one-shot restart cover its uses?
2. How is the burden bound on a row parameter written, and does it compose with `Clone` bounds on the live values of generic code?
3. What are the semantics of handler state across resumptions: moved into the resume (backtracking) or shared?
4. How does `Drop` behave for an unresumed clone that is abandoned, and for a panic while several clones exist?
5. If `for` lowers to hidden state, is that state captured implicitly when `Clone`, or must suspension points be statement-level calls
   with no pending temporaries?
6. Can frame-internal borrows be relocated in the Core evaluator, and what does the compiled form do?
7. Does an `&outer` entry (sharing outside data among clones) justify bringing the capture list back once origins exist?

## 13. What to reserve now

None of this is needed before handlers. Four cheap steps keep the option open:

- Keep room in RFC-0245's classification for a fourth control class.
- Do not make a continuation permanently non-`Clone` at the type level (RFC-0008 says a fat pointer is not `Copy`; metel-core#2135
  already allows `Copy` on an erased callable).
- Design the Core reference evaluator with reified frames, or record why it cannot have them (compare RFC-0241 open question 29,
  on how handler control is represented).
- Take the rule 4 refinement into RFC-0245 now.

## Sources

- OCaml discussion, "Multi-shot continuations gone forever?" (discuss.ocaml.org/t/multi-shot-continuations-gone-forever/9072)
- ocaml-multicont (github.com/dhil/ocaml-multicont)
- Affect, POPL 2025 (iris-project.org/pdfs/2025-popl-affect.pdf)
- Soundly Handling Linearity, POPL 2024 (arxiv.org/pdf/2307.09383)
- Multiple resumptions without copying, Tubingen 2025 (se.cs.uni-tuebingen.de/publications/muhcu2025multiple.pdf)
- Koka evidence passing slides (xnning.github.io/slides/multip.pdf)
