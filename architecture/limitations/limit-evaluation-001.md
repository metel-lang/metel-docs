---
id: LIMIT-EVALUATION-001
title: "Generic function dispatch re-constructs on every call"
summary: "A generic function's body is re-constructed at every call instead of once per instantiation."
scope: "architecture/spec/evaluation.md#evaluation"
owner: metel-interpreter
discovered_by: "ADR-0010; metel-interpreter/docs/evaluator.md, \"Known Limitations\""
disposition: accepted
review: "revisit if performance becomes a concern — a call-site cache keyed on the concrete type tuple is the documented mitigation path (ADR-0010's own \"Future work\" note)"
---

## Limitation

Generic functions and let-polymorphic closures re-run the construction pass
at every call site rather than monomorphizing once per instantiation. This
is correct, not optimal — `evaluator.md` states it is "acceptable for the
tree-walk interpreter," and `architecture.md` already cites ADR-0010's
requirement that a *future compiler backend* must pre-monomorphize instead
of reusing this path. This is a real, currently-live performance
characteristic of the interpreter, not a hypothetical one.

## Impact

A hot generic function pays repeated construction cost on every call. A
future compiled backend cannot reuse the evaluator's runtime
reconstruction approach and must pre-monomorphize instead — already stated
as a hard requirement elsewhere (ADR-0004's compiler path, ADR-0010).

## Affects

- `arch.type-construction.requirement-2`
- `arch.evaluation.requirement-1`

<!-- limit.py:markers:start -->
- [`metel-frontend/src/pipeline/type_checking/construction.rs::construct_generic_body`](https://github.com/metel-lang/metel-core/blob/4155d94ccbc5b1657799f3537515610f3bb139c3/metel-frontend/src/pipeline/type_checking/construction.rs#L1059)
<!-- limit.py:markers:end -->

## Resolution

None yet. ADR-0010's own "Future work" note: if performance becomes a
concern, a call-site cache keyed on the concrete type tuple can be added
without changing the interface.
