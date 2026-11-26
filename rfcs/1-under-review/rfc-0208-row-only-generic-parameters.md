---
id: rfc-0208
title: "Row-Only Generic Parameters"
date: '2026-11-02'
status: under-review
updated: '2026-11-26'
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

1. In bound position, `T: .{ .id: i32 }` requires exactly the named field. Write
   `T: .{ .id: i32, .. }` to permit other fields. A value parameter typed `.{ .id: i32 }` names an exact anonymous
   record type. The bound preserves the argument type and its brand. RFC-0243 governs
   which fields of a nominal type are eligible.
2. A parameter bound by `<..R>` denotes labelled fields. Use `R` as a record tail
   (`.{ .id: i32, R }`), as the entire row of an anonymous record (`.{ R }`), as a row
   argument (`Packet<R>`), or as a residual tail (`Handle.{ .fd, R }`). The enclosing
   residual supplies the brand. `Handle.{ .fd, R }` matches only residuals of `Handle`;
   `R` supplies their remaining fields and must exclude `.fd`. A same-shaped residual of
   another brand does not match. The empty remainder is `Handle.{ .fd }`, which a named
   view may name (RFC-0109). A value annotation `v: R` requires a type and is an error.
3. In an operand position, `..T` extracts the row of a type whose row is available.
   `where T: Clone` constrains the type itself. `where ..T: Clone` constrains every
   field in its available row. For an already-bound row, write `where R: Clone`.
   Applying extraction to a row is a kind error with the suggested replacement `R`.
4. Extraction observes the same visibility as the operation that made the row available.
   Under RFC-0243's public-row option, matching a public bound against a residual exposes
   only its present public fields. Binding a remainder cannot reveal private fields.
5. RFC-0186's existing `<record T>` can still bind a record type and extract its row with
   `..T`. No conversion of existing declarations is required. Row parameters are erased.
6. A row parameter may carry a structural bound at its binder or in a `where` clause.
   `<..R: .{ .id: i32, .. }>` and `<..R> ... where R: .{ .id: i32, .. }` impose
   the same requirement. A closed bound is exact and `..` allows additional fields.
7. `..{ .id: i32, .name: String }` is a row literal, usable where a row is expected,
   including as an explicit row argument, `f::<..{ .id: i32 }>(value)`. A row literal
   without a tail denotes exactly its listed fields. An open row literal may include a
   bound row, as in `..{ .id: i32, R }`, when `.id` is provably absent from `R`; duplicate
   or not-provably-disjoint labels are rejected. `.{ .id: i32 }` names an anonymous record
   type. `..T` extracts the available row of a type, while `R` uses an already-bound row.
   Explicit type-argument application spelling follows RFC-0192; this example is
   illustrative until its interaction with row arguments is integrated.

RFC-0254 proposes retiring `record T` and making `..T` available for every type.
Until that proposal is integrated, references here to existing `record T` describe the
current language, not the intended end state.

## 2. Numeric rows and variadics

`<..R>` binds one row kind, including rows with numeric labels. RFC-0151 is implemented:
tuples are numeric-label anonymous records. There is no separate tuple-pack kind to
disambiguate. RFC-0125's remaining positional row operations, including renumbering,
and RFC-0247's variadic call parameters are separate questions. A tuple-shaped use of
the row binder does not by itself specify a positional splice or renumbering operation.

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
- **RFC-0125** — positional operations over numeric rows.
- **RFC-0151** — implemented tuples as numeric-label rows; no separate tuple-pack kind.
- **RFC-0247** — proposed variadic call parameters collect arguments into a row.
- **RFC-0137 / RFC-0146** — branded rows and row-polymorphic self-views, the places a residual
  tail appears.
- **RFC-0192** — turbofish for record parameters; its argument rule for a row parameter is an
  open question below.
- **RFC-0209** — per-aspect row visibility (RFC-0207 is now only the colon list and `derives`); its derivation template is written with row-only
  parameters, which is the motivating use.

## Open questions

1. **Resolved (language owner, 2026-11-26).** The row-literal spelling is `..{ .name: i64 }`.
   A `<..R>` parameter's turbofish argument is that row literal, checked by exactly
   RFC-0192's existing rule (declaration-order pinning, the row bound, the field-wise
   bound, disjointness) — applied to a row argument where RFC-0192 applies it to a
   `record R` argument, since RFC-0192's rule was already stated generically over "the
   type each argument denotes" and never assumed a record brand. No new rule is needed;
   RFC-0192 itself should gain a line extending its scope to `<..R>` explicitly, since its
   current text only names `record R`.
2. **Row equations**: the left operand is the bound row `R` and a literal row on the right
   is written `..{ .token: Token }`. An open literal may use a provably disjoint row tail,
   `..{ .token: Token, Rest }` (language owner, 2026-11-25). Equation solving and inference
   across generic boundaries need review.
3. *(Pruned, PROCESS.md's "prune harder" rule, 2026-11-26.)* A lint or rewrite for
   `record R` parameters used only as `..R` is a tooling convenience, not a design
   question blocking acceptance.
4. **Row bounds at the binder or in `where`:** both are allowed with the same meaning
   (language owner, 2026-11-25).
5. **Tuple packs:** resolved. RFC-0151's numeric rows use the same row kind (language
   owner, 2026-11-25); positional operations remain with RFC-0125.
6. **Residual tails:** `Handle.{ .fd, R }` preserves `Handle`'s brand and requires a
   disjoint remainder (language owner, 2026-11-25). **Not blocking:** RFC-0146 (the other
   half of this question, `Self.R` in receiver position) is committed to the v0.18.1
   milestone (issue #886), a release after this one — a dated dependency that isn't
   landing alongside this RFC either way. Worth a note for whoever picks up RFC-0146
   then, not a question this RFC needs to answer now: RFC-0146's `where R: { fd, .. }`
   lower bound on a receiver-only `<row R>` looks like it may already be expressible as
   this RFC's general `Self.{ .fd, R }` splice, which would make RFC-0146's separate
   `<row R>`/`Self.R`/`where` apparatus redundant rather than a second spelling to
   reconcile — but that's RFC-0146's call to make against its own v0.18.1 timeline.

---

## Decision

**Outcome:** *(pending)*
