---
id: rfc-0099
title: "Dot-Separated Module Paths"
date: '2026-07-13'
status: draft
target:
---

## Summary

Replace `::` with `.` for import paths, `export` paths, static/module paths, and enum-variant paths, and `::<` with `.<` for turbofish. Unlike RFC-0098's renames, this is **not** a pure token substitution: `.` already means field/method access (RFC-0045), so this RFC has to settle a real disambiguation rule before the grammar change is even well-formed. Amends RFC-0030's path grammar and its `root::`/`std::`/`self::`/`super::` reserved-root spellings, and RFC-0023's turbofish call-site syntax.

---

## Motivation

`::` is one of the strongest Rust/C++ tells in Metel's surface syntax — nearly every other language with a module system spells the path separator `.` (Python, Java, JavaScript's `import`, Kotlin, Swift's dotted member/module access). Metel already uses `::` for three genuinely different things that happen to share a token: import/export paths (RFC-0030), enum-variant paths (`Colour::Blue`), and static/associated-function paths (`List::new()`). All three read as one visual family today; a dot-based rewrite should keep them reading as one family, not fragment them.

The reason this isn't "just" a rename: RFC-0045 already committed `.` to a different, well-specified job — chained lvalue-path field/tuple/array access (`pair.counter`, `&mut pair.counter`). Reusing `.` for module paths means `List.new` and `list.new` (a value named `list` with a method `new`) both parse through the same token, and the grammar needs an actual rule for telling them apart, not just a substitution.

---

## 1. Where `::` appears today

Per RFC-0030 and the current grammar (`import_path`, `path_expr`, `type_path`, `enum_pattern`):

```metel
import parser::{Ast, Token};
import std::math;
import root::lexer::Token as Tok;
export ast::Ast;

let p: root::parser::Ast = root::parser::Ast::new();

match colour {
    Colour::Blue => ...,
}

let l = List::new();
```

Four distinct uses: import/export module paths, the reserved path roots (`root::`, `std::`, `self::`, `super::`), enum-variant paths, and static/associated-function paths on a type.

## 2. Proposed spelling

```metel
import parser.{Ast, Token};
import std.math;
import root.lexer.Token as Tok;
export ast.Ast;

let p: root.parser.Ast = root.parser.Ast.new();

match colour {
    Colour.Blue => ...,
}

let l = List.new();
```

`root.`/`std.`/`self.`/`super.` replace `root::`/`std::`/`self::`/`super::` as reserved path-root spellings (RFC-0030 §"Path roots" table). The `::` → `/` filesystem-mapping rule (RFC-0030: "`::` maps directly to `/` in the filesystem") carries over unchanged as `.` → `/` — only the separator's spelling changes, not the one-segment-per-path-component mapping to directory/file structure.

## 3. The disambiguation rule

This is the section that actually makes this RFC more than a find-replace.

**Option A — capitalization-based (considered, rejected).** Metel already uses PascalCase for every construct a path can terminate in at the type level — structs, enums, aspects — and lowerCamelCase/snake_case for values and functions (not grammar-enforced today, but true of every existing example and the whole stdlib). The idea: a leading-segment capitalization check (`List.new` — capitalized first segment, resolved as a module/type path; `list.new` — lowercase first segment, resolved as ordinary field/method access on the value `list`) would need no new resolution machinery, since it's a syntactic check the parser could make before handing anything to `name_resolver` at all.

This does not survive the worked-example pass this RFC's own draft called for. An actual, existing fixture —
`tests/integration/sources/module_semantics/std_core_perhaps_path_in_struct_literal/main.mtl` —
has, in expression position (not an import statement, where a keyword already disambiguates):

```metel
let x = std::core::Perhaps::Some { value: 42 };
```

