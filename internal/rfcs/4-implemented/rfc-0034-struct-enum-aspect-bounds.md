---
status: implemented
id: rfc-0034
title: "Aspect Bounds on Struct and Enum Generic Parameters"
date: '2026-06-01'
supersedes: rfc-0002 (partial)
---

## Summary

Define the syntax, enforcement model, and method-dispatch rules for aspect bounds on struct and enum generic type parameters. RFC-0002 deferred this topic; this RFC resolves it.

**Supersedes:** RFC-0002 (partial — this RFC covers struct/enum-specific questions deferred by RFC-0002, and also supersedes RFC-0002 Q2: inline multi-bound is now permitted with `+`, making inline and `where` clause equivalent)  
**Target:** v0.7.0

---

## Motivation

RFC-0002 shipped single-bound enforcement for function type parameters (`fun foo<T: Comparable>(x: T)`) and left struct/enum bounds explicitly out of scope. Without struct-level bounds it is impossible to write a generic data structure that guarantees its element type supports a required operation:

```metel
// Cannot currently express: T must implement Comparable to be stored in SortedList
struct SortedList<T> {
    items: T[],
}
```

Two concrete problems result:
1. The struct body cannot call any aspect methods on `T`, even when every real instantiation satisfies the bound.
2. Every function that receives a `SortedList<T>` and wants to sort it must re-declare `T: Comparable` itself, duplicating the constraint everywhere.

---

## Goals

1. Define the syntax for aspect bounds on struct and enum type parameters.
2. Define when the bound is enforced.
3. Define how bounds propagate into `impl` blocks and match arm bodies.
4. Produce grammar and AST changes ready for implementation.

## Non-Goals

- Conditional `impl` blocks (`impl Aspect for S<T> where T: OtherAspect`) — deferred to RFC-0036.
- Bounds on type aliases — future RFC.
- Higher-kinded bounds — future RFC.
- Conditional `impl` blocks — deferred to RFC-0036.

---

## Design

### Syntax

Inline bounds and `where` clause bounds are fully equivalent. Either form may be used for any number of bounds. Multiple bounds on a single type parameter may be expressed inline using `+`, or in a `where` clause, or a mix of both — the typechecker normalises all forms to the same internal representation.

**This supersedes RFC-0002 Q2**, which restricted inline bounds to a single bound and required multiple bounds to use the `where` clause. That restriction is lifted: `+` is now the inline conjunction operator for multiple bounds, and inline and `where` are interchangeable.

```metel
// Single bound — inline
struct SortedList<T: Comparable> {
    items: T[],
}

// Multiple bounds — inline with +
struct Window<T: Comparable + Display> {
    items: T[],
}

// Multiple bounds — where clause (equivalent to inline +)
struct Cache<K, V> where K: Hashable + Comparable {
    entries: Pair<K, V>[],
}

// Mixed — inline single bound plus additional bound in where clause (also valid)
struct Buffer<T: Comparable> where T: Display {
    items: T[],
}

enum Result<T: Printable, E: Printable> {
    Ok(T),
    Err(E),
}
```

All four forms above are semantically identical where applicable. The recommended style is inline `+` for short bound lists and `where` clause for longer or multi-parameter constraints, but both are always valid.

### Enforcement

Bounds are checked at **construction time**. Instantiating a bounded struct or enum with a concrete type that does not implement the declared aspect is error `T0012` ("Aspect bound not satisfied"), with the span on the offending type argument at the construction call site — not on the parameter declaration.

```metel
struct SortedList<T: Comparable> { items: T[] }

// error[T0012]: NonComparable does not implement Comparable
let list = SortedList<NonComparable> { items: [] }
```

Inside the struct's own method bodies and `impl` blocks, the typechecker treats bounded type parameters as having the declared aspect's methods in scope, without requiring any additional annotation.

### Bound Propagation into `impl` Blocks

`impl` blocks for a bounded struct inherit the struct's bounds without re-declaration:

```metel
struct SortedList<T: Comparable> { items: T[] }

impl SortedList<T> {
    fun insert(self, item: T) {
        // T: Comparable is in scope — aspect methods on item are valid
    }
}
```

Re-declaring the bound in the `impl` header is not required and is not an error, but is redundant.

### Bound Propagation into `impl AspectName for Struct<T>`

The same rule applies to aspect implementation blocks:

```metel
struct SortedList<T: Comparable> { items: T[] }

impl Printable for SortedList<T> {
    fun print(self) {
        // T: Comparable is in scope here — Comparable methods on T are valid
    }
}
```

