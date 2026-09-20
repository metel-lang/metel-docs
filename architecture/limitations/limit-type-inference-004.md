---
id: LIMIT-TYPE-INFERENCE-004
title: "`List<T>` does not implement `Iterable<T>`"
summary: "`for (x in list)` does not typecheck for `List<T>`; iterate `list.as_slice()`."
scope: "architecture/spec/type-inference.md#type-inference"
owner: metel-frontend
discovered_by: "metel-core#871; confirmed in the metel-core#1217/#1218 limitation analysis"
disposition: known
review: null
---

## Limitation

`for (x in list)` fails to typecheck for every `List<T>`. Reproduced against
current `develop`:

```metel
fun main() {
    var l: List<i64> := List::new();
    l.push(1);
    for (v in l) { assert(v == 1); }
}
```

```
[T0001] type error: type `List<i64>` does not implement `Iterable<T>`
```

`List`'s own methods iterate `self.as_slice()` instead; arrays iterate
natively.

## Impact

Visible to Metel programmers: `.as_slice()` is required to iterate a list.

## Affects

- `arch.type-inference.requirement-1`
- `metel-frontend/src/typechecker/inference/expressions.rs` (`for`-`in` `Iterable` check)
- `metel-frontend/stdlib/core.mtl` (`List` methods)

## Resolution

None yet, tracked as `#871`.
