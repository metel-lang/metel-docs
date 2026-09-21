---
id: LIMIT-TYPE-INFERENCE-001
title: "`?` error coercion requires an explicit From impl"
summary: "Superseded: the spec itself requires an explicit `From` impl for `?` to convert between error types, so this is specified behaviour, not a limitation."
scope: "architecture/spec/type-inference.md#type-inference"
owner: metel-frontend
discovered_by: "metel-interpreter/docs/evaluator.md, \"Known Limitations\" (updated v0.7.0 / METEL-80); re-scoped during ADR lifecycle triage (#1158) after checking which pass actually performs the check"
disposition: superseded
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
- `spec.functions.the-operator.legality-2`

## Resolution

Superseded, not fixed: this is not a limitation of the implementation. The
Language Spec specifies exactly this behaviour: `spec.functions.the-operator.legality-2`
says the operand error type `E1` "must equal `E2` or satisfy `E2: From<E1>`", and the
`?` prose says `From::from` is called on the error when they differ. A correct
implementation of the current spec therefore also requires an explicit `From` impl
(ADR-0057's sorting test), and the only built-in impls are the `i64`/`f64` ones the
spec lists (`runtime.md`, built-in aspects). The follow-up this record cited, `#13`,
is closed. If automatic or derived error conversion is ever wanted, that is a new
language change, not the closing of this record.
