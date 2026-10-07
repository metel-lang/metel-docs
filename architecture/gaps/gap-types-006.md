---
id: GAP-TYPES-006
title: "A generic body cannot construct or consume a row remainder"
summary: "A `where` equation can type the remainder of a row, but no form lets a body take an abstract row apart or build one, so typestate over a row cannot be implemented generically."
scope: "reference/spec/types.md#open-rows"
owner: language
discovered_by: "metel-core#1397 documentation work on records and rows; filed as metel-core#1399"
disposition: resolved
review: null
---

## Gap

**Resolved.** RFC-0178 specifies `..name` as an owned remainder binding in a record
pattern, and `..expr` as an owned row spread in a record literal. The type rules remove
named labels from the strongest entailed decomposition, distinguish missing presence from
an undetermined remainder, and define the empty remainder as `{}`. Bare `..` remains
discard-only; multiple spreads are outside the feature.

The implemented forms support that transition by matching the owned record with
`{ token, ..rest }` and spreading `rest` into the result record.

The syntax and behavior are specified in
`reference/spec/expressions.md#record-rest-patterns` and
`reference/spec/types.md#spec.types.generics.open-rows.legality-4`.

## Impact

No remaining spec gap. The compiler implementation and integration fixtures are tracked by
metel-core#1399.

## Affects

- `spec.types.generics.open-rows.legality-2`
- `spec.expressions.record-rest-patterns.legality-1`
- `spec.types.generics.open-rows.legality-4`
- `RFC-0178`

## Resolution

Resolved by RFC-0178's specification and implementation in
`reference/spec/expressions.md#record-rest-patterns`,
`reference/spec/types.md#open-rows`, and metel-core#1399.
