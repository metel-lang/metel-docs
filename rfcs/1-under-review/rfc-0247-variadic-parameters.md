---
id: rfc-0247
title: "Variadic parameters"
date: '2026-11-23'
status: under-review
updated: '2026-11-23'
tracking: 'https://github.com/metel-lang/metel-core/issues/2173'
---

> **Status — under review (2026-11-23).** Taken to review as part of the metel-core v0.17.0 plan (#2173)

## Summary

A parameter list may end in a **rest parameter**, `..rest: .{ ..R }`, that receives the extra positional arguments of a call as one
row. Metel has no variadic function today (RFC-0125 says so in its Motivation), and a call's argument list is already a row
(RFC-0151, RFC-0223), so a rest parameter is that row's tail given a name:

```metel
fun log<..R>(level: String, ..rest: .{ ..R }) where ..R: Display { /* rest is a tuple */ }

log("info");                      // R = .{}            rest = ()
log("info", 1, "two", 3.5);       // R = .{ .0: i64, .1: String, .2: f64 }   rest = (1, "two", 3.5)
log("warn", sep = "; ", 7);       // keyword arguments bind named parameters, never the rest
```

Inside the body `rest` is an ordinary tuple, with labels numbered from `.0` for that value. The call packs the extra positional arguments
into it, once, left to right. The function's arity is a property of the call, not of the declaration, and each call instantiates `R`.

This is a design draft. It does not decide how to write operations that recurse over a row's positions (RFC-0125), and it adds no
variadic function *type*: a variadic function used as a value is instantiated at the callable type it is used at.

---

## Motivation

1. **There is no way to write a function that takes "the rest of the arguments".** `print<T: Display>(x: T)` takes one. RFC-0125 judged
   the need real but undriven by a program. There is now a program. RFC-0246 needs a `derive` function whose `Args` is a few leading
   values and then a flow of any width, and today that can only be said as a row tail that renumbers its labels, which RFC-0125 records as
   unbuilt. A rest parameter says the same thing with no renumbering visible in the signature.
2. **`Callable<Args, Ret>` cannot be composed.** RFC-0232 makes a function type a callable over an `Args` row. A function that applies another
   to "its remaining arguments" (`apply`, `curry`, `compose`) takes a row of unknown width. It can be written today with an explicit
   tuple parameter, and a rest parameter is that parameter written at the call site as plain arguments.
3. **Formatting and aggregation read worse with a tuple.** `max(a, b, c)` and `log("info", x, y)` are the shapes other languages give
   variadic functions. Wrapping the extras in a tuple at every call, `log("info", (x, y))`, is possible today and is the thing this
   removes.

Note what a rest parameter does *not* give. Everything here is already expressible with an explicit row-typed parameter,
`fun log<..R>(level: String, rest: .{ ..R })`, called as `log("info", (x, y))`. The feature is the call-site spelling and the
instantiation of `R` per call. That is a smaller claim than "variadics", and the Alternatives table weighs it against doing nothing.

---

## Proposal

### 1. Declaration

```
param_list   = { positional_param* ~ rest_param? ~ keyword_only_param* }
rest_param   = { ".." ~ ident ~ ":" ~ row_type }       // row_type is `.{ ..R }` or a closed row
```

- At most one rest parameter, after every positional parameter. Parameters after it are **keyword-only**: they bind by name
  (RFC-0223), because a positional argument after a variable number of extras has no place to land.
- The rest parameter's type is an open row `.{ ..R }` with `R` bound by a row binder `<..R>` (RFC-0208), or a closed row `.{ .0: i64, .1: i64 }`.
  A closed row makes it a fixed-arity group and not variadic, which is legal and means the same as the parameters written out.
- A bound on the row is the existing field-wise bound: `where ..R: Display` means every extra argument is `Display`.

### 2. Calls

A call's arguments split by RFC-0223's rules: positional arguments first, then keyword arguments. The positional arguments bind, in order, to
the positional parameters; **the remainder, in order, are packed into the rest parameter** as `.{ .0 = x0, .1 = x1, .. }`. Then:

- `R` is the row of the extras' types, inferred at the call. No extras gives `.{}`, which is `()` (RFC-0231).
- A keyword argument binds a named parameter. A keyword that binds none is an error (`T0039`), because the rest takes positionals only and there
  is no keyword rest.
- Arguments evaluate left to right as written (RFC-0223).
- Too few positional arguments for the fixed positionals is the usual arity error, not a short rest.

### 3. The body

`rest` is a local of tuple type. It supports `rest.0`, a tuple pattern, and every operation a tuple does, including `Copy`, `Clone` and `Display` by the
existing row impls (RFC-0151, RFC-0125's stand-ins), partial moves (RFC-0071), and being passed to a function generic over a row. A by-value
rest parameter **owns** the packed extras (RFC-0179), so they are the callee's to move, return or drop.

The body cannot yet loop over `rest`'s elements one by one. Per-element code needs RFC-0174's `comptime for` over a row (under review),
or a call to a function that is itself generic over the row. This RFC does not add either.

### 4. Function values

A variadic function has no variadic type. Used as a value, it is instantiated at the callable type the context asks for:

```metel
let f: |String, i64, String| = log;       // R = .{ .0: i64, .1: String }
```

The coercion fixes `R` from the expected `Args` row. With no expected type there is nothing to instantiate and the use is an error
("`log` is variadic: its arity is fixed by the call or by the expected function type"). The function's own `Callable` impl is generic over
`R` and relates its `Args` to the fixed parameters by renumbering the rest's labels after them, which is RFC-0125's open problem. Using a variadic function
as a value at a **concrete** instantiation does not need it, because the instantiated `Args` row is concrete.

### 5. Overloads

A candidate with a rest parameter is less specific than one that fixes the arity. A call that matches a fixed-arity overload and a variadic one
selects the fixed one. Two variadic candidates that both match are an ambiguous call, reported as an ambiguous overload is today. Overload resolution stays static.

---

## Alternatives considered

| Alternative | Why not |
|---|---|
| Do nothing: pass an explicit tuple, `log("info", (x, y))` | It works today. It is the baseline, and the Motivation says what a rest parameter removes. Reasonable to choose if nothing else needs the feature. |
| Homogeneous rest, `..xs: i64` collecting into a sequence of `i64` | Needs a collection with an unknown length, which a row of fixed arity does not. A bound on the row (`where ..R: Is<i64>`-style) covers the common case without one. Left to a later RFC. |
| `*args` or `...args` spelling | `..` already means "the rest" in row tails, spreads and patterns, and the RFC-0208 binder is `..R`. |
| A keyword rest (`**kwargs`) | A named label that binds no parameter is an error today (`T0039`) and keeping it so catches misspelled keywords. |
| Variadic function types, `|A, ..R| -> Ret` | A function's arity is a call fact, and `Callable<Args, Ret>` already has a row for it. A variadic type adds a third thing that is neither a row nor an aspect. |
| Fold the feature into RFC-0125 | RFC-0125 is about operations that recurse by position (`cons`, `uncons`, `curry`) and proposes building nothing yet. A rest parameter does not need any of them, so it should not wait. |

---

## Interaction with other work

- **RFC-0151** (implemented): tuples are numeric-label rows and a call's arguments are such a row. The packed rest is a tuple, so it needs no
  new value form.
- **RFC-0223** (implemented): the binding rules. This RFC adds one parameter kind to them and nothing to keyword arguments.
- **RFC-0208** (under review): the row binder `<..R>`. The signature uses it.
- **RFC-0179** (implemented): a by-value open-row parameter owns the whole argument, which is the ownership of the rest parameter.
- **RFC-0232, RFC-0161** (under review): function types and `Callable`. Section 4 interacts with both and decides only the concrete case.
- **RFC-0125** (under review): positional recursion over rows. This RFC is independent of its renumbering designs except for the generic
  `Callable` impl of a variadic function, which waits for them. RFC-0125's statement that Metel has no variadic function stops being true
  once this is accepted.
- **RFC-0246** (under review): a `derive` function takes a flow after leading positionals. A rest parameter is one way to say it
  (question 7 below).
- **RFC-0174** (under review): iterating the elements of `rest` needs `comptime for` over a row.

---

## Costs

- **Parser and checker.** One parameter kind, the packing of extras at a call, and keyword-only parameters after the rest. Overload resolution
  gains a specificity rule.
- **Per-call instantiation of a row.** `R` is inferred per call. The checker already instantiates row parameters, and the evaluator is
  indifferent to arity, but each variadic function adds instantiations the tree-walker never specialises.
- **A feature expressible without itself.** Because an explicit tuple parameter already works, the justification is readability and
  RFC-0246's need, not new power. If the second does not hold, the first alone is a thin case.
- **Diagnostics.** A wrong call to a variadic function has to say whether the failure is in the fixed positionals, the rest bound or a keyword.

---

## Open questions

1. **Surface spelling of the type.** `..rest: .{ ..R }` is exact and long. `..rest: ..R` is shorter and matches RFC-0208's rule that a row
   parameter is written `..R` at every use, but reads as if `rest` had the row's type directly. Recommendation: the long form until
   RFC-0208 is settled.
2. **Homogeneous rest.** Is `..xs: T` ("any number of `T`") wanted, and is it a row bound or a collection? Recommendation: neither now.
3. **Call-site spread.** The dual of a rest parameter is `f(a, ..t)`, passing a tuple's elements as separate arguments, which `apply`
   needs. Recommendation: a separate RFC, since the rest parameter is useful without it.
4. **A variadic function type.** Section 4 says there is none. Does a program need to write a type that quantifies over arity, or is the
   generic `Callable` impl enough?
5. **Overloads.** Is "fixed-arity beats variadic" the right rule, and do two matching variadics need a tie-break instead of an error?
6. **Defaults before the rest.** Metel has no default parameter values (RFC-0223 rule 3); whether it should is metel-core#2181. If it
   gains them, a defaulted positional before a rest makes the split of extras ambiguous. Recommendation: forbid a default before a rest
   parameter.
7. **RFC-0246's flow.** Should a derivation's `Args` be written as a parameter list with a rest parameter, `derive(Target, name: String,
   ..flow: Flow)`, in place of RFC-0246's `..Flow` row tail with renumbering? It avoids renumbering and is the stronger reason to accept this.
8. **Placement.** This is drafted for v0.17.0, after the Function types stage (RFC-0232). RFC-0125 is committed to a later release and says
   build nothing; that statement has to be reconciled when this is accepted.

---

## Decision

**Outcome:** *(pending)*
