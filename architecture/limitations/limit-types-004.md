---
id: LIMIT-TYPES-004
title: "RFC-0173 generic bodies are not yet checked against their declared bounds"
summary: "A declared type parameter is not rigid in its own definition: a body can collapse it into a concrete type or another parameter, and a use the bounds do not grant is accepted or reported at a call."
scope: "architecture/spec/type-inference.md#type-inference"
owner: metel-frontend
discovered_by: "RFC-0173 entering 3-integrated with no implementation yet; metel-core#1320, #1323"
disposition: planned
planned_for: v0.14.0
rfc: RFC-0173
review: null
---

## Limitation

RFC-0173 makes the definition-time check the contract for a generic body: each declared
parameter is rigid, and a use is allowed only if the declared bounds entail it. The
checker does not enforce that yet. A generic body is also re-checked at every call with
concrete types substituted (`LIMIT-EVALUATION-001`), and that re-check is where several
definitions that should be rejected are accepted or fail late:

```metel
fun pick<T>(a: T) -> i64 { a }          // accepted: T collapses into i64
fun id2<T, U>(a: T) -> U { a }          // accepted: T and U collapse into one variable
fun add<T>(a: T, b: T) -> T { a + b }   // accepted: no bound grants `+`
fun g<U>(b: Box<U>) { b.f() }           // `f` needs `U: Tag`; checked per call, reported inside `g`
```

- A parameter used where its bounds do not grant the use is reported at a call, or not at
  all, instead of at the definition (metel-core#1320, #1323).
- A method, field or conditional-impl method the bounds do not grant is reported as
  `T0002` where the spec says `T0035`.
- The per-call re-check can accept something the definition check would reject, and a
  disagreement the other way is reported as an ordinary type error at a call site, not as
  the internal error `I0010`.

Operators on a bare parameter are a separate, language-level gap: `GAP-TYPES-005`.

## Impact

Visible to Metel programmers: a generic function that over-constrains its parameters, or
uses something its bounds never granted, is accepted and then fails at some caller (or at
none). Row-polymorphic code is affected most, because `Rest` collapsing into `R` is
accepted. Contributors: the row guarantees of RFC-0121 are not fully enforced until this
lands.

## Affects

- `spec.types.generics.rigid-type-parameters.legality-1`
- `spec.types.generics.rigid-type-parameters.legality-2`
- `spec.types.generics.rigid-type-parameters.dynamics-1`

## Resolution

Planned: implemented in installments under metel-core#1364, which closes #1320 and #1323.
`LIMIT-EVALUATION-001` (the per-call reconstruction) is removed separately, with
frontend monomorphization (metel-core#1352, #288).
