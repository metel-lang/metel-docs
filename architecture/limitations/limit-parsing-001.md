---
id: LIMIT-PARSING-001
title: "The dynamic array type's RFC-0171 spelling (`[T]`) does not parse yet"
summary: "RFC-0171 moves the dynamic array type from postfix `T[]` to prefix `[T]`; the grammar has not migrated, so only `T[]` parses."
scope: "architecture/spec/parsing.md#parsing"
owner: metel-frontend
discovered_by: "RFC-0171 integration pass (reference/spec/types.md 3-integrated cross-check), 2026-09-28"
disposition: resolved
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

Implemented 2026-10-01, tracked by metel-core#1291 (RFC-0171, milestone v0.14.0).
`metel-frontend/src/grammar.pest`'s `SizedArrayType`/`ArrayType`/`array_atom` productions
are merged into one `bracket_array_type = "[" type_expr (";" INT)? "]"`, unifying onto
`SizedArrayType`'s always-fully-general inner slot; postfix `T[]` no longer parses in type
position (flag-day, no dual-spelling window, per RFC-0171's own Migration section). Every
fixture in `metel-interpreter/tests/integration/sources/` and `metel-frontend/stdlib/`
(107 files, 412 sites) and every `metel` code-fence in `docs/getting-started/`,
`docs/reference/`, and `docs/rfcs/` (16 files, 46 sites) was swept to `[T]` in the same
change, via an AST-driven migration tool (never a blind regex) — scoped by code-fence
language and verified by compiling, per `PROCESS.md`'s exit criteria. This record's
exemptions on the three affected rules below are removed now that real `[T]`-spelled
fixtures cover them.
