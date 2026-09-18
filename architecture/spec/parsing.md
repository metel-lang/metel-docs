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
([control-flow expressions](#arch.parsing.requirement-4)); grammar ordering protects
surface disambiguations such as `None` and keyword-prefix identifiers
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
| `implements` | `metel-frontend/src/module_loader.rs` (`Loader::load_module`, `ModuleGraph`) |
| `verified by` | `metel-frontend/src/module_loader.rs` unit tests (`std_namespace_is_reserved_for_user_modules`, `source_provider_overlay_supplies_in_memory_source`, `multi_file_source_provider_resolves_an_import`, `virtual_root_loads_without_an_on_disk_root`); integration fixtures `metel-interpreter/tests/integration/sources/module_loading/rejects_circular_module_graph`, `multi_file_program_runs_after_module_loading`, `transitive_dependency_loaded_via_facade` |
| `related` | RFC-0058, ADR-0023 (hierarchical module paths), ADR-0031 (diamond-dependency path aliasing), `#1147` |

##### Requirement {#arch.parsing.requirement-2}

Module source is read through a `SourceProvider` abstraction rather than a hardcoded filesystem call — the default (`EmbeddedStdlibProvider`) serves `std::…` modules from a binary-embedded source and everything else from disk, but an `InMemorySourceProvider` / `MultiFileSourceProvider` can substitute a virtual root (and its imports) without touching disk, and `load_virtual_root_with` skips filesystem canonicalization entirely for that case. This is what lets an LSP overlay shadow a stdlib module or serve unsaved buffers through the same loading path production use takes, rather than a parallel one. The embedded source itself is real, physical `.mtl` files (`metel-frontend/stdlib/*.mtl`) compiled in at build time (ADR-0039, superseding ADR-0027's virtual, no-physical-file injection list).

| Field | Value |
|---|---|
| `status` | `implemented` |
| `owner` | `metel-frontend` |
| `specified by` | `#parsing` |
| `implements` | `metel-frontend/src/module_loader.rs` (`SourceProvider`, `EmbeddedStdlibProvider`, `InMemorySourceProvider`, `MultiFileSourceProvider`, `load_virtual_root_with`) |
| `verified by` | `metel-frontend/src/module_loader.rs::source_provider_overlay_supplies_in_memory_source`, `::multi_file_source_provider_resolves_an_import`, `::multi_file_source_provider_reports_a_missing_sibling`, `::virtual_root_loads_without_an_on_disk_root` |
| `related` | RFC-0058, ADR-0039 |

##### Requirement {#arch.parsing.requirement-3}

A single file parses through one PEG grammar (`grammar.pest`, driven by `pest`/`pest_derive`) via the sole entry point `parser::parse(source, filename) -> Result<Program, MetelError>`. Every AST node's `Span` carries byte offsets plus resolved line/col, and derives `Eq`/`Hash` so it can key the reference-resolution side table later in the pipeline — a span is diagnostic-and-lookup infrastructure, not decoration. The grammar's own ordering invariants (e.g. `stmt` tried before binding declarations so `let_x = 5;` parses as assignment, not declaration; `return`/`break`/`continue` as expressions per `#229`) are documented inline in `grammar.pest` itself, not only in this section.

| Field | Value |
|---|---|
| `status` | `implemented` |
| `owner` | `metel-frontend` |
| `specified by` | `#parsing` |
| `implements` | `metel-frontend/src/parser/mod.rs` (`parse`), `metel-frontend/src/grammar.pest`, `metel-frontend/src/ast/mod.rs` (`Span`, `Program`) |
| `verified by` | `metel-frontend/src/parser/mod.rs::multi_segment_path_carries_one_span_per_segment`, `::keyword_root_path_spans_cover_the_root_segment`, `::two_segment_path_in_call_position_keeps_segment_spans` (span-tracking specifically); general grammar correctness is a precondition of the full integration suite (1,183 `.mtl` fixtures under `metel-interpreter/tests/integration/sources/`, every one of which must parse before its actual assertion runs) rather than a dedicated parser-correctness suite of its own |
| `related` | `#229` |

##### Requirement {#arch.parsing.requirement-4}

Control flow has one expression-shaped representation through the parser and AST: `if`, `match`, and `loop` can be a block tail or an expression statement, with statement position discarding the expression value rather than introducing parallel statement-only AST forms. An `if` without `else` is `Unit`-typed, and an `else if` is represented as a nested `if` in a block rather than a separate chain node.

| Field | Value |
|---|---|
| `status` | `implemented` |
| `owner` | `metel-frontend` |
| `specified by` | `#parsing` |
| `implements` | `metel-frontend/src/grammar.pest` (`block_item`, `block_expr_stmt`, expression rules); `metel-frontend/src/parser/mod.rs` (`parse_if_expr`, `parse_block`); `metel-frontend/src/ast/mod.rs` (`Expr::If`, `Expr::Match`, `Expr::Loop`) |
| `verified by` | general integration-suite coverage of control-flow expressions; no dedicated current parser unit test naming the statement-versus-tail representation was found |
| `related` | ADR-0005 |

##### Requirement {#arch.parsing.requirement-5}

Grammar ordering preserves identifier-prefix and `None`-literal disambiguation: a literal token is bounded so `Perhaps::None` and a user variant named `None` remain paths, while standalone `None` parses as the literal; keyword-prefix identifiers are not consumed by a keyword alternative. These are grammar-order invariants, not typechecker rewrites.

| Field | Value |
|---|---|
| `status` | `implemented` |
| `owner` | `metel-frontend` |
| `specified by` | `#parsing` |
| `implements` | `metel-frontend/src/grammar.pest` (`none_lit`, `primary_expr`, `pattern`, keyword/identifier alternatives) |
| `verified by` | general integration-suite coverage of enum paths, literals, and identifiers; no dedicated current parser unit test naming each ordering invariant was found |
| `related` | ADR-0015, ADR-0018 |

##### Requirement {#arch.parsing.requirement-6}

String interpolation is lowered while parsing into ordinary expression nodes: each hole is parsed as an expression and converted to a `to_string` method call, and literal segments are joined with `BinOp::Plus`. Downstream passes therefore see no interpolation-specific AST variant or dispatch path.

| Field | Value |
|---|---|
| `status` | `implemented` |
| `owner` | `metel-frontend` |
| `specified by` | `#parsing` |
| `implements` | `metel-frontend/src/parser/mod.rs` (`parse_string_interpolation`); `metel-frontend/src/ast/mod.rs` (`Expr::MethodCall`, `Expr::Binary`) |
| `verified by` | general integration-suite coverage of interpolation; no dedicated parser unit test naming the lowering shape was found |
| `related` | ADR-0033 |

</details>

## Known limitations

`LIMIT-*` records are the authoritative inventory of known boundaries for this
section. They carry the impact, owner, disposition, and review point; the
Atlas limitations view projects the same records rather than duplicating them.

### Active records

No active `LIMIT-*` records are currently recorded for this section. This is
a current inventory, not a claim of complete coverage.

### Resolved records

No resolved `LIMIT-*` records are currently recorded for this section.
