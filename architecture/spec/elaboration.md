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

Every `TypedExpr::MethodCall`'s `dispatch` field starts as `MethodDispatch::Dynamic` and is resolved during elaboration to `Aspect { aspect_id }` (dispatched through a named aspect, by its stable `SymbolId`) when the receiver's type registers the method through an aspect, and to `Inherent` (a plain call on the concrete receiver type) otherwise. Two different aspects providing the same method name for the same type is rejected as ambiguous (`T0013`) rather than silently picking one. No site is left `Dynamic`: a receiver with no nameable type (a `fn` or tuple, say) resolves to `Inherent`, which the evaluator treats identically to a residual `Dynamic`. The evaluator reads a resolved site's dispatch decision rather than re-deriving it.

| Field | Value |
|---|---|
| `status` | `implemented` |
| `owner` | `metel-frontend` |
| `specified by` | `#elaboration` |
| `implements` | [`metel-frontend/src/elaborator/mod.rs::elaborate`](https://github.com/metel-lang/metel-core/blob/307eb632c452a6988be9b2bbb6ccac2cb96869b2/metel-frontend/src/elaborator/mod.rs#L45) |
| `verified by` | [`metel-frontend/src/elaborator/mod.rs::resolve_dispatch_aspect_returns_aspect_variant`](https://github.com/metel-lang/metel-core/blob/307eb632c452a6988be9b2bbb6ccac2cb96869b2/metel-frontend/src/elaborator/mod.rs#L558); [`metel-frontend/src/elaborator/mod.rs::resolve_dispatch_no_type_returns_inherent`](https://github.com/metel-lang/metel-core/blob/307eb632c452a6988be9b2bbb6ccac2cb96869b2/metel-frontend/src/elaborator/mod.rs#L597); [`metel-frontend/src/elaborator/mod.rs::resolve_dispatch_non_aspect_method_returns_inherent`](https://github.com/metel-lang/metel-core/blob/307eb632c452a6988be9b2bbb6ccac2cb96869b2/metel-frontend/src/elaborator/mod.rs#L617); [`metel-frontend/src/elaborator/mod.rs::resolve_dispatch_same_bare_name_different_identity_returns_inherent`](https://github.com/metel-lang/metel-core/blob/307eb632c452a6988be9b2bbb6ccac2cb96869b2/metel-frontend/src/elaborator/mod.rs#L586); [`metel-frontend/src/elaborator/mod.rs::resolve_dispatch_wrong_type_returns_inherent`](https://github.com/metel-lang/metel-core/blob/307eb632c452a6988be9b2bbb6ccac2cb96869b2/metel-frontend/src/elaborator/mod.rs#L571); [`metel-interpreter/tests/integration/sources/module_semantics/same_type_aspect_method_collision_is_t0013/test.toml`](https://github.com/metel-lang/metel-core/blob/307eb632c452a6988be9b2bbb6ccac2cb96869b2/metel-interpreter/tests/integration/sources/module_semantics/same_type_aspect_method_collision_is_t0013/test.toml#L1) |
| `last_reviewed` | 2aa2c5729e26ccba73bcc69fe338f0941ffc4966 |
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
