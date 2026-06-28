---
id: rfc-0071
title: "Ownership and Move Semantics"
date: '2026-06-28'
---

> **Status — draft, design-only.** Establishes the foundational ownership model for Metel
> values. Required by RFC-0063 (Region Handles) and all downstream region RFCs, which
> depend on affine ownership as a given.

## Summary

Metel values are **affine by default**: a non-`Copy` value has exactly one owner at any
point in time. Moving a value transfers ownership to a new binding; the source becomes
invalid. This RFC specifies:

1. move semantics as the default for all struct and enum values;
2. `Copy` as an opt-in trait for types that may be bitwise duplicated;
3. `Drop` as an opt-in trait for types with destructor logic;
4. the mutual exclusion of `Copy` and `Drop`;
5. drop order within a scope;
6. explicit drop and partial moves.

---

## Motivation

Affine ownership is the foundation of Metel's memory safety model. The region system
(RFC-0063 and downstream) relies on region pointers being affine — if `@[r] T` could be
copied freely, the entire lifetime and disjointness analysis would be unsound. The borrow
checker's single-owner invariant, the `T: !Drop` constraint on scoped move-out (RFC-0066),
and the drop ordering that makes struct-owned arenas safe (RFC-0068) all assume that values
move rather than copy by default.

This RFC makes that assumption explicit and normative.

---

## 1. Values move by default

When a value of a non-`Copy` type is assigned, passed as an argument, or returned, it is
**moved**: ownership transfers from the source to the destination. After a move, the source
binding is invalid and may not be used.

```metel
let x = Node { val: 1 };
let y = x;          // x is moved into y; x is now invalid
process(y);         // y is moved into process; y is now invalid
```

The compiler enforces this statically. A use of an invalidated binding is a compile error:

```
error: use of moved value `x`
  --> ...
   | let y = x;   // x moved here
   | …
   | let z = x;   // error: x is no longer valid
```

Move semantics apply to all struct and enum values by default. Primitive types and types
implementing `Copy` are excluded (§2).

---

## 2. The `Copy` trait

A type implementing `Copy` is **bitwise-copyable**: whenever it appears in a value
position, a copy of its bits is made and the original remains valid. No ownership transfer
occurs.

```metel
let x: i64 = 42;
let y = x;   // copy — x is still valid
let z = x;   // copy again — x is still valid
```

`Copy` is opt-in. The following are `Copy` by default:

- Primitive numeric types (`i8`–`i64`, `u8`–`u64`, `f32`, `f64`)
- `bool`, `char`
- Fixed-size arrays whose element type is `Copy`
- Tuples whose element types are all `Copy`

Structs and enums are not `Copy` unless explicitly declared. A type may implement `Copy`
only if all its fields (for structs) or all payload types (for enum variants) are `Copy`;
the compiler enforces this structurally:

```metel
struct Point { x: f64, y: f64 }
impl Copy for Point {}   // valid — f64 is Copy

struct Node { val: i64, next: @[r] Node }
impl Copy for Node {}    // compile error — @[r] Node is not Copy
```

---

## 3. The `Drop` trait

A type implementing `Drop` declares destructor logic that runs when its last owner is
dropped — either by going out of scope or by an explicit `drop` call (§6).

```metel
struct Handle { fd: u64 }

impl Drop for Handle {
    fun drop(self: Handle) {
        close_fd(self.fd);
    }
}

{
    let h = Handle { fd: open("file.txt") };
    use_handle(&h);
}   // h goes out of scope; Handle::drop runs automatically
```

`Drop` is opt-in. Types without a `Drop` impl are reclaimed by recursively dropping their
fields, with no user-defined logic.

---

## 4. `Copy` and `Drop` are mutually exclusive

A type may not implement both `Copy` and `Drop`. The combination is unsound: if a `Copy`
type could be duplicated freely, the destructor would run once per copy, potentially
releasing the same resource multiple times.

```metel
impl Copy for Handle {}   // compile error — Handle implements Drop
```

The negative bound `T: !Drop` (RFC-0066) is satisfied by any type with no `Drop` impl.
All `Copy` types satisfy `T: !Drop` by this mutual exclusion rule — `Copy` implies `!Drop`.

