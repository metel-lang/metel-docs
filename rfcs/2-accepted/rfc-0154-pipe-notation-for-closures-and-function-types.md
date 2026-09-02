---
id: rfc-0154
title: "Pipe Notation for Closures and Function Types"
date: '2026-08-30'
status: accepted
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
> that word). An adversarial pass the same day made explicit that this RFC **supersedes**
> RFC-0041's rule that `->` precede every closure body (spec `closures.legality-1`/`-2`/
> `-3`) — `|…|` self-disambiguates, so the arrow is written only with a return type — and
> flagged the grammar productions as illustrative and the RFC-0151 / RFC-0125 interactions
> as anticipatory (both unscheduled).
>
> **Scope (2026-09-02): the first iteration is the spelling migration and nothing more.**
> `->` and the return type are written wherever a function *type* is written — there is no
> infer-the-return form for a written type. The closure *literal* keeps RFC-0041's
> return-type inference (inferred from the body when omitted); the `->` RFC-0041 required
> before *every* body is dropped for that case (§2), with `|…|` doing the disambiguation
> the arrow used to. Bare-expression bodies and every other inference / omission
> convenience are deferred; real usage after v0.13.0 decides which, if any, are worth adding.

> **Split from RFC-0134 §3a on 2026-08-30.** RFC-0134's acceptance review flagged
> that bundling a corpus-wide function-type grammar change into a closure-soundness
> RFC left half-swept normative examples, and that §3a's chosen spelling
> (`fun(T) -> U`) is a straight revert of RFC-0041's ergonomic change. The syntax
> question is its own RFC; this is it. RFC-0134 keeps only its `once`/`many`
> qualifier, which prefixes whatever spelling lands here.

> **Status — under review (2026-08-30).** Split from RFC-0134 §3a: the base function-type spelling is a corpus-wide grammar question. Proposes |T| -> U for the type and |x| body for the literal, freeing (...) for grouping and RFC-0151 tuples/records.

> **Status — accepted (2026-09-02).** spelling migration settled; §5 advisory, copy deferred to RFC-0163, RFC-0041 legality-1/2/3 supersession explicit; F1-F11 addressed

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
- **RFC-0151 *would* make that last one a true ambiguity, not just fragility.** RFC-0151
  (`0-draft`, unscheduled) makes `(A, B)` the record type `{ 0: A, 1: B }`; then
  `(A, B) -> C` cannot say whether it is a function of *two* arguments or of *one record*
  argument. That collision is anticipatory — the first two are live today and are reason
  enough to move.

`|A, B| -> C` says two arguments unambiguously; `|(A, B)| -> C` says one record argument
once `(A, B)` type syntax exists (RFC-0151). `|...|` for the literal and the type also
means `let f: |i64| -> String = |n| { n.to_string() };` reads with the annotation and the
value in the same shape — today they diverge (`(i64) -> String` vs `(n) -> String { ... }`).

RFC-0134 §3a proposed `fun(T) -> U` for the type. That is a revert of RFC-0041's
change in the type-annotation half and reads heavier, without unifying the
literal. This RFC keeps RFC-0041's lightness and fixes the collision it left.

## Proposal

The productions below are **illustrative**. Metel's spec states closure grammar as prose
(`spec.functions.closures.legality-1`), not a maintained EBNF; `type_list`, `param_list`,
`capture_list`, and `block` are the existing nonterminals from RFC-0041 and RFC-0050. This
RFC changes two things: the delimiter (`(...)` → `|...|`), and — for the closure *literal*
only — the arrow's optionality (§2).

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
- Return type: `|x| -> String { ... }` when written, or omitted — `|x| { ... }` — and
  inferred from the body. **This supersedes RFC-0041** (spec
  `spec.functions.closures.legality-1`/`-2`/`-3`), which required `->` before *every*
  closure body (`(x) -> { x * 2 }`, `() -> { ... }`). That mandatory arrow was RFC-0041's
  disambiguator between `(x)` grouping and `(x) -> {}` a closure; `|...|` carries that
  itself, so the arrow now appears **exactly when a return type is written**. Return-type
  *inference* from the body is unchanged. The result is an intentional asymmetry with a
  written *type* (§1, `->` and the return type mandatory): a literal has a body to infer
  from, a bare type annotation does not.
- Body: a block `|x| { ...; last }`. RFC-0041's block-only body rule is retained; a
  bare-expression form is out of scope for this migration. A bare `{ ... }` with no
  preceding `|...|` is still a block expression — RFC-0041's `() -> { ... }` becomes
  `|| { ... }`, not `{ ... }`.
