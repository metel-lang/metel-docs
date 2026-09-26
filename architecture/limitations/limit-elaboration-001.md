---
id: LIMIT-ELABORATION-001
title: "ElaboratedModuleGraph's field is fully public, unlike NormalizedModuleGraph's"
summary: "`ElaboratedModuleGraph`'s field is public, so code outside the frontend can build one without running elaboration, unlike `NormalizedModuleGraph`."
scope: "architecture/spec/elaboration.md#elaboration"
owner: metel-frontend
discovered_by: "this session's architecture-spec inventory (direct source reading), 2026-09-17"
disposition: known
review: null
---

## Limitation

`ElaboratedModuleGraph(pub TypedModuleGraph)`'s inner field is fully `pub`,
so code outside `metel-frontend` can construct one directly without having
run `elaborate` — unlike `NormalizedModuleGraph` (`arch.path-normalization.requirement-1`),
whose `pub(crate)` field blocks exactly that from outside the crate. The two
"proof this pass has run" wrapper types are not actually symmetric in what
they enforce, despite both existing for the same stated purpose.

## Impact

Nothing in the current codebase exploits this, but nothing prevents a
future caller — inside `metel-interpreter`, or any external crate depending
on `metel-frontend` — from synthesizing an `ElaboratedModuleGraph` whose
`MethodDispatch` fields were never actually resolved, defeating the
"proof" the type's own doc comment claims it carries.

## Affects

- `arch.elaboration.requirement-1`
- `arch.path-normalization.requirement-1`

<!-- limit.py:markers:start -->
- [`metel-frontend/src/pipeline/elaboration/mod.rs::ElaboratedModuleGraph`](https://github.com/metel-lang/metel-core/blob/5586a5cdb8bda4fa8f25a51700e048c33fe28f73/metel-frontend/src/pipeline/elaboration/mod.rs#L35)
<!-- limit.py:markers:end -->

## Resolution

None yet. The straightforward fix (narrow the field to `pub(crate)`,
matching `NormalizedModuleGraph`) has not been evaluated for what it would
break in existing callers.
