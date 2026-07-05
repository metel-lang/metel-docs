---
id: rfc-0067
title: "Reference Types"
date: '2026-06-28'
---

> **Status — under review.** Moved back from accepted, together with the rest of the
> region RFC cluster (RFC-0063, 0065, 0066, 0068, 0069, 0073, 0077) — see RFC-0063's status
> note and `docs/reports/lifetimes-vs-regions-2026-07-02.md`. The proposed split assigns
> this RFC's borrows an **inferred lifetime**, not a region; the `&[r]` tag-slot rule (does
> a borrow slot admit an allocator name, or only a binding?) is called out there as the
> highest-leverage open decision, and is decided here once settled. Supersedes RFC-0043
> (Regular Pointers). Amends RFC-0044 (Explicit Receiver Semantics), RFC-0063 (Region
> Handles), RFC-0065 (Region Ergonomics), and RFC-0066 (Region Pointer Extraction).

## Summary

Replace Metel's `*T` / `*mut T` pointer model (RFC-0043) with Rust-style **reference
types**: `&T` (shared immutable reference) and `&mut T` (exclusive mutable reference).
Remove the explicit `*p` dereference operator. Access to referenced values is always
through auto-deref; the language has no safe dereference expression.

The same change resolves the move-out syntax for region pointers: `*ptr` is gone, and
consuming a region pointer is handled by a dedicated method and type-directed move-out.

---

## Motivation

RFC-0043 introduced `*T` / `*mut T` as the non-owning alias types with `&x` for
address-of and `*p` for explicit dereference. This model accumulates visible friction
when combined with the region pointer system. The extraction examples in RFC-0066 show
it most clearly:

```metel
// clone extraction from a region pointer — current
let copy: @[Heap] Config = (*(&src)).clone();
```

`src: @[r] Config`. To call `.clone()` the programmer must borrow-deref (`&*src` or
`&src` producing `*Config`), then dereference again — two visible `*` operations that
obscure a conceptually simple "borrow this value and clone it." The same sigil (`*`)
marks region-pointer move-out, regular-pointer dereference, and the type notation for
non-owning references. The overloading is the source of confusion.

Rust's reference model resolves this: `&T` / `&mut T` are the reference types, auto-deref
handles all value access, and the programmer only names pointers when creating or
explicitly storing them. The same example becomes:

```metel
// clone extraction — with reference types
let copy: @[Heap] Config = src.clone();
```

---

## 1. Reference types

Metel has two reference types:

```metel
&T      // shared immutable reference
&mut T  // exclusive mutable reference
```

These replace `*T` and `*mut T` from RFC-0043. Their semantics are unchanged: both are
non-owning aliases to a value held elsewhere. `&T` allows multiple simultaneous readers;
`&mut T` is exclusive — no other reference to the same location may exist while it is
live.

`&mut T` coerces to `&T` implicitly. No other reference coercion is implicit.

---

## 2. Address-of

The address-of operators `&` and `&mut` are syntactically unchanged:

```metel
let x = 42;
let r: &i64      = &x;      // shared reference to x
let mut y = 42;
let m: &mut i64  = &mut y;  // exclusive reference to y
```

Addressability rules from RFC-0043 §5 are preserved: only stable lvalues (named
bindings, fields, array elements, and chains thereof) may be addressed. Temporaries
cannot.

---

## 3. Auto-deref

There is no explicit dereference operator in safe code. All access to referenced values
goes through auto-deref, which applies in three positions:

1. **Field access** — `r.field` where `r: &T` dereferences to access `T.field`.
2. **Method dispatch** — `r.method(args)` inserts the borrow required by the method's
   receiver.
3. **Deref coercions** — `&T` or `&mut T` coerces to a less-capable reference in
   positions where a shared borrow of the inner type is expected:
   `& @[r] T` coerces to `&T`; `&mut @[r] T` coerces to `&mut T`.

Auto-deref chains: a `& &T` will deref through both levels if needed. The compiler
resolves the chain depth from the expected type.

---

## 4. Region pointer access

`@[r] T` participates in auto-deref. It is treated by the compiler as a "one-level
owner" over `T`: field access and method dispatch deref through the region pointer
transparently.

```metel
let node = @[r] Node { val: 1, next: null };

let v = node.val;           // auto-deref: @[r] Node → Node, read field
node.val = 2;               // auto-deref: @[r] Node → Node, write field
node.method(args);          // auto-deref: dispatches on Node
```

**Explicit borrows** through a region pointer produce a region-tagged reference:

```metel
let r: &[r] Node     = &node;      // shared borrow — &[r] Node, coerces to &Node
let m: &mut [r] Node = &mut node;  // exclusive borrow — &mut [r] Node, coerces to &mut Node
```

`&node` where `node: @[r] T` gives `&[r] T` — the region-tagged borrow established in
RFC-0063 §2 as the shorthand for `& @[r] T`. `&[r] T` coerces to `&T` in positions
where the region tag is not needed (e.g., calls to functions that take plain `&T`).

