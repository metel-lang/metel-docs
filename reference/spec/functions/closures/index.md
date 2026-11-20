---
sidebar_position: 4
---

# Closures

> **Gap** GAP-FUNCTIONS-006

> **Gap** GAP-FUNCTIONS-007

Anonymous functions are [written with the `[captures]? once? var? |params| (-> ret)? { body }` form](capture-semantics.md#spec.functions.closures.legality-1):

```metel
fun main() -> i64 {
    let double := |x: i64| -> i64 { return x * 2; };
    return double(5);
}
```

A closure parameter may be annotated with an open record whose tail is anonymous
(`|p: .{ .x: i64, .. }| { p.x }`); the closure is then polymorphic in that row and accepts
records of different shapes ([open rows](../../types/generics/open-rows.md#spec.types.generics.open-rows.legality-5)).

[A stand-alone closure has no generics list](capture-semantics.md#spec.functions.closures.legality-28), so it cannot declare a row parameter, and a written
return annotation cannot name one: `|p: .{ .x: i64, ..R }| -> .{ .x: i64, ..R } { p }` is rejected
(`T0003`, undefined row variable `R`). Inside a generic function the closure uses the enclosing
function's `R`. When the return type is omitted it is inferred, and keeps the row of the argument:

<!-- doc-example: expect-fail reason="a stand-alone closure cannot name a row parameter" -->
```metel
fun main() {
    let f := |p: .{ .x: i64, ..R }| -> .{ .x: i64, ..R } { p };
}
```

```metel
fun keep<record R>(r: .{ .x: i64, ..R }) -> i64 {
    let f := |p: .{ .x: i64, ..R }| -> .{ .x: i64, ..R } { p };
    return f(r).x;
}

fun main() {
    let f := |p: .{ .x: i64, .. }| { p };
    assert(f(.{ .x = 1, .y = 2 }).y == 2);
    assert(keep(.{ .x = 1, .y = 2 }) == 1);
}
```

A closure has one type. [A `let`-bound closure is used at the one type its uses fix](capture-semantics.md#spec.functions.closures.legality-26), and [a closure bound by a top-level `let` is determined by its own initializer](capture-semantics.md#spec.functions.closures.legality-27). Polymorphism is written or declared: a generic `fun`, a reference to one ([First-Class Functions](../first-class-functions.md)), or the open-record parameter above.
