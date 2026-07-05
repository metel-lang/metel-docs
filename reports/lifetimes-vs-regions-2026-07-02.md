---
id: lifetimes-vs-regions-2026-07-02
title: "Allocators first-class, lifetimes visible — the split model"
type: report
created_date: '2026-07-02'
updated_date: '2026-07-04'
---

# Allocators first-class, lifetimes visible — the split model

*Position report, not an RFC. Supersedes the "two-level model" draft of this same
document: that draft kept lifetimes inside the `Region` aspect (a unified model) and
recommended against splitting. The review of RFC-0085/0086/0087 — especially the
value-lifetime vs region-lifetime distinction forced by RFC-0066 (individual drop) — is
the evidence that unification does not hold. This report resolves it the other way.*

*Updated 2026-07-04: expanded with subsequent design decisions — (1) "regions" renamed to
"allocators"; (2) `own` keyword dropped from struct allocator declarations; (3) `Outlives`
dropped from the allocator layer; (4) `SubRegion` retracted; (5) lifetimes revised from
"inferred" to "visible-but-elidable" via binding-anchored bracket channel; (6) `[self]`
denotation settled; (7) the Storage Transparency Principle added as §3.*

*Nothing here is ratified; the remaining Open Questions are real decisions for the
designer. The purpose, as before, is to settle a single model **before** any accepted RFC
is rewritten.*

---

## 1. The finding

The region cluster (RFC-0063 onward) was built on a premise the blog states as a pitch:
the region name does triple duty — **lifetime tag, disjointness proof, allocation
strategy** — and "the lifetime *is* the region, a variable sitting right there in scope."

That premise holds **only when a value lives exactly as long as the region it is
allocated into.** RFC-0066 (Region Pointer Extraction) breaks that: a region-allocated
value can be **moved out or dropped while its region continues** to hold other
allocations. Once that is allowed, a value's lifetime and its region's lifetime are two
different things, and the triple-duty premise stops being literally true. Every
consequence in this report follows from that one crack.

## 2. The reframe

Regions were **always meant to be allocators** — that is literally the blog's pitch ("a
region is an allocation arena with a scope"). The mis-step was not the region concept; it
was RFC-0085/0087 **trying to make lifetimes into pseudo-regions** (`PhantomRegion`, the
universal own-region) so that every binding carried a `Region` for the `Outlives`
machinery and the `[x, y]` sugar to name. Once individual drop (0066) forces value
lifetimes to exist separately from region lifetimes, that move stops being an economy and
starts being the source of every conflation in the cluster.

The honest framing retracts that move and renames accordingly:

- **Allocators are first-class values** — `Heap`, `LocalHeap`, `BumpAlloc`, `AutoAlloc`,
  and scoped allocators, passed explicitly, stored in structs, named in signatures. These
  were called "regions" because they also acted as lifetimes; that role is now separated
  out, so the correct name is the plain one. Nothing about the allocator concept changes —
  only the name and the dropped lifetime duties.
- **Lifetimes are a separate, visible-but-elidable concept.** Every borrow carries a
  lifetime anchor — a binding whose scope bounds the borrow's validity. The anchor is
  named in the bracket channel on borrows: `&[r] T` means "borrow valid while `r` is
  alive," `&[r, t] T` means "valid while both are alive" (intersection). The anchor is
  elidable when unambiguous from context; in complex cases (function signatures, structs)
  it is named explicitly. There is no `'a`-style abstract lifetime variable — lifetime
  anchors are always binding names, concrete things already in scope. At the function
  boundary, anchors are introduced as bracket-channel parameters: `fun foo[r](&[r] T) ->
  &[r] U` universally quantifies `r` over the call, the same way allocator parameters do.

This is the blog's "best of Rust's lifetimes with Zig's Allocator model," taken literally
and named correctly: allocators are the named, passed, first-class thing; lifetimes are
binding-anchored and elidable, never abstract variables.

## 3. The Storage Transparency Principle

**Storage transparency:** a language construct that does not explicitly reference an
allocator or lifetime anchor is implicitly polymorphic over storage. Storage qualifiers
propagate through such constructs without annotation.

This partitions the language surface into two strata:

**Storage-transparent** — no annotation needed, polymorphism is implicit:
- Functions that do not allocate
- Struct definitions that do not own an allocator
- Closures
- Pattern matching and destructuring
- Generic functions and aspect methods
- Operators and control flow
- Type aliases and enums

**Storage-explicit** — the only places where storage annotations appear:
- Allocation expressions: `@[a] expr`
- Borrows with explicit lifetime anchors: `&[r] T`
- Struct allocator ownership declarations: `struct Foo[r]`
- Passing allocators as first-class values: `fun new(alloc: BumpAlloc)`

