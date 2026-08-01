# Technical Debt Audit

**Date:** 2026-05-31  
**Last updated:** 2026-06-01  
**Scope:** Metel interpreter architecture, typechecker, module pipeline, evaluator, and compiler-readiness  
**Status:** Audit report with one first-pass fix applied and follow-up audit findings added

## Executive Summary

Metel has a coherent high-level pipeline: module loading, name resolution, path normalization, typechecking, then evaluation. The main technical debt is not lack of structure; it is that several stage boundaries are still enforced by convention rather than by stronger data models. That is manageable for the current interpreter, but it will become expensive as the compiler backend, richer module semantics, generics, and the memory model land.

The highest immediate correctness risk found in this pass was builtin precedence. `std::core` is specified as a lowest-priority auto-glob, but builtin schemes were inserted in ways that could override local or imported names during inference, construction, and export filtering. That has been fixed in this run.

The 2026-06-01 follow-up audit confirmed two additional implementation bugs:

- Index assignment accepts arbitrary index expressions in the parser and typechecker, but the evaluator only supports literal or identifier indexes in assignment lvalues and fails with an internal error for expressions such as `arr[i + 1] = value`.
- Same-tier glob conflicts are still reported eagerly even when the duplicated name is never referenced, contrary to the spec and ADR-0026.

The highest future-scaling risks are the incomplete public value export model, eager glob conflict detection, the amount of semantic re-derivation in Pass 2, and the evaluator's current `Rc<RefCell<Value>>` environment model. These are not all bugs today, but they are likely blockers for compiler-oriented architecture and for linear/reference semantics. Public docs are also drifting from the implementation: the current public spec still mentions `.mln` source files and `v0.6.4`, while the interpreter and tests use `.mtl` and the crate is `v0.7.0`.

## Findings

### 1. Std Prelude Precedence Could Override User Names

**Severity:** High  
**Category:** Correctness, module semantics, compiler-readiness  
**Affected files:** `metel-interpreter/src/typechecker/mod.rs`, `metel-interpreter/src/typechecker/registry.rs`, `metel-interpreter/src/typeinference/mod.rs`

The spec says `std::core` is auto-imported at the lowest priority tier. Local declarations, explicit imports, and user glob imports must beat std names. The implementation already modeled this in some places, but builtin schemes were still inserted into inference and construction environments in ways that could overwrite user-defined or imported names such as `print`.

This matters now because a valid program can define or import a function with the same name as a builtin and expect the user definition to win. Before the fix, inference, construction, or public export filtering could silently use the builtin scheme instead.

This matters later because compiler symbol resolution must have a single, durable precedence model. If the interpreter and typechecker preserve precedence differently, a compiler backend will inherit subtle ABI and name-resolution bugs.

**Action taken:** Fixed in this run. Builtin schemes are now inserted only when absent, imported schemes are seeded before std schemes in construction, and user-defined public names that collide with prelude names are preserved in module exports.

**Safe to fix now:** Yes.

### 2. Public Top-Level `let` / `mut` Are Specified But Not Implemented

**Severity:** High  
**Category:** Spec mismatch, public API model, module semantics  
**Affected files:** `docs/public/reference/spec/modules.md`, `docs/public/reference/spec/declarations.md`, `docs/public/reference/spec/grammar.md`, `metel-interpreter/src/grammar.pest`, `metel-interpreter/src/ast/mod.rs`, `metel-interpreter/src/name_resolver.rs`, `metel-interpreter/src/typechecker/mod.rs`, `metel-interpreter/src/evaluator/mod.rs`

The spec is internally inconsistent. The modules and grammar sections say `pub` is valid on top-level `let` and `mut` bindings. The declarations section only lists `fun`, `struct`, `enum`, and `aspect`. The implementation follows the narrower model: the AST does not carry visibility for `LetDecl` or `MutDecl`, the grammar does not parse `pub let` or `pub mut`, and the public export pipeline is function-scheme oriented.

The 2026-06-01 follow-up audit verified this with a temporary program: `pub let answer = 42;` fails with P0001 at parse time.

This matters now because user-facing documentation promises a capability that the implementation cannot accept. It also means module API tests can miss a whole category of public values.

This matters later because compiler-facing module ABI cannot be function-only. Constants, public values, and eventually type-level or memory-model-related declarations need a consistent export representation.

