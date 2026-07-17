---
id: rfc-0101
title: "Grammar-Enforced Naming Case Conventions"
date: '2026-07-14'
status: draft
target:
updated: '2026-07-17'
---

## Summary

PascalCase for type declarations (struct/enum/aspect/generic params), camelCase for fun declarations (free functions, methods, associated functions), snake_case for everything else that introduces a name (let bindings, parameters, struct fields) -- enforced as a real compile-time rule, not just a style convention.

---

## Motivation

Metel's identifier casing is, today, a convention with no enforcement behind it: every struct/enum/aspect
in `stdlib/core.mtl` happens to be PascalCase, and every function, method, variable, and field happens to
be snake_case — but nothing in the grammar or typechecker would reject `struct point { ... }` or
`fun IsSome(self) -> boolean { ... }` if someone wrote them. This RFC proposes making three specific
casing rules real, compiler-enforced constraints rather than an unstated house style, with one deliberate
departure from the current de-facto convention: **`fun` declarations (free functions, methods, associated
functions) move from snake_case to camelCase**, distinguishing "this name was introduced by a `fun`
declaration" from "this name was introduced by `let`, a parameter, or a struct field" — a distinction the
current all-snake_case convention doesn't draw at all.

This surfaced directly out of reviewing RFC-0100 (Constructor-Call Construction): its call-site keyword
arguments (`Type(field: value)`) collide, at the grammar level, with the existing type-ascription
expression (`expr: Type`, RFC-0023) — `Foo(bar: Baz)` is genuinely ambiguous between "keyword argument
`bar` bound to value `Baz`" and "the expression `bar`, ascribed to type `Baz`." A casing rule that makes
"bare PascalCase identifier" reliably mean "type reference, never a standalone value" removes the one
residual case grammar-ordering alone can't fully rule out. But the idea earns its own RFC rather than
riding on RFC-0100's coattails: it's a real, general readability property (an identifier's own spelling
tells you what kind of thing it names, without needing declaration-site context), and it's a materially
bigger change than anything RFC-0100 needs on its own — it touches every function and method name in the
existing codebase, not just call-argument syntax.

---

## 1. The three categories

Not "type vs. value," and not "callable vs. binding" (a binding can hold a closure and be called exactly
like a function — casing can't and shouldn't try to describe runtime behavior, since a static check can
only see how a name was *declared*, never what ends up bound to it). The actual axis is **declaration
form**:

| Category | Casing | Introduced by |
|---|---|---|
| Type declarations | PascalCase | `struct`, `enum`, `aspect` names; generic parameters (`T`, `U`, `E` — already universal convention, zero known exceptions) |
| Enum variants | PascalCase | `enum Colour { Red, Green, Blue }` — grouped with types because they're spelled and read like one (`Colour.Blue`), even though *referencing* one produces a value, not a type |
| `fun` declarations | camelCase | free functions, methods inside an `impl`/`extend` block, associated functions (`List.new`) |
| Constants | SCREAMING_CASE | module-level, immutable `let` bindings (`let MAX_RETRIES = 5;`) |
| Everything else that introduces a name | snake_case | function-local `let` bindings (mutable or not), function/closure parameters, struct fields |

The middle rows are the actual content of this RFC — PascalCase-for-types and snake_case-for-bindings
already hold universally in the current codebase (verified: zero violations found across `stdlib/` and the
full test-fixture tree while reviewing RFC-0099). The camelCase-for-`fun` rule is the one real, active
change: every existing function and method (`is_some`, `unwrap_or_else`, `and_then`, `list_new`, and so on,
throughout `stdlib/core.mtl`) is snake_case today and would need renaming.

**Constants get their own row, resolving what was an open question in an earlier draft of this RFC.**
Metel has no dedicated `const` declaration form — a module-level constant today is written as an ordinary
`let` binding at the top level rather than inside a function body. The grammar already distinguishes
immutable `let` from mutable `let mut` (`let_decl` vs. `let_mut_decl`), so "module-scope and immutable" is
a precise, already-checkable definition of "constant" without inventing any new declaration syntax: `let
MAX_RETRIES = 5;` at module scope is a constant (SCREAMING_CASE); the exact same `let x = 5;` written
inside a function body is an ordinary local binding (snake_case), and a module-level `let mut` is neither
a constant nor exempt from module-scope naming — it's just an unusual, mutable piece of module state, and
stays snake_case like any other binding. No existing code needs renaming for this row either: there are
currently zero module-level `let` bindings anywhere in `stdlib/` to begin with.

