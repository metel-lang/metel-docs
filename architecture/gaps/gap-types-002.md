---
id: GAP-TYPES-002
title: "The storage model of `List<T>` and its boundary with `T[]` and `[T; N]` is not specified"
summary: "How a growable `List<T>` allocates and grows its storage, and where it ends and `T[]` and `[T; N]` begin, is not fully specified."
scope: "reference/spec/types.md#arrays"
owner: language
discovered_by: "metel-core#1235 records pass over the limit-phrasing lint of `reference/spec/types.md`"
disposition: known
review: null
---

## Gap

The three-way split between `T[]`, `[T; N]` and `List<T>` reflects the current design. The exact boundary between them, in particular how a growable list's storage is allocated and grown, is not specified and may change in a future release.

## Impact

Programs must not depend on capacity, reallocation or aliasing behaviour beyond what the rules state; a later design may move the boundary.

## Affects

- `spec.types.arrays.legality-1`

## Resolution

No RFC or issue tracks it yet.
