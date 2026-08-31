---
id: rfc-0156
title: "Parenthesize match Scrutinee"
date: '2026-08-31'
target:
status: under-review
updated: '2026-08-31'
tracking: 'https://github.com/metel-lang/metel-core/issues/701'
---

> **Status — under review (2026-08-31).** Single substantiated proposal: parenthesize the match scrutinee to match if/while/for. No load-bearing open questions; tuple-scrutinee interaction resolved by reusing tuple_or_paren. Mechanical sweep, RFC-0130/0136 precedent.

## Summary

Require parentheses around a `match` expression's scrutinee, so that `match (x) { … }`
is the only accepted spelling and `match x { … }` is a parse error. This aligns `match`
with every other scrutinee/condition construct in the grammar — `if`, `while`, `for`,
`for`-in all already require the parentheses. A pure surface-syntax change: pattern
matching, exhaustiveness, arm typing, reference-transparent scrutinees (RFC-0108),
bare-variant patterns (RFC-0107), and arm-block rules (RFC-0018) are all untouched.

---

## Motivation

Checked directly against `metel-frontend/src/grammar.pest`:

```pest
if_expr      = { "if"    ~ "(" ~ expr ~ ")" ~ (block | expr) ~ ("else" ~ …)? }
while_stmt   = { "while" ~ "(" ~ expr ~ ")" ~ block }
for_stmt     = { "for"   ~ "(" ~ for_init ~ expr? ~ ";" ~ expr? ~ ")" ~ block }
for_in_stmt  = { "for"   ~ "(" ~ … ~ "in" ~ expr ~ ")" ~ block }
match_expr   = { "match" ~ expr ~ "{" ~ (match_arm ~ ("," ~ match_arm)* ~ ","?)? ~ "}" }
```

`match` is the one construct that does not require the parentheses. `match (y) { … }`
is accepted today only incidentally — `(y)` already parses as an ordinary parenthesized
expression (`tuple_or_paren`), so `match (y) { … }` and `match y { … }` both work,
verified against the interpreter. Nothing in the grammar makes the parentheses
mandatory the way `if` / `while` / `for` do.

The result is a reader- and writer-facing inconsistency: the same "keyword, then the
thing being tested, then a body" shape is spelled two ways depending on which keyword it
is. Every other construct in this family was given the parentheses deliberately;
`match` was not, and there is no recorded rationale for the difference — it is an
accident of the grammar, the same kind of unargued inheritance RFC-0130 and RFC-0098
set out to remove elsewhere in the surface syntax.

Doing it now: `match` scrutinee syntax is otherwise stable, and the migration surface
only grows. v0.13 already carries two surface-syntax sweeps (RFC-0130 `extends`,
RFC-0136 `:=`); folding this normalization into the same release keeps the churn in one
place rather than spreading a third breaking parse change across a later version.

---

## 1. The rule

`match`'s scrutinee must be parenthesized. The grammar rule becomes:

```pest
match_expr = { "match" ~ tuple_or_paren ~ "{" ~ (match_arm ~ ("," ~ match_arm)* ~ ","?)? ~ "}" }
```

`tuple_or_paren` is the existing production:

```pest
tuple_or_paren = { "(" ~ expr ~ ("," ~ expr)+ ~ ")" | "(" ~ expr ~ ")" }
```

Reusing it rather than writing a fresh `"(" ~ expr ~ ")"` is deliberate — it is what
keeps a **tuple scrutinee** working. `match (a, b) { (0, 0) => … }` is common and valid
today; under a naive `"(" ~ expr ~ ")"` rule the parser would consume `(`, match `a` as
`expr`, then fail on the `,`. With `tuple_or_paren`, the scrutinee's own parentheses
double as the required ones, exactly as they do today.

**What stays valid (no source change needed):**

| Form | Meaning |
|---|---|
| `match (x) { … }` | single parenthesized scrutinee |
| `match (a, b) { … }` | tuple scrutinee — the tuple's parentheses are the required ones |
| `match (f(x)) { … }` | any expression, parenthesized |
| `match ((a, b)) { … }` | still accepted; inner parens are the tuple, outer are redundant grouping |

**What becomes a parse error:**

| Form | Was | Now |
|---|---|---|
| `match x { … }` | accepted | `P0001` parse error — parentheses required |
| `match f(x) { … }` | accepted | `P0001` |
| `match x.field { … }` | accepted | `P0001` |

Nothing else about `match` moves. The scrutinee is still an arbitrary expression, still
type-checked the same way, still reference-peeled per RFC-0108, still the resolution
context for bare-variant patterns per RFC-0107. The `MatchExpr` AST node is unchanged;
the parser unwraps `tuple_or_paren` to recover the scrutinee expression (a single inner
`expr`, or a synthesized tuple expression for the 2+-element form) exactly as it already
does everywhere `tuple_or_paren` appears.

### Diagnostic

A bare scrutinee is a `P0001` parse error. The message should name the fix directly —
`match requires parentheses around its scrutinee: write \`match (x) { … }\`` — rather
than the raw "expected `{`" the grammar would produce, since this is the one error every
pre-migration `.mtl` file will hit. Whether that is a dedicated parser check or a
recovery hint on the generic `P0001` is an implementation detail for metel-core#701.

