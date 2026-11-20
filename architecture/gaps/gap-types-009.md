---
id: GAP-TYPES-009
title: "Tuples have no rest pattern or spread over their numeric-label row"
summary: "A tuple cannot be split into its first element and the rest, or extended, in a generic body."
scope: "reference/spec/types/tuples.md"
owner: language
discovered_by: "RFC-0178 review"
disposition: known
rfc: RFC-0178, RFC-0151, RFC-0125
review: null
---

## Gap

A tuple cannot be split into its first element and the rest, or extended, in a generic
body. RFC-0151 (implemented) makes tuples rows with numeric labels, so RFC-0178's forms apply to
them, and RFC-0151 decides the question this gap left open: a remainder **keeps its original
labels** (`rest.1` is the old `.1`) and nothing renumbers it, because elements are named by
label. A re-indexed tuple is got by an explicit relabelling. The positional operations that
need the renumbering (`head`, `tail`, `cons`, `append`, `zip`) are the question RFC-0125 is
re-scoped to.

## Impact

Visible to Metel programmers: variadic-style tuple code (a `head`/`tail`) has no generic
spelling; use a record or a fixed arity.

## Affects

- `spec.types.tuples.legality-1`

## Resolution

Narrowed by RFC-0151: the remainder keeps its labels. The positional operations are RFC-0125's re-scoped question (comptime over rows that carry the dense-integer predicate, RFC-0202); the gap closes when one of them is accepted and implemented.
