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

A parameter list may end in a **rest parameter**, `..rest: .{ R }`, that receives the extra positional arguments of a call as one
row. Metel has no variadic function today (RFC-0125 says so in its Motivation), and a call's argument list is already a row
(RFC-0151, RFC-0223), so a rest parameter is that row's tail given a name:

```metel
fun log<..R>(level: String, ..rest: .{ R }) where R: Display { /* rest is a tuple */ }

log("info");                      // R = .{}            rest = ()
log("info", 1, "two", 3.5);       // R = .{ .0: i64, .1: String, .2: f64 }   rest = (1, "two", 3.5)
fun log_with_sep<..R>(level: String, ..rest: .{ R }, sep: String) where R: Display { /* ... */ }

log_with_sep("warn", 7, sep = "; "); // only 7 goes into the rest
```

Inside the body `rest` is an ordinary tuple, with labels numbered from `.0` for that value. The call packs the extra positional arguments
into it, once, left to right. The function's arity is a property of the call, not of the declaration, and each call instantiates `R`.

This is a design draft. It does not decide how to write operations that recurse over a row's positions (RFC-0125), and it adds no
variadic function *type*: a variadic function used as a value is instantiated at the callable type it is used at.

---

## Motivation

1. **Direct calls can pass a variable number of extra positionals.** A logging or aggregation
   function can receive a tuple while callers write `log("info", x, y)` or `max(a, b, c)`.
2. **The ordinary binder can separate fixed positionals from a tuple.** RFC-0246's deriver
   signature is a potential consumer of that rule. Its target-dependent flow type and computed
   default need separate design, so this RFC can stand on ordinary calls.

Note what a rest parameter does *not* give. Everything here is already expressible with an explicit row-typed parameter,
`fun log<..R>(level: String, rest: .{ R })`, called as `log("info", (x, y))`. The feature is the call-site spelling and the
instantiation of `R` per call. That is a smaller claim than "variadics", and the Alternatives table weighs it against doing nothing.

---

## Proposal

### 1. Declaration

```
param_list   = { positional_param* ~ rest_param? ~ keyword_only_param* }
rest_param   = { ".." ~ ident ~ ":" ~ row_type }       // row_type is `.{ R }` or a closed row
```

- At most one rest parameter, after every positional parameter. Parameters after it are **keyword-only**: they bind by name
  (RFC-0223), because a positional argument after a variable number of extras has no place to land.
- The rest parameter's type is an open row `.{ R }` with `R` bound by a row binder `<..R>` (RFC-0208), or a
  closed tuple type with consecutive numeric labels starting at `.0`, such as `.{ .0: i64, .1: i64 }`.
  The closed tuple groups a fixed number of positional arguments into one local.
- A generic rest parameter is written `..rest: .{ R }`. The name `R` denotes a row. The record type
  `.{ R }` gives the rest parameter its tuple type, using the same type syntax as an ordinary tuple parameter.
- A field-wise bound `where R: Display` means every extra argument is `Display` under RFC-0208's proposed syntax.

### 2. Calls

A call's arguments split by RFC-0223's rules: positional arguments first, then keyword arguments. The positional arguments bind, in order, to
the positional parameters that precede the rest; **the remainder, in order, are packed into the rest parameter** as `.{ .0 = x0, .1 = x1, .. }`. Then:

- When explicit extras are supplied, `R` is inferred from their types. An open rest with no extras normally
  receives `.{}`, which is `()` (RFC-0231). A closed rest checks the full row against its declared tuple type.
  A final bare `..` and zero explicit extras can select a declared default for the whole rest under RFC-0248.
  A partly filled closed rest is an arity error.
- A keyword argument binds a named parameter. A keyword that binds none is an error (`T0039`), because the rest takes positionals only and there
  is no keyword rest.
- Arguments evaluate left to right as written (RFC-0223).
- After explicit arguments bind, every remaining fixed parameter needs a binding. RFC-0248's final
  `..` can supply a declared default. An empty rest alone cannot supply a missing fixed parameter.

### 3. The body

`rest` is a local of tuple type. It supports ordinary tuple operations under the same shape and aspect
requirements as any other tuple (RFC-0151). Access to `rest.0` requires the row to establish that the position
exists. An unconstrained `R` can be empty. The rest can be passed to a function generic over a row. A by-value
rest parameter **owns** the packed extras (RFC-0179), so they are the callee's to move, return or drop.

