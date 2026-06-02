---
id: rfc-0042
title: "let mut for Mutable Bindings"
date: '2026-06-02'
status: draft
spec_status: pending
---

## Summary

Replace standalone mutable binding declarations with `let mut` declarations.

```metel
// Before
mut counter = 0;
pub mut cache: Int[] = [];

// After
let mut counter = 0;
pub let mut cache: Int[] = [];
```

The `mut` keyword remains the marker for mutability, but `let` becomes the only keyword that introduces value bindings. This makes mutable and immutable declarations one syntactic family:

```metel
let name = "Ada";
let mut counter = 0;
```

---

## Motivation

Metel currently uses two binding introducers:

```metel
let value = 1;
mut counter = 0;
```

This makes `mut` serve two roles:

- declaration introducer for mutable bindings
- mutability modifier in other positions, such as `mut self`, `*mut T`, and `&mut x`

Using `let mut` keeps `mut` consistently modifier-like. A binding is introduced by `let`; mutability is an attribute of that binding. This also matches the shape used by Rust and makes declarations easier to scan, especially beside `pub`:

```metel
pub let value = 1;
pub let mut counter = 0;
```

---

## Design

### Binding Declarations

The canonical syntax for value bindings becomes:

```metel
let IDENTIFIER ( ":" Type )? "=" Expression ";"
let mut IDENTIFIER ( ":" Type )? "=" Expression ";"
```

`let` creates an immutable binding. `let mut` creates a mutable binding.

```metel
let x = 1;
let y: Int = 2;
let mut count = 0;
let mut total: Int = 0;
```

The mutability semantics are unchanged:

- immutable bindings cannot be assigned after initialization
- mutable bindings can be assigned after initialization
- all bindings must be initialized at declaration
- type annotations remain optional
- binding visibility and shadowing rules are unchanged

### Public Bindings

For top-level public bindings, `pub` continues to prefix the declaration:

```metel
pub let version = "0.8.0";
pub let mut global_counter = 0;
```

`pub mut name = value;` is replaced by `pub let mut name = value;`.

### For-Loop Initializers

C-style `for` loop initializers use the same declaration syntax:

```metel
for (let mut i = 0; i < 10; i += 1) {
    // ...
}
```

The old `for (mut i = 0; ... )` form is replaced by `for (let mut i = 0; ... )`.

### For-In Bindings

For-in loop bindings remain immutable by default:

```metel
for (let item in items) {
    // item is immutable
}
```

This RFC also allows a mutable iteration binding:

```metel
for (let mut item in items) {
    item = normalize(item);
}
```

The mutable iteration binding only permits reassignment of the loop-local binding. It does not mutate the collection element in place.

### Other Uses of `mut`

This RFC does not change other uses of `mut`:

```metel
fun increment(mut self) { ... }

let p: *mut Int = &mut counter;
```

`mut self`, `*mut T`, and `&mut x` keep their current spelling and semantics.

---

## Grammar Changes

The declaration grammar changes from separate `LetDeclaration` and `MutDeclaration` forms to one binding declaration with an optional `mut` modifier:

```text
BindingDeclaration -> "pub"? "let" "mut"? IDENTIFIER ( ":" Type )? "=" Expression ";"
```

The C-style `for` initializer accepts a binding declaration:

```text
ForInit -> BindingDeclaration | ExpressionStatement | ";"
```

The for-in grammar permits the same mutability modifier on the loop binding:

```text
ForInStatement -> "for" "(" "let" "mut"? IDENTIFIER "in" Expression ")" Block
```

---

## Migration

The migration is mechanical:

| Before | After |
|---|---|
| `mut x = value;` | `let mut x = value;` |
| `mut x: T = value;` | `let mut x: T = value;` |
| `pub mut x = value;` | `pub let mut x = value;` |
| `for (mut i = 0; cond; step)` | `for (let mut i = 0; cond; step)` |

Open migration question:

- Should the old standalone `mut` declaration remain accepted for one release as a compatibility alias, or become a parse error immediately?

---

## Resolved Decisions

### D1 - One-version compatibility window

`mut x = value;` remains accepted as a compatibility alias for `let mut x = value;` for one minor-version transition window. After that window, the old form should become a hard error.

### D2 - Mutable for-in bindings are included

This RFC includes `for (let mut item in items)` so that loop-local bindings use the same mutable-binding syntax as ordinary declarations. The binding itself is reassignable; this does not imply in-place mutation of the iterated source element.

### D3 - Initial implementation keeps the current AST split

The parser may lower `let mut` into the existing mutable-declaration node shape for the initial implementation. A later internal cleanup may merge declaration nodes if that removes real complexity, but this RFC does not require that refactor.

---

## Decision

**Outcome:** Under review

The user-visible syntax and migration behavior are resolved here. Remaining work is implementation and follow-through in examples, tests, and the spec.
