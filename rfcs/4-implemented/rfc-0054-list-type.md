---
id: rfc-0054
title: "Standard List<T> Type"
date: '2026-06-05'
---

## Summary

Introduce `List<T>` as the standard growable-sequence type in `std::core`. `List<T>` replaces the ad-hoc use of `T[]` (dynamic arrays with `array_push`) for mutable, variable-length sequences, and provides a clean generic API. `T[]` remains as the immutable/read-only array type; `List<T>` is the mutation-oriented counterpart.

## Motivation

The removal of `array_push` (see RFC-0053) leaves no ergonomic way to build variable-length sequences dynamically. `List<T>` fills this gap as a first-class standard type with an explicit, type-checked API. It also names the concept: callers that want to grow a collection say so by choosing `List<T>`, rather than using a raw `T[]` and a builtin side-effectful procedure.

## Design

### Type

`List<T>` is a generic struct defined in `std::core`. It wraps a dynamic array and exposes methods for inspection and mutation.

```
use std::core::List;

let xs: List<i64> = List::new();
xs.push(1);
xs.push(2);
xs.push(3);
println(xs.len().to_string());  // 3
```

### Construction

```
List::new()          // empty list
List::from(arr)      // construct from T[] — copies elements
```

### Core methods

| Method | Signature | Description |
|--------|-----------|-------------|
| `new` | `() -> List<T>` | Create an empty list |
| `from` | `(T[]) -> List<T>` | Construct from a dynamic array |
| `push` | `(self: *mut List<T>, value: T) -> ()` | Append an element |
| `pop` | `(self: *mut List<T>) -> Perhaps<T>` | Remove and return the last element |
| `len` | `(self: *List<T>) -> i64` | Number of elements |
| `get` | `(self: *List<T>, index: i64) -> Perhaps<T>` | Bounds-checked access; returns `Perhaps::None` on out-of-bounds |
| `as_slice` | `(self: *List<T>) -> T[]` | View as an immutable dynamic array (no copy) |

### Coercion

`List<T>` does not implicitly coerce to `T[]`. Call `.as_slice()` explicitly. This makes mutation visible at call sites: passing a `List<T>` to a function that takes `T[]` requires an explicit conversion.

### Relationship to `[T; N]`

`List<T>` is conceptually backed by a `[T; N]` inline buffer with a separate length counter (small-vector optimisation). The initial implementation uses a plain dynamic array internally; the SVO optimisation is deferred and transparent to callers.

### Runtime representation

The initial implementation wraps `Value::Array` (the same `Rc<RefCell<Vec<Value>>>` used by `T[]`). `List::new()` allocates a fresh empty array; `push`/`pop` mutate it in place via the mutable pointer receiver.

## Type system rules

- `List<T>` is a named generic struct: `Type::Named("List", vec![T])`.
- `List<T>` does not unify with `T[]` — coercion is explicit (`.as_slice()`).
- Method resolution follows the standard impl lookup.

## Alternatives considered

**Keep `array_push` and `array_len` as builtins** — rejected. Free-function mutation procedures on raw arrays are unprincipled and do not compose with the type system. A named type with method syntax is cleaner.

**Implicit coercion `List<T>` → `T[]`** — rejected. Hiding the mutation boundary makes it harder to reason about aliasing. Explicit `.as_slice()` is one extra character and clearly signals "I am giving up mutability here".

## Open questions

All open questions are resolved or explicitly deferred.

| Question | Status |
|----------|--------|
| `Display` impl for `List<T>` where `T: Display` | **Deferred** — needs derived aspects or a manual impl; not blocking |
| `List::with_capacity(n: i64)` constructor | **Deferred** — irrelevant for the tree-walking interpreter; relevant for compiled output |
| Index operator `list[i]` | **Moved to RFC-0011** — design of the `Index` aspect (panic vs `Perhaps<T>`) tracked there |
