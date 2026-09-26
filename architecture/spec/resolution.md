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

Once inference has solved a body and the frontend has frozen its resolution, no later phase looks anything up by source spelling: every meaning is found by a stable identity, and every value reference has a total `Resolution` (`Global(SymbolId)` or `Local(LocalId)`), with no silent unresolved case.

| Field | Value |
|---|---|
| `status` | `implemented` |
| `owner` | `metel-frontend` |
| `specified by` | `#resolution` |
| `implements` | [`metel-frontend/src/identity/allocate.rs::allocate_module`](https://github.com/metel-lang/metel-core/blob/5586a5cdb8bda4fa8f25a51700e048c33fe28f73/metel-frontend/src/identity/allocate.rs#L170) |
| `verified by` | [`metel-frontend/src/identity/tests.rs::a_body_with_only_bound_names_has_no_unresolved_references`](https://github.com/metel-lang/metel-core/blob/5586a5cdb8bda4fa8f25a51700e048c33fe28f73/metel-frontend/src/identity/tests.rs#L313); [`metel-frontend/src/identity/tests.rs::a_use_of_a_global_declaration_is_classified_as_global`](https://github.com/metel-lang/metel-core/blob/5586a5cdb8bda4fa8f25a51700e048c33fe28f73/metel-frontend/src/identity/tests.rs#L326); [`metel-frontend/src/identity/tests.rs::reference_table_is_total_and_unknown_names_are_explicit`](https://github.com/metel-lang/metel-core/blob/5586a5cdb8bda4fa8f25a51700e048c33fe28f73/metel-frontend/src/identity/tests.rs#L301) |
| `last_reviewed` | 282f563360390f6648e81bc9d3974bcb8070c496 |
| `related` | ADR-0054, ADR-0041, ADR-0042 |

##### Requirement {#arch.resolution.requirement-2}

Bindings and value references get structural identities (`LocalId`, `RefId`) from a parse-driven walk keyed on `LexicalPath`, not on byte offsets or traversal counters, so reformatting, an earlier sibling binding, or an edit to another body does not change an existing identity.

| Field | Value |
|---|---|
| `status` | `implemented` |
| `owner` | `metel-frontend` |
| `specified by` | `#resolution` |
| `implements` | [`metel-frontend/src/identity/allocate.rs::allocate_module`](https://github.com/metel-lang/metel-core/blob/5586a5cdb8bda4fa8f25a51700e048c33fe28f73/metel-frontend/src/identity/allocate.rs#L171) |
| `verified by` | [`metel-frontend/src/identity/tests.rs::blank_lines_and_reformatting_change_no_identity`](https://github.com/metel-lang/metel-core/blob/5586a5cdb8bda4fa8f25a51700e048c33fe28f73/metel-frontend/src/identity/tests.rs#L118); [`metel-frontend/src/identity/tests.rs::editing_one_body_leaves_another_bodys_identities_untouched`](https://github.com/metel-lang/metel-core/blob/5586a5cdb8bda4fa8f25a51700e048c33fe28f73/metel-frontend/src/identity/tests.rs#L152); [`metel-frontend/src/identity/tests.rs::inserting_an_earlier_binding_does_not_renumber_a_later_one`](https://github.com/metel-lang/metel-core/blob/5586a5cdb8bda4fa8f25a51700e048c33fe28f73/metel-frontend/src/identity/tests.rs#L139) |
| `last_reviewed` | 282f563360390f6648e81bc9d3974bcb8070c496 |
| `related` | ADR-0054 (2026-09-10 amendment) |

##### Requirement {#arch.resolution.requirement-3}

Struct fields and enum variants are interned to stable `FieldId` / `VariantId`, keyed by `(owning type SymbolId, member name)` before inference, and threaded onto the typed IR as `Option<FieldId>` / `Option<VariantId>` rather than re-derived from a string.

| Field | Value |
|---|---|
| `status` | `implemented` |
| `owner` | `metel-frontend` |
| `specified by` | `#resolution` |
| `implements` | [`metel-frontend/src/identity/member.rs::collect_members`](https://github.com/metel-lang/metel-core/blob/5586a5cdb8bda4fa8f25a51700e048c33fe28f73/metel-frontend/src/identity/member.rs#L156) |
| `verified by` | [`metel-frontend/src/identity/member.rs::absent_members_report_none_not_a_fabricated_id`](https://github.com/metel-lang/metel-core/blob/5586a5cdb8bda4fa8f25a51700e048c33fe28f73/metel-frontend/src/identity/member.rs#L330); [`metel-frontend/src/identity/member.rs::enum_variants_and_their_fields_are_interned`](https://github.com/metel-lang/metel-core/blob/5586a5cdb8bda4fa8f25a51700e048c33fe28f73/metel-frontend/src/identity/member.rs#L293); [`metel-frontend/src/identity/member.rs::interning_is_reformat_stable_and_order_independent`](https://github.com/metel-lang/metel-core/blob/5586a5cdb8bda4fa8f25a51700e048c33fe28f73/metel-frontend/src/identity/member.rs#L310); [`metel-frontend/src/identity/member.rs::same_field_name_on_different_types_is_a_different_id`](https://github.com/metel-lang/metel-core/blob/5586a5cdb8bda4fa8f25a51700e048c33fe28f73/metel-frontend/src/identity/member.rs#L280); [`metel-frontend/src/identity/member.rs::struct_fields_get_distinct_ids_owned_by_the_struct`](https://github.com/metel-lang/metel-core/blob/5586a5cdb8bda4fa8f25a51700e048c33fe28f73/metel-frontend/src/identity/member.rs#L268); [`metel-frontend/src/pipeline/type_checking/tests.rs::typed_ir_threads_member_ids_rather_than_rederiving_them`](https://github.com/metel-lang/metel-core/blob/5586a5cdb8bda4fa8f25a51700e048c33fe28f73/metel-frontend/src/pipeline/type_checking/tests.rs#L2) |
| `last_reviewed` | 26ffffc1aabe3e17d10726af0d719a8ab79a7869 |
| `related` | ADR-0054 step 3, `#1051` |

##### Requirement {#arch.resolution.requirement-4}

`PositionIndex` is the one byte-position-keyed lookup: rebuilt from a parsed snapshot, never persisted, never a semantic input. `BindingSpans` is a transient construction-time bridge; every durable resolved artifact (`ResolutionMap`, the frozen IR) is keyed by identity, not position.

| Field | Value |
|---|---|
| `status` | `implemented` |
| `owner` | `metel-frontend` |
| `specified by` | `#resolution` |
| `implements` | [`metel-frontend/src/identity/position.rs::from_entries`](https://github.com/metel-lang/metel-core/blob/5586a5cdb8bda4fa8f25a51700e048c33fe28f73/metel-frontend/src/identity/position.rs#L42) |
| `verified by` | [`metel-frontend/src/identity/tests.rs::module_segment_hit_is_position_stable_under_reformatting`](https://github.com/metel-lang/metel-core/blob/5586a5cdb8bda4fa8f25a51700e048c33fe28f73/metel-frontend/src/identity/tests.rs#L701); [`metel-frontend/src/identity/tests.rs::position_index_finds_a_use_and_misses_whitespace`](https://github.com/metel-lang/metel-core/blob/5586a5cdb8bda4fa8f25a51700e048c33fe28f73/metel-frontend/src/identity/tests.rs#L769); [`metel-frontend/src/identity/tests.rs::the_durable_resolution_map_is_keyed_by_identity_not_position`](https://github.com/metel-lang/metel-core/blob/5586a5cdb8bda4fa8f25a51700e048c33fe28f73/metel-frontend/src/identity/tests.rs#L791) |
| `last_reviewed` | de72649a95a5c947ac985069b692008b76a82f7e |
| `related` | ADR-0054 (2026-09-10 amendment) |

</details>

## Known limitations

<!-- records:limitations -->
