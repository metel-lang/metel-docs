# Name & Reference Resolution {#name-resolution}

The pipeline stage after module loading (`#parsing`): every top-level declaration across the loaded `ModuleGraph` gets a stable `SymbolId`, import/glob visibility is settled per module, and every reference site — bare identifier or multi-segment qualified path — is classified against that symbol space. Owning crate: `metel-frontend`. Defined in `name_resolver.rs`, `reference_resolver.rs`, `symbols.rs`, and `path_normalizer.rs`.

This is adjacent to, but distinct from, [Resolution](resolution.md) (`arch.resolution.*`, ADR-0054's identity-freeze model in `identity.rs`/`identity/`). That section covers structural `LocalId`/`RefId`/`FieldId`/`VariantId` allocation for lexical bindings and member declarations. This section covers an earlier, different concern: binding a top-level *declaration* to a `SymbolId`, and classifying which *references* point at one. A reader should not conflate the two symbol/identity systems just because both produce stable ids.

##### Requirement {#arch.name-resolution.requirement-1}

Every top-level declaration is assigned a `SymbolId` from one canonical table (`SymbolTable`), not a private per-call counter. Builtin `std::core` types and aspects are pre-seeded at fixed, well-known `SYM_TYPE_*`/`SYM_ASPECT_*` constants (so runtime impl-seeding can register builtin behavior under those same ids); user declarations are allocated starting at `USER_SYM_START`; a separately-reserved range (`OVERLOAD_SYM_START`) exists for overload-synthesized symbols. The same declaration always maps to the same `SymbolId` regardless of which module imports it, what local alias it's imported under, or the order modules were resolved in.

| Field | Value |
|---|---|
| `status` | `implemented` |
| `owner` | `metel-frontend` |
| `specified by` | `#name-resolution` |
| `implements` | `metel-frontend/src/symbols.rs` (`SymbolId`, `SymbolTable`, `SYM_TYPE_*`/`SYM_ASPECT_*`, `USER_SYM_START`, `OVERLOAD_SYM_START`); `metel-frontend/src/name_resolver.rs` (`resolve`, `ResolvedNames::symbols`/`::definitions`) |
| `verified by` | `metel-frontend/src/name_resolver.rs::same_declaration_gets_same_symbol_id_regardless_of_importer`, `::aliased_import_has_same_symbol_id_as_direct_import`, `::distinct_declarations_get_distinct_symbol_ids`, `::symbol_id_is_stable_in_symbol_table`, `::symbol_id_is_independent_of_module_resolution_order`, `::definitions_index_covers_every_declared_symbol`, `::interns_impl_and_aspect_method_symbols` |
| `related` | METEL-185, ADR-0041 |

##### Requirement {#arch.name-resolution.requirement-2}

A module's import scope resolves with explicit precedence: an explicit `import` binding always wins over a glob-imported (`import path::*`) name, and two explicit imports of the same local name are rejected outright (a compile error) rather than one silently shadowing the other. Among globs, priority is tiered — an auto-inserted std glob (`GlobTier::Std`) loses silently to a user glob (`GlobTier::User`) of the same name; `T0011` (ambiguous glob import) fires only when two globs of the *same* tier export the same name.

| Field | Value |
|---|---|
| `status` | `implemented` |
| `owner` | `metel-frontend` |
| `specified by` | `#name-resolution` |
| `implements` | `metel-frontend/src/name_resolver.rs` (`GlobTier`, `ModuleScope`, `resolve`) |
| `verified by` | `metel-frontend/src/name_resolver.rs::resolves_explicit_item_import`, `::resolves_glob_import`, `::rejects_duplicate_explicit_import`; integration fixtures `metel-interpreter/tests/integration/sources/module_semantics/two_glob_imports_same_name_is_t0011`, `two_explicit_imports_same_local_name_is_t0011` |
| `related` | `T0011` |

##### Requirement {#arch.name-resolution.requirement-3}

Every expression-level bare-identifier reference is classified as either `Res::Def` (a reference to a top-level declaration, carrying its `SymbolId`) or `Res::Local` (a true local: a function/closure parameter, a block-local `let`/`mut`, a `for`/`for-in` binding, or a match-pattern binding). Only `Def` references are recorded, in a side table keyed by the reference's `Span`; a local shadowing a top-level declaration of the same name resolves to the local, not the shadowed global. This classification feeds `arch.resolution.requirement-1`'s totality claim (every reference has a definite `Resolution`) but is a separate pass, run before that freeze.

| Field | Value |
|---|---|
| `status` | `implemented` |
| `owner` | `metel-frontend` |
| `specified by` | `#name-resolution` |
| `implements` | `metel-frontend/src/reference_resolver.rs` (`Res`, `collect_references`) |
| `verified by` | `metel-frontend/src/reference_resolver.rs::resolves_top_level_call_to_its_symbol_id`, `::local_binding_shadows_top_level_declaration`, `::overloaded_name_reference_does_not_resolve_to_a_stale_id` |
| `related` | METEL-187, ADR-0041 |

##### Requirement {#arch.name-resolution.requirement-4}

Multi-segment qualified paths (`Expr::Path`, e.g. `math::sin`, `self::Foo`) rewrite to `Expr::ResolvedPath` carrying the resolved `SymbolId`, producing a `NormalizedModuleGraph`. That type's inner field is crate-private (`pub(crate)`), so nothing outside `metel-frontend` can construct one except through `path_normalizer::normalize` — later pipeline stages that take a `NormalizedModuleGraph` by type therefore can't be handed an un-normalized graph from another crate, though within `metel-frontend` itself this is API discipline, not a compiler-enforced guarantee against every internal caller.

| Field | Value |
|---|---|
| `status` | `implemented` |
| `owner` | `metel-frontend` |
| `specified by` | `#name-resolution` |
| `implements` | `metel-frontend/src/path_normalizer.rs` (`NormalizedModuleGraph`, `normalize`) |
| `verified by` | `metel-frontend/src/path_normalizer.rs::glob_imported_qualified_call_carries_a_symbol_id`, `::explicitly_imported_qualified_call_carries_the_same_symbol_id`, `::self_qualified_call_carries_a_symbol_id` |
| `related` | ADR-0031 |

## Known limitations

- [`LIMIT-NAME-RESOLUTION-001`](../limitations/limit-name-resolution-001.md) — `std::core` has no physical module file, so it can't be listed or enumerated.
