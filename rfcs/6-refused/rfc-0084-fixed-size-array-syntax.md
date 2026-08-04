---
id: rfc-0084
title: "Fixed-Size Array Syntax — Retaining [T; N]"
date: '2026-07-01'
updated: '2026-07-10'
status: refused
---

> **Status — accepted. Rewritten 2026-07-10, reversing this RFC's original 2026-07-01
> conclusion.** The original text replaced RFC-0053's `[T; N]` with postfix `T[N]` and
> removed the `[expr; N]` repeat-construction expression. On reconsideration, both
> changes are reverted: the type syntax stays `[T; N]` (Rust-derived, as RFC-0053
> specified it), and `[expr; N]` is kept. Depends on RFC-0053 for semantics, unchanged
> throughout.
>
> Two things make this a clean reversal rather than a contested one:
>
> 1. **The collision that motivated removing `[expr; N]` no longer exists.** §2.3 of the
>    original text removed repeat construction because it collided with "the region
>    bracket channel," citing `@[r] expr` (RFC-0063 as it stood on 2026-07-01). RFC-0063
>    was itself rewritten 2026-07-05 — four days later — from that bracket-based region
>    syntax to the current tag-based `@a T` / `@a expr` (see
>    `public/rfcs/2-accepted/rfc-0063-allocator-handles.md`), which uses no
>    brackets at all. The specific ambiguity this RFC gave up `[expr; N]` to avoid
>    evaporated independently, four days after this RFC cited it.
> 2. **Reverting costs nothing.** RFC-0084 was accepted but never implemented or applied
>    — `public/reference/spec/types.md`, `expressions.md`, `runtime.md`, the changelog,
>    and the getting-started tutorials all still use `[T; N]` today, exactly as RFC-0053
>    left them. There is no migration in either direction; this RFC now simply stops
>    proposing one.

> **Status — refused (2026-07-10).** Reverted 2026-07-10 to reaffirm RFC-0053's [T; N]/[expr; N] exactly, with no remaining change of its own to propose (see the RFC's own Migration section: 'None'). Refusing rather than leaving it accepted-but-inert, since it no longer does anything RFC-0053 doesn't already specify.

## Summary

RFC-0053 introduced the fixed-size array type with Rust-derived syntax `[T; N]` and the
repeat-construction expression `[expr; N]`. This RFC's original text (2026-07-01)
proposed replacing `[T; N]` with the postfix form `T[N]`, for consistency with the
dynamic-array convention `T[]`, and removed `[expr; N]` as colliding with region-handle
bracket syntax. **This rewrite keeps `[T; N]` and `[expr; N]` exactly as RFC-0053
specified them.** Nothing about fixed-size arrays changes as a result of this RFC.

---

## Motivation for the reversal

The postfix-consistency argument for `T[N]` was real and is not retracted here: `T[]`
(dynamic array) and `[T; N]` (fixed-size array) do use two different bracket
conventions for what is structurally the same construct with an added size constraint.
That inconsistency still exists in the language as specified. It is outweighed here by:

- **Rust familiarity.** `[T; N]` and `[expr; N]` are literally Rust's syntax for this
  feature — no relearning for the population of users this project is most directly
  positioned to draw from. Consistency with `T[]` is a real but purely internal
  aesthetic; consistency with a syntax convention users already know is worth more.
- **Zero cost to reverting now, real cost to proceeding.** Nothing in the public spec,
  the changelog, or the tutorials was ever updated to `T[N]` — RFC-0084 sat accepted but
  unimplemented since 2026-07-01. Reverting is free. Proceeding would require rewriting
  all of the above, plus every internal RFC example already written against `[T; N]`
  (RFC-0061, RFC-0092, and others), for a purely cosmetic gain.
- **The removal of `[expr; N]` is no longer motivated at all.** Independently of the
  `T[N]` question, §2.3's collision with the region bracket channel stopped being true
  once RFC-0063 moved to `@a`/`@a expr`. Keeping `[expr; N]` removed today would be
  paying a real ergonomic cost (users write explicit loops to build a repeated-element
  array) for a conflict that no longer exists.

---

## 1. Type Syntax — `[T; N]`, unchanged from RFC-0053

```
[T; N]
```

