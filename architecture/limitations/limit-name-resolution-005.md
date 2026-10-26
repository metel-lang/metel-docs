---
id: LIMIT-NAME-RESOLUTION-005
title: "Symbol identity is a (module, name-string) key, so distinct declarations can share one SymbolId"
summary: "`ResolvedNames.symbols` keys ids by module path and a name string: every declaration kind shares that key space, and a method's key drops its impl's type arguments, so different impls collide."
scope: "architecture/spec/name-resolution.md#name-resolution"
owner: metel-frontend
discovered_by: "maintainer review of metel-frontend/src/identity/symbols.rs and `ResolvedNames.symbols`; reproduced as metel-core#1228 and #1229"
disposition: resolved
review: null
---

## Limitation

The canonical symbol table, exposed as `pub symbols: HashMap<(Vec<String>,
String), SymbolId>` on `ResolvedNames` (a copy of `SymbolTable::map`), maps a
module path and a **name string** to an id. Anything that maps to the same key
gets the same `SymbolId`, and `intern_all_symbols` does not check for a clash:

1. **One key space for every declaration kind.** Functions, structs, enums,
   aspects, `let`/`mut` globals and type aliases are keyed by their bare name
   (`decl_any_name`). A struct and a function both called `Foo` in one module
   share an id, and `definitions.entry(id).or_insert(span)` keeps only the first
   declaration's span, so the second is invisible to goto-definition. That pair
   is legal (types and values are separate namespaces) and behaves correctly,
   used locally and through an import: the registries that consume the id happen
   to be per-kind. Two declarations in the *same* namespace (two structs, a
   struct and an enum, a `let` and a `fun`) used to share an id as well; they are
   now `T0037` (`metel-core#1560`), so only the legal cross-namespace pair still
   shares a key.
2. **A method's key drops its impl's type arguments.** *(Fixed by `metel-core#1571`.)*
   `method_symbol_name` used to be fed the target's *base name*, so
   `extend W<i64>: Tag { fun t … }` and `extend W<String>: Tag { fun t … }` both produced
   `W::Tag::t` and both methods received one `SymbolId`. `impl_method_symbol_name` now renders the
   target and the aspect with their type arguments (`W<i64>::Tag::t`, `S::Conv<String>::conv`),
   naming an impl's own type parameters by position; a target with no arguments keeps its bare name.

3. **Methods are not overloaded, so a repeated name collides even inside one
   impl.** Two methods called `m` in one `extend S` block, whatever their
   parameter types, share `S::m` and one id; the later definition replaces the
   earlier. Free functions are different: each overloaded *definition* gets its
   own id from the overload allocator (`LIMIT-NAME-RESOLUTION-002`), and only the
   bare *name* shares one table entry.

## Impact

Cases 2 and 3 no longer give wrong results. Case 2: `W { v = 1 }.t()` and `W { v = "s" }.t()` each
answer from their own impl, for aspect impls, inherent `extend` blocks and through a generic bound
(`metel-core#1228`, checked again at `metel-core#1229`). Case 3: a repeated method name in one
`extend` block, whatever the parameter types, or in one aspect impl or `aspect` declaration, is
`T0034`, as is the same name in two inherent blocks that can apply to one receiver
(`metel-core#1322`, `metel-core#1229`). Those symptoms were closed without changing the key; the key itself now
distinguishes the instantiations (`metel-core#1571`), so a consumer relying on the id alone no longer
conflates them. Case 1 has no observed runtime effect for the legal pair; identity is
a string key, not the declaration.

## Affects

- `arch.name-resolution.requirement-1`
- `arch.resolution.requirement-1`
- `metel-frontend/src/pipeline/name_resolution/name_resolver/mod.rs::intern_all_symbols`
- `metel-frontend/src/pipeline/name_resolution/name_resolver/mod.rs::decl_any_name`
- `metel-frontend/src/pipeline/name_resolution/name_resolver/mod.rs::method_symbol_name`
- `metel-frontend/src/pipeline/name_resolution/name_resolver/mod.rs::impl_method_symbol_name`
- `metel-frontend/src/pipeline/name_resolution/name_resolver/mod.rs::check_duplicate_declarations`
- `metel-frontend/src/identity/allocate.rs` (method-symbol lookup)

## Resolution

Resolved by `metel-core#1560`, `metel-core#1571` and the symptom fixes before them.

- Case 1 (one key space for every kind): the symbol table is keyed by `(module, namespace, name)`.
  Structs, enums, aspects, type aliases and module handles are type-namespace symbols; functions,
  `let`, `var` and methods are value-namespace symbols. `struct Foo` and `fun Foo` have different ids
  and each keeps its own definition span. Two declarations in one namespace are `T0037`
  (`metel-core#1560`). `ModuleScope` bindings, `pub_surface`, `declared_names` and re-exports carry the
  namespace, so an import brings a name in every namespace the source module provides it in, and a name
  public in either namespace is importable.
- Case 2 (a method's key drops its impl's type arguments): `impl_method_symbol_name` renders the
  target and the aspect with their arguments (`W<i64>::Tag::t`, `S::Conv<String>::conv`), naming an
  impl's own type parameters by position (`metel-core#1571`, first slice). Different instantiations were
  already dispatched correctly (`metel-core#1228`).
- Case 3 (a repeated method name collides): `T0034` for a name defined twice where both definitions can
  apply to one receiver (`metel-core#1322` for inherent blocks, `metel-core#1229` for aspect impls and
  aspect declarations).

The reference resolver tries the value namespace first and then the type namespace for a bare name (a
unit struct is a type used as a value); type positions, impl targets and aspects resolve in the type
namespace.
