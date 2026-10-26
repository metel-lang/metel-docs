---
id: rfc-0182
title: "Question Mark on Option"
date: '2026-10-24'
status: accepted
updated: '2026-10-26'
tracking: 'https://github.com/metel-lang/metel-core/issues/1593'
---

> **Status — under review (2026-10-24).** design settlement committed to a release milestone (tracking issue linked).

> **Naming (2026-10-26).** This RFC was written when the type was `Perhaps<T>`. RFC-0184 (accepted
> 2026-10-26) renames it `Option<T>`; the text below uses the new name throughout so the `?` rule
> never appears under the old one. No design change.

> **Status — accepted (2026-10-26).** Reviewed 2026-10-26; open questions resolved

## Summary

Extend the `?` operator to `Option<T>`. In a function (or closure) that returns
`Option<U>`, `e?` with `e: Option<T>` evaluates to `T` on `Some` and returns `None` from
the enclosing function on `None`. `?` stays one operator with one rule: **the operand's
type constructor must match the enclosing function's return type constructor.**

Mixed use is not added. `?` on an `Option` inside a `Result`-returning function, and `?` on
a `Result` inside an `Option`-returning function, remain type errors, and the diagnostic
names the existing conversion (`.ok_or(...)`, `.ok()`) that bridges them.

This is a language-surface change to a shipped operator, so it needs this RFC before any
implementation (see `metel_rfc_before_implementation`).

---

## Motivation

### The gap

