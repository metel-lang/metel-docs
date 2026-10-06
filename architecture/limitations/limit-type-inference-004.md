---
id: LIMIT-TYPE-INFERENCE-004
title: "`List<T>` iteration"
summary: "`List<T>` implements `Iterable<T>` with an independent cursor per loop."
scope: "architecture/spec/type-inference.md#type-inference"
owner: metel-frontend
discovered_by: "metel-core#871; confirmed in the metel-core#1217/#1218 limitation analysis"
disposition: resolved
review: 2026-10-06
---

## Limitation

`List<T>` now implements `Iterable<T>` for every `T`. Each `for` loop receives
its own copied cursor, so nested loops over the same list are independent:

```metel
fun main() {
    var l: List<i64> := List::new();
    l.push(1);
    for (v in l) { assert(v == 1); }
}
```

The list's existing eager methods continue to use `self.as_slice()` because
they do not need iterator state.

## Impact

Visible to Metel programmers: lists can now be used directly in `for` loops.
`.as_slice()` remains available when an immutable array view is specifically
required.

## Affects

- `arch.type-inference.requirement-1`
- `metel-frontend/stdlib/core.mtl` (`List` and its `Iterable` implementation)
- `metel-interpreter/src/evaluator/builtins.rs` (native list construction)

## Resolution

Implemented for #871. The private cursor is part of the copied list value;
the backing array remains the shared list storage.
