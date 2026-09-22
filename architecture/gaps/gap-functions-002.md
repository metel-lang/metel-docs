---
id: GAP-FUNCTIONS-002
title: "`Callable<A, B>` does not exist, so a function type cannot be bounded by an aspect"
summary: "`Callable<A, B>` is not defined in `std::core`, so a function or closure type cannot satisfy an aspect bound and `dyn Callable` is unavailable."
scope: "reference/spec/functions.md#first-class-functions"
owner: language
discovered_by: "metel-core#1235 records pass over the limit-phrasing lint of `reference/spec/declarations.md`"
disposition: planned
rfc: RFC-0161
review: null
---

## Gap

A plain function and a closure share one type, `|A| -> B`; there is no `fun(A) -> B` pointer type. The aspect that function types are sometimes described as implementing, `Callable<A, B>`, is not defined in `std::core`, so no bound names it and `dyn Callable` cannot be written. RFC-0161 (`1-under-review`) proposes the contract.

## Impact

No aspect bound can require "any callable", and `dyn Callable` cannot be written.

## Affects

- `RFC-0161`

## Resolution

No release committed. Design is RFC-0161 (`1-under-review`, metel-core#923), deliberately
kept off the v0.13.1–v0.17.0 ownership-finalization roadmap: `Callable`/`dyn Callable`
completes the closure/aspect surface but establishes no new identity for the language,
unlike the ownership and row-polymorphism work those milestones carry. Revisit once that
work lands.
