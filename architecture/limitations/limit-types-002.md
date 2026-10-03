---
id: LIMIT-TYPES-002
title: "`where all R: Aspect` is only implemented on a record-target impl and an open-row parameter's tail"
summary: "`where all R: A` is checked on a `{ ..R }` impl and an open-row parameter's tail, not on other impl targets, a bare row generic, or as an assumption inside a generic body."
scope: "architecture/spec/type-inference.md#type-inference"
owner: metel-frontend
discovered_by: "RFC-0123 entering 3-integrated with no implementation yet; narrowed by the first implementation slice"
disposition: planned
planned_for: v0.14.0
rfc: RFC-0123
review: null
---

## Limitation

`where all R: Aspect` parses (`all` is contextual, not reserved). It is checked on an
`extend` whose target is `{ ..R }` -- the impl applies to a record only when every field
satisfies the aspect -- and at the call for a function whose parameter has an open-row
tail (`{ x, ..R }`, a struct
residual tail, and the remainder of a `where R = { .., ..Rest }` decomposition): every
field of the argument beyond the ones the parameter names must satisfy each aspect, else
`T0012` names the field. It is not implemented in these places:

- **On other impl targets.** `extend<T> [T]: A where all T: A` and the like are rejected with
  `T0012` rather than silently ignored; only a record target has a row to walk.
- **On a row generic that is not a parameter tail.** `fun f<row R>(x: i64) where all R: Copy`
  is rejected with `T0012` rather than silently ignored.
- **As an assumption inside a generic body.** A body over an unconstrained `<row R>` gets
  nothing from `all R: Copy`, so the abstract case of width subtyping
  (`spec.types.generics.open-rows.legality-3`) is still not rejected.

```metel
fun consume<row R>(r: { id: i64, ..R }) -> i64 where all R: Copy { r.id }
consume({ id = 1, label = "x".to_string() });   // T0012: field `label` ... does not implement `Copy`
```

The Language Spec specifies the whole constraint
(`spec.types.generics.field-wise-row-constraints.legality-1`), so what remains is an
implementation shortfall against the spec, not a spec gap.

## Impact

Visible to Metel programmers: no blanket aspect implementation can be written over
every row of a given shape for an aspect whose methods need something from each field
(`Display`, `Copy`, `Eq`) in the standard library: the constraint is available to user
code on a local aspect. `std::core` declares `Display` for records this way (its body is a
built-in, `LIMIT-TYPES-003`) and `Copy` (a bodyless impl). A function can
state the requirement of its own parameter, which is checked at each call.

## Affects

- `spec.types.generics.field-wise-row-constraints.legality-1`

## Resolution

Planned: tracked as metel-core#1302 (RFC-0123 implementation tracking, milestone
v0.14.0, lands alongside RFC-0121).
