---
id: LIMIT-TYPE-CONSTRUCTION-004
title: "Construction finds module-level values and their schemes by name"
summary: "Module-level values and the inference SchemeEnv are keyed by spelling in construction; everything a binding names is keyed by identity."
scope: "architecture/spec/type-construction.md#type-construction"
owner: metel-frontend
discovered_by: "metel-core#1570 step 3 scoping (corpus measurement of SchemeEnv keys)"
disposition: resolved
review: null
---

## Limitation

Construction resolves locals, nested generic functions, struct fields, types, aspects and
top-level declarations by identity. Module-level values (functions, builtins, top-level
`let`/`var`) are still found by name: `ConstructCtx::module_values` and `module_fn_decls` are seeded
from the inference output `SchemeEnv`, a `HashMap<String, TypeScheme>`, and a callee reads its scheme
from it by spelling. The two maps are exempted in `check_no_semantic_name_lookup.py`'s scan with this
record as the retirement condition.

The blocker is a path callee such as `List::new`: path normalization stamps no symbol on a
`Type::method` path, so the use site has no identity to look the scheme up by. Measured over the
integration corpus, about 15,000 of the `SchemeEnv` entries built are such joined keys, against
imported names (~58%) and `std::core` items (~40%), which can carry an id from where they are
produced.

## Impact

Internal. A module-level value whose spelling is shadowed or aliased is resolved correctly today by
the name resolver's own tables before construction; the name-keyed read happens after that, on a
spelling the resolver already accepted.

## Affects

- `arch.type-construction.requirement-13`
- `metel-frontend/src/pipeline/type_checking/construction/mod.rs` (`module_values`, `module_fn_decls`, `lookup_module`)

## Resolution

Resolved by metel-core#1604 (PRs #1608, #1609, #1610). `Type::member` static constructors are read from the
registry by the type's `SymbolId` and the member name (`List::new` was the only joined key construction
ever read: 150 reads over the integration corpus, all `List::new`/`List::from`). The inference output
now also yields the module's schemes keyed by the declaration they belong to (`SchemeIds`): a function
or closure under the binder recorded for its declaration span, an import or `std::core` entry under the
`SymbolId` its name denotes in the module's scope. `ConstructCtx::module_values` and `module_fn_decls`
are keyed by `BindingId`, a use site reaches a scheme through the binding the identity pass resolved it
to, and the runtime `TypeCtx` carries the same table, so a reconstructed generic body reads it too. The
two exemptions in `check_no_semantic_name_lookup.py`'s scan are gone, and the name-keyed `scheme_env` is
no longer carried past inference's own export step. The path normalization step the original plan named
turned out unnecessary: an impl-method symbol embeds the impl's type arguments, which a written
`Type::method` path cannot reconstruct, and the registry already keys methods by owner identity.
