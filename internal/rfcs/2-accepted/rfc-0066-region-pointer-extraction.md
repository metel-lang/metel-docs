---
id: rfc-0066
title: "Region Pointer Extraction"
date: '2026-06-27'
---

> **Status — accepted.** Depends on RFC-0063 (Region Handles) and RFC-0065
> (Region Ergonomics). Addresses the gap identified in RFC-0063 §8.1: how a caller obtains
> a plain `T` or `&T` from an `@[r] T` region pointer, and what the destructor semantics
> are in each case.

## Summary

`@[r] expr` allocates `T` into region `r`; extraction is the inverse. Given `ptr: @[r] T`,
two families of operations are available:

- **Borrow-deref** — obtain `&T` or `&mut T` without consuming `ptr`; works for any region
  kind and any `T`.
- **Move-out** — obtain `T` by consuming `ptr`; always safe for `@[Heap] T`, constrained
  by `T`'s Drop status for scoped `@[r] T`.

The asymmetry between region kinds follows directly from their Drop semantics: heap regions
free slots individually; scoped bump arenas reclaim memory in bulk, which creates a
double-drop hazard when a slot has been vacated by move-out.

---

## Motivation

Functions and methods take plain `T` or `&T`. A caller holding `@[r] List<T>` cannot pass
it to such a call site without extracting the value first. The extraction forms this RFC
specifies are the complement to the `@[r] expr` allocation form: together they define the
full lifecycle of a region-allocated value.

---

## 1. Borrow-deref

Borrow-deref obtains a temporary loan of the value without consuming the region pointer.
It is unconditional — no restriction on region kind or `T`:

```metel
let ptr = @[r] Node { val: 1, next: null };

let v: &Node     = &ptr;     // shared borrow — &[r] Node, coerces to &Node
let v: &mut Node = &mut ptr; // exclusive borrow
// ptr is still live after the borrows expire
```

The borrow checker enforces that no borrow outlives `ptr`, and that a `&mut` borrow is
exclusive. No new rules are needed beyond the existing borrow semantics. Auto-deref handles
field access and method dispatch through region pointers (RFC-0067 §3–4).

---

## 2. Move-out

Move-out consumes `ptr` and returns `T`. Safety depends on the region kind.

### 2.1 `@[Heap] T` — always safe

The heap tracks allocations individually. When `ptr` is consumed by move-out, the heap
slot is freed without calling `T::drop` again — `T` is now owned elsewhere and will be
dropped by its new owner. This is exactly symmetric with `@[Heap] expr` allocation:

```metel
let ptr = @[Heap] String { … };
let s = ptr: String;  // type ascription drives move-out; heap slot freed; ptr consumed
// s is dropped normally when it goes out of scope
```

Move-out from `@[Heap] T` is safe for all `T`, including `T: Drop`.

### 2.2 Non-heap `@[r] T` — constrained by allocator drop strategy

Move-out safety for non-heap regions depends on how the allocator handles drops, not on
whether the region is scoped. Two strategies are possible:

**Bulk-deallocating allocators** reclaim all backing memory in one operation when the region
drops, without calling individual destructors per slot. A slot vacated by move-out is
*orphaned* — the allocator cannot distinguish it from a live slot. If `T` has a `Drop` impl,
the allocator would invoke `T::drop` on the orphaned slot at drop time, but `T::drop` has
already been called by the new owner — undefined behaviour. The stdlib `BumpRegion` (bump arena)
is a bulk-deallocating allocator.

**Individually-tracking allocators** maintain a record of live allocations and their
destructor status. Move-out removes the entry; the allocator's own drop calls destructors
only for entries still in the list. Such an allocator supports move-out for all `T`,
including `T: Drop`, at the cost of per-allocation bookkeeping.

The constraints in §2.2.1–2.2.3 apply to bulk-deallocating allocators. A custom region type
that implements individual tracking does not impose the `T: !Drop` restriction on its callers.

#### 2.2.1 `T: Copy`

A `Copy` type is extracted by copy, not move. The slot is not vacated; `ptr` remains
valid:

```metel
let ptr = @[r] Point { x: 1, y: 2 };
let p = ptr: Point;   // type ascription copies Point out — ptr still valid, slot intact
```

Copy extraction works for any region kind and imposes no Drop-related constraint.

#### 2.2.2 `T: !Drop` (non-Copy, no Drop impl)

If `T` has no `Drop` impl — expressed as the negative bound `T: !Drop` — move-out is safe.
The slot is orphaned, but when the arena drops it reclaims raw memory without calling any
destructor. Nothing leaks; nothing runs twice:

