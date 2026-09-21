---
id: GAP-DECLARATIONS-003
title: "No `Ord` or `Hash` aspect exists, so no type has ordering or hashing impls"
summary: "Neither `Ord` nor `Hash` exists in `std::core`, so no type, arrays included, has an ordering or hashing implementation."
scope: "reference/spec/declarations.md#structural-aspect-bounds"
owner: language
discovered_by: "metel-core#1235 records pass over the limit-phrasing lint of `reference/spec/declarations.md`"
disposition: known
rfc: RFC-0062
review: null
---

## Gap

The standard array impls cover `Display`, `Clone` and `Eq` only. `Ord` is proposed in RFC-0062, which is still `0-draft`; `Hash` has not been proposed. Neither aspect exists in `std::core`, for arrays or any other type.

## Impact

No aspect bound can require ordering or hashing, and no type has such an implementation.

## Affects

- `RFC-0062`

## Resolution

Not scheduled: RFC-0062 is `0-draft` and `Hash` has no RFC. Moves to `planned` once an RFC is accepted and milestoned.
