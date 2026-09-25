# Coherence {#coherence}

A standalone validation pass between path normalization and type checking: it resolves aspect-impl type/aspect *names* to their declaring module using only `ResolvedNames` (no inferred types needed) and rejects two categories of illegal impl. Owning crate: `metel-frontend`. Defined in `coherence.rs`.

## Model

Coherence answers a deliberately narrow question before inference adds any
implementation-specific facts: may these aspect implementations coexist at all?
An implementation is allowed only when the module owns one side of the relation;
otherwise downstream type checking would make independently-authored modules change
each other's meaning. That ownership boundary is the [orphan rule](#arch.coherence.requirement-1).

Within the implementations that are allowed to exist, the pass rejects pairs that
could apply to the same type. It reasons about declared bounds and canonical type
parameters, rather than inferred types, so the [overlap rule](#arch.coherence.requirement-2)
is stable regardless of which call sites happen to be checked.

<details>
<summary>Verifiable architecture claims</summary>

##### Requirement {#arch.coherence.requirement-1}

The orphan rule (`T0014`): an aspect impl must be local to the aspect's declaring module or the implementing type's; an impl of a foreign aspect on a foreign type, including a negative or blanket/conditional impl with no local anchor, is rejected.

| Field | Value |
|---|---|
| `status` | `implemented` |
| `owner` | `metel-frontend` |
| `specified by` | `#coherence` |
| `implements` | [`metel-frontend/src/pipeline/coherence/mod.rs::check`](https://github.com/metel-lang/metel-core/blob/482a47de2a50db592c02804b14155c2310a76bb5/metel-frontend/src/pipeline/coherence/mod.rs#L660) |
| `verified by` | [`metel-interpreter/tests/integration/sources/typechecking/aspects/bare_parameter_blanket_foreign_aspect_is_orphan/test.toml`](https://github.com/metel-lang/metel-core/blob/482a47de2a50db592c02804b14155c2310a76bb5/metel-interpreter/tests/integration/sources/typechecking/aspects/bare_parameter_blanket_foreign_aspect_is_orphan/test.toml#L1); [`metel-interpreter/tests/integration/sources/typechecking/aspects/conditional_impl_orphan_violation/test.toml`](https://github.com/metel-lang/metel-core/blob/482a47de2a50db592c02804b14155c2310a76bb5/metel-interpreter/tests/integration/sources/typechecking/aspects/conditional_impl_orphan_violation/test.toml#L1); [`metel-interpreter/tests/integration/sources/typechecking/aspects/negative_impl_orphan_violation/test.toml`](https://github.com/metel-lang/metel-core/blob/482a47de2a50db592c02804b14155c2310a76bb5/metel-interpreter/tests/integration/sources/typechecking/aspects/negative_impl_orphan_violation/test.toml#L1); [`metel-interpreter/tests/integration/sources/typechecking/aspects/orphan_impl_cross_module_violation/test.toml`](https://github.com/metel-lang/metel-core/blob/482a47de2a50db592c02804b14155c2310a76bb5/metel-interpreter/tests/integration/sources/typechecking/aspects/orphan_impl_cross_module_violation/test.toml#L1) |
| `last_reviewed` | 2c95c6d9c5f131d86fa08889153355b451e12c9e |
| `related` | RFC-0060, `#238`, ADR-0042, RFC-0036 |

##### Requirement {#arch.coherence.requirement-2}

Overlap detection (`T0015`): two impls whose coverage overlaps conflict unless provably disjoint, decided by `scoped_type_param_bounds` (negation disjointness, RFC-0060 §3.1; unconditional-vs-conditional, §3.2) over impl-scoped `CanonicalType::TypeParam`s.

| Field | Value |
|---|---|
| `status` | `implemented` |
| `owner` | `metel-frontend` |
| `specified by` | `#coherence` |
| `implements` | [`metel-frontend/src/pipeline/coherence/mod.rs::provably_disjoint`](https://github.com/metel-lang/metel-core/blob/482a47de2a50db592c02804b14155c2310a76bb5/metel-frontend/src/pipeline/coherence/mod.rs#L364) |
| `verified by` | [`metel-interpreter/tests/integration/sources/typechecking/aspects/blanket_vs_concrete_impl_conflict/test.toml`](https://github.com/metel-lang/metel-core/blob/482a47de2a50db592c02804b14155c2310a76bb5/metel-interpreter/tests/integration/sources/typechecking/aspects/blanket_vs_concrete_impl_conflict/test.toml#L1); [`metel-interpreter/tests/integration/sources/typechecking/aspects/conditional_impl_negation_disjoint_accepted/test.toml`](https://github.com/metel-lang/metel-core/blob/482a47de2a50db592c02804b14155c2310a76bb5/metel-interpreter/tests/integration/sources/typechecking/aspects/conditional_impl_negation_disjoint_accepted/test.toml#L1); [`metel-interpreter/tests/integration/sources/typechecking/aspects/conditional_vs_unconditional_impl_conflict/test.toml`](https://github.com/metel-lang/metel-core/blob/482a47de2a50db592c02804b14155c2310a76bb5/metel-interpreter/tests/integration/sources/typechecking/aspects/conditional_vs_unconditional_impl_conflict/test.toml#L1); [`metel-interpreter/tests/integration/sources/typechecking/aspects/conflicting_impl_same_target/test.toml`](https://github.com/metel-lang/metel-core/blob/482a47de2a50db592c02804b14155c2310a76bb5/metel-interpreter/tests/integration/sources/typechecking/aspects/conflicting_impl_same_target/test.toml#L1); [`metel-interpreter/tests/integration/sources/typechecking/aspects/neg_26_bare_parameter_blanket_overlap.toml`](https://github.com/metel-lang/metel-core/blob/482a47de2a50db592c02804b14155c2310a76bb5/metel-interpreter/tests/integration/sources/typechecking/aspects/neg_26_bare_parameter_blanket_overlap.toml#L1) |
| `last_reviewed` | 2aa2c5729e26ccba73bcc69fe338f0941ffc4966 |
| `related` | RFC-0060 §3.1/§3.2, `#238`, ADR-0042 |

</details>

## Known limitations

<!-- records:limitations -->