A closure stored in a `let` binding or passed as a parameter stays snake_case (or SCREAMING_CASE, if it's
a module-level constant closure) regardless of what it does at runtime — `let add = fun(x, y) { x + y };`
keeps `add` snake_case even though it's called exactly like a function, and a parameter `callback: (T) ->
U` stays snake_case even though whatever's passed for it is itself invariably some callable. None of these
are declared by `fun`, so none qualify for the camelCase rule — the casing describes the declaration, not
the value.

## 2. Enforcement mechanism

This is a compile-time rule, not a grammar-level one in the literal sense of being encoded into
`grammar.pest`'s own productions — PEG grammars express *structure*, not identifier-content validation,
and pest doesn't have a natural way to jointly match "this position expects an identifier" and "this
identifier's characters satisfy a casing predicate" without contorting the grammar. The check instead
belongs to a post-parse pass over the AST (early — alongside or immediately after name registration, well
before typechecking), walking each declaration site (`StructDecl`, `EnumDecl`, `AspectDecl`, `FunDecl`,
`GenericParam`, `LetDecl`, `Param`, struct field entries) and validating its name against the casing rule
for that category, raising a hard compile error (a new error code, not a warning) on violation. `LetDecl`
needs one extra bit of context beyond the node itself — whether it sits at module scope or inside a
function/block body — to pick between the constant (SCREAMING_CASE) and ordinary-binding (snake_case)
rule; that's already ordinary information the pass has while walking the AST; no separate lookup is
needed. This mirrors how every other compile-time check in this pipeline already works — the typechecker
itself is a series of AST-walking passes, not something embedded in the grammar file.

## 3. Migration

PascalCase-for-types, snake_case-for-bindings, and SCREAMING_CASE-for-constants need no renames anywhere
in the existing codebase — the first two conventions already hold without exception, and there are
currently zero module-level `let` bindings in `stdlib/` for the constants rule to touch at all.
camelCase-for-`fun` is a real, mechanical rename pass across every existing function and method declaration
*and every call site*, in `stdlib/core.mtl` and the entire `tests/integration/sources/` fixture tree. This
is large in raw line count but mechanical in nature (a name-for-name rewrite, no semantic change), similar
in kind to — but larger in scope than — the identifier audit RFC-0098 already needs for its own `var`
keyword collision.

---

## 4. Interaction with sibling surface-syntax RFCs

- **RFC-0099 (Dot-Separated Module Paths) — does *not* rescue Option A.** RFC-0099's own disambiguation
  problem (`std.core.Perhaps.Some`) isn't a type-vs-value casing question — it's that *module* path
  segments (`std`, `core`, `parser`) are lowercase, same as values, sitting in the middle of a path that's
  unambiguously "type-side." This RFC doesn't introduce a fourth category for modules, and even if it did,
  a hard casing rule still couldn't distinguish "lowercase module segment, keep resolving" from "lowercase
  value, stop here" without the hop-by-hop resolution RFC-0099's Option B already does. RFC-0099's choice
  of Option B stands unchanged; this RFC and that one solve different problems that happen to look similar
  at a glance.
- **RFC-0100 (Constructor-Call Construction) — narrows, but does not replace, the grammar-ordering fix.**
  Once a bare PascalCase identifier reliably means "type reference, never a standalone value" (since
  RFC-0100's own call-shaped construction means a *bare* type name with no trailing `(args)` never
  constructs anything), the one residual ambiguity case for `ident: expr` inside a call's argument
  list — a bare capitalized value on the right of the colon — essentially can't arise in legitimate code.
  But the actual grammar collision (an argument shaped `ident : expr` being greedily consumed by the
  existing `asc_expr` ascription production before a keyword-argument alternative is ever tried) is
  structural, not casing-shaped, and still needs the ordering fix discussed against that RFC directly
  (trying a keyword-argument shape before falling through to plain `expr` inside `arg_list`). This RFC
  makes that fix's remaining edge case negligible in practice; it doesn't make the fix itself unnecessary.
- **RFC-0098 (Surface Keyword Renames) — no conflict.** All three new/renamed keywords (`extend`,
  `public`, `var`) are lowercase, consistent with this RFC's non-type casing — nothing to reconcile.

---

## Alternatives Considered

- **Two-way split only (PascalCase types / snake_case everything else), no `fun`-specific camelCase.**
  This is the status quo convention, formalized as a hard rule instead of a style guide. Needs zero
  renames anywhere in the existing codebase. Rejected as the primary proposal here in favor of the
  three-way split, per direct discussion — the `fun`-vs-`let`/parameter/field distinction was judged
  worth the migration cost for the readability it buys, but this remains the far cheaper fallback if that
  judgment doesn't survive wider review.
- **camelCase determined by "is this value callable" rather than "was this declared by `fun`."** Considered
  and rejected during this RFC's own drafting discussion: a `let`-bound closure or a closure-typed
  parameter is exactly as callable as a `fun` declaration, so "callable-ness" isn't a property a static
  casing check can coherently key on — only the declaration form (which keyword/production introduced the
  name) is available at the point the check runs.
- **No enforcement, keep it a documented convention only.** Rejected: a convention with zero enforcement
  is exactly the situation motivating this RFC — every current codebase example already follows it, so
  enforcement costs nothing in practice today but catches real future mistakes (shadowing a type with a
  value or vice versa) that a style guide alone wouldn't.

---

## Unresolved Questions

1. **Enum variants accessed unqualified** (e.g. a hypothetical future `import Colour.*` bringing `Red`,
   `Green`, `Blue` into scope bare, mirroring how ordinary glob imports already work for other items). Not
   a live conflict today — `enum_pattern` in the grammar always requires the qualified `Type.Variant` form,
   so there's no unqualified bare-PascalCase-value case to collide with "PascalCase means type" yet. Worth
   checking explicitly if unqualified variant access is ever proposed.

   **Now proposed: RFC-0107** (Unqualified Enum Variants in Match Patterns, draft,
   2026-07-17) — narrower than the glob-import mechanism sketched above (type-directed
   against the match scrutinee's own resolved enum, not a general scope import), so it
   doesn't reopen the collision concern this item raises; see RFC-0107 §1.3/§3 for why,
   and §3 there for how this RFC's PascalCase convention reduces (without being required
   for) the shadowing ambiguity a bare variant pattern can still produce.
2. **Exact scope of the post-parse enforcement pass** — does a violation block compilation outright (this
   RFC's assumption), or is there a suppression/opt-out mechanism for generated code or FFI-bound native
   declarations whose names might legitimately need to mirror an external, differently-cased API? Needs a
   decision before implementation, not assumed either way here.
3. **Full migration checklist** (every `stdlib/core.mtl` function/method rename, every test-fixture call
   site) is real, tracked work once this RFC is accepted — not detailed line-by-line here, but flagged so
   it isn't underestimated relative to RFC-0098's much smaller single-collision audit.
4. **Module-level mutable state naming** — a module-level `let mut` is neither a constant nor a `fun`
   declaration; this RFC puts it in the snake_case bucket (§1) since it's still fundamentally a binding,
   but it's worth confirming that reads right in practice once real module-level mutable state exists to
   look at (there is none in `stdlib/` today).

---

## References

- RFC-0023 (Type Ascription vs Turbofish) — the existing `expr: Type` production this RFC's motivating
  example (RFC-0100 interaction) collides with; not amended by this RFC.
- RFC-0034 (Aspect Bounds on Struct and Enum Generic Parameters) — existing precedent for PascalCase
  generic parameter names, continued unchanged by this RFC's type-declaration category.
- RFC-0098 (Surface Keyword Renames) — sibling surface-syntax RFC from the same review; no conflict (§4).
- RFC-0099 (Dot-Separated Module Paths) — sibling surface-syntax RFC from the same review; this RFC does
  not resolve RFC-0099's own disambiguation question (§4) — different axis, similar surface appearance.
- RFC-0100 (Constructor-Call Construction) — the RFC whose review surfaced this proposal; narrows but does
  not replace the grammar-ordering fix that RFC still needs for its own keyword-argument syntax (§4).

---

## Decision

**Outcome:** *(pending)*
**Target:** *(set when accepted)*
