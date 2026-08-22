---
id: rfc-0030
title: "Module System Redesign"
date: '2026-05-28'
coverage:
  "1": { spec: "spec.modules.imports.legality-4" }
  "2": { spec: "spec.modules.re-exports.legality-2" }
  "3": { spec: "spec.modules.file-to-module-mapping.legality-1" }
  "4": { spec: "spec.modules.visibility.legality-1" }
  "5": { spec: "spec.modules.file-header-ordering.legality-1" }
  "6": { spec: "spec.modules.paths.legality-1" }
  "7": { spec: "spec.modules.import-conflicts.legality-4" }
  "8": { spec: "spec.modules.module-graph-loading.legality-2" }
  "9": { spec: "spec.modules.module-graph-loading.legality-2" }
  "10": { spec: "spec.modules.single-file-compatibility.legality-1" }
  "11": { spec: "spec.modules.std-core-auto-import.legality-1" }
  "12": { spec: "spec.modules.removed-module-keywords.legality-1" }
---

## Summary

Replaces RFC-0009 and RFC-0029 with a revised module system that addresses the ergonomic shortcomings of the Rust-inspired design. The core problems with the previous design were: the required two-step `mod` + `use` pattern for every imported module, the `name/mod.mln` directory module convention, and `pub use` as the re-export mechanism. This RFC resolves all three with minimal added complexity.

**Supersedes:** RFC-0009 (Module System), RFC-0029 (Module System — Gaps and Clarifications)  
**Target:** v0.5.0

---
:
## Motivation

The RFC-0009 design required two separate declarations to use a module:

```metel
mod parser;               // declares the module exists (loads the file)
use parser::{Ast, Token}; // brings names into scope
```

Both steps are mandatory. Skipping `mod` means the file is never loaded. Skipping `use` means you can only access names via fully-qualified paths. This double-declaration pattern was the primary ergonomic complaint.

Additionally, `pub use` reads as a mechanism (`pub` + `use`) rather than an intent (`export`), and `name/mod.mln` as the directory module entry point directly imports a Rust convention that has no other motivation.

---

## Design

### `import` replaces both `mod` and `use`

A single `import` declaration both loads the module file and brings names into the current scope:

```metel
import parser::{Ast, Token};       // loads parser.mln, brings Ast and Token into scope
import std::math;                  // loads std/math, brings math into scope as a module handle
import root::lexer::Token as Tok;  // absolute path with alias
import parser::*;                  // glob import — all public names from parser.mln
```

There is no `mod` keyword and no `use` keyword for module imports. `import` is the only form.

Import forms:

| Form | Effect |
|---|---|
| `import path::Name;` | imports `Name` |
| `import path::Name as Alias;` | imports `Name` under `Alias` |
| `import path::{A, B, C};` | imports multiple names from one path |
| `import path::{A as X, B};` | imports with per-item aliases |
| `import path::*;` | imports all public names from the module |
| `import path::module;` | imports `module` as a module handle; `module::item` is then valid |

### `export` replaces `pub use`

Re-exporting names from submodules uses an explicit `export` declaration:

```metel
// parser.mln — facade module for the parser namespace
export ast::Ast;
export lexer::{Token, Span};
export ast::ParseError as Error;
```

`export` and `import` share the same path and tree syntax. `export` re-exports into the current module's public API; the exported names are then accessible as if defined directly in the re-exporting module.

`pub` on declarations continues to mark individual items as externally accessible. `pub` and `export` serve different roles:

| Keyword | Purpose |
|---|---|
| `pub` | Marks a declaration in this file as externally accessible |
| `export path::Name;` | Re-exports a name from a submodule into this module's public API |

### File-to-module mapping

`::` maps directly to `/` in the filesystem. There is no special directory module file.

| Import | File resolved |
|---|---|
| `import parser::Ast;` | `parser.mln` |
| `import parser::ast::Ast;` | `parser/ast.mln` |
| `import root::a::b::c::T;` | `a/b/c.mln` relative to the root file |

A directory module with a public facade is expressed by placing `name.mln` alongside the `name/` directory. The two coexist without ambiguity — they are different paths:

```
src/
  main.mln            ← import parser::Ast; import parser::lexer::Token;
  parser.mln          ← export ast::Ast; export lexer::Token;
  parser/
    ast.mln           ← pub struct Ast { ... }
    lexer.mln         ← pub struct Token { ... }
```