The programmer only thinks about storage when making a storage decision. Reading a field,
calling a method, transforming a value, matching on an enum — none of these require
storage annotations because none of them make a storage decision. Storage flows through
them the way types flow through a generic function.

This is the key distinction from Rust. Rust makes lifetimes pervasive — every reference
carries one, and complex function signatures accumulate annotations regardless of whether
the function makes any storage decision. Storage transparency inverts this: annotations
concentrate at decision points and are absent everywhere else.

**Storage transparency as a design rule:** any proposed language feature that requires
storage annotations on code that does not allocate or explicitly borrow is a design leak.
The feature should be revised until the annotation is gone.

## 4. Why split, not unify

The prior draft of this report recommended *unified* — keep `LifetimeRegion` as a `Region`
implementor. The whole review since is the evidence that unified does not work:

- Under unified, a "region that does not allocate" (`PhantomRegion`/`LifetimeRegion`)
  stretches the `Region` aspect past its meaning; the rename to `LifetimeRegion` only
  names the stretch, it does not remove it.
- The "two regions on one value" conflation (RFC-0087 Exception B) exists *because* both
  the allocator and the value's duration are forced into the same `Region` category.
- The `&[r]` vs `&[n]` borrow-tag ambiguity exists *because* the tag slot can hold either
  an allocator or a pseudo-region-lifetime and nothing distinguishes them.

Splitting resolves all three by category: an allocator and a lifetime are simply different
kinds of thing, so there is nothing to conflate. Splitting is also more faithful to the
blog's stated goal than the unified over-reading was.

The usual objection to splitting — that the unified model gives errors a concrete
region-in-scope to point at — does not survive: lifetime anchors are binding names in the
bracket channel (`&[x] T`), so diagnostics still say "escapes the lifetime of `x`,"
pointable because `x` is a real binding. No `'a`-style abstract variable is reintroduced;
the rejected RFC-0052 phantom-lifetime failure mode does not return.

## 5. RFCs that retract

**RFC-0085 (`PhantomRegion`) and RFC-0087 (universal own-region)** exist for one reason:
to give every binding *a `Region`* so that `Outlives` and the `[x, y]` sugar have
something to name. Once lifetime anchors are binding names rather than `Region` instances,
that reason disappears. Both retract into the single statement: lifetime anchors are
binding names, not allocator instances.

**RFC-0069 (`SubRegion`)** exists to propagate `Outlives` relationships automatically
when a struct's allocator is nested inside an outer allocator. Since `Outlives` is dropped
(see §6), `SubRegion` has nothing left to propagate. The nesting relationship it expressed
is now handled by the borrow checker directly: if a struct `Foo[r]` is allocated into
allocator `a` (`@[a] Foo::new()`), any borrow `&[r] T` from `Foo`'s allocator is bounded
by `Foo`'s own scope, which is bounded by `a`'s scope — the borrow checker derives this
chain from scope nesting without allocator-level constraints. RFC-0069 retracts entirely.

**`Outlives` as an allocator constraint** retracts from RFC-0063 and RFC-0077. It was
introduced to order allocator scopes so that the region-as-lifetime machinery could reason
about which region outlived which. Allocators do not need to carry this constraint:
ordering relationships between durations are expressed through the lifetime anchor system
(`&[r, t] T`), and the borrow checker reasons about scope nesting from binding structure,
not from declared allocator constraints.

When a reframe retracts four RFCs and one cross-cutting constraint as workarounds for a
single mis-framing, that is a strong signal the frame is correct.

## 6. What stays, what changes

- **Allocators are first-class values.** `Heap`, `LocalHeap`, `BumpAlloc`, `AutoAlloc`,
  scoped allocators. The `Alloc` aspect means "an allocator." It replaces the `Region`
  aspect in name and drops the lifetime obligations that the old name carried.
- **`@[a] T` carries an allocator; `&[r] T` carries a lifetime anchor.** The prefix sigil
  decides the category. Allocator bindings may appear as lifetime anchors — their scope is
  a duration like any other binding's, so `&[a] T` where `a` is an allocator binding means
  "borrow valid for the scope of allocator `a`." This falls out of the general rule; it is
  not a special case.
- **`[x, y]` on borrows is the lifetime anchor syntax.** `&[x, y] T` is a borrow valid
  while both `x` and `y` are alive — intersection of their scopes. Elidable when context
  is unambiguous.
- **Struct allocator declarations use plain `[r]`.** The `own` keyword is dropped. A
  struct declares it holds an allocator with `struct Foo[r] { ... }`; the allocator is
  owned by the struct implicitly — the struct's constructor creates it, the struct's
  destructor drops it. The allocator type may be constrained: `struct Foo[r: BumpAlloc]`.
  The `own` keyword was needed to distinguish "this struct owns a region (allocator)" from
  "this struct is parameterized by a lifetime-region" — a distinction that no longer
  exists once the two roles are separated.
