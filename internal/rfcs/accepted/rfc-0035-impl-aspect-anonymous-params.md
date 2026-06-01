---
id: rfc-0035
title: "impl Aspect Anonymous Type Parameters"
date: '2026-06-01'
supersedes: rfc-0002 (partial)
---

## Summary

Define the syntax, desugaring rules, and restrictions for `impl Aspect` as an anonymous bounded type parameter in function parameter position. RFC-0002 Q3 proposed this feature; this RFC resolves the design details before implementation begins.

**Supersedes:** RFC-0002 (partial — the named type parameter and `where` clause decisions in RFC-0002 stand; this RFC specifies the `impl Aspect` shorthand form)  
**Target:** v0.7.0

---
:
## Motivation

Named type parameters are verbose when a type variable is used only once and is never cross-referenced within the signature:

```metel
// Named — T appears only once and is never referenced again
fun print_all<T: Printable>(items: T[]) { ... }

// Proposed shorthand
fun print_all(items: impl Printable[]) { ... }
```

Every single-use bounded parameter currently forces an explicit type variable name that adds no information. The RFC-0002 decision to include `impl Aspect` was correct, but the semantic details were deferred. This RFC pins them down.

---

## Goals

1. Define the desugaring strategy for `impl Aspect` in parameter position.
2. Define the semantics of multiple `impl Aspect` occurrences in one signature.
3. Define the positions where `impl Aspect` is and is not permitted.
4. Define error message requirements for violated anonymous bounds.
5. Define the interaction with explicit named type parameters in the same signature.

## Non-Goals

- `impl Aspect` in return position — deferred to RFC-0037.
- `impl Aspect` in struct fields or as a type alias — existential types (RFC-0038) and aspect aliases (RFC-0039) cover those cases respectively.

---
:
## Design

### `impl Aspect` is Pure Syntactic Sugar

`impl Aspect` in parameter position desugars to a fresh anonymous named type parameter during an AST lowering pass that runs before the typechecker. The typechecker never sees `impl Aspect`; it sees only named type parameters.

```metel
fun foo(x: impl Display)
// desugars to:
fun foo<_T0: Display>(x: _T0)

fun print_all(items: impl Printable[])
// desugars to:
fun print_all<_T0: Printable>(items: _T0[])
```

The lowering pass is a dedicated phase between parsing and typechecking. It walks every `ImplAspect` type expression node and replaces it with a fresh `TypeParam` whose bound is the named aspect, attaching source-spelling metadata to the generated variable (see Error Messages below).

### Multiple Occurrences Are Independent

Each `impl Aspect` occurrence in a signature generates a **fresh, independent** type variable. Two parameters typed `impl Comparable` are not required to have the same concrete type:

```metel
fun compare(a: impl Comparable, b: impl Comparable) -> Bool { ... }
// desugars to:
fun compare<_T0: Comparable, _T1: Comparable>(a: _T0, b: _T1) -> Bool { ... }
```

`compare(1, "hello")` is valid as long as both `Int` and `String` implement `Comparable`. To constrain two parameters to the same type, use a named type parameter: `fun compare<T: Comparable>(a: T, b: T)`.

### Permitted Positions

`impl Aspect` is permitted **only in function parameter position** in this RFC.

| Position | Permitted? | Note |
|---|---|---|
| Function parameter type | Yes | This RFC |
| Function return type | No | RFC-0037 |
| Struct field type | No | RFC-0038 (`dyn Aspect`) |
| Type alias | No | RFC-0039 (`aspect` alias syntax) |
| `let`/`mut` binding annotation | No | Use a named param |

The parser (or a post-parse validation pass) must reject `impl Aspect` in all non-parameter positions with an error that names the correct RFC for the deferred case.

### Mixing with Named Type Parameters

`impl Aspect` and named type parameters may coexist freely in the same signature. The anonymous parameter has no special relationship to any named parameter:

```metel
fun zip<T>(a: impl Iterable, b: T) -> Pair<T, T> { ... }
// desugars to:
fun zip<T, _T0: Iterable>(a: _T0, b: T) -> Pair<T, T> { ... }
```

### Error Messages

When a bound is not satisfied, error messages must reference the **source spelling** (`impl Display`), not the generated internal name (`_T0`). The desugaring pass annotates each generated `TypeParam` with:

- `source_spelling: String` — the text `"impl Display"` as written by the programmer
- `source_span: Span` — the span of the `impl Display` node in the source

The typechecker uses `source_spelling` when generating `T0012` for an anonymous parameter:

```
error[T0012]: argument does not implement Display
  --> main.mtl:3:12
fun foo(x: impl Display)
           ^^^^^^^^^^^^ this parameter requires Display
```

Never expose the generated name (`_T0`) in user-facing error messages.

### Grammar

New production added to `type_expr`:

```pest
impl_type = { "impl" ~ type_expr }
// Added as an alternative in type_expr — parameter position only
```

A validation pass after parsing rejects `impl_type` nodes that appear outside function parameter position.

### AST

New `TypeExpr` variant for the pre-lowering AST:

```rust
pub enum TypeExpr {
    // ... existing variants ...
    ImplAspect {
        bound: Box<TypeExpr>,
        source_span: Span,
    },
}
```

The lowering pass eliminates all `ImplAspect` nodes before the typechecker runs, replacing each with a generated `TypeParam` and recording the source spelling for error messages.

---

## Out of Scope

| Feature | Deferred to |
|---|---|
| `impl Aspect` in return position | RFC-0037 |
| `impl Aspect` in struct fields / existential types | RFC-0038 |
| `aspect` alias syntax (`aspect Sortable = A + B`) | RFC-0039 |
| Conditional impls | RFC-0036 |

---
:
## Resolved Questions

1. **Sugar vs distinct form:** Pure syntactic sugar. `impl Aspect` desugars to a fresh anonymous `TypeParam` in a pre-typechecking lowering pass. The typechecker sees only named type parameters.

2. **Multiple occurrences:** Each occurrence is a fresh, independent type variable. Two `impl Comparable` params may be different concrete types. Use a named param to enforce the same type.

3. **Return position:** Not permitted in this RFC. Return-position `impl Aspect` requires careful design around opaque types, inference, and monomorphisation — deferred to RFC-0037.

4. **Struct fields and type aliases:** Not permitted in this RFC. Struct fields require existential type support (`dyn Aspect`, RFC-0038). Type aliases that name a bound are the job of `aspect` aliases (RFC-0039).

5. **Error messages:** The desugaring pass attaches `source_spelling` and `source_span` to each generated `TypeParam`. Error messages name the aspect (`impl Display`), never the internal generated variable name.

6. **Mixing with named type parameters:** Allowed freely. The anonymous parameter is independent of any named parameter in the same signature.

---

## Decision

**Outcome:** Accepted  
**Target:** v0.7.0

All resolved questions above are the final decisions. Implementation tracked in METEL-57 (AST lowering pass, error message metadata, T0012 enforcement with source spelling).
