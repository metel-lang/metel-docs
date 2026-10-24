---
id: rfc-0186
title: "Rows as an Operator on Record Parameters"
date: '2026-10-24'
status: under-review
updated: '2026-10-24'
tracking: 'https://github.com/metel-lang/metel-core/issues/1597'
---

> **Status — under review (2026-10-24).** design settlement committed to a release milestone (tracking issue linked).

## Summary

Remove the `row` generic-parameter kind and the `where all` field-wise constraint, and let
the existing `..` spread be the one way to get at a record's row. A generic parameter that
stands for a record is declared `record R` (as `record T` already is), and `..R` is an
operator on it that yields **R's row**. Everything `row R` and `all R` did is spelled with
that operator:

```metel
// before                                              // after
fun get_x<row R>(p: { x: f64, ..R }) -> f64            fun get_x<record R>(p: { x: f64, ..R }) -> f64
fun consume<row R>(r: { ..R }) where all R: Copy       fun consume<record R>(r: { ..R }) where ..R: Copy
extend<row R> { ..R }: Display where all R: Display    extend<record R> { ..R }: Display where ..R: Display
record Packet<row R> { data: { ..R } }                 record Packet<record R> { data: { ..R } }
fun f<row R>(p: Packet<..R>) -> ...                    fun f<record R>(p: Packet<..R>) -> ...
```

Two mechanical rewrites cover existing code: `row` becomes `record` at the binder, and
`where all R: A` becomes `where ..R: A`. Every use of `..R` is unchanged. `row` stops being a
reserved word.

This amends RFC-0121 (open rows) and RFC-0123 (field-wise constraints), both implemented.
It is a breaking change to shipped syntax and needs this RFC first (see
`metel_rfc_before_implementation`).

---

## Motivation

### 1. Two kinds for one idea

Today a generic parameter that stands for a record comes in two forms
(`generic_param = (record_kw | row_kw)? ~ ident …`):

- `record T` (optionally `: { x: f64, .. }`): a type variable that is *a record*. The body
  can use `T` as a type: `fun f<record T: { x: f64, .. }>(p: T)`.
- `row R`: a variable that is *the rest of a record's fields*. The body cannot name `R` as a
  type; it can only write `..R` inside a record type or a nominal type's argument list.

The spec's own map of the area ("Records and Rows at a Glance") lists them as rungs of a
ladder, but they differ only in what the variable may be *written as*. A row is the set of
labelled fields, and the spec says an anonymous record *is* its row, while a `struct` or
`record` declaration is a brand paired with a row. The second kind exists because the first has no way to say
"the fields of T", not because the two describe different things.

Measured against the current build: `fun get_x<record R>(p: { x: i64, ..R })` is rejected
with `T0012: R is not a row parameter; declare it <row R>`, so the two kinds are not
interchangeable today even though both stand for a set of fields.

### 2. `..` already means "the fields of" everywhere else

RFC-0178 added value-level `..` forms that all read as "the fields of this record":

- a rest pattern `{ token, ..rest }` binds the remaining fields;
- a record-literal spread `{ ..rest, auth = a }` places a record's fields into a new one.

The type level uses the same token (`{ x: f64, ..R }`), but with a different grammar:
`..` followed by a *row variable*, which can only be declared with the special `row` binder.
If `..` is an operator on a record, the value level and the type level say the same thing:
`..r` is the fields of the value `r`, and `..R` is the fields of the type `R`.

### 3. Two extra words to learn

