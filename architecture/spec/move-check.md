# Move Check {#move-check}

An opt-in validation pass over the typed module graph that rejects use-after-move. It
runs only when requested: `RunOptions::move_check` and the CLI's `--move-check` default to
`false`, and each of the orchestrator's entry points gates the pass behind that option.
The owning crate is `metel-frontend`; the pass lives in `move_check/`, and the addressable
lvalue-path representation it shares with the typechecker lives in `ownership/place`.

## Model

Move checking is a consumer of typed structure, not a second type checker. When
enabled, it follows values through [places](#arch.move-check.requirement-2)—a root
binding plus projections—and records the state transitions that make a later use
illegal. This makes partial moves explainable: consuming one field is different from
consuming the whole value, and `Drop` or reference rules can constrain either form.
Places carry binding identities and use the shared ownership projection algebra, and
the flow lattice is keyed by binding identity, so source names appear only when a
diagnostic is rendered.

The general pass is opt-in, but closure capture safety is language behaviour. Its
capture-list and multiplicity checks run unconditionally during type checking
([closure captures](#arch.move-check.requirement-3)), so a program cannot evade a closure
ownership error merely by omitting `--move-check`.

### Generic bodies

A generic body is checked against what its **definition** declares, never against a
concrete instantiation. Definition-time checking retains an abstract signature, the
declared facts of each parameter, and a typed body (operations, places, control flow,
receiver and argument ownership modes) for every generic free function, impl method and
let-bound polymorphic closure
([retained bodies](#arch.move-check.requirement-4),
[closures](#arch.move-check.requirement-5)). Move checking consumes that artifact
directly; it never re-runs inference or re-type-checks source AST, so even an unused
definition is checked. The design and its boundary with specialization are in
[ADR-0063](https://github.com/metel-lang/metel-docs/blob/main/architecture/decisions/adr-0063-abstract-generic-bodies.md).

Whether a value is `Copy` is decided from the retained facts
([Copy from declared bounds](#arch.move-check.requirement-8)): an unbounded parameter
is not `Copy`, a `T: Copy` parameter is, and an unknown row tail is preserved rather than
sampled as an empty record. Retained subtraction equations propagate field-wise `Copy`
from a source row to its remainder, including chains; every field-wise exception must be
among the removed labels, and a remainder's grant never proves that its source is
`Copy`. Copy heads and a `Copy` remainder compose into a `Copy` structural row, and an
unproven alternative decomposition cannot override a successful proof. Closed-source
subtraction equations determine the actual remainder fields, whose retained types decide
`Copy`. Definition templates preserve declared parameters that appear only in row facts
without adding caller-visible quantifiers, and method templates retain source names and
inherited body grants without changing call-site schemes. Borrowed `self` remains access
rather than ownership. An arithmetic or ordering operation on an unannotated parameter is
retained as an observation of its operands, not as a sampled operator
([operators](#arch.move-check.requirement-9)).

Array reads with retained `u64` indices preserve index evaluation throughout projection
chains and reject non-`Copy` moves through opaque-index places. Structural record
patterns retain typed fields, explicit discards, binding identities and owned
remainders, including unknown open tails; scrutinee inputs are evaluated once rather
than once per projected field. A named remainder consumes the source as a whole, while a
pattern without one consumes its named and explicitly discarded fields separately.
Parameter-backed open shapes require a typed row grant and an exact retained remainder
equation; unknown tails are preserved. See
[ADR-0060](https://github.com/metel-lang/metel-docs/blob/main/architecture/decisions/adr-0060-symbolic-row-ownership-witnesses.md).

### Closures

Closure environment ownership is retained separately from callable axes and preserved
through direct local aliases and nested captures. Owned closure sources carry resolved
entry types from construction, so ownership analysis consumes these explicit captures
even if they are unused or shadowed
([ADR-0062](https://github.com/metel-lang/metel-docs/blob/main/architecture/decisions/adr-0062-owned-capture-entry-types.md)).
A closure body uses its own flow state. A closure written without a capture list may
capture a still-generic value only if the definition grants `Copy`, whatever the
instantiation ([capture grant](#arch.move-check.requirement-7)). A bare alias of a
generic function (`let g := f;`) introduces no body; the function's own is analysed where
it is declared.

### Completeness

Analysis is all-or-nothing per body. When an operation or entailment cannot be decided
from the retained facts, the body is recorded as unanalysed and the run fails with
`I0011`, a distinct error from the `T0019` use-after-move diagnostic
([completeness](#arch.move-check.requirement-6)). A passing `--move-check` run has
therefore analysed every generic body, including unused and embedded-standard-library
definitions, and a test over the whole integration corpus asserts that none is left
unanalysed. There is no fallback that reconstructs a body against invented concrete
arguments ([no reconstruction](#arch.move-check.requirement-10)). Conditional variants
whose flattened method symbols collide are tracked by `LIMIT-NAME-RESOLUTION-005`.

<details>
<summary>Verifiable architecture claims</summary>

##### Requirement {#arch.move-check.requirement-1}

Move checking is off unless requested (`--move-check` / `RunOptions::move_check`). `check_graph` then rejects seven categories of move violation, reporting the first as `T0019`, and fails with `I0011` if any generic body cannot be analysed, so success means every body was checked.

| Field | Value |
|---|---|
| `status` | `implemented` |
| `owner` | `metel-frontend` |
| `specified by` | `#move-check` |
| `implements` | [`metel-frontend/src/pipeline/move_check/mod.rs::check_graph`](https://github.com/metel-lang/metel-core/blob/9a472e9538ad11a18f2f7f5a8dc3d6123967493d/metel-frontend/src/pipeline/move_check/mod.rs#L214) |
| `verified by` | [`metel-frontend/src/pipeline/move_check/tests.rs::a_by_value_method_through_a_shared_reference_is_rejected_at_the_first_call`](https://github.com/metel-lang/metel-core/blob/5586a5cdb8bda4fa8f25a51700e048c33fe28f73/metel-frontend/src/pipeline/move_check/tests.rs#L4763); [`metel-frontend/src/pipeline/move_check/tests.rs::ambiguous_aspect_method_body_is_analyzed_from_its_retained_definition`](https://github.com/metel-lang/metel-core/blob/d8cb4c3c0582a18b0fd859c8c4ec95fde74db946/metel-frontend/src/pipeline/move_check/tests.rs#L3462); [`metel-frontend/src/pipeline/move_check/tests.rs::array_element_move_is_reported`](https://github.com/metel-lang/metel-core/blob/5586a5cdb8bda4fa8f25a51700e048c33fe28f73/metel-frontend/src/pipeline/move_check/tests.rs#L3958); [`metel-frontend/src/pipeline/move_check/tests.rs::assignment_move_then_use_is_reported`](https://github.com/metel-lang/metel-core/blob/5586a5cdb8bda4fa8f25a51700e048c33fe28f73/metel-frontend/src/pipeline/move_check/tests.rs#L3618); [`metel-frontend/src/pipeline/move_check/tests.rs::borrowed_array_for_in_cannot_move_a_noncopy_element`](https://github.com/metel-lang/metel-core/blob/25e71d8966dfb6e54799ec22be9247609654a833/metel-frontend/src/pipeline/move_check/tests.rs#L4189); [`metel-frontend/src/pipeline/move_check/tests.rs::partial_move_of_drop_type_is_reported`](https://github.com/metel-lang/metel-core/blob/5586a5cdb8bda4fa8f25a51700e048c33fe28f73/metel-frontend/src/pipeline/move_check/tests.rs#L3756); [`metel-frontend/src/pipeline/move_check/tests.rs::plain_binding_of_mut_ref_then_use_is_reported`](https://github.com/metel-lang/metel-core/blob/5586a5cdb8bda4fa8f25a51700e048c33fe28f73/metel-frontend/src/pipeline/move_check/tests.rs#L4070); [`metel-frontend/src/pipeline/move_check/tests.rs::symbolic_row_forwarding_closure_is_checked_without_skipping`](https://github.com/metel-lang/metel-core/blob/8ed18533e08f605e0df6c188f1d30797fb72171f/metel-frontend/src/pipeline/move_check/tests.rs#L3372); [`metel-frontend/src/pipeline/move_check/tests.rs::symbolic_row_without_all_copy_is_still_move_only`](https://github.com/metel-lang/metel-core/blob/8ed18533e08f605e0df6c188f1d30797fb72171f/metel-frontend/src/pipeline/move_check/tests.rs#L3397); [`metel-frontend/src/pipeline/move_check/tests.rs::whole_value_use_after_partial_move_is_a_typecheck_error`](https://github.com/metel-lang/metel-core/blob/5586a5cdb8bda4fa8f25a51700e048c33fe28f73/metel-frontend/src/pipeline/move_check/tests.rs#L3729); [`metel-interpreter/src/orchestrator/mod.rs::move_checking_is_off_unless_requested`](https://github.com/metel-lang/metel-core/blob/2aa2c5729e26ccba73bcc69fe338f0941ffc4966/metel-interpreter/src/orchestrator/mod.rs#L313); [`metel-interpreter/tests/integration/sources/evaluator/move_check/01_move_then_use.toml`](https://github.com/metel-lang/metel-core/blob/2aa2c5729e26ccba73bcc69fe338f0941ffc4966/metel-interpreter/tests/integration/sources/evaluator/move_check/01_move_then_use.toml#L1); [`metel-interpreter/tests/integration/sources/evaluator/move_check/generic_row_forwarding_moves_unknown_tail.toml`](https://github.com/metel-lang/metel-core/blob/8ed18533e08f605e0df6c188f1d30797fb72171f/metel-interpreter/tests/integration/sources/evaluator/move_check/generic_row_forwarding_moves_unknown_tail.toml#L1) |
| `last_reviewed` | d8cb4c3c0582a18b0fd859c8c4ec95fde74db946 |
| `related` | RFC-0071, `#579` |

##### Requirement {#arch.move-check.requirement-2}

Places (a binding root plus a path of projections) carry no move-specific state: `place.rs` lives at the crate root, outside `move_check`, so a future borrow-check pass can analyse the same places without the two analyses disagreeing about partial moves.

| Field | Value |
|---|---|
| `status` | `implemented` |
| `owner` | `metel-frontend` |
| `specified by` | `#move-check` |
| `implements` | [`metel-frontend/src/ownership/place/mod.rs::from_expr`](https://github.com/metel-lang/metel-core/blob/dbc1ef44225cefee863befa599cf91b680768dfb/metel-frontend/src/ownership/place/mod.rs#L194) |
| `verified by` | [`metel-frontend/src/ownership/place/mod.rs::place_representation_carries_no_move_analysis_state`](https://github.com/metel-lang/metel-core/blob/853b2feb32949cce5ac62e59c7e20060c9241be0/metel-frontend/src/ownership/place/mod.rs#L249) |
| `last_reviewed` | 853b2feb32949cce5ac62e59c7e20060c9241be0 |
| `related` | RFC-0071 §9b, ADR-0035 (`TypedPlace` for assignment targets), ADR-0045 |

##### Requirement {#arch.move-check.requirement-3}

Closure capture legality holds with move checking off: type checking rejects unlisted non-`Copy` captures (`T0026`, judged at the definition when generic), consuming captures without `once` (`T0027`), mutating captures without `var` (`T0028`), and shared-access calls of mutating closures (`T0029`).

| Field | Value |
|---|---|
| `status` | `implemented` |
| `owner` | `metel-frontend`, `metel-interpreter` |
| `specified by` | `#move-check` |
| `implements` | [`metel-frontend/src/pipeline/type_checking/construction/calls.rs::construct_call`](https://github.com/metel-lang/metel-core/blob/de72649a95a5c947ac985069b692008b76a82f7e/metel-frontend/src/pipeline/type_checking/construction/calls.rs#L30); [`metel-frontend/src/pipeline/type_checking/construction/expressions.rs::verify_capture_specs`](https://github.com/metel-lang/metel-core/blob/de72649a95a5c947ac985069b692008b76a82f7e/metel-frontend/src/pipeline/type_checking/construction/expressions.rs#L148); [`metel-frontend/src/pipeline/type_checking/construction/expressions.rs::verify_closure_capture_list`](https://github.com/metel-lang/metel-core/blob/8ed18533e08f605e0df6c188f1d30797fb72171f/metel-frontend/src/pipeline/type_checking/construction/expressions.rs#L19) |
| `verified by` | [`metel-interpreter/tests/integration/sources/evaluator/closures/v0_13_0_neg_capture_list_required.toml`](https://github.com/metel-lang/metel-core/blob/2aa2c5729e26ccba73bcc69fe338f0941ffc4966/metel-interpreter/tests/integration/sources/evaluator/closures/v0_13_0_neg_capture_list_required.toml#L1); [`metel-interpreter/tests/integration/sources/evaluator/closures/v0_13_0_neg_once_required_for_consuming_body.toml`](https://github.com/metel-lang/metel-core/blob/2aa2c5729e26ccba73bcc69fe338f0941ffc4966/metel-interpreter/tests/integration/sources/evaluator/closures/v0_13_0_neg_once_required_for_consuming_body.toml#L1); [`metel-interpreter/tests/integration/sources/evaluator/closures/v0_13_0_neg_var_call_through_shared_ref.toml`](https://github.com/metel-lang/metel-core/blob/2aa2c5729e26ccba73bcc69fe338f0941ffc4966/metel-interpreter/tests/integration/sources/evaluator/closures/v0_13_0_neg_var_call_through_shared_ref.toml#L1); [`metel-interpreter/tests/integration/sources/evaluator/closures/v0_13_0_neg_var_required_for_mutating_body.toml`](https://github.com/metel-lang/metel-core/blob/2aa2c5729e26ccba73bcc69fe338f0941ffc4966/metel-interpreter/tests/integration/sources/evaluator/closures/v0_13_0_neg_var_required_for_mutating_body.toml#L1) |
| `last_reviewed` | b5e31f5afc1d13391ece5c9a3e156d5cb4b22e61 |
| `related` | ADR-0052, RFC-0050, RFC-0134, RFC-0153 |

##### Requirement {#arch.move-check.requirement-4}

Definition-time checking retains an abstract signature and typed body for every generic free function, impl method and let-bound polymorphic closure; move checking consumes them directly and never re-type-checks source AST.

| Field | Value |
|---|---|
| `status` | `implemented` |
| `owner` | `metel-frontend` |
| `specified by` | `#move-check` |
| `implements` | [`metel-frontend/src/pipeline/type_checking/handoff/abstract_signature/body.rs::prepare_abstract_body`](https://github.com/metel-lang/metel-core/blob/6469705aaeb2aefd7c60ead845b69e7b6c8dcab4/metel-frontend/src/pipeline/type_checking/handoff/abstract_signature/body.rs#L38) |
| `verified by` | [`metel-frontend/src/pipeline/move_check/tests.rs::let_polymorphic_closures_are_analyzed_from_retained_bodies`](https://github.com/metel-lang/metel-core/blob/0a53acdfab3832c712957ee03e9700f32006f025/metel-frontend/src/pipeline/move_check/tests.rs#L5216); [`metel-interpreter/tests/unit/move_check_completeness_tests.rs::every_generic_body_in_the_corpus_is_analyzed`](https://github.com/metel-lang/metel-core/blob/9a472e9538ad11a18f2f7f5a8dc3d6123967493d/metel-interpreter/tests/unit/move_check_completeness_tests.rs#L96) |
| `last_reviewed` | b5e31f5afc1d13391ece5c9a3e156d5cb4b22e61 |
| `related` | `ADR-0063`, `#273` |

##### Requirement {#arch.move-check.requirement-5}

A let-bound polymorphic closure is a generic definition: it retains an abstract signature and body keyed by its own span, while a bare alias of a generic function introduces no body and is analysed through the function itself.

| Field | Value |
|---|---|
| `status` | `implemented` |
| `owner` | `metel-frontend` |
| `specified by` | `#move-check` |
| `implements` | [`metel-frontend/src/pipeline/type_checking/construction/declarations.rs::closure_definition`](https://github.com/metel-lang/metel-core/blob/d8cb4c3c0582a18b0fd859c8c4ec95fde74db946/metel-frontend/src/pipeline/type_checking/construction/declarations.rs#L38) |
| `verified by` | [`metel-frontend/src/pipeline/move_check/tests.rs::let_polymorphic_closures_are_analyzed_from_retained_bodies`](https://github.com/metel-lang/metel-core/blob/0a53acdfab3832c712957ee03e9700f32006f025/metel-frontend/src/pipeline/move_check/tests.rs#L5216); [`metel-interpreter/tests/integration/sources/evaluator/move_check/abstract_let_polymorphic_closure.toml`](https://github.com/metel-lang/metel-core/blob/b5e31f5afc1d13391ece5c9a3e156d5cb4b22e61/metel-interpreter/tests/integration/sources/evaluator/move_check/abstract_let_polymorphic_closure.toml#L1); [`metel-interpreter/tests/integration/sources/evaluator/move_check/neg_abstract_let_polymorphic_closure_double_move.toml`](https://github.com/metel-lang/metel-core/blob/b5e31f5afc1d13391ece5c9a3e156d5cb4b22e61/metel-interpreter/tests/integration/sources/evaluator/move_check/neg_abstract_let_polymorphic_closure_double_move.toml#L1) |
| `last_reviewed` | b5e31f5afc1d13391ece5c9a3e156d5cb4b22e61 |
| `related` | `ADR-0063`, `#273` |

##### Requirement {#arch.move-check.requirement-6}

Under `--move-check`, a generic body that cannot be analysed is reported as `I0011`, an error distinct from `T0019`, so an incomplete analysis never authorizes execution and success means every body was checked.

| Field | Value |
|---|---|
| `status` | `implemented` |
| `owner` | `metel-frontend` |
| `specified by` | `#move-check` |
| `implements` | [`metel-frontend/src/pipeline/move_check/abstract_bodies.rs::analyze_generic_definition`](https://github.com/metel-lang/metel-core/blob/d8cb4c3c0582a18b0fd859c8c4ec95fde74db946/metel-frontend/src/pipeline/move_check/abstract_bodies.rs#L65) |
| `verified by` | [`metel-frontend/src/pipeline/move_check/tests.rs::analyzable_generic_bodies_pass_the_completeness_guard`](https://github.com/metel-lang/metel-core/blob/9a472e9538ad11a18f2f7f5a8dc3d6123967493d/metel-frontend/src/pipeline/move_check/tests.rs#L5205); [`metel-frontend/src/pipeline/move_check/tests.rs::incomplete_analysis_is_a_distinct_error_and_never_passes`](https://github.com/metel-lang/metel-core/blob/9a472e9538ad11a18f2f7f5a8dc3d6123967493d/metel-frontend/src/pipeline/move_check/tests.rs#L5180); [`metel-interpreter/tests/unit/move_check_completeness_tests.rs::every_generic_body_in_the_corpus_is_analyzed`](https://github.com/metel-lang/metel-core/blob/9a472e9538ad11a18f2f7f5a8dc3d6123967493d/metel-interpreter/tests/unit/move_check_completeness_tests.rs#L96) |
| `last_reviewed` | b5e31f5afc1d13391ece5c9a3e156d5cb4b22e61 |
| `related` | `ADR-0063`, `#273` |

##### Requirement {#arch.move-check.requirement-7}

A closure with no capture list may capture a still-generic value only if the definition grants `Copy`; an unbounded or inferred parameter is rejected with `T0026` at the definition, in every mode, whatever the instantiation.

| Field | Value |
|---|---|
| `status` | `implemented` |
| `owner` | `metel-frontend` |
| `specified by` | `#move-check` |
| `implements` | [`metel-frontend/src/pipeline/type_checking/mod.rs::check_implicit_capture_copy_obligations`](https://github.com/metel-lang/metel-core/blob/119862e8e95be8e850d81d66bdda0c0264364d39/metel-frontend/src/pipeline/type_checking/mod.rs#L1547) |
| `verified by` | [`metel-interpreter/tests/integration/sources/evaluator/closures/v0_14_0_generic_implicit_capture_copy_bound.toml`](https://github.com/metel-lang/metel-core/blob/b5e31f5afc1d13391ece5c9a3e156d5cb4b22e61/metel-interpreter/tests/integration/sources/evaluator/closures/v0_14_0_generic_implicit_capture_copy_bound.toml#L1); [`metel-interpreter/tests/integration/sources/evaluator/closures/v0_14_0_neg_generic_implicit_capture_declared.toml`](https://github.com/metel-lang/metel-core/blob/b5e31f5afc1d13391ece5c9a3e156d5cb4b22e61/metel-interpreter/tests/integration/sources/evaluator/closures/v0_14_0_neg_generic_implicit_capture_declared.toml#L1); [`metel-interpreter/tests/integration/sources/evaluator/closures/v0_14_0_neg_generic_implicit_capture_inferred.toml`](https://github.com/metel-lang/metel-core/blob/b5e31f5afc1d13391ece5c9a3e156d5cb4b22e61/metel-interpreter/tests/integration/sources/evaluator/closures/v0_14_0_neg_generic_implicit_capture_inferred.toml#L1) |
| `last_reviewed` | b5e31f5afc1d13391ece5c9a3e156d5cb4b22e61 |
| `related` | RFC-0050, RFC-0134, `#273` |

##### Requirement {#arch.move-check.requirement-8}

Whether a generic value is `Copy` is decided from the definition's declared facts: an unbounded parameter or unknown row tail is never assumed `Copy`, and a declared `Copy` bound or proven field-wise grant is honoured.

| Field | Value |
|---|---|
| `status` | `implemented` |
| `owner` | `metel-frontend` |
| `specified by` | `#move-check` |
| `implements` | [`metel-frontend/src/pipeline/move_check/abstract_bodies.rs::abstract_is_copy_in`](https://github.com/metel-lang/metel-core/blob/361e16a48ab475161d83d33ad52bbe6fac0c49f2/metel-frontend/src/pipeline/move_check/abstract_bodies.rs#L1105) |
| `verified by` | [`metel-frontend/src/pipeline/move_check/tests.rs::abstract_ownership_distinguishes_unknown_and_copy_row_tails`](https://github.com/metel-lang/metel-core/blob/6469705aaeb2aefd7c60ead845b69e7b6c8dcab4/metel-frontend/src/pipeline/move_check/tests.rs#L1935); [`metel-frontend/src/pipeline/move_check/tests.rs::abstract_ownership_proves_declared_conditional_copy`](https://github.com/metel-lang/metel-core/blob/6469705aaeb2aefd7c60ead845b69e7b6c8dcab4/metel-frontend/src/pipeline/move_check/tests.rs#L1655); [`metel-frontend/src/pipeline/move_check/tests.rs::abstract_ownership_retains_implicit_copy_capture_environments`](https://github.com/metel-lang/metel-core/blob/119862e8e95be8e850d81d66bdda0c0264364d39/metel-frontend/src/pipeline/move_check/tests.rs#L2264); [`metel-interpreter/tests/integration/sources/evaluator/move_check/17_unbounded_generic_body_is_checked.toml`](https://github.com/metel-lang/metel-core/blob/b5e31f5afc1d13391ece5c9a3e156d5cb4b22e61/metel-interpreter/tests/integration/sources/evaluator/move_check/17_unbounded_generic_body_is_checked.toml#L1); [`metel-interpreter/tests/integration/sources/evaluator/move_check/neg_abstract_conditional_nominal_copy.toml`](https://github.com/metel-lang/metel-core/blob/b5e31f5afc1d13391ece5c9a3e156d5cb4b22e61/metel-interpreter/tests/integration/sources/evaluator/move_check/neg_abstract_conditional_nominal_copy.toml#L1) |
| `last_reviewed` | b5e31f5afc1d13391ece5c9a3e156d5cb4b22e61 |
| `related` | ADR-0060, ADR-0063, `#273` |

##### Requirement {#arch.move-check.requirement-9}

An arithmetic or ordering operation on an unannotated parameter is retained in the abstract body without sampling an operand type, and its operands are observed rather than consumed.

| Field | Value |
|---|---|
| `status` | `implemented` |
| `owner` | `metel-frontend` |
| `specified by` | `#move-check` |
| `implements` | [`metel-frontend/src/pipeline/type_checking/handoff/abstract_signature/body.rs::binary_operator`](https://github.com/metel-lang/metel-core/blob/59afe2d56f0381072a21c6ce16a76b780f266bde/metel-frontend/src/pipeline/type_checking/handoff/abstract_signature/body.rs#L1273) |
| `verified by` | [`metel-interpreter/tests/integration/sources/evaluator/move_check/abstract_inferred_operand_arithmetic.toml`](https://github.com/metel-lang/metel-core/blob/b5e31f5afc1d13391ece5c9a3e156d5cb4b22e61/metel-interpreter/tests/integration/sources/evaluator/move_check/abstract_inferred_operand_arithmetic.toml#L1); [`metel-interpreter/tests/integration/sources/evaluator/move_check/neg_abstract_inferred_operand_double_move.toml`](https://github.com/metel-lang/metel-core/blob/b5e31f5afc1d13391ece5c9a3e156d5cb4b22e61/metel-interpreter/tests/integration/sources/evaluator/move_check/neg_abstract_inferred_operand_double_move.toml#L1) |
| `last_reviewed` | b5e31f5afc1d13391ece5c9a3e156d5cb4b22e61 |
| `related` | RFC-0173, ADR-0063, `#273` |

##### Requirement {#arch.move-check.requirement-10}

Move checking never reconstructs a generic body against invented concrete arguments: with the scheme environment removed, retained bodies are still analysed and the result is unchanged.

| Field | Value |
|---|---|
| `status` | `implemented` |
| `owner` | `metel-frontend` |
| `specified by` | `#move-check` |
| `implements` | [`metel-frontend/src/pipeline/move_check/abstract_bodies.rs::analyze_generic_definition`](https://github.com/metel-lang/metel-core/blob/d8cb4c3c0582a18b0fd859c8c4ec95fde74db946/metel-frontend/src/pipeline/move_check/abstract_bodies.rs#L65) |
| `verified by` | [`metel-frontend/src/pipeline/move_check/tests.rs::abstract_ownership_retains_implicit_copy_capture_environments`](https://github.com/metel-lang/metel-core/blob/119862e8e95be8e850d81d66bdda0c0264364d39/metel-frontend/src/pipeline/move_check/tests.rs#L2264); [`metel-frontend/src/pipeline/move_check/tests.rs::let_polymorphic_closures_are_analyzed_from_retained_bodies`](https://github.com/metel-lang/metel-core/blob/0a53acdfab3832c712957ee03e9700f32006f025/metel-frontend/src/pipeline/move_check/tests.rs#L5216); [`metel-interpreter/tests/unit/move_check_completeness_tests.rs::every_generic_body_in_the_corpus_is_analyzed`](https://github.com/metel-lang/metel-core/blob/9a472e9538ad11a18f2f7f5a8dc3d6123967493d/metel-interpreter/tests/unit/move_check_completeness_tests.rs#L96) |
| `last_reviewed` | b5e31f5afc1d13391ece5c9a3e156d5cb4b22e61 |
| `related` | ADR-0063, `#273` |

</details>

## Known limitations

<!-- records:limitations -->
