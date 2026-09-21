# Interpreter Architecture

## Pipeline

Each stage is a separate Rust module. Module loading through elaboration are owned by
`metel-frontend`; `pipeline.rs` in `metel-interpreter` orchestrates those stages and
then invokes the evaluator. No stage is skipped, though Move Check only runs when
`--move-check` is passed — see `pipeline.rs::run_file`.

```
.mln root source file
       │
       ▼
  ┌───────────────┐
  │ Module Loader │  root file → ModuleGraph (topological order); invokes parser per file
  └───────────────┘
       │  module_loader::ModuleGraph
       ▼
  ┌───────────────┐
  │ Name Resolver │  per-module import scopes, pub_surface, re-exports; assigns SymbolIds;
  │               │  internally calls reference_resolver::collect_references to build a
  │               │  ReferenceTable, carried in ResolvedNames for later stages to consume
  └───────────────┘
       │  name_resolver::ResolvedNames  (carries symbols: HashMap<(module, name) → SymbolId>)
       ▼
  ┌─────────────────┐
  │ Path Normalizer │  rewrites qualified Expr::Path nodes to Expr::ResolvedPath
  └─────────────────┘
       │  path_normalizer::NormalizedModuleGraph
       ▼
  ┌────────────┐
  │ Coherence  │  aspect-impl orphan rule (T0014) and overlap detection (T0015); validation
  │            │  only — resolves type/aspect names to their declaring module, nothing more
  └────────────┘
       │  path_normalizer::NormalizedModuleGraph (unchanged; validation gate only)
       ▼
  ┌──────────────┐
  │ Type Checker │  per-module HM inference + construction (errors reported here)
  │              │  also populates TypedImplBlock::aspect_id via names.symbols
  └──────────────┘
       │  typed_ast::TypedModuleGraph
       ▼
  ┌─────────────┐
  │ Move Check  │  optional (--move-check flag): rejects use-after-move (RFC-0071);
  │ (optional)  │  validation only — off by default
  └─────────────┘
       │  typed_ast::TypedModuleGraph (unchanged; validation gate only)
       ▼
  ┌─────────────┐
  │  Elaborator │  resolves MethodDispatch per call site; wraps graph in ElaboratedModuleGraph
  └─────────────┘
       │  elaborator::ElaboratedModuleGraph
       ▼
  ┌─────────────┐
  │  Evaluator  │  tree-walks ElaboratedModuleGraph → program output
  └─────────────┘
```

For the current state of this spec — which requirements are implemented, partial or
planned, whether each has verifying evidence, and which limitations are still open —
see [Architecture Health](../status/architecture-health.md); every limitation and gap is listed on
[Limitations and Gaps](../status/limitations-and-gaps.md).

---

## Error Design

All errors use a unified `MetelError` type:

```rust
enum MetelError {
    ParseError   { code: ErrorCode, message: String, start: usize, end: usize, filename: String },
    TypeError    { code: ErrorCode, message: String, start: usize, end: usize, filename: String },
    RuntimePanic { message: String, start: usize, end: usize, filename: String },
    Internal     { message: String },
}
```

Type error codes: E0001–E0008. Runtime panics (`.yolo()` on `nope`, out-of-bounds, division by zero) terminate with a non-zero exit code.

---
