---
id: rfc-0053
title: "Fixed-Size Array Type [T;N]"
date: '2026-06-05'
---

## Summary

Introduce a fixed-size array type `[T; N]` where `N` is a compile-time integer literal. A fixed-size array is a distinct type from the dynamic array `T[]`, but coerces to it implicitly. The construction syntax `[expr; N]` creates an array of `N` elements, each initialised by evaluating `expr` once and cloning the result.

## Motivation

Dynamic arrays (`T[]`) carry no size information in the type. This means the typechecker cannot reject out-of-bounds access on arrays whose size is statically known, and callers cannot express "this function requires exactly 3 arguments" at the type level. A fixed-size array type closes this gap for the common case where size is known at compile time.

## Design

### Type syntax

```
[T; N]
```

`T` is any type. `N` is a non-negative integer literal (e.g. `5`, `0`). Two fixed-size array types are equal only when both the element type and the size match: `[i64; 3]` and `[i64; 4]` are distinct types.

### Expression syntax

**Repeat construction** — evaluates `expr` once and clones the result `N` times:

```
[expr; N]
```

If `expr` has side effects, it is still evaluated exactly once. To evaluate an expression `N` times independently, use a loop. This matches Rust's semantics and avoids a subtle divergence between `[f(); 3]` and `[f(), f(), f()]`.

**Literal construction** — the existing `[e1, e2, e3]` syntax typechecks against `[T; N]` when the element count equals `N` and all elements are of type `T`:

```
let arr: [i64; 3] = [1, 2, 3];
```

### Coercion

`[T; N]` coerces implicitly to `T[]`. The reverse is a type error.

```
fun sum(arr: i64[]) -> i64 { ... }

let fixed: [i64; 4] = [1, 2, 3, 4];
sum(fixed);   // ok — coerces to i64[]
```

`array_push` is being removed from the language (see planned removal); the coercion therefore does not expose any mutation-by-growth operation.

### Size expression

`N` is restricted to non-negative integer literals in this RFC. Named constants and const expressions are left for a future RFC once a `const` declaration form exists.

`[T; 0]` is a valid type. It represents an empty fixed-size array and is the identity element of array concatenation. Indexing into a `[T; 0]` is always a type error (statically rejected when the index is a literal; a runtime bounds error otherwise).

### Struct fields

`[T; N]` is a valid field type:

```
struct Matrix {
    rows: [[f64; 4]; 4],
}
```

### Nested fixed arrays

Fixed-size arrays may be nested. `[[T; M]; N]` is a fixed-size array of `N` fixed-size arrays of `M` elements of type `T`, and is the natural representation for a statically-sized matrix.

### Pattern matching and destructuring

Array patterns bind elements by position:

```
let [a, b, c] = arr;        // destructure [T; 3]
let [head, ..rest] = arr;   // head + remainder (rest is T[])
```

A fixed-size array pattern must match the size exactly; a mismatch is a type error.

### Generics limitation

Without const generics, `N` cannot appear as a type parameter. It is not possible to write a generic function that is polymorphic over the size:

```
// not valid in this RFC — N is not a type parameter
fun reverse<T>(arr: [T; N]) -> [T; N] { ... }
```

Such functions must either accept `T[]` via coercion (losing size information) or be written for specific sizes. Const generics (`<const N: u64>`) are the path forward and are left for a future RFC.

### Coercion in generic instantiation

When a generic function takes `T[]` and a `[E; N]` is passed at a call site, the coercion applies and the type variable `T` is instantiated as `E`. The size information is erased at the coercion boundary.

```
fun sum<T>(arr: T[]) -> T { ... }
let v: [i64; 5] = [1, 2, 3, 4, 5];
sum(v);   // T = i64, v coerces to i64[]
```

### Runtime representation

`[T; N]` uses the same `Value::Array` runtime representation as `T[]`. The size constraint is enforced statically by the typechecker and is not checked at runtime.

## Type system rules

- `[T; N]` is a new `Type` variant: `Type::SizedArray(Box<Type>, u64)`.
- `[T; N]` unifies only with `[T; N]` (same element type and same size).
- Coercion to `T[]` is handled in the construction pass: when a `[T; N]` value appears where `T[]` is expected, it is wrapped in a coercion node.
- A repeat construction `[expr; N]` has type `[T; N]` where `T` is the type of `expr`.
- A literal `[e1, ..., eN]` may be typed as either `T[]` or `[T; N]`; the construction pass chooses based on the expected type.
- `[T; N]` is a valid struct field type.
- Nested fixed arrays `[[T; M]; N]` are valid and follow the same rules recursively.

## Alternatives considered

**Runtime-size arrays (`[T; expr]` where `expr` is any expression)** — rejected because `N` is part of the type and cannot be a runtime value in a statically typed system. Analogous to VLAs in C99, which are widely considered a design mistake.

**No coercion to `T[]`** — would require users to manually convert, adding friction for the common pattern of passing a fixed-size array to a function that works on any array. Since the runtime representation is identical, coercion is free and correct.

## Open questions

- Should there be an indexing operation that returns a compile-time-checked result (no bounds check needed)? Deferred until const generics exist; the case is too narrow to justify the complexity beforehand.
