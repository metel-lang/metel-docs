---
id: rfc-0073
title: "AutoRegion"
date: '2026-06-29'
---

> **Status — draft.** Depends on RFC-0063 (Region Handles), RFC-0065 (Region
> Ergonomics), RFC-0066 (Region Pointer Extraction), RFC-0071 (Ownership and Move
> Semantics), and RFC-0072 (Negative Bounds). Introduces `AutoRegion` as a fourth
> stdlib region that provides scoped bump allocation with automatic destructor tracking,
> filling the gap identified in RFC-0066 §2.2.3 (Option B — deferred).

## Summary

The three existing stdlib regions cover three distinct allocation strategies:

| Type | Lifetime | Move-out | Sendable |
|---|---|---|---|
| `Heap` | Indefinite | Always safe | Yes |
| `LocalHeap` | Indefinite, thread-local | Always safe | No |
| `BumpRegion` | Scoped, bump arena | `T: !Drop` only | No |

One slot is empty: a scoped region where move-out is always safe — where the
`T: !Drop` restriction from RFC-0066 §2.2 does not apply. `AutoRegion` fills it.

`AutoRegion` is a bump allocator that additionally maintains a **drop list** — a
per-region record of live allocations that carry `Drop` implementations. When the
region is dropped, it calls `Drop::drop` on each tracked live slot before reclaiming
the backing memory. When a value is moved out of the region, its entry is removed from
the drop list so the destructor is not called twice. Values with no `Drop` impl are
never entered into the drop list; for a region whose allocations are all `T: !Drop`,
`AutoRegion` is observationally equivalent to `Region`.

The programmer uses `AutoRegion` when they want scoped lifetime tracking without
committing to a specific allocator strategy or reasoning about `T: !Drop` constraints.
The lifetime tag, SubRegion relationships, Outlives bounds, and borrow checking all work
identically to any other scoped region.

---

## Motivation

### The RFC-0066 gap

RFC-0066 §2.2.3 identifies three options for move-out from non-heap regions when `T:
Drop`:

- **Option A** — restrict move-out to `T: !Drop`. Recommended for `BumpRegion` (bump
  arena). Zero runtime overhead; double-drop hazard is statically impossible.
- **Option B** — allocator-tracked destruction. Maintain a live-allocation list; remove
  entries on move-out; call remaining destructors at region drop. Fully safe for all
  `T`; some per-Drop-allocation bookkeeping overhead.
- **Option C** — caller-driven (unsafe). Rejected.

RFC-0066 adopts Option A for the stdlib `BumpRegion` and defers Option B: "If move-out of
`Drop` types from scoped arenas proves necessary in practice, the drop-list approach
becomes worth its overhead. Deferred until profiling data from realistic workloads is
available."

`AutoRegion` is Option B, promoted to a first-class stdlib type. Rather than retrofitting
`BumpRegion` with optional drop tracking, it is a separate type with clearly-stated semantics:
bump allocation, always-safe move-out, destructor-calling drop.

### The allocation-decision burden

The existing stdlib regions require a deliberate choice: `BumpRegion` for short-lived
scratch data that never holds external resources; `Heap` for anything long-lived or that
needs to cross fiber boundaries. That choice is meaningful and the explicit form is
correct when the programmer cares about it. When they do not — when they want scoped
lifetime grouping and use-after-free prevention but have no opinion on the backing
allocator — there is currently no type to reach for. `AutoRegion` is that type.

---

## Design

### The region allocator interface

`AutoRegion` implements the region allocator interface established in RFC-0063 §1.1:

```metel
impl Region for AutoRegion {
    type AllocationError = !;
}
```

`AllocationError = !` declares the region infallible: `@[r] expr` has type `@[r] T`,
not `Perhaps<@[r] T, _>`, and OOM panics rather than returning an error. This matches
`BumpRegion`, `Heap`, and `LocalHeap`.

### Creation

Two forms, mirroring `BumpRegion` (RFC-0063 §1):

**Closure-scoped** — the arena is created and freed within a closure boundary:

```metel
AutoRegion::scoped([r]() -> {
    let node = @[r] Node { val: 1, next: null };
    process(&node);
});
// r dropped here; destructors for tracked slots called; memory reclaimed
```

