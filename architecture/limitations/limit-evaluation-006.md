---
id: LIMIT-EVALUATION-006
title: "RFC-0167's error-code reclassification and main-entry Legality Rule are not implemented"
summary: "Six R00NN codes still fire instead of their I00NN replacements; the main-entry check still runs at evaluator startup instead of typechecking, under retired R0001/R0002."
scope: "architecture/spec/evaluation.md#evaluation"
owner: metel-interpreter
discovered_by: "RFC-0167 integration pass (reference/spec/functions.md, reference/error-codes.md 3-integrated cross-check), 2026-09-28"
disposition: resolved
review: null
---

## Limitation

RFC-0167 (`2-accepted`, moved to `3-integrated` 2026-09-28) reclassifies six
unsoundness-only runtime codes (`R0003`, `R0006`, `R0008`, `R0009`, `R0010`, `R0011`)
as internal errors (`I0003`-`I0008`), retires `R0001`/`R0002` in favor of a new
compile-time Legality Rule (`T0031`, `spec.functions.program-entry-point.legality-1`)
for the program's `main` function, and splits `R0002`'s two non-`main` raise sites
into `I0007` (merging with the `R0010` reclassification) and a wholly new `I0009`.
None of this is implemented: `metel-frontend/src/data/error/mod.rs`'s
`RuntimeErrorCode`/`InternalErrorCode`/`TypeErrorCode` enums are unchanged, and
`evaluator/mod.rs`'s `env.get("main")` check still runs lazily at evaluator startup,
not during typechecking. Every one of R0001/R0002/R0003/R0006/R0008/R0009/R0010/R0011
continues to fire exactly as documented in their own (now-retired) `error-codes.md`
entries.

## Impact

A program triggering any of the six reclassified codes, or either main-entry case,
still sees the pre-RFC-0167 code and message today — the reclassification is a
documentation-and-numbering decision made now (per RFC-0167's own Migration section:
"new number assignment happens at integration time"), not yet backed by matching
interpreter behavior. The nine new/retired-target entries in `error-codes.md`
(`T0031`, `I0003`-`I0009`) and the new `spec.functions.program-entry-point.legality-1`
rule in `reference/spec/functions.md` are exempted from fixture coverage for this
reason; the eight retired entries (`R0001`/`R0002`/`R0003`/`R0006`/`R0008`/`R0009`/
`R0010`/`R0011`) keep their own existing fixtures/exemptions unchanged, since they
still accurately describe today's actual behavior.

## Affects

- `spec.functions.program-entry-point.legality-1`

## Resolution

Implemented 2026-09-28, tracked by metel-core#991 (RFC-0167, milestone v0.14.0).
`metel-frontend/src/data/error/mod.rs`'s `RuntimeErrorCode` no longer has R0001-R0003/
R0006/R0008-R0011; `InternalErrorCode` gained `I0003`-`I0009`; `TypeErrorCode` gained
`T0031`. `evaluator/mod.rs::evaluate_graph_with_options` now runs a new
`check_program_entry_point` static check against the root module's already-typed
declarations *before* any module's passes run (not lazily inside `run_main` as
`env.get("main")` used to), raising `T0031` for a missing/non-function/generic/
non-zero-arity `main`; `run_main` itself no longer raises R0001/R0002 at all --
every remaining arm there is a "should be unreachable after T0031" internal-error
defensive fallback. All eight retired R-codes' raise sites in `call.rs`/`lvalue.rs`/
`builtins.rs`/`evaluator/mod.rs` now raise their `I00NN`/`T0031` replacements
instead. Fixtures `neg_07_no_main`/`neg_08_main_not_a_function` were updated to
expect `T0031`/`typecheck_error`; two new fixtures (`neg_09_main_is_generic`,
`neg_10_main_has_params`) were added since no fixture previously exercised those
cases. `error-codes.md`'s and `spec.functions.program-entry-point.legality-1`'s
`blocked`-on-#991 exemptions are removed now that real fixtures cover them; the
per-code `blocked`-on-#986/#989 reachability exemptions on `I0003`-`I0008` carry
over unchanged from their retired R-code predecessors (the underlying reachability
question, not the RFC-0167 timing question, which is now moot).
