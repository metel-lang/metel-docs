---
id: GAP-DECLARATIONS-002
title: "Aspect implementations may not safely widen a method's generic constraints"
summary: "An implementation's generic constraints must match the aspect method's exactly, even where a looser signature would be safe."
scope: "reference/spec/declarations.md#spec.declarations.aspects.implementing-an-aspect.legality-13"
owner: language
discovered_by: "metel-core#1217 limitation analysis; fixtures `typechecking/aspects/stage21_neg_08` and `stage21_neg_09`"
disposition: known
review: null
---

## Gap

An implementation method's generic-constraint conjunction must be
structurally equal to the aspect method's, after normalization. This is the
RFC-0129 minimal interim rule, and it rejects some implementations that would
be sound: one that drops a generic bound (a constraint *widening*), and one
that drops the record kind. Both are rejected with `T0012`.

## Impact

An implementation cannot be more permissive than its aspect's method
signature even where that is safe. The workaround is to restate the aspect's
constraints exactly.

## Affects

- `spec.declarations.aspects.implementing-an-aspect.legality-13`
- `RFC-0129`

## Resolution

None scheduled. The two negative fixtures pin the behaviour and are marked to
flip to positive fixtures if admissible-domain-inclusion conformance is ever
adopted.
