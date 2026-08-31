---
status: implemented
id: rfc-0010
title: "String Interpolation"
date: '2026-05-31'
coverage:
  "1": { spec: "spec.lexical.literals.dynamics-1" }
  "2": { spec: "spec.lexical.literals.dynamics-1" }
  "3": { spec: "spec.lexical.literals.dynamics-2" }
  "4": { spec: "spec.lexical.literals.dynamics-3" }
  "5": { spec: "spec.lexical.literals.dynamics-4" }
---

> **Status — qualified (2026-08-12, metel-core#704 and #705).** This RFC's own §Open
> Questions never settled how much of `expr` is reachable inside `${...}` — it says
> "an ordinary expression tree" and left it there. Because `${...}` re-parses its
> content as a bare `Rule::expr`, that silently pulled in `if`/`match`/`loop` and
> immediately-invoked closures, which means a loop, a mutation, or a println can run
> as a side effect of building a string (#704 confirms this concretely, not
> hypothetically). **Ruled intentional, not a defect:** restricting `${...}` to
> "calls only" would break existing idiomatic usage this corpus already depends on
> (`"${if (c) { "yes" } else { "no" }}"`, in `lexical.md`'s own worked example), for a
> purity guarantee the rest of the language doesn't otherwise make — Metel has no
> effect-tracking or purity system elsewhere for a narrower `${...}` grammar to be
> consistent with. This puts Metel's interpolation with Kotlin's/Swift's/C#'s
> full-expression model rather than Rust's macro-based one — and unlike Rust, Metel
> has a first-class string literal grammar rule to attach this to, so the macro
> workaround Rust needs doesn't apply here. `lexical.md` should state this
> explicitly (full-expression scope, deliberate, with a worked example showing a
> side effect firing) rather than leaving it only empirically discoverable, per
> #704's own acceptance criteria. This ruling does not touch #705, a straightforward
> parser bug (leading whitespace inside `${...}` breaks keyword-led expressions)
> that needs fixing regardless of scope.

> **Correction to the above, same day (2026-08-12).** "Metel has no effect-tracking or
> purity system elsewhere for a narrower `${...}` grammar to be consistent with" is not
> quite true — `reports/substructural-types/algebraic-effects.md` is an actively
> maintained design report (`status: active`, last synced 2026-07-23) for exactly such a
> system, not implemented or RFC'd yet, but real design work, not a hypothetical. Its own
> §11.1 example already interpolates inside an effect handler
> (`Console::print("Hello, ${name}!")`) without ever asking whether the interpolated
> content itself may perform an effect. Under this RFC's full-expression ruling above, it
> may: `"${Console::read_line()}"` lowers (per this RFC's own "before typechecking" rule)
> to an ordinary nested call, so effect-row inference sees it correctly and there is no
> *soundness* gap. The tension is with this RFC's own §Semantics claim that interpolation
> is "a compile-time convenience only; no runtime formatting engine is introduced" — once
> `${...}` can embed an effect performance, evaluating a string literal becomes a
> potential *suspension point* (the enclosing computation can hand control to an
> arbitrary handler, mid-string-construction, and the handler may never resume it or may
> resume it from another fiber). That is a real runtime consequence, not a compile-time
> convenience, and it was not on the table when "compile-time convenience only" was
> written because no effect system existed to make it possible. Not re-litigating the
> full-expression ruling here — effects are still a report, not an RFC, so nothing is
> settled enough to force a decision — but recorded in `algebraic-effects.md` itself
> (§15, Open Question 7) as one of the things that needs settling before effect syntax
> moves from proposed to an actual RFC, per that document's own Open Question 4 pattern.

> **#704's last open item closed, 2026-08-25.** `lexical.md` now states the
> full-expression ruling explicitly, with a worked example verified directly against
> the interpreter (`target/debug/metel`) showing a side effect firing mid-interpolation
> before the enclosing `println` call's own argument finishes evaluating. #704 closed.
> #705 (leading whitespace inside `${...}` breaking keyword-led expressions) is
> unaffected and remains open on its own.

## Summary

Add string interpolation to string literals using `${expr}` placeholders, with semantics defined entirely in terms of string concatenation and `.to_string()`. This RFC depends on `+` being defined for `String + String -> String`; interpolation is just syntax sugar over that operator.

---
:
# RFC-0010: String Interpolation

## Motivation

Metel currently has the pieces needed for ergonomic text rendering, but they are still too low-level for everyday use:

- `Display` already exists for values that can be rendered as text.
- `.to_string()` exists on built-in `Display` types.
- `string_concat` exists as a primitive string-building helper.

Today, users must write nested concatenation by hand:

```metel
let name := "Ada";
let count := 3;
let msg := string_concat("hello, ", string_concat(name, string_concat(" (", string_concat(count.to_string(), ")"))));
```

That is verbose, fragile, and hard to read once the number of interpolated values grows. The language needs a direct expression form for mixed literal/text/value output.

This RFC deliberately makes interpolation depend on `+` for strings instead of inventing a separate formatting engine. That keeps the feature consistent with the rest of the language and avoids a second concatenation mechanism.

## Proposal

### Syntax

Allow `${expr}` inside normal string literals:

```metel
let name := "Ada";
let count := 3;

let msg := "hello, ${name}; count=${count}";
```

Interpolation is only supported inside string literals. A plain string with no placeholders remains a normal `String` literal.

### Semantics

Interpolation lowers to a chain of string concatenations. Each embedded expression is converted with `.to_string()` before concatenation.

The example above desugars to:

```metel
let msg :=
    "hello, " +
    name.to_string() +
    "; count=" +
    count.to_string();
```

This implies:

- The result type of an interpolated string is always `String`.
- Each interpolated expression is evaluated exactly once, left to right.
- Every interpolated expression must be renderable as a string through `Display` / `.to_string()`.
- Interpolation is a compile-time convenience only; no runtime formatting engine is introduced.

### Dependency on string `+`

String interpolation is not a standalone feature. It is defined in terms of string concatenation, so the language must first support:

```metel
let s := "hello, " + "world";
```

Once `+` is available for `String + String -> String`, interpolation is just parser sugar that expands to nested `+` expressions and `.to_string()` calls.

### Escaping

The interpolation syntax must preserve a way to emit a literal `${` sequence in text. The simplest rule is:

- `\${` emits a literal `${`
- `\\` continues to mean a literal backslash

This keeps the literal grammar predictable and avoids introducing a special raw-string mode just for interpolation.

### Parser lowering

The parser or early lowering pass should translate an interpolated literal into an ordinary expression tree before typechecking.

That keeps the rest of the pipeline simple:

- typechecking only sees `+` and `.to_string()`
- construction only needs to typecheck ordinary expressions
- evaluation only needs to execute ordinary concatenation and method calls

## Alternatives Considered

**Keep `string_concat` as the only composition mechanism.**  
Rejected. It is correct but too verbose for the common case and scales poorly as soon as more than one value needs to be rendered.

**Introduce a separate formatting macro or printf-style function.**  
Rejected. That would add a second text-formatting model alongside `Display` and `.to_string()`, which is redundant and harder to teach.

**Make interpolation call `print`/`println`-style formatting internally.**  
Rejected. That couples string construction to output behavior and does not compose as cleanly with pure expressions.

**Allow interpolation without string `+`.**  
Rejected. That makes interpolation special-case runtime behavior instead of a syntax layer over an already-supported operator.

## Open Questions

1. Should interpolation accept any `Display` value directly, or should the lowering always insert explicit `.to_string()` calls? The current proposal prefers explicit lowering to `.to_string()` so the desugared form is stable and obvious.
2. Should empty interpolations like `"${}"` be a parse error or a type error? Parse error is preferable.
3. Should interpolation be allowed in future raw string literals? Not in this RFC; that should be evaluated separately if raw strings are added later.

## Timing Recommendation

Implement after string `+` is available. If `+` is deferred, this RFC should remain deferred as well.

## References

- Runtime builtins and `Display`: `docs/public/reference/spec/runtime.md`
- Existing string operations: `string_concat`, `.to_string()`
- Current literal grammar: `metel-interpreter/src/grammar.pest`
- Existing string handling in the interpreter: `metel-interpreter/src/parser/mod.rs`

## Coverage Checklist (added 2026-08-19, not part of the original RFC)

Retroactive breakdown of this RFC's distinct, fixture-testable normative claims,
as headed sections for citation purposes only. The document above is
unchanged and remains the historical record. Deliberately excludes claims that
aren't independently observable from a program's behavior -- implementation
strategy, design rationale, or internal architecture discussion belongs in the
RFC's own prose, not here.

### 1. String literals may contain expression interpolations

Normal string literals may contain `${expr}` placeholders, while literals without a
placeholder retain ordinary `String` literal behavior. The expression position accepts
the language's full expression grammar, including expressions with side effects.

### 2. Interpolation produces a String by rendering each embedded value

An interpolated literal has type `String`. Each embedded expression must be renderable
through `Display` / `.to_string()` before it is combined with the literal text.

### 3. Interpolated expressions evaluate once in source order

Each placeholder expression is evaluated exactly once, from left to right, as the
interpolated string is constructed.

### 4. Interpolation uses ordinary string concatenation semantics

Interpolation is equivalent to combining literal segments and rendered expressions with
`String + String -> String`; it does not introduce separate runtime formatting behavior.

### 5. Escaped interpolation openers remain literal text

Within an interpolated string literal, `\${` emits the literal characters `${`, and `\\`
emits a literal backslash.
