---
id: LIMIT-PATH-NORMALIZATION-001
title: "`root::`/`super::` are rejected in expression position when the target is declared directly in that module"
summary: "`root::name` and `super::name` work through a submodule path but are rejected in expression position when `name` is declared directly in the root or parent module."
scope: "architecture/spec/path-normalization.md#path-normalization"
owner: metel-frontend
discovered_by: "metel-core#1221"
disposition: resolved
review: null
---

## Limitation

`reference/spec/modules.md` lists `root` and `super` as path roots and says a
fully-qualified path is valid anywhere a name is expected. Reproduced against
current `develop`: `root::helper()`, called from a submodule where `helper` is
declared directly at the root, fails with `T0003 undefined name
`root::helper``. The same root path through a further submodule
(`root::parser::make`) resolves correctly, and `self::f()` also works. The
symptom is consistent with path normalization handling a multi-segment root
path but not the one-segment case where the root module is also the
declaring module.

## Impact

A program cannot call a root- or parent-module item by its fully-qualified
path from a submodule unless it goes through an intermediate module segment;
the spec gives no such exception. The workaround is an explicit `import`.

## Affects

- `spec.modules.paths.legality-1`
- `metel-frontend/src/pipeline/path_normalization/mod.rs`

## Resolution

Resolved by metel-core#1743. The program this record reproduced is a circular module dependency: the root imports the submodule, and the submodule names `root::helper`, declared in the root. Cycles are a compile error (`GAP-MODULES-001`), and it is now reported as one (`P0001`, at the path) instead of `T0003` undefined name. A `root::` or `super::` path to an item declared directly in the root or parent module resolves wherever the module graph is acyclic. The `// limit:` marker in `path_normalization/mod.rs` is removed in a follow-up core change.
