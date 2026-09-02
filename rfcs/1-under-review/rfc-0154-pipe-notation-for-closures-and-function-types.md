---
id: rfc-0154
title: "Pipe Notation for Closures and Function Types"
date: '2026-08-30'
status: under-review
target: v0.13.0
updated: '2026-09-02'
tracking: 'https://github.com/metel-lang/metel-core/issues/903'
---

> **Brought into v0.13.0 (2026-09-02).** The `once` / `var` qualifier grammar this RFC
> uses has landed with the closure cluster (RFC-0050 / RFC-0134 / RFC-0152 / RFC-0153 /
> RFC-0157). This RFC now follows as the one corpus-wide syntax migration from the
> parenthesized implementation that shipped in that cluster. Its four grammar questions
> were resolved together on 2026-09-02; it remains `1-under-review` pending acceptance
> review and implementation planning. An adversarial review on 2026-09-02 found the
> initial pipe grammar had omitted capture lists; this revision restores them. RFC-0160
> (Type Aliases) co-lands alongside it. A second acceptance-review pass the same day
> trimmed §5's nested-type rule to a style recommendation (not a parse error; no tooling
> to enforce it yet) and dropped the conditional `copy` pre-declaration (RFC-0163 owns
> that word).
>
> **Scope (2026-09-02): the first iteration is the spelling migration and nothing more.**
> `->` and the return type are written wherever a function *type* is written — there is no
> infer-the-return form for a written type — and the closure *literal* keeps exactly
> RFC-0041's rule (return type inferred from the body when omitted). Bare-expression bodies
> and every other inference / omission convenience are deferred; real usage after v0.13.0
> decides which, if any, are worth adding.

> **Split from RFC-0134 §3a on 2026-08-30.** RFC-0134's acceptance review flagged
> that bundling a corpus-wide function-type grammar change into a closure-soundness
> RFC left half-swept normative examples, and that §3a's chosen spelling
> (`fun(T) -> U`) is a straight revert of RFC-0041's ergonomic change. The syntax
> question is its own RFC; this is it. RFC-0134 keeps only its `once`/`many`
> qualifier, which prefixes whatever spelling lands here.

> **Status — under review (2026-08-30).** Split from RFC-0134 §3a: the base function-type spelling is a corpus-wide grammar question. Proposes |T| -> U for the type and |x| body for the literal, freeing (...) for grouping and RFC-0151 tuples/records.

## Summary

Replace the `(...)` form for closure literals and function types with a `|...|`
form:

| Today (RFC-0041) | Proposed |
|---|---|
| `(x: i64) -> String { x.to_string() }` | `\|x: i64\| -> String { x.to_string() }` |
| `(x) -> i64 { x * 2 }` | `\|x\| { x * 2 }` |
| `() -> { print(x); }` | `\|\| { print(x); }` |
| `(i64, String) -> boolean` *(the type)* | `\|i64, String\| -> boolean` |
| `fun apply(f: (i64) -> i64)` | `fun apply(f: \|i64\| -> i64)` |

The closure literal and its type annotation then share one shape, and `(...)` is
freed entirely for grouping and for tuples / records (RFC-0151).

## Motivation

**RFC-0041 (`4-implemented`) was right to drop the `fun` keyword** from closure
literals — `items.map(fun(x: i64) -> i64 { x * 2 })` is noisier than it needs to
be. But it landed on `(...)`, and that spelling now collides in three ways:

- **Literal vs grouping / call.** `closure_expr` is `"(" ~ param_list? ~ ")" ~
  "->" ~ type_expr? ~ block` — a parenthesised list followed by `->`. It is told
  apart from an ordinary parenthesised expression only by lookahead for the
  `->`, and from a call only by what precedes the `(`.
- **Type vs grouping / tuple.** `fun_type` is `"(" ~ type_list? ~ ")" ~ "->" ~
  type_expr`, and `tuple_type` is `"(" ~ type_expr ~ ("," ~ type_expr)+ ~ ")"`.
  They share the `(` prefix; `fun_type` must be PEG-ordered ahead of
  `tuple_type` and disambiguated by backtracking past the `)`.
- **RFC-0151 makes that last one a true ambiguity, not just fragility.** Once
  `(A, B)` is the record type `{ 0: A, 1: B }`, `(A, B) -> C` cannot say whether
  it means a function of *two* arguments or a function of *one record* argument.

