# Path Normalization {#path-normalization}

Path normalization follows Name & Reference Resolution and precedes Coherence. It
rewrites resolved multi-segment paths into identity-bearing forms consumed by later
stages, producing the boundary type that proves the rewrite has run. Owning crate:
`metel-frontend`; implementation: `path_normalizer.rs`.

<details>
<summary>Verifiable architecture claims</summary>

##### Requirement {#arch.path-normalization.requirement-1}

Multi-segment qualified paths (`Expr::Path`, e.g. `math::sin`) rewrite to `Expr::ResolvedPath` carrying the resolved `SymbolId` (a path through a type, such as `lib::Counter::new` or `root::Kind::A`, instead names the type its module prefix names, where a `root`, `self` or `super` prefix is resolved against the current module), producing a `NormalizedModuleGraph` whose fields are `pub(crate)`, so only `path_normalizer::normalize` can construct one.

| Field | Value |
|---|---|
| `status` | `implemented` |
| `owner` | `metel-frontend` |
| `specified by` | `#path-normalization` |
| `implements` | _Generated at publish._ |
| `verified by` | _Generated at publish._ |
| `last_reviewed` | 1c891f6d20f329b56274dc40ab6c27c879cc5e04 |
| `related` | ADR-0021, ADR-0031 |

</details>

## Known limitations

<!-- records:limitations -->