`T` is any type; `N` is a compile-time integer constant (a non-negative integer literal,
or, once RFC-0092's comptime core is accepted, a `comptime`-evaluable expression). Two
fixed-size array types are equal only when both element type and size match: `[i64; 3]`
and `[i64; 4]` are distinct types. `T[]` (dynamic array) is unrelated and unchanged.

### 1.1 Nested arrays

`[[f64; 4]; 4]` is the matrix type: a fixed-size array of 4 elements, each itself a
fixed-size array of 4 `f64` values. The outer dimension is written outermost (leftmost),
matching ordinary Rust-style nesting — this is the opposite reading order from the
postfix `f64[4][4]` this RFC's original text proposed, which wrote the outer dimension
last.

```metel
let matrix: [[f64; 4]; 4] = [
    [0.0, 0.0, 0.0, 0.0],
    [0.0, 0.0, 0.0, 0.0],
    [0.0, 0.0, 0.0, 0.0],
    [0.0, 0.0, 0.0, 0.0],
];
```

---

## 2. Expression Syntax — `[expr; N]`, kept

Repeat construction evaluates `expr` once and clones the result `N` times:

```
[expr; N]
```

If `expr` has side effects, it is still evaluated exactly once — matching Rust's
semantics and avoiding a divergence between `[f(); 3]` and `[f(), f(), f()]`. To
evaluate an expression `N` times independently, use a loop.

Literal construction (`[e1, e2, e3]`) and repeat construction (`[expr; N]`) are
distinguished the same way Rust distinguishes them: by what follows the first element —
a comma starts a literal, a semicolon starts a repeat. This RFC's original text treated
that distinction as insufficiently robust once region bracket syntax entered the
picture; with that syntax gone (see status note above), the distinction is unambiguous
again.

```metel
let zeros: [i64; 5] = [0; 5];       // repeat construction
let ones: [i64; 3] = [1, 1, 1];     // literal construction
```

---

## 3. Unchanged from RFC-0053

Everything else RFC-0053 specified is unaffected by this RFC, in either direction:

- **Coercion.** `[T; N]` coerces implicitly to `T[]`; the reverse is a type error.
- **Struct fields.** `[T; N]` is a valid field type.
- **Pattern matching.** `[a, b, c]` matches a `[T; 3]` exactly; a count mismatch is a
  type error.

  ```metel
  fun sum(xs: [i64; 3]) -> i64 {
      match xs {
          [a, b, c] => a + b + c,
      }
  }
  ```
- **Generics limitation.** Without const generics, `N` cannot appear as a type
  parameter; `fun reverse<T>(arr: [T; N]) -> [T; N]` remains unwritable until a const
  generics RFC exists.
- **Runtime representation.** `[T; N]` uses the same `Value::Array` representation as
  `T[]`; the size constraint is enforced statically only.

---

## 4. Migration

None. This RFC reverts to what RFC-0053 already specifies and what
`public/reference/spec/`, the changelog, and the tutorials already show. No spec text,
example, or (per the roadmap) interpreter code needs to change as a result of this RFC.

---

## 5. Alternatives Considered

### `T[N]` (postfix, this RFC's own original 2026-07-01 proposal)

Real consistency argument with `T[]` (see "Motivation for the reversal" above), and
resolves the literal-vs-repeat-construction ambiguity by construction (the size sits
outside a distinct bracket pair from the literal). Rejected on reconsideration: the
ambiguity it resolves no longer exists once `[expr; N]` doesn't collide with anything,
and it trades Rust-familiar syntax for internal consistency at a real (if one-time)
migration cost across specs and RFC examples that was never actually paid.

### `Array<T, N>` (generic struct)

Avoids bracket syntax entirely; self-evidently readable but requires const generics
(not yet specified). Deferred, as in the original text; if const generics land,
`Array<T, N>` could exist as an alias alongside `[T; N]`, not instead of it.

### `[N]T` (Go-style prefix)

Places the size before the type. Rejected, as in the original text — it does not
resolve anything `[T; N]` doesn't already resolve, and is less familiar than either
`[T; N]` or `T[N]` to this project's likely audience.

---

## Unresolved Questions

None.

---

## References

- RFC-0053 (Fixed-Size Array Type, implemented) — this RFC reaffirms its syntax in
  full rather than replacing any part of it.
- RFC-0063 (Allocator Handles) — the bracket-syntax collision this RFC's original text
  cited to justify removing `[expr; N]` no longer exists; RFC-0063 moved from
  bracket-based region syntax to tag-based `@a`/`@a expr` on 2026-07-05.
- RFC-0092 (Comptime Core) — will extend valid `N` expressions beyond integer literals;
  its examples use `[T; N]` per this RFC.
- RFC-0061 (Structural Aspect Bounds) — references fixed-size arrays in §1 (structural
  type constructors); no syntax-specific text there requires updating.
