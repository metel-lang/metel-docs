---
id: rfc-0010
title: "String Interpolation"
date: '2026-05-31'
---

## Summary

Add string interpolation to string literals using `${expr}` placeholders, with semantics defined entirely in terms of string concatenation and `.to_string()`. This RFC depends on `+` being defined for `String + String -> String`; interpolation is just syntax sugar over that operator.

---

# RFC-0010: String Interpolation

## Motivation

Metel currently has the pieces needed for ergonomic text rendering, but they are still too low-level for everyday use:

- `Display` already exists for values that can be rendered as text.
- `.to_string()` exists on built-in `Display` types.
- `string_concat` exists as a primitive string-building helper.

Today, users must write nested concatenation by hand:

```metel
let name = "Ada";
let count = 3;
let msg = string_concat("hello, ", string_concat(name, string_concat(" (", string_concat(count.to_string(), ")"))));
```

That is verbose, fragile, and hard to read once the number of interpolated values grows. The language needs a direct expression form for mixed literal/text/value output.

This RFC deliberately makes interpolation depend on `+` for strings instead of inventing a separate formatting engine. That keeps the feature consistent with the rest of the language and avoids a second concatenation mechanism.

## Proposal

### Syntax

Allow `${expr}` inside normal string literals:

```metel
let name = "Ada";
let count = 3;

let msg = "hello, ${name}; count=${count}";
```

Interpolation is only supported inside string literals. A plain string with no placeholders remains a normal `String` literal.

### Semantics

Interpolation lowers to a chain of string concatenations. Each embedded expression is converted with `.to_string()` before concatenation.

The example above desugars to:

```metel
let msg =
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
let s = "hello, " + "world";
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

