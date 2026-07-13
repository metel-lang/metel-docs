---
id: rfc-0099
title: "Dot-Separated Module Paths"
date: '2026-07-13'
status: draft
target:
---

## Summary

Replace `::` with `.` for import paths, `export` paths, static/module paths, and enum-variant paths. Unlike RFC-0098's renames, this is **not** a pure token substitution: `.` already means field/method access (RFC-0045), so this RFC has to settle a real disambiguation rule before the grammar change is even well-formed. Amends RFC-0030's path grammar and its `root::`/`std::`/`self::`/`super::` reserved-root spellings.

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

This is the section that actually makes this RFC more than a find-replace. Two candidate rules, both grounded in what's already true of Metel today rather than invented for this RFC:

**Option A — capitalization-based.** Metel already uses PascalCase for every construct a path can terminate in at the type level — structs, enums, aspects — and lowerCamelCase/snake_case for values and functions (not grammar-enforced today, but true of every existing example and the whole stdlib). A leading-segment capitalization check (`List.new` — capitalized first segment, resolved as a module/type path; `list.new` — lowercase first segment, resolved as ordinary field/method access on the value `list`) requires no new resolution machinery — it's a syntactic check the parser can make before handing anything to `name_resolver` at all. Risk: this promotes an informal convention into a hard grammar rule, which means a lowercase module name or an uppercase local variable (both currently legal, if unconventional) would become a parse-time error or silently resolve wrong. Needs a worked-example pass specifically hunting for existing code that violates the convention before this is accepted as sound, per this project's own `3-integrated` discipline.

**Option B — resolved at name-resolution time, not grammar time.** Parse `a.b` as one production regardless of what `a` turns out to be; let `name_resolver` decide whether `a` is a module handle, a type name, or a value binding, and dispatch accordingly. More uniform, no reliance on a capitalization convention holding everywhere — but it pushes an ambiguity the grammar could reject early into a later pass, and interacts with forward-reference/hoisting order in ways Option A never has to consider.

**Recommendation for review, not yet decided:** start with Option A. It costs nothing new to check (the convention already holds everywhere in practice), fails fast at parse time rather than surfacing a confusing error deep in name resolution, and if a real counterexample turns up during the worked-example pass, that's exactly the kind of thing this RFC needs to find before acceptance, not after.

## 4. What doesn't change

- **Turbofish call syntax (`f::<T>(args)`, RFC-0023's territory) keeps its `::<` spelling, unchanged.** This is a *third*, separate use of `::` beyond the two this RFC addresses (module/static paths, enum variants) — found while writing this RFC, not in the original motivating discussion, which only tracked the first two. `::<` is a distinctive two-character digraph that never collides with ordinary `.` field/method access, so leaving it alone avoids inventing a `.< ... >` spelling that would read worse than what it replaces and isn't needed for this RFC's own disambiguation goal (§3) to work. If turbofish's own spelling is ever revisited, that belongs to RFC-0023's follow-up, not this one.
- RFC-0045's lvalue-path semantics (chained field/tuple/array access, `&mut` through a chain) — completely untouched; this RFC's disambiguation rule exists specifically so RFC-0045's job and this one's don't collide.
- RFC-0030's module-to-file mapping, `import`/`export` semantics, glob imports, aliasing (`as`), and `std::core` auto-import — only the separator token changes.
- Enum-variant pattern matching semantics (`enum_pattern` in the grammar) — only its spelling.

---

## Alternatives Considered

- **Hybrid: keep `::` for type-level paths (modules, enum variants), `.` only for value-level field/method access.** Smaller change, zero new ambiguity — Option A/B above become unnecessary. Rejected as the default proposal here because it keeps the strongest Rust tell (`::`) fully intact for exactly the paths most visible in everyday code (imports, static calls); noted as the fallback if neither disambiguation option survives review.
- **`.` everywhere, ambiguity resolved by making static/module paths a distinct token requiring a capital-letter grammar rule enforced universally (not just for disambiguation, but as a new naming-convention requirement).** Rejected as out of scope — this RFC disambiguates a token, it doesn't newly mandate a naming convention across the whole language.

---

## Unresolved Questions

1. **Which disambiguation option (§3 A or B) survives a worked-example pass against real stdlib and test-fixture code?** This is the one genuinely blocking question in this RFC — everything else here is closer to mechanical once this is settled.
2. Does the reserved-path-root spelling (`root.`/`std.`/`self.`/`super.`) need its own escape from the disambiguation rule, since none of the four are PascalCase? (Likely resolved as "yes, these four are recognized as reserved keywords before the capitalization check ever runs" — but worth stating explicitly in whichever option is chosen, not left implicit.)

---

## References

- RFC-0030 (Module System Redesign) — amended: path grammar, reserved path roots, `::`/`/` filesystem mapping (becomes `.`/`/`).
- RFC-0009 (Module System) — superseded by RFC-0030; not directly amended by this RFC.
- RFC-0045 (Mutable Address-Of for Lvalue Paths) — the existing, unamended owner of `.` for field/tuple/array chains; this RFC's §3 exists to avoid colliding with it.
- RFC-0023 (Type Ascription vs Turbofish) — turbofish's `::<T>` call-site syntax is a third use of `::` this RFC does not touch (§4); not amended.
- RFC-0098 (Surface Keyword Renames) — sibling surface-syntax RFC from the same review; independent of this one (no shared grammar production, no shared open question).
- RFC-0100 (Constructor-Call Construction) — sibling surface-syntax RFC from the same review; independent of this one.

---

## Decision

**Outcome:** *(pending)*
**Target:** *(set when accepted)*
