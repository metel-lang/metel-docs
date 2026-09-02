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
> hosts (§4) lands with the closure cluster (RFC-0050 / RFC-0134 / RFC-0152 / RFC-0153 /
> RFC-0157). Shipping v0.13.0 on the `(...)` spelling and switching to `|...|` afterward
> would migrate every closure signature in the corpus twice, so this co-lands rather than
> follows. **All four Open Questions resolved 2026-09-02** and §5 (nested-paren rule)
> added — acceptance-ready. RFC-0160 (Type Aliases) co-lands alongside it.

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
  expression's type; no `->` needed. It extends to the widest expression the
  surrounding precedence allows — a `,`, `)`, `]`, `}`, or a lower-precedence
  operator ends it, so `f(|x| x + 1, y)` is `f((|x| x + 1), y)` and
  `|x| x + 1 * 2` is `|x| (x + (1 * 2))` — Rust's rule.
- Nullary: `|| expr` / `|| { ... }`.

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

## Grammar: the `|` disambiguation rule

`|` is bitwise-or, `||` is logical-or. **Normative rule (Open Question 1, resolved):** a
closure literal — `|params| …` or `|| …` — is recognised **only in expression-start
position**: the beginning of an expression, or immediately after `=`, `:=`, `(`, `[`, `{`,
`,`, `return`, `->`, or a binary operator — any position where an operand is expected. In
any other position, `|` and `||` are the bitwise / logical-or operators. This resolves
both `|| expr` vs `a || b` and `|x| c` vs `a | b | c` with **no lexer split of `||`** —
the PEG's ordered choice plus the position rule is enough. It is Rust's rule.

In **type position** `|` is not an operator, so `|A| -> B` and `|| -> B` are unambiguous
with no rule needed.

## Migration

Hard switch, one-pass corpus sweep, no dual-accept — the same call RFC-0134 §3a
made, for the same reasons. **Sequenced into v0.13.0 with the closure cluster** so the
qualifier grammar and its base spelling land in one migration, not two. Three mechanical
rewrites:

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

## Open Questions

*All resolved 2026-09-02.*

1. **The `|` disambiguation rule** (§Grammar). **✓ Resolved — position-based, normative.**
   A closure literal opens only in expression-start position; `|` / `||` anywhere else is
   the bitwise / logical-or operator. No lexer split of `||`. Stated in §Grammar. (This
   also settles OQ4.)
2. **Is `->` mandatory in the type?** **✓ Resolved — yes.** `|A| -> B`, `|| -> C`.
   Dropping the arrow saves two characters, reads ambiguously beside generics, and loses
   the "returns" signal the literal's optional `-> Ret` shares.
3. **Bare-expression closure body** (§2). **✓ Resolved — allowed.** `closure_body = block
   | expr`; `|x| x * 2` is legal, has the expression's type, needs no `->`, and extends to
   the widest expression the surrounding precedence permits (a comma, `)`, `]`, `}`, or a
   lower-precedence operator ends it) — Rust's rule. Blocks are unchanged.
4. **`||` nullary spelling.** **✓ Resolved — `||`, by position (OQ1).** Not `| |`; a
   whitespace-significant form is a typo magnet and buys nothing.

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

**Outcome:** *(pending — `1-under-review` (#903), split from RFC-0134 §3a. **All four
Open Questions resolved 2026-09-02** (position-based `|` rule, `->` mandatory,
bare-expression bodies, `||` nullary); §5 nested-paren rule added. Grammar and migration
are both settled — acceptance-ready. Sequence with or before RFC-0151 and RFC-0125, both
of which need `(...)` back.)*
**Target:** **v0.13.0** — set 2026-09-02 to co-land with the closure cluster's `once` /
`var` qualifier grammar (§4) and with RFC-0160 (Type Aliases), so the base function-type
spelling migrates once rather than twice. Targeting precedes acceptance here for the same
reason RFC-0132 is v0.13.0-targeted while under review: real planned engagement, recorded
so sequencing decisions can be made against it.
