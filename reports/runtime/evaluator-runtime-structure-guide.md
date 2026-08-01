# Evaluator Runtime Structure Guide

**Date:** 2026-06-06  
**Scope:** Evaluator runtime metadata layout, method/aspect dispatch structure, and migration guidance toward System F elaboration  
**Status:** Implementation guide

## Purpose

This document defines a recommended runtime structure for the Metel evaluator
that:

- follows the principle that methods belong to the types they are attached to
- preserves explicit structure for aspect implementations
- makes `std::core` the owner of current builtin names rather than treating them
  as a separate evaluator-global namespace
- removes synthetic string-key dispatch as structural identity
- leaves room for a later System F elaboration pass
- remains compatible with possible dynamic-aspect work

This is an implementation guide, not a language specification and not an RFC.
It is intended to steer evaluator and runtime refactors without forcing early
typechecker redesign.

## Design Goal

The evaluator should stop modeling methods and aspect implementations as
disguised global functions. A method is part of some type-owned runtime
metadata, and an aspect implementation is a structured attachment of methods to
that type.

The evaluator should also stop modeling builtins as a separate conceptual
namespace. Names such as `print`, `dbg`, `assert`, `clock`, and `List::new`
should belong to `std::core`. They may still be implemented intrinsically by
the interpreter, but their semantic ownership belongs to the standard library
module structure.

At the same time, the runtime should avoid baking in assumptions that method
dispatch will forever be "look up nominal type, then look up method name."
System F elaboration may later replace some or all of this with explicit
evidence or dictionary passing.

The right compromise is:

- nominal type-owned runtime metadata now
- explicit aspect-implementation entries now
- a lookup API that can later be backed by elaborated evidence rather than by
  nominal runtime tables

## Recommended Structure

### Top-Level Registry

The evaluator should use a shared runtime registry separate from lexical
environment capture.

```rust
struct RuntimeRegistry {
    modules: HashMap<ModulePath, RuntimeModuleEntry>,
    types: HashMap<String, RuntimeTypeEntry>,
}
```

```rust
struct RuntimeModuleEntry {
    values: HashMap<String, RuntimeValueEntry>,
}
```

`modules` contains runtime-visible module-owned names. For the current
interpreter, the most important entry is `std::core`.

`std::core` should own ordinary callable names such as:

- `print`
- `println`
- `dbg`
- `assert`
- `assert_msg`
- `clock`

These are module-owned namespace entries, not evaluator-owned special globals.
User code may still access them unqualified if `std::core` is auto-imported, but
that is a resolver/typechecker concern rather than an evaluator special case.

Type-owned constructors and static-style callables such as `List::new` and
`List::from` should still belong to `std::core` semantically, but their runtime
storage belongs under the owning type entry rather than in a flat module value
map.

Their implementation may remain intrinsic:

- a `std::core` function can still be backed by Rust code
- a `std::core` constructor can still be backed by interpreter code
- a `std::core` method can still be backed by a builtin callable

The guide's requirement is about semantic ownership, not about requiring every
`std::core` entry to be implemented as Metel source code immediately.

`types` contains runtime metadata owned by each nominal type.

### Type-Owned Entries

```rust
struct RuntimeTypeEntry {
    associated_values: HashMap<String, RuntimeValueEntry>,
    inherent_methods: HashMap<String, RuntimeMethod>,
    aspect_impls: Vec<RuntimeAspectImpl>,
}
```

This is the core design rule:

- module-owned value names live under a runtime module entry such as `std::core`
- static-style callables such as `Type::new` live under the owning type entry
- inherent methods live directly under the type
- aspect methods live under explicit aspect-implementation records

Do not flatten aspect methods into `inherent_methods`.

That flattening would throw away information needed for:

- `From<S>` disambiguation
- dynamic aspects
- future evidence-oriented elaboration

### Aspect Implementation Entries

```rust
struct RuntimeAspectImpl {
    aspect: String,
    type_args: Vec<RuntimeTypeRef>,
    methods: HashMap<String, RuntimeMethod>,
}
```

Examples:

- `extend String: Display`
  - `aspect = "Display"`
  - `type_args = []`
  - methods: `to_string`

- `extend Char: From<u32>`
  - attached to owner type `Char`
  - `aspect = "From"`
  - `type_args = [RuntimeTypeRef::Named("u32")]`
  - methods: `from`

- `extend Counter: Iterable<i64>`
  - attached to owner type `Counter`
  - `aspect = "Iterable"`
  - `type_args = [RuntimeTypeRef::Named("i64")]`
  - methods: `next`

This structure is intentionally explicit. The evaluator should not recover these
 relationships from encoded strings such as `"Char::From<u32>::from"`.

### Method Entries