`|A, B| -> C` and `|(A, B)| -> C` say it. `|...|` for the literal and the type
means `let f: |i64| -> String = |n| { n.to_string() };` reads with the annotation
and the value in the same shape — today they diverge (`(i64) -> String` vs
`(n) -> String { ... }`).

RFC-0134 §3a proposed `fun(T) -> U` for the type. That is a revert of RFC-0041's
change in the type-annotation half and reads heavier, without unifying the
literal. This RFC keeps RFC-0041's lightness and fixes the collision it left.

## Proposal

### 1. Function type

```
fun_type = { fun_type_qualifier* ~ "|" ~ type_list? ~ "|" ~ "->" ~ type_expr }
fun_type_qualifier = { once_kw | var_kw }
```

`|A, B| -> C`. A nullary function type is `|| -> C`. The `->` and the return type are
always written: `|A|` with no `-> C` is a parse error, and there is **no** infer-the-return
form for a written type — a type annotation has no body to recover the return type from.
This is deliberately stricter than the closure literal (§2), which keeps RFC-0041's
body-inference; loosening it, if ever, waits on evidence from real signatures.
`once` and `var` are order-insensitive type qualifiers (from RFC-0134 / RFC-0153); they are
reserved words in v0.13.0, not ordinary identifiers. Making them contextual is a possible
future lexer/parser improvement, outside this RFC. RFC-0163, if accepted, adds a
type-only `copy` qualifier to this same `fun_type_qualifier` position — see Interactions.

### 2. Closure literal

```
closure_expr = { capture_list? ~ once_kw? ~ var_kw? ~ "|" ~ param_list? ~ "|" ~ ("->" ~ type_expr)? ~ block }
```

- The prefix order is fixed: `[captures]? once? var? |params|`. For example,
  `[state] once var |x: i64| -> String { ... }`. `var once` remains invalid on
  a literal even though type qualifiers are order-insensitive.
- Parameters: `|x|`, `|x, y|`, with optional per-parameter types `|x: i64, y: String|`.
- Return type: `|x| -> String { ... }`, or omitted — `|x| { ... }` — and inferred from the
  body, **exactly as RFC-0041 already does**. This RFC does not change that rule. The
  asymmetry with a written type (§1, where `->` and the return type are mandatory) is
  intentional: the literal has a body to infer from, a bare type annotation does not.
- Body: a block `|x| { ...; last }`. RFC-0041's block-only body rule is retained;
  a bare-expression form is deliberately out of scope for this migration.
- Nullary: `|| { ... }`.

### 3. `(...)` is freed

The `()` unit type/value, `(e)` grouping, `(a, b)` tuple/record (RFC-0151), and
call syntax `f(a, b)` are the only users of `(...)` after this. `fun_type` and
`closure_expr` no longer compete with any of them.

### 4. Qualifier composition

RFC-0134's `once` / `many` and RFC-0153's mutation qualifier (`var`) prefix the `|`:

```
once |i64| -> String
once var |i64| -> String        // RFC-0153; order-insensitive per RFC-0134 §5
```

The reserved-word rule applies equally to both qualifiers.

Reference qualifiers wrap the whole thing: `&|i64| -> String`,
`&var |i64| -> String` — a shared/exclusive reference *to* a function value.

### 5. Nested function types — right-associative; parentheses are a style recommendation

`->` is **right-associative**, so a function type nested as another's return or parameter
type parses unambiguously with no extra rule:

```
|A| -> |B| -> C                          // == |A| -> (|B| -> C)
var |Request| -> once |Response| -> Result   // == var |Request| -> (once |Response| -> Result)
```

Both spellings — with the parentheses and without — are legal and denote the same type.