**Recommended action:** Create a focused issue to implement public value exports or update the spec if they are intentionally deferred. If implemented, add grammar support, AST visibility, resolver pub-surface handling, typechecker export schemes for values, evaluator import seeding, and integration tests.

**Safe to fix now:** Needs a dedicated task. The behavior is spec-visible and crosses multiple stages.

### 3. Same-Tier Glob Conflicts Are Reported Too Early

**Severity:** Medium  
**Category:** Module semantics, diagnostic accuracy  
**Affected files:** `metel-interpreter/src/typechecker/mod.rs`, `metel-interpreter/src/name_resolver.rs`

The spec and ADR-0026 say two user globs exporting the same name are a T0011 conflict only if that name is actually referenced. The current `build_import_schemes` path reports same-tier glob conflicts while building imports, even if the conflicting name is unused.

The 2026-06-01 follow-up audit verified this with a temporary program: `import a::*; import b::*; fun main() -> Int { return 0; }` still reports T0011 for an unused duplicated `foo`.

This matters now because unused imports can reject otherwise valid modules. It also makes diagnostics less precise because the error is tied to a synthetic file-level span rather than the actual use site.

This matters later because scalable module resolution needs to carry ambiguity as structured symbol state. A compiler backend should not receive an environment that has already collapsed all import decisions into a flat `HashMap<String, TypeScheme>`.

**Recommended action:** Replace eager glob conflict rejection with a scoped import binding model that can carry `Single` and `Conflict` states through lookup. Report T0011 only when resolving a referenced ambiguous name.

**Safe to fix now:** Fix soon, but it is larger than a local patch.

### 4. Index Assignment Re-enters Untyped Lvalue Evaluation

**Severity:** High  
**Category:** Correctness, stage boundary, compiler-readiness  
**Affected files:** `metel-interpreter/src/typechecker/inference.rs`, `metel-interpreter/src/typechecker/construction.rs`, `metel-interpreter/src/typed_ast/mod.rs`, `metel-interpreter/src/evaluator/mod.rs`, `metel-interpreter/src/evaluator/lvalue.rs`

The grammar and typechecker allow assignment to indexed lvalues where the index is an arbitrary expression. Inference checks the object and index expression normally. Construction then stores the original untyped `AssignTarget` inside `TypedExpr::Assign`. The evaluator handles typed assignment by calling `eval_untyped_index` and `eval_untyped_lvalue_value`, which only support literal or identifier index expressions and a small subset of receiver forms.

The 2026-06-01 follow-up audit verified this with a temporary program:

```metel
fun main() {
    var arr: Int[] = [1, 2, 3];
    var i = 0;
    arr[i + 1] = 9;
    assert(arr[1] == 9);
}
```

The program reaches evaluation and fails with `[I0001] internal error: index expression too complex; assign the index to a variable first`.

This matters now because a program accepted by earlier stages fails as an internal runtime error instead of executing or being rejected with a proper diagnostic.

This matters later because assignment targets are exactly where linear types, borrows, moves, and write permissions need precise place semantics. Keeping raw AST assignment targets inside typed AST will be a liability for compiler lowering and ownership/alias analysis.

**Recommended action:** Add a typed lvalue/place representation, for example `TypedAssignTarget` or `Place`, whose index and receiver components are typed expressions. Evaluate typed places in the evaluator and use the same representation later for compiler lowering. Add regression tests for `arr[i + 1] = v`, compound assignment with computed indexes, and chained field/index assignment.

**Safe to fix now:** Yes, if scoped to typed lvalue construction/evaluation and regression tests. It should not require a spec decision because current grammar and typechecker already accept the behavior.

### 5. Pass 2 Re-Derives Too Much Semantic Information

**Severity:** Medium  
**Category:** Typechecker architecture, compiler-readiness  
**Affected files:** `metel-interpreter/src/typechecker/inference.rs`, `metel-interpreter/src/typechecker/construction.rs`, `metel-interpreter/src/typed_ast/mod.rs`

The two-pass design is sound in principle: inference emits constraints and construction builds typed AST. In practice, construction still repeats semantic work from inference, including method lookup, enum literal handling, generic struct field remapping, and polymorphic call instantiation.

This matters now because duplicated logic is a source of drift. A fix in inference can be incomplete if the construction mirror is not updated.

This matters later because a compiler backend needs a stable, lowerable representation with resolved symbols and explicit instantiations. Re-walking untyped AST and re-deriving meaning is acceptable for an interpreter but weak as a compiler boundary.

