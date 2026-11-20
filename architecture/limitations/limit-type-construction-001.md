---
id: LIMIT-TYPE-CONSTRUCTION-001
title: "Call::callee_id falls back to name dispatch for first-class functions"
summary: "`callee_id` is empty for methods, nested functions and first-class function calls, which fall back to name dispatch."
scope: "architecture/spec/type-construction.md#type-construction"
owner: metel-frontend
discovered_by: "ADR-0041, ADR-0042 (corroborated independently in both)"
disposition: known
review: "revisit if a consumer of a first-class callee identity appears"
---

## Limitation

`Call::callee_id: Option<SymbolId>` is only populated where construction can
determine a concrete callee `SymbolId` — it is `None` for methods,
nested/local functions, and a call through a first-class function value.
ADR-0041 and ADR-0042 both name this directly as "the deferred
first-class-function environment question," not a bug — confirmed still
present in current source (`typed_ast/mod.rs`'s own doc comments on
`callee_id`).

## Impact

This is a real, currently-live exception to the resolution-freeze invariant
(`arch.resolution.requirement-1`) for exactly this call shape: a call
through a first-class function value still resolves by a name-keyed
fallback at the point `callee_id` is `None`, not by identity alone.

## Affects

- `arch.resolution.requirement-1`
- `arch.type-construction.requirement-2`

## Resolution

None yet. ADR-0041 and ADR-0042 call this the deferred first-class-function environment question, and the sealed-accessor work they tie it to has no scheduled consumer (the coherence stage they cited has shipped). The `typed_ast` doc comments on `callee_id` still state it.
