# Synthetic Standard Library Refactor Plan

**Date:** 2026-06-06
**Scope:** Replace all hand-coded builtin registration logic with synthetic standard library
modules that pass through the full compiler pipeline like regular user modules.
**Status:** Deferred — scheduled for a follow-up sprint alongside the initial stdlib implementation

## Goal

`builtins.rs`, `StdPrelude`, `register_primitive_type_bindings`, and
`register_builtin_aspect_impls` all exist because the compiler has no way to learn
about standard library functions and types from source. They are parallel,
manually-maintained copies of information that should live in one place.

The target state: `std::core` (and later `std::fs`, etc.) are modules written in
Metel source (or as source strings embedded in the binary). They are parsed,
name-resolved, type-checked, and evaluated exactly like user modules. The compiler
pipeline gains no special cases for them. The hand-coded registration infrastructure
is deleted.

## Current State

| Concern | Where it lives | Problem |
|---|---|---|
| Free-function type schemes (`print`, `assert`, ...) | `StdPrelude` → injected per-module | Parallel list to evaluator; no single source of truth |
| Primitive method registrations (`to_string`, `String::len`) | `register_primitive_type_bindings` → re-injected per module | Re-computed on every `check_impl` call |
| Aspect declarations (Display, Iterable, From) | `register_primitive_type_bindings` → re-injected per module | Same |
| Aspect impl registrations (numeric From cross-product, Display impls) | `register_builtin_aspect_impls` in `build_registry` | In TypeDefinitionRegistry but still hand-coded |
| Runtime implementations | `builtins.rs` `register_builtins` | Carries both type info (wrong place) and Rust fn pointers |

## Design Decisions

### 1. `native fun` declaration

Native functions have a signature but no Metel body. The body is provided by the
interpreter at link time. New syntax:

```metel
native fun println(msg: String)
native fun clock() -> f64
```

`native fun` is only valid inside a synthetic standard library module. User code
cannot declare `native fun`. The parser accepts it unconditionally; the name resolver
or a later pass enforces the restriction.

This is the prerequisite for all subsequent phases. It needs a grammar change, AST
node, parser update, typechecker handling (signature only, no body inference), and
evaluator dispatch.

### 2. Native dispatch table and linking

When the evaluator processes a `native fun` declaration while evaluating `std::core`,
it looks up the function's fully-qualified name in a static dispatch table. If the
entry exists, the evaluator stores a `Value::Callable(Intrinsic { label, fun })` in
the module's env — exactly the same `Value` variant used today. From that point on,
calls to `println` take the normal closure dispatch path with no special casing at
call time.

If a `native fun` declaration has no dispatch table entry, the module fails to load
at interpreter startup, not at call time. This replaces the `free_function_names`
parity test with a structural guarantee.

The dispatch table is built in `builtins.rs` using a registration macro that
co-locates the qualified key and the Rust implementation:

```rust
native!("std::core::println",   |args, span| { ... });
native!("std::core::List::push", |args, span| { ... });
```

Keys are always fully qualified (`module::name`) so that `std::fs` and later modules
can share the same table without collisions. Bare names are not used as keys.

`builtins.rs` after the refactor contains only: the `native!` macro definition, the
dispatch table, and a `runtime_registry()` constructor that sets up `RuntimeRegistry`
for the evaluator. All type information is gone.

### 3. Module source embedding

`std/core.mtl` lives as a source string embedded in the binary via `include_str!`.
This avoids filesystem dependency at runtime and keeps the source version-controlled
alongside the interpreter. Later modules (`std::fs`, etc.) follow the same pattern.

### 4. Primitive type `impl` blocks

Metel source cannot currently declare `impl i64 { ... }` because `i64` has no struct
declaration. Two options:

- **Option A**: Allow `impl` on primitive type names in the synthetic module only.
  Simple, but creates a special case in the parser/typechecker.
- **Option B**: Treat primitive types as implicitly-declared structs with no fields.
  The typechecker already knows their names; giving them a nominal declaration entry
  makes `impl` work uniformly.

Option B is cleaner and aligns with the long-term direction. The synthetic module
would declare `native struct i64` (or similar) and `impl` blocks would follow
naturally.

## Phases

### Phase 1 — Centralize primitive bindings in TypeDefinitionRegistry
*(No new language features required — can be done now)*

Move the method and aspect registrations from `register_primitive_type_bindings`
into `register_builtin_aspect_impls` (renamed to `seed_builtin_type_registry`).
These facts belong in `TypeDefinitionRegistry` and propagate via `merge_from` like
all other cross-module type knowledge. The per-module re-injection disappears.

After this phase: `register_primitive_type_bindings` contains only the StdPrelude
free-function loop and can be renamed `inject_prelude_schemes`.

**Acceptance:** all 482 tests pass; `register_primitive_type_bindings` has no method
or aspect registration calls.

---

### Phase 2 — `native fun` syntax
*(Grammar + AST + parser + typechecker + evaluator)*

