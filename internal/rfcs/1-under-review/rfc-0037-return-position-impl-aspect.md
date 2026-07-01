---
id: rfc-0037
title: "Return-Position impl Aspect"
date: '2026-07-01'
deferred_from: rfc-0035 (Q3)
---

> **Status — under review.** Depends on RFC-0060 (Aspect Impl Coherence). Specifies
> `impl Aspect` in function return position: the return type is an opaque concrete
> type known only to satisfy the named aspect. Complements RFC-0035 (parameter-
> position `impl Aspect`).

## Summary

Return-position `impl Aspect` allows a function to return a value whose concrete type
is hidden from the caller. The caller knows only that the value satisfies the named
aspect and may call its methods. The concrete type is fixed per function body —
determined at compile time — with no heap allocation or vtable.

```metel
fun make_adder(n: i64) -> impl Callable<i64, i64> {
    fun(x: i64) -> i64 { x + n }
}
```

The caller receives a value they can call as `f(42)` but cannot name its type or
store it except as the same opaque type. This separates the API contract (the aspect)
from the implementation detail (the concrete type).

---

## 1. Semantics

### 1.1 Opaque monomorphised type

A function returning `impl Aspect` returns a single concrete type, fixed by its body.
The caller sees an opaque type alias — a fresh anonymous type that is known to
implement `Aspect`. There is no boxing, no heap allocation, and no vtable.

Each function definition produces exactly one concrete return type. Two calls to the
same function return values of the same opaque type:

```metel
fun make_pair() -> impl Display {
    42
}

let a = make_pair();
let b = make_pair();
// typeof(a) == typeof(b) — both are the same opaque type
```

This is not dynamic dispatch. If a function body conditionally returns different
concrete types on different code paths, the body is a type error:

```metel
fun bad(flag: boolean) -> impl Display {
    if flag { 42 } else { "hello" }  // error: branches return different concrete types
}
```

### 1.2 Caller rights

The caller may:
- Call any method defined by the declared aspect on the returned value.
- Store the value and pass it to functions that accept the same opaque type or the
  same aspect bound.
- Use it as an argument to a function with an `impl Aspect` parameter.

The caller may not:
- Name the concrete type.
- Cast or convert the value to a different type.
- Call methods not defined by the declared aspect (even if the concrete type has them).

### 1.3 Each `impl Aspect` in a signature is independent

Each occurrence of `impl Aspect` in a function signature is a fresh independent type
variable. Two `impl Display` positions in the same signature may resolve to different
concrete types:

```metel
fun pair() -> (impl Display, impl Display) {
    (42, "hello")   // first is i64, second is String — permitted
}
```

This is consistent with RFC-0035's rule for parameter position.

---

## 2. Relationship to Parameter Position

`impl Aspect` in parameter position (RFC-0035) and return position (this RFC) follow
the same independence rule. A function may have both:

```metel
fun transform(x: impl Display) -> impl Display {
    x   // the return type is the same concrete type as x's type
}
```

The return type resolves to the same concrete type as the parameter because the body
returns `x` directly. This falls out of type inference — no special linkage syntax
is needed. The two `impl Display` positions are independent type variables; the body
constrains them to be equal.

---

## 3. Interaction with Ownership

Return-position `impl Aspect` follows normal ownership rules. The returned value is
moved out of the function body:

```metel
fun make_list() -> impl Iterable<i64> {
    List::new()
}

let xs = make_list();   // xs owns the returned value
```

The opaque type participates in move semantics, `Clone`, and `Drop` according to its
concrete type's implementations. The caller cannot observe which impls the concrete
type has beyond those declared in the aspect bound.

---

## 4. Limitations

### 4.1 Single concrete type per function

A function returning `impl Aspect` must return the same concrete type on all code
paths. If the function needs to return different types based on runtime conditions,
it must either:
- Use a concrete enum that wraps both possibilities and implements the aspect.
- Use an aspect object (`@[r] dyn Aspect`, RFC-0008) for true runtime polymorphism.

### 4.2 Opaque type is not nameable

The caller cannot write the concrete return type in their own code. If a caller needs
to store the value in a struct field or pass it across a module boundary, the field or
parameter type must also use `impl Aspect` (or a generic bound `T: Aspect`).

---

## 5. Unresolved Questions

1. **Named linkage syntax.** Whether to allow explicit linkage between an `impl Aspect`
   parameter and an `impl Aspect` return type — e.g., `fun identity(x: impl Display)
   -> impl(x) Display` — is deferred. The natural-unification approach (§1.3) handles
   the common case without syntax.

2. **`impl Aspect` in struct fields.** Whether struct fields may have `impl Aspect`
   types is deferred to RFC-0038.

3. **Multiple aspect bounds.** Whether return-position `impl Aspect + OtherAspect` is
   supported is deferred. The machinery is the same; the question is syntax and whether
   the bound list is orderless.

---

## References

- RFC-0035 — parameter-position `impl Aspect`; this RFC extends it to return position.
- RFC-0008 (Aspect Objects) — dynamic dispatch alternative when the concrete type is
  not fixed at compile time.
- RFC-0060 (Aspect Impl Coherence) — coherence rules apply to the inferred concrete
  type's impls.