- Nullary: `|| { ... }`.

### 3. `(...)` is freed

The `()` unit type/value, `(e)` grouping, `(a, b)` tuple/record (RFC-0151), and
call syntax `f(a, b)` are the only users of `(...)` after this. `fun_type` and
`closure_expr` no longer compete with any of them.

### 4. Qualifier composition

RFC-0134's `once` (its `many` counterpart is the unwritten default and never appears in a
type spelling) and RFC-0153's mutation qualifier (`var`) prefix the `|`:

```
once |i64| -> String
once var |i64| -> String        // RFC-0153; order-insensitive per RFC-0134 §5
```

The reserved-word rule applies equally to both qualifiers.

Reference qualifiers wrap the whole thing, **outermost**: `&` / `&var`, then `once` /
`var`, then `|...|`. `&var once var |T| -> U` is `&var (once var |T| -> U)` — an exclusive
reference *to* a `once`-`var` function value. A reference qualifier placed *after* a type
qualifier (`once &var |T| -> U`) is a parse error. The mutation qualifier `var` is not
repeatable: `var var |T| -> U` is an error — the only other `var` a function type can
carry is the one attached to `&` (`&var`), which is a reference, not a second prefix.

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

`||` is logical-or. The parser recognises `|| ...` as a closure through the ordinary
operand-position production; it does not split tokens or inspect a previous token in the
lexer:

- **Nullary `||`.** `||` opens a nullary closure (or, in type position, a nullary
  function type) **wherever the parser expects an operand rather than an operator** — the
  head of an expression, or any type position. With a completed left operand in hand
  (`a || b`), `||` is logical-or. This is exactly Rust's rule, minus the bitwise-`|` case
  Rust also has to handle.
- **`|x|` inside an expression.** `a | b | c` (bitwise-or) versus a closure `|b| { c }`
  used as an argument. Metel has no bitwise-`|` operator, so this is not a current
  ambiguity. If one is added later, its precedence grammar must treat a pipe closure as an
  ordinary primary expression; this RFC reserves no special "not a right operand" rule.

Type position has no such conflict *today* — `|` is not an operator there. If Metel later
adds an `A | B` union / sum-type spelling it would collide with `|...|` in type position
the same way a bitwise-`|` would in expression position; the RFC that introduces one must
reconcile them (require the union inside the pipes, or pick a different union spelling).

## Migration

Hard switch, one-pass corpus sweep, no dual-accept — the same discipline the closure
cluster and RFC-0115 used. Metel has no public users, so a single sweep beats a
dual-accept window. Everything below is located by parsed-tree node, **never by text**:

- **Type position:** `(T…) -> U` → `|T…| -> U`. Find by `fun_type` nodes — *not* by `) ->`
  text, which also matches every named `fun f(x: T) -> U` declaration (those keep
  `(...)`). Any `fun(T…) -> U` still left in RFC or spec prose migrates too (the stray one
  in `closures.legality-24` is corrected separately).
- **Expression position:** `(params) -> Ret { body }` → `|params| -> Ret { body }`, and
  `(params) -> { body }` → `|params| { body }` — the inferred-return form loses its arrow
  (§2). Preserve the prefix: `[captures] once? var? (params)` → `[captures] once? var?
  |params|`. Find by `closure_expr` nodes.
- **Spec anchors:** `spec.functions.first-class-functions.legality-1` (the `(T) -> U` type
  form) and `spec.functions.closures.legality-1`/`-2`/`-3` (the `(params) -> ret? { body
  }` literal form and the "arrow before every body" rule this RFC supersedes) are reworded
  to the `|...|` forms and their citing fixtures re-anchored, in the same change.

Nested function types (§5) need no rewrite — the bare form stays legal. The recommended
style writes the parentheses around a `fun_type` nested in another's return or parameter
position, but nothing enforces that (Metel has no formatter or linter), so the sweep may
apply it as a readability pass or skip it. If RFC-0163 is later accepted, it carries its
own `copy` sweep.

No runtime effect; nothing leaves the compiler.

## Interactions

- **RFC-0041 (`4-implemented`)** — this amends its surface syntax and **supersedes** its
  rule that `->` precede every closure body (spec `closures.legality-1`/`-2`/`-3`): with
  `|...|` self-disambiguating, the arrow is written only with a return type. Closure
  semantics — capture, `fun`-only-for-named, return-type *inference* from the body — are
  unchanged. RFC-0041 and its spec anchors get dated correction notes.
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
- **RFC-0151 (Tuples as Numeric-Label Rows, `0-draft`, unscheduled)** — the *anticipated*
  reason `(A, B) -> C` must stop being a function type. This RFC frees `(...)` ahead of
  it; the `|(A, B)| -> C` one-record-parameter form becomes writable only once `(A, B)`
  type syntax lands.
