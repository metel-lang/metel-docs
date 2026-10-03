---
id: GAP-TYPES-005
title: "No spelling for an operator on a generic parameter"
summary: "An operator such as `+` or `<` on a bare type parameter is rejected, and no aspect exists that grants it."
scope: "reference/spec/types.md#rigid-type-parameters"
owner: language
discovered_by: "RFC-0173 review (D5): the stdlib has no arithmetic or ordering aspects, so a generic body cannot be given a bound that grants an operator"
disposition: known
review: null
---

## Gap

RFC-0173 requires a body to use only what its declared bounds entail. Equality is covered
(`Eq` grants `==` through its `eq` method), but there is no aspect that grants `+`, `-`,
`<` and the like, so a generic `add<T>(a: T, b: T) -> T { a + b }` cannot be written: the
operator is rejected (`T0005`) and there is no bound to add. Arithmetic on concrete types
is unaffected.

## Impact

Visible to Metel programmers: generic numeric code (a `sum<T>`, a `max<T>`) has no
spelling; write it for the concrete types instead. It is a limit of the language, not a
checker shortfall. When operators desugar to aspects (an RFC that does not exist yet),
`T: Add` grants `+` by the ordinary entailment rule and this gap closes with no change to
RFC-0173.

## Affects

- `spec.types.generics.rigid-type-parameters.legality-3`
