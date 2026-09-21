---
id: GAP-MODULES-003
title: "Top-level `let` and `var` bindings cannot be exported"
summary: "A top-level `let` or `var` is always module-private; there are no public value exports."
scope: "reference/spec/modules.md#visibility"
owner: language
discovered_by: "metel-core#1235 records pass over the limit-phrasing lint of `reference/spec/modules.md`"
disposition: known
review: null
---

## Gap

`public` is valid on `struct`, `enum`, `fun` and `aspect` declarations. A top-level `let` or `var` binding is always module-private, so a module cannot export a constant or a mutable value; public value exports are not supported in the current version.

## Impact

A module cannot export a top-level value binding.

## Affects

- `spec.modules.visibility.legality-1`

## Resolution

No RFC or issue tracks public value exports yet.