**Recommended action:** Introduce a compiler-facing HIR or enriched typed AST design before native compiler work begins. The representation should carry resolved symbol identity, import source, method/impl target, and generic instantiation data explicitly.

**Safe to fix now:** Defer until compiler/IR planning. Do not redesign this opportunistically inside feature work.

### 6. Closure Capture Semantics Are Now Spec/Architecture Inconsistent

**Severity:** Medium  
**Category:** Runtime architecture, spec consistency, future memory model  
**Affected files:** `docs/public/reference/spec/functions.md`, `metel-interpreter/docs/evaluator.md`, `metel-interpreter/src/evaluator/mod.rs`, `metel-interpreter/src/evaluator/call.rs`

The evaluator stores bindings as `Rc<RefCell<Value>>`. This conveniently supports mutation and recursive closure knot-tying, but closure capture semantics currently share mutable state through cloned environments.

The public spec now says captured `mut` variables are shared and mutations are visible in the outer scope. The evaluator documentation still says this behavior is an unintentional consequence of the PoC design and that RFC-0006 will establish the intended semantics.

This matters now because tests or features that depend on this behavior can lock in semantics that RFC-0006 and the memory/reference model may later reject.

This matters later because linear types, move capture, `@T` read references, `*T` pointers, and region allocation need ownership and aliasing behavior that cannot be represented as unconstrained `Rc<RefCell<Value>>` sharing.

**Recommended action:** Make a spec/ADR decision. If shared captures are now accepted language behavior, update evaluator docs and ADR references to remove the "unintentional" warning and explicitly call out the implications for future linear/reference semantics. If shared captures are not accepted, revert or qualify the public spec text and keep tests from depending on this behavior.

**Safe to fix now:** Documentation can be fixed now after a decision. Runtime redesign should wait for closure-capture and memory-model decisions.

### 7. Type and Value Export Data Are Too Function-Centric

**Severity:** Medium  
**Category:** Module ABI, compiler-readiness  
**Affected files:** `metel-interpreter/src/typechecker/mod.rs`, `metel-interpreter/src/name_resolver.rs`

`GlobalExports` currently stores public schemes. Type-only imports are handled through side checks against `pub_surface`, and value exports rely on function schemes. This split works for the current feature set but does not model a full module interface.

This matters now because it contributed to the std-shadowing export bug: filtering out builtin names also filtered out a user-defined public function named like a builtin.

This matters later because compiler module interfaces should distinguish exported values, types, aspects, impls, and re-exports explicitly. A flat scheme map is too narrow for long-term ABI work.

**Recommended action:** Define a `ModuleInterface` representation with separate exported namespaces for values, types, aspects, impl metadata, and re-export aliases. Migrate `GlobalExports` toward that representation.

**Safe to fix now:** Fix soon as part of module API cleanup, not as a drive-by refactor.

### 8. Import and Path Normalization Still Depend on Name Strings

**Severity:** Medium  
**Category:** Stage boundary, compiler-readiness  
**Affected files:** `metel-interpreter/src/path_normalizer.rs`, `metel-interpreter/src/name_resolver.rs`, `metel-interpreter/src/typechecker/construction.rs`, `metel-interpreter/src/evaluator/mod.rs`

Path normalization rewrites qualified expression paths to resolved local names, and later stages often recover meaning from the final string segment. This is pragmatic, but it leaves symbol identity implicit.

This matters now because aliases, glob imports, re-exports, and std auto-import all need to agree on string-level precedence. Bugs appear when one stage uses source names and another stage uses local aliases.

This matters later because a compiler should lower from stable symbol IDs, not strings. Linear types and richer references will also need precise binding identity for consumption and alias analysis.

**Recommended action:** Add symbol IDs or a resolved-name handle to normalized/typed nodes. Keep source spelling separately for diagnostics.

**Safe to fix now:** Defer until the module interface or HIR work begins.

### 9. Public Spec Version, Extension, and CLI Version Drift

**Severity:** Medium  
**Category:** Spec accuracy, tooling, release hygiene  
**Affected files:** `docs/public/reference/spec.md`, `docs/public/reference/spec/modules.md`, `docs/public/release-notes/changelog.md`, `metel-interpreter/Cargo.toml`, `metel-interpreter/src/main.rs`, `metel-interpreter/src/module_loader.rs`

