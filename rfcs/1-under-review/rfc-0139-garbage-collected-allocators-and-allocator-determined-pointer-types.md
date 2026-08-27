---
id: rfc-0139
title: "Garbage-Collected Allocators and Allocator-Determined Pointer Types"
date: '2026-08-24'
status: under-review
target: v0.20.0
tracking: 'https://github.com/metel-lang/metel-core/issues/831'
updated: '2026-08-27'
---

> **Soundness review update, 2026-08-27.** Four issues in this proposal are promotion
> blockers, not implementation details: complete root-location discovery, cross-arena
> edges during subset collection, reclamation of GC objects containing affine
> resources, and the concurrency contract implied by a sendable `GlobalGc`. This RFC
> must not move to accepted until it gives each issue a normative rule and an
> implementable enforcement strategy. The earlier claims that borrow liveness alone is
> a precise root set and that tag disjointness alone permits subset collection are
> withdrawn below.

> **Status — under review (2026-08-27).** Scheduled for v0.20.0 local-GC design settlement under metel-core#831

## Summary

A GC allocator (global, thread-local, and instantiable local kinds) as a case of the
existing allocator interface rather than a new primitive, addressing Rust's
cyclic-data-structure shortcoming directly. Proposes generalizing the `Alloc` aspect
with a second, generic, defaulted associated type (`Pointer<T>`) so each allocator
determines what an allocation expression produces — `@a T` for the affine kinds,
unchanged, `Gc<T>` for a GC arena. Borrow liveness may contribute to keeping transient
dereferences alive, but it is not a complete root-location mechanism: the collector
must separately locate every live copied handle. Requires defaulted and generic
associated types, both explicitly declined by RFC-0082 for lack of a use case; this is
that use case.

This RFC is **not** ready for acceptance. It entered review because scheduled design
settlement is itself the process trigger; it remains at the same maturity as the
exploration it formalizes (`reports/substructural-types/gc-allocator-and-cyclic-
structures.md`, metel-docs-internal): real open questions remain unresolved, named
explicitly in "Promotion blockers and open questions" rather than glossed over. It
exists so the design has a
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
question, not a settled premise (see "Promotion blockers and open questions").

---

## Design

### 1. Three arena kinds

- **`GlobalGc`** — one process-wide arena, always nameable (parallel to `Heap`). It is
  not specified as `Send` or `Sync` until §9's synchronization and mutation contract is
  settled.
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

Storage tags prove that objects allocated in `g1` and `g2` are distinct. They do **not**
prove that an object in `g2` contains no handle into `g1`. Consequently, tag
disjointness alone does not make subset collection sound. `g1.collect()` is permitted
only under one of §7's normative cross-arena-edge policies; until one is selected,
scoped collection is a design goal rather than an established consequence of the
allocator model.

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

`Copy` is feasible only if the compiler/runtime can still enumerate every live copy at
a collection safepoint. Exemption from affine move tracking removes one possible source
of that information; it does not remove the collector's obligation to find roots.

### 6. Root-finding via the borrow checker

At every collection safepoint, the runtime must discover all roots that can reach the
collected arena. This includes live `Gc<T>` copies in registers, stack slots,
aggregates, globals/statics, and objects in other storage, plus transient `&T`/`&var T`
values derived from GC handles. Heap tracing discovers edges only after these roots are
known; it does not explain how register and stack roots are found.

RFC-0071's move/drop and borrow-liveness analysis can establish the extent of transient
borrows and can prevent a moving collector from relocating an object behind a live
borrow. It cannot by itself enumerate all `Gc<T>: Copy` values, because those copies are
deliberately exempt from affine move tracking. A sound design must select and specify at
least one complete mechanism, such as:

- compiler-emitted stack/register maps at restricted safepoints;
- an explicit or compiler-maintained shadow-root stack whose API prevents unregistered
  handles from surviving a safepoint; or
- conservative stack/register scanning, while dropping any claim of precise roots and
  specifying its interaction with pointer representation and movement.

The chosen mechanism must cover optimized code, spills, aggregates, globals, foreign
calls, and suspension/captured continuations. A non-moving collector avoids pinning and
pointer-update obligations but not root discovery. A moving collector additionally
needs relocation metadata and a rule that pins or rejects movement behind every live
derived borrow.

### 7. Cross-arena edges and subset collection

Before `g1.collect()` can collect without scanning every other arena, the language must
choose one of the following policies or an equivalently complete one:

1. reject handles from `g1` when storing into objects whose storage identity is not
   `g1` (including globals and non-GC storage);
2. record every incoming cross-arena edge in a remembered set/write barrier and scan
   that set as roots of `g1`; or
3. scan every storage domain that may contain an incoming edge.

The policy must cover edges introduced through interior mutation, generic containers,
erased/dynamic values, and unsafe or foreign interfaces. Distinct storage identities
remain useful for stating the policy, but non-aliasing is not non-reachability. Subset
collection is a promotion-blocking claim until the edge rule is normative and tested.

### 8. Affine contents, destruction, and finalization

A traced object may become unreachable without an explicit affine owner performing its
drop. Therefore `Gc<T>` cannot be admitted for arbitrary `T` merely because the handle
itself is `Copy`. Before acceptance, this RFC must choose and enforce one of these semantic
boundaries:

