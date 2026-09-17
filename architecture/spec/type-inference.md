# Type Inference {#type-inference}

The largest single area in the codebase (~12,500 lines): a reusable Hindley-Milner engine (`typeinference/`, 5,582 lines — type variables, substitution, unification, type schemes) driven by an AST-walking inference pass (`typechecker::inference`, ~6,900 lines across `typechecker/inference.rs` and `typechecker/inference/{declarations,expressions,lowering,narrowing,patterns}.rs`). The engine/pass boundary is real, not incidental: `typeinference` is `pub mod` at the crate root (usable by `move_check` and `typechecker::construction` too, both of which import from it directly), while `typechecker::inference` is a private submodule (`mod inference;` in `typechecker/mod.rs`) — only the driving pass is typechecker-internal, not the machinery it's built on. Owning crate: `metel-frontend`.

The pass that consumes this section's output to build the typed IR (`typechecker::construction`) is a separate section — see `#type-construction`.

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
| `related` | ADR-0041 |

## Known limitations

Not audited this session: the memory that `ctx.solve()` (the recursive substitution/constraint-solving walk) is stack-depth-sensitive — a prior real stack-overflow incident whose fix addressed a symptom, not `solve_constraints`'s recursive structure itself — was not re-verified against current source here. If it's still true, it belongs in `#1161`'s extraction as a `LIMIT-*` record (a known, accepted boundary — not something this section can respond to as an `arch-*` requirement, since it's a limitation, not a checkable claim of current correct behavior).
