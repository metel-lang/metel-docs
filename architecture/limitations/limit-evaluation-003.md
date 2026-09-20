---
id: LIMIT-EVALUATION-003
title: "RuntimeRegistry is not fully covered by the resolution-freeze checker"
summary: "Two runtime registry maps are name-keyed by design and sit outside the check that forbids name lookups after resolution."
scope: "architecture/spec/evaluation.md#evaluation"
owner: metel-interpreter
discovered_by: "this session's architecture-spec inventory (direct source + tools/check_no_semantic_name_lookup.py reading), 2026-09-17"
disposition: known
review: "extend tools/check_no_semantic_name_lookup.py's SCAN_FILES to cover RuntimeRegistry, per that tool's own \"Deliberately NOT scanned\" note"
---

## Limitation

`RuntimeRegistry`'s `type_ids` (surface-name→`SymbolId` translation for
sites with no already-threaded id) and `pattern_methods` (structural,
pattern-dispatched method names) remain genuinely name-keyed by design.
`tools/check_no_semantic_name_lookup.py`'s own docstring names
`RuntimeRegistry` as "a separate, adjacent concern with its own
nuances... not yet brought under this check" — the checker documents the
gap itself rather than silently missing it.

## Impact

The resolution-freeze invariant (`arch.resolution.requirement-1`) is not
mechanically verified for these two `RuntimeRegistry` paths the way it is
for the frontend's own identity tables. A regression that reintroduced a
semantic name lookup here would not be caught by the existing CI backstop.

## Affects

- `arch.evaluation.requirement-2`
- `arch.resolution.requirement-1`

## Resolution

None yet. `tools/check_no_semantic_name_lookup.py`'s own "Deliberately NOT
scanned" section names extending `SCAN_FILES` to cover `RuntimeRegistry` as
the straightforward next step.
