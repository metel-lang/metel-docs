---
id: rfc-0061
title: "Structural Aspect Bounds"
date: '2026-07-01'
---

> **Status — under review.** Depends on RFC-0060 (Aspect Impl Coherence) and
> RFC-0036 (Conditional Impl Blocks). Specifies how aspect bounds are satisfied for
> structural types — arrays (`T[]`), tuples, and function types — and how `std::core`
> provides blanket impls for structural type constructors.

## Summary

Aspect bounds on structural types — `T[]`, `(A, B)`, `fun(A) -> B` — cannot be
satisfied by the standard impl lookup, which keys on type names. Without a
specification for structural impls:

- `println([1, 2, 3])` fails at compile time with no way to fix it.
- Generic library code cannot write `impl<T: Display> Display for T[]`.
- The type checker has no representation for "array of displayable elements is
  displayable."

This RFC specifies:

1. **Structural type constructors** (`T[]`, tuples, `fun`) are owned by `std::core`
   for orphan rule purposes.
2. **Blanket impls for structural constructors** may be declared in `std::core` using
   the conditional impl syntax from RFC-0036.
3. **Phase 1 behaviour**: without a matching structural impl, structural types fail
   aspect bounds with a precise diagnostic.
4. **Standard impls**: `std::core` provides `Display`, `Clone`, and `Eq` for arrays
   when the element type satisfies the bound.
5. Tuples and function types are deferred.

---

## 1. Structural Type Constructors

A structural type is one defined by a constructor built into the language rather than
declared by a user. The structural constructors in Metel are:

| Constructor | Example | Notes |
|---|---|---|
| Array | `T[]` | Homogeneous sequence of `T` |
| Tuple | `(A, B)`, `(A, B, C)`, … | Heterogeneous fixed-arity product |
| Function type | `fun(A) -> B` | First-class function |

These are not nominal types — they have no name that can appear as the key in an
impl. For the orphan rule (RFC-0060 §1), structural type constructors are treated as
belonging to `std::core`. A user module may not write `impl Aspect for T[]` unless
the **aspect** is local to that module.

---

## 2. Blanket Impls for Structural Constructors

`std::core` may declare impls whose target is a structural type constructor. The
syntax follows RFC-0036 conditional impl syntax:

```metel
// std::core
impl<T: Display> Display for T[] {
    fun to_string(self: &T[]) -> String { ... }
}
```

The type parameter `T` ranges over all types; the `where` bound `T: Display` is the
condition. The impl is applicable to any array `U[]` where `U: Display`.

This is the mechanism that makes `println([1, 2, 3])` compile: `[1, 2, 3]` has type
`i64[]`; `i64: Display`; therefore the conditional impl applies.

Coherence rules for structural impl targets follow RFC-0060 §2 with one addition:
structural type constructors are considered a single family per arity. Two impls of
the same aspect for `T[]` are a conflict regardless of the bound on `T`.

---

## 3. Phase 1 Behaviour

Until `std::core` provides an impl for a structural type constructor, any attempt to
use a value of a structural type in a position that requires an aspect bound fails
with a diagnostic that names the structural constructor:

```
T0012: i64[] does not implement Display
       hint: arrays implement Display only when their element type does;
             no impl<T: Display> Display for T[] is registered
```

This is a compile error, not a runtime panic. Code that was previously passing this
check silently (because structural types were skipped by the bound checker) is now
correctly rejected.

---

## 4. Standard Impls

`std::core` provides the following impls for arrays in the standard library:

```metel
impl<T: Display> Display for T[] {
    fun to_string(self: &T[]) -> String {
        // "[" + elements joined by ", " + "]"
    }
}

impl<T: Clone> Clone for T[] {
    fun clone(self: &T[]) -> T[] {
        // element-wise clone
    }
}

impl<T: Eq> Eq for T[] {
    fun eq(self: &T[], other: &T[]) -> boolean {
        // element-wise equality, short-circuiting
    }
}
```

These impls are in `std::core` and cannot be overridden by user code (orphan rule).
`List<T>` is a nominal struct and its impls are separate from the array impls; both
coexist.

---

## 5. Tuples

Tuples (`(A, B)`, `(A, B, C)`, …) have variable arity and heterogeneous element
types. Providing blanket impls for every arity — the Rust approach — requires
per-arity boilerplate or variadic generics. Both are deferred:

- Per-arity impls (e.g. up to arity 12): deferred pending a decision on where
  boilerplate of this kind lives.
- Variadic generics: no design exists; deferred.

Until tuples have impls, they fail aspect bounds in Phase 1 with a diagnostic:

```
T0012: (i64, String) does not implement Display
       hint: tuple impls are not yet provided; use a named struct instead
```

---

## 6. Function Types

Function types (`fun(A) -> B`) cannot implement aspects in general — the aspects
that would be useful (`Display`, `Clone`) require capabilities that functions do not
have (a function cannot display itself; cloning a closure is non-trivial). Function
types fail aspect bounds with a permanent diagnostic:

```
T0012: fun(i64) -> String does not implement Display
       note: function types cannot implement aspects
```

---

## 7. Unresolved Questions

1. **Tuple impls.** Per-arity blanket impls vs. variadic generics. Deferred.

2. **User impls for structural constructors with local aspects.** The orphan rule
   permits `impl MyAspect for T[]` when `MyAspect` is local. The coherence rules
   for this case — particularly, whether it conflicts with `std::core`'s blanket
   impls of `MyAspect` — are deferred to RFC-0060's parameterised overlap extension.

3. **`Display` vs `Debug` for arrays.** Rust provides `Debug` for arrays but not
   `Display`, arguing that collections have no canonical human format. Metel's
   decision to provide `Display for T[]` is made here based on the `dbg` formatter
   already covering the debug case. This may be revisited.

---

## References

- RFC-0036 (Conditional Impl Blocks) — the conditional impl syntax used for
  structural blanket impls.
- RFC-0060 (Aspect Impl Coherence) — orphan rule; structural constructors owned by
  `std::core`; overlap detection.
- RFC-0054 — `List<T>` as a nominal struct; `List<T>` impls are separate from
  array impls and coexist.