### Bound Propagation into Match Arms

Struct and enum bounds are visible inside match arm bodies. The bound is an invariant of the type, not of the binding site. A value of type `SortedList<T>` always carries the guarantee that `T: Comparable`:

```metel
fun process<T: Comparable>(list: SortedList<T>) {
    match list {
        SortedList { items } => {
            // T: Comparable is available — no need to re-declare
        }
    }
}
```

### Grammar

```pest
struct_decl = { pub_kw? ~ "struct" ~ ident ~ generic_params? ~ where_clause? ~ "{" ~ field_list? ~ "}" }
enum_decl   = { pub_kw? ~ "enum"   ~ ident ~ generic_params? ~ where_clause? ~ "{" ~ variant_list? ~ "}" }
```

`generic_param` must be extended to support `+`-separated multiple bounds inline:

```pest
generic_param  = { ident ~ (":" ~ bound_list)? }
bound_list     = { type_expr ~ ("+" ~ type_expr)* }
```

The addition on struct/enum declarations is `where_clause?`. The `where_clause` and `where_constraint` productions from RFC-0002 must also be updated to use `bound_list`, since `where T: Display + Clone` is now valid:

```pest
where_clause     = { "where" ~ where_constraint ~ ("," ~ where_constraint)* }
where_constraint = { ident ~ ":" ~ bound_list }
```

This supersedes the RFC-0002 grammar for `where_constraint` (which used a single `type_expr`).

### AST Extension

The `TypeParam` struct must change from a single optional bound to a list of bounds to support inline `+`:

```rust
// Before (RFC-0002):
pub struct TypeParam {
    pub name: String,
    pub bound: Option<TypeExpr>,   // single bound only
}

// After (this RFC):
pub struct TypeParam {
    pub name: String,
    pub bounds: Vec<TypeExpr>,     // empty = unconstrained; multiple = all must be satisfied
}
```

Similarly, `WhereClause` must store a list of bounds per constraint:

```rust
// Before (RFC-0002):
pub struct WhereClause {
    pub constraints: Vec<(String, TypeExpr)>,
}

// After (this RFC):
pub struct WhereClause {
    pub constraints: Vec<(String, Vec<TypeExpr>)>,  // (param_name, [bound, ...])
}
```

The typechecker normalises both sources into the same `(param_name, [bounds])` map before enforcement — inline `+` bounds and `where` clause bounds for the same parameter are merged.

Add `where_clause` to `StructDecl` and `EnumDecl`:

```rust
pub struct StructDecl {
    pub name: String,
    pub generic_params: Vec<TypeParam>,
    pub where_clause: Option<WhereClause>,  // new
    pub fields: Vec<FieldDecl>,
    pub span: Span,
}

pub struct EnumDecl {
    pub name: String,
    pub generic_params: Vec<TypeParam>,
    pub where_clause: Option<WhereClause>,  // new
    pub variants: Vec<VariantDecl>,
    pub span: Span,
}
```

---

## Out of Scope

| Feature | Deferred to |
|---|---|
| Conditional impls (`impl Aspect for S<T> where T: Other`) | RFC-0036 |
| Bounds on type aliases | Future RFC |
| Higher-kinded bounds | Future RFC |

---

## Resolved Questions

1. **Syntax:** Inline and `where` clause are fully equivalent. Multiple bounds inline use `+` (`<T: A + B>`). `where` clause form also valid. **Supersedes RFC-0002 Q2** (which restricted inline to a single bound). The `+` inline form is now canonical for multiple bounds.

2. **Enforcement point:** At construction time only (plus body-level method access). A value of a bounded type can never be constructed without satisfying the bound. Error code `T0012`, span on the offending type argument at the construction call site.

3. **Propagation into `impl` blocks:** Inherited automatically. No re-declaration needed or enforced.

4. **Propagation into `impl AspectName for Struct<T>` blocks:** Inherited automatically, consistent with rule 3.

5. **Propagation into match arms:** Yes. The bound is a type invariant. The typechecker propagates it into match arm bodies wherever a value of the bounded type is in scope.

6. **Conditional impls:** Deferred to RFC-0036. This RFC covers unconditional declaration-level bounds only. Conditional impls require coherence and overlap checking beyond this scope.

---

## Decision

**Outcome:** Accepted  
**Target:** v0.7.0

All resolved questions above are the final decisions. Implementation tracked in METEL-57 (T0012 error code, impl_aspect_env lookup) and METEL-60 (grammar, AST, parser, typechecker enforcement, bound propagation).
