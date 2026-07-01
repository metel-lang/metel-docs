---
id: rfc-0084
title: "Fixed-Size Array Syntax — T[N]"
date: '2026-07-01'
---

> **Status — accepted.** Supersedes the type syntax introduced in RFC-0053 (Fixed-Size
> Array Type). Depends on RFC-0053 for the semantics of fixed-size arrays; this RFC
> changes only the surface syntax. The replacement syntax must be implemented and the
> public spec updated before RFC-0053 is considered fully superseded.

## Summary

RFC-0053 introduced the fixed-size array type with Rust-derived syntax `[T; N]`. This
syntax conflicts with Metel's existing array convention: dynamic arrays use the postfix
form `T[]`, so `T` followed by `[]` means "array of T." Fixed-size arrays should
follow the same postfix convention. This RFC replaces `[T; N]` with `T[N]`.

---

## Motivation

The two array type syntaxes in the current language are structurally inconsistent:

| Type | Syntax | Convention |
|---|---|---|
| Dynamic array | `T[]` | Postfix — the element type comes first |
| Fixed-size array | `[T; N]` | Prefix bracket — the element type is inside |

A reader who sees `i64[]` and `[i64; 3]` in the same codebase must remember two
unrelated syntactic conventions for what is fundamentally the same construct with an
additional size constraint.

`[T; N]` also introduces two independent sources of visual ambiguity:

1. It resembles an array literal expression: `[1, 2, 3]` creates a `T[]`; `[T; N]`
   looks like it might create a fixed-size literal, not name a type.
2. The repeat construction expression `[expr; N]` (also from RFC-0053) uses the same
   bracket-semicolon form, making the distinction between the type and the expression
   form rely entirely on what is inside the brackets.

`T[N]` resolves both problems. It extends `T[]` uniformly: `T[]` is "an array of T
with unspecified length"; `T[N]` is "an array of T with length N." The size is a
postfix annotation, not a wrapper.

---

## 1. New Type Syntax

### 1.1 Replacement

The fixed-size array type is now written with the size inside the postfix brackets:

```
T[N]
```

where `T` is any type and `N` is a compile-time integer constant (non-negative integer
literal or, when RFC-0055 is accepted, a comptime expression).

Old and new forms side-by-side:

| Old | New |
|---|---|
| `[i64; 3]` | `i64[3]` |
| `[f64; 0]` | `f64[0]` |
| `[[f64; 4]; 4]` | `f64[4][4]` |
| `[String; 8]` | `String[8]` |

`T[]` (dynamic array) is unchanged.

### 1.2 Grammar

Old rule:

```
Type ::= … | "[" Type ";" INT "]"
```

New rule — the two array forms are now both postfix variants of the same grammar
production:

```
Type ::= TypeBase ArraySuffix*
ArraySuffix ::= "[" "]"          // dynamic array: T[]
              | "[" INT "]"      // fixed-size array: T[N]
```

This grammar also naturally expresses nested fixed arrays: `f64[4][4]` parses as
`(f64[4])[4]` — a fixed-size array of 4 elements, each a fixed-size array of 4
`f64` values.

### 1.3 Nested arrays

`f64[4][4]` is the matrix type. The outer dimension is written last, matching the
postfix left-to-right order:

```metel
let matrix: f64[4][4] = [
    [0.0, 0.0, 0.0, 0.0],
    [0.0, 0.0, 0.0, 0.0],
    [0.0, 0.0, 0.0, 0.0],
    [0.0, 0.0, 0.0, 0.0],
];
```

This is equivalent to the old `[[f64; 4]; 4]`. The reading is: "`f64`, in a
fixed-size array of 4, in a fixed-size array of 4."

---

## 2. Unchanged

### 2.1 Semantics

All semantics from RFC-0053 are unchanged: two-way distinct types keyed on both
element type and size; coercion from `T[N]` to `T[]`; no reverse coercion; `T[0]`
is valid; indexing and `for-in` work identically to `T[]`.

### 2.2 Literal construction

Array literals are typed by context and are unchanged:

```metel
let ones: i64[3] = [1, 2, 3];   // literal [1, 2, 3] typed as i64[3]
let dyn: i64[] = [1, 2, 3];     // same literal typed as i64[]
```

### 2.3 Repeat construction — removed

The repeat construction expression `[expr; N]` is **removed**. It uses the same
bracket form as the region bracket channel (RFC-0063), which takes priority. No
replacement syntax is specified at this stage; fixed-size arrays are constructed via
explicit literals or loops.

### 2.4 Pattern matching

Array patterns are unchanged:

```metel
fun sum(xs: i64[3]) -> i64 {
    match xs {
        [a, b, c] => a + b + c,
    }
}
```

The pattern `[a, b, c]` matches a `T[3]`; an incorrect count is a type error.

### 2.5 Coercion

`T[N]` coerces to `T[]` implicitly. The coercion rule from RFC-0053 is unchanged; only
the type name in the source changes.

---

## 3. Migration

Two breaking changes:

1. **`[T; N]` → `T[N]` in type position.** Mechanical replacement.
2. **`[expr; N]` repeat construction is removed.** Call sites must be rewritten
   as explicit array literals or loops.

The public spec (types.md, grammar.md, expressions.md, runtime.md) and all internal
RFC examples using `[T; N]` or `[expr; N]` must be updated as part of implementing
this RFC.

---

## 4. Alternatives Considered

### Keep `[T; N]`

Retaining the existing syntax avoids a breaking change but leaves a permanent
inconsistency in the type system. Every future occurrence of fixed-size arrays in
specs, RFCs, and user code requires readers to hold two conventions simultaneously.

### `Array<T, N>` (generic struct)

A fully generic notation avoids the bracket syntax entirely. It is self-evidently
readable but requires const generics (not yet specified) and breaks the visual
uniformity with `T[]`. Deferred; if const generics land, `Array<T, N>` could be an
alias.

### `[N]T` (Go-style prefix)

`[N]T` places the size before the type. It differs from `T[]` (size after), making it
inconsistent in the opposite direction. Rejected.

---

## Unresolved Questions

None.

---

## References

- RFC-0053 (Fixed-Size Array Type) — semantics specification this RFC replaces the
  syntax of; moves to superseded status when this RFC is implemented.
- RFC-0055 (Comptime, draft) — will extend valid `N` expressions beyond integer
  literals.
- RFC-0061 (Structural Aspect Bounds) — references fixed-size arrays in §1 (structural
  type constructors); the `T[N]` syntax applies there.
