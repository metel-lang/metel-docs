---
id: GAP-EXPRESSIONS-001
title: "A record rest pattern cannot borrow the remainder through a reference"
summary: "No form binds the remainder of a record through a reference: a borrowed view of \"everything but these fields\" has no spelling."
scope: "reference/spec/expressions.md#struct-patterns"
owner: language
discovered_by: "RFC-0178 review: borrowed rest patterns need the `&var` splitting rules of RFC-0122"
disposition: known
rfc: RFC-0178, RFC-0122
review: null
---

## Gap

RFC-0178's rest pattern (`let { x, ..rest } := r`) consumes an owned record. Applied to a
reference, `let { x, ..rest } := &r` could bind `x: &T` and `rest: &{ ..Rest }`, a borrowed
view of the remainder, and with `&var` a split mutable borrow. That needs the shared/exclusive
rules that borrow checking provides, so it is reserved: the form is rejected with a message
pointing at the owned form. Until then a function that must not consume its argument cannot
take a remainder out of it generically.

## Impact

Visible to Metel programmers: typestate steps that take `self` by value are unaffected. Code
that wants "this field, and a view of everything else" from a borrowed row has no spelling;
read the named fields through the reference instead.

## Affects

- `spec.expressions.struct-patterns.legality-1`

## Resolution

Not scheduled. Revisit once RFC-0122 (borrow checking) is implemented; RFC-0175's
`drain_field` sketch has the same shape.
