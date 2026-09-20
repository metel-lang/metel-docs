---
id: LIMIT-NAME-RESOLUTION-001
title: "std::core had no physical module file (resolved by ADR-0039)"
summary: "`std::core` had no physical module file; resolved by ADR-0039."
scope: "architecture/spec/name-resolution.md#name-resolution"
owner: metel-frontend
discovered_by: "ADR-0027; found stale and resolved during ADR lifecycle triage, 2026-09-17"
disposition: resolved
review: null
---

## Limitation

As of ADR-0027, `std::core` was a virtual module — no physical `.mln` file,
seeded from a hard-coded injection list, with a new core type requiring
three separate manual registration steps (`build_registry`, `pub_surface`
injection in `name_resolver.rs`, `StdPrelude`). This record originally
cited ADR-0027 directly without checking whether it was still current — it
wasn't: ADR-0027's own frontmatter already says `supersedes: adr-0027`
pointing the other way (`adr-0039` supersedes it), caught during the
`#1158` lifecycle triage pass, not during this record's original filing.

## Impact

At the time, tooling enumerating module files would not find `std::core`,
and adding a core type meant touching three separate registration points
rather than one declarative source file.

## Affects

- `arch.name-resolution.requirement-1`
- `arch.parsing.requirement-2`

## Resolution

Resolved by ADR-0039 (`Native Host Bindings and std::core as a Real
Embedded Module`, 2026-06-11). Verified directly against current source,
not just the ADR text: real physical files exist at
`metel-frontend/stdlib/*.mtl` (`core.mtl`, `process.mtl`, `fs.mtl`,
`env.mtl`); `build.rs` scans `stdlib/**/*.mtl` and embeds them into the
binary via `stdlib.rs`'s generated `EMBEDDED_STDLIB` table, which
`module_paths()` enumerates directly. `build_registry` and `pub_surface`
injection no longer exist anywhere in current source (`grep` returns
nothing) — native items now declare host bindings via `native(@...)` in
the `.mtl` source itself, one declarative site instead of three.
