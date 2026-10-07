---
id: GAP-TYPES-009
title: "Tuples have no rest pattern or spread over their numeric-label row"
summary: "A tuple cannot be split into its first element and the rest, or extended, in a generic body."
scope: "reference/spec/types.md#tuples"
owner: language
discovered_by: "RFC-0178 review"
disposition: known
rfc: RFC-0178, RFC-0151
review: null
---

## Gap

A tuple cannot be split into its first element and the rest, or extended, in a generic
body. If RFC-0151 makes tuples rows with numeric labels, RFC-0178's forms could apply, but
whether `(a, ..rest)` yields a re-indexed tuple (`rest.0` is the old `.1`) or keeps the
original labels is that RFC's decision, not RFC-0178's.

## Impact

Visible to Metel programmers: variadic-style tuple code (a `head`/`tail`) has no generic
spelling; use a record or a fixed arity.

## Affects

- `spec.types.tuples.legality-1`

## Resolution

Not scheduled. Decide together with RFC-0151.
