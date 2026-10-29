---
id: GAP-FUNCTIONS-006
title: "A `let`-bound closure cannot call itself"
summary: "A closure bound by `let` is not in scope in its own body, so it cannot be recursive; recursion needs a named `fun`."
scope: "reference/spec/functions.md#spec.functions.closures.legality-1"
owner: language
discovered_by: "RFC-0193 review (metel-core#1665): checking when a let-bound closure can replace a private function"
disposition: planned
tracked_by: metel-core#1667
rfc: RFC-0193
review: null
---

## Gap

A closure is a value, and a `let` binding is visible only from its declaration point (`spec.declarations.variables.scoping-and-shadowing.legality-2`), so the name a closure is bound to is not in scope in the closure's own initializer. `let fact := |n: i64| { … fact(n - 1) };` is `T0003: undefined name fact`. A named `fun` recurses freely.

## Impact

A recursive helper must be a `fun`, and a `fun` writes its return type (RFC-0193: a named declaration does not infer one). The compiler's let-bound-closure suggestion for a private function with no return type is therefore withheld for a function that calls itself, directly or through other functions.

## Affects

- `spec.functions.closures.legality-1`
- `RFC-0193`

## Resolution

Planned, tracked as metel-core#1667: either a recursive binding form or a documented decision to keep recursion to named functions. Needs an RFC before any implementation; RFC-0193 does not change it.
