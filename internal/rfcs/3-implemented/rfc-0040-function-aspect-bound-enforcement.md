---
status: incorporated
id: rfc-0040
title: "Aspect Bound Enforcement on Function Type Parameters"
date: '2026-06-01'
supersedes: rfc-0002 (enforcement)
---

## Summary

Define the typechecker enforcement of aspect bounds on function generic type parameters. RFC-0002 designed the syntax and was partially implemented (parsing only). The actual typechecker enforcement — verifying that call-site type arguments satisfy declared bounds, making bound methods available in function bodies, and producing the correct error — was never implemented. This RFC pins down the implementation contract.

**Supersedes:** RFC-0002 (enforcement section only — all syntax decisions from RFC-0002 stand unchanged)  
**Target:** v0.7.0

---

## Background

RFC-0002 accepted the following syntax decisions. RFC-0034 additionally superseded RFC-0002 Q2 by allowing inline `+` for multiple bounds, making inline and `where` clause equivalent. Both forms are already parsed:

```metel
// Single bound — inline
fun largest<T: Comparable>(a: T, b: T) -> T { ... }

// Multiple bounds — inline with + (supersedes RFC-0002 Q2)
fun print_and_sort<T: Display + Comparable>(items: T[]) { ... }

// Multiple bounds — where clause (equivalent to inline +)
fun foo<T, U>(x: T, y: U) -> T
    where T: Display + Clone,
          U: Iterable<T>
```

The parser accepts all these forms. What was never implemented:
1. The typechecker does not verify that type arguments at call sites satisfy the declared bounds.
2. Bound methods are not made available inside the function body.
3. No error is produced when a bound is violated.

RFC-0034 solved the same problem for structs and enums. RFC-0035 solved it for `impl Aspect` desugaring. This RFC applies the same model to named function type parameters.

---

## Decisions

All decisions are inferred from RFC-0002 (syntax), RFC-0034 (enforcement model), and RFC-0035 (error messages). No new design work is required.

### 1 — Enforcement point: call site

Bounds are checked when a generic function is called with concrete type arguments, either explicitly (`largest<Int>(a, b)`) or inferred by the typechecker from the argument types.

This is the same enforcement point as RFC-0034 (struct/enum construction). Consistent model: bounds are always checked at the point of use, not the point of declaration.

```metel
fun largest<T: Comparable>(a: T, b: T) -> T { ... }

largest(1, 2)          // OK — Int implements Comparable
largest("x", "y")     // error[T0012] if String does not implement Comparable
```

### 2 — Error code and span

Same as RFC-0034: **T0012** ("Aspect bound not satisfied"), span on the offending type argument at the call site.

```
error[T0012]: Int does not implement Display
  --> main.mtl:5:8
foo(42)
    ^^ argument of type Int does not satisfy bound Display
```

For bounds inferred from arguments (no explicit type annotation), the span falls on the argument expression itself.

### 3 — Bound methods in the function body

Inside the function body, the typechecker treats a bounded type parameter as having the declared aspect's methods available, without any additional annotation. This mirrors RFC-0034's propagation into `impl` blocks.

```metel
fun print_all<T: Display>(items: T[]) {
    for item in items {
        item.display()   // OK — T: Display is in scope, display() is available
    }
}
```

If a function calls an aspect method on a type parameter that does not have the corresponding bound declared, the typechecker produces **T0013** ("Method not found on unconstrained type parameter").

### 4 — Inline `+` and `where` clause are fully equivalent

Bounds declared inline with `+` and bounds declared in a `where` clause are enforced identically. The typechecker normalises all forms to the same internal representation (a map from type parameter name to a list of required aspects) before enforcement. This applies equally to all combinations:

```metel
// All three of these are identical at the typechecker level:
fun foo<T: Display + Clone, U: Iterable<T>>(x: T, y: U) -> T { ... }

fun foo<T, U>(x: T, y: U) -> T
    where T: Display + Clone, U: Iterable<T> { ... }

fun foo<T: Display, U: Iterable<T>>(x: T, y: U) -> T
    where T: Clone { ... }
```

This is consistent with RFC-0034's syntax decision, which superseded RFC-0002 Q2 (the old restriction that inline bounds were limited to a single bound and multiple bounds required a `where` clause).

### 5 — Multiple bounds: all must be satisfied

When a type parameter has multiple bounds (via `where`), all of them must be satisfied at the call site. The typechecker checks each bound independently. If more than one is unsatisfied, a T0012 error is emitted for each unsatisfied bound.

### 6 — Interaction with impl Aspect desugaring (RFC-0035)

`impl Aspect` parameters are desugared to named type parameters before the typechecker runs. The enforcement defined here applies equally to named type parameters introduced by desugaring. The `source_spelling` metadata (RFC-0035) is used for error messages on desugared parameters, so users see `impl Display` rather than the generated name `_T0`.

### 7 — Generic functions in impl blocks

Bounds on generic functions defined inside `impl` blocks are enforced with the same rules. The `impl` block's own type parameter bounds (from RFC-0034) are in scope and do not need to be re-declared on individual methods:

```metel
struct SortedList<T: Comparable> { items: T[] }

impl SortedList<T> {
    fun find<U: Display>(self, needle: U) -> boolean {
        // T: Comparable is in scope (from struct bound, RFC-0034)
        // U: Display is in scope (from this method's bound)
    }
}
```

---

## Non-Goals

- `impl Aspect` in return position — RFC-0037
- Conditional impls — RFC-0036
- Higher-kinded bounds — future RFC
- Associated type constraints — future RFC

---

## Implementation Notes

### AST prerequisite (RFC-0034)

RFC-0034 changes `TypeParam.bound: Option<TypeExpr>` → `TypeParam.bounds: Vec<TypeExpr>` and `WhereClause.constraints: Vec<(String, TypeExpr)>` → `Vec<(String, Vec<TypeExpr>)>`. All function-level enforcement in this RFC depends on that AST change landing first (METEL-60).

### Normalisation

Before enforcement, the typechecker must merge inline bounds and `where` clause bounds for the same parameter into a single list. Given:

```metel
fun foo<T: Display + Clone>(x: T) where T: Comparable { ... }
```

The effective bound list for `T` is `[Display, Clone, Comparable]`. Duplicates are ignored.

### Enforcement algorithm

1. After type inference, walk all function call expressions.
2. For each generic function call, resolve the concrete type arguments (explicit or inferred).
3. Merge inline `TypeParam.bounds` and matching `where_clause` entries into a single bound list per type parameter.
4. For each bound in the list, check whether the concrete type argument has a registered `impl AspectName for T` in `impl_aspect_env`.
5. If not, emit T0012 with span on the call-site argument.

The bound-availability pass for function bodies (decision 3) seeds the type environment with the merged bound list so all aspect methods are in scope inside the function.

---

## Decision

**Outcome:** Accepted  
**Target:** v0.7.0

All decisions above are final. No open questions remain — all design points are direct applications of RFC-0002 (syntax), RFC-0034 (enforcement model and error codes), and RFC-0035 (error message metadata). Implementation may proceed once the RFC-0034 implementation work (METEL-60) is merged, as this RFC shares the same typechecker infrastructure.
