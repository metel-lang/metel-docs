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

> **Gap** GAP-MODULES-002

Each non-prelude module path maps directly to its `.mtl` file path. A facade file and
the same-named directory are distinct paths; `name/mod.mtl` has no special meaning.

<!-- rfc.py:last_reviewed 722a13049df7dd2ba817e781ebbc6bb3689f9d6e -->

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0030](../../rfcs/4-implemented/rfc-0030-module-system-redesign.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<p class="rigor-backlink"><em>Tested by</em></p>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoic3VjY2VzcyJ9LCJmaWxlcyI6W3sibmFtZSI6Im1haW4ubXRsIiwic291cmNlIjoiaW1wb3J0IHBhcnNlcjo6VG9rZW47XG5mdW4gbWFpbigpIHsgfVxuIn0seyJuYW1lIjoicGFyc2VyLm10bCIsInNvdXJjZSI6InN0cnVjdCBUb2tlbiB7IHZhbHVlOiBpNjQgfVxuIn0seyJuYW1lIjoicGFyc2VyL2FzdC5tdGwiLCJzb3VyY2UiOiJwdWJsaWMgc3RydWN0IEFzdCB7IHB1YmxpYyB2YWx1ZTogaTY0IH1cbiJ9XSwiaHJlZiI6Imh0dHBzOi8vZ2l0aHViLmNvbS9tZXRlbC1sYW5nL21ldGVsLWNvcmUvYmxvYi92MC4xNC4xL21ldGVsLWludGVycHJldGVyL3Rlc3RzL2ludGVncmF0aW9uL3NvdXJjZXMvbW9kdWxlX2xvYWRpbmcvZmFjYWRlX21vZHVsZV9hbG9uZ3NpZGVfZGlyZWN0b3J5IiwibmFtZSI6ImZhY2FkZV9tb2R1bGVfYWxvbmdzaWRlX2RpcmVjdG9yeSJ9"></details>
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

<!-- rfc.py:last_reviewed cfff5473333ed9035b5f8fc9ecf285c8fc394a1d -->

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0030](../../rfcs/4-implemented/rfc-0030-module-system-redesign.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<p class="rigor-backlink"><em>Tested by</em></p>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6IlAwMDAxIiwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoicGFyc2VfZXJyb3IifSwiZmlsZXMiOlt7Im5hbWUiOiJyZmMwMDMwX2ltcG9ydF9hZnRlcl9kZWNsYXJhdGlvbi5tdGwiLCJzb3VyY2UiOiJmdW4gbWFpbigpIC0+IGk2NCB7IDAgfVxuaW1wb3J0IGhlbHBlcjo6YW5zd2VyO1xuIn1dLCJocmVmIjoiaHR0cHM6Ly9naXRodWIuY29tL21ldGVsLWxhbmcvbWV0ZWwtY29yZS9ibG9iL3YwLjE0LjEvbWV0ZWwtaW50ZXJwcmV0ZXIvdGVzdHMvaW50ZWdyYXRpb24vc291cmNlcy9wYXJzaW5nL3JmYzAwMzBfaW1wb3J0X2FmdGVyX2RlY2xhcmF0aW9uLm10bCIsIm5hbWUiOiJyZmMwMDMwX2ltcG9ydF9hZnRlcl9kZWNsYXJhdGlvbi5tdGwifQ=="></details>
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

<!-- rfc.py:last_reviewed 722a13049df7dd2ba817e781ebbc6bb3689f9d6e -->

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0030](../../rfcs/4-implemented/rfc-0030-module-system-redesign.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<p class="rigor-backlink"><em>Tested by</em></p>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoic3VjY2VzcyJ9LCJmaWxlcyI6W3sibmFtZSI6Im1haW4ubXRsIiwic291cmNlIjoiaW1wb3J0IHBhcnNlcjo6VG9rZW47XG5mdW4gbWFpbigpIHsgfVxuIn0seyJuYW1lIjoiY2hpbGQubXRsIiwic291cmNlIjoic3RydWN0IFRoaW5nIHsgdmFsdWU6IGk2NCB9XG4ifSx7Im5hbWUiOiJwYXJzZXIubXRsIiwic291cmNlIjoiXG5pbXBvcnQgc2VsZjo6Y2hpbGQ6OlRoaW5nO1xuaW1wb3J0IHJvb3Q6OmNoaWxkOjpUaGluZztcbmltcG9ydCBzdXBlcjo6Y2hpbGQ6OlRoaW5nO1xuaW1wb3J0IHN0ZDo6Y29yZTo6aTY0O1xuaW1wb3J0IGNoaWxkOjpUaGluZztcblxuc3RydWN0IFRva2VuIHsgdmFsdWU6IGk2NCB9XG4ifV0sImhyZWYiOiJodHRwczovL2dpdGh1Yi5jb20vbWV0ZWwtbGFuZy9tZXRlbC1jb3JlL2Jsb2IvdjAuMTQuMS9tZXRlbC1pbnRlcnByZXRlci90ZXN0cy9pbnRlZ3JhdGlvbi9zb3VyY2VzL21vZHVsZV9sb2FkaW5nL2FjY2VwdHNfcm9vdF9zZWxmX3N1cGVyX3N0ZF9hbmRfY2hpbGRfcm9vdHNfaW5fbm9uX3Jvb3RfbW9kdWxlcyIsIm5hbWUiOiJhY2NlcHRzX3Jvb3Rfc2VsZl9zdXBlcl9zdGRfYW5kX2NoaWxkX3Jvb3RzX2luX25vbl9yb290X21vZHVsZXMifQ=="></details>
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

<!-- rfc.py:last_reviewed 8d1f13bf3a5dfa4c0ffa3aac1de385fbb4c73cd1 -->

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0031](../../rfcs/4-implemented/rfc-0031-topological-typechecker.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<details class="rigor-fixtures-toggle" open>
<summary>Tested by (2)</summary>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6IlQwMDAzIiwiY29sIjpudWxsLCJjb250YWlucyI6InVua25vd24gc3RydWN0IGBQYWNrZXRgIiwibGluZSI6bnVsbCwic3RhdHVzIjoidHlwZWNoZWNrX2Vycm9yIn0sImZpbGVzIjpbeyJuYW1lIjoibWFpbi5tdGwiLCJzb3VyY2UiOiJpbXBvcnQgbW9kZWw6OkVtcHR5UGFja2V0O1xuXG5mdW4gdGFrZSh2YWx1ZTogRW1wdHlQYWNrZXQpIC0+IGk2NCB7IHZhbHVlLmlkIH1cbmZ1biBtYWluKCkge1xuICAgIGxldCBmb3JiaWRkZW4gOj0gUGFja2V0IHsgaWQgPSA3LCBkYXRhID0ge30gfTsgLy8gRVJST1JbVDAwMDNdXG59XG4ifSx7Im5hbWUiOiJtb2RlbC5tdGwiLCJzb3VyY2UiOiJwdWJsaWMgcmVjb3JkIFBhY2tldDxyb3cgUj4geyBpZDogaTY0LCBkYXRhOiB7IC4uUiB9IH1cbnB1YmxpYyB0eXBlIEVtcHR5UGFja2V0IDo9IFBhY2tldDx7fT47XG4ifV0sImhyZWYiOiJodHRwczovL2dpdGh1Yi5jb20vbWV0ZWwtbGFuZy9tZXRlbC1jb3JlL2Jsb2IvdjAuMTQuMS9tZXRlbC1pbnRlcnByZXRlci90ZXN0cy9pbnRlZ3JhdGlvbi9zb3VyY2VzL21vZHVsZV9zZW1hbnRpY3MvYWxpYXNfcmhzX2NvbnN0cnVjdG9yX25vdF9pbXBvcnRlZCIsIm5hbWUiOiJhbGlhc19yaHNfY29uc3RydWN0b3Jfbm90X2ltcG9ydGVkIn0="></details>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoic3VjY2VzcyJ9LCJmaWxlcyI6W3sibmFtZSI6Im1haW4ubXRsIiwic291cmNlIjoiaW1wb3J0IGhlbHBlcjo6YW5zd2VyO1xuZnVuIG1haW4oKSAtPiBpNjQgeyByZXR1cm4gYW5zd2VyKCk7IH1cbiJ9LHsibmFtZSI6ImhlbHBlci5tdGwiLCJzb3VyY2UiOiJwdWJsaWMgZnVuIGFuc3dlcigpIC0+IGk2NCB7IHJldHVybiA3OyB9XG4ifV0sImhyZWYiOiJodHRwczovL2dpdGh1Yi5jb20vbWV0ZWwtbGFuZy9tZXRlbC1jb3JlL2Jsb2IvdjAuMTQuMS9tZXRlbC1pbnRlcnByZXRlci90ZXN0cy9pbnRlZ3JhdGlvbi9zb3VyY2VzL21vZHVsZV9zZW1hbnRpY3MvZXhwbGljaXRfbmFtZWRfaW1wb3J0X2Z1bmN0aW9uX2NhbGwiLCJuYW1lIjoiZXhwbGljaXRfbmFtZWRfaW1wb3J0X2Z1bmN0aW9uX2NhbGwifQ=="></details>
</details>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.modules.imports.legality-2}

An aliased import binds only its alias locally. The alias may be used wherever the
imported declaration's kind permits, including as a value, type, or constructor.

