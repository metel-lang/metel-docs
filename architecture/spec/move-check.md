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
| `implements` | [`metel-frontend/src/move_check/mod.rs::whole_use_of_narrowed_value_is_intact`](https://github.com/metel-lang/metel-core/blob/22f1104b6b7e8cc50978fd429537ecfd4267c336/metel-frontend/src/move_check/mod.rs#L56) |
| `verified by` | [`metel-frontend/src/move_check/mod.rs::assignment_move_then_use_is_reported`](https://github.com/metel-lang/metel-core/blob/22f1104b6b7e8cc50978fd429537ecfd4267c336/metel-frontend/src/move_check/mod.rs#L3082) |
| `last_reviewed` | 2ae8fae97336bfe87d459103ad85d8fecbbab4ca |
| `related` | RFC-0071, `#579` |

##### Requirement {#arch.move-check.requirement-2}

Places (the syntactic locations a program can name — a binding root plus a path of projections) are analysis-neutral: `place.rs` carries no move-specific state and makes no move-specific assumption. It lives at the crate root, not inside `move_check`, specifically so a future borrow-check pass can run a second analysis over the *same* places without rebuilding them and without the two analyses disagreeing about partial moves — policy lives with each analysis, not with the place representation itself.

| Field | Value |
|---|---|
| `status` | `implemented` |
| `owner` | `metel-frontend` |
| `specified by` | `#move-check` |
| `implements` | [`metel-frontend/src/place.rs::field`](https://github.com/metel-lang/metel-core/blob/22f1104b6b7e8cc50978fd429537ecfd4267c336/metel-frontend/src/place.rs#L49) |
| `verified by` | [`metel-interpreter/tests/integration/sources/evaluator/move_check/02_partial_move_used_as_whole.toml`](https://github.com/metel-lang/metel-core/blob/22f1104b6b7e8cc50978fd429537ecfd4267c336/metel-interpreter/tests/integration/sources/evaluator/move_check/02_partial_move_used_as_whole.toml#L1) |
| `last_reviewed` | 2ae8fae97336bfe87d459103ad85d8fecbbab4ca |
| `related` | RFC-0071 §9b, ADR-0035 (`TypedPlace` for assignment targets), ADR-0045 |

##### Requirement {#arch.move-check.requirement-3}

Closure capture legality is enforced even while the general move-check gate remains opt-in: construction validates capture lists and closure multiplicity/mutation qualifiers, rejecting unlisted non-`Copy` captures (`T0026`), consuming captures without `once` (`T0027`), mutating captures without `var` (`T0028`), and calls to mutating closures through shared access (`T0029`). The ordinary move checker reuses the same closure and place concepts when its wider gate is enabled.

| Field | Value |
|---|---|
| `status` | `implemented` |
| `owner` | `metel-frontend`, `metel-interpreter` |
| `specified by` | `#move-check` |
| `implements` | [`metel-frontend/src/typechecker/construction/expressions.rs::capture_name`](https://github.com/metel-lang/metel-core/blob/22f1104b6b7e8cc50978fd429537ecfd4267c336/metel-frontend/src/typechecker/construction/expressions.rs#L18) |
| `verified by` | [`metel-interpreter/tests/integration/sources/evaluator/move_check/06_array_element_move_is_banned.toml`](https://github.com/metel-lang/metel-core/blob/22f1104b6b7e8cc50978fd429537ecfd4267c336/metel-interpreter/tests/integration/sources/evaluator/move_check/06_array_element_move_is_banned.toml#L1) |
| `last_reviewed` | 8b844c9117d5c6a730882aeaf521184c3055eb2f |
| `related` | ADR-0052, RFC-0050, RFC-0134, RFC-0153 |

</details>

## Known limitations

`LIMIT-*` records are the authoritative inventory of known boundaries for this
section. They carry the impact, owner, disposition, and review point; the
Atlas limitations view projects the same records rather than duplicating them.

### Active records

- [`LIMIT-MOVE-CHECK-001`](../limitations/limit-move-check-001.md) — closure move-check is always-on while general move-check stays opt-in (a documented temporary asymmetry).

### Resolved records

No resolved `LIMIT-*` records are currently recorded for this section.