- require a bound that excludes `Drop`/affine contents from the transitive object graph;
- provide a finalization protocol that runs each required destructor exactly once and
  specifies ordering, resurrection, cycles, panics/aborts, and collection reentrancy;
  or
- require affine resources to live behind a separately owned handle whose lifetime is
  not determined by GC reachability.

“Wrap it in GC too” is insufficient for files, locks, unique heap allocations, and
other resources whose correctness depends on deterministic release. This rule belongs
at placement/type-checking boundaries and must apply through fields, rows, generic type
parameters, aspect objects, and captured continuations.

### 9. `GlobalGc`, concurrency, and `Send`/`Sync`

A process-wide arena is not automatically safe to access from multiple threads. If a
`GlobalGc` handle is `Send` or `Sync`, the design must specify how dereference,
mutation, root publication, and collection synchronize. A complete contract must say
whether collection stops participating threads, whether writes require barriers, which
operations are atomic, where safepoints occur, and what happens when a thread is in
foreign code or holds a derived borrow.

Merely making its handles `!Send + !Sync` is insufficient if every thread can
independently access the same process-wide singleton. Until that contract exists,
`GlobalGc` is a reserved design row, not an available safe standard allocator. A
resolution may instead remove it, restrict the entire arena to one statically
designated thread, or specify safe shared access. Concurrent or stop-the-world
collection algorithms may remain implementation choices only after the observable
safety contract is fixed.

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

- The tracer's concrete algorithm and performance policy (mark/sweep versus copying,
  generations, compaction heuristics, and pause targets). Root completeness,
  cross-arena-edge handling, finalization restrictions, and concurrency safety are
  **not** out of scope because the public type and collection operations are unsound
  without them.
- A particular concurrent collector implementation. The safety contract required for
  `GlobalGc: Send + Sync` remains in scope even if the first implementation is
  stop-the-world or keeps `GlobalGc` thread-bound.
- Rank-2 polymorphism and the semantics of effect handling themselves. However, any
  selected root protocol must still enumerate GC handles held in suspended
  continuations once those continuations exist.

---

## Promotion blockers and open questions

### Soundness blockers

The following are mandatory before this RFC may move to `2-accepted`. Deferring
them to implementation or leaving them as algorithm choices is not acceptable:

1. **Complete root-location protocol.** Select one of §6's mechanisms, specify its
   safepoints and optimizer/FFI/continuation obligations, and demonstrate that live
   copied handles and derived borrows cannot be omitted.
2. **Cross-arena-edge policy.** Select and enforce one of §7's policies. Until then,
   subset collection must not appear as a safe operation or claimed consequence of
   static identity.
3. **Affine-content/finalization boundary.** State the admissibility bound or complete
   finalization semantics from §8, including transitive generic contents and cycles.
4. **Concurrency and sendability contract.** Remove/defer `GlobalGc`, prove the whole
   arena is confined to one designated thread, or specify and validate §9's shared
   synchronization contract. `!Send + !Sync` handles alone do not confine an
   independently nameable process-wide singleton.

### Other design questions

1. **Does `Gc<T>` hold as `Copy` under the selected root protocol?** (§5) Copyable
   traced handles have prior implementation precedent, but Metel must verify its own
   representation, safepoints, mutation rules, and compiler lowering.
2. **`collect()`'s exact signature.** (§6) A coarse `&var g` may block derived borrows
   of that arena, but it still does not locate independent copied handles. Decide the
   signature only after the root protocol is selected.
3. **The `Alloc::Pointer<T>` mechanism itself is unverified against real associated-type
   default semantics.** RFC-0082's declined-defaults reasoning (§9 there) is worked
   through in "Relationship to existing RFCs" above but not formally resolved as an
   amendment to that RFC. This is the load-bearing prerequisite the rest of this RFC
   depends on; until it's actually written up and checked, everything downstream of it
   is provisional.
4. **Surface expression of §8's affine-content boundary.** Decide whether this is a
   negative `Drop`/affinity bound, a transitive trace-safety aspect, or a finalizer
   capability. Re-wrapping an affine resource in another `Gc` is not a solution because
   it leaves the same nondeterministic-destruction obligation one level deeper.
5. **`brand-kind-unification.md`'s role-crossing matrix** (metel-docs-internal) does
   not yet enumerate the specific crossing `GcRegion`'s tag reuse (§1) depends on.
6. **Whether `GlobalGc` should ever be sendable.** This is a product/design choice;
   if yes, the associated safety contract is nevertheless a soundness blocker above.
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
- `reports/strategy/research-novelty-audit-2026-07-16.md`, reassessment dated
  2026-08-27 (metel-docs-internal) — prior-art and soundness review that identified the
  four promotion blockers incorporated above.
- `gc-arena` — copyable branded GC handles and independently collectible arenas:
  <https://github.com/kyren/gc-arena>.
- `zerogc` — explicit safepoints and borrow-checker-assisted roots:
  <https://docs.rs/zerogc>.
- Hughes and Marr, “Garbage Collection for Rust: The Finalizer Frontier” — survey of
  rooting/finalization constraints in Rust GC designs: <https://doi.org/10.1145/3763179>.

---

## Decision

**Outcome:** *(pending — under review, not ready for acceptance; see Promotion blockers and open
questions)*
**Target:** *(set when accepted)*
