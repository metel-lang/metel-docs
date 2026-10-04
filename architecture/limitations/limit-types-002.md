---
id: LIMIT-TYPES-002
title: "`where all R: Aspect` is checked where it is written and called, not assumed in a generic body at its definition"
summary: "`where all R: A` is enforced on `{ ..R }` impls and open-row parameters at each call; a generic body gets nothing from it at its definition, and it is rejected on other impl targets and bare row generics."
scope: "architecture/spec/type-inference.md#type-inference"
owner: metel-frontend
discovered_by: "RFC-0123 entering 3-integrated with no implementation yet; narrowed by the implementation slices (metel-core#1335, #1336, #1341)"
disposition: planned
planned_for: v0.14.0
rfc: RFC-0123
review: null
---

## Limitation

`where all R: Aspect` parses (`all` is contextual, not reserved) and is fully enforced where
it is written: on an `extend` whose target is `{ ..R }` (the impl applies to a record only
when every field satisfies the aspect, through method calls and `T: A` bounds, for
anonymous and nominal records) and on a function whose parameter has an open-row tail
(`{ x, ..R }`, a struct-residual tail, and the `Rest` of a `where R = { .., ..Rest }`
decomposition), where every field of the argument beyond the ones the parameter names must
satisfy each aspect, else `T0012` names the field.

```metel
fun consume<row R>(r: { id: i64, ..R }) -> i64 where all R: Copy { r.id }
consume({ id = 1, label = "x".to_string() });   // T0012: field `label` ... does not implement `Copy`
```

What does not exist:

- **An assumption inside a generic body, at its definition.** A body over an unconstrained
  `<row R>` that narrows a by-value row (`spec.types.generics.open-rows.legality-3`) is not
  rejected where it is defined. Generic bodies are checked per instantiation (ADR-0010,
  `LIMIT-EVALUATION-001`), so the narrowing is rejected as `T0033` when the body is
  reconstructed for a call that supplies a non-`Copy` field, and accepted when it supplies
  `Copy` fields or states `where all R: Copy`. Rejecting it at the definition is the
  bounds-only rule of RFC-0173 (metel-core#1334): a body may use only what its bounds entail,
  and `all R: Copy` is such a bound.
- **Other impl targets.** `extend<T> [T]: A where all T: A` and the like are rejected with
  `T0012` rather than silently ignored; only a record target has a row to walk.
- **A row generic that is not a parameter tail.** `fun f<row R>(x: i64) where all R: Copy`
  is rejected with `T0012` rather than silently ignored.

The Language Spec specifies the whole constraint
(`spec.types.generics.field-wise-row-constraints.legality-1`, now covered by fixtures), so
the remaining gap is the definition-time check that RFC-0173 settles.

## Impact

Visible to Metel programmers: the constraint works as written, and `std::core` uses it for
`Display` (a runtime built-in body, `LIMIT-TYPES-003`) and `Copy` (a bodyless impl) on
records. A generic function that narrows an unknown row gets its error at the call that
instantiates it, inside the body, instead of at its own definition.

## Affects

- `spec.types.generics.open-rows.legality-3`

## Resolution

Implemented: the definition-time half is part of RFC-0173 (`4-implemented`, implementation metel-core#1364),
which this record's own implementation tracking (metel-core#1302) waits on.
