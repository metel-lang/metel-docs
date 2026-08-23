---
id: adr-0048
title: "Split the Reusable Language Frontend from the Tree-Walking Interpreter"
date: '2026-08-04'
status: accepted
relates: adr-0004, adr-0010
implements: issue #610
---

## Context

The original `metel-interpreter` crate contained both the reusable language pipeline
and the tree-walking runtime. That made the current evaluator convenient to build, but
it would force a future compiler or the dormant LSP to depend on evaluator runtime
values, builtin registration, and runtime generic re-construction merely to parse,
resolve, type-check, or elaborate a program.

ADR-0004 anticipated a future compiler. ADR-0010 also records that a compiler must
pre-monomorphize instead of reusing the evaluator's runtime re-construction strategy.
The crate boundary therefore needs to follow the fully checked program representation,
not an accidental division between individual passes.

## Decision

Create a Cargo workspace with two crates:

- `metel-frontend` owns syntax, ASTs, module loading, name and reference resolution,
  path normalization, coherence, type inference/checking, move checking, elaboration,
  standard-library source embedding, and the shared `MetelError` type.
- `metel-interpreter` owns CLI and pipeline orchestration, integration-test support,
  evaluator runtime values and environments, builtin registration, runtime dispatch,
  and `evaluator::evaluate_graph`.

The frontend's terminal representation is `ElaboratedModuleGraph`. The interpreter
consumes that representation to evaluate a program. The interpreter re-exports the
frontend's public modules for compatibility, but new compiler- or tooling-facing code
depends on `metel-frontend` directly.

Exactly the small typechecker API surface genuinely used by evaluator-side generic
re-construction remains public across the boundary. This is an intentional compatibility
bridge for the tree-walker, not evidence that the evaluator owns frontend semantics.

## Consequences

- A compiler backend and LSP can reuse the complete frontend without pulling in runtime
  evaluation machinery.
- The current interpreter remains the shipped runtime and keeps its existing public
  import surface while downstream users migrate at their own pace.
- Runtime generic re-construction stays confined to the interpreter. A compiler must
  use its own ahead-of-time monomorphization strategy, as ADR-0010 requires.
- Workspace-level test, formatting, and lint commands are the normal project gate;
  member-crate commands remain useful for focused local work.
