---
id: GAP-DECLARATIONS-004
title: "`let` and `var` bindings are not hoisted, so a function cannot use a later closure binding"
summary: "A `fun` is hoisted but a `let`-bound closure is visible only from its declaration onward, so a function declared above it cannot call it."
scope: "reference/spec/declarations.md#spec.declarations.variables.scoping-and-shadowing.legality-2"
owner: language
discovered_by: "RFC-0193 review (metel-core#1665): checking when a let-bound closure can replace a private function"
disposition: planned
tracked_by: metel-core#933
rfc: RFC-0131
review: null
---

## Gap

`fun` declarations are hoisted to the top of their block; `let` and `var` bindings are sequential. A function that calls a module-level `let`-bound closure is therefore accepted when it follows the binding and is `T0003: undefined name` when it precedes it:

```metel
fun main() { println(f(1)); }       // T0003: undefined name `f`
let f := |a: i64| { a + 1 };
```

## Impact

Replacing a named function by a `let`-bound closure changes where it may be used. The compiler's let-bound-closure suggestion for a private function with no return type is withheld when any use precedes the declaration (RFC-0193 §2).

## Affects

- `spec.declarations.variables.scoping-and-shadowing.legality-2`
- `RFC-0131`
- `RFC-0193`

## Resolution

Planned: RFC-0131 (hoist `let`/`var` bindings to the top of their block) is under review, tracked as metel-core#933. RFC-0193 does not change it.
