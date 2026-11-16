---
id: rfc-0240
title: "Spelling of Written Function Types"
date: '2026-11-16'
status: draft
---

## Summary

A written function type is spelled `|P0, .., Pn| -> R` today (RFC-0154), with the qualifiers `once`, `var` and `copy` before
it. This RFC lays out the alternatives for changing that spelling and the costs of each. It does not pick one. The options:

| | A function of `i64` and `String` returning `boolean` | One tuple argument | No arguments |
|---|---|---|---|
| **Pipe (today)** | `\|i64, String\| -> boolean` | `\|(i64, String)\| -> boolean` | `\|\| -> boolean` |
| **A. `Fun(T) -> R`** | `Fun(i64, String) -> boolean` | `Fun((i64, String)) -> boolean` | `Fun() -> boolean` |
| **B. `Fun<T, R>`**, `T` a row | `Fun<(i64, String), boolean>` | `Fun<((i64, String),), boolean>` | `Fun<(), boolean>` |
| **C. `fun(T) -> R`** | `fun(i64, String) -> boolean` | `fun((i64, String)) -> boolean` | `fun() -> boolean` |
| **D. `(T) -> R`** | `(i64, String) -> boolean` | `((i64, String)) -> boolean` | `() -> boolean` |

In option B the first argument of `Fun` is the **parameter row**: a tuple type, which is a numeric-label row (RFC-0151), so
`(i64, String)` is `.{ .0: i64, .1: String }` and `()` is the empty row (RFC-0231). The qualifiers keep their prefix position in
every option: `once Fun(i64) -> i64`, `copy once Fun<(i64,), i64>`.

Whatever the choice, it changes spelling only: the type, its meaning, the qualifiers and every rule about them stay as RFC-0154,
RFC-0153, RFC-0219 and RFC-0232 state them. This is a design draft. Nothing here is accepted.

---

## Motivation

The pipe form was chosen on purpose and is implemented, so the case for changing it has to be made.

1. **RFC-0232 makes the written type a regular type.** `|A, B| -> R` is `dyn Callable<.{ .0: A, .1: B }, R>` together with
   marker aspects. Every other type is written as a name, with arguments in `<>` (`Option<T>`, `dyn Callable<Args, Ret>`); the
   function type is the one type with a bespoke delimiter. Option B spells the same type the way its meaning is written.
2. **The pipe is one of the harder places in the grammar.** `|` is also bitwise or, and `||` logical or, so a type or literal
   that starts with it needs position-based parsing (RFC-0154 "the `|` wrinkle"). A form that starts with a name (`Fun`, `fun`)
   has no wrinkle.
3. **Nested and qualified forms read poorly.** `var || -> i64` as a return type needed its own note in RFC-0154, and
   `|i64| -> |i64| -> i64` shows no boundary between the two arrows.
4. **A reader meets the type before the literal.** The pipe form's argument for itself (RFC-0154) is that the literal
   `|n| { .. }` and its annotation share a shape. That holds only where both are written; most function types appear in
   signatures, fields and aliases with no literal beside them.

---

## What RFC-0154 decided, and what each option does to it

RFC-0154 picked the pipe form for three reasons and rejected two spellings. The options must answer them.

1. **One shape for the literal and its annotation** (`let f: |i64| -> String = |n| n.to_string();`).
   Pipe: kept. A, B, C, D: the annotation and the literal diverge, as they did before RFC-0154.
2. **No ambiguity between two arguments and one tuple argument** (`(A, B) -> C`).
   Pipe, A, B, C: none, since the parameter list is delimited and a tuple argument needs its own parentheses. D: reintroduces it,
   which is why RFC-0154 left that spelling. B is explicit by construction: the first argument is the row.
3. **Freeing `(...)` for grouping and tuples.** A, C keep a call-like `(` after a name, not a bare one. D does not.
4. **`fun(T) -> U` was rejected** (option C here): it reverts RFC-0041's lightness and does not touch the literal.
5. **`Fn(T) -> U` was rejected** as the spelling of the `Callable` aspect, "an erased, dispatched form". Option A is the same
   shape under a different name; RFC-0232 now says the written type is that erased form, which weakens that rejection.

