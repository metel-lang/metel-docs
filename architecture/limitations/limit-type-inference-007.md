---
id: LIMIT-TYPE-INFERENCE-007
title: "Type checking time grows super-linearly with the number of functions in a module"
summary: "Two confirmed O(n) per-function costs (metel-core#1232) cut an 8,000-function module from ~79s to ~6.6s; a smaller super-linear residual remains, unprofiled."
scope: "architecture/spec/type-inference.md#type-inference"
owner: metel-frontend
discovered_by: "size probe run while reviewing the type var generator (LIMIT-TYPE-INFERENCE-005)"
disposition: known
review: null
---

## Limitation

Type checking cost is not linear in the number of function declarations in one
module. Measured on a release build (`cargo build --release -p metel`), running a
module of `n` one-line functions plus an empty `main`, **before** metel-core#1232:

| `n` | generic (`fun gN<T>(x: T) -> T`) | non-generic (`fun fN(x: i64) -> i64`) | structs (`struct SN { a: i64 }`) |
|---|---|---|---|
| 1,000 | 1.5 s | 1.6 s | 0.5 s |
| 2,000 | 4.6 s | 5.2 s | 0.9 s |
| 4,000 | 17.2 s | 19.7 s | 2.2 s |
| 8,000 | not run | 78.6 s | not run |

Each doubling of the function count multiplied the time by about four, for
generic and non-generic functions alike. Structs scaled close to linearly, so
the cost was per function declaration.

metel-core#1232 profiled this (`std::time::Instant` around each pipeline stage,
plus `TypecheckPhaseTimings`'s existing per-phase breakdown) and found two
confirmed, independent `O(position)`-per-call costs, neither the originally
suspected `generalize`/`env_free_vars` (checked directly: `InferContext::
mono_env`'s length stays constant across thousands of functions, so its
`env_free_vars` scan is not the cause):

1. **Parsing, not type checking, was the dominant cost** (~95% of total time
   at 4,000 functions): `data::ast::Span::of` called `pest::Position::
   line_col()` once per parsed AST node, which scans the input *from its
   start* to count newlines -- `O(byte offset)` per call. A precedence-climbing
   grammar builds many nodes per expression, at increasing file positions
   throughout a module, so the summed cost was `O(file length)^2`. Fixed by
   precomputing each line's starting offset once per parse and answering each
   query by binary search.
2. **`InferContext::default_literal_vars`** cloned its entire `subst`
   argument -- `InferContext`'s one substitution, accumulated across every
   function in the module -- and this runs once per function (the "inline
   solve-and-generalize" step in `infer_fun_decl`/`infer_impl_method`), even
   for a body with no integer or float literals to default. Fixed by
   returning a small overlay chained onto the base substitution instead of a
   merged clone.

After both fixes, the same non-generic series: 2,000 in 0.56 s (was 5.2 s),
4,000 in 1.8 s (was 19.7 s), 8,000 in 6.6 s (was 78.6 s) -- roughly a 10-12x
improvement at each size. Scaling is markedly closer to linear (each doubling
now costs roughly 3.2-3.6x, not ~4x) but a smaller super-linear residual
remains in `TypecheckPhaseTimings::inference_ns`, confirmed independent of
both fixed causes (still present with `integer_literal_vars`/
`float_literal_vars` empty throughout, e.g. `fun fN() {}`, and independent of
`env_free_vars`, checked directly as above). Not yet isolated further.

## Impact

Large generated or machine-written modules (thousands of functions) are
checked more slowly than they should be, though the fixed causes accounted
for the overwhelming majority of the originally measured cost. Ordinary
hand-written modules are far below the size where the residual shows. It is
also a reason parallelising the checker would not by itself be enough
(`LIMIT-TYPE-INFERENCE-006`).

## Affects

- `arch.type-inference.requirement-1`
- `arch.type-inference.requirement-7`
- `metel-frontend/src/data/ast.rs` (`Span::of`, `with_line_index`)
- `metel-frontend/src/pipeline/type_checking/typeinference/mod.rs`
  (`InferContext::default_literal_vars`, `DefaultedSubstitution`)
- `metel-frontend/src/pipeline/type_checking/inference/declarations.rs`
  (`infer_fun_decl`, where the remaining residual most likely lives)

<!-- limit.py:markers:start -->
- [`metel-frontend/src/pipeline/type_checking/inference/declarations.rs::infer_fun_decl`](https://github.com/metel-lang/metel-core/blob/482a47de2a50db592c02804b14155c2310a76bb5/metel-frontend/src/pipeline/type_checking/inference/declarations.rs#L527)
<!-- limit.py:markers:end -->

## Resolution

Partial: the two confirmed, profiled causes above are fixed (metel-core#1232).
The remaining super-linear residual in `inference_ns` needs its own profile
(a large module with empty function bodies, so neither fixed cause
contributes, still shows super-linear scaling) -- `generalize`/
`env_free_vars` is directly ruled out; `infer_fun_decl`'s other per-function
work (param/return-type conversion, `ctx.solve()`'s own bookkeeping,
`ctx.lookup`/`bind_poly` against `poly_env`) is unexamined.
