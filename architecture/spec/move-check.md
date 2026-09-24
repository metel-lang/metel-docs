# Move Check {#move-check}

An opt-in validation pass over the typed module graph, rejecting use-after-move. Verified directly against `pipeline.rs` and the CLI's `clap` argument (not assumed from prior documentation): `RunOptions`/`main.rs`'s `move_check: bool` derive/default to `false`, and every one of `pipeline.rs`'s three call sites gates the pass behind `if options.move_check`. Owning crate: `metel-frontend`. Defined in `move_check/` and `place.rs` (the addressable lvalue-path representation move check shares with the typechecker).

## Model

Move checking is a consumer of typed structure, not a second type checker. When
enabled, it follows values through [places](#arch.move-check.requirement-2)—a root
binding plus projections—and records the state transitions that make a later use
illegal. This makes partial moves explainable: consuming one field is different from
consuming the whole value, and `Drop` or reference rules can constrain either form.

The general pass is still opt-in, but closure capture safety is language behaviour
today. Its capture-list and multiplicity checks run unconditionally during
construction ([closure captures](#arch.move-check.requirement-3)), so a program cannot
evade a closure ownership error merely by omitting `--move-check`.

<details>
<summary>Verifiable architecture claims</summary>

##### Requirement {#arch.move-check.requirement-1}

Move checking is off unless requested (`--move-check` / `RunOptions::move_check`). `check_graph` then rejects seven categories of move violation, reporting the first as `T0019`, and reports generic bodies it cannot check as `unchecked_generic_bodies`, not silently accepted.

| Field | Value |
|---|---|
| `status` | `implemented` |
| `owner` | `metel-frontend` |
| `specified by` | `#move-check` |
| `implements` | [`metel-frontend/src/move_check/mod.rs::check_graph`](https://github.com/metel-lang/metel-core/blob/4155d94ccbc5b1657799f3537515610f3bb139c3/metel-frontend/src/move_check/mod.rs#L158) |
| `verified by` | [`metel-frontend/src/move_check/mod.rs::a_by_value_method_through_a_shared_reference_is_rejected_at_the_first_call`](https://github.com/metel-lang/metel-core/blob/4155d94ccbc5b1657799f3537515610f3bb139c3/metel-frontend/src/move_check/mod.rs#L4092); [`metel-frontend/src/move_check/mod.rs::array_element_move_is_reported`](https://github.com/metel-lang/metel-core/blob/4155d94ccbc5b1657799f3537515610f3bb139c3/metel-frontend/src/move_check/mod.rs#L3287); [`metel-frontend/src/move_check/mod.rs::assignment_move_then_use_is_reported`](https://github.com/metel-lang/metel-core/blob/4155d94ccbc5b1657799f3537515610f3bb139c3/metel-frontend/src/move_check/mod.rs#L2961); [`metel-frontend/src/move_check/mod.rs::borrowed_array_for_in_cannot_move_a_noncopy_element`](https://github.com/metel-lang/metel-core/blob/4155d94ccbc5b1657799f3537515610f3bb139c3/metel-frontend/src/move_check/mod.rs#L3518); [`metel-frontend/src/move_check/mod.rs::partial_move_of_drop_type_is_reported`](https://github.com/metel-lang/metel-core/blob/4155d94ccbc5b1657799f3537515610f3bb139c3/metel-frontend/src/move_check/mod.rs#L3099); [`metel-frontend/src/move_check/mod.rs::plain_binding_of_mut_ref_then_use_is_reported`](https://github.com/metel-lang/metel-core/blob/4155d94ccbc5b1657799f3537515610f3bb139c3/metel-frontend/src/move_check/mod.rs#L3399); [`metel-frontend/src/move_check/mod.rs::unchecked_generic_body_is_reported_to_compiler_callers`](https://github.com/metel-lang/metel-core/blob/4155d94ccbc5b1657799f3537515610f3bb139c3/metel-frontend/src/move_check/mod.rs#L2857); [`metel-frontend/src/move_check/mod.rs::whole_value_use_after_partial_move_is_a_typecheck_error`](https://github.com/metel-lang/metel-core/blob/4155d94ccbc5b1657799f3537515610f3bb139c3/metel-frontend/src/move_check/mod.rs#L3072); [`metel-interpreter/src/pipeline.rs::move_checking_is_off_unless_requested`](https://github.com/metel-lang/metel-core/blob/4155d94ccbc5b1657799f3537515610f3bb139c3/metel-interpreter/src/pipeline.rs#L323); [`metel-interpreter/tests/integration/sources/evaluator/move_check/01_move_then_use.toml`](https://github.com/metel-lang/metel-core/blob/4155d94ccbc5b1657799f3537515610f3bb139c3/metel-interpreter/tests/integration/sources/evaluator/move_check/01_move_then_use.toml#L1) |
| `last_reviewed` | 2aa2c5729e26ccba73bcc69fe338f0941ffc4966 |
| `related` | RFC-0071, `#579` |

##### Requirement {#arch.move-check.requirement-2}

Places (a binding root plus a path of projections) carry no move-specific state: `place.rs` lives at the crate root, outside `move_check`, so a future borrow-check pass can analyse the same places without the two analyses disagreeing about partial moves.

| Field | Value |
|---|---|
| `status` | `implemented` |
| `owner` | `metel-frontend` |
| `specified by` | `#move-check` |
| `implements` | [`metel-frontend/src/place.rs::from_expr`](https://github.com/metel-lang/metel-core/blob/4155d94ccbc5b1657799f3537515610f3bb139c3/metel-frontend/src/place.rs#L194) |
| `verified by` | [`metel-frontend/src/place.rs::place_representation_carries_no_move_analysis_state`](https://github.com/metel-lang/metel-core/blob/4155d94ccbc5b1657799f3537515610f3bb139c3/metel-frontend/src/place.rs#L321) |
| `last_reviewed` | 2aa2c5729e26ccba73bcc69fe338f0941ffc4966 |
| `related` | RFC-0071 §9b, ADR-0035 (`TypedPlace` for assignment targets), ADR-0045 |

##### Requirement {#arch.move-check.requirement-3}

Closure capture legality is enforced even with move checking off: construction rejects unlisted non-`Copy` captures (`T0026`), consuming captures without `once` (`T0027`), mutating captures without `var` (`T0028`), and mutating closures called through shared access (`T0029`).

| Field | Value |
|---|---|
| `status` | `implemented` |
| `owner` | `metel-frontend`, `metel-interpreter` |
| `specified by` | `#move-check` |
| `implements` | [`metel-frontend/src/typechecker/construction/calls.rs::construct_call`](https://github.com/metel-lang/metel-core/blob/4155d94ccbc5b1657799f3537515610f3bb139c3/metel-frontend/src/typechecker/construction/calls.rs#L30); [`metel-frontend/src/typechecker/construction/expressions.rs::verify_capture_specs`](https://github.com/metel-lang/metel-core/blob/4155d94ccbc5b1657799f3537515610f3bb139c3/metel-frontend/src/typechecker/construction/expressions.rs#L454); [`metel-frontend/src/typechecker/construction/expressions.rs::verify_closure_capture_list`](https://github.com/metel-lang/metel-core/blob/4155d94ccbc5b1657799f3537515610f3bb139c3/metel-frontend/src/typechecker/construction/expressions.rs#L328) |
| `verified by` | [`metel-interpreter/tests/integration/sources/evaluator/closures/v0_13_0_neg_capture_list_required.toml`](https://github.com/metel-lang/metel-core/blob/4155d94ccbc5b1657799f3537515610f3bb139c3/metel-interpreter/tests/integration/sources/evaluator/closures/v0_13_0_neg_capture_list_required.toml#L1); [`metel-interpreter/tests/integration/sources/evaluator/closures/v0_13_0_neg_once_required_for_consuming_body.toml`](https://github.com/metel-lang/metel-core/blob/4155d94ccbc5b1657799f3537515610f3bb139c3/metel-interpreter/tests/integration/sources/evaluator/closures/v0_13_0_neg_once_required_for_consuming_body.toml#L1); [`metel-interpreter/tests/integration/sources/evaluator/closures/v0_13_0_neg_var_call_through_shared_ref.toml`](https://github.com/metel-lang/metel-core/blob/4155d94ccbc5b1657799f3537515610f3bb139c3/metel-interpreter/tests/integration/sources/evaluator/closures/v0_13_0_neg_var_call_through_shared_ref.toml#L1); [`metel-interpreter/tests/integration/sources/evaluator/closures/v0_13_0_neg_var_required_for_mutating_body.toml`](https://github.com/metel-lang/metel-core/blob/4155d94ccbc5b1657799f3537515610f3bb139c3/metel-interpreter/tests/integration/sources/evaluator/closures/v0_13_0_neg_var_required_for_mutating_body.toml#L1) |
| `last_reviewed` | 2aa2c5729e26ccba73bcc69fe338f0941ffc4966 |
| `related` | ADR-0052, RFC-0050, RFC-0134, RFC-0153 |

</details>

## Known limitations

<!-- records:limitations -->
