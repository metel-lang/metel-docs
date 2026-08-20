---
id: rfc-0053
title: "Fixed-Size Array Type [T;N]"
date: '2026-06-05'
---

> **Status — qualified (2026-08-12, metel-core#715, #263, #702).** This RFC specifies
> that "a literal `[e1, ..., eN]` may be typed as either `T[]` or `[T; N]`; the
> construction pass chooses based on the expected type" — but never says what happens
> when there is no expected type to consult, which is exactly `println([1, 2, 3])`:
> `println`'s parameter is bound by a conditional `Display` impl, not a concrete `T[]`
> or `[T; N]` annotation, so the construction pass has nothing to key its choice on.
> `declarations.md`'s own worked example claims this compiles via `i64[]`; #715 found
> the interpreter instead infers `[i64; 3]`, which RFC-0061's structural `Display` impl
> doesn't cover (it's specced only for `T[]`), so the spec's own example fails to
> compile. **Ruled: an unconstrained array literal defaults to `T[]`, not `[T; N]`.**
> This RFC's own Motivation section already treats `T[]` as the general-purpose type
> and `[T; N]` as the opt-in special case for when size specifically matters, and
> coercion is one-directional (`[T; N] → T[]` is free, the reverse is a type error) —
> defaulting the ambiguous case to the general type is the same direction that
> coercion already treats as cheap, and matches what a reader of `println([1, 2, 3])`
> actually means (nothing about that call asserts anything about the array's size).
> This resolves #715 without further spec changes and needs no change to RFC-0061.
> It does not touch #263 (Copy rules for fixed arrays hardcoded into the typechecker)
> or #702 (arrays, tuples and other structural types not yet modeled as regular
> types) — both are pre-existing type-system architecture debt that this RFC's
> design sits on top of rather than causes, and are tracked separately.

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

All open questions are resolved or explicitly deferred.

| Question | Status |
|----------|--------|
| Compile-time-checked indexing (no bounds check when index is a literal in `[0, N)`) | **Deferred** — requires const generics; too narrow to justify before that RFC lands |

## Coverage Checklist (added 2026-08-19, not part of the original RFC; expanded 2026-08-19: split former item 5 into items 5 and 6; added item 9)

Retroactive breakdown of this RFC's distinct, fixture-testable normative claims,
as headed sections for ADR-0049 citation purposes only. The document above is
unchanged and remains the historical record. Deliberately excludes claims that
aren't independently observable from a program's behavior -- implementation
strategy, design rationale, or internal architecture discussion belongs in the
RFC's own prose, not here.

### 1. `[T; N]` denotes a fixed-size array type

`N` is a non-negative integer literal and participates in type identity, so
`[i64; 3]` and `[i64; 4]` are different types. `[T; 0]` is a valid fixed-size
array type.

### 2. A repeat array expression evaluates its element expression once

`[expr; N]` produces a `[T; N]` by evaluating `expr` once and cloning that
result for all `N` elements. It does not evaluate `expr` independently for each
element.

### 3. An array literal can construct an expected fixed-size array

Where `[T; N]` is expected, `[e1, ..., eN]` is accepted only when it has exactly
`N` elements of type `T`. Without an expected array type, an array literal
defaults to the general-purpose `T[]` view type.

### 4. A fixed-size array coerces to `T[]` in one direction

`[T; N]` may be passed or bound where `T[]` is expected, including at a generic
call site. A `T[]` value does not implicitly coerce to `[T; N]`.

Fixture: `metel-interpreter/tests/integration/sources/typechecking/types/stage3_neg_10_sized_array_dynamic_to_fixed.mtl`

### 5. Fixed-size arrays may be used as field types

`[T; N]` is valid in a struct field.

### 6. Fixed-size arrays may be nested

A fixed-size array may itself have a fixed-size array element type, for example
`[[i64; 4]; 4]`.

### 7. Fixed-size array patterns must have a compatible element count

An exact array pattern such as `[a, b, c]` matches a `[T; 3]` value by position.
An exact pattern with a different element count is rejected for that fixed-size
array type.

### 8. Array length is not a generic type parameter

This feature accepts integer literals in `[T; N]`, not a named const parameter
or arbitrary runtime size expression. A function cannot be polymorphic over a
fixed-array length through this RFC's syntax.

### 9. Literal indexing into an empty fixed-size array is statically rejected

Because every literal index is out of bounds for `[T; 0]`, indexing one with a
literal is a type error. A non-literal index remains a runtime bounds error.

Fixture: `metel-interpreter/tests/integration/sources/typechecking/types/stage3_neg_11_sized_array_zero_literal_index.mtl`
