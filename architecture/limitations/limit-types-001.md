---
id: LIMIT-TYPES-001
title: "RFC-0121 open rows are only partly implemented"
summary: "Row kinds, reusable row extension, anonymous row arguments and row-conditional impls work; native open-row parameters and residual dispatch remain limited."
scope: "architecture/spec/type-inference.md#type-inference"
owner: metel-frontend
discovered_by: "RFC-0121 entering 3-integrated with no implementation yet"
disposition: planned
planned_for: v0.14.0
rfc: RFC-0121
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

- An impl on a record target is matched against a nominal record's declared fields; its
  row after a partial move (a struct residual) has not been checked, and an aspect that
  takes type parameters, implemented more than once for one record target, resolves as
  it does for a nominal type.
- A `native` function cannot take an open-row-tailed parameter.

## Impact

Visible to Metel programmers: row-polymorphic code over a nominal type works, including
typestate (`authenticate` / `send_data` as separate impls), and a local aspect can be
implemented for every record of a given shape. The standard library provides
the blanket `Display` and `Copy` impls for records, and a function
that extends a row rather than only narrowing or decomposing it is unavailable.
`record`'s own row-conditional impl eligibility (`spec.declarations.records.legality-2`,
`LIMIT-DECLARATIONS-001`) has not been re-checked against this work.

## Affects

- `spec.types.generics.open-rows.legality-1`
- `spec.types.generics.open-rows.legality-2`
- `spec.types.generics.open-rows.legality-3`
- `spec.types.generics.row-conditional-impls.legality-1`
- `spec.types.generics.row-conditional-impls.legality-2`
- `spec.types.generics.row-conditional-impls.legality-3`

## Resolution

Planned: tracked as metel-core#1301 (RFC-0121 implementation tracking, milestone
v0.14.0), with the remaining pieces itemized on metel-core#1306 and metel-core#1310.
