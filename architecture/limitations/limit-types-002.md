---
id: LIMIT-TYPES-002
title: "`where all R: Aspect` is not implemented"
summary: "`all` is not a `WhereConstraint` alternative; a row-conditional impl's body cannot require an aspect of every field."
scope: "architecture/spec/type-inference.md#type-inference"
owner: metel-frontend
discovered_by: "RFC-0123 entering 3-integrated with no implementation yet"
disposition: planned
planned_for: v0.14.0
rfc: RFC-0123
review: null
---

## Limitation

`where all R: Aspect` does not parse — `WhereConstraint` has no `all` alternative, only
an ordinary bound and RFC-0121's row equation (also not implemented, `LIMIT-TYPES-001`).
Reproduced against current `develop`:

```metel
fun consume<row R>(r: { ..R }) where all R: Copy { }
```

```
[P0001] parse error: expected a where-constraint (`ident : BoundList` or `ident =
Type`), found `all`
```

The Language Spec specifies this constraint
(`spec.types.generics.field-wise-row-constraints.legality-1`), so this is an
implementation shortfall against the spec, not a spec gap.

## Impact

Visible to Metel programmers: no blanket aspect implementation can be written over
every row of a given shape for an aspect whose methods need something from each field
(`Display`, `Copy`, `Eq`) — only a concrete, closed-row impl is writable today. The
abstract/generic case of width subtyping's `Copy` requirement
(`spec.types.generics.open-rows.legality-3`) is also unreachable until this lands,
independent of `LIMIT-TYPES-001`.

## Affects

- `spec.types.generics.field-wise-row-constraints.legality-1`

<!-- limit.py:markers:start -->
<!-- limit.py:markers:end -->

## Resolution

Planned: tracked as metel-core#1302 (RFC-0123 implementation tracking, milestone
v0.14.0, lands alongside RFC-0121).
