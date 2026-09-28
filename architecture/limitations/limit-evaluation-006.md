---
id: LIMIT-EVALUATION-006
title: "RFC-0167's error-code reclassification and main-entry Legality Rule are not implemented"
summary: "Six R00NN codes still fire instead of their I00NN replacements; the main-entry check still runs at evaluator startup instead of typechecking, under retired R0001/R0002."
scope: "architecture/spec/evaluation.md#evaluation"
owner: metel-interpreter
discovered_by: "RFC-0167 integration pass (reference/spec/functions.md, reference/error-codes.md 3-integrated cross-check), 2026-09-28"
disposition: planned
planned_for: v0.14.0
rfc: RFC-0167
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

Planned: tracked as metel-core#991 (RFC-0167, milestone v0.14.0). Implementation:
add `I0003`-`I0009` and retire `R0001`-`R0002` (main cases)/`R0003`/`R0006`/`R0008`/
`R0009`/`R0010`/`R0011` in the Rust enums; move the `main`-declaration check from
`evaluator/mod.rs` into the typechecking (or program-assembly) pipeline as `T0031`;
update every fixture citing a retired code to its replacement (`rfc.py check`'s
per-fixture citation-consistency check catches anything missed). Once implemented,
remove this record's exemptions from the affected `error-codes.md` entries and
`spec.functions.program-entry-point.legality-1`, re-point their fixture citations at
the real new-code fixtures, and run `rfc.py transition rfc-0167 --to implemented`.
