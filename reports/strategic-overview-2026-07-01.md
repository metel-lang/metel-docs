---
id: strategic-overview-2026-07-01
title: "Language Design — Strategic Overview and Progress Report"
type: report
created_date: '2026-07-01'
---

# Language Design — Strategic Overview and Progress Report

*This document updates the June 29 overview. For the load-bearing identity and prior
state, see `strategic-overview-2026-06-29.md` and `strategic-vision-2026-06-28.md`.*

---

## What Changed Since June 29

The June 29 overview ended with four recommendations: implement the borrow checker
(Priority 1), accept RFC-0072, stabilise 0073/0074/0075 as a group, and hold RFC-0076
until the core is running.

The first was not acted on. Instead, the design work continued:

- **RFC-0074 was significantly rewritten.** Rc and Arc are no longer regions —
  they are library smart pointer structs. The `SharedPointer` aspect replaces the
  `SharedRegion: Region` supertrait. This change resolves the "seven exceptions"
  problem identified in the June 29 review. The new design is cleaner and internally
  consistent.
- **RFC-0076 was moved from draft to under-review.** The GhostCell pattern is now
  formally documented as the `RcToken<'b>` future direction for both RFC-0074 and
  RFC-0076. Token-gated access was expanded to cover algebraic effects and structured
  concurrency.
- **Two analysis reports were written.** The shared-ownership survey confirmed that
  no existing language solves the aliased-RC exclusive-access problem — GhostCell
  is the right direction. The `Allocatable` analysis confirmed that an `Allocatable`
  supertrait is not justified: transparent strategy change does not hold across the
  unique/shared ownership boundary.

The RFC-0074 rewrite was the right call — the old design had accumulated too many
exceptions and was not coherent. The cost is that the under-review queue grew from
four to six RFCs rather than shrinking.

---

## RFC State

### Accepted (7)

The core memory model is fully specified and internally consistent:

| RFC | Title |
|---|---|
| 0063 | Region Handles — `@[r] T`, bracket channel, sendability |
| 0065 | Region Ergonomics — `@` elision, call-site inference |
| 0066 | Region Pointer Extraction — move-out semantics |
| 0067 | Reference Types — `&T`, `&mut T` |
| 0068 | Struct-Owned Regions — `[own r]` |
| 0069 | Sub-Region Typing — `SubRegion<R>`, `Outlives` |
| 0071 | Ownership and Move Semantics — affine types, `Clone`, `Drop` |

None of these is implemented. Every one of them is ahead of the interpreter.

### Under Review (6)

**RFC-0072 — Negative Bounds.** `T: !Aspect`. Zero unresolved questions. Required
by accepted RFCs 0066 and 0071. This RFC can be accepted immediately.

**RFC-0073 — AutoRegion.** Five open questions, but all are non-blocking:
minimum optimization commitment, observability boundary, comptime interaction,
`[own r]` backing allocator, and debug/release strategy stability. The core design
is sound. The open questions are implementation-policy questions, not soundness
questions. Ready to accept with all five deferred.

**RFC-0074 — Shared Pointers (Rc and Arc).** Post-rewrite: `Rc<T, 'b>` and
`Arc<T, 'b>` as library structs with brand parameters; `SharedPointer` aspect;
`get_mut`, `try_unwrap`, `strong_count`. Four open questions:

1. `@[Rc] expr` / `@[Arc] expr` allocation sugar — unresolved; may require a
   special syntax rule without a backing trait.
2. Cycle handling — weak pointers, GC, or type-system prohibition. Deferred.
3. `RcToken<'b>` static exclusive access — deferred to follow-on after RFC-0076.
4. `Arc<T, 'b>` static exclusive access — deferred to RFC-0064.

Questions 2–4 are clearly deferred future work. Question 1 is the only live design
question: whether `@[Rc]` allocation sugar should exist without an `Allocatable`
trait. This interacts with RFC-0076 (allocation-site brands) and should be resolved
jointly. Everything else is ready to accept.

**RFC-0075 — Region Inference (Implicit AutoRegion).** The third elision level:
eliding both `@` and the region tag. Depends on RFC-0073. The open questions include
whether every struct with region-typed fields gets an implicit owned AutoRegion, and
the inference scope when a value's lifetime is not locally determinable. Less mature
than 0072–0074. Should wait for RFC-0073 acceptance before being accepted.

**RFC-0076 — Brand Types.** The broad design: phantom brand parameters, fresh-per-site
brands, token-gated access (RC, effects, concurrency), typestate, capability systems.
Five open questions:

1. **Brand introduction mechanism.** Whether `brand 'b { ... }` blocks and
   `forall<brand 'b>` closures are the right syntax, or whether the compiler can
   introduce brands implicitly per binding. This is a fundamental design question —
   the answer changes how brands appear in error messages, function signatures, and
   the surface area for library authors.
