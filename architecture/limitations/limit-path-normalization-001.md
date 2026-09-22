---
id: LIMIT-PATH-NORMALIZATION-001
title: "`root::`/`super::` are rejected in expression position when the target is declared directly in that module"
summary: "`root::name` and `super::name` work through a submodule path but are rejected in expression position when `name` is declared directly in the root or parent module."
scope: "architecture/spec/path-normalization.md#path-normalization"
owner: metel-frontend
discovered_by: "metel-core#1221"
disposition: known
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
- `metel-frontend/src/path_normalizer.rs`

<!-- limit.py:markers:start -->
- [`metel-frontend/src/path_normalizer.rs::try_resolve_path`](https://github.com/metel-lang/metel-core/blob/4155d94ccbc5b1657799f3537515610f3bb139c3/metel-frontend/src/path_normalizer.rs#L404)
<!-- limit.py:markers:end -->

## Resolution

None yet; tracked as `metel-core#1221`.