---

## 5. Drop order

Within a scope, values are dropped in **reverse declaration order** — the last-declared
value is dropped first:

```metel
{
    let a = A::new();   // dropped third
    let b = B::new();   // dropped second
    let c = C::new();   // dropped first
}   // c drops, then b, then a
```

Struct fields are dropped in **declaration order** — first field first. This is symmetric
with construction order and allows later fields to safely depend on earlier ones at init
time without requiring reverse cleanup logic.

```metel
struct Conn {
    socket: Socket,   // dropped first
    buffer: Buffer,   // dropped second
}
```

For structs with owned regions (`[own r]`, RFC-0068), the struct's fields are dropped
before the owned arena is freed. This ensures that any `@[r] T` pointers stored as fields
are unreachable before the bulk free, preventing use-after-free at the drop site.

---

## 6. Explicit drop

A value may be dropped before the end of its scope with the free function `drop`:

```metel
let handle = Handle { fd: open("file.txt") };
use_handle(&handle);
drop(handle);   // destructor runs here; handle is invalid from this point
```

`drop` takes ownership of its argument. The compiler treats the binding as moved-out after
the call; any subsequent use is a compile error.

---

## 7. Partial moves

Moving out of a struct field leaves the containing value **partially moved**. A partially
moved value may not be used as a whole; only the remaining un-moved fields may be accessed:

```metel
let p = Pair { a: String { … }, b: 42i64 };
let s = p.a;   // p.a moved out; p is partially moved
let n = p.b;   // p.b moved out; p is now fully consumed
// p itself cannot be used as a whole at any point after the first partial move
```

A struct implementing `Drop` may not be partially moved — the destructor requires access
to the complete value. The compiler rejects partial moves of `Drop` types:

```metel
let h = Handle { fd: open("file.txt"), tag: 1u64 };
let fd = h.fd;   // compile error — Handle implements Drop; partial move not allowed
```

---

## 8. Interaction with the region system

Region pointers (`@[r] T`) are non-`Copy` by construction — they carry an allocation that
must have a single owner at all times. Affine ownership is the mechanism that makes region
lifetime guarantees sound:

- Because `@[r] T` is affine, any region-allocated value always has exactly one live
  owner. This is what allows the interpreter's uniform allocator to provide deterministic
  drop semantics equivalent to the compiled region system.
- The `T: !Drop` bound in RFC-0066 §2.2 requires the definitions of `Drop` and the
  negative bound mechanism established in §3–4 of this RFC.
- The drop ordering in §5 directly determines the order in which arena-allocated fields
  become unreachable before `drop(r)` reclaims the arena's backing memory.

---

## 9. Unresolved questions

1. **`Copy` declaration syntax — resolved.** `Copy` is declared via `impl Copy for T {}`.
   This is consistent with how other aspects are implemented in Metel. A derive-like
   shorthand (e.g. `derive(Copy)`) will be considered when the derived aspects system
   (RFC-0012) is designed; until then, the explicit impl is the only supported form.

2. **Partial moves and pattern matching — resolved.** Pattern destructuring may
   simultaneously move out of multiple fields, subject to the same rules as sequential
   partial moves: the compiler tracks moved fields at field granularity, `Drop` types may
   not be partially destructured, and a partially destructured value may not be used as a
   whole. Whether individual pattern bindings may borrow rather than move a field (a `ref`
   binding modifier or equivalent) is deferred to the pattern syntax RFC.

---

## References

- RFC-0024 (Linear Types, superseded) — prior exploration of linear/affine ownership in
  Metel; this RFC is the settled formulation of the same core idea.
- RFC-0049 (Linear Function Type System, draft) — function-level linearity constraints;
  orthogonal to but compatible with the value-level move semantics specified here.
- RFC-0063 (Region Handles) — depends on affine ownership of `@[r] T`; §2 states the
  non-`Copy` property of region pointers without grounding it in a prior RFC.
- RFC-0066 (Region Pointer Extraction) — the `T: !Drop` bound is founded on §3–4 of
  this RFC.
- RFC-0068 (Struct-Owned Regions) — drop ordering in §5 of this RFC governs when
  struct fields become unreachable relative to arena freeing.
