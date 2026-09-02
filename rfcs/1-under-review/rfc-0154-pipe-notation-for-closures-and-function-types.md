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
> review and implementation planning. RFC-0160 (Type Aliases) co-lands alongside it.

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
fun_type = { "|" ~ type_list? ~ "|" ~ "->" ~ type_expr }
```

`|A, B| -> C`. A nullary function type is `|| -> C`. The `->` is required.

### 2. Closure literal

```
closure_expr = { "|" ~ param_list? ~ "|" ~ ("->" ~ type_expr)? ~ block }
```

- Parameters: `|x|`, `|x, y|`, with optional per-parameter types `|x: i64, y: String|`.
- Optional return type: `|x| -> String { ... }`.
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

Reference qualifiers wrap the whole thing: `&|i64| -> String`,
`&var |i64| -> String` — a shared/exclusive reference *to* a function value.

### 5. Nested function types are parenthesized

A function type that appears as **another function type's return type or parameter
type** must be wrapped in `(...)`:

```
|Request| -> (|Response| -> Result)     // a function that returns a function
|(|i64| -> i64)| -> String              // a function that takes a function
```

Unparenthesized, `|A| -> |B| -> C` relies entirely on `->` right-associativity and on
the reader tracking where each `|...|` opens; the closure cluster's interleaved `once` /
`var` prefixes (`var |Request| -> once |Response| -> Result`) make the chain unreadable.
The parentheses give the nesting an unambiguous visual bracket, and a formatter inserts
them.

The rule is specifically *function-type-in-function-type*. A **named** function's own
signature is not nested, so it needs no parentheses:

```
fun make_counter() -> var || -> i64          // fine — `var || -> i64` is the fn's return, not nested in a fn type
fun compose(f: |A| -> B, g: |B| -> C) -> (|A| -> C)   // the return IS nested -> parenthesized
```

For anything deeper than one level, name it with a type alias (RFC-0160):
`type Curried = |A| -> (|B| -> C);`.

Grammar: in `fun_type = "|" ~ type_list? ~ "|" ~ "->" ~ type_expr`, a `type_expr` in the
`->` position (or inside `type_list`) that is itself a `fun_type` is only accepted
parenthesized. Reference-qualified function types (`&|A| -> B`) already read as a unit and
are unaffected; a bare qualifier prefix (`once`, `var`) is part of the `fun_type` it
precedes, so `|A| -> (once |B| -> C)` is the form, not `|A| -> once (|B| -> C)`.

## Grammar: the `|` wrinkle

`|` is bitwise-or and `||` is logical-or. The parser resolves both by expression
position; neither token is split or given a lexer-only special case:

- **Nullary `||`.** `|| { ... }` is a nullary closure only at expression start
  (after `=`, `(`, `,`, `return`, `->`, and analogous expression-introducing
  positions). `a || b` has a completed left operand and is always logical-or.
- **`|x|` inside an expression.** `a | b | c` (two bitwise-ors) versus a closure
  `|b| { c }` used as an argument. A closure is only recognised in expression-start
  position, never as the right operand of `|`.

Type position has no such conflict — `|` is not an operator there.

## Migration

Hard switch, one-pass corpus sweep, no dual-accept — the same call RFC-0134 §3a
made, for the same reasons. The closure cluster has already supplied the qualifier
grammar; this is its v0.13.0 syntax-migration follow-up. Three mechanical rewrites:

- Type position: `(T…) -> U` → `|T…| -> U`. Find by `) ->` in a type context.
- Expression position: `(params) -> Ret? { body }` → `|params| -> Ret? { body }`.
  Find by `closure_expr` nodes in the parsed tree, not text.
- Nested function types (§5): wrap a `fun_type` that is another `fun_type`'s return or
  parameter in `(...)`. Find by a `fun_type` node whose `->` child (or a `type_list`
  member) is itself a `fun_type`.

No runtime effect; nothing leaves the compiler.

## Interactions

- **RFC-0041 (`4-implemented`)** — this amends its surface syntax (the `(...)`
  choice), not its semantics. RFC-0041 gets a dated correction note.
- **RFC-0134 (Closure Call Capability)** — its §3a is removed and folded here;
  its `once`/`many` qualifier prefixes `|...|` (§4).
- **RFC-0153 (Closure Mutation Axis)** — its `var` qualifier likewise (§4).
- **RFC-0160 (Type Aliases, `1-under-review`)** — co-lands in v0.13.0. Aliases are the
  recommended tool for anything deeper than the one level §5 parenthesizes; RFC-0160's
  RHS uses this RFC's `|...|` form.
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
2. **Function-type arrow:** `->` is mandatory in `|A| -> B`.
3. **Closure body:** retain RFC-0041's block-only form. Bare-expression closures are
   out of scope and may be proposed separately after this migration.
4. **Nullary spelling:** `|| { ... }`, resolved by the same position rule as logical-or.

## References

- **RFC-0041 (Lambda Syntax for Anonymous Functions), `4-implemented`** — the
  RFC that dropped `fun` and chose `(...)`; this amends that surface choice.
- **RFC-0134 (Closure Call Capability)** — §3a split from here; the `once`/`many`
  qualifier this composes with.
- **RFC-0153 (Closure Mutation Axis)** — the `var` qualifier.
- **RFC-0160 (Type Aliases), `1-under-review`** — co-lands in v0.13.0; names deep /
  qualified function types so §5's parentheses appear once, in the alias, not at every use.
- **RFC-0151 (Tuples as Numeric-Label Rows)** — frees `(...)` for tuples/records,
  which is what makes the current function-type spelling ambiguous.
- **RFC-0125 (Variadic Generics)** — `|...Ts| -> R`.
- **RFC-0061 §7.4** — its unbuilt `fun(A) -> B` prose adopts `|A| -> B` here.
- **RFC-0006 (Closure Capture Semantics)** — unchanged; this is spelling only.

---

## Decision

**Outcome:** *(proposal complete — `1-under-review` (#903), split from RFC-0134 §3a.
All four grammar questions were resolved 2026-09-02. Acceptance review must verify the
position rule and the corpus migration.)*
**Target:** **v0.13.0** — follows the merged closure cluster as its syntax-migration
work, alongside RFC-0160 (Type Aliases). The migration is intentionally limited to
pipe notation; bare-expression closure bodies are not part of this release.
