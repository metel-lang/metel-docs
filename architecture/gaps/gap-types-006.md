---
id: GAP-TYPES-006
title: "A generic body cannot construct or consume a row remainder"
summary: "A `where` equation can type the remainder of a row, but no form lets a body take an abstract row apart or build one, so typestate over a row cannot be implemented generically."
scope: "reference/spec/types.md#open-rows"
owner: language
discovered_by: "metel-core#1397 documentation work on records and rows; filed as metel-core#1399"
disposition: planned
rfc: RFC-0178
review: null
---

## Gap

`where R = { token: Token, ..Rest }` lets a signature promise `Session<..Rest>`, and a
caller gets that type. The language has no value-level form for the same operation. A record
pattern's bare `..` discards the unnamed fields instead of binding them, and a record
literal has no `..`-form, although the same tail is written freely in a record *type*. A
body therefore cannot produce the remainder of an abstract row from the whole, nor extend a
row by a field. Writing the removed label back is rejected by design.

```metel
extend<row R, row Rest> Session<..R> where R = { token: Token, ..Rest } {
    fun authenticate(self) -> Session<..Rest> { ... }   // no way to write the body
}
```

Concrete rows are unaffected: with the fields known, a literal can be rebuilt by hand.

## Impact

Visible to Metel programmers: the signature of a typestate step over an open row is
expressible, its implementation is not. Write the step for concrete rows, or model the
state as a separate type.

## Affects

- `spec.types.generics.open-rows.legality-2`

## Resolution

Planned: RFC-0178 (`1-under-review`) proposes a record rest pattern (`{ token, ..rest }`) and
a row spread in record literals (`{ ..rest, auth = a }`). Tracked by metel-core#1399.
