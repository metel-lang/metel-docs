---
id: GAP-TYPES-012
title: "A record or struct field cannot have an open-record type with an anonymous tail"
summary: "An anonymous open record is rejected as a field type, so a field cannot hold 'any record with at least these fields'."
scope: "reference/spec/types.md#open-rows"
owner: language
discovered_by: "metel-core#1478 review of anonymous open-record tails"
disposition: accepted
rfc: RFC-0181
review: "revisit together with GAP-TYPES-010 if existential rows are ever added"
---

## Gap

`record W { d: { x: i64, .. } }` is rejected with `T0032`. The field's type would be existential,
so two values of one nominal type could hide different rows, which does not fit a nominal type.
The same applies to the anonymous splice (`record W { s: Session<..> }`).

## Impact

A field cannot hold an arbitrary wider record. The use is covered by a row parameter on the
record, `record W<row R> { d: { x: i64, ..R } }`, at the cost of making `W` generic over the row.

## Affects

- `spec.types.generics.open-rows.legality-5`
- `RFC-0181`

## Resolution

Accepted by RFC-0181. This would follow from an existential row (GAP-TYPES-010), not stand alone.
