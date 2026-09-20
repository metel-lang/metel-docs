# Resolution {#resolution}

This section is the Architecture Spec's versioned description of how the
frontend resolves source spellings to stable identities, and the boundary that
binds typechecking, elaboration, and evaluation to those identities instead of
re-deriving meaning from names. It documents the implemented resolved-identity
model described by [ADR-0054](https://github.com/metel-lang/metel-docs/blob/main/architecture/decisions/adr-0054-resolved-identity-freeze-and-generic-instance-preparation.md);
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
| `implements` | [`metel-frontend/src/identity/allocate.rs::allocate_module`](https://github.com/metel-lang/metel-core/blob/2aa2c5729e26ccba73bcc69fe338f0941ffc4966/metel-frontend/src/identity/allocate.rs#L170) |
| `verified by` | [`metel-frontend/src/identity/tests.rs::a_body_with_only_bound_names_has_no_unresolved_references`](https://github.com/metel-lang/metel-core/blob/2aa2c5729e26ccba73bcc69fe338f0941ffc4966/metel-frontend/src/identity/tests.rs#L312); [`metel-frontend/src/identity/tests.rs::a_use_of_a_global_declaration_is_classified_as_global`](https://github.com/metel-lang/metel-core/blob/2aa2c5729e26ccba73bcc69fe338f0941ffc4966/metel-frontend/src/identity/tests.rs#L325); [`metel-frontend/src/identity/tests.rs::reference_table_is_total_and_unknown_names_are_explicit`](https://github.com/metel-lang/metel-core/blob/2aa2c5729e26ccba73bcc69fe338f0941ffc4966/metel-frontend/src/identity/tests.rs#L300) |
| `last_reviewed` | 282f563360390f6648e81bc9d3974bcb8070c496 |
| `related` | ADR-0054, ADR-0041, ADR-0042 |

##### Requirement {#arch.resolution.requirement-2}

Lexical bindings and value references are allocated structural identities (`LocalId`, `RefId`) by a parse-driven walk keyed on `LexicalPath` — the chain of structural positions from an owning body to a binding or use, carrying interned spellings and block/parameter ordinals rather than byte offsets or traversal counters. An unrelated text edit (reformatting, an earlier sibling binding, an edit to a different body) does not change an existing identity.

| Field | Value |
|---|---|
| `status` | `implemented` |
| `owner` | `metel-frontend` |
| `specified by` | `#resolution` |
| `implements` | [`metel-frontend/src/identity/allocate.rs::allocate_module`](https://github.com/metel-lang/metel-core/blob/2aa2c5729e26ccba73bcc69fe338f0941ffc4966/metel-frontend/src/identity/allocate.rs#L171) |
| `verified by` | [`metel-frontend/src/identity/tests.rs::blank_lines_and_reformatting_change_no_identity`](https://github.com/metel-lang/metel-core/blob/2aa2c5729e26ccba73bcc69fe338f0941ffc4966/metel-frontend/src/identity/tests.rs#L118); [`metel-frontend/src/identity/tests.rs::editing_one_body_leaves_another_bodys_identities_untouched`](https://github.com/metel-lang/metel-core/blob/2aa2c5729e26ccba73bcc69fe338f0941ffc4966/metel-frontend/src/identity/tests.rs#L152); [`metel-frontend/src/identity/tests.rs::inserting_an_earlier_binding_does_not_renumber_a_later_one`](https://github.com/metel-lang/metel-core/blob/2aa2c5729e26ccba73bcc69fe338f0941ffc4966/metel-frontend/src/identity/tests.rs#L139) |
| `last_reviewed` | 282f563360390f6648e81bc9d3974bcb8070c496 |
| `related` | ADR-0054 (2026-09-10 amendment) |

##### Requirement {#arch.resolution.requirement-3}

Struct and enum member declarations (fields and enum variants) are interned to stable `FieldId` / `VariantId`, keyed structurally by `(owning type SymbolId, declared member name)`, built from parsed type declarations before inference. These ids are threaded onto the typed IR (`TypedExpr`'s field/variant-access and construction forms carry `Option<FieldId>` / `Option<VariantId>`) rather than re-derived by a later phase from a string.

| Field | Value |
|---|---|
| `status` | `implemented` |
| `owner` | `metel-frontend` |
| `specified by` | `#resolution` |
| `implements` | [`metel-frontend/src/identity/member.rs::collect_members`](https://github.com/metel-lang/metel-core/blob/2aa2c5729e26ccba73bcc69fe338f0941ffc4966/metel-frontend/src/identity/member.rs#L156) |
| `verified by` | [`metel-frontend/src/identity/member.rs::absent_members_report_none_not_a_fabricated_id`](https://github.com/metel-lang/metel-core/blob/2aa2c5729e26ccba73bcc69fe338f0941ffc4966/metel-frontend/src/identity/member.rs#L322); [`metel-frontend/src/identity/member.rs::enum_variants_and_their_fields_are_interned`](https://github.com/metel-lang/metel-core/blob/2aa2c5729e26ccba73bcc69fe338f0941ffc4966/metel-frontend/src/identity/member.rs#L285); [`metel-frontend/src/identity/member.rs::interning_is_reformat_stable_and_order_independent`](https://github.com/metel-lang/metel-core/blob/2aa2c5729e26ccba73bcc69fe338f0941ffc4966/metel-frontend/src/identity/member.rs#L302); [`metel-frontend/src/identity/member.rs::same_field_name_on_different_types_is_a_different_id`](https://github.com/metel-lang/metel-core/blob/2aa2c5729e26ccba73bcc69fe338f0941ffc4966/metel-frontend/src/identity/member.rs#L272); [`metel-frontend/src/identity/member.rs::struct_fields_get_distinct_ids_owned_by_the_struct`](https://github.com/metel-lang/metel-core/blob/2aa2c5729e26ccba73bcc69fe338f0941ffc4966/metel-frontend/src/identity/member.rs#L260); [`metel-frontend/src/typechecker/mod.rs::typed_ir_threads_member_ids_rather_than_rederiving_them`](https://github.com/metel-lang/metel-core/blob/2aa2c5729e26ccba73bcc69fe338f0941ffc4966/metel-frontend/src/typechecker/mod.rs#L1481) |
| `last_reviewed` | 282f563360390f6648e81bc9d3974bcb8070c496 |
| `related` | ADR-0054 step 3, `#1051` |

##### Requirement {#arch.resolution.requirement-4}

Source-position lookup (`PositionIndex`) is the one lookup structure keyed by byte position. It is rebuilt from a parsed snapshot, never persisted, and never a semantic input — it exists only to answer an editor's "what identity is at byte N" question. The one other span-keyed table, `BindingSpans`, is a transient construction-time bridge: the typed-AST pass reads it to stamp each node's `BindingId` and discards it. Every durable resolved artifact (`ResolutionMap`, the frozen IR) is keyed by identity, never by position.

| Field | Value |
|---|---|
| `status` | `implemented` |
| `owner` | `metel-frontend` |
| `specified by` | `#resolution` |
| `implements` | [`metel-frontend/src/identity/position.rs::from_entries`](https://github.com/metel-lang/metel-core/blob/2aa2c5729e26ccba73bcc69fe338f0941ffc4966/metel-frontend/src/identity/position.rs#L42) |
| `verified by` | [`metel-frontend/src/identity/tests.rs::module_segment_hit_is_position_stable_under_reformatting`](https://github.com/metel-lang/metel-core/blob/2aa2c5729e26ccba73bcc69fe338f0941ffc4966/metel-frontend/src/identity/tests.rs#L694); [`metel-frontend/src/identity/tests.rs::position_index_finds_a_use_and_misses_whitespace`](https://github.com/metel-lang/metel-core/blob/2aa2c5729e26ccba73bcc69fe338f0941ffc4966/metel-frontend/src/identity/tests.rs#L758); [`metel-frontend/src/identity/tests.rs::the_durable_resolution_map_is_keyed_by_identity_not_position`](https://github.com/metel-lang/metel-core/blob/2aa2c5729e26ccba73bcc69fe338f0941ffc4966/metel-frontend/src/identity/tests.rs#L780) |
| `last_reviewed` | 282f563360390f6648e81bc9d3974bcb8070c496 |
| `related` | ADR-0054 (2026-09-10 amendment) |

</details>

## Known limitations

`LIMIT-*` records are the authoritative inventory of known boundaries for this
section. They carry the impact, owner, disposition, and review point; the
Atlas limitations view projects the same records rather than duplicating them.

### Active records

- [`LIMIT-RESOLUTION-001`](../limitations/limit-resolution-001.md) — the resolved-identity model is in-memory only; no on-disk persistence or cross-process interner stability.
- [`LIMIT-RESOLUTION-002`](../limitations/limit-resolution-002.md) — inference-time type lookup falls back to a name-approximate, cross-module search (`#1222`).

### Resolved records

No resolved `LIMIT-*` records are currently recorded for this section.
