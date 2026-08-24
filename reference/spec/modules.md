# Modules

## Files and Modules

> **Availability:** Since v0.5.0.

Every `.mtl` source file is a module. There is no `mod` declaration — the module graph is built entirely from `import` declarations.

The root file passed to the toolchain is the root module:

```bash
metel src/main.mtl
```

In that example, `root::` refers to `src/main.mtl`.

## File-to-Module Mapping

`::` maps directly to `/` in the filesystem. There is no special directory module file.

| Import | File resolved |
|---|---|
| `import parser::Ast;` | `parser.mtl` |
| `import parser::ast::Ast;` | `parser/ast.mtl` |
| `import root::a::b::c::T;` | `a/b/c.mtl` relative to the root file |

A directory module with a public facade is expressed by placing `name.mtl` alongside the `name/` directory. The two coexist without ambiguity — they are different paths:

```
src/
  main.mtl            ← import parser::Ast; import parser::lexer::Token;
  parser.mtl          ← export ast::Ast; export lexer::Token;
  parser/
    ast.mtl           ← public struct Ast { ... }
    lexer.mtl         ← public struct Token { ... }
```

`parser.mtl` is the facade. Files in `parser/` form the namespace. There is no `name/mod.mtl` convention.

<details>
<summary>Formal rules</summary>

##### Legality Rule {#spec.modules.file-to-module-mapping.legality-1}

Each non-prelude module path maps directly to its `.mtl` file path. A facade file and
the same-named directory are distinct paths; `name/mod.mtl` has no special meaning.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0030](../../rfcs/4-implemented/rfc-0030-module-system-redesign.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [main.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/module_loading/facade_module_alongside_directory/main.mtl)_</span>
<!-- rfc.py:fixtures:end -->

</details>

## File Header Ordering

At file scope, `import` and `export` declarations must precede all other declarations:

```
(import | export)* declaration*
```

`import` and `export` are not valid inside blocks.

<details>
<summary>Formal rules</summary>

##### Legality Rule {#spec.modules.file-header-ordering.legality-1}

At file scope, imports and exports may be interleaved but must precede ordinary
declarations; neither declaration form is valid in a block.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0030](../../rfcs/4-implemented/rfc-0030-module-system-redesign.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [rfc0030_import_after_declaration.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/parsing/rfc0030_import_after_declaration.mtl)_</span>
<!-- rfc.py:fixtures:end -->

</details>

## Paths

Paths use `::` separators.

Path roots are:

| Root | Meaning |
|---|---|
| `root::` | The selected root module for the current program |
| `std::` | The bundled standard library root; `std::core` is always available |
| `self::` | The current module |
| `super::` | The parent module; invalid from the root module |
| imported module handle | A module brought into scope by `import path::module;` |

### Reserved namespaces

The `std` top-level namespace is reserved for the standard library. User module
paths may not begin with `std` — a module file at `std.mtl` or anywhere under
`std/` in the project tree is a compile error:

```
error: module path `std::…` is reserved for the standard library
```

`std` is also a reserved keyword and cannot appear as an identifier. Both
restrictions are consistent: `std` is not a valid name for user code at any
level.

No other top-level names are currently reserved.

Fully-qualified paths are valid anywhere a name is expected:

```metel
// src/main.mtl
import root::parser::Token;

fun main() -> i64 {
    let token: root::parser::Token = root::parser::Token { value = 42 };
    return token.value;
}

// src/parser.mtl
public struct Token {
    public value: i64,
}
```

<details>
<summary>Formal rules</summary>

##### Legality Rule {#spec.modules.paths.legality-1}

`root`, `std`, `self`, and `super` resolve as path roots in their valid module
contexts. A qualified path is valid wherever its resolved name is valid; `super` is
invalid in the root module.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0030](../../rfcs/4-implemented/rfc-0030-module-system-redesign.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [main.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/module_loading/accepts_root_self_super_std_and_child_roots_in_non_root_modules/main.mtl)_</span>
<!-- rfc.py:fixtures:end -->

</details>

## Imports

`import` loads the referenced module file and declares which names from it are in scope for the current module:

```metel
// src/main.mtl
import parser::*;
import root::lexer::Token as Tok;

fun main() -> i64 {
    let ast = Ast { token = Token { value = 1 } };
    let tok: Tok = dbg(Tok { value = 2 });
    return ast.token.value + tok.value + parse(ast.token);
}

// src/parser.mtl
export ast::Ast;
export ast::parse;
export lexer::Token;

// src/parser/ast.mtl
import super::lexer::Token;
public struct Ast { public token: Token }
public fun parse(token: Token) -> i64 { token.value }

// src/lexer.mtl
public struct Token { public value: i64 }
```

`import parser::*;` brings in `Ast`, `parse`, and the re-exported `Token` all at
once; `Tok` — an alias for that same `Token`, reached via a second,
`root`-qualified import — works as both a type annotation and a struct
constructor, and unifies with the un-aliased name since both name the same
declaration.

Import forms:

| Form | Effect |
|---|---|
| `import path::Name;` | imports `Name` |
| `import path::Name as Alias;` | imports `Name` under `Alias` |
| `import path::{A, B, C};` | imports multiple names from one path |
| `import path::{A as X, B};` | imports with per-item aliases |
| `import path::*;` | imports all public names from the module |
| `import path::module;` | imports `module` as a module handle; `module::item` is then valid |

<details>
<summary>Formal rules</summary>

##### Legality Rule {#spec.modules.imports.legality-1}

A module may use its own declarations and public declarations brought into scope by an
import. Loading another module alone does not make that module's names available.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0031](../../rfcs/4-implemented/rfc-0031-topological-typechecker.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [main.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/module_semantics/explicit_named_import_function_call/main.mtl)_</span>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.modules.imports.legality-2}

An aliased import binds only its alias locally. The alias may be used wherever the
imported declaration's kind permits, including as a value, type, or constructor.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0031](../../rfcs/4-implemented/rfc-0031-topological-typechecker.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [main.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/module_semantics/alias_import_original_name_not_in_scope/main.mtl), [main.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/module_semantics/alias_import_usable_as_type_annotation_and_constructor/main.mtl)_</span>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.modules.imports.legality-3}

A qualified use resolves through an imported binding; an unresolved qualified path is a
name-resolution error and is not retried as an arbitrary bare name.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0031](../../rfcs/4-implemented/rfc-0031-topological-typechecker.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [main.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/module_semantics/qualified_call_normalized_to_bare_name/main.mtl)_</span>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.modules.imports.legality-4}