<!-- rfc.py:last_reviewed 33d4a37696e073c0581e3e0a4a08a119a20677bd -->

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0031](../../rfcs/4-implemented/rfc-0031-topological-typechecker.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<details class="rigor-fixtures-toggle">
<summary>Tested by (9)</summary>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoidHlwZWNoZWNrX2Vycm9yIn0sImZpbGVzIjpbeyJuYW1lIjoibWFpbi5tdGwiLCJzb3VyY2UiOiJpbXBvcnQgaGVscGVyOjphbnN3ZXIgYXMgY29tcHV0ZTtcbmZ1biBtYWluKCkgLT4gaTY0IHsgcmV0dXJuIGFuc3dlcigpOyB9XG4ifSx7Im5hbWUiOiJoZWxwZXIubXRsIiwic291cmNlIjoicHVibGljIGZ1biBhbnN3ZXIoKSAtPiBpNjQgeyByZXR1cm4gNDI7IH1cbiJ9XSwiaHJlZiI6Imh0dHBzOi8vZ2l0aHViLmNvbS9tZXRlbC1sYW5nL21ldGVsLWNvcmUvYmxvYi92MC4xNC4xL21ldGVsLWludGVycHJldGVyL3Rlc3RzL2ludGVncmF0aW9uL3NvdXJjZXMvbW9kdWxlX3NlbWFudGljcy9hbGlhc19pbXBvcnRfb3JpZ2luYWxfbmFtZV9ub3RfaW5fc2NvcGUiLCJuYW1lIjoiYWxpYXNfaW1wb3J0X29yaWdpbmFsX25hbWVfbm90X2luX3Njb3BlIn0="></details>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoic3VjY2VzcyJ9LCJmaWxlcyI6W3sibmFtZSI6Im1haW4ubXRsIiwic291cmNlIjoiaW1wb3J0IGxleGVyOjpUb2tlbiBhcyBUb2s7XG5cbmZ1biBtYWluKCkge1xuICAgIGxldCBhOiBUb2sgOj0gVG9rIHsgdmFsdWUgPSAxIH07XG4gICAgYXNzZXJ0KGEudmFsdWUgPT0gMSk7XG4gICAgbGV0IGIgOj0gVG9rIHsgdmFsdWUgPSAyIH07XG4gICAgYXNzZXJ0KGIudmFsdWUgPT0gMik7XG59XG4ifSx7Im5hbWUiOiJsZXhlci5tdGwiLCJzb3VyY2UiOiJwdWJsaWMgc3RydWN0IFRva2VuIHsgcHVibGljIHZhbHVlOiBpNjQgfVxuIn1dLCJocmVmIjoiaHR0cHM6Ly9naXRodWIuY29tL21ldGVsLWxhbmcvbWV0ZWwtY29yZS9ibG9iL3YwLjE0LjEvbWV0ZWwtaW50ZXJwcmV0ZXIvdGVzdHMvaW50ZWdyYXRpb24vc291cmNlcy9tb2R1bGVfc2VtYW50aWNzL2FsaWFzX2ltcG9ydF91c2FibGVfYXNfdHlwZV9hbm5vdGF0aW9uX2FuZF9jb25zdHJ1Y3RvciIsIm5hbWUiOiJhbGlhc19pbXBvcnRfdXNhYmxlX2FzX3R5cGVfYW5ub3RhdGlvbl9hbmRfY29uc3RydWN0b3IifQ=="></details>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoic3VjY2VzcyJ9LCJmaWxlcyI6W3sibmFtZSI6Im1haW4ubXRsIiwic291cmNlIjoiLy8gbWV0ZWwtY29yZSMxNTg4OiBhIHZhcmlhbnQgb2YgYW4gYWxpYXNlZCBjb3JlIGVudW0gaXMgYnVpbHQgYWdhaW5zdCB0aGUgYW5ub3RhdGlvbiB0aGF0IHNwZWxsc1xuLy8gdGhlIHNhbWUgZW51bSB0aHJvdWdoIHRoZSBhbGlhcywgc28gdGhlIHR5cGUgcGFyYW1ldGVyIHRoZSB2YXJpYW50IGRvZXMgbm90IGZpeCAoYEVgKSBjb21lcyBmcm9tIGl0LlxuaW1wb3J0IHN0ZDo6Y29yZTo6UmVzdWx0IGFzIENSO1xuXG5mdW4gbWFpbigpIHtcbiAgICBsZXQgb2s6IENSPGk2NCwgU3RyaW5nPiA6PSBDUjo6T2sgeyB2YWx1ZSA9IDEgfTtcbiAgICBsZXQgYmFkOiBDUjxpNjQsIFN0cmluZz4gOj0gQ1I6OkVyciB7IGVycm9yID0gXCJlXCIgfTtcbiAgICBsZXQgYSA6PSBtYXRjaCAob2spIHtcbiAgICAgICAgT2sgeyB2YWx1ZSB9ID0+IHsgdmFsdWUgfSxcbiAgICAgICAgRXJyIHsgZXJyb3IgfSA9PiB7IDAgfSxcbiAgICB9O1xuICAgIGxldCBiIDo9IG1hdGNoIChiYWQpIHtcbiAgICAgICAgT2sgeyB2YWx1ZSB9ID0+IHsgXCJub25lXCIgfSxcbiAgICAgICAgRXJyIHsgZXJyb3IgfSA9PiB7IGVycm9yIH0sXG4gICAgfTtcbiAgICBhc3NlcnQoYSA9PSAxKTtcbiAgICBhc3NlcnQoYiA9PSBcImVcIik7XG59XG4ifV0sImhyZWYiOiJodHRwczovL2dpdGh1Yi5jb20vbWV0ZWwtbGFuZy9tZXRlbC1jb3JlL2Jsb2IvdjAuMTQuMS9tZXRlbC1pbnRlcnByZXRlci90ZXN0cy9pbnRlZ3JhdGlvbi9zb3VyY2VzL21vZHVsZV9zZW1hbnRpY3MvYWxpYXNlZF9jb3JlX2VudW1fY29uc3RydWN0c192YXJpYW50c191bmRlcl9pdHNfYW5ub3RhdGlvbiIsIm5hbWUiOiJhbGlhc2VkX2NvcmVfZW51bV9jb25zdHJ1Y3RzX3ZhcmlhbnRzX3VuZGVyX2l0c19hbm5vdGF0aW9uIn0="></details>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoic3VjY2VzcyJ9LCJmaWxlcyI6W3sibmFtZSI6Im1haW4ubXRsIiwic291cmNlIjoiaW1wb3J0IGZhY2FkZTo6RW1wdHlQYWNrZXQgYXMgRW52ZWxvcGU7XG5pbXBvcnQgZmFjYWRlOjpOdW1lcmljQm94IGFzIENvbnRhaW5lcjtcbmltcG9ydCBtb2RlbDo6e21ha2VfcGFja2V0LCBtYWtlX2JveH07XG5cbnJlY29yZCBQYWNrZXQgeyBpZDogU3RyaW5nIH1cbnN0cnVjdCBCb3ggeyBwdWJsaWMgdmFsdWU6IFN0cmluZyB9XG5mdW4gaW5zcGVjdF9wYWNrZXQocGFja2V0OiBFbnZlbG9wZSkgLT4gaTY0IHsgcGFja2V0LmlkIH1cbmZ1biBpbnNwZWN0X2JveCh2YWx1ZTogQ29udGFpbmVyKSAtPiBpNjQgeyB2YWx1ZS52YWx1ZSB9XG5cbmZ1biBtYWluKCkge1xuICAgIGFzc2VydChpbnNwZWN0X3BhY2tldChtYWtlX3BhY2tldCgpKSA9PSA3KTtcbiAgICBhc3NlcnQoaW5zcGVjdF9ib3gobWFrZV9ib3goKSkgPT0gOSk7XG4gICAgYXNzZXJ0KFBhY2tldCB7IGlkID0gXCJsb2NhbFwiIH0uaWQgPT0gXCJsb2NhbFwiKTtcbiAgICBhc3NlcnQoQm94IHsgdmFsdWUgPSBcImxvY2FsXCIgfS52YWx1ZSA9PSBcImxvY2FsXCIpO1xufVxuIn0seyJuYW1lIjoiZmFjYWRlLm10bCIsInNvdXJjZSI6ImV4cG9ydCBtb2RlbDo6e0VtcHR5UGFja2V0LCBOdW1lcmljQm94fTtcbiJ9LHsibmFtZSI6Im1vZGVsLm10bCIsInNvdXJjZSI6InB1YmxpYyByZWNvcmQgUGFja2V0PHJvdyBSPiB7IGlkOiBpNjQsIGRhdGE6IHsgLi5SIH0gfVxucHVibGljIHR5cGUgRW1wdHlQYWNrZXQgOj0gUGFja2V0PHt9PjtcbnB1YmxpYyBzdHJ1Y3QgQm94PFQ+IHsgcHVibGljIHZhbHVlOiBUIH1cbnB1YmxpYyB0eXBlIE51bWVyaWNCb3ggOj0gQm94PGk2ND47XG5wdWJsaWMgZnVuIG1ha2VfcGFja2V0KCkgLT4gRW1wdHlQYWNrZXQgeyBQYWNrZXQgeyBpZCA9IDcsIGRhdGEgPSB7fSB9IH1cbnB1YmxpYyBmdW4gbWFrZV9ib3goKSAtPiBOdW1lcmljQm94IHsgQm94IHsgdmFsdWUgPSA5IH0gfVxuIn1dLCJocmVmIjoiaHR0cHM6Ly9naXRodWIuY29tL21ldGVsLWxhbmcvbWV0ZWwtY29yZS9ibG9iL3YwLjE0LjEvbWV0ZWwtaW50ZXJwcmV0ZXIvdGVzdHMvaW50ZWdyYXRpb24vc291cmNlcy9tb2R1bGVfc2VtYW50aWNzL2ltcG9ydGVkX25vbWluYWxfYWxpYXNfZGVmaW5pdGlvbl9zY29wZSIsIm5hbWUiOiJpbXBvcnRlZF9ub21pbmFsX2FsaWFzX2RlZmluaXRpb25fc2NvcGUifQ=="></details>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoic3VjY2VzcyJ9LCJmaWxlcyI6W3sibmFtZSI6Im1haW4ubXRsIiwic291cmNlIjoiaW1wb3J0IGhlbHBlcjo6bWFrZV9tZXNzYWdlO1xuaW1wb3J0IGhlbHBlcjo6TWVzc2FnZUNhbGxiYWNrO1xuXG5mdW4gbWFpbigpIHtcbiAgICBsZXQgY2FsbGJhY2s6IE1lc3NhZ2VDYWxsYmFjayA6PSBtYWtlX21lc3NhZ2UoXCJmcm9tIGhlbHBlclwiKTtcbiAgICBhc3NlcnQoY2FsbGJhY2soKSA9PSBcImZyb20gaGVscGVyXCIpO1xufVxuIn0seyJuYW1lIjoiaGVscGVyLm10bCIsInNvdXJjZSI6InB1YmxpYyB0eXBlIE1lc3NhZ2VDYWxsYmFjayA6PSBvbmNlIHx8IC0+IFN0cmluZztcblxucHVibGljIGZ1biBtYWtlX21lc3NhZ2UobWVzc2FnZTogU3RyaW5nKSAtPiBNZXNzYWdlQ2FsbGJhY2sge1xuICAgIFttZXNzYWdlXSBvbmNlIHx8IHsgbWVzc2FnZSB9XG59XG4ifV0sImhyZWYiOiJodHRwczovL2dpdGh1Yi5jb20vbWV0ZWwtbGFuZy9tZXRlbC1jb3JlL2Jsb2IvdjAuMTQuMS9tZXRlbC1pbnRlcnByZXRlci90ZXN0cy9pbnRlZ3JhdGlvbi9zb3VyY2VzL21vZHVsZV9zZW1hbnRpY3MvcmVsZWFzZV9tYXRyaXhfY2xvc3VyZV9jcm9zc19tb2R1bGUiLCJuYW1lIjoicmVsZWFzZV9tYXRyaXhfY2xvc3VyZV9jcm9zc19tb2R1bGUifQ=="></details>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoic3VjY2VzcyJ9LCJmaWxlcyI6W3sibmFtZSI6Im1haW4ubXRsIiwic291cmNlIjoiaW1wb3J0IGxpYjo6e0V2ZW50LCBldmVudHMsIHdlaWdodCwgRG9jLCBtYWtlLCBmaXJzdF9nZW5lcmljfTtcbmZ1biBtYWluKCkge1xuICAgIHZhciB0b3RhbCA6PSAwO1xuICAgIGZvciAoZSBpbiBldmVudHMoKSkgeyB0b3RhbCA6PSB0b3RhbCArIHdlaWdodChlKTsgfVxuICAgIGFzc2VydCh0b3RhbCA9PSAxMCk7XG4gICAgbGV0IGQgOj0gbWFrZSgpO1xuICAgIGxldCB0aXRsZSA6PSBkLnRpdGxlO1xuICAgIGxldCBwYWdlcyA6PSBkLnBhZ2VzO1xuICAgIGFzc2VydCh0aXRsZSA9PSBcInRcIik7XG4gICAgYXNzZXJ0KGZpcnN0X2dlbmVyaWMocGFnZXMpID09IDMpO1xufVxuIn0seyJuYW1lIjoibGliLm10bCIsInNvdXJjZSI6InB1YmxpYyBlbnVtIEV2ZW50IHsgQ2xpY2sgeyB4OiBpNjQsIHk6IGk2NCB9LCBLZXkgeyBjb2RlOiBpNjQgfSB9XG5wdWJsaWMgZnVuIGV2ZW50cygpIC0+IFtFdmVudDsgMl0geyBbRXZlbnQ6OkNsaWNrIHsgeCA9IDEsIHkgPSAyIH0sIEV2ZW50OjpLZXkgeyBjb2RlID0gNyB9XSB9XG5wdWJsaWMgZnVuIHdlaWdodChlOiBFdmVudCkgLT4gaTY0IHtcbiAgICBtYXRjaCAoZSkgeyBFdmVudDo6Q2xpY2sgeyB4LCB5IH0gPT4geCArIHksIEV2ZW50OjpLZXkgeyBjb2RlIH0gPT4gY29kZSB9XG59XG5wdWJsaWMgcmVjb3JkIERvYyB7IHRpdGxlOiBTdHJpbmcsIHBhZ2VzOiBbaTY0OyAyXSB9XG5wdWJsaWMgZnVuIG1ha2UoKSAtPiBEb2MgeyBEb2MgeyB0aXRsZSA9IFwidFwiLnRvX3N0cmluZygpLCBwYWdlcyA9IFszLCA0XSB9IH1cbnB1YmxpYyBmdW4gZmlyc3RfZ2VuZXJpYzxUOiBDb3B5Pih4czogW1Q7IDJdKSAtPiBUIHsgeHNbMF0gfVxuIn1dLCJocmVmIjoiaHR0cHM6Ly9naXRodWIuY29tL21ldGVsLWxhbmcvbWV0ZWwtY29yZS9ibG9iL3YwLjE0LjEvbWV0ZWwtaW50ZXJwcmV0ZXIvdGVzdHMvaW50ZWdyYXRpb24vc291cmNlcy9tb2R1bGVfc2VtYW50aWNzL3JlbGVhc2VfbWF0cml4X2VudW1fYXJyYXlfZ2VuZXJpY19hY3Jvc3NfbW9kdWxlcyIsIm5hbWUiOiJyZWxlYXNlX21hdHJpeF9lbnVtX2FycmF5X2dlbmVyaWNfYWNyb3NzX21vZHVsZXMifQ=="></details>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6IlQwMDA5IiwiY29sIjpudWxsLCJjb250YWlucyI6ImNhbm5vdCBwYXR0ZXJuLW1hdGNoIG9uIHByaXZhdGUgZmllbGQgYHhgIiwibGluZSI6IjUiLCJzdGF0dXMiOiJ0eXBlY2hlY2tfZXJyb3IifSwiZmlsZXMiOlt7Im5hbWUiOiJtYWluLm10bCIsInNvdXJjZSI6ImltcG9ydCBsaWI6OntFdmVudCwgZXZlbnRzfTtcbmZ1biBtYWluKCkge1xuICAgIGZvciAoZSBpbiBldmVudHMoKSkge1xuICAgICAgICBtYXRjaCAoZSkge1xuICAgICAgICAgICAgRXZlbnQ6OkNsaWNrIHsgeCwgeSB9ID0+IGFzc2VydCh4ID09IDEpLCAvLyBFUlJPUltUMDAwOV1cbiAgICAgICAgICAgIEV2ZW50OjpLZXkgeyBjb2RlIH0gPT4gYXNzZXJ0KGNvZGUgPT0gNyksXG4gICAgICAgIH1cbiAgICB9XG59XG4ifSx7Im5hbWUiOiJsaWIubXRsIiwic291cmNlIjoicHVibGljIGVudW0gRXZlbnQgeyBDbGljayB7IHg6IGk2NCwgeTogaTY0IH0sIEtleSB7IGNvZGU6IGk2NCB9IH1cbnB1YmxpYyBmdW4gZXZlbnRzKCkgLT4gW0V2ZW50OyAyXSB7IFtFdmVudDo6Q2xpY2sgeyB4ID0gMSwgeSA9IDIgfSwgRXZlbnQ6OktleSB7IGNvZGUgPSA3IH1dIH1cbnB1YmxpYyBmdW4gd2VpZ2h0KGU6IEV2ZW50KSAtPiBpNjQge1xuICAgIG1hdGNoIChlKSB7IEV2ZW50OjpDbGljayB7IHgsIHkgfSA9PiB4ICsgeSwgRXZlbnQ6OktleSB7IGNvZGUgfSA9PiBjb2RlIH1cbn1cbnB1YmxpYyByZWNvcmQgRG9jIHsgdGl0bGU6IFN0cmluZywgcGFnZXM6IFtpNjQ7IDJdIH1cbnB1YmxpYyBmdW4gbWFrZSgpIC0+IERvYyB7IERvYyB7IHRpdGxlID0gXCJ0XCIudG9fc3RyaW5nKCksIHBhZ2VzID0gWzMsIDRdIH0gfVxucHVibGljIGZ1biBmaXJzdF9nZW5lcmljPFQ6IENvcHk+KHhzOiBbVDsgMl0pIC0+IFQgeyB4c1swXSB9XG4ifV0sImhyZWYiOiJodHRwczovL2dpdGh1Yi5jb20vbWV0ZWwtbGFuZy9tZXRlbC1jb3JlL2Jsb2IvdjAuMTQuMS9tZXRlbC1pbnRlcnByZXRlci90ZXN0cy9pbnRlZ3JhdGlvbi9zb3VyY2VzL21vZHVsZV9zZW1hbnRpY3MvcmVsZWFzZV9tYXRyaXhfZW51bV92YXJpYW50X2ZpZWxkc19wcml2YXRlX2Fjcm9zc19tb2R1bGVzIiwibmFtZSI6InJlbGVhc2VfbWF0cml4X2VudW1fdmFyaWFudF9maWVsZHNfcHJpdmF0ZV9hY3Jvc3NfbW9kdWxlcyJ9"></details>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoic3VjY2VzcyJ9LCJmaWxlcyI6W3sibmFtZSI6Im1haW4ubXRsIiwic291cmNlIjoiaW1wb3J0IG1vZGVsOjpQYWNrZXQ7XG5pbXBvcnQgc3RkOjpjb3JlOjpDbG9uZTtcblxuZnVuIG1haW4oKSB7XG4gICAgbGV0IG9yaWdpbmFsIDo9IFBhY2tldCB7IGlkID0gNywgbmFtZSA9IFwiY3Jvc3MgbW9kdWxlXCIgfTtcbiAgICBsZXQgY29waWVkIDo9IG9yaWdpbmFsLmNsb25lKCk7XG4gICAgYXNzZXJ0KGNvcGllZC5pZCA9PSA3KTtcbiAgICBhc3NlcnQoY29waWVkLm5hbWUgPT0gXCJjcm9zcyBtb2R1bGVcIik7XG59XG4ifSx7Im5hbWUiOiJtb2RlbC5tdGwiLCJzb3VyY2UiOiJwdWJsaWMgcmVjb3JkIFBhY2tldCB7IGlkOiBpNjQsIG5hbWU6IFN0cmluZyB9XG4ifV0sImhyZWYiOiJodHRwczovL2dpdGh1Yi5jb20vbWV0ZWwtbGFuZy9tZXRlbC1jb3JlL2Jsb2IvdjAuMTQuMS9tZXRlbC1pbnRlcnByZXRlci90ZXN0cy9pbnRlZ3JhdGlvbi9zb3VyY2VzL21vZHVsZV9zZW1hbnRpY3MvcmVsZWFzZV9tYXRyaXhfcmVjb3JkX2Nsb25lX2Nyb3NzX21vZHVsZSIsIm5hbWUiOiJyZWxlYXNlX21hdHJpeF9yZWNvcmRfY2xvbmVfY3Jvc3NfbW9kdWxlIn0="></details>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoic3VjY2VzcyJ9LCJmaWxlcyI6W3sibmFtZSI6Im1haW4ubXRsIiwic291cmNlIjoiaW1wb3J0IHNoYXBlczo6e0ZyYW1lLCBXZWlnaCwgc3RyaXBfbGFiZWwsIHRvdGFsLCBlbXB0eV9hZnRlcn07XG5mdW4gbWFpbigpIHtcbiAgICBsZXQgZiA6PSBGcmFtZSB7IHB1YmxpY19yb3dzID0gWzEsIDIsIDNdLCBsYWJlbCA9IFwieFwiIH07XG4gICAgbGV0IHN0cmlwcGVkIDo9IHN0cmlwX2xhYmVsKGYpO1xuICAgIGFzc2VydChzdHJpcHBlZC5wdWJsaWNfcm93c1syXSA9PSAzKTtcbiAgICBhc3NlcnQodG90YWwoc3RyaXBwZWQpID09IDYpO1xuICAgIGFzc2VydCh0b3RhbCh7IHB1YmxpY19yb3dzID0gWzQsIDUsIDZdLCBleHRyYSA9IHRydWUgfSkgPT0gMTUpO1xuICAgIGxldCBlIDo9IGVtcHR5X2FmdGVyKHsgbGFiZWwgPSBcImdvbmVcIi50b19zdHJpbmcoKSB9KTtcbiAgICBhc3NlcnQoZS53ZWlnaCgpID09IDEpO1xuICAgIGFzc2VydChzdHJpcHBlZC53ZWlnaCgpID09IDEpO1xufVxuIn0seyJuYW1lIjoic2hhcGVzLm10bCIsInNvdXJjZSI6InB1YmxpYyByZWNvcmQgRnJhbWUgeyBwdWJsaWNfcm93czogW2k2NDsgM10sIGxhYmVsOiBTdHJpbmcgfVxucHVibGljIGFzcGVjdCBXZWlnaCB7IGZ1biB3ZWlnaCgmc2VsZikgLT4gaTY0OyB9XG5leHRlbmQ8cm93IFI+IHsgLi5SIH06IFdlaWdoIHdoZXJlIGFsbCBSOiBDb3B5IHsgZnVuIHdlaWdoKCZzZWxmKSAtPiBpNjQgeyAxIH0gfVxucHVibGljIGZ1biBzdHJpcF9sYWJlbChmOiBGcmFtZSkgLT4geyBwdWJsaWNfcm93czogW2k2NDsgM10gfSB7XG4gICAgbGV0IHsgbGFiZWw6IF8sIC4ucmVzdCB9IDo9IGY7XG4gICAgcmVzdFxufVxucHVibGljIGZ1biB0b3RhbDxyb3cgUj4odjogeyBwdWJsaWNfcm93czogW2k2NDsgM10sIC4uUiB9KSAtPiBpNjQgd2hlcmUgYWxsIFI6IENvcHkge1xuICAgIHYucHVibGljX3Jvd3NbMF0gKyB2LnB1YmxpY19yb3dzWzFdICsgdi5wdWJsaWNfcm93c1syXVxufVxucHVibGljIGZ1biBlbXB0eV9hZnRlcjxyb3cgUiwgcm93IFJlc3Q+KHY6IHsgLi5SIH0pIC0+IHsgLi5SZXN0IH0gd2hlcmUgUiA9IHsgbGFiZWw6IFN0cmluZywgLi5SZXN0IH0ge1xuICAgIGxldCB7IGxhYmVsOiBfLCAuLnJlc3QgfSA6PSB2O1xuICAgIHJlc3Rcbn1cbiJ9XSwiaHJlZiI6Imh0dHBzOi8vZ2l0aHViLmNvbS9tZXRlbC1sYW5nL21ldGVsLWNvcmUvYmxvYi92MC4xNC4xL21ldGVsLWludGVycHJldGVyL3Rlc3RzL2ludGVncmF0aW9uL3NvdXJjZXMvbW9kdWxlX3NlbWFudGljcy9yZWxlYXNlX21hdHJpeF9yZWNvcmRfcm93c19hY3Jvc3NfbW9kdWxlcyIsIm5hbWUiOiJyZWxlYXNlX21hdHJpeF9yZWNvcmRfcm93c19hY3Jvc3NfbW9kdWxlcyJ9"></details>
</details>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.modules.imports.legality-3}

A qualified use resolves through an imported binding; an unresolved qualified path is a
name-resolution error and is not retried as an arbitrary bare name.

