---
id: rfc-0208
title: "Row-Only Generic Parameters"
date: '2026-11-02'
status: draft
---

## Summary

A generic parameter that stands only for a row, never for a type, is declared with a **row
binder**, `<..R>`. `record R` is kept for parameters that are used as types.

```metel
extend<record R> { ..R }: Display where ..R: Display    // today: R is never used as a type
extend<..R> { ..R }: Display where ..R: Display         // proposed: the binder says "a row"

fun get_x<..R>(p: { x: i64, ..R }) -> i64 { p.x }
fun sum<record T>(p: T) -> T { p }                      // unchanged: T is used as a type
```

A row parameter is written `..R` at every use, as today: in a record type's tail
(`{ x: f64, ..R }`), in a nominal type's argument list (`Packet<..R>`), in a struct's residual
tail (`Handle.{ fd, ..R }`) and in a field-wise bound (`where ..R: A`). A bare `R` is not a type,
and naming it is an error. The change adds a binder and removes nothing: `record R` keeps its
current meaning, and `row` does not return as a keyword.

This is an additive amendment to RFC-0186 (implemented), which merged the `row` kind into
`record R`. It does not reverse that RFC. It splits `record R` by what the parameter is used as,
not by a second reserved word.

---

## Motivation

RFC-0186 removed the `row` kind because it was "two kinds for one idea": `record R` and `row R`
both stand for a set of fields. That argument holds when the parameter is a record. It does not
hold when the parameter is only ever the *row* of something, and `record R` then says more than
the code means:

- **It misleads at the binder.** In `extend<record R> { ..R }: Display where ..R: Display`,
  `R` is never a type. It appears only as `..R`. A reader of `<record R>` expects a record
  type they can name.
- **It names a brand the code never uses.** RFC-0186 §Open Question 5 records that a
  `record R` instantiated by a branded record keeps the brand, and `..R` forgets it. A
  parameter that is only ever spliced can never observe a brand, so the keyword promises a
  distinction the code cannot use.
- **A struct's residual tail is not a record.** `Handle.{ fd, ..R }` splices the remaining
  fields of a struct. `R` there is the tail of a branded row, and declaring it `record R`
  suggests a standalone record. Impls that are generic over a struct's row (the Copy/Clone
  derivation in RFC-0209) are written entirely in these tails.
- **It turns on a real distinction in turbofish.** RFC-0192 makes the argument for a
  `record R` parameter "the record `R`, the remainder that the signature splices as `..R`".
  A row-only parameter makes that explicit: its argument is a row, with no type to bind.

Two alternatives were weighed and declined (see Alternatives): restoring the `row` keyword, and
inferring the kind from a `..` use.

---

## 1. The row binder

`..R` in a generic parameter list declares **R** as a row parameter: zero or more labelled
fields. It matches the pack binder `<..Ts>` of RFC-0125 and every use of `..R` in the corpus.

| | `record R` | `..R` |
|---|---|---|
| R is | a record type | a set of labelled fields, no brand |
| usable as a type | yes (`p: R`) | no |
| usable as `..R` | yes | yes |
| instantiated with a branded record | keeps the brand | forgets it (there is none to keep) |
| turbofish argument (RFC-0192) | the record | the row, written as a record type |

**Legality.**
1. A row parameter may be used only under `..`: as a record type tail, a nominal argument,
   a residual tail, or the operand of a field-wise bound. Any other use of the bare name is
   `T0012`, with a fix-it suggesting `record R` if the code needs the type.
2. `where ..R: A` bounds every member of the row, exactly as RFC-0186 specifies. `where R: A`
   is not valid for a row parameter, because a row implements no aspect.
3. A row parameter has no bounds in the binder; a lower bound on its fields is written in the
   `where` clause, as for `record R`.
4. A parameter declared `..R` may be instantiated with any row: an anonymous record's, a
   struct's or `record` declaration's declared row, or a residual's row. The brand is never
   part of the instantiation.

**Dynamic semantics.** None. A row parameter is erased exactly as a `record R` parameter is.

---

## 2. Relationship to packs

