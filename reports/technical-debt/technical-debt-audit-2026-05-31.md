# Technical Debt Audit

**Date:** 2026-05-31  
**Scope:** Metel interpreter architecture, typechecker, module pipeline, evaluator, and compiler-readiness  
**Status:** Audit report with one first-pass fix applied

## Executive Summary

Metel has a coherent high-level pipeline: module loading, name resolution, path normalization, typechecking, then evaluation. The main technical debt is not lack of structure; it is that several stage boundaries are still enforced by convention rather than by stronger data models. That is manageable for the current interpreter, but it will become expensive as the compiler backend, richer module semantics, generics, and the memory model land.

The highest immediate correctness risk found in this pass was builtin precedence. `std::core` is specified as a lowest-priority auto-glob, but builtin schemes were inserted in ways that could override local or imported names during inference, construction, and export filtering. That has been fixed in this run.

The highest future-scaling risks are the incomplete public value export model, eager glob conflict detection, the amount of semantic re-derivation in Pass 2, and the evaluator's current `Rc<RefCell<Value>>` environment model. These are not all bugs today, but they are likely blockers for compiler-oriented architecture and for linear/reference semantics.

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
**Affected files:** `docs/public/spec/modules.md`, `metel-interpreter/src/grammar.pest`, `metel-interpreter/src/ast/mod.rs`, `metel-interpreter/src/name_resolver.rs`, `metel-interpreter/src/typechecker/mod.rs`, `metel-interpreter/src/evaluator/mod.rs`

The spec says `pub` is valid on top-level `let` and `mut` bindings. The AST does not carry visibility for `LetDecl` or `MutDecl`, the grammar does not parse `pub let` or `pub mut`, and the public export pipeline is function-scheme oriented.

This matters now because user-facing documentation promises a capability that the implementation cannot accept. It also means module API tests can miss a whole category of public values.

This matters later because compiler-facing module ABI cannot be function-only. Constants, public values, and eventually type-level or memory-model-related declarations need a consistent export representation.

**Recommended action:** Create a focused issue to implement public value exports or update the spec if they are intentionally deferred. If implemented, add grammar support, AST visibility, resolver pub-surface handling, typechecker export schemes for values, evaluator import seeding, and integration tests.

**Safe to fix now:** Needs a dedicated task. The behavior is spec-visible and crosses multiple stages.

### 3. Same-Tier Glob Conflicts Are Reported Too Early

**Severity:** Medium  
**Category:** Module semantics, diagnostic accuracy  
**Affected files:** `metel-interpreter/src/typechecker/mod.rs`, `metel-interpreter/src/name_resolver.rs`

The spec says two user globs exporting the same name are a T0011 conflict only if that name is actually referenced. The current `build_import_schemes` path reports same-tier glob conflicts while building imports, even if the conflicting name is unused.

This matters now because unused imports can reject otherwise valid modules. It also makes diagnostics less precise because the error is tied to a synthetic file-level span rather than the actual use site.

This matters later because scalable module resolution needs to carry ambiguity as structured symbol state. A compiler backend should not receive an environment that has already collapsed all import decisions into a flat `HashMap<String, TypeScheme>`.

**Recommended action:** Replace eager glob conflict rejection with a scoped import binding model that can carry `Single` and `Conflict` states through lookup. Report T0011 only when resolving a referenced ambiguous name.

**Safe to fix now:** Fix soon, but it is larger than a local patch.

### 4. Pass 2 Re-Derives Too Much Semantic Information

**Severity:** Medium  
**Category:** Typechecker architecture, compiler-readiness  
**Affected files:** `metel-interpreter/src/typechecker/inference.rs`, `metel-interpreter/src/typechecker/construction.rs`, `metel-interpreter/src/typed_ast/mod.rs`

The two-pass design is sound in principle: inference emits constraints and construction builds typed AST. In practice, construction still repeats semantic work from inference, including method lookup, enum literal handling, generic struct field remapping, and polymorphic call instantiation.

This matters now because duplicated logic is a source of drift. A fix in inference can be incomplete if the construction mirror is not updated.

This matters later because a compiler backend needs a stable, lowerable representation with resolved symbols and explicit instantiations. Re-walking untyped AST and re-deriving meaning is acceptable for an interpreter but weak as a compiler boundary.

**Recommended action:** Introduce a compiler-facing HIR or enriched typed AST design before native compiler work begins. The representation should carry resolved symbol identity, import source, method/impl target, and generic instantiation data explicitly.

