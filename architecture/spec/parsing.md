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

Loading a root file produces a `ModuleGraph` whose `modules: Vec<LoadedModule>` is in dependency order — each module appears only after every module it imports or re-exports (`export path::Name;`, #660), because `Loader::load_module` recurses into a module's imports and exports before pushing the module itself onto the graph. A circular import chain is rejected with the full cycle traced through the loader's DFS stack, not merely detected.

| Field | Value |
|---|---|
| `status` | `implemented` |
| `owner` | `metel-frontend` |
| `specified by` | `#parsing` |
| `implements` | [`metel-frontend/src/module_loader.rs::load_module`](https://github.com/metel-lang/metel-core/blob/2aa2c5729e26ccba73bcc69fe338f0941ffc4966/metel-frontend/src/module_loader.rs#L506) |
| `verified by` | [`metel-frontend/src/module_loader.rs::a_cycle_is_reported_with_its_full_chain`](https://github.com/metel-lang/metel-core/blob/2aa2c5729e26ccba73bcc69fe338f0941ffc4966/metel-frontend/src/module_loader.rs#L1076); [`metel-frontend/src/module_loader.rs::modules_load_in_dependency_order`](https://github.com/metel-lang/metel-core/blob/2aa2c5729e26ccba73bcc69fe338f0941ffc4966/metel-frontend/src/module_loader.rs#L1046); [`metel-interpreter/tests/integration/sources/module_loading/rejects_circular_module_graph/test.toml`](https://github.com/metel-lang/metel-core/blob/2aa2c5729e26ccba73bcc69fe338f0941ffc4966/metel-interpreter/tests/integration/sources/module_loading/rejects_circular_module_graph/test.toml#L1) |
| `last_reviewed` | 7de56e3de9a7841d926b5c185ff95b6c7bf03b22 |
| `related` | RFC-0058, ADR-0023 (hierarchical module paths), ADR-0031 (diamond-dependency path aliasing), `#1147` |

##### Requirement {#arch.parsing.requirement-2}

Module source is read through a `SourceProvider` abstraction rather than a hardcoded filesystem call — the default (`EmbeddedStdlibProvider`) serves `std::…` modules from a binary-embedded source and everything else from disk, but an `InMemorySourceProvider` / `MultiFileSourceProvider` can substitute a virtual root (and its imports) without touching disk, and `load_virtual_root_with` skips filesystem canonicalization entirely for that case. This is what lets an LSP overlay shadow a stdlib module or serve unsaved buffers through the same loading path production use takes, rather than a parallel one. The embedded source itself is real, physical `.mtl` files (`metel-frontend/stdlib/*.mtl`) compiled in at build time (ADR-0039, superseding ADR-0027's virtual, no-physical-file injection list).

| Field | Value |
|---|---|
| `status` | `implemented` |
| `owner` | `metel-frontend` |
| `specified by` | `#parsing` |
| `implements` | [`metel-frontend/src/module_loader.rs::load_virtual_root_with`](https://github.com/metel-lang/metel-core/blob/2aa2c5729e26ccba73bcc69fe338f0941ffc4966/metel-frontend/src/module_loader.rs#L297) |
| `verified by` | [`metel-frontend/src/module_loader.rs::multi_file_source_provider_reports_a_missing_sibling`](https://github.com/metel-lang/metel-core/blob/2aa2c5729e26ccba73bcc69fe338f0941ffc4966/metel-frontend/src/module_loader.rs#L1095); [`metel-frontend/src/module_loader.rs::multi_file_source_provider_resolves_an_import`](https://github.com/metel-lang/metel-core/blob/2aa2c5729e26ccba73bcc69fe338f0941ffc4966/metel-frontend/src/module_loader.rs#L1018); [`metel-frontend/src/module_loader.rs::source_provider_overlay_supplies_in_memory_source`](https://github.com/metel-lang/metel-core/blob/2aa2c5729e26ccba73bcc69fe338f0941ffc4966/metel-frontend/src/module_loader.rs#L999); [`metel-frontend/src/module_loader.rs::virtual_root_loads_without_an_on_disk_root`](https://github.com/metel-lang/metel-core/blob/2aa2c5729e26ccba73bcc69fe338f0941ffc4966/metel-frontend/src/module_loader.rs#L1111) |
| `last_reviewed` | 7de56e3de9a7841d926b5c185ff95b6c7bf03b22 |
| `related` | RFC-0058, ADR-0039 |

##### Requirement {#arch.parsing.requirement-3}

A single file parses through one PEG grammar (`grammar.pest`, driven by `pest`/`pest_derive`) via the sole entry point `parser::parse(source, filename) -> Result<Program, MetelError>`. Every AST node's `Span` carries byte offsets plus resolved line/col, and derives `Eq`/`Hash` so it can key the reference-resolution side table later in the pipeline — a span is diagnostic-and-lookup infrastructure, not decoration. The grammar's own ordering invariants (e.g. `stmt` tried before binding declarations so `let_x = 5;` parses as assignment, not declaration; `return`/`break`/`continue` as expressions per `#229`) are documented inline in `grammar.pest` itself, not only in this section.

| Field | Value |
|---|---|
| `status` | `implemented` |
| `owner` | `metel-frontend` |
| `specified by` | `#parsing` |
| `implements` | [`metel-frontend/src/parser/mod.rs::parse`](https://github.com/metel-lang/metel-core/blob/2aa2c5729e26ccba73bcc69fe338f0941ffc4966/metel-frontend/src/parser/mod.rs#L27) |
| `verified by` | [`metel-frontend/src/parser/mod.rs::multi_segment_path_carries_one_span_per_segment`](https://github.com/metel-lang/metel-core/blob/2aa2c5729e26ccba73bcc69fe338f0941ffc4966/metel-frontend/src/parser/mod.rs#L3508); [`metel-frontend/src/parser/mod.rs::span_is_eq_hash_and_carries_resolved_line_and_column`](https://github.com/metel-lang/metel-core/blob/2aa2c5729e26ccba73bcc69fe338f0941ffc4966/metel-frontend/src/parser/mod.rs#L3573) |
| `last_reviewed` | 7de56e3de9a7841d926b5c185ff95b6c7bf03b22 |
| `related` | `#229` |

##### Requirement {#arch.parsing.requirement-4}

Control flow has one expression-shaped representation through the parser and AST: `if`, `match`, and `loop` can be a block tail or an expression statement, with statement position discarding the expression value rather than introducing parallel statement-only AST forms. An `if` without `else` is `Unit`-typed, and an `else if` is represented as a nested `if` in a block rather than a separate chain node.

| Field | Value |
|---|---|
| `status` | `implemented` |
| `owner` | `metel-frontend` |
| `specified by` | `#parsing` |
| `implements` | [`metel-frontend/src/parser/mod.rs::parse_if_expr`](https://github.com/metel-lang/metel-core/blob/2aa2c5729e26ccba73bcc69fe338f0941ffc4966/metel-frontend/src/parser/mod.rs#L1822) |
| `verified by` | [`metel-frontend/src/parser/mod.rs::control_flow_is_an_expression_in_tail_and_statement_position`](https://github.com/metel-lang/metel-core/blob/2aa2c5729e26ccba73bcc69fe338f0941ffc4966/metel-frontend/src/parser/mod.rs#L3624); [`metel-frontend/src/parser/mod.rs::else_if_is_a_nested_if_in_the_else_block_and_a_bare_if_has_no_else`](https://github.com/metel-lang/metel-core/blob/2aa2c5729e26ccba73bcc69fe338f0941ffc4966/metel-frontend/src/parser/mod.rs#L3589); [`metel-interpreter/tests/integration/sources/evaluator/control_flow/88_braceless_if_no_else_in_expression_position.toml`](https://github.com/metel-lang/metel-core/blob/2aa2c5729e26ccba73bcc69fe338f0941ffc4966/metel-interpreter/tests/integration/sources/evaluator/control_flow/88_braceless_if_no_else_in_expression_position.toml#L1) |
| `last_reviewed` | 7de56e3de9a7841d926b5c185ff95b6c7bf03b22 |
| `related` | ADR-0005 |

##### Requirement {#arch.parsing.requirement-5}

Keyword-prefix disambiguation is a grammar-level invariant, not a typechecker rewrite: the `keyword` rule matches a whole word only (it ends in a word-boundary lookahead) and `ident` is `!keyword` followed by identifier characters, so a name that merely begins with a keyword (`letter`, `iffy`, `returned`) is an ordinary identifier while a whole keyword is never one. The grammar does not special-case `None`: standalone `None`, `Perhaps::None`, and a user variant named `None` are all ordinary identifiers or paths, given meaning by later stages.

| Field | Value |
|---|---|
| `status` | `implemented` |
| `owner` | `metel-frontend` |
| `specified by` | `#parsing` |
| `implements` | [`metel-frontend/src/grammar.pest::ident`](https://github.com/metel-lang/metel-core/blob/2aa2c5729e26ccba73bcc69fe338f0941ffc4966/metel-frontend/src/grammar.pest#L418); [`metel-frontend/src/grammar.pest::keyword`](https://github.com/metel-lang/metel-core/blob/2aa2c5729e26ccba73bcc69fe338f0941ffc4966/metel-frontend/src/grammar.pest#L423) |
| `verified by` | [`metel-interpreter/tests/integration/sources/parsing/keyword_prefixed_identifiers.toml`](https://github.com/metel-lang/metel-core/blob/2aa2c5729e26ccba73bcc69fe338f0941ffc4966/metel-interpreter/tests/integration/sources/parsing/keyword_prefixed_identifiers.toml#L1); [`metel-interpreter/tests/integration/sources/parsing/neg_keyword_as_identifier.toml`](https://github.com/metel-lang/metel-core/blob/2aa2c5729e26ccba73bcc69fe338f0941ffc4966/metel-interpreter/tests/integration/sources/parsing/neg_keyword_as_identifier.toml#L1) |
| `last_reviewed` | e351096dc3e82c3715c0709f274081691673946e |
| `related` | ADR-0015, ADR-0018 |

##### Requirement {#arch.parsing.requirement-6}

String interpolation is lowered while parsing into ordinary expression nodes: each hole is parsed as an expression and converted to a `to_string` method call, and the segments are joined with `BinOp::Add` in a balanced tree (so a long interpolation does not become a deeply left-nested chain that overflows downstream recursion). Downstream passes therefore see no interpolation-specific AST variant or dispatch path.

| Field | Value |
|---|---|
| `status` | `implemented` |
| `owner` | `metel-frontend` |
| `specified by` | `#parsing` |
| `implements` | [`metel-frontend/src/parser/mod.rs::parse_string_literal_expr`](https://github.com/metel-lang/metel-core/blob/2aa2c5729e26ccba73bcc69fe338f0941ffc4966/metel-frontend/src/parser/mod.rs#L1171) |
| `verified by` | [`metel-frontend/src/parser/mod.rs::interpolation_lowers_to_add_of_to_string_calls`](https://github.com/metel-lang/metel-core/blob/2aa2c5729e26ccba73bcc69fe338f0941ffc4966/metel-frontend/src/parser/mod.rs#L3648); [`metel-frontend/src/parser/mod.rs::the_ast_has_no_interpolation_node`](https://github.com/metel-lang/metel-core/blob/2aa2c5729e26ccba73bcc69fe338f0941ffc4966/metel-frontend/src/parser/mod.rs#L3667) |
| `last_reviewed` | 7de56e3de9a7841d926b5c185ff95b6c7bf03b22 |
| `related` | ADR-0033 |

</details>

## Known limitations

<!-- records:limitations -->
