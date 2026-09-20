---
id: GAP-MODULES-001
title: "Module graphs may not be cyclic, so modules cannot be mutually dependent"
summary: "A circular import is a compile error, so two modules cannot depend on each other."
scope: "reference/spec/modules.md#spec.modules.module-graph-loading.legality-2"
owner: language
discovered_by: "metel-core#1211 limitation analysis; re-sorting LIMIT-EVALUATION-002 under ADR-0057"
disposition: known
review: null
---

## Gap

A circular import is a compile error (`circular module dependency`, with the
full import chain). Two modules therefore cannot call each other's functions:
mutual recursion across a module boundary is not expressible, and a cycle
must be broken by moving the shared definitions into a third module.

## Impact

Programs that would naturally express mutually recursive modules must
restructure them. This is a specified property of the module system, not an
implementation shortfall.

## Affects

- `spec.modules.module-graph-loading.legality-2`
- `LIMIT-EVALUATION-002`

## Resolution

None recorded: no RFC or issue proposes allowing cyclic module graphs.