```metel
let ptr = @[r] Pair { a: 1, b: 2 };  // Pair has no Drop impl
let p = ptr: Pair;                     // type ascription moves out — safe; slot orphaned
// arena frees the raw memory on drop, no destructor to call
```

#### 2.2.3 `T: Drop`

Move-out creates a double-drop hazard. Three options resolve this:

**Option A — restrict move-out to `T: !Drop` (recommended for bulk-deallocating
allocators).** Move-out from `@[r] T` is a compile error when `T: Drop`. The type system
enforces the restriction statically via the negative bound; no runtime bookkeeping. Types
that hold external resources should use `@[Heap] T`, which supports move-out for all `T`.

**Option B — allocator-tracked destruction.** The allocator maintains a live-allocation
list with destructor entries. Move-out removes the entry; the allocator's own drop only
calls destructors for entries still in the list. Fully safe for all `T`; the allocator
opts into this by implementing the tracking. A custom region type may implement Option B
natively without language changes, making it transparent to callers.

**Option C — caller-driven.** Move-out requires the caller to explicitly run `T::drop`
before vacating the slot. Unsafe; inconsistent with Metel's safe-by-default posture.

Option A is the recommended starting point for the stdlib `BumpRegion` (bump arena). Arena
workloads typically deal in plain data types, not resource-holding ones. The restriction is
zero-cost, statically visible at the call site, and the escape valve — use `@[Heap] T` — is
idiomatic. Custom allocators with specific requirements may implement Option B instead.

---

## 3. Type-directed move-out

Move-out is expressed in two equivalent forms:

**Type-directed binding** — when a `let` binding declares type `T` and the right-hand
side is `@[r] T`, move-out is implicit:

```metel
let node: Node = ptr;   // declared type drives move-out; ptr consumed
```

**Type ascription** — the ascription operator drives move-out in any expression position,
including call sites and return expressions:

```metel
let ptr = @[r] Node { val: 1, next: null };
let node = ptr: Node;         // ascription in expression position
process(ptr: Node);           // move-out at call site
```

Both forms obey the same constraints: unconditionally legal for `@[Heap] T`; requires
`T: !Drop` for bulk-deallocating `@[r] T` (Option A). The compiler enforces this via the
negative bound — if `T` has a `Drop` impl the binding is rejected at the call site.

---

## 4. Clone extraction

When `T: Clone` and move-out from a scoped arena is unavailable (Option A: `T: Drop`),
the safe path is to clone the value into a target region:

```metel
// auto-deref dispatches clone() through the region pointer
let copy: @[Heap] Config = src.clone();

// stdlib convenience (naming open — see §5)
let copy: @[Heap] Config = src.clone_into[Heap]();
```

The source pointer and its arena slot remain valid. The clone is independently owned in
the target region. The target does not have to be `Heap`; any region whose lifetime
encompasses the clone's use is valid.

---

## 5. Unresolved questions

1. **Drop list overhead acceptability (Option B) — deferred.** If move-out of `Drop` types
   from scoped arenas proves necessary in practice, the drop-list approach becomes worth its
   overhead. Deferred until profiling data from realistic workloads is available.

2. **`clone_into` naming and placement — deferred.** The stdlib convenience in §4 needs a
   name and a home (free function vs method, generic over region kind). Deferred to the
   clone API RFC.

---

## 6. Summary table

| Extraction form | `@[Heap] T` | `T: Copy` | `T: !Drop` | `T: Drop` |
|---|---|---|---|---|
| Borrow `&T` | `&ptr` | `&ptr` | `&ptr` | `&ptr` |
| Borrow `&mut T` | `&mut ptr` | `&mut ptr` | `&mut ptr` | `&mut ptr` |
| Copy out | `ptr: T` | `ptr: T` | — | — |
| Move out | `ptr: T` | — | `ptr: T` | not supported |
| Type-directed move | `let x: T = ptr` | — | `let x: T = ptr` | not supported |
| Clone out | `clone_into[dst]()` | — | — | `clone_into[dst]()` |

---

## References

- RFC-0063 (Region Handles) §8.1 — the extraction gap this RFC addresses; §2 —
  type-directed allocation, the symmetric counterpart to §3 of this RFC.
- RFC-0065 (Region Ergonomics) §1 — elision rules that interact with auto-deref (§5.3).
- `docs/reports/memory-model/arena-handles-as-lifetime-annotations.md` §8 — bump arena
  Drop semantics.
