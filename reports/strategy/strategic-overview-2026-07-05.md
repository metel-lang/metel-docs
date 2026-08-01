---
id: strategic-overview-2026-07-05
title: "Language Design — Strategic Overview"
type: report
created_date: '2026-07-05'
---

# Language Design — Strategic Overview

*This document supersedes `strategic-overview-2026-07-01.md`. For the prior state,
see that document. The archives in `reports/archive/` cover the earlier session
history.*

---

## What Changed

The July 1 overview closed Phase 2 with 22 accepted RFCs and one remaining design
item (RFC-0064, fork-join parallelism). Between July 2 and July 4, a single crack
in the accepted region cluster propagated into a full redesign of the memory model.

**The crack.** RFC-0066 (individual drop/move-out) allows a value to be moved out
of a region while the region continues. This breaks RFC-0063's founding invariant:
value lifetime = region lifetime. Once that invariant fails, the region concept is
doing triple duty — allocation strategy, disjointness proof, lifetime tag — and
only the first two hold. The entire `PhantomRegion`/`Outlives`/`SubRegion` cluster
(RFC-0085, RFC-0087, RFC-0069) exists solely to paper over the third.

**The redesign.** Eight accepted RFCs (0063, 0065, 0066, 0067, 0068, 0069, 0073,
0077) moved back to under review. The model was rebuilt from first principles and
documented in `reports/memory-model/lifetimes-vs-regions-2026-07-02.md`:

- **Allocators are first-class values.** `Heap`, `LocalHeap`, `BumpAlloc`,
  `AutoAlloc`, and scoped allocators live in the **value channel** `()` with
  the `@` prefix: `fun build(@a: BumpAlloc, v: T) -> @a Node<T>`. The `Alloc`
  aspect replaces the old `Region` aspect. Renamed throughout: `BumpRegion` →
  `BumpAlloc`, `AutoRegion` → `AutoAlloc`.

- **Lifetime anchors are a separate compile-time concept.** A borrow `&r T`
  carries `r` — a binding name, not an abstract `'a`-style variable. Lifetime
  anchor parameters are declared in the **type-parameter channel** `<>` with
  the `&` prefix: `fun foo<&r>(&r T) -> &r U`. Anchors are elidable; explicit
  `<&r>` declarations appear only when ambiguous.

- **Channel assignments** — the three parameter channels now have unambiguous
  semantic categories:

  | Channel | Contents | Syntax |
  |---------|----------|--------|
  | `<>` | Types and lifetime anchor parameters | `<T>`, `<&r>`, `<&s, &t: &s>` |
  | `()` | Values and allocator parameters | `(x: T)`, `(@a: BumpAlloc)` |
  | `[]` | Capture lists | `[x, y]` |

- **Storage Transparency Principle.** Any language construct that does not
  explicitly reference an allocator or lifetime anchor is implicitly polymorphic
  over storage. Annotations appear only at allocation expressions and explicit
  borrow anchors — the two points where storage decisions are actually made.

- **`Outlives` dropped** from the allocator layer. Duration ordering is expressed
  through lifetime anchor bounds `<&t: &s>` and the borrow checker's scope analysis.

- **RFC-0069 (`SubRegion`), RFC-0085 (`PhantomRegion`), RFC-0087 (universal
  own-region)** identified for retraction. All three exist solely to support the
  region-as-lifetime mechanism, which the split model eliminates.

All semantic questions in the position report are settled: drop order with
interleaved move-out, sendability, `&self` denotation, lifetime anchor grammar,
elision rules. The one remaining open question is the ratification vehicle (new
RFC-0088 vs. amendment to RFC-0063).

**Reports reorganized.** The `reports/` directory was restructured into
topic subdirectories (`memory-model/`, `strategy/`, `implementation/`, `blog/`,
`module-system/`, `runtime/`, `technical-debt/`) with an `archive/` for superseded
documents.

---

## RFC State

### Accepted (14)

The type-system cluster and core ownership RFC are unaffected by the redesign.

