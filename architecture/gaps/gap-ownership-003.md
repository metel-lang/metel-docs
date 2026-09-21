---
id: GAP-OWNERSHIP-003
title: "A field cannot be moved out of a `Drop` type, even where its destructor would not need it"
summary: "Moving a field out of a `Drop` type is always rejected; row-bounded `Drop` dispatch would allow it where the destructor does not need that field."
scope: "reference/spec/ownership.md#spec.ownership.partial-moves.legality-2"
owner: language
discovered_by: "metel-core#1235 conversion of the `Planned for` notes in `reference/spec/ownership.md` (RFC-0137 §5)"
disposition: planned
planned_for: v0.14.0
rfc: RFC-0137
review: null
---

## Gap

The Language Spec bans moving a field out of a `Drop` type unconditionally
([legality-2](../../reference/spec/ownership.md#spec.ownership.partial-moves.legality-2)),
so a destructor never runs against a value whose fields have been narrowed
away. RFC-0137 §5 replaces the ban with row-bounded `Drop` dispatch: a `Drop`
impl's required field set is the residual row its `drop` receiver declares,
and a move is allowed when the remaining row still covers it. That needs the
narrowed `drop` receiver (RFC-0109). The section "Drop dispatch against a
narrowed residual" specifies the mechanism; until it is built the ban is
enforced exactly as stated.

## Impact

Code that wants to take one field of a `Drop` type and let the rest be
dropped later must restructure, for example by moving the whole value.

## Affects

- `spec.ownership.partial-moves.legality-2`
- `spec.ownership.drop-dispatch-against-a-narrowed-residual.legality-1`
- `RFC-0137`

## Resolution

Planned for v0.14.0, tracked as metel-core#949 (RFC-0137 §5).
