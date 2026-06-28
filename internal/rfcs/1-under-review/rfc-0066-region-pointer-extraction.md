---
id: rfc-0066
title: "Region Pointer Extraction"
date: '2026-06-27'
---

> **Status — draft, design-only.** Depends on RFC-0063 (Region Handles) and RFC-0065
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
let s: String = mem::move_out(ptr);  // moves String out; heap slot freed; ptr consumed
// s is dropped normally when it goes out of scope
```

Move-out from `@[Heap] T` is safe for all `T`, including `T: Drop`.

### 2.2 Scoped `@[r] T` — constrained by `T`'s Drop status

Scoped bump arenas use bulk deallocation: when the arena drops, it reclaims all arena
memory in one O(1) operation. This creates a constraint for move-out: a slot vacated by
move-out is *orphaned* — the arena cannot distinguish it from a live slot. If `T` has a
`Drop` impl, the arena would call `T::drop` on the orphaned slot at bulk-drop time, but
`T::drop` has already been called by the new owner — undefined behaviour.

#### 2.2.1 `T: Copy`

A `Copy` type is extracted by copy, not move. The slot is not vacated; `ptr` remains
valid:

```metel
let ptr = @[r] Point { x: 1, y: 2 };
let p: Point = mem::move_out(ptr);   // copies Point out — ptr still valid, slot intact
```

Copy extraction works for any region kind and imposes no Drop-related constraint.

#### 2.2.2 `T: NoDrop` (non-Copy, no Drop impl)

If `T` carries no external resources — no `Drop` impl — move-out is safe. The slot is
orphaned, but when the arena drops it reclaims raw memory without needing to call any
destructor. Nothing leaks; nothing runs twice:

```metel
let ptr = @[r] Pair { a: 1, b: 2 };  // Pair has no Drop impl
let p: Pair = mem::move_out(ptr);      // moves out — safe; slot orphaned
// arena frees the raw memory on drop, no destructor to call
```

#### 2.2.3 `T: Drop`

Move-out creates a double-drop hazard. Three options resolve this:

**Option A — restrict move-out to `NoDrop` types (recommended).** `mem::move_out` on
scoped `@[r] T` is a compile error when `T: Drop`. The type system enforces the
restriction statically; no runtime bookkeeping. Types that hold external resources should
use `@[Heap] T`, which supports move-out for all `T`.

**Option B — drop list in the arena.** The arena maintains a `(slot, destructor)` list
for every Drop-typed allocation. Move-out removes the entry; the arena's own Drop only
calls destructors for entries still in the list. Fully safe for all `T`; adds
per-allocation overhead for `Drop` types; arena drop becomes O(live Drop-slots) rather
than O(1).

**Option C — caller-driven.** Move-out requires the caller to explicitly run `T::drop`
before vacating the slot. Unsafe; inconsistent with Metel's safe-by-default posture.

Option A is the recommended starting point. Bump-arena workloads typically deal in plain
data types, not resource-holding ones. The restriction is zero-cost, statically visible at
the call site, and the escape valve — use `@[Heap] T` — is idiomatic.

---

## 3. Type-directed move-out

Symmetric with type-directed allocation (RFC-0063 §2): when a `let` binding declares
type `T` and the right-hand side is `@[r] T`, move-out is implicit from the type
annotation. The same constraints as `mem::move_out` apply.

```metel
let ptr = @[r] Node { val: 1, next: null };

// explicit move-out via std::mem
let node: Node = mem::move_out(ptr);

// type-directed move-out — equivalent, ptr consumed
let node: Node = ptr;
```

For `@[Heap] T` this is unconditionally legal. For scoped `@[r] T`, the `NoDrop`
restriction (Option A) applies: the declared binding type `T` must satisfy `NoDrop`, or
the compiler rejects the binding.

---

## 4. Clone extraction

When `T: Clone` and move-out from a scoped arena is unavailable (Option A: `T: Drop`),
the safe path is to clone the value into a target region:

```metel
// type-directed allocation drives the clone into Heap
let copy: @[Heap] Config = (*(&src)).clone();

// stdlib convenience (naming open — see §5)
let copy: @[Heap] Config = src.clone_into[Heap]();
```

The source pointer and its arena slot remain valid. The clone is independently owned in
the target region. The target does not have to be `Heap`; any region whose lifetime
encompasses the clone's use is valid.

---

## 5. Unresolved questions

1. **`NoDrop` as a first-class bound.** Option A requires the compiler to enforce at the
   type level that `T` has no `Drop` impl. Whether this is expressed as a `NoDrop` bound,
   a negative bound (`T: !Drop`), or a compiler-understood auto-trait is unspecified.
   Negative bounds have precedent in Rust's `auto trait` system but are a significant
   addition to the type system.

2. **Drop list overhead acceptability (Option B).** If move-out of `Drop` types from
   scoped arenas proves necessary in practice, the drop-list approach becomes worth its
   overhead. The right decision depends on observed allocation patterns in realistic
   workloads. Remain on Option A until profiling data is available.

3. **`clone_into` naming and placement.** The stdlib convenience in §4 needs a name and
   a home (free function vs method, generic over region kind). Naming is deferred until
   the clone API is designed holistically.

---

## 6. Summary table

| Extraction form | `@[Heap] T` | Scoped `@[r] T`, `T: Copy` | Scoped `@[r] T`, `T: NoDrop` | Scoped `@[r] T`, `T: Drop` |
|---|---|---|---|---|
| Borrow `&T` | `&ptr` | `&ptr` | `&ptr` | `&ptr` |
| Borrow `&mut T` | `&mut ptr` | `&mut ptr` | `&mut ptr` | `&mut ptr` |
| Copy out | `mem::move_out(ptr)` | `mem::move_out(ptr)` | — | — |
| Move out | `mem::move_out(ptr)` | — | `mem::move_out(ptr)` (Option A) | not supported (Option A) |
| Type-directed move | `let x: T = ptr` | — | `let x: T = ptr` (Option A) | not supported (Option A) |
| Clone out | `clone_into[dst]()` | — | — | `clone_into[dst]()` |

---

## References

- RFC-0063 (Region Handles) §8.1 — the extraction gap this RFC addresses; §2 —
  type-directed allocation, the symmetric counterpart to §3 of this RFC.
- RFC-0065 (Region Ergonomics) §1 — elision rules that interact with auto-deref (§5.3).
- `docs/reports/memory-model/arena-handles-as-lifetime-annotations.md` §8 — bump arena
  Drop semantics.