- **`[self]` on borrows** denotes the scope of the `self` binding, uniformly. In
  `&self`/`&mut self` methods, `self` is the borrow, so `&[self] T` chains the caller's
  borrow to the returned reference. In by-value methods the scope ends at return, making
  `&[self] T` as a return type always unsatisfiable (borrow checker catches it, no special
  rule). In associated functions `self` is not in scope — undefined binding error.
- **`Outlives` is dropped** from the allocator layer. Duration ordering between scopes is
  expressed through the lifetime anchor system and derived by the borrow checker from
  binding structure.
- **`SubRegion` is retracted** (§5). The borrow checker derives nesting from scope
  structure.
- **`AutoAlloc` stays**, a first-class allocator specified by semantic contract (scoped,
  non-sendable, sound move-out, observationally equivalent to heap within its scope).
  Renamed from `AutoRegion`.
- **Storage transparency (§3) applies to all language constructs** that do not explicitly
  reference an allocator or lifetime anchor. Functions, closures, pattern matching,
  operators, type aliases, and aspect methods are all storage-polymorphic by default.

## 7. The `[...]` slot: disambiguated by sigil

The `[...]` slot holds two categories, disambiguated by the prefix sigil:

- after `@`, it holds an **allocator** (`@[a] T`, `@[Heap] expr`);
- after `&` / `&mut`, it holds a **lifetime anchor** — a binding name or comma-separated
  list of binding names (`&[r] T`, `&[r, t] T`, `&[self] T`).

The disambiguator is the prefix sigil, which the reader already has in hand. This is the
explicit rule: `@` → allocator, `&`/`&mut` → lifetime anchor. Both positions are elidable
when the context is unambiguous — elision is the default, annotation the exception,
consistent with the Storage Transparency Principle (§3).

**The `&[a]` rule — settled.** Allocator names are allowed in borrow slots. An allocator
binding is a binding; its scope is a duration; `&[a] T` where `a` is an allocator means
"borrow valid for the scope of allocator `a`." The general rule subsumes it.

**The multi-anchor form.** `&[r, t] T` is valid in both the lifetime-anchor and the
function-parameter positions. At the call site, `r` and `t` are bindings; the borrow's
validity is the intersection of their scopes. At the function declaration site, `[r, t]`
in the bracket channel introduces two generic lifetime parameters. The exact grammar for
introducing vs. naming anchors is deferred to grammar refinement; the semantics are
settled.

## 8. Concrete implications, re-read under the split

1. **The allocator tag is not a value-lifetime.** `@[a] T`'s tag is where the value is
   allocated and the disjointness witness; the value's validity duration is tracked by the
   borrow checker through the lifetime anchor system, and may be shorter (individual drop).
2. **Borrows carry lifetime anchors.** A borrow derived from `@[a] T` carries an anchor
   naming the binding that determines its validity scope — not the allocator itself, unless
   the programmer explicitly writes `&[a] T` to tie the borrow to the allocator's scope.
3. **Disjointness and sendability are allocator properties**, preserved unchanged from
   the old region model. The allocator's identity (not the value's lifetime) determines
   whether data can cross fiber/thread boundaries.
4. **Drop order is two-sorted** (move-out drops interleaved with scope-end drops); arena
   teardown stays scope-based, value drops incremental within. Unchanged.
5. **Wellformedness:** a value's lifetime is nested in its allocator's scope — the borrow
   checker enforces this from binding structure without an explicit `Outlives` constraint.
6. **Allocator identity is compile-time**; runtime dispatch is per-kind deallocation
   semantics (`Heap` per-slot free, `BumpAlloc` arena-free-at-scope, etc.).
7. **Storage-transparent constructs are monomorphized over storage at compile time.**
   Storage qualifiers are erased at runtime — a value is a value; the qualifier is a
   compile-time property used for borrow checking and optimization only.

## 9. Underspecified behaviors the model must settle

1. ~~**The `&[r]` rule**~~ — **Settled** (§7): allocator names allowed in borrow slots.
2. ~~**The `[...]` disambiguation rule**~~ — **Settled** (§7): `@` → allocator,
   `&`/`&mut` → lifetime anchor. Grammar formalization deferred.
3. ~~**`Outlives` on durations**~~ — **Dropped** (§5, §6): not part of the allocator
   layer. Duration ordering is expressed through the lifetime anchor system.
4. **Drop order with interleaved move-out** — RFC-0071's rules extended for mid-scope
   drops and already-moved values.
