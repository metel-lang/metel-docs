# Type Construction {#type-construction}

The pass that builds the typed IR from `#type-inference`'s results: `typechecker::construction` (~8,050 lines across `typechecker/construction.rs` and `typechecker/construction/{declarations,expressions,calls,patterns,narrowing}.rs`), `typed_ast/` (748 lines, the typed IR itself), and the typechecker's shared support consumed by construction — `registry.rs`, `projections.rs`, `overload.rs`, `conversions.rs`, `object_safety.rs`, `handoff.rs` (~3,500 lines). ~12,300 lines total. Owning crate: `metel-frontend`. This section consumes `#type-inference`'s output; it does not re-derive it.

## Model

Construction turns solved facts into the typed program consumed by move checking,
elaboration, and evaluation. It processes modules in dependency order and carries
their exported schemes forward ([module handoff](#arch.type-construction.requirement-1)).
Where earlier stages resolved an identity, construction preserves it on typed nodes
instead of replacing it with another name lookup ([identity stamping](#arch.type-construction.requirement-2)).

It is also the last place to enforce rules whose operands must already be concrete:
ascriptions disappear after guiding construction ([ascriptions](#arch.type-construction.requirement-6)),
operator and import diagnostics retain their distinct meanings
([operators](#arch.type-construction.requirement-7), [visibility](#arch.type-construction.requirement-8)),
and defaults, overload selections, and generic shape recovery become explicit typed
facts ([defaults](#arch.type-construction.requirement-9), [overloads](#arch.type-construction.requirement-10),
[generic reconstruction](#arch.type-construction.requirement-12)).

<details>
<summary>Verifiable architecture claims</summary>

##### Requirement {#arch.type-construction.requirement-1}

`check_graph` typechecks a normalized module graph in topological order — dependencies before dependents — running both passes (inference, then construction) per module, and accumulates each module's exported type schemes into a `GlobalExports` structure so a later module can import an earlier module's inferred types without re-inferring them.

| Field | Value |
|---|---|
| `status` | `implemented` |
| `owner` | `metel-frontend` |
| `specified by` | `#type-construction` |
| `implements` | [`metel-frontend/src/typechecker/mod.rs::empty`](https://github.com/metel-lang/metel-core/blob/a66d52c5851de9647d18d858e0829b6a8477a2a2/metel-frontend/src/typechecker/mod.rs#L134) |
| `verified by` | [`metel-interpreter/tests/integration/sources/typechecking/aspects/stage12_01_default_methods.toml`](https://github.com/metel-lang/metel-core/blob/a66d52c5851de9647d18d858e0829b6a8477a2a2/metel-interpreter/tests/integration/sources/typechecking/aspects/stage12_01_default_methods.toml#L1) |
| `related` | ADR-0022 |

##### Requirement {#arch.type-construction.requirement-2}

Construction stamps the typed IR with resolved identities wherever the frontend has already produced one, rather than re-deriving them: a `FrozenIdentity` bundle threads the member table (`#1051`, field-access and enum-variant-literal `FieldId`/`VariantId`, `#1062`) and the span→`BindingId` bridge (`#1052`) through `check_graph_with_report`, so e.g. `TypedExpr::Ident` carries its resolved binding. The move-check and diagnostic-tool entry points pass `None` for this bundle and get every id as `None` — construction degrades gracefully rather than requiring the full identity system for every caller.

| Field | Value |
|---|---|
| `status` | `implemented` |
| `owner` | `metel-frontend` |
| `specified by` | `#type-construction` |
| `implements` | [`metel-frontend/src/typechecker/mod.rs::empty`](https://github.com/metel-lang/metel-core/blob/a66d52c5851de9647d18d858e0829b6a8477a2a2/metel-frontend/src/typechecker/mod.rs#L135) |
| `verified by` | [`metel-frontend/src/typechecker/mod.rs::construct_generic_body_stamps_a_real_local_id`](https://github.com/metel-lang/metel-core/blob/a66d52c5851de9647d18d858e0829b6a8477a2a2/metel-frontend/src/typechecker/mod.rs#L1513) |
| `related` | `arch.resolution.requirement-2`, `arch.resolution.requirement-3`, ADR-0054, `#1051`, `#1052` |

##### Requirement {#arch.type-construction.requirement-3}

Opaque return variables are validated at constraint-composition time, not by inspecting only the final solved substitution. When an opaque-return marker resolves directly to a concrete type, inference reports `T0018` at that constraint; it may remain a type variable while it is threaded through another generic or opaque interface. Construction consumes that solved result and must not reintroduce the concrete identity.

| Field | Value |
|---|---|
| `status` | `implemented` |
| `owner` | `metel-frontend` |
| `specified by` | `#type-construction` |
| `implements` | [`metel-frontend/src/typeinference/mod.rs::fmt`](https://github.com/metel-lang/metel-core/blob/a66d52c5851de9647d18d858e0829b6a8477a2a2/metel-frontend/src/typeinference/mod.rs#L25) |
| `verified by` | [`metel-interpreter/tests/integration/sources/typechecking/types/stage3_04_sized_arrays.toml`](https://github.com/metel-lang/metel-core/blob/a66d52c5851de9647d18d858e0829b6a8477a2a2/metel-interpreter/tests/integration/sources/typechecking/types/stage3_04_sized_arrays.toml#L1) |
| `related` | ADR-0044, RFC-0037 |

##### Requirement {#arch.type-construction.requirement-4}

The typechecker treats `T[]` as `Copy` unconditionally: its copy eligibility is a deliberate `InferType::Array` special case and does not inspect the element type. Other array-aspect eligibility remains conditional on the element and ordinary stdlib impl/bound machinery; this is not a temporary stdlib-lookup gap.

| Field | Value |
|---|---|
| `status` | `implemented` |
| `owner` | `metel-frontend` |
| `specified by` | `#type-construction` |
| `implements` | [`metel-frontend/src/typeinference/mod.rs::infer_type_satisfies_aspect`](https://github.com/metel-lang/metel-core/blob/a66d52c5851de9647d18d858e0829b6a8477a2a2/metel-frontend/src/typeinference/mod.rs#L3148) |
| `verified by` | [`metel-interpreter/tests/integration/sources/typechecking/aspects/stage12_02_override_replaces_default.toml`](https://github.com/metel-lang/metel-core/blob/a66d52c5851de9647d18d858e0829b6a8477a2a2/metel-interpreter/tests/integration/sources/typechecking/aspects/stage12_02_override_replaces_default.toml#L1) |
| `related` | ADR-0046, RFC-0126 |

##### Requirement {#arch.type-construction.requirement-5}

Until destructor invocation exists, a `std::core::Drop` impl may declare only an empty `drop` method body. Construction identifies the standard aspect by declaring module, leaving a user-defined same-named aspect alone, and rejects a non-empty body with `T0001` rather than accepting cleanup code that the evaluator would silently never run.

| Field | Value |
|---|---|
| `status` | `implemented` |
| `owner` | `metel-frontend` |
| `specified by` | `#type-construction` |
| `implements` | [`metel-frontend/src/typechecker/construction/declarations.rs::method_fun_decl`](https://github.com/metel-lang/metel-core/blob/a66d52c5851de9647d18d858e0829b6a8477a2a2/metel-frontend/src/typechecker/construction/declarations.rs#L12) |
| `verified by` | [`metel-interpreter/tests/integration/sources/typechecking/aspects/stage12_02_override_replaces_default.toml`](https://github.com/metel-lang/metel-core/blob/a66d52c5851de9647d18d858e0829b6a8477a2a2/metel-interpreter/tests/integration/sources/typechecking/aspects/stage12_02_override_replaces_default.toml#L1) |
| `related` | ADR-0047, RFC-0071 §9c, `#261` |

##### Requirement {#arch.type-construction.requirement-6}

Type ascriptions constrain inference and construction but are erased from typed IR: construction builds the inner expression using the resolved annotation as context instead of emitting a runtime no-op `TypedExpr::Ascribe` node.

| Field | Value |
|---|---|
| `status` | `implemented` |
| `owner` | `metel-frontend` |
| `specified by` | `#type-construction` |
| `implements` | [`metel-frontend/src/typechecker/inference/expressions.rs::infer_stmt`](https://github.com/metel-lang/metel-core/blob/a66d52c5851de9647d18d858e0829b6a8477a2a2/metel-frontend/src/typechecker/inference/expressions.rs#L17) |
| `verified by` | [`metel-interpreter/tests/integration/sources/typechecking/builtins/stage8_neg_02_ascribe_type_mismatch.toml`](https://github.com/metel-lang/metel-core/blob/a66d52c5851de9647d18d858e0829b6a8477a2a2/metel-interpreter/tests/integration/sources/typechecking/builtins/stage8_neg_02_ascribe_type_mismatch.toml#L1) |
| `related` | ADR-0009 |

##### Requirement {#arch.type-construction.requirement-7}

Operand legality is checked after operand types are resolved: arithmetic and unary negation accept numeric or `Never` operands, while ordering comparisons additionally accept `Str`. The construction pass reports the language's operand-type diagnostic (`T0005`) rather than leaving invalid operator shapes for evaluation.

| Field | Value |
|---|---|
| `status` | `implemented` |
| `owner` | `metel-frontend` |
| `specified by` | `#type-construction` |
| `implements` | [`metel-frontend/src/typechecker/construction.rs::build_concrete_struct_env`](https://github.com/metel-lang/metel-core/blob/a66d52c5851de9647d18d858e0829b6a8477a2a2/metel-frontend/src/typechecker/construction.rs#L39) |
| `verified by` | [`metel-interpreter/tests/integration/sources/typechecking/literals/neg_05_generic_field_literal_add_string.toml`](https://github.com/metel-lang/metel-core/blob/a66d52c5851de9647d18d858e0829b6a8477a2a2/metel-interpreter/tests/integration/sources/typechecking/literals/neg_05_generic_field_literal_add_string.toml#L1) |
| `related` | ADR-0017, `T0005` |

##### Requirement {#arch.type-construction.requirement-8}

Import visibility is diagnosed while building import schemes, where the full module graph and exports are available. Name resolution records import bindings without prematurely collapsing a private-item error into a missing-item error; construction/typechecking then distinguishes `T0009` visibility from `T0003` absence.

| Field | Value |
|---|---|
| `status` | `implemented` |
| `owner` | `metel-frontend` |
| `specified by` | `#type-construction` |
| `implements` | [`metel-frontend/src/name_resolver.rs::canonical_path`](https://github.com/metel-lang/metel-core/blob/a66d52c5851de9647d18d858e0829b6a8477a2a2/metel-frontend/src/name_resolver.rs#L101) |
| `verified by` | [`metel-interpreter/tests/integration/sources/typechecking/aspects/orphan_impl_cross_module_violation/test.toml`](https://github.com/metel-lang/metel-core/blob/a66d52c5851de9647d18d858e0829b6a8477a2a2/metel-interpreter/tests/integration/sources/typechecking/aspects/orphan_impl_cross_module_violation/test.toml#L1) |
| `related` | ADR-0024, `T0003`, `T0009` |

##### Requirement {#arch.type-construction.requirement-9}

Aspect default methods are materialized as typed methods before evaluation. Inference collects inherited defaults for an impl and construction emits a concrete typed body for each applicable default, while negative impls deliberately do not acquire default bodies; runtime dispatch therefore never evaluates untyped default-method syntax.

| Field | Value |
|---|---|
| `status` | `implemented` |
| `owner` | `metel-frontend` |
| `specified by` | `#type-construction` |
| `implements` | [`metel-frontend/src/typechecker/inference/declarations.rs::infer_decl`](https://github.com/metel-lang/metel-core/blob/a66d52c5851de9647d18d858e0829b6a8477a2a2/metel-frontend/src/typechecker/inference/declarations.rs#L18) |
| `verified by` | [`metel-interpreter/tests/integration/sources/typechecking/aspects/stage12_01_default_methods.toml`](https://github.com/metel-lang/metel-core/blob/a66d52c5851de9647d18d858e0829b6a8477a2a2/metel-interpreter/tests/integration/sources/typechecking/aspects/stage12_01_default_methods.toml#L1) |
| `related` | ADR-0034 |

##### Requirement {#arch.type-construction.requirement-10}

Free-function overload selection is exact-match and construction stamps the selected callable's stable `SymbolId` on the typed call. The runtime dispatches that identity through its symbol-value registry; overloaded sets remain module-local and do not become an ambiguous name lookup at evaluation time.

| Field | Value |
|---|---|
| `status` | `implemented` |
| `owner` | `metel-frontend` |
| `specified by` | `#type-construction` |
| `implements` | [`metel-frontend/src/typechecker/overload.rs::next_overload_symbol`](https://github.com/metel-lang/metel-core/blob/a66d52c5851de9647d18d858e0829b6a8477a2a2/metel-frontend/src/typechecker/overload.rs#L35) |
| `verified by` | [`metel-interpreter/tests/integration/sources/evaluator/functions/toplevel_let_mut_bound_function_dispatch.toml`](https://github.com/metel-lang/metel-core/blob/a66d52c5851de9647d18d858e0829b6a8477a2a2/metel-interpreter/tests/integration/sources/evaluator/functions/toplevel_let_mut_bound_function_dispatch.toml#L1) |
| `related` | ADR-0038, `arch.evaluation.requirement-2`, `LIMIT-TYPE-CONSTRUCTION-002` |

##### Requirement {#arch.type-construction.requirement-11}

Construction keeps generic struct field templates separate from concrete struct field scopes. At a generic struct literal or field access, it instantiates the declared raw field template with the receiver's resolved type arguments; it does not cache one concrete field type under the generic declaration's surface name.

| Field | Value |
|---|---|
| `status` | `implemented` |
| `owner` | `metel-frontend` |
| `specified by` | `#type-construction` |
| `implements` | [`metel-frontend/src/typechecker/construction.rs::build_concrete_struct_env`](https://github.com/metel-lang/metel-core/blob/a66d52c5851de9647d18d858e0829b6a8477a2a2/metel-frontend/src/typechecker/construction.rs#L40) |
| `verified by` | [`metel-interpreter/tests/integration/sources/typechecking/structs/stage5_neg_36_copy_generic_field_type_not_copy.toml`](https://github.com/metel-lang/metel-core/blob/a66d52c5851de9647d18d858e0829b6a8477a2a2/metel-interpreter/tests/integration/sources/typechecking/structs/stage5_neg_36_copy_generic_field_type_not_copy.toml#L1) |
| `related` | ADR-0012 |

##### Requirement {#arch.type-construction.requirement-12}

Generic runtime reconstruction recovers nominal type arguments from a struct or enum's typed field values against the declared field templates when the runtime value itself carries no complete argument list. The recovery is intentionally best-effort for values whose fields reveal no parameter, rather than changing every `Value::Struct`/`Value::Enum` representation to store duplicated generic metadata.

| Field | Value |
|---|---|
| `status` | `implemented` |
| `owner` | `metel-frontend`, `metel-interpreter` |
| `specified by` | `#type-construction` |
| `implements` | [`metel-frontend/src/typechecker/mod.rs::empty`](https://github.com/metel-lang/metel-core/blob/a66d52c5851de9647d18d858e0829b6a8477a2a2/metel-frontend/src/typechecker/mod.rs#L136) |
| `verified by` | [`metel-interpreter/tests/integration/sources/evaluator/generics/51_generic_nested_types.toml`](https://github.com/metel-lang/metel-core/blob/a66d52c5851de9647d18d858e0829b6a8477a2a2/metel-interpreter/tests/integration/sources/evaluator/generics/51_generic_nested_types.toml#L1) |
| `related` | ADR-0043 |

</details>

## Known limitations

`LIMIT-*` records are the authoritative inventory of known boundaries for this
section. They carry the impact, owner, disposition, and review point; the
Atlas limitations view projects the same records rather than duplicating them.

### Active records

- [`LIMIT-TYPE-CONSTRUCTION-001`](../limitations/limit-type-construction-001.md) — `Call::callee_id` falls back to name dispatch for first-class function values (a live exception to the resolution-freeze invariant).
- [`LIMIT-TYPE-CONSTRUCTION-002`](../limitations/limit-type-construction-002.md) — overload sets are not yet exportable across modules (METEL-188).

### Resolved records

No resolved `LIMIT-*` records are currently recorded for this section.
