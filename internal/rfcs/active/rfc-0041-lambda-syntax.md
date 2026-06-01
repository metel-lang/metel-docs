---
status: active
id: rfc-0041
title: "Lambda Syntax for Anonymous Functions"
date: '2026-06-01'
---

## Summary

Replace the `fun(...) -> { }` syntax for anonymous functions (closures) with a lighter `(...) -> { }` form, dropping the `fun` keyword. The `fun` keyword remains required for named function declarations. The corresponding closure type annotation changes from `fun(T) -> U` to `(T) -> U`.

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
mut count = 0;
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
impl Stack<T> { fun push(self, item: T) }  // named — fun required
```

`fun` in named position is never ambiguous with the new closure syntax.

---

## Open Questions

### Q1 — Disambiguation: `(x)` as a grouped expression vs a zero-return-type closure start

The parser sees `(x)` and must decide: is this a grouped expression, or the start of `(x) -> { ... }`? The lookahead needed is `->` after the closing `)`.

**Option A — Two-token lookahead (recommended):** After parsing a `(...)` group, if the next token is `->`, reinterpret as a closure. This is the approach used by Kotlin and Swift. The cost is one extra token of lookahead; the grammar remains unambiguous with this rule.

**Option B — Require at least one param annotation to distinguish:** `(x: Int)` is unambiguously a closure param list; `(x)` is ambiguous. Require type annotations on all params when the closure appears in an expression-start position outside an explicit type context.

**Option C — Keep `fun` as an optional marker:** `fun(x) -> { }` remains valid alongside `(x) -> { }`. Deprecate over time.

**Proposal: Option A.** The `->` lookahead is simple, unambiguous, and consistent with how Kotlin and Swift handle the same situation. It requires no change to the way params are written.

### Q2 — No-argument closures: `() -> { }` vs `{ }` bare block

Some languages (Kotlin, Swift) allow a bare `{ }` as a zero-argument closure. Metel already uses `{ }` as a block expression, so a bare block cannot mean a closure without context. The `() -> { }` form is required.

**Proposal:** No bare block shorthand. `() -> { }` is the canonical zero-argument closure form.

### Q3 — Return type omission: `(x: Int) -> { x + 1 }` without a type

When the return type is omitted, the `->` still appears before the block. This is required to distinguish a closure from a grouped expression followed by a block statement.

```metel
// Return type omitted — inferred from body
let double = (x: Int) -> { x * 2 };
```

**Proposal:** `->` is always required between params and body, even when the return type is omitted. `(params) -> { body }` not `(params) { body }`. This keeps the closure grammar unambiguous and readable.

### Q4 — Type annotation syntax: `(T) -> U` vs keeping `fun(T) -> U`

If the type annotation syntax also changes from `fun(T) -> U` to `(T) -> U`, there is a migration cost for all existing code that uses `fun` in type positions.

**Option A — Change both expression and type syntax (recommended):** `(Int) -> Int` in both positions. Consistent and clean; the `fun` keyword disappears entirely from anonymous/closure contexts.

**Option B — Change expression syntax only, keep `fun(T) -> U` in type position:** Reduces migration cost, but creates an inconsistency where the value and its type are written differently.

**Proposal: Option A.** Consistency between expression and type form is more important than minimising migration effort. The migration is mechanical (rename `fun(` to `(` and `)` to `)` in type positions).

### Q5 — Migration: are existing `fun(...)` closures a hard error or a deprecation warning?

**Option A — Hard error immediately:** All `fun(...)` closure expressions are a parse error after this RFC lands.

**Option B — Deprecation warning, then error:** `fun(...)` in expression position emits a warning for one version, then becomes an error.

**Option C — Silent acceptance (recommended for initial implementation):** Accept both forms during the transition period. The old form is not warned or errored; the new form is documented as canonical. Remove old form in a future version.

**Proposal: Option C for initial implementation.** The old `fun` form can be silently accepted as sugar that desugars to the new form. This avoids breaking existing programs in tests and examples during the transition.

---

## Decision

**Outcome:** Draft — open for review

All questions above need resolution before implementation begins.
