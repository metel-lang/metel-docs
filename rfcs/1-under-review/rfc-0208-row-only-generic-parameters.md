---
id: rfc-0208
title: "Row-Only Generic Parameters"
date: '2026-11-02'
status: under-review
updated: '2026-11-25'
tracking: 'https://github.com/metel-lang/metel-core/issues/1789'
---

> **Status — under review (2026-11-03).** review of the row-only binder

## Summary

A structural bound can be written directly on a type parameter. A parameter declared with
`<..R>` instead binds a row. Use its bare name wherever a row is expected.

```metel
fun read_id<T: .{ .id: i32 }>(v: &T) -> i32 { v.id }
fun read_tail<..R>(v: .{ .id: i32, R }) -> i32 { v.id }
extend<..R> .{ R }: Display where R: Display { … }
```

## 1. Type bounds, row binders and extraction

1. In bound position, `T: .{ .id: i32 }` requires at least the named field. Other fields
   are permitted. A value parameter typed `.{ .id: i32 }` still names an exact anonymous
   record type. The bound preserves the argument type and its brand. RFC-0243 governs
   which fields of a nominal type are eligible.
2. A parameter bound by `<..R>` denotes labelled fields. Use `R` as a record tail
   (`.{ .id: i32, R }`), as the entire row of an anonymous record (`.{ R }`), as a row
   argument (`Packet<R>`), or as a residual tail (`Handle.{ .fd, R }`). The enclosing
   residual supplies the brand. A value annotation `v: R` requires a type and is an error.
3. In an operand position, `..T` extracts the row of a type whose row is available.
   `where T: Clone` constrains the type itself. `where ..T: Clone` constrains every
   field in its available row. For an already-bound row, write `where R: Clone`.
   Applying extraction to a row is a kind error with the suggested replacement `R`.
4. Extraction observes the same visibility as the operation that made the row available.
   Under RFC-0243's public-row option, matching a public bound against a residual exposes
   only its present public fields. Binding a remainder cannot reveal private fields.
5. RFC-0186's existing `<record T>` can still bind a record type and extract its row with
   `..T`. No conversion of existing declarations is required. Row parameters are erased.

## 2. Relationship to packs

RFC-0125 also proposes `<..Ts>`. A record tail supplies a row context and a tuple pack
position supplies a pack context. Mixed uses are a kind error. How to disambiguate a
binder with no determining use remains a question for joint review.

## 3. Alternatives considered

Earlier drafts required `..R` at every row use. That made extracting a row from a
type and referring to fields already bound as a row look identical. Restoring the
`row` keyword would also duplicate the proposed binder.

## 4. Costs

Parsing and kind checking must recognize bare tails and distinguish a bare row in
`where R: A` from a type parameter constrained by the same aspect. Diagnostics need
the declaration of the parameter to suggest the correct spelling.

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
   (`.{ .name: i64 }`), or with the dots (`..{ name: i64 }`)? The first matches RFC-0192 as it
   stands.
2. **Row equations**: the left operand is the bound row `R`; the row-literal spelling on the right remains open.
3. **A lint or rewrite** for `record R` parameters used only as `..R`.
4. **Whether a row parameter may carry a lower bound in the binder**, as `record R` does with
   `record R: .{ .x: f64, .. }`.
5. **Merging with packs** if RFC-0151 is accepted: one `..X` kind with a shared binder.
6. **Residual tails**: whether `Handle.{ .fd, R }` with `R` declared `..R` needs a rule about
   the brand being the struct's, and how it interacts with RFC-0146's `Self.R`.

---

## Decision

**Outcome:** *(pending)*
