---
id: rfc-0248
title: "Default parameter values and the rest marker"
date: '2026-11-24'
status: draft
---

## Summary

A parameter may declare a default value. A call uses defaults only by saying so: `..` at the end of an argument list binds every
parameter that is not bound yet to its default. Leaving a parameter out without `..` is an error, as it is today.

```metel
fun connect(host: String, port: i64 = 5432, tls: boolean = true) -> Conn { /* .. */ }

connect("db", ..)                // port = 5432, tls = true
connect("db", port = 1, ..)      // tls = true
connect("db", 6000, false)       // no defaults used
connect("db")                    // error: `port` and `tls` are not bound; write `..` to use their defaults
```

The same rule gives the computed flow of a derivation a meaning that is not a special case. `derive` takes its flow as a rest
parameter whose default is the flow the fields need, so `derives Copy` passes no flow (empty), `derives Copy(T)` states one, and
`derives Copy(..)` takes the default:

```metel
struct Id<T>    derives Clone, Copy           { n: i64 }    // no flow: the empty flow
struct Boxed<T> derives Clone(T), Copy(T)     { v: T }      // a stated flow
struct Pair<A, B> derives Clone(..), Copy(..) { a: A, b: B } // the flow's default: what the fields need, (A, B)
```

`..` means the same thing in every call. This is a design draft, tracked by metel-core#2181. Nothing here is accepted.

---

## Motivation

1. **Metel has no default values.** RFC-0223 rule 3 says a call binds every parameter, and lists default values as out of scope;
   RFC-0136 leaves declaration-side defaults to a future RFC. A function with an option that is almost always the same value makes
   every caller write it.
