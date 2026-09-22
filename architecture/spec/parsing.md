# Module Loading & Parsing {#parsing}

The pipeline's front door: a root source file becomes a per-file-parsed, dependency-ordered `ModuleGraph` before any resolution or type checking begins. Owning crate: `metel-frontend`. Defined in `module_loader.rs` (graph loading), `module_paths.rs` (path-root resolution), `parser/` + `grammar.pest` (per-file parsing), and `ast/` (the untyped AST the parser produces).

## Model

Loading first establishes the program boundary: modules are discovered from a root,
their dependencies are ordered, and cycles are rejected before a later stage can see a
partial program ([module graph](#arch.parsing.requirement-1)). Source providers make
that same model work for files, embedded standard-library modules, and in-memory test
programs ([source provisioning](#arch.parsing.requirement-2)).

Parsing then produces one ordinary AST vocabulary for the rest of the pipeline. Control
flow is expression-shaped whether used as a block tail or statement
([control-flow expressions](#arch.parsing.requirement-4)); the grammar keeps keyword-prefix
identifiers distinct from keywords
([disambiguation](#arch.parsing.requirement-5)); and interpolation lowers immediately
to ordinary expressions ([interpolation](#arch.parsing.requirement-6)). No downstream
stage needs a parser-only semantic special case.

<details>
<summary>Verifiable architecture claims</summary>

##### Requirement {#arch.parsing.requirement-1}

Loading a root file yields a `ModuleGraph` in dependency order: a module appears only after every module it imports or re-exports, because `Loader::load_module` recurses into them first. A circular import is rejected with the full cycle traced through the DFS stack.

| Field | Value |
|---|---|
| `status` | `implemented` |
| `owner` | `metel-frontend` |
| `specified by` | `#parsing` |
| `implements` | [`metel-frontend/src/module_loader.rs::load_module`](https://github.com/metel-lang/metel-core/blob/4155d94ccbc5b1657799f3537515610f3bb139c3/metel-frontend/src/module_loader.rs#L506) |
| `verified by` | [`metel-frontend/src/module_loader.rs::a_cycle_is_reported_with_its_full_chain`](https://github.com/metel-lang/metel-core/blob/4155d94ccbc5b1657799f3537515610f3bb139c3/metel-frontend/src/module_loader.rs#L1076); [`metel-frontend/src/module_loader.rs::modules_load_in_dependency_order`](https://github.com/metel-lang/metel-core/blob/4155d94ccbc5b1657799f3537515610f3bb139c3/metel-frontend/src/module_loader.rs#L1046); [`metel-interpreter/tests/integration/sources/module_loading/rejects_circular_module_graph/test.toml`](https://github.com/metel-lang/metel-core/blob/4155d94ccbc5b1657799f3537515610f3bb139c3/metel-interpreter/tests/integration/sources/module_loading/rejects_circular_module_graph/test.toml#L1) |
| `last_reviewed` | 7de56e3de9a7841d926b5c185ff95b6c7bf03b22 |
| `related` | RFC-0058, ADR-0023 (hierarchical module paths), ADR-0031 (diamond-dependency path aliasing), `#1147` |

##### Requirement {#arch.parsing.requirement-2}

Module source is read through a `SourceProvider` (embedded stdlib plus disk by default), and `InMemorySourceProvider` / `MultiFileSourceProvider` can substitute a virtual root without touching disk, so an LSP overlay uses the same loading path as production.

| Field | Value |
|---|---|
| `status` | `implemented` |
| `owner` | `metel-frontend` |
| `specified by` | `#parsing` |
| `implements` | [`metel-frontend/src/module_loader.rs::load_virtual_root_with`](https://github.com/metel-lang/metel-core/blob/4155d94ccbc5b1657799f3537515610f3bb139c3/metel-frontend/src/module_loader.rs#L297) |
| `verified by` | [`metel-frontend/src/module_loader.rs::multi_file_source_provider_reports_a_missing_sibling`](https://github.com/metel-lang/metel-core/blob/4155d94ccbc5b1657799f3537515610f3bb139c3/metel-frontend/src/module_loader.rs#L1095); [`metel-frontend/src/module_loader.rs::multi_file_source_provider_resolves_an_import`](https://github.com/metel-lang/metel-core/blob/4155d94ccbc5b1657799f3537515610f3bb139c3/metel-frontend/src/module_loader.rs#L1018); [`metel-frontend/src/module_loader.rs::source_provider_overlay_supplies_in_memory_source`](https://github.com/metel-lang/metel-core/blob/4155d94ccbc5b1657799f3537515610f3bb139c3/metel-frontend/src/module_loader.rs#L999); [`metel-frontend/src/module_loader.rs::virtual_root_loads_without_an_on_disk_root`](https://github.com/metel-lang/metel-core/blob/4155d94ccbc5b1657799f3537515610f3bb139c3/metel-frontend/src/module_loader.rs#L1111) |
| `last_reviewed` | 7de56e3de9a7841d926b5c185ff95b6c7bf03b22 |
| `related` | RFC-0058, ADR-0039 |

##### Requirement {#arch.parsing.requirement-3}

A file parses through one PEG grammar (`grammar.pest`) via the sole entry point `parser::parse(source, filename)`. Every AST node's `Span` carries byte offsets and resolved line/col and derives `Eq`/`Hash`, so it can key the reference-resolution side table.

| Field | Value |
|---|---|
| `status` | `implemented` |
| `owner` | `metel-frontend` |
| `specified by` | `#parsing` |
| `implements` | [`metel-frontend/src/parser/mod.rs::parse`](https://github.com/metel-lang/metel-core/blob/4155d94ccbc5b1657799f3537515610f3bb139c3/metel-frontend/src/parser/mod.rs#L27) |
| `verified by` | [`metel-frontend/src/parser/mod.rs::multi_segment_path_carries_one_span_per_segment`](https://github.com/metel-lang/metel-core/blob/4155d94ccbc5b1657799f3537515610f3bb139c3/metel-frontend/src/parser/mod.rs#L3508); [`metel-frontend/src/parser/mod.rs::span_is_eq_hash_and_carries_resolved_line_and_column`](https://github.com/metel-lang/metel-core/blob/4155d94ccbc5b1657799f3537515610f3bb139c3/metel-frontend/src/parser/mod.rs#L3573) |
| `last_reviewed` | 7de56e3de9a7841d926b5c185ff95b6c7bf03b22 |
| `related` | `#229` |

##### Requirement {#arch.parsing.requirement-4}

Control flow has one expression-shaped representation: `if`, `match` and `loop` may be a block tail or an expression statement, with statement position discarding the value. An `if` without `else` is `Unit`-typed, and `else if` is a nested `if` in the else block.

| Field | Value |
|---|---|
| `status` | `implemented` |
| `owner` | `metel-frontend` |
| `specified by` | `#parsing` |
| `implements` | [`metel-frontend/src/parser/mod.rs::parse_if_expr`](https://github.com/metel-lang/metel-core/blob/4155d94ccbc5b1657799f3537515610f3bb139c3/metel-frontend/src/parser/mod.rs#L1822) |
| `verified by` | [`metel-frontend/src/parser/mod.rs::control_flow_is_an_expression_in_tail_and_statement_position`](https://github.com/metel-lang/metel-core/blob/4155d94ccbc5b1657799f3537515610f3bb139c3/metel-frontend/src/parser/mod.rs#L3624); [`metel-frontend/src/parser/mod.rs::else_if_is_a_nested_if_in_the_else_block_and_a_bare_if_has_no_else`](https://github.com/metel-lang/metel-core/blob/4155d94ccbc5b1657799f3537515610f3bb139c3/metel-frontend/src/parser/mod.rs#L3589); [`metel-interpreter/tests/integration/sources/evaluator/control_flow/88_braceless_if_no_else_in_expression_position.toml`](https://github.com/metel-lang/metel-core/blob/4155d94ccbc5b1657799f3537515610f3bb139c3/metel-interpreter/tests/integration/sources/evaluator/control_flow/88_braceless_if_no_else_in_expression_position.toml#L1) |
| `last_reviewed` | 7de56e3de9a7841d926b5c185ff95b6c7bf03b22 |
| `related` | ADR-0005 |

##### Requirement {#arch.parsing.requirement-5}

Keyword disambiguation is a grammar invariant: `keyword` matches a whole word only and `ident` is `!keyword` plus identifier characters, so `letter` or `iffy` is an identifier and a whole keyword never is. `None` is not special-cased by the grammar.

| Field | Value |
|---|---|
| `status` | `implemented` |
| `owner` | `metel-frontend` |
| `specified by` | `#parsing` |
| `implements` | [`metel-frontend/src/grammar.pest::ident`](https://github.com/metel-lang/metel-core/blob/4155d94ccbc5b1657799f3537515610f3bb139c3/metel-frontend/src/grammar.pest#L418); [`metel-frontend/src/grammar.pest::keyword`](https://github.com/metel-lang/metel-core/blob/4155d94ccbc5b1657799f3537515610f3bb139c3/metel-frontend/src/grammar.pest#L423) |
| `verified by` | [`metel-interpreter/tests/integration/sources/parsing/keyword_prefixed_identifiers.toml`](https://github.com/metel-lang/metel-core/blob/4155d94ccbc5b1657799f3537515610f3bb139c3/metel-interpreter/tests/integration/sources/parsing/keyword_prefixed_identifiers.toml#L1); [`metel-interpreter/tests/integration/sources/parsing/neg_keyword_as_identifier.toml`](https://github.com/metel-lang/metel-core/blob/4155d94ccbc5b1657799f3537515610f3bb139c3/metel-interpreter/tests/integration/sources/parsing/neg_keyword_as_identifier.toml#L1) |
| `last_reviewed` | e351096dc3e82c3715c0709f274081691673946e |
| `related` | ADR-0015, ADR-0018 |

##### Requirement {#arch.parsing.requirement-6}

String interpolation is lowered while parsing: each hole becomes a `to_string` method call and the segments are joined with `BinOp::Add` in a balanced tree, so downstream passes see no interpolation node and no deeply left-nested chain.

| Field | Value |
|---|---|
| `status` | `implemented` |
| `owner` | `metel-frontend` |
| `specified by` | `#parsing` |
| `implements` | [`metel-frontend/src/parser/mod.rs::parse_string_literal_expr`](https://github.com/metel-lang/metel-core/blob/4155d94ccbc5b1657799f3537515610f3bb139c3/metel-frontend/src/parser/mod.rs#L1171) |
| `verified by` | [`metel-frontend/src/parser/mod.rs::interpolation_lowers_to_add_of_to_string_calls`](https://github.com/metel-lang/metel-core/blob/4155d94ccbc5b1657799f3537515610f3bb139c3/metel-frontend/src/parser/mod.rs#L3648); [`metel-frontend/src/parser/mod.rs::the_ast_has_no_interpolation_node`](https://github.com/metel-lang/metel-core/blob/4155d94ccbc5b1657799f3537515610f3bb139c3/metel-frontend/src/parser/mod.rs#L3667) |
| `last_reviewed` | 7de56e3de9a7841d926b5c185ff95b6c7bf03b22 |
| `related` | ADR-0033 |

</details>

## Known limitations

<!-- records:limitations -->