**Safe to fix now:** Defer until compiler/IR planning. Do not redesign this opportunistically inside feature work.

### 5. Evaluator Environment Semantics Are Intentionally Temporary

**Severity:** Medium  
**Category:** Runtime architecture, future memory model  
**Affected files:** `metel-interpreter/src/evaluator/mod.rs`, `metel-interpreter/src/evaluator/call.rs`

The evaluator stores bindings as `Rc<RefCell<Value>>`. This conveniently supports mutation and recursive closure knot-tying, but closure capture semantics currently share mutable state through cloned environments. The evaluator docs correctly describe this as PoC behavior.

This matters now because tests or features that depend on this behavior can lock in semantics that RFC-0006 and the memory/reference model may later reject.

This matters later because linear types, move capture, `@T` read references, `*T` pointers, and region allocation need ownership and aliasing behavior that cannot be represented as unconstrained `Rc<RefCell<Value>>` sharing.

**Recommended action:** Keep evaluator changes small until closure capture and memory model decisions are resolved. When those decisions land, redesign the runtime environment around explicit capture modes and value ownership rather than incidental shared cells.

**Safe to fix now:** No. Defer until memory-model and closure-capture decisions land.

### 6. Type and Value Export Data Are Too Function-Centric

**Severity:** Medium  
**Category:** Module ABI, compiler-readiness  
**Affected files:** `metel-interpreter/src/typechecker/mod.rs`, `metel-interpreter/src/name_resolver.rs`

`GlobalExports` currently stores public schemes. Type-only imports are handled through side checks against `pub_surface`, and value exports rely on function schemes. This split works for the current feature set but does not model a full module interface.

This matters now because it contributed to the std-shadowing export bug: filtering out builtin names also filtered out a user-defined public function named like a builtin.

This matters later because compiler module interfaces should distinguish exported values, types, aspects, impls, and re-exports explicitly. A flat scheme map is too narrow for long-term ABI work.

**Recommended action:** Define a `ModuleInterface` representation with separate exported namespaces for values, types, aspects, impl metadata, and re-export aliases. Migrate `GlobalExports` toward that representation.

**Safe to fix now:** Fix soon as part of module API cleanup, not as a drive-by refactor.

### 7. Import and Path Normalization Still Depend on Name Strings

**Severity:** Medium  
**Category:** Stage boundary, compiler-readiness  
**Affected files:** `metel-interpreter/src/path_normalizer.rs`, `metel-interpreter/src/name_resolver.rs`, `metel-interpreter/src/typechecker/construction.rs`, `metel-interpreter/src/evaluator/mod.rs`

Path normalization rewrites qualified expression paths to resolved local names, and later stages often recover meaning from the final string segment. This is pragmatic, but it leaves symbol identity implicit.

This matters now because aliases, glob imports, re-exports, and std auto-import all need to agree on string-level precedence. Bugs appear when one stage uses source names and another stage uses local aliases.

This matters later because a compiler should lower from stable symbol IDs, not strings. Linear types and richer references will also need precise binding identity for consumption and alias analysis.

**Recommended action:** Add symbol IDs or a resolved-name handle to normalized/typed nodes. Keep source spelling separately for diagnostics.

**Safe to fix now:** Defer until the module interface or HIR work begins.

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

1. **Implement public top-level value exports.** Add grammar and AST visibility for `pub let` / `pub mut`, export their schemes, seed evaluator imports, and add module semantics tests.

2. **Defer same-tier glob conflicts until use site.** Carry ambiguous glob bindings through import resolution and emit T0011 only when the ambiguous name is referenced.

3. **Introduce a structured module interface.** Replace function-only `GlobalExports` with a representation for exported values, types, aspects, impl metadata, and re-exports.

4. **Design a compiler-facing HIR boundary.** Define a typed, lowerable representation with resolved symbol IDs, import sources, method targets, and generic instantiations.

5. **Add symbol identity to resolved paths.** Stop relying on final path segments as semantic identity across normalization, typechecking, and evaluation.

6. **Plan evaluator closure-environment redesign with RFC-0006 and RFC-0028.** Avoid stabilizing current `Rc<RefCell<Value>>` capture behavior before closure and memory-model decisions are incorporated.

7. **Audit inference/construction duplication.** Identify cases where Pass 2 mirrors Pass 1 logic and either extract shared helpers or move the information into typed/HIR nodes.

