---
status: active
id: rfc-0039
title: "aspect Alias Syntax"
date: '2026-06-01'
deferred_from: rfc-0002 (Q7), referenced in rfc-0035 (Q4)
---

## Summary

Design the syntax and semantics for naming compound aspect bounds as aliases. RFC-0002 Q7 proposed this; RFC-0035 Q4 referenced it as the right mechanism for type aliases that name a bound. This RFC designs it.

---

## Motivation

Compound bounds that appear in many signatures should be nameable. The alternative is repetition that drifts out of sync when the compound bound changes:

```metel
// Without aspect aliases: repeated compound bound
fun sort<T: Comparable + Display + Clone>(items: T[]) -> T[] { ... }
fun filter<T: Comparable + Display + Clone>(items: T[], pred: fun(T) -> boolean) -> T[] { ... }

// With aspect alias:
aspect Sortable = Comparable + Display + Clone

fun sort<T: Sortable>(items: T[]) -> T[] { ... }
fun filter<T: Sortable>(items: T[], pred: fun(T) -> boolean) -> T[] { ... }
```

---

## Open Questions

### Q1 — Syntax of the alias declaration

**Option A — `aspect Alias = A + B + C` (recommended):** Uses `+` as the aspect combination operator. Reads as "Alias is the combination of A, B, and C".

**Option B — `aspect Alias: A + B + C`:** Uses the existing bound syntax `:`. Reads as "Alias requires A, B, and C".

**Option C — `type Alias = A & B & C`:** Uses `&` to avoid conflict with future arithmetic on aspect expressions.

**Proposal: Option A.** `+` is the established operator for combining bounds in most languages with this feature (Rust, Scala, Swift). `=` is the natural assignment-style alias form.

### Q2 — Is an aspect alias a new aspect or just a shorthand?

**Option A — Shorthand only (recommended):** `aspect Sortable = Comparable + Display + Clone` is purely a compile-time alias. A type that implements all three automatically satisfies `Sortable`. No new `impl Sortable for T` is needed or allowed.

**Option B — New aspect requiring an explicit impl:** `Sortable` is a distinct aspect. Types must explicitly `impl Sortable for T { ... }` in addition to implementing the component aspects.

**Proposal: Option A.** Option B creates redundant work and a sync hazard (a type may implement all three components but forget to add `impl Sortable`). An alias should be transparent.

### Q3 — Can an alias include another alias?

```metel
aspect Sortable = Comparable + Display + Clone
aspect SortableAndPrintable = Sortable + Printable  // alias of an alias
```

**Option A — Yes (recommended):** Aliases are expanded recursively at compile time. Cycles are a compile error.

**Option B — No; only concrete aspects may appear in an alias.**

**Proposal: Option A.** Disallowing alias composition would make the feature significantly less useful for building layered abstractions.

### Q4 — Can an aspect alias be used as a bound on struct/enum generic params (RFC-0034)?

**Proposal: Yes.** `struct SortedList<T: Sortable>` is valid and expands to `T: Comparable + Display + Clone`. The struct's bounds are enforced at construction as per RFC-0034.

### Q5 — Interaction with `impl Aspect` (RFC-0035)

**Proposal:** `fun foo(x: impl Sortable)` is valid and desugars to a type variable with all component bounds. The error message when the bound is not satisfied should name `Sortable` (not expand it to the components), so the user sees the alias name they wrote.

---

## Decision

**Outcome:** Draft — open for review

All questions above need resolution before implementation. Once accepted, this provides a shorthand mechanism for compound bounds used with RFC-0034 and RFC-0035.
