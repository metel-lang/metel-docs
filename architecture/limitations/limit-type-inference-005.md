---
id: LIMIT-TYPE-INFERENCE-005
title: "TypeVar identity is a global number, and generator ranges are kept apart by hard-coded offsets"
summary: "A `TypeVar` is just a `u32`, so every generator in a run must start past the others; the frontend does that with unguarded constants (10,000, 1M-5M) scattered over six files."
scope: "architecture/spec/type-inference.md#type-inference"
owner: metel-frontend
discovered_by: "maintainer note on the type var generator; reviewed in metel-frontend/src/pipeline/type_checking/type_engine/mod.rs"
disposition: resolved
review: null
---

## Limitation

`TypeVar(pub u32)` is compared by number: "two vars with the same `u32` are the
*same* variable" (the generator's own doc comment). `TypeVarGenerator` is a bare
counter (`fresh` does an unchecked `+= 1`). So every generator alive in one
type-check run has to start past every variable any other one can produce, or a
"fresh" variable aliases a live one, which the same comment says produces
"self-referential substitutions and infinite recursion in `Substitution::apply`".

Nothing owns that coordination. It is spread over separate call sites as literal
starting values:

| Start | Where | Purpose |
|---|---|---|
| 0 | `check_one_module` (`TypeVarGenerator::new()`), restarted per module | a module's registry and inference variables |
| 10,000 | `StdPrelude::default` | prelude schemes ("registry typically allocates fewer than 100 vars") |
| 1,000,000 | `construct_generic_body` | runtime reconstruction of a generic body, every call |
| 2,000,000 | `check_graph` (two variants) and move-check's `method_gen` | alpha-renamed exported schemes; symbolic aspect methods |
| 3,000,000 | `symbolic_aspect_method_type` | move-check symbolic aspect methods |
| 4,000,000 | move-check's repaired scheme | generic parameters of a repaired scheme |
| 5,000,000 | symbolic impl-method scheme | impl-method schemes |

Nothing enforces the widths. The 10,000 offset rests on an estimate; the
2,000,000 start is shared by two unrelated users; no allocator checks that a
range stays below the next one, and `+= 1` on a `u32` panics on overflow in a
debug build and wraps in release.

`InferContext::split_gen(&self)` is a hazard of the same kind: it returns a
generator that starts at the context's current counter without advancing the
context's own, so a context that keeps allocating after the split reissues the
same ids. ADR-0044 records this exact mistake happening with a disposable
generator (three opaque-returning calls in one scope aliased an unrelated
variable, and the failure looked like a validation bug).

## Impact

No user-visible symptom today; the scheme works while each range stays below the
next. What it costs is safety and change risk: adding a generator means picking
a range by hand, and getting it wrong yields aliased variables and a hang in
`Substitution::apply` rather than an error. Variable numbers also appear in
diagnostics (`?t1`), so they are part of observable output.

Probed, not proved: to see whether a module with more than 10,000 registry
variables reaches the prelude range, I ran a release build over modules of `n`
generic functions (`fun idN<T>(x: T) -> T { x }`, one type parameter each, so
about `n` registry variables), calling the first and the last one. `n = 9,000` and
`n = 10,500` both finished with correct results, so crossing 10,000 produced no
wrong answer, hang or error. That does not show the ranges cannot collide (an
aliasing needs the particular variables to interact), only that this shape does
not. The runs also showed that checking time grows quadratically with the number
of functions (`LIMIT-TYPE-INFERENCE-007`).

## Affects

- `arch.type-inference.requirement-1`
- `metel-frontend/src/pipeline/type_checking/type_engine/type_var_space/mod.rs::TypeVarGenerator`
- `metel-frontend/src/pipeline/type_checking/type_engine/mod.rs::split_gen`
- `metel-frontend/src/pipeline/type_checking/mod.rs`, `typechecker/construction.rs`, `move_check/mod.rs` (the offsets)

## Resolution

Resolved by metel-core#1541. `type_engine/type_var_space` owns the whole `TypeVar` space and
declares four named, disjoint ranges of 2^24 variables each: local (a module's registry and
inference), prelude, construction (`construct_generic_body`) and export (alpha-renamed exported
schemes). The ranges are checked twice. A `const` assertion rejects ranges that overlap, are empty
or are out of order, so editing one into its neighbour is a compile error. `TypeVarGenerator::fresh`
asserts it stays inside its range instead of wrapping or entering the next one. `with_counter`, the
way a literal start was passed, no longer exists; a generator is made with `new()` (local),
`in_range(RANGE)` or `continuing()` (the same range, from the current counter). Instantiating a
scheme reserves past the scheme's variables only when they lie in the generator's own range;
variables of another range are disjoint by construction. The full suite (1,462 integration, 385
unit tests) passes unchanged, and eight new tests cover the range check, the exhaustion panic and
the reservation rule.

Two things the record described are not what the code showed when this was closed. The move-check
starts at 3,000,000 to 5,000,000 listed in the table no longer exist as separate literals (they were
removed when `split_gen` and `continuing` took over, ADR-0044). Two small allocators still start at
0 and are not covered by the ranges: the impl-signature counter (`next_signature_type_var`) and the
throwaway substitution in `resolve_row_field_type`. Both live inside one function's isolated
substitution and never mix with the module's variables, so they are not a collision risk; they are
noted here so a future reader does not take the ranges for the whole story. The `split_gen` hazard
is a different problem and stays tracked as `LIMIT-TYPE-INFERENCE-006`.