Add `native fun` as a declaration form. The typechecker checks the signature and
registers the scheme exactly as it would for a regular function, but skips body
inference. The evaluator, when loading the module that contains the `native fun`
declaration, looks up the fully-qualified name in the dispatch table and stores the
resulting `Value::Callable(Intrinsic { ... })` in the module's env. No special casing
is needed at call time.

Grammar change:

```pest
fun_decl = { "native"? ~ "fun" ~ ident ~ ... ~ block? }
```

The block is `None` for native functions; the typechecker enforces that body is
absent iff `native` is present.

**Acceptance:** a single-file test can declare `native fun add(a: i64, b: i64) -> i64`,
register a Rust implementation in the dispatch table under `"test::add"`, and call it
from `main`.

---

### Phase 3 — Create `std/core.mtl`
*(Write the source module)*

A Metel source file declaring everything currently in `builtins.rs` and
`register_primitive_type_bindings`:

- Free functions: `native fun print`, `native fun println`, `native fun assert`,
  `native fun assert_msg`, `native fun dbg`, `native fun clock`,
  `native fun string_len`, `native fun string_concat`
- Aspects: `aspect Display`, `aspect Iterable`, `aspect From<T>`
- Primitive impl blocks: `native impl Display for i64`, ..., `native impl From<T> for i64`, ...
- `List<T>` struct declaration and all its methods
- `Char` associated functions (`from_u32`, etc.)
- Numeric type associated functions (`to_string`, etc.)

The dispatch table in `builtins.rs` provides the Rust fn pointers for each
`native fun`. Type information lives entirely in `std/core.mtl`.

**Acceptance:** `std/core.mtl` compiles cleanly through the pipeline (parse,
name-resolve, typecheck, evaluate) with no errors.

---

### Phase 4 — Wire `std::core` into the module loader
*(Thread the synthetic module through the pipeline)*

Before the module graph is typechecked, the module loader prepends the `std::core`
synthetic `LoadedModule` to the graph. It goes through `check_impl` first. Its
`scheme_env` output flows into `GlobalExports["std::core"]` exactly as any other
module. `StdPrelude`'s role — seeding `GlobalExports` — is replaced.

The implicit glob import of `std::core` (the "no import required" user convenience)
stays in place at both the typechecker level (auto-glob via `GlobTier::Std`) and the
evaluator level (the lazy `std_core_lookup` fallback added in the previous sprint).

**Acceptance:** user programs can call `print` and `assert` without any import; they
also work with an explicit `import std::core::*`.

---

### Phase 5 — Delete the old infrastructure
*(Remove everything that is now dead code)*

- Delete `StdPrelude` struct, `populate_std_schemes`, `register_builtin_schemes`.
- Delete `register_primitive_type_bindings` (now empty after Phase 1 + Phase 4).
- Delete `register_builtin_aspect_impls` (now in `std/core.mtl`).
- Gut `builtins.rs` to just the native dispatch table and `runtime_registry` setup.
- Remove the `free_function_names` parity function and its test (the pipeline itself
  now enforces parity — if a native fun has no dispatch entry the evaluator errors).

**Acceptance:** all tests pass; `grep -r "StdPrelude"` returns no results.

---

## Dependency Graph

```
Phase 1  ──────────────────────────────────────────────────────► Phase 5
Phase 2 (native fun) ──► Phase 3 (std/core.mtl) ──► Phase 4 ──► Phase 5
```

Phase 1 is independent and can be done immediately. Phases 2–4 must be sequential.
Phase 5 is the cleanup after Phase 4.

## Open Questions

1. **`native struct` for primitives** — No new keyword needed. `impl i64 { ... }` already
   parses. The fix required before Phase 3 is in `infer_impl_method`: build `self_ty` via
   `type_expr_to_infer(TypeExpr::Named(target_name, []))` instead of constructing `Named`
   directly, so `"i64"` resolves to `Concrete(Type::I64)` and unification with call sites
   works. ~3 lines.

2. **Generic native impls** — `extend<T> i64: From<T>` cannot be written generically:
   `register_aspect_impl` drops TypeVar args via `filter_map`, so the registration would
   be empty. Resolution: keep `register_builtin_aspect_impls` for the 90-entry numeric
   From cross-product in Phase 3 as explicit technical debt; revisit when parameterized
   aspects are properly designed.

3. **`native fun` in `impl` blocks** — Phase 2 must cover this case. Dispatch key format:
   `"std::core::i64::to_string"`. `infer_impl_method` and the construction pass must skip
   body checking when the `native` flag is set.

4. **Error type** — `Result<T, E>` and propagation (`?`) — is `std::core` the right
   home, or does it go in a separate `std::result`?

5. **Module load order** — `std::core` must be fully checked before user modules.
   The module loader already processes modules in dependency order; `std::core` just
   needs to be treated as an implicit dependency of every user module.