5. ~~**`[self]`'s exact denotation**~~ — **Settled** (§6): scope of the `self` binding,
   uniformly. In `&self`/`&mut self` methods, `self` is the borrow — `[self]` chains the
   caller's borrow to the returned reference. In by-value methods the scope ends at return,
   making `&[self] T` as a return type always unsatisfiable (borrow checker, no special
   rule). In associated functions `self` is not in scope — undefined binding error.
6. **Sendability** — allocators by kind (`Heap` sendable, scoped not); borrows with
   lifetime anchors never sendable. Stated per category.
7. **Lifetime anchor grammar** — introducing vs. naming anchors (function-level generic
   bracket parameters vs. call-site binding references); elision rules. Deferred to
   grammar refinement.

## 10. Blast radius across the cluster

| RFC | Effect of the split |
|---|---|
| 0063 | **Rewritten as "allocators."** `Region` aspect → `Alloc` aspect; `Outlives` dropped from the allocator layer; lifetime duties separated out entirely. |
| 0065 | Elision becomes **lifetime anchor elision** (from `&[r]` to `&`); the rules restate over anchors rather than region names. Elision is the default per §3. |
| 0066 | The trigger; move-out is what forces lifetimes to be shorter than allocator scopes. Borrow tagging becomes the category distinction (`&` = lifetime anchor). |
| 0067 | Reference types carry **lifetime anchors**; `&[r]` rule settled (§7). Storage-transparent by default per §3. |
| 0068 | `[own r]` → **`[r]`**; `own` dropped. Struct allocator declarations are plain bracket parameters. |
| 0069 | **Retracted** (§5): `SubRegion` was `Outlives` propagation for allocators; both are dropped. |
| 0071 | Drop order extended for interleaved move-out and moved values. |
| 0073 | `AutoRegion` → **`AutoAlloc`**, first-class allocator, spec'd by semantic contract (§6). |
| 0077 | Wellformedness/variance restate over **allocator scopes** only; value-lifetime constraints fall to the borrow checker via anchor structure, not declared `Outlives`. |
| 0085 | **Retracted** (§5). |
| 0086 | `[x, y]` sugar **survives**, reinterpreted as lifetime anchor intersection on borrows. |
| 0087 | **Retracted** (§5). |

This is a larger change than the "two-level model" draft: it touches 0063 fundamentally,
**retracts 0069, 0085, and 0087**, drops `Outlives` from the allocator layer, and renames
throughout. It also re-bases the implementation plan in
`rfc-implementation-breakdown-2026-07-01.md`: Phase 3 (region cluster) is **pending the
model settle**; the static type-system cluster (Phase 1) is unaffected and proceeds
independently.

## 11. Recommended process and open questions

**Process.** (1) Agree this report's split model. (2) Ratify it as a short foundational
RFC — a new RFC-0088 ("Allocators and Lifetimes") that states the split model and the
Storage Transparency Principle, which the cluster then conforms to; explicitly mark 0069,
0085, 0087 retracted. (3) Sweep the cluster mechanically against the ratified model. (4)
Re-base the implementation breakdown's Phase 3. As before, a position report is faster to
iterate on than RFC rewrites; do not start the sweep until the model is signed off.

**Open questions for the designer.**

- ~~**Confirm the split.**~~ **Decided:** allocators first-class, lifetimes
  visible-but-elidable via binding-anchored bracket channel.
- ~~**The `&[r]` rule.**~~ **Decided** (§7): allowed; allocator bindings are bindings.
- ~~**The `[...]` disambiguation.**~~ **Decided** (§7): `@` → allocator, `&`/`&mut` →
  lifetime anchor.
- ~~**`Outlives` as duration-general.**~~ **Dropped** (§5): not part of the allocator
  layer; duration ordering is the borrow checker's concern via anchor structure.
- ~~**`[own r]` replacement syntax.**~~ **Decided** (§6): plain `[r]`; `own` dropped.
- ~~**`[self]`'s exact denotation.**~~ **Decided** (§6, §9 item 5): scope of the `self`
  binding, uniformly across all receiver forms.
- **Drop order with interleaved move-out** — RFC-0071 extension. Remaining semantic open
  question.
- **Sendability** — per-category statement (allocators by kind, borrows never sendable).
- **Lifetime anchor grammar** — elision rules; function-level generic anchor parameters
  vs. call-site binding references. Deferred to grammar refinement.
- **Ratification vehicle** — new RFC-0088, or an amendment that reframes RFC-0063 and
  marks 0069/0085/0087 retracted?

The model is now internally consistent: allocators are allocators, lifetimes are
binding-scoped anchors, storage transparency means most code carries no storage
annotations at all, and the annotation burden concentrates exactly at the points where
storage decisions are actually being made.
