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
| `implements` | _Generated at publish._ |
| `verified by` | _Generated at publish._ |
| `last_reviewed` | 006a9aafdcb4bc9c7328ad882c08d32737058a51 |
| `related` | RFC-0058, ADR-0023 (hierarchical module paths), ADR-0031 (diamond-dependency path aliasing), `#1147` |

##### Requirement {#arch.parsing.requirement-2}

Module source is read through a `SourceProvider` (embedded stdlib plus disk by default), and `InMemorySourceProvider` / `MultiFileSourceProvider` can substitute a virtual root without touching disk, so an LSP overlay uses the same loading path as production.

| Field | Value |
|---|---|
| `status` | `implemented` |
| `owner` | `metel-frontend` |
| `specified by` | `#parsing` |
| `implements` | _Generated at publish._ |
| `verified by` | _Generated at publish._ |
| `last_reviewed` | 006a9aafdcb4bc9c7328ad882c08d32737058a51 |
| `related` | RFC-0058, ADR-0039 |

##### Requirement {#arch.parsing.requirement-3}

A file parses through one PEG grammar (`grammar.pest`) via the sole entry point `parser::parse(source, filename)`. Every AST node's `Span` carries byte offsets and resolved line/col and derives `Eq`/`Hash`, so it can key the reference-resolution side table.

| Field | Value |
|---|---|
| `status` | `implemented` |
| `owner` | `metel-frontend` |
| `specified by` | `#parsing` |
| `implements` | _Generated at publish._ |
| `verified by` | _Generated at publish._ |
| `last_reviewed` | 482a47de2a50db592c02804b14155c2310a76bb5 |
| `related` | `#229` |

##### Requirement {#arch.parsing.requirement-4}

Control flow has one expression-shaped representation: `if`, `match` and `loop` may be a block tail or an expression statement, with statement position discarding the value. An `if` without `else` is `Unit`-typed, and `else if` is a nested `if` in the else block.

| Field | Value |
|---|---|
| `status` | `implemented` |
| `owner` | `metel-frontend` |
| `specified by` | `#parsing` |
| `implements` | _Generated at publish._ |
| `verified by` | _Generated at publish._ |
| `last_reviewed` | 7de56e3de9a7841d926b5c185ff95b6c7bf03b22 |
| `related` | ADR-0005 |

##### Requirement {#arch.parsing.requirement-5}

Keyword disambiguation is a grammar invariant: `keyword` matches a whole word only and `ident` is `!keyword` plus identifier characters, so `letter` or `iffy` is an identifier and a whole keyword never is. `None` is not special-cased by the grammar.

| Field | Value |
|---|---|
| `status` | `implemented` |
| `owner` | `metel-frontend` |
| `specified by` | `#parsing` |
| `implements` | _Generated at publish._ |
| `verified by` | _Generated at publish._ |
| `last_reviewed` | 46f1f6a74b6a2dec071dd6511c82bd1bc668fd03 |
| `related` | ADR-0015, ADR-0018 |

##### Requirement {#arch.parsing.requirement-6}

String interpolation is lowered while parsing: each hole becomes a `to_string` method call and the segments are joined with `BinOp::Add` in a balanced tree, so downstream passes see no interpolation node and no deeply left-nested chain.

| Field | Value |
|---|---|
| `status` | `implemented` |
| `owner` | `metel-frontend` |
| `specified by` | `#parsing` |
| `implements` | _Generated at publish._ |
| `verified by` | _Generated at publish._ |
| `last_reviewed` | de72649a95a5c947ac985069b692008b76a82f7e |
| `related` | ADR-0033 |

</details>

## Known limitations

<!-- records:limitations -->
