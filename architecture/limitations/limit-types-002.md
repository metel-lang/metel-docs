---
id: LIMIT-TYPES-002
title: "RFC-0123 field-wise row constraints were incomplete"
summary: "Resolved: `where all R: Aspect` is enforced at calls and supplies the definition-time entitlement required for abstract by-value row narrowing."
scope: "architecture/spec/type-inference.md#type-inference"
owner: metel-frontend
discovered_by: "RFC-0123 entering 3-integrated with no implementation yet; narrowed by the implementation slices (metel-core#1335, #1336, #1341)"
disposition: resolved
review: null
---

## Limitation

`where all R: Aspect` parses (`all` is contextual, not reserved) and is enforced where it
is written: on an `extend` whose target is `{ ..R }` (the impl applies to a record only
when every field satisfies the aspect, through method calls and `T: A` bounds, for
anonymous and nominal records) and on a function whose parameter has an open-row tail
(`{ x, ..R }`, a struct-residual tail, and the `Rest` of a `where R = { .., ..Rest }`
decomposition), where every field of the argument beyond the ones the parameter names must
satisfy each aspect, else `T0012` names the field.

```metel
fun consume<row R>(r: { id: i64, ..R }) -> i64 where all R: Copy { r.id }
consume({ id = 1, label = "x".to_string() });   // T0012: field `label` ... does not implement `Copy`
```

The completed implementation also carries this entitlement into generic bodies. A body over
an unconstrained `<row R>` that narrows a by-value row
(`spec.types.generics.open-rows.legality-3`) is rejected with `T0033` at that expression;
the same body is accepted when it states `where all R: Copy`. The entitlement applies to
the row's fields, not to `R` as a whole. Other impl targets and a row generic not used as a
parameter tail remain rejected with `T0012`, rather than silently ignoring the constraint.

## Impact

At the time, generic functions could narrow an unknown row and only fail when a caller
instantiated the body with a non-`Copy` field. The completed implementation checks the
generic body against its declared field-wise entitlement instead.

## Affects

- `spec.types.generics.open-rows.legality-3`

## Resolution

Resolved by metel-core#1302 with RFC-0173's completed generic-body checking
(metel-core#1364). Fixtures cover both the rejected unconstrained body and the accepted
`where all R: Copy` form.
