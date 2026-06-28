---
id: rfc-0072
title: "Negative Bounds"
date: '2026-06-28'
---

> **Status — under review, design-only.** Introduces `T: !Aspect` as a bound that is
> satisfied when `T` does not implement `Aspect`. Required by RFC-0066 (Region Pointer
> Extraction) and RFC-0071 (Ownership and Move Semantics), both of which use `T: !Drop`.

## Summary

Aspect bounds (`T: Aspect`) assert that a type implements a given aspect. This RFC
introduces the complementary form: `T: !Aspect` asserts that a type does **not** implement
a given aspect. A negative bound is satisfied automatically when no implementation of the
named aspect exists for the type; it does not require any declaration at the implementation
site.

The primary motivating use is `T: !Drop`, which constrains move-out from bulk-deallocating
region allocators (RFC-0066 §2.2) and is implied by `T: Copy` (RFC-0071 §4). The
mechanism is general and applies to any aspect.

---

## Motivation

RFC-0071 establishes that `Copy` and `Drop` are mutually exclusive: a type may not
implement both. The constraint "T has no Drop implementation" is already a meaningful and
checkable property — it is what makes bulk-deallocation safe in RFC-0066:

- A bulk-deallocating allocator (e.g. `Region`) frees all backing memory at once when the
  region drops. It does not track individual allocations and cannot call per-element
  destructors at that point.
- When a value `ptr: @[r] T` is moved out of such an arena, the slot is orphaned. The
  allocator has no record of the vacated slot.
- If `T: Drop`, the allocator would need to call `T::drop` on occupied slots at bulk-free
  time — but it cannot distinguish occupied from vacated slots. Moving out a `T: Drop` value
  therefore creates a situation where the Drop impl may run on already-evacuated memory.
- If `T: !Drop`, no destructor call is needed at bulk-free time. The backing memory may be
  reclaimed unconditionally.

There is currently no mechanism to express this constraint in a bound position. `T: !Drop`
cannot be written; only the absence of a `Drop` impl can be informally assumed. This RFC
provides the formal mechanism.

---

## 1. Syntax

A negative bound is written with `!` before the aspect name, in any position where a
positive bound is accepted:

```metel
// generic parameter bound
fun move_out<T: !Drop>(ptr: @[r] T) -> T { … }

// multiple bounds — positive and negative may mix
fun transfer<T: Clone + !Drop>(src: @[r] T) -> T { … }

// bracket channel bounds
fun extract<T: !Drop>[r](ptr: @[r] T) -> T { … }

// struct field bounds (when conditional impls are in play, RFC-0036)
struct Arena<T: !Drop> { … }
```

The `!` binds tightly to the aspect name. `T: !Drop + Clone` reads as
`T: (!Drop) + Clone` — T does not implement Drop, and T implements Clone.

---

## 2. Satisfaction

### 2.1 Concrete types

For a concrete type `T`, `T: !Aspect` is satisfied iff no implementation of `Aspect` for
`T` is reachable in the current compilation scope. This is the same lookup the compiler
already performs to check positive bounds — a negative bound simply inverts the result.

```metel
struct Point { x: f64, y: f64 }
// no impl Drop for Point — Point: !Drop is satisfied

struct Handle { fd: u64 }
impl Drop for Handle { fun drop(self: Handle) { close_fd(self.fd); } }
// impl Drop for Handle exists — Handle: !Drop is NOT satisfied
```

### 2.2 Generic types

In a generic context, `T: !Aspect` is not automatically assumed. The absence of a bound
does not imply the absence of an implementation — the type parameter may be instantiated
with any concrete type, including one that implements the aspect.

A function that requires `T: !Drop` must declare it explicitly:

```metel
// correct — T: !Drop is a stated requirement
fun extract<T: !Drop>[r](ptr: @[r] T) -> T { … }

// incorrect — T may or may not implement Drop; this is a type error if the
// body requires T: !Drop
fun extract<T>[r](ptr: @[r] T) -> T { … }
```

