---
id: GAP-TYPES-003
title: "There is no nominal record kind, so named records are unavailable"
summary: "Only anonymous records exist; a nominal record kind (RFC-0120 Named Records) is accepted but not implemented."
scope: "reference/spec/types.md#row-bounds"
owner: language
discovered_by: "metel-core#1235 records pass over the limit-phrasing lint of `reference/spec/types.md`"
disposition: planned
planned_for: v0.14.0
rfc: RFC-0120
review: null
---

## Gap

Nominal structs do not satisfy row bounds, and the only record type is the anonymous record. RFC-0120 (`2-accepted`) would provide a nominal record kind.

## Impact

A record that needs a name, an owning module or its own aspect impls has to be a struct, which does not satisfy a row bound.

## Affects

- `RFC-0120`

## Resolution

Planned for v0.14.0, tracked as metel-core#791 (RFC-0120).
