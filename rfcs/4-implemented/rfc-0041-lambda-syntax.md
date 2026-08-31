---
status: implemented
spec_status: done
id: rfc-0041
title: "Lambda Syntax for Anonymous Functions"
date: '2026-06-01'
coverage:
  "1": { spec: "spec.functions.closures.legality-1" }
  "2": { spec: "spec.functions.closures.legality-2" }
  "3": { spec: "spec.functions.closures.legality-3" }
  "4": { spec: "spec.functions.first-class-functions.legality-1" }
  "5": { spec: "spec.functions.named-function-declarations.legality-1" }
  "6": { spec: "spec.functions.closures.legality-4" }
---

## Summary

Replace the `fun(...) -> { }` syntax for anonymous functions (closures) with a lighter `(...) -> { }` form, dropping the `fun` keyword. The `fun` keyword remains required for named function declarations. The corresponding closure type annotation changes from `fun(T) -> U` to `(T) -> U`.

> **Correction 2026-08-30 — the `(...)` surface choice is being revised, not the goal.**
> Dropping `fun` was right, but `(...)` collides with grouping, call syntax, and — once
> RFC-0151 makes `(A, B)` a record type — genuinely ambiguously with tuple/record types
> (`(A, B) -> C` cannot say two-args-versus-one-record). **RFC-0154 (Pipe Notation for
> Closures and Function Types)** moves the closure literal and the function type to
> `|...|` (`|x, y| body`, `|A, B| -> C`), keeping this RFC's lightness while freeing
> `(...)`. This RFC's semantics — anonymous functions, capture, the `fun`-only-for-named
> rule — are unchanged.

---

## Motivation

The current closure syntax requires the `fun` keyword even when context makes the anonymous function obvious:

```metel
let double = fun(x: Int) -> Int { x * 2 };
items.map(fun(x: Int) -> Int { x * 2 })
```

In every other language with first-class functions (Swift, Kotlin, Rust, TypeScript, Scala), anonymous functions use a shorter form that drops the named-declaration keyword. The `fun` keyword belongs to named declarations; its presence in anonymous position is noise that adds visual weight without adding information.

The proposed form reads more naturally:

```metel
let double = (x: Int) -> Int { x * 2 };
items.map((x: Int) -> Int { x * 2 })
```

---

## Design

### Closure expression syntax

```
(Params?) -> ReturnType? Block
```

The `fun` keyword is removed. Parentheses, parameter list, optional return type annotation, and body block are otherwise unchanged.

```metel
// No params, no return type (inferred Unit)
let greet = () -> { print("hello"); };

// Params with annotations, explicit return type
let add = (x: Int, y: Int) -> Int { x + y };

// In a call position
items.map((x: Int) -> Int { x * 2 })

// Capturing from outer scope
var count = 0;
let inc = () -> { count += 1; };
```

### Closure type syntax

The type of a closure currently uses `fun(T) -> U`. With this RFC, closures are typed as `(T) -> U`:

```metel
// Before:
let f: fun(Int) -> Int = fun(x: Int) -> Int { x };

// After:
let f: (Int) -> Int = (x: Int) -> Int { x };
```

Function parameters and return types that accept closures also use the new form:

```metel
fun apply(f: (Int) -> Int, x: Int) -> Int { f(x) }
```

### Named function declarations are unchanged

The `fun` keyword is still required for all named declarations at any scope:

```metel
fun double(x: Int) -> Int { x * 2 }       // named — fun required
extend Stack<T> { fun push(self, item: T) }  // named — fun required
```

`fun` in named position is never ambiguous with the new closure syntax.

---

## Resolved Decisions

### D1 — Closure-start disambiguation uses `->` lookahead

The parser resolves `(x)` versus `(x) -> { ... }` by looking for `->` after the closing `)`. If `->` is present, the parser interprets the construct as a closure expression; otherwise it remains a grouped expression. No extra parameter annotation rule is introduced.

### D2 — Zero-argument closures use `() -> { ... }`

Bare `{ ... }` remains a block expression, not a closure shorthand. Zero-argument closures must be written as `() -> { ... }`.

### D3 — `->` is always required before the closure body

Return-type omission does not remove the arrow. The canonical inferred-return form is:

```metel
let double := (x: Int) -> { x * 2 };
```

`(params) { body }` is not introduced as closure syntax.

### D4 — Function type syntax changes with the expression syntax

This RFC adopts `(T) -> U` in type position as well as expression position. `fun(T) -> U` is not retained as the long-term type syntax.

### D5 — Existing `fun(...)` closures are dropped immediately

`fun(...)` closure expressions are removed as soon as this RFC is implemented. The closure expression syntax is `(params) -> { body }`, and old `fun(...)` forms become parse errors rather than compatibility aliases.

---

## Decision

**Outcome:** Accepted
**Target:** *(pending milestone assignment)*

The syntax and migration questions above are resolved in this RFC. Remaining work is spec alignment and later implementation planning.

## Coverage Checklist (added 2026-08-19, not part of the original RFC; expanded 2026-08-19: split former item 5 into items 5 and 6)

Retroactive breakdown of this RFC's distinct, fixture-testable normative claims,
as headed sections for citation purposes only. The document above is
unchanged and remains the historical record. Deliberately excludes claims that
aren't independently observable from a program's behavior -- implementation
strategy, design rationale, or internal architecture discussion belongs in the
RFC's own prose, not here.

### 1. Anonymous functions use parenthesized parameters followed by `->`

A closure expression is written `(params) -> { body }`, with parameter and
return types supplied or inferred as context permits. It may be passed directly
as an argument or capture names from its enclosing scope.

### 2. The arrow distinguishes a closure from a grouped expression

`(x) -> { ... }` is a closure, while `(x)` remains a grouped expression. A
parameter list followed directly by a block, without `->`, is not closure syntax.

### 3. Zero-argument closures use `() -> { ... }`

The empty parameter list is still followed by `->`; a bare block is not an
anonymous function.

### 4. Function types use `(T) -> U` syntax

Closure values can be annotated or accepted by parameters using function types
such as `(i64) -> i64`, including zero-argument function types.

### 5. Named functions still require `fun`

`fun name(...) { ... }` remains the declaration form for named functions.

### 6. The former anonymous `fun(...)` form is rejected

The former `fun(...) { ... }` anonymous-function spelling is rejected.