---

## 5. Move-out from `@[r] T`

Move-out is the consuming operation that extracts `T` from `@[r] T`, destroying the
region pointer. Since `*ptr` is gone, move-out is expressed in two ways:

### 5.1 Type-directed move-out

When a `let` binding or return position declares type `T` and the source is `@[r] T`,
the compiler performs move-out implicitly:

```metel
let ptr = @[r] Node { val: 1, next: null };
let node: Node = ptr;    // move-out: ptr consumed, Node returned
```

If `T: Copy`, the operation is a copy — `ptr` remains valid:

```metel
let ptr = @[r] Point { x: 1, y: 2 };
let p: Point = ptr;   // copy: Point is Copy, ptr still valid
```

The same rules from RFC-0066 apply: move-out from `@[Heap] T` is always safe; move-out
from bulk-deallocating `@[r] T` requires `T: !Drop` (Option A) or allocator-tracked
destruction (Option B).

### 5.2 Type ascription move-out

For explicit move-out in any expression position, the type ascription operator drives
consumption the same way a declared binding type does:

```metel
let node = ptr: Node;     // ascription in let — ptr consumed
process(ptr: Node);       // ascription at call site — ptr consumed
```

This keeps `@[r] T` behaviorally identical to `T` itself — the pointer type carries no
special consuming method, and no stdlib import is required.

---

## 6. Impact on the borrow forms in RFC-0063

RFC-0063 §2 defines borrow shorthand:

| Sugar | Expands to | Meaning |
|---|---|---|
| `&[r] T` | `&@[r] T` | shared borrow of a region-`r` value |
| `&mut [r] T` | `&mut @[r] T` | exclusive borrow of a region-`r` value |

Under this RFC, `&node` where `node: @[r] T` gives `&[r] T` (§4) — the RFC-0063
shorthand for `& @[r] T`. `&[r] T` coerces to plain `&T` where the region tag is not
required. The `&[r] T` form in signatures names the region for lifetime tracking and
elision; `&T` is what callers that don't care about the region observe after coercion.
These describe the same borrow from different vantage points.

---

## 7. Impact on RFC-0066

RFC-0066's extraction forms update as follows:

| Extraction form | Old syntax | New syntax |
|---|---|---|
| Borrow `&[r] T` (→ `&T`) | `&*ptr` | `&ptr` |
| Borrow `&mut [r] T` (→ `&mut T`) | `&mut *ptr` | `&mut ptr` |
| Copy out (T: Copy) | `*ptr` | `let x: T = ptr` or `ptr: T` |
| Move out | `*ptr` | `let x: T = ptr` or `ptr: T` |
| Clone out | `(*(&src)).clone()` | `src.clone()` |

RFC-0066 §5.3 (auto-deref for borrows, open question) is resolved by this RFC: `src.clone()` on `@[r] T` dispatches to `T::clone` through auto-deref. The unresolved question is closed.

---

## 8. Supersession of RFC-0043

This RFC supersedes RFC-0043. The correspondence is:

| RFC-0043 | This RFC |
|---|---|
| `*T` | `&T` |
| `*mut T` | `&mut T` |
| `&x` → `*T` | `&x` → `&T` |
| `&mut x` → `*mut T` | `&mut x` → `&mut T` |
| `*p` explicit dereference | removed; auto-deref only |
| `*mut T` coerces to `*T` | `&mut T` coerces to `&T` |

RFC-0043 §6 (auto-deref for field access, method calls, function pointer calls) is
preserved and extended to apply to `@[r] T` as specified in §4.

RFC-0043 §8 (no pointer arithmetic) and §8 (nullability via `Perhaps<*T>`) carry over
unchanged, with the type renamed to `Perhaps<&T>`.

---

## 9. Unresolved questions

None.

**Closed — `&[r] T` coercion depth.** `&[r] T` coerces to `&T` implicitly at coercion
sites — function arguments, return expressions, and `let` bindings with an explicit type
annotation. No coercion is inserted in unannotated expression positions where no expected
type is known. This matches Rust's deref-coercion rules for `&Box<T>` → `&T`.

**Closed — Auto-deref chain depth.** The compiler follows the deref chain until it reaches
the expected type, with no explicit numeric depth limit. The chain is bounded by the type
structure (no infinite deref cycles are possible). Ambiguous chains are resolved by the
expected type at the coercion site. This also matches Rust's approach.

---

## References

- RFC-0043 (Regular Pointers) — superseded by this RFC.
- RFC-0044 (Explicit Receiver Semantics) — `&self` / `&mut self` receivers are now
  consistent with `&T` / `&mut T` as general reference types.
- RFC-0063 (Region Handles) §2 — borrow forms `&[r] T` and `&mut [r] T`.
- RFC-0065 (Region Ergonomics) §1 — elision rules apply to `&T` and `&mut T` equally.
- RFC-0066 (Region Pointer Extraction) — move-out and borrow-deref forms updated by §5
  and §7 of this RFC.
