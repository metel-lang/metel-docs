---
id: LIMIT-TYPES-001
title: "RFC-0121 open rows are only partly implemented"
summary: "Row kinds, `..R`, decomposition, concrete width subtyping and nominal-target row-conditional impls work; the structural `{ ..R }` impl target, row extension, anonymous `..` arguments and abstract-row width subtyping do not."
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
residual-projection tail and generic-argument position; a `where R = { label: Type,
..Rest }` decomposition, which bounds `R` and derives `Rest` at each call; by-value width
subtyping when the row's fields are concretely known at the narrowing site; and
row-conditional impls (`extend<row R: { .. }> Session<..R>`, inherent and aspect) on a
nominal target, with row-versus-row coherence and runtime dispatch.

Not implemented, each reproduced against the current implementation:

```metel
// the spec's structural impl target
extend<row R: { id: i64, .. }> { ..R }: Describe { fun describe(self) -> i64 { 1 } }
```

```
[P0001] parse error: expected ident
```

```metel
// an anonymous row as a generic argument
fun f(b: Builder<..>) -> i64 { 0 }
```

```
[T0032] an anonymous row (`..`) in this position is not yet implemented
```

- Row extension, a row literal's trailing `..R` with named fields outside a function
  parameter (`record Wrap<row R> { data: { x: i64, ..R } }`): rejected with T0032 (it
  used to panic, metel-core#1324).
- Abstract-row width subtyping: by-value narrowing of an unconstrained `<row R>` inside a
  generic body is not rejected, because it needs `all R: Copy` (`LIMIT-TYPES-002`,
  metel-core#1302).
- A row-conditional method is not hidden inside a generic body over an unconstrained
  `<row R>` (metel-core#1323).
- A `native` function cannot take an open-row-tailed parameter.

## Impact

Visible to Metel programmers: row-polymorphic code over a nominal type works, including
typestate (`authenticate` / `send_data` as separate impls), but a blanket aspect
implementation over every record shape (`Display`, `Copy`) still cannot be written
(`GAP-TYPES-004`, which additionally needs RFC-0123's `all R: Aspect`), and a function that
extends a row rather than only narrowing or decomposing it is unavailable.
`record`'s own row-conditional impl eligibility (`spec.declarations.records.legality-2`,
`LIMIT-DECLARATIONS-001`) was blocked on this work and has not been re-checked against it.

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