2. **Brand kind.** Whether brands and lifetime parameters share a syntactic kind.
3. **Brand inference at function boundaries.** Existential vs propagating brand
   inference for recursive functions and trait objects.
4. **`RcToken<'b>` and `Arc<'b>` across fiber boundaries.** Whether cross-fiber
   `Arc` brands need a distinct `SharedToken<'b>` with lock semantics.
5. **Brand equality across modules.** Visibility rules for opaque brands.

Question 1 is the load-bearing open question. Until it is resolved, the RFC should
not be accepted — the answer affects both the user-visible syntax and the
implementation strategy for the type checker.

**RFC-0077 — Region Generics.** Fills four gaps in the accepted region RFC cluster:
`impl` block headers for externally region-parameterised structs; generic region
bounds in the bracket channel; wellformedness of `@[r] T` when `T` contains nested
region-tagged types; variance rules. Four open questions: formal subtype
formalisation, explicit `WellFormed<r>` bound, variance for user-defined generics,
and region parameters on closures. These are all specification-completeness questions.
The core design is needed and correct; the gaps can be deferred.

### Draft Backlog (24 RFCs)

Two priority clusters matter to the near term:

**Type system completeness** — RFC-0060 (coherence), RFC-0061 (structural bounds),
RFC-0036 (conditional impls), RFC-0037 (return-position impl aspect), RFC-0008
(aspect objects). These determine whether real generic library code can be written.
The `SharedPointer` aspect introduced in RFC-0074 is now part of the under-review
layer, but RFC-0060 (coherence rules that govern which impls are reachable) is still
a draft. This is a dependency risk: RFC-0074's `SharedPointer` aspect can be written
in the RFC, but without RFC-0060 it cannot be correctly implemented.

**Concurrency** — RFC-0003 (concurrency model), RFC-0064 (fork-join parallelism).
RFC-0064 is a prerequisite for the `JoinToken<'b>` pattern in RFC-0076, and for
`Arc<T, 'b>` static exclusive access in RFC-0074. The concurrency model is directly
downstream of the stable region model and can be resumed now.

---

## The Design/Implementation Gap

The June 29 overview named this risk clearly. It has not changed.

Seven accepted RFCs specify a coherent memory model. The interpreter does not enforce
any of it. There is no borrow checker. There is no region allocator. There is no
move semantics enforcement. The language that runs on the interpreter today is not
the language described by the RFCs.

This gap is the dominant risk. Every design decision made now is made without
feedback from real programs running against the real model. The GhostCell insight,
the brand introduction mechanism, the `@[Rc] expr` sugar question — all of these
are easier to evaluate once the core is running.

---

## The New Cross-RFC Dependency

A dependency that did not exist on June 29: RFC-0074 Q1 (`@[Rc] expr` sugar) and
RFC-0076 Q1 (brand introduction mechanism) are coupled.

