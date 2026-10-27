---
id: rfc-0186
title: "Rows as an Operator on Record Parameters"
date: '2026-10-24'
coverage:
  "1": { spec: "spec.types.generics.open-rows.legality-1" }
  "2": { kind: untestable, reason: "an alternatives analysis; it states no rule a program can exhibit" }
  "3": { kind: untestable, reason: "a cost analysis; it states no rule a program can exhibit" }
  "4": { kind: untestable, reason: "records review findings and resolved design questions; each resolution is stated as a rule in section 1" }
status: implemented
updated: '2026-10-27'
tracking: 'https://github.com/metel-lang/metel-core/issues/1597'
impl_tracking: 'https://github.com/metel-lang/metel-core/issues/1644'
impl_status: implemented
---

> **Status — under review (2026-10-24).** design settlement committed to a release milestone (tracking issue linked).

> **Revised (2026-10-27; restored by the #1653 amendment below).** An earlier draft replaced `where all R: A` with `where ..R: A`. That is dropped: `..` stays an unpacking operator everywhere, and the field-wise constraint keeps a keyword, renamed `all` to `each`. Row declarations are this RFC's alone (RFC-0187 and RFC-0188 no longer touch them).

> **Status — accepted (2026-10-27).** Open questions resolved 2026-10-27; keyword each

> **Status — integrated (2026-10-27).** Spec integrated with Pending markers; implementation tracked in #1644

> **Status — implemented (2026-10-27).** Implemented by metel-core#1644

> **Amended (2026-10-27, metel-core#1653, pending review).** The field-wise bound is written `where ..R: A`, with no keyword: `all` and the interim `each` are both removed. `..R` is "the members of R's row" exactly as it is everywhere else, so `..R: A` reads "every member of R's row is `A`". An earlier draft of this RFC proposed this and it was dropped; it is restored for the reasons in Motivation §4. `each` was only ever unreleased, so there is no user-facing migration. Implementation is tracked in #1653 and waits for this amendment to be accepted.

## Summary

Remove the `row` generic-parameter kind and replace the field-wise constraint `where all R: A` with
`where ..R: A`. A generic parameter that stands for a record is declared `record R` (as `record T`
already is), and the existing `..` spread is the one way to get at a record's row: `..R` yields
**R's row**. `..` stays an unpacking operator everywhere (record tails, row arguments, spreads,
rest patterns, pack splices); in a bound, `..R: A` says every member of that unpacked row is `A`.

```metel
// before                                              // after
fun get_x<row R>(p: { x: f64, ..R }) -> f64            fun get_x<record R>(p: { x: f64, ..R }) -> f64
fun consume<row R>(r: { ..R }) where all R: Copy       fun consume<record R>(r: { ..R }) where ..R: Copy
extend<row R> { ..R }: Display where all R: Display    extend<record R> { ..R }: Display where ..R: Display
record Packet<row R> { data: { ..R } }                 record Packet<record R> { data: { ..R } }
fun f<row R>(p: Packet<..R>) -> ...                    fun f<record R>(p: Packet<..R>) -> ...
```

Two mechanical rewrites cover existing code: `row` becomes `record` at the binder, and `all R`
becomes `..R` in a field-wise bound (for rows and, in RFC-0125, `..Ts` for packs). Every use of `..R`
is unchanged. `row` stops being a reserved word, and the contextual keyword `all` is removed with
no replacement.

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

### 4. The constraint is written with the row operator

The field-wise constraint (`where all R: A`) bounds `R` differently from `where R: A`: the record
as a whole versus each of its fields. With `record R` and `..R` in place, that difference is
already carried by the operator: `R: A` bounds the record, `..R: A` bounds the members of its row.
A separate quantifier word adds nothing a reader cannot already see (amended, #1653; the interim
spelling was `each R` / `each ..R`).

- **`..` keeps one meaning, "the members of".** `{ ..R }` splices R's members into a record,
  `comptime for member in ..self` (RFC-0174) iterates them, `..R: A` constrains them. The bound is
  not a second job for the token; it is the same job applied to a constraint.
- **A keyword would only make sense next to the `row` kind.** If `<row R>` still existed, `R` would
  be a row and `each R: A` would need a word to say "per member". With `record R`, the name is the
  record and `..R` is already how the row is named, so a keyword would repeat it. (Keeping `row`
  was rejected in §1; it is two kinds for one idea.)
- **It carries over unchanged** to packs (`..Ts: A`), to tuples read as numeric-label rows
  (RFC-0151) and to a pack-or-row-generic `extend<record R> { ..R }: A where ..R: A`.
- **One keyword fewer.** `all` was contextual; `each` is unreleased and is dropped before it ships.

The risk is that `..R: Display` could be read as "the row as a whole is `Display`". It cannot be
satisfied that way: a row is not a type and implements no aspect, so the only reading with a
meaning is per member, and the checker rejects `..R: A` when `R` is not a `record` parameter
(`T0012`). The remaining cost is that a bound looks like a spread; the `where` position and the
`: Aspect` suffix disambiguate it, and spreads never take a bound.

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

`where ..R: A` holds when every field type in `R`'s row satisfies `A`, vacuously on an empty
row. It is `where all R: A` with the operand written as the unpacked row and no keyword; the
meaning, the walkable positions (an open-record tail, a `where` decomposition's remainder, the
tail of an `extend` target, a row argument of a nominal type) and the forwarding rule (it is
forwarded only to another `..R: A`) are unchanged. The operand must be `..` followed by the
name of a `record` parameter.

`R: A` keeps its present meaning, a bound on the record as a whole. The two are distinct forms of
one bound list:

```metel
fun show<record R>(r: { ..R }) -> String where ..R: Display { … }   // each field is Display
fun dup<record R: Copy>(r: R) -> (R, R) { (r, r) }                  // the record is Copy
```

### What does not change

- Row bounds (`record R: { x, .. }`), negative bounds (`!{ token }`), and row equations
  (`where R = { token: Token, ..Rest }`). Equation sides are record types, so `Rest` is now
  declared `record Rest`.
- Disjointness: a label written next to `..R` must be absent from `R`, as for rows today.
- The field-wise constraint's meaning, positions and forwarding rule (RFC-0123); only the spelling changes.
- Rest patterns and record spreads at the value level (RFC-0178).
- Literal rows in row arguments (RFC-0180), `Req<..{ host: String, ..R }>`.
- Anonymous tails and where they are accepted (RFC-0181).
- Width subtyping and the by-value ownership rules for the extras.
- The `label L` kind proposed by RFC-0175: this RFC removes `row`, not other kinds.

### Diagnostics

`row R` becomes a targeted error ("the `row` kind was removed; declare `record R`"), and
`where all R: A` likewise ("`all` was removed; write `where ..R: A`"), and so does the interim
`where each R: A` / `where each ..R: A`. `..R: A` where `R` is not a `record` parameter reports
`T0012` as `..R` does. `..R` on a non-`record` parameter says "`..R` takes the row of a record
parameter; declare `record R`".

---

## 2. Alternatives considered

1. **Status quo.** Two kinds, one reserved word, one contextual keyword. Nothing breaks. The cost is
   the vocabulary in Motivation §§1 and 3.
2. **Remove only `row`, keep `all`.** Fewer rewrites (no constraint rename). Declined: with `record R`
   the bound is already distinguished by `..R`, so the keyword is redundant (Motivation §4), and
   the rewrite is cheapest done in the same parser-based pass as `row` to `record`.
3. **A keyword with the bare name, `where each R: A` (the interim form of this RFC, 2026-10-27).**
   Keeps `..` away from bounds. Declined (#1653): it makes sense only if the `row` kind is kept
   (`<row R> where each R: A`, where `R` is the row and the word says "per member"), and §1 removes
   that kind. With `record R`, `R` is the record, so `each R: A` reads "R is A" and hides that the
   row is enumerated.
4. **A different keyword or token**, e.g. `where R.*: A`. A new token for what `..R` already says.
5. **Keep `row` as a deprecated alias for one release.** A transitional option, not a design
   alternative: see Open Question 3.
6. **Keep the `row` kind and `each R`** (`<row R> where each R: A`). Two kinds for one idea
   (Motivation §1); this is the pre-RFC state with a renamed keyword.
7. **`each ..R: A`** (this amendment's first draft, 2026-10-27). Keeps the keyword and adds the
   unpack operand. Declined: once the operand is `..R`, `each` repeats it. Costs a keyword, a
   contextual-keyword rule and a longer bound for no information the operator does not carry.

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
- **The #1653 amendment.** About 45 fixtures (65 sites), 6 standard-library sites, the spec,
  tutorial, dated blog posts, the changelog, and the diagnostics that say `each` (six sites);
  `each_kw` is removed from the grammar. One parser-based pass like the `row`/`all` rewrite;
  `each` is unreleased so there is no user-facing migration.
- **Churn in pending RFCs.** RFC-0125 (`all Ts: Copy` becomes `..Ts: Copy`), RFC-0146 (`Self.R`
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
   `each` in this RFC. RFC-0125's pack bounds follow (`each Ts: A` in that interim; see finding 5).
5. **No keyword (amended 2026-10-27, #1653).** `each R: A` was shipped as the keyword form. On
   review, `each` is redundant once the operand is `..R`: `R: A` bounds the record and `..R: A`
   bounds its members. The bound is written `where ..R: A`; `each` is dropped before it ships. The
   earlier objection (a quantifier in bound position is a second job for `..`) is answered in
   Motivation §4. Open Question 4.

---

## Open Questions — resolved 2026-10-27

1. **Row arguments: keep `Packet<..R>` or write `Packet<R>`?** *Resolved: keep `Packet<..R>`,*
   defined as `Packet<{ ..R }>`. This RFC is the single rows change (review finding 3), so no
   argument position changes. Making a `record`-kinded parameter take a record type (`Packet<R>`,
   dropping literal-row arguments) would change brand behaviour at the argument and is not part of
   this RFC.
2. **Variadic packs (RFC-0125).** *Resolved:* packs share the quantifier with rows, now spelled
   `..Ts: Copy`. RFC-0125 is under review and unimplemented, so it changes spelling only.
3. **Deprecation window or hard cut?** *Resolved: hard cut*, as RFC-0136 and RFC-0098 were. `row R`
   and `where all R: A` become targeted errors (see Diagnostics), and one parser-based rewrite
   migrates the corpus.
4. **Can a generic body name `R` as a type when `R` is an anonymous remainder?** *Resolved: yes, both
   spellings are allowed.* `R` is a type and `{ ..R }` is its anonymous record; they are the same
   type when `R` is anonymous. They differ only when `R` is a branded `record` (`R` keeps the brand,
   `{ ..R }` drops it), which is a difference in meaning, not style, so no lint steers between them.
5. **`record R` instantiated by a branded `record`.** *Confirmed.* A branded record already goes
   through a `row R` parameter today (`get_x(p)` with `p: P` compiles), and `R` is inferred as the
   anonymous remainder, so inference is unchanged. `..R` forgets the brand where one is supplied
   explicitly. A fixture for the explicit-instantiation case is part of the implementation.
6. **Release timing.** *Resolved: v0.15.0*, the milestone already on the tracking issue, so the
   release's explicit-syntax changes migrate once. The rewrites are sequenced as separate reviewable
   changes.

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
4. **Keyword form, or the bare row operand?** *Resolved (pending review): `where ..R: A`, no
   keyword* (Motivation §4, Alternatives 3, 6, 7). Hard cut, no deprecation window: `each` is
   unreleased. Implementation is metel-core#1653 and waits for this amendment to be accepted.