<!-- rfc.py:last_reviewed 96efb7986f7025157efce9ff719d56f2b892a989 -->

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0031](../../rfcs/4-implemented/rfc-0031-topological-typechecker.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<p class="rigor-backlink"><em>Tested by</em></p>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoic3VjY2VzcyJ9LCJmaWxlcyI6W3sibmFtZSI6Im1haW4ubXRsIiwic291cmNlIjoiaW1wb3J0IGhlbHBlcjo6KjtcbmZ1biBtYWluKCkgLT4gaTY0IHsgcmV0dXJuIGhlbHBlcjo6YW5zd2VyKCk7IH1cbiJ9LHsibmFtZSI6ImhlbHBlci5tdGwiLCJzb3VyY2UiOiJwdWJsaWMgZnVuIGFuc3dlcigpIC0+IGk2NCB7IHJldHVybiA5OTsgfVxuIn1dLCJocmVmIjoiaHR0cHM6Ly9naXRodWIuY29tL21ldGVsLWxhbmcvbWV0ZWwtY29yZS9ibG9iL3YwLjE0LjEvbWV0ZWwtaW50ZXJwcmV0ZXIvdGVzdHMvaW50ZWdyYXRpb24vc291cmNlcy9tb2R1bGVfc2VtYW50aWNzL3F1YWxpZmllZF9jYWxsX25vcm1hbGl6ZWRfdG9fYmFyZV9uYW1lIiwibmFtZSI6InF1YWxpZmllZF9jYWxsX25vcm1hbGl6ZWRfdG9fYmFyZV9uYW1lIn0="></details>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.modules.imports.legality-4}

An import loads its referenced module and introduces the selected public names or module
handle into the importing module's scope.

<!-- rfc.py:last_reviewed 722a13049df7dd2ba817e781ebbc6bb3689f9d6e -->

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0030](../../rfcs/4-implemented/rfc-0030-module-system-redesign.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<p class="rigor-backlink"><em>Tested by</em></p>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoic3VjY2VzcyJ9LCJmaWxlcyI6W3sibmFtZSI6Im1haW4ubXRsIiwic291cmNlIjoiaW1wb3J0IGhlbHBlcjo6YW5zd2VyO1xuZnVuIG1haW4oKSAtPiBpNjQgeyByZXR1cm4gYW5zd2VyKCk7IH1cbiJ9LHsibmFtZSI6ImhlbHBlci5tdGwiLCJzb3VyY2UiOiJwdWJsaWMgZnVuIGFuc3dlcigpIC0+IGk2NCB7IHJldHVybiA3OyB9XG4ifV0sImhyZWYiOiJodHRwczovL2dpdGh1Yi5jb20vbWV0ZWwtbGFuZy9tZXRlbC1jb3JlL2Jsb2IvdjAuMTQuMS9tZXRlbC1pbnRlcnByZXRlci90ZXN0cy9pbnRlZ3JhdGlvbi9zb3VyY2VzL21vZHVsZV9zZW1hbnRpY3MvZXhwbGljaXRfbmFtZWRfaW1wb3J0X2Z1bmN0aW9uX2NhbGwiLCJuYW1lIjoiZXhwbGljaXRfbmFtZWRfaW1wb3J0X2Z1bmN0aW9uX2NhbGwifQ=="></details>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.modules.imports.legality-5}

`import m::name` binds `name` in every namespace in which module `m` provides it, whether
`m` declares it or re-exports it, and `export m::name` re-exports it in the same way; an alias
renames the name in each. A name that `m` provides as both a type and a value is therefore
imported as both. A module handle (`import m`) binds in the type namespace.

<!-- rfc.py:last_reviewed fa44859ef74e6592a3ef7ffe086e4afb0de8743e -->

<!-- rfc.py:fixtures:start -->
<details class="rigor-fixtures-toggle" open>
<summary>Tested by (2)</summary>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoic3VjY2VzcyJ9LCJmaWxlcyI6W3sibmFtZSI6Im1haW4ubXRsIiwic291cmNlIjoiaW1wb3J0IGxpYjo6Rm9vO1xuXG5mdW4gbWFpbigpIHtcbiAgICBsZXQgYSA6PSBGb28geyB4ID0gMSB9O1xuICAgIGFzc2VydChhLnggPT0gMSk7XG59XG4ifSx7Im5hbWUiOiJsaWIubXRsIiwic291cmNlIjoiLy8gbWV0ZWwtY29yZSMxNTcxOiBgRm9vYCBpcyBwdWJsaWMgYXMgYSB0eXBlIGFuZCBwcml2YXRlIGFzIGEgZnVuY3Rpb24uIEltcG9ydGluZyBgRm9vYCBicmluZ3Ncbi8vIGluIHRoZSB0eXBlOyB0aGUgcHJpdmF0ZSBmdW5jdGlvbiBpcyBub3QgaW1wb3J0YWJsZSBidXQgZG9lcyBub3QgbWFrZSB0aGUgaW1wb3J0IGZhaWwuXG5wdWJsaWMgc3RydWN0IEZvbyB7XG4gICAgcHVibGljIHg6IGk2NCxcbn1cblxuZnVuIEZvbygpIC0+IGk2NCB7XG4gICAgNVxufVxuIn1dLCJocmVmIjoiaHR0cHM6Ly9naXRodWIuY29tL21ldGVsLWxhbmcvbWV0ZWwtY29yZS9ibG9iL3YwLjE0LjEvbWV0ZWwtaW50ZXJwcmV0ZXIvdGVzdHMvaW50ZWdyYXRpb24vc291cmNlcy9ldmFsdWF0b3Ivc3RydWN0cy9hX3ByaXZhdGVfZnVuY3Rpb25fZG9lc19ub3RfaGlkZV9hX3B1YmxpY190eXBlX29mX2l0c19uYW1lIiwibmFtZSI6ImFfcHJpdmF0ZV9mdW5jdGlvbl9kb2VzX25vdF9oaWRlX2FfcHVibGljX3R5cGVfb2ZfaXRzX25hbWUifQ=="></details>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoic3VjY2VzcyJ9LCJmaWxlcyI6W3sibmFtZSI6Im1haW4ubXRsIiwic291cmNlIjoiaW1wb3J0IGxpYjo6Rm9vO1xuXG5mdW4gbWFpbigpIHtcbiAgICBsZXQgYSA6PSBGb28geyB4ID0gMSB9O1xuICAgIGFzc2VydChhLnggPT0gMSk7XG4gICAgYXNzZXJ0KEZvbygpID09IDUpO1xufVxuIn0seyJuYW1lIjoibGliLm10bCIsInNvdXJjZSI6Ii8vIG1ldGVsLWNvcmUjMTU3MTogYSBtb2R1bGUgZXhwb3J0aW5nIGEgc3RydWN0IGFuZCBhIGZ1bmN0aW9uIG9mIG9uZSBuYW1lLiBFYWNoIGhhcyBpdHMgb3duXG4vLyBTeW1ib2xJZCwgc28gYSBzaW5nbGUgYGltcG9ydCBsaWI6OkZvbztgIGJyaW5ncyBib3RoIGludG8gc2NvcGUgYW5kIGVhY2ggdXNlIGZpbmRzIGl0cyBvd24uXG5wdWJsaWMgc3RydWN0IEZvbyB7XG4gICAgcHVibGljIHg6IGk2NCxcbn1cblxucHVibGljIGZ1biBGb28oKSAtPiBpNjQge1xuICAgIDVcbn1cbiJ9XSwiaHJlZiI6Imh0dHBzOi8vZ2l0aHViLmNvbS9tZXRlbC1sYW5nL21ldGVsLWNvcmUvYmxvYi92MC4xNC4xL21ldGVsLWludGVycHJldGVyL3Rlc3RzL2ludGVncmF0aW9uL3NvdXJjZXMvZXZhbHVhdG9yL3N0cnVjdHMvYV90eXBlX2FuZF9hX2Z1bmN0aW9uX21heV9iZV9pbXBvcnRlZF90b2dldGhlciIsIm5hbWUiOiJhX3R5cGVfYW5kX2FfZnVuY3Rpb25fbWF5X2JlX2ltcG9ydGVkX3RvZ2V0aGVyIn0="></details>
</details>
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

<!-- rfc.py:last_reviewed cfff5473333ed9035b5f8fc9ecf285c8fc394a1d -->

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0031](../../rfcs/4-implemented/rfc-0031-topological-typechecker.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<p class="rigor-backlink"><em>Tested by</em></p>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6IlQwMDA5IiwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoidHlwZWNoZWNrX2Vycm9yIn0sImZpbGVzIjpbeyJuYW1lIjoibWFpbi5tdGwiLCJzb3VyY2UiOiJpbXBvcnQgZmFjYWRlOjpzZWNyZXQ7XG5mdW4gbWFpbigpIC0+IGk2NCB7IHNlY3JldCgpIH1cbiJ9LHsibmFtZSI6ImZhY2FkZS5tdGwiLCJzb3VyY2UiOiJleHBvcnQgaGVscGVyOjpzZWNyZXQ7XG4ifSx7Im5hbWUiOiJoZWxwZXIubXRsIiwic291cmNlIjoiZnVuIHNlY3JldCgpIC0+IGk2NCB7IDQyIH1cbiJ9XSwiaHJlZiI6Imh0dHBzOi8vZ2l0aHViLmNvbS9tZXRlbC1sYW5nL21ldGVsLWNvcmUvYmxvYi92MC4xNC4xL21ldGVsLWludGVycHJldGVyL3Rlc3RzL2ludGVncmF0aW9uL3NvdXJjZXMvbW9kdWxlX3NlbWFudGljcy9yZmMwMDMxX3JlZXhwb3J0X3ByaXZhdGVfaXRlbV9pc190MDAwOSIsIm5hbWUiOiJyZmMwMDMxX3JlZXhwb3J0X3ByaXZhdGVfaXRlbV9pc190MDAwOSJ9"></details>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.modules.re-exports.legality-2}

A re-export makes a public source declaration available through the current module's
public API, including under an alias; importers may use it as a declaration of the facade.

<!-- rfc.py:last_reviewed 722a13049df7dd2ba817e781ebbc6bb3689f9d6e -->

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0030](../../rfcs/4-implemented/rfc-0030-module-system-redesign.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<p class="rigor-backlink"><em>Tested by</em></p>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoic3VjY2VzcyJ9LCJmaWxlcyI6W3sibmFtZSI6Im1haW4ubXRsIiwic291cmNlIjoiaW1wb3J0IGZhY2FkZTo6YW5zd2VyO1xuZnVuIG1haW4oKSAtPiBpNjQgeyByZXR1cm4gYW5zd2VyKCk7IH1cbiJ9LHsibmFtZSI6ImZhY2FkZS5tdGwiLCJzb3VyY2UiOiJpbXBvcnQgaGVscGVyOjphbnN3ZXI7XG5leHBvcnQgaGVscGVyOjphbnN3ZXI7XG4ifSx7Im5hbWUiOiJoZWxwZXIubXRsIiwic291cmNlIjoicHVibGljIGZ1biBhbnN3ZXIoKSAtPiBpNjQgeyByZXR1cm4gNDI7IH1cbiJ9XSwiaHJlZiI6Imh0dHBzOi8vZ2l0aHViLmNvbS9tZXRlbC1sYW5nL21ldGVsLWNvcmUvYmxvYi92MC4xNC4xL21ldGVsLWludGVycHJldGVyL3Rlc3RzL2ludGVncmF0aW9uL3NvdXJjZXMvbW9kdWxlX3NlbWFudGljcy9mYWNhZGVfcmVfZXhwb3J0c19pdGVtX2FuZF9jb25zdW1lcl9jYW5fdXNlX2l0IiwibmFtZSI6ImZhY2FkZV9yZV9leHBvcnRzX2l0ZW1fYW5kX2NvbnN1bWVyX2Nhbl91c2VfaXQifQ=="></details>
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

Every module automatically has `std::core` glob-imported at the lowest priority tier. This means `Option`, `Result`, `Display`, `Iterable`, `From`, and all built-in functions are available in every module without any explicit import statement.

```metel
// No import needed — Option and Result are always in scope
fun maybe_parse(s: String) -> Option<i64> {
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

You can still write `import std::core::Option;` or `import std::core::*;` explicitly — the result is the same. If a local declaration or explicit import shadows a `std::core` name, the local binding wins silently.

`std::core` is a **virtual module** — it has no physical `.mtl` file and cannot be listed or enumerated. Its contents are seeded by the runtime.

<details>
<summary>Formal rules</summary>

##### Legality Rule {#spec.modules.std-core-auto-import.legality-1}

Every module has the `std::core` names available without an import; the same names may also
be named through their explicit `std::core::` paths.

<!-- rfc.py:last_reviewed 052e8604c616372659749277ef96efec80d79fe6 -->

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0030](../../rfcs/4-implemented/rfc-0030-module-system-redesign.md), [rfc-0057](../../rfcs/4-implemented/rfc-0057-stdlib-layering-and-host-modules.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<details class="rigor-fixtures-toggle" open>
<summary>Tested by (3)</summary>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoic3VjY2VzcyJ9LCJmaWxlcyI6W3sibmFtZSI6ImludF8wOF9zdGRfY29yZV9wYXRocy5tdGwiLCJzb3VyY2UiOiIvLyBJbnRlZ3JhdGlvbiBUZXN0IDggXHUyMDE0IENvcmUgdHlwZSBjb21wbGV0ZW5lc3M6IE9wdGlvbiBhbmQgUmVzdWx0ICh2MC42LjApXG4vL1xuLy8gRmVhdHVyZSBjb3ZlcmFnZTpcbi8vICAgT3B0aW9uPFQ+IGNvbnN0cnVjdGlvbiwgbWF0Y2hpbmcsIGFuZCBjaGFpbmluZ1xuLy8gICBSZXN1bHQ8VCxFPiBjb25zdHJ1Y3Rpb24sIG1hdGNoaW5nLCA/IHByb3BhZ2F0aW9uLCBhbmQgRnJvbSBjb2VyY2lvblxuLy8gICBHZW5lcmljIGZ1bmN0aW9ucyBvdmVyIE9wdGlvbiBhbmQgUmVzdWx0XG4vLyAgIEludGVyYWN0aW9uOiBmdW5jdGlvbiByZXR1cm5pbmcgT3B0aW9uIHVzZWQgaW4gUmVzdWx0IGNvbnRleHQgdmlhIG1hcFxuLy8gICBSZWdyZXNzaW9uOiBlbnN1cmUgIzEzMyAoVHlwZURlZmluaXRpb25SZWdpc3RyeSkgZGlkIG5vdCBicmVhayB0aGVzZSBwYXRoc1xuXG4vLyBcdTI1MDBcdTI1MDAgUmVzdWx0IGhlbHBlcnMgXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXG5cbnN0cnVjdCBQYXJzZUVycm9yIHsgbXNnOiBTdHJpbmcgfVxuc3RydWN0IE1hdGhFcnJvciAgeyBtc2c6IFN0cmluZyB9XG5cbmV4dGVuZCBNYXRoRXJyb3I6IEZyb208UGFyc2VFcnJvcj4ge1xuICAgIGZ1biBmcm9tKHZhbHVlOiBQYXJzZUVycm9yKSAtPiBNYXRoRXJyb3Ige1xuICAgICAgICBNYXRoRXJyb3IgeyBtc2cgPSBcInBhcnNlOiBcIiArIHZhbHVlLm1zZyB9XG4gICAgfVxufVxuXG5mdW4gcGFyc2VfcG9zaXRpdmUoczogU3RyaW5nKSAtPiBSZXN1bHQ8aTY0LCBQYXJzZUVycm9yPiB7XG4gICAgaWYgKHMgPT0gXCIxXCIpIHsgUmVzdWx0OjpPayB7IHZhbHVlID0gMSB9IH1cbiAgICBlbHNlIGlmIChzID09IFwiMlwiKSB7IFJlc3VsdDo6T2sgeyB2YWx1ZSA9IDIgfSB9XG4gICAgZWxzZSBpZiAocyA9PSBcIjEwXCIpIHsgUmVzdWx0OjpPayB7IHZhbHVlID0gMTAgfSB9XG4gICAgZWxzZSBpZiAocyA9PSBcIjQyXCIpIHsgUmVzdWx0OjpPayB7IHZhbHVlID0gNDIgfSB9XG4gICAgZWxzZSB7IFJlc3VsdDo6RXJyIHsgZXJyb3IgPSBQYXJzZUVycm9yIHsgbXNnID0gXCJiYWQgaW5wdXQ6IFwiICsgcyB9IH0gfVxufVxuXG5mdW4gZG91YmxlX3BhcnNlZChzOiBTdHJpbmcpIC0+IFJlc3VsdDxpNjQsIFBhcnNlRXJyb3I+IHtcbiAgICBsZXQgbiA6PSBwYXJzZV9wb3NpdGl2ZShzKT87XG4gICAgUmVzdWx0OjpPayB7IHZhbHVlID0gbiAqIDIgfVxufVxuXG5mdW4gYWRkX3BhcnNlZChhOiBTdHJpbmcsIGI6IFN0cmluZykgLT4gUmVzdWx0PGk2NCwgTWF0aEVycm9yPiB7XG4gICAgLy8gY3Jvc3MtdHlwZSBtYXRjaCArIGFzLWNhc3QgKD8gY3Jvc3MtdHlwZSBkZWZlcnJlZCB0byAjMTMpXG4gICAgbGV0IHggOj0gbWF0Y2ggKHBhcnNlX3Bvc2l0aXZlKGEpKSB7XG4gICAgICAgIFJlc3VsdDo6T2sgeyB2YWx1ZSB9ID0+IHZhbHVlLFxuICAgICAgICBSZXN1bHQ6OkVyciB7IGVycm9yIH0gPT4geyByZXR1cm4gUmVzdWx0OjpFcnIgeyBlcnJvciA9IGVycm9yIGFzIE1hdGhFcnJvciB9OyB9LFxuICAgIH07XG4gICAgbGV0IHkgOj0gbWF0Y2ggKHBhcnNlX3Bvc2l0aXZlKGIpKSB7XG4gICAgICAgIFJlc3VsdDo6T2sgeyB2YWx1ZSB9ID0+IHZhbHVlLFxuICAgICAgICBSZXN1bHQ6OkVyciB7IGVycm9yIH0gPT4geyByZXR1cm4gUmVzdWx0OjpFcnIgeyBlcnJvciA9IGVycm9yIGFzIE1hdGhFcnJvciB9OyB9LFxuICAgIH07XG4gICAgUmVzdWx0OjpPayB7IHZhbHVlID0geCArIHkgfVxufVxuXG4vLyBcdTI1MDBcdTI1MDAgT3B0aW9uIGhlbHBlcnMgXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXG5cbmZ1biBmaW5kX2luKGFycjogW2k2NF0sIHRhcmdldDogaTY0KSAtPiBPcHRpb248aTY0PiB7XG4gICAgdmFyIGkgOj0gMDtcbiAgICB3aGlsZSAoaSA8IGFyci5sZW4oKSkge1xuICAgICAgICBpZiAoYXJyW2kgYXMgdTY0XSA9PSB0YXJnZXQpIHsgcmV0dXJuIE9wdGlvbjo6U29tZSB7IHZhbHVlID0gaSB9OyB9XG4gICAgICAgIGkgKz0gMTtcbiAgICB9XG4gICAgTm9uZVxufVxuXG5mdW4gbWFwX3NvbWUocDogT3B0aW9uPGk2ND4sIGZhY3RvcjogaTY0KSAtPiBPcHRpb248aTY0PiB7XG4gICAgbWF0Y2ggKHApIHtcbiAgICAgICAgT3B0aW9uOjpTb21lIHsgdmFsdWUgfSA9PiBPcHRpb246OlNvbWUgeyB2YWx1ZSA9IHZhbHVlICogZmFjdG9yIH0sXG4gICAgICAgIE5vbmUgPT4gTm9uZSxcbiAgICB9XG59XG5cbmZ1biBwZXJoYXBzX3RvX3Jlc3VsdChwOiBPcHRpb248aTY0PiwgZXJyb3I6IFN0cmluZykgLT4gUmVzdWx0PGk2NCwgU3RyaW5nPiB7XG4gICAgbWF0Y2ggKHApIHtcbiAgICAgICAgT3B0aW9uOjpTb21lIHsgdmFsdWUgfSA9PiBSZXN1bHQ6Ok9rIHsgdmFsdWUgPSB2YWx1ZSB9LFxuICAgICAgICBOb25lID0+IFJlc3VsdDo6RXJyIHsgZXJyb3IgPSBlcnJvciB9LFxuICAgIH1cbn1cblxuZnVuIG1haW4oKSB7XG4gICAgLy8gXHUyNTAwXHUyNTAwIEJhc2ljIFJlc3VsdCBtYXRjaGluZyBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcdTI1MDBcblxuICAgIGxldCByMSA6PSBwYXJzZV9wb3NpdGl2ZShcIjQyXCIpO1xuICAgIG1hdGNoIChyMSkge1xuICAgICAgICBSZXN1bHQ6Ok9rICB7IHZhbHVlIH0gPT4gYXNzZXJ0KHZhbHVlID09IDQyKSxcbiAgICAgICAgUmVzdWx0OjpFcnIgeyBlcnJvciB9ID0+IGFzc2VydChmYWxzZSksXG4gICAgfTtcblxuICAgIGxldCByMiA6PSBwYXJzZV9wb3NpdGl2ZShcImJhZFwiKTtcbiAgICBtYXRjaCAocjIpIHtcbiAgICAgICAgUmVzdWx0OjpPayAgeyB2YWx1ZSB9ID0+IGFzc2VydChmYWxzZSksXG4gICAgICAgIFJlc3VsdDo6RXJyIHsgZXJyb3IgfSA9PiBhc3NlcnQoZXJyb3IubXNnID09IFwiYmFkIGlucHV0OiBiYWRcIiksXG4gICAgfTtcblxuICAgIC8vIFx1MjUwMFx1MjUwMCA/IHByb3BhZ2F0aW9uIChzYW1lLXR5cGUpIFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFxuXG4gICAgbGV0IGQxIDo9IGRvdWJsZV9wYXJzZWQoXCIxMFwiKTtcbiAgICBtYXRjaCAoZDEpIHtcbiAgICAgICAgUmVzdWx0OjpPayAgeyB2YWx1ZSB9ID0+IGFzc2VydCh2YWx1ZSA9PSAyMCksXG4gICAgICAgIFJlc3VsdDo6RXJyIHsgZXJyb3IgfSA9PiBhc3NlcnQoZmFsc2UpLFxuICAgIH07XG5cbiAgICBsZXQgZDIgOj0gZG91YmxlX3BhcnNlZChcIm5vcGVcIik7XG4gICAgbWF0Y2ggKGQyKSB7XG4gICAgICAgIFJlc3VsdDo6T2sgIHsgdmFsdWUgfSA9PiBhc3NlcnQoZmFsc2UpLFxuICAgICAgICBSZXN1bHQ6OkVyciB7IGVycm9yIH0gPT4gYXNzZXJ0KGVycm9yLm1zZyA9PSBcImJhZCBpbnB1dDogbm9wZVwiKSxcbiAgICB9O1xuXG4gICAgLy8gXHUyNTAwXHUyNTAwID8gcHJvcGFnYXRpb24gd2l0aCBGcm9tIGNvZXJjaW9uIChQYXJzZUVycm9yIFx1MjE5MiBNYXRoRXJyb3IpIFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFxuXG4gICAgbGV0IGExIDo9IGFkZF9wYXJzZWQoXCIxXCIsIFwiMlwiKTtcbiAgICBtYXRjaCAoYTEpIHtcbiAgICAgICAgUmVzdWx0OjpPayAgeyB2YWx1ZSB9ID0+IGFzc2VydCh2YWx1ZSA9PSAzKSxcbiAgICAgICAgUmVzdWx0OjpFcnIgeyBlcnJvciB9ID0+IGFzc2VydChmYWxzZSksXG4gICAgfTtcblxuICAgIGxldCBhMiA6PSBhZGRfcGFyc2VkKFwiMVwiLCBcImJhZFwiKTtcbiAgICBtYXRjaCAoYTIpIHtcbiAgICAgICAgUmVzdWx0OjpPayAgeyB2YWx1ZSB9ID0+IGFzc2VydChmYWxzZSksXG4gICAgICAgIFJlc3VsdDo6RXJyIHsgZXJyb3IgfSA9PiBhc3NlcnQoZXJyb3IubXNnID09IFwicGFyc2U6IGJhZCBpbnB1dDogYmFkXCIpLFxuICAgIH07XG5cbiAgICBsZXQgYTMgOj0gYWRkX3BhcnNlZChcInhcIiwgXCIyXCIpO1xuICAgIG1hdGNoIChhMykge1xuICAgICAgICBSZXN1bHQ6Ok9rICB7IHZhbHVlIH0gPT4gYXNzZXJ0KGZhbHNlKSxcbiAgICAgICAgUmVzdWx0OjpFcnIgeyBlcnJvciB9ID0+IGFzc2VydChlcnJvci5tc2cgPT0gXCJwYXJzZTogYmFkIGlucHV0OiB4XCIpLFxuICAgIH07XG5cbiAgICAvLyBcdTI1MDBcdTI1MDAgT3B0aW9uOiBmaW5kX2luIFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFxuXG4gICAgbGV0IGFyciA6PSBbMTAsIDIwLCAzMCwgNDAsIDUwXTtcblxuICAgIGxldCBmMSA6PSBmaW5kX2luKGFyciwgMzApO1xuICAgIG1hdGNoIChmMSkge1xuICAgICAgICBPcHRpb246OlNvbWUgeyB2YWx1ZSB9ID0+IGFzc2VydCh2YWx1ZSA9PSAyKSxcbiAgICAgICAgTm9uZSA9PiBhc3NlcnQoZmFsc2UpLFxuICAgIH07XG5cbiAgICBsZXQgZjIgOj0gZmluZF9pbihhcnIsIDk5KTtcbiAgICBtYXRjaCAoZjIpIHtcbiAgICAgICAgT3B0aW9uOjpTb21lIHsgdmFsdWUgfSA9PiBhc3NlcnQoZmFsc2UpLFxuICAgICAgICBOb25lID0+IGFzc2VydCh0cnVlKSxcbiAgICB9O1xuXG4gICAgLy8gXHUyNTAwXHUyNTAwIE9wdGlvbiBjaGFpbmluZyB2aWEgbWFwX3NvbWUgXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXHUyNTAwXG5cbiAgICBsZXQgbTEgOj0gbWFwX3NvbWUoT3B0aW9uOjpTb21lIHsgdmFsdWUgPSA1IH0sIDMpO1xuICAgIG1hdGNoIChtMSkge1xuICAgICAgICBPcHRpb246OlNvbWUgeyB2YWx1ZSB9ID0+IGFzc2VydCh2YWx1ZSA9PSAxNSksXG4gICAgICAgIE5vbmUgPT4gYXNzZXJ0KGZhbHNlKSxcbiAgICB9O1xuXG4gICAgbGV0IG0yIDo9IG1hcF9zb21lKE5vbmUsIDMpO1xuICAgIG1hdGNoIChtMikge1xuICAgICAgICBPcHRpb246OlNvbWUgeyB2YWx1ZSB9ID0+IGFzc2VydChmYWxzZSksXG4gICAgICAgIE5vbmUgPT4gYXNzZXJ0KHRydWUpLFxuICAgIH07XG5cbiAgICAvLyBtYXBfc29tZSBvZiBhIGZpbmRfaW4gcmVzdWx0XG4gICAgbGV0IG1hcHBlZCA6PSBtYXBfc29tZShmaW5kX2luKGFyciwgMjApLCAxMCk7XG4gICAgbWF0Y2ggKG1hcHBlZCkge1xuICAgICAgICBPcHRpb246OlNvbWUgeyB2YWx1ZSB9ID0+IGFzc2VydCh2YWx1ZSA9PSAxMCksIC8vIGluZGV4IDEsIG11bHRpcGxpZWQgYnkgMTBcbiAgICAgICAgTm9uZSA9PiBhc3NlcnQoZmFsc2UpLFxuICAgIH07XG5cbiAgICAvLyBcdTI1MDBcdTI1MDAgcGVyaGFwc190b19yZXN1bHQgYnJpZGdlIFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFx1MjUwMFxuXG4gICAgbGV0IHAycl9vayA6PSBwZXJoYXBzX3RvX3Jlc3VsdChPcHRpb246OlNvbWUgeyB2YWx1ZSA9IDcgfSwgXCJub3QgZm91bmRcIik7XG4gICAgbWF0Y2ggKHAycl9vaykge1xuICAgICAgICBSZXN1bHQ6Ok9rICB7IHZhbHVlIH0gPT4gYXNzZXJ0KHZhbHVlID09IDcpLFxuICAgICAgICBSZXN1bHQ6OkVyciB7IGVycm9yIH0gPT4gYXNzZXJ0KGZhbHNlKSxcbiAgICB9O1xuXG4gICAgbGV0IHAycl9lcnIgOj0gcGVyaGFwc190b19yZXN1bHQoTm9uZSwgXCJub3QgZm91bmRcIik7XG4gICAgbWF0Y2ggKHAycl9lcnIpIHtcbiAgICAgICAgUmVzdWx0OjpPayAgeyB2YWx1ZSB9ID0+IGFzc2VydChmYWxzZSksXG4gICAgICAgIFJlc3VsdDo6RXJyIHsgZXJyb3IgfSA9PiBhc3NlcnQoZXJyb3IgPT0gXCJub3QgZm91bmRcIiksXG4gICAgfTtcblxuICAgIC8vIENvbWJpbmUgZmluZF9pbiAocmV0dXJucyBPcHRpb24pIHdpdGggcGVyaGFwc190b19yZXN1bHQgKGNvbnZlcnRzIHRvIFJlc3VsdClcbiAgICBsZXQgYnJpZGdlIDo9IHBlcmhhcHNfdG9fcmVzdWx0KGZpbmRfaW4oYXJyLCA0MCksIFwibWlzc2luZ1wiKTtcbiAgICBtYXRjaCAoYnJpZGdlKSB7XG4gICAgICAgIFJlc3VsdDo6T2sgIHsgdmFsdWUgfSA9PiBhc3NlcnQodmFsdWUgPT0gMyksIC8vIGluZGV4IDNcbiAgICAgICAgUmVzdWx0OjpFcnIgeyBlcnJvciB9ID0+IGFzc2VydChmYWxzZSksXG4gICAgfTtcblxuICAgIGxldCBicmlkZ2VfbWlzcyA6PSBwZXJoYXBzX3RvX3Jlc3VsdChmaW5kX2luKGFyciwgMCksIFwibWlzc2luZ1wiKTtcbiAgICBtYXRjaCAoYnJpZGdlX21pc3MpIHtcbiAgICAgICAgUmVzdWx0OjpPayAgeyB2YWx1ZSB9ID0+IGFzc2VydChmYWxzZSksXG4gICAgICAgIFJlc3VsdDo6RXJyIHsgZXJyb3IgfSA9PiBhc3NlcnQoZXJyb3IgPT0gXCJtaXNzaW5nXCIpLFxuICAgIH07XG59XG4ifV0sImhyZWYiOiJodHRwczovL2dpdGh1Yi5jb20vbWV0ZWwtbGFuZy9tZXRlbC1jb3JlL2Jsb2IvdjAuMTQuMS9tZXRlbC1pbnRlcnByZXRlci90ZXN0cy9pbnRlZ3JhdGlvbi9zb3VyY2VzL2V2YWx1YXRvci9pbnRlZ3JhdGlvbi9pbnRfMDhfc3RkX2NvcmVfcGF0aHMubXRsIiwibmFtZSI6ImludF8wOF9zdGRfY29yZV9wYXRocy5tdGwifQ=="></details>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoic3VjY2VzcyJ9LCJmaWxlcyI6W3sibmFtZSI6Im1haW4ubXRsIiwic291cmNlIjoiaW1wb3J0IGhlbHBlcjo6c3VtOyAgICAgICAgIFxuZnVuIG1haW4oKSB7ICAgICAgICAgXG4gICAgbGV0IGFyciA6PSBbMSwgMiwgMywgNCwgNV07ICAgICAgICAgXG4gICAgbGV0IHJlc3VsdCA6PSBzdW0oYXJyKTsgICAgICAgICBcbiAgICBhc3NlcnQocmVzdWx0ID09IDE1KTsgICAgICAgICBcbiAgICBwcmludChyZXN1bHQpOyAgICAgICAgIFxufVxuIn0seyJuYW1lIjoiaGVscGVyLm10bCIsInNvdXJjZSI6InB1YmxpYyBmdW4gc3VtKGFycjogW2k2NF0pIC0+IGk2NCB7ICAgICAgICAgXG4gICAgYXNzZXJ0KGFyci5sZW4oKSA+IDApOyAgICAgICAgIFxuICAgIHZhciB0b3RhbCA6PSAwOyAgICAgICAgIFxuICAgIHZhciBpIDo9IDA7ICAgICAgICAgXG4gICAgd2hpbGUgKGkgPCBhcnIubGVuKCkpIHsgdG90YWwgKz0gYXJyW2kgYXMgdTY0XTsgaSArPSAxOyB9ICAgICAgICAgXG4gICAgcmV0dXJuIHRvdGFsOyAgICAgICAgIFxufVxuIn1dLCJocmVmIjoiaHR0cHM6Ly9naXRodWIuY29tL21ldGVsLWxhbmcvbWV0ZWwtY29yZS9ibG9iL3YwLjE0LjEvbWV0ZWwtaW50ZXJwcmV0ZXIvdGVzdHMvaW50ZWdyYXRpb24vc291cmNlcy9tb2R1bGVfc2VtYW50aWNzL3N0ZF9jb3JlX2J1aWx0aW5zX2F2YWlsYWJsZV9pbl9lYWNoX21vZHVsZV93aXRob3V0X2ltcG9ydCIsIm5hbWUiOiJzdGRfY29yZV9idWlsdGluc19hdmFpbGFibGVfaW5fZWFjaF9tb2R1bGVfd2l0aG91dF9pbXBvcnQifQ=="></details>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoic3VjY2VzcyJ9LCJmaWxlcyI6W3sibmFtZSI6Im1haW4ubXRsIiwic291cmNlIjoiLy8gbWV0ZWwtY29yZSMxNTg3OiB0aGUgZXhwbGljaXQgYHN0ZDo6Y29yZTo6YCBwYXRoIG5hbWVzIGEgY29yZSB0eXBlIGluIGEgdHlwZSBwb3NpdGlvbiwgYWxzbyB3aGVyZVxuLy8gdGhlIG1vZHVsZSBkZWNsYXJlcyBhIHR5cGUgb2YgdGhlIHNhbWUgbmFtZS5cbmVudW0gT3B0aW9uPFQ+IHtcbiAgICBOb3BlLFxufVxuXG5mdW4gZmlyc3QodmFsdWVzOiBbaTY0XSkgLT4gc3RkOjpjb3JlOjpPcHRpb248aTY0PiB7XG4gICAgaWYgKHZhbHVlcy5sZW4oKSA9PSAwKSB7XG4gICAgICAgIHJldHVybiBOb25lO1xuICAgIH1cbiAgICBTb21lIHsgdmFsdWUgPSB2YWx1ZXNbMF0gfVxufVxuXG5mdW4gbWFpbigpIHtcbiAgICBsZXQgZ290IDo9IG1hdGNoIChmaXJzdChbNCwgNV0pKSB7XG4gICAgICAgIFNvbWUgeyB2YWx1ZSB9ID0+IHsgdmFsdWUgfSxcbiAgICAgICAgTm9uZSA9PiB7IDAgfSxcbiAgICB9O1xuICAgIGFzc2VydChnb3QgPT0gNCk7XG59XG4ifV0sImhyZWYiOiJodHRwczovL2dpdGh1Yi5jb20vbWV0ZWwtbGFuZy9tZXRlbC1jb3JlL2Jsb2IvdjAuMTQuMS9tZXRlbC1pbnRlcnByZXRlci90ZXN0cy9pbnRlZ3JhdGlvbi9zb3VyY2VzL21vZHVsZV9zZW1hbnRpY3Mvc3RkX2NvcmVfcXVhbGlmaWVkX3BhdGhfbmFtZXNfYV9jb3JlX3R5cGUiLCJuYW1lIjoic3RkX2NvcmVfcXVhbGlmaWVkX3BhdGhfbmFtZXNfYV9jb3JlX3R5cGUifQ=="></details>
</details>
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

<!-- rfc.py:last_reviewed 282f563360390f6648e81bc9d3974bcb8070c496 -->

<!-- rfc.py:fixtures:start -->
<p class="rigor-backlink"><em>Tested by</em></p>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6IlQwMDExIiwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoidHlwZWNoZWNrX2Vycm9yIn0sImZpbGVzIjpbeyJuYW1lIjoibWFpbi5tdGwiLCJzb3VyY2UiOiJpbXBvcnQgYTo6Zm9vO1xuaW1wb3J0IGI6OmZvbztcbmZ1biBtYWluKCkgLT4gaTY0IHsgcmV0dXJuIGZvbygpOyB9XG4ifSx7Im5hbWUiOiJhLm10bCIsInNvdXJjZSI6InB1YmxpYyBmdW4gZm9vKCkgLT4gaTY0IHsgcmV0dXJuIDE7IH1cbiJ9LHsibmFtZSI6ImIubXRsIiwic291cmNlIjoicHVibGljIGZ1biBmb28oKSAtPiBpNjQgeyByZXR1cm4gMjsgfVxuIn1dLCJocmVmIjoiaHR0cHM6Ly9naXRodWIuY29tL21ldGVsLWxhbmcvbWV0ZWwtY29yZS9ibG9iL3YwLjE0LjEvbWV0ZWwtaW50ZXJwcmV0ZXIvdGVzdHMvaW50ZWdyYXRpb24vc291cmNlcy9tb2R1bGVfc2VtYW50aWNzL3R3b19leHBsaWNpdF9pbXBvcnRzX3NhbWVfbG9jYWxfbmFtZV9pc190MDAxMSIsIm5hbWUiOiJ0d29fZXhwbGljaXRfaW1wb3J0c19zYW1lX2xvY2FsX25hbWVfaXNfdDAwMTEifQ=="></details>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.modules.import-conflicts.legality-2}

A collision between two user glob imports is rejected with `T0011` only when code refers
to the ambiguous name.

<!-- rfc.py:last_reviewed 282f563360390f6648e81bc9d3974bcb8070c496 -->

<!-- rfc.py:fixtures:start -->
<p class="rigor-backlink"><em>Tested by</em></p>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6IlQwMDExIiwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoidHlwZWNoZWNrX2Vycm9yIn0sImZpbGVzIjpbeyJuYW1lIjoibWFpbi5tdGwiLCJzb3VyY2UiOiJpbXBvcnQgYTo6KjtcbmltcG9ydCBiOjoqO1xuZnVuIG1haW4oKSAtPiBpNjQgeyByZXR1cm4gZm9vKCk7IH1cbiJ9LHsibmFtZSI6ImEubXRsIiwic291cmNlIjoicHVibGljIGZ1biBmb28oKSAtPiBpNjQgeyByZXR1cm4gMTsgfVxuIn0seyJuYW1lIjoiYi5tdGwiLCJzb3VyY2UiOiJwdWJsaWMgZnVuIGZvbygpIC0+IGk2NCB7IHJldHVybiAyOyB9XG4ifV0sImhyZWYiOiJodHRwczovL2dpdGh1Yi5jb20vbWV0ZWwtbGFuZy9tZXRlbC1jb3JlL2Jsb2IvdjAuMTQuMS9tZXRlbC1pbnRlcnByZXRlci90ZXN0cy9pbnRlZ3JhdGlvbi9zb3VyY2VzL21vZHVsZV9zZW1hbnRpY3MvdHdvX2dsb2JfaW1wb3J0c19zYW1lX25hbWVfaXNfdDAwMTEiLCJuYW1lIjoidHdvX2dsb2JfaW1wb3J0c19zYW1lX25hbWVfaXNfdDAwMTEifQ=="></details>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.modules.import-conflicts.legality-3}

An explicit import takes precedence over a glob-imported binding of the same name.

<!-- rfc.py:last_reviewed 282f563360390f6648e81bc9d3974bcb8070c496 -->

<!-- rfc.py:fixtures:start -->
<p class="rigor-backlink"><em>Tested by</em></p>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoic3VjY2VzcyJ9LCJmaWxlcyI6W3sibmFtZSI6Im1haW4ubXRsIiwic291cmNlIjoiaW1wb3J0IGE6OmZvbztcbmltcG9ydCBiOjoqO1xuZnVuIG1haW4oKSAtPiBpNjQgeyByZXR1cm4gZm9vKCk7IH1cbiJ9LHsibmFtZSI6ImEubXRsIiwic291cmNlIjoicHVibGljIGZ1biBmb28oKSAtPiBpNjQgeyByZXR1cm4gMTsgfVxuIn0seyJuYW1lIjoiYi5tdGwiLCJzb3VyY2UiOiJwdWJsaWMgZnVuIGZvbygpIC0+IGk2NCB7IHJldHVybiAyOyB9XG4ifV0sImhyZWYiOiJodHRwczovL2dpdGh1Yi5jb20vbWV0ZWwtbGFuZy9tZXRlbC1jb3JlL2Jsb2IvdjAuMTQuMS9tZXRlbC1pbnRlcnByZXRlci90ZXN0cy9pbnRlZ3JhdGlvbi9zb3VyY2VzL21vZHVsZV9zZW1hbnRpY3MvZXhwbGljaXRfaW1wb3J0X3dpbnNfb3Zlcl9nbG9iX3NhbWVfbmFtZSIsIm5hbWUiOiJleHBsaWNpdF9pbXBvcnRfd2luc19vdmVyX2dsb2Jfc2FtZV9uYW1lIn0="></details>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.modules.import-conflicts.legality-4}

Import conflicts follow their binding kind: duplicate explicit imports fail immediately,
ambiguous user-glob names fail when referenced, and an explicit import disambiguates a
glob-provided name.

<!-- rfc.py:last_reviewed 282f563360390f6648e81bc9d3974bcb8070c496 -->

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0030](../../rfcs/4-implemented/rfc-0030-module-system-redesign.md), [rfc-0031](../../rfcs/4-implemented/rfc-0031-topological-typechecker.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<details class="rigor-fixtures-toggle" open>
<summary>Tested by (3)</summary>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoic3VjY2VzcyJ9LCJmaWxlcyI6W3sibmFtZSI6Im1haW4ubXRsIiwic291cmNlIjoiaW1wb3J0IGE6OmZvbztcbmltcG9ydCBiOjoqO1xuZnVuIG1haW4oKSAtPiBpNjQgeyByZXR1cm4gZm9vKCk7IH1cbiJ9LHsibmFtZSI6ImEubXRsIiwic291cmNlIjoicHVibGljIGZ1biBmb28oKSAtPiBpNjQgeyByZXR1cm4gMTsgfVxuIn0seyJuYW1lIjoiYi5tdGwiLCJzb3VyY2UiOiJwdWJsaWMgZnVuIGZvbygpIC0+IGk2NCB7IHJldHVybiAyOyB9XG4ifV0sImhyZWYiOiJodHRwczovL2dpdGh1Yi5jb20vbWV0ZWwtbGFuZy9tZXRlbC1jb3JlL2Jsb2IvdjAuMTQuMS9tZXRlbC1pbnRlcnByZXRlci90ZXN0cy9pbnRlZ3JhdGlvbi9zb3VyY2VzL21vZHVsZV9zZW1hbnRpY3MvZXhwbGljaXRfaW1wb3J0X3dpbnNfb3Zlcl9nbG9iX3NhbWVfbmFtZSIsIm5hbWUiOiJleHBsaWNpdF9pbXBvcnRfd2luc19vdmVyX2dsb2Jfc2FtZV9uYW1lIn0="></details>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6IlQwMDExIiwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoidHlwZWNoZWNrX2Vycm9yIn0sImZpbGVzIjpbeyJuYW1lIjoibWFpbi5tdGwiLCJzb3VyY2UiOiJpbXBvcnQgYTo6Zm9vO1xuaW1wb3J0IGI6OmZvbztcbmZ1biBtYWluKCkgLT4gaTY0IHsgcmV0dXJuIGZvbygpOyB9XG4ifSx7Im5hbWUiOiJhLm10bCIsInNvdXJjZSI6InB1YmxpYyBmdW4gZm9vKCkgLT4gaTY0IHsgcmV0dXJuIDE7IH1cbiJ9LHsibmFtZSI6ImIubXRsIiwic291cmNlIjoicHVibGljIGZ1biBmb28oKSAtPiBpNjQgeyByZXR1cm4gMjsgfVxuIn1dLCJocmVmIjoiaHR0cHM6Ly9naXRodWIuY29tL21ldGVsLWxhbmcvbWV0ZWwtY29yZS9ibG9iL3YwLjE0LjEvbWV0ZWwtaW50ZXJwcmV0ZXIvdGVzdHMvaW50ZWdyYXRpb24vc291cmNlcy9tb2R1bGVfc2VtYW50aWNzL3R3b19leHBsaWNpdF9pbXBvcnRzX3NhbWVfbG9jYWxfbmFtZV9pc190MDAxMSIsIm5hbWUiOiJ0d29fZXhwbGljaXRfaW1wb3J0c19zYW1lX2xvY2FsX25hbWVfaXNfdDAwMTEifQ=="></details>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6IlQwMDExIiwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoidHlwZWNoZWNrX2Vycm9yIn0sImZpbGVzIjpbeyJuYW1lIjoibWFpbi5tdGwiLCJzb3VyY2UiOiJpbXBvcnQgYTo6KjtcbmltcG9ydCBiOjoqO1xuZnVuIG1haW4oKSAtPiBpNjQgeyByZXR1cm4gZm9vKCk7IH1cbiJ9LHsibmFtZSI6ImEubXRsIiwic291cmNlIjoicHVibGljIGZ1biBmb28oKSAtPiBpNjQgeyByZXR1cm4gMTsgfVxuIn0seyJuYW1lIjoiYi5tdGwiLCJzb3VyY2UiOiJwdWJsaWMgZnVuIGZvbygpIC0+IGk2NCB7IHJldHVybiAyOyB9XG4ifV0sImhyZWYiOiJodHRwczovL2dpdGh1Yi5jb20vbWV0ZWwtbGFuZy9tZXRlbC1jb3JlL2Jsb2IvdjAuMTQuMS9tZXRlbC1pbnRlcnByZXRlci90ZXN0cy9pbnRlZ3JhdGlvbi9zb3VyY2VzL21vZHVsZV9zZW1hbnRpY3MvdHdvX2dsb2JfaW1wb3J0c19zYW1lX25hbWVfaXNfdDAwMTEiLCJuYW1lIjoidHdvX2dsb2JfaW1wb3J0c19zYW1lX25hbWVfaXNfdDAwMTEifQ=="></details>
</details>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.modules.import-conflicts.legality-5}

Two explicit imports of one local name conflict only when they bind it in the same namespace.
With a struct `Foo` in module `a` and a function `Foo` in module `b`, `import a::Foo;` and
`import b::Foo;` together are legal, and each use finds the one it needs. Two imports that both
provide a *type* `Foo`, or both a *value* `Foo`, are the conflict of
[legality-4](#spec.modules.import-conflicts.legality-4).

<!-- rfc.py:last_reviewed fa44859ef74e6592a3ef7ffe086e4afb0de8743e -->

<!-- rfc.py:fixtures:start -->
<p class="rigor-backlink"><em>Tested by</em></p>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoic3VjY2VzcyJ9LCJmaWxlcyI6W3sibmFtZSI6Im1haW4ubXRsIiwic291cmNlIjoiLy8gbWV0ZWwtY29yZSMxNTc3OiBgYWAgcHJvdmlkZXMgYSB0eXBlIGBGb29gIGFuZCBgYmAgYSB2YWx1ZSBgRm9vYDsgYm90aCBpbXBvcnRzIGJpbmQgdGhlIHNhbWUgbG9jYWxcbi8vIG5hbWUsIGluIGRpZmZlcmVudCBuYW1lc3BhY2VzLCBzbyB0aGV5IGRvIG5vdCBjb25mbGljdC5cbmltcG9ydCBhOjpGb287XG5pbXBvcnQgYjo6Rm9vO1xuXG5mdW4gbWFpbigpIHtcbiAgICBsZXQgdiA6PSBGb28geyB4ID0gMSB9O1xuICAgIGFzc2VydCh2LnggPT0gMSk7XG4gICAgYXNzZXJ0KEZvbygpID09IDUpO1xufVxuIn0seyJuYW1lIjoiYS5tdGwiLCJzb3VyY2UiOiJwdWJsaWMgc3RydWN0IEZvbyB7XG4gICAgcHVibGljIHg6IGk2NCxcbn1cbiJ9LHsibmFtZSI6ImIubXRsIiwic291cmNlIjoicHVibGljIGZ1biBGb28oKSAtPiBpNjQge1xuICAgIDVcbn1cbiJ9XSwiaHJlZiI6Imh0dHBzOi8vZ2l0aHViLmNvbS9tZXRlbC1sYW5nL21ldGVsLWNvcmUvYmxvYi92MC4xNC4xL21ldGVsLWludGVycHJldGVyL3Rlc3RzL2ludGVncmF0aW9uL3NvdXJjZXMvZXZhbHVhdG9yL3N0cnVjdHMvaW1wb3J0c19vZl9vbmVfbmFtZV9pbl9kaWZmZXJlbnRfbmFtZXNwYWNlc19kb19ub3RfY29uZmxpY3QiLCJuYW1lIjoiaW1wb3J0c19vZl9vbmVfbmFtZV9pbl9kaWZmZXJlbnRfbmFtZXNwYWNlc19kb19ub3RfY29uZmxpY3QifQ=="></details>
<!-- rfc.py:fixtures:end -->

</details>

## Visibility

Declarations are module-private by default. [A declaration is accessible from outside its module only if it is annotated with `public`](#spec.modules.visibility.legality-1).

```metel
public struct Token { public kind: i64, span: i64 }
struct InternalState { count: i64 }

public fun parse(tokens: [Token]) -> i64 { return tokens.len(); }
fun helper(token: Token) -> boolean { return token.kind == 0; }

fun main() -> i64 {
    let token := Token { kind = 0, span = 1 };
    let state := InternalState { count = 2 };
    if (helper(token)) { return parse([token]) + state.count; }
    return 0;
}
```

`public` is valid on `struct`, `enum`, `fun`, and `aspect` declarations. Top-level `let` and `var` bindings are always module-private.

> **Gap** GAP-MODULES-003

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
must be used to omit it instead. A private field's name also cannot appear in a [public
signature](#spec.modules.visibility.legality-8), so it never becomes part of the module's API.

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

<!-- rfc.py:last_reviewed fee29158f82d543baecf5b42642ccebeff2cfde8 -->

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0030](../../rfcs/4-implemented/rfc-0030-module-system-redesign.md), [rfc-0031](../../rfcs/4-implemented/rfc-0031-topological-typechecker.md), [rfc-0032](../../rfcs/4-implemented/rfc-0032-field-level-visibility.md), [rfc-0098](../../rfcs/4-implemented/rfc-0098-surface-keyword-renames.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<details class="rigor-fixtures-toggle" open>
<summary>Tested by (3)</summary>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6IlQwMDA5IiwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoidHlwZWNoZWNrX2Vycm9yIn0sImZpbGVzIjpbeyJuYW1lIjoibWFpbi5tdGwiLCJzb3VyY2UiOiJpbXBvcnQgaGVscGVyOjpzZWNyZXQ7XG5mdW4gbWFpbigpIC0+IGk2NCB7IHJldHVybiBzZWNyZXQoKTsgfVxuIn0seyJuYW1lIjoiaGVscGVyLm10bCIsInNvdXJjZSI6ImZ1biBzZWNyZXQoKSAtPiBpNjQgeyByZXR1cm4gNDI7IH1cbiJ9XSwiaHJlZiI6Imh0dHBzOi8vZ2l0aHViLmNvbS9tZXRlbC1sYW5nL21ldGVsLWNvcmUvYmxvYi92MC4xNC4xL21ldGVsLWludGVycHJldGVyL3Rlc3RzL2ludGVncmF0aW9uL3NvdXJjZXMvbW9kdWxlX3NlbWFudGljcy9pbXBvcnRpbmdfcHJpdmF0ZV9pdGVtX2lzX3QwMDA5IiwibmFtZSI6ImltcG9ydGluZ19wcml2YXRlX2l0ZW1faXNfdDAwMDkifQ=="></details>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoic3VjY2VzcyJ9LCJmaWxlcyI6W3sibmFtZSI6Im1haW4ubXRsIiwic291cmNlIjoiaW1wb3J0IHRva2VuOjptYWtlO1xuZnVuIG1haW4oKSAtPiBpNjQgeyBsZXQgdCA6PSBtYWtlKCk7IHJldHVybiB0LmtpbmQ7IH1cbiJ9LHsibmFtZSI6InRva2VuLm10bCIsInNvdXJjZSI6InB1YmxpYyBzdHJ1Y3QgVG9rZW4geyBwdWJsaWMga2luZDogaTY0LCBvZmZzZXQ6IGk2NCB9XG5wdWJsaWMgZnVuIG1ha2UoKSAtPiBUb2tlbiB7IHJldHVybiBUb2tlbiB7IGtpbmQgPSAxMSwgb2Zmc2V0ID0gNyB9OyB9XG4ifV0sImhyZWYiOiJodHRwczovL2dpdGh1Yi5jb20vbWV0ZWwtbGFuZy9tZXRlbC1jb3JlL2Jsb2IvdjAuMTQuMS9tZXRlbC1pbnRlcnByZXRlci90ZXN0cy9pbnRlZ3JhdGlvbi9zb3VyY2VzL21vZHVsZV9zZW1hbnRpY3MvbWl4ZWRfdmlzaWJpbGl0eV9zdHJ1Y3RfYWxsb3dzX3B1YmxpY19maWVsZF9hY2Nlc3NfYWNyb3NzX21vZHVsZXMiLCJuYW1lIjoibWl4ZWRfdmlzaWJpbGl0eV9zdHJ1Y3RfYWxsb3dzX3B1YmxpY19maWVsZF9hY2Nlc3NfYWNyb3NzX21vZHVsZXMifQ=="></details>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6IlQwMDA5IiwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoidHlwZWNoZWNrX2Vycm9yIn0sImZpbGVzIjpbeyJuYW1lIjoibWFpbi5tdGwiLCJzb3VyY2UiOiIvLyAjNzc2OiBgcHVibGljYCBvbiBhIGZpZWxkIGlzIGNvbmRpdGlvbmFsIG9uIHRoZSBlbmNsb3Npbmcgc3RydWN0J3Mgb3duXG4vLyB2aXNpYmlsaXR5LCBub3QgYW4gaW5kZXBlbmRlbnQgZ3JhbnQuIGBTZWNyZXRgIGlzIG5vdCBgcHVibGljYCwgc28gaXRzXG4vLyBgcHVibGljIHZhbHVlOiBpNjRgIGZpZWxkIG11c3Qgc3RheSB1bnJlYWNoYWJsZSBhY3Jvc3MgYSBtb2R1bGUgYm91bmRhcnlcbi8vIGV2ZW4gb25jZSBhIGBTZWNyZXRgIGlzIG9idGFpbmVkIHZpYSBgbWFrZSgpYCwgYSBwdWJsaWMgZnVuY3Rpb24gdGhhdFxuLy8gbmV2ZXIgbmFtZXMgYFNlY3JldGAgaXRzZWxmLlxuaW1wb3J0IHRva2VuOjptYWtlO1xuZnVuIG1haW4oKSAtPiBpNjQge1xuICAgIGxldCBzIDo9IG1ha2UoKTtcbiAgICByZXR1cm4gcy52YWx1ZTtcbn1cbiJ9LHsibmFtZSI6InRva2VuLm10bCIsInNvdXJjZSI6InN0cnVjdCBTZWNyZXQgeyBwdWJsaWMgdmFsdWU6IGk2NCB9XG5wdWJsaWMgZnVuIG1ha2UoKSAtPiBTZWNyZXQgeyByZXR1cm4gU2VjcmV0IHsgdmFsdWUgPSA0MiB9OyB9XG4ifV0sImhyZWYiOiJodHRwczovL2dpdGh1Yi5jb20vbWV0ZWwtbGFuZy9tZXRlbC1jb3JlL2Jsb2IvdjAuMTQuMS9tZXRlbC1pbnRlcnByZXRlci90ZXN0cy9pbnRlZ3JhdGlvbi9zb3VyY2VzL21vZHVsZV9zZW1hbnRpY3MvcHVibGljX2ZpZWxkX29uX3ByaXZhdGVfc3RydWN0X2Fjcm9zc19tb2R1bGVzX2lzX3QwMDA5IiwibmFtZSI6InB1YmxpY19maWVsZF9vbl9wcml2YXRlX3N0cnVjdF9hY3Jvc3NfbW9kdWxlc19pc190MDAwOSJ9"></details>
</details>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.modules.visibility.legality-2}

A public function declaration must carry the explicit type annotations required for its
public API; an omitted required annotation is `T0010`.

<!-- rfc.py:last_reviewed cfff5473333ed9035b5f8fc9ecf285c8fc394a1d -->

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0031](../../rfcs/4-implemented/rfc-0031-topological-typechecker.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<p class="rigor-backlink"><em>Tested by</em></p>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6IlQwMDEwIiwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoidHlwZWNoZWNrX2Vycm9yIn0sImZpbGVzIjpbeyJuYW1lIjoibWFpbi5tdGwiLCJzb3VyY2UiOiJpbXBvcnQgaGVscGVyOjoqO1xuZnVuIG1haW4oKSAtPiBpNjQgeyByZXR1cm4gYW5zd2VyKCk7IH1cbiJ9LHsibmFtZSI6ImhlbHBlci5tdGwiLCJzb3VyY2UiOiJwdWJsaWMgZnVuIGFuc3dlcigpIHsgcmV0dXJuIDQyOyB9XG4ifV0sImhyZWYiOiJodHRwczovL2dpdGh1Yi5jb20vbWV0ZWwtbGFuZy9tZXRlbC1jb3JlL2Jsb2IvdjAuMTQuMS9tZXRlbC1pbnRlcnByZXRlci90ZXN0cy9pbnRlZ3JhdGlvbi9zb3VyY2VzL21vZHVsZV9zZW1hbnRpY3MvcHViX2Z1bl93aXRob3V0X3JldHVybl90eXBlX2lzX3QwMDEwIiwibmFtZSI6InB1Yl9mdW5fd2l0aG91dF9yZXR1cm5fdHlwZV9pc190MDAxMCJ9"></details>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.modules.visibility.legality-3}

Reading or assigning a private struct field from outside its declaring module is
rejected with `T0009`. The declaring module retains access to all of its own fields,
including private ones.

The rule follows the field, not the value's current type. A residual (`Token.{ offset }`,
[ownership](ownership.md)) keeps its struct's brand, so reading a private field through one,
projecting it (`t.{ offset }`), or writing it in a residual type (`Token.{ offset }`) from
outside the declaring module is the same `T0009`. A residual of public fields only
(`Token.{ kind }`) is unrestricted.

<!-- rfc.py:last_reviewed d1f40994 -->

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0032](../../rfcs/4-implemented/rfc-0032-field-level-visibility.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<details class="rigor-fixtures-toggle">
<summary>Tested by (7)</summary>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6IlQwMDA5IiwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoidHlwZWNoZWNrX2Vycm9yIn0sImZpbGVzIjpbeyJuYW1lIjoibWFpbi5tdGwiLCJzb3VyY2UiOiJpbXBvcnQgdG9rZW46Om1ha2U7XG5mdW4gbWFpbigpIC0+IGk2NCB7IHJldHVybiBtYWtlKCkub2Zmc2V0OyB9XG4ifSx7Im5hbWUiOiJ0b2tlbi5tdGwiLCJzb3VyY2UiOiJwdWJsaWMgc3RydWN0IFRva2VuIHsgcHVibGljIGtpbmQ6IGk2NCwgb2Zmc2V0OiBpNjQgfVxucHVibGljIGZ1biBtYWtlKCkgLT4gVG9rZW4geyByZXR1cm4gVG9rZW4geyBraW5kID0gMSwgb2Zmc2V0ID0gNyB9OyB9XG4ifV0sImhyZWYiOiJodHRwczovL2dpdGh1Yi5jb20vbWV0ZWwtbGFuZy9tZXRlbC1jb3JlL2Jsb2IvdjAuMTQuMS9tZXRlbC1pbnRlcnByZXRlci90ZXN0cy9pbnRlZ3JhdGlvbi9zb3VyY2VzL21vZHVsZV9zZW1hbnRpY3MvcHJpdmF0ZV9zdHJ1Y3RfZmllbGRfYWNjZXNzX2Fjcm9zc19tb2R1bGVzX2lzX3QwMDA5IiwibmFtZSI6InByaXZhdGVfc3RydWN0X2ZpZWxkX2FjY2Vzc19hY3Jvc3NfbW9kdWxlc19pc190MDAwOSJ9"></details>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6IlQwMDA5IiwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoidHlwZWNoZWNrX2Vycm9yIn0sImZpbGVzIjpbeyJuYW1lIjoibWFpbi5tdGwiLCJzb3VyY2UiOiJpbXBvcnQgdG9rZW46Om1ha2U7XG5mdW4gbWFpbigpIC0+IGk2NCB7IHZhciB0IDo9IG1ha2UoKTsgdC5vZmZzZXQgOj0gOTsgcmV0dXJuIHQua2luZDsgfVxuIn0seyJuYW1lIjoidG9rZW4ubXRsIiwic291cmNlIjoicHVibGljIHN0cnVjdCBUb2tlbiB7IHB1YmxpYyBraW5kOiBpNjQsIG9mZnNldDogaTY0IH1cbnB1YmxpYyBmdW4gbWFrZSgpIC0+IFRva2VuIHsgcmV0dXJuIFRva2VuIHsga2luZCA9IDEsIG9mZnNldCA9IDcgfTsgfVxuIn1dLCJocmVmIjoiaHR0cHM6Ly9naXRodWIuY29tL21ldGVsLWxhbmcvbWV0ZWwtY29yZS9ibG9iL3YwLjE0LjEvbWV0ZWwtaW50ZXJwcmV0ZXIvdGVzdHMvaW50ZWdyYXRpb24vc291cmNlcy9tb2R1bGVfc2VtYW50aWNzL3ByaXZhdGVfc3RydWN0X2ZpZWxkX2Fzc2lnbm1lbnRfYWNyb3NzX21vZHVsZXNfaXNfdDAwMDkiLCJuYW1lIjoicHJpdmF0ZV9zdHJ1Y3RfZmllbGRfYXNzaWdubWVudF9hY3Jvc3NfbW9kdWxlc19pc190MDAwOSJ9"></details>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoic3VjY2VzcyJ9LCJmaWxlcyI6W3sibmFtZSI6Im1haW4ubXRsIiwic291cmNlIjoicHVibGljIHN0cnVjdCBUb2tlbiB7IHB1YmxpYyBraW5kOiBpNjQsIG9mZnNldDogaTY0IH1cbiAgICAgICAgIGZ1biBvZmZzZXRfb2YodDogVG9rZW4pIC0+IGk2NCB7IHJldHVybiB0Lm9mZnNldDsgfVxuICAgICAgICAgZnVuIG1haW4oKSAtPiBpNjQgeyBsZXQgdCA6PSBUb2tlbiB7IGtpbmQgPSAzLCBvZmZzZXQgPSA5IH07IHJldHVybiBvZmZzZXRfb2YodCk7IH1cbiJ9XSwiaHJlZiI6Imh0dHBzOi8vZ2l0aHViLmNvbS9tZXRlbC1sYW5nL21ldGVsLWNvcmUvYmxvYi92MC4xNC4xL21ldGVsLWludGVycHJldGVyL3Rlc3RzL2ludGVncmF0aW9uL3NvdXJjZXMvbW9kdWxlX3NlbWFudGljcy9wcml2YXRlX3N0cnVjdF9maWVsZHNfcmVtYWluX2FjY2Vzc2libGVfaW5zaWRlX2RlY2xhcmluZ19tb2R1bGUiLCJuYW1lIjoicHJpdmF0ZV9zdHJ1Y3RfZmllbGRzX3JlbWFpbl9hY2Nlc3NpYmxlX2luc2lkZV9kZWNsYXJpbmdfbW9kdWxlIn0="></details>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoic3VjY2VzcyJ9LCJmaWxlcyI6W3sibmFtZSI6Im1haW4ubXRsIiwic291cmNlIjoiLy8gUmVzaWR1YWwgcHJpdmFjeSB4IHBhcnRpYWwgbW92ZXMgeCB3aG9sZS1yZWNvcmQgb3BlbiByb3dzIChtZXRlbC1jb3JlIzE0ODgsIFJGQy0wMTc5KTogY29kZVxuLy8gb3V0c2lkZSB0aGUgbW9kdWxlIG1vdmVzIGEgcHVibGljIG5vbi1Db3B5IGZpZWxkIG91dCwgd2hpY2ggbmFycm93cyB0aGUgdmFsdWUgdG8gYSByZXNpZHVhbFxuLy8gdGhhdCBoaWRlcyB0aGUgcHJpdmF0ZSBmaWVsZDsgdGhlIHJlc2lkdWFsIGlzIHBhc3NlZCBvbiBnZW5lcmljYWxseSBhbmQgdG8gYSBwcm9qZWN0aW9uLXRhaWxcbi8vIHBhcmFtZXRlciB0aGF0IG5hbWVzIG9ubHkgYSBwdWJsaWMgZmllbGQuXG5pbXBvcnQgdGlja2V0OjpUaWNrZXQ7XG5pbXBvcnQgdGlja2V0OjptYWtlO1xuXG5mdW4gaWRfb2Y8cm93IFI+KHQ6IFRpY2tldC57IGlkLCAuLlIgfSkgLT4gaTY0IHsgdC5pZCB9XG5mdW4gcGFzczxUPih4OiBUKSAtPiBUIHsgeCB9XG5cbmZ1biBtYWluKCkge1xuICAgIGxldCB0IDo9IG1ha2UoKTtcbiAgICBsZXQgbGFiZWwgOj0gdC5sYWJlbDtcbiAgICBsZXQga2VwdCA6PSBwYXNzKHQpO1xuICAgIGFzc2VydChpZF9vZihrZXB0KSA9PSAxKTtcbiAgICBhc3NlcnQobGFiZWwgPT0gXCJsXCIpO1xufVxuIn0seyJuYW1lIjoidGlja2V0Lm10bCIsInNvdXJjZSI6InB1YmxpYyBzdHJ1Y3QgVGlja2V0IHsgcHVibGljIGlkOiBpNjQsIHB1YmxpYyBsYWJlbDogU3RyaW5nLCBzZWNyZXQ6IFN0cmluZyB9XG5wdWJsaWMgZnVuIG1ha2UoKSAtPiBUaWNrZXQgeyBUaWNrZXQgeyBpZCA9IDEsIGxhYmVsID0gXCJsXCIudG9fc3RyaW5nKCksIHNlY3JldCA9IFwic1wiLnRvX3N0cmluZygpIH0gfVxuIn1dLCJocmVmIjoiaHR0cHM6Ly9naXRodWIuY29tL21ldGVsLWxhbmcvbWV0ZWwtY29yZS9ibG9iL3YwLjE0LjEvbWV0ZWwtaW50ZXJwcmV0ZXIvdGVzdHMvaW50ZWdyYXRpb24vc291cmNlcy9tb2R1bGVfc2VtYW50aWNzL3JlbGVhc2VfbWF0cml4X2xhdGVfcmVzaWR1YWxfcHJpdmFjeV93aXRoX3dob2xlX3JlY29yZF9wcm9qZWN0aW9uIiwibmFtZSI6InJlbGVhc2VfbWF0cml4X2xhdGVfcmVzaWR1YWxfcHJpdmFjeV93aXRoX3dob2xlX3JlY29yZF9wcm9qZWN0aW9uIn0="></details>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6IlQwMDA5IiwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6IjYiLCJzdGF0dXMiOiJ0eXBlY2hlY2tfZXJyb3IifSwiZmlsZXMiOlt7Im5hbWUiOiJtYWluLm10bCIsInNvdXJjZSI6Ii8vIG1ldGVsLWNvcmUjMTQ4ODogcHJvamVjdGluZyBhIHByaXZhdGUgZmllbGQgb3V0IG9mIGl0cyBkZWNsYXJpbmcgbW9kdWxlIGlzIHJlamVjdGVkLlxuaW1wb3J0IHRpY2tldDo6bWFrZTtcblxuZnVuIG1haW4oKSB7XG4gICAgbGV0IHQgOj0gbWFrZSgpO1xuICAgIGxldCBzIDo9IHQueyBzZWNyZXQgfTtcbn1cbiJ9LHsibmFtZSI6InRpY2tldC5tdGwiLCJzb3VyY2UiOiJwdWJsaWMgc3RydWN0IFRpY2tldCB7IHB1YmxpYyBpZDogaTY0LCBzZWNyZXQ6IFN0cmluZyB9XG5cbnB1YmxpYyBmdW4gbWFrZSgpIC0+IFRpY2tldCB7IFRpY2tldCB7IGlkID0gMSwgc2VjcmV0ID0gXCJzXCIudG9fc3RyaW5nKCkgfSB9XG4ifV0sImhyZWYiOiJodHRwczovL2dpdGh1Yi5jb20vbWV0ZWwtbGFuZy9tZXRlbC1jb3JlL2Jsb2IvdjAuMTQuMS9tZXRlbC1pbnRlcnByZXRlci90ZXN0cy9pbnRlZ3JhdGlvbi9zb3VyY2VzL21vZHVsZV9zZW1hbnRpY3MvcmVzaWR1YWxfcHJvamVjdGluZ19wcml2YXRlX2ZpZWxkX2Fjcm9zc19tb2R1bGVzX2lzX3QwMDA5IiwibmFtZSI6InJlc2lkdWFsX3Byb2plY3RpbmdfcHJpdmF0ZV9maWVsZF9hY3Jvc3NfbW9kdWxlc19pc190MDAwOSJ9"></details>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoic3VjY2VzcyJ9LCJmaWxlcyI6W3sibmFtZSI6Im1haW4ubXRsIiwic291cmNlIjoiLy8gbWV0ZWwtY29yZSMxNDg4OiB0aGUgdmlzaWJpbGl0eSBjaGVjayBsZWF2ZXMgcHVibGljIGZpZWxkcyBhbG9uZTsgYSBwdWJsaWMtZmllbGQgcmVzaWR1YWxcbi8vIGNhbiBiZSBwcm9qZWN0ZWQsIG5hbWVkLCBhbmQgcmVhZCBmcm9tIGFueXdoZXJlLlxuaW1wb3J0IHRpY2tldDo6VGlja2V0O1xuaW1wb3J0IHRpY2tldDo6bWFrZTtcblxuZnVuIGlkX29mKHQ6IFRpY2tldC57IGlkIH0pIC0+IGk2NCB7IHQuaWQgfVxuXG5mdW4gbWFpbigpIHtcbiAgICBsZXQgdCA6PSBtYWtlKCk7XG4gICAgbGV0IGp1c3RfaWQgOj0gdC57IGlkIH07XG4gICAgYXNzZXJ0KGlkX29mKGp1c3RfaWQpID09IDEpO1xufVxuIn0seyJuYW1lIjoidGlja2V0Lm10bCIsInNvdXJjZSI6InB1YmxpYyBzdHJ1Y3QgVGlja2V0IHsgcHVibGljIGlkOiBpNjQsIHNlY3JldDogU3RyaW5nIH1cblxucHVibGljIGZ1biBtYWtlKCkgLT4gVGlja2V0IHsgVGlja2V0IHsgaWQgPSAxLCBzZWNyZXQgPSBcInNcIi50b19zdHJpbmcoKSB9IH1cbiJ9XSwiaHJlZiI6Imh0dHBzOi8vZ2l0aHViLmNvbS9tZXRlbC1sYW5nL21ldGVsLWNvcmUvYmxvYi92MC4xNC4xL21ldGVsLWludGVycHJldGVyL3Rlc3RzL2ludGVncmF0aW9uL3NvdXJjZXMvbW9kdWxlX3NlbWFudGljcy9yZXNpZHVhbF9wcm9qZWN0aW5nX3B1YmxpY19maWVsZF9hY3Jvc3NfbW9kdWxlc19pc19hbGxvd2VkIiwibmFtZSI6InJlc2lkdWFsX3Byb2plY3RpbmdfcHVibGljX2ZpZWxkX2Fjcm9zc19tb2R1bGVzX2lzX2FsbG93ZWQifQ=="></details>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6IlQwMDA5IiwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6IjQiLCJzdGF0dXMiOiJ0eXBlY2hlY2tfZXJyb3IifSwiZmlsZXMiOlt7Im5hbWUiOiJtYWluLm10bCIsInNvdXJjZSI6Ii8vIG1ldGVsLWNvcmUjMTQ4ODogYSByZXNpZHVhbCB0eXBlIHdyaXR0ZW4gb3V0c2lkZSB0aGUgbW9kdWxlIGNhbm5vdCBuYW1lIGEgcHJpdmF0ZSBmaWVsZC5cbmltcG9ydCB0aWNrZXQ6OlRpY2tldDtcblxuZnVuIHRha2UodDogVGlja2V0Lnsgc2VjcmV0IH0pIHt9XG5cbmZ1biBtYWluKCkge31cbiJ9LHsibmFtZSI6InRpY2tldC5tdGwiLCJzb3VyY2UiOiJwdWJsaWMgc3RydWN0IFRpY2tldCB7IHB1YmxpYyBpZDogaTY0LCBzZWNyZXQ6IFN0cmluZyB9XG5cbnB1YmxpYyBmdW4gbWFrZSgpIC0+IFRpY2tldCB7IFRpY2tldCB7IGlkID0gMSwgc2VjcmV0ID0gXCJzXCIudG9fc3RyaW5nKCkgfSB9XG4ifV0sImhyZWYiOiJodHRwczovL2dpdGh1Yi5jb20vbWV0ZWwtbGFuZy9tZXRlbC1jb3JlL2Jsb2IvdjAuMTQuMS9tZXRlbC1pbnRlcnByZXRlci90ZXN0cy9pbnRlZ3JhdGlvbi9zb3VyY2VzL21vZHVsZV9zZW1hbnRpY3MvcmVzaWR1YWxfdHlwZV9uYW1pbmdfcHJpdmF0ZV9maWVsZF9hY3Jvc3NfbW9kdWxlc19pc190MDAwOSIsIm5hbWUiOiJyZXNpZHVhbF90eXBlX25hbWluZ19wcml2YXRlX2ZpZWxkX2Fjcm9zc19tb2R1bGVzX2lzX3QwMDA5In0="></details>
</details>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.modules.visibility.legality-4}

Constructing a struct literal outside its declaring module is rejected with `T0009` if
it names any private field. A module-local constructor or helper function may still
construct the value.

<!-- rfc.py:last_reviewed cfff5473333ed9035b5f8fc9ecf285c8fc394a1d -->

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0032](../../rfcs/4-implemented/rfc-0032-field-level-visibility.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<p class="rigor-backlink"><em>Tested by</em></p>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6IlQwMDA5IiwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoidHlwZWNoZWNrX2Vycm9yIn0sImZpbGVzIjpbeyJuYW1lIjoibWFpbi5tdGwiLCJzb3VyY2UiOiJpbXBvcnQgdG9rZW46OlRva2VuO1xuZnVuIG1haW4oKSB7IGxldCB0IDo9IFRva2VuIHsga2luZCA9IDEsIG9mZnNldCA9IDcgfTsgcHJpbnQodC5raW5kKTsgfVxuIn0seyJuYW1lIjoidG9rZW4ubXRsIiwic291cmNlIjoicHVibGljIHN0cnVjdCBUb2tlbiB7IHB1YmxpYyBraW5kOiBpNjQsIG9mZnNldDogaTY0IH1cbiJ9XSwiaHJlZiI6Imh0dHBzOi8vZ2l0aHViLmNvbS9tZXRlbC1sYW5nL21ldGVsLWNvcmUvYmxvYi92MC4xNC4xL21ldGVsLWludGVycHJldGVyL3Rlc3RzL2ludGVncmF0aW9uL3NvdXJjZXMvbW9kdWxlX3NlbWFudGljcy9wcml2YXRlX3N0cnVjdF9maWVsZF9jb25zdHJ1Y3Rpb25fYWNyb3NzX21vZHVsZXNfaXNfdDAwMDkiLCJuYW1lIjoicHJpdmF0ZV9zdHJ1Y3RfZmllbGRfY29uc3RydWN0aW9uX2Fjcm9zc19tb2R1bGVzX2lzX3QwMDA5In0="></details>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.modules.visibility.legality-5}

Declaring a field `public` on a struct that is not itself `public` produces a compiler
warning: the field cannot be reached across a module boundary through a private type,
so the `public` marker on it has no effect from outside the declaring module.

<!-- rfc.py:last_reviewed cfff5473333ed9035b5f8fc9ecf285c8fc394a1d -->

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0032](../../rfcs/4-implemented/rfc-0032-field-level-visibility.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<details class="rigor-fixtures-toggle" open>
<summary>Tested by (2)</summary>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoic3VjY2VzcyJ9LCJmaWxlcyI6W3sibmFtZSI6InB1YmxpY19maWVsZF9vbl9wcml2YXRlX3N0cnVjdF93YXJucy5tdGwiLCJzb3VyY2UiOiJzdHJ1Y3QgVGhpbmcge1xuICAgIHB1YmxpYyB2YWx1ZTogaTY0LFxufVxuXG5mdW4gbWFpbigpIHtcbiAgICBsZXQgdCA6PSBUaGluZyB7IHZhbHVlID0gMSB9O1xuICAgIHByaW50bG4odC52YWx1ZS50b19zdHJpbmcoKSk7XG59XG4ifV0sImhyZWYiOiJodHRwczovL2dpdGh1Yi5jb20vbWV0ZWwtbGFuZy9tZXRlbC1jb3JlL2Jsb2IvdjAuMTQuMS9tZXRlbC1pbnRlcnByZXRlci90ZXN0cy9pbnRlZ3JhdGlvbi9zb3VyY2VzL3R5cGVjaGVja2luZy9zdHJ1Y3RzL3B1YmxpY19maWVsZF9vbl9wcml2YXRlX3N0cnVjdF93YXJucy5tdGwiLCJuYW1lIjoicHVibGljX2ZpZWxkX29uX3ByaXZhdGVfc3RydWN0X3dhcm5zLm10bCJ9"></details>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6IlQwMDA5IiwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoidHlwZWNoZWNrX2Vycm9yIn0sImZpbGVzIjpbeyJuYW1lIjoibWFpbi5tdGwiLCJzb3VyY2UiOiIvLyAjNzc2OiBgcHVibGljYCBvbiBhIGZpZWxkIGlzIGNvbmRpdGlvbmFsIG9uIHRoZSBlbmNsb3Npbmcgc3RydWN0J3Mgb3duXG4vLyB2aXNpYmlsaXR5LCBub3QgYW4gaW5kZXBlbmRlbnQgZ3JhbnQuIGBTZWNyZXRgIGlzIG5vdCBgcHVibGljYCwgc28gaXRzXG4vLyBgcHVibGljIHZhbHVlOiBpNjRgIGZpZWxkIG11c3Qgc3RheSB1bnJlYWNoYWJsZSBhY3Jvc3MgYSBtb2R1bGUgYm91bmRhcnlcbi8vIGV2ZW4gb25jZSBhIGBTZWNyZXRgIGlzIG9idGFpbmVkIHZpYSBgbWFrZSgpYCwgYSBwdWJsaWMgZnVuY3Rpb24gdGhhdFxuLy8gbmV2ZXIgbmFtZXMgYFNlY3JldGAgaXRzZWxmLlxuaW1wb3J0IHRva2VuOjptYWtlO1xuZnVuIG1haW4oKSAtPiBpNjQge1xuICAgIGxldCBzIDo9IG1ha2UoKTtcbiAgICByZXR1cm4gcy52YWx1ZTtcbn1cbiJ9LHsibmFtZSI6InRva2VuLm10bCIsInNvdXJjZSI6InN0cnVjdCBTZWNyZXQgeyBwdWJsaWMgdmFsdWU6IGk2NCB9XG5wdWJsaWMgZnVuIG1ha2UoKSAtPiBTZWNyZXQgeyByZXR1cm4gU2VjcmV0IHsgdmFsdWUgPSA0MiB9OyB9XG4ifV0sImhyZWYiOiJodHRwczovL2dpdGh1Yi5jb20vbWV0ZWwtbGFuZy9tZXRlbC1jb3JlL2Jsb2IvdjAuMTQuMS9tZXRlbC1pbnRlcnByZXRlci90ZXN0cy9pbnRlZ3JhdGlvbi9zb3VyY2VzL21vZHVsZV9zZW1hbnRpY3MvcHVibGljX2ZpZWxkX29uX3ByaXZhdGVfc3RydWN0X2Fjcm9zc19tb2R1bGVzX2lzX3QwMDA5IiwibmFtZSI6InB1YmxpY19maWVsZF9vbl9wcml2YXRlX3N0cnVjdF9hY3Jvc3NfbW9kdWxlc19pc190MDAwOSJ9"></details>
</details>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.modules.visibility.legality-6}

Named fields of an enum struct-like variant follow the same visibility rules as an
ordinary struct's fields: constructing a variant literal outside the enum's declaring
module and naming a private field is rejected with `T0009`, the same as for a struct.

<!-- rfc.py:last_reviewed cfff5473333ed9035b5f8fc9ecf285c8fc394a1d -->

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0032](../../rfcs/4-implemented/rfc-0032-field-level-visibility.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<p class="rigor-backlink"><em>Tested by</em></p>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6IlQwMDA5IiwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoidHlwZWNoZWNrX2Vycm9yIn0sImZpbGVzIjpbeyJuYW1lIjoibWFpbi5tdGwiLCJzb3VyY2UiOiJpbXBvcnQgdG9rZW46OlRva2VuO1xuZnVuIG1haW4oKSB7IGxldCB0IDo9IFRva2VuOjpJbm5lciB7IGtpbmQgPSAxLCBvZmZzZXQgPSA3IH07IH1cbiJ9LHsibmFtZSI6InRva2VuLm10bCIsInNvdXJjZSI6InB1YmxpYyBlbnVtIFRva2VuIHsgSW5uZXIgeyBwdWJsaWMga2luZDogaTY0LCBvZmZzZXQ6IGk2NCB9IH1cbiJ9XSwiaHJlZiI6Imh0dHBzOi8vZ2l0aHViLmNvbS9tZXRlbC1sYW5nL21ldGVsLWNvcmUvYmxvYi92MC4xNC4xL21ldGVsLWludGVycHJldGVyL3Rlc3RzL2ludGVncmF0aW9uL3NvdXJjZXMvbW9kdWxlX3NlbWFudGljcy9wcml2YXRlX2VudW1fdmFyaWFudF9maWVsZF9jb25zdHJ1Y3Rpb25fYWNyb3NzX21vZHVsZXNfaXNfdDAwMDkiLCJuYW1lIjoicHJpdmF0ZV9lbnVtX3ZhcmlhbnRfZmllbGRfY29uc3RydWN0aW9uX2Fjcm9zc19tb2R1bGVzX2lzX3QwMDA5In0="></details>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.modules.visibility.legality-7}

Naming a private field in a struct pattern from outside the struct's declaring module is
rejected with `T0009`. The pattern must either omit that field with a trailing `..`, or
be written inside the declaring module, where private fields remain nameable.

<!-- rfc.py:last_reviewed cfff5473333ed9035b5f8fc9ecf285c8fc394a1d -->

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0032](../../rfcs/4-implemented/rfc-0032-field-level-visibility.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<details class="rigor-fixtures-toggle" open>
<summary>Tested by (2)</summary>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6IlQwMDA5IiwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6IjciLCJzdGF0dXMiOiJ0eXBlY2hlY2tfZXJyb3IifSwiZmlsZXMiOlt7Im5hbWUiOiJtYWluLm10bCIsInNvdXJjZSI6ImltcG9ydCB0b2tlbjo6VG9rZW47XG5pbXBvcnQgdG9rZW46Om1ha2VfdG9rZW47XG5cbmZ1biBtYWluKCkge1xuICAgIGxldCB0IDo9IG1ha2VfdG9rZW4oMSwgMik7XG4gICAgbGV0IHggOj0gbWF0Y2ggKHQpIHtcbiAgICAgICAgVG9rZW4geyBraW5kLCBvZmZzZXQgfSA9PiBraW5kICsgb2Zmc2V0LFxuICAgIH07XG4gICAgcHJpbnRsbih4KTtcbn1cbiJ9LHsibmFtZSI6InRva2VuLm10bCIsInNvdXJjZSI6InB1YmxpYyBzdHJ1Y3QgVG9rZW4geyBwdWJsaWMga2luZDogaTY0LCBvZmZzZXQ6IGk2NCB9XG5cbnB1YmxpYyBmdW4gbWFrZV90b2tlbihraW5kOiBpNjQsIG9mZnNldDogaTY0KSAtPiBUb2tlbiB7XG4gICAgcmV0dXJuIFRva2VuIHsga2luZCA9IGtpbmQsIG9mZnNldCA9IG9mZnNldCB9O1xufVxuIn1dLCJocmVmIjoiaHR0cHM6Ly9naXRodWIuY29tL21ldGVsLWxhbmcvbWV0ZWwtY29yZS9ibG9iL3YwLjE0LjEvbWV0ZWwtaW50ZXJwcmV0ZXIvdGVzdHMvaW50ZWdyYXRpb24vc291cmNlcy9tb2R1bGVfc2VtYW50aWNzL3N0cnVjdF9wYXR0ZXJuX25hbWVzX3ByaXZhdGVfZmllbGRfYWNyb3NzX21vZHVsZXNfaXNfdDAwMDkiLCJuYW1lIjoic3RydWN0X3BhdHRlcm5fbmFtZXNfcHJpdmF0ZV9maWVsZF9hY3Jvc3NfbW9kdWxlc19pc190MDAwOSJ9"></details>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoic3VjY2VzcyJ9LCJmaWxlcyI6W3sibmFtZSI6Im1haW4ubXRsIiwic291cmNlIjoiaW1wb3J0IHRva2VuOjpUb2tlbjtcbmltcG9ydCB0b2tlbjo6bWFrZV90b2tlbjtcblxuZnVuIG1haW4oKSB7XG4gICAgbGV0IHQgOj0gbWFrZV90b2tlbigxLCAyKTtcbiAgICBsZXQgeCA6PSBtYXRjaCAodCkge1xuICAgICAgICBUb2tlbiB7IGtpbmQsIC4uIH0gPT4ga2luZCxcbiAgICB9O1xuICAgIHByaW50bG4oeCk7XG59XG4ifSx7Im5hbWUiOiJ0b2tlbi5tdGwiLCJzb3VyY2UiOiJwdWJsaWMgc3RydWN0IFRva2VuIHsgcHVibGljIGtpbmQ6IGk2NCwgb2Zmc2V0OiBpNjQgfVxuXG5wdWJsaWMgZnVuIG1ha2VfdG9rZW4oa2luZDogaTY0LCBvZmZzZXQ6IGk2NCkgLT4gVG9rZW4ge1xuICAgIHJldHVybiBUb2tlbiB7IGtpbmQgPSBraW5kLCBvZmZzZXQgPSBvZmZzZXQgfTtcbn1cbiJ9XSwiaHJlZiI6Imh0dHBzOi8vZ2l0aHViLmNvbS9tZXRlbC1sYW5nL21ldGVsLWNvcmUvYmxvYi92MC4xNC4xL21ldGVsLWludGVycHJldGVyL3Rlc3RzL2ludGVncmF0aW9uL3NvdXJjZXMvbW9kdWxlX3NlbWFudGljcy9zdHJ1Y3RfcGF0dGVybl9yZXN0X29taXRzX3ByaXZhdGVfZmllbGRfYWNyb3NzX21vZHVsZXMiLCJuYW1lIjoic3RydWN0X3BhdHRlcm5fcmVzdF9vbWl0c19wcml2YXRlX2ZpZWxkX2Fjcm9zc19tb2R1bGVzIn0="></details>
</details>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.modules.visibility.legality-8}

A `public` function, a `public` inherent method, or a `public` field of a `public` struct
may not write a residual type that names a private field of the struct
(`public fun peek(t: Ticket) -> Ticket.{ secret }`): the field's name would become part of
the module's API. The declaration is rejected with `T0009`. Private functions, aspect impl
methods (which take their visibility from the aspect), and residuals that name only
`public` fields are unrestricted. Naming a private field of *another* module's struct is
already rejected by [legality-3](#spec.modules.visibility.legality-3).

<!-- rfc.py:last_reviewed d1f40994 -->

<!-- rfc.py:fixtures:start -->
<details class="rigor-fixtures-toggle">
<summary>Tested by (7)</summary>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoic3VjY2VzcyJ9LCJmaWxlcyI6W3sibmFtZSI6InByaXZhdGVfc2lnbmF0dXJlX21heV9uYW1lX3ByaXZhdGVfZmllbGQubXRsIiwic291cmNlIjoiLy8gbWV0ZWwtY29yZSMxNDg4OiBvbmx5IHB1YmxpYyBzaWduYXR1cmVzIGFyZSByZXN0cmljdGVkLiBBIHByaXZhdGUgZnVuY3Rpb24gYW5kIGEgcHVibGljXG4vLyBzaWduYXR1cmUgdGhhdCBuYW1lcyBvbmx5IHB1YmxpYyBmaWVsZHMgYXJlIGJvdGggZmluZS5cbnB1YmxpYyBzdHJ1Y3QgVGlja2V0IHsgcHVibGljIGlkOiBpNjQsIHNlY3JldDogU3RyaW5nIH1cblxuZnVuIGhpZGUodDogVGlja2V0KSAtPiBUaWNrZXQueyBzZWNyZXQgfSB7IHQueyBzZWNyZXQgfSB9XG5cbnB1YmxpYyBmdW4gaWRzKHQ6IFRpY2tldCkgLT4gVGlja2V0LnsgaWQgfSB7IHQueyBpZCB9IH1cblxuZnVuIG1haW4oKSB7XG4gICAgbGV0IHUgOj0gVGlja2V0IHsgaWQgPSAyLCBzZWNyZXQgPSBcInVcIi50b19zdHJpbmcoKSB9O1xuICAgIGFzc2VydChoaWRlKHUpLnNlY3JldCA9PSBcInVcIik7XG4gICAgbGV0IHYgOj0gVGlja2V0IHsgaWQgPSAzLCBzZWNyZXQgPSBcInZcIi50b19zdHJpbmcoKSB9O1xuICAgIGFzc2VydChpZHModikuaWQgPT0gMyk7XG59XG4ifV0sImhyZWYiOiJodHRwczovL2dpdGh1Yi5jb20vbWV0ZWwtbGFuZy9tZXRlbC1jb3JlL2Jsb2IvdjAuMTQuMS9tZXRlbC1pbnRlcnByZXRlci90ZXN0cy9pbnRlZ3JhdGlvbi9zb3VyY2VzL3R5cGVjaGVja2luZy9yZWNvcmRzL3ByaXZhdGVfc2lnbmF0dXJlX21heV9uYW1lX3ByaXZhdGVfZmllbGQubXRsIiwibmFtZSI6InByaXZhdGVfc2lnbmF0dXJlX21heV9uYW1lX3ByaXZhdGVfZmllbGQubXRsIn0="></details>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6IlQwMDA5IiwiY29sIjpudWxsLCJjb250YWlucyI6InB1YmxpYyBmaWVsZCBgaW5uZXJgIiwibGluZSI6IjMiLCJzdGF0dXMiOiJ0eXBlY2hlY2tfZXJyb3IifSwiZmlsZXMiOlt7Im5hbWUiOiJwdWJsaWNfZmllbGRfbmFtZXNfcHJpdmF0ZV9maWVsZF9yZWplY3RlZC5tdGwiLCJzb3VyY2UiOiIvLyBtZXRlbC1jb3JlIzE0ODg6IGEgcHVibGljIGZpZWxkIG9mIGEgcHVibGljIHN0cnVjdCBpcyBwYXJ0IG9mIGl0cyBBUEkgdG9vLlxucHVibGljIHN0cnVjdCBUaWNrZXQgeyBwdWJsaWMgaWQ6IGk2NCwgc2VjcmV0OiBTdHJpbmcgfVxucHVibGljIHN0cnVjdCBIb2xkZXIgeyBwdWJsaWMgaW5uZXI6IFRpY2tldC57IHNlY3JldCB9IH0gLy8gRVJST1JbVDAwMDldXG5cbmZ1biBtYWluKCkge31cbiJ9XSwiaHJlZiI6Imh0dHBzOi8vZ2l0aHViLmNvbS9tZXRlbC1sYW5nL21ldGVsLWNvcmUvYmxvYi92MC4xNC4xL21ldGVsLWludGVycHJldGVyL3Rlc3RzL2ludGVncmF0aW9uL3NvdXJjZXMvdHlwZWNoZWNraW5nL3JlY29yZHMvcHVibGljX2ZpZWxkX25hbWVzX3ByaXZhdGVfZmllbGRfcmVqZWN0ZWQubXRsIiwibmFtZSI6InB1YmxpY19maWVsZF9uYW1lc19wcml2YXRlX2ZpZWxkX3JlamVjdGVkLm10bCJ9"></details>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6IlQwMDA5IiwiY29sIjpudWxsLCJjb250YWlucyI6InB1YmxpYyBmdW5jdGlvbiBgcmVhZGAiLCJsaW5lIjoiNCIsInN0YXR1cyI6InR5cGVjaGVja19lcnJvciJ9LCJmaWxlcyI6W3sibmFtZSI6InB1YmxpY19mdW5jdGlvbl9wYXJhbV9uYW1lc19wcml2YXRlX2ZpZWxkX3JlamVjdGVkLm10bCIsInNvdXJjZSI6Ii8vIG1ldGVsLWNvcmUjMTQ4ODogdGhlIHBhcmFtZXRlciBwb3NpdGlvbiBpcyBhIHB1YmxpYyBzaWduYXR1cmUgdG9vLlxucHVibGljIHN0cnVjdCBUaWNrZXQgeyBwdWJsaWMgaWQ6IGk2NCwgc2VjcmV0OiBTdHJpbmcgfVxuXG5wdWJsaWMgZnVuIHJlYWQodDogVGlja2V0Lnsgc2VjcmV0IH0pIC0+ICgpIHt9IC8vIEVSUk9SW1QwMDA5XVxuXG5mdW4gbWFpbigpIHt9XG4ifV0sImhyZWYiOiJodHRwczovL2dpdGh1Yi5jb20vbWV0ZWwtbGFuZy9tZXRlbC1jb3JlL2Jsb2IvdjAuMTQuMS9tZXRlbC1pbnRlcnByZXRlci90ZXN0cy9pbnRlZ3JhdGlvbi9zb3VyY2VzL3R5cGVjaGVja2luZy9yZWNvcmRzL3B1YmxpY19mdW5jdGlvbl9wYXJhbV9uYW1lc19wcml2YXRlX2ZpZWxkX3JlamVjdGVkLm10bCIsIm5hbWUiOiJwdWJsaWNfZnVuY3Rpb25fcGFyYW1fbmFtZXNfcHJpdmF0ZV9maWVsZF9yZWplY3RlZC5tdGwifQ=="></details>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6IlQwMDA5IiwiY29sIjpudWxsLCJjb250YWlucyI6InB1YmxpYyBmdW5jdGlvbiBgbmFycm93YCIsImxpbmUiOiI0Iiwic3RhdHVzIjoidHlwZWNoZWNrX2Vycm9yIn0sImZpbGVzIjpbeyJuYW1lIjoicHVibGljX2Z1bmN0aW9uX3JldHVybl9uYW1lc19wcml2YXRlX2ZpZWxkX3JlamVjdGVkLm10bCIsInNvdXJjZSI6Ii8vIG1ldGVsLWNvcmUjMTQ4ODogYSBwdWJsaWMgc2lnbmF0dXJlIG1heSBub3QgbmFtZSBhIHByaXZhdGUgZmllbGQgaW4gYSByZXNpZHVhbCB0eXBlLlxucHVibGljIHN0cnVjdCBUaWNrZXQgeyBwdWJsaWMgaWQ6IGk2NCwgc2VjcmV0OiBTdHJpbmcgfVxuXG5wdWJsaWMgZnVuIG5hcnJvdyh0OiBUaWNrZXQpIC0+IFRpY2tldC57IHNlY3JldCB9IHsgLy8gRVJST1JbVDAwMDldXG4gICAgdC57IHNlY3JldCB9XG59XG5cbmZ1biBtYWluKCkge31cbiJ9XSwiaHJlZiI6Imh0dHBzOi8vZ2l0aHViLmNvbS9tZXRlbC1sYW5nL21ldGVsLWNvcmUvYmxvYi92MC4xNC4xL21ldGVsLWludGVycHJldGVyL3Rlc3RzL2ludGVncmF0aW9uL3NvdXJjZXMvdHlwZWNoZWNraW5nL3JlY29yZHMvcHVibGljX2Z1bmN0aW9uX3JldHVybl9uYW1lc19wcml2YXRlX2ZpZWxkX3JlamVjdGVkLm10bCIsIm5hbWUiOiJwdWJsaWNfZnVuY3Rpb25fcmV0dXJuX25hbWVzX3ByaXZhdGVfZmllbGRfcmVqZWN0ZWQubXRsIn0="></details>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6IlQwMDA5IiwiY29sIjpudWxsLCJjb250YWlucyI6InB1YmxpYyBmdW5jdGlvbiBgcGVla2AiLCJsaW5lIjoiNSIsInN0YXR1cyI6InR5cGVjaGVja19lcnJvciJ9LCJmaWxlcyI6W3sibmFtZSI6InB1YmxpY19tZXRob2RfbmFtZXNfcHJpdmF0ZV9maWVsZF9yZWplY3RlZC5tdGwiLCJzb3VyY2UiOiIvLyBtZXRlbC1jb3JlIzE0ODg6IGFuZCBzbyBpcyBhIHB1YmxpYyBpbmhlcmVudCBtZXRob2QuXG5wdWJsaWMgc3RydWN0IFRpY2tldCB7IHB1YmxpYyBpZDogaTY0LCBzZWNyZXQ6IFN0cmluZyB9XG5cbmV4dGVuZCBUaWNrZXQge1xuICAgIHB1YmxpYyBmdW4gcGVlayhzZWxmKSAtPiBUaWNrZXQueyBzZWNyZXQgfSB7IC8vIEVSUk9SW1QwMDA5XVxuICAgICAgICBzZWxmLnsgc2VjcmV0IH1cbiAgICB9XG59XG5cbmZ1biBtYWluKCkge31cbiJ9XSwiaHJlZiI6Imh0dHBzOi8vZ2l0aHViLmNvbS9tZXRlbC1sYW5nL21ldGVsLWNvcmUvYmxvYi92MC4xNC4xL21ldGVsLWludGVycHJldGVyL3Rlc3RzL2ludGVncmF0aW9uL3NvdXJjZXMvdHlwZWNoZWNraW5nL3JlY29yZHMvcHVibGljX21ldGhvZF9uYW1lc19wcml2YXRlX2ZpZWxkX3JlamVjdGVkLm10bCIsIm5hbWUiOiJwdWJsaWNfbWV0aG9kX25hbWVzX3ByaXZhdGVfZmllbGRfcmVqZWN0ZWQubXRsIn0="></details>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6IlQwMDA5IiwiY29sIjpudWxsLCJjb250YWlucyI6InB1YmxpYyBmdW5jdGlvbiBgcGVla2AiLCJsaW5lIjoiNyIsInN0YXR1cyI6InR5cGVjaGVja19lcnJvciJ9LCJmaWxlcyI6W3sibmFtZSI6InJlbGVhc2VfbWF0cml4X2xhdGVfcHVibGljX2FsaWFzX25hbWVzX3ByaXZhdGVfZmllbGRfcmVqZWN0ZWQubXRsIiwic291cmNlIjoiLy8gUmVzaWR1YWwgcHJpdmFjeSB4IHR5cGUgYWxpYXNlcyAobWV0ZWwtY29yZSMxNDg4LCBSRkMtMDE2MCk6IGFuIGFsaWFzIHRoYXQgc3BlbGxzIGEgcHJpdmF0ZVxuLy8gZmllbGQgZG9lcyBub3QgaGlkZSBpdDsgdGhlIHB1YmxpYyBzaWduYXR1cmUgdXNpbmcgdGhlIGFsaWFzIGlzIHJlamVjdGVkIGFmdGVyIGV4cGFuc2lvbi5cbnB1YmxpYyBzdHJ1Y3QgVGlja2V0IHsgcHVibGljIGlkOiBpNjQsIHNlY3JldDogU3RyaW5nIH1cblxudHlwZSBQZWVrIDo9IFRpY2tldC57IHNlY3JldCB9O1xuXG5wdWJsaWMgZnVuIHBlZWsodDogVGlja2V0KSAtPiBQZWVrIHsgLy8gRVJST1JbVDAwMDldXG4gICAgdC57IHNlY3JldCB9XG59XG5cbmZ1biBtYWluKCkge31cbiJ9XSwiaHJlZiI6Imh0dHBzOi8vZ2l0aHViLmNvbS9tZXRlbC1sYW5nL21ldGVsLWNvcmUvYmxvYi92MC4xNC4xL21ldGVsLWludGVycHJldGVyL3Rlc3RzL2ludGVncmF0aW9uL3NvdXJjZXMvdHlwZWNoZWNraW5nL3JlY29yZHMvcmVsZWFzZV9tYXRyaXhfbGF0ZV9wdWJsaWNfYWxpYXNfbmFtZXNfcHJpdmF0ZV9maWVsZF9yZWplY3RlZC5tdGwiLCJuYW1lIjoicmVsZWFzZV9tYXRyaXhfbGF0ZV9wdWJsaWNfYWxpYXNfbmFtZXNfcHJpdmF0ZV9maWVsZF9yZWplY3RlZC5tdGwifQ=="></details>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoic3VjY2VzcyJ9LCJmaWxlcyI6W3sibmFtZSI6Im1haW4ubXRsIiwic291cmNlIjoiLy8gUmVzaWR1YWwgcHJpdmFjeSB4IHBhcnRpYWwgbW92ZXMgeCB3aG9sZS1yZWNvcmQgb3BlbiByb3dzIChtZXRlbC1jb3JlIzE0ODgsIFJGQy0wMTc5KTogY29kZVxuLy8gb3V0c2lkZSB0aGUgbW9kdWxlIG1vdmVzIGEgcHVibGljIG5vbi1Db3B5IGZpZWxkIG91dCwgd2hpY2ggbmFycm93cyB0aGUgdmFsdWUgdG8gYSByZXNpZHVhbFxuLy8gdGhhdCBoaWRlcyB0aGUgcHJpdmF0ZSBmaWVsZDsgdGhlIHJlc2lkdWFsIGlzIHBhc3NlZCBvbiBnZW5lcmljYWxseSBhbmQgdG8gYSBwcm9qZWN0aW9uLXRhaWxcbi8vIHBhcmFtZXRlciB0aGF0IG5hbWVzIG9ubHkgYSBwdWJsaWMgZmllbGQuXG5pbXBvcnQgdGlja2V0OjpUaWNrZXQ7XG5pbXBvcnQgdGlja2V0OjptYWtlO1xuXG5mdW4gaWRfb2Y8cm93IFI+KHQ6IFRpY2tldC57IGlkLCAuLlIgfSkgLT4gaTY0IHsgdC5pZCB9XG5mdW4gcGFzczxUPih4OiBUKSAtPiBUIHsgeCB9XG5cbmZ1biBtYWluKCkge1xuICAgIGxldCB0IDo9IG1ha2UoKTtcbiAgICBsZXQgbGFiZWwgOj0gdC5sYWJlbDtcbiAgICBsZXQga2VwdCA6PSBwYXNzKHQpO1xuICAgIGFzc2VydChpZF9vZihrZXB0KSA9PSAxKTtcbiAgICBhc3NlcnQobGFiZWwgPT0gXCJsXCIpO1xufVxuIn0seyJuYW1lIjoidGlja2V0Lm10bCIsInNvdXJjZSI6InB1YmxpYyBzdHJ1Y3QgVGlja2V0IHsgcHVibGljIGlkOiBpNjQsIHB1YmxpYyBsYWJlbDogU3RyaW5nLCBzZWNyZXQ6IFN0cmluZyB9XG5wdWJsaWMgZnVuIG1ha2UoKSAtPiBUaWNrZXQgeyBUaWNrZXQgeyBpZCA9IDEsIGxhYmVsID0gXCJsXCIudG9fc3RyaW5nKCksIHNlY3JldCA9IFwic1wiLnRvX3N0cmluZygpIH0gfVxuIn1dLCJocmVmIjoiaHR0cHM6Ly9naXRodWIuY29tL21ldGVsLWxhbmcvbWV0ZWwtY29yZS9ibG9iL3YwLjE0LjEvbWV0ZWwtaW50ZXJwcmV0ZXIvdGVzdHMvaW50ZWdyYXRpb24vc291cmNlcy9tb2R1bGVfc2VtYW50aWNzL3JlbGVhc2VfbWF0cml4X2xhdGVfcmVzaWR1YWxfcHJpdmFjeV93aXRoX3dob2xlX3JlY29yZF9wcm9qZWN0aW9uIiwibmFtZSI6InJlbGVhc2VfbWF0cml4X2xhdGVfcmVzaWR1YWxfcHJpdmFjeV93aXRoX3dob2xlX3JlY29yZF9wcm9qZWN0aW9uIn0="></details>
</details>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.modules.visibility.legality-9}

A name that a module provides as a public type and a private function can be imported: the
import is accepted and brings in the type. Using the name as a value is then rejected with
`T0009`, reported at the use rather than at the import, and a local binding of that name
shadows it. A name the module provides publicly in no namespace is rejected at the import:
`T0009` when it is private there, `T0003` when it does not exist.

<!-- rfc.py:last_reviewed fa44859ef74e6592a3ef7ffe086e4afb0de8743e -->

<!-- rfc.py:fixtures:start -->
<details class="rigor-fixtures-toggle" open>
<summary>Tested by (3)</summary>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoic3VjY2VzcyJ9LCJmaWxlcyI6W3sibmFtZSI6Im1haW4ubXRsIiwic291cmNlIjoiaW1wb3J0IGxpYjo6Rm9vO1xuXG5mdW4gbWFpbigpIHtcbiAgICBsZXQgRm9vIDo9IDc7XG4gICAgYXNzZXJ0KEZvbyA9PSA3KTtcbn1cbiJ9LHsibmFtZSI6ImxpYi5tdGwiLCJzb3VyY2UiOiIvLyBtZXRlbC1jb3JlIzE1NzU6IHRoZSBwcml2YXRlIGZ1bmN0aW9uIGBGb29gIGlzIG5vdCBpbXBvcnRhYmxlLCBzbyBhIGxvY2FsIG9mIHRoYXQgbmFtZSBpcyB0aGUgb25seVxuLy8gYEZvb2AgaW4gc2NvcGUgYW5kIHRoZSBtaXNzaW5nLWZ1bmN0aW9uIGVycm9yIG11c3Qgbm90IGZpcmUuXG5wdWJsaWMgc3RydWN0IEZvbyB7XG4gICAgcHVibGljIHg6IGk2NCxcbn1cblxuZnVuIEZvbygpIC0+IGk2NCB7XG4gICAgNVxufVxuIn1dLCJocmVmIjoiaHR0cHM6Ly9naXRodWIuY29tL21ldGVsLWxhbmcvbWV0ZWwtY29yZS9ibG9iL3YwLjE0LjEvbWV0ZWwtaW50ZXJwcmV0ZXIvdGVzdHMvaW50ZWdyYXRpb24vc291cmNlcy9ldmFsdWF0b3Ivc3RydWN0cy9hX2xvY2FsX3NoYWRvd3NfYW5faW1wb3J0ZWRfbmFtZV93aG9zZV9mdW5jdGlvbl9pc19wcml2YXRlIiwibmFtZSI6ImFfbG9jYWxfc2hhZG93c19hbl9pbXBvcnRlZF9uYW1lX3dob3NlX2Z1bmN0aW9uX2lzX3ByaXZhdGUifQ=="></details>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoic3VjY2VzcyJ9LCJmaWxlcyI6W3sibmFtZSI6Im1haW4ubXRsIiwic291cmNlIjoiaW1wb3J0IGxpYjo6Rm9vO1xuXG5mdW4gbWFpbigpIHtcbiAgICBsZXQgYSA6PSBGb28geyB4ID0gMSB9O1xuICAgIGFzc2VydChhLnggPT0gMSk7XG59XG4ifSx7Im5hbWUiOiJsaWIubXRsIiwic291cmNlIjoiLy8gbWV0ZWwtY29yZSMxNTcxOiBgRm9vYCBpcyBwdWJsaWMgYXMgYSB0eXBlIGFuZCBwcml2YXRlIGFzIGEgZnVuY3Rpb24uIEltcG9ydGluZyBgRm9vYCBicmluZ3Ncbi8vIGluIHRoZSB0eXBlOyB0aGUgcHJpdmF0ZSBmdW5jdGlvbiBpcyBub3QgaW1wb3J0YWJsZSBidXQgZG9lcyBub3QgbWFrZSB0aGUgaW1wb3J0IGZhaWwuXG5wdWJsaWMgc3RydWN0IEZvbyB7XG4gICAgcHVibGljIHg6IGk2NCxcbn1cblxuZnVuIEZvbygpIC0+IGk2NCB7XG4gICAgNVxufVxuIn1dLCJocmVmIjoiaHR0cHM6Ly9naXRodWIuY29tL21ldGVsLWxhbmcvbWV0ZWwtY29yZS9ibG9iL3YwLjE0LjEvbWV0ZWwtaW50ZXJwcmV0ZXIvdGVzdHMvaW50ZWdyYXRpb24vc291cmNlcy9ldmFsdWF0b3Ivc3RydWN0cy9hX3ByaXZhdGVfZnVuY3Rpb25fZG9lc19ub3RfaGlkZV9hX3B1YmxpY190eXBlX29mX2l0c19uYW1lIiwibmFtZSI6ImFfcHJpdmF0ZV9mdW5jdGlvbl9kb2VzX25vdF9oaWRlX2FfcHVibGljX3R5cGVfb2ZfaXRzX25hbWUifQ=="></details>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6IlQwMDA5IiwiY29sIjpudWxsLCJjb250YWlucyI6ImBGb29gIGlzIG5vdCBwdWJsaWMgaW4gbW9kdWxlIGBsaWJgIiwibGluZSI6bnVsbCwic3RhdHVzIjoidHlwZWNoZWNrX2Vycm9yIn0sImZpbGVzIjpbeyJuYW1lIjoibWFpbi5tdGwiLCJzb3VyY2UiOiIvLyBUaGUgaW1wb3J0IGlzIGZpbmUgKHRoZSB0eXBlIGlzIHB1YmxpYyksIGJ1dCBjYWxsaW5nIGBGb29gIG5lZWRzIHRoZSBwcml2YXRlIGZ1bmN0aW9uOiB0aGF0IGlzIGFcbi8vIHZpc2liaWxpdHkgZXJyb3IsIG5vdCBhbiB1bmRlZmluZWQgbmFtZS5cbmltcG9ydCBsaWI6OkZvbztcblxuZnVuIG1haW4oKSB7XG4gICAgbGV0IGEgOj0gRm9vKCk7XG59XG4ifSx7Im5hbWUiOiJsaWIubXRsIiwic291cmNlIjoiLy8gbWV0ZWwtY29yZSMxNTc1OiBgRm9vYCBpcyBhIHB1YmxpYyB0eXBlIGFuZCBhIHByaXZhdGUgZnVuY3Rpb24uXG5wdWJsaWMgc3RydWN0IEZvbyB7XG4gICAgcHVibGljIHg6IGk2NCxcbn1cblxuZnVuIEZvbygpIC0+IGk2NCB7XG4gICAgNVxufVxuIn1dLCJocmVmIjoiaHR0cHM6Ly9naXRodWIuY29tL21ldGVsLWxhbmcvbWV0ZWwtY29yZS9ibG9iL3YwLjE0LjEvbWV0ZWwtaW50ZXJwcmV0ZXIvdGVzdHMvaW50ZWdyYXRpb24vc291cmNlcy90eXBlY2hlY2tpbmcvdHlwZXMvbmVnX3ByaXZhdGVfZnVuY3Rpb25fYmVzaWRlX2FuX2ltcG9ydGVkX3B1YmxpY190eXBlX2lzX3QwMDA5IiwibmFtZSI6Im5lZ19wcml2YXRlX2Z1bmN0aW9uX2Jlc2lkZV9hbl9pbXBvcnRlZF9wdWJsaWNfdHlwZV9pc190MDAwOSJ9"></details>
</details>
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

<!-- rfc.py:last_reviewed 722a13049df7dd2ba817e781ebbc6bb3689f9d6e -->

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0031](../../rfcs/4-implemented/rfc-0031-topological-typechecker.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<p class="rigor-backlink"><em>Tested by</em></p>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6ImNhbm5vdCBmaW5kIG1vZHVsZSIsImxpbmUiOm51bGwsInN0YXR1cyI6ImxvYWRfZXJyb3IifSwiZmlsZXMiOlt7Im5hbWUiOiJtYWluLm10bCIsInNvdXJjZSI6ImltcG9ydCBub25leGlzdGVudDo6VGhpbmc7XG5mdW4gbWFpbigpIC0+IGk2NCB7IHJldHVybiBUaGluZygpOyB9XG4ifV0sImhyZWYiOiJodHRwczovL2dpdGh1Yi5jb20vbWV0ZWwtbGFuZy9tZXRlbC1jb3JlL2Jsb2IvdjAuMTQuMS9tZXRlbC1pbnRlcnByZXRlci90ZXN0cy9pbnRlZ3JhdGlvbi9zb3VyY2VzL21vZHVsZV9sb2FkaW5nL2ltcG9ydF9ub25leGlzdGVudF9tb2R1bGVfaXNfYV9sb2FkX2Vycm9yIiwibmFtZSI6ImltcG9ydF9ub25leGlzdGVudF9tb2R1bGVfaXNfYV9sb2FkX2Vycm9yIn0="></details>
<!-- rfc.py:fixtures:end -->

##### Legality Rule {#spec.modules.module-graph-loading.legality-2}

> **Gap** GAP-MODULES-001

Imports and re-exports both contribute module-graph edges. Missing modules and circular
dependencies are load errors, and a bare re-export loads its target module.

<!-- rfc.py:last_reviewed 8b844c9117d5c6a730882aeaf521184c3055eb2f -->

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0030](../../rfcs/4-implemented/rfc-0030-module-system-redesign.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<details class="rigor-fixtures-toggle" open>
<summary>Tested by (3)</summary>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6ImNhbm5vdCBmaW5kIG1vZHVsZSIsImxpbmUiOm51bGwsInN0YXR1cyI6ImxvYWRfZXJyb3IifSwiZmlsZXMiOlt7Im5hbWUiOiJtYWluLm10bCIsInNvdXJjZSI6ImltcG9ydCBub25leGlzdGVudDo6VGhpbmc7XG5mdW4gbWFpbigpIC0+IGk2NCB7IHJldHVybiBUaGluZygpOyB9XG4ifV0sImhyZWYiOiJodHRwczovL2dpdGh1Yi5jb20vbWV0ZWwtbGFuZy9tZXRlbC1jb3JlL2Jsb2IvdjAuMTQuMS9tZXRlbC1pbnRlcnByZXRlci90ZXN0cy9pbnRlZ3JhdGlvbi9zb3VyY2VzL21vZHVsZV9sb2FkaW5nL2ltcG9ydF9ub25leGlzdGVudF9tb2R1bGVfaXNfYV9sb2FkX2Vycm9yIiwibmFtZSI6ImltcG9ydF9ub25leGlzdGVudF9tb2R1bGVfaXNfYV9sb2FkX2Vycm9yIn0="></details>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6ImNpcmN1bGFyIG1vZHVsZSBkZXBlbmRlbmN5IiwibGluZSI6bnVsbCwic3RhdHVzIjoibG9hZF9lcnJvciJ9LCJmaWxlcyI6W3sibmFtZSI6Im1haW4ubXRsIiwic291cmNlIjoiaW1wb3J0IGE6OlRoaW5nO1xuZnVuIG1haW4oKSB7IH1cbiJ9LHsibmFtZSI6ImEubXRsIiwic291cmNlIjoiaW1wb3J0IGI6Ok90aGVyO1xuIn0seyJuYW1lIjoiYi5tdGwiLCJzb3VyY2UiOiJpbXBvcnQgYTo6VGhpbmc7XG4ifV0sImhyZWYiOiJodHRwczovL2dpdGh1Yi5jb20vbWV0ZWwtbGFuZy9tZXRlbC1jb3JlL2Jsb2IvdjAuMTQuMS9tZXRlbC1pbnRlcnByZXRlci90ZXN0cy9pbnRlZ3JhdGlvbi9zb3VyY2VzL21vZHVsZV9sb2FkaW5nL3JlamVjdHNfY2lyY3VsYXJfbW9kdWxlX2dyYXBoIiwibmFtZSI6InJlamVjdHNfY2lyY3VsYXJfbW9kdWxlX2dyYXBoIn0="></details>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoic3VjY2VzcyJ9LCJmaWxlcyI6W3sibmFtZSI6Im1haW4ubXRsIiwic291cmNlIjoiaW1wb3J0IGZhY2FkZTo6YW5zd2VyO1xuZnVuIG1haW4oKSAtPiBpNjQgeyBhbnN3ZXIoKSB9XG4ifSx7Im5hbWUiOiJmYWNhZGUubXRsIiwic291cmNlIjoiZXhwb3J0IGhlbHBlcjo6YW5zd2VyO1xuIn0seyJuYW1lIjoiaGVscGVyLm10bCIsInNvdXJjZSI6InB1YmxpYyBmdW4gYW5zd2VyKCkgLT4gaTY0IHsgNDIgfVxuIn1dLCJocmVmIjoiaHR0cHM6Ly9naXRodWIuY29tL21ldGVsLWxhbmcvbWV0ZWwtY29yZS9ibG9iL3YwLjE0LjEvbWV0ZWwtaW50ZXJwcmV0ZXIvdGVzdHMvaW50ZWdyYXRpb24vc291cmNlcy9tb2R1bGVfc2VtYW50aWNzL3JmYzAwMzBfYmFyZV9leHBvcnRfbG9hZHNfbW9kdWxlIiwibmFtZSI6InJmYzAwMzBfYmFyZV9leHBvcnRfbG9hZHNfbW9kdWxlIn0="></details>
</details>
<!-- rfc.py:fixtures:end -->

</details>

## Single-File Compatibility

A `.mtl` file with no `import` or `export` declarations is a complete program. Existing single-file programs remain valid without modification.

<details>
<summary>Formal rules</summary>

##### Legality Rule {#spec.modules.single-file-compatibility.legality-1}

A source file with no import or export declarations is a complete single-module program.

<!-- rfc.py:last_reviewed 722a13049df7dd2ba817e781ebbc6bb3689f9d6e -->

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0030](../../rfcs/4-implemented/rfc-0030-module-system-redesign.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<p class="rigor-backlink"><em>Tested by</em></p>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoic3VjY2VzcyJ9LCJmaWxlcyI6W3sibmFtZSI6Im1haW4ubXRsIiwic291cmNlIjoiZnVuIG1haW4oKSB7IH1cbiJ9XSwiaHJlZiI6Imh0dHBzOi8vZ2l0aHViLmNvbS9tZXRlbC1sYW5nL21ldGVsLWNvcmUvYmxvYi92MC4xNC4xL21ldGVsLWludGVycHJldGVyL3Rlc3RzL2ludGVncmF0aW9uL3NvdXJjZXMvbW9kdWxlX2xvYWRpbmcvc2luZ2xlX2ZpbGVfcHJvZ3JhbV9sb2Fkc193aXRob3V0X21vZHVsZXMiLCJuYW1lIjoic2luZ2xlX2ZpbGVfcHJvZ3JhbV9sb2Fkc193aXRob3V0X21vZHVsZXMifQ=="></details>
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

<!-- rfc.py:last_reviewed cfff5473333ed9035b5f8fc9ecf285c8fc394a1d -->

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0030](../../rfcs/4-implemented/rfc-0030-module-system-redesign.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<p class="rigor-backlink"><em>Tested by</em></p>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6IlAwMDAxIiwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoicGFyc2VfZXJyb3IifSwiZmlsZXMiOlt7Im5hbWUiOiJyZmMwMDMwX2xlZ2FjeV9tb2RfdXNlX3JlamVjdGVkLm10bCIsInNvdXJjZSI6Im1vZCBoZWxwZXI7XG5mdW4gbWFpbigpIC0+IGk2NCB7IDAgfVxuIn1dLCJocmVmIjoiaHR0cHM6Ly9naXRodWIuY29tL21ldGVsLWxhbmcvbWV0ZWwtY29yZS9ibG9iL3YwLjE0LjEvbWV0ZWwtaW50ZXJwcmV0ZXIvdGVzdHMvaW50ZWdyYXRpb24vc291cmNlcy9wYXJzaW5nL3JmYzAwMzBfbGVnYWN5X21vZF91c2VfcmVqZWN0ZWQubXRsIiwibmFtZSI6InJmYzAwMzBfbGVnYWN5X21vZF91c2VfcmVqZWN0ZWQubXRsIn0="></details>
<!-- rfc.py:fixtures:end -->

</details>

## Known gaps

<!-- records:gaps -->
