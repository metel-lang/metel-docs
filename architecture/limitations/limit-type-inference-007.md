---
id: LIMIT-TYPE-INFERENCE-007
title: "Type checking time grows quadratically with the number of functions in a module"
summary: "Checking a module takes about four times as long each time its function count doubles: 8,000 trivial functions take about 79 seconds in a release build."
scope: "architecture/spec/type-inference.md#type-inference"
owner: metel-frontend
discovered_by: "size probe run while reviewing the type var generator (LIMIT-TYPE-INFERENCE-005)"
disposition: known
review: null
---

## Limitation

Type checking cost is not linear in the number of function declarations in one
module. Measured on a release build (`cargo build --release -p metel`), running a
module of `n` one-line functions plus an empty `main`:

| `n` | generic (`fun gN<T>(x: T) -> T`) | non-generic (`fun fN(x: i64) -> i64`) | structs (`struct SN { a: i64 }`) |
|---|---|---|---|
| 1,000 | 1.5 s | 1.6 s | 0.5 s |
| 2,000 | 4.6 s | 5.2 s | 0.9 s |
| 4,000 | 17.2 s | 19.7 s | 2.2 s |
| 8,000 | not run | 78.6 s | not run |

Each doubling of the function count multiplies the time by about four, for
generic and non-generic functions alike (a further generic series: 5,000 in
28.7 s, 9,000 in 89.6 s, 10,500 in 120.5 s, 12,000 over 150 s). Structs scale
close to linearly, so the cost is per function declaration, not per declaration.

I did not profile it. The pattern is consistent with a per-function step that
scans the whole environment, for example `generalize` over
`InferContext::env_free_vars()`, which visits every binding in scope each time a
function is generalized; that is a suspicion, not a finding.

## Impact

Large generated or machine-written modules (thousands of functions) are checked
slowly, and doubling the module quadruples the cost; a debug build is several
times slower again. Ordinary hand-written modules are far below the size where it
shows. It is also a reason parallelising the checker would not by itself be
enough (`LIMIT-TYPE-INFERENCE-006`).

## Affects

- `arch.type-inference.requirement-1`
- `arch.type-inference.requirement-7`
- `metel-frontend/src/typeinference/mod.rs` (`generalize`, `env_free_vars`)

<!-- limit.py:markers:start -->
- [`metel-frontend/src/typeinference/mod.rs::generalize`](https://github.com/metel-lang/metel-core/blob/4155d94ccbc5b1657799f3537515610f3bb139c3/metel-frontend/src/typeinference/mod.rs#L1695)
<!-- limit.py:markers:end -->

## Resolution

None yet. Profile a large module first; if the environment scan is the cause,
maintaining the environment's free variables incrementally (or generalizing
top-level functions against a fixed prelude environment) would make it linear.
