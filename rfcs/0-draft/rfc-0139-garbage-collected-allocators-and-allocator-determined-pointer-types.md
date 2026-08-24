---
id: rfc-0139
title: "Garbage-Collected Allocators and Allocator-Determined Pointer Types"
date: '2026-08-24'
status: draft
target:
---

## Summary

A GC allocator (global, thread-local, and instantiable local kinds) as a case of the
existing allocator interface rather than a new primitive, addressing Rust's
cyclic-data-structure shortcoming directly. Proposes generalizing the `Alloc` aspect
with a second, generic, defaulted associated type (`Pointer<T>`) so each allocator
determines what an allocation expression produces — `@a T` for the affine kinds,
unchanged, `Gc<T>` for a GC arena — and reuses the borrow checker's own move/drop
liveness analysis as a precise GC root set. Requires defaulted and generic associated
types, both explicitly declined by RFC-0082 for lack of a use case; this is that use
case.

This RFC is **not** ready for review. It is drafted at the same maturity as the
exploration it formalizes (`reports/substructural-types/gc-allocator-and-cyclic-
structures.md`, metel-docs-internal): real open questions remain unresolved, named
explicitly in "Open Questions" rather than glossed over. It exists so the design has a
tracked, numbered home and a milestoned issue rather than living only in a
conversation transcript.

---

## Motivation

### The problem this addresses

Rust's answer to cyclic, freely-shared data (a doubly-linked list, a graph, an
observer pattern, a parent-pointing tree) is `Rc`/`Weak` discipline: the programmer
manually identifies which edges are "owning" and which are "back" pointers, spells
them differently, and a single wrong choice leaks the cycle forever. Nothing checks
that the `Weak`/`Rc` split matches the graph's actual reachability structure. This is
not a soundness bug — nothing is memory-unsafe — it's an ergonomics and correctness
failure with no compiler backstop.

This is a **different problem** from the one `shared-ownership-survey-2026-06-29.md`
(metel-docs-internal) already solved for Metel: that document's `RcToken` answers
*exclusive mutation of an aliased value*. It says nothing about *reclaiming* a cyclic
structure — granting exclusive mutation access doesn't tell you when a cycle's nodes
become unreachable. Both problems involve `Rc`-shaped values, which makes them easy to
conflate; this RFC is only about the second.

The stated goal driving this RFC: a real tracing GC as one allocator option
(global-singleton, thread-local-singleton, and independently instantiable local
kinds), with the option to manually trigger a collection cycle — including a *subset*
collection, scoped to one local arena without touching any other — and appropriate
relief from the borrow checker's ordinary ownership tracking for GC-managed values,
since a GC-managed value has no single owner by design.

### Why this needs an `Alloc` change, not just a new library type

The entire allocator design (RFC-0063 and its cluster) stands on RFC-0071's affine
ownership: `@a T` is non-`Copy` by construction, moves transfer exclusive ownership,
and exactly one live owner exists at any point. A tracing GC's value proposition is
the opposite premise: many simultaneous live references, no static owner, freed when
runtime reachability analysis — not move-tracking — says nothing points to it anymore.

`allocators-as-emergent-synthesis.md` (metel-docs-internal) decomposes the allocator
design into context parameter + brand + owned box + borrow checker, and names the `@`
allocation-expression sugar and the `Alloc` aspect as the only genuinely
allocator-specific residue. This RFC's central bet is that a GC allocator is *not* a
case the decomposition needs a fifth primitive for — it's a case that needs the
allocator to determine a *different* result shape for the same `@a expr` sugar, not a
different primitive. Whether that bet survives implementation is this RFC's open
question, not a settled premise (see "Open Questions").

---

## Design

### 1. Three arena kinds

- **`GlobalGc`** — one process-wide arena, always nameable (parallel to `Heap`),
  sendable.
- **`LocalGc`** — one per thread, always nameable (parallel to `LocalHeap`), not
  sendable.
- **`GcRegion::new()`** — independently instantiable, multiple live at once (parallel
  to `BumpAlloc`), not sendable.

