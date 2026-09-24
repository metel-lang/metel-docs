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
| `implements` | [`metel-frontend/src/path_normalizer.rs::normalize`](https://github.com/metel-lang/metel-core/blob/4155d94ccbc5b1657799f3537515610f3bb139c3/metel-frontend/src/path_normalizer.rs#L45) |
| `verified by` | [`metel-frontend/src/path_normalizer.rs::explicitly_imported_qualified_call_carries_the_same_symbol_id`](https://github.com/metel-lang/metel-core/blob/4155d94ccbc5b1657799f3537515610f3bb139c3/metel-frontend/src/path_normalizer.rs#L647); [`metel-frontend/src/path_normalizer.rs::glob_imported_qualified_call_carries_a_symbol_id`](https://github.com/metel-lang/metel-core/blob/4155d94ccbc5b1657799f3537515610f3bb139c3/metel-frontend/src/path_normalizer.rs#L627); [`metel-frontend/src/path_normalizer.rs::normalized_graph_can_only_be_built_inside_this_crate`](https://github.com/metel-lang/metel-core/blob/4155d94ccbc5b1657799f3537515610f3bb139c3/metel-frontend/src/path_normalizer.rs#L705); [`metel-frontend/src/path_normalizer.rs::self_qualified_call_carries_a_symbol_id`](https://github.com/metel-lang/metel-core/blob/4155d94ccbc5b1657799f3537515610f3bb139c3/metel-frontend/src/path_normalizer.rs#L681) |
| `last_reviewed` | 2c95c6d9c5f131d86fa08889153355b451e12c9e |
| `related` | ADR-0021, ADR-0031 |

</details>

## Known limitations

<!-- records:limitations -->
