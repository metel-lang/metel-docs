---
id: rfc-0061
title: "Structural Aspect Bounds"
date: '2026-07-01'
status: integrated
updated: '2026-07-13'
impl_tracking: 'https://codeberg.org/metel-lang/metel-core/issues/245'
impl_status: not-started
---

> **Status — accepted.** Depends on RFC-0060 (Aspect Impl Coherence) and
> RFC-0036 (Conditional Impl Blocks). Specifies how aspect bounds are satisfied for
> structural types — arrays (`T[]`), tuples, and function types — and how `std::core`
> provides blanket impls for structural type constructors.

> **Status — integrated (2026-07-13).** Integrated ahead of implementing issue #245. Confirmed no error-code collision (T0012 reuse, consistent with RFC-0036's precedent). Confirmed via direct source testing that #233/#241 did NOT leave structural impls in a safe not-yet-implemented state as this RFC's dependents assumed -- three independent hard-crash/skip bugs block any structural impl today (inference.rs's unconditional internal error for any non-Named impl target, a hardcoded array-method dispatch gate, and registry.rs silently skipping structural targets during registration) -- flagged as groundwork issue #245 must fix first, not a gap in this RFC's own content. Auto-impl propagation (S5) and function-pointer auto-derived aspects (S7.2) both depend on the auto-impl mechanism itself, which doesn't exist for any type yet (confirmed zero hits for auto-impl anywhere in source) -- marked not-yet-implemented pending that separate prerequisite, consistent with how RFC-0060 S4 auto-impl is itself still unimplemented.

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
5. **Auto-impl propagation**: `Send`, `Sync`, and `Drop` propagate through `T[]`
   structurally via the RFC-0060 §4 auto-impl rule.
6. Tuples and function types are covered below; tuples are deferred.

---

## 1. Structural Type Constructors

A structural type is one defined by a constructor built into the language rather than
declared by a user. The structural constructors in Metel are:

| Constructor | Example | Notes |
|---|---|---|
| Array | `T[]` | Owned, sized, homogeneous sequence of `T` |
| Tuple | `(A, B)`, `(A, B, C)`, … | Heterogeneous fixed-arity product |
| Function type | `fun(A) -> B` | Function pointer; not closures (RFC-0050) |

These are not nominal types — they have no name that can appear as the key in an
impl. For the orphan rule (RFC-0060 §1), structural type constructors are treated as
belonging to `std::core`. A user module may not write `impl Aspect for T[]` unless
the **aspect** is local to that module.

### 1.1 Array representation

`T[]` is a **sized, owned** sequence type: a fat struct carrying a pointer to
element storage, a length, and a capacity. It is not an unsized slice. It may be
passed by value (moving ownership of the fat struct) and may appear as a struct field.
Because it owns its element storage, `T[]` is never `Copy`.

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

Coherence rules for structural impl targets follow RFC-0060 §2 and RFC-0036 §3.1
without special cases: two impls of the same aspect for `T[]` are checked for
overlap by the standard rules. If one uses `T: Bound` and the other uses `T: !Bound`
(syntactic negation, RFC-0036 §3.1), they are disjoint and both accepted. If neither
directly negates the other, they are a conflict.

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

`std::core` provides the following explicit blanket impls for arrays:

```metel
impl<T: Display> Display for T[] {
    fun to_string(self: &T[]) -> String {
        // "[" + elements joined by ", " + "]"
    }
}

impl<T: Clone> Clone for T[] {
    fun clone(self: &T[]) -> T[] {
        // element-wise clone into new backing storage
    }
}

impl<T: Eq> Eq for T[] {
    fun eq(self: &T[], other: &T[]) -> boolean {
        // element-wise equality, short-circuiting; false if lengths differ
    }
}
```

These impls are in `std::core` and cannot be overridden by user code (orphan rule).
`List<T>` is a nominal struct and its impls are separate from the array impls; both
coexist.

### 4.1 Deferred standard impls

The following blanket impls are natural but deferred pending their aspect definitions:

| Impl | Blocked on |
|---|---|
| `impl<T: Ord> Ord for T[]` — lexicographic ordering | RFC-0062 (Ord Comparison Aspect, draft) |
| `impl<T: Hash> Hash for T[]` — element-wise hashing | No Hash RFC yet |

Until RFC-0062 is accepted, `T[]` does not implement `Ord`. Until a Hash RFC is
accepted, `T[]` does not implement `Hash`. The blanket impls will be added to
`std::core` when the respective aspect RFCs are accepted.

---

## 5. Auto-Impl Propagation

The RFC-0060 §4 auto-impl rule generates impls for marker aspects whose conditions
hold structurally over all fields. `T[]` is a structural type whose single "field"
kind is its element type `T`. The rule applies as follows:

### 5.1 Send

`T[]: Send` is auto-derived when `T: Send`.

An array can be transferred across fiber boundaries when its elements can — all
elements are of type `T`, and no additional non-`T` state introduces a thread
dependency. If `T: !Send`, `T[]: !Send` automatically (no negative impl required).

### 5.2 Sync

`T[]: Sync` is auto-derived when `T: Sync`.

A shared reference `&T[]` is safe to use from multiple fibers when `&T` is, which
holds exactly when `T: Sync`.