An import loads its referenced module and introduces the selected public names or module
handle into the importing module's scope.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0030](../../rfcs/4-implemented/rfc-0030-module-system-redesign.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [main.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/module_semantics/explicit_named_import_function_call/main.mtl)_</span>
<!-- rfc.py:fixtures:end -->

</details>

## Re-exports

`export` re-exports names from submodules into the current module's public API:

<!-- doc-example: skip reason="syntax illustration only -- ast/lexer/ParseError aren't real files here" -->
```metel
// parser.mtl — facade module for the parser namespace
export ast::Ast;
export lexer::{Token, Span};
export ast::ParseError as Error;

fun main() -> i64 {
    return 0;
}
```

`export` and `import` share the same path and tree syntax. Re-exported names are indistinguishable from names defined directly in the re-exporting module.

<details>
<summary>Formal rules</summary>

##### Legality Rule {#spec.modules.re-exports.legality-1}

A re-export may expose only a declaration that is public in its source module. Re-exporting
a private source declaration is a `T0009` visibility error.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0031](../../rfcs/4-implemented/rfc-0031-topological-typechecker.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [main.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/module_semantics/rfc0031_reexport_private_item_is_t0009/main.mtl)_</span>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.modules.re-exports.legality-2}

A re-export makes a public source declaration available through the current module's
public API, including under an alias; importers may use it as a declaration of the facade.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0030](../../rfcs/4-implemented/rfc-0030-module-system-redesign.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [main.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/module_semantics/facade_re_exports_item_and_consumer_can_use_it/main.mtl)_</span>
<!-- rfc.py:fixtures:end -->

</details>

`public` and `export` serve different roles:

| Keyword | Purpose |
|---|---|
| `public` | Marks a declaration in this file as externally accessible |
| `export path::Name;` | Re-exports a name from a submodule into this module's public API |

Since v0.12.1 (metel-core#664), a bare `export path::Name;` also loads `path`'s module file, exactly as an `import` of the same path would — otherwise a name reachable *only* through a re-export, with no `import` anywhere pulling its module in directly, would never actually resolve: it would exist nowhere in the compiled program for the re-export to point at. `export` and `import` therefore build the module graph together; an `export` is not merely a post-load renaming step over files `import` already loaded.

## std::core Auto-Import

> **Availability:** Since v0.6.1.

Every module automatically has `std::core` glob-imported at the lowest priority tier. This means `Perhaps`, `Result`, `Display`, `Iterable`, `From`, and all built-in functions are available in every module without any explicit import statement.

```metel
// No import needed — Perhaps and Result are always in scope
fun maybe_parse(s: String) -> Perhaps<i64> {
    if (s == "1") { return Some { value = 1 }; }
    return None;
}

fun main() -> i64 {
    match maybe_parse("1") {
        Some { value } => value,
        None => 0,
    }
}
```

You can still write `import std::core::Perhaps;` or `import std::core::*;` explicitly — the result is the same. If a local declaration or explicit import shadows a `std::core` name, the local binding wins silently.

`std::core` is a **virtual module** — it has no physical `.mtl` file and cannot be listed or enumerated. Its contents are seeded by the runtime.

<details>
<summary>Formal rules</summary>

##### Legality Rule {#spec.modules.std-core-auto-import.legality-1}

Every module has the `std::core` names available without an import; the same names may also
be named through their explicit `std::core::` paths.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0030](../../rfcs/4-implemented/rfc-0030-module-system-redesign.md), [rfc-0057](../../rfcs/4-implemented/rfc-0057-stdlib-layering-and-host-modules.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [int_08_std_core_paths.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/integration/int_08_std_core_paths.mtl), [main.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/module_semantics/std_core_builtins_available_in_each_module_without_import/main.mtl)_</span>
<!-- rfc.py:fixtures:end -->

</details>

## Import Conflicts

Two explicit imports that bind the same local name in the same module are a compile-time error at the second import.

Glob imports use a priority tier system:

| Tier | Source | Priority |
|------|--------|----------|
| `Std` | Auto-inserted by the runtime (e.g. `std::core`) | Lowest |
| `User` | Explicit `import path::*` in source | Higher |

Conflict rules:
- Local declarations beat all glob imports.
- Explicit imports beat all glob imports.
- A `User` glob silently wins over a `Std` glob for the same name (no error).
- Two `User` globs exporting the same name are a conflict error (T0011) only if that name is actually referenced.

<details>
<summary>Formal rules</summary>

##### Legality Rule {#spec.modules.import-conflicts.legality-1}

Two explicit imports that bind the same local name are rejected with `T0011` at import
time.

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [main.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/module_semantics/two_explicit_imports_same_local_name_is_t0011/main.mtl)_</span>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.modules.import-conflicts.legality-2}

A collision between two user glob imports is rejected with `T0011` only when code refers
to the ambiguous name.

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [main.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/module_semantics/two_glob_imports_same_name_is_t0011/main.mtl)_</span>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.modules.import-conflicts.legality-3}

