---
id: rfc-0182
title: "Question Mark on Perhaps"
date: '2026-10-24'
status: under-review
updated: '2026-10-24'
tracking: 'https://github.com/metel-lang/metel-core/issues/1593'
---

> **Status — under review (2026-10-24).** design settlement committed to a release milestone (tracking issue linked).

## Summary

Extend the `?` operator to `Perhaps<T>`. In a function (or closure) that returns
`Perhaps<U>`, `e?` with `e: Perhaps<T>` evaluates to `T` on `Some` and returns `None` from
the enclosing function on `None`. `?` stays one operator with one rule: **the operand's
type constructor must match the enclosing function's return type constructor.**

Mixed use is not added. `?` on a `Perhaps` inside a `Result`-returning function, and `?` on
a `Result` inside a `Perhaps`-returning function, remain type errors, and the diagnostic
names the existing conversion (`.ok_or(...)`, `.ok()`) that bridges them.

This is a language-surface change to a shipped operator, so it needs this RFC before any
implementation (see `metel_rfc_before_implementation`).

---

## Motivation

### The gap

`?` is defined over `Result<T, E>` only
([`spec.functions.the-operator.legality-1`](../../reference/spec/functions.md#spec.functions.the-operator.legality-1)),
and the spec says so on purpose: "`?` does not apply to `Perhaps<T>` in this language
version". Every other absence-returning API in the language is `Perhaps`: `std::env::get`,
list and map lookups, `Result::ok`, `Perhaps::and_then`. A function that chains them cannot
use `?`:

```metel
import std::env::get;

fun config_path() -> Perhaps<String> {
    let home := get("HOME")?;            // T0001: cannot unify Perhaps<String> with Result<?1, ?2>
    Some { value = home + "/.config" }
}
```

The only alternatives today are a nested `match` per call or a chain of `.and_then` closures.
A two-step lookup is already noisy; a five-step one is the case `?` exists for.

### The diagnostic is also bad

The message above exposes inference variables (`?1`, `?2`) and never says that `?` needs a
`Result`. This was found while fixing metel-core#1585 and filed as metel-core#1589. Whatever
this RFC decides, that message has to change: if `Perhaps` support is refused, the rule
should be stated in the error (see §6).

### Prior decisions this RFC has to respect

- **RFC-0079** (refused 2026-07-10) specified `?` on `Perhaps` in §6, with the same
  `None`-propagating desugaring proposed here, and deferred "`Perhaps<T>` and `?` in
  `Result`-returning functions" as its Open Question 4. It was refused because most of the
  RFC was already implemented, not because of a design objection to this section. Its closing
  note lists "undocumented `?`-on-`Perhaps`" as a remaining gap, but the spec is not
  undocumented now: it documents the opposite (an explicit rejection). This RFC replaces
  that rejection.
- **RFC-0015** (unwrap syntax) chose method form for `.yolo()` and treats `?` as a compiler
  special form. Nothing here changes that.
- **RFC-0004** (`main` return type, draft) assumes `?` is Result-only ("because `?` is only
  valid inside functions returning `Result<T, E>`"). §7 notes the interaction.

---

## 1. The rule

`e?` is well-typed when, for the enclosing function or closure's return type `R`:

| operand `e` | `R` | result type | on the failure case |
|---|---|---|---|
| `Result<T, E1>` | `Result<U, E2>`, `E2: From<E1>` | `T` | `return Err { error = E2::from(error) }` (unchanged) |
| `Perhaps<T>` | `Perhaps<U>` | `T` | `return None` (new) |
| anything else, or any other pairing | | | type error |

The return type decides which row applies. That matters for inference: an operand whose type
is still a variable when `?` is checked (a closure parameter, an un-annotated `let`) is
resolved by the return type, as it is today, instead of being ambiguous. The return type
must therefore be known to be `Result` or `Perhaps` at the `?`; outside such a function the
error stays `T0005`.

```metel
fun port(env_name: String) -> Perhaps<u16> {
    let raw := get(env_name)?;           // Perhaps<String>, in a Perhaps-returning fn
    let n   := parse_u16(raw)?;          // Perhaps<u16>
    Some { value = n }
}
```

`None` carries no payload, so there is no `From`/conversion step and no `E` to check: the
Perhaps row has no error-type constraint.

### Desugaring

```metel
let x := match (e) {
    Some { value } => { value },
    None => { return None; },
};
```

with the same value-category rules as the `Result` desugaring (`e` is moved, `value` is
moved out, the early return is an ordinary `return` for ownership and drop purposes). The
explicit `return` is the same one `?` on `Result` already lowers to, so `once`/`mutating`
closure bodies, `defer`-style scopes and move checking see no new control-flow shape.

---

## 2. Why not allow mixed use

Two mixed cases are tempting. Neither is proposed.

### `Perhaps` inside a `Result`-returning function

```metel
fun load() -> Result<String, ConfigError> {
    let home := get("HOME")?;            // None -> which ConfigError?
    ...
}
```

`None` has no error value. Converting it needs one from somewhere: a default error, an
`E2: From<NoneError>` impl, or per-site text. All three are invented machinery for a case
the language already covers with one explicit word at the site that knows the answer:

```metel
let home := get("HOME").ok_or(ConfigError::NoHome)?;
```

`ok_or` already exists in `std::core`, the error is named where it is meaningful, and the
`?` rule stays "type constructors match". RFC-0079's Open Question 4 is therefore answered
"no, use `ok_or`".

### `Result` inside a `Perhaps`-returning function

`e?` would discard the error. Silently throwing an `Err` away is the opposite of what the
operator signals; `.ok()` makes the discard visible at the site (`parse(s).ok()?`).

---

## 3. Alternatives considered

1. **Status quo.** Keep `?` Result-only; fix only the diagnostic. Cheapest, but leaves
   `Perhaps`-returning functions with no early-exit syntax, in a language where `Perhaps` is
   the standard absence type. The cost is paid at every call site, the benefit is a smaller
   operator.
2. **A `Try` aspect** (Rust's `Try`/`FromResidual`, Swift/Kotlin-style generalisation). `?`
   would be defined over any type implementing the aspect, with `Result` and `Perhaps` as
   the two impls and user types allowed. This is the principled end state, but it needs a
   residual/branch associated-type design, a story for how it composes with `From`, and it
   touches RFC-0008 object safety and RFC-0161's `Callable` question for closures. That is a
   large design to block a two-type feature on. The closed `{Result, Perhaps}` rule here is
   the first two impls of such an aspect, so it does not prevent it (§8).
3. **Mixed conversion with a default error** (§2). Rejected above.
4. **A separate operator for `Perhaps`** (e.g. `?!`). More surface, and it makes the author
   pick the operator by operand type, which the compiler already knows.

---

## 4. Interactions

- **Closures.** `?` returns from the nearest enclosing function or closure body. A closure
  with a `Perhaps<U>` return can use it exactly as a `Result`-returning one can today.
  RFC-0153's `mutating` closures already state that an early exit is "a `?`-propagated
  `Err` or an early `return`" (`spec.functions.closures.dynamics-13`); that sentence widens to
  "`?`-propagated `Err` or `None`".
- **`main`.** `fun main() -> Perhaps<()>` is not proposed here. RFC-0004 decides what `main`
  may return; if it adopts `Result`, it should also say whether `Perhaps` is allowed.
- **Shadowing.** The checker currently builds the operand constraint from the spelling
  `"Result"` with no declaration id (`infer_propagate_error`). Since metel-core#1585 a module
  may shadow `Perhaps`/`Result`, so an implementation must constrain against the *core*
  declarations by id, not by name; otherwise a module that declares its own `Result` breaks
  `?` on std values. This RFC's implementation must include that.
- **Error codes.** Unchanged in the Result row (`T0005` for `?` outside a
  Result-returning function, `T0007` for a missing `From`). `T0005`'s message widens to name
  both return types. See §6.

---

## 5. Specification changes (on acceptance)

`reference/spec/functions.md`, "The ? Operator":

- **Legality Rule 1** now reads: the operand must be `Result<T, E>` or `Perhaps<T>` and the
  enclosing return type must be the same type constructor; any other pairing is a type error.
  The prose sentence "`?` does not apply to `Perhaps<T>` in this language version" is
  removed.
- **Legality Rule 2** (`From`) is scoped to the `Result` row.
- **New Dynamic Semantics 3:** evaluating `None?` returns `None` from the enclosing
  function; `Some { value }?` produces `value`.
- `spec.functions.closures.dynamics-13` adds `None`.

The current negative fixture `stage6_neg_05_error_propagation_non_result` (`42?`) stays valid
(an `i64` operand is neither type). A fixture asserting `Perhaps` is *rejected* does not
exist today (the rule is covered only through `42?`), so there is no fixture to retire.

---

## 6. Diagnostics

Independent of the outcome (and the reason metel-core#1589 exists), `?` on a mismatched
pairing should say what the rule is, with no inference variables:

```
T0001: `?` on `Perhaps<String>` needs the enclosing function to return `Perhaps<_>`,
but it returns `Result<Config, ConfigError>`
  = help: turn the absence into an error first: `.ok_or(...)`
```

and the converse suggests `.ok()`. If this RFC is refused, the same message ships with the
sentence "`?` requires a `Result`" in place of the first line, so that closing it does not
leave #1589's complaint standing.

---

## Open Questions

1. **Is a closed `{Result, Perhaps}` rule enough, or should this wait for a `Try` aspect?**
   §3.2 argues the closed rule is the first two impls of that aspect. The risk is that the
   closed rule bakes in a semantics (`None` has no payload, so no conversion step) that an
   aspect would have to generalise. Is that acceptable debt?
2. **Should the `Perhaps`-in-`Result` case be revisited with a conversion hook later?**
   §2 says no for now, on the grounds that `ok_or` is one word. If real code shows the
   `ok_or(SameError)` repeated across a function, an `E2: From<NoneError>`-style impl is the
   place to add it, and it would be a strictly additive rule.
3. **`?` on a `Perhaps<Result<T, E>>` / `Result<Perhaps<T>, E>` (transpose).** Not addressed:
   each `?` strips one layer and checks it against the return type, so nesting works by
   repeated `?`. Worth one worked example before acceptance.
4. **Implicit-return position.** `get("X")?` as the tail expression of a block that is not
   the function body: the early `return` leaves the function, not the block. This is the
   same as `Result` today but should be stated in the Dynamic Semantics.
5. **Move checking.** The `return None` path drops everything live in scope, as an ordinary
   `return` does. Confirm this needs no new rule and add a fixture (a partially moved struct
   live at the `?`).

---

## References

- metel-core#1589 — the report this RFC answers (`?` on `Perhaps` is a unification error).
- metel-core#1585 — made shadowing `Perhaps`/`Result` safe; §4 depends on its id-based lookups.
- RFC-0079 — refused; §6 proposed the same `None` propagation, OQ4 the mixed case.
- RFC-0015 — unwrap syntax (`.yolo()` as a method); `?` as a compiler form.
- RFC-0004 — `main` return type.
- RFC-0153 — closure mutation axis (`dynamics-13`, early exit through `?`).
- `reference/spec/functions.md` — "The ? Operator".

---

## Decision

**Outcome:** *(pending)*
