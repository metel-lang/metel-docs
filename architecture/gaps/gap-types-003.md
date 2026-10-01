---
id: GAP-TYPES-003
title: "There is no nominal record kind, so named records are unavailable"
summary: "RESOLVED: RFC-0120 (Named Records) specifies and now implements a nominal record kind that satisfies row bounds."
scope: "reference/spec/types.md#row-bounds"
owner: language
discovered_by: "metel-core#1235 records pass over the limit-phrasing lint of `reference/spec/types.md`; found stale during RFC-0120's implementation pass, 2026-10-01"
disposition: resolved
review: null
---

## Gap

**Resolved.** Nominal structs do not satisfy row bounds, and the only record type used
to be the anonymous record. RFC-0120 (Named Records, `4-implemented`) specifies and now
implements a nominal `record` declaration kind whose row is structurally visible
(`spec.declarations.records.*`).

## Impact

None remaining — a record that needs a name, an owning module or its own aspect impls
can now be declared `record` instead of `struct`, and its declared row satisfies a row
bound.

## Affects

- `RFC-0120`

## Resolution

Resolved 2026-10-01: RFC-0120 reached `3-integrated` (spec text committed to
`reference/spec/declarations.md#records`) and then `4-implemented`, landed in
metel-core#1303 (tracked by metel-core#1300).