An explicit import takes precedence over a glob-imported binding of the same name.

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [main.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/module_semantics/explicit_import_wins_over_glob_same_name/main.mtl)_</span>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.modules.import-conflicts.legality-4}

Import conflicts follow their binding kind: duplicate explicit imports fail immediately,
ambiguous user-glob names fail when referenced, and an explicit import disambiguates a
glob-provided name.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0030](../../rfcs/4-implemented/rfc-0030-module-system-redesign.md), [rfc-0031](../../rfcs/4-implemented/rfc-0031-topological-typechecker.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [main.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/module_semantics/explicit_import_wins_over_glob_same_name/main.mtl), [main.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/module_semantics/two_explicit_imports_same_local_name_is_t0011/main.mtl), [main.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/module_semantics/two_glob_imports_same_name_is_t0011/main.mtl)_</span>
<!-- rfc.py:fixtures:end -->

</details>

## Visibility

Declarations are module-private by default. [A declaration is accessible from outside its module only if it is annotated with `public`](#spec.modules.visibility.legality-1).

```metel
public struct Token { public kind: i64, span: i64 }
struct InternalState { count: i64 }

public fun parse(tokens: Token[]) -> i64 { return tokens.len(); }
fun helper(token: Token) -> boolean { return token.kind == 0; }

fun main() -> i64 {
    let token = Token { kind = 0, span = 1 };
    let state = InternalState { count = 2 };
    if (helper(token)) { return parse([token]) + state.count; }
    return 0;
}
```

`public` is valid on `struct`, `enum`, `fun`, and `aspect` declarations. Top-level `let` and `var` bindings are always module-private; public value exports are not supported in the current version.

Struct field visibility is independent from the struct's own visibility. Fields are module-private by default; [add `public` on each field that should be accessible outside the declaring module](#spec.modules.visibility.legality-1).

```metel
public struct Token {
    public kind: i64,
    span: i64,
}
```

From outside the declaring module, `Token` is nameable, `token.kind` is accessible, and
[reading or assigning `token.span` is a `T0009` visibility error](#spec.modules.visibility.legality-3);
the declaring module retains access to all of its own fields.
[Constructing `Token` directly outside its declaring module also requires visibility to
every named field](#spec.modules.visibility.legality-4), so private fields force
construction through module-local helpers or constructors instead. Marking a field
`public` on a struct that is not itself `public` doesn't expose that field to any other
module — [the compiler warns on this combination](#spec.modules.visibility.legality-5),
since the field can never actually be reached across a module boundary through a private
type. [Pattern-matching `Token` outside its declaring module follows the same rule as
construction](#spec.modules.visibility.legality-7) — a private field may not be named in
the pattern; a `..` rest pattern (see [Struct patterns](expressions.md#struct-patterns))
must be used to omit it instead.

Within a module, all names defined in that module are accessible without qualification, including private names.

Modules do not have their own visibility annotation. Module-level access control is handled entirely by `public` on individual items.

<details>
<summary>Formal rules</summary>

##### Legality Rule {#spec.modules.visibility.legality-1}

Only declarations marked `public` are accessible from outside their declaring module; a
public struct field is accessible outside that module only when the field itself is public.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0030](../../rfcs/4-implemented/rfc-0030-module-system-redesign.md), [rfc-0031](../../rfcs/4-implemented/rfc-0031-topological-typechecker.md), [rfc-0032](../../rfcs/4-implemented/rfc-0032-field-level-visibility.md), [rfc-0098](../../rfcs/4-implemented/rfc-0098-surface-keyword-renames.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [main.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/module_semantics/importing_private_item_is_t0009/main.mtl), [main.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/module_semantics/mixed_visibility_struct_allows_public_field_access_across_modules/main.mtl)_</span>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.modules.visibility.legality-2}

A public function declaration must carry the explicit type annotations required for its
public API; an omitted required annotation is `T0010`.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0031](../../rfcs/4-implemented/rfc-0031-topological-typechecker.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [main.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/module_semantics/pub_fun_without_return_type_is_t0010/main.mtl)_</span>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.modules.visibility.legality-3}

Reading or assigning a private struct field from outside its declaring module is
rejected with `T0009`. The declaring module retains access to all of its own fields,
including private ones.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0032](../../rfcs/4-implemented/rfc-0032-field-level-visibility.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [main.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/module_semantics/private_struct_field_access_across_modules_is_t0009/main.mtl), [main.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/module_semantics/private_struct_field_assignment_across_modules_is_t0009/main.mtl), [main.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/module_semantics/private_struct_fields_remain_accessible_inside_declaring_module/main.mtl)_</span>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.modules.visibility.legality-4}

Constructing a struct literal outside its declaring module is rejected with `T0009` if
it names any private field. A module-local constructor or helper function may still
construct the value.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0032](../../rfcs/4-implemented/rfc-0032-field-level-visibility.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [main.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/module_semantics/private_struct_field_construction_across_modules_is_t0009/main.mtl)_</span>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.modules.visibility.legality-5}

Declaring a field `public` on a struct that is not itself `public` produces a compiler
warning: the field cannot be reached across a module boundary through a private type,
so the `public` marker on it has no effect from outside the declaring module.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0032](../../rfcs/4-implemented/rfc-0032-field-level-visibility.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [public_field_on_private_struct_warns.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/typechecking/structs/public_field_on_private_struct_warns.mtl)_</span>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.modules.visibility.legality-6}

Named fields of an enum struct-like variant follow the same visibility rules as an
ordinary struct's fields: constructing a variant literal outside the enum's declaring
module and naming a private field is rejected with `T0009`, the same as for a struct.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0032](../../rfcs/4-implemented/rfc-0032-field-level-visibility.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [main.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/module_semantics/private_enum_variant_field_construction_across_modules_is_t0009/main.mtl)_</span>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.modules.visibility.legality-7}

Naming a private field in a struct pattern from outside the struct's declaring module is
rejected with `T0009`. The pattern must either omit that field with a trailing `..`, or
be written inside the declaring module, where private fields remain nameable.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0032](../../rfcs/4-implemented/rfc-0032-field-level-visibility.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [main.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/module_semantics/struct_pattern_names_private_field_across_modules_is_t0009/main.mtl), [main.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/module_semantics/struct_pattern_rest_omits_private_field_across_modules/main.mtl)_</span>
<!-- rfc.py:fixtures:end -->

</details>

## Circular Imports

[Circular imports are a compile error](#spec.modules.module-graph-loading.legality-2). The
error message includes the full import chain.

## Module Graph Loading

The module graph is built from both `import` and `export` declarations — a re-export
needs its target module loaded exactly as much as an ordinary import does, since a
name that resolves nowhere can't be re-exported (metel-core#664):

1. The root file is parsed.
2. All `import` and `export` declarations are collected; each is resolved to a file
   path via the `::` → `/` mapping.
3. Each referenced file is loaded recursively; cycles are detected and rejected.
4. Only files reachable via at least one `import` or `export` declaration are loaded.

An `export` still differs from an `import` in what it does with the resolved name —
`import` brings it into local scope, `export` re-exports it through the current
module's public API without making it locally visible — but both equally decide
*which files enter the module graph at all*.

<details>
<summary>Formal rules</summary>

##### Legality Rule {#spec.modules.module-graph-loading.legality-1}

Every non-prelude import must resolve to a loadable module. A missing module is a load
error rather than an import that contributes an empty scope.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0031](../../rfcs/4-implemented/rfc-0031-topological-typechecker.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [main.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/module_loading/import_nonexistent_module_is_a_load_error/main.mtl)_</span>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.modules.module-graph-loading.legality-2}

Imports and re-exports both contribute module-graph edges. Missing modules and circular
dependencies are load errors, and a bare re-export loads its target module.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0030](../../rfcs/4-implemented/rfc-0030-module-system-redesign.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [main.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/module_loading/import_nonexistent_module_is_a_load_error/main.mtl), [main.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/module_loading/rejects_circular_module_graph/main.mtl), [main.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/module_semantics/rfc0030_bare_export_loads_module/main.mtl)_</span>
<!-- rfc.py:fixtures:end -->

</details>

## Single-File Compatibility

A `.mtl` file with no `import` or `export` declarations is a complete program. Existing single-file programs remain valid without modification.

<details>
<summary>Formal rules</summary>

##### Legality Rule {#spec.modules.single-file-compatibility.legality-1}

A source file with no import or export declarations is a complete single-module program.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0030](../../rfcs/4-implemented/rfc-0030-module-system-redesign.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [main.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/module_loading/single_file_program_loads_without_modules/main.mtl)_</span>
<!-- rfc.py:fixtures:end -->

</details>

## Removed Module Keywords

`mod`, `use`, and `pub use` are not module declarations in Metel. Module loading and
re-export use `import` and `export`.

<details>
<summary>Formal rules</summary>

##### Legality Rule {#spec.modules.removed-module-keywords.legality-1}

`mod`, `use`, and `pub use` are rejected by the grammar; module declarations use
`import` and `export` instead.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0030](../../rfcs/4-implemented/rfc-0030-module-system-redesign.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [rfc0030_legacy_mod_use_rejected.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/parsing/rfc0030_legacy_mod_use_rejected.mtl)_</span>
<!-- rfc.py:fixtures:end -->

</details>
