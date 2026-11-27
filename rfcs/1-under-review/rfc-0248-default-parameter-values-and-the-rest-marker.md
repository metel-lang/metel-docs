---
id: rfc-0248
title: "Default parameter values and the rest marker"
date: '2026-11-24'
status: under-review
updated: '2026-11-27'
tracking: 'https://github.com/metel-lang/metel-core/issues/2181'
---

> **Status — under review.** Scheduled in Function types (metel-core#2181).

## Summary

A parameter may declare a default value. A final bare `..` binds remaining fixed parameters
to their defaults and can select a whole-rest default. A fixed parameter left out without `..`
is an error.

```metel
fun connect(host: String, port: i64 = 5432, tls: boolean = true) -> Conn { /* .. */ }

connect("db", ..)                // port = 5432, tls = true
connect("db", port = 1, ..)      // tls = true
connect("db", 6000, false)       // no defaults used
connect("db")                    // error: `port` and `tls` are not bound; write `..` to use their defaults
```

RFC-0246 owns the application of these rules to derivation clauses and the visibility
of computed flows. Existing `derives A(..)` remains governed by RFC-0244.

---

## Motivation

1. **Metel has no default values.** RFC-0223 rule 3 says a call binds every parameter, and lists default values as out of scope;
   RFC-0136 leaves declaration-side defaults to a future RFC. A function with an option that is almost always the same value makes
   every caller write it.
2. **`..` already means "the rest".** A row tail (`.{ .x: i64, ..R }`), a pattern (`let .{ .x, .. } := p`) and a record spread
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

For an aspect method, the aspect declaration supplies the defaults. An implementation declares the full
parameter list without default expressions. Calls resolved to that aspect method use the same defaults
through a concrete receiver, an aspect bound, or an aspect object where the method is object-safe. The
implementation receives the completed argument list.

```metel
aspect Scale {
    fun scale(self, by: i64 = 2) -> i64;
}

extend i64: Scale {
    fun scale(self, by: i64) -> i64 { self * by }
}
```

### 2. Using defaults: `..`

`..` as the **last** argument of a call binds every parameter not bound by an earlier argument to its default (decided 2026-11-24:
defaults are used only explicitly).

A bare `..` followed by another argument is an error. For example, rewrite
`connect("db", .., tls = false)` as `connect("db", tls = false, ..)`.

1. Positional and keyword arguments bind first, by RFC-0223's rules.
2. `..` then binds each remaining fixed parameter to its default and can select a rest default under section 5.
   A remaining fixed parameter with no default makes `..` an error that names it.
3. Without `..`, every fixed parameter must be bound. A diagnostic lists the unbound parameters and suggests
   adding `..` only if every missing parameter has a default.
4. `..` binds only what is unbound. `f(1, ..)` and `f(1, 2, ..)` are both fine; `..` after every parameter is bound is accepted and
   does nothing.

So a call shows when it relies on a default. A reader of `connect("db", ..)` knows that something was left to the declaration; a
reader of `connect("db")` knows nothing was.

In a free-function pipeline stage (RFC-0204), insert the input before applying the default marker.
`xs |> pad(4, ..)` binds as `pad(xs, 4, ..)`. A bare hole does not receive the piped input.
Use an explicit hole section under RFC-0205 to choose a position, as in `(pad(_, ..))(xs)`.

### 3. Evaluation

A default is an ordinary expression checked at the declaration against the parameter's declared type. It can
refer to earlier parameters and uses the ordinary type, ownership, borrowing, and effect rules. It may read
or borrow an earlier parameter, provided the parameter remains available for the function body. For example,
`fun run(tx: Tx, audit: Audit = make_audit(&tx))` may inspect `tx` to compute `audit`. A default expression
that passes `tx` to a consuming helper and leaves it moved is an error at the declaration.

An argument default does not introduce a function or closure body. A `return` or `?` in a
default needs an ordinary enclosing function or closure body inside that expression, such as
a nested closure. It cannot return from either the caller or the declaration whose parameter
has the default.

At each call that uses defaults, evaluate the explicit arguments first, then the requested defaults in
parameter order. A default of a `comptime` function is evaluated at comptime. The call accounts for the
effects of the defaults it evaluates (RFC-0245). Providing the argument explicitly skips the default and
its effects.

### 4. Function values and types

A default is a property of a declaration, so `..` works only in a direct call to a named function, method or associated function,
like a keyword argument (RFC-0223: a keyword in a call through a function value is `T0041`). A call through a function value is
positional and binds every parameter. The type of a function with defaults is its full-arity type: `pad` above is a
`fun(String, i64, String) -> String` (RFC-0240), and assigning it to a value of that type is unchanged.

### 5. Rest parameters (RFC-0247)

Explicit positional arguments fill the fixed positions first, and the extras form the rest tuple. If
there are no explicit extras, a final bare `..` selects the rest's declared default, if it has one.
Otherwise the rest receives the explicit tuple, which may be empty. In either case the whole tuple must
match the rest type. Supplying any extras bypasses the rest default. Defaults do not fill individual
positions in a partly supplied rest tuple.

```metel
fun draw(..point: .{ .0: i64, .1: i64 } = (1, 2)) { /* ... */ }

draw(..)        // point = (1, 2)
draw(9, 8, ..) // point = (9, 8)
draw(9, ..)    // error: the explicit rest has one element
draw()         // error: the empty tuple does not match the closed rest type
```

### 6. Overloads

A call with `..` considers only the overload candidates that can bind the requested defaults under sections 2
and 5. This is a viability check before overload selection. When RFC-0247's rest parameters participate, its
fixed-arity preference applies among the viable candidates. Selection uses the declared signatures. Only the
selected call evaluates its defaults, after evaluating the explicit arguments.

### 7. Documentation and diagnostics

Generated API documentation prints the declared default expression in the parameter list, for example
`port: i64 = 5432`. An unbound-parameter diagnostic names the parameters. `connect("db")` can suggest
`connect("db", ..)`. `connect(..)` identifies the required `host` parameter.

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
| Implicit defaults | A call would hide which arguments come from the declaration. |
| Defaults on keyword parameters only | A final `..` already gives positional calls an unambiguous binding rule. |
| Defaults in a row type | Defaults belong to callable declarations, and putting values inside a row type would affect its identity and unification. |
| Call-site spread `f(a, ..t)` | Expansion is a separate operation owned by RFC-0256 and follow-up work. |

---

## Interaction with other work

- **RFC-0223** (implemented): rule 3 ("there are no default values") is amended: a call binds every parameter, through its arguments
  or through `..`.
- **RFC-0136** (implemented): its out-of-scope note on declaration-side defaults is answered here.
- **RFC-0247** (under review): a rest parameter can select a whole-tuple default as in section 5.
- **RFC-0246** (under review): owns derivation argument lowering and public-flow visibility. RFC-0244
  continues to govern built-in derivation clauses.
- **RFC-0240** (under review): a function type has full arity. Defaults belong to the declaration.
- **RFC-0245** (draft): a default contributes its effects to calls that use it.
- **RFC-0132** (comptime): defaults of comptime functions evaluate at comptime.
- **RFC-0256** (under review): ordinary call expansion uses a sole section such as `f(..args)`.
  Combining expansion with the bare default marker (`f(..args, ..)`) is outside that proposal.

---

## Costs

- **A call that uses defaults writes `..`.** That is one token more than Kotlin or Swift, and it is the point.
- **Evaluation at the call.** A default is code that runs at each call that uses it, in the callee's parameter scope.
- **Overloads.** `..` adds a filter to candidate selection (section 6).

---

## Design resolutions

1. **Default expressions.** Resolved. Ordinary expressions may use effects and may read or borrow earlier
   parameters, subject to the usual rules and the requirement that the parameters remain available for the
   body. Only defaults the call uses contribute effects.
2. **Defaults on aspect methods.** Resolved. The aspect declaration supplies defaults for calls to its
   method. An implementation cannot repeat or override them.
3. **Position of `..`.** Resolved. The bare default marker is final, after all positional and keyword arguments.
4. **Documentation and diagnostics.** Resolved. API documentation shows declared defaults. Diagnostics
   suggest adding `..` only when doing so can complete the binding.
5. **Pipelines and holes.** Resolved. Ordinary pipeline insertion precedes default binding. Bare holes
   in a pipeline stage are rejected. Explicit hole sections use the ordinary call and default rules.

---

## Decision

**Outcome:** *(pending)*
