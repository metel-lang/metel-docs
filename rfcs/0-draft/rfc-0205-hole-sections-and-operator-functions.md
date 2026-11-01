---
id: rfc-0205
title: "Hole Sections and Operator Functions"
date: '2026-11-01'
status: draft
---

## Summary

Two small conveniences for writing short function values without a full closure:

1. **Hole sections:** `(_ * 10)`, `(10 - _)`, `(_ + _)`, `(_.len())` are shorthand for closures
   whose parameters are the `_` holes, in order.
2. **Operator functions:** std exposes each operator as an ordinary function (`ops::add`,
   `ops::mul`, `ops::lt`, ...), so an operator can be passed where a function is expected.

Both lower to ordinary closures and calls before type checking; no new type-system concept
is introduced. This RFC is independent of RFC-0204 (pipelines and composition); the two read
well together but neither requires the other.

---

## Motivation

Short closures carry a lot of noise today:

```metel
let total := List::from([1, 2, 3, 4])
    .filter(|x: i64| -> boolean { x % 2 == 1 })
    .map(|x: i64| -> i64 { x * 10 })
    .fold(0i64, |a: i64, x: i64| -> i64 { a + x });
```

Haskell's operator sections remove this noise, but a literal port does not fit Metel's
grammar: `(- 1)` is ambiguous with unary minus, `(*x)` with dereference, and `(&x)` with
borrowing. A hole marker avoids all three.

---

## Design

### 1. Hole sections

```
section := '(' expr-containing-holes ')'
```

An expression in parentheses that contains one or more bare `_` in *expression position*
becomes a closure with one parameter per `_`, left to right. The holes are the closure
parameters:

| Written | Means |
|---|---|
| `(_ * 10)` | `\|x\| x * 10` |
| `(10 - _)` | `\|x\| 10 - x` |
| `(_ + _)` | `\|a, b\| a + b` |
| `(_.len())` | `\|s\| s.len()` |
| `(_ % 2 == 1)` | `\|x\| x % 2 == 1` |

Rules:

1. The section extends to the **nearest enclosing parentheses** only; `f((_ + 1))` is one
   section, `f(_ + 1)` is a call with a bare `_`, which is an error.
2. Parameter and return types are **inferred from context**; a section never takes annotations.
   Where context does not fix them (`let f := (_ + 1);`), it is a type error that asks for an
   annotated closure.
3. **Capture follows closure defaults** (move by default, RFC-0157). A section may mention outer
   names, and the standard capture list rules apply to the generated closure.
4. Sections do not nest holes: a `_` belongs to the innermost enclosing section.
5. `_` as a *pattern* wildcard is unaffected; the two are told apart by position.

### 2. Operator functions

Rather than inventing `(+)` as a bare-operator syntax, std exposes operators as ordinary
functions through the operator aspects (RFC-0011): `ops::add`, `ops::mul`, `ops::lt`, and so
on. They are usable anywhere a function value is:

```metel
let total := xs.fold(0, ops::add);
let sorted := xs.sort_by(ops::lt);
```

For two-hole cases a section is equivalent: `(_ + _)` and `ops::add` mean the same thing for
`i64`. `ops::*` additionally works for user types that implement the operator aspects.

### 3. Example

With both features, the motivating chain becomes:

```metel
let total := List::from([1, 2, 3, 4])
    .filter((_ % 2 == 1))
    .map((_ * 10))
    .fold(0, ops::add);
```

---

## Interactions

- **RFC-0154 (function type spelling):** sections produce values of `|A| -> B`.
- **RFC-0134 / RFC-0153 / RFC-0157 (closure qualifiers, default capture):** governs capture of
  sections.
- **RFC-0011 (operator overloading, draft):** `ops::*` are the operator aspects' methods, so
  section 2 depends on that RFC (or on a hardcoded set of primitive operators until it lands).
  Section 1 does not.
- **RFC-0197 (generic closures):** a section is monomorphic; generic use needs that RFC.
- **RFC-0204 (pipelines and composition):** sections are the natural arguments to `|>` stages and to `.then()`.
- **RFC-0203 (comprehensions):** overlaps on `map`/`filter` for simple expressions.
- **RFC-0201 (pattern synonyms):** `_` already appears as a wildcard in patterns; position
  distinguishes the two uses.

---

## Alternatives considered

1. **Haskell-style operator sections `(+ 1)`.** Rejected: ambiguity with unary operators,
   dereference and borrowing.
2. **Scala/Kotlin implicit `it` or numbered parameters (`$0`).** Less flexible (no multiple
   holes in order), and no syntactic marker at the closure boundary.
3. **Bare operators as values, `(+)`.** Possible alongside `ops::add`; rejected here to keep one
   mechanism.
4. **Do nothing**, leaving closures fully annotated. Valid; this RFC is ergonomics only.

---

## Open Questions

1. Should sections infer the parameter type from a *single* method call (`(_.len())`) when the
   context is ambiguous? That needs bidirectional inference not present in the two-pass checker.
2. Do hole sections need a hole-count limit (for example three) for readability?
3. Is it a problem that `f(_ + 1)` is an error while `f((_ + 1))` is a section? The extra
   parentheses are the cost of an unambiguous boundary; the alternative is to let a call's
   argument list delimit a section.
4. Should `ops::*` be a module or a set of associated functions on the operator aspects?
5. Does a section's inferred closure count as `Copy`/`Clone` under RFC-0162's outcome when it
   captures nothing?

---

## Decision

**Outcome:** *(pending)*
