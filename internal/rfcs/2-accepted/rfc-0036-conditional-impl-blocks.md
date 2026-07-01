---
id: rfc-0036
title: "Conditional Impl Blocks"
date: '2026-07-01'
deferred_from: rfc-0034 (Q6)
---

> **Status — accepted.** Depends on RFC-0060 (Aspect Impl Coherence). Specifies
> conditional `impl` blocks where an aspect implementation for a generic type is
> valid only when the type's parameters satisfy additional bounds. Required by
> RFC-0072 (Negative Bounds) §4 and by the region cluster's generic region bounds.

## Summary

A conditional impl declares that a type implements an aspect only when its type
parameters satisfy specified bounds. Without conditional impls, an aspect can only
be implemented for a generic type unconditionally — which either forces the
constraint onto the type definition itself (preventing construction with
non-satisfying parameters) or leaves the impl absent entirely.

```metel
struct Pair<A, B> { first: A, second: B }

impl Printable for Pair<A, B> where A: Printable, B: Printable {
    fun print(self) { ... }
}
```

`Pair<i64, String>` is `Printable`; `Pair<i64, SomeNonPrintableType>` is not —
but both are constructable.

---

## 1. Syntax

Conditional bounds are written in a `where` clause on the `impl` block, after the
target type:

```metel
impl Aspect for Type<T> where T: Bound { ... }
impl Aspect for Type<T> where T: Bound1, T: Bound2 { ... }
impl Aspect for Type<A, B> where A: Bound1, B: Bound2 { ... }
```

Type parameters scoped to the impl block are written before the aspect name:

```metel
impl<T: Bound> Aspect for Type<T> { ... }
```

Both forms are equivalent. The `where` form is preferred for readability when bounds
are numerous; the inline form is preferred for simple single-parameter cases.

Negative bounds (RFC-0072) may appear in the `where` clause:

```metel
impl<T: !Drop> BulkDrop for Container<T> { ... }
```

---

## 2. Semantics

### 2.1 Use-site checking

A conditional impl is applicable at a use site when all conditions in its `where`
clause are satisfied by the concrete type arguments. The compiler checks the bounds
at every point where the aspect is required — method call, bound check, impl
selection — not at the impl declaration site.

```metel
fun print_pair<A: Printable, B: Printable>(p: Pair<A, B>) {
    p.print();   // ok — conditional impl applies; A: Printable and B: Printable
}

fun use_pair(p: Pair<i64, SomeNonPrintable>) {
    p.print();   // error — T0012: Pair<i64, SomeNonPrintable> does not implement Printable
                 //         because SomeNonPrintable does not implement Printable
}
```

### 2.2 Struct bounds and impl bounds are independent

A struct may have unconditional bounds on its type parameters (from RFC-0034), and
separately a conditional impl for an aspect. The struct bound governs construction;
the impl bound governs whether the aspect applies at a given call site. They are
checked independently.

```metel
struct SortedList<T: Comparable> { ... }

impl<T: Comparable + Printable> Printable for SortedList<T> {
    fun print(self) { ... }
}
```

`SortedList<T>` always requires `T: Comparable` (unconditional, governs construction).
The `Printable` impl additionally requires `T: Printable` (conditional, governs
whether `.print()` is callable).

### 2.3 Propagation through generic functions

A generic function that holds a value of type `Container<T>` can propagate the
conditional impl to its callers by including the relevant bound:

```metel
fun print_sorted<T: Comparable + Printable>(list: SortedList<T>) {
    list.print();   // ok — T: Printable, so the conditional impl applies
}
```

The function signature makes explicit which concrete instantiations are valid. The
compiler does not infer which bounds are needed; the author must state them.

---

## 3. Coherence

### 3.1 Overlap rule for conditional impls

Two conditional impls of the same aspect for the same type are a coherence error if
there exists any concrete instantiation for which both would apply (RFC-0060 §2).

The compiler uses **syntactic negation** to determine disjointness: two conditional
impls are accepted as non-conflicting only when one contains an explicit negative bound
(RFC-0072) that directly negates a positive bound in the other. No inference beyond
this direct negation check is performed.

```metel
// Accepted — T: !Copy directly negates T: Copy; provably disjoint
impl<T: Copy>  Serialize for Wrapper<T> { ... }
impl<T: !Copy> Serialize for Wrapper<T> { ... }
```

```metel
// Error T0015 — no direct negation between Clone and Display;
// the compiler cannot prove these are disjoint
impl<T: Clone>   Serialize for Wrapper<T> { ... }
impl<T: Display> Serialize for Wrapper<T> { ... }
```

To make the second example compile, the programmer must add an explicit negative bound
to establish disjointness:

```metel
impl<T: Clone, T: !Display> Serialize for Wrapper<T> { ... }
impl<T: Display>             Serialize for Wrapper<T> { ... }
```

This rule is intentional: disjointness appears explicitly in the source code, making
it visible and verifiable without running a constraint solver.

### 3.2 Conditional and unconditional impls

A conditional impl and an unconditional impl for the same type constructor are a
coherence error, because the unconditional impl covers all instantiations including
those the conditional impl would cover.

### 3.3 Orphan rule

Conditional impls are subject to the same orphan rule as unconditional impls
(RFC-0060 §1): the aspect or the outermost type constructor must be local.

---

## 4. Error Reporting

A failed conditional impl bound is reported with a diagnostic that names the
unsatisfied condition:

```
T0013: Pair<i64, SomeNonPrintable> does not implement Printable
       because SomeNonPrintable does not implement Printable
       (required by: impl<A: Printable, B: Printable> Printable for Pair<A, B>)
```

The error chain traces from the call site through the conditional impl to the
innermost unsatisfied bound.

---

## 5. Unresolved Questions

1. **Where clause on `impl` blocks for non-generic types.** Whether a non-generic
   type may have a conditional impl (e.g. `impl Aspect for Foo where SOME_CONST: Condition`)
   is deferred. The primary use case for conditional impls is generic types.

---

## References

- RFC-0034 — unconditional aspect bounds on struct/enum generic parameters;
  this RFC deferred conditional impls (Q6).
- RFC-0060 (Aspect Impl Coherence) — orphan rule and overlap detection; conditional
  impls must satisfy both.
- RFC-0061 (Structural Aspect Bounds) — blanket impls for structural type constructors;
  depends on the conditional impl mechanism defined here.
- RFC-0072 (Negative Bounds) — negative bounds in `where` clauses of conditional
  impls; §4 of RFC-0072 assumes this RFC.
