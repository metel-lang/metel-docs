# Name & Reference Resolution {#name-resolution}

The pipeline stage after module loading (`#parsing`): every top-level declaration across the loaded `ModuleGraph` gets a stable `SymbolId`, import/glob visibility is settled per module, and every reference site is classified against that symbol space. Owning crate: `metel-frontend`. Defined in `name_resolver.rs`, `reference_resolver.rs`, and `symbols.rs`.

This is adjacent to, but distinct from, [Resolution](resolution.md) (`arch.resolution.*`, ADR-0054's identity-freeze model in `identity.rs`/`identity/`). That section covers structural `LocalId`/`RefId`/`FieldId`/`VariantId` allocation for lexical bindings and member declarations. This section covers an earlier, different concern: binding a top-level *declaration* to a `SymbolId`, and classifying which *references* point at one. A reader should not conflate the two symbol/identity systems just because both produce stable ids.

## Model

Resolution begins by giving every declaration one canonical `SymbolId`; imports and
aliases then point back to that declaration rather than minting local replacements
([declaration identity](#arch.name-resolution.requirement-1)). Import precedence is
settled before reference classification, so explicit imports and globs behave
predictably ([import scopes](#arch.name-resolution.requirement-2)).

Reference collection records the identity selected at each use site
([references](#arch.name-resolution.requirement-3)). Path normalization is a
following, separate stage; both precede the structural identity freeze described
in the Resolution section.

<details>
<summary>Verifiable architecture claims</summary>

##### Requirement {#arch.name-resolution.requirement-1}

Every top-level declaration is assigned a `SymbolId` from one canonical table (`SymbolTable`), not a private per-call counter. Builtin `std::core` types and aspects are pre-seeded at fixed, well-known `SYM_TYPE_*`/`SYM_ASPECT_*` constants (so runtime impl-seeding can register builtin behavior under those same ids); user declarations are allocated starting at `USER_SYM_START`; a separately-reserved range (`OVERLOAD_SYM_START`) exists for overload-synthesized symbols. The same declaration always maps to the same `SymbolId` regardless of which module imports it, what local alias it's imported under, or the order modules were resolved in.

| Field | Value |
|---|---|
| `status` | `implemented` |
| `owner` | `metel-frontend` |
| `specified by` | `#name-resolution` |
| `implements` | [`metel-frontend/src/symbols.rs::intern`](https://github.com/metel-lang/metel-core/blob/282f563360390f6648e81bc9d3974bcb8070c496/metel-frontend/src/symbols.rs#L118); [`metel-frontend/src/symbols.rs::new`](https://github.com/metel-lang/metel-core/blob/282f563360390f6648e81bc9d3974bcb8070c496/metel-frontend/src/symbols.rs#L80) |
| `verified by` | [`metel-frontend/src/name_resolver.rs::aliased_import_has_same_symbol_id_as_direct_import`](https://github.com/metel-lang/metel-core/blob/282f563360390f6648e81bc9d3974bcb8070c496/metel-frontend/src/name_resolver.rs#L1338); [`metel-frontend/src/name_resolver.rs::distinct_declarations_get_distinct_symbol_ids`](https://github.com/metel-lang/metel-core/blob/282f563360390f6648e81bc9d3974bcb8070c496/metel-frontend/src/name_resolver.rs#L1381); [`metel-frontend/src/name_resolver.rs::same_declaration_gets_same_symbol_id_regardless_of_importer`](https://github.com/metel-lang/metel-core/blob/282f563360390f6648e81bc9d3974bcb8070c496/metel-frontend/src/name_resolver.rs#L1295); [`metel-frontend/src/name_resolver.rs::symbol_id_is_independent_of_module_resolution_order`](https://github.com/metel-lang/metel-core/blob/282f563360390f6648e81bc9d3974bcb8070c496/metel-frontend/src/name_resolver.rs#L1513); [`metel-frontend/src/name_resolver.rs::symbol_id_is_stable_in_symbol_table`](https://github.com/metel-lang/metel-core/blob/282f563360390f6648e81bc9d3974bcb8070c496/metel-frontend/src/name_resolver.rs#L1483); [`metel-frontend/src/symbols.rs::builtin_std_core_declarations_are_pre_seeded_at_their_fixed_ids`](https://github.com/metel-lang/metel-core/blob/282f563360390f6648e81bc9d3974bcb8070c496/metel-frontend/src/symbols.rs#L136); [`metel-frontend/src/symbols.rs::user_declarations_are_allocated_from_the_user_range_below_the_overload_range`](https://github.com/metel-lang/metel-core/blob/282f563360390f6648e81bc9d3974bcb8070c496/metel-frontend/src/symbols.rs#L145) |
| `last_reviewed` | 282f563360390f6648e81bc9d3974bcb8070c496 |
| `related` | METEL-185, ADR-0041 |

##### Requirement {#arch.name-resolution.requirement-2}

A module's import scope resolves with explicit precedence: an explicit `import` binding always wins over a glob-imported (`import path::*`) name, and two explicit imports of the same local name are rejected outright (a compile error) rather than one silently shadowing the other. Among globs, priority is tiered — an auto-inserted std glob (`GlobTier::Std`) loses silently to a user glob (`GlobTier::User`) of the same name; `T0011` (ambiguous glob import) fires only when two globs of the *same* tier export the same name.

| Field | Value |
|---|---|
| `status` | `implemented` |
| `owner` | `metel-frontend` |
| `specified by` | `#name-resolution` |
| `implements` | [`metel-frontend/src/name_resolver.rs::add_explicit`](https://github.com/metel-lang/metel-core/blob/282f563360390f6648e81bc9d3974bcb8070c496/metel-frontend/src/name_resolver.rs#L708); [`metel-frontend/src/name_resolver.rs::resolve_module`](https://github.com/metel-lang/metel-core/blob/282f563360390f6648e81bc9d3974bcb8070c496/metel-frontend/src/name_resolver.rs#L426) |
| `verified by` | [`metel-frontend/src/name_resolver.rs::resolves_explicit_item_import`](https://github.com/metel-lang/metel-core/blob/282f563360390f6648e81bc9d3974bcb8070c496/metel-frontend/src/name_resolver.rs#L815); [`metel-interpreter/tests/integration/sources/module_semantics/explicit_import_wins_over_glob_same_name/test.toml`](https://github.com/metel-lang/metel-core/blob/282f563360390f6648e81bc9d3974bcb8070c496/metel-interpreter/tests/integration/sources/module_semantics/explicit_import_wins_over_glob_same_name/test.toml#L1); [`metel-interpreter/tests/integration/sources/module_semantics/two_explicit_imports_same_local_name_is_t0011/test.toml`](https://github.com/metel-lang/metel-core/blob/282f563360390f6648e81bc9d3974bcb8070c496/metel-interpreter/tests/integration/sources/module_semantics/two_explicit_imports_same_local_name_is_t0011/test.toml#L1); [`metel-interpreter/tests/integration/sources/module_semantics/two_glob_imports_same_name_is_t0011/test.toml`](https://github.com/metel-lang/metel-core/blob/282f563360390f6648e81bc9d3974bcb8070c496/metel-interpreter/tests/integration/sources/module_semantics/two_glob_imports_same_name_is_t0011/test.toml#L1); [`metel-interpreter/tests/integration/sources/module_semantics/two_glob_imports_same_name_unused_no_t0011/test.toml`](https://github.com/metel-lang/metel-core/blob/282f563360390f6648e81bc9d3974bcb8070c496/metel-interpreter/tests/integration/sources/module_semantics/two_glob_imports_same_name_unused_no_t0011/test.toml#L1); [`metel-interpreter/tests/integration/sources/module_semantics/user_glob_wins_over_std_glob_same_name_no_t0011/test.toml`](https://github.com/metel-lang/metel-core/blob/282f563360390f6648e81bc9d3974bcb8070c496/metel-interpreter/tests/integration/sources/module_semantics/user_glob_wins_over_std_glob_same_name_no_t0011/test.toml#L1) |
| `last_reviewed` | 282f563360390f6648e81bc9d3974bcb8070c496 |
| `related` | `T0011`, ADR-0026 |

##### Requirement {#arch.name-resolution.requirement-3}

Every expression-level bare-identifier reference is classified as either `Res::Def` (a reference to a top-level declaration, carrying its `SymbolId`) or `Res::Local` (a true local: a function/closure parameter, a block-local `let`/`mut`, a `for`/`for-in` binding, or a match-pattern binding). Only `Def` references are recorded, in a side table keyed by the reference's `Span`; a local shadowing a top-level declaration of the same name resolves to the local, not the shadowed global. This classification feeds `arch.resolution.requirement-1`'s totality claim (every reference has a definite `Resolution`) but is a separate pass, run before that freeze.

| Field | Value |
|---|---|
| `status` | `implemented` |
| `owner` | `metel-frontend` |
| `specified by` | `#name-resolution` |
| `implements` | [`metel-frontend/src/reference_resolver.rs::collect_references`](https://github.com/metel-lang/metel-core/blob/282f563360390f6648e81bc9d3974bcb8070c496/metel-frontend/src/reference_resolver.rs#L70) |
| `verified by` | [`metel-frontend/src/reference_resolver.rs::local_binding_shadows_top_level_declaration`](https://github.com/metel-lang/metel-core/blob/282f563360390f6648e81bc9d3974bcb8070c496/metel-frontend/src/reference_resolver.rs#L491); [`metel-frontend/src/reference_resolver.rs::resolves_top_level_call_to_its_symbol_id`](https://github.com/metel-lang/metel-core/blob/282f563360390f6648e81bc9d3974bcb8070c496/metel-frontend/src/reference_resolver.rs#L472) |
| `last_reviewed` | 282f563360390f6648e81bc9d3974bcb8070c496 |
| `related` | METEL-187, ADR-0041 |

</details>

## Known limitations

`LIMIT-*` records are the authoritative inventory of known boundaries for this
section. They carry the impact, owner, disposition, and review point; the
Atlas limitations view projects the same records rather than duplicating them.

### Active records

No active `LIMIT-*` records are currently recorded for this section. This is
a current inventory, not a claim of complete coverage.

### Resolved records

- [`LIMIT-NAME-RESOLUTION-001`](../limitations/limit-name-resolution-001.md) — `std::core` lacking a physical module file, resolved by ADR-0039.
