# Resolution {#resolution}

This section is the Architecture Spec's versioned description of how the
frontend resolves source spellings to stable identities, and the boundary that
binds typechecking, elaboration, and evaluation to those identities instead of
re-deriving meaning from names. It documents the implemented resolved-identity
model described by [ADR-0054](../decisions/adr-0054-resolved-identity-freeze-and-generic-instance-preparation.md);
the `arch-*` requirements below are its checkable claims.

Owning crate: `metel-frontend`. The model is defined in `identity.rs` and `identity/` (`allocate.rs`, `lexical_path.rs`, `member.rs`, `position.rs`), and consumed by `name_resolver.rs`, `reference_resolver.rs`, `typed_ast/`, and every later pipeline stage.

## Model

The resolution freeze separates source spelling from durable semantic identity. Every
reference is total—local or global—and later stages consume that result rather than
looking the spelling up again ([frozen references](#arch.resolution.requirement-1)).
Lexical bindings and uses receive structural identities that survive unrelated edits
([lexical identity](#arch.resolution.requirement-2)); fields and variants receive the
same treatment at the declaration level ([member identity](#arch.resolution.requirement-3)).

Editor lookup is intentionally different. A position index maps an ephemeral parsed
snapshot back to these identities, but position never becomes a semantic key
([position isolation](#arch.resolution.requirement-4)). This distinction lets tools be
responsive without making formatting alter program meaning.

<details>
<summary>Verifiable architecture claims</summary>

##### Requirement {#arch.resolution.requirement-1}

After inference has solved a body and the frontend has frozen its resolution, no later phase performs semantic lookup keyed by source spelling — every meaning (expression, type, member, field, method, or runtime binding) is instead looked up by a stable identity the frontend already assigned. Every value reference in a resolved body has a *total* `Resolution` (`Global(SymbolId)` or `Local(LocalId)`); there is no silent third case for "unresolved."

| Field | Value |
|---|---|
| `status` | `implemented` |
| `owner` | `metel-frontend` |
| `specified by` | `#resolution` |
| `implements` | `metel-frontend/src/identity.rs` (`ResolutionMap`, `Resolution`, `UnresolvedCause`) |
| `verified by` | `tools/check_no_semantic_name_lookup.py` (CI-wired, `.github/workflows/ci.yml`); `metel-frontend/src/identity/tests.rs::reference_table_is_total_and_unknown_names_are_explicit` |
| `related` | ADR-0054, ADR-0041, ADR-0042 |

##### Requirement {#arch.resolution.requirement-2}

Lexical bindings and value references are allocated structural identities (`LocalId`, `RefId`) by a parse-driven walk keyed on `LexicalPath` — the chain of structural positions from an owning body to a binding or use, carrying interned spellings and block/parameter ordinals rather than byte offsets or traversal counters. An unrelated text edit (reformatting, an earlier sibling binding, an edit to a different body) does not change an existing identity.

| Field | Value |
|---|---|
| `status` | `implemented` |
| `owner` | `metel-frontend` |
| `specified by` | `#resolution` |
| `implements` | `metel-frontend/src/identity/allocate.rs`, `metel-frontend/src/identity/lexical_path.rs` |
| `verified by` | `metel-frontend/src/identity/tests.rs::blank_lines_and_reformatting_change_no_identity`, `::inserting_an_earlier_binding_does_not_renumber_a_later_one`, `::editing_one_body_leaves_another_bodys_identities_untouched`, `::allocation_is_order_independent_for_the_same_graph`, `::shadowing_produces_distinct_local_ids` |
| `related` | ADR-0054 (2026-09-10 amendment) |

##### Requirement {#arch.resolution.requirement-3}

Struct and enum member declarations (fields and enum variants) are interned to stable `FieldId` / `VariantId`, keyed structurally by `(owning type SymbolId, declared member name)`, built from parsed type declarations before inference. These ids are threaded onto the typed IR (`TypedExpr`'s field/variant-access and construction forms carry `Option<FieldId>` / `Option<VariantId>`) rather than re-derived by a later phase from a string.

| Field | Value |
|---|---|
| `status` | `implemented` |
| `owner` | `metel-frontend` |
| `specified by` | `#resolution` |
| `implements` | `metel-frontend/src/identity/member.rs` (`MemberTable`); `metel-frontend/src/typed_ast/mod.rs` (`FieldId`/`VariantId` on field-access, construction, and variant forms) |
| `verified by` | `metel-frontend/src/identity/member.rs::struct_fields_get_distinct_ids_owned_by_the_struct`, `::same_field_name_on_different_types_is_a_different_id`, `::enum_variants_and_their_fields_are_interned`, `::interning_is_reformat_stable_and_order_independent`, `::absent_members_report_none_not_a_fabricated_id` |
| `related` | ADR-0054 step 3, `#1051` |

##### Requirement {#arch.resolution.requirement-4}

Source-position lookup (`PositionIndex`) is the one structure permitted to be keyed by byte position. It is rebuilt from a parsed snapshot, never persisted, and never a semantic input — it exists only to answer an editor's "what identity is at byte N" question. Every durable resolved artifact (`ResolutionMap`, the frozen IR) is keyed by identity, never by position.

| Field | Value |
|---|---|
| `status` | `implemented` |
| `owner` | `metel-frontend` |
| `specified by` | `#resolution` |
| `implements` | `metel-frontend/src/identity/position.rs` (`PositionIndex`) |
| `verified by` | `tools/check_no_semantic_name_lookup.py` (deliberately exempts `identity::position` as the sanctioned exception, rather than silently missing it) |
| `related` | ADR-0054 (2026-09-10 amendment) |

</details>

## Known limitations

- [`LIMIT-RESOLUTION-001`](../limitations/limit-resolution-001.md) — the resolved-identity model is in-memory only; no on-disk persistence or cross-process interner stability.
