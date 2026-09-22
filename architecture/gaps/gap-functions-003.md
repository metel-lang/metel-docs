---
id: GAP-FUNCTIONS-003
title: "Written function types are move-only, with no `copy` qualifier or `Erased` state yet"
summary: "A written function type is always move-only; the `copy |T| -> U` qualifier and the `Erased` (capability unknown) state are not available."
scope: "reference/spec/functions.md#first-class-functions"
owner: language
discovered_by: "metel-core#1235 records pass over the limit-phrasing lint of `reference/spec/functions.md`"
disposition: planned
planned_for: v0.17.0
rfc: RFC-0163
review: null
---

## Gap

RFC-0166 (v0.13.0) makes a written function type lower to a concrete move-only type and erases copyability where a value flows into such a slot. The full surface (a `copy |T| -> U` qualifier for an explicitly copyable callable, and a distinct "capability unknown" state) is RFC-0163, rescheduled to v0.17.0, which refines the move-only state rather than replacing it.

## Impact

A closure that could be copied loses that once it passes through a slot with a written function type, and there is no way to require or preserve copyability there.

## Affects

- `RFC-0163`
- `LIMIT-TYPE-INFERENCE-008`

## Resolution

Planned for v0.17.0, tracked as metel-core#936 (RFC-0163).