2. **Derivations need one.** A derivation's flow has a natural default, the flow its fields need, and the language has spelled
   "use it" three ways in two days: a postfix `?`, the bare entry before RFC-0244, and `(..)`. Each was a special case in what
   RFC-0238 makes an ordinary call. RFC-0238 and RFC-0246 had also started to write defaults into row types
   (`.{ .rename_all: String = "none" }`), which put a value in a type; that was taken out (#2181).
3. **`..` already means "the rest".** A row tail (`.{ .x: i64, ..R }`), a pattern (`let .{ .x, .. } := p`) and a record spread
   (`.{ ..s, .a = 10 }`) all read `..` as "the rest". In an argument list it can read the same way: the rest of the parameters, from
   their defaults.

---

## Proposal

### 1. Declaring a default

A parameter of a function, method, associated function or aspect method may declare a default after its type:

```metel
fun pad(s: String, width: i64 = 8, fill: String = " ") -> String { /* .. */ }
```

- Any parameter may have one, positional or keyword (decided 2026-11-24). A default before a parameter without one is allowed, since
  defaults are only ever used through `..` (section 2) and so never make a positional call ambiguous.
- `self` has no default.
- A default belongs to the declaration, not to a type. A row type has no defaults; a written function type has none either.

### 2. Using defaults: `..`

`..` as the **last** argument of a call binds every parameter not bound by an earlier argument to its default (decided 2026-11-24:
defaults are used only explicitly).

1. Positional and keyword arguments bind first, by RFC-0223's rules.
2. `..` then binds each remaining parameter to its default. A remaining parameter with no default makes `..` an error that names it.
3. Without `..`, every parameter must be bound, as today: a defaulted parameter left out is an error whose fix-it adds `..`.
4. `..` binds only what is unbound. `f(1, ..)` and `f(1, 2, ..)` are both fine; `..` after every parameter is bound is accepted and
   does nothing.

So a call shows when it relies on a default. A reader of `connect("db", ..)` knows that something was left to the declaration; a
reader of `connect("db")` knows nothing was.

### 3. Evaluation

A default expression is evaluated at each call that uses it, after the explicit arguments, left to right in parameter order. It may
refer to the parameters before it (`fun slice(xs: &[T], from: u64 = 0, to: u64 = xs.len())`), and not to later ones. A default of a
`comptime` function is evaluated at comptime. A default's effects (RFC-0245) are the effects of the call that uses it.

### 4. Function values and types

A default is a property of a declaration, so `..` works only in a direct call to a named function, method or associated function,
like a keyword argument (RFC-0223: a keyword in a call through a function value is `T0041`). A call through a function value is
positional and binds every parameter. The type of a function with defaults is its full-arity type: `pad` above is a
`fun(String, i64, String) -> String` (RFC-0240), and assigning it to a value of that type is unchanged.

### 5. Rest parameters (RFC-0247)

A rest parameter with no arguments is empty; that is what a rest parameter means, not a default. A rest parameter may also declare a
default, which `..` uses when no argument was given to it. Because defaults apply only through `..`, a defaulted positional before a
rest parameter is not ambiguous: extra positionals go to the positionals first and then to the rest, and `..` fills what is left.
This answers RFC-0247 question 6.

### 6. Derivations

`derive` is written as a parameter list (RFC-0247 question 7), with the flow as a rest parameter whose default is the flow the fields
need:

```metel
extend Clone: Derivable {
    comptime fun derive(Target: type, ..flow: Flow = std::derive::needed_flow(Target, Clone)) -> Decl {
        field_wise(Clone, Target, flow)
    }
}
```

- `derives Clone` passes no flow: the rest is empty, the empty flow of RFC-0244. It is not a default.
- `derives Clone(T)` passes the flow `(T)`.
- `derives Clone(..)` binds the flow to its default: `needed_flow(Target, Clone)`, the smallest set of parameters every field's
  `Clone` depends on (RFC-0227's dependence analysis). `needed_flow` is a native std function, as other std natives are, and the
  knowledge of what a field needs lives in it, not in the syntax.
- `derives Clone(T, ..)` is `derives Clone(T)`: the flow is bound by `T`, so `..` has nothing to fill. There is no "at least `T`"
  form.
- A derivation with other parameters works the same: `derive(Target: type, name: String, ..flow: Flow = needed_flow(..))` takes
  `derives Serialize("x", T)` or `derives Serialize("x", ..)`.

So `(..)` in a `derives` clause is the general `..` of a call, and the only thing particular to derivations is the default std
declares for its flow.

The `pub` rule (RFC-0227 section 3) returns in the form RFC-0244 gave it: a `pub` generic type may use `(..)` only when the flow it
yields is empty, because a computed flow is an interface a field edit could change. A `pub` type states its flow. This is a rule about
derivations, not about `..`.

### 7. Overloads

A call with `..` considers only the overload candidates that have a default for every parameter `..` would bind. Selection is
otherwise unchanged and stays static.

---

## Prior art

Recalled, not re-checked against each language's current documentation.

| Language | Defaults | Used how |
|---|---|---|
| Kotlin, Swift, C#, Python, C++ | on the declaration | implicitly, by leaving the argument out |
| Rust | none for functions | struct update syntax `Config { port: 1, ..Default::default() }`: an explicit `..` for "the rest from defaults" in a struct literal |
| OCaml | optional labelled arguments `?(x = 0)` | implicitly, with rules for when an optional argument is erased |
| Haskell | none | record update on a default value, or builder functions |

The explicit `..` follows Rust's struct update syntax, which writes "the rest from defaults" at the use site, and extends it from
struct literals to calls.

---

## Alternatives considered

| Alternative | Why not |
|---|---|
| Implicit defaults: leaving a defaulted argument out uses its default | The common choice. It makes a default invisible at the call, and in a `derives` clause it would make a bare entry mean "computed", reversing RFC-0244. Decided against 2026-11-24. |
| Defaults on keyword parameters only | Simpler to read, but a rest parameter's default (the flow) still needs a rule, and with explicit `..` positional defaults are not ambiguous. Decided against 2026-11-24. |
| Defaults in a row type (`.{ .x: i64 = 1 }`) | Puts a value in a type: whether `.{ .x: i64 = 1 }` is `.{ .x: i64 }`, and how a default takes part in unification, have no good answer. Removed from RFC-0238 and RFC-0246 (#2181). |
| Call-site spread `f(a, ..t)` in this RFC | The same `..` family, but useful without defaults and the dual of a rest parameter (RFC-0247 question 3). Left to its own RFC (decided 2026-11-24). |
| Keep `(..)` as a `derives`-only form | The special case this RFC removes. |
| A flow is always stated | Merged state of metel-core#2182, not merged: no computed flow at all. The ergonomic cost (writing and maintaining every flow) was judged too high. |

---

## Interaction with other work

- **RFC-0223** (implemented): rule 3 ("there are no default values") is amended: a call binds every parameter, through its arguments
  or through `..`.
- **RFC-0136** (implemented): its out-of-scope note on declaration-side defaults is answered here.
- **RFC-0247** (under review): a rest parameter with no arguments is empty, and may declare a default; question 6 is answered (section 5)
  and question 7 (a parameter list for `derive`) is adopted.
- **RFC-0246** (under review): its trailing `Flow` becomes a rest parameter of `derive`, which replaces the renumbering row tail
  `..Flow` and its dependence on RFC-0125. Its question 5 ("a computed flow anywhere?") is reopened by this RFC: `(..)` returns as the
  general `..`.
- **RFC-0238** (under review): `derive`'s signature is a parameter list, not a `type Args` row.
- **RFC-0244** (implemented): a bare entry stays the empty flow; `(..)` stays, now as the general `..`.
- **RFC-0240** (under review): a function type has full arity; defaults are not part of it.
- **RFC-0245** (draft): a default's effects are the call's.
- **RFC-0092, RFC-0132** (comptime): defaults of `comptime` functions, and `needed_flow`.

---

## Costs

- **A call that uses defaults writes `..`.** That is one token more than Kotlin or Swift, and it is the point.
- **Evaluation at the call.** A default is code that runs at each call that uses it, in the callee's parameter scope.
- **Overloads.** `..` adds a filter to candidate selection (section 7).
- **Derivations depend on rest parameters.** Section 6 needs RFC-0247, or the trailing positional of RFC-0246, to give `derive` a rest
  parameter.

---

## Open questions

1. **What may a default expression do?** Any expression, or a restricted set (no effects beyond the call's, no reference to mutable
   state)?
2. **Defaults on aspect methods.** If an aspect method declares a default, does an impl repeat it, may it differ, or is it the
   aspect's alone (RFC-0223 requires impls to repeat parameter names, `T0042`)?
3. **`..` before keyword arguments.** This draft puts `..` last. Is `connect("db", .., tls = false)` worth allowing?
4. **Documentation and diagnostics.** How a signature with defaults prints in diagnostics and in generated documentation.
5. **Pipelines (RFC-0204, RFC-0205).** How `..` interacts with hole sections and `|>`, for example `xs |> pad(_, ..)`.

---

## Decision

**Outcome:** *(pending)*
