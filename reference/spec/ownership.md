---
title: "Ownership and Move Semantics"
---

# Ownership and Move Semantics

> **Planned for v0.12.0 (RFC-0071): values move by default; `Copy` and `Drop` are opt-in aspects.**

Nothing on this page is enforced by the current interpreter, which copies every value. The
rules below describe the model v0.12.0 introduces.

## Values move by default

A value whose type is not `Copy` has exactly one owner at any point. Assigning it, passing it
as an argument, or returning it **moves** it: ownership transfers, and the source binding
becomes invalid.

```metel
struct Buffer { data: i64[] }

fun consume(b: Buffer) -> i64 { b.data.len() }

fun main() {
    let a = Buffer { data = [1, 2, 3] };
    let b = a;          // a is moved into b
    // let n = a.data;  // error: `a` was moved
    consume(b);         // b is moved into consume
    // consume(b);      // error: `b` was moved
}
```

Primitive types and any type implementing `Copy` are exempt — they are duplicated instead.

## `Copy`

`Copy` marks a type whose values may be duplicated rather than moved. It is **opt in**, and
declared like any other aspect:

```metel
struct Point { x: f64, y: f64 }
extend Point: Copy;
```

A type may implement `Copy` only if every one of its fields — or, for an enum, every payload
in every variant — is itself `Copy`. Fixed-size arrays and tuples are `Copy` when their
elements are.

**References:** `&T` is `Copy`. `&var T` is not — an exclusive reference must remain unique,
so it is moved or reborrowed rather than duplicated.

## `Drop`

`Drop` gives a type destructor logic that runs when a value goes out of scope:

```metel
struct Handle { fd: i64 }

extend Handle: Drop {
    fun drop(self) { close_fd(self.fd); }
}
```

`Drop` is opt in. A type without a `Drop` implementation is reclaimed by recursively dropping
its fields.

## `Copy` and `Drop` are mutually exclusive

A type may not implement both. A `Copy` value may be duplicated freely, so there is no single
point at which a destructor should run.

## Drop order

Within a scope, values are dropped in **reverse declaration order**. A value that has been
moved out is not dropped where it was declared — the new owner drops it.

For a type with a `Drop` implementation, `drop(self)` runs first, then its fields are dropped
recursively.

For a struct that owns an allocator (`struct Parser(@a: BumpAlloc)`), the struct's fields are
dropped before the owned arena is freed, so any `@a T` pointers held as fields are reclaimed
while their backing memory is still valid.

## Explicit drop

`drop(x)` consumes `x`, runs its destructor if it has one, and marks the binding moved. Using
`x` afterwards is an error, exactly as after any other move.

## Partial moves

Moving a field out of a struct leaves the containing value **partially moved**. The remaining
fields stay accessible; the value as a whole does not.

```metel
struct Pair { a: Buffer, b: i64 }

fun main() {
    let p = Pair { a = Buffer { data = [1] }, b = 42 };
    let x = p.a;        // p.a moved out; p is partially moved
    let y = p.b;        // still fine — p.b was not moved
    // consume_pair(p); // error: `p` cannot be used as a whole
}
```

Tracking is at **field granularity**. Pattern destructuring may move several fields at once,
under the same rules.

**A type implementing `Drop` may not be partially moved** — its destructor requires the whole
value.

> **Planned for v0.12.0 (RFC-0071): a `Drop` type may still be partially *borrowed*; only moving out is restricted.**

### Which constructs support partial moves

| construct | partial move |
|---|---|
| struct fields | yes, at field granularity |
| tuple elements | yes — positional fields are statically named |
| record fields | yes, and the residual takes a narrower record type |
| enum payloads | no — matching a variant and moving its payload consumes the enum wholly |
| array elements | **no** |

An array element cannot be moved out because the index may be computed at run time, so which
element left is not a static fact.

## Closures

Closures capture by value, so capturing a non-`Copy` value **moves** it. To keep using the
original, capture a shared reference — `&T` is `Copy`, so the reference is duplicated and the
referent is untouched.

## What ownership does not cover

Ownership answers *how many owners a value has*, and `Copy` answers *whether a value may be
duplicated*. Neither answers *what is borrowed at a given point* — that is the borrow
checker's job, and it is not part of this release. In particular, nothing here prevents two
`&var T` references to the same place; see the References section of the Type System page.
