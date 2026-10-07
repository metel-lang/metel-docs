---
id: GAP-TYPES-008
title: "A record literal accepts at most one row spread"
summary: "No form combines the fields of two rows into one record: merging two generic records has no spelling."
scope: "reference/spec/types.md#open-rows"
owner: language
discovered_by: "RFC-0178 review"
disposition: known
rfc: RFC-0178
review: null
---

## Gap

`{ ..a, ..b }` places two rows in one record. Its row is well-formed only if the two rows
share no label. For concrete rows that is a check by inspection; for abstract rows
(`{ ..R }` and `{ ..S }`) the declared bounds can state per-label absence (`R: !{ x }`) but
not that two rows are disjoint as wholes. RFC-0178 therefore allows one spread per literal.
Nesting does not work around it, since each spread still needs its own absence proof.

## Impact

Visible to Metel programmers: merging two generic records into one has no spelling. Merge
concrete records field by field.

## Affects

- `spec.types.generics.open-rows.legality-2`

## Resolution

Not scheduled. Needs a row-disjointness bound (for example `R # S`), which would be its own
RFC.
