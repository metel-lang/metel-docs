# Elaboration {#elaboration}

The pass between type checking and evaluation: it resolves method-call dispatch statically wherever possible, so the evaluator can skip a runtime aspect-registry lookup at those call sites. Owning crate: `metel-frontend`. Defined in `elaborator/`. See ADR-0037.

## Model

Typing establishes what a receiver can do; elaboration turns that fact into an
execution decision. A call whose receiver and selected implementation are known
becomes an inherent or aspect dispatch, carrying the aspect identity where relevant.
The evaluator consumes that decision rather than repeating semantic selection. Calls
that genuinely lack enough type information remain dynamic, which keeps the boundary
explicit instead of making the runtime guess. The checkable form of this contract is
the [dispatch requirement](#arch.elaboration.requirement-1).

<details>
<summary>Verifiable architecture claims</summary>

##### Requirement {#arch.elaboration.requirement-1}

Elaboration resolves each method call's `dispatch` from `Dynamic` to `Aspect { aspect_id }` when the receiver's type gets the method through that aspect (by `SymbolId`), else to `Inherent`, including for a receiver with no nameable type; a method shared by two aspects is ambiguous (`T0013`).

| Field | Value |
|---|---|
| `status` | `implemented` |
| `owner` | `metel-frontend` |
| `specified by` | `#elaboration` |
| `implements` | _Generated at publish._ |
| `verified by` | _Generated at publish._ |
| `last_reviewed` | 006a9aafdcb4bc9c7328ad882c08d32737058a51 |
| `related` | ADR-0037 |

</details>

## Known limitations

<!-- records:limitations -->
