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

**Type system** — still incomplete. RFC-0060 (coherence) is still a draft. The
`SharedPointer` aspect in RFC-0074 is now in the under-review layer but its coherence
properties are unspecified. This will become a blocker when implementation begins.

**Concurrency** — still parked. RFC-0064 can be resumed. The memory model is stable
enough to ground it.

**Borrow checker** — unimplemented. This is still Priority 1.

---

## Priorities

**Immediate.**

1. Accept RFC-0072. Zero open questions. Unblocks nothing further but clears the
   queue of a ready item.

2. Accept RFC-0073 and RFC-0074 together, with all non-blocking open questions
   deferred. The group is ready. RFC-0074 Q1 (allocation sugar) is marked "deferred
   pending RFC-0076 Q1."

**Short term.**

3. Resolve RFC-0076 Q1 (brand introduction mechanism). This is the single question
   that blocks RFC-0076 acceptance and, by dependency, closes RFC-0074 Q1. It is a
   design decision, not a specification gap — it can be resolved with a focused
   analysis.

4. Accept RFC-0075 once RFC-0073 is accepted (its primary dependency).

5. Accept RFC-0077 with remaining open questions deferred. The core design is
   implementation-blocking without it.

**Medium term.**

6. Resume RFC-0064 (fork-join parallelism). The memory model is stable; the
   `JoinToken<'b>` pattern from RFC-0076 provides a well-specified integration
   point.

7. Return to RFC-0060 (coherence) and RFC-0061 (structural bounds). These are the
   type system blockers that determine whether generic library code is writable.

**Hold.**

- RFC-0076 acceptance: wait for Q1 resolution.
- RFC-0075 acceptance: wait for RFC-0073 acceptance.
- All draft backlog items outside the clusters above.

**Priority 1, unchanged: implement the borrow checker.** Every design decision
between now and then is made without feedback from the actual model. The six-RFC
under-review cluster is ready to land; the implementation is not.

---

## What Would Change This Assessment

The analysis remains the same as June 29: implement the borrow checker in the
interpreter, even partially, and the design/implementation gap begins to close.
At that point, brand introduction can be evaluated against real programs, the
`@[Rc] expr` sugar question becomes testable, and RFC-0076 Q1 may resolve itself
through observed ergonomics rather than top-down design.

Until then, the project is in a state where the design is approximately two layers
ahead of the implementation: the under-review cluster (0072–0077) assumes the
accepted cluster (0063–0071) is running, and the accepted cluster is not running.
