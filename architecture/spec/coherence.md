# Coherence {#coherence}

A standalone validation pass between path normalization and type checking: it resolves aspect-impl type/aspect *names* to their declaring module using only `ResolvedNames` (no inferred types needed) and rejects two categories of illegal impl. Owning crate: `metel-frontend`. Defined in `coherence.rs`.

##### Requirement {#arch.coherence.requirement-1}

The orphan rule (`T0014`): an aspect implementation must be local to either the aspect's declaring module or the implementing type's declaring module. An impl for a foreign aspect on a foreign type — including a negative (`!Aspect`) impl or a blanket/conditional generic impl with no concrete local anchor — is rejected.

| Field | Value |
|---|---|
| `status` | `implemented` |
| `owner` | `metel-frontend` |
| `specified by` | `#coherence` |
| `implements` | `metel-frontend/src/coherence.rs` (`check`) |
| `verified by` | integration fixtures `metel-interpreter/tests/integration/sources/typechecking/aspects/bare_parameter_blanket_foreign_aspect_is_orphan`, `orphan_impl_cross_module_violation`, `negative_impl_orphan_violation` |
| `related` | RFC-0060, `#238`, ADR-0042, RFC-0036 |

##### Requirement {#arch.coherence.requirement-2}

Overlap detection (`T0015`): two impls whose type/aspect coverage overlaps conflict unless provably disjoint. Disjointness is decided via `scoped_type_param_bounds` — negation disjointness (RFC-0060 §3.1) and unconditional-vs-conditional conflict (§3.2) — using `CanonicalType::TypeParam` to represent impl-scoped type variables, not inferred types.

| Field | Value |
|---|---|
| `status` | `implemented` |
| `owner` | `metel-frontend` |
| `specified by` | `#coherence` |
| `implements` | `metel-frontend/src/coherence.rs` (`check`, `provably_disjoint`) |
| `verified by` | integration fixtures `metel-interpreter/tests/integration/sources/typechecking/aspects/blanket_vs_concrete_impl_conflict`, `conditional_vs_unconditional_impl_conflict`, `conditional_impl_different_letters_overlap`, `conditional_impl_non_disjoint_rejected`, `conflicting_impl_same_target` |
| `related` | RFC-0060 §3.1/§3.2, `#238`, ADR-0042 |

## Known limitations

None recorded yet for this section — `#1161` (extracting `LIMIT-*` records from the existing ADR corpus) runs next in this chain and will file any that apply here.
