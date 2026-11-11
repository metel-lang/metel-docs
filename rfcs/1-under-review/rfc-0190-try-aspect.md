---
id: rfc-0190
title: "Try Aspect"
date: '2026-10-28'
status: under-review
updated: '2026-10-28'
tracking: 'https://github.com/metel-lang/metel-core/issues/1637'
---

> **Status — under review (2026-10-28).** design settled; open questions resolved; committed to v0.15.0 via metel-core#1637

## Summary

Define `?` over a pair of core aspects instead of two hard-coded types. `Try` is implemented by
the **operand** type and says how to split a value into "keep going" or "leave early".
`FromResidual<R>` is implemented by the **enclosing return type** and says how to rebuild itself
from an early exit. `Result` and `Option` get the first two impls, so every program that compiles
under RFC-0182's closed rule keeps compiling, and a user-defined type can now be used with `?`.

```metel
enum Lookup<T> { Found { value: T }, Missing }
struct Missed {}

extend<T> Lookup<T>: Try {
    type Output := T;
    type Residual := Missed;
    fun branch(self) -> ControlFlow<Missed, T> {
        match (self) {
            Found { value } => ControlFlow::Continue { value },
            Missing => ControlFlow::Break { value = Missed {} },
        }
    }
}
extend<T> Lookup<T>: FromResidual<Missed> {
    fun from_residual(residual: Missed) -> Lookup<T> { Missing }
}

fun both(a: Lookup<i64>, b: Lookup<i64>) -> Lookup<i64> {
    Found { value = a? + b? }          // either Missing leaves `both` with Missing
}
```