```rust
struct RuntimeMethod {
    label: &'static str,
    receiver: Option<ReceiverKind>,
    signature: RuntimeSignature,
    body: RuntimeCallable,
}
```

```rust
struct RuntimeSignature {
    params: Vec<RuntimeTypeRef>,
    ret: Option<RuntimeTypeRef>,
}
```

`label` is diagnostic text only. It is not a lookup key and not part of runtime
identity. Labels may still be human-readable strings such as:

- `String::to_string`
- `List::push`
- `Char::From<u32>::from`
- `std::core::print`

Those labels are acceptable for debugging and error messages. They must not be
structurally significant.

`receiver` records whether the method expects:

- value `self`
- `&self`
- `&var self`

`signature` is metadata. It is useful for:

- runtime assertions in builtin implementations
- debugging and tracing
- future reflection or tooling
- keeping the registry shape compatible with later elaboration

The evaluator should not grow a second complete type system here. Store only the
minimum metadata needed.

### Runtime Type References

Start with a deliberately small type-reference shape.

```rust
enum RuntimeTypeRef {
    Named(&'static str),
    Special(&'static str),
}
```

If needed later, this can grow into:

```rust
enum RuntimeTypeRef {
    Named(String),
    App { head: String, args: Vec<RuntimeTypeRef> },
}
```

Do not overbuild this until the evaluator needs richer runtime type metadata.

## Lookup API

The runtime lookup interface should distinguish inherent lookup from aspect
lookup.

```rust
enum MethodLookupKey<'a> {
    Inherent {
        owner: &'a str,
        method: &'a str,
    },
    Aspect {
        owner: &'a str,
        aspect: &'a str,
        type_args: &'a [RuntimeTypeRef],
        method: &'a str,
    },
}
```

This API is more important than the exact storage container. It is the seam that
keeps the evaluator adaptable.

Today:

- lookup resolves to a `RuntimeMethod`
- evaluator executes the attached callable

Later:

- lookup may resolve to elaborated evidence or dictionary entries
- evaluator may dispatch through explicit evidence rather than nominal tables

If the evaluator code talks in terms of `MethodLookupKey` rather than encoded
string names, the internal implementation can change without forcing a large
surface rewrite.

The same principle applies to module-level entries:

- resolve them as module-owned names
- do not treat them as an evaluator-only builtin namespace
- allow intrinsic implementations behind those module-owned names

## Compatibility with System F Elaboration

This structure is intentionally only partially semantic. It gives the evaluator
nominal runtime ownership now without claiming that nominal ownership is the
final elaborated representation.

To stay compatible with a later System F pass:

- keep lexical `Environment` separate from runtime metadata
- keep module-owned names separate from evaluator-global special cases
- keep method lookup behind a narrow API
- treat `RuntimeSignature` as metadata, not as the final dispatch truth
- do not require the typechecker to mirror the evaluator's storage layout yet

The expected post-elaboration change is:

- the typechecker may elaborate method/aspect use into explicit evidence passing
- runtime lookup may become dictionary lookup or evidence application
- some nominal runtime entries may remain only for builtins or host intrinsics

This guide is compatible with that future because it preserves explicit method
and aspect identity without requiring the evaluator to believe that all dispatch
will remain nominal forever.

It also avoids tying the language model to the implementation mechanism. A name
may belong to `std::core` semantically while still being implemented
intrinsically by the evaluator or compiler.

## Compatibility with Dynamic Aspects

This structure is also compatible with dynamic aspects, if aspect implementations
remain first-class structured entries.

Dynamic aspects need the runtime to preserve the fact that:

- a method came from an aspect
- that aspect may have type arguments
- the method belongs to a particular implementation record

That is exactly what `RuntimeAspectImpl` preserves.

What would break future dynamic-aspect work:

- flattening all aspect methods into plain type-owned methods
- discarding aspect identity after registration
- relying on strings like `"Type::method"` as the only structural handle

What remains compatible:

- inherent methods under the type
- aspect methods under explicit aspect impl entries
- runtime lookup that can ask for "the `Display` method on this type" rather
  than "the method named `to_string` on this type"

## Relationship to the Typechecker

This guide does **not** require the typechecker to adopt the same internal
storage structure now.

The typechecker should instead expose an API boundary such as:

- `lookup_inherent_method(type, name)`
- `lookup_aspect_method(type, aspect, args, name)`
- `has_impl(type, aspect, args)`

Internally, the typechecker may keep its current registries until the System F
work clarifies how aspect evidence and method access should be represented.

The evaluator and the typechecker do not need identical storage layouts at this
stage. They need compatible concepts and compatible lookup boundaries.

## Migration Plan

### Phase 1 — Remove synthetic string dispatch from structural runtime identity

Already started by introducing a dedicated `RuntimeRegistry`.

Next steps:

