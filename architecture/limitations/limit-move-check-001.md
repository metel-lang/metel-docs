---
id: LIMIT-MOVE-CHECK-001
title: "Closure move-check is always-on while general move-check stays opt-in"
scope: "architecture/spec/move-check.md#move-check"
owner: metel-frontend
discovered_by: "ADR-0052 §1"
disposition: accepted
review: "revisit when #267 (move checking default-on) is picked up"
---

## Limitation

v0.13.0's closure-specific move checks run unconditionally, while the
general move checker (`--move-check`, `arch.move-check.requirement-1`)
stays opt-in and off by default. ADR-0052 §1 names this explicitly as "a
temporary asymmetry," recorded so a future default-on migration (`#267`)
treats the closure checks as already-unconditional rather than something
that still needs enabling.

## Impact

A reader auditing "is move-checking on for this code" gets two different
answers depending on whether the code path involves closure captures or
not, until `#267` unifies the default.

## Affects

- `arch.move-check.requirement-1`

## Resolution

None yet — tracked as `#267` (move checking default-on).
