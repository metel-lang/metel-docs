---
id: rfc-0240
title: "Spelling of Written Function Types"
date: '2026-11-16'
status: under-review
updated: '2026-11-22'
tracking: 'https://github.com/metel-lang/metel-core/issues/2134'
---

> **Status — under review (2026-11-22).** Taken to review as part of the metel-core v0.17.0 plan (#2134)

## Summary

A written function type is spelled `|P0, .., Pn| -> R` today (RFC-0154), with the qualifiers `once`, `var` and `copy` before it. That
spelling answers two separate questions, and this RFC separates them:

1. **The generic spelling.** What is the written type of a function when it is spelled like any other type: a name with
   arguments, where the parameters are a row? RFC-0232 gives it as `dyn Callable<Args, Ret> + markers`; `Fun<Args, Ret>` would be an
   alias for it. Only this form can abstract over the parameter row (`fun apply<Args, R>(f: Fun<Args, R>, a: Args) -> R`).
2. **The sugar.** What, if anything, is written for the common case where the parameters are listed: the pipe form
   `|i64, String| -> boolean` (RFC-0154), `fun(i64, String) -> boolean`, `Fun(i64, String) -> boolean`, or none.

The two compose, as they do in Rust, where `Fn(A, B) -> R` is sugar for `Fn<(A, B), Output = R>`:

| Sugar over the generic form | A function of `i64` and `String` returning `boolean` | One tuple argument | No arguments |
|---|---|---|---|
| **Pipe (today)** | `\|i64, String\| -> boolean` | `\|(i64, String)\| -> boolean` | `\|\| -> boolean` |
| **`fun(T) -> R`** | `fun(i64, String) -> boolean` | `fun((i64, String)) -> boolean` | `fun() -> boolean` |
| **`Fun(T) -> R`** | `Fun(i64, String) -> boolean` | `Fun((i64, String)) -> boolean` | `Fun() -> boolean` |
| **None** | `Fun<(i64, String), boolean>` | `Fun<((i64, String),), boolean>` | `Fun<(), boolean>` |

In the generic form the first argument is the **parameter row**: a tuple type is a numeric-label row (RFC-0151), so `(i64, String)`
is `.{ .0: i64, .1: String }`, and `()` is the empty row (RFC-0231). The qualifiers keep their prefix position in every spelling:
`once fun(i64) -> i64`, `copy once Fun<(i64,), i64>`.

Whatever the choice, it changes spelling only: the type, its meaning, the qualifiers and every rule about them stay as RFC-0154,
RFC-0153, RFC-0219 and RFC-0232 state them. This is a design draft. Nothing here is accepted.

---

## Motivation

The pipe form was chosen on purpose and is implemented, so the case for changing it has to be made.

1. **RFC-0232 makes the written type a regular type.** Every other type is written as a name, with arguments in `<>`
   (`Option<T>`, `dyn Callable<Args, Ret>`); the function type is the one type with a bespoke delimiter. A generic spelling is the
   one that reads like the others, and the only one that can quantify over the parameter row.
2. **The pipe is one of the harder places in the grammar.** `|` is also bitwise or, and `||` logical or, so a type or literal that
   starts with it needs position-based parsing (RFC-0154 "the `|` wrinkle"). A form that starts with a name has no wrinkle.
3. **Nested and qualified forms read poorly.** `var || -> i64` as a return type needed its own note in RFC-0154, and
   `|i64| -> |i64| -> i64` shows no boundary between the two arrows.
4. **A reader meets the type before the literal.** The pipe form's argument for itself (RFC-0154) is that the literal `|n| { .. }`
   and its annotation share a shape. That holds only where both are written; most function types appear in signatures, fields and
   aliases with no literal beside them.

---

## Prior art

Recalled, not re-checked against each language's current documentation.

| Family | Languages | Spelling |
|---|---|---|
| Keyword, parentheses, arrow | Rust (`fn` pointers), Gleam, Carbon | `fn(A, B) -> R` |
| Keyword, parentheses, no arrow | Go, Zig | `func(A, B) R`, `fn (A, B) R` |
| Bare parentheses, arrow | Swift, Kotlin | `(A, B) -> R` |
| Bare parentheses, fat arrow | TypeScript, Scala | `(a: A, b: B) => R` |
| Curried arrow | Haskell, OCaml, Elm, Roc | `A -> B -> R` |
| Generic type per arity | C#, Java, Scala and Kotlin internals | `Func<A, B, R>`, `Function2[A, B, R]` |
| Generic type with a list of parameters | Python | `Callable[[A, B], R]` |
| Named constructor | Crystal | `Proc(A, B, R)` |
| Trait sugar over a tuple row | Rust | `Fn(A, B) -> R` is `Fn<(A, B), Output = R>` |

What they show:

1. **Pipe-delimited function types are unusual.** Pipes are common for closure literals (Rust, Ruby, Smalltalk blocks), and Rust
   splits the two: literals use `|x|`, types use `fn(..)` or `Fn(..)`. I know of no mainstream language that writes a function type
   with pipes.
2. **A tuple row as the argument list has precedent.** Rust's `Fn` takes its arguments as a tuple, with the one-element tuple
   `Fn<(A,)>` for one argument, and hides it behind parenthesised sugar. That is this RFC's generic form with a sugar over it.
3. **The two-arguments-or-one-tuple ambiguity is documented.** Swift spent SE-0110 distinguishing `((A, B)) -> R` from `(A, B) -> R`; Scala 3
   and Kotlin write a tuple argument with doubled parentheses or `Pair`. It supports RFC-0154's motive and counts against a bare `(T) -> R`.
4. **Arity-indexed generics exist where there is no row.** `Func`, `BiFunction` and `Function2` stand in for a parameter row;
   Python's `ParamSpec` and Rust's `Fn<Args>` abstract over it as the generic form here does.
5. **Qualifiers have two homes.** A prefix modifier (Kotlin's `suspend (A) -> R`), as here; or separate type families (Rust's `Fn`,
   `FnMut`, `FnOnce`; C#'s `Func`, `Action`).
6. **Labels in function types exist** (Swift, Kotlin, TypeScript). A parameter row with keyword labels spells them in the generic form.

---

## What RFC-0154 decided, and how each sugar answers it

RFC-0154 picked the pipe form for three reasons and rejected two spellings. Each sugar must answer them.

| Reason or rejection | Pipe | `fun(T) -> R` | `Fun(T) -> R` |
|---|---|---|---|
| One shape for the literal and its annotation | kept | diverges | diverges |
| No ambiguity between two arguments and one tuple argument | kept | kept (the parameter list is delimited) | kept |
| Free `(...)` for grouping and tuples | kept | kept (a `(` follows a name) | kept |
| `fun(T) -> U` was rejected as heavier and as reverting RFC-0041 | n/a | the rejection stands unless the generic form changes the calculus | n/a |
| `Fn(T) -> U` was rejected as the spelling of the `Callable` aspect | n/a | n/a | the rejection weakens: RFC-0232 says the written type is that erased form |

---

## Question 1: the generic spelling

The written type is `dyn Callable<Args, Ret> + markers` (RFC-0232). Two ways to write it:

- **Only `dyn Callable<Args, Ret> + CallMany + ..`.** No new name; the qualifiers are the markers.
- **`Fun<Args, Ret>`**, an alias, with the qualifiers as the prefix keywords (`once`, `var`, `copy`). Shorter than the `dyn` form and
  reads like `Option<T>`.

Either way `Args` is a row, so a tuple type lists the parameters and a record type lists keyword parameters (`Fun<.{ .x: i64 }, R>`),
which the sugars below cannot write. The unary case needs the one-element tuple, `Fun<(i64,), String>`: a bare `i64` is not a row, and
accepting it as a shorthand would make `Fun<(A, B), C>` ambiguous between two parameters and one tuple parameter again.

## Question 2: the sugar

- **Pipe (today).** Keeps the literal and annotation alike. Costs the pipe's parsing wrinkle and its nesting.
- **`fun(T) -> R`.** Reads as a declaration with the name and parameter names dropped (`fun area(r: Rect) -> f64` has the type
  `fun(Rect) -> f64`), as in Rust, Gleam, Carbon, Go and Zig. Lowercase, so it is syntax and `Fun<..>` is the type: no name with two
  bracket styles. Costs RFC-0154's two objections (heavier, literal diverges), and stacks qualifiers into a run of keywords
  (`copy var fun(&T) -> boolean`, where `var fun` can read as a binding).
- **`Fun(T) -> R`.** A capitalised name with call-like parentheses, which no other type has; the same name as `Fun<..>` with a
  different bracket. Nearest precedent: Rust's `Fn(..) -> R` and Crystal's `Proc(..)`.
- **None.** Only the generic form. One spelling, longest at every site; the common `|i64| -> i64` becomes `Fun<(i64,), i64>`.

**Two spellings of one type** is the cost of any sugar beside the generic form. It is the objection earlier RFCs raised against
duplicate spellings (RFC-0230). It is answered here by what the generic form alone can do (abstract over the parameter row) and the sugar
alone is for (the common case), and by the sugar being syntax only: it desugars at parse time to the one type.

---

## What does not change

- The qualifiers `once`, `var` and `copy` (RFC-0153, RFC-0219), their prefix position and their meaning.
- The closure literal `|x| ..`, unless open question 3 says otherwise.
- Function declarations (`fun f(x: i64) -> i64`), whose syntax is a different production.
- RFC-0232's reading of the written type, and its markers.

---

## Costs

- **Migration.** The pipe form appears in std, about 40 fixture and source files, and the spec. A spelling change is mechanical but
  must not be a blind regex (RFC process: three earlier sweeps corrupted files); it is checked by compiling the examples.
- **No transition period.** The language has no users, so the old spelling is a parse error naming the new one.
- **Grammar.** `fun(..)`: a type production starting with `fun`. `Fun(..)`: a production starting with a type name and `(`. The
  generic form: none, if `Fun` is an ordinary std type; a rule for the qualifiers before it.

---

## Open questions

1. **Is there a generic spelling beside `dyn Callable<..> + markers`?** An alias `Fun<Args, Ret>`, or only the `dyn` form.
2. **Which sugar, if any.** The draft lays them out without choosing.
3. **Does the closure literal change with the type?** Keeping the annotation and the literal in one shape was RFC-0154's main reason.
   If the type moves off the pipe, the literal can stay (`|n| { .. }`) or follow it.
4. **Is two spellings acceptable?** Section "Question 2" argues it is; the alternative is the generic form alone.
5. **Is `Fun` a reserved name or an ordinary std type?** A reserved name cannot be shadowed or imported under another name.
6. **The unary row in the generic form.** `Fun<(i64,), R>`, or a separate spelling for the common case.
7. **Ordering with RFC-0232.** The generic form is a restatement of RFC-0232; should the two be decided together?

---

## Decision

**Outcome:** *(pending)*
