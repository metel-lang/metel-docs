---
id: LIMIT-TYPES-003
title: "Record `Display` is a runtime built-in, not Metel code"
summary: "`Display` for a record of `Display` fields is a built-in in the evaluator, a stand-in for RFC-0174's `comptime for`; no user aspect, and no `Eq`/`Hash`, can walk a record's fields; `Clone` is likewise a built-in."
scope: "architecture/spec/evaluation.md#evaluation"
owner: metel-interpreter
discovered_by: "metel-core#1338: implementing `Display` for records after RFC-0123's `where all R: Display` landed"
disposition: planned
rfc: RFC-0174
review: null
---

## Limitation

`std::core` declares `extend<row R> { ..R }: Display where all R: Display`, so every record
whose fields are all `Display` is `Display`: anonymous and nominal records, nested records,
and records with fields whose types have a `Display` impl of their own. The impl's body is
not Metel code. Nothing in the language can iterate a row's fields, so the method is a
`native` whose host function (`metel-interpreter/src/evaluator/record_display.rs`,
intercepted by label in `call_runtime_callable` because it needs the runtime to call each
field's own `to_string`) formats the receiver at runtime, fields in label order:

```metel
let p := { x = 1, y = 2.5, s = "hi" };
println("${p}");        // { s: hi, x: 1, y: 2.5 }
```

The condition is checked statically (`where all R: Display`; a field without `Display` is
`T0012` naming the field). Only the *body* is built in. Consequences:

- **The format and the aspect are fixed in the evaluator.** There is no way to write a
  different blanket impl, or the same impl for another aspect.
- **No other aspect gets this for free.** `Eq`, `Hash` and `Default` for records,
  and any user aspect (a serializer, a schema generator), cannot walk a record's fields.
  `Copy` needs no body: `std::core` provides it as an ordinary bodyless impl, so it is not
  affected by this limitation (metel-core#1337).
- **A nominal `record`'s own `Display` still wins**, by brand-first dispatch
  (`spec.types.generics.row-conditional-impls.legality-2`).

## Impact

Visible to Metel programmers: records print and compare through `Display` where they could
not before, but a user cannot write the same kind of field-walking impl for their own
aspect. Contributors: the built-in is a special case that every further derived aspect would
have to repeat in Rust.

## Affects

- `spec.types.generics.field-wise-row-constraints.legality-1`
- `spec.types.anonymous-records.legality-1`

<!-- limit.py:markers:start -->
- [`metel-interpreter/src/evaluator/record_display.rs::record_to_string`](https://github.com/metel-lang/metel-core/blob/cb6e01cd8aff28da4c3f2a860dbcb18969b4f2f1/metel-interpreter/src/evaluator/record_display.rs#L20)
<!-- limit.py:markers:end -->

## Resolution

Planned: RFC-0174 (`1-under-review`, design settlement metel-core#1340) specifies a
`comptime for` loop over a row's fields with computed access `self.[field.name]`, checked
once against a symbolic field. When it is implemented the `std::core` impl is rewritten in
Metel with that loop and `record_display.rs`, the label interception and the
`StdCoreRecordToString` native key are deleted. Until then this record stays open; the
implementation of `Display` itself is metel-core#1338.