---

## Migration

`match` appears across the corpus in an identifiable, mechanically-rewritable set of
places. Per `PROCESS.md`'s "changes existing syntax" exit criteria, the sweep lands in
the same change as the grammar flip, not as a follow-up:

- **Scope the rewrite to `match` keyword sites**, not a blind regex. An AST-driven
  rewriter (the RFC-0136 `walrus_migrate.rs` precedent) is the right tool: parse under
  the old grammar, find every `match_expr`, and wrap the scrutinee span in parentheses
  unless it is already a `tuple_or_paren`. This correctly leaves `match (a, b) { … }`
  and `match (x) { … }` alone and only touches the bare forms.
- **Sweep prose, not only code.** Every `` ```metel `` block showing a bare `match` in
  `reference/spec/` (≈30 sites in `expressions.md` and `types.md` alone), `getting-started/`,
  `docs/blog/`, and the `rfcs/` examples the parser can reach. Rust snippets and other
  non-Metel fenced blocks are excluded.
- **stdlib** (`metel-frontend/stdlib/*.mtl`) and the **fixture corpus**
  (`metel-interpreter/tests/integration/sources/**/*.mtl`) — the largest count, all
  mechanical.
- **Inline Metel in Rust** — `r#"…"#` test strings in `metel-frontend` / `metel-interpreter`.
- **Negative fixture**: `parsing/neg_NN_bare_match_scrutinee.mtl` asserting `match x { … }`
  is now `P0001`, the hard-switch guard (the RFC-0130 `neg_13` / RFC-0136 `neg_14`
  precedent).
- **Changelog** entry under v0.13.0, flagged as a syntax-breaking change.
- **Identifier audit**: none needed — no new keyword or reserved word is introduced,
  only a punctuation requirement.
- **`check_doc_examples.py`** and the full fixture suite must pass against the flipped
  grammar; one hand-extracted prose example compiled by hand, per `PROCESS.md`.

No transition alias / deprecation period: the language is not used publicly, so once the
in-repo surface is migrated there is nothing to keep a grace path for (the RFC-0136
OQ#4 reasoning applies unchanged).

---

## Spec integration

At `3-integrated`, `reference/spec/expressions.md` "Pattern Matching" gains a Legality
Rule stating the scrutinee must be parenthesized, and RFC-0156 is recorded as its
origin:

```
##### Legality Rule {#spec.expressions.pattern-matching.legality-3}

A `match` expression's scrutinee must be enclosed in parentheses; the bare form
`match x { … }` is a parse error. A tuple scrutinee's own parentheses satisfy this.
```

`coverage` frontmatter maps this RFC's §1 to `spec.expressions.pattern-matching.legality-3`,
cited by the negative fixture above and by any positive `match (…)` fixture.

---

## Alternatives Considered

- **Do nothing — keep `match x { … }` accepted.** Leaves the inconsistency in place.
  "Cheap to leave" is not a reason once "find the unargued Rust/grammar inheritance and
  normalize it" is already this project's stated practice (RFC-0098, RFC-0130).
- **Drop the parentheses from `if` / `while` / `for` instead**, normalizing the other
  way. Much larger and riskier change (dangling-brace ambiguity in `if cond { }`, which
  is exactly why C-family grammars keep the parens or require braces), touches four
  constructs instead of one, and throws away the disambiguation the parens already buy.
  Not chosen.
- **Accept both spellings forever**, treating the parens as optional sugar. That is the
  status quo; it is the thing being removed. An optional-delimiter rule is precisely
  the kind of "two ways to write one thing" the surface-syntax cleanups exist to close.
- **Fresh `"(" ~ expr ~ ")"` rule** instead of reusing `tuple_or_paren`. Rejected: it
  breaks `match (a, b) { … }` tuple scrutinees, as shown in §1.

---

## Unresolved Questions

None load-bearing. The design surface is a single grammar rule; the tuple-scrutinee
interaction is resolved in §1 by reusing `tuple_or_paren`. The only real work is the
sweep, which has three recent precedents (RFC-0098, RFC-0130, RFC-0136).

---

## References

- **metel-core#701** — the tracking issue; its body established the inconsistency
  against `grammar.pest` and the breaking-change framing this RFC formalizes.
- **RFC-0130** (`extends Aspect`, implemented) — direct process template: a
  single-rule surface-syntax normalization with a mechanical sweep and a `neg_*`
  hard-switch guard, same v0.13 release.
- **RFC-0136** (Walrus for Kept Bindings, implemented) — the largest recent
  surface-syntax migration; source of the AST-driven-rewriter approach and the
  "no transition alias, not used publicly" migration stance.
- **RFC-0098** (Surface Keyword Renames, implemented) — the "normalize the unargued
  inheritance" practice this RFC continues.
- **RFC-0108** (Reference-Transparent Match Scrutinees, implemented),
  **RFC-0107** (Unqualified Enum Variants in Match Patterns, implemented),
  **RFC-0018** (Match Arm Blocks, implemented) — the match-semantics RFCs this change
  explicitly does **not** touch.
- `reference/spec/expressions.md` "Pattern Matching" — the spec section that gains the
  new Legality Rule at integration.

---

## Decision

**Outcome:** *(pending)*
**Target:** *(set when accepted)*
