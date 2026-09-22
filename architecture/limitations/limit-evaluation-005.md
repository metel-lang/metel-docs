---
id: LIMIT-EVALUATION-005
title: "Destructor invocation is not implemented; only empty `drop` bodies are accepted"
summary: "`Drop` bodies never run, so only an empty `drop` body is accepted."
scope: "architecture/spec/evaluation.md#evaluation"
owner: metel-interpreter
discovered_by: "metel-core#1211 limitation analysis; skipped fixture `evaluator/closures/v0_13_0_captured_drop_order.toml`"
disposition: planned
planned_for: v0.15.0
rfc: RFC-0071
review: null
---

## Limitation

The evaluator never runs a `Drop` implementation. Because a `drop` body
would then silently never execute, the typechecker rejects any `drop` body
that is not empty. Reproduced against current `develop`:

```metel
struct G { n: i64 }
extend G: Drop { fun drop(&var self) { println("dropped"); } }
fun main() { let g := G { n = 1 }; }
```

```
[T0001] type error: a `drop` body cannot run yet: destructor invocation is not implemented (metel-core#261), so this cleanup would silently never happen. Leave the body …
```

The Language Spec specifies drop order and explicit drop
(`spec.ownership.drop-order.*`, `spec.ownership.explicit-drop.*`), so this is
an implementation shortfall against the spec, not a spec gap.

## Impact

Visible to Metel programmers: no user-defined cleanup logic can run, so
resource-owning types cannot release resources through `Drop`. The one skipped
fixture in the tree, `v0_13_0_captured_drop_order`, is skipped for this
reason and should be enabled when the limitation is lifted.

## Affects

- `arch.evaluation.requirement-1`
- `arch.type-construction.requirement-5`

<!-- limit.py:markers:start -->
- [`metel-frontend/src/typechecker/construction/declarations.rs::reject_inert_destructor`](https://github.com/metel-lang/metel-core/blob/4155d94ccbc5b1657799f3537515610f3bb139c3/metel-frontend/src/typechecker/construction/declarations.rs#L391)
<!-- limit.py:markers:end -->

## Resolution

Planned: tracked as metel-core#261 (RFC-0071 3/4: drop order and explicit
drop, milestone v0.15.0).
