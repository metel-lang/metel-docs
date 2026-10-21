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
| `implements` | _Generated at publish._ |
| `verified by` | _Generated at publish._ |
| `last_reviewed` | 2dfbafb950a84ea11b259a1f9e4bc1e964cfaf96 |
| `related` | RFC-0060, `#238`, ADR-0042, RFC-0036 |

##### Requirement {#arch.coherence.requirement-2}

Overlap detection (`T0015`): two impls whose coverage overlaps conflict unless provably disjoint, decided over impl-scoped `CanonicalType::TypeParam`s by `scoped_type_param_bounds` (negation, RFC-0060 §3.1; unconditional-vs-conditional, §3.2; row presence/absence or type contradiction, RFC-0121 §3).

| Field | Value |
|---|---|
| `status` | `implemented` |
| `owner` | `metel-frontend` |
| `specified by` | `#coherence` |
| `implements` | _Generated at publish._ |
| `verified by` | _Generated at publish._ |
| `last_reviewed` | 985bce0fa797032e108a0c567d67206c39b8fcb5 |
| `related` | RFC-0060 §3.1/§3.2, `#238`, ADR-0042 |

</details>

## Known limitations

<!-- records:limitations -->