`parser.mln` is the facade. Files in `parser/` form the namespace. There is no `parser/mod.mln` convention.

### Module visibility

Modules do not have their own visibility annotation. Module-level access control is handled entirely by `pub` on individual items. If an item is `pub`, its full path is accessible to any importer. If it is private, it is not.

To hide the internal file structure from importers, a parent module uses `export` to expose only the names it chooses:

```metel
// parser.mln
export ast::Ast;          // Ast is accessible as root::parser::Ast
export lexer::Token;      // Token is accessible as root::parser::Token
                          // parser/ast.mln and parser/lexer.mln paths remain accessible
                          // but callers are expected to use the facade
```

There is no equivalent of `pub mod` / private mod from RFC-0009. This simplification is intentional for v0.5.0. Path-level module privacy is deferred.

### Paths

Path roots are unchanged from RFC-0029:

| Root | Meaning |
|---|---|
| `root::` | The selected root module for the current program |
| `std::` | The bundled standard library root |
| `self::` | The current module |
| `super::` | The parent module; invalid from the root module |
| imported module handle | A module brought into scope by `import path::module;` |

Fully-qualified paths are valid anywhere a name is expected without a preceding `import`:

```metel
let p: root::parser::Ast = root::parser::Ast::new();
```

`import` is a local binding convenience, not the only access mechanism.

### File header ordering

```
(import | export)* declaration*
```

`import` and `export` declarations may appear in any order relative to each other, but all must precede any other declarations. `import` and `export` are not valid inside blocks.

### Import conflicts

Explicit import conflicts (two `import` statements binding the same local name) are a compile error at the second import.

Glob imports use a softer rule:
- Local declarations beat glob imports.
- Explicit imports beat glob imports.
- Two glob imports may name the same item without an immediate error; using that name is an error only if the reference is ambiguous.

### Circular imports

Circular imports are a compile error. The error message includes the full import chain.

### Module graph loading

The module graph is built from `import` declarations. The loader:

1. Parses the root file.
2. Collects all `import` declarations; resolves each to a file path via `::` → `/` mapping.
3. Recursively loads each referenced file, detecting cycles.
4. Only files reachable via at least one `import` declaration are loaded.

`export` declarations are processed after the graph is fully loaded. They do not affect which files are loaded.

### std::core auto-import

Unchanged from RFC-0029: `std::core` is auto-imported into every file as if `import std::core::*;` appeared implicitly. The auto-import is lowest priority; any explicit `import` beats it. A local declaration shadows the auto-import in its declaring module only.

### Single-file compatibility

A `.mln` file with no `import` or `export` declarations is a complete program. Fully preserved.

---
:
## Grammar changes

```
file         ::= header-decl* declaration*
header-decl  ::= import-decl | export-decl
import-decl  ::= 'import' import-path ';'
export-decl  ::= 'export' import-path ';'
import-path  ::= path-root '::' import-tree
               | path-root
path-root    ::= 'root' | 'std' | 'self' | 'super' | identifier
import-tree  ::= import-item
               | '{' import-item (',' import-item)* '}'
               | '*'
               | identifier '::' import-tree
import-item  ::= identifier ('as' identifier)?
pub-ann      ::= 'pub'   -- unchanged; valid on struct, enum, fun, let, mut, linear struct, linear enum, aspect
```

`mod`, `use`, and `pub use` are removed from the grammar.

---

## Changes from RFC-0009 / RFC-0029

| RFC-0009/0029 | RFC-0030 |
|---|---|
| `mod name;` declares a submodule | removed — `import` builds the module graph |
| `pub mod name;` makes a submodule public | removed — no module-level visibility annotation |
| `use path::Name;` brings a name into scope | `import path::Name;` |
| `pub use path::Name;` re-exports a name | `export path::Name;` |
| `name/mod.mln` as directory module entry point | removed — `name.mln` alongside `name/` directory |
| File header: `mod* use* declaration*` | `(import\|export)* declaration*` |
| Glob import `use path::*;` | `import path::*;` — same conflict rules |
| `use path::Name as Alias;` | `import path::Name as Alias;` |
| `super::`, `self::` path roots | unchanged |
| `root::` path root | unchanged |
| Circular import is a compile error | unchanged |
| `pub` on declarations | unchanged |
| `std::core` auto-import | unchanged |
| Single-file compatibility | unchanged |

