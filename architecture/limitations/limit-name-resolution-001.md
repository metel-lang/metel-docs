---
id: LIMIT-NAME-RESOLUTION-001
title: "std::core has no physical module file"
scope: "architecture/spec/name-resolution.md#name-resolution"
owner: metel-frontend
discovered_by: "ADR-0027"
disposition: known
review: null
---

## Limitation

`std::core` is a virtual module — it has no physical `.mln` file, so it
cannot be listed or enumerated the way a real module can. This is stated
directly in ADR-0027 as "a known limitation documented in the spec."

## Impact

Tooling that enumerates a directory of module files (an IDE's module
browser, a doc generator) will not find `std::core`. Adding a new core type
also requires three separate manual registration steps (`build_registry`,
`pub_surface` injection in `name_resolver.rs`, `StdPrelude` if it has
associated functions) rather than one declarative source file a contributor
could just add.

## Affects

- `arch.name-resolution.requirement-1` (the canonical `SymbolId` table,
  which pre-seeds `std::core`'s builtin ids)
- `arch.parsing.requirement-2` (`SourceProvider`/`EmbeddedStdlibProvider`,
  which serves `std::core`'s source from a binary-embedded string, not a
  file)

## Resolution

None yet.
