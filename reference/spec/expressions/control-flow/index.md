---
sidebar_position: 6
---

# Control Flow

## While

```metel
fun main() -> i64 {
    var n := 3;
    var total := 0;
    while (n > 0) {
        total += n;
        n -= 1;
    }
    return total;
}
```

## Loop

[`loop` creates an infinite loop](../../types/never/return-type.md#spec.types.never-type.dynamics-1). It is the only loop form that can produce a value:

```metel
fun main() -> i64 {
    let result := loop {
        break 42;
    };
    return result;
}
```

**Typing rules:**

- `loop { break expr; }` has type `T` where `expr: T`. All `break` arms must produce the same type; a `break` expression is [typechecked against its enclosing loop value type](../../types/type-inference.md#spec.types.type-inference.legality-2).
- `loop { }` — a loop with no reachable `break` — has type `!` (Never). See [Never Type](../../types/never/index.md).
