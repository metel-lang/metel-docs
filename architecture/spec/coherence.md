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

The orphan rule (`T0014`): an aspect implementation must be local to either the aspect's declaring module or the implementing type's declaring module. An impl for a foreign aspect on a foreign type — including a negative (`!Aspect`) impl or a blanket/conditional generic impl with no concrete local anchor — is rejected.

| Field | Value |
|---|---|
| `status` | `implemented` |
| `owner` | `metel-frontend` |
| `specified by` | `#coherence` |
| `implements` | _Exempt; see exemption below._ |
| `verified by` | _Exempt; see exemption below._ |
| `implements exemption` | rationale: backward implementation citation migration is pending; owner: Architecture maintainers; review: 2026-12-18 |
| `verification exemption` | rationale: backward verification citation migration is pending; owner: Architecture maintainers; review: 2026-12-18 |
| `related` | RFC-0060, `#238`, ADR-0042, RFC-0036 |

##### Requirement {#arch.coherence.requirement-2}

Overlap detection (`T0015`): two impls whose type/aspect coverage overlaps conflict unless provably disjoint. Disjointness is decided via `scoped_type_param_bounds` — negation disjointness (RFC-0060 §3.1) and unconditional-vs-conditional conflict (§3.2) — using `CanonicalType::TypeParam` to represent impl-scoped type variables, not inferred types.

| Field | Value |
|---|---|
| `status` | `implemented` |
| `owner` | `metel-frontend` |
| `specified by` | `#coherence` |
| `implements` | _Exempt; see exemption below._ |
| `verified by` | _Exempt; see exemption below._ |
| `implements exemption` | rationale: backward implementation citation migration is pending; owner: Architecture maintainers; review: 2026-12-18 |
| `verification exemption` | rationale: backward verification citation migration is pending; owner: Architecture maintainers; review: 2026-12-18 |
| `related` | RFC-0060 §3.1/§3.2, `#238`, ADR-0042 |

</details>

## Known limitations

`LIMIT-*` records are the authoritative inventory of known boundaries for this
section. They carry the impact, owner, disposition, and review point; the
Atlas limitations view projects the same records rather than duplicating them.

### Active records

No active `LIMIT-*` records are currently recorded for this section. This is
a current inventory, not a claim of complete coverage.

### Resolved records

No resolved `LIMIT-*` records are currently recorded for this section.
