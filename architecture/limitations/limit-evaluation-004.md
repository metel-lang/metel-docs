---
id: LIMIT-EVALUATION-004
title: "The evaluator is a deliberate PoC, not the target implementation shape"
scope: "architecture/spec/evaluation.md#evaluation"
owner: metel-interpreter
discovered_by: "this session's architecture-spec inventory (direct source reading), 2026-09-17"
disposition: accepted
review: null
---

## Limitation

`evaluator/mod.rs` opens with its own verbatim statement of intent: "PoC
evaluator — this implementation will almost certainly be rewritten.
Implement the simplest correct thing; do not over-engineer." This is a
deliberate, currently-real architectural posture, not an incidental
comment — `evaluator.md`'s own "Rewrite" section names the intended
eventual replacement (a tagged-pointer or NaN-boxing value representation,
carrying the v0.13.0 closure-capture model forward, RFC-0122 borrow
checking replacing the in-call reentrancy flag, `dyn Aspect`'s real
fat-pointer/vtable representation).

## Impact

None of `arch.evaluation.*`'s requirements should be read as describing a
stable target shape for future extension — they describe the current,
real, correct-for-now PoC, which the project's own docs say will almost
certainly be rewritten. A future implementer should not treat this
section's requirements as constraints on the rewrite; they describe what
exists, not what must persist.

## Affects

- `arch.evaluation.requirement-1`
- `arch.evaluation.requirement-2`

## Resolution

None yet — accepted as the current, deliberate state. `evaluator.md`'s
"Rewrite" section is the forward-looking plan, not this record's job to
restate in full.
