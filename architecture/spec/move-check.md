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

Move checking is off by default and runs only when explicitly requested (the `--move-check` CLI flag / `RunOptions::move_check`). When it runs, `check_graph` walks a `TypedModuleGraph` and rejects seven categories of violation — `UseAfterMove`, `PartialMoveUsedAsWhole`, `PartialMoveOfDropType`, `ArrayElementMove`, `BorrowedArrayElementMove`, `MovedMutReferenceWithoutReborrow`, `MoveOutOfReference` — reporting the first as `T0019`. A generic body whose bound-satisfaction can't be checked is not silently accepted; it's collected as `unchecked_generic_bodies` in the report.

| Field | Value |
|---|---|
| `status` | `implemented` |
| `owner` | `metel-frontend` |
| `specified by` | `#move-check` |
| `implements` | [`metel-frontend/src/move_check/mod.rs::check_graph`](https://github.com/metel-lang/metel-core/blob/2aa2c5729e26ccba73bcc69fe338f0941ffc4966/metel-frontend/src/move_check/mod.rs#L158) |
| `verified by` | [`metel-frontend/src/move_check/mod.rs::a_by_value_method_through_a_shared_reference_is_rejected_at_the_first_call`](https://github.com/metel-lang/metel-core/blob/2aa2c5729e26ccba73bcc69fe338f0941ffc4966/metel-frontend/src/move_check/mod.rs#L4214); [`metel-frontend/src/move_check/mod.rs::array_element_move_is_reported`](https://github.com/metel-lang/metel-core/blob/2aa2c5729e26ccba73bcc69fe338f0941ffc4966/metel-frontend/src/move_check/mod.rs#L3409); [`metel-frontend/src/move_check/mod.rs::assignment_move_then_use_is_reported`](https://github.com/metel-lang/metel-core/blob/2aa2c5729e26ccba73bcc69fe338f0941ffc4966/metel-frontend/src/move_check/mod.rs#L3083); [`metel-frontend/src/move_check/mod.rs::borrowed_array_for_in_cannot_move_a_noncopy_element`](https://github.com/metel-lang/metel-core/blob/2aa2c5729e26ccba73bcc69fe338f0941ffc4966/metel-frontend/src/move_check/mod.rs#L3640); [`metel-frontend/src/move_check/mod.rs::partial_move_of_drop_type_is_reported`](https://github.com/metel-lang/metel-core/blob/2aa2c5729e26ccba73bcc69fe338f0941ffc4966/metel-frontend/src/move_check/mod.rs#L3221); [`metel-frontend/src/move_check/mod.rs::plain_binding_of_mut_ref_then_use_is_reported`](https://github.com/metel-lang/metel-core/blob/2aa2c5729e26ccba73bcc69fe338f0941ffc4966/metel-frontend/src/move_check/mod.rs#L3521); [`metel-frontend/src/move_check/mod.rs::unchecked_generic_body_is_reported_to_compiler_callers`](https://github.com/metel-lang/metel-core/blob/2aa2c5729e26ccba73bcc69fe338f0941ffc4966/metel-frontend/src/move_check/mod.rs#L2979); [`metel-frontend/src/move_check/mod.rs::whole_value_use_after_partial_move_is_a_typecheck_error`](https://github.com/metel-lang/metel-core/blob/2aa2c5729e26ccba73bcc69fe338f0941ffc4966/metel-frontend/src/move_check/mod.rs#L3194); [`metel-interpreter/src/pipeline.rs::move_checking_is_off_unless_requested`](https://github.com/metel-lang/metel-core/blob/2aa2c5729e26ccba73bcc69fe338f0941ffc4966/metel-interpreter/src/pipeline.rs#L326); [`metel-interpreter/tests/integration/sources/evaluator/move_check/01_move_then_use.toml`](https://github.com/metel-lang/metel-core/blob/2aa2c5729e26ccba73bcc69fe338f0941ffc4966/metel-interpreter/tests/integration/sources/evaluator/move_check/01_move_then_use.toml#L1) |
| `last_reviewed` | 2aa2c5729e26ccba73bcc69fe338f0941ffc4966 |
| `related` | RFC-0071, `#579` |

##### Requirement {#arch.move-check.requirement-2}

Places (the syntactic locations a program can name — a binding root plus a path of projections) are analysis-neutral: `place.rs` carries no move-specific state and makes no move-specific assumption. It lives at the crate root, not inside `move_check`, specifically so a future borrow-check pass can run a second analysis over the *same* places without rebuilding them and without the two analyses disagreeing about partial moves — policy lives with each analysis, not with the place representation itself.

| Field | Value |
|---|---|
| `status` | `implemented` |
| `owner` | `metel-frontend` |
| `specified by` | `#move-check` |
| `implements` | [`metel-frontend/src/place.rs::from_expr`](https://github.com/metel-lang/metel-core/blob/2aa2c5729e26ccba73bcc69fe338f0941ffc4966/metel-frontend/src/place.rs#L194) |
| `verified by` | [`metel-frontend/src/place.rs::place_representation_carries_no_move_analysis_state`](https://github.com/metel-lang/metel-core/blob/2aa2c5729e26ccba73bcc69fe338f0941ffc4966/metel-frontend/src/place.rs#L321) |
| `last_reviewed` | 2aa2c5729e26ccba73bcc69fe338f0941ffc4966 |
| `related` | RFC-0071 §9b, ADR-0035 (`TypedPlace` for assignment targets), ADR-0045 |

##### Requirement {#arch.move-check.requirement-3}

Closure capture legality is enforced even while the general move-check gate remains opt-in: construction validates capture lists and closure multiplicity/mutation qualifiers, rejecting unlisted non-`Copy` captures (`T0026`), consuming captures without `once` (`T0027`), mutating captures without `var` (`T0028`), and calls to mutating closures through shared access (`T0029`). The ordinary move checker reuses the same closure and place concepts when its wider gate is enabled.

| Field | Value |
|---|---|
| `status` | `implemented` |
| `owner` | `metel-frontend`, `metel-interpreter` |
| `specified by` | `#move-check` |
| `implements` | [`metel-frontend/src/typechecker/construction/calls.rs::construct_call`](https://github.com/metel-lang/metel-core/blob/2aa2c5729e26ccba73bcc69fe338f0941ffc4966/metel-frontend/src/typechecker/construction/calls.rs#L30); [`metel-frontend/src/typechecker/construction/expressions.rs::verify_capture_specs`](https://github.com/metel-lang/metel-core/blob/2aa2c5729e26ccba73bcc69fe338f0941ffc4966/metel-frontend/src/typechecker/construction/expressions.rs#L454); [`metel-frontend/src/typechecker/construction/expressions.rs::verify_closure_capture_list`](https://github.com/metel-lang/metel-core/blob/2aa2c5729e26ccba73bcc69fe338f0941ffc4966/metel-frontend/src/typechecker/construction/expressions.rs#L328) |
| `verified by` | [`metel-interpreter/tests/integration/sources/evaluator/closures/v0_13_0_neg_capture_list_required.toml`](https://github.com/metel-lang/metel-core/blob/2aa2c5729e26ccba73bcc69fe338f0941ffc4966/metel-interpreter/tests/integration/sources/evaluator/closures/v0_13_0_neg_capture_list_required.toml#L1); [`metel-interpreter/tests/integration/sources/evaluator/closures/v0_13_0_neg_once_required_for_consuming_body.toml`](https://github.com/metel-lang/metel-core/blob/2aa2c5729e26ccba73bcc69fe338f0941ffc4966/metel-interpreter/tests/integration/sources/evaluator/closures/v0_13_0_neg_once_required_for_consuming_body.toml#L1); [`metel-interpreter/tests/integration/sources/evaluator/closures/v0_13_0_neg_var_call_through_shared_ref.toml`](https://github.com/metel-lang/metel-core/blob/2aa2c5729e26ccba73bcc69fe338f0941ffc4966/metel-interpreter/tests/integration/sources/evaluator/closures/v0_13_0_neg_var_call_through_shared_ref.toml#L1); [`metel-interpreter/tests/integration/sources/evaluator/closures/v0_13_0_neg_var_required_for_mutating_body.toml`](https://github.com/metel-lang/metel-core/blob/2aa2c5729e26ccba73bcc69fe338f0941ffc4966/metel-interpreter/tests/integration/sources/evaluator/closures/v0_13_0_neg_var_required_for_mutating_body.toml#L1) |
| `last_reviewed` | 2aa2c5729e26ccba73bcc69fe338f0941ffc4966 |
| `related` | ADR-0052, RFC-0050, RFC-0134, RFC-0153 |

</details>

## Known limitations

`LIMIT-*` records are the authoritative inventory of known boundaries for this
section. They carry the impact, owner, disposition, and review point; the
Atlas limitations view projects the same records rather than duplicating them.

### Active records

- [`LIMIT-MOVE-CHECK-001`](../limitations/limit-move-check-001.md) — closure move-check is always-on while general move-check stays opt-in (a documented temporary asymmetry).
- [`LIMIT-MOVE-CHECK-002`](../limitations/limit-move-check-002.md) — move-check skips generic bodies that read a row-bound field or use some bound methods, so a use-after-move there passes with only a warning (`#1226`).

### Resolved records

No resolved `LIMIT-*` records are currently recorded for this section.
