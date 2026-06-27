---
id: rfc-0066
title: "Region Pointer Extraction"
date: '2026-06-27'
---

> **Status — draft, design-only.** Depends on RFC-0063 (Region Handles) and the
> arena-handles report (`docs/reports/memory-model/arena-handles-as-lifetime-annotations.md`).
> Addresses the gap identified in RFC-0063 §8.1: how a caller obtains a plain `T` or `&T`
> from an `@[r] T` region pointer, and what the destructor semantics are in each case.

## Summary

RFC-0063 specifies how values are allocated *into* regions (`r.alloc(v) -> @[r] T`) and
how they are borrowed (`&[r] T`, `&mut [r] T`). It does not specify how a value is
extracted *out of* a region pointer — either by move or by borrow-deref — to satisfy a
call site that expects a plain `T` or `&T`. This RFC analyses the design space, identifies
where the arena-handles report already resolves the question, and surfaces what remains
open.

---

## Motivation

Existing functions and methods in the stdlib — and in user code written before regions
were introduced — take plain `T` or `&T` parameters. A caller holding `@[r] List<T>`
cannot pass it to such a function without extracting the value. Two extraction forms are
needed:

- **Borrow-deref** — obtain `&T` (or `&mut T`) from `@[r] T` without consuming the
  pointer; used for read-only or mutation calls.
- **Move-out** — obtain `T` from `@[r] T`, consuming the pointer; used when the callee
  takes ownership.

The analysis differs between `@[Heap] T` and scoped `@[r] T` because the two region
kinds have fundamentally different Drop semantics.

---

## 1. Extraction from `@[Heap] T`

`@[Heap] T` is structurally equivalent to the `Box<T>[Heap]` type defined in the
arena-handles report (§7.2). That report already specifies both extraction forms:

**Borrow-deref.** `&*ptr` produces `&T` by borrowing through the region pointer.
Auto-deref may be added so that `&ptr` or a method call on `ptr` transparently produces
the borrow, but this is a separate ergonomics question (see §4).

**Move-out.** `Box::into_inner` is defined as:

```metel
fun into_inner(self) -> T { *self.ptr }
```

This consumes the `Box<T>[Heap]` (and therefore the underlying `@[Heap] T`), moves `T`
out, and frees the heap slot. The Drop impl for `Box<T>[Heap]` calls `T::drop` if T
requires it and then calls `Heap.free(ptr)` to reclaim the allocation. Because the heap
tracks each allocation individually, this is safe and complete — no orphaned memory, no
missed destructor.

For raw `@[Heap] T` not wrapped in `Box`, the same semantics apply: `*ptr` moves the
value out and the heap slot is freed. `@[Heap] T` is therefore fully symmetric with
`Box<T>` at the value-extraction level.

---

## 2. Extraction from scoped `@[r] T`

Scoped arenas have a fundamentally different Drop model. The arena-handles report §11.3
defines bump arena `free` as a no-op:

```metel
fun free<T>(&mut self, _ptr: *iso[R] T) {}  // bump arenas don't free individually
```

And the `Box<T>[R]` Drop comment for scoped arenas reads:

> scoped bump arena: no-op — the arena drop reclaims all memory at once

This is the standard bump-arena trade-off: O(1) bulk deallocation in exchange for the
inability to free individual slots during the arena's lifetime. The consequence for value
extraction depends on whether `T` has a destructor.

### 2.1 Types without a destructor (`NoDrop`)

If `T` carries no external resources — no file handles, no heap sub-allocations, no
`Drop` impl — move-out is safe. The slot becomes orphaned (logically empty but still
occupying arena memory), and when the arena drops it reclaims the raw memory without
needing to call any destructor. Nothing leaks; nothing is called twice.

```metel
let n: @[r] Point = r.alloc(Point { x: 1, y: 2 });
let p: Point = *n;   // move out — safe, Point has no Drop
// n consumed; slot is orphaned but arena still frees the memory on drop
```

### 2.2 Types with a destructor

If `T` has a `Drop` impl, move-out creates a double-drop hazard. The value's destructor
runs when the moved-out `T` is eventually dropped by its new owner. If the arena also
attempts to call `T::drop` for the orphaned slot when it drops, the destructor runs
twice — undefined behaviour.

The bump arena's Drop currently has no mechanism to distinguish live slots from orphaned
ones. Three approaches resolve this:

**Option A — restrict move-out to `NoDrop` types.** The type system enforces that `*ptr`
on a scoped `@[r] T` is only legal when `T: NoDrop` (a new compiler-understood bound
meaning "no Drop impl"). Attempting to move out a `T: Drop` from a scoped arena is a
compile error. This is the most conservative option and requires no runtime bookkeeping.

**Option B — drop list in the arena.** The arena maintains a list of (slot, destructor)
pairs for every allocation that has a `Drop` impl. Move-out removes the entry; the
arena's own Drop only runs destructors for entries still in the list. This preserves full
safety for all types but adds per-allocation overhead for `Drop` types and makes the
bump arena no longer purely O(1) on drop (it is O(live Drop-types) instead of O(1)).

