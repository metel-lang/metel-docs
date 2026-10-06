---
id: GAP-TYPES-004
title: "A blanket row-conditional aspect impl's body cannot require an aspect of every field"
summary: "RESOLVED: `where all R: Aspect` (RFC-0123) now specifies the per-field quantifier a blanket row-conditional impl's body needs."
scope: "reference/spec/types.md#implementing-an-aspect-for-a-record"
owner: language
discovered_by: "metel-core#1235 stale-passage check of `reference/spec/types.md`; narrowed 2026-10-01 once RFC-0121 specified row variables and row-conditional impl resolution, then closed the same day once RFC-0123 specified `all R: Aspect`"
disposition: resolved
review: null
---

## Gap

**Resolved.** The spec sketched three ways to implement an aspect for a record: one
concrete row (`GAP-DECLARATIONS-001`, separately tracked), every row of a given shape,
and every row. The second and third needed row variables (now specified, RFC-0121,
`3-integrated` — `spec.types.generics.open-rows.*`) and, for a body to actually use a
field generically, a way to require an aspect of every field in the row (now specified,
RFC-0123, `3-integrated` — `spec.types.generics.field-wise-row-constraints.legality-1`,
`where all R: Aspect`). A fully correct implementation of the current Language Spec
would now deliver both forms; what remains is a pure implementation shortfall
(`LIMIT-TYPES-002`), not a spec gap.

## Impact

None remaining at the spec level — closed by the two RFCs above.

## Affects

- `spec.types.generics.row-conditional-impls.legality-1`
- `spec.types.generics.field-wise-row-constraints.legality-1`
- `RFC-0121`
- `RFC-0123`

## Resolution

Resolved 2026-10-01: RFC-0121 (row variables, row-conditional impl resolution) and
RFC-0123 (`all R: Aspect`) both reached the integrated spec; their implementations are
now complete, with the remaining RFC-0123 limitation tracked separately in
`LIMIT-TYPES-002`.
