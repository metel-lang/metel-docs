---
id: rfc-0154
title: "Pipe Notation for Closures and Function Types"
date: '2026-08-30'
status: under-review
target:
updated: '2026-08-30'
tracking: 'https://github.com/metel-lang/metel-core/issues/903'
---

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
| `(x) -> x * 2` *(n/a — needs block)* → `(x) -> i64 { x * 2 }` | `\|x\| x * 2` |
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
means `let f: |i64| -> String = |n| n.to_string();` reads with the annotation and
the value in the same shape — today they diverge (`(i64) -> String` vs
`(n) -> String { ... }`).

RFC-0134 §3a proposed `fun(T) -> U` for the type. That is a revert of RFC-0041's
change in the type-annotation half and reads heavier, without unifying the
literal. This RFC keeps RFC-0041's lightness and fixes the collision it left.

## Proposal

### 1. Function type

```
fun_type = { "|" ~ type_list? ~ "|" ~ "->" ~ type_expr }
```

`|A, B| -> C`. A nullary function type is `|| -> C`. The `->` is required (Open
Question 2).

### 2. Closure literal

```
closure_expr = { "|" ~ param_list? ~ "|" ~ ("->" ~ type_expr)? ~ closure_body }
closure_body = { block | expr }
```

- Parameters: `|x|`, `|x, y|`, with optional per-parameter types `|x: i64, y: String|`.
- Optional return type: `|x| -> String { ... }`.
- Body: a block `|x| { ...; last }` **or** a bare expression `|x| x * 2` (new —
  RFC-0041's grammar required a block). A bare-expression body has the
  expression's type; no `->` needed.
- Nullary: `|| expr` / `|| { ... }`.

### 3. `(...)` is freed

The `()` unit type/value, `(e)` grouping, `(a, b)` tuple/record (RFC-0151), and
call syntax `f(a, b)` are the only users of `(...)` after this. `fun_type` and
`closure_expr` no longer compete with any of them.

### 4. Qualifier composition

RFC-0134's `once` / `many` and RFC-0153's mutation qualifier prefix the `|`:

```
once |i64| -> String
once mut |i64| -> String        // RFC-0153; order-insensitive per RFC-0134 §5
```

Reference qualifiers wrap the whole thing: `&|i64| -> String`,
`&var |i64| -> String` — a shared/exclusive reference *to* a function value.

## Grammar: the `|` wrinkle

`|` is bitwise-or and `||` is logical-or. Two cases need a rule:

- **Nullary `||`.** `|| expr` (a nullary closure) versus `a || b` (logical-or).
  A closure literal only starts an expression or follows `=`, `(`, `,`, `return`,
  `->`, etc.; `a || b` has a left operand. Resolvable by position, as Rust does;
  the RFC should state the rule rather than leave it to the parser.
- **`|x|` inside an expression.** `a | b | c` (two bitwise-ors) versus a closure
  `|b| c` used as an argument. Same resolution: a closure is only recognised in
  expression-start position, never as the right operand of `|`.

Type position has no such conflict — `|` is not an operator there.

## Migration

Hard switch, one-pass corpus sweep, no dual-accept — the same call RFC-0134 §3a
made, for the same reasons. Two mechanical rewrites:

- Type position: `(T…) -> U` → `|T…| -> U`. Find by `) ->` in a type context.
- Expression position: `(params) -> Ret? { body }` → `|params| -> Ret? { body }`.
  Find by `closure_expr` nodes in the parsed tree, not text.

No runtime effect; nothing leaves the compiler.

## Interactions

- **RFC-0041 (`4-implemented`)** — this amends its surface syntax (the `(...)`
  choice), not its semantics. RFC-0041 gets a dated correction note.
- **RFC-0134 (Closure Call Capability)** — its §3a is removed and folded here;
  its `once`/`many` qualifier prefixes `|...|` (§4).
- **RFC-0153 (Closure Mutation Axis)** — its `mut` qualifier likewise (§4).
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

## Open Questions

1. **The `|` disambiguation rule** (§Grammar) — position-based, as sketched, or is
   an explicit lexer hack (`||` as one token that splits) needed? Nail it before
   acceptance.
2. **Is `->` mandatory in the type?** `|A| -> B` versus a shorter `|A| B`. The
   arrow keeps parsing simple and reads clearly; dropping it saves two
   characters. Leaning: keep `->`.
3. **Bare-expression closure body** (§2) — add it, or keep RFC-0041's
   block-only rule and require `|x| { x * 2 }`? Bare expressions are the common
   `map`/`filter` case and match every other language with this notation.
4. **`||` nullary spelling.** `|| expr` reads oddly next to logical-or. Is there
   appetite for `| | expr` (space-separated) or a different nullary form? Most
   languages accept `||` and rely on position.

## References

- **RFC-0041 (Lambda Syntax for Anonymous Functions), `4-implemented`** — the
  RFC that dropped `fun` and chose `(...)`; this amends that surface choice.
- **RFC-0134 (Closure Call Capability)** — §3a split from here; the `once`/`many`
  qualifier this composes with.
- **RFC-0153 (Closure Mutation Axis)** — the `mut` qualifier.
- **RFC-0151 (Tuples as Numeric-Label Rows)** — frees `(...)` for tuples/records,
  which is what makes the current function-type spelling ambiguous.
- **RFC-0125 (Variadic Generics)** — `|...Ts| -> R`.
- **RFC-0061 §7.4** — its unbuilt `fun(A) -> B` prose adopts `|A| -> B` here.
- **RFC-0006 (Closure Capture Semantics)** — unchanged; this is spelling only.

---

## Decision

**Outcome:** *(pending — draft, opened 2026-08-30, split from RFC-0134 §3a. The
grammar is straightforward once the `|` disambiguation rule (Open Question 1) is
fixed; migration is mechanical. Sequence with or before RFC-0151 and RFC-0125,
both of which need `(...)` back.)*
**Target:** *(set when accepted.)*