**Variable-scoped** — the arena is bound to a named variable:

```metel
let r = AutoRegion::new();
let node = @[r] Node { val: 1, next: null };
process(&node);
drop(r);   // or implicit at end of scope
```

`AutoRegion::scoped` is equivalent to a block with an implicit `drop(r)` at the end,
identical to `BumpRegion::scoped` in RFC-0063 §1.

### Drop list

Every `@[r] T` allocation is recorded at allocation time:

- If `T: Drop`: an entry `(slot_ptr, drop_fn)` is appended to the drop list, where
  `drop_fn` is a pointer to `T::drop`.
- If `T: !Drop` (RFC-0072): no entry is added. The backing memory is reclaimed at
  bulk-free without any destructor call.

When `r` is dropped:

1. Iterate the drop list in reverse allocation order (consistent with RFC-0071 §5
   scope drop ordering).
2. For each entry still in the list, call `drop_fn(slot_ptr)`.
3. Reclaim the entire backing memory in O(1).

Step 3 is still a bulk free — the bump arena's efficiency advantage is preserved for
the memory reclamation step. Step 2 is O(n) in the number of `T: Drop` allocations,
which is unavoidable: destructors must run regardless of allocator.

### Move-out removes the drop-list entry

When a value is moved out of the region — via type-directed move-out or type-ascription
(RFC-0066 §2, §3) — the slot's drop-list entry is removed before the value is handed
to the caller:

```metel
let ptr: @[r] FileHandle = @[r] FileHandle::open("data.txt");
let handle: FileHandle = ptr;   // move-out; drop-list entry for this slot removed
                                 // FileHandle::drop will run when `handle` drops,
                                 // not when `r` drops
```

The value is now owned by the caller's binding. Its destructor will run through normal
ownership when the caller's binding goes out of scope. The region no longer tracks it.

If the move-out type is `T: !Drop`, no drop-list entry was ever created; there is
nothing to remove.

### Copy extraction

`T: Copy` extraction is unchanged from RFC-0066 §2.2.1: the slot is copied out, the
original slot is intact, and the drop-list entry (if any — a `Copy` type cannot have
`Drop` by RFC-0071 §4) is unaffected. In practice, since `Copy` implies `!Drop`,
`Copy` types are never in the drop list.

### Sendability

`AutoRegion` is a scoped region. Its tag follows the existing rule from RFC-0063 §4:
a scoped tag is never sendable. `@[r] T` where `r` is an `AutoRegion` binding cannot
cross a fiber boundary. If sendability is required, `@[Heap] T` is the correct choice.

### Interaction with struct-owned regions (RFC-0068)

`[own r]` struct declarations may use `AutoRegion` as the backing allocator. Since
`AutoRegion::AllocationError = !`, the constraint that `[own r]` desugars to an
infallible region is satisfied. The struct's constructor creates the `AutoRegion`; the
struct's destructor drops it, which runs the drop list and reclaims memory.

```metel
struct Cache[own r] {
    entries: @[r] List<CacheEntry>,   // CacheEntry may implement Drop
}
```

With `BumpRegion` as the backing allocator (current behaviour), `CacheEntry: Drop` would
require either `@[Heap] CacheEntry` fields or careful API design to avoid move-out.
With `AutoRegion` as the backing allocator, `CacheEntry: Drop` is handled automatically:
destructors run when the `Cache` drops, without the programmer managing it.

The backing allocator for `[own r]` is the subject of a separate open question; this
RFC does not resolve how the programmer specifies which allocator backs an `[own r]`
field. Until that question is resolved, `[own r]` continues to desugar to `BumpRegion`. The
relationship described above is illustrative of the intended future composition.

### Interaction with SubRegion (RFC-0069)

`AutoRegion` participates in SubRegion typing identically to any other region. When a
struct with `[own r]` backed by `AutoRegion` is allocated into an outer region `R`, the
compiler assigns `r: SubRegion<R>` — `R: Outlives<r>` is derived automatically. The
drop list is scoped to `r`; destructors run before `r`'s backing memory is reclaimed,
which occurs before `R` drops.

---

## The four stdlib regions

