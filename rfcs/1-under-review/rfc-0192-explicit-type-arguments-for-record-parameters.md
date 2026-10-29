---
id: rfc-0192
title: "Explicit Type Arguments for Record Parameters"
date: '2026-10-29'
status: under-review
updated: '2026-10-29'
tracking: 'https://github.com/metel-lang/metel-core/issues/1664'
---

> **Status — under review (2026-10-29).** design drafted; tracked by metel-core#1664 (Records and surface syntax); one open question (arity until a placeholder exists)

## Summary

A turbofish argument for a `record R` parameter is **the record `R`**, the remainder that the
signature splices as `..R`. Arguments pin a function's declared generics in declaration order,
record parameters included, and a mixed list works.

```metel
fun get_x<record R>(p: { x: i64, ..R }) -> i64 { p.x }

get_x::<{ name: i64 }>({ x = 1, name = 2 })     // R = { name: i64 }; p : { x: i64, name: i64 }

fun tag<T, record R>(t: T, p: { id: u32, ..R }) -> (T, u32) { (t, p.id) }

tag::<String, { ok: boolean }>("a", { id = 7, ok = true })
```

Today the first call is `T0004: explicit type arguments are not supported on get_x: it takes an
open-record parameter`, and no function with a `..R` parameter can be called with `::<…>` at
all (GAP-FUNCTIONS-005, metel-core#1647). This RFC settles the language rule so that gap can
close. It amends the turbofish rule (`spec.functions.turbofish.legality-1`, RFC-0023) and adds
no syntax.

---

## Motivation

RFC-0186 removed the `row` generic kind: a parameter standing for a record is declared
`record R`, and `..R` is "the row of `R`". After it, `R` is an ordinary type-kinded parameter
that happens to be a record, so there is no reason its type argument should be special. The one
thing still missing is a statement of what is written for it.

The need is the same as for any turbofish (RFC-0023): a type parameter that the arguments do not
determine. For a record parameter that arises when:

- **The row only appears in the return type.** `fun empty_with<record R>(x: i64) -> { x: i64, ..R }`
  has nothing to infer `R` from at the call.
- **The inferred row is wider than intended.** Passing a record with extra fields infers a `R`
  that includes them; the author wants to state the narrower row the function is meant to see
  (width subtyping, RFC-0121).
- **A mixed list.** `fun f<T, record R>(…)` cannot pin `T` at all while any `record` parameter
  with a `..R` splice rules out `::<…>`, so a record parameter takes the ordinary parameters
  down with it.

### What blocks it today

The reason in metel-core#1647 is implementation, not language: the checker's scheme quantifies a
synthetic variable for `p`'s own open-record type in addition to the declared `R`, and orders
quantified variables by variable identity, not declaration. The language rule below is
independent of that; it only has to say which type each argument denotes.

---

## 1. The rule

### What the argument is

For a generic parameter `record R` (optionally with a row bound, `record R: { name, .. }`), the
type argument is a **record type**: an anonymous record or a `record` declaration. It is `R`
itself, not the record that contains it:

- In `p: { x: i64, ..R }`, `R = { name: i64 }` makes `p`'s type `{ x: i64, name: i64 }`. The
  argument is the remainder, the thing `..R` splices.
- In `p: R` (no splice), `R` is the whole parameter type; this is the case that already works
  (`make::<{ name: i64 }>({ name = 2 })`) and is unchanged.
- An argument that is a `record` declaration is accepted. `R` keeps its brand where it is used as
  `R`, and `..R` forgets it (RFC-0186 §1).

### What it must satisfy

The argument is checked exactly as an inferred `R` would be:

1. **The row bound** (`record R: { name, .. }`, negative bounds, RFC-0118/0189) and any
   `where R = …` equation hold of the argument.
2. **The field-wise bound** `where ..R: A` holds of every field type of the argument
   (RFC-0123, RFC-0186).
3. **Disjointness.** A label written next to `..R` must be absent from `R`
   (`{ x: i64, ..R }` with `R = { x: i64 }` is rejected, `T0012`, naming `x`).
4. **The call's arguments unify** with the parameter types so obtained, per
   `spec.functions.turbofish.legality-2`.

A struct or enum as the argument is rejected with the same message as `record R` inferred to one.

### Which arguments, in which order

Type arguments pin the function's **declared** generics in the order the generics are declared,
including `record` parameters; mixed lists (`<T, record R>`, `<record R, T>`) are in
declaration order. The same "expected N type arguments, got M" error applies when the count is
wrong, and N counts declared generics only.

Anonymous open tails (`{ x: i64, .. }`, RFC-0181) and the synthetic type of such a parameter are
not declared generics, so they are neither counted nor pinnable.

### Out of scope

- **A placeholder (`_`).** Naming only some of a function's generics is an arity error today
  for ordinary parameters (`first::<i64>(1, 2)` on `first<A, B>` is `T0004`), and `_` is not
  a type. Both are general turbofish questions, not record-parameter ones; they would be settled
  in their own RFC and apply to every parameter kind. Until then, a mixed list writes the record
  argument in full.
- **Methods.** Turbofish on a method pins the method's own generics (RFC-0099 §4); generics of an
  enclosing `extend<record R>` come from the receiver and are not pinnable.
- **Splice arguments** (`f::<..S>`). The parser keeps rejecting a `..R` in an explicit argument
  list; the argument is the record, not its row.

---

## 2. Interactions

- **RFC-0186.** This is its open question 5 (explicit instantiation), answered by the fact that
  `record R` is an ordinary type parameter.
- **RFC-0138 (generic functions as first-class values).** Turbofish stays fused to the call
  (`spec.functions.turbofish.legality-3`); instantiation without a call remains out of scope.
- **RFC-0099 (`::<` becomes `.<`).** Examples use `::<`; the rule does not depend on spelling.
- **RFC-0187 / RFC-0188.** Records in type-argument position are written with whatever delimiter
  RFC-0187 settles on (`{| … |}` if it extends to types, which is one of its open questions).
- **RFC-0189.** Negative bounds are checked on the argument like positive ones.

---

## Alternatives Considered

1. **Status quo (rows are inferred, never pinned).** Works while a row is always determined by the
   arguments. Rejected because it makes `::<…>` all-or-nothing across a function's kinds, and the
   rows that cannot be inferred (return position, intentional narrowing) have no spelling at all.
2. **The argument is the whole open record (`get_x::<{ x: i64, name: i64 }>`).** Reads naturally for
   `p: R`, but for `{ x: i64, ..R }` it asks the author to repeat the fixed labels and then
   derive `R` by subtraction, which a rigid parameter (RFC-0173) never does. It also makes the
   argument depend on how the signature happens to split the record.
3. **A separate row-argument position (`get_x::<; name: i64>` or `get_x::<..{ name: i64 }>`).** A
   second list for the same declared generics. It exists only because the `row` kind did, and
   RFC-0186 removed it.
4. **Allow partial lists now (`_` or trailing defaults).** Valuable, but it changes every generic
   call and is unrelated to rows; folding it in would make this RFC a turbofish redesign.

---

## Open question

**Is all-or-nothing arity acceptable for mixed lists until a placeholder exists?** A function
`fun f<T, record R>` whose `R` is inferable but whose `T` is not must write `R` out to pin `T`
(`f::<u8, { ok: boolean }>(…)`). That is the same cost an ordinary two-parameter function pays
today, and `{ … }` record arguments are short, but a wide row is not. If review finds this too
costly the placeholder RFC moves ahead of this one; the rule above does not change.

---

## Specification impact

Spec text lands only at `3-integrated`. `reference/spec/functions.md` *Turbofish*:
`legality-1` states that arguments pin the declared generics in declaration order and that the
argument for a `record` parameter is the record (new Legality Rule for the argument's checks
and for the count); the `> Gap GAP-FUNCTIONS-005` marker is removed on implementation. The
bounded/negative-bound checks reuse `T0012`; a wrong count is the existing `T0004`. No new error
code.

## Implementation notes

Implementation detail goes in an ADR at `3-integrated`, not here. The constraints:

- The scheme records the declared generics and maps each to its quantified variable, so arguments
  zip in declaration order instead of by `TypeVar` order.
- A pinned `R` determines the synthetic open-record variable of each parameter that splices `..R`
  (the type is the written fixed fields plus the argument's row); the checker then runs the same
  bound and disjointness checks it runs for an inferred `R`.
- The `T0004` rejection added for #1646 is removed when this lands.

## References

- RFC-0023 (Type Ascription vs Turbofish): the rule this extends.
- RFC-0186 (Rows as an Operator on Record Parameters): `record R`, `..R`, the removed `row` kind.
- RFC-0121 (Open Rows), RFC-0173: rigidity of `R`, why the argument is the remainder.
- RFC-0099: turbofish respelling.
- GAP-FUNCTIONS-005; metel-core#1646, #1647.

---

## Decision

**Outcome:** *(pending)*
