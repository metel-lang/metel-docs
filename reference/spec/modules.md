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
<p class="rigor-backlink"><em>Tested by</em></p>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoic3VjY2VzcyJ9LCJmaWxlcyI6W3sibmFtZSI6Im1haW4ubXRsIiwic291cmNlIjoiaW1wb3J0IHBhcnNlcjo6VG9rZW47XG5mdW4gbWFpbigpIHsgfVxuIn0seyJuYW1lIjoicGFyc2VyLm10bCIsInNvdXJjZSI6InN0cnVjdCBUb2tlbiB7IHZhbHVlOiBpNjQgfVxuIn0seyJuYW1lIjoicGFyc2VyL2FzdC5tdGwiLCJzb3VyY2UiOiJwdWJsaWMgc3RydWN0IEFzdCB7IHB1YmxpYyB2YWx1ZTogaTY0IH1cbiJ9XSwiaHJlZiI6Imh0dHBzOi8vZ2l0aHViLmNvbS9tZXRlbC1sYW5nL21ldGVsLWNvcmUvYmxvYi92MC4xMy4wL21ldGVsLWludGVycHJldGVyL3Rlc3RzL2ludGVncmF0aW9uL3NvdXJjZXMvbW9kdWxlX2xvYWRpbmcvZmFjYWRlX21vZHVsZV9hbG9uZ3NpZGVfZGlyZWN0b3J5IiwibmFtZSI6ImZhY2FkZV9tb2R1bGVfYWxvbmdzaWRlX2RpcmVjdG9yeSJ9"></details>
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
<p class="rigor-backlink"><em>Tested by</em></p>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6IlAwMDAxIiwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoicGFyc2VfZXJyb3IifSwiZmlsZXMiOlt7Im5hbWUiOiJyZmMwMDMwX2ltcG9ydF9hZnRlcl9kZWNsYXJhdGlvbi5tdGwiLCJzb3VyY2UiOiJmdW4gbWFpbigpIC0+IGk2NCB7IDAgfVxuaW1wb3J0IGhlbHBlcjo6YW5zd2VyO1xuIn1dLCJocmVmIjoiaHR0cHM6Ly9naXRodWIuY29tL21ldGVsLWxhbmcvbWV0ZWwtY29yZS9ibG9iL3YwLjEzLjAvbWV0ZWwtaW50ZXJwcmV0ZXIvdGVzdHMvaW50ZWdyYXRpb24vc291cmNlcy9wYXJzaW5nL3JmYzAwMzBfaW1wb3J0X2FmdGVyX2RlY2xhcmF0aW9uLm10bCIsIm5hbWUiOiJyZmMwMDMwX2ltcG9ydF9hZnRlcl9kZWNsYXJhdGlvbi5tdGwifQ=="></details>
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
    let token: root::parser::Token := root::parser::Token { value = 42 };
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
<p class="rigor-backlink"><em>Tested by</em></p>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoic3VjY2VzcyJ9LCJmaWxlcyI6W3sibmFtZSI6Im1haW4ubXRsIiwic291cmNlIjoiaW1wb3J0IHBhcnNlcjo6VG9rZW47XG5mdW4gbWFpbigpIHsgfVxuIn0seyJuYW1lIjoiY2hpbGQubXRsIiwic291cmNlIjoic3RydWN0IFRoaW5nIHsgdmFsdWU6IGk2NCB9XG4ifSx7Im5hbWUiOiJwYXJzZXIubXRsIiwic291cmNlIjoiXG5pbXBvcnQgc2VsZjo6Y2hpbGQ6OlRoaW5nO1xuaW1wb3J0IHJvb3Q6OmNoaWxkOjpUaGluZztcbmltcG9ydCBzdXBlcjo6Y2hpbGQ6OlRoaW5nO1xuaW1wb3J0IHN0ZDo6Y29yZTo6aTY0O1xuaW1wb3J0IGNoaWxkOjpUaGluZztcblxuc3RydWN0IFRva2VuIHsgdmFsdWU6IGk2NCB9XG4ifV0sImhyZWYiOiJodHRwczovL2dpdGh1Yi5jb20vbWV0ZWwtbGFuZy9tZXRlbC1jb3JlL2Jsb2IvdjAuMTMuMC9tZXRlbC1pbnRlcnByZXRlci90ZXN0cy9pbnRlZ3JhdGlvbi9zb3VyY2VzL21vZHVsZV9sb2FkaW5nL2FjY2VwdHNfcm9vdF9zZWxmX3N1cGVyX3N0ZF9hbmRfY2hpbGRfcm9vdHNfaW5fbm9uX3Jvb3RfbW9kdWxlcyIsIm5hbWUiOiJhY2NlcHRzX3Jvb3Rfc2VsZl9zdXBlcl9zdGRfYW5kX2NoaWxkX3Jvb3RzX2luX25vbl9yb290X21vZHVsZXMifQ=="></details>
<!-- rfc.py:fixtures:end -->

</details>

## Imports

`import` loads the referenced module file and declares which names from it are in scope for the current module:

