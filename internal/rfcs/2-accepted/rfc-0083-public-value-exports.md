---
id: rfc-0083
title: "Public Value Exports"
date: '2026-07-01'
---

> **Status — accepted.** Extends the module system (RFC-0030, implemented) to allow
> module-level `let` bindings to be marked `pub`, making them importable by other
> modules. The current spec explicitly withholds this: "public value exports are not
> supported in the current version." This RFC specifies the semantics and lifts that
> restriction.

## Summary

RFC-0030 permits `pub` on structs, enums, funs, and aspects. Module-level `let`
bindings are always private in the current design. This RFC adds `pub` semantics to
module-level `let` bindings so that named values — not only types and functions — can
be exported and imported.

The motivating case is `heap` and `local_heap` in `std::mem`: region handles that
user code passes to the bracket channel. They need to be importable as values.

---

## Motivation

`Heap` and `LocalHeap` are unit structs that implement `Region`. User code uses a
value of each type in the bracket channel:

```metel
import std::mem::heap;

let node = @[heap] Node { val: 1 };
```

The bracket channel position expects a runtime value — the same as any region handle
`r` bound in a bracket parameter. Without an importable value, the user must construct
one explicitly (`@[Heap {}]`) every time, which is verbose and requires importing the
type `Heap` rather than the ready-made singleton `heap`.

`pub let` resolves this: `std::mem` exports `heap` as a named value of type `Heap`,
the user imports it, and `@[heap]` is an ordinary value reference with no special
cases.

Metel has a single module namespace — types and values share the same name pool. The
`Heap` / `heap` naming convention (PascalCase for the type, snake_case for the
singleton value) prevents collision and follows the existing convention for all other
Metel declarations.

The same mechanism generalises to any stdlib or user-defined constant that should be
shared across module boundaries: error codes, default configuration, sentinel values.

---

## 1. `pub let` declarations

A module-level `let` binding may be marked `pub`:

```metel
pub let heap: Heap = Heap {};
pub let local_heap: LocalHeap = LocalHeap {};
pub let MAX_CONNECTIONS: u64 = 1024;
```

`pub let` declares a named, typed, immutable value that is part of the module's public
API. There is no `pub let mut` — mutable module-level state is not exported.

The type annotation is required. The initialiser must be a **constant expression** —
defined as: literal values, arithmetic on literals, struct constructors whose fields
are constant expressions, and calls to functions declared `comptime` (RFC-0055). This
RFC does not extend the definition of constant expressions; it defers to RFC-0055 for
the full specification.

For the immediate use case, unit struct constructors (`Heap {}`, `LocalHeap {}`) are
constant expressions under any reasonable definition.

---

## 2. Importing `pub let` values

A `pub let` value is imported with the same `import` syntax as types and functions:

```metel
import std::mem::heap;
import std::mem::local_heap;
import std::mem::{heap, local_heap};
```

After import, the name is bound in the current scope and may be used anywhere a value
of the declared type is accepted:

```metel
import std::mem::{Heap, heap};

let node = @[heap] Node { val: 1 };   // heap as a bracket-channel value
let h: Heap = heap;                   // heap as a value in an expression
```

The value is always read-only at the import site — it is not a mutable binding.

---

## 3. `std::mem` definitions

In `std::mem`, the types and their singleton values are separate declarations with
distinct names:

```metel
// std/mem.mtl (conceptual)
pub struct Heap {}
impl Region for Heap { type AllocationError = !; … }
pub let heap: Heap = Heap {};

pub struct LocalHeap {}
impl Region for LocalHeap { type AllocationError = !; … }
pub let local_heap: LocalHeap = LocalHeap {};
```

Importing the type (`Heap`) and importing the value (`heap`) are independent. User
code that only needs to annotate types imports `Heap`; code that allocates imports
`heap`. Both may be imported in the same statement:

```metel
import std::mem::{Heap, heap, LocalHeap, local_heap};
```

---

## 4. `export` re-exports

A `pub let` value may be re-exported with the existing `export` declaration:

```metel
// my_project/prelude.mtl
export std::mem::heap;
export std::mem::local_heap;
```

Re-exported names carry the same semantics as at their definition site.

---

## 5. `std::core` auto-import

RFC-0030 auto-imports `std::core` at the lowest priority tier. This RFC does not
change that rule. `heap`, `local_heap`, and other `std::mem` values are not added to
`std::core`; they must be imported explicitly.

---

## 6. Implementation requirements

The current implementation does not support `pub let`:

- `LetDecl` in the AST has no `visibility` field.
- The name resolver's `decl_pub_name` function does not handle `Decl::Let`.
- The parser's `parse_let_decl` does not check for a leading `pub` keyword.

Implementing this RFC requires:

1. Add `visibility: Visibility` to `LetDecl` in `ast/mod.rs`.
2. Update `parse_let_decl` in `parser/mod.rs` to parse an optional leading `pub`.
3. Update `decl_pub_name` in `name_resolver.rs` to include
   `Decl::Let(d) if d.visibility == Visibility::Public => Some(d.name.clone())`.
4. Update the evaluator to expose module-level `pub let` values through the module
   scope, so they are accessible to importers.

---

## 7. What does not change

Everything in RFC-0030 and the current module spec is unchanged:

- `import` and `export` syntax and semantics.
- File-to-module mapping (`::` → `/`).
- Visibility rules for types, functions, and aspects.
- `pub` on `struct`, `enum`, `fun`, `aspect` fields.
- Circular import detection.
- `std::core` auto-import priority tiers.
- `pub let mut` remains invalid — mutable module-level state is never exported.

---

## Unresolved Questions

1. **Constant expression scope.** The full definition of what initialisers are legal
   in `pub let` is deferred to RFC-0055 (Comptime). Until RFC-0055 is accepted, legal
   initialisers are restricted to literals and unit struct constructors.

---

## References

- RFC-0030 (Module System Redesign) — implemented module system this RFC extends;
  grammar already permits `pub` on `let` syntactically.
- RFC-0055 (Comptime) — constant expression definition; governs `pub let` initialisers.
- RFC-0063 (Region Handles) — bracket channel; `heap` and `local_heap` are used as
  region handles in `@[heap]` expressions, the primary motivating case.
- RFC-0073 (AutoRegion) — context for why `heap` and `local_heap` are importable by
  user code.