### 5.3 Drop

`T[]: Drop` is auto-derived when `T: Drop`.

When an array is dropped:
1. If `T: Drop`, the destructor is called on each live element in reverse index order.
2. The backing storage is then reclaimed.

When `T: !Drop`, step 1 is skipped — only the backing storage is reclaimed. The array
itself therefore has a Drop impl iff `T: Drop`. When `T: !Drop`, the array satisfies
`T[]: !Drop`, which permits move-out from scoped regions under RFC-0066 §2.2.

---

## 6. Tuples

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

Auto-impl propagation (§5) applies to tuples as soon as per-arity blanket impls land:
`(A, B): Send` when `A: Send` and `B: Send`, and so on. The auto-impl rule already
handles this — no separate specification is needed once the blanket impls exist.

---

## 7. Function Types

`fun(A) -> B` is a **function pointer** type — a word-sized code address with no
captured state. It is distinct from closures, which are covered by RFC-0050.

### 7.1 `Callable`

Every function type `fun(A) -> B` automatically implements `Callable<A, B>` — the
aspect for callable values. The compiler provides this impl for all function pointer
types without a declaration at the user level:

```metel
// auto-provided by the compiler for every function pointer type
impl Callable<A, B> for fun(A) -> B {
    fun call(self: &fun(A) -> B, arg: A) -> B { (*self)(arg) }
}
```

This is what allows function pointers to be passed as `&dyn Callable<A, B>` (RFC-0008)
and used in higher-order functions. The formal definition of `Callable` — its aspect
declaration and method signatures — is deferred to a follow-on stdlib RFC; its
object-safety is established in RFC-0008 §3.

### 7.2 Copy, Clone, Send, Sync

Function pointers carry no state. Their relevant aspect impls:

| Aspect | Status | Reason |
|---|---|---|
| `Copy` | Yes | Function pointers are word-sized; bitwise copy is correct |
| `Clone` | Yes | Derived from `Copy` via RFC-0080 blanket |
| `Send` | Yes | No captured state; code pointers are globally valid |
| `Sync` | Yes | Same reason as `Send` |

These are provided by `std::core`. No user declaration is needed.

### 7.3 Aspects function pointers do not implement

| Aspect | Reason |
|---|---|
| `Display` | No canonical string representation for code addresses |
| `Eq` | Function equality is undecidable in general |
| `Ord` | No total ordering on functions |
| `Hash` | Pointer-equality hashing would be address-dependent and non-portable |
| `Drop` | Function pointers own no resources |

Attempting to use `fun(A) -> B` where one of these bounds is required is a compile
error under Phase 1 behaviour (§3).

### 7.4 Closures

Closures defined in RFC-0050 have distinct anonymous types that implement `Callable`
and may implement `Send` and `Sync` depending on their captures. `fun(A) -> B` is not
a closure type; closure types are structural types generated per-closure-site. Their
aspect impls are specified in RFC-0050.

---

## 8. Unresolved Questions

1. **Tuple impls.** Per-arity blanket impls vs. variadic generics. Deferred.

2. **`Display` vs `Debug` for arrays.** Rust provides `Debug` for arrays but not
   `Display`, arguing that collections have no canonical human format. Metel's
   decision to provide `Display for T[]` is made here based on the `dbg` formatter
   already covering the debug case. This may be revisited.

3. **`Callable` formal definition.** The `Callable<A, B>` aspect is referenced in
   RFC-0008 (object safety) and this RFC (function pointer auto-impl) but has no
   formal aspect declaration. Its definition — including multi-argument forms and
   the distinction between `&self`, `&mut self`, and by-move receivers — is deferred
   to a follow-on stdlib RFC.

4. **Multi-argument function types.** `fun(A, B) -> C` should implement
   `Callable<(A, B), C>` (with a tuple argument) or a multi-parameter `Callable`.
   The exact mechanism depends on the tuple blanket impls and the `Callable` formal
   definition; both are deferred.

---

## References

- RFC-0036 (Conditional Impl Blocks) — the conditional impl syntax used for
  structural blanket impls.
- RFC-0050 (Closure Capture Lists, draft) — closure types and their aspect impls;
  distinct from function pointer types.
- RFC-0060 (Aspect Impl Coherence) — orphan rule; structural constructors owned by
  `std::core`; overlap detection; §4 auto-impl rule used in §5.
- RFC-0062 (Ord Comparison Aspect, draft) — prerequisite for `impl<T: Ord> Ord for T[]`.
- RFC-0066 (Region Pointer Extraction) — §2.2 move-out constraint requires `T: !Drop`;
  §5.3 specifies when `T[]: !Drop`.
- RFC-0071 (Ownership and Move Semantics) — `Copy`/`Drop` mutual exclusion; function
  pointers are `Copy`.
- RFC-0080 (Stdlib Aspects) — `Clone`, `Send`, `Sync` formal definitions; `Copy`
  implies `Clone` blanket; function pointer `Send`/`Sync` follows from §3.2/§4.2.
- RFC-0008 (Aspect Objects) — `Callable<A, B>` object safety; `dyn Callable<A, B>`.
- RFC-0054 — `List<T>` as a nominal struct; `List<T>` impls are separate from array
  impls and coexist.
