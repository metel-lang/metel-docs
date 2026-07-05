---
id: lifetimes-vs-regions-2026-07-02
title: "Allocators first-class, lifetimes visible — the split model"
type: report
created_date: '2026-07-02'
updated_date: '2026-07-05'
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
"inferred" to "visible-but-elidable" via binding-anchored syntax; (6) `[self]` denotation
settled; (7) Storage Transparency Principle added; (8) all semantic open questions
settled; (9) syntactic channel reassignment: allocators move to the value channel `()` with
`@` prefix (they are values), lifetime anchors move to the type-parameter channel `<>` with
`&` prefix, `[]` freed for capture lists, multi-anchor form deferred.*

*Updated 2026-07-05: mutable borrow syntax settled — `&r mut T` (anchor groups with `&`,
`mut` follows); anchors are type-level only, expression position always uses `&val` /
`&mut val` with anchor inferred from context.*

*Nothing here is ratified; the remaining open question is the ratification vehicle. The
purpose, as before, is to settle a single model **before** any accepted RFC is rewritten.*

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
  out, so the correct name is the plain one. Because allocators are values, they live in
  the **value channel** `()` with the `@` prefix: `fun build(@a: BumpAlloc, val: T) ->
  @a Node<T>`. Elision applies when exactly one allocator is in scope; `@` alone suffices.
- **Lifetime anchors are a separate, visible-but-elidable concept.** Every borrow carries
  a lifetime anchor — a binding whose scope bounds the borrow's validity. Anchors are
  named directly after the `&` sigil in type position: `&r T` (immutable) and `&r mut T`
  (mutable) — the anchor groups with `&`, and mutability qualifies the reference after.
  Because lifetime anchors are a form of compile-time parameter (like type parameters),
  they are declared in the **type-parameter channel** `<>` with the `&` prefix:
  `fun foo<&r>(&r T) -> &r mut U`. There is no `'a`-style abstract variable — anchor
  names are always binding names, concrete things in scope. Elision covers the common
  cases; explicit `<&r>` declarations appear only when the anchor relationship is
  ambiguous. **Anchors are a type-level concept only** — in expression position you
  write `&val` and `&mut val`; the anchor is inferred from the expected type.

This is the blog's "best of Rust's lifetimes with Zig's Allocator model," taken literally
and named correctly: allocators are values passed through the value channel; lifetime
anchors are compile-time parameters declared in the type channel.

## 3. The Storage Transparency Principle

**Storage transparency:** a language construct that does not explicitly reference an
allocator or lifetime anchor is implicitly polymorphic over storage. Storage qualifiers
propagate through such constructs without annotation.

This partitions the language surface into two strata:

**Storage-transparent — no annotation needed:**
- Functions that do not allocate
- Struct definitions without owned allocators
- Closures, pattern matching, operators, type aliases

**Storage-explicit — the only places where storage annotations appear:**
- Allocation expressions: `@a expr` (or `@expr` with elision)
- Explicit borrow anchors: `&r T`
- Struct allocator ownership: `struct Foo(@a: BumpAlloc) { ... }`
- Passing allocators as values: `fun new(@a: BumpAlloc, ...)`

The programmer only thinks about storage when making a storage decision. Storage flows
through all other constructs the way types flow through a generic function.

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
- Borrow-tag ambiguity exists *because* the tag slot could hold either an allocator or a
  pseudo-region-lifetime with nothing distinguishing them.

Splitting resolves all three by category: an allocator and a lifetime are simply different
kinds of thing, so there is nothing to conflate. The syntactic split reinforces the
semantic one: allocators in `()`, lifetime anchors in `<>`.

The usual objection to splitting — that the unified model gives errors a concrete
region-in-scope to point at — does not survive: lifetime anchors are binding names
(`&r T`), so diagnostics still say "escapes the lifetime of `r`," pointable because `r`
is a real binding. No `'a`-style abstract variable is reintroduced; the rejected RFC-0052
phantom-lifetime failure mode does not return.

## 5. RFCs that retract

**RFC-0085 (`PhantomRegion`) and RFC-0087 (universal own-region)** exist for one reason:
to give every binding *a `Region`* so that `Outlives` and the `[x, y]` sugar have
something to name. Once lifetime anchors are binding names rather than `Region` instances,
that reason disappears. Both retract into the single statement: lifetime anchors are
binding names, not allocator instances.

