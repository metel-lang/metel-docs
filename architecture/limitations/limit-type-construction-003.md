---
id: LIMIT-TYPE-CONSTRUCTION-003
title: "`==` and `!=` reject non-primitive operands instead of dispatching through `Eq`"
summary: "`==` and `!=` reject operands that are not numbers, booleans, strings or chars; call `.eq(..)` instead."
scope: "architecture/spec/type-construction.md#type-construction"
owner: metel-frontend
discovered_by: "metel-core#1217 limitation analysis; `typechecker/construction.rs`"
disposition: known
review: null
---

## Limitation

Construction accepts `==`/`!=` only when the operand type is numeric,
`boolean`, `String`, `char` or `Never`. Any other type, including a struct
that implements `Eq`, is rejected rather than dispatched to the `Eq` aspect.
Reproduced against current `develop`:

```metel
struct P { x: i64 }
fun main() {
    let a := P { x = 1 };
    let b := P { x = 1 };
    assert(a == b);
}
```

```
[T0005] type error: equality comparison requires a primitive operand (numeric, boolean, String, or char), got `P`; `==` does not yet dispatch through the `Eq` aspect — use `.eq(..)` on a type that implements it
```

The guard deliberately rejects rather than peeling references, to avoid
committing the language to referent-equality versus identity semantics.

## Impact

Visible to Metel programmers: user types must call `.eq(..)` explicitly.
The source comment attributes the fix to `metel-core#263`, which is now about
Copy rules for tuples and arrays; the reference is stale and the follow-up
issue needs to be found or filed.

## Affects

- `arch.type-construction.requirement-7`
- `metel-frontend/src/typechecker/construction.rs` (equality guard)

## Resolution

None yet; needs a tracking issue (the cited `#263` no longer matches).