The bare form *reads* badly once the closure cluster's `once` / `var` prefixes are
interleaved, so **the recommended style is to write the parentheses** around a function
type nested in another's return or parameter position: `|Request| -> (|Response| ->
Result)`. This is guidance for whoever writes the code — Metel has no formatter or linter
today, so nothing enforces it — and it is deliberately *not* a parse error in v0.13.0.
A formatter or lint could adopt the convention if either is built later, and a hard
grammar rule stays on the table if the bare form proves to read badly enough in real use
to warrant it.

Parentheses around a type are ordinary grouping — the same `(e)` that groups an
expression, here in type position — accepted anywhere a type is expected. They carry no
runtime or type-level identity, and a comma-free `( T )` is never a tuple (a tuple type
requires a comma). Reference-qualified function types read as a unit, so a nested one is
grouped the same way: `|A| -> (&|B| -> C)`. A qualifier prefix binds tighter than the
enclosing `->`, so `|A| -> once |B| -> C` is `|A| -> (once |B| -> C)`.

A **named** function's own signature is not a nested function type — nothing to
parenthesize:

```
fun make_counter() -> var || -> i64                    // `var || -> i64` is the return, not nested in a fn type
fun compose(f: |A| -> B, g: |B| -> C) -> |A| -> C      // legal; the recommended style writes the return as (|A| -> C)
```

For anything deeper than one level, name it with a type alias (RFC-0160): `type Curried =
|A| -> (|B| -> C);` — the nesting then never appears at a use site.

## Grammar: the `|` wrinkle

`||` is logical-or. The parser recognises `|| { ... }` as a closure only through
the ordinary expression-start / primary-expression production; it does not split
tokens or inspect a previous token in the lexer:

- **Nullary `||`.** `|| { ... }` is a nullary closure only at expression start
  (after `=`, `(`, `,`, `return`, `->`, and analogous expression-introducing
  positions). `a || b` has a completed left operand and is always logical-or.
- **`|x|` inside an expression.** `a | b | c` (two bitwise-ors) versus a closure
  `|b| { c }` used as an argument. Metel does not currently have a bitwise-OR
  operator, so this is not a current-language ambiguity or example. If one is
  added later, its precedence grammar must treat a pipe closure as an ordinary
  primary expression; this RFC reserves no special "not a right operand" rule.

Type position has no such conflict — `|` is not an operator there.

## Migration

Hard switch, one-pass corpus sweep, no dual-accept — the same call RFC-0134 §3a
made, for the same reasons. The closure cluster has already supplied the qualifier
grammar; this is its v0.13.0 syntax-migration follow-up. Two mechanical rewrites:

- Type position: `(T…) -> U` → `|T…| -> U`. Find by `) ->` in a type context.
- Expression position: `(params) -> Ret? { body }` → `|params| -> Ret? { body }`.
  Preserve the closure prefix: `[captures] once? var? (params)` becomes
  `[captures] once? var? |params|`. Find by `closure_expr` nodes in the parsed
  tree, not text.

Nested function types (§5) need no rewrite — the bare form stays legal. The recommended
style writes the parentheses around a `fun_type` nested in another's return or parameter
position, but nothing enforces that (Metel has no formatter or linter), so the sweep may
apply it as a readability pass or skip it. If RFC-0163 is later accepted, it carries its
own `copy` sweep.

No runtime effect; nothing leaves the compiler.

## Interactions

- **RFC-0041 (`4-implemented`)** — this amends its surface syntax (the `(...)`
  choice), not its semantics; its return-type inference on closure literals is left
  exactly as-is. RFC-0041 gets a dated correction note.
- **RFC-0134 (Closure Call Capability)** — its §3a is removed and folded here;
  its `once`/`many` qualifier prefixes `|...|` (§4).
- **RFC-0153 (Closure Mutation Axis)** — its `var` qualifier likewise (§4).
- **RFC-0163 (Function-Type Use-Multiplicity Surface, `1-under-review`)** — owns the
  type-only `copy` qualifier. This RFC deliberately does **not** pre-declare `copy` in its
  grammar: if RFC-0163 is accepted it adds `copy` to `fun_type_qualifier` and runs its own
  corpus sweep, prefixing whatever spelling this RFC lands. No dependency in the other
  direction.
- **RFC-0160 (Type Aliases, `1-under-review`)** — co-lands in v0.13.0. Aliases are the
  recommended tool for anything deeper than the one level §5's recommended parentheses
  cover; RFC-0160's RHS uses this RFC's `|...|` form.
- **RFC-0151 (Tuples as Numeric-Label Rows)** — the reason `(A, B) -> C` must
  stop being a function type; this RFC is what frees `(...)` for it.
- **RFC-0125 (Variadic Generics)** — `|...Ts| -> R` folds a pack into the
  parameter list; no extra rule beyond §1.
- **RFC-0061 §7.4** — currently writes function-pointer types as `fun(A) -> B` in
  prose (never implemented). It adopts `|A| -> B` here, with a correction note.

## Alternatives considered

### `fun(T) -> U` (RFC-0134 §3a's original)

A leading `fun` keyword on the type. Disambiguates, but reverts RFC-0041's
type-annotation change, reads heavier at every call site, and does not touch the
closure literal, so annotation and value still diverge. Rejected in favour of the
lighter form that also unifies the two.

### Keep `(T) -> U` (status quo)

Leaves the literal/grouping and type/tuple collisions, and cannot express
RFC-0151's two-arg-vs-one-record distinction at all. Rejected.

### `Fn(T) -> U` / trait-object style

That spelling is the `Callable` *aspect* (RFC-0061 §7.1 / metel-core#893), a
different thing — an erased, dispatched form. Not the bare function type.

## Resolved questions (2026-09-02)

1. **`|` / `||` disambiguation:** position-based parsing, as specified in
   [Grammar: the `|` wrinkle](#grammar-the--wrinkle); no lexer hack or token splitting.
2. **Function-type arrow:** `->` and the return type are mandatory in a written function
   type (`|A| -> B`); `|A|` alone is an error. The closure *literal* is unchanged from
   RFC-0041 — return type inferred from the body when omitted. An infer-the-return form for
   the *type*, and any other omission convenience, is out of scope for this migration and
   revisited only if real usage shows the annotation cost is high.
3. **Closure body:** retain RFC-0041's block-only form. Bare-expression closures are
   out of scope and may be proposed separately after this migration.
4. **Nullary spelling:** `|| { ... }`, resolved by the same position rule as logical-or.

## Acceptance tests

The implementation must cover, at minimum:

- capture-list literals in every prefix combination (`[x] |x|`, `[x] once |x|`,
  `[&var x] var ||`, `[x] once var |x|`), including the rejected `var once` literal;
- nullary closure and function types at expression/type start, and ordinary `a || b`;
- closure literals after `=`, `(`, `,`, and `return`;
- nested function types in parameters and returns, **both** unparenthesized (`|A| -> |B|
  -> C`) and grouped (`|A| -> (|B| -> C)`), parsing to the same type, including a nested
  reference-qualified function type;
- tuple types beside grouped function types, proving `(A, B)` remains a tuple while
  `(|A| -> B)` is grouping; and
- every accepted `once` / `var` qualifier combination and order in function types.

## References

- **RFC-0041 (Lambda Syntax for Anonymous Functions), `4-implemented`** — the
  RFC that dropped `fun` and chose `(...)`; this amends that surface choice.
- **RFC-0134 (Closure Call Capability)** — §3a split from here; the `once`/`many`
  qualifier this composes with.
- **RFC-0153 (Closure Mutation Axis)** — the `var` qualifier.
- **RFC-0160 (Type Aliases), `1-under-review`** — co-lands in v0.13.0; names deep /
  qualified function types so a nested `|A| -> (|B| -> C)` appears once, in the alias,
  not at every use.
- **RFC-0151 (Tuples as Numeric-Label Rows)** — frees `(...)` for tuples/records,
  which is what makes the current function-type spelling ambiguous.
- **RFC-0125 (Variadic Generics)** — `|...Ts| -> R`.
- **RFC-0061 §7.4** — its unbuilt `fun(A) -> B` prose adopts `|A| -> B` here.
- **RFC-0006 (Closure Capture Semantics)** — unchanged; this is spelling only.

---

## Decision

**Outcome:** *(proposal complete — `1-under-review` (#903), split from RFC-0134 §3a.
All four grammar questions were resolved 2026-09-02; the acceptance-review follow-ups
(2026-09-02) trimmed §5 to a non-enforced style recommendation and removed the
conditional `copy` pre-declaration. Acceptance review must verify the capture-prefix
grammar, the
`|` / `||` position rule, and the corpus migration.)*
**Target:** **v0.13.0** — follows the merged closure cluster as its syntax-migration
work, alongside RFC-0160 (Type Aliases). The migration is intentionally limited to
pipe notation; bare-expression bodies, and any return-type-omission convenience beyond
RFC-0041's existing literal inference, are not part of this release — usage after v0.13.0
decides which, if any, are worth adding.