---
:
## Open Questions

None — all questions from RFC-0009 and RFC-0029 are either resolved by this RFC or unchanged.

---

## Decision

**Outcome:** Accepted  
**Target:** v0.5.0

The Rust-inspired `mod` + `use` two-step was the primary ergonomic shortcoming of RFC-0009. Collapsing both into `import` eliminates the pattern without adding complexity elsewhere. `export` as an explicit re-export keyword is cleaner than `pub use`. Dropping `name/mod.mln` removes a Rust convention with no independent motivation.

The removal of module-level visibility (`pub mod`) is the most significant simplification. Item-level `pub` is sufficient for v0.5.0; path-level module privacy can be added later if the need arises in practice.

## Coverage Checklist (added 2026-08-19, not part of the original RFC)

Retroactive breakdown of this RFC's distinct, fixture-testable normative claims
(expanded 2026-08-19: added item 12, missed in the original pass),
as headed sections for citation purposes only. The document above is
unchanged and remains the historical record. Deliberately excludes claims that
aren't independently observable from a program's behavior -- implementation
strategy, design rationale, or internal architecture discussion belongs in the
RFC's own prose, not here.

### 1. Import both loads a module and introduces selected names

An `import` declaration loads the referenced module and brings its selected public
names into the importing module's scope. Named, grouped, aliased, glob, and
module-handle imports are accepted forms.

### 2. Export re-exports names through a module's public API

An `export` declaration makes a name from a submodule available through the
current module, including under an alias. Importers may use that re-export as if
the name were declared directly by the facade module.

### 3. Module paths map directly to .mtl source paths

`::` path segments resolve to directories and `.mtl` files, so `a::b::Thing`
resolves through `a/b.mtl`. A facade `name.mtl` may coexist with `name/`; no
special `name/mod.mtl` entry file is used.

### 4. Only public items are accessible across a module boundary

Declarations are module-private unless marked `public`; modules themselves have
no separate visibility modifier. An import or qualified reference to a private
item is rejected with the visibility error `T0009`.

### 5. Header imports and exports precede declarations

At file scope, `import` and `export` declarations may be interleaved but must
come before ordinary declarations. They are not valid inside blocks.

### 6. Module roots and qualified paths resolve in source code

`root::`, `std::`, `self::`, and `super::` are supported path roots in their
valid contexts, and fully qualified paths may be used wherever a name is expected.
`super::` from the root module is rejected.

### 7. Import conflicts follow explicit and glob priority rules

Two explicit imports of the same local name are an immediate `T0011` error.
Explicit imports and local declarations win over glob imports, while a name from
two user glob imports is rejected only if it is used ambiguously.

### 8. Circular and missing imports are load errors

An import cycle is rejected with its dependency chain, and an import whose module
file is absent is an error rather than a silently ignored dependency.

### 9. A bare export also loads its referenced module

An `export path::Name;` with no corresponding `import` of `path` still resolves
and loads `path`'s module file into the graph. (Resolved 2026-08-19,
metel-core#749/#664: this RFC's original text claimed the opposite --
"`export` declarations are processed after the graph is fully loaded. They do
not affect which files are loaded" -- but that design was found to be a real
bug, not a stated intent worth keeping: without loading the export's target,
a name reachable only through a re-export resolved nowhere in the compiled
program, so the re-export itself was permanently broken. Fixed deliberately in
metel-core#664 -- `export` and `import` now build the module graph together.
`docs/public/reference/spec/modules.md`'s "Module Graph Loading" section,
which repeated this RFC's original claim, is corrected to match.)

### 10. Single-file programs remain valid

A `.mtl` program with no `import` or `export` declarations runs as a complete
single-module program.

### 11. std::core names are available in every module

Every module receives the `std::core` surface at the lowest import-priority tier.
An explicit import or a local declaration takes precedence over an auto-imported
name.

### 12. Legacy `mod` and `use` declarations are rejected

The former module declarations `mod`, `use`, and `pub use` are not valid Metel
syntax; imports and re-exports use `import` and `export` instead.