---

## The options

### Pipe (status quo)

No change. Keeps RFC-0154's reasons and leaves the motivation above open.

### A. `Fun(T) -> R`

A capitalised type name followed by a parenthesised parameter list and an arrow.

- Reads like a function signature, and like the type of a call.
- `Fun` is a type name by convention (capitalised), written with call-like parentheses, which no other type does.
- Parameters are positional, so keyword parameters (RFC-0223) have no spelling in the type, as today.
- Nesting: `Fun(Fun(i64) -> i64) -> i64` and `Fun(i64) -> Fun(i64) -> i64`; the arrows still run together.

### B. `Fun<T, R>`, `T` a row

`Fun` is a std type with two type arguments: the parameter row and the result.

- Spelled like every other generic type; no new production, `Fun<..>` parses today.
- Matches RFC-0232 (`dyn Callable<Args, Ret>`): `Fun<Args, Ret>` can be the alias, with the markers as the prefix qualifiers.
- Parameters are a row, so an argument list is a tuple type, and a parameter row with keyword parameters is a record type
  (`Fun<.{ .x: i64 }, R>`), which the other options cannot write.
- The unary case needs the one-element tuple, `Fun<(i64,), String>`, since a bare `i64` is not a row. If a bare type were accepted
  as a one-parameter shorthand, `Fun<(A, B), C>` would be ambiguous between two parameters and one tuple parameter again.
- Longer than the pipe at every site: the most common function types (`|i64| -> i64`) gain the most characters.

### C. `fun(T) -> R`

The spelling RFC-0134 proposed and RFC-0154 rejected. Listed for completeness: lowercase, so it reads as the `fun` keyword of
declarations, which makes a type look like an item.

### D. `(T) -> R`

The spelling RFC-0041 had and RFC-0154 removed. It reintroduces the two-arguments-or-one-tuple ambiguity and the type-versus-grouping
collision. Listed for completeness.

---

## What does not change

- The qualifiers `once`, `var` and `copy` (RFC-0153, RFC-0219), their prefix position and their meaning.
- The closure literal `|x| ..`. Unless this RFC says otherwise (open question 2), the literal keeps the pipe.
- Function declarations (`fun f(x: i64) -> i64`), whose syntax is a different production.
- RFC-0232's reading of the written type, and its markers.

---

## Costs

- **Migration.** The pipe form appears in std, about 40 fixture and source files, and the spec. A spelling change is mechanical
  but must not be a blind regex (RFC process: three earlier sweeps corrupted files). It is checked by compiling the examples.
- **Both spellings during a transition** is not proposed: the language has no users, so the old spelling is a parse error naming
  the new one.
- **Grammar.** A: a new production starting with a type name and `(`. B: none, if `Fun` is an ordinary std type; a rule for
  the qualifiers before it. C: a production starting with `fun`. D: backtracking past `)`.

---

## Open questions

1. **Which option, if any.** The draft lays them out without choosing. B is the least new machinery if RFC-0232 is accepted; A reads
   closest to other languages; the pipe form keeps the literal and the annotation alike.
2. **Does the closure literal change too?** Keeping the annotation and the literal in one shape was RFC-0154's main reason. If the
   type moves off the pipe, the literal can stay (`|n| { .. }`), or follow it.
3. **Is `Fun` a reserved name or an ordinary std type?** A reserved name cannot be shadowed or imported under another name; an
   ordinary type can be, which matters for option B's resolution.
4. **The unary row in option B.** `Fun<(i64,), R>`, a bare type as a shorthand, or a separate spelling for the common case.
5. **Ordering with RFC-0232.** Option B is a restatement of RFC-0232; should the two be decided together?

---

## Decision

**Outcome:** *(pending)*
