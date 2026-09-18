# Type Inference {#type-inference}

The largest single area in the codebase (~12,500 lines): a reusable Hindley-Milner engine (`typeinference/`, 5,582 lines — type variables, substitution, unification, type schemes) driven by an AST-walking inference pass (`typechecker::inference`, ~6,900 lines across `typechecker/inference.rs` and `typechecker/inference/{declarations,expressions,lowering,narrowing,patterns}.rs`). The engine/pass boundary is real, not incidental: `typeinference` is `pub mod` at the crate root (usable by `move_check` and `typechecker::construction` too, both of which import from it directly), while `typechecker::inference` is a private submodule (`mod inference;` in `typechecker/mod.rs`) — only the driving pass is typechecker-internal, not the machinery it's built on. Owning crate: `metel-frontend`.

The pass that consumes this section's output to build the typed IR (`typechecker::construction`) is a separate section — see `#type-construction`.

## Model

Inference describes programs in terms of variables, constraints, and schemes, then
solves those constraints into types. Let-polymorphism is central: generalization records
which variables are abstract, and each use receives fresh variables rather than sharing
one accidental concrete choice ([core inference](#arch.type-inference.requirement-1)).
The registry supplies the nominal facts that structural unification cannot infer on its
own ([type definitions](#arch.type-inference.requirement-2)).

This pass owns semantic decisions that require unsolved information, including `?`
coercion and opaque-return validation. Construction consumes the result; it does not
silently infer it again ([pass boundary](#arch.type-inference.requirement-4)). A
let-polymorphic closure remains in the scheme environment precisely so calls continue
to instantiate it ([polymorphic closures](#arch.type-inference.requirement-5)).

<details>
<summary>Verifiable architecture claims</summary>

##### Requirement {#arch.type-inference.requirement-1}

Type inference is Hindley-Milner with let-polymorphism. `unify` performs structural unification over `InferType` with an occurs check (rejecting an infinite type rather than looping or silently accepting one). `generalize` quantifies a type over every free type variable that does not also appear free in the surrounding environment (so a variable still being solved elsewhere is never wrongly captured); `instantiate` gives each use of a generalized (`let`-polymorphic) binding fresh type variables.

| Field | Value |
|---|---|
| `status` | `implemented` |
| `owner` | `metel-frontend` |
| `specified by` | `#type-inference` |
| `implements` | `metel-frontend/src/typeinference/mod.rs` (`InferType`, `TypeVar`, `Substitution`, `unify`, `generalize`, `instantiate`, `Constraint`, `solve_constraints`) |
| `verified by` | general correctness is a precondition of the full integration suite (1,183 `.mtl` fixtures, `metel-interpreter/tests/integration/sources/`) rather than a dedicated unify/occurs-check unit suite — only 4 unit tests exist directly in `typeinference/mod.rs` itself (see requirement-2, which they actually cover) |
| `related` | `metel-frontend/docs/typechecker.md` |

##### Requirement {#arch.type-inference.requirement-2}

`TypeDefinitionRegistry` keeps struct/enum definitions namespaced per declaring module: two modules may declare same-named structs or enums without their field or variant sets colliding, and a `merge_from` combination of registries does not collapse same-named-but-distinct declarations into one. Block-local type ids are a disjoint space from name-resolver `SymbolId`s.

| Field | Value |
|---|---|
| `status` | `implemented` |
| `owner` | `metel-frontend` |
| `specified by` | `#type-inference` |
| `implements` | `metel-frontend/src/typeinference/mod.rs` (`TypeDefinitionRegistry`, `FieldEntry`, `VariantInfo`, `EnumInfo`) |
| `verified by` | `metel-frontend/src/typeinference/mod.rs::same_named_structs_in_two_modules_keep_distinct_field_sets`, `::merge_from_does_not_collapse_same_named_structs`, `::block_local_type_id_is_disjoint_from_name_resolver_ids`, `::same_named_enums_in_two_modules_keep_distinct_variant_sets` |
| `related` | ADR-0025 (unified `TypeDefinitionRegistry`), ADR-0041 |

##### Requirement {#arch.type-inference.requirement-3}

`?`'s error-type compatibility is checked during inference, not construction — `infer_expr`'s `?`-handling solves the inner and target error types, and if they differ, calls `ctx.has_from_impl(target, source)`; a missing `impl From<source> for target` is rejected as `T0007`. (`evaluator.md`'s own "Known Limitations" describes this as happening "during construction" — checked directly against current source for this record, and that's not where it happens; `path_normalizer` desugars `?` into a `PropagateError` node, but the `From`-impl lookup itself runs in `typechecker::inference`, not `typechecker::construction`.)

| Field | Value |
|---|---|
| `status` | `implemented` |
| `owner` | `metel-frontend` |
| `specified by` | `#type-inference` |
| `implements` | `metel-frontend/src/typechecker/inference.rs` (the `?`-expression inference arm); `metel-frontend/src/typeinference/mod.rs` (`has_from_impl`) |
| `verified by` | integration fixture `metel-interpreter/tests/integration/sources/typechecking/error_handling/stage6_neg_06_error_propagation_mismatched_types`; no dedicated unit test found naming this check directly |
| `related` | ADR-0030 (`?` desugared in `path_normalizer` pre-pass), `#13` (full coercion for arbitrary type pairs, still open) |

##### Requirement {#arch.type-inference.requirement-4}

Typechecking keeps inference and construction as separate passes. Inference solves constraints and produces substitutions and schemes; construction rebuilds typed IR from those solved facts and does not run unification, occurs checking, or fresh-variable allocation as a second inference engine.

| Field | Value |
|---|---|
| `status` | `implemented` |
| `owner` | `metel-frontend` |
| `specified by` | `#type-inference` |
| `implements` | `metel-frontend/src/typechecker/mod.rs` (module check orchestration); `metel-frontend/src/typechecker/inference.rs`; `metel-frontend/src/typechecker/construction.rs` |
| `verified by` | full integration-suite coverage of checked programs; no dedicated unit test asserting the pass boundary was found |
| `related` | ADR-0002, `arch.type-construction.requirement-1` |

##### Requirement {#arch.type-inference.requirement-5}

Let-bound polymorphic closures are represented in the polymorphic scheme environment rather than retained as a monomorphic fallback binding. Call sites instantiate the scheme; preserving an ordinary monomorphic environment entry would silently bypass that instantiation path.

| Field | Value |
|---|---|
| `status` | `implemented` |
| `owner` | `metel-frontend` |
| `specified by` | `#type-inference` |
| `implements` | `metel-frontend/src/typechecker/inference.rs` (`mono_env`, `poly_env`); `metel-frontend/src/typechecker/mod.rs` (`build_module_scheme_env`); `metel-frontend/src/typechecker/construction/declarations.rs` |
| `verified by` | general integration-suite coverage of generic let-bound closures; no dedicated regression test naming the environment-absence invariant was found |
| `related` | ADR-0011, ADR-0010 |

</details>

## Known limitations

`LIMIT-*` records are the authoritative inventory of known boundaries for this
section. They carry the impact, owner, disposition, and review point; the
Atlas limitations view projects the same records rather than duplicating them.

### Active records

- [`LIMIT-TYPE-INFERENCE-001`](../limitations/limit-type-inference-001.md) — `?` error coercion requires an explicit `From` impl; only `Int`/`Float` are built in. (Filed as `LIMIT-TYPE-CONSTRUCTION-003` originally, before checking which pass actually performs the check — renamed during `#1158`'s triage.)

### Resolved records

No resolved `LIMIT-*` records are currently recorded for this section.
