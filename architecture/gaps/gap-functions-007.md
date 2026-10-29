---
id: GAP-FUNCTIONS-007
title: "A closure cannot name a type parameter, a bound or a row fact"
summary: "A closure has no generics list, so it cannot declare a type parameter, bound, `where` clause or row fact, nor tie a written return type to a parameter's row."
scope: "reference/spec/functions.md#spec.functions.closures.legality-1"
owner: language
discovered_by: "metel-core#1544 §2 (closure row binders), extended by the RFC-0193 review (metel-core#1665)"
disposition: planned
tracked_by: metel-core#1668
rfc: RFC-0193
review: null
---

## Gap

A closure is written `[captures] |params| -> ret { body }` and has no generics list. It generalizes over unannotated parameters and takes an anonymous open record as a parameter, but it cannot declare or name a type parameter, a bound, a `where` clause or a row fact. `let add_host := |r| { { ..r, host = "h" } };` is `T0012` (the absence of `host` is not provable), where `fun add_host<record R: !{ host }>(r: { ..R }) -> { ..R, host: String }` states the bound. For the same reason a stand-alone closure cannot tie a written return annotation to a parameter's row; inside a generic function it can use the enclosing `R`.

## Impact

A function that needs a bound, a `where` clause or a row fact cannot be written as a closure. The compiler's let-bound-closure suggestion for a private function with no return type is withheld for a function with a generics list, bounds or a `where` clause, and for a body that extends a parameter's record (RFC-0193 §2).

## Affects

- `spec.functions.closures.legality-1`
- `RFC-0193`

## Resolution

Planned, tracked as metel-core#1668: a binder on a closure, or a documented decision to keep closures bound-free. Needs an RFC before any implementation; RFC-0193 does not change it.
