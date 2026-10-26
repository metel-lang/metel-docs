---
id: adr-0066
title: "Construction Finds Values and Schemes by the Declaration's Identity"
date: '2026-10-26'
status: accepted
relates: adr-0011, adr-0020, adr-0022, adr-0041, adr-0054, adr-0065
implements: metel-core#1604
---

## Context

ADR-0054 moved name resolution to identity: a use site resolves to a `BindingId` (a `SymbolId` for a
module-level declaration, a `LocalId` for a local) and everything downstream reads that id. Construction
was the last place that still found a module-level value, or the scheme of a generic function, by
spelling. `ConstructCtx::module_values`, `module_fn_decls` and the inference output `SchemeEnv`
(`HashMap<String, TypeScheme>`) were keyed by name, and the evaluator reconstructed a generic body from
the same name-keyed `TypeCtx::scheme_env`. A name is the wrong key: a local that shadows a module
function, or an import under an alias, makes two declarations answer to one spelling.

ADR-0020 recorded the opposite stance for v0.5.0, when all modules were merged into one flat namespace: a
qualified path that could not be resolved as a type member fell back to its last segment as a plain
name. It said the fallback "must be removed when the name resolver is wired into the typechecker".

## Decision

A scheme is keyed by the declaration it belongs to, not by its spelling.

- `build_module_scheme_env` also returns `SchemeIds` (`BindingId -> TypeScheme`). A function or closure
  scheme is filed under the binder recorded for its declaration span (`FunGeneralization` carries the
  span). An imported or `std::core` entry is filed under the `SymbolId` its name denotes in the module's
  scope (own declaration, explicit import, user glob, then the `std::core` auto-glob). A name the module
  overloads is resolved past its own leftover symbol to what it extends (ADR-0042).
- Construction reads a scheme through the binding a use site resolved to (`scheme_at(span)`); a
  normalized path reads through the `symbol_id` it carries; `module_values` and `module_fn_decls` are
  keyed by `BindingId`.
- A static `Type::member` constructor (`List::new`) is read from the registry by the type's `SymbolId` and
  the member name (`method_scheme_by_id`). The key cannot be a path-stamped impl-method symbol: that symbol
  embeds the impl's type arguments (`List<$0>::new`), which a written `Type::method` path cannot
  reconstruct.
- The evaluator reconstructs a generic body from `TypeCtx::scheme_ids`. `ClosureValue` and the typed
  `GenericClosure` node carry a `scheme_id`; `main` is looked up by its `def_id`.
- `symbols` is no longer passed into construction. The one reader, finding the source symbol of an aspect's
  default method, asks the registry (`aspect_default_method_symbol`), which already holds the resolver's
  symbol map.

The last-segment fallback of ADR-0020 is removed. It was measured dead: over the whole integration corpus,
instrumented, no program reached the last-segment scheme arm. A `Path` carries no identity, so there was
nothing to key it by, and deleting it was cheaper than porting it.

## Consequences

- Shadowing and aliasing cannot make construction pick the wrong scheme. Before the switch, the two lookups
  were compared over about 16,500 reads; the only differences were six local `let f` that shadow a module
  `f`, where the name-keyed lookup returned the module function's scheme (the bug) and the identity lookup
  returns none (the right answer).
- `TypeCtx` and `TypedModule` no longer carry a name-keyed `scheme_env`. The inference export path
  (`GlobalExports`, ADR-0022) is still name-keyed, because it crosses modules and feeds inference, which
  has no `BindingId` for an import yet.
- ADR-0011's invariant (a let-bound polymorphic closure is absent from the monomorphic environment and
  present in the scheme environment) still holds, with "scheme environment" now meaning `SchemeIds`.
- What construction still reads by spelling is definition-scoped: generic parameter names, the field labels
  of one literal, and the one place a written block-local type name becomes an id. Giving those an identity
  needs spans on `TypeExpr` (metel-core#1612).
