---
id: rfc-0186
title: "Rows as an Operator on Record Parameters"
date: '2026-10-24'
status: under-review
updated: '2026-10-27'
tracking: 'https://github.com/metel-lang/metel-core/issues/1597'
---

> **Status — under review (2026-10-24).** design settlement committed to a release milestone (tracking issue linked).

> **Revised (2026-10-27).** An earlier draft replaced `where all R: A` with `where ..R: A`. That is dropped: `..` stays an unpacking operator everywhere, and the field-wise constraint keeps a keyword, renamed `all` to `each`. Row declarations are this RFC's alone (RFC-0187 and RFC-0188 no longer touch them).

## Summary

Remove the `row` generic-parameter kind and rename the field-wise constraint keyword `all` to
`each`. A generic parameter that stands for a record is declared `record R` (as `record T`
already is), and the existing `..` spread is the one way to get at a record's row: `..R` yields
**R's row**. `..` stays an unpacking operator everywhere (record tails, row arguments, spreads,
rest patterns, pack splices); the field-wise bound is a keyword, not a use of `..`.

```metel
// before                                              // after
fun get_x<row R>(p: { x: f64, ..R }) -> f64            fun get_x<record R>(p: { x: f64, ..R }) -> f64
fun consume<row R>(r: { ..R }) where all R: Copy       fun consume<record R>(r: { ..R }) where each R: Copy
extend<row R> { ..R }: Display where all R: Display    extend<record R> { ..R }: Display where each R: Display
record Packet<row R> { data: { ..R } }                 record Packet<record R> { data: { ..R } }
fun f<row R>(p: Packet<..R>) -> ...                    fun f<record R>(p: Packet<..R>) -> ...
```

Two mechanical rewrites cover existing code: `row` becomes `record` at the binder, and `all`
becomes `each` in a field-wise bound (for rows and, in RFC-0125, for packs). Every use of `..R`
is unchanged. `row` stops being a reserved word, and `each` replaces `all` as the contextual
keyword.

This amends RFC-0121 (open rows) and RFC-0123 (field-wise constraints), both implemented, and
renames the quantifier RFC-0125 reuses for packs. It is a breaking change to shipped syntax and
needs this RFC first (see `metel_rfc_before_implementation`).

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

### 3. A reserved word that does one job

