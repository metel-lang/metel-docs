---
id: GAP-MODULES-002
title: "A directory cannot be a module on its own: there is no `mod.mtl` equivalent"
summary: "There is no `mod.rs` equivalent: a directory is not a module by itself, so `name/mod.mtl` has no meaning; the facade is a `name.mtl` file beside the `name/` directory."
scope: "reference/spec/modules.md#spec.modules.file-to-module-mapping.legality-1"
owner: language
discovered_by: "maintainer note during the Atlas limitation review"
disposition: accepted
review: "revisit if the `name.mtl` facade proves awkward for large module trees"
---

## Gap

Rust lets a directory be its own module through `mod.rs` (`util/mod.rs`
declares `util`). Metel has no counterpart. `::` maps directly to `/`, so a
module path names exactly one file, and `import root::util::answer;` looks for
`util.mtl`, never for `util/mod.mtl`. Reproduced against current `develop`:

```metel
// main.mtl
import root::util::answer;
fun main() { assert(answer() == 42); }
```

with the module in `util/mod.mtl`:

```
[P0001] parse error: cannot find module file for `util::answer`
```

The same program passes with the module in `util.mtl`. A directory module that
needs a public facade is written as `name.mtl` alongside the `name/` directory
(`parser.mtl` re-exporting from `parser/ast.mtl`, `parser/lexer.mtl`); the two
are distinct paths and coexist. The spec states this directly: there is no
`name/mod.mtl` convention.

## Impact

A module cannot keep its root file inside its own directory. Moving or renaming
a module means moving a file and a directory that sit side by side, and the
directory cannot be relocated as a self-contained unit the way a `mod.rs`
directory can. Programs that group submodules under a directory must add the
facade file next to it.

## Affects

- `spec.modules.file-to-module-mapping.legality-1`
- `RFC-0030`

## Resolution

Accepted as designed: RFC-0030 (module system redesign, implemented) chose
"`::` maps to `/`, no special directory module file", and the spec records that
as Legality Rule `file-to-module-mapping.legality-1`, covered by a fixture.
Reopen if directory-local module roots are wanted; that would be a new RFC.