- **RFC-0125 (Variadic Generics, `1-under-review`, unscheduled)** — when it lands,
  `|...Ts| -> R` folds a pack into the parameter list with no extra rule beyond §1.
- **RFC-0061** — its `fun(A) -> B` function-pointer prose is *already* superseded in the
  spec (`declarations.md`: "no separate function-pointer type … `fun(A) -> B` is a parse
  error"; plain functions and closures share one `(A) -> B` type). This RFC only carries
  that spelling forward to `|A| -> B`; RFC-0061's own prose still needs the sweep, with a
  correction note.

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
   *type* (`|A| -> B`); `|A|` alone is an error, and there is no infer-the-return form for
   a written type. The closure *literal* keeps RFC-0041's return-type *inference* (from the
   body when omitted) but drops the `->` RFC-0041 required before *every* body — see §2.
   An infer-the-return form for the type, and any other omission convenience, is out of
   scope for this migration and revisited only if real usage shows the annotation cost is
   high.
3. **Closure body:** retain RFC-0041's block-only form. Bare-expression closures are out of
   scope. The `->` RFC-0041 placed before every body is not replaced by anything — the
   `|...|` delimiters do that disambiguation (§2).
4. **Nullary spelling:** `|| { ... }`, resolved by the operand-position rule that also
   settles logical-or.

## Acceptance tests

The implementation must cover, at minimum:

- capture-list literals in every prefix combination (`[x] |x|`, `[x] once |x|`,
  `[&var x] var ||`, `[x] once var |x|`), including the rejected `var once` literal;
- a closure literal with **no** `->` (`|x| { ... }`, `|| { ... }`) and with `-> T { ... }`
  — both parse; a bare `{ ... }` with no `|...|` is a block, not a nullary closure;
- nullary closure and function types at expression/type start, and ordinary `a || b`;
- closure literals after `=`, `(`, `,`, and `return`;
- the `&` / `&var` / `once` / `var` prefix order on a function type, including the rejected
  `once &var |T| -> U` and `var var |T| -> U`;
- nested function types in parameters and returns, **both** unparenthesized (`|A| -> |B|
  -> C`) and grouped (`|A| -> (|B| -> C)`), parsing to the same type, including a nested
  reference-qualified function type;
- (once `(A, B)` type syntax exists — RFC-0151) tuple types beside grouped function types,
  proving `(A, B)` is a tuple while `(|A| -> B)` is grouping; and
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
- **RFC-0151 (Tuples as Numeric-Label Rows), `0-draft`** — the anticipated collision that
  makes the current function-type spelling ambiguous; unscheduled.
- **RFC-0125 (Variadic Generics), `1-under-review`** — `|...Ts| -> R`; unscheduled.
- **RFC-0061** — its `fun(A) -> B` function-pointer prose (already a spec parse error)
  adopts `|A| -> B` here.
- **RFC-0006 (Closure Capture Semantics)** — unchanged; this is spelling only.

---

## Decision

**Outcome:** **Accepted 2026-09-02** (`2-accepted`, #903), split from RFC-0134 §3a. All
four grammar questions were resolved 2026-09-02; two follow-up passes the same day trimmed
§5 to a non-enforced style recommendation, removed the conditional `copy` pre-declaration,
and — from an adversarial pass — made the supersession of RFC-0041's mandatory `->`
explicit (§2, Migration), flagged the grammar productions as illustrative, resolved the
`&` / `&var` / `once` / `var` prefix ordering, and marked the RFC-0151 / RFC-0125
interactions anticipatory. **Carried into `3-integrated`** (umbrella checklist on #903):
reword `first-class-functions.legality-1` and `closures.legality-1`–`3` to the `|...|`
forms, re-anchor their citing fixtures, and add worked examples hunting for soundness gaps
at the intersections with the closure cluster.
**Target:** **v0.13.0** — follows the merged closure cluster as its syntax-migration
work, alongside RFC-0160 (Type Aliases). The migration is intentionally limited to
pipe notation; bare-expression bodies, and any return-type-omission convenience beyond
RFC-0041's existing literal inference, are not part of this release — usage after v0.13.0
decides which, if any, are worth adding.