`row` is a reserved word (`grammar.pest`'s reserved list) used in exactly one place, the binder.
Once a `record R` parameter can stand for the rest of a record, the word has nothing left to do.

### 4. The constraint keeps a keyword, and a clearer one

The field-wise constraint (`where all R: A`) bounds `R` differently from `where R: A`: the record
as a whole versus each of its fields. The difference is carried by the keyword in front of the
name, and it should stay there. This RFC renames `all` to `each`: `where each R: Display` says
what is quantified (each field's type), and for a pack in RFC-0125 `where each Ts: Copy` says each
member. It deliberately does **not** write the bound as `..R: A`. `..` means "unpack" in every
other position the language gives it (a record tail, a row argument, a spread, a rest pattern, a
pack splice); in bound position it would be a quantifier, a second job for the same token.

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

`..R` anywhere else, or on a parameter that is not `record`-kinded, is an error. Anonymous
`..` (`{ x: f64, .. }`) is unchanged.

`R` itself remains usable as a type. If `R` is an anonymous record, `R` and `{ ..R }` are the
same type. If `R` is a branded `record` declaration, `R` keeps its brand and `{ ..R }` is
the anonymous record with the same fields. In particular `..` is the one operation that
forgets a brand while keeping the fields: the spec describes a declaration as a brand paired
with a row, and `..R` is the "row" half of that pair.

### The field-wise constraint

`where each R: A` holds when every field type in `R`'s row satisfies `A`, vacuously on an empty
row. It is `where all R: A` with the keyword renamed and the same meaning, the same walkable
positions (an open-record tail, a `where` decomposition's remainder, the tail of an `extend`
target, a row argument of a nominal type) and the same forwarding rule (it is forwarded only to
another `each R: A`).

`R: A` keeps its present meaning, a bound on the record as a whole. The two are distinct forms of
one bound list:

```metel
fun show<record R>(r: { ..R }) -> String where each R: Display { … }   // each field is Display
fun dup<record R: Copy>(r: R) -> (R, R) { (r, r) }                      // the record is Copy
```

`each` is a contextual keyword, recognised only at the start of a `where` bound as `all` is.

### What does not change

- Row bounds (`record R: { x, .. }`), negative bounds (`!{ token }`), and row equations
  (`where R = { token: Token, ..Rest }`). Equation sides are record types, so `Rest` is now
  declared `record Rest`.
- Disjointness: a label written next to `..R` must be absent from `R`, as for rows today.
- The field-wise constraint's meaning, positions and forwarding rule (RFC-0123); only the keyword changes.
- Rest patterns and record spreads at the value level (RFC-0178).
- Literal rows in row arguments (RFC-0180), `Req<..{ host: String, ..R }>`.
- Anonymous tails and where they are accepted (RFC-0181).
- Width subtyping and the by-value ownership rules for the extras.
- The `label L` kind proposed by RFC-0175: this RFC removes `row`, not other kinds.

### Diagnostics

`row R` becomes a targeted error ("the `row` kind was removed; declare `record R`"), and
`where all R: A` likewise ("`all` was renamed; write `where each R: A`"). `..R` on a non-`record`
parameter says "`..R` takes the row of a record parameter; declare `record R`".

---

## 2. Alternatives considered

1. **Status quo.** Two kinds, one reserved word, one contextual keyword. Nothing breaks. The cost is
   the vocabulary in Motivation §§1 and 3.
2. **Remove only `row`, keep `all`.** Fewer rewrites (no constraint rename). Declined: `each` states
   the distribution, and the rename is cheapest done in the same parser-based pass as
   `row` to `record`; a later standalone rename would be a second migration over the same
   declarations.
3. **`where ..R: A` for the constraint (the earlier draft of this RFC).** Removes a keyword by
   reusing `..`. Declined: it gives `..` a second job, a quantifier in bound position, where
   everywhere else it unpacks. A reader may also take `..R: Display` to mean the row as a whole is
   `Display`.
4. **A different keyword or token**, e.g. `where R.*: A`. A new token for what a word says plainly.
5. **Keep `row` as a deprecated alias for one release.** A transitional option, not a design
   alternative: see Open Question 3.

---

## 3. Costs

- **A breaking rewrite of two shipped forms.** 192 integration fixtures (410 sites) bind a `row`
  parameter and 45 (73 sites) use `where all`; 46 Markdown files in this repository mention one of
  them; the standard library (`core.mtl`) has 6 sites. Both rewrites are purely lexical and run in
  one parser-based pass, but the spec sections for RFC-0121, RFC-0123, RFC-0178, RFC-0180 and
  RFC-0181 are amended, and so is the spec's own map of the area.
- **Implementation.** `row` is a kind in the parser, the AST, the registry (row kinds on type
  parameters), projection checking, and the type engine's row kinds. The change merges the kind and
  adds the operator check; it removes a parallel code path, but it touches every site that
  distinguishes the kinds. The constraint rename is a keyword change in `field_wise_constraint`.
- **Churn in pending RFCs.** RFC-0125 (`all Ts: Copy` becomes `each Ts: Copy`), RFC-0146 (`Self.R`
  with `row R`), RFC-0174 (`fields(R)` examples) and RFC-0175 (draft) use `row R` or `all`.

---

## Review findings (2026-10-27)

1. **Claims checked against the build and the corpus.** `fun get_x<record R>(p: { x: i64, ..R })` is
   rejected today with `T0012`, "`R` is not a row parameter; declare it `<row R>`", as stated.
   192 fixtures bind a `row` parameter (410 sites), 45 use `all` (73 sites), 46 Markdown files
   mention either form (25 of them RFC examples). The cost estimates in §3 stand.
2. **The standard library is missing from the costs.** `metel-frontend/stdlib/core.mtl` has 6
   `row`/`all` sites that the rewrite must cover.
3. **Overlap with RFC-0188 and RFC-0187, resolved.** RFC-0187 originally also proposed removing the
   row kind (`<row R>` to `<R>`, `Packet<R>`, no kind keyword). That part was dropped: **this RFC is
   the single change to row declarations**. RFC-0187 keeps only the `{| … |}` delimiters and
   RFC-0188 keeps only the label spelling. Both use this RFC's `record R` and `..R` in their
   examples. This avoids rewriting the same declarations twice (`row R`, then `record R`, then bare
   `R`).
4. **The constraint keyword (revised 2026-10-27).** The first draft replaced `all` with `..R: A`.
   Reviewed and changed: `..` stays an unpacking operator, and the keyword is renamed `all` to
   `each` in this RFC. RFC-0125's pack bounds follow (`each Ts: A`).

---

## Open Questions

1. **Row arguments: keep `Packet<..R>` or write `Packet<R>`?** *Resolved 2026-10-27: keep
   `Packet<..R>`.* This RFC is the single rows change (review finding 3), so the argument forms do
   not change here. The original discussion follows. This draft keeps
   `Packet<..R>` and defines it as `Packet<{ ..R }>`, so no argument position changes. The
   alternative is that a `record`-kinded parameter of a nominal type takes a record type,
   so `Packet<R>` replaces `Packet<..R>`, which would also remove literal-row arguments
   (RFC-0180) in favour of ordinary record types. That is simpler but changes brand
   behaviour at the argument (§1: `R` keeps its brand, `{ ..R }` does not) and so should be
   decided separately.
2. **Variadic packs (RFC-0125).** *Resolved 2026-10-27.* Packs keep their one quantifier shared with
   rows, now spelled `each`: `each Ts: Copy`. RFC-0125 is under review and unimplemented, so it
   changes spelling only.
3. **Deprecation window or hard cut?** `row R` and `where all R: A` (now `where each R: A`) could still parse for one
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
