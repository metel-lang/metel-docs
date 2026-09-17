---
id: LIMIT-TYPE-CONSTRUCTION-003
title: "`?` error coercion requires an explicit From impl"
scope: "architecture/spec/type-construction.md#type-construction"
owner: metel-frontend
discovered_by: "metel-interpreter/docs/evaluator.md, \"Known Limitations\" (updated v0.7.0 / METEL-80)"
disposition: known
review: null
---

## Limitation

`?` is desugared in the `path_normalizer` pre-pass, then checked during
construction for error-type compatibility. If the inner `Result<_, E1>`'s
error type differs from the enclosing function's `Result<_, E2>`, construction
looks up `impl From<E1> for E2`; if none exists, the program is rejected with
`T0007`. Only two built-in `From` impls exist: `From<Float> for Int` and
`From<Int> for Float`. Full coercion for arbitrary type pairs is tracked
separately as `#13`.

## Impact

A user combining two custom error types across a `?` boundary must write an
explicit `From` impl themselves; there is no automatic or derived coercion
path for arbitrary error types.

## Affects

- `arch.type-construction.requirement-2`

## Resolution

Partial. The `?`/`From` coercion mechanism itself is fully wired (METEL-80,
shipped v0.7.0) — the open part is only "full coercion for arbitrary type
pairs," tracked as `#13`.
