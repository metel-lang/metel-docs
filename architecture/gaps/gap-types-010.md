---
id: GAP-TYPES-010
title: "A function cannot return an open record while hiding its extra fields"
summary: "An open record with an anonymous tail is rejected as a return type, so an API cannot promise only some fields of the record it returns."
scope: "reference/spec/types.md#open-rows"
owner: language
discovered_by: "metel-core#1478 review of anonymous open-record tails"
disposition: accepted
rfc: RFC-0181
review: "revisit if a real API needs to hide a record's extra fields from its callers"
---

## Gap

`fun make() -> { x: i64, .. }` is rejected with `T0032`. Such a return type would be an
existential: the callee picks the row and the caller sees `x` plus an extra row it cannot name.
The language has no form for it.

The cases that motivate it are covered by other forms:

- a private function omits its return type and the exact record is inferred, so the caller reads
  every field;
- a `public` function must write a return type (`T0010`) and writes the record in full,
  `-> { x: i64, y: i64 }`;
- a function whose row comes from an argument names it, `-> { x: i64, ..R }`.

## Impact

An API cannot return a record and promise only some of its fields. A public function that returns
a record exposes its exact field set, so adding a field to it changes its type.

## Affects

- `spec.types.generics.open-rows.legality-5`
- `RFC-0181`

## Resolution

Accepted by RFC-0181, which records the decision and what an existential return would cost: an
opaque, rigid remainder carried through the caller's inference, a distinct type per call site, and
a rule for storing such a value. RFC-0179 gives the caller the whole record, so soundness is not
the obstacle. Reopen when a real API needs to hide fields.