Under the dot rename this is `std.core.Perhaps.Some { ... }` — leading segment `std` is lowercase. A
leading-segment-only check misreads this as ordinary value/field access on a (nonexistent) local `std`.
This isn't a contrived edge case — the RFC's own §2 example (`root.parser.Ast.new()`) has the identical
shape: two lowercase segments (`root`, `parser`) before reaching the PascalCase type. Repairing the rule
to handle this ("scan left-to-right; lowercase/reserved-root segments are module names; the first
PascalCase segment is the type; everything after is ordinary member access") is meaningfully more complex
than "check the leading segment," and still leaves one residual case unresolved: Metel doesn't
grammatically enforce field-name casing today, so a struct field that happens to be named with a capital
letter (legal, if unconventional) would still misparse under any capitalization-based rule, not only at
the top level.

**This isn't rescued by RFC-0101** (Grammar-Enforced Naming Case Conventions, reviewed alongside this RFC),
even though that RFC makes PascalCase-vs-non-PascalCase a real, compiler-enforced rule rather than an
informal convention. RFC-0101's categories are type declarations, `fun` declarations, and
everything-else-that-introduces-a-name — modules aren't a fourth category there, and module path segments
(`std`, `core`, `parser`) stay lowercase, same as ordinary values, under that RFC exactly as they are
today. A hard casing rule still can't tell "lowercase module segment, keep resolving" from "lowercase
value, stop here" — that's not a casing question at all, which is exactly why Option B is chosen below
instead of a repaired Option A.

**Option B — resolved at name-resolution time, not grammar time. Chosen.** Parse `a.b.c` as one uniform
production regardless of what `a` turns out to be — this needs *no new grammar* beyond the `::` → `.`
token substitution itself, since it's exactly the existing `postfix_expr`/`postfix` chain
(`primary_expr ~ postfix*`) already used for ordinary field/method access. `name_resolver` then decides,
hop by hop, whether each segment is a module, a type, or a value binding, and dispatches accordingly —
no capitalization convention is promoted to grammar, and the struct-field-casing risk above simply
doesn't exist, since resolution never guesses from spelling.

This isn't a novel mechanism invented for this RFC: `Expr::ResolvedPath` (`src/ast/mod.rs`) already exists
precisely to hold a path expression once the resolver has determined what it actually refers to, separate
from how it was originally parsed. Option B is that same pattern applied one level earlier — parse
`root.parser.Ast.new()` uniformly, let the resolver walk it (`root` → reserved root, `parser` → a module,
`Ast` → a type in that module, `new` → an associated function on that type), and produce the appropriate
resolved node, the same way it already does for ordinary paths today.

The cost, honestly stated: this pushes what Option A would catch at parse time into a later pass, and its
interaction with forward-reference/hoisting order (does `a.b` remain resolvable before `a`'s own module
is fully loaded, in every ordering the loader permits today?) needs verification during implementation —
not a blocking design question, but a real one to check against the module-loading pipeline before this
lands.

## 4. Turbofish: `::<` → `.<`

Turbofish call syntax (`f::<T>(args)`, RFC-0023's territory) is a *third*, separate use of `::` beyond the
two this RFC otherwise addresses (module/static paths, enum variants) — found while writing this RFC, not
in the original motivating discussion, which only tracked the first two. Leaving it as `::<` once every
other `::` in the language has become `.` would leave one visible fossil of the exact syntax this RFC (and
RFC-0098) exist to remove, so it is respelled too: `f.<T>(args)`, `method.<T>(args)` for the postfix
method-call form.

This is a straight token substitution, not a new disambiguation problem. `.<` remains a distinct two-character
token that `postfix` recognizes *before* it would ever fall through to ordinary `.` field/method access or up
to `cmp_expr`'s bare `<`/`>` comparison operators (`grammar.pest`'s `cmp_op`) — the same structural guarantee
`::<` already provides today, just spelled to match. Considered and rejected instead:

- **Bare `<T>` with no marker at all** (e.g. `std.core.method<Aspect>()`): reintroduces the exact ambiguity
  turbofish exists to prevent. `<`/`>` are real comparison operators (`cmp_expr`, one grammar level above
  `postfix_expr`) — a PEG parser encountering `method<Aspect>(args)` with no distinguishing marker would
  greedily parse `method < Aspect` as a comparison, then fail on the trailing `> (args)`. The dotted-path
  prefix (`std.core.`) doesn't change this; the collision lives entirely in the tail, independent of how
  the identifier before it was reached.
- **Square-bracket type args** (`method[Aspect](args)`): avoids the `<`/`>` collision, but `[...]` is
  already indexing, array literals, *and* sized-array types in this grammar — adding a fourth meaning
  trades one ambiguity for another rather than removing one.
- **Deleting turbofish, forcing type ascription everywhere instead:** not viable without reopening
  RFC-0023 (Type Ascription vs Turbofish) — that RFC's own title implies ascription doesn't fully
  substitute for turbofish (e.g. pinning one of several independent type params that a single return-type
  annotation can't reach), so this isn't a free simplification, it's undoing a separate, already-settled
  decision.

**Amends RFC-0023**'s surface syntax only — the ascription-vs-turbofish decision itself, and everything
about when each is required, is untouched; only turbofish's own token changes.

## 5. What doesn't change

- RFC-0045's lvalue-path semantics (chained field/tuple/array access, `&mut` through a chain) — completely untouched; this RFC's disambiguation rule exists specifically so RFC-0045's job and this one's don't collide.
- RFC-0030's module-to-file mapping, `import`/`export` semantics, glob imports, aliasing (`as`), and `std::core` auto-import — only the separator token changes.
- Enum-variant pattern matching semantics (`enum_pattern` in the grammar) — only its spelling.

---

## Alternatives Considered

- **Capitalization-based disambiguation (§3 Option A).** Considered as the RFC's original recommendation; rejected once checked against real fixture code (`std::core::Perhaps::Some` and the RFC's own `root.parser.Ast.new()` example both have lowercase segments before the type) — see §3 for the full finding.
- **Hybrid: keep `::` for type-level paths (modules, enum variants), `.` only for value-level field/method access.** Smaller change, zero new ambiguity — §3's disambiguation problem becomes unnecessary. Rejected as the default proposal here because it keeps the strongest Rust tell (`::`) fully intact for exactly the paths most visible in everyday code (imports, static calls); recorded here as the fallback should Option B's forward-reference/hoisting-order check (§3) turn up a real blocker during implementation.
- **`.` everywhere, ambiguity resolved by making static/module paths a distinct token requiring a capital-letter grammar rule enforced universally (not just for disambiguation, but as a new naming-convention requirement).** Rejected as out of scope — this RFC disambiguates a token, it doesn't newly mandate a naming convention across the whole language.
- **Turbofish alternatives** (bare `<T>`, square-bracket type args, deleting turbofish for ascription-only) — see §4 for each and why they were rejected in favor of respelling `::<` to `.<`.

---

## Unresolved Questions

None load-bearing. §3's disambiguation rule is settled (Option B); its one remaining implementation-time
check — forward-reference/hoisting-order interaction with the module loader — is not expected to block
acceptance, but should be verified before this RFC moves past `1-accepted`, with the hybrid alternative
above as a documented fallback if it does turn up a real problem. The reserved-path-root spelling
(`root.`/`std.`/`self.`/`super.`) needs no special carve-out under Option B, unlike under Option A: the
resolver already recognizes these as reserved at the first hop of any path today, the same way it does
before this RFC, so there is no capitalization check for them to be exempted from in the first place.

---

## References

- RFC-0030 (Module System Redesign) — amended: path grammar, reserved path roots, `::`/`/` filesystem mapping (becomes `.`/`/`).
- RFC-0009 (Module System) — superseded by RFC-0030; not directly amended by this RFC.
- RFC-0045 (Mutable Address-Of for Lvalue Paths) — the existing, unamended owner of `.` for field/tuple/array chains; this RFC's §3 exists to avoid colliding with it.
- RFC-0023 (Type Ascription vs Turbofish) — amended, §4 (`::<T>` → `.<T>` call-site syntax, a third use of `::` beyond the two this RFC otherwise addresses). The ascription-vs-turbofish decision itself is untouched.
- RFC-0098 (Surface Keyword Renames) — sibling surface-syntax RFC from the same review; independent of this one (no shared grammar production, no shared open question).
- RFC-0100 (Constructor-Call Construction) — sibling surface-syntax RFC from the same review; independent of this one.
- RFC-0101 (Grammar-Enforced Naming Case Conventions) — reviewed alongside this RFC; does not resolve this RFC's own disambiguation question (§3) — different axis, similar surface appearance.

---

## Decision

**Outcome:** *(pending)*
**Target:** *(set when accepted)*
