---
id: LIMIT-TYPES-001
title: "Row-kinded generic parameters (`<row R>`, `..R`) are not implemented"
summary: "`row` is not a generic-parameter kind and `..R` does not parse; no row-conditional impls, row decomposition, or row-aware width subtyping."
scope: "architecture/spec/type-inference.md#type-inference"
owner: metel-frontend
discovered_by: "RFC-0121 entering 3-integrated with no implementation yet"
disposition: planned
planned_for: v0.14.0
rfc: RFC-0121
review: null
---

## Limitation

The grammar has no `row` generic-parameter kind and `..R` does not parse in any type
position. Reproduced against current `develop`:

```metel
fun get_x<row R>(p: { x: f64, ..R }) -> f64 { p.x }
```

```
[P0001] parse error: expected a generic parameter (`record`? `ident`), found `row`
```

The Language Spec specifies row variables, row decomposition, row-conditional impl
resolution and the width-subtyping rule (`spec.types.generics.open-rows.*`,
`spec.types.generics.row-conditional-impls.*`), so this is an implementation
shortfall against the spec, not a spec gap.

## Impact

Visible to Metel programmers: no generic function or impl can abstract over "the rest
of a row." Every one of the records cluster's row-shaped capabilities that need it stays
unreachable — `drain_field`-style decomposition has no substitute at all (RFC-0118's
row bounds cannot express it), row-conditional typestate does not exist, and a blanket
aspect implementation over every record shape (`Display`, `Copy`) cannot be written
(`GAP-TYPES-004`, which additionally needs RFC-0123's `all R: Aspect` once this lands).
`record`'s own row-conditional impl eligibility (`spec.declarations.records.legality-2`,
`LIMIT-DECLARATIONS-001`) is blocked on this too.

## Affects

- `spec.types.generics.open-rows.legality-1`
- `spec.types.generics.open-rows.legality-2`
- `spec.types.generics.open-rows.legality-3`
- `spec.types.generics.row-conditional-impls.legality-1`
- `spec.types.generics.row-conditional-impls.legality-2`
- `spec.types.generics.row-conditional-impls.legality-3`

## Resolution

Planned: tracked as metel-core#1301 (RFC-0121 implementation tracking, milestone
v0.14.0, the expensive half of the records cluster per the RFC's own cost accounting
— genuinely new row-kinded variables and row unification in the elaborator/inference
system).
