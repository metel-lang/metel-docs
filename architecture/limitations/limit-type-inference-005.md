---
id: LIMIT-TYPE-INFERENCE-005
title: "TypeVar identity is a global number, and generator ranges are kept apart by hard-coded offsets"
summary: "A `TypeVar` is just a `u32`, so every generator in a run must start past the others; the frontend does that with unguarded constants (10,000, 1M-5M) scattered over six files."
scope: "architecture/spec/type-inference.md#type-inference"
owner: metel-frontend
discovered_by: "maintainer note on the type var generator; reviewed in metel-frontend/src/pipeline/type_checking/typeinference/mod.rs"
disposition: known
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
- [`metel-frontend/src/pipeline/type_checking/typeinference/mod.rs::TypeVarGenerator`](https://github.com/metel-lang/metel-core/blob/26ffffc1aabe3e17d10726af0d719a8ab79a7869/metel-frontend/src/pipeline/type_checking/typeinference/mod.rs#L51)
- [`metel-frontend/src/pipeline/type_checking/typeinference/mod.rs::split_gen`](https://github.com/metel-lang/metel-core/blob/26ffffc1aabe3e17d10726af0d719a8ab79a7869/metel-frontend/src/pipeline/type_checking/typeinference/mod.rs#L4985)
- `metel-frontend/src/pipeline/type_checking/mod.rs`, `typechecker/construction.rs`, `move_check/mod.rs` (the offsets)

<!-- limit.py:markers:start -->
- [`metel-frontend/src/pipeline/type_checking/construction.rs::construct_generic_body`](https://github.com/metel-lang/metel-core/blob/26ffffc1aabe3e17d10726af0d719a8ab79a7869/metel-frontend/src/pipeline/type_checking/construction.rs#L1059)
- [`metel-frontend/src/pipeline/type_checking/typeinference/mod.rs::TypeVarGenerator`](https://github.com/metel-lang/metel-core/blob/26ffffc1aabe3e17d10726af0d719a8ab79a7869/metel-frontend/src/pipeline/type_checking/typeinference/mod.rs#L50)
- [`metel-frontend/src/pipeline/type_checking/typeinference/mod.rs::split_gen`](https://github.com/metel-lang/metel-core/blob/26ffffc1aabe3e17d10726af0d719a8ab79a7869/metel-frontend/src/pipeline/type_checking/typeinference/mod.rs#L4984)
<!-- limit.py:markers:end -->

## Resolution

None yet. One allocator that owns the whole `TypeVar` space and hands out
checked, disjoint ranges (or namespaces variables per unit so numbers stop
needing to be globally unique) would replace the constants.
