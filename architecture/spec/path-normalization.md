# Path Normalization {#path-normalization}

Path normalization follows Name & Reference Resolution and precedes Coherence. It
rewrites resolved multi-segment paths into identity-bearing forms consumed by later
stages, producing the boundary type that proves the rewrite has run. Owning crate:
`metel-frontend`; implementation: `path_normalizer.rs`.

<details>
<summary>Verifiable architecture claims</summary>

##### Requirement {#arch.path-normalization.requirement-1}

Multi-segment qualified paths (`Expr::Path`, e.g. `math::sin`) rewrite to `Expr::ResolvedPath` carrying the resolved `SymbolId`, producing a `NormalizedModuleGraph` whose fields are `pub(crate)`, so only `path_normalizer::normalize` can construct one.

| Field | Value |
|---|---|
| `status` | `implemented` |
| `owner` | `metel-frontend` |
| `specified by` | `#path-normalization` |
| `implements` | [`metel-frontend/src/pipeline/path_normalization/mod.rs::normalize`](https://github.com/metel-lang/metel-core/blob/006a9aafdcb4bc9c7328ad882c08d32737058a51/metel-frontend/src/pipeline/path_normalization/mod.rs#L45) |
| `verified by` | [`metel-frontend/src/pipeline/path_normalization/mod.rs::normalized_graph_can_only_be_built_inside_this_crate`](https://github.com/metel-lang/metel-core/blob/006a9aafdcb4bc9c7328ad882c08d32737058a51/metel-frontend/src/pipeline/path_normalization/mod.rs#L565); [`metel-frontend/src/pipeline/path_normalization/tests.rs::explicitly_imported_qualified_call_carries_the_same_symbol_id`](https://github.com/metel-lang/metel-core/blob/006a9aafdcb4bc9c7328ad882c08d32737058a51/metel-frontend/src/pipeline/path_normalization/tests.rs#L87); [`metel-frontend/src/pipeline/path_normalization/tests.rs::glob_imported_qualified_call_carries_a_symbol_id`](https://github.com/metel-lang/metel-core/blob/006a9aafdcb4bc9c7328ad882c08d32737058a51/metel-frontend/src/pipeline/path_normalization/tests.rs#L67); [`metel-frontend/src/pipeline/path_normalization/tests.rs::self_qualified_call_carries_a_symbol_id`](https://github.com/metel-lang/metel-core/blob/006a9aafdcb4bc9c7328ad882c08d32737058a51/metel-frontend/src/pipeline/path_normalization/tests.rs#L121) |
| `last_reviewed` | 006a9aafdcb4bc9c7328ad882c08d32737058a51 |
| `related` | ADR-0021, ADR-0031 |

</details>

## Known limitations

<!-- records:limitations -->
