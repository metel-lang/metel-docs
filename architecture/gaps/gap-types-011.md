---
id: GAP-TYPES-011
title: "A written function type cannot say it accepts any record with at least these fields"
summary: "An open record with an anonymous tail is rejected inside a function type, and a named row fixes the row for the whole signature, so no written type means 'works for every wider record'."
scope: "reference/spec/types.md#open-rows"
owner: language
discovered_by: "metel-core#1478 review of anonymous open-record tails"
disposition: accepted
rfc: RFC-0181
review: "revisit if a real function must apply one callback to two differently shaped records it holds"
---

## Gap

`|{ x: i64, .. }| -> i64` is rejected with `T0032`. Read as a fresh row of the enclosing signature
it would let the caller choose the row, so the callee could not call the function on records of
its own; read as "accepts every wider record" it is a rank-2 type, which the checker does not
model. A named row, `|{ x: i64, ..R }| -> i64`, is supported and fixes `R` for the signature.

A closure with an open-row parameter already generalizes, so a value of the rank-2 kind exists
(one closure accepts records of different shapes); only its written type does not.

## Impact

A callback over records of one shape is written with a shared `R` and works. A function that must
apply one callback to differently shaped records it holds itself cannot say so: it takes two
callbacks, or is generic over two rows.

## Affects

- `spec.types.generics.open-rows.legality-5`
- `RFC-0181`

## Resolution

Accepted by RFC-0181. A rank-2 function type needs higher-rank checking for a body that calls a
parameter of that type, which Metel has no other use for. Reopen when a real function needs it.
