---
id: LIMIT-TYPES-002
title: "`where all R: Aspect` is only implemented on an open-row parameter's tail"
summary: "`where all R: A` parses and is checked at the call for an open-row parameter's tail, not on an impl, a bare row generic, or inside a generic body."
scope: "architecture/spec/type-inference.md#type-inference"
owner: metel-frontend
discovered_by: "RFC-0123 entering 3-integrated with no implementation yet; narrowed by the first implementation slice"
disposition: planned
planned_for: v0.14.0
rfc: RFC-0123
review: null
---

## Limitation

`where all R: Aspect` parses (`all` is contextual, not reserved) and is checked at the
call for a function whose parameter has an open-row tail (`{ x, ..R }`, a struct
residual tail, and the remainder of a `where R = { .., ..Rest }` decomposition): every
field of the argument beyond the ones the parameter names must satisfy each aspect, else
`T0012` names the field. It is not implemented in these places:

- **On an `extend` block.** `extend<row R> { ..R }: Display where all R: Display` needs
  the structural impl target, which does not parse (metel-core#1306 item 8).
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
(`Display`, `Copy`, `Eq`) — only a concrete, closed-row impl is writable today. A
function can state the requirement of its own parameter, which is checked at each call.

## Affects

- `spec.types.generics.field-wise-row-constraints.legality-1`

## Resolution

Planned: tracked as metel-core#1302 (RFC-0123 implementation tracking, milestone
v0.14.0, lands alongside RFC-0121).