`row` is a reserved word (`grammar.pest`'s reserved list) used in exactly one place, the
binder. `all` is a contextual keyword used in exactly one place, the field-wise constraint.
RFC-0125 (variadic generics) then reuses `all` for packs ("the same construct … quantified
over an ordered list"). Each is a word a reader must learn that does one job.

### 4. `where all R: A` sits oddly next to `where R: A`

Both bound `R`; they mean different things (the record as a whole versus each of its fields),
and the difference is carried by a keyword in front of the name. With an operator the
difference is on the thing being bounded: `R: A` bounds the record, `..R: A` bounds its row,
meaning each field. That is how the spec already explains the constraint ("it constrains
`R`'s field *contents*").

---

## 1. The change

### One kind, `record`

A generic parameter is a type, or `record`-kinded. The `row` kind is removed. A `record R`
parameter stands for a record type: an anonymous record or a `record` declaration (not a
`struct` or `enum`, whose rows are not visible to bounds and impls, per the same section).
Everything the spec already says about `record T` applies unchanged, including row bounds
(`record R: { x: f64, .. }`) and negative bounds (`record R: !{ token }`).

### `..R` is an operator on a record parameter

`..R` is the **row** of `R`: its labelled fields, without any brand. It is valid only
where a row is wanted, and `R` must be `record`-kinded:

| position | meaning |
|---|---|
| the tail of a record type: `{ x: f64, ..R }` | the fields of `R`, spliced after `x` |
| the argument of a nominal type: `Packet<..R>` | the anonymous record `{ ..R }` |
| a struct's residual tail: `Handle.{ fd, ..R }` | as today, the remaining fields |
| the left side of a bound: `where ..R: Display` | each field of `R` (below) |

`..R` anywhere else, or on a parameter that is not `record`-kinded, is an error. Anonymous
`..` (`{ x: f64, .. }`) is unchanged.

`R` itself remains usable as a type. If `R` is an anonymous record, `R` and `{ ..R }` are the
same type. If `R` is a branded `record` declaration, `R` keeps its brand and `{ ..R }` is
the anonymous record with the same fields. In particular `..` is the one operation that
forgets a brand while keeping the fields: the spec describes a declaration as a brand paired
with a row, and `..R` is the "row" half of that pair.

### The field-wise constraint

`where ..R: A` holds when every field type in `R`'s row satisfies `A`, vacuously on an empty
row. It replaces `where all R: A` with the same meaning, the same walkable positions
(an open-record tail, a `where` decomposition's remainder, the tail of an `extend` target, a
row argument of a nominal type) and the same forwarding rule (it is forwarded only to
another `..R: A`).

`R: A` keeps its present meaning, a bound on the record as a whole. The two are distinct
forms of one bound list:

```metel
fun show<record R>(r: { ..R }) -> String where ..R: Display { … }   // each field is Display
fun dup<record R: Copy>(r: R) -> (R, R) { (r, r) }                  // the record is Copy
```

### What does not change

- Row bounds (`record R: { x, .. }`), negative bounds (`!{ token }`), and row equations
  (`where R = { token: Token, ..Rest }`). Equation sides are record types, so `Rest` is now
  declared `record Rest`.
- Disjointness: a label written next to `..R` must be absent from `R`, as for rows today.
- Rest patterns and record spreads at the value level (RFC-0178).
- Literal rows in row arguments (RFC-0180), `Req<..{ host: String, ..R }>`.
- Anonymous tails and where they are accepted (RFC-0181).
- Width subtyping and the by-value ownership rules for the extras.
- The `label L` kind proposed by RFC-0175: this RFC removes `row`, not other kinds.

### Diagnostics

`row R` becomes a targeted error ("the `row` kind was removed; declare `record R`"), and
`where all R: A` likewise ("write `where ..R: A`"). `..R` on a non-`record` parameter says
"`..R` takes the row of a record parameter; declare `record R`".

---

## 2. Alternatives considered

1. **Status quo.** Two kinds, one reserved word, one contextual keyword. Nothing breaks.
   The cost is the vocabulary in Motivation §§1, 3 and 4.
2. **Remove only `all`** (keep `row R`; `where ..R: A`). Smaller migration, and fixes §4. It
   leaves `row` and the difference between a row variable and a record variable, so the
   reasons for the second kind stay.
3. **Remove only `row`** (declare `record R`, keep `where all R: A`). Leaves `all` and the
   keyword-in-front-of-a-name form.
4. **A different operator for the constraint**, e.g. `where each R: A` or `where R.*: A`. A
   new keyword or token for what `..` already reads as. The point of the RFC is to reuse
   `..`.
5. **Keep `row` as a deprecated alias for one release.** A transitional option, not a design
   alternative: see Open Question 3.

---

## 3. Costs

- **A breaking rewrite of two shipped forms.** About 190 integration fixtures bind a `row`
  parameter and about 45 use `where all`; 49 Markdown files in this repository mention one of
  them. Both rewrites are purely lexical, but the spec sections for RFC-0121, RFC-0123,
  RFC-0178, RFC-0180 and RFC-0181 are amended, and so is the spec's own map of the area.
- **Implementation.** `row` is a kind in the parser, the AST, the registry (row kinds on type
  parameters), projection checking, and the type engine's row kinds. The change merges the
  kind and adds the operator check; it removes a parallel code path, but it touches every site
  that distinguishes the kinds.
- **The new reading of `..R: A` is not obvious.** A reader may take `..R: Display` to mean
  that the row is `Display` as a whole. The spec has to say once, clearly, that a bound on a
  row is a bound on each field, and the diagnostic for a missing bound should say so.
- **Churn in pending RFCs.** RFC-0125 (`all Ts: Copy` for packs), RFC-0146 (`Self.R`
  with `row R`), RFC-0174 (`fields(R)` examples) and RFC-0175 (draft) use `row R` or `all`.

---

## Open Questions

1. **Row arguments: keep `Packet<..R>` or write `Packet<R>`?** This draft keeps
   `Packet<..R>` and defines it as `Packet<{ ..R }>`, so no argument position changes. The
   alternative is that a `record`-kinded parameter of a nominal type takes a record type,
   so `Packet<R>` replaces `Packet<..R>`, which would also remove literal-row arguments
   (RFC-0180) in favour of ordinary record types. That is simpler but changes brand
   behaviour at the argument (§1: `R` keeps its brand, `{ ..R }` does not) and so should be
   decided separately.
2. **Variadic packs (RFC-0125).** Packs are declared `<..Ts>` and bounded `all Ts: Copy`. If
   `all` goes, the pack form is `..Ts: Copy`, the same operator over an ordered list instead
   of a row. RFC-0125 is under review; it should adopt the same spelling, or this RFC
   should carve `all` out for packs.
3. **Deprecation window or hard cut?** `row R` and `where all R: A` could still parse for one
   release with a warning and an automated rewrite, or be removed at once as RFC-0136 and
   RFC-0098 were.
4. **Can a generic body name `R` as a type when `R` is an anonymous remainder?** Today
   `{ ..R }` is the only spelling. With `record R`, a body can write `R`, which is the same
   type. Is the second spelling acceptable, or should the checker steer to one?
5. **`record R` instantiated by a branded `record`.** `..R` forgets the brand. Confirm that
   the places where today's row inference always yields an anonymous remainder (a call
   `get_x({ x = 1, name = "a" })` infers `R = { name: String }`) are unchanged, and that no
   rule relied on `row R` never being instantiated with a branded record.
6. **Release timing.** A language-visible, breaking change to generic declarations.

---

## References

- RFC-0121 — Open Rows (introduced `row R`; amended here).
- RFC-0123 — Field-Wise Row Constraints (`where all R: A`; amended here).
- RFC-0178 — Row Remainder Construction (value-level `..` rest patterns and spreads).
- RFC-0180 — Literal rows in row arguments; RFC-0181 — Open rows in every type position.
- RFC-0137 — Nominal types as branded rows (the brand versus row distinction).
- RFC-0125 — Variadic Generics (`all Ts`), RFC-0146 — Row-polymorphic self-views,
  RFC-0174 — Compile-time iteration over a row's fields, RFC-0175 — Label polymorphism
  (examples that use `row R`).
- `reference/spec/types.md` — "Records and Rows at a Glance", "Open rows", "Field-wise row
  constraints".

---

## Decision

**Outcome:** *(pending)*