| RFC | Title |
|-----|-------|
| 0008 | Aspect Objects — `dyn Aspect`, fat pointer, object safety |
| 0036 | Conditional Impl Blocks — `where` clause, syntactic negation disjointness |
| 0037 | Return-Position `impl Aspect` — opaque monomorphised return type |
| 0060 | Aspect Impl Coherence — orphan rule, overlap, CWA, auto-impl, priority |
| 0061 | Structural Aspect Bounds — `T[]` blanket impls, auto-impl propagation, `Callable` |
| 0071 | Ownership and Move Semantics — affine types, `Clone`, `Drop`, drop order |
| 0072 | Negative Bounds — `T: !Aspect` |
| 0078 | Bottom Type — `!`, uninhabited coercions, `Result<T, !>` collapse |
| 0079 | Perhaps and Result — formal definitions, prelude membership |
| 0080 | Stdlib Aspects — `Clone`, `Deref`, `Send`, `Sync` |
| 0081 | Negative Impls — `extend Type: !Aspect;`, priority over auto-impl |
| 0082 | Associated Types — `type X;` in aspects, `type X = Y;` in impls, projection |
| 0083 | Public Value Exports — `pub let`, `heap`/`local_heap` naming |
| 0084 | Fixed-Size Array Syntax — `T[N]` replaces `[T; N]` |

None is implemented except basic aspects, generics, and some stdlib types. Every
RFC from 0036 onward is ahead of the interpreter.

### Under Review (12)

**RFC-0063 — Region Handles (now: Allocator Handles).** The founding RFC of the
memory cluster. Must be rewritten: `Region` → `Alloc`, allocators move to the
value channel, `Outlives` dropped, bracket-channel allocation syntax replaced by
`@a expr` use-site form.

**RFC-0065 — Region Ergonomics.** Elision rules must be restated for the split
model: allocator elision (single `@`), lifetime anchor elision (three rules in §7
of the position report).

**RFC-0066 — Region Pointer Extraction.** The trigger for the redesign. Move-out
semantics survive; the `@[r] T` syntax becomes `@a T`. The `T: !Drop` legality
matrix is unchanged in substance.

**RFC-0067 — Reference Types.** `&T`, `&var T` survive. Borrow syntax becomes
`&r T` at use, `<&r>` at declaration. Auto-deref and deref coercions unchanged.

**RFC-0068 — Struct-Owned Regions (now: Struct-Owned Allocators).** `[own r]`
replaced by primary constructor syntax: `struct Foo(@a: BumpAlloc)`. Bracket
channel dropped; `own` keyword dropped.

**RFC-0069 — Sub-Region Typing.** **Identified for retraction.** `SubRegion<R>`
and its `Outlives` propagation are eliminated by the split model. The borrow
checker derives nesting from scope structure.

**RFC-0073 — AutoRegion (now: AutoAlloc).** Rename only; the five semantic
guarantees and compiler latitude clauses are unchanged.

**RFC-0074 — Shared Ownership (`Rc`, `Arc`).** Core API and sendability rules
are sound. The `brand 'b` parameter in type signatures depends on RFC-0076 Q1.
Blocking: RFC-0076.

**RFC-0077 — Region Generics (now: Allocator Generics).** Wellformedness restated
over allocator scopes only; value-lifetime constraints are borrow-checker-derived.
Variance analysis is unchanged in structure.

**RFC-0085 — PhantomRegion.** **Identified for retraction.** Exists solely to give
non-allocating bindings a `Region` for `Outlives` machinery. Eliminated by the
split model.

**RFC-0086 — Borrow-Outlives Sugar.** `[x, y]` sugar reinterpreted: in the new
model it reads as `<&x, &y>` lifetime anchor parameter declarations. Multi-anchor
borrow form (`&r, s T`) deferred. RFC needs rewriting or retraction depending on
whether the multi-anchor form is eventually accepted.

**RFC-0087 — Universal Own-Region.** **Identified for retraction.** Exists to give
every binding an own-region so that `Outlives` has something to name. Eliminated by
the split model.

### Draft / Parked

**RFC-0075 — Region Inference.** Parked. Cannot be fairly evaluated without
implementation experience. Revisit after the borrow checker and allocators are
running. The explicit annotation system with elision is ergonomic enough to begin.

**RFC-0076 — Brand Types.** Back in draft. Q1 (brand introduction mechanism)
remains unresolved; the correct call is to defer rather than speculate. Unblocks
RFC-0074 when resolved.

**Draft backlog (~22 RFCs).** Includes RFC-0064 (fork-join parallelism), RFC-0038
(impl aspect struct fields), RFC-0039 (aspect alias syntax), RFC-0049 (linear fun
type system), RFC-0003 (concurrency model), and others.

---

## The Design/Implementation Gap

The gap named in the July 1 overview has not narrowed. It has, however, been
recalibrated: the July 1 count of "23 accepted" has corrected to 14 accepted + 8
under review, but 14 correctly-stated accepted RFCs are a better foundation than
22 that included a cracked cluster.

The interpreter still has no borrow checker, no allocator, and no move semantics
enforcement. It deep-clones values and leans on reference counting internally.

Two timelines of risk:

