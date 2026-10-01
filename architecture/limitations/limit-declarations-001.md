---
id: LIMIT-DECLARATIONS-001
title: "`record` declarations are not implemented"
summary: "The `record` declaration kind (RFC-0120) does not parse; only `struct` does."
scope: "architecture/spec/parsing.md#parsing"
owner: metel-frontend
discovered_by: "RFC-0120 entering 3-integrated with no implementation yet"
disposition: resolved
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

## Resolution

Implemented 2026-10-01, tracked by metel-core#1300, landed in metel-core#1303
(merge commit `3797758d6dc2fa068939f9ca8877c144555fe2cc`). `metel-frontend/src/
grammar.pest` gained a `record_decl` production (`decl`'s alternatives now include
`record_decl`); `Decl::Struct` carries a `StructKind::{Struct, Record}` discriminant,
and the parser rejects a non-`public` field inside a `record` as `P0001`. A new
`TypeDefinitionRegistry::record_structs: HashSet<SymbolId>` tracks which struct ids
were declared `record`, and `visible_type_kind` resolves `VisibleTypeKind::Record`
for them (by brand name, uniformly for `Type::Named` and `Type::Residual`, per
RFC-0137 §3) — a `record`'s row is now structurally visible to row bounds exactly as
this record's "Impact" section described it should be. Row-conditional impl
resolution itself remains gated on RFC-0121 (Open Rows, not yet implemented; see
`LIMIT-TYPES-001`). Verified directly: `record Handle { public fd: i64 }` now parses
and typechecks, `record Handle { fd: i64 }` (missing `public`) is rejected as `P0001`,
and a function generic over `<record T: { fd: i64, .. }>` accepts `Handle` and its
narrowed residuals but rejects an equivalent `struct`. This record's exemptions on
the four affected rules below are removed now that real fixtures cover them
(`metel-interpreter/tests/integration/sources/evaluator/structs/112-114_*`,
`parsing/negative_record_private_field_is_parse_error`).