| Type | Lifetime | Drop behaviour | Move-out | Sendable |
|---|---|---|---|---|
| `Heap` | Indefinite | Individual `Drop::drop` on last owner | Always safe | Yes |
| `LocalHeap` | Indefinite, thread-local | Individual `Drop::drop` on last owner | Always safe | No |
| `BumpRegion` | Scoped, bump arena | Bulk free; no `Drop::drop` per slot | `T: !Drop` only (RFC-0072) | No |
| `AutoRegion` | Scoped, bump arena + drop list | Drop list then bulk free | Always safe | No |

---

## Alternatives considered

### Retrofit `BumpRegion` with an opt-in drop-tracking mode

Adding a flag or type parameter to `BumpRegion` — e.g. `BumpRegion<TrackDrops>` — would unify
the two scoped region types but introduces a type-level distinction that is invisible
in bracket parameters unless explicitly annotated. Separate named types (`BumpRegion`,
`AutoRegion`) are clearer at use sites and in signatures.

### Make `AutoRegion` the default scoped region, retire `Region`

`AutoRegion` is strictly more capable than `BumpRegion` (it accepts all `T` without
restriction). One option is to retire `BumpRegion` and use `AutoRegion` everywhere.

This is rejected because the drop-list overhead — while small per allocation — is not
zero, and `BumpRegion`'s zero-overhead guarantee is its value proposition for
performance-sensitive code. The `T: !Drop` restriction on `BumpRegion` is not a bug; it is
the statically-enforced contract that makes the guarantee hold. Programmers who want
zero overhead can still choose `BumpRegion` and accept the restriction. `AutoRegion` is the
ergonomic alternative, not a replacement.

### Compiler-inferred allocator selection

An alternative to `AutoRegion` is a special `auto` region kind that the compiler backs
with the best allocator based on escape analysis: bump arena when possible, heap when
values escape. This is a language extension (a new region kind) rather than a stdlib
type, and requires the compiler to decide sendability, which is currently determined
entirely by the tag. A stdlib type has no such complications — it fits into the existing
system with no new language rules.

---

## Unresolved questions

1. **Drop list data structure.** The drop list must support O(1) removal (for
   move-out) and O(n) forward-or-reverse iteration (for region drop). A singly-linked
   list embedded into the bump arena's backing memory satisfies both: each `T: Drop`
   allocation is followed immediately by a node containing the drop function pointer and
   a pointer to the next node. Move-out patches the previous node's next pointer.
   Whether this embedded-list approach or a separate side-allocation is preferable is
   deferred to the implementation RFC.

2. **Drop ordering for `AutoRegion`.** RFC-0071 §5 specifies reverse-declaration order
   for scope bindings and forward-declaration order for struct fields. The drop list
   could be iterated in reverse allocation order (approximating reverse-declaration
   order for local bindings) or forward order. Reverse is more consistent with RFC-0071
   and less likely to surprise programmers who reason about destructor ordering. Formal
   resolution deferred.

3. **Backing allocator for `[own r]` structs.** As noted above, how the programmer
   specifies whether `[own r]` uses `Region` or `AutoRegion` is an open question not
   addressed here.

---

## References

- RFC-0063 (Region Handles) — region allocator interface; `@[r] expr`; bracket channel;
  sendability rules; `BumpRegion::scoped` and `BumpRegion::new()` creation forms.
- RFC-0065 (Region Ergonomics) — `@`-position elision; call-site inference; both apply
  to `AutoRegion` identically.
- RFC-0066 (Region Pointer Extraction) — Option B (allocator-tracked destruction) that
  this RFC promotes to a first-class stdlib type; §2.2.1 `T: Copy` extraction unchanged;
  §2.2.3 `T: Drop` move-out now fully resolved for `AutoRegion`.
- RFC-0068 (Struct-Owned Regions) — `[own r]` interaction; illustrative future
  composition with `AutoRegion` as backing allocator.
- RFC-0069 (Sub-Region Typing) — `SubRegion<R>` applies to `AutoRegion` without change.
- RFC-0071 (Ownership and Move Semantics) — `Drop` aspect; `Copy`/`Drop` mutual
  exclusion; drop ordering that governs drop-list iteration order.
- RFC-0072 (Negative Bounds) — `T: !Drop` used to determine whether a drop-list entry
  is created at allocation time.