At the call site, the compiler verifies that the instantiated type satisfies the bound:

```metel
let ptr: @[r] Point = @[r] Point { x: 1.0, y: 2.0 };
extract(ptr);    // Point: !Drop ✓

let ptr: @[r] Handle = @[r] Handle { fd: open("f") };
extract(ptr);    // compile error: Handle implements Drop; Handle: !Drop not satisfied
```

### 2.3 The `Copy` implies `!Drop` rule

RFC-0071 §4 establishes that `Copy` and `Drop` are mutually exclusive. This is encoded as
an implication: any type satisfying `T: Copy` automatically satisfies `T: !Drop`. The
compiler derives this without any explicit declaration:

```metel
fun needs_no_drop<T: !Drop>(val: T) { … }

let p = Point { x: 1.0, y: 2.0 };
impl Copy for Point {}   // Point: Copy
needs_no_drop(p);        // valid — Point: Copy implies Point: !Drop
```

This implication is unconditional: there is no way to implement both `Copy` and `Drop` for
the same type, so the bound `T: Copy` is always a strictly stronger condition than `T: !Drop`.

### 2.4 Compound types

For compound types (structs, enums, tuples), `T: !Drop` is a claim about the type itself —
whether it has a `Drop` implementation — not about its fields. A struct whose fields
implement `Drop` does not itself implement `Drop` unless an explicit `impl Drop for Struct`
is provided:

```metel
struct Wrapper { inner: Handle }
// No impl Drop for Wrapper — Wrapper: !Drop is satisfied
// (Handle::drop will still run when Wrapper is dropped,
//  via recursive field dropping — but Wrapper itself has no Drop impl)
```

This matches the semantics of RFC-0066: the concern is whether the *slot* in the arena
carries a destructor obligation. A `Wrapper` with no `Drop` impl has no such obligation for
the slot itself; field destructors run through the normal ownership chain before the arena
is freed.

---

## 3. Negative bounds in where clauses

Where clauses (when present in a function or impl block) accept negative bounds:

```metel
fun extract<T>[r](ptr: @[r] T) -> T
    where T: !Drop
{ … }
```

This is equivalent to the inline form `<T: !Drop>`. The two forms may be mixed freely.

---

## 4. Interaction with conditional impls (RFC-0036)

RFC-0036 allows impl blocks that are conditional on type bounds. Negative bounds participate
in these conditions on the same terms as positive bounds:

```metel
impl<T: !Drop> BulkMove for Arena<T> { … }
```

This impl applies only when `T` does not implement `Drop`. The compiler checks the condition
at each instantiation.

---

## 5. What negative bounds do not cover

### 5.1 Explicit negative impls

This RFC does not introduce a mechanism to explicitly *declare* that a type does not
implement an aspect (`impl !Drop for T {}`). Negative bounds are checked against the
absence of a positive impl; they do not require any opt-out declaration at the type
definition site.

Explicit negative impls (for opting concrete types out of auto-aspects, if such a feature
is ever introduced) are a separate and more complex mechanism. That question is deferred.

### 5.2 Negative bounds on the `Self` type within impl blocks

Within an impl block, placing a negative bound on `Self` (e.g. to provide a method only
when the type does not implement some aspect) interacts with aspect coherence (RFC-0060) in
non-trivial ways. This is deferred until a concrete use case is established.

---

## 6. Unresolved questions

None.

---

## References

- RFC-0034 (Struct-Enum-Aspect Bounds) — the bound syntax this RFC extends.
- RFC-0060 (Aspect Impl Coherence) — coherence rules that govern which impls are reachable
  and therefore relevant to negative bound checking.
- RFC-0066 (Region Pointer Extraction) — primary consumer of `T: !Drop`; §2.2 specifies
  the move-out constraint that motivates this RFC.
- RFC-0071 (Ownership and Move Semantics) — establishes `Copy`/`Drop` mutual exclusion;
  §3–4 ground the `Copy implies !Drop` implication.
