---
id: LIMIT-TYPE-INFERENCE-001
title: "`?` error coercion requires an explicit From impl"
summary: "`?` needs an explicit `From` impl to convert between error types; only `Int` and `Float` are built in."
scope: "architecture/spec/type-inference.md#type-inference"
owner: metel-frontend
discovered_by: "metel-interpreter/docs/evaluator.md, \"Known Limitations\" (updated v0.7.0 / METEL-80); re-scoped during ADR lifecycle triage (#1158) after checking which pass actually performs the check"
disposition: known
review: null
---

## Limitation

`?` is desugared in the `path_normalizer` pre-pass, then checked during
*inference* (not construction — `evaluator.md`'s own text says "during
construction," which this record originally repeated without checking; the
real call site is `typechecker/inference.rs`'s `?`-expression handling
calling `TypeCtx::has_from_impl`, confirmed directly against current
source) for error-type compatibility. If the inner `Result<_, E1>`'s error
type differs from the enclosing function's `Result<_, E2>`, inference looks
up `impl From<E1> for E2`; if none exists, the program is rejected with
`T0007`. Only two built-in `From` impls exist: `From<Float> for Int` and
`From<Int> for Float`. Full coercion for arbitrary type pairs is tracked
separately as `#13`.

## Impact

A user combining two custom error types across a `?` boundary must write an
explicit `From` impl themselves; there is no automatic or derived coercion
path for arbitrary error types.

## Affects

- `arch.type-inference.requirement-3`

## Resolution

Partial. The `?`/`From` coercion mechanism itself is fully wired (METEL-80,
shipped v0.7.0) — the open part is only "full coercion for arbitrary type
pairs," tracked as `#13`.
