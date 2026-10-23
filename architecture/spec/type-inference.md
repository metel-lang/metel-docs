# Type Inference {#type-inference}

The largest single area in the codebase (~12,700 lines): a reusable Hindley-Milner engine (`pipeline::type_checking::type_engine`, 5,688 lines — type variables, substitution, unification, type schemes) driven by an AST-walking inference pass (`pipeline::type_checking::inference`, ~6,973 lines across `type_checking/inference/mod.rs` and `type_checking/inference/{declarations,expressions,lowering,narrowing,patterns}.rs`). The engine/pass boundary is real, not incidental: `type_engine` is `pub mod` (usable by `move_check` and `type_checking::construction` too, both of which import from it directly), while `type_checking::inference` is a private submodule (`mod inference;` in `type_checking/mod.rs`) — only the driving pass is type_checking-internal, not the machinery it's built on. Owning crate: `metel-frontend`.

The pass that consumes this section's output to build the typed IR (`type_checking::construction`) is a separate section — see [Type Construction](type-construction.md).

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

Type inference is Hindley-Milner with let-polymorphism: `instantiate` gives each use of a generalized binding fresh type variables, so one binding can be used at different types without the uses interfering.

| Field | Value |
|---|---|
| `status` | `implemented` |
| `owner` | `metel-frontend` |
| `specified by` | `#type-inference` |
| `implements` | _Generated at publish._ |
| `verified by` | _Generated at publish._ |
| `last_reviewed` | 6469705aaeb2aefd7c60ead845b69e7b6c8dcab4 |
| `related` | `metel-frontend/docs/typechecker.md` |

##### Requirement {#arch.type-inference.requirement-2}

`TypeDefinitionRegistry` namespaces struct and enum definitions per declaring module, so same-named types in two modules keep distinct field and variant sets, including across `merge_from`. Block-local type ids are disjoint from name-resolver `SymbolId`s.

| Field | Value |
|---|---|
| `status` | `implemented` |
| `owner` | `metel-frontend` |
| `specified by` | `#type-inference` |
| `implements` | _Generated at publish._ |
| `verified by` | _Generated at publish._ |
| `last_reviewed` | d05bbfd47ae51437f565e0142a58f8e8a950d114 |
| `related` | ADR-0025 (unified `TypeDefinitionRegistry`), ADR-0041 |

##### Requirement {#arch.type-inference.requirement-3}

`?`'s error-type compatibility is decided in inference, not construction: `infer_propagate_error` calls `ctx.has_from_impl(target, source)` when the error types differ and rejects a missing `From` impl as `T0007`.

| Field | Value |
|---|---|
| `status` | `implemented` |
| `owner` | `metel-frontend` |
| `specified by` | `#type-inference` |
| `implements` | _Generated at publish._ |
| `verified by` | _Generated at publish._ |
| `last_reviewed` | c6932074a86151f5faa1d265d6a761d574ded021 |
| `related` | ADR-0030 (`?` desugared in `path_normalizer` pre-pass), `#13` (full coercion for arbitrary type pairs) |

##### Requirement {#arch.type-inference.requirement-4}

Inference and construction are separate passes: inference solves constraints and hands construction a substitution, frozen resolution facts and schemes; construction rebuilds typed IR from them and never runs the constraint solver, only best-effort matching when re-typing a generic body at a call.

| Field | Value |
|---|---|
| `status` | `implemented` |
| `owner` | `metel-frontend` |
| `specified by` | `#type-inference` |
| `implements` | _Generated at publish._ |
| `verified by` | _Generated at publish._ |
| `last_reviewed` | 41b0f74be0c6e648506cce4821b4d76b2f41e6f8 |
| `related` | ADR-0002, `arch.type-construction.requirement-1` |

##### Requirement {#arch.type-inference.requirement-5}

Let-bound polymorphic closures are represented in the polymorphic scheme environment rather than retained as a monomorphic fallback binding. Call sites instantiate the scheme; preserving an ordinary monomorphic environment entry would silently bypass that instantiation path.

| Field | Value |
|---|---|
| `status` | `implemented` |
| `owner` | `metel-frontend` |
| `specified by` | `#type-inference` |
| `implements` | _Generated at publish._ |
| `verified by` | _Generated at publish._ |
| `last_reviewed` | 6469705aaeb2aefd7c60ead845b69e7b6c8dcab4 |
| `related` | ADR-0011, ADR-0010 |

##### Requirement {#arch.type-inference.requirement-6}

`unify` performs structural unification over `InferType` with an occurs check: binding a variable to a type that contains it (`?t0 = ?t0[]`, `?t0 = (?t0) -> i64`) is rejected as an infinite type rather than looping or being silently accepted.

| Field | Value |
|---|---|
| `status` | `implemented` |
| `owner` | `metel-frontend` |
| `specified by` | `#type-inference` |
| `implements` | _Generated at publish._ |
| `verified by` | _Generated at publish._ |
| `last_reviewed` | b6da47e5a683a1327336beb135cc2febb45235fd |
| `related` | `metel-frontend/docs/typechecker.md` |

##### Requirement {#arch.type-inference.requirement-7}

`generalize` quantifies a type over every free type variable that does not also appear free in the surrounding environment, so a variable still being solved elsewhere is never wrongly captured into a scheme.

| Field | Value |
|---|---|
| `status` | `implemented` |
| `owner` | `metel-frontend` |
| `specified by` | `#type-inference` |
| `implements` | _Generated at publish._ |
| `verified by` | _Generated at publish._ |
| `last_reviewed` | 6469705aaeb2aefd7c60ead845b69e7b6c8dcab4 |
| `related` | `metel-frontend/docs/typechecker.md` |

##### Requirement {#arch.type-inference.requirement-8}

Array literals retain their intrinsic fixed length during inference, and
structural aspect-bound lookup may satisfy that sized type through the existing
one-way `[T; N]` → `[T]` coercion without changing the expression's type identity.

| Field | Value |
|---|---|
| `status` | `implemented` |
| `owner` | `metel-frontend` |
| `specified by` | `#type-inference` |
| `implements` | _Generated at publish._ |
| `verified by` | _Generated at publish._ |
| `last_reviewed` | 8ed18533e08f605e0df6c188f1d30797fb72171f |
| `related` | RFC-0177; `spec.declarations.structural-aspect-bounds.legality-2` |

</details>

## Known limitations

<!-- records:limitations -->
