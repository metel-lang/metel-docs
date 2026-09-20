# Path Normalization {#path-normalization}

Path normalization follows Name & Reference Resolution and precedes Coherence. It
rewrites resolved multi-segment paths into identity-bearing forms consumed by later
stages, producing the boundary type that proves the rewrite has run. Owning crate:
`metel-frontend`; implementation: `path_normalizer.rs`.

<details>
<summary>Verifiable architecture claims</summary>

##### Requirement {#arch.path-normalization.requirement-1}

Multi-segment qualified paths (`Expr::Path`, including `math::sin` and `self::Foo`)
rewrite to `Expr::ResolvedPath` carrying the resolved `SymbolId`, producing a
`NormalizedModuleGraph`. Its inner field is crate-private (`pub(crate)`), so code
outside `metel-frontend` cannot construct one except through
`path_normalizer::normalize`; later stages therefore cannot receive an un-normalized
graph from another crate.

| Field | Value |
|---|---|
| `status` | `implemented` |
| `owner` | `metel-frontend` |
| `specified by` | `#path-normalization` |
| `implements` | [`metel-frontend/src/path_normalizer.rs::normalize`](https://github.com/metel-lang/metel-core/blob/c5619cae663b522b9c41aaa04f5a82788394dbbe/metel-frontend/src/path_normalizer.rs#L36) |
| `verified by` | [`metel-frontend/src/path_normalizer.rs::explicitly_imported_qualified_call_carries_the_same_symbol_id`](https://github.com/metel-lang/metel-core/blob/c5619cae663b522b9c41aaa04f5a82788394dbbe/metel-frontend/src/path_normalizer.rs#L635); [`metel-frontend/src/path_normalizer.rs::glob_imported_qualified_call_carries_a_symbol_id`](https://github.com/metel-lang/metel-core/blob/c5619cae663b522b9c41aaa04f5a82788394dbbe/metel-frontend/src/path_normalizer.rs#L615); [`metel-frontend/src/path_normalizer.rs::self_qualified_call_carries_a_symbol_id`](https://github.com/metel-lang/metel-core/blob/c5619cae663b522b9c41aaa04f5a82788394dbbe/metel-frontend/src/path_normalizer.rs#L669) |
| `last_reviewed` | 61b7338f18e07e5916b01894aab15db6686ed997 |
| `related` | ADR-0021, ADR-0031 |

</details>

## Known limitations

`LIMIT-*` records are the authoritative inventory of known boundaries for this
section. They carry the impact, owner, disposition, and review point; the
Atlas limitations view projects the same records rather than duplicating them.

### Active records

No active `LIMIT-*` records are currently recorded for this section. This is a
current inventory, not a claim of complete coverage.

### Resolved records

No resolved `LIMIT-*` records are currently recorded for this section.
