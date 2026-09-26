---
id: LIMIT-TYPE-INFERENCE-003
title: "`..` is not supported in an anonymous record pattern"
summary: "A pattern ending in `..` is rejected for a concrete anonymous record; name every field."
scope: "architecture/spec/type-inference.md#type-inference"
owner: metel-frontend
discovered_by: "metel-core#1218 limitation analysis; `typechecker/inference/patterns.rs`"
disposition: known
review: null
---

## Limitation

A pattern that ends in `..` is accepted by the grammar (`RecordRest`) and by
the parser, but the typechecker rejects it when the scrutinee is a concrete
anonymous record. Reproduced against current `develop`:

```metel
fun main() {
    let r := { x = 1, y = 2 };
    match (r) {
        { x, .. } => { assert(x == 1); },
    }
}
```

```
[T0001] type error: `..` is not yet supported in an anonymous record pattern -- name every field, or match a named struct instead
```

The row-bounded generic case (`fun f<record T: { x: f64, .. }>(p: T)`) is
handled separately and works.

## Impact

Visible to Metel programmers: partial matching of an anonymous record needs
every field named. The Language Spec specifies `..` for struct patterns and
for row-bounded records but is silent on a concrete anonymous record, so the
spec text should say which way this goes (a follow-up); until then this is
recorded as an implementation limitation.

## Affects

- `arch.type-inference.requirement-1`
- `metel-frontend/src/pipeline/type_checking/inference/patterns.rs`

<!-- limit.py:markers:start -->
- [`metel-frontend/src/pipeline/type_checking/inference/patterns.rs::infer_pattern`](https://github.com/metel-lang/metel-core/blob/006a9aafdcb4bc9c7328ad882c08d32737058a51/metel-frontend/src/pipeline/type_checking/inference/patterns.rs#L82)
<!-- limit.py:markers:end -->

## Resolution

None yet. If the spec decides `..` is not allowed there, this record is
re-filed as a `GAP-*` (ADR-0057) and superseded.
