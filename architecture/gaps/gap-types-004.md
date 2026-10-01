---
id: GAP-TYPES-004
title: "A blanket row-conditional aspect impl's body cannot require an aspect of every field"
summary: "`extend<row R> { ..R }: A { ... }` has no way to say `A`'s body needs every field in `R` to itself be `A` (or any other aspect)."
scope: "reference/spec/types.md#implementing-an-aspect-for-a-record"
owner: language
discovered_by: "metel-core#1235 stale-passage check of `reference/spec/types.md`; narrowed 2026-10-01 once RFC-0121 specified row variables and row-conditional impl resolution (`spec.types.generics.open-rows.*`, `spec.types.generics.row-conditional-impls.*`, LIMIT-TYPES-001)"
disposition: planned
planned_for: v0.14.0
rfc: RFC-0123
review: null
---

## Gap

The spec now specifies row variables, `..R`, row decomposition, and row-conditional
impl resolution (RFC-0121, `3-integrated` — see [Open
rows](../../reference/spec/types.md#open-rows) and the row-conditional-impls rules
immediately below it in [Implementing an aspect for a
record](../../reference/spec/types.md#implementing-an-aspect-for-a-record)); none of it
is implemented yet (`LIMIT-TYPES-001`), which is an implementation shortfall, not a
spec gap, for everything RFC-0121 covers.

What the spec still does not specify: `extend<row R> { ..R }: A { ... }`'s *body* has no
way to require that every field in `R` itself satisfies some aspect (`A` or otherwise) —
`Display`'s own body needs each field to itself be `Display` before it can call
`.to_string()` on it generically, and nothing in RFC-0121 supplies that per-field
quantifier. `extend<row R> { ..R }: Display` is legal *declaration* syntax under
RFC-0121 alone, but there is no bound letting its body type-check against an arbitrary
field. This is `all R: Aspect` (RFC-0123, `2-accepted`, not yet integrated).

## Impact

A blanket aspect implementation over every row cannot be written for any aspect whose
own methods need something from each field (`Display`, `Copy`, `Eq`) — only a
concrete, closed-row impl (the first of the three forms) is actually writable today.
Anonymous records and `record`s stay unable to implement any such aspect generically.

## Affects

- `spec.types.generics.row-conditional-impls.legality-1`
- `RFC-0123`

## Resolution

Planned for v0.14.0, alongside RFC-0121 (same cluster, same milestone) — tracked as
metel-core#1302 (RFC-0123 implementation tracking).
