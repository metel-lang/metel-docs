# Elaboration {#elaboration}

The pass between type checking and evaluation: it resolves method-call dispatch statically wherever possible, so the evaluator can skip a runtime aspect-registry lookup at those call sites. Owning crate: `metel-frontend`. Defined in `elaborator/`. See ADR-0037.

##### Requirement {#arch.elaboration.requirement-1}

Every `TypedExpr::MethodCall`'s `dispatch` field starts as `MethodDispatch::Dynamic` and is upgraded during elaboration to `Inherent` (a direct call on the concrete receiver type) or `Aspect { aspect_id }` (dispatched through a named aspect, by its stable `SymbolId`) wherever the target is statically determinable from the type registry. Two different aspects providing the same method name for the same type is rejected as ambiguous (`T0013`) rather than silently picking one. Only genuinely indeterminate sites (e.g. calls on `fn`/tuple types with no aspect-method registration) remain `Dynamic`; the evaluator reads a resolved site's dispatch decision rather than re-deriving it.

| Field | Value |
|---|---|
| `status` | `implemented` |
| `owner` | `metel-frontend` |
| `specified by` | `#elaboration` |
| `implements` | `metel-frontend/src/elaborator/mod.rs` (`elaborate`, `ElaboratedModuleGraph`); `metel-frontend/src/typed_ast/mod.rs` (`MethodDispatch`) |
| `verified by` | `metel-frontend/src/elaborator/mod.rs::resolve_dispatch_aspect_returns_aspect_variant`, `::resolve_dispatch_wrong_type_returns_inherent`, `::resolve_dispatch_same_bare_name_different_identity_returns_inherent`, `::resolve_dispatch_no_type_returns_inherent`, `::resolve_dispatch_unknown_method_returns_inherent`, `::resolve_dispatch_non_aspect_method_returns_inherent`, `::resolve_dispatch_primitive_receiver_has_no_identity`; integration fixture `metel-interpreter/tests/integration/sources/module_semantics/same_type_aspect_method_collision_is_t0013` |
| `related` | ADR-0037 |

## Known limitations

`ElaboratedModuleGraph(pub TypedModuleGraph)`'s field is fully `pub`, unlike `NormalizedModuleGraph`'s `pub(crate)` field (`#name-resolution`, `arch.name-resolution.requirement-4`) — nothing stops code outside `metel-frontend` from constructing an `ElaboratedModuleGraph` without having actually run `elaborate`, an asymmetry the two wrapper types' otherwise-identical "proof this pass ran" design doesn't explain. Worth `#1161` filing as a `LIMIT-*` record rather than silently carrying the inconsistency forward.
