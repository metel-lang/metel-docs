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
| `implements` | [`metel-frontend/src/elaborator/mod.rs::elaborate`](https://github.com/metel-lang/metel-core/blob/4155d94ccbc5b1657799f3537515610f3bb139c3/metel-frontend/src/elaborator/mod.rs#L49) |
| `verified by` | [`metel-frontend/src/elaborator/mod.rs::resolve_dispatch_aspect_returns_aspect_variant`](https://github.com/metel-lang/metel-core/blob/4155d94ccbc5b1657799f3537515610f3bb139c3/metel-frontend/src/elaborator/mod.rs#L560); [`metel-frontend/src/elaborator/mod.rs::resolve_dispatch_no_type_returns_inherent`](https://github.com/metel-lang/metel-core/blob/4155d94ccbc5b1657799f3537515610f3bb139c3/metel-frontend/src/elaborator/mod.rs#L599); [`metel-frontend/src/elaborator/mod.rs::resolve_dispatch_non_aspect_method_returns_inherent`](https://github.com/metel-lang/metel-core/blob/4155d94ccbc5b1657799f3537515610f3bb139c3/metel-frontend/src/elaborator/mod.rs#L619); [`metel-frontend/src/elaborator/mod.rs::resolve_dispatch_same_bare_name_different_identity_returns_inherent`](https://github.com/metel-lang/metel-core/blob/4155d94ccbc5b1657799f3537515610f3bb139c3/metel-frontend/src/elaborator/mod.rs#L588); [`metel-frontend/src/elaborator/mod.rs::resolve_dispatch_wrong_type_returns_inherent`](https://github.com/metel-lang/metel-core/blob/4155d94ccbc5b1657799f3537515610f3bb139c3/metel-frontend/src/elaborator/mod.rs#L573); [`metel-interpreter/tests/integration/sources/module_semantics/same_type_aspect_method_collision_is_t0013/test.toml`](https://github.com/metel-lang/metel-core/blob/4155d94ccbc5b1657799f3537515610f3bb139c3/metel-interpreter/tests/integration/sources/module_semantics/same_type_aspect_method_collision_is_t0013/test.toml#L1) |
| `last_reviewed` | 2c95c6d9c5f131d86fa08889153355b451e12c9e |
| `related` | ADR-0037 |

</details>

## Known limitations

<!-- records:limitations -->