**RFC-0069 (`SubRegion`)** exists to propagate `Outlives` relationships automatically
when a struct's allocator is nested inside an outer allocator. Since `Outlives` is dropped
(see §6), `SubRegion` has nothing left to propagate. The nesting relationship it expressed
is now handled by the borrow checker directly: if a struct `Foo(@a)` is allocated via
`@b Foo::new(arena_a)`, any borrow `&a T` from `Foo`'s allocator is bounded by `Foo`'s
own scope, which is bounded by `b`'s scope — the borrow checker derives this chain from
scope nesting without allocator-level constraints. RFC-0069 retracts entirely.

**`Outlives` as an allocator constraint** retracts from RFC-0063 and RFC-0077. It was
introduced to order allocator scopes so that the region-as-lifetime machinery could reason
about which region outlived which. Allocators do not need to carry this constraint:
ordering relationships between durations are expressed through the lifetime anchor system
and the borrow checker's scope analysis.

When a reframe retracts four RFCs and one cross-cutting constraint as workarounds for a
single mis-framing, that is a strong signal the frame is correct.

## 6. What stays, what changes

- **Allocators are first-class values.** `Heap`, `LocalHeap`, `BumpAlloc`, `AutoAlloc`,
  scoped allocators. The `Alloc` aspect means "an allocator." Allocator parameters are
  declared in the value channel with `@` prefix: `(@a: BumpAlloc)`. Allocation
  expressions use `@a expr`; elided to `@expr` when exactly one allocator is in scope.
- **Lifetime anchors in `<>` with `&` prefix.** `<&r>` at declaration, `&r T` at use.
  Anchors are binding names — concrete things already in scope. The `&` prefix
  distinguishes lifetime anchor parameters from type parameters within `<>`.
- **Lifetime ordering bounds** use `: &s` in the `<>` declaration: `<&s, &t: &s>` means
  t outlives s, matching the established `:` bound convention. Needed only when anchors
  are structurally unrelated at the call site.
- **Struct allocator ownership uses primary constructor syntax.** `struct Foo(@a: BumpAlloc)`
  brings `a` into scope for field types: `struct Foo(@a: BumpAlloc) { data: @a [u8] }`.
  The allocator is created at construction and dropped with the struct. This replaces the
  old `[own r]` / `[r]` bracket syntax.
- **Scoped allocator closures** use the value channel naturally: `BumpAlloc::scoped((@a)
  -> { @a Node { val: 1 } })`. `@a` is a closure parameter. No special lambda syntax.
- **`&self` on borrows** — `self` in `&self`/`&mut self` methods is a binding; `&self T`
  as a return type means "borrow valid while `self` is alive." Works without any explicit
  `<&self>` declaration because `self` is always in scope in method bodies.
- **`[]` freed for capture lists.** Closures use `[x, y]` for capture lists without
  conflict. The bracket channel is no longer a storage-parameter channel.
- **`Outlives` is dropped** from the allocator layer. Duration ordering is expressed
  through lifetime anchor bounds in `<>` and derived by the borrow checker from scope
  nesting.
- **`SubRegion` is retracted** (§5). The borrow checker derives nesting from scope
  structure.
- **`AutoAlloc` stays**, renamed from `AutoRegion`, a first-class allocator specified by
  semantic contract (scoped, non-sendable, sound move-out, observationally equivalent to
  heap within its scope).
- **Storage transparency (§3) applies to all constructs** that do not explicitly
  reference an allocator or lifetime anchor.

## 7. Channel assignments

The language has three parameter channels, each with a clear semantic category:

| Channel | Contents | Syntax |
|---|---|---|
| `<>` | Type parameters and lifetime anchor parameters | `<T>`, `<&r>`, `<&r, &s: &r>` |
| `()` | Value parameters and allocator parameters | `(x: T)`, `(@a: BumpAlloc)` |
| `[]` | Capture lists (closures) | `[x, y]` |