`?` is defined over `Result<T, E>` only
([`spec.functions.the-operator.legality-1`](../../reference/spec/functions.md#spec.functions.the-operator.legality-1)),
and the spec says so on purpose: "`?` does not apply to `Option<T>` in this language
version". Every other absence-returning API in the language is `Option`: `std::env::get`,
list and map lookups, `Result::ok`, `Option::and_then`. A function that chains them cannot
use `?`:

```metel
import std::env::get;

fun config_path() -> Option<String> {
    let home := get("HOME")?;            // T0001: cannot unify Option<String> with Result<?1, ?2>
    Some { value = home + "/.config" }
}
```

The only alternatives today are a nested `match` per call or a chain of `.and_then` closures.
A two-step lookup is already noisy; a five-step one is the case `?` exists for.

### The diagnostic is also bad

The message above exposes inference variables (`?1`, `?2`) and never says that `?` needs a
`Result`. This was found while fixing metel-core#1585 and filed as metel-core#1589. Whatever
this RFC decides, that message has to change: if `Option` support is refused, the rule
should be stated in the error (see §6).

### Prior decisions this RFC has to respect

- **RFC-0079** (refused 2026-07-10) specified `?` on `Option` (then named `Perhaps`) in §6, with the same
  `None`-propagating desugaring proposed here, and deferred "`Option<T>` and `?` in
  `Result`-returning functions" as its Open Question 4. It was refused because most of the
  RFC was already implemented, not because of a design objection to this section. Its closing
  note lists "undocumented `?`-on-`Option`" as a remaining gap, but the spec is not
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
| `Option<T>` | `Option<U>` | `T` | `return None` (new) |
| anything else, or any other pairing | | | type error |

The return type decides which row applies. That matters for inference: an operand whose type
is still a variable when `?` is checked (a closure parameter, an un-annotated `let`) is
resolved by the return type, as it is today, instead of being ambiguous.

When the return type is itself still unresolved (a closure with no written return type), the
operand decides: if its constructor is already `Result` or `Option`, that fixes the return
type's constructor, and the matching rule then applies. If both are unresolved the error is
`T0002`, asking for an annotation. Outside any function or closure `?` stays `T0005`; every
mismatched pairing is `T0001` with the message in §6.

```metel
fun port(env_name: String) -> Option<u16> {
    let raw := get(env_name)?;           // Option<String>, in an Option-returning fn
    let n   := parse_u16(raw)?;          // Option<u16>
    Some { value = n }
}
```

`None` carries no payload, so there is no `From`/conversion step and no `E` to check: the
Option row has no error-type constraint.

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

### Nesting, early exit and scope

- **Nested types.** Each `?` strips one layer and checks it against the return type, so
  `Option<Result<T, E>>` and `Result<Option<T>, E>` need no transpose rule:

  ```metel
  fun first_port(names: List<String>) -> Option<u16> {
      let raw := names.first()?;               // Option<String>   -> String
      let n   := parse_u16(raw).ok()?;         // Result -> Option  -> u16
      Some { value = n }
  }
  ```
- **Early exit leaves the function.** `e?` in the tail of an inner block returns from the
  enclosing function or closure body, not from the block, exactly as for `Result`.
- **Drops and moves.** The `return None` path is an ordinary `return`: every binding live in
  scope is dropped or moved as it would be at an explicit `return`. A partially moved struct
  live at the `?` is handled by the existing rules; no new ownership rule is needed.

---

## 2. Why not allow mixed use

Two mixed cases are tempting. Neither is proposed.

### `Option` inside a `Result`-returning function

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

### `Result` inside an `Option`-returning function

`e?` would discard the error. Silently throwing an `Err` away is the opposite of what the
operator signals; `.ok()` makes the discard visible at the site (`parse(s).ok()?`).

---

## 3. Alternatives considered

1. **Status quo.** Keep `?` Result-only; fix only the diagnostic. Cheapest, but leaves
   `Option`-returning functions with no early-exit syntax, in a language where `Option` is
   the standard absence type. The cost is paid at every call site, the benefit is a smaller
   operator.
2. **A `Try` aspect** (Rust's `Try`/`FromResidual`, Swift/Kotlin-style generalisation). `?`
   would be defined over any type implementing the aspect, with `Result` and `Option` as
   the two impls and user types allowed. This is the principled end state, but it needs a
   residual/branch associated-type design, a story for how it composes with `From`, and it
   touches RFC-0008 object safety and RFC-0161's `Callable` question for closures. That is a
   large design to block a two-type feature on. The closed `{Result, Option}` rule here is
   the first two impls of such an aspect, so it does not prevent it (§8).
3. **Mixed conversion with a default error** (§2). Rejected above.
4. **A separate operator for `Option`** (e.g. `?!`). More surface, and it makes the author
   pick the operator by operand type, which the compiler already knows.

---

## 4. Interactions

- **Closures.** `?` returns from the nearest enclosing function or closure body. A closure
  with an `Option<U>` return can use it exactly as a `Result`-returning one can today.
  RFC-0153's `mutating` closures already state that an early exit is "a `?`-propagated
  `Err` or an early `return`" (`spec.functions.closures.dynamics-13`); that sentence widens to
  "`?`-propagated `Err` or `None`".
- **`main`.** `fun main() -> Option<()>` is not proposed here. RFC-0004 decides what `main`
  may return; if it adopts `Result`, it should also say whether `Option` is allowed.
- **Shadowing.** The checker currently builds the operand constraint from the spelling
  `"Result"` with no declaration id (`infer_propagate_error`). Since metel-core#1585 a module
  may shadow `Option`/`Result`, so an implementation must constrain against the *core*
  declarations by id, not by name; otherwise a module that declares its own `Result` breaks
  `?` on std values. This RFC's implementation must include that.
- **Error codes.** The Result row is unchanged for a missing `From` (`T0007`). `T0005` stays
  for `?` with no enclosing function or closure, and its message widens to name both return
  types. Every mismatched pairing (including `?` in a function returning neither) is `T0001`
  with the message in §6 and no inference variables. See §6.

---

## 5. Specification changes (on acceptance)

`reference/spec/functions.md`, "The ? Operator":

- **Legality Rule 1** now reads: the operand must be `Result<T, E>` or `Option<T>` and the
  enclosing return type must be the same type constructor; any other pairing is a type error.
  The prose sentence "`?` does not apply to `Option<T>` in this language version" is
  removed.
- **Legality Rule 2** (`From`) is scoped to the `Result` row.
- **New Dynamic Semantics 3:** evaluating `None?` returns `None` from the enclosing
  function; `Some { value }?` produces `value`.
- `spec.functions.closures.dynamics-13` adds `None`.

The current negative fixture `stage6_neg_05_error_propagation_non_result` (`42?`) stays valid
(an `i64` operand is neither type). A fixture asserting `Option` is *rejected* does not
exist today (the rule is covered only through `42?`), so there is no fixture to retire.

---

## 6. Diagnostics

Independent of the outcome (and the reason metel-core#1589 exists), `?` on a mismatched
pairing should say what the rule is, with no inference variables:

```
T0001: `?` on `Option<String>` needs the enclosing function to return `Option<_>`,
but it returns `Result<Config, ConfigError>`
  = help: turn the absence into an error first: `.ok_or(...)`
```

and the converse suggests `.ok()`. If this RFC is refused, the same message ships with the
sentence "`?` requires a `Result`" in place of the first line, so that closing it does not
leave #1589's complaint standing.

---

## Open Questions — resolved 2026-10-26

1. **Closed `{Result, Option}` rule or a `Try` aspect.** *Resolved: the closed rule.* It is the
   first two impls of a future `Try` aspect, so a later aspect is an additive generalisation.
   The accepted debt is that "`None` has no payload, so no conversion step" is fixed until then.
2. **Revisiting `Option`-in-`Result` with a conversion hook.** *Resolved: not now.* `ok_or` is
   one word at the site that knows the error. If real code repeats `ok_or(SameError)`, an
   `E2: From<NoneError>`-style impl is a strictly additive rule.
3. **Nested `Option`/`Result` (transpose).** *Resolved:* each `?` strips one layer; worked
   example in §1.
4. **Implicit-return position.** *Resolved:* `?` returns from the enclosing function or closure
   body, not the block; stated in §1 and in the new Dynamic Semantics.
5. **Move checking.** *Resolved:* `return None` is an ordinary `return`; no new rule. A fixture
   with a partially moved struct live at the `?` is part of the implementation.
6. **Error codes (added in review).** *Resolved:* mismatches are `T0001` with the §6 message;
   `T0005` only without an enclosing function; `T0007` for a missing `From`. §1 and §4 said
   `T0005` for the mismatch; that was wrong against the implementation.
7. **Closures without a written return type (added in review).** *Resolved:* the operand fixes
   the constructor when the return type is unresolved; both unresolved is `T0002`.

---

## References

- metel-core#1589 — the report this RFC answers (`?` on `Option` is a unification error).
- metel-core#1585 — made shadowing `Option`/`Result` safe; §4 depends on its id-based lookups.
- RFC-0079 — refused; §6 proposed the same `None` propagation, OQ4 the mixed case.
- RFC-0015 — unwrap syntax (`.yolo()` as a method); `?` as a compiler form.
- RFC-0004 — `main` return type.
- RFC-0153 — closure mutation axis (`dynamics-13`, early exit through `?`).
- `reference/spec/functions.md` — "The ? Operator".

---

## Decision

**Outcome:** accepted (2026-10-26).

`?` extends to `Option<T>` under one rule: the operand's type constructor must match the
enclosing function's. `None` propagates as `return None`. Mixed use is not added; the
diagnostic names `.ok_or(...)` and `.ok()`. Mismatches are `T0001`; an unresolved closure return
type is fixed by the operand. Closed `{Result, Option}` rule now; a `Try` aspect is a later,
additive generalisation. Implementation constrains against the core declarations by id (not the
spelling `"Result"`) so a shadowing module is safe.
