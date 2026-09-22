---
id: LIMIT-TYPE-INFERENCE-008
title: "T0002 'cannot infer receiver type' is used for a known type that simply has no matching method"
summary: "Calling a method that a receiver's type does not implement reports 'cannot infer receiver type; add a type annotation' even when the receiver is fully annotated, instead of naming the missing method."
scope: "architecture/spec/type-inference.md#type-inference"
owner: metel-frontend
discovered_by: "metel-core#1242"
disposition: known
review: null
---

## Limitation

Reproduced against current `develop`:

```metel
fun main() {
    let f: |i64| -> i64 := |x: i64| -> i64 { x + 1 };
    let g: |i64| -> i64 := f.clone();   // T0002
    println("${f}");                     // T0002
}
```

Both calls fail with `[T0002] type error: cannot infer receiver type for
method call; add a type annotation`, although `f`'s type is fully annotated.
The real cause is that function types implement no aspects (`GAP-FUNCTIONS-002`,
`GAP-FUNCTIONS-003`), so there is no `Clone`/`Display` to dispatch to. The same
message appears for a method call through a never-applying impl
(`LIMIT-COHERENCE-001`) — in both cases the receiver type is known and the
real problem is that no method by that name exists on it, not that inference
could not determine the receiver's type.

## Impact

The message sends the reader to add an annotation that changes nothing,
instead of naming the actual cause (no such method, or no aspect impl).

## Affects

- `GAP-FUNCTIONS-002`
- `GAP-FUNCTIONS-003`
- `LIMIT-COHERENCE-001`

## Resolution

None yet; tracked as `metel-core#1242`. A diagnostic naming the cause for a
receiver of known type — "no method `clone` on `|i64| -> i64`" — would
reserve "cannot infer receiver type" for a receiver whose type really is
unresolved.