RFC-0125 declares a type-parameter pack with the same binder token, `<..Ts>`. The two differ in
what they stand for and where they may be spliced:

- a pack is an ordered list of types, spliced into a tuple type `(..Ts)` or a bound `..Ts: A`;
- a row is an unordered set of labelled fields, spliced into a record tail, a nominal argument
  or a residual tail.

The binder alone does not say which kind a parameter is, and a bound `where ..X: A` reads the
same for both. The checker takes the kind from where the parameter is spliced in the signature
and rejects a parameter spliced in both a tuple position and a record position. If RFC-0151
(tuples as numeric-label rows) is accepted, a tuple is a row, a pack is a row with numeric
labels, and the two binders merge into one kind. This RFC does not depend on that.

---

## 3. Alternatives considered

1. **Restore the `row` kind** (`<row R>`). Declined: it reverses RFC-0186, which rewrote 192
   fixtures and the standard library, and it leaves `<row R>` beside the pack binder `<..Ts>`.
   Its one unique benefit, a bound without dots (`where R: Clone`), was considered and is not
   wanted: the dots already say "the members of", and a row bound that differs from a pack
   bound would be an inconsistency.
2. **Infer the kind from a `..` use**, so a bare `<R>` becomes a row if it is spliced.
   Declined: a bare `..R` in a bound is ambiguous between a row and a pack; the kind becomes
   implicit and depends on other parts of the signature; hover text, documentation and
   diagnostics must show an inferred kind; and a declaration `<R>` becomes indistinguishable
   from a plain type parameter. It would be safe only where the parameter is used under `..`
   exclusively, which is when the brand cannot matter.
3. **Keep `record R` and document it.** No churn. The misleading name stays, and the residual
   tail `Handle.{ fd, ..R }` is still declared as a record.

---

## 4. Costs

- **A new binder form** in the parser, the registry's kinds on type parameters, projection
  checking and diagnostics. It adds a kind check to every use of a bare parameter name.
- **Migration is optional.** `record R` parameters used only as `..R` keep working. Whether to
  lint them, or rewrite the standard library and the corpus (RFC-0186 counted 192 fixtures and
  6 standard-library sites binding a row), is an open question.
- **Two parameters that look alike.** `<record R>` and `<..R>` differ in a single token, and a
  reader must know the rule above. The error and fix-it in Legality 1 are the mitigation.

---

## Relationship to existing RFCs

- **RFC-0186** — amended additively. It stays implemented; `record R` is unchanged.
- **RFC-0121 / RFC-0123** — open rows and field-wise constraints, the origin of `..R` and
  `where ..R: A`.
- **RFC-0125** — variadic generics; shares the binder token. A conflict in kind is rejected, as
  in section 2.
- **RFC-0151** — tuples as numeric-label rows; would merge packs and rows.
- **RFC-0137 / RFC-0146** — branded rows and row-polymorphic self-views, the places a residual
  tail appears.
- **RFC-0192** — turbofish for record parameters; its argument rule for a row parameter is an
  open question below.
- **RFC-0209** — per-aspect row visibility (RFC-0207 is now only the colon list and `derives`); its derivation template is written with row-only
  parameters, which is the motivating use.

## Open questions

1. **Turbofish for a row parameter** (RFC-0192): is the argument written as a record type
   (`{ name: i64 }`), or with the dots (`..{ name: i64 }`)? The first matches RFC-0192 as it
   stands.
2. **Row equations** (`where R = { token: Token, ..Rest }`, RFC-0121): how the left side is
   written when `R` is declared `..R`. Presumably `..R = { … }`.
3. **A lint or rewrite** for `record R` parameters used only as `..R`.
4. **Whether a row parameter may carry a lower bound in the binder**, as `record R` does with
   `record R: { x: f64, .. }`.
5. **Merging with packs** if RFC-0151 is accepted: one `..X` kind with a shared binder.
6. **Residual tails**: whether `Handle.{ fd, ..R }` with `R` declared `..R` needs a rule about
   the brand being the struct's, and how it interacts with RFC-0146's `Self.R`.

---

## Decision

**Outcome:** *(pending)*
