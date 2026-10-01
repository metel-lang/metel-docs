---
id: LIMIT-DECLARATIONS-001
title: "`record` declarations are not implemented"
summary: "The `record` declaration kind (RFC-0120) does not parse; only `struct` does."
scope: "architecture/spec/parsing.md#parsing"
owner: metel-frontend
discovered_by: "RFC-0120 entering 3-integrated with no implementation yet"
disposition: planned
planned_for: v0.14.0
rfc: RFC-0120
review: null
---

## Limitation

The grammar has no `record` keyword. `decl`'s alternatives accept `struct`, `enum`,
`aspect`, `extend`, `fun` and `type`, but not `record` — writing `record Handle { fd:
i64 }` is a parse error today, not a declaration of a structurally-visible nominal type.
Reproduced against current `develop`:

```metel
record Handle { fd: i64 }
```

```
[P0001] parse error: expected a declaration (`struct`, `enum`, `aspect`, `extend`,
`fun`, or `type`), found `record`
```

The Language Spec specifies named records (`spec.declarations.records.*`), so this is
an implementation shortfall against the spec, not a spec gap.

## Impact

Visible to Metel programmers: there is no way to declare a nominal type whose row is
structurally visible to row bounds or row-conditional impl resolution — every struct's
row stays private to structural matching (RFC-0137 §3), with no opt-in to publish it.
Row-conditional impl resolution itself is additionally gated on RFC-0121 (Open Rows),
not implemented either (see `LIMIT-TYPES-*` once RFC-0121 integrates).

## Affects

- `spec.declarations.records.legality-1`
- `spec.declarations.records.legality-2`
- `spec.declarations.records.legality-3`
- `spec.declarations.records.legality-4`

<!-- limit.py:markers:start -->
<!-- limit.py:markers:end -->

## Resolution

Planned: tracked as metel-core#1300 (RFC-0120 implementation tracking, milestone
v0.14.0, lands alongside RFC-0121).
