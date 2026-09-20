---
id: LIMIT-EVALUATION-002
title: "Cross-module mutual recursion is not supported"
summary: "Superseded by GAP-MODULES-001: the scenario needs a circular import, which the spec forbids."
scope: "architecture/spec/evaluation.md#evaluation"
owner: metel-interpreter
discovered_by: "metel-interpreter/docs/evaluator.md, \"Known Limitations\", #189"
disposition: superseded
review: null
---

## Limitation

`run_passes` runs all three passes (1a placeholders, 1b closures, 2
bindings) for one module before moving to the next. If function `foo` in
module A calls `bar` in module B and `bar` calls `foo`, a specific
multi-module structure (A and B peers, both importing a third module C)
requires B's environment to exist while A is still being evaluated — but it
doesn't yet, so A's closures cannot capture B's functions. The documented
fix requires running Pass 1a for every module before Pass 1b for any
module. No current test program exercises this pattern, per the source's
own note.

## Impact

That one specific circular multi-module dependency shape is unsupported.

## Affects

- `arch.evaluation.requirement-1`
- `GAP-MODULES-001`

## Resolution

Superseded by `GAP-MODULES-001` (ADR-0057 §5). The scenario this record
describes needs A and B to call each other, which requires a circular
import; the Language Spec makes that a compile error
(`spec.modules.module-graph-loading.legality-2`, fixture
`module_loading/rejects_circular_module_graph`), so the evaluator's pass
ordering is never exercised by it. The cited `#189` is closed (v0.6.3).