At use sites, the sigil alone carries the meaning — no brackets needed:
- `@a T` — value of type T allocated in allocator `a`
- `@T` — same, allocator elided (one in scope)
- `&r T` — immutable borrow of T anchored to binding `r`
- `&r mut T` — mutable borrow of T anchored to `r`; anchor groups with `&`, `mut` follows
- `&T` / `&mut T` — anchor elided (one input anchor, or `self` wins)

**Anchors are type-level only.** In expression position, write `&val` or `&mut val`;
the anchor is inferred from the expected type. Explicit anchor annotations never appear
on expressions.

**Allocator elision rule:** if exactly one allocator is in scope, `@` without a name
suffices. When a second allocator enters scope, both must be named.

**Lifetime anchor elision rules:**
1. Each elided `&` in input position gets a distinct fresh anchor
2. If `&self`/`&mut self` is present, the elided output anchor is `self`'s anchor
3. If exactly one input anchor exists, the elided output anchor is that anchor
4. Otherwise — compile error, explicit `<&r>` declaration required

**Lifetime ordering bounds** in `<>`: `<&s, &t: &s>` declares anchors `s` and `t` where
`t` outlives `s`. The right-hand side is the shorter-lived anchor. Needed only when two
anchors arrive from outside with no structural relationship the borrow checker can derive.

**Multi-anchor borrows** (`&r, s T` — borrow valid while both `r` and `s` are alive) are
deferred. The multi-anchor form is needed only for the "return one of several borrows"
case, which is uncommon in practice. Deferral does not affect any other part of the model.

## 8. Concrete implications, re-read under the split

1. **The allocator is not a value-lifetime.** `@a T`'s allocator tag is where the value
   is allocated and the disjointness witness; the value's validity duration is tracked by
   the borrow checker through lifetime anchors, and may be shorter (individual drop).
2. **Borrows carry lifetime anchors.** A borrow derived from `@a T` carries an anchor
   naming the binding that determines its validity scope.
3. **Disjointness and sendability are allocator properties**, preserved unchanged from
   the old region model. The allocator's identity (not the value's lifetime) determines
   whether data can cross fiber/thread boundaries.
4. **Drop order:** values drop at the earliest of (a) explicit `drop(x)` — destructor
   runs immediately in program order; (b) move-out — obligation transfers to recipient;
   (c) scope end — reverse declaration order among surviving values. Allocator teardown
   follows all value-level drops at the same scope boundary. Conditional move of `T: Drop`
   requires all branches to resolve the obligation.
5. **Wellformedness:** a value's lifetime is nested in its allocator's scope — the borrow
   checker enforces this from binding structure without an explicit `Outlives` constraint.
6. **Allocator identity is compile-time**; runtime dispatch is per-kind deallocation
   semantics (`Heap` per-slot free, `BumpAlloc` arena-free-at-scope, etc.).
7. **Storage-transparent constructs monomorphize over storage at compile time.** Storage
   qualifiers are erased at runtime — a value is a value; the qualifier is a compile-time
   property used for borrow checking and optimization only.

## 9. Underspecified behaviors — all settled

1. ~~**The borrow-tag rule**~~ — **Settled** (§7): `&r T` at use sites; `<&r>` at
   declaration. Allocator bindings are bindings; `&a T` where `a` is an allocator means
   "borrow valid for the scope of allocator `a`."
2. ~~**Channel disambiguation**~~ — **Settled** (§7): `<>` for types and lifetime
   anchors, `()` for values and allocators, `[]` for capture lists.
3. ~~**`Outlives` on durations**~~ — **Dropped** (§5, §6): not part of the allocator
   layer. Duration ordering is expressed through lifetime anchor bounds `<&t: &s>` and
   the borrow checker's scope analysis.
4. ~~**Drop order with interleaved move-out**~~ — **Settled** (§8 item 4): earliest of
   explicit drop, move-out, or scope end; allocator teardown last; conditional move of
   `T: Drop` must resolve in all branches.
5. ~~**`[self]` / `&self` denotation**~~ — **Settled** (§6): `&self T` as a return type
   means "borrow valid while `self` is alive." `self` is always in scope in method bodies;
   no explicit `<&self>` declaration needed. In by-value methods the scope ends at return,
   making `&self T` as a return type always unsatisfiable (borrow checker, no special
   rule). In associated functions `self` is not in scope — undefined binding error.
