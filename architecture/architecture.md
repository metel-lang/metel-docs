# Interpreter Architecture

> Rationale for the tree-walk approach: [ADR-0004](decisions/adr-0004-interpreter-architecture.md)
> (ADR-0051, amended 2026-08-23 — this file moved here from `metel-docs-internal`
> alongside the ADRs it links to, so the link above is local again)

## Pipeline

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
  │ Move Check  │  optional (--move-check flag): rejects use-after-move (RFC-0071, #579);
  │ (optional)  │  validation only — off by default in v0.12.0, see the changelog
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

Each stage is a separate Rust module. Module loading through elaboration are owned by
`metel-frontend`; `pipeline.rs` in `metel-interpreter` orchestrates those stages and
then invokes the evaluator. No stage is skipped, though Move Check only runs when
`--move-check` is passed — see `pipeline.rs::run_file`.

---

## Workspace Structure

```
metel-core/                         Cargo workspace
├── metel-frontend/                 reusable language frontend
│   └── src/
│       ├── grammar.pest, parser/, ast/, types/, typed_ast/
│       ├── module_loader.rs, name_resolver.rs, reference_resolver.rs,
│       │   module_paths.rs, path_normalizer.rs, symbols.rs
│       ├── coherence.rs, move_check/, place.rs
│       ├── typeinference/, typechecker/, elaborator/
│       ├── stdlib.rs, native_keys.rs, error/
│       └── lib.rs
└── metel-interpreter/              tree-walking runtime and executable
    └── src/
        ├── main.rs, pipeline.rs, lib.rs
        ├── evaluator/              runtime values, environments, dispatch, patterns,
        │                            builtins, calls, and lvalue evaluation
        └── bin/                    measurement and benchmark tools
```

`metel-frontend` owns every representation and validation step from parsing through
`ElaboratedModuleGraph`: module loading, name/reference resolution, path normalization,
coherence, type checking, move checking, and elaboration. Its public API is deliberately
the language-facing boundary a future compiler and the LSP can consume without depending
on evaluator runtime values or runtime generic reconstruction.

`metel-interpreter` owns pipeline orchestration, the CLI, test harnesses, and
`evaluator::evaluate_graph`. It re-exports the frontend modules for compatibility with
existing consumers, but new frontend-facing code should depend on `metel-frontend`
directly. The boundary follows the data flow: the frontend produces an
`ElaboratedModuleGraph`; evaluation begins only after that point. This preserves
ADR-0004's compiler path and ADR-0010's requirement that a compiler pre-monomorphize
rather than reuse the evaluator's runtime reconstruction.

---

## Component Boundaries

| Data | Type | Owning crate | Produced by | Consumed by |
|------|------|--------------|-------------|-------------|
| Module graph | `module_loader::ModuleGraph` | `metel-frontend` | module loader | name resolver / path normalizer |
| Resolved names | `name_resolver::ResolvedNames` | `metel-frontend` | name resolver | path normalizer / typechecker / elaborator |
| Normalized graph | `path_normalizer::NormalizedModuleGraph` | `metel-frontend` | path normalizer | coherence / typechecker |
| Reference table | `reference_resolver::ReferenceTable` | `metel-frontend` | reference resolver (called from name resolver) | typechecker |
| Typed module graph | `typed_ast::TypedModuleGraph` | `metel-frontend` | typechecker (`check_graph`) | move check (optional) / elaborator (`elaborate`) |
| Elaborated module graph | `elaborator::ElaboratedModuleGraph` | `metel-frontend` | elaborator (`elaborate`) | evaluator (`evaluate_graph`) |
| Untyped program (single-file) | `ast::Program` | `metel-frontend` | `load_program` (single-file shim) | typechecker (`check`) |
| Typed program (single-file) | `typed_ast::TypedProgram` | `metel-frontend` | typechecker (`check`) | evaluator (`evaluate`) |
| Errors | `MetelError` | `metel-frontend` | any stage | caller / CLI |

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

## Component Notes

| Component | Notes |
|-----------|-------|
| Module Loader | `src/module_loader.rs` — `load_root` builds the topological `ModuleGraph`; `load_program` parses a single file (shim for single-file test harnesses) |
| Name Resolver | `src/name_resolver.rs` — `resolve` produces per-module `ModuleScope`, `pub_surface`, and re-exports; also assigns a `SymbolId` to every top-level declaration and stores the intern table in `ResolvedNames::symbols` |
| Path Normalizer | `src/path_normalizer.rs` — `normalize` rewrites qualified `Expr::Path` nodes to `Expr::ResolvedPath`; produces `NormalizedModuleGraph` |
| Symbols | `src/symbols.rs` — `SymbolId` newtype; reserved ID constants for builtin types and aspects; `SymbolTable` intern helper |
| Reference Resolver | `src/reference_resolver.rs` — `collect_references` builds the `ReferenceTable` consumed later by the typechecker; invoked from within `name_resolver::resolve`, not a standalone pipeline call |
| Coherence | `src/coherence.rs` — `check(&NormalizedModuleGraph, &ResolvedNames)`; aspect-impl orphan rule (`T0014`) and overlap detection (`T0015`), RFC-0060/#542; validation only, runs after path normalization and before type-checking |
| Move Check | `src/move_check/` — `check_graph(&TypedModuleGraph)`, opt-in via `--move-check`; rejects use-after-move (RFC-0071, #579); shares `src/place.rs`'s addressable lvalue-path representation with the typechecker |
| Elaborator | `src/elaborator/mod.rs` — `elaborate(TypedModuleGraph, &ResolvedNames) -> ElaboratedModuleGraph`; resolves every `MethodDispatch::Dynamic` site to `Inherent` or `Aspect { aspect_id }`; see [ADR-0037](decisions/adr-0037-elaboration-boundary.md) |
| Parser | `src/parser/`, `src/grammar.pest` |
| Type Checker | [typechecker.md](https://github.com/metel-lang/metel-core/blob/main/metel-frontend/docs/typechecker.md) *(metel-core, not this repo)* |
| Evaluator | [evaluator.md](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/docs/evaluator.md) *(metel-core, not this repo)* |
| Testing | [testing.md](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/docs/testing.md) *(metel-core, not this repo)* |
| Design decisions | [`decisions/`](decisions/) |
