# Evaluation {#evaluation}

The tree-walk over `ElaboratedModuleGraph` to program output. Owning crate: `metel-interpreter`. Defined in `evaluator/` (`mod.rs`, `call.rs`, `display.rs`, `lvalue.rs`, `pattern.rs`, `type_of.rs`, `builtins.rs`) and `pipeline.rs` (stage orchestration).

##### Requirement {#arch.evaluation.requirement-1}

`Environment`, the lexical activation-frame model, is keyed entirely by `LocalId`, not by name: a binding is defined and read back by its `LocalId`, two distinct `LocalId`s never alias even for the same source spelling, and no scopes name-map exists as a fallback lookup path.

| Field | Value |
|---|---|
| `status` | `implemented` |
| `owner` | `metel-interpreter` |
| `specified by` | `#evaluation` |
| `implements` | `metel-interpreter/src/evaluator/mod.rs` (`Environment`) |
| `verified by` | `metel-interpreter/src/evaluator/mod.rs::define_binding_is_readable_by_local_id`, `::a_binding_with_no_id_is_simply_not_stored`, `::distinct_local_ids_do_not_alias`, `::capture_clone_starts_with_an_empty_frame`, `::capture_closure_installs_captures_in_the_frame_by_enclosing_id`, `::capture_closure_copy_installs_a_clone_capture_by_id`, `::mut_ref_capture_shares_one_cell_with_the_source`, `::ident_rc_resolves_by_identity_only`, `::lvalue_field_cell_resolves_a_nested_receiver_root_by_id_without_the_name_map`, `::set_local_mutates_the_shared_cell_in_place` |
| `related` | `arch.resolution.requirement-1`, `arch.resolution.requirement-2`, ADR-0029 (per-module isolation, supersedes ADR-0019), ADR-0054, `#1052a`/`#1052b` series |

##### Requirement {#arch.evaluation.requirement-2}

`RuntimeRegistry` dispatches struct/enum type entries and overloaded/top-level function values (`symbol_values`) by stable `SymbolId`, not by re-deriving a name lookup at call time — the runtime-side counterpart of `arch.resolution.requirement-1`'s frozen-identity invariant. Two parts remain genuinely name-keyed by design: `type_ids` (the single surface-name→`SymbolId` translation point for sites that only have a name, e.g. `List::new`, and never had an id threaded to them) and `pattern_methods` (structural, pattern-dispatched method names for receivers like arrays that carry no `type_id`). This is not full coverage of the no-semantic-lookup invariant — `tools/check_no_semantic_name_lookup.py`'s own docstring names `RuntimeRegistry` as "a separate, adjacent concern with its own nuances... not yet brought under this check," i.e. the checker itself documents the gap rather than silently missing it.

| Field | Value |
|---|---|
| `status` | `partial` |
| `owner` | `metel-interpreter` |
| `specified by` | `#evaluation` |
| `implements` | `metel-interpreter/src/evaluator/mod.rs` (`RuntimeRegistry`) |
| `verified by` | general integration-suite coverage (every fixture dispatching a method or calling an overloaded/top-level function exercises this); no unit test directly names the `SymbolId`-keyed dispatch invariant, and `tools/check_no_semantic_name_lookup.py` explicitly excludes `RuntimeRegistry` from its scan |
| `related` | `arch.resolution.requirement-1`, `tools/check_no_semantic_name_lookup.py` |

## Known limitations

- [`LIMIT-EVALUATION-001`](../limitations/limit-evaluation-001.md) — generic function dispatch re-constructs on every call rather than monomorphizing once.
- [`LIMIT-EVALUATION-002`](../limitations/limit-evaluation-002.md) — one specific cross-module mutual-recursion shape is unsupported (`#189`).
- [`LIMIT-EVALUATION-003`](../limitations/limit-evaluation-003.md) — `RuntimeRegistry`'s `type_ids`/`pattern_methods` remain name-keyed and are explicitly outside `tools/check_no_semantic_name_lookup.py`'s scan.
- [`LIMIT-EVALUATION-004`](../limitations/limit-evaluation-004.md) — the evaluator is a deliberate PoC ("will almost certainly be rewritten"), not a stable target shape.
