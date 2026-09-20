# Type Inference {#type-inference}

The largest single area in the codebase (~12,500 lines): a reusable Hindley-Milner engine (`typeinference/`, 5,582 lines — type variables, substitution, unification, type schemes) driven by an AST-walking inference pass (`typechecker::inference`, ~6,900 lines across `typechecker/inference.rs` and `typechecker/inference/{declarations,expressions,lowering,narrowing,patterns}.rs`). The engine/pass boundary is real, not incidental: `typeinference` is `pub mod` at the crate root (usable by `move_check` and `typechecker::construction` too, both of which import from it directly), while `typechecker::inference` is a private submodule (`mod inference;` in `typechecker/mod.rs`) — only the driving pass is typechecker-internal, not the machinery it's built on. Owning crate: `metel-frontend`.

The pass that consumes this section's output to build the typed IR (`typechecker::construction`) is a separate section — see `#type-construction`.

## Model

Inference describes programs in terms of variables, constraints, and schemes, then
solves those constraints into types. Let-polymorphism is central: generalization records
which variables are abstract, and each use receives fresh variables rather than sharing
one accidental concrete choice ([instantiation](#arch.type-inference.requirement-1),
[generalization](#arch.type-inference.requirement-7)). Unification rejects infinite types
([occurs check](#arch.type-inference.requirement-6)).
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

Type inference is Hindley-Milner with let-polymorphism: `instantiate` gives each use of a generalized (`let`-polymorphic) binding fresh type variables, so the same binding can be used at different types without the uses interfering. Generalization (`arch.type-inference.requirement-7`) and unification's occurs check (`arch.type-inference.requirement-6`) are separate claims.

| Field | Value |
|---|---|
| `status` | `implemented` |
| `owner` | `metel-frontend` |
| `specified by` | `#type-inference` |
| `implements` | [`metel-frontend/src/typeinference/mod.rs::instantiate`](https://github.com/metel-lang/metel-core/blob/7de56e3de9a7841d926b5c185ff95b6c7bf03b22/metel-frontend/src/typeinference/mod.rs#L1730) |
| `verified by` | [`metel-interpreter/tests/integration/sources/typechecking/functions/06_let_polymorphism.toml`](https://github.com/metel-lang/metel-core/blob/7de56e3de9a7841d926b5c185ff95b6c7bf03b22/metel-interpreter/tests/integration/sources/typechecking/functions/06_let_polymorphism.toml#L1); [`metel-interpreter/tests/unit/typeinference_tests.rs::test_instantiate_twice_gives_different_vars`](https://github.com/metel-lang/metel-core/blob/7de56e3de9a7841d926b5c185ff95b6c7bf03b22/metel-interpreter/tests/unit/typeinference_tests.rs#L751) |
| `last_reviewed` | 22f1104b6b7e8cc50978fd429537ecfd4267c336 |
| `related` | `metel-frontend/docs/typechecker.md` |

##### Requirement {#arch.type-inference.requirement-2}

`TypeDefinitionRegistry` keeps struct/enum definitions namespaced per declaring module: two modules may declare same-named structs or enums without their field or variant sets colliding, and a `merge_from` combination of registries does not collapse same-named-but-distinct declarations into one. Block-local type ids are a disjoint space from name-resolver `SymbolId`s.

| Field | Value |
|---|---|
| `status` | `implemented` |
| `owner` | `metel-frontend` |
| `specified by` | `#type-inference` |
| `implements` | [`metel-frontend/src/typeinference/mod.rs::merge_from`](https://github.com/metel-lang/metel-core/blob/7de56e3de9a7841d926b5c185ff95b6c7bf03b22/metel-frontend/src/typeinference/mod.rs#L3977) |
| `verified by` | [`metel-frontend/src/typeinference/mod.rs::block_local_type_id_is_disjoint_from_name_resolver_ids`](https://github.com/metel-lang/metel-core/blob/7de56e3de9a7841d926b5c185ff95b6c7bf03b22/metel-frontend/src/typeinference/mod.rs#L5521); [`metel-frontend/src/typeinference/mod.rs::merge_from_does_not_collapse_same_named_structs`](https://github.com/metel-lang/metel-core/blob/7de56e3de9a7841d926b5c185ff95b6c7bf03b22/metel-frontend/src/typeinference/mod.rs#L5486); [`metel-frontend/src/typeinference/mod.rs::same_named_structs_in_two_modules_keep_distinct_field_sets`](https://github.com/metel-lang/metel-core/blob/7de56e3de9a7841d926b5c185ff95b6c7bf03b22/metel-frontend/src/typeinference/mod.rs#L5455) |
| `last_reviewed` | 22f1104b6b7e8cc50978fd429537ecfd4267c336 |
| `related` | ADR-0025 (unified `TypeDefinitionRegistry`), ADR-0041 |

##### Requirement {#arch.type-inference.requirement-3}

`?`'s error-type compatibility is decided during inference, not construction: `infer_propagate_error` solves the inner and target error types and, if they differ, calls `ctx.has_from_impl(target, source)`; a missing `impl From<source> for target` is rejected as `T0007`. Construction never looks up `From` impls.

| Field | Value |
|---|---|
| `status` | `implemented` |
| `owner` | `metel-frontend` |
| `specified by` | `#type-inference` |
| `implements` | [`metel-frontend/src/typechecker/inference.rs::infer_propagate_error`](https://github.com/metel-lang/metel-core/blob/7de56e3de9a7841d926b5c185ff95b6c7bf03b22/metel-frontend/src/typechecker/inference.rs#L1477) |
| `verified by` | [`metel-frontend/src/typechecker/mod.rs::from_impl_lookup_runs_in_inference_not_construction`](https://github.com/metel-lang/metel-core/blob/7de56e3de9a7841d926b5c185ff95b6c7bf03b22/metel-frontend/src/typechecker/mod.rs#L1501); [`metel-interpreter/tests/integration/sources/typechecking/error_handling/stage6_neg_06_error_propagation_mismatched_types.toml`](https://github.com/metel-lang/metel-core/blob/7de56e3de9a7841d926b5c185ff95b6c7bf03b22/metel-interpreter/tests/integration/sources/typechecking/error_handling/stage6_neg_06_error_propagation_mismatched_types.toml#L1) |
| `last_reviewed` | 8717cc6088e4dcf55f6f5580e60ad936d9bf69cf |
| `related` | ADR-0030 (`?` desugared in `path_normalizer` pre-pass), `#13` (full coercion for arbitrary type pairs) |

##### Requirement {#arch.type-inference.requirement-4}

Typechecking keeps inference and construction as separate passes. Inference solves constraints and hands construction a substitution, frozen resolution facts, and the schemes; construction rebuilds typed IR from those and never runs the constraint solver (`InferContext`, `solve`). Its unification is limited to best-effort matching when re-typing a generic body at call time (`construct_generic_body`), and it allocates fresh type variables only from the generator inference hands off, to instantiate a callee's scheme at a call site.

| Field | Value |
|---|---|
| `status` | `implemented` |
| `owner` | `metel-frontend` |
| `specified by` | `#type-inference` |
| `implements` | [`metel-frontend/src/typechecker/construction.rs::construct_program`](https://github.com/metel-lang/metel-core/blob/7de56e3de9a7841d926b5c185ff95b6c7bf03b22/metel-frontend/src/typechecker/construction.rs#L1061) |
| `verified by` | [`metel-frontend/src/typechecker/mod.rs::construction_never_runs_the_constraint_solver`](https://github.com/metel-lang/metel-core/blob/7de56e3de9a7841d926b5c185ff95b6c7bf03b22/metel-frontend/src/typechecker/mod.rs#L1512); [`metel-interpreter/tests/integration/sources/typechecking/functions/stage7_01_return_type_propagation.toml`](https://github.com/metel-lang/metel-core/blob/7de56e3de9a7841d926b5c185ff95b6c7bf03b22/metel-interpreter/tests/integration/sources/typechecking/functions/stage7_01_return_type_propagation.toml#L1) |
| `last_reviewed` | 22f1104b6b7e8cc50978fd429537ecfd4267c336 |
| `related` | ADR-0002, `arch.type-construction.requirement-1` |

##### Requirement {#arch.type-inference.requirement-5}

Let-bound polymorphic closures are represented in the polymorphic scheme environment rather than retained as a monomorphic fallback binding. Call sites instantiate the scheme; preserving an ordinary monomorphic environment entry would silently bypass that instantiation path.

| Field | Value |
|---|---|
| `status` | `implemented` |
| `owner` | `metel-frontend` |
| `specified by` | `#type-inference` |
| `implements` | [`metel-frontend/src/typechecker/inference/declarations.rs::infer_decl`](https://github.com/metel-lang/metel-core/blob/7de56e3de9a7841d926b5c185ff95b6c7bf03b22/metel-frontend/src/typechecker/inference/declarations.rs#L19) |
| `verified by` | [`metel-interpreter/tests/integration/sources/evaluator/generics/52_let_polymorphism.toml`](https://github.com/metel-lang/metel-core/blob/7de56e3de9a7841d926b5c185ff95b6c7bf03b22/metel-interpreter/tests/integration/sources/evaluator/generics/52_let_polymorphism.toml#L1); [`metel-interpreter/tests/integration/sources/typechecking/aspects/stage21_12_aspect_impl_generic_constraint_in_where_clause.toml`](https://github.com/metel-lang/metel-core/blob/7de56e3de9a7841d926b5c185ff95b6c7bf03b22/metel-interpreter/tests/integration/sources/typechecking/aspects/stage21_12_aspect_impl_generic_constraint_in_where_clause.toml#L1) |
| `last_reviewed` | 22f1104b6b7e8cc50978fd429537ecfd4267c336 |
| `related` | ADR-0011, ADR-0010 |

##### Requirement {#arch.type-inference.requirement-6}

`unify` performs structural unification over `InferType` with an occurs check: binding a variable to a type that contains it (`?t0 = ?t0[]`, `?t0 = (?t0) -> i64`) is rejected as an infinite type rather than looping or being silently accepted.

| Field | Value |
|---|---|
| `status` | `implemented` |
| `owner` | `metel-frontend` |
| `specified by` | `#type-inference` |
| `implements` | [`metel-frontend/src/typeinference/mod.rs::unify`](https://github.com/metel-lang/metel-core/blob/7de56e3de9a7841d926b5c185ff95b6c7bf03b22/metel-frontend/src/typeinference/mod.rs#L831) |
| `verified by` | [`metel-interpreter/tests/unit/typeinference_tests.rs::test_occurs_check_array`](https://github.com/metel-lang/metel-core/blob/7de56e3de9a7841d926b5c185ff95b6c7bf03b22/metel-interpreter/tests/unit/typeinference_tests.rs#L481); [`metel-interpreter/tests/unit/typeinference_tests.rs::test_occurs_check_function`](https://github.com/metel-lang/metel-core/blob/7de56e3de9a7841d926b5c185ff95b6c7bf03b22/metel-interpreter/tests/unit/typeinference_tests.rs#L490) |
| `last_reviewed` | 22f1104b6b7e8cc50978fd429537ecfd4267c336 |
| `related` | `metel-frontend/docs/typechecker.md` |

##### Requirement {#arch.type-inference.requirement-7}

`generalize` quantifies a type over every free type variable that does not also appear free in the surrounding environment, so a variable still being solved elsewhere is never wrongly captured into a scheme.

| Field | Value |
|---|---|
| `status` | `implemented` |
| `owner` | `metel-frontend` |
| `specified by` | `#type-inference` |
| `implements` | [`metel-frontend/src/typeinference/mod.rs::generalize`](https://github.com/metel-lang/metel-core/blob/7de56e3de9a7841d926b5c185ff95b6c7bf03b22/metel-frontend/src/typeinference/mod.rs#L1693) |
| `verified by` | [`metel-interpreter/tests/unit/typeinference_tests.rs::test_generalize_env_blocks_capture`](https://github.com/metel-lang/metel-core/blob/7de56e3de9a7841d926b5c185ff95b6c7bf03b22/metel-interpreter/tests/unit/typeinference_tests.rs#L685); [`metel-interpreter/tests/unit/typeinference_tests.rs::test_generalize_partial_capture`](https://github.com/metel-lang/metel-core/blob/7de56e3de9a7841d926b5c185ff95b6c7bf03b22/metel-interpreter/tests/unit/typeinference_tests.rs#L699) |
| `last_reviewed` | 22f1104b6b7e8cc50978fd429537ecfd4267c336 |
| `related` | `metel-frontend/docs/typechecker.md` |

</details>

## Known limitations

`LIMIT-*` records are the authoritative inventory of known boundaries for this
section. They carry the impact, owner, disposition, and review point; the
Atlas limitations view projects the same records rather than duplicating them.

### Active records

- [`LIMIT-TYPE-INFERENCE-001`](../limitations/limit-type-inference-001.md) — `?` error coercion requires an explicit `From` impl; only `Int`/`Float` are built in.

### Resolved records

No resolved `LIMIT-*` records are currently recorded for this section.
