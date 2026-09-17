# Type Construction {#type-construction}

The pass that builds the typed IR from `#type-inference`'s results: `typechecker::construction` (~8,050 lines across `typechecker/construction.rs` and `typechecker/construction/{declarations,expressions,calls,patterns,narrowing}.rs`), `typed_ast/` (748 lines, the typed IR itself), and the typechecker's shared support consumed by construction — `registry.rs`, `projections.rs`, `overload.rs`, `conversions.rs`, `object_safety.rs`, `handoff.rs` (~3,500 lines). ~12,300 lines total. Owning crate: `metel-frontend`. This section consumes `#type-inference`'s output; it does not re-derive it.

##### Requirement {#arch.type-construction.requirement-1}

`check_graph` typechecks a normalized module graph in topological order — dependencies before dependents — running both passes (inference, then construction) per module, and accumulates each module's exported type schemes into a `GlobalExports` structure so a later module can import an earlier module's inferred types without re-inferring them.

| Field | Value |
|---|---|
| `status` | `implemented` |
| `owner` | `metel-frontend` |
| `specified by` | `#type-construction` |
| `implements` | `metel-frontend/src/typechecker/mod.rs` (`check_graph`, `check_graph_with_report`, `GlobalExports`) |
| `verified by` | general correctness is a precondition of the full 1,183-fixture integration suite; no dedicated topological-order unit test was found directly naming this invariant (unlike `arch.parsing.requirement-1`'s module-loading order, which has one) |
| `related` | ADR-0022 |

##### Requirement {#arch.type-construction.requirement-2}

Construction stamps the typed IR with resolved identities wherever the frontend has already produced one, rather than re-deriving them: a `FrozenIdentity` bundle threads the member table (`#1051`, field-access and enum-variant-literal `FieldId`/`VariantId`, `#1062`) and the span→`BindingId` bridge (`#1052`) through `check_graph_with_report`, so e.g. `TypedExpr::Ident` carries its resolved binding. The move-check and diagnostic-tool entry points pass `None` for this bundle and get every id as `None` — construction degrades gracefully rather than requiring the full identity system for every caller.

| Field | Value |
|---|---|
| `status` | `implemented` |
| `owner` | `metel-frontend` |
| `specified by` | `#type-construction` |
| `implements` | `metel-frontend/src/typechecker/mod.rs` (`check_graph_with_report`, `FrozenIdentity` parameter); `metel-frontend/src/typechecker/construction.rs` and `construction/*.rs` |
| `verified by` | `metel-frontend/src/typechecker/mod.rs::construct_generic_body_stamps_a_real_local_id`, `::propagate_error_desugar_shares_one_local_id_between_arms`, `::toplevel_let_initializer_reference_carries_a_symbol_id`, `::implicit_copy_capture_carries_the_enclosing_local_id`, `::array_extend_method_self_param_carries_a_local_id`, `::qualified_path_static_method_call_carries_a_type_id`, `::record_projection_base_carries_its_binding_id`, `::toplevel_bare_statement_reference_carries_a_symbol_id` (8 of 10 unit tests in the module; no `construction/*.rs` file has its own unit tests — the pass is otherwise verified only by the integration suite) |
| `related` | `arch.resolution.requirement-2`, `arch.resolution.requirement-3`, ADR-0054, `#1051`, `#1052` |

##### Requirement {#arch.type-construction.requirement-3}

Opaque return variables are validated at constraint-composition time, not by inspecting only the final solved substitution. When an opaque-return marker resolves directly to a concrete type, inference reports `T0018` at that constraint; it may remain a type variable while it is threaded through another generic or opaque interface. Construction consumes that solved result and must not reintroduce the concrete identity.

| Field | Value |
|---|---|
| `status` | `implemented` |
| `owner` | `metel-frontend` |
| `specified by` | `#type-construction` |
| `implements` | `metel-frontend/src/typeinference/mod.rs` (`apply_constraint_with_coercion`, `opaque_return_vars`) |
| `verified by` | integration fixtures `metel-interpreter/tests/integration/sources/typechecking/generics/stage18_neg_03_return_impl_aspect_caller_cannot_name`, `stage18_neg_06_return_impl_aspect_non_generic_param` |
| `related` | ADR-0044, RFC-0037 |

##### Requirement {#arch.type-construction.requirement-4}

The typechecker treats `T[]` as `Copy` unconditionally: its copy eligibility is a deliberate `InferType::Array` special case and does not inspect the element type. Other array-aspect eligibility remains conditional on the element and ordinary stdlib impl/bound machinery; this is not a temporary stdlib-lookup gap.

| Field | Value |
|---|---|
| `status` | `implemented` |
| `owner` | `metel-frontend` |
| `specified by` | `#type-construction` |
| `implements` | `metel-frontend/src/typeinference/mod.rs` (`InferContext::infer_type_satisfies_aspect`, `InferType::Array`) |
| `verified by` | general integration-suite coverage of slice moves and `Copy`/`Drop` eligibility; no dedicated `T[]`-with-non-`Copy`-element fixture was identified in this pass |
| `related` | ADR-0046, RFC-0126 |

##### Requirement {#arch.type-construction.requirement-5}

Until destructor invocation exists, a `std::core::Drop` impl may declare only an empty `drop` method body. Construction identifies the standard aspect by declaring module, leaving a user-defined same-named aspect alone, and rejects a non-empty body with `T0001` rather than accepting cleanup code that the evaluator would silently never run.

| Field | Value |
|---|---|
| `status` | `implemented` |
| `owner` | `metel-frontend` |
| `specified by` | `#type-construction` |
| `implements` | `metel-frontend/src/typechecker/construction/declarations.rs` (`reject_inert_destructor`) |
| `verified by` | integration fixtures `metel-interpreter/tests/integration/sources/typechecking/structs/stage5_neg_39_drop_body_cannot_run_yet`, `stage5_40_empty_drop_body_still_declares_drop`, `metel-interpreter/tests/integration/sources/typechecking/aspects/stage13_11_user_declared_drop_aspect_is_unaffected` |
| `related` | ADR-0047, RFC-0071 §9c, `#261` |

##### Requirement {#arch.type-construction.requirement-6}

Type ascriptions constrain inference and construction but are erased from typed IR: construction builds the inner expression using the resolved annotation as context instead of emitting a runtime no-op `TypedExpr::Ascribe` node.

| Field | Value |
|---|---|
| `status` | `implemented` |
| `owner` | `metel-frontend` |
| `specified by` | `#type-construction` |
| `implements` | `metel-frontend/src/typechecker/inference/expressions.rs`; `metel-frontend/src/typechecker/construction/expressions.rs`; `metel-frontend/src/typed_ast/mod.rs` |
| `verified by` | integration fixtures `metel-interpreter/tests/integration/sources/typechecking/builtins/stage8_neg_02_ascribe_type_mismatch`, `stage8_neg_03_ascribe_bool_as_int`, `stage8_neg_04_ascribe_wrong_struct` |
| `related` | ADR-0009 |

##### Requirement {#arch.type-construction.requirement-7}

Operand legality is checked after operand types are resolved: arithmetic and unary negation accept numeric or `Never` operands, while ordering comparisons additionally accept `Str`. The construction pass reports the language's operand-type diagnostic (`T0005`) rather than leaving invalid operator shapes for evaluation.

| Field | Value |
|---|---|
| `status` | `implemented` |
| `owner` | `metel-frontend` |
| `specified by` | `#type-construction` |
| `implements` | `metel-frontend/src/typechecker/construction.rs` (`construct_binop`, `construct_unaryop`) |
| `verified by` | general integration-suite coverage of operator type errors; no dedicated unit test naming the pass-2 placement was found |
| `related` | ADR-0017, `T0005` |

##### Requirement {#arch.type-construction.requirement-8}

Import visibility is diagnosed while building import schemes, where the full module graph and exports are available. Name resolution records import bindings without prematurely collapsing a private-item error into a missing-item error; construction/typechecking then distinguishes `T0009` visibility from `T0003` absence.

| Field | Value |
|---|---|
| `status` | `implemented` |
| `owner` | `metel-frontend` |
| `specified by` | `#type-construction` |
| `implements` | `metel-frontend/src/name_resolver.rs`; `metel-frontend/src/typechecker/mod.rs` (`build_import_schemes`) |
| `verified by` | general integration-suite coverage of imports and visibility; no dedicated test naming this ownership boundary was found |
| `related` | ADR-0024, `T0003`, `T0009` |

##### Requirement {#arch.type-construction.requirement-9}

Aspect default methods are materialized as typed methods before evaluation. Inference collects inherited defaults for an impl and construction emits a concrete typed body for each applicable default, while negative impls deliberately do not acquire default bodies; runtime dispatch therefore never evaluates untyped default-method syntax.

| Field | Value |
|---|---|
| `status` | `implemented` |
| `owner` | `metel-frontend` |
| `specified by` | `#type-construction` |
| `implements` | `metel-frontend/src/typechecker/inference/declarations.rs`; `metel-frontend/src/typechecker/construction/declarations.rs` |
| `verified by` | integration fixtures `metel-interpreter/tests/integration/sources/typechecking/aspects/stage12_01_default_methods`, `stage12_02_override_replaces_default`, `stage12_03_multiple_defaults` |
| `related` | ADR-0034 |

##### Requirement {#arch.type-construction.requirement-10}

Free-function overload selection is exact-match and construction stamps the selected callable's stable `SymbolId` on the typed call. The runtime dispatches that identity through its symbol-value registry; overloaded sets remain module-local and do not become an ambiguous name lookup at evaluation time.

| Field | Value |
|---|---|
| `status` | `implemented` |
| `owner` | `metel-frontend` |
| `specified by` | `#type-construction` |
| `implements` | `metel-frontend/src/typechecker/overload.rs` (`build_overload_table`, selection); `metel-frontend/src/typechecker/construction/calls.rs`; `metel-interpreter/src/evaluator/mod.rs` (`RuntimeRegistry::symbol_values`) |
| `verified by` | integration fixtures `metel-interpreter/tests/integration/sources/typechecking/overload_duplicate`, `overload_no_match` |
| `related` | ADR-0038, `arch.evaluation.requirement-2`, `LIMIT-TYPE-CONSTRUCTION-002` |

##### Requirement {#arch.type-construction.requirement-11}

Construction keeps generic struct field templates separate from concrete struct field scopes. At a generic struct literal or field access, it instantiates the declared raw field template with the receiver's resolved type arguments; it does not cache one concrete field type under the generic declaration's surface name.

| Field | Value |
|---|---|
| `status` | `implemented` |
| `owner` | `metel-frontend` |
| `specified by` | `#type-construction` |
| `implements` | `metel-frontend/src/typechecker/construction.rs` (`ConstructCtx`, concrete struct scopes and generic method/type environments); `metel-frontend/src/typechecker/construction/expressions.rs` |
| `verified by` | general integration-suite coverage of generic struct literals and field access; no dedicated unit test naming the split-environment invariant was found |
| `related` | ADR-0012 |

##### Requirement {#arch.type-construction.requirement-12}

Generic runtime reconstruction recovers nominal type arguments from a struct or enum's typed field values against the declared field templates when the runtime value itself carries no complete argument list. The recovery is intentionally best-effort for values whose fields reveal no parameter, rather than changing every `Value::Struct`/`Value::Enum` representation to store duplicated generic metadata.

| Field | Value |
|---|---|
| `status` | `implemented` |
| `owner` | `metel-frontend`, `metel-interpreter` |
| `specified by` | `#type-construction` |
| `implements` | `metel-frontend/src/typechecker/mod.rs` (`infer_named_type_args`); `metel-interpreter/src/evaluator/type_of.rs` (`value_to_type`); `metel-interpreter/src/evaluator/call.rs` |
| `verified by` | general integration-suite coverage of generic method/runtime reconstruction; no focused fixture naming field-based recovery was found |
| `related` | ADR-0043 |

## Known limitations

- [`LIMIT-TYPE-CONSTRUCTION-001`](../limitations/limit-type-construction-001.md) — `Call::callee_id` falls back to name dispatch for first-class function values (a live exception to the resolution-freeze invariant).
- [`LIMIT-TYPE-CONSTRUCTION-002`](../limitations/limit-type-construction-002.md) — overload sets are not yet exportable across modules (METEL-188).

`?` error coercion (originally filed here as `LIMIT-TYPE-CONSTRUCTION-003`) moved to [`#type-inference`'s Known limitations](type-inference.md#known-limitations) as `LIMIT-TYPE-INFERENCE-001` — the actual `From`-impl check runs during inference, not construction; this section only carries the desugared node's identity stamping (`arch.type-construction.requirement-2`).
