---
id: rfc-0181
title: "Open rows in every type position"
date: '2026-10-16'
status: draft
---

## Summary

Settle what an open-row tail means in the positions where it is not yet supported: a return
type and a written function type. An open record with an anonymous tail (`{ x: i64, .. }`) now
works as a function or method parameter, a `let` or `var` annotation, and a closure parameter
(metel-core#1478). Those are the positions where the tail is a fresh variable the enclosing
construct can solve for. In a return type and in a function type the tail has no obvious
solver, so those positions report `T0032` and are owned by this RFC.

---

## Motivation

An open record can be written with a named tail (`{ x: i64, ..R }`, `R` declared `row`) or an
anonymous one (`{ x: i64, .. }`). The sibling anonymous splice `Session<..>` already works in all
of these positions. For an open record, the table below is the state after #1478:

| position | anonymous tail | named tail |
|---|---|---|
| function / method parameter | works (implicit row parameter of the signature) | works |
| `let` / `var` annotation | works (inference variable) | works |
| closure parameter | works (generalized with the closure) | cannot be declared |
| return type | `T0032` | works when `R` comes from a parameter |
| written function type | `T0032` | works |
| record or struct field | `T0032` | works (`record W<row R> { d: { x: i64, ..R } }`) |
| type alias | works (each use is its own fresh row, as a parameter) | works |

Two gaps follow, and both are real needs:

- **A function that returns an open record with no row input.** `fun make() -> { x: i64, .. }`
  has no parameter for `R` to come from, so a named tail cannot be written. This is the factory
  case.
- **A callback over open records.** `fun each(f: |{ x: i64, .. }| -> i64)` reads naturally as
  "any function that accepts a record with at least `x`", and the callee wants to call `f` on
  records of its own.

Neither has an unambiguous meaning, which is why they report `T0032` instead of guessing.

---

## 1. Open design questions

### 1.1 Return types

An anonymous tail in a return type is an **existential**: the callee chooses the row, and the
caller sees `{ x: i64, ..?}` with an extra row it cannot name. The caller can read `x`, and
pass the value to a by-value open-row parameter. With RFC-0179 the caller owns the whole record
and the extra fields drop with it, so the existential is sound without an extra bound. It is
the record analogue of `-> impl Aspect`.

*Proposal.* Accept it, checking that the body's returned record has at least the named fields,
and treating the remainder as opaque at the call site.

### 1.2 Written function types

An anonymous tail in `|{ x: i64, .. }| -> i64` has two readings:

- **Rank-1:** a fresh row parameter of the enclosing signature. It is consistent with how an
  anonymous tail in a parameter works, but the body cannot call `f` on its own records, because
  the row is the caller's choice. It is accepted by the checker and nearly useless.
- **Rank-2:** the function accepts every wider record. This is what the callback case wants.
  Metel's closures are let-polymorphic, so a closure with an open-row parameter is already a
  value of this kind. Checking a body that calls a parameter of such a type needs higher-rank
  handling.

*Proposal.* Keep rejecting an anonymous tail in a function type until a use case needs rank-2.
A named tail stays rank-1 as today.

### 1.3 Fields

An anonymous tail in a struct or record field would make the field's type existential, so two
values of the same record type could hide different rows. That does not fit a nominal type.
*Proposal.* Keep `T0032`; `record W<row R> { d: { x: i64, ..R } }` covers the use.

### 1.4 Aliases

`type P := { x: i64, .. };` is accepted and each use freshens its own row, exactly like writing
the open record at the use. *Proposal.* Keep this; document it.

---

## 2. Costs

- **Existential returns need an opaque row at the call site.** The checker must carry a rigid
  remainder through the caller's inference without letting it unify with anything.
- **Rank-2 function types** need higher-rank checking for the callee's body, which Metel has no
  other use for today.

## 3. Alternatives considered

- **Never allow an anonymous tail outside a parameter.** Simplest, but #1478 already allows it in
  annotations and closure parameters, where it is unambiguous and useful.
- **Allow rank-1 in function types now.** Consistent, but it accepts types whose only usable
  values are trivial.

---

## Open Questions

1. **Should a factory function with an existential return be allowed at all, or is `impl`-style
   opacity enough?** The existential is useful but is the largest piece of work here.
2. **Is a rank-2 function type worth the checking cost**, given that closures already generalize?
3. **What is the diagnostic when a record with an anonymous tail is stored** in a collection or
   returned inside a tuple? The existential would propagate; it needs a rule.

## References

- RFC-0121 §1 and §5 — row parameters and the grammar of row tails.
- RFC-0179 — by-value open-row parameters take the whole record (it makes the existential sound).
- RFC-0160 — type aliases.
- `reference/error-codes.md`, `T0032`.
- metel-core#1478 — the change that made annotations and closure parameters work and left these
  positions reporting `T0032`.

---

## Decision

**Outcome:** *(pending)*
