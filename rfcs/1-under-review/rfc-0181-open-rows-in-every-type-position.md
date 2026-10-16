---
id: rfc-0181
title: "Anonymous open rows in return and function types"
date: '2026-10-16'
status: under-review
updated: '2026-10-16'
tracking: 'https://github.com/metel-lang/metel-core/issues/1480'
---

> **Status — under review (2026-10-16).** Opened for review; split out of RFC-0179 open question 3.

## Summary

An open record with an anonymous tail (`{ x: i64, .. }`) is accepted as a function or method
parameter, a `let` or `var` annotation, a closure parameter and a type alias right-hand side
(metel-core#1478; `spec.types.generics.open-rows.legality-5`). This RFC decides the positions
where it is not: a **return type** and a **written function type** keep reporting `T0032`. It
records why, what to write instead, and what would make us reopen the question.

---

## Motivation

The table is the state after #1478:

| position | anonymous tail | named tail |
|---|---|---|
| function / method parameter | works (implicit row parameter of the signature) | works |
| `let` / `var` annotation | works (inference variable) | works |
| closure parameter | works (generalized with the closure) | cannot be declared |
| return type | `T0032` | works when `R` comes from a parameter |
| written function type | `T0032` | works |
| record or struct field | `T0032` | works (`record W<row R> { d: { x: i64, ..R } }`) |
| type alias | works (each use is its own fresh row) | works |

The three unsupported anonymous cases look like gaps, and two needs are plausible behind them: a
function that returns an open record with no row input (a factory), and a callback that accepts
any wider record. This RFC checks each against what the language already does.

---

## 1. Decisions

### 1.1 Return types: keep `T0032`

An anonymous tail in a return type would be an **existential**: the callee chooses the row and
the caller sees `{ x: i64, ..? }` with an extra row it cannot name. The factory case does not need
it:

- A private function can omit its return type, and the **exact** record is inferred: the caller
  reads every field, which is strictly more than an existential gives.
- A public function must write a return type (`T0010`), and can write the concrete record in
  full: `-> { x: i64, y: i64 }`.
- A function whose row comes from an argument names it: `-> { x: i64, ..R }`.

What an existential would add is **hiding the extra fields from callers**, an API-abstraction
feature with no demonstrated demand. The `T0032` message for a return type should say what to do:
omit the type, write the record in full, or name a row parameter that comes from an argument. It
should not suggest a row parameter alone, which is impossible for a function with no row input.

### 1.2 Written function types: keep `T0032`

An anonymous tail in `|{ x: i64, .. }| -> i64` has two readings. As a fresh row of the enclosing
signature (rank-1), the callee cannot call the function on its own records, because the row is
the caller's choice. As "accepts every wider record" (rank-2), it needs higher-rank checking.

A named row already covers a callback over records of one shape, which is the common case:
`fun apply<row R>(f: |{ x: i64, ..R }| -> i64, a: { x: i64, ..R }, b: { x: i64, ..R }) -> i64`
type-checks and runs. A callee that must apply one callback to **differently shaped** records
it holds can take two callbacks, or be generic over two rows. A closure with an open-row
parameter already generalizes, so a rank-2 *value* exists; only the written *type* of one does not.

### 1.3 Fields: keep `T0032`

An anonymous tail in a struct or record field would make the field's type existential, so two
values of one nominal type could hide different rows. That does not fit a nominal type. A record
with a row parameter, `record W<row R> { d: { x: i64, ..R } }`, covers the use.

### 1.4 Aliases: unchanged

`type P := { x: i64, .. };` is accepted and each use is its own fresh row, exactly as writing the
open record at the use. In a return type or function type it reports `T0032` like the written form.

---

## 2. What reversing a decision would take

- **An existential return** needs an opaque, rigid remainder carried through the caller's inference
  that unifies with nothing, a distinct type per call site, and a rule for storing such a value in a
  collection or a tuple. RFC-0179 gives the caller the whole record, so soundness is not the
  obstacle; the cost is in the checker.
- **A rank-2 function type** needs higher-rank checking for a body that calls a parameter of that
  type, which Metel has no other use for today.

## 3. When to reopen

- A real API that must **hide** a record's extra fields from its callers (existential return).
- A real function that must apply **one callback to two row shapes** it holds itself, where two
  callbacks or two rows are not acceptable (rank-2 function type).

## 4. Changes on acceptance

- The three deferred features are recorded as language gaps, with inline markers in the Open rows
  section of the spec: GAP-TYPES-010 (an existential return), GAP-TYPES-011 (a written function type
  over any wider record) and GAP-TYPES-012 (an open-record field). Each is `accepted`, with the
  reopening trigger from §3 as its review condition.
- The `T0032` message for a return type lists the alternatives in §1.1 (metel-core#1484).
- Nothing else: `reference/error-codes.md` and `spec.types.generics.open-rows.legality-5` already
  state the supported and unsupported positions.

---

## Open Questions

None.

## References

- RFC-0121 §1 and §5 — row parameters and the grammar of row tails.
- RFC-0179 — by-value open-row parameters take the whole record.
- RFC-0160 — type aliases.
- `reference/error-codes.md`, `T0032`; `reference/spec/types.md`, `legality-5`.
- `architecture/gaps/`: GAP-TYPES-010, GAP-TYPES-011, GAP-TYPES-012.
- metel-core#1478 — the change that made annotations and closure parameters work.
- metel-core#1480 — this RFC's tracker.

---

## Decision

**Outcome:** *(pending)*
