---
id: rfc-0067
title: "Reference Types"
date: '2026-06-28'
updated: '2026-07-05'
---

> **Status — under review.** Rewritten 2026-07-05. The original RFC used `&[r] T` /
> `&mut [r] T` for region-tagged borrows. Under the split model (RFC-0063 rewritten),
> borrows carry **lifetime anchors**, not allocator tags. The anchor syntax is `&r T`
> (immutable) and `&r mut T` (mutable) — the anchor groups with `&`, mutability follows.
> Anchors are type-level only; expression position always uses `&val` / `&mut val`.
> Supersedes RFC-0043 (Regular Pointers). Amends RFC-0044 (Explicit Receiver Semantics).
> Depends on RFC-0063 (Allocator Handles) and RFC-0071 (Ownership and Move Semantics).

## Summary

Replace Metel's `*T` / `*mut T` pointer model (RFC-0043) with **reference types**:
`&T` (shared immutable) and `&mut T` (exclusive mutable). Remove the explicit `*p`
dereference operator — all value access is through auto-deref.

This RFC also specifies **lifetime anchors** — the compile-time names that bound a
borrow's validity scope. A borrow `&r T` carries anchor `r`, a binding whose scope
determines how long the borrow remains valid. Anchors are separate from allocators:
the allocator says where a value lives; the lifetime anchor says how long a particular
borrow of it is valid.

---

## Motivation

RFC-0043's `*T` / `*mut T` model accumulates friction when combined with the allocator
system. The extraction examples in RFC-0066 show it most clearly:

```metel
// clone extraction — current *T model
let copy: @Heap Config = (*(&src)).clone();
```

Two visible `*` operations obscure a conceptually simple "borrow this value and clone
it." The same sigil marks allocator-pointer move-out, regular-pointer dereference, and
the type notation for non-owning references.

Reference types and auto-deref resolve this:

```metel
// clone extraction — with reference types
let copy: @Heap Config = src.clone();
```

---

## 1. Reference types

Metel has two reference types:

```metel
&T       // shared immutable reference
&mut T   // exclusive mutable reference
```

These replace `*T` and `*mut T` from RFC-0043. Semantics are unchanged: both are
non-owning aliases. `&T` allows multiple simultaneous readers; `&mut T` is exclusive —
no other reference to the same location may exist while it is live.

`&mut T` coerces to `&T` implicitly. No other reference coercion is implicit.

---

## 2. Lifetime anchors

Every borrow carries a **lifetime anchor** — the name of a binding whose scope bounds
the borrow's validity. The anchor appears directly after `&` in type position:

```metel
&r T       // immutable borrow of T; valid while binding r is alive
&r mut T   // mutable borrow of T; valid while binding r is alive
```

The anchor groups with `&`; `mut` qualifies the reference after it. A borrow `&r T`
does not know or care whether `T` was allocated in allocator `r` — `r` is a binding
name, and the borrow is valid for exactly as long as `r` is in scope.

**Anchors are type-level only.** In expression position, write `&val` and `&mut val`.
The anchor is inferred from the expected type; explicit anchors never appear on
expressions. This matches Rust's design: lifetimes annotate types, not terms.

**Declaration.** When a function needs to name an anchor explicitly (because elision is
ambiguous), it declares it in the type-parameter channel `<>` with the `&` prefix:

```metel
fun longest<&r>(&r Str, &r Str) -> &r Str { ... }
```

Elision rules (RFC-0065 §2) cover the common cases; `<&r>` declarations appear only
when the relationship is ambiguous.

**Lifetime ordering bounds.** When two anchors have no structural relationship the
borrow checker can derive, a `: &s` bound in the `<>` declaration expresses that the
right-hand side is the shorter-lived anchor:

```metel
fun pick<&s, &t: &s>(&s Str, &t Str) -> &t Str { ... }
// &t: &s means t outlives s; t is the shorter-lived anchor
```

---

## 3. Address-of

The address-of operators `&` and `&mut` are syntactically unchanged at the expression level:

```metel
let x = 42;
let r: &i64     = &x;      // shared reference to x
let mut y = 42;
let m: &mut i64 = &mut y;  // exclusive reference to y
```

Addressability rules from RFC-0043 §5 are preserved: only stable lvalues (named
bindings, fields, array elements, and chains thereof) may be addressed. Temporaries
cannot.