The public spec frontmatter still says `version: v0.6.4`, while the changelog and crate version are `v0.7.0`. The public spec says source files use the `.mln` extension and the modules section uses `.mln` throughout. The implementation and tests use `.mtl`, and the module loader resolves imports by appending `.mtl`. The CLI also hardcodes `#[command(version = "0.1.0")]` rather than deriving from `Cargo.toml`.

This matters now because the public reference does not describe the actual tool users run.

This matters later because the docs release workflow depends on the public spec being authoritative. Extension/version drift undermines spec discipline and makes future compiler/tooling conventions ambiguous.

**Recommended action:** Decide whether `.mtl` or `.mln` is the canonical source extension. Then update either the public docs or implementation consistently. Also change the CLI version to derive from `CARGO_PKG_VERSION` and keep the public spec frontmatter aligned with the changelog.

**Safe to fix now:** Yes for version derivation and docs alignment after confirming the intended extension.

### 10. `std::core` Public Surface Is Split Across Resolver and Typechecker

**Severity:** Medium  
**Category:** Module architecture, spec consistency  
**Affected files:** `docs/public/reference/spec/modules.md`, `docs/public/reference/spec/runtime.md`, `metel-interpreter/src/name_resolver.rs`, `metel-interpreter/src/typechecker/mod.rs`, `metel-interpreter/src/typechecker/registry.rs`, `metel-interpreter/src/evaluator/builtins.rs`

The spec says `std::core` contains builtin functions, core types, and builtin aspects. The typechecker seeds builtin function schemes into `GlobalExports` for `std::core`, while the name resolver injects only a small virtual public surface for `Perhaps`, `Result`, `Display`, `Iterable`, and `From`. This split currently works for common imports because different stages compensate for each other, but there is no single authoritative representation of the virtual module's public API.

This matters now for re-export and enumeration-like behavior. A facade that attempts to re-export `std::core::*` depends on the resolver's `pub_surface`, which does not include builtin functions.

This matters later because a compiler module interface cannot be assembled from stage-local special cases. The standard prelude should look like a normal module interface to resolution, typechecking, lowering, and documentation generation.

**Recommended action:** Introduce one `StdCoreSurface` or `StdPreludeInterface` provider that exposes builtin values, types, aspects, and methods to resolver, typechecker, evaluator parity tests, and docs generation.

**Safe to fix now:** Fix soon as module-interface cleanup.

## First-Pass Fix Applied

The first patch fixed std prelude shadowing:

- Added `InferContext::bind_poly_if_absent` for lower-priority prelude bindings.
- Changed builtin inference registration to preserve existing imported or local schemes.
- Changed construction `scheme_env` population so imports are present before std builtins and std builtins fill only missing names.
- Preserved user-defined top-level value names in public exports even when their name matches a std builtin.
- Strengthened module semantics tests so a user glob exporting `print` beats the std builtin, and a local `print` beats the std auto-glob.

Verification:

```bash
cargo test --manifest-path metel-interpreter/Cargo.toml
```

Result: all tests pass.

## Suggested Follow-Up Issues

1. **Fix typed assignment places.** Add a typed lvalue/place representation, stop storing raw AST assignment targets inside `TypedExpr::Assign`, and add regression tests for computed index assignment.

2. **Defer same-tier glob conflicts until use site.** Carry ambiguous glob bindings through import resolution and emit T0011 only when the ambiguous name is referenced.

3. **Resolve the public top-level value export decision.** Either remove `pub let` / `pub mut` from the public spec for now or implement grammar, AST visibility, export schemes, evaluator seeding, and tests.

4. **Align public spec metadata and source extension.** Update version/frontmatter, examples, module docs, and either the implementation or docs so `.mtl` / `.mln` has one canonical answer.

5. **Decide closure capture semantics before linear-type work.** Update the public spec, evaluator docs, and ADRs so shared captured mutation is either accepted behavior or explicitly deferred/unstable.

6. **Introduce a structured module interface.** Replace function-only `GlobalExports` with a representation for exported values, types, aspects, impl metadata, standard-library surface, and re-exports.

7. **Design a compiler-facing HIR boundary.** Define a typed, lowerable representation with resolved symbol IDs, import sources, method targets, generic instantiations, and eventually ownership/place metadata.

8. **Add symbol identity to resolved paths.** Stop relying on final path segments as semantic identity across normalization, typechecking, and evaluation.

9. **Audit inference/construction duplication.** Identify cases where Pass 2 mirrors Pass 1 logic and either extract shared helpers or move the information into typed/HIR nodes.