`GlobalGc`/`LocalGc`'s tag is the allocator's own fixed, globally-known name — no
per-instance disambiguation needed, exactly the way `Heap`/`LocalHeap` already use
their own type name as the tag today, so no generic-parameter threading is required at
any use site. `GcRegion` instances reuse `@a T`'s *existing* invisible, per-allocation-
site tagging (RFC-0063 §2's instance-level, not type-level, identity) — no new tagging
mechanism, and (§4 below) the same permanent-tag rule every other allocator already
has, not a degrading/runtime-tracked one, kept uniform deliberately rather than giving
GC a special exception.

### 2. `Alloc::Pointer<T>` — the allocator determines what `@a expr` produces

`Alloc` currently has one associated type (`AllocationError`, RFC-0063 §1). Add a
second, generic, defaulted one:

```metel
// Illustrative — names not proposed as final surface syntax.
aspect Alloc {
    type AllocationError;
    type Pointer<T> = @Self T;   // default: today's exact behavior, unchanged
    fun alloc<T>(self: &Self, value: T) -> Result<Self::Pointer<T>, Self::AllocationError>;
}
```

`@a expr` stays exactly the primitive it already is (RFC-0063 §3: "not a method
call... the compiler lowers to a call through the runtime handle") — only its *type*
changes, from a hardcoded `@a T` to `A::Pointer<T>`, an associated-type projection
resolved from whatever `a`'s allocator type declares. Every existing allocator (`Heap`,
`LocalHeap`, `BumpAlloc`, `AutoAlloc`, and any custom `Alloc` implementor) needs **zero**
changes to its own specification, because its current behavior is the default case of
the generalized interface. `GcHeap`/`GcRegion` declare `type Pointer<T> = Gc<T>;` and
that declaration is the entire integration point — no new expression form, no new
sugar.

Generic code parameterized over `<A: Alloc>` (RFC-0077) allocating via `@a` where
`a: A` resolves `A::Pointer<T>` as an associated-type projection at a still-abstract
type — the same mechanism `T::AssocType`-style projections already use elsewhere
(RFC-0082), reapplied, not a new kind of type-level computation.

**This RFC does not propose a `Gc<T, A>` type-parameterized alternative.** An earlier
pass considered making `Gc<T>` itself generic over the allocator's type
(Rust-`Box<T,A>`-style) to distinguish `GlobalGc`-produced from `LocalGc`-produced
values without reviving bracket-tag notation. Superseded: §1's "allocator's own fixed
name as the tag" answer already provides that distinction through the *existing*
tagging mechanism, so no second, parallel type-parameter scheme is needed on top of it.

### 3. Manual, scoped collection

Falls directly out of the tag-disjointness fact the allocator model already proves for
an unrelated reason (RFC-0063 §2: "`@a T` and `@b T` with `a ≠ b` are provably
non-aliasing"). `g1.collect()` cannot touch `g2`'s live objects for the same reason two
region pointers with distinct tags already provably cannot alias — not a new
mechanism, a direct reuse of an existing proof.

```metel
// Illustrative.
let g1 = GcRegion::new();
let g2 = GcRegion::new();
let n1 = @g1 Node { value = 1, next = None };
g1.collect();          // traces and reclaims only g1's arena
GlobalGc.collect();     // the singleton case
```

### 4. Tag permanence, kept uniform with every other allocator

A design fork was raised and closed during this RFC's exploration: does `@a Gc<T>`'s
tag stay part of the type permanently (as `@a T` already does for every other
allocator today), or does it degrade to an arena-erased `Gc<T>` once stored, with
arena identity tracked at runtime instead (the way mainstream tracing collectors — V8,
the JVM, Go — actually track multi-space heaps, via a runtime per-object tag rather
than a compile-time-proven one)?

**Decided: permanent, uniform with the existing model.** Regular allocators do not
degrade today — `@a T`'s tag is the entire foundation of the disjointness and
sendability story. Extending the identical rule to `Gc<T>` was chosen deliberately
over carving out a GC-specific exception, even though it diverges from how mainstream
GCs are usually built. Traced through for ergonomic cost: this only actually bites for
`GcRegion` (a struct holding a `GcRegion`-tagged field needs to be generic over the
tag, exactly the pre-existing `BumpAlloc` tradeoff for scoped allocators) — `GlobalGc`/
`LocalGc`, the kinds actually motivating this RFC's cyclic-structure goal, cost nothing
here, since their tag is a fixed name usable from anywhere, no threading required.

### 5. `Gc<T>` needs no new pointer kind, because it needs no `Clone`

Unlike `Rc<T>` (needs `Clone`, not `Copy`, because cloning increments a refcount — a
side effect that must run exactly once per alias), a tracing-GC handle has no refcount
and no per-alias side effect: the tracer discovers every live copy by walking
reachable memory, regardless of how many copies exist. This makes `Gc<T>` a plausible
candidate for genuine `Copy` — and `Copy` is already, in the existing model, what
exempts a type from affine move-tracking. If this holds, the "borrow-checker
exemption" this RFC's motivating goal named may not be a new carve-out at all, just an
existing rule applying normally. Requires interior mutability for write access (the
same shared-mutability story `Rc<RefCell<T>>` already needs in Rust, nothing
GC-specific) and relies on `Copy`/`Drop`'s existing mutual exclusion (RFC-0071) rather
than a new special case — a `Gc<T>` handle correctly has no per-handle `Drop`, since
reclamation timing is the tracer's decision, not any individual handle's.

### 6. Root-finding via the borrow checker

A stored `Gc<T>` handle is found by the tracer regardless of where it's been copied to
— that's §5's whole point. A *transient dereference* (a short-lived `&Node` obtained
from a `Gc<T>` handle) is not itself a stored handle, and needs a root set the same way
every tracing GC does — normally built via compiler-generated stack maps purpose-built
for the collector. This RFC proposes reusing infrastructure that already has to exist
for an unrelated reason: RFC-0071's move/drop analysis already computes, precisely,
which stack slots hold live borrows and for how long. If `collect()` can query that
directly, the collector gets root-set precision from infrastructure built for move/drop
correctness, not a from-scratch stack-map builder — a genuine Metel-specific advantage
over a conservative or hand-rolled collector, contingent on the query actually being
buildable against the real move-check implementation (unverified — see "Open
Questions").

---

## Relationship to existing RFCs

- **RFC-0063 (Allocator Handles)** — this RFC generalizes `Alloc`'s interface; every
  existing stdlib allocator's behavior is the default case, unchanged.
- **RFC-0077 (Allocator Generics)** — the generic-`<A: Alloc>`-code machinery this RFC's
  `A::Pointer<T>` resolution reuses directly; this RFC does not revisit RFC-0077's own
  impl-header/wellformedness/variance questions.
- **RFC-0071 (Ownership and Move Semantics)** — `Copy`/`Drop` mutual exclusion (§5) and
  the move/drop liveness analysis (§6) this RFC proposes reusing, not rebuilding.
- **RFC-0074 (Shared Ownership, `Rc`/`Arc`)** — a genuinely separate design (two
  brand-parameterized structs backed by a fixed `@Heap`-internal allocation), not
  something this RFC's `Pointer<T>` mechanism unifies with or changes. An earlier draft
  of this exploration incorrectly claimed a retirement of `Arc<T>[Heap]`-style special
  casing; withdrawn on inspection — no such special case exists in RFC-0074's actual
  design. Noted here so the record is explicit, not silently dropped.
- **RFC-0082 (Associated Types)** — this RFC needs two extensions RFC-0082 explicitly
  declined (§9, §10 item 2): defaulted associated types and generic associated types.
  RFC-0082's stated reason for declining defaults was un-worked coherence risk under
  RFC-0060; this RFC's own investigation (below) suggests that risk is more tractable
  than the one-sentence dismissal implied, but does not claim to have resolved it.
- **RFC-0060 (Aspect Implementation Coherence)** — checked directly rather than
  assumed: its overlap-detection rule is specifically about aspect-impl-for-*type*
  coverage, and a defaulted associated type does not add a new impl-for-a-type at all
  (there is still exactly one `Alloc` impl per allocator type, whether or not it
  restates `Pointer<T>`). Two sub-problems defaults would introduce both have working,
  unreused precedent already in RFC-0060: same-named-associated-type ambiguity across
  two aspects (§10 item 1's existing hard-error rule, generalizes directly) and
  blanket-vs-concrete priority (§5's existing "concrete overrides blanket" rule,
  structurally the same shape). Neither has been formally written up as an amendment;
  this is a finding that the path looks tractable, not a proof.

---

## Out of Scope

- The tracer's actual algorithm and runtime implementation — real, unbuilt runtime
  work, the same category of gap as the effects system's unbuilt continuation-capture
  mechanism (`algebraic-effects.md` §8, metel-docs-internal). This RFC specifies the
  type-level surface a tracer would need to satisfy, not the tracer itself.
- A concurrent/shared collector for a *sendable* GC arena. `GlobalGc`'s sendability in
  this RFC means "one arena, no thread affinity requiring no cross-thread
  synchronization" — not "safe for concurrent tracing while multiple fibers mutate it."
  A genuinely concurrent collector is a materially harder implementation problem, not
  assumed solved here.
- Rank-2 polymorphism, effect-handler interaction, or any connection to the separate
  algebraic-effects/structured-concurrency design threads — this RFC is scoped to
  allocation and reclamation only.

---

## Open Questions

1. **Does `Gc<T>` actually hold as `Copy`?** (§5) The central hypothesis this whole
   design rests on. Not verified against a real implementation.
2. **`collect()`'s exact signature.** (§6) Coarse (`&var g`, sound and cheap today,
   blocks on any outstanding borrow anywhere in the arena — mirrors the diagnostic
   already shown for `drop(a)` on a `BumpAlloc`, RFC-0063 §5) vs. precise (a per-borrow
   root scan against the borrow checker's live-borrow set at an arbitrary program
   point — more valuable, real unbuilt analysis work, not proven buildable against the
   actual move-check implementation). Leaning coarse-first; not decided.
3. **The `Alloc::Pointer<T>` mechanism itself is unverified against real associated-type
   default semantics.** RFC-0082's declined-defaults reasoning (§9 there) is worked
   through in "Relationship to existing RFCs" above but not formally resolved as an
   amendment to that RFC. This is the load-bearing prerequisite the rest of this RFC
   depends on; until it's actually written up and checked, everything downstream of it
   is provisional.
4. **Coherence with the affine world at a `Gc<T>`-reachable struct's boundary.** Can
   such a struct contain an affine-owned `@Heap U` field directly? Likely "no, unless
   `U` is itself `Copy` or re-wrapped as its own `Gc<U>`," mirroring the existing rule
   for any `Copy` struct — not yet stated as an explicit rule.
5. **`brand-kind-unification.md`'s role-crossing matrix** (metel-docs-internal) does
   not yet enumerate the specific crossing `GcRegion`'s tag reuse (§1) depends on.
6. **Sendability for a genuinely shared GC arena** — deliberately out of scope (see
   above), but the question of whether it's ever wanted at all is unexamined.
7. **Whether "manual trigger" (§3) is ever more than a single synchronous `.collect()`
   call** — incremental/generational controls are not examined.

---

## References

- `reports/substructural-types/gc-allocator-and-cyclic-structures.md` (metel-docs-
  internal) — the exploration document this RFC formalizes; read it for the full
  reasoning trail, including the corrections made along the way.
- `reports/substructural-types/allocators-as-emergent-synthesis.md` (metel-docs-
  internal) — the decomposition this RFC's central bet either confirms or falsifies.
- `reports/memory-model/shared-ownership-survey-2026-06-29.md` (metel-docs-internal) —
  the adjacent, already-solved problem (exclusive mutation via `RcToken`) this RFC is
  explicitly not about.
- `reports/memory-model/memory-model-overview.md` (metel-docs-internal) — corrected
  2026-08-24 for staleness found while drafting this RFC; the accurate current source
  for the allocator model this RFC builds on.

---

## Decision

**Outcome:** *(pending — not ready for review; see Open Questions)*
**Target:** *(set when accepted)*
