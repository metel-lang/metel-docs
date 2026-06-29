---
id: strategic-overview-2026-06-29
title: "Language Design — Strategic Overview and Progress Report"
type: report
created_date: '2026-06-29'
---

# Language Design — Strategic Overview and Progress Report

*This document summarises the state of Metel language design as of June 29, 2026.
For the motivating identity and design rationale, see the June 28 strategic vision
(`strategic-vision-2026-06-28.md`).*

---

## The Identity

Metel's central design decision is that **allocator objects and lifetime tags are the
same thing**. The bracket channel (`[r]`) serves simultaneously as the runtime handle
for an allocator and as the compile-time tag that appears in pointer types and
borrow-checker errors. There are no phantom lifetimes. Every lifetime annotation
names a real value visible in source.

This is the load-bearing principle. All design work should be evaluated against it.

---

## Where the Design Stands

### Done and accepted (7 RFCs)

The core memory model is fully specified:

- **Region handles** (0063) — `@[r] T`, the bracket channel, sendability rules
- **Region ergonomics** (0065) — `@` elision, call-site bracket inference
- **Region pointer extraction** (0066) — move-out semantics
- **Reference types** (0067) — `&T`, `&mut T`
- **Struct-owned regions** (0068) — `[own r]`, private arenas
- **Sub-region typing** (0069) — `SubRegion<R>`, automatic `Outlives`
- **Ownership and move semantics** (0071) — affine types, `Clone`, `Drop`

These form a coherent, internally consistent model. None are implemented yet.

### Near-final, under review (4 RFCs)

The layer above the core, actively being reviewed:

- **Negative bounds** (0072) — `T: !Aspect`; no open questions; can be accepted now
- **AutoRegion** (0073) — compiler-managed allocation strategy; minimum optimisation
  requirement is unresolved but not a blocker
- **Shared ownership** (0074) — `SharedRegion`, `Rc`, `Arc`, `unique` keyword
- **Region inference** (0075) — implicit `AutoRegion` for bare value expressions

### Recent drafts (2 RFCs, this sprint)

Two RFCs written to fill concrete gaps:

- **Brand types** (0076) — phantom identity tokens for alias analysis, typestate, and
  algebraic effect handler disambiguation. A broad design with several applications;
  requires review before being locked in.
- **Region generics** (0077) — `impl[r] Foo[r]` blocks, generic region bounds
  (`[r: R]` where `R: Region`), wellformedness of `@[r] T` when T contains nested
  region pointers, variance rules. Fills genuine gaps the accepted RFCs leave open.

### Older drafts (26 RFCs)

A backlog of drafts from earlier development cycles, at varying levels of maturity.
Two clusters matter to the near term:

**Type system** — coherence (0060), structural bounds (0061), conditional impls (0036),
return-position impl aspect (0037), aspect objects (0008). These are prerequisites for
practical generic library code. Several have been sitting since before the memory model
work started.

**Concurrency** — concurrency model (0003) and fork-join parallelism (0064). Both are
directly downstream of the now-stable region model and can be resumed.

The rest (comptime, operators, panic recovery, FFI, unsafe, edition system, derived
aspects) are real features but not on the critical path.

---

## The Central Tension

The June 28 strategic vision concluded: *"The design work is largely done. The task
now is to make it run."*

Since that report, three more RFCs have been written (0075, 0076, 0077). This is not
necessarily wrong — 0077 fills genuine implementation-blocking gaps in the accepted
model, and 0075 was a natural next step from 0073/0074. But 0076 (brand types) is a
substantial new design direction that expands the language surface significantly.

The risk is **design drift**: the accepted cluster is not implemented, yet the design
continues to grow. Each new RFC adds surface area that must eventually be implemented
and must compose correctly with everything before it. The design coherence that exists
today is not free — it takes active effort to maintain as the RFC count grows.

---

## Honest Assessment by Area

**Memory model** — well ahead of implementation. The specification is detailed and
internally consistent. The implementation is at zero. This gap is the most important
fact about the project's current state.

**Type system** — incomplete. The aspect system as implemented handles the basic cases,
but coherence, structural bounds, and conditional impls are unspecified. These will
become blockers as soon as real generic library code is attempted.

**Ownership** — specified (0071), not implemented. The interpreter does not run the
borrow checker. Affine ownership is the foundation everything rests on, and it is not
enforced at runtime yet.

**Concurrency** — parked. RFC-0064 was deferred pending memory model stability. That
stability is now achieved in design. The RFC is ready to resume.

**Brands, effects, typestate** — exploratory. RFC-0076 covers a large design space
(alias analysis, typestate, algebraic effects) at a high level. It is conceptually
interesting but does not have the same maturity as the region cluster. Some of it
(brand types as a generic mechanism) is fairly concrete; other parts (effects via
branded capabilities) are sketch-level.

---

## Priorities

**Immediate.** Implement the borrow checker in the interpreter. This is Priority 1
from the June 28 vision and has not moved. Every subsequent design decision is easier
to evaluate once the accepted model is running against real programs.

**Short term.** Accept RFC-0072 (negative bounds) — no open questions remain.
Stabilise RFC-0073/0074/0075 as a group — they form a natural unit and completing
that review closes the under-review queue.

**Medium term.** Return to the type system draft backlog, starting with coherence
(0060) and structural bounds (0061). These are not glamorous but they determine
whether library code is actually writable.

**Hold.** RFC-0076 (brand types) should not be developed further until the core memory
model is implemented. The design is promising but it is extending the surface area at a
point where the priority is validation, not expansion. Resume after Sprint 23 or when
the borrow checker is running.

---

## What Would Change This Assessment

The analysis above would shift significantly if the borrow checker were running in the
interpreter, even partially. At that point, the design/implementation gap begins to
close, real programs provide feedback, and extension work (brands, effects, parallelism)
can be grounded in observed behaviour rather than design intuition.

Until then, the project is in a state where the design is ahead of the implementation
by roughly the entire RFC-0063–0077 cluster. That is a real risk and it should be
named clearly.
