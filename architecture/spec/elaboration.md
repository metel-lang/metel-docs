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

Every `TypedExpr::MethodCall`'s `dispatch` field starts as `MethodDispatch::Dynamic` and is upgraded during elaboration to `Inherent` (a direct call on the concrete receiver type) or `Aspect { aspect_id }` (dispatched through a named aspect, by its stable `SymbolId`) wherever the target is statically determinable from the type registry. Two different aspects providing the same method name for the same type is rejected as ambiguous (`T0013`) rather than silently picking one. Only genuinely indeterminate sites (e.g. calls on `fn`/tuple types with no aspect-method registration) remain `Dynamic`; the evaluator reads a resolved site's dispatch decision rather than re-deriving it.

| Field | Value |
|---|---|
| `status` | `implemented` |
| `owner` | `metel-frontend` |
| `specified by` | `#elaboration` |
| `implements` | [`metel-frontend/src/elaborator/mod.rs::elaborate`](https://github.com/metel-lang/metel-core/blob/282f563360390f6648e81bc9d3974bcb8070c496/metel-frontend/src/elaborator/mod.rs#L44) |
| `verified by` | [`metel-frontend/src/elaborator/mod.rs::resolve_dispatch_aspect_returns_aspect_variant`](https://github.com/metel-lang/metel-core/blob/282f563360390f6648e81bc9d3974bcb8070c496/metel-frontend/src/elaborator/mod.rs#L557) |
| `last_reviewed` | 2ae8fae97336bfe87d459103ad85d8fecbbab4ca |
| `related` | ADR-0037 |

</details>

## Known limitations

`LIMIT-*` records are the authoritative inventory of known boundaries for this
section. They carry the impact, owner, disposition, and review point; the
Atlas limitations view projects the same records rather than duplicating them.

### Active records

- [`LIMIT-ELABORATION-001`](../limitations/limit-elaboration-001.md) — `ElaboratedModuleGraph`'s field is fully `pub`, unlike `NormalizedModuleGraph`'s `pub(crate)`; the two "proof this pass ran" wrapper types aren't actually symmetric in what they enforce.

### Resolved records

No resolved `LIMIT-*` records are currently recorded for this section.
