# Type Construction {#type-construction}

The pass that builds the typed IR from [Type Inference](type-inference.md)'s results: `typechecker::construction` (~8,050 lines across `typechecker/construction.rs` and `typechecker/construction/{declarations,expressions,calls,patterns,narrowing}.rs`), `typed_ast/` (748 lines, the typed IR itself), and the typechecker's shared support consumed by construction — `registry.rs`, `projections.rs`, `overload.rs`, `conversions.rs`, `object_safety.rs`, `handoff.rs` (~3,500 lines). ~12,300 lines total. Owning crate: `metel-frontend`. This section consumes [Type Inference](type-inference.md)'s output; it does not re-derive it.

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

`check_graph` typechecks a normalized module graph in topological order, running inference then construction per module, and accumulates each module's exported schemes in `GlobalExports` so later modules import them without re-inferring.

| Field | Value |
|---|---|
| `status` | `implemented` |
| `owner` | `metel-frontend` |
| `specified by` | `#type-construction` |
| `implements` | [`metel-frontend/src/pipeline/type_checking/mod.rs::check_graph`](https://github.com/metel-lang/metel-core/blob/4155d94ccbc5b1657799f3537515610f3bb139c3/metel-frontend/src/pipeline/type_checking/mod.rs#L353) |
| `verified by` | [`metel-interpreter/tests/integration/sources/module_semantics/elaboration_polymorphic_cross_module/test.toml`](https://github.com/metel-lang/metel-core/blob/4155d94ccbc5b1657799f3537515610f3bb139c3/metel-interpreter/tests/integration/sources/module_semantics/elaboration_polymorphic_cross_module/test.toml#L1) |
| `last_reviewed` | 2c95c6d9c5f131d86fa08889153355b451e12c9e |
| `related` | ADR-0022 |

##### Requirement {#arch.type-construction.requirement-2}

Construction stamps the typed IR with the identities the frontend already produced (`FieldId`/`VariantId` member ids, the span-to-`BindingId` bridge) through a `FrozenIdentity` bundle in `check_graph_with_report`; callers that pass `None` get every id as `None`, so construction degrades gracefully.

| Field | Value |
|---|---|
| `status` | `implemented` |
| `owner` | `metel-frontend` |
| `specified by` | `#type-construction` |
| `implements` | [`metel-frontend/src/pipeline/type_checking/mod.rs::check_graph_with_report`](https://github.com/metel-lang/metel-core/blob/4155d94ccbc5b1657799f3537515610f3bb139c3/metel-frontend/src/pipeline/type_checking/mod.rs#L370) |
| `verified by` | [`metel-frontend/src/pipeline/type_checking/mod.rs::construct_generic_body_stamps_a_real_local_id`](https://github.com/metel-lang/metel-core/blob/4155d94ccbc5b1657799f3537515610f3bb139c3/metel-frontend/src/pipeline/type_checking/mod.rs#L1621) |
| `last_reviewed` | de72649a95a5c947ac985069b692008b76a82f7e |
| `related` | `arch.resolution.requirement-2`, `arch.resolution.requirement-3`, ADR-0054, `#1051`, `#1052` |

##### Requirement {#arch.type-construction.requirement-3}

Opaque return variables are validated at constraint-composition time, not only against the final substitution: when an opaque-return marker resolves directly to a concrete type, inference reports `T0018`, and construction must not reintroduce the concrete identity.

| Field | Value |
|---|---|
| `status` | `implemented` |
| `owner` | `metel-frontend` |
| `specified by` | `#type-construction` |
| `implements` | [`metel-frontend/src/pipeline/type_checking/typeinference/mod.rs::apply_constraint_with_coercion`](https://github.com/metel-lang/metel-core/blob/4155d94ccbc5b1657799f3537515610f3bb139c3/metel-frontend/src/pipeline/type_checking/typeinference/mod.rs#L1265) |
| `verified by` | [`metel-interpreter/tests/integration/sources/typechecking/generics/stage18_neg_03_return_impl_aspect_caller_cannot_name.toml`](https://github.com/metel-lang/metel-core/blob/4155d94ccbc5b1657799f3537515610f3bb139c3/metel-interpreter/tests/integration/sources/typechecking/generics/stage18_neg_03_return_impl_aspect_caller_cannot_name.toml#L1) |
| `last_reviewed` | de72649a95a5c947ac985069b692008b76a82f7e |
| `related` | ADR-0044, RFC-0037 |

##### Requirement {#arch.type-construction.requirement-4}

The typechecker treats `T[]` as `Copy` unconditionally, as a deliberate `InferType::Array` special case that does not inspect the element type; other array-aspect eligibility stays conditional on the element through ordinary stdlib impl and bound machinery.

| Field | Value |
|---|---|
| `status` | `implemented` |
| `owner` | `metel-frontend` |
| `specified by` | `#type-construction` |
| `implements` | [`metel-frontend/src/pipeline/type_checking/typeinference/mod.rs::infer_type_satisfies_aspect`](https://github.com/metel-lang/metel-core/blob/4155d94ccbc5b1657799f3537515610f3bb139c3/metel-frontend/src/pipeline/type_checking/typeinference/mod.rs#L3168) |
| `verified by` | [`metel-interpreter/tests/integration/sources/typechecking/types/dynamic_array_is_copy_unconditionally.toml`](https://github.com/metel-lang/metel-core/blob/4155d94ccbc5b1657799f3537515610f3bb139c3/metel-interpreter/tests/integration/sources/typechecking/types/dynamic_array_is_copy_unconditionally.toml#L1) |
| `last_reviewed` | 8717cc6088e4dcf55f6f5580e60ad936d9bf69cf |
| `related` | ADR-0046, RFC-0126 |

##### Requirement {#arch.type-construction.requirement-5}

Until destructors run, a `std::core::Drop` impl may declare only an empty `drop` body: construction identifies the standard aspect by declaring module (a same-named user aspect is unaffected) and rejects a non-empty body with `T0001`.

| Field | Value |
|---|---|
| `status` | `implemented` |
| `owner` | `metel-frontend` |
| `specified by` | `#type-construction` |
| `implements` | [`metel-frontend/src/pipeline/type_checking/construction/declarations.rs::reject_inert_destructor`](https://github.com/metel-lang/metel-core/blob/4155d94ccbc5b1657799f3537515610f3bb139c3/metel-frontend/src/pipeline/type_checking/construction/declarations.rs#L392) |
| `verified by` | [`metel-interpreter/tests/integration/sources/typechecking/aspects/neg_std_drop_nonempty_body_is_rejected.toml`](https://github.com/metel-lang/metel-core/blob/4155d94ccbc5b1657799f3537515610f3bb139c3/metel-interpreter/tests/integration/sources/typechecking/aspects/neg_std_drop_nonempty_body_is_rejected.toml#L1); [`metel-interpreter/tests/integration/sources/typechecking/aspects/stage13_11_user_declared_drop_aspect_is_unaffected.toml`](https://github.com/metel-lang/metel-core/blob/4155d94ccbc5b1657799f3537515610f3bb139c3/metel-interpreter/tests/integration/sources/typechecking/aspects/stage13_11_user_declared_drop_aspect_is_unaffected.toml#L1) |
| `last_reviewed` | de72649a95a5c947ac985069b692008b76a82f7e |
| `related` | ADR-0047, RFC-0071 §9c, `#261` |

##### Requirement {#arch.type-construction.requirement-6}

Type ascriptions constrain inference and construction but are erased from typed IR: construction builds the inner expression using the resolved annotation as context instead of emitting a runtime no-op `TypedExpr::Ascribe` node.

| Field | Value |
|---|---|
| `status` | `implemented` |
| `owner` | `metel-frontend` |
| `specified by` | `#type-construction` |
| `implements` | [`metel-frontend/src/pipeline/type_checking/construction/expressions.rs::construct_expr`](https://github.com/metel-lang/metel-core/blob/4155d94ccbc5b1657799f3537515610f3bb139c3/metel-frontend/src/pipeline/type_checking/construction/expressions.rs#L703) |
| `verified by` | [`metel-frontend/src/pipeline/type_checking/mod.rs::typed_ir_has_no_ascription_node`](https://github.com/metel-lang/metel-core/blob/4155d94ccbc5b1657799f3537515610f3bb139c3/metel-frontend/src/pipeline/type_checking/mod.rs#L1527); [`metel-interpreter/tests/integration/sources/typechecking/builtins/stage8_neg_02_ascribe_type_mismatch.toml`](https://github.com/metel-lang/metel-core/blob/4155d94ccbc5b1657799f3537515610f3bb139c3/metel-interpreter/tests/integration/sources/typechecking/builtins/stage8_neg_02_ascribe_type_mismatch.toml#L1) |
| `last_reviewed` | de72649a95a5c947ac985069b692008b76a82f7e |
| `related` | ADR-0009 |

##### Requirement {#arch.type-construction.requirement-7}

Operand legality is checked once operand types are resolved: arithmetic and unary negation accept numeric or `Never` operands, ordering comparisons also accept `Str`, and construction reports `T0005` rather than leaving invalid operator shapes for evaluation.

| Field | Value |
|---|---|
| `status` | `implemented` |
| `owner` | `metel-frontend` |
| `specified by` | `#type-construction` |
| `implements` | [`metel-frontend/src/pipeline/type_checking/construction.rs::construct_binop`](https://github.com/metel-lang/metel-core/blob/4155d94ccbc5b1657799f3537515610f3bb139c3/metel-frontend/src/pipeline/type_checking/construction.rs#L1455); [`metel-frontend/src/pipeline/type_checking/construction.rs::construct_unaryop`](https://github.com/metel-lang/metel-core/blob/4155d94ccbc5b1657799f3537515610f3bb139c3/metel-frontend/src/pipeline/type_checking/construction.rs#L1771) |
| `verified by` | [`metel-interpreter/tests/integration/sources/typechecking/literals/neg_05_generic_field_literal_add_string.toml`](https://github.com/metel-lang/metel-core/blob/4155d94ccbc5b1657799f3537515610f3bb139c3/metel-interpreter/tests/integration/sources/typechecking/literals/neg_05_generic_field_literal_add_string.toml#L1) |
| `last_reviewed` | de72649a95a5c947ac985069b692008b76a82f7e |
| `related` | ADR-0017, `T0005` |

##### Requirement {#arch.type-construction.requirement-8}

Import visibility is diagnosed while building import schemes, where the full module graph is known: name resolution records import bindings without collapsing a private-item error into a missing-item one, so construction reports `T0009` (visibility) apart from `T0003` (absence).

| Field | Value |
|---|---|
| `status` | `implemented` |
| `owner` | `metel-frontend` |
| `specified by` | `#type-construction` |
| `implements` | [`metel-frontend/src/pipeline/type_checking/mod.rs::build_import_schemes`](https://github.com/metel-lang/metel-core/blob/4155d94ccbc5b1657799f3537515610f3bb139c3/metel-frontend/src/pipeline/type_checking/mod.rs#L633) |
| `verified by` | [`metel-interpreter/tests/integration/sources/module_semantics/importing_nonexistent_name_is_t0003/test.toml`](https://github.com/metel-lang/metel-core/blob/4155d94ccbc5b1657799f3537515610f3bb139c3/metel-interpreter/tests/integration/sources/module_semantics/importing_nonexistent_name_is_t0003/test.toml#L1); [`metel-interpreter/tests/integration/sources/module_semantics/importing_private_item_is_t0009/test.toml`](https://github.com/metel-lang/metel-core/blob/4155d94ccbc5b1657799f3537515610f3bb139c3/metel-interpreter/tests/integration/sources/module_semantics/importing_private_item_is_t0009/test.toml#L1) |
| `last_reviewed` | 8717cc6088e4dcf55f6f5580e60ad936d9bf69cf |
| `related` | ADR-0024, `T0003`, `T0009` |

##### Requirement {#arch.type-construction.requirement-9}

Aspect default methods are materialized as typed methods before evaluation: inference collects an impl's inherited defaults and construction emits a typed body for each, except that negative impls acquire none, so runtime dispatch never evaluates untyped default-method syntax.

| Field | Value |
|---|---|
| `status` | `implemented` |
| `owner` | `metel-frontend` |
| `specified by` | `#type-construction` |
| `implements` | [`metel-frontend/src/pipeline/type_checking/inference/declarations.rs::infer_decl`](https://github.com/metel-lang/metel-core/blob/4155d94ccbc5b1657799f3537515610f3bb139c3/metel-frontend/src/pipeline/type_checking/inference/declarations.rs#L18) |
| `verified by` | [`metel-interpreter/tests/integration/sources/typechecking/aspects/stage12_01_default_methods.toml`](https://github.com/metel-lang/metel-core/blob/4155d94ccbc5b1657799f3537515610f3bb139c3/metel-interpreter/tests/integration/sources/typechecking/aspects/stage12_01_default_methods.toml#L1) |
| `last_reviewed` | de72649a95a5c947ac985069b692008b76a82f7e |
| `related` | ADR-0034 |

##### Requirement {#arch.type-construction.requirement-10}

Free-function overload selection is exact-match, and construction stamps the selected callable's stable `SymbolId` on the typed call; the runtime dispatches that identity through its symbol-value registry, and overload sets stay module-local.

| Field | Value |
|---|---|
| `status` | `implemented` |
| `owner` | `metel-frontend` |
| `specified by` | `#type-construction` |
| `implements` | [`metel-frontend/src/pipeline/type_checking/overload.rs::next_overload_symbol`](https://github.com/metel-lang/metel-core/blob/4155d94ccbc5b1657799f3537515610f3bb139c3/metel-frontend/src/pipeline/type_checking/overload.rs#L38) |
| `verified by` | [`metel-interpreter/tests/integration/sources/evaluator/functions/toplevel_let_mut_bound_function_dispatch.toml`](https://github.com/metel-lang/metel-core/blob/4155d94ccbc5b1657799f3537515610f3bb139c3/metel-interpreter/tests/integration/sources/evaluator/functions/toplevel_let_mut_bound_function_dispatch.toml#L1) |
| `last_reviewed` | 8b844c9117d5c6a730882aeaf521184c3055eb2f |
| `related` | ADR-0038, `arch.evaluation.requirement-2`, `LIMIT-TYPE-CONSTRUCTION-002` |

##### Requirement {#arch.type-construction.requirement-11}

At a generic struct literal or field access, construction instantiates the declared raw field template with the receiver's resolved type arguments; it does not cache one concrete field type under the generic declaration's surface name.

| Field | Value |
|---|---|
| `status` | `implemented` |
| `owner` | `metel-frontend` |
| `specified by` | `#type-construction` |
| `implements` | [`metel-frontend/src/pipeline/type_checking/construction.rs::build_concrete_struct_env`](https://github.com/metel-lang/metel-core/blob/4155d94ccbc5b1657799f3537515610f3bb139c3/metel-frontend/src/pipeline/type_checking/construction.rs#L39) |
| `verified by` | [`metel-interpreter/tests/integration/sources/evaluator/generics/53_generic_struct.toml`](https://github.com/metel-lang/metel-core/blob/4155d94ccbc5b1657799f3537515610f3bb139c3/metel-interpreter/tests/integration/sources/evaluator/generics/53_generic_struct.toml#L1) |
| `last_reviewed` | 8717cc6088e4dcf55f6f5580e60ad936d9bf69cf |
| `related` | ADR-0012 |

##### Requirement {#arch.type-construction.requirement-12}

Generic runtime reconstruction recovers a struct or enum's type arguments from its typed field values against the declared field templates when the value carries no argument list; this is best-effort for values whose fields reveal no parameter, rather than storing generic metadata on every value.

| Field | Value |
|---|---|
| `status` | `implemented` |
| `owner` | `metel-frontend`, `metel-interpreter` |
| `specified by` | `#type-construction` |
| `implements` | [`metel-frontend/src/pipeline/type_checking/mod.rs::infer_named_type_args`](https://github.com/metel-lang/metel-core/blob/4155d94ccbc5b1657799f3537515610f3bb139c3/metel-frontend/src/pipeline/type_checking/mod.rs#L1175) |
| `verified by` | [`metel-interpreter/tests/integration/sources/evaluator/generics/51_generic_nested_types.toml`](https://github.com/metel-lang/metel-core/blob/4155d94ccbc5b1657799f3537515610f3bb139c3/metel-interpreter/tests/integration/sources/evaluator/generics/51_generic_nested_types.toml#L1) |
| `last_reviewed` | de72649a95a5c947ac985069b692008b76a82f7e |
| `related` | ADR-0043 |

</details>

## Known limitations

<!-- records:limitations -->