1. Stop encoding method identity in strings such as `"Type::method"` or
   `"Target::From<Source>::from"`.
2. Keep any remaining string labels for diagnostics only.
3. Ensure all method and aspect lookup goes through typed runtime lookup keys.

### Phase 1b — Remove evaluator-global builtins as a conceptual namespace

Move current builtin ownership under `std::core`.

That means:

- `print`, `println`, `dbg`, `assert`, `assert_msg`, `clock`, `string_len`,
  `string_concat`, `List::new`, and `List::from` are represented as names owned
  by `std::core`
- unqualified access comes only from the existing `std::core` auto-import model
- the evaluator stops thinking in terms of "special global builtins"

This phase does **not** require removing intrinsic implementations. It only
changes semantic ownership and runtime registration structure.

### Phase 2 — Reshape runtime storage around type-owned entries

Refactor the registry so that:

- module-owned callables live under `modules["std::core"]` or other runtime
  module entries
- methods move under `types[owner].inherent_methods`
- aspect implementations move under `types[owner].aspect_impls`

This is the point where the runtime starts matching the conceptual language
model rather than a flattened internal encoding.

### Phase 3 — Store lightweight signature metadata with methods

Add `receiver` and `signature` metadata to `RuntimeMethod`.

Use it only for:

- internal assertions
- diagnostics
- future tooling

Do not introduce runtime overload resolution based on those signatures unless
the language design explicitly requires it.

This phase is now part of the evaluator target structure as well:

- associated/static callables and receiver methods are structurally distinct
- receiver binding can follow runtime metadata instead of re-inspecting closure
  parameter lists
- parameter and return type links are preserved as lightweight runtime metadata

### Phase 4 — Preserve a stable lookup interface during elaboration work

When the System F rework begins:

- do not expose raw storage tables widely in evaluator code
- keep dispatch behind lookup helpers
- allow those helpers to switch from nominal tables to explicit evidence-backed
  dispatch as needed

## Concrete Examples

### `String.to_string`

```rust
types["String"].aspect_impls = [
    RuntimeAspectImpl {
        aspect: "Display",
        type_args: [],
        methods: {
            "to_string" => RuntimeMethod { ... }
        }
    }
]
```

### `List.push`

`push` is an inherent method on `List`, not an aspect method:

```rust
types["List"].inherent_methods = {
    "push" => RuntimeMethod { ... },
    "pop" => RuntimeMethod { ... },
    "len" => RuntimeMethod { ... },
}
```

### `extend Char: From<u32>`

```rust
types["Char"].aspect_impls = [
    RuntimeAspectImpl {
        aspect: "From",
        type_args: [RuntimeTypeRef::Named("u32")],
        methods: {
            "from" => RuntimeMethod { ... }
        }
    }
]
```

This is clearer than storing any structural runtime entry under the string
`"Char::From<u32>::from"`.

### `std::core::print`

```rust
modules[["std", "core"]].values = {
    "print" => RuntimeValueEntry { ... },
    "println" => RuntimeValueEntry { ... },
    "dbg" => RuntimeValueEntry { ... },
}
```

These names may still be backed by intrinsic Rust callables. The important point
is that they belong to `std::core`, not to a separate evaluator-global builtin
category.

## Non-Goals

This guide does not attempt to:

- redesign the typechecker around the same structure immediately
- define dynamic aspects as a language feature
- define the exact System F elaboration strategy
- add runtime reflection as a public API
- introduce multiple dispatch or overload resolution

## Recommended Rules

Use these rules during evaluator work:

1. A method belongs to a type entry, not to the global namespace.
2. A module-level callable such as `print` belongs to a runtime module entry,
   normally `std::core`, not to a separate builtin-global namespace.
3. An aspect method belongs to an aspect implementation entry, not to the
   inherent method table.
4. Strings may label runtime entries for diagnostics, but must never define
   structural identity.
5. Lexical environment capture must stay separate from runtime metadata.
6. Runtime lookup should go through a narrow typed API so elaboration can later
   replace the storage model without rewriting all evaluator call sites.

## Summary

The recommended intermediate architecture is:

- `RuntimeRegistry`
  - `modules`
  - `types`
- `RuntimeModuleEntry`
  - `values`
- `RuntimeTypeEntry`
  - `associated_values`
  - `inherent_methods`
  - `aspect_impls`
- `RuntimeAspectImpl`
  - `aspect`
  - `type_args`
  - `methods`
- `RuntimeMethod`
  - `label`
  - `receiver`
  - `signature`
  - `body`

This structure follows the instinct that methods should live inside the types
they belong to, while preserving enough explicit aspect structure to remain
compatible with both dynamic aspects and a future System F elaboration pass.
It also makes `std::core` the semantic owner of current builtin names without
requiring those entries to stop being implemented intrinsically right away.
