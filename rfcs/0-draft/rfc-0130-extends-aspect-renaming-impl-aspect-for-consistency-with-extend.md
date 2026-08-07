---
id: rfc-0130
title: "extends Aspect: Renaming impl Aspect for Consistency with extend"
date: '2026-08-06'
status: draft
target:
---

## Summary

Rename the `impl Aspect` keyword — in both of its permitted positions, function
parameter (RFC-0035) and function return (RFC-0037) — to `extends Aspect`. A pure
lexical rename with zero semantic change: desugaring, monomorphization, opacity
rules, and permitted positions (including the T0022 restriction just added this
session, metel-core#240/#622) are all untouched. This follows the exact precedent
and rationale RFC-0098 already established for `impl` (block form) → `extend`,
`pub` → `public`, and `mut` → `var` — except it targets the one spot that sweep
left out.

---

## Motivation

RFC-0002, the very first aspect-bound-syntax RFC, flagged this exact tension as
Open Question 3 and never actually resolved it with a real rationale:

> `impl Aspect` for parameter position is a known Rust tension (why `impl` — what
> does it implement?). Swift's `some` is semantically clear. Should Metel
> introduce a keyword, or require explicit `<T: Aspect>` for all generic
> positions?

The eventual decision table just recorded *"Anonymous type parameters → `impl
Aspect` syntax"* with no comparison written down — inherited from Rust by
default, not argued for.

RFC-0098 later renamed the impl-*block* keyword from `impl` to `extend`
specifically to shed exactly this kind of "pure Rust tell" (its own words:
*"Metel already diverges from Rust's naming where it costs nothing... it reads as
a deliberate identity rather than an accident of copying Rust's grammar"*). But it
stopped at the block form. The result is that **one underlying claim — "this type
satisfies this aspect" — is now spelled two unrelated ways depending on
grammatical position**:

```metel
extend IntBox: Printable { ... }        // a concrete type satisfies an aspect (declaration)
fun foo(x: impl Printable) { ... }      // some type satisfies an aspect (anonymous quantification)
```

This is still live in the current spec today — `declarations.md:859-888` spells
the anonymous/opaque-type feature `impl Aspect` throughout, including the section
this session just extended with `T0022` (metel-core#622): *"`impl Aspect` is only
allowed in parameter or return position."* The inconsistency isn't hypothetical;
it's in the diagnostic text shipping right now.

---

## Proposal

### Keyword

`impl` retires from type-expression position. `extends` replaces it, in exactly
the two positions `impl Aspect` is legal today — function parameter (RFC-0035)
and function return (RFC-0037). No new grammar positions are proposed. This RFC
does not reopen RFC-0038 (struct fields / existential types) and does not attempt
to legalize `extends Aspect` anywhere `impl Aspect` is rejected today, including
every position metel-core#622 just finished enforcing.

```metel
// today
fun print_all(items: impl Printable[]) { ... }
fun make_adder(n: i64) -> impl Callable<i64, i64> { ... }

// proposed
fun print_all(items: extends Printable[]) { ... }
fun make_adder(n: i64) -> extends Callable<i64, i64> { ... }
```

### Why `extends`, not bare `extend`

`extend` (no `-s`) is already a claimed, differently-shaped keyword: RFC-0098
assigned it to the statement-level impl-block form (`extend Type: Aspect { ...
}`), which opens a declaration and is followed by a target type. A
type-expression-position keyword instead needs to read as a predicate about the
position's own subject — a parameter binding, or a function's return value —
"x extends Printable" / "the return value extends Printable." This mirrors
TypeScript's `T extends Comparable`, which RFC-0002's own language survey
endorsed for exactly this reading: *"`extends` reads naturally (T must be a
subtype / implementor)."* Distinct tokens (`extend` vs. `extends`) also mean zero
grammar ambiguity — the parser never has to disambiguate one spelling doing two
jobs, unlike Rust's own `impl`, which already juggles two unrelated productions
under one spelling.

### Semantics: nothing changes

Restated explicitly, matching how RFC-0098 itself scoped its three renames:

- RFC-0035's desugaring rule (fresh, independent type variable per occurrence;
  same error-message source-spelling requirement, just spelled `extends Display`
  instead of `impl Display`) — unchanged.
- RFC-0037's opacity rule (same concrete type on every code path; one fixed type
  per function definition, not per call; no boxing, no vtable) — unchanged.
- RFC-0035's "Permitted Positions" table — unchanged; only the spelling of the
  `Yes` rows changes.
- The T0022 restriction (metel-core#240/#622 — `impl Aspect` rejected outside
  parameter/return position) — unchanged; the diagnostic text updates to name
  `extends Aspect` instead of `impl Aspect`, but which positions are legal does
  not move at all.
- RFC-0038 (draft, still open) — unaffected. Its own Q2 already reserves `dyn
  Aspect` for a distinct, future, vtable-based existential-types feature. This
  RFC does not touch, consume, or foreclose `dyn` in any way; the two keywords
  continue to mark two genuinely different runtime mechanisms (static
  monomorphization vs. dynamic dispatch), exactly as they do today.

### Grammar

```pest
extends_type = { "extends" ~ type_expr }
// Replaces impl_type in type_expr. Same permitted positions (parameter, return)
// as impl_type today; only the keyword token changes.
```

`impl_type` retires as a grammar rule. The `ImplAspect` AST node name is an
internal, non-user-facing identifier and may keep its current name or be renamed
for hygiene — an implementation detail, not a design question this RFC needs to
settle.

---

## Migration

RFC-0098 didn't have to solve this at scale because `mut`/`pub` appear
everywhere; `impl Aspect` appears in a narrower, identifiable set of places:
every function signature using the parameter- or return-position shorthand,
across `stdlib/`, `tests/`, and every prose example in `public/`, `reports/`, and
`public/rfcs/` that shows one.

- A mechanical rewrite (`impl <TypeExpr>` → `extends <TypeExpr>`) is unambiguous
  in source *only* because `impl` was already fully retired from every other
  grammar position by RFC-0098 — there is no remaining bare `impl` token to
  collide with. That still does not make a blind regex safe, per this project's
  own `PROCESS.md` rule ("sweep prose, not only code," the RFC-0115/metel-core#585
  precedent): scope the rewrite to type-expression positions specifically (an
  `impl` token immediately followed by a type name, itself preceded by `:` or
  `->` or sitting inside a bound list), and exclude fenced code blocks that are
  not Metel source (several existing RFCs embed Rust snippets describing the AST
  itself, which must not be swept).
- Every worked example inside `public/rfcs/`, `public/reference/spec/`, and
  `reports/` showing `impl Aspect` needs the same sweep in the same change, not
  as a follow-up — this is `PROCESS.md`'s explicit exit criterion for any RFC
  that changes the spelling of something already written down.
- `error-codes.md`'s `T0022` entry (added this session, metel-core#622 /
  metel-docs-internal#8) has exactly one diagnostic string containing `impl
  Aspect` that needs updating in the same pass.
- Identifier-collision audit, per RFC-0098 §3's own precedent (reserving `var`
  collided with the existing `std::env::var`, resolved by renaming the stdlib
  function to `std::env::get`): a grep of `stdlib/` and `tests/` for an
  identifier literally named `extends` should be run at implementation time and
  resolved the same way if it collides.

---

## Alternatives Considered

- **Keep `impl Aspect`, do nothing.** Leaves the exact inconsistency RFC-0098 set
  out to fix, in the one spot that sweep missed. Not chosen: "cheap to leave"
  isn't a reason once the underlying practice — find a Rust-tell while it's still
  isolated, replace it — is already this project's own stated norm.
- **Swift's `some Aspect`.** A genuinely strong option; RFC-0002's own survey
  rated it "very clean" and "semantically clear" against Rust's `impl`, and it is
  the closest real precedent for this exact position. Not chosen here because it
  introduces a fourth, unrelated keyword family (alongside `extend`, `aspect`,
  and `impl`-now-retired) instead of reusing a word Metel has already committed
  to for the same underlying relationship. Worth recording as the strongest
  runner-up, not dismissing it.
- **`is Aspect`.** Reads naturally at return position ("returns something that is
  Display") but oddly at parameter position ("x is Display" reads as an identity
  claim, not a capability bound) — asymmetric in a way `extends` (and `some`) are
  not.
- **Inventing a wholly new keyword pair rather than reusing `extend`'s own
  conjugation.** Considered and rejected: `extend`/`extends` already *is* that
  matching pair — same verb, subject-position conjugation, no new lexical family
  required.

---

## Unresolved Questions

None load-bearing. This is a pure lexical rename with an already-precedented
migration process (RFC-0098; the sweep discipline from RFC-0115/metel-core#585).
The only real work is the sweep itself, not any remaining design decision.

---

## References

- RFC-0002 (Aspect Bound Syntax, superseded) — Open Question 3, the original
  unresolved tension this RFC finally answers with a real rationale instead of a
  Rust-default pick; also the source of the TypeScript survey ("`extends` reads
  naturally") this RFC's keyword choice draws on directly.
- RFC-0035 (`impl Aspect` Anonymous Type Parameters, implemented) — amended,
  surface spelling only; desugaring, independence, and permitted-positions rules
  unchanged.
- RFC-0037 (Return-Position `impl Aspect`, implemented) — amended, surface
  spelling only; opacity and monomorphization rules unchanged.
- RFC-0098 (Surface Keyword Renames, implemented) — direct precedent and process
  template for this RFC; the source of the `extend` token whose conjugation this
  RFC reuses.
- RFC-0038 (`impl Aspect` in Struct Fields and Existential Types, draft) —
  explicitly unaffected; reserves `dyn Aspect` for a distinct, still-undesigned
  feature this RFC does not touch.
- metel-core#240 / #622 (T0022, landed this session) — the most recent code using
  the `impl Aspect` spelling; its diagnostic text and six negative fixtures are
  exactly what an implementation of this RFC would need to update.
- `public/reference/spec/declarations.md:859-888` — current spec text this RFC
  would rewrite once integrated.

---

## Decision

**Outcome:** *(pending)*
**Target:** *(set when accepted)*