The body cannot yet loop over `rest`'s elements one by one. Per-element code needs RFC-0174's `comptime for` over a row (under review),
or a call to a function that is itself generic over the row. This RFC does not add either.

### 4. Function values

A variadic declaration can be used as a function value at a known arity supplied by the expected callable type:

```metel
let f: |String, i64, String| := log;       // R = .{ .0: i64, .1: String }
```

The expected positional `Args` row supplies every fixed positional parameter and fixes `R` from the remaining
positions, renumbered from `.0`. The result is an ordinary function value at that arity. Its calls use ordinary
function-value binding, so they supply the full positional list. A declaration with keyword-only parameters
needs an explicit closure that binds them by name. An absent expected type, or one whose arity is still unknown,
is an error. This conversion requires no generic variadic `Callable` impl or type that quantifies over arity.

### 5. Overloads

First determine which candidates can bind the call. Check the candidate's positional and keyword parameters,
rest shape and bounds, argument types, and the defaults requested by a final `..` (RFC-0248). Among viable
candidates, fixed arity takes priority over open rest. A declaration with a closed rest counts as fixed arity,
as does one with individually declared parameters. Existing overload rules apply among fixed-arity candidates.
If two or more viable open-rest candidates remain and there is no viable fixed-arity candidate, the call is
ambiguous. The number of leading parameters and the rest's field-wise bounds do not break that tie.

---

## Alternatives considered

| Alternative | Why not |
|---|---|
| Do nothing: pass an explicit tuple, `log("info", (x, y))` | It works today. It is the baseline, and the Motivation says what a rest parameter removes. Reasonable to choose if nothing else needs the feature. |
| Homogeneous rest, `..xs: i64` collecting into a sequence of `i64` | Needs a collection with an unknown length, which a row of fixed arity does not. A bound on the row (`where R: Is<i64>`-style) covers the common case without one. Left to a later RFC. |
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
- **RFC-0125** (under review): positional recursion over rows. Direct calls and conversion at a known arity
  use concrete argument positions. A callable abstraction over unknown arities is deferred.
- **RFC-0248** (under review): a final bare `..` may fill unbound defaults after ordinary positional and
  keyword binding. It also specifies how an empty rest can use a declared default.
- **RFC-0246** (under review): owns any use of the rest mechanism by derivations, including
  their target-dependent flow type. Ordinary rest parameters can ship independently.
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

## Design resolutions

1. **Surface spelling of the type.** Resolved. `..rest: .{ R }` forms the parameter's tuple type from the row
   bound by `<..R>`, using RFC-0208's ordinary row and type syntax.
2. **Homogeneous rest.** Deferred. This RFC uses tuple-valued rest parameters. A future proposal for
   `..xs: T` must decide between a homogeneous tuple and a variable-length sequence.
3. **Call-site spread — owned by RFC-0256.** [RFC-0256](rfc-0256-whole-row-argument-expansion-at-ordinary-calls.md)
   proposes sole-section ordinary calls, `f(..t)`, using RFC-0255's extraction contract.
   Generic density evidence and callable compatibility are acceptance questions there.
   Mixed calls such as `f(a, ..t)` remain outside that proposal; positional concatenation
   remains with RFC-0125 or a follow-up. Rest parameters do not wait for call-site expansion.
4. **Function values.** Resolved. The expected callable type fixes the arity. Callable values that can be
   invoked at multiple arities are deferred.
5. **Overloads.** Resolved. Among viable candidates, fixed arity (including closed rest) takes priority over
   open rest. Two or more remaining open-rest matches are ambiguous.
6. **Defaults before the rest.** Settled by RFC-0248 §5. Explicit arguments fill fixed positions before
   the rest. Only the final bare `..` supplies defaults.
7. **Derivation flows.** Owned by RFC-0246. A derivation-specific `Flow` contract is outside this RFC.
8. **Placement.** Function types owns this RFC and the basic RFC-0208 binder prerequisite
   (metel-core#1789 and #2167). Direct calls and conversion at a concrete callable arity need binding
   and inferring `<..R>`, materializing `.{ R }`, and field-wise bounds. They do not depend on
   general row-equation inference or RFC-0125's generic positional renumbering.

---

## Decision

**Outcome:** *(pending)*