1. **Design risk** — the memory model is settled on paper but not ratified as an
   RFC. Until the cluster sweep is complete (RFC-0088 ratified, 0069/0085/0087
   retracted, 0063/0065/0066/0067/0068/0073/0077 rewritten), the cluster's
   accepted/under-review state is ambiguous.

2. **Implementation risk** — every additional design session before implementation
   begins extends the feedback gap. RFC-0075 is the concrete example: inference
   that looked plausible on paper became speculative without running programs.

Phase 1 (static type-system cluster) is unaffected by the redesign and proceeds
independently.

---

## Honest Assessment

**Type system** — complete and unaffected. Fourteen accepted RFCs specifying a
coherent, mutually consistent static type system. RFC-0061 in particular received
significant cleanup in the July 1 session: function-types-cannot-implement-aspects
claim corrected, auto-impl propagation specified, `T[]` representation made explicit.

**Memory model** — design is settled; ratification is not. The position report
(`lifetimes-vs-regions-2026-07-02.md`) resolves all semantic questions. The split
model (allocators as values in `()`, lifetime anchors in `<>`) is internally
consistent and satisfies the Storage Transparency Principle. The cluster sweep
(rewriting 8 under-review RFCs) is the concrete work remaining on the design side.

**Brand types** — deferred. RFC-0076 Q1 is an open design question. Correct call.

**Concurrency** — not started. RFC-0064 (fork-join) remains a draft priority;
`JoinToken<'b>` integration waits for RFC-0076.

**Implementation** — still the dominant risk, still the right next step after
ratification. The borrow checker, allocators, and move semantics have a stable
target once the cluster sweep is done.

---

## Priorities

### Immediate — Ratify the memory model

The position report is complete. The ratification path:

1. **Write RFC-0088 ("Allocators and Lifetimes")** — the split model, Storage
   Transparency Principle, channel assignments, elision rules, sendability, and
   drop order as a first-class ratified RFC.
2. **Retract RFC-0069, RFC-0085, RFC-0087** — mark as retracted with a one-line
   note pointing to RFC-0088.
3. **Sweep the cluster** — rewrite RFC-0063, 0065, 0066, 0067, 0068, 0073, 0077
   against the ratified model and return them to accepted.

### Short-term — Update the implementation breakdown

`rfc-implementation-breakdown-2026-07-01.md` was written for the old 22-RFC
cluster. Phase 3 (region system) references `@[r] T`, `[own r]`, `SubRegion`,
and `Outlives` — all superseded. Once the cluster sweep is complete, Phase 3 needs
to be rewritten against the new model:

- New primitives: `@a T`, `&r T`, primary constructor syntax, `<&r>` declarations
- `SubRegion` / `Outlives` entries removed from the dependency graph
- `AutoAlloc` replaces `AutoRegion` throughout

The cross-cutting prerequisites (borrow-checker stage, value-representation
overhaul) are unaffected and do not need rewriting.

### Phase 3 — Implementation (after ratification)

The implementation begins the same way whether the ratification happens now or
later. Start with:

1. Move semantics enforcement (RFC-0071) — affine types, no implicit copy
2. Reference types and borrow checking (RFC-0067) — `&T`, `&var T`
3. Allocator layer (RFC-0063 rewritten) — `@a T`, `Alloc` aspect, `BumpAlloc`,
   `AutoAlloc` backed by real allocators
4. `pub let` (RFC-0083) and array syntax (RFC-0084) — mechanical changes

Phase 1 (Cluster A, static type system) is independent and can proceed in parallel
if implementation bandwidth allows.

### Follow-on — RFC-0064 and RFC-0076

RFC-0064 (fork-join parallelism) closes the concurrency design gap; scope it
without brand-gated tokens. RFC-0076 (brand types) revisit once the borrow checker
is running.

---

## What Would Change This Assessment

**If the cluster sweep surfaces a new contradiction** in the split model — that is,
if rewriting 0063/0065/0066/0067/0068/0073/0077 reveals a case the position report
did not anticipate — the position report takes another revision pass. The model is
settled on the dimensions covered; it is possible that a detail in one of the
cluster RFCs was not covered. Targeted amendment is the right response; the core
split (allocators in `()`, lifetime anchors in `<>`) is not in question.

**If RFC-0064 is scoped**, the concurrency design closes and RFC-0074 becomes the
one remaining pre-implementation design item pending RFC-0076.

**If implementation begins**, the borrow checker and allocator work will surface
ergonomic questions that paper review cannot — in particular, how burdensome the
explicit `<&r>` declarations are in practice, which will inform whether RFC-0075
(inference) is worth revisiting.