This is the generalisation RFC-0182 §3 and its resolved Open Question 1 reserved: the closed
`{Result, Option}` rule becomes the first two impls rather than being replaced. It closes
GAP-FUNCTIONS-004 (metel-core#1637). It changes the checker's handling of a shipped operator, so
it needs this RFC before any implementation (see `metel_rfc_before_implementation`).

---

## Motivation

`?` is a compiler special form over exactly two types, recognised by declaration identity
(`infer_propagate_error`, `construct_propagate_error`). The cost shows in two places:

- **Library types cannot take part.** A type that models its own fallible or absent value
  (a three-state `Lookup`, a `Validation` that accumulates, a parser result) must be bridged to
  `Result` or `Option` with `.ok()` / `.ok_or(…)` at every use before `?` applies, and cannot be
  the *return* type of a function that uses `?` at all.
- **The rule is not extensible where RFC-0182 said it should be.** RFC-0182 §2 and its Open
  Question 2 left "an `E2: From<NoneError>`-style impl" as a strictly additive follow-up. With a
  closed rule there is nowhere to hang it.

Two shipped facts constrain the design and are checked here rather than assumed:

- `Result<!, String>` is already a valid type (checked against the current build), so the
  never type may appear as a type argument.
- Aspects already have associated types, bound with `type Name := T;` in an impl, and the
  object-safety rules already exclude methods whose signatures mention them (RFC-0008 §3b).

---

## 1. The aspects

```metel
enum ControlFlow<B, C> {
    Continue { value: C },
    Break { value: B },
}

aspect Try {
    type Output;
    type Residual;
    fun branch(self) -> ControlFlow<Residual, Output>;
}

aspect FromResidual<R> {
    fun from_residual(residual: R) -> Self;
}
```

(`Try`, `FromResidual` and `ControlFlow` live in `std::core` and are **not** in the prelude:
ordinary `?` use names none of them, and only code that implements the aspects or writes generic
bounds imports them. `ControlFlow` is a plain generic enum; it is not special to the checker.)

`Try` is about the operand: `Output` is what `e?` evaluates to when execution continues,
`Residual` is the value carried out when it does not. `FromResidual<R>` is about the function:
a return type `Ret` can absorb a residual `R` when `Ret: FromResidual<R>`. Keeping them separate
is the point. The operand's family and the return type's family need not be the same, and the
conversion between them lives in an ordinary impl instead of in the operator.

### The core impls

```metel
extend<T, E> Result<T, E>: Try {
    type Output := T;
    type Residual := Result<!, E>;
}
extend<T, E1, E2: From<E1>> Result<T, E2>: FromResidual<Result<!, E1>> { … }  // Err { error = E2::from(error) }

extend<T> Option<T>: Try {
    type Output := T;
    type Residual := Option<!>;
}
extend<T> Option<T>: FromResidual<Option<!>> { … }                             // None
```

The residual of a core type is the type itself with the success payload erased to `!`
(`Result<!, E>`, `Option<!>`). That keeps the families distinct (a `Result` residual is not an
`Option` residual), carries the error value for `Result` and nothing for `Option`, and needs no
new nominal types. The `From` conversion for `Result` is the `E2: From<E1>` bound on its
`FromResidual` impl, so RFC-0182's error-conversion row is now an impl, not a clause of the
operator.

**The same-type case uses a reflexive `From`.** Today's checker skips the conversion when
`E1 == E2`. The impl above needs `E2: From<E1>` to hold then too, so core gains
`extend<T> T: From<T>` (the identity). It is additive and overlaps no existing impl: the numeric
`From` impls convert between *different* types. After this the checker no longer special-cases
equal error types.

---

## 2. The operator

For `e?` in a function or closure whose return type is `Ret`:

1. The type of `e` must implement `Try`; call it `X`.
2. `Ret` must implement `FromResidual<X::Residual>`.
3. The expression has type `X::Output`.

It evaluates as

```metel
match (e.branch()) {
    ControlFlow::Continue { value } => value,
    ControlFlow::Break { value } => return Ret::from_residual(value),
}
```

with the same ownership rules as today: `e` is moved into `branch`, and the `return` is an
ordinary `return` (every live binding is dropped or moved as at any explicit `return`; no new
control-flow shape for `once`/`mutating` closures or move checking, `spec.functions.closures.dynamics-13`).

### What does not change

- `Result` operand in a `Result` function with `E2: From<E1>`: same behaviour, same `T0007` when
  the conversion is missing.
- `Option` in `Option`: same behaviour.
- `Option` in a `Result` function, and `Result` in an `Option` function: still rejected, because
  no `FromResidual` impl connects them. The diagnostic keeps RFC-0182 §6's help line
  (`.ok_or(...)` / `.ok()`); it is a special case in the message for these two core pairings, not
  a rule of the operator.
- `?` outside any function or closure stays `T0005`; a mismatch stays `T0001`.

### Inference

RFC-0182 resolves an operand whose type is still a variable from the return type's constructor,
and the reverse for a closure with no written return type. A bare `FromResidual<?>` constraint
cannot do this (`Result<U, E2>` absorbs any `Result<!, E1>` with `E2: From<E1>`, so the operand is
not determined). The rule is therefore kept as a **defaulting step for the core types only**: if
the operand type is unresolved and the return type's constructor is `Result` or `Option`, the
operand defaults to that constructor applied to fresh variables, as today; likewise for an
unresolved return type and a known `Result`/`Option` operand. A user-defined `Try` type is **not** defaulted: its
operand and return type must be known when `?` is checked; otherwise the error is `T0002`, asking
for an annotation. No program accepted today is affected.

### Generic code

A function generic over `Try` states the link between operand and return type as bounds: the
operand `T: Try`, and the return type `R: FromResidual<T::Residual>`, using the associated-type
projection the spec already defines for aspects. This RFC adds no bound syntax.

---

## 3. Interactions

- **Object safety (RFC-0008).** `Try::branch` names `Residual` and `Output` in its signature, so
  by RFC-0008 §3b it is not object-safe and `dyn Try` is rejected. That costs nothing: `?` is
  resolved statically on the operand's concrete type, so no runtime dispatch is involved.
  `FromResidual<R>::from_residual` returns `Self`, so it is not dispatchable either, for the usual
  reason.
- **Closures and `Callable` (RFC-0161).** `?` targets the closure body's own return type, exactly
  as it targets a function's. It never consults the closure's call contract, so this RFC does not
  depend on `Callable`, and a `Callable<Args, R>` bound with `R: Try` composes with no extra rule.
- **Coherence and orphans (RFC-0060, RFC-0097).** `Try` and `FromResidual` impls are ordinary
  aspect impls and follow the existing rules. A user type can implement both for itself, and can
  implement `FromResidual<Missed>` for `Result<T, E>` when `Missed` is local, which is how a custom
  absence converts into any chosen error type.
- **`From` and `as`.** The `From` aspect is unchanged. `as` still desugars to `T::from(value)`.
- **`main` (RFC-0004).** Out of scope. Whatever `main` may return is decided there; a natural
  later step is a bound on `FromResidual`.
- **Shadowing (RFC-0182 §4).** Resolution goes through the core `Try`/`FromResidual`
  declarations by identity, never by spelling, so a module that declares its own `Result` still
  cannot capture `?` on std values.

---

## Alternatives Considered

- **Keep the closed rule (RFC-0182 as shipped).** Zero new surface, but nothing generalises and
  the error-conversion row stays inside the operator. Rejected as the end state; it remains the
  behaviour of every program that does not define a `Try` type.
- **One aspect (`Try` only, Rust's original `into_result`/`from_error`/`from_ok` shape).** The
  return type's rebuild is expressed through the operand's own aspect, so the family of the
  operand and of the function are forced to be the same, and cross-family conversion has nowhere
  to live. Splitting out `FromResidual` is what allows `Result<T, E2>: FromResidual<Result<!, E1>>`
  to own the `From` step.
- **A dedicated nominal residual type per core type** (`ResultResidual<E>`, `OptionResidual`).
  Works, adds two stdlib types. Rejected in favour of erasing the payload to `!` in the type
  itself, which already parses.
- **Method on the return type only** (`Ret::from_operand(e)`). Loses the distinction between
  "keep going" and "leave", so the operator cannot produce the `Output` value.

---

## Changes on Acceptance

- `reference/spec/functions.md`, *The ? Operator*: Legality Rule 1 restated through `Try` /
  `FromResidual`, with `Result` and `Option` as the first two impls; Legality Rule 2 (`From`)
  becomes the bound on the core `Result` impl; Dynamic Semantics gains the `branch` form.
- `reference/spec/runtime.md`, *Built-in aspects*: `Try`, `FromResidual<R>`, `ControlFlow`.
- `architecture/gaps/gap-functions-004.md`: resolved and removed on integration.
- RFC-0182: a note that its closed rule is now the first two impls.

## References

- metel-core#1637 — the design issue; GAP-FUNCTIONS-004.
- RFC-0182 (Question Mark on Option) §3 alternative 2, Open Questions 1–2: the closed rule this
  generalises, and the `From<NoneError>`-style follow-up it left open.
- RFC-0008 (Aspect Objects) §3b: why `Try` is not object-safe.
- RFC-0161 (Callable Object Contract): `?` does not depend on it.
- RFC-0060, RFC-0097: coherence and orphan rules for the new impls.
- RFC-0004 (`main` return type): out of scope.

---

## Decision

**Outcome:** *(pending)*
**Target:** *(set when accepted)*