If `@[Rc] expr` is allocation sugar, it implicitly introduces a fresh brand at the
call site — this is exactly the allocation-site brand form described in RFC-0076.
If RFC-0076's brand introduction uses explicit `brand 'b { ... }` blocks, then
the allocation-site form is a special rule layered on top. If RFC-0076's brand
introduction instead uses implicit per-binding brands, then `@[Rc] expr` sugar
becomes a natural special case of the general mechanism with no special rule needed.

The design of each RFC is blocked on the resolution of the other. The practical path:
resolve RFC-0076 Q1 first (brand introduction mechanism), then close RFC-0074 Q1
as a consequence. RFC-0074 can be accepted with Q1 marked as "deferred pending
RFC-0076 Q1."

---

## Honest Assessment

**Memory model** — fully specified, not implemented. The specification quality is
high after the RFC-0074 rewrite. The design/implementation gap is unchanged.

**Shared ownership** — the design is now internally consistent. Rc and Arc as library
structs is the right call; the seven-exceptions problem is resolved. The cost is a
new dependency on RFC-0076 for the allocation sugar question.

**Brand types** — under review but not ready to accept. The brand introduction
mechanism (Q1) is a fundamental open question. Resolving it is the critical path
before RFC-0076 can be accepted.

**Type system** — incomplete, and now the first priority. RFC-0060 (coherence) is
still a draft. The `SharedPointer` aspect in RFC-0074 is in the under-review layer
but its coherence properties are unspecified. Several type system drafts predate the
current region model and may need to be reviewed against it rather than simply
completed. These are prerequisites for the region system — without coherence,
`SharedPointer` cannot be correctly scoped; without conditional impls, generic region
bounds cannot express complex constraints.

**Concurrency** — parked until the region system is finalised. RFC-0064 belongs in
the region-finalization phase, not before.

**Implementation** — deferred until the type system and region system designs are
complete. Implementing before the specification is stable risks implementation rework
when design decisions change. The RFC-0074 rewrite is a concrete example: implementing
the borrow checker against the old `SharedRegion` design would have produced discarded
work.

---

## Priorities

The project has three phases in sequence. No phase begins until the previous one is
complete.

### Phase 1 — Type System

Finish the type system RFC cluster. These are prerequisites for correctly specifying
the region and shared-ownership designs, and for any implementation that handles
generic code.

A dependency audit (`region-rfc-dependency-audit.md`) identified concrete gaps that
make the accepted region RFCs internally inconsistent right now. Phase 1 must address
these before the region cluster can be considered complete.

**Blocking gaps — must be resolved in Phase 1:**

| Gap | Blocking RFC(s) | Action |
|---|---|---|
| `Perhaps<T>` (nullable) and `Result<T, E>` (fallible) — naming settled, neither formally defined | 0063–0077 throughout | Single RFC defining both types and the `Result<T, !>` → `T` collapse rule |
| Never type `!` and `Result<T, !>` → `T` collapse rule | 0063, 0073 | Include in same RFC |
| Negative impls (`impl !Send for Rc<T>`) — not covered by RFC-0072 | 0074 | Extend RFC-0072 or introduce in negative-impls RFC |
| `Clone`, `Deref`, `Send`, `Sync` — assumed pre-existing, never specified | 0066, 0071, 0074, 0076 | Stdlib aspects RFC |
| RFC-0063 contradicts RFC-0074 — Arc/Rc model split | 0063 (accepted) | Amend RFC-0063 to reflect library struct model |
| `Vec<T>` vs `List<T>` naming inconsistency | 0076 | Update RFC-0076 examples to use `List<T>` |

**Type system drafts to complete or rewrite (audit required first):**

| RFC | Title | Notes |
|---|---|---|
| 0060 | Aspect Impl Coherence | Orphan rules; needed by SharedPointer, all aspect impls |
| 0061 | Structural Aspect Bounds | `T: {field: Aspect}`; needed for generic region code |
| 0036 | Conditional Impl Blocks | `impl<T: Aspect> Foo for Bar<T>`; generic library code |
| 0037 | Return-Position Impl Aspect | `fun f() -> impl Aspect`; needed for ergonomic APIs |
| 0008 | Aspect Objects | `dyn Aspect`; needed for dynamic dispatch |

Several of these are low-numbered and were written before the current region and
ownership model existed. Each must be reviewed against the current language before
being completed or rewritten.

Secondary type system drafts (in scope for this phase but not blocking the region
cluster): RFC-0038 (impl aspect struct fields), RFC-0039 (aspect alias syntax),
RFC-0049 (linear fun type system).

### Phase 2 — Region System Finalization

With the type system specified, finalize the region and shared-ownership designs.
The under-review cluster is the primary target; RFC-0064 (concurrency) closes the
phase.

1. **Accept RFC-0072** — zero open questions; clear the queue.
2. **Accept RFC-0073 and RFC-0074** together. RFC-0074 Q1 (allocation sugar) is
   deferred pending RFC-0076 Q1 resolution.
3. **Resolve RFC-0076 Q1** (brand introduction mechanism) — the single open question
   blocking RFC-0076 acceptance, and by dependency, RFC-0074 Q1. Requires a focused
   design decision.
4. **Accept RFC-0075** (region inference) — after RFC-0073.
5. **Accept RFC-0076 and RFC-0077** — after Q1 is resolved.
6. **Complete RFC-0064** (fork-join parallelism) — the memory model is stable enough;
   `JoinToken<'b>` from RFC-0076 provides the integration point.

### Phase 3 — Implementation

With a complete, coherent specification, begin implementation. The borrow checker,
region allocators, and move semantics enforcement can all be built against a stable
target. Implementation rework risk is minimised.

---

## What Would Change This Assessment

The primary risk of the design-first approach is that design without feedback from
running programs can produce specifications that are internally consistent but
ergonomically wrong. The longer the feedback loop, the higher this risk.

The mitigant: the type system phase produces RFCs that can be evaluated syntactically
and by worked examples, before any implementation. The RFC-0074 rewrite demonstrated
that paper-level review is effective at catching fundamental design errors. The brand
introduction mechanism (RFC-0076 Q1) is a design decision that can be resolved the
same way.

The assessment changes if: the type system RFC audit reveals that the draft backlog
is more extensively stale than expected, making Phase 1 substantially longer than
anticipated. In that case, a narrower scope — accept the under-review region cluster
first, then do the type system — may be warranted to avoid indefinite deferral of
the region design.
