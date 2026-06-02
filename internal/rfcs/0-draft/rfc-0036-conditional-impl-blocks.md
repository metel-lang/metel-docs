---
status: active
id: rfc-0036
title: "Conditional impl Blocks for Aspects"
date: '2026-06-01'
deferred_from: rfc-0034 (Q6)
---

## Summary

Design conditional impl blocks where an aspect implementation for a generic struct is only valid when its type parameters satisfy additional constraints. RFC-0034 accepted unconditional aspect bounds on struct/enum generic parameters and deferred this case. This RFC addresses conditional impls.

---

## Motivation

With RFC-0034, you can declare `struct Pair<A: Printable, B: Printable>` to require both fields to be printable. But sometimes you want a struct to be printable **only when** its type params are — without requiring the constraint unconditionally:

```metel
struct Pair<A, B> { first: A, second: B }

// Pair<A, B> is Printable only when both A and B are
impl Printable for Pair<A, B> where A: Printable, B: Printable {
    fun print(self) { ... }
}

// Pair<A, B> is still usable when A or B are not Printable — just not as Printable
```

This is impossible to express with RFC-0034's unconditional bounds, which would prevent constructing `Pair<Int, SomeNonPrintableType>` entirely.

---

## Open Questions

### Q1 — Syntax of conditional `impl` where clause

**Option A (recommended):** `impl AspectName for TypeName<T> where T: OtherAspect { ... }` — mirrors the function `where` clause syntax from RFC-0002.

**Option B:** `impl<T: OtherAspect> AspectName for TypeName<T> { ... }` — Rust-style with the constraint in the impl type parameter list.

**Proposal: Option A.** Consistent with the existing `where` clause syntax already established for functions and structs.

### Q2 — Coherence: can two conditional impls overlap?

Example: `impl Printable for Pair<A, B> where A: Printable` and `impl Printable for Pair<A, B> where B: Printable`. When both `A` and `B` are `Printable`, which impl applies?

**Option A — Overlap is a compile error (recommended):** Two conditional impls for the same aspect on the same type must not have overlapping constraint sets. The compiler rejects ambiguous configurations at the point where the impl blocks are declared.

**Option B — First-match wins:** Impls are checked in declaration order; the first matching impl applies.

**Proposal: Option A.** First-match semantics are fragile and order-dependent. A compile error at the declaration site is safer and more predictable.

### Q3 — Interaction with unconditional impls (RFC-0034)

If a struct has an unconditional bound (`struct SortedList<T: Comparable>`) and there is also a conditional impl (`impl Printable for SortedList<T> where T: Printable`), how do they interact?

**Proposal:** The struct's unconditional bound and the impl's conditional bound are independent. The struct bound governs construction; the impl bound governs whether the `Printable` impl applies at a given call site. The typechecker checks both independently.

### Q4 — Error reporting: what message when the conditional impl's bound is not satisfied?

**Option A (recommended):** `T0013: Pair<Int, NonPrintable> does not implement Printable because NonPrintable does not implement Printable` — names the unsatisfied constraint.

**Option B:** Reuse `T0012` with a note about the conditional impl.

**Proposal: Option A.** A distinct error code makes it clear the failure is in a conditional impl's constraint, not in a direct bound on the type argument.

---

## Decision

**Outcome:** Draft — open for review

All questions above need resolution before implementation. Once accepted, update METEL-57/58/60 with conditional impl scope.