```metel
// src/main.mtl
import parser::*;
import root::lexer::Token as Tok;

fun main() -> i64 {
    let ast := Ast { token = Token { value = 1 } };
    let tok: Tok := dbg(Tok { value = 2 });
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
<p class="rigor-backlink"><em>Tested by</em></p>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoic3VjY2VzcyJ9LCJmaWxlcyI6W3sibmFtZSI6Im1haW4ubXRsIiwic291cmNlIjoiaW1wb3J0IGhlbHBlcjo6YW5zd2VyO1xuZnVuIG1haW4oKSAtPiBpNjQgeyByZXR1cm4gYW5zd2VyKCk7IH1cbiJ9LHsibmFtZSI6ImhlbHBlci5tdGwiLCJzb3VyY2UiOiJwdWJsaWMgZnVuIGFuc3dlcigpIC0+IGk2NCB7IHJldHVybiA3OyB9XG4ifV0sImhyZWYiOiJodHRwczovL2dpdGh1Yi5jb20vbWV0ZWwtbGFuZy9tZXRlbC1jb3JlL2Jsb2IvdjAuMTMuMC9tZXRlbC1pbnRlcnByZXRlci90ZXN0cy9pbnRlZ3JhdGlvbi9zb3VyY2VzL21vZHVsZV9zZW1hbnRpY3MvZXhwbGljaXRfbmFtZWRfaW1wb3J0X2Z1bmN0aW9uX2NhbGwiLCJuYW1lIjoiZXhwbGljaXRfbmFtZWRfaW1wb3J0X2Z1bmN0aW9uX2NhbGwifQ=="></details>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.modules.imports.legality-2}

An aliased import binds only its alias locally. The alias may be used wherever the
imported declaration's kind permits, including as a value, type, or constructor.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0031](../../rfcs/4-implemented/rfc-0031-topological-typechecker.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<p class="rigor-backlink"><em>Tested by</em></p>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoidHlwZWNoZWNrX2Vycm9yIn0sImZpbGVzIjpbeyJuYW1lIjoibWFpbi5tdGwiLCJzb3VyY2UiOiJpbXBvcnQgaGVscGVyOjphbnN3ZXIgYXMgY29tcHV0ZTtcbmZ1biBtYWluKCkgLT4gaTY0IHsgcmV0dXJuIGFuc3dlcigpOyB9XG4ifSx7Im5hbWUiOiJoZWxwZXIubXRsIiwic291cmNlIjoicHVibGljIGZ1biBhbnN3ZXIoKSAtPiBpNjQgeyByZXR1cm4gNDI7IH1cbiJ9XSwiaHJlZiI6Imh0dHBzOi8vZ2l0aHViLmNvbS9tZXRlbC1sYW5nL21ldGVsLWNvcmUvYmxvYi92MC4xMy4wL21ldGVsLWludGVycHJldGVyL3Rlc3RzL2ludGVncmF0aW9uL3NvdXJjZXMvbW9kdWxlX3NlbWFudGljcy9hbGlhc19pbXBvcnRfb3JpZ2luYWxfbmFtZV9ub3RfaW5fc2NvcGUiLCJuYW1lIjoiYWxpYXNfaW1wb3J0X29yaWdpbmFsX25hbWVfbm90X2luX3Njb3BlIn0="></details>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoic3VjY2VzcyJ9LCJmaWxlcyI6W3sibmFtZSI6Im1haW4ubXRsIiwic291cmNlIjoiaW1wb3J0IGxleGVyOjpUb2tlbiBhcyBUb2s7XG5cbmZ1biBtYWluKCkge1xuICAgIGxldCBhOiBUb2sgOj0gVG9rZW4geyB2YWx1ZSA9IDEgfTtcbiAgICBhc3NlcnQoYS52YWx1ZSA9PSAxKTtcbiAgICBsZXQgYiA6PSBUb2sgeyB2YWx1ZSA9IDIgfTtcbiAgICBhc3NlcnQoYi52YWx1ZSA9PSAyKTtcbn1cbiJ9LHsibmFtZSI6ImxleGVyLm10bCIsInNvdXJjZSI6InB1YmxpYyBzdHJ1Y3QgVG9rZW4geyBwdWJsaWMgdmFsdWU6IGk2NCB9XG4ifV0sImhyZWYiOiJodHRwczovL2dpdGh1Yi5jb20vbWV0ZWwtbGFuZy9tZXRlbC1jb3JlL2Jsb2IvdjAuMTMuMC9tZXRlbC1pbnRlcnByZXRlci90ZXN0cy9pbnRlZ3JhdGlvbi9zb3VyY2VzL21vZHVsZV9zZW1hbnRpY3MvYWxpYXNfaW1wb3J0X3VzYWJsZV9hc190eXBlX2Fubm90YXRpb25fYW5kX2NvbnN0cnVjdG9yIiwibmFtZSI6ImFsaWFzX2ltcG9ydF91c2FibGVfYXNfdHlwZV9hbm5vdGF0aW9uX2FuZF9jb25zdHJ1Y3RvciJ9"></details>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.modules.imports.legality-3}

A qualified use resolves through an imported binding; an unresolved qualified path is a
name-resolution error and is not retried as an arbitrary bare name.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0031](../../rfcs/4-implemented/rfc-0031-topological-typechecker.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<p class="rigor-backlink"><em>Tested by</em></p>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoic3VjY2VzcyJ9LCJmaWxlcyI6W3sibmFtZSI6Im1haW4ubXRsIiwic291cmNlIjoiaW1wb3J0IGhlbHBlcjo6KjtcbmZ1biBtYWluKCkgLT4gaTY0IHsgcmV0dXJuIGhlbHBlcjo6YW5zd2VyKCk7IH1cbiJ9LHsibmFtZSI6ImhlbHBlci5tdGwiLCJzb3VyY2UiOiJwdWJsaWMgZnVuIGFuc3dlcigpIC0+IGk2NCB7IHJldHVybiA5OTsgfVxuIn1dLCJocmVmIjoiaHR0cHM6Ly9naXRodWIuY29tL21ldGVsLWxhbmcvbWV0ZWwtY29yZS9ibG9iL3YwLjEzLjAvbWV0ZWwtaW50ZXJwcmV0ZXIvdGVzdHMvaW50ZWdyYXRpb24vc291cmNlcy9tb2R1bGVfc2VtYW50aWNzL3F1YWxpZmllZF9jYWxsX25vcm1hbGl6ZWRfdG9fYmFyZV9uYW1lIiwibmFtZSI6InF1YWxpZmllZF9jYWxsX25vcm1hbGl6ZWRfdG9fYmFyZV9uYW1lIn0="></details>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.modules.imports.legality-4}

An import loads its referenced module and introduces the selected public names or module
handle into the importing module's scope.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0030](../../rfcs/4-implemented/rfc-0030-module-system-redesign.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<p class="rigor-backlink"><em>Tested by</em></p>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoic3VjY2VzcyJ9LCJmaWxlcyI6W3sibmFtZSI6Im1haW4ubXRsIiwic291cmNlIjoiaW1wb3J0IGhlbHBlcjo6YW5zd2VyO1xuZnVuIG1haW4oKSAtPiBpNjQgeyByZXR1cm4gYW5zd2VyKCk7IH1cbiJ9LHsibmFtZSI6ImhlbHBlci5tdGwiLCJzb3VyY2UiOiJwdWJsaWMgZnVuIGFuc3dlcigpIC0+IGk2NCB7IHJldHVybiA3OyB9XG4ifV0sImhyZWYiOiJodHRwczovL2dpdGh1Yi5jb20vbWV0ZWwtbGFuZy9tZXRlbC1jb3JlL2Jsb2IvdjAuMTMuMC9tZXRlbC1pbnRlcnByZXRlci90ZXN0cy9pbnRlZ3JhdGlvbi9zb3VyY2VzL21vZHVsZV9zZW1hbnRpY3MvZXhwbGljaXRfbmFtZWRfaW1wb3J0X2Z1bmN0aW9uX2NhbGwiLCJuYW1lIjoiZXhwbGljaXRfbmFtZWRfaW1wb3J0X2Z1bmN0aW9uX2NhbGwifQ=="></details>
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
<p class="rigor-backlink"><em>Tested by</em></p>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6IlQwMDA5IiwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoidHlwZWNoZWNrX2Vycm9yIn0sImZpbGVzIjpbeyJuYW1lIjoibWFpbi5tdGwiLCJzb3VyY2UiOiJpbXBvcnQgZmFjYWRlOjpzZWNyZXQ7XG5mdW4gbWFpbigpIC0+IGk2NCB7IHNlY3JldCgpIH1cbiJ9LHsibmFtZSI6ImZhY2FkZS5tdGwiLCJzb3VyY2UiOiJleHBvcnQgaGVscGVyOjpzZWNyZXQ7XG4ifSx7Im5hbWUiOiJoZWxwZXIubXRsIiwic291cmNlIjoiZnVuIHNlY3JldCgpIC0+IGk2NCB7IDQyIH1cbiJ9XSwiaHJlZiI6Imh0dHBzOi8vZ2l0aHViLmNvbS9tZXRlbC1sYW5nL21ldGVsLWNvcmUvYmxvYi92MC4xMy4wL21ldGVsLWludGVycHJldGVyL3Rlc3RzL2ludGVncmF0aW9uL3NvdXJjZXMvbW9kdWxlX3NlbWFudGljcy9yZmMwMDMxX3JlZXhwb3J0X3ByaXZhdGVfaXRlbV9pc190MDAwOSIsIm5hbWUiOiJyZmMwMDMxX3JlZXhwb3J0X3ByaXZhdGVfaXRlbV9pc190MDAwOSJ9"></details>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.modules.re-exports.legality-2}

A re-export makes a public source declaration available through the current module's
public API, including under an alias; importers may use it as a declaration of the facade.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0030](../../rfcs/4-implemented/rfc-0030-module-system-redesign.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<p class="rigor-backlink"><em>Tested by</em></p>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoic3VjY2VzcyJ9LCJmaWxlcyI6W3sibmFtZSI6Im1haW4ubXRsIiwic291cmNlIjoiaW1wb3J0IGZhY2FkZTo6YW5zd2VyO1xuZnVuIG1haW4oKSAtPiBpNjQgeyByZXR1cm4gYW5zd2VyKCk7IH1cbiJ9LHsibmFtZSI6ImZhY2FkZS5tdGwiLCJzb3VyY2UiOiJpbXBvcnQgaGVscGVyOjphbnN3ZXI7XG5leHBvcnQgaGVscGVyOjphbnN3ZXI7XG4ifSx7Im5hbWUiOiJoZWxwZXIubXRsIiwic291cmNlIjoicHVibGljIGZ1biBhbnN3ZXIoKSAtPiBpNjQgeyByZXR1cm4gNDI7IH1cbiJ9XSwiaHJlZiI6Imh0dHBzOi8vZ2l0aHViLmNvbS9tZXRlbC1sYW5nL21ldGVsLWNvcmUvYmxvYi92MC4xMy4wL21ldGVsLWludGVycHJldGVyL3Rlc3RzL2ludGVncmF0aW9uL3NvdXJjZXMvbW9kdWxlX3NlbWFudGljcy9mYWNhZGVfcmVfZXhwb3J0c19pdGVtX2FuZF9jb25zdW1lcl9jYW5fdXNlX2l0IiwibmFtZSI6ImZhY2FkZV9yZV9leHBvcnRzX2l0ZW1fYW5kX2NvbnN1bWVyX2Nhbl91c2VfaXQifQ=="></details>
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
    match (maybe_parse("1")) {
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
<p class="rigor-backlink"><em>Tested by</em></p>
<details class="spec-fixture" data-fixture="eyJmaWxlcyI6W3sibmFtZSI6ImludF8wOF9zdGRfY29yZV9wYXRocy5tdGwiLCJzb3VyY2UiOiIvLyBJbnRlZ3JhdGlvbiBUZXN0IDggXHUyMDE0IENvcmUgdHlwZSBjb21wbGV0ZW5lc3M6IFBlcmhhcHMgYW5kIFJlc3VsdCAodjAuNi4wKVxuLy9cbi8vIEZlYXR1cmUgY292ZXJhZ2U6XG4vLyAgIFBlcmhhcHM8VD4gY29uc3RydWN0aW9uLCBtYXRjaGluZywgYW5kIGNoYWluaW5nXG4vLyAgIFJlc3VsdDxULEU+IGNvbnN0cnVjdGlvbiwgbWF0Y2hpbmcsID8gcHJvcGFnYXRpb24sIGFuZCBGcm9tIGNvZXJjaW9uXG4vLyAgIEdlbmVyaWMgZnVuY3Rpb25zIG92ZXIgUGVyaGFwcyBhbmQgUmVzdWx0XG4vLyAgIEludGVyYWN0aW9uOiBmdW5jdGlvbiByZXR1cm5pbmcgUGVyaGFwcyB1c2VkIGluIFJlc3VsdCBjb250ZXh0IHZpYSBtYXBcbi8vICAgUmVncmVzc2lvbjogZW5zdXJlICMxMzMgKFR5cGVEZWZpbml0aW9uUmVnaXN0cnkpIGRpZCBub3QgYnJlYWsgdGhlc2UgcGF0aHNcblxuLy8gXHUyNTAwXHUyNTAwIFJlc3VsdCBoZWxwZXJzIFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFxuXG5zdHJ1Y3QgUGFyc2VFcnJvciB7IG1zZzogU3RyaW5nIH1cbnN0cnVjdCBNYXRoRXJyb3IgIHsgbXNnOiBTdHJpbmcgfVxuXG5leHRlbmQgTWF0aEVycm9yOiBGcm9tPFBhcnNlRXJyb3I+IHtcbiAgICBmdW4gZnJvbSh2YWx1ZTogUGFyc2VFcnJvcikgLT4gTWF0aEVycm9yIHtcbiAgICAgICAgTWF0aEVycm9yIHsgbXNnID0gXCJwYXJzZTogXCIgKyB2YWx1ZS5tc2cgfVxuICAgIH1cbn1cblxuZnVuIHBhcnNlX3Bvc2l0aXZlKHM6IFN0cmluZykgLT4gUmVzdWx0PGk2NCwgUGFyc2VFcnJvcj4ge1xuICAgIGlmIChzID09IFwiMVwiKSB7IFJlc3VsdDo6T2sgeyB2YWx1ZSA9IDEgfSB9XG4gICAgZWxzZSBpZiAocyA9PSBcIjJcIikgeyBSZXN1bHQ6Ok9rIHsgdmFsdWUgPSAyIH0gfVxuICAgIGVsc2UgaWYgKHMgPT0gXCIxMFwiKSB7IFJlc3VsdDo6T2sgeyB2YWx1ZSA9IDEwIH0gfVxuICAgIGVsc2UgaWYgKHMgPT0gXCI0MlwiKSB7IFJlc3VsdDo6T2sgeyB2YWx1ZSA9IDQyIH0gfVxuICAgIGVsc2UgeyBSZXN1bHQ6OkVyciB7IGVycm9yID0gUGFyc2VFcnJvciB7IG1zZyA9IFwiYmFkIGlucHV0OiBcIiArIHMgfSB9IH1cbn1cblxuZnVuIGRvdWJsZV9wYXJzZWQoczogU3RyaW5nKSAtPiBSZXN1bHQ8aTY0LCBQYXJzZUVycm9yPiB7XG4gICAgbGV0IG4gOj0gcGFyc2VfcG9zaXRpdmUocyk/O1xuICAgIFJlc3VsdDo6T2sgeyB2YWx1ZSA9IG4gKiAyIH1cbn1cblxuZnVuIGFkZF9wYXJzZWQoYTogU3RyaW5nLCBiOiBTdHJpbmcpIC0+IFJlc3VsdDxpNjQsIE1hdGhFcnJvcj4ge1xuICAgIC8vIGNyb3NzLXR5cGUgbWF0Y2ggKyBhcy1jYXN0ICg/IGNyb3NzLXR5cGUgZGVmZXJyZWQgdG8gIzEzKVxuICAgIGxldCB4IDo9IG1hdGNoIChwYXJzZV9wb3NpdGl2ZShhKSkge1xuICAgICAgICBSZXN1bHQ6Ok9rIHsgdmFsdWUgfSA9PiB2YWx1ZSxcbiAgICAgICAgUmVzdWx0OjpFcnIgeyBlcnJvciB9ID0+IHsgcmV0dXJuIFJlc3VsdDo6RXJyIHsgZXJyb3IgPSBlcnJvciBhcyBNYXRoRXJyb3IgfTsgfSxcbiAgICB9O1xuICAgIGxldCB5IDo9IG1hdGNoIChwYXJzZV9wb3NpdGl2ZShiKSkge1xuICAgICAgICBSZXN1bHQ6Ok9rIHsgdmFsdWUgfSA9PiB2YWx1ZSxcbiAgICAgICAgUmVzdWx0OjpFcnIgeyBlcnJvciB9ID0+IHsgcmV0dXJuIFJlc3VsdDo6RXJyIHsgZXJyb3IgPSBlcnJvciBhcyBNYXRoRXJyb3IgfTsgfSxcbiAgICB9O1xuICAgIFJlc3VsdDo6T2sgeyB2YWx1ZSA9IHggKyB5IH1cbn1cblxuLy8gXHUyNTAwXHUyNTAwIFBlcmhhcHMgaGVscGVycyBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcblxuZnVuIGZpbmRfaW4oYXJyOiBpNjRbXSwgdGFyZ2V0OiBpNjQpIC0+IFBlcmhhcHM8aTY0PiB7XG4gICAgdmFyIGkgOj0gMDtcbiAgICB3aGlsZSAoaSA8IGFyci5sZW4oKSkge1xuICAgICAgICBpZiAoYXJyW2kgYXMgdTY0XSA9PSB0YXJnZXQpIHsgcmV0dXJuIFBlcmhhcHM6OlNvbWUgeyB2YWx1ZSA9IGkgfTsgfVxuICAgICAgICBpICs9IDE7XG4gICAgfVxuICAgIE5vbmVcbn1cblxuZnVuIG1hcF9zb21lKHA6IFBlcmhhcHM8aTY0PiwgZmFjdG9yOiBpNjQpIC0+IFBlcmhhcHM8aTY0PiB7XG4gICAgbWF0Y2ggKHApIHtcbiAgICAgICAgUGVyaGFwczo6U29tZSB7IHZhbHVlIH0gPT4gUGVyaGFwczo6U29tZSB7IHZhbHVlID0gdmFsdWUgKiBmYWN0b3IgfSxcbiAgICAgICAgTm9uZSA9PiBOb25lLFxuICAgIH1cbn1cblxuZnVuIHBlcmhhcHNfdG9fcmVzdWx0KHA6IFBlcmhhcHM8aTY0PiwgZXJyb3I6IFN0cmluZykgLT4gUmVzdWx0PGk2NCwgU3RyaW5nPiB7XG4gICAgbWF0Y2ggKHApIHtcbiAgICAgICAgUGVyaGFwczo6U29tZSB7IHZhbHVlIH0gPT4gUmVzdWx0OjpPayB7IHZhbHVlID0gdmFsdWUgfSxcbiAgICAgICAgTm9uZSA9PiBSZXN1bHQ6OkVyciB7IGVycm9yID0gZXJyb3IgfSxcbiAgICB9XG59XG5cbmZ1biBtYWluKCkge1xuICAgIC8vIFx1MjUwMFx1MjUwMCBCYXNpYyBSZXN1bHQgbWF0Y2hpbmcgXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXG5cbiAgICBsZXQgcjEgOj0gcGFyc2VfcG9zaXRpdmUoXCI0MlwiKTtcbiAgICBtYXRjaCAocjEpIHtcbiAgICAgICAgUmVzdWx0OjpPayAgeyB2YWx1ZSB9ID0+IGFzc2VydCh2YWx1ZSA9PSA0MiksXG4gICAgICAgIFJlc3VsdDo6RXJyIHsgZXJyb3IgfSA9PiBhc3NlcnQoZmFsc2UpLFxuICAgIH07XG5cbiAgICBsZXQgcjIgOj0gcGFyc2VfcG9zaXRpdmUoXCJiYWRcIik7XG4gICAgbWF0Y2ggKHIyKSB7XG4gICAgICAgIFJlc3VsdDo6T2sgIHsgdmFsdWUgfSA9PiBhc3NlcnQoZmFsc2UpLFxuICAgICAgICBSZXN1bHQ6OkVyciB7IGVycm9yIH0gPT4gYXNzZXJ0KGVycm9yLm1zZyA9PSBcImJhZCBpbnB1dDogYmFkXCIpLFxuICAgIH07XG5cbiAgICAvLyBcdTI1MDBcdTI1MDAgPyBwcm9wYWdhdGlvbiAoc2FtZS10eXBlKSBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcblxuICAgIGxldCBkMSA6PSBkb3VibGVfcGFyc2VkKFwiMTBcIik7XG4gICAgbWF0Y2ggKGQxKSB7XG4gICAgICAgIFJlc3VsdDo6T2sgIHsgdmFsdWUgfSA9PiBhc3NlcnQodmFsdWUgPT0gMjApLFxuICAgICAgICBSZXN1bHQ6OkVyciB7IGVycm9yIH0gPT4gYXNzZXJ0KGZhbHNlKSxcbiAgICB9O1xuXG4gICAgbGV0IGQyIDo9IGRvdWJsZV9wYXJzZWQoXCJub3BlXCIpO1xuICAgIG1hdGNoIChkMikge1xuICAgICAgICBSZXN1bHQ6Ok9rICB7IHZhbHVlIH0gPT4gYXNzZXJ0KGZhbHNlKSxcbiAgICAgICAgUmVzdWx0OjpFcnIgeyBlcnJvciB9ID0+IGFzc2VydChlcnJvci5tc2cgPT0gXCJiYWQgaW5wdXQ6IG5vcGVcIiksXG4gICAgfTtcblxuICAgIC8vIFx1MjUwMFx1MjUwMCA/IHByb3BhZ2F0aW9uIHdpdGggRnJvbSBjb2VyY2lvbiAoUGFyc2VFcnJvciBcdTIxOTIgTWF0aEVycm9yKSBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcblxuICAgIGxldCBhMSA6PSBhZGRfcGFyc2VkKFwiMVwiLCBcIjJcIik7XG4gICAgbWF0Y2ggKGExKSB7XG4gICAgICAgIFJlc3VsdDo6T2sgIHsgdmFsdWUgfSA9PiBhc3NlcnQodmFsdWUgPT0gMyksXG4gICAgICAgIFJlc3VsdDo6RXJyIHsgZXJyb3IgfSA9PiBhc3NlcnQoZmFsc2UpLFxuICAgIH07XG5cbiAgICBsZXQgYTIgOj0gYWRkX3BhcnNlZChcIjFcIiwgXCJiYWRcIik7XG4gICAgbWF0Y2ggKGEyKSB7XG4gICAgICAgIFJlc3VsdDo6T2sgIHsgdmFsdWUgfSA9PiBhc3NlcnQoZmFsc2UpLFxuICAgICAgICBSZXN1bHQ6OkVyciB7IGVycm9yIH0gPT4gYXNzZXJ0KGVycm9yLm1zZyA9PSBcInBhcnNlOiBiYWQgaW5wdXQ6IGJhZFwiKSxcbiAgICB9O1xuXG4gICAgbGV0IGEzIDo9IGFkZF9wYXJzZWQoXCJ4XCIsIFwiMlwiKTtcbiAgICBtYXRjaCAoYTMpIHtcbiAgICAgICAgUmVzdWx0OjpPayAgeyB2YWx1ZSB9ID0+IGFzc2VydChmYWxzZSksXG4gICAgICAgIFJlc3VsdDo6RXJyIHsgZXJyb3IgfSA9PiBhc3NlcnQoZXJyb3IubXNnID09IFwicGFyc2U6IGJhZCBpbnB1dDogeFwiKSxcbiAgICB9O1xuXG4gICAgLy8gXHUyNTAwXHUyNTAwIFBlcmhhcHM6IGZpbmRfaW4gXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXG5cbiAgICBsZXQgYXJyIDo9IFsxMCwgMjAsIDMwLCA0MCwgNTBdO1xuXG4gICAgbGV0IGYxIDo9IGZpbmRfaW4oYXJyLCAzMCk7XG4gICAgbWF0Y2ggKGYxKSB7XG4gICAgICAgIFBlcmhhcHM6OlNvbWUgeyB2YWx1ZSB9ID0+IGFzc2VydCh2YWx1ZSA9PSAyKSxcbiAgICAgICAgTm9uZSA9PiBhc3NlcnQoZmFsc2UpLFxuICAgIH07XG5cbiAgICBsZXQgZjIgOj0gZmluZF9pbihhcnIsIDk5KTtcbiAgICBtYXRjaCAoZjIpIHtcbiAgICAgICAgUGVyaGFwczo6U29tZSB7IHZhbHVlIH0gPT4gYXNzZXJ0KGZhbHNlKSxcbiAgICAgICAgTm9uZSA9PiBhc3NlcnQodHJ1ZSksXG4gICAgfTtcblxuICAgIC8vIFx1MjUwMFx1MjUwMCBQZXJoYXBzIGNoYWluaW5nIHZpYSBtYXBfc29tZSBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcblxuICAgIGxldCBtMSA6PSBtYXBfc29tZShQZXJoYXBzOjpTb21lIHsgdmFsdWUgPSA1IH0sIDMpO1xuICAgIG1hdGNoIChtMSkge1xuICAgICAgICBQZXJoYXBzOjpTb21lIHsgdmFsdWUgfSA9PiBhc3NlcnQodmFsdWUgPT0gMTUpLFxuICAgICAgICBOb25lID0+IGFzc2VydChmYWxzZSksXG4gICAgfTtcblxuICAgIGxldCBtMiA6PSBtYXBfc29tZShOb25lLCAzKTtcbiAgICBtYXRjaCAobTIpIHtcbiAgICAgICAgUGVyaGFwczo6U29tZSB7IHZhbHVlIH0gPT4gYXNzZXJ0KGZhbHNlKSxcbiAgICAgICAgTm9uZSA9PiBhc3NlcnQodHJ1ZSksXG4gICAgfTtcblxuICAgIC8vIG1hcF9zb21lIG9mIGEgZmluZF9pbiByZXN1bHRcbiAgICBsZXQgbWFwcGVkIDo9IG1hcF9zb21lKGZpbmRfaW4oYXJyLCAyMCksIDEwKTtcbiAgICBtYXRjaCAobWFwcGVkKSB7XG4gICAgICAgIFBlcmhhcHM6OlNvbWUgeyB2YWx1ZSB9ID0+IGFzc2VydCh2YWx1ZSA9PSAxMCksIC8vIGluZGV4IDEsIG11bHRpcGxpZWQgYnkgMTBcbiAgICAgICAgTm9uZSA9PiBhc3NlcnQoZmFsc2UpLFxuICAgIH07XG5cbiAgICAvLyBcdTI1MDBcdTI1MDAgcGVyaGFwc190b19yZXN1bHQgYnJpZGdlIFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFxuXG4gICAgbGV0IHAycl9vayA6PSBwZXJoYXBzX3RvX3Jlc3VsdChQZXJoYXBzOjpTb21lIHsgdmFsdWUgPSA3IH0sIFwibm90IGZvdW5kXCIpO1xuICAgIG1hdGNoIChwMnJfb2spIHtcbiAgICAgICAgUmVzdWx0OjpPayAgeyB2YWx1ZSB9ID0+IGFzc2VydCh2YWx1ZSA9PSA3KSxcbiAgICAgICAgUmVzdWx0OjpFcnIgeyBlcnJvciB9ID0+IGFzc2VydChmYWxzZSksXG4gICAgfTtcblxuICAgIGxldCBwMnJfZXJyIDo9IHBlcmhhcHNfdG9fcmVzdWx0KE5vbmUsIFwibm90IGZvdW5kXCIpO1xuICAgIG1hdGNoIChwMnJfZXJyKSB7XG4gICAgICAgIFJlc3VsdDo6T2sgIHsgdmFsdWUgfSA9PiBhc3NlcnQoZmFsc2UpLFxuICAgICAgICBSZXN1bHQ6OkVyciB7IGVycm9yIH0gPT4gYXNzZXJ0KGVycm9yID09IFwibm90IGZvdW5kXCIpLFxuICAgIH07XG5cbiAgICAvLyBDb21iaW5lIGZpbmRfaW4gKHJldHVybnMgUGVyaGFwcykgd2l0aCBwZXJoYXBzX3RvX3Jlc3VsdCAoY29udmVydHMgdG8gUmVzdWx0KVxuICAgIGxldCBicmlkZ2UgOj0gcGVyaGFwc190b19yZXN1bHQoZmluZF9pbihhcnIsIDQwKSwgXCJtaXNzaW5nXCIpO1xuICAgIG1hdGNoIChicmlkZ2UpIHtcbiAgICAgICAgUmVzdWx0OjpPayAgeyB2YWx1ZSB9ID0+IGFzc2VydCh2YWx1ZSA9PSAzKSwgLy8gaW5kZXggM1xuICAgICAgICBSZXN1bHQ6OkVyciB7IGVycm9yIH0gPT4gYXNzZXJ0KGZhbHNlKSxcbiAgICB9O1xuXG4gICAgbGV0IGJyaWRnZV9taXNzIDo9IHBlcmhhcHNfdG9fcmVzdWx0KGZpbmRfaW4oYXJyLCAwKSwgXCJtaXNzaW5nXCIpO1xuICAgIG1hdGNoIChicmlkZ2VfbWlzcykge1xuICAgICAgICBSZXN1bHQ6Ok9rICB7IHZhbHVlIH0gPT4gYXNzZXJ0KGZhbHNlKSxcbiAgICAgICAgUmVzdWx0OjpFcnIgeyBlcnJvciB9ID0+IGFzc2VydChlcnJvciA9PSBcIm1pc3NpbmdcIiksXG4gICAgfTtcbn1cbiJ9XSwiaHJlZiI6Imh0dHBzOi8vZ2l0aHViLmNvbS9tZXRlbC1sYW5nL21ldGVsLWNvcmUvYmxvYi92MC4xMy4wL21ldGVsLWludGVycHJldGVyL3Rlc3RzL2ludGVncmF0aW9uL3NvdXJjZXMvZXZhbHVhdG9yL2ludGVncmF0aW9uL2ludF8wOF9zdGRfY29yZV9wYXRocy5tdGwiLCJuYW1lIjoiaW50XzA4X3N0ZF9jb3JlX3BhdGhzLm10bCJ9"></details>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoic3VjY2VzcyJ9LCJmaWxlcyI6W3sibmFtZSI6Im1haW4ubXRsIiwic291cmNlIjoiaW1wb3J0IGhlbHBlcjo6c3VtOyAgICAgICAgIFxuZnVuIG1haW4oKSB7ICAgICAgICAgXG4gICAgbGV0IGFyciA6PSBbMSwgMiwgMywgNCwgNV07ICAgICAgICAgXG4gICAgbGV0IHJlc3VsdCA6PSBzdW0oYXJyKTsgICAgICAgICBcbiAgICBhc3NlcnQocmVzdWx0ID09IDE1KTsgICAgICAgICBcbiAgICBwcmludChyZXN1bHQpOyAgICAgICAgIFxufVxuIn0seyJuYW1lIjoiaGVscGVyLm10bCIsInNvdXJjZSI6InB1YmxpYyBmdW4gc3VtKGFycjogaTY0W10pIC0+IGk2NCB7ICAgICAgICAgXG4gICAgYXNzZXJ0KGFyci5sZW4oKSA+IDApOyAgICAgICAgIFxuICAgIHZhciB0b3RhbCA6PSAwOyAgICAgICAgIFxuICAgIHZhciBpIDo9IDA7ICAgICAgICAgXG4gICAgd2hpbGUgKGkgPCBhcnIubGVuKCkpIHsgdG90YWwgKz0gYXJyW2kgYXMgdTY0XTsgaSArPSAxOyB9ICAgICAgICAgXG4gICAgcmV0dXJuIHRvdGFsOyAgICAgICAgIFxufVxuIn1dLCJocmVmIjoiaHR0cHM6Ly9naXRodWIuY29tL21ldGVsLWxhbmcvbWV0ZWwtY29yZS9ibG9iL3YwLjEzLjAvbWV0ZWwtaW50ZXJwcmV0ZXIvdGVzdHMvaW50ZWdyYXRpb24vc291cmNlcy9tb2R1bGVfc2VtYW50aWNzL3N0ZF9jb3JlX2J1aWx0aW5zX2F2YWlsYWJsZV9pbl9lYWNoX21vZHVsZV93aXRob3V0X2ltcG9ydCIsIm5hbWUiOiJzdGRfY29yZV9idWlsdGluc19hdmFpbGFibGVfaW5fZWFjaF9tb2R1bGVfd2l0aG91dF9pbXBvcnQifQ=="></details>
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
<p class="rigor-backlink"><em>Tested by</em></p>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6IlQwMDExIiwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoidHlwZWNoZWNrX2Vycm9yIn0sImZpbGVzIjpbeyJuYW1lIjoibWFpbi5tdGwiLCJzb3VyY2UiOiJpbXBvcnQgYTo6Zm9vO1xuaW1wb3J0IGI6OmZvbztcbmZ1biBtYWluKCkgLT4gaTY0IHsgcmV0dXJuIGZvbygpOyB9XG4ifSx7Im5hbWUiOiJhLm10bCIsInNvdXJjZSI6InB1YmxpYyBmdW4gZm9vKCkgLT4gaTY0IHsgcmV0dXJuIDE7IH1cbiJ9LHsibmFtZSI6ImIubXRsIiwic291cmNlIjoicHVibGljIGZ1biBmb28oKSAtPiBpNjQgeyByZXR1cm4gMjsgfVxuIn1dLCJocmVmIjoiaHR0cHM6Ly9naXRodWIuY29tL21ldGVsLWxhbmcvbWV0ZWwtY29yZS9ibG9iL3YwLjEzLjAvbWV0ZWwtaW50ZXJwcmV0ZXIvdGVzdHMvaW50ZWdyYXRpb24vc291cmNlcy9tb2R1bGVfc2VtYW50aWNzL3R3b19leHBsaWNpdF9pbXBvcnRzX3NhbWVfbG9jYWxfbmFtZV9pc190MDAxMSIsIm5hbWUiOiJ0d29fZXhwbGljaXRfaW1wb3J0c19zYW1lX2xvY2FsX25hbWVfaXNfdDAwMTEifQ=="></details>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.modules.import-conflicts.legality-2}

A collision between two user glob imports is rejected with `T0011` only when code refers
to the ambiguous name.

<!-- rfc.py:fixtures:start -->
<p class="rigor-backlink"><em>Tested by</em></p>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6IlQwMDExIiwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoidHlwZWNoZWNrX2Vycm9yIn0sImZpbGVzIjpbeyJuYW1lIjoibWFpbi5tdGwiLCJzb3VyY2UiOiJpbXBvcnQgYTo6KjtcbmltcG9ydCBiOjoqO1xuZnVuIG1haW4oKSAtPiBpNjQgeyByZXR1cm4gZm9vKCk7IH1cbiJ9LHsibmFtZSI6ImEubXRsIiwic291cmNlIjoicHVibGljIGZ1biBmb28oKSAtPiBpNjQgeyByZXR1cm4gMTsgfVxuIn0seyJuYW1lIjoiYi5tdGwiLCJzb3VyY2UiOiJwdWJsaWMgZnVuIGZvbygpIC0+IGk2NCB7IHJldHVybiAyOyB9XG4ifV0sImhyZWYiOiJodHRwczovL2dpdGh1Yi5jb20vbWV0ZWwtbGFuZy9tZXRlbC1jb3JlL2Jsb2IvdjAuMTMuMC9tZXRlbC1pbnRlcnByZXRlci90ZXN0cy9pbnRlZ3JhdGlvbi9zb3VyY2VzL21vZHVsZV9zZW1hbnRpY3MvdHdvX2dsb2JfaW1wb3J0c19zYW1lX25hbWVfaXNfdDAwMTEiLCJuYW1lIjoidHdvX2dsb2JfaW1wb3J0c19zYW1lX25hbWVfaXNfdDAwMTEifQ=="></details>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.modules.import-conflicts.legality-3}

An explicit import takes precedence over a glob-imported binding of the same name.

<!-- rfc.py:fixtures:start -->
<p class="rigor-backlink"><em>Tested by</em></p>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoic3VjY2VzcyJ9LCJmaWxlcyI6W3sibmFtZSI6Im1haW4ubXRsIiwic291cmNlIjoiaW1wb3J0IGE6OmZvbztcbmltcG9ydCBiOjoqO1xuZnVuIG1haW4oKSAtPiBpNjQgeyByZXR1cm4gZm9vKCk7IH1cbiJ9LHsibmFtZSI6ImEubXRsIiwic291cmNlIjoicHVibGljIGZ1biBmb28oKSAtPiBpNjQgeyByZXR1cm4gMTsgfVxuIn0seyJuYW1lIjoiYi5tdGwiLCJzb3VyY2UiOiJwdWJsaWMgZnVuIGZvbygpIC0+IGk2NCB7IHJldHVybiAyOyB9XG4ifV0sImhyZWYiOiJodHRwczovL2dpdGh1Yi5jb20vbWV0ZWwtbGFuZy9tZXRlbC1jb3JlL2Jsb2IvdjAuMTMuMC9tZXRlbC1pbnRlcnByZXRlci90ZXN0cy9pbnRlZ3JhdGlvbi9zb3VyY2VzL21vZHVsZV9zZW1hbnRpY3MvZXhwbGljaXRfaW1wb3J0X3dpbnNfb3Zlcl9nbG9iX3NhbWVfbmFtZSIsIm5hbWUiOiJleHBsaWNpdF9pbXBvcnRfd2luc19vdmVyX2dsb2Jfc2FtZV9uYW1lIn0="></details>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.modules.import-conflicts.legality-4}

Import conflicts follow their binding kind: duplicate explicit imports fail immediately,
ambiguous user-glob names fail when referenced, and an explicit import disambiguates a
glob-provided name.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0030](../../rfcs/4-implemented/rfc-0030-module-system-redesign.md), [rfc-0031](../../rfcs/4-implemented/rfc-0031-topological-typechecker.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<p class="rigor-backlink"><em>Tested by</em></p>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoic3VjY2VzcyJ9LCJmaWxlcyI6W3sibmFtZSI6Im1haW4ubXRsIiwic291cmNlIjoiaW1wb3J0IGE6OmZvbztcbmltcG9ydCBiOjoqO1xuZnVuIG1haW4oKSAtPiBpNjQgeyByZXR1cm4gZm9vKCk7IH1cbiJ9LHsibmFtZSI6ImEubXRsIiwic291cmNlIjoicHVibGljIGZ1biBmb28oKSAtPiBpNjQgeyByZXR1cm4gMTsgfVxuIn0seyJuYW1lIjoiYi5tdGwiLCJzb3VyY2UiOiJwdWJsaWMgZnVuIGZvbygpIC0+IGk2NCB7IHJldHVybiAyOyB9XG4ifV0sImhyZWYiOiJodHRwczovL2dpdGh1Yi5jb20vbWV0ZWwtbGFuZy9tZXRlbC1jb3JlL2Jsb2IvdjAuMTMuMC9tZXRlbC1pbnRlcnByZXRlci90ZXN0cy9pbnRlZ3JhdGlvbi9zb3VyY2VzL21vZHVsZV9zZW1hbnRpY3MvZXhwbGljaXRfaW1wb3J0X3dpbnNfb3Zlcl9nbG9iX3NhbWVfbmFtZSIsIm5hbWUiOiJleHBsaWNpdF9pbXBvcnRfd2luc19vdmVyX2dsb2Jfc2FtZV9uYW1lIn0="></details>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6IlQwMDExIiwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoidHlwZWNoZWNrX2Vycm9yIn0sImZpbGVzIjpbeyJuYW1lIjoibWFpbi5tdGwiLCJzb3VyY2UiOiJpbXBvcnQgYTo6Zm9vO1xuaW1wb3J0IGI6OmZvbztcbmZ1biBtYWluKCkgLT4gaTY0IHsgcmV0dXJuIGZvbygpOyB9XG4ifSx7Im5hbWUiOiJhLm10bCIsInNvdXJjZSI6InB1YmxpYyBmdW4gZm9vKCkgLT4gaTY0IHsgcmV0dXJuIDE7IH1cbiJ9LHsibmFtZSI6ImIubXRsIiwic291cmNlIjoicHVibGljIGZ1biBmb28oKSAtPiBpNjQgeyByZXR1cm4gMjsgfVxuIn1dLCJocmVmIjoiaHR0cHM6Ly9naXRodWIuY29tL21ldGVsLWxhbmcvbWV0ZWwtY29yZS9ibG9iL3YwLjEzLjAvbWV0ZWwtaW50ZXJwcmV0ZXIvdGVzdHMvaW50ZWdyYXRpb24vc291cmNlcy9tb2R1bGVfc2VtYW50aWNzL3R3b19leHBsaWNpdF9pbXBvcnRzX3NhbWVfbG9jYWxfbmFtZV9pc190MDAxMSIsIm5hbWUiOiJ0d29fZXhwbGljaXRfaW1wb3J0c19zYW1lX2xvY2FsX25hbWVfaXNfdDAwMTEifQ=="></details>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6IlQwMDExIiwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoidHlwZWNoZWNrX2Vycm9yIn0sImZpbGVzIjpbeyJuYW1lIjoibWFpbi5tdGwiLCJzb3VyY2UiOiJpbXBvcnQgYTo6KjtcbmltcG9ydCBiOjoqO1xuZnVuIG1haW4oKSAtPiBpNjQgeyByZXR1cm4gZm9vKCk7IH1cbiJ9LHsibmFtZSI6ImEubXRsIiwic291cmNlIjoicHVibGljIGZ1biBmb28oKSAtPiBpNjQgeyByZXR1cm4gMTsgfVxuIn0seyJuYW1lIjoiYi5tdGwiLCJzb3VyY2UiOiJwdWJsaWMgZnVuIGZvbygpIC0+IGk2NCB7IHJldHVybiAyOyB9XG4ifV0sImhyZWYiOiJodHRwczovL2dpdGh1Yi5jb20vbWV0ZWwtbGFuZy9tZXRlbC1jb3JlL2Jsb2IvdjAuMTMuMC9tZXRlbC1pbnRlcnByZXRlci90ZXN0cy9pbnRlZ3JhdGlvbi9zb3VyY2VzL21vZHVsZV9zZW1hbnRpY3MvdHdvX2dsb2JfaW1wb3J0c19zYW1lX25hbWVfaXNfdDAwMTEiLCJuYW1lIjoidHdvX2dsb2JfaW1wb3J0c19zYW1lX25hbWVfaXNfdDAwMTEifQ=="></details>
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
    let token := Token { kind = 0, span = 1 };
    let state := InternalState { count = 2 };
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
struct field is accessible outside that module only when both the field itself and its
enclosing struct are public. A `public` field on a struct that is not itself `public`
never becomes reachable across a module boundary, regardless of how a value of that
struct's type was obtained (e.g. returned from a public function that never names the
struct type itself).

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0030](../../rfcs/4-implemented/rfc-0030-module-system-redesign.md), [rfc-0031](../../rfcs/4-implemented/rfc-0031-topological-typechecker.md), [rfc-0032](../../rfcs/4-implemented/rfc-0032-field-level-visibility.md), [rfc-0098](../../rfcs/4-implemented/rfc-0098-surface-keyword-renames.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<p class="rigor-backlink"><em>Tested by</em></p>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6IlQwMDA5IiwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoidHlwZWNoZWNrX2Vycm9yIn0sImZpbGVzIjpbeyJuYW1lIjoibWFpbi5tdGwiLCJzb3VyY2UiOiJpbXBvcnQgaGVscGVyOjpzZWNyZXQ7XG5mdW4gbWFpbigpIC0+IGk2NCB7IHJldHVybiBzZWNyZXQoKTsgfVxuIn0seyJuYW1lIjoiaGVscGVyLm10bCIsInNvdXJjZSI6ImZ1biBzZWNyZXQoKSAtPiBpNjQgeyByZXR1cm4gNDI7IH1cbiJ9XSwiaHJlZiI6Imh0dHBzOi8vZ2l0aHViLmNvbS9tZXRlbC1sYW5nL21ldGVsLWNvcmUvYmxvYi92MC4xMy4wL21ldGVsLWludGVycHJldGVyL3Rlc3RzL2ludGVncmF0aW9uL3NvdXJjZXMvbW9kdWxlX3NlbWFudGljcy9pbXBvcnRpbmdfcHJpdmF0ZV9pdGVtX2lzX3QwMDA5IiwibmFtZSI6ImltcG9ydGluZ19wcml2YXRlX2l0ZW1faXNfdDAwMDkifQ=="></details>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoic3VjY2VzcyJ9LCJmaWxlcyI6W3sibmFtZSI6Im1haW4ubXRsIiwic291cmNlIjoiaW1wb3J0IHRva2VuOjptYWtlO1xuZnVuIG1haW4oKSAtPiBpNjQgeyBsZXQgdCA6PSBtYWtlKCk7IHJldHVybiB0LmtpbmQ7IH1cbiJ9LHsibmFtZSI6InRva2VuLm10bCIsInNvdXJjZSI6InB1YmxpYyBzdHJ1Y3QgVG9rZW4geyBwdWJsaWMga2luZDogaTY0LCBvZmZzZXQ6IGk2NCB9XG5wdWJsaWMgZnVuIG1ha2UoKSAtPiBUb2tlbiB7IHJldHVybiBUb2tlbiB7IGtpbmQgPSAxMSwgb2Zmc2V0ID0gNyB9OyB9XG4ifV0sImhyZWYiOiJodHRwczovL2dpdGh1Yi5jb20vbWV0ZWwtbGFuZy9tZXRlbC1jb3JlL2Jsb2IvdjAuMTMuMC9tZXRlbC1pbnRlcnByZXRlci90ZXN0cy9pbnRlZ3JhdGlvbi9zb3VyY2VzL21vZHVsZV9zZW1hbnRpY3MvbWl4ZWRfdmlzaWJpbGl0eV9zdHJ1Y3RfYWxsb3dzX3B1YmxpY19maWVsZF9hY2Nlc3NfYWNyb3NzX21vZHVsZXMiLCJuYW1lIjoibWl4ZWRfdmlzaWJpbGl0eV9zdHJ1Y3RfYWxsb3dzX3B1YmxpY19maWVsZF9hY2Nlc3NfYWNyb3NzX21vZHVsZXMifQ=="></details>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6IlQwMDA5IiwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoidHlwZWNoZWNrX2Vycm9yIn0sImZpbGVzIjpbeyJuYW1lIjoibWFpbi5tdGwiLCJzb3VyY2UiOiIvLyAjNzc2OiBgcHVibGljYCBvbiBhIGZpZWxkIGlzIGNvbmRpdGlvbmFsIG9uIHRoZSBlbmNsb3Npbmcgc3RydWN0J3Mgb3duXG4vLyB2aXNpYmlsaXR5LCBub3QgYW4gaW5kZXBlbmRlbnQgZ3JhbnQuIGBTZWNyZXRgIGlzIG5vdCBgcHVibGljYCwgc28gaXRzXG4vLyBgcHVibGljIHZhbHVlOiBpNjRgIGZpZWxkIG11c3Qgc3RheSB1bnJlYWNoYWJsZSBhY3Jvc3MgYSBtb2R1bGUgYm91bmRhcnlcbi8vIGV2ZW4gb25jZSBhIGBTZWNyZXRgIGlzIG9idGFpbmVkIHZpYSBgbWFrZSgpYCwgYSBwdWJsaWMgZnVuY3Rpb24gdGhhdFxuLy8gbmV2ZXIgbmFtZXMgYFNlY3JldGAgaXRzZWxmLlxuaW1wb3J0IHRva2VuOjptYWtlO1xuZnVuIG1haW4oKSAtPiBpNjQge1xuICAgIGxldCBzIDo9IG1ha2UoKTtcbiAgICByZXR1cm4gcy52YWx1ZTtcbn1cbiJ9LHsibmFtZSI6InRva2VuLm10bCIsInNvdXJjZSI6InN0cnVjdCBTZWNyZXQgeyBwdWJsaWMgdmFsdWU6IGk2NCB9XG5wdWJsaWMgZnVuIG1ha2UoKSAtPiBTZWNyZXQgeyByZXR1cm4gU2VjcmV0IHsgdmFsdWUgPSA0MiB9OyB9XG4ifV0sImhyZWYiOiJodHRwczovL2dpdGh1Yi5jb20vbWV0ZWwtbGFuZy9tZXRlbC1jb3JlL2Jsb2IvdjAuMTMuMC9tZXRlbC1pbnRlcnByZXRlci90ZXN0cy9pbnRlZ3JhdGlvbi9zb3VyY2VzL21vZHVsZV9zZW1hbnRpY3MvcHVibGljX2ZpZWxkX29uX3ByaXZhdGVfc3RydWN0X2Fjcm9zc19tb2R1bGVzX2lzX3QwMDA5IiwibmFtZSI6InB1YmxpY19maWVsZF9vbl9wcml2YXRlX3N0cnVjdF9hY3Jvc3NfbW9kdWxlc19pc190MDAwOSJ9"></details>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.modules.visibility.legality-2}

A public function declaration must carry the explicit type annotations required for its
public API; an omitted required annotation is `T0010`.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0031](../../rfcs/4-implemented/rfc-0031-topological-typechecker.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<p class="rigor-backlink"><em>Tested by</em></p>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6IlQwMDEwIiwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoidHlwZWNoZWNrX2Vycm9yIn0sImZpbGVzIjpbeyJuYW1lIjoibWFpbi5tdGwiLCJzb3VyY2UiOiJpbXBvcnQgaGVscGVyOjoqO1xuZnVuIG1haW4oKSAtPiBpNjQgeyByZXR1cm4gYW5zd2VyKCk7IH1cbiJ9LHsibmFtZSI6ImhlbHBlci5tdGwiLCJzb3VyY2UiOiJwdWJsaWMgZnVuIGFuc3dlcigpIHsgcmV0dXJuIDQyOyB9XG4ifV0sImhyZWYiOiJodHRwczovL2dpdGh1Yi5jb20vbWV0ZWwtbGFuZy9tZXRlbC1jb3JlL2Jsb2IvdjAuMTMuMC9tZXRlbC1pbnRlcnByZXRlci90ZXN0cy9pbnRlZ3JhdGlvbi9zb3VyY2VzL21vZHVsZV9zZW1hbnRpY3MvcHViX2Z1bl93aXRob3V0X3JldHVybl90eXBlX2lzX3QwMDEwIiwibmFtZSI6InB1Yl9mdW5fd2l0aG91dF9yZXR1cm5fdHlwZV9pc190MDAxMCJ9"></details>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.modules.visibility.legality-3}

Reading or assigning a private struct field from outside its declaring module is
rejected with `T0009`. The declaring module retains access to all of its own fields,
including private ones.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0032](../../rfcs/4-implemented/rfc-0032-field-level-visibility.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<p class="rigor-backlink"><em>Tested by</em></p>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6IlQwMDA5IiwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoidHlwZWNoZWNrX2Vycm9yIn0sImZpbGVzIjpbeyJuYW1lIjoibWFpbi5tdGwiLCJzb3VyY2UiOiJpbXBvcnQgdG9rZW46Om1ha2U7XG5mdW4gbWFpbigpIC0+IGk2NCB7IHJldHVybiBtYWtlKCkub2Zmc2V0OyB9XG4ifSx7Im5hbWUiOiJ0b2tlbi5tdGwiLCJzb3VyY2UiOiJwdWJsaWMgc3RydWN0IFRva2VuIHsgcHVibGljIGtpbmQ6IGk2NCwgb2Zmc2V0OiBpNjQgfVxucHVibGljIGZ1biBtYWtlKCkgLT4gVG9rZW4geyByZXR1cm4gVG9rZW4geyBraW5kID0gMSwgb2Zmc2V0ID0gNyB9OyB9XG4ifV0sImhyZWYiOiJodHRwczovL2dpdGh1Yi5jb20vbWV0ZWwtbGFuZy9tZXRlbC1jb3JlL2Jsb2IvdjAuMTMuMC9tZXRlbC1pbnRlcnByZXRlci90ZXN0cy9pbnRlZ3JhdGlvbi9zb3VyY2VzL21vZHVsZV9zZW1hbnRpY3MvcHJpdmF0ZV9zdHJ1Y3RfZmllbGRfYWNjZXNzX2Fjcm9zc19tb2R1bGVzX2lzX3QwMDA5IiwibmFtZSI6InByaXZhdGVfc3RydWN0X2ZpZWxkX2FjY2Vzc19hY3Jvc3NfbW9kdWxlc19pc190MDAwOSJ9"></details>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6IlQwMDA5IiwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoidHlwZWNoZWNrX2Vycm9yIn0sImZpbGVzIjpbeyJuYW1lIjoibWFpbi5tdGwiLCJzb3VyY2UiOiJpbXBvcnQgdG9rZW46Om1ha2U7XG5mdW4gbWFpbigpIC0+IGk2NCB7IHZhciB0IDo9IG1ha2UoKTsgdC5vZmZzZXQgOj0gOTsgcmV0dXJuIHQua2luZDsgfVxuIn0seyJuYW1lIjoidG9rZW4ubXRsIiwic291cmNlIjoicHVibGljIHN0cnVjdCBUb2tlbiB7IHB1YmxpYyBraW5kOiBpNjQsIG9mZnNldDogaTY0IH1cbnB1YmxpYyBmdW4gbWFrZSgpIC0+IFRva2VuIHsgcmV0dXJuIFRva2VuIHsga2luZCA9IDEsIG9mZnNldCA9IDcgfTsgfVxuIn1dLCJocmVmIjoiaHR0cHM6Ly9naXRodWIuY29tL21ldGVsLWxhbmcvbWV0ZWwtY29yZS9ibG9iL3YwLjEzLjAvbWV0ZWwtaW50ZXJwcmV0ZXIvdGVzdHMvaW50ZWdyYXRpb24vc291cmNlcy9tb2R1bGVfc2VtYW50aWNzL3ByaXZhdGVfc3RydWN0X2ZpZWxkX2Fzc2lnbm1lbnRfYWNyb3NzX21vZHVsZXNfaXNfdDAwMDkiLCJuYW1lIjoicHJpdmF0ZV9zdHJ1Y3RfZmllbGRfYXNzaWdubWVudF9hY3Jvc3NfbW9kdWxlc19pc190MDAwOSJ9"></details>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoic3VjY2VzcyJ9LCJmaWxlcyI6W3sibmFtZSI6Im1haW4ubXRsIiwic291cmNlIjoicHVibGljIHN0cnVjdCBUb2tlbiB7IHB1YmxpYyBraW5kOiBpNjQsIG9mZnNldDogaTY0IH1cbiAgICAgICAgIGZ1biBvZmZzZXRfb2YodDogVG9rZW4pIC0+IGk2NCB7IHJldHVybiB0Lm9mZnNldDsgfVxuICAgICAgICAgZnVuIG1haW4oKSAtPiBpNjQgeyBsZXQgdCA6PSBUb2tlbiB7IGtpbmQgPSAzLCBvZmZzZXQgPSA5IH07IHJldHVybiBvZmZzZXRfb2YodCk7IH1cbiJ9XSwiaHJlZiI6Imh0dHBzOi8vZ2l0aHViLmNvbS9tZXRlbC1sYW5nL21ldGVsLWNvcmUvYmxvYi92MC4xMy4wL21ldGVsLWludGVycHJldGVyL3Rlc3RzL2ludGVncmF0aW9uL3NvdXJjZXMvbW9kdWxlX3NlbWFudGljcy9wcml2YXRlX3N0cnVjdF9maWVsZHNfcmVtYWluX2FjY2Vzc2libGVfaW5zaWRlX2RlY2xhcmluZ19tb2R1bGUiLCJuYW1lIjoicHJpdmF0ZV9zdHJ1Y3RfZmllbGRzX3JlbWFpbl9hY2Nlc3NpYmxlX2luc2lkZV9kZWNsYXJpbmdfbW9kdWxlIn0="></details>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.modules.visibility.legality-4}

Constructing a struct literal outside its declaring module is rejected with `T0009` if
it names any private field. A module-local constructor or helper function may still
construct the value.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0032](../../rfcs/4-implemented/rfc-0032-field-level-visibility.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<p class="rigor-backlink"><em>Tested by</em></p>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6IlQwMDA5IiwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoidHlwZWNoZWNrX2Vycm9yIn0sImZpbGVzIjpbeyJuYW1lIjoibWFpbi5tdGwiLCJzb3VyY2UiOiJpbXBvcnQgdG9rZW46OlRva2VuO1xuZnVuIG1haW4oKSB7IGxldCB0IDo9IFRva2VuIHsga2luZCA9IDEsIG9mZnNldCA9IDcgfTsgcHJpbnQodC5raW5kKTsgfVxuIn0seyJuYW1lIjoidG9rZW4ubXRsIiwic291cmNlIjoicHVibGljIHN0cnVjdCBUb2tlbiB7IHB1YmxpYyBraW5kOiBpNjQsIG9mZnNldDogaTY0IH1cbiJ9XSwiaHJlZiI6Imh0dHBzOi8vZ2l0aHViLmNvbS9tZXRlbC1sYW5nL21ldGVsLWNvcmUvYmxvYi92MC4xMy4wL21ldGVsLWludGVycHJldGVyL3Rlc3RzL2ludGVncmF0aW9uL3NvdXJjZXMvbW9kdWxlX3NlbWFudGljcy9wcml2YXRlX3N0cnVjdF9maWVsZF9jb25zdHJ1Y3Rpb25fYWNyb3NzX21vZHVsZXNfaXNfdDAwMDkiLCJuYW1lIjoicHJpdmF0ZV9zdHJ1Y3RfZmllbGRfY29uc3RydWN0aW9uX2Fjcm9zc19tb2R1bGVzX2lzX3QwMDA5In0="></details>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.modules.visibility.legality-5}

Declaring a field `public` on a struct that is not itself `public` produces a compiler
warning: the field cannot be reached across a module boundary through a private type,
so the `public` marker on it has no effect from outside the declaring module.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0032](../../rfcs/4-implemented/rfc-0032-field-level-visibility.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<p class="rigor-backlink"><em>Tested by</em></p>
<details class="spec-fixture" data-fixture="eyJmaWxlcyI6W3sibmFtZSI6InB1YmxpY19maWVsZF9vbl9wcml2YXRlX3N0cnVjdF93YXJucy5tdGwiLCJzb3VyY2UiOiJzdHJ1Y3QgVGhpbmcge1xuICAgIHB1YmxpYyB2YWx1ZTogaTY0LFxufVxuXG5mdW4gbWFpbigpIHtcbiAgICBsZXQgdCA6PSBUaGluZyB7IHZhbHVlID0gMSB9O1xuICAgIHByaW50bG4odC52YWx1ZS50b19zdHJpbmcoKSk7XG59XG4ifV0sImhyZWYiOiJodHRwczovL2dpdGh1Yi5jb20vbWV0ZWwtbGFuZy9tZXRlbC1jb3JlL2Jsb2IvdjAuMTMuMC9tZXRlbC1pbnRlcnByZXRlci90ZXN0cy9pbnRlZ3JhdGlvbi9zb3VyY2VzL3R5cGVjaGVja2luZy9zdHJ1Y3RzL3B1YmxpY19maWVsZF9vbl9wcml2YXRlX3N0cnVjdF93YXJucy5tdGwiLCJuYW1lIjoicHVibGljX2ZpZWxkX29uX3ByaXZhdGVfc3RydWN0X3dhcm5zLm10bCJ9"></details>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6IlQwMDA5IiwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoidHlwZWNoZWNrX2Vycm9yIn0sImZpbGVzIjpbeyJuYW1lIjoibWFpbi5tdGwiLCJzb3VyY2UiOiIvLyAjNzc2OiBgcHVibGljYCBvbiBhIGZpZWxkIGlzIGNvbmRpdGlvbmFsIG9uIHRoZSBlbmNsb3Npbmcgc3RydWN0J3Mgb3duXG4vLyB2aXNpYmlsaXR5LCBub3QgYW4gaW5kZXBlbmRlbnQgZ3JhbnQuIGBTZWNyZXRgIGlzIG5vdCBgcHVibGljYCwgc28gaXRzXG4vLyBgcHVibGljIHZhbHVlOiBpNjRgIGZpZWxkIG11c3Qgc3RheSB1bnJlYWNoYWJsZSBhY3Jvc3MgYSBtb2R1bGUgYm91bmRhcnlcbi8vIGV2ZW4gb25jZSBhIGBTZWNyZXRgIGlzIG9idGFpbmVkIHZpYSBgbWFrZSgpYCwgYSBwdWJsaWMgZnVuY3Rpb24gdGhhdFxuLy8gbmV2ZXIgbmFtZXMgYFNlY3JldGAgaXRzZWxmLlxuaW1wb3J0IHRva2VuOjptYWtlO1xuZnVuIG1haW4oKSAtPiBpNjQge1xuICAgIGxldCBzIDo9IG1ha2UoKTtcbiAgICByZXR1cm4gcy52YWx1ZTtcbn1cbiJ9LHsibmFtZSI6InRva2VuLm10bCIsInNvdXJjZSI6InN0cnVjdCBTZWNyZXQgeyBwdWJsaWMgdmFsdWU6IGk2NCB9XG5wdWJsaWMgZnVuIG1ha2UoKSAtPiBTZWNyZXQgeyByZXR1cm4gU2VjcmV0IHsgdmFsdWUgPSA0MiB9OyB9XG4ifV0sImhyZWYiOiJodHRwczovL2dpdGh1Yi5jb20vbWV0ZWwtbGFuZy9tZXRlbC1jb3JlL2Jsb2IvdjAuMTMuMC9tZXRlbC1pbnRlcnByZXRlci90ZXN0cy9pbnRlZ3JhdGlvbi9zb3VyY2VzL21vZHVsZV9zZW1hbnRpY3MvcHVibGljX2ZpZWxkX29uX3ByaXZhdGVfc3RydWN0X2Fjcm9zc19tb2R1bGVzX2lzX3QwMDA5IiwibmFtZSI6InB1YmxpY19maWVsZF9vbl9wcml2YXRlX3N0cnVjdF9hY3Jvc3NfbW9kdWxlc19pc190MDAwOSJ9"></details>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.modules.visibility.legality-6}

Named fields of an enum struct-like variant follow the same visibility rules as an
ordinary struct's fields: constructing a variant literal outside the enum's declaring
module and naming a private field is rejected with `T0009`, the same as for a struct.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0032](../../rfcs/4-implemented/rfc-0032-field-level-visibility.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<p class="rigor-backlink"><em>Tested by</em></p>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6IlQwMDA5IiwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoidHlwZWNoZWNrX2Vycm9yIn0sImZpbGVzIjpbeyJuYW1lIjoibWFpbi5tdGwiLCJzb3VyY2UiOiJpbXBvcnQgdG9rZW46OlRva2VuO1xuZnVuIG1haW4oKSB7IGxldCB0IDo9IFRva2VuOjpJbm5lciB7IGtpbmQgPSAxLCBvZmZzZXQgPSA3IH07IH1cbiJ9LHsibmFtZSI6InRva2VuLm10bCIsInNvdXJjZSI6InB1YmxpYyBlbnVtIFRva2VuIHsgSW5uZXIgeyBwdWJsaWMga2luZDogaTY0LCBvZmZzZXQ6IGk2NCB9IH1cbiJ9XSwiaHJlZiI6Imh0dHBzOi8vZ2l0aHViLmNvbS9tZXRlbC1sYW5nL21ldGVsLWNvcmUvYmxvYi92MC4xMy4wL21ldGVsLWludGVycHJldGVyL3Rlc3RzL2ludGVncmF0aW9uL3NvdXJjZXMvbW9kdWxlX3NlbWFudGljcy9wcml2YXRlX2VudW1fdmFyaWFudF9maWVsZF9jb25zdHJ1Y3Rpb25fYWNyb3NzX21vZHVsZXNfaXNfdDAwMDkiLCJuYW1lIjoicHJpdmF0ZV9lbnVtX3ZhcmlhbnRfZmllbGRfY29uc3RydWN0aW9uX2Fjcm9zc19tb2R1bGVzX2lzX3QwMDA5In0="></details>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.modules.visibility.legality-7}

Naming a private field in a struct pattern from outside the struct's declaring module is
rejected with `T0009`. The pattern must either omit that field with a trailing `..`, or
be written inside the declaring module, where private fields remain nameable.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0032](../../rfcs/4-implemented/rfc-0032-field-level-visibility.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<p class="rigor-backlink"><em>Tested by</em></p>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6IlQwMDA5IiwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6IjciLCJzdGF0dXMiOiJ0eXBlY2hlY2tfZXJyb3IifSwiZmlsZXMiOlt7Im5hbWUiOiJtYWluLm10bCIsInNvdXJjZSI6ImltcG9ydCB0b2tlbjo6VG9rZW47XG5pbXBvcnQgdG9rZW46Om1ha2VfdG9rZW47XG5cbmZ1biBtYWluKCkge1xuICAgIGxldCB0IDo9IG1ha2VfdG9rZW4oMSwgMik7XG4gICAgbGV0IHggOj0gbWF0Y2ggKHQpIHtcbiAgICAgICAgVG9rZW4geyBraW5kLCBvZmZzZXQgfSA9PiBraW5kICsgb2Zmc2V0LFxuICAgIH07XG4gICAgcHJpbnRsbih4KTtcbn1cbiJ9LHsibmFtZSI6InRva2VuLm10bCIsInNvdXJjZSI6InB1YmxpYyBzdHJ1Y3QgVG9rZW4geyBwdWJsaWMga2luZDogaTY0LCBvZmZzZXQ6IGk2NCB9XG5cbnB1YmxpYyBmdW4gbWFrZV90b2tlbihraW5kOiBpNjQsIG9mZnNldDogaTY0KSAtPiBUb2tlbiB7XG4gICAgcmV0dXJuIFRva2VuIHsga2luZCA9IGtpbmQsIG9mZnNldCA9IG9mZnNldCB9O1xufVxuIn1dLCJocmVmIjoiaHR0cHM6Ly9naXRodWIuY29tL21ldGVsLWxhbmcvbWV0ZWwtY29yZS9ibG9iL3YwLjEzLjAvbWV0ZWwtaW50ZXJwcmV0ZXIvdGVzdHMvaW50ZWdyYXRpb24vc291cmNlcy9tb2R1bGVfc2VtYW50aWNzL3N0cnVjdF9wYXR0ZXJuX25hbWVzX3ByaXZhdGVfZmllbGRfYWNyb3NzX21vZHVsZXNfaXNfdDAwMDkiLCJuYW1lIjoic3RydWN0X3BhdHRlcm5fbmFtZXNfcHJpdmF0ZV9maWVsZF9hY3Jvc3NfbW9kdWxlc19pc190MDAwOSJ9"></details>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoic3VjY2VzcyJ9LCJmaWxlcyI6W3sibmFtZSI6Im1haW4ubXRsIiwic291cmNlIjoiaW1wb3J0IHRva2VuOjpUb2tlbjtcbmltcG9ydCB0b2tlbjo6bWFrZV90b2tlbjtcblxuZnVuIG1haW4oKSB7XG4gICAgbGV0IHQgOj0gbWFrZV90b2tlbigxLCAyKTtcbiAgICBsZXQgeCA6PSBtYXRjaCAodCkge1xuICAgICAgICBUb2tlbiB7IGtpbmQsIC4uIH0gPT4ga2luZCxcbiAgICB9O1xuICAgIHByaW50bG4oeCk7XG59XG4ifSx7Im5hbWUiOiJ0b2tlbi5tdGwiLCJzb3VyY2UiOiJwdWJsaWMgc3RydWN0IFRva2VuIHsgcHVibGljIGtpbmQ6IGk2NCwgb2Zmc2V0OiBpNjQgfVxuXG5wdWJsaWMgZnVuIG1ha2VfdG9rZW4oa2luZDogaTY0LCBvZmZzZXQ6IGk2NCkgLT4gVG9rZW4ge1xuICAgIHJldHVybiBUb2tlbiB7IGtpbmQgPSBraW5kLCBvZmZzZXQgPSBvZmZzZXQgfTtcbn1cbiJ9XSwiaHJlZiI6Imh0dHBzOi8vZ2l0aHViLmNvbS9tZXRlbC1sYW5nL21ldGVsLWNvcmUvYmxvYi92MC4xMy4wL21ldGVsLWludGVycHJldGVyL3Rlc3RzL2ludGVncmF0aW9uL3NvdXJjZXMvbW9kdWxlX3NlbWFudGljcy9zdHJ1Y3RfcGF0dGVybl9yZXN0X29taXRzX3ByaXZhdGVfZmllbGRfYWNyb3NzX21vZHVsZXMiLCJuYW1lIjoic3RydWN0X3BhdHRlcm5fcmVzdF9vbWl0c19wcml2YXRlX2ZpZWxkX2Fjcm9zc19tb2R1bGVzIn0="></details>
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
<p class="rigor-backlink"><em>Tested by</em></p>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6ImNhbm5vdCBmaW5kIG1vZHVsZSIsImxpbmUiOm51bGwsInN0YXR1cyI6ImxvYWRfZXJyb3IifSwiZmlsZXMiOlt7Im5hbWUiOiJtYWluLm10bCIsInNvdXJjZSI6ImltcG9ydCBub25leGlzdGVudDo6VGhpbmc7XG5mdW4gbWFpbigpIC0+IGk2NCB7IHJldHVybiBUaGluZygpOyB9XG4ifV0sImhyZWYiOiJodHRwczovL2dpdGh1Yi5jb20vbWV0ZWwtbGFuZy9tZXRlbC1jb3JlL2Jsb2IvdjAuMTMuMC9tZXRlbC1pbnRlcnByZXRlci90ZXN0cy9pbnRlZ3JhdGlvbi9zb3VyY2VzL21vZHVsZV9sb2FkaW5nL2ltcG9ydF9ub25leGlzdGVudF9tb2R1bGVfaXNfYV9sb2FkX2Vycm9yIiwibmFtZSI6ImltcG9ydF9ub25leGlzdGVudF9tb2R1bGVfaXNfYV9sb2FkX2Vycm9yIn0="></details>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.modules.module-graph-loading.legality-2}

Imports and re-exports both contribute module-graph edges. Missing modules and circular
dependencies are load errors, and a bare re-export loads its target module.

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0030](../../rfcs/4-implemented/rfc-0030-module-system-redesign.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<p class="rigor-backlink"><em>Tested by</em></p>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6ImNhbm5vdCBmaW5kIG1vZHVsZSIsImxpbmUiOm51bGwsInN0YXR1cyI6ImxvYWRfZXJyb3IifSwiZmlsZXMiOlt7Im5hbWUiOiJtYWluLm10bCIsInNvdXJjZSI6ImltcG9ydCBub25leGlzdGVudDo6VGhpbmc7XG5mdW4gbWFpbigpIC0+IGk2NCB7IHJldHVybiBUaGluZygpOyB9XG4ifV0sImhyZWYiOiJodHRwczovL2dpdGh1Yi5jb20vbWV0ZWwtbGFuZy9tZXRlbC1jb3JlL2Jsb2IvdjAuMTMuMC9tZXRlbC1pbnRlcnByZXRlci90ZXN0cy9pbnRlZ3JhdGlvbi9zb3VyY2VzL21vZHVsZV9sb2FkaW5nL2ltcG9ydF9ub25leGlzdGVudF9tb2R1bGVfaXNfYV9sb2FkX2Vycm9yIiwibmFtZSI6ImltcG9ydF9ub25leGlzdGVudF9tb2R1bGVfaXNfYV9sb2FkX2Vycm9yIn0="></details>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6ImNpcmN1bGFyIG1vZHVsZSBkZXBlbmRlbmN5IiwibGluZSI6bnVsbCwic3RhdHVzIjoibG9hZF9lcnJvciJ9LCJmaWxlcyI6W3sibmFtZSI6Im1haW4ubXRsIiwic291cmNlIjoiaW1wb3J0IGE6OlRoaW5nO1xuZnVuIG1haW4oKSB7IH1cbiJ9LHsibmFtZSI6ImEubXRsIiwic291cmNlIjoiaW1wb3J0IGI6Ok90aGVyO1xuIn0seyJuYW1lIjoiYi5tdGwiLCJzb3VyY2UiOiJpbXBvcnQgYTo6VGhpbmc7XG4ifV0sImhyZWYiOiJodHRwczovL2dpdGh1Yi5jb20vbWV0ZWwtbGFuZy9tZXRlbC1jb3JlL2Jsb2IvdjAuMTMuMC9tZXRlbC1pbnRlcnByZXRlci90ZXN0cy9pbnRlZ3JhdGlvbi9zb3VyY2VzL21vZHVsZV9sb2FkaW5nL3JlamVjdHNfY2lyY3VsYXJfbW9kdWxlX2dyYXBoIiwibmFtZSI6InJlamVjdHNfY2lyY3VsYXJfbW9kdWxlX2dyYXBoIn0="></details>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoic3VjY2VzcyJ9LCJmaWxlcyI6W3sibmFtZSI6Im1haW4ubXRsIiwic291cmNlIjoiaW1wb3J0IGZhY2FkZTo6YW5zd2VyO1xuZnVuIG1haW4oKSAtPiBpNjQgeyBhbnN3ZXIoKSB9XG4ifSx7Im5hbWUiOiJmYWNhZGUubXRsIiwic291cmNlIjoiZXhwb3J0IGhlbHBlcjo6YW5zd2VyO1xuIn0seyJuYW1lIjoiaGVscGVyLm10bCIsInNvdXJjZSI6InB1YmxpYyBmdW4gYW5zd2VyKCkgLT4gaTY0IHsgNDIgfVxuIn1dLCJocmVmIjoiaHR0cHM6Ly9naXRodWIuY29tL21ldGVsLWxhbmcvbWV0ZWwtY29yZS9ibG9iL3YwLjEzLjAvbWV0ZWwtaW50ZXJwcmV0ZXIvdGVzdHMvaW50ZWdyYXRpb24vc291cmNlcy9tb2R1bGVfc2VtYW50aWNzL3JmYzAwMzBfYmFyZV9leHBvcnRfbG9hZHNfbW9kdWxlIiwibmFtZSI6InJmYzAwMzBfYmFyZV9leHBvcnRfbG9hZHNfbW9kdWxlIn0="></details>
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
<p class="rigor-backlink"><em>Tested by</em></p>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoic3VjY2VzcyJ9LCJmaWxlcyI6W3sibmFtZSI6Im1haW4ubXRsIiwic291cmNlIjoiZnVuIG1haW4oKSB7IH1cbiJ9XSwiaHJlZiI6Imh0dHBzOi8vZ2l0aHViLmNvbS9tZXRlbC1sYW5nL21ldGVsLWNvcmUvYmxvYi92MC4xMy4wL21ldGVsLWludGVycHJldGVyL3Rlc3RzL2ludGVncmF0aW9uL3NvdXJjZXMvbW9kdWxlX2xvYWRpbmcvc2luZ2xlX2ZpbGVfcHJvZ3JhbV9sb2Fkc193aXRob3V0X21vZHVsZXMiLCJuYW1lIjoic2luZ2xlX2ZpbGVfcHJvZ3JhbV9sb2Fkc193aXRob3V0X21vZHVsZXMifQ=="></details>
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
<p class="rigor-backlink"><em>Tested by</em></p>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6IlAwMDAxIiwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoicGFyc2VfZXJyb3IifSwiZmlsZXMiOlt7Im5hbWUiOiJyZmMwMDMwX2xlZ2FjeV9tb2RfdXNlX3JlamVjdGVkLm10bCIsInNvdXJjZSI6Im1vZCBoZWxwZXI7XG5mdW4gbWFpbigpIC0+IGk2NCB7IDAgfVxuIn1dLCJocmVmIjoiaHR0cHM6Ly9naXRodWIuY29tL21ldGVsLWxhbmcvbWV0ZWwtY29yZS9ibG9iL3YwLjEzLjAvbWV0ZWwtaW50ZXJwcmV0ZXIvdGVzdHMvaW50ZWdyYXRpb24vc291cmNlcy9wYXJzaW5nL3JmYzAwMzBfbGVnYWN5X21vZF91c2VfcmVqZWN0ZWQubXRsIiwibmFtZSI6InJmYzAwMzBfbGVnYWN5X21vZF91c2VfcmVqZWN0ZWQubXRsIn0="></details>
<!-- rfc.py:fixtures:end -->

</details>
