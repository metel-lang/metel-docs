# Evaluation {#evaluation}

The tree-walk over `ElaboratedModuleGraph` to program output. Owning crate: `metel-interpreter`. Defined in `evaluator/` (`mod.rs`, `call.rs`, `display.rs`, `lvalue.rs`, `pattern.rs`, `type_of.rs`, `builtins.rs`) and `pipeline.rs` (stage orchestration).

## Model

Evaluation executes the elaborated graph with identity-keyed lexical frames. A local
binding, closure capture, and module-level value share cells only when the earlier
pipeline deliberately established that relationship; spelling is not a fallback
semantic key ([environment](#arch.evaluation.requirement-1)). The runtime registry
extends the same principle to callable and nominal dispatch
([registry](#arch.evaluation.requirement-2)).

Values retain language-level behaviour rather than exposing evaluator shortcuts:
built-in sum types use the common enum representation
([enum values](#arch.evaluation.requirement-3)); receiver modes determine mutation
visibility ([receivers](#arch.evaluation.requirement-4)); and arrays copy at binding
boundaries ([array values](#arch.evaluation.requirement-5)). Runtime reconstruction,
dynamic aspects, and error call stacks are explicit mechanisms, not hidden evaluator
fallbacks ([generic calls](#arch.evaluation.requirement-7), [dynamic aspects](#arch.evaluation.requirement-8),
[call stacks](#arch.evaluation.requirement-6)).

<details>
<summary>Verifiable architecture claims</summary>

##### Requirement {#arch.evaluation.requirement-1}

`Environment`, the lexical activation-frame model, is keyed entirely by `LocalId`, not by name: a binding is defined and read back by its `LocalId`, two distinct `LocalId`s never alias even for the same source spelling, and no scopes name-map exists as a fallback lookup path. Each module runs in its own isolated `Environment` (ADR-0029, superseding ADR-0019's flat-merge approach), seeded from already-evaluated dependency environments.

| Field | Value |
|---|---|
| `status` | `implemented` |
| `owner` | `metel-interpreter` |
| `specified by` | `#evaluation` |
| `implements` | [`metel-interpreter/src/evaluator/mod.rs::get_local`](https://github.com/metel-lang/metel-core/blob/e351096dc3e82c3715c0709f274081691673946e/metel-interpreter/src/evaluator/mod.rs#L1641) |
| `verified by` | [`metel-interpreter/src/evaluator/mod.rs::define_binding_is_readable_by_local_id`](https://github.com/metel-lang/metel-core/blob/e351096dc3e82c3715c0709f274081691673946e/metel-interpreter/src/evaluator/mod.rs#L3989) |
| `last_reviewed` | 2ae8fae97336bfe87d459103ad85d8fecbbab4ca |
| `related` | `arch.resolution.requirement-1`, `arch.resolution.requirement-2`, ADR-0029, ADR-0054, `#1052a`/`#1052b` series |

##### Requirement {#arch.evaluation.requirement-3}

`Perhaps` and `Result` have the same runtime representation as every user-defined enum: `Value::Enum { name, variant, fields, .. }`. Evaluation of propagation, iteration, pattern matching, and callable error signals uses the ordinary enum variant and field-map paths; name-specific handling is restricted to presentation in `display.rs`. The earlier flat string-keyed aspect-method environment in ADR-0013 is not current architecture: nominal methods are now held in `RuntimeRegistry` entries keyed by stable `SymbolId` (requirement 2).

| Field | Value |
|---|---|
| `status` | `implemented` |
| `owner` | `metel-interpreter` |
| `specified by` | `#evaluation` |
| `implements` | [`metel-interpreter/src/evaluator/pattern.rs::match_pattern`](https://github.com/metel-lang/metel-core/blob/e351096dc3e82c3715c0709f274081691673946e/metel-interpreter/src/evaluator/pattern.rs#L24) |
| `verified by` | [`metel-interpreter/tests/integration/sources/evaluator/builtins/83_perhaps_result_methods.toml`](https://github.com/metel-lang/metel-core/blob/e351096dc3e82c3715c0709f274081691673946e/metel-interpreter/tests/integration/sources/evaluator/builtins/83_perhaps_result_methods.toml#L1) |
| `last_reviewed` | 55dff632839ded1d889f2f38ccf8bb563846e3b1 |
| `related` | ADR-0028, `arch.evaluation.requirement-2` |

##### Requirement {#arch.evaluation.requirement-4}

Method dispatch preserves the receiver mode carried by the typed AST. Value receivers use the ordinary call path; `&self` receives a read-only view; and `&mut self` shares the caller's receiver cell into the method frame so mutations, including nested-field mutation, are immediately visible without an ad-hoc writeback convention. This is tree-walk evaluator behavior, not a compiled-backend representation commitment.

| Field | Value |
|---|---|
| `status` | `implemented` |
| `owner` | `metel-interpreter` |
| `specified by` | `#evaluation` |
| `implements` | [`metel-interpreter/src/evaluator/call.rs::bind_method_params`](https://github.com/metel-lang/metel-core/blob/e351096dc3e82c3715c0709f274081691673946e/metel-interpreter/src/evaluator/call.rs#L16) |
| `verified by` | [`metel-interpreter/tests/integration/sources/evaluator/aspects/93_dyn_aspect_mutable_receiver_dispatch.toml`](https://github.com/metel-lang/metel-core/blob/e351096dc3e82c3715c0709f274081691673946e/metel-interpreter/tests/integration/sources/evaluator/aspects/93_dyn_aspect_mutable_receiver_dispatch.toml#L1) |
| `last_reviewed` | 55dff632839ded1d889f2f38ccf8bb563846e3b1 |
| `related` | ADR-0036, RFC-0044 |

##### Requirement {#arch.evaluation.requirement-5}

Array values use value semantics at evaluator binding and assignment boundaries: `Environment::define` and `Environment::set` deep-clone their stored value, recursively cloning arrays and nested aggregate contents rather than allowing an ordinary assignment to create a mutable array alias.

| Field | Value |
|---|---|
| `status` | `implemented` |
| `owner` | `metel-interpreter` |
| `specified by` | `#evaluation` |
| `implements` | [`metel-interpreter/src/evaluator/mod.rs::define_binding`](https://github.com/metel-lang/metel-core/blob/e351096dc3e82c3715c0709f274081691673946e/metel-interpreter/src/evaluator/mod.rs#L1600) |
| `verified by` | [`metel-interpreter/tests/integration/sources/evaluator/control_flow/91_nested_break_propagation.toml`](https://github.com/metel-lang/metel-core/blob/e351096dc3e82c3715c0709f274081691673946e/metel-interpreter/tests/integration/sources/evaluator/control_flow/91_nested_break_propagation.toml#L1) |
| `last_reviewed` | 55dff632839ded1d889f2f38ccf8bb563846e3b1 |
| `related` | ADR-0007 |

##### Requirement {#arch.evaluation.requirement-6}

The evaluator maintains call frames in thread-local storage. Call entry pushes its function name and source call-site, normal and error exits pop it, and diagnostic construction reads the resulting stack without adding a stack parameter through every evaluation helper.

| Field | Value |
|---|---|
| `status` | `implemented` |
| `owner` | `metel-interpreter` |
| `specified by` | `#evaluation` |
| `implements` | [`metel-interpreter/src/evaluator/mod.rs::push_frame`](https://github.com/metel-lang/metel-core/blob/e351096dc3e82c3715c0709f274081691673946e/metel-interpreter/src/evaluator/mod.rs#L27) |
| `verified by` | [`metel-interpreter/tests/integration/sources/evaluator/functions/18_return.toml`](https://github.com/metel-lang/metel-core/blob/e351096dc3e82c3715c0709f274081691673946e/metel-interpreter/tests/integration/sources/evaluator/functions/18_return.toml#L1) |
| `last_reviewed` | 55dff632839ded1d889f2f38ccf8bb563846e3b1 |
| `related` | ADR-0008 |

##### Requirement {#arch.evaluation.requirement-7}

Generic functions and let-polymorphic closures retain an untyped body plus typechecking context at runtime. A call reconstructs the body with the call-site types before evaluation, rather than storing one incorrectly monomorphic typed body for all instantiations.

| Field | Value |
|---|---|
| `status` | `implemented` |
| `owner` | `metel-interpreter`, `metel-frontend` |
| `specified by` | `#evaluation` |
| `implements` | [`metel-interpreter/src/evaluator/call.rs::call_runtime_callable`](https://github.com/metel-lang/metel-core/blob/e351096dc3e82c3715c0709f274081691673946e/metel-interpreter/src/evaluator/call.rs#L55) |
| `verified by` | [`metel-interpreter/tests/integration/sources/evaluator/types/fixed_array_nested.toml`](https://github.com/metel-lang/metel-core/blob/e351096dc3e82c3715c0709f274081691673946e/metel-interpreter/tests/integration/sources/evaluator/types/fixed_array_nested.toml#L1) |
| `last_reviewed` | 55dff632839ded1d889f2f38ccf8bb563846e3b1 |
| `related` | ADR-0010, ADR-0011, `LIMIT-EVALUATION-001` |

##### Requirement {#arch.evaluation.requirement-8}

`dyn Aspect` evaluation uses an explicit `Value::DynAspect` wrapper containing the erased value and the already-resolved concrete type and principal-aspect identities. Typed `DynCoerce` nodes introduce the wrapper at coercion sites; runtime method dispatch reuses the type-keyed registry while `value_to_type` rebuilds the dynamic type from wrapper metadata without exposing the contained concrete value.

| Field | Value |
|---|---|
| `status` | `implemented` |
| `owner` | `metel-interpreter`, `metel-frontend` |
| `specified by` | `#evaluation` |
| `implements` | [`metel-interpreter/src/evaluator/type_of.rs::value_to_type`](https://github.com/metel-lang/metel-core/blob/e351096dc3e82c3715c0709f274081691673946e/metel-interpreter/src/evaluator/type_of.rs#L22) |
| `verified by` | [`metel-interpreter/tests/integration/sources/evaluator/aspects/91_dyn_aspect_borrowed_reference_dispatch.toml`](https://github.com/metel-lang/metel-core/blob/e351096dc3e82c3715c0709f274081691673946e/metel-interpreter/tests/integration/sources/evaluator/aspects/91_dyn_aspect_borrowed_reference_dispatch.toml#L1) |
| `last_reviewed` | 55dff632839ded1d889f2f38ccf8bb563846e3b1 |
| `related` | ADR-0053, RFC-0008 |

##### Requirement {#arch.evaluation.requirement-2}

`RuntimeRegistry` dispatches struct/enum type entries and overloaded/top-level function values (`symbol_values`) by stable `SymbolId`, not by re-deriving a name lookup at call time — the runtime-side counterpart of `arch.resolution.requirement-1`'s frozen-identity invariant. Two parts remain genuinely name-keyed by design: `type_ids` (the single surface-name→`SymbolId` translation point for sites that only have a name, e.g. `List::new`, and never had an id threaded to them) and `pattern_methods` (structural, pattern-dispatched method names for receivers like arrays that carry no `type_id`). This is not full coverage of the no-semantic-lookup invariant — `tools/check_no_semantic_name_lookup.py`'s own docstring names `RuntimeRegistry` as "a separate, adjacent concern with its own nuances... not yet brought under this check," i.e. the checker itself documents the gap rather than silently missing it.

| Field | Value |
|---|---|
| `status` | `partial` |
| `owner` | `metel-interpreter` |
| `specified by` | `#evaluation` |
| `implements` | [`metel-interpreter/src/evaluator/mod.rs::get_type_value_by_id`](https://github.com/metel-lang/metel-core/blob/e351096dc3e82c3715c0709f274081691673946e/metel-interpreter/src/evaluator/mod.rs#L724) |
| `verified by` | [`metel-interpreter/tests/integration/sources/evaluator/functions/toplevel_let_mut_bound_function_dispatch.toml`](https://github.com/metel-lang/metel-core/blob/e351096dc3e82c3715c0709f274081691673946e/metel-interpreter/tests/integration/sources/evaluator/functions/toplevel_let_mut_bound_function_dispatch.toml#L1) |
| `last_reviewed` | 55dff632839ded1d889f2f38ccf8bb563846e3b1 |
| `related` | `arch.resolution.requirement-1`, `tools/check_no_semantic_name_lookup.py` |

</details>

## Known limitations

`LIMIT-*` records are the authoritative inventory of known boundaries for this
section. They carry the impact, owner, disposition, and review point; the
Atlas limitations view projects the same records rather than duplicating them.

### Active records

- [`LIMIT-EVALUATION-001`](../limitations/limit-evaluation-001.md) — generic function dispatch re-constructs on every call rather than monomorphizing once.
- [`LIMIT-EVALUATION-002`](../limitations/limit-evaluation-002.md) — one specific cross-module mutual-recursion shape is unsupported (`#189`).
- [`LIMIT-EVALUATION-003`](../limitations/limit-evaluation-003.md) — `RuntimeRegistry`'s `type_ids`/`pattern_methods` remain name-keyed and are explicitly outside `tools/check_no_semantic_name_lookup.py`'s scan.
- [`LIMIT-EVALUATION-004`](../limitations/limit-evaluation-004.md) — the evaluator is a deliberate PoC ("will almost certainly be rewritten"), not a stable target shape.

### Resolved records

No resolved `LIMIT-*` records are currently recorded for this section.