6. ~~**Sendability**~~ — **Settled:** `Heap` sendable; `LocalHeap`, `BumpAlloc`,
   `AutoAlloc`, and scoped allocators not. `@a T` sendable iff `a` and `T` are both
   `Send`. Borrows `&r T` never sendable — scopes are per-fiber. No `Sync` distinction
   needed.
7. ~~**Lifetime anchor grammar**~~ — **Settled** (§7): `<&r>` declaration, `&r T`
   (immutable) and `&r mut T` (mutable) at use; anchor groups with `&`, `mut` follows.
   Anchors are type-level only — expression position always uses `&val` / `&mut val`,
   anchor inferred from expected type. Optional `@`/`&` prefix within `<>` when mixing
   kinds: required when declaration contains both type params and anchor params or
   anchors and ordering bounds. Elision rules as stated in §7. Ordering bounds:
   `<&s, &t: &s>` — t outlives s. Multi-anchor form deferred (§7).

## 10. Blast radius across the cluster

| RFC | Effect of the split |
|---|---|
| 0063 | **Rewritten as "allocators."** `Region` aspect → `Alloc` aspect; `Outlives` dropped; allocators move to value channel. |
| 0065 | Elision restated: allocator elision (single `@`), anchor elision (three rules in §7). |
| 0066 | The trigger; move-out forces lifetimes shorter than allocator scopes. |
| 0067 | Reference types carry lifetime anchors; `&r T` syntax at use, `<&r>` at declaration. |
| 0068 | `[own r]` → **primary constructor** `(@a: AllocType)`; `own` and bracket channel dropped. |
| 0069 | **Retracted** (§5): `SubRegion` was `Outlives` propagation; both dropped. |
| 0071 | Drop order extended for interleaved move-out and moved values. |
| 0073 | `AutoRegion` → **`AutoAlloc`**, first-class allocator, semantic contract unchanged. |
| 0077 | Wellformedness restated over allocator scopes only; value-lifetime constraints are borrow-checker-derived. |
| 0085 | **Retracted** (§5). |
| 0086 | `[x, y]` sugar reinterpreted as `<&x, &y>` lifetime anchor parameter declarations; multi-anchor borrow form deferred. |
| 0087 | **Retracted** (§5). |

Phase 3 of `rfc-implementation-breakdown-2026-07-01.md` remains **pending model
ratification**. Phase 1 (static type-system cluster) is unaffected and proceeds
independently.

## 11. Recommended process and open questions

**Process.** (1) Ratify this report's model as RFC-0088 ("Allocators and Lifetimes"):
allocators = first-class values in the value channel, lifetime anchors = `<>` channel
with `&` prefix, Storage Transparency Principle as a named constraint. Mark 0069, 0085,
0087 retracted. (2) Sweep the cluster against the ratified model. (3) Re-base the
implementation breakdown's Phase 3.

**Open questions for the designer.**

- ~~**Confirm the split.**~~ **Decided.**
- ~~**Borrow-tag rule.**~~ **Decided** (§7).
- ~~**Channel disambiguation.**~~ **Decided** (§7): `<>` types/anchors, `()` values/allocators, `[]` captures.
- ~~**`Outlives` as duration-general.**~~ **Dropped** (§5).
- ~~**Struct allocator syntax.**~~ **Decided** (§6): primary constructor `(@a: AllocType)`.
- ~~**`&self` denotation.**~~ **Decided** (§6, §9 item 5).
- ~~**Drop order.**~~ **Decided** (§8 item 4, §9 item 4).
- ~~**Sendability.**~~ **Decided** (§9 item 6).
- ~~**Lifetime anchor grammar.**~~ **Decided** (§7, §9 item 7).
- **Multi-anchor borrows** — deferred (§7). No other part of the model depends on this.
- **Ratification vehicle** — new RFC-0088 vs. amendment that reframes RFC-0063.

All semantic questions are settled. The model is internally consistent: allocators are
values in the value channel, lifetime anchors are compile-time parameters in the type
channel, storage transparency means most code carries no storage annotations at all, and
the annotation burden concentrates exactly at the points where storage decisions are
actually being made.
