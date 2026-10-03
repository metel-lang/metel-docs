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
parameter is rigid, and a use is allowed only if the declared bounds entail it. Installments
of it are implemented (metel-core#1364): a free function's and a method's own declared
parameters are rigid after the body is solved (`T0001` at the definition), a method or field
a parameter's bounds do not grant is `T0035`, and an arithmetic or ordering operator on a
bare parameter is `T0005`. What is still missing:

```metel
fun g<U>(b: Box<U>) { b.f() }           // `f` needs `U: Tag`; checked per call, reported inside `g`
```

- A conditional-impl method is visible inside a generic body whose parameter does not
  satisfy the impl's condition; the condition is checked at the call (metel-core#1323).
- The struct's and impl's own parameters are not rigid yet, nor are closures and nested
  generic functions.
- Row equations (`where R = { label, ..Rest }`) and associated-type bindings are not held
  as typed facts inside the body, so a wrong row returned from a body is caught only where
  `Rest` collapses into `R` after solving.
- The error for a collapse is reported at the function, not at the offending expression,
  because the check runs on the solved substitution.
- A bare parameter in call position is rejected as `T0001`, not as a use the bounds do not
  grant, and bound forwarding (`g(x)` against a callee's bound) is checked per call.
- The per-call re-check (`LIMIT-EVALUATION-001`) can still reject a body the definition
  check accepted, as an ordinary type error at a call site rather than as the internal
  error `I0010`.
- Operators on a bare parameter are a separate, language-level gap: `GAP-TYPES-005`.

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
