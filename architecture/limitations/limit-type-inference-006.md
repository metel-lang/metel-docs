---
id: LIMIT-TYPE-INFERENCE-006
title: "Type checking is sequential by construction: one shared generator, one export generator, Rc state"
summary: "Inference threads one `&mut` generator through every pass and one export generator through every module, and its context uses `Rc`, so modules cannot be checked in parallel."
scope: "architecture/spec/type-inference.md#type-inference"
owner: metel-frontend
discovered_by: "maintainer note on the type var generator; reviewed in metel-frontend/src/pipeline/type_checking/mod.rs and typeinference/mod.rs"
disposition: known
review: null
---

## Limitation

Several things make the type checker impossible to run in parallel, independent
of any decision to do so:

- **A shared mutable generator.** Registry building, inference and construction
  each take `&mut TypeVarGenerator` (about twenty `registry.rs` functions do), and
  `split_gen` hands the next pass a generator that continues from the last. The
  order of allocation is therefore fixed by the order the passes run.
- **One export generator across modules.** Each module's own generator restarts
  near 0 (`check_one_module`), which would let modules be inferred independently,
  but exported schemes are alpha-renamed through a single
  `export_gen: TypeVarGenerator` (starting at 2,000,000) that `check_graph`
  threads through every module in topological order, so their numbering depends on
  that order.
- **`Rc`-based state.** The inference context shares `Rc<HashMap<..>>` (symbols,
  scopes) and `Rc<Substitution>`, which are not `Send`, so a context cannot be
  moved to another thread.
- **Variable numbers are output.** `TypeVar` prints as `?tN` and reaches user
  diagnostics (for example "cannot unify ((?1, ?1), (?1, ?1)) with (i64, i64)"),
  so nondeterministic allocation would make error messages nondeterministic.

## Impact

Type checking cannot use more than one core. Parallelising it would need, at
least: per-unit variable ranges so numbering is independent of scheduling,
`Arc` (or owned, per-thread) replacements for the `Rc` state, and a way to
allocate exported scheme variables without a single sequential generator. It
also collides with the ADR-0054 statement that identities are the same
"regardless of ... parallelism", which the id allocators already do not meet
(`LIMIT-NAME-RESOLUTION-002`).

This is read from the code and the requirement to keep diagnostics stable; no
attempt at parallel checking was made.

## Affects

- `arch.type-inference.requirement-1`
- `LIMIT-TYPE-INFERENCE-005`
- `metel-frontend/src/pipeline/type_checking/mod.rs` (`check_graph`, `export_gen`)
- `metel-frontend/src/pipeline/type_checking/typeinference/mod.rs` (`InferContext`, `TypeVarGenerator`)

<!-- limit.py:markers:start -->
- [`metel-frontend/src/pipeline/type_checking/mod.rs::check_graph`](https://github.com/metel-lang/metel-core/blob/5586a5cdb8bda4fa8f25a51700e048c33fe28f73/metel-frontend/src/pipeline/type_checking/mod.rs#L354)
- [`metel-frontend/src/pipeline/type_checking/typeinference/mod.rs::TypeVarGenerator`](https://github.com/metel-lang/metel-core/blob/5586a5cdb8bda4fa8f25a51700e048c33fe28f73/metel-frontend/src/pipeline/type_checking/typeinference/mod.rs#L50)
<!-- limit.py:markers:end -->

## Resolution

None yet. There is no plan or issue for parallel type checking.