**Option C — caller-driven destructor.** Move-out from a scoped arena requires the
caller to explicitly run `T::drop` before calling `r.move_out(ptr)`. This is the
`unsafe` model — the type system cannot enforce it, but it is what Zig-style manual
memory management expects. Inconsistent with Metel's safe-by-default posture.

Option A is the recommended starting point. It is zero-cost, statically enforced, and
consistent with how bump arenas are used in practice — allocation-heavy workloads
typically deal in plain data types, not resource-holding ones. Types with `Drop` should
use `@[Heap] T`.

### 2.3 Copy extraction

`T: Copy` is always safe regardless of arena kind. Reading through a borrow copies the
value without consuming the pointer or orphaning the slot:

```metel
let n: @[r] Point = r.alloc(Point { x: 1, y: 2 });
let p: Point = *(&n);   // copy through borrow — n still valid, slot intact
```

This does not require any new language machinery: it follows from the existing borrow
and copy rules. It is the right answer for small plain-data types.

### 2.4 Clone extraction

For types that are neither `Copy` nor `NoDrop` and must be extracted from a scoped
arena, `Clone` is the safe path. The value is cloned *into* a target region rather than
moved out of the source:

```metel
// explicit two-step form — already idiomatic in the showcase programs
let copy: @[Heap] Config = Heap.alloc((*(&src)).clone());

// possible stdlib convenience
let copy: @[Heap] Config = src.clone_into[Heap]();
```

The source pointer and its arena slot remain valid. The clone is independently owned in
the target region. This pattern appears throughout the showcase programs as
`dst.alloc(string_copy(v))` and is already the intended idiom; `clone_into[dst]()` is a
naming question only.

---

## 3. Borrow-deref and call-site forms

Both region kinds support borrow-deref — obtaining `&T` from `@[r] T` — through
explicit `&*ptr`. The question is whether auto-deref should make this implicit.

RFC-0063 §8.1 identifies several risks of blanket auto-deref coercion (call-site
ambiguity with `&[r] T`, conflict with RFC-0065 §1.2 elision rules, sendability holes).
Those risks apply to borrow-deref as much as to move-out.

The proposed resolution for borrow-deref is consistent with §8.1: explicit `&*ptr` is
required. A future ergonomics RFC may introduce limited auto-deref once the interaction
with elision is understood.

---

## 4. Summary table

| Extraction form | `@[Heap] T` | Scoped `@[r] T`, `T: Copy` | Scoped `@[r] T`, `T: NoDrop` | Scoped `@[r] T`, `T: Drop` |
|---|---|---|---|---|
| Borrow `&T` | `&*ptr` | `&*ptr` | `&*ptr` | `&*ptr` |
| Borrow `&mut T` | `&mut *ptr` | `&mut *ptr` | `&mut *ptr` | `&mut *ptr` |
| Copy out | `*ptr` (Copy) | `*ptr` | — | — |
| Move out | `*ptr` / `into_inner` | — | `*ptr` (Option A) | not supported (Option A) |
| Clone out | `clone_into[dst]()` | — | — | `clone_into[dst]()` |

---

## 5. Unresolved questions

1. **`NoDrop` as a first-class bound.** Option A requires the compiler to know whether
   `T` has a `Drop` impl at the type level. Whether this is expressed as a `NoDrop`
   bound, a negative bound (`T: !Drop`), or an auto-trait is unspecified. Negative bounds
   have precedent in Rust's `auto trait` system but are a significant addition to the type
   system.

2. **Drop list overhead acceptability (Option B).** If the use cases for move-out of
   `Drop` types from scoped arenas are compelling, the drop-list approach becomes worth
   its overhead. The right decision depends on observed allocation patterns. This should
   remain open until realistic workloads are profiled.

3. **Auto-deref for borrows only.** A narrow form of auto-deref — `@[r] T` transparently
   coerces to `&T` for method dispatch and borrow contexts, but never for move — avoids
   most of the risks in §8.1. Whether this narrower form is safe with respect to RFC-0065
   elision requires a dedicated analysis.

4. **`into_inner` naming and placement.** For `@[Heap] T` move-out: is `*ptr` sufficient
   at the syntax level, or is an explicit `into_inner` method on a wrapper type (`Box`)
   the right surface? The arena-handles report defines it on `Box<T>[R]`; whether raw
   `@[r] T` should also support `*` dereference-move directly is open.

5. **Interaction with `freeze`.** The arena-handles report defines `freeze(ptr)` which
   consumes `@[r] T` and returns a sendable immutable pointer (`*val T`). This is a
   third extraction form not covered above. Its interaction with the move-out rules for
   scoped arenas (particularly for `Drop` types) should be addressed alongside this RFC.

---

## References

- RFC-0063 (Region Handles) §8.1 — the extraction gap this RFC addresses.
- `docs/reports/memory-model/arena-handles-as-lifetime-annotations.md` §7.2 — `Box<T>[R]`
  and `into_inner`; §8.1 — bump arena Drop semantics; §11.2 — `Arena` aspect with `free`.
- RFC-0065 (Region Ergonomics) §1.2 — elision rules that interact with auto-deref.
