---
id: LIMIT-PARSING-001
title: "The dynamic array type's RFC-0171 spelling (`[T]`) does not parse yet"
summary: "RFC-0171 moves the dynamic array type from postfix `T[]` to prefix `[T]`; the grammar has not migrated, so only `T[]` parses."
scope: "architecture/spec/parsing.md#parsing"
owner: metel-frontend
discovered_by: "RFC-0171 integration pass (reference/spec/types.md 3-integrated cross-check), 2026-09-28"
disposition: planned
planned_for: v0.14.0
rfc: RFC-0171
review: null
---

## Limitation

RFC-0171 (`2-accepted`, moved to `3-integrated` 2026-09-28) moves the dynamic array type's
spelling from postfix `T[]` to prefix `[T]`, matching `[T; N]`'s existing convention. The
grammar has not migrated: `metel-frontend/src/grammar.pest`'s `SizedArrayType`/`ArrayType`
productions are unchanged, and `reference/spec/grammar.md` (generated from that file) still
shows them as-is. `[T]` in type position does not parse; postfix `T[]` remains the only
spelling the interpreter accepts. Verified directly against `develop`, 2026-09-28:

```metel
fun sum(xs: [i64]) -> i64 { xs[0] }
```

fails to parse; the postfix spelling (`fun sum(xs: i64[]) -> i64 { xs[0] }`) is required
today.

## Impact

Every `T[]`-typed program in the corpus (~460 fixture sites, ~395 doc/prose sites at RFC
drafting time) continues to use the pre-RFC-0171 spelling; none of it is affected
semantically — RFC-0171 changes only the spelling token, not the type's runtime
representation, coercions, or Copy/ownership semantics (RFC-0171 §1: "same runtime
representation, same coercions, same everything except the spelling"). `reference/spec/
types.md`'s "Arrays" and "Fixed-size arrays" sections now state `[T]` as the current design;
the interpreter has not caught up. Every other mention of the dynamic array type elsewhere
in the spec corpus (the `List<T>` section, generic-function examples, aspect-impl prose, and
so on) deliberately still reads `T[]` — those sweep together with the actual code migration
per RFC-0171's own Migration section, not piecemeal ahead of it.

## Affects

- `spec.types.arrays.legality-1`
- `spec.types.fixed-size-arrays.legality-1`
- `spec.types.fixed-size-arrays.legality-2`

## Resolution

Planned: tracked as metel-core#1291 (RFC-0171, milestone v0.14.0). Implementation is a
flag-day migration (RFC-0171's own Migration section, no dual-spelling window): merge
`SizedArrayType`/`ArrayType` into one `BracketArrayType` production, retire postfix `T[]`
in type position the same release, and sweep every fixture and doc site to `[T]` in the same
change — not as a follow-up. Once implemented, remove this record's exemptions from the
three affected rules above, re-point their fixture citations at real `[T]`-spelled fixtures,
and run `rfc.py transition rfc-0171 --to implemented`.
