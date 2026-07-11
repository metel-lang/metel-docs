---
id: rfc-0083
title: "Public Value Exports"
date: '2026-07-01'
status: integrated
updated: '2026-07-10'
impl_tracking: 'https://codeberg.org/metel-lang/metel-core/issues/235'
impl_status: not-started
---

> **Status — accepted.** Extends the module system (RFC-0030, implemented) to allow
> module-level `let` bindings to be marked `pub`, making them importable by other
> modules. The current spec explicitly withholds this: "public value exports are not
> supported in the current version." This RFC specifies the semantics and lifts that
> restriction.
>
> **Amended 2026-07-10, while integrating into the spec.** The original Motivation below
> was written entirely around `heap`/`local_heap` needing an importable singleton value
> for the pre-split bracket-channel model (`@[heap] Node {...}`). Under the ratified
> allocator design (RFC-0063/0065, accepted 2026-07-10), `Heap`/`LocalHeap` are referenced
> directly by type name — `@Heap expr` — with no instance value ever constructed anywhere
> in that cluster; the singleton-value problem this RFC set out to solve no longer exists
> for that specific case. The mechanism itself (`pub let`) is independently useful and not
> affected — module-level exported constants are a real, common need regardless of
> allocators — so the Motivation is rewritten below to lead with that case instead of a
> now-obsolete one. Terminology elsewhere in this RFC (bracket channel, RFC-0055, old
> RFC-0063/0073 titles) is also corrected to match the ratified cluster.

> **Status — integrated (2026-07-10).** Integrated into public/reference/spec/modules.md: pub let declarations, import/export. RFC's heap/local_heap motivating example rewritten (obsolete under the ratified allocator design; mechanism itself unaffected).

## Summary

RFC-0030 permits `pub` on structs, enums, funs, and aspects. Module-level `let`
bindings are always private in the current design. This RFC adds `pub` semantics to
module-level `let` bindings so that named values — not only types and functions — can
be exported and imported.

The motivating case is exported constants shared across module boundaries: error codes,
default configuration, sentinel values — anything a module wants to expose as a named
value rather than requiring every importer to redeclare the same literal.

---

## Motivation

Metel has no way to share a named constant value across modules. A module defining a
protocol limit, a default timeout, or a well-known sentinel has to either duplicate the
literal at every use site or wrap it in a zero-argument function purely to make it
importable:

```metel
// workaround: a function standing in for a constant, only because pub let doesn't exist
pub fun max_connections() -> u64 { 1024 }
```

`pub let` removes the workaround: a module-level `let` marked `pub` is directly
importable as a named value, with the same visibility rules already governing `pub` on
`struct`/`enum`/`fun`/`aspect`:

```metel
// definition
pub let MAX_CONNECTIONS: u64 = 1024;

// importer
import my_module::MAX_CONNECTIONS;
let limit = MAX_CONNECTIONS;
```

Metel has a single module namespace — types and values share the same name pool. This
RFC introduces no new naming convention beyond what already exists for any other Metel
declaration.

**A previously-considered motivating case no longer applies, noted honestly rather than
silently dropped.** An earlier draft of this RFC used `std::mem`'s `heap`/`local_heap`
singleton values (needed for the pre-split bracket-channel allocator model) as the
driving example. Under the ratified allocator design, `Heap` and `LocalHeap` are used
directly by type name in allocation expressions (`@Heap expr`, RFC-0065 §1) — no
instance value is ever constructed for either, so there is nothing for `pub let` to
export in that specific case anymore. This RFC's actual mechanism doesn't depend on that
example in any way; the exported-constants case above stands on its own.

---

## 1. `pub let` declarations

A module-level `let` binding may be marked `pub`:

```metel
pub let MAX_CONNECTIONS: u64 = 1024;
pub let DEFAULT_TIMEOUT_MS: u64 = 5000;
pub let PROTOCOL_VERSION: Version = Version { major: 1, minor: 0 };
```

`pub let` declares a named, typed, immutable value that is part of the module's public
API. There is no `pub let mut` — mutable module-level state is not exported.

The type annotation is required. The initialiser must be a **constant expression** —
defined as: literal values, arithmetic on literals, struct constructors whose fields
are constant expressions, and calls to functions declared `comptime` (RFC-0092). This
RFC does not extend the definition of constant expressions; it defers to RFC-0092 for
the full specification.

For the immediate use case, literals and struct constructors over other constant
expressions (as in `PROTOCOL_VERSION` above) are constant expressions under any
reasonable definition.

---

## 2. Importing `pub let` values

A `pub let` value is imported with the same `import` syntax as types and functions:

```metel
import my_module::MAX_CONNECTIONS;
import my_module::DEFAULT_TIMEOUT_MS;
import my_module::{MAX_CONNECTIONS, DEFAULT_TIMEOUT_MS};
```

After import, the name is bound in the current scope and may be used anywhere a value
of the declared type is accepted:

```metel
import my_module::MAX_CONNECTIONS;

fun accept(current: u64) -> boolean {
    current < MAX_CONNECTIONS
}
```

The value is always read-only at the import site — it is not a mutable binding.

---

## 3. Definitions alongside types

A module may export a type and a related constant value as independent declarations
with distinct names — no special coupling between them is required by this RFC:

```metel
// config.mtl (conceptual)
pub struct Limits { max_connections: u64 }
pub let DEFAULT_LIMITS: Limits = Limits { max_connections: 1024 };
```

Importing the type (`Limits`) and importing the value (`DEFAULT_LIMITS`) are
independent. Both may be imported in the same statement:

```metel
import config::{Limits, DEFAULT_LIMITS};
```

---

## 4. `export` re-exports

A `pub let` value may be re-exported with the existing `export` declaration:

```metel
// my_project/prelude.mtl
export config::DEFAULT_LIMITS;
```

Re-exported names carry the same semantics as at their definition site.

---

## 5. `std::core` auto-import

RFC-0030 auto-imports `std::core` at the lowest priority tier. This RFC does not
change that rule. `pub let` values, in `std::core` or any other module, follow the same
auto-import tiering as any other `std::core` declaration — nothing new is introduced by
this RFC on that axis.

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
   in `pub let` is deferred to RFC-0092 (Comptime Core, draft — successor to RFC-0055).
   Until RFC-0092 is accepted, legal initialisers are restricted to literals and
   struct constructors over other constant expressions.

---

## References

- RFC-0030 (Module System Redesign) — implemented module system this RFC extends;
  grammar already permits `pub` on `let` syntactically.
- RFC-0092 (Comptime Core, draft) — constant expression definition; governs `pub let`
  initialisers. Successor to RFC-0055, which this RFC originally cited.
- RFC-0063 (Allocator Handles), RFC-0065 (Allocator and Lifetime Ergonomics) — the
  ratified allocator design under which `Heap`/`LocalHeap` are referenced by type name
  (`@Heap expr`) rather than through an imported singleton value; this RFC's earlier
  motivating example predated that design and has been corrected above.