The anchor in the resulting type is inferred from the binding being addressed. Taking
`&x` where `x` is in the current scope produces a borrow with the anchor inferred to
be `x`'s scope.

---

## 4. Auto-deref

There is no explicit dereference operator in safe code. All access goes through auto-deref:

1. **Field access** — `r.field` where `r: &T` dereferences to access `T.field`.
2. **Method dispatch** — `r.method(args)` inserts the borrow required by the method's
   receiver.
3. **Deref coercions** — `&T` or `&mut T` coerces to a less-capable reference when the
   expected type requires it.

Auto-deref chains: a `&&T` will deref through both levels if needed. Chain depth is
bounded by the type structure; no infinite cycles are possible.

---

## 5. Allocator pointer access

`@a T` participates in auto-deref. It is treated as a one-level owner over `T`: field
access and method dispatch deref through the allocator pointer transparently.

```metel
let node = @a Node { val: 1, next: null };

let v = node.val;      // auto-deref: @a Node → Node, read field
node.val = 2;          // auto-deref: @a Node → Node, write field
node.method(args);     // auto-deref: dispatches on Node
```

**Explicit borrows** through an allocator pointer produce an anchor-carrying reference.
The anchor is the binding being borrowed:

```metel
let r: &node T   = &node;      // shared borrow; anchor = `node` binding
let m: &node mut T = &mut node; // exclusive borrow; anchor = `node` binding
```

In practice the anchor is almost always elided and inferred from context. The explicit
form appears in type signatures when the anchor must be named.

**Coercion.** A borrow of `@a T` — written `&node` where `node: @a T` — coerces to
plain `&T` in positions where the allocator tag and anchor are not needed. The coercion
is implicit at function arguments, return expressions, and annotated `let` bindings.

---

## 6. Move-out from `@a T`

Move-out is the consuming operation that extracts `T` from `@a T`, destroying the
allocator pointer. Since `*ptr` is gone, move-out is expressed via type context:

**Type-directed** — when a `let` binding or return position declares type `T` and the
source is `@a T`, the compiler performs move-out implicitly:

```metel
let ptr = @a Node { val: 1 };
let node: Node = ptr;    // move-out: ptr consumed, Node returned
```

**Type ascription** — drives move-out in any expression position:

```metel
let node = ptr: Node;       // ascription in let — ptr consumed
process(ptr: Node);         // ascription at call site — ptr consumed
```

Move-out semantics and constraints (heap always safe, scoped allocators require
`T: !Drop` for bulk-deallocating kinds) are specified in RFC-0066.

---

## 7. Supersession of RFC-0043

| RFC-0043 | This RFC |
|----------|----------|
| `*T` | `&T` |
| `*mut T` | `&mut T` |
| `&x` → `*T` | `&x` → `&T` |
| `&mut x` → `*mut T` | `&mut x` → `&mut T` |
| `*p` explicit dereference | removed; auto-deref only |
| `*mut T` coerces to `*T` | `&mut T` coerces to `&T` |

RFC-0043 §6 (auto-deref for field access, method calls) is preserved and extended to
apply to `@a T`. RFC-0043 §8 (no pointer arithmetic) carries over unchanged.
Nullability via `Perhaps<*T>` becomes `Perhaps<&T>`.

---

## 8. Unresolved questions

None.

**Closed — borrow coercion depth.** A borrow of `@a T` coerces to `&T` at coercion
sites (function arguments, return expressions, annotated `let` bindings). No coercion
is inserted in unannotated expression positions where no expected type is known. Matches
Rust's deref-coercion rules.

**Closed — auto-deref chain depth.** The compiler follows the deref chain until it
reaches the expected type, with no explicit depth limit. Chain bounded by type structure.

---

## References

- RFC-0043 (Regular Pointers) — superseded by this RFC.
- RFC-0044 (Explicit Receiver Semantics) — `&self` / `&mut self` receivers are now
  consistent with `&T` / `&mut T` as general reference types.
- RFC-0063 (Allocator Handles) — `@a T`; allocator-tagged owned pointers that this
  RFC borrows from.
- RFC-0065 (Allocator Ergonomics) — elision rules for lifetime anchors and allocator tags.
- RFC-0066 (Allocated Value Extraction) — move-out and borrow forms updated by §6
  of this RFC.
