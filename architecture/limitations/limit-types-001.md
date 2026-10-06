---
id: LIMIT-TYPES-001
title: "RFC-0121 open rows were incomplete"
summary: "Resolved: row extension, reusable row positions, decomposition, and row-conditional implementations are implemented."
scope: "architecture/spec/type-inference.md#type-inference"
owner: metel-frontend
discovered_by: "RFC-0121 entering 3-integrated with no implementation yet"
disposition: resolved
review: null
---

## Limitation

RFC-0121 is implemented in installments (metel-core#1306), and what is left is the part
the Language Spec still states as design.

Implemented: the `row` generic-parameter kind; `..R` in a record type's tail, a struct's
residual-projection tail, generic-argument position and reusable nested/return/field
type positions; a `where R = { label: Type,
..Rest }` decomposition, which bounds `R` and derives `Rest` at each call; by-value width
subtyping when the row's fields are concretely known at the narrowing site; and
row-conditional impls (`extend<row R: { .. }> Session<..R>`, inherent and aspect) on a
nominal target, and aspect impls on a record target (`extend<row R: { .. }> { ..R }: A`,
`extend { x: f64 }: A`; anonymous and nominal records), with row-versus-row coherence
and runtime dispatch.

- A record-target impl with an aspect that takes type parameters, implemented more than
  once for one record target, resolves as it does for a nominal type; residual dispatch
  after a partial move is implemented and covered by the RFC-0121 fixture suite.

## Impact

At the time, row-polymorphic code over a nominal type worked, including
typestate (`authenticate` / `send_data` as separate impls), and a local aspect can be
implemented for every record of a given shape. The standard library provides
the blanket `Display` and `Copy` impls for records. Row extension now also permits the
tail before newly-added fields, such as `{ ..R, auth: String }`.

## Affects

- `spec.types.generics.open-rows.legality-1`
- `spec.types.generics.open-rows.legality-2`
- `spec.types.generics.open-rows.legality-3`
- `spec.types.generics.row-conditional-impls.legality-1`
- `spec.types.generics.row-conditional-impls.legality-2`
- `spec.types.generics.row-conditional-impls.legality-3`

## Resolution

Resolved by metel-core#1301, #1306, and #1384. The grammar and reusable-type
implementation now accept both `{ fields, ..R }` and `{ ..R, fields }` forms.
