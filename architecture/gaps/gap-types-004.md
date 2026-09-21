---
id: GAP-TYPES-004
title: "An aspect cannot be implemented over a row: no row variables, overlap checking or per-field constraints"
summary: "`extend<row R: { x: f64, .. }> { ..R }: A` and `extend<row R> { ..R }: A` do not parse: the language has no row variables."
scope: "reference/spec/types.md#implementing-an-aspect-for-a-record"
owner: language
discovered_by: "metel-core#1235 stale-passage check of `reference/spec/types.md`; both forms rejected with `P0001` (expected `record_kw`) on the v0.13.0 interpreter"
disposition: known
rfc: RFC-0121, RFC-0123
review: null
---

## Gap

The spec sketches three ways to implement an aspect for a record: one concrete row
(`extend { x: f64, y: f64 }: A`, see `GAP-DECLARATIONS-001`), every row of a given shape
(`extend<row R: { x: f64, .. }> { ..R }: A`) and every row (`extend<row R> { ..R }: A`).
The second and third need row variables, which the language does not have: a row is bounded
through a `record T: { .. }` type parameter, and `{ ..R }` does not parse. The second also
needs overlap checking between row bounds (two shape-conditional impls can be incomparable,
so they must be disjoint), and the third a way to require an aspect of every field in the
row. Open rows and field-wise constraints are proposed in RFC-0121 and RFC-0123, both
`1-under-review`.

## Impact

An aspect cannot be given one implementation covering every record of a shape; each concrete
record type needs its own, and anonymous records cannot implement an aspect at all today.

## Affects

- `RFC-0121`
- `RFC-0123`

## Resolution

Not scheduled: the RFCs are under review.
