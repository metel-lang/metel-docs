---
id: GAP-FUNCTIONS-002
title: "`Callable<A, B>` does not exist, so a function type cannot be bounded by an aspect"
summary: "`Callable<A, B>` is not defined in `std::core`, so a function or closure type cannot satisfy an aspect bound and `dyn Callable` is unavailable."
scope: "reference/spec/functions.md#first-class-functions"
owner: language
discovered_by: "metel-core#1235 records pass over the limit-phrasing lint of `reference/spec/declarations.md`"
disposition: planned
planned_for: v0.13.1
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

Planned for v0.13.1, tracked as metel-core#923 (RFC-0161).
