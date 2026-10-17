---
id: rfc-0179
title: "By-value open-row parameters take the whole record"
date: '2026-10-16'
status: accepted
updated: '2026-10-17'
tracking: 'https://github.com/metel-lang/metel-core/issues/1471'
---

> **Status — accepted (2026-10-17).** Accepted by the language owner (2026-10-17); implementation tracked in metel-core#1471

## Summary

A by-value parameter whose type has an open row tail (`{ x: f64, ..R }`, `Handle.{ fd, ..R }`)
owns the whole argument. The fields the parameter does not name are the callee's to move,
return or drop; they are not forgotten at the call boundary. This replaces RFC-0121 §4's rule
that by-value width subtyping is sound only when every unnamed field is `Copy`, and it makes
the inline spelling `{ f: T, ..Rest }` mean the same as the row equation
`{ ..R } where R = { f: T, ..Rest }`.

---

## Motivation

**Two spellings of one function disagree.** RFC-0121 §2 gives two ways to take a field off a
record and keep the rest. They are accepted or rejected differently:

```metel
// rejected today (T0033) when `Rest` holds a `String`
fun strip<row Rest>(d: { token: String, ..Rest }) -> { ..Rest } {
    let { token: _, ..rest } := d;
    rest
}

// accepted today, same meaning
fun strip<row R, row Rest>(d: { ..R }) -> { ..Rest } where R = { token: String, ..Rest } {
    let { token: _, ..rest } := d;
    rest
}
```

The equation form is accepted because a tail-only parameter `{ ..R }` is never narrowed: the
callee receives the whole record. The inline form is rejected because RFC-0121 §4 treats it as
narrowing at the call, which forgets the unnamed fields.

**What §4 was protecting, and what it costs.** RFC-0121 §4 chose this rule deliberately: reject a
by-value open row whose unnamed fields are not `Copy`, and require an explicit
`where R = { .., ..Rest }` decomposition instead. Besides soundness, that made discarding data
visible, because the author had to write the remainder down. This RFC gives that up for open-row
parameters. The alternatives section considers keeping the visibility by other means.

**The restriction protects against a problem the callee can already solve.** §4's reasoning is
that a forgotten non-`Copy` field has no owner left to drop it. If the callee owns the whole
argument, the owner exists: the callee. It can return the remainder, destructure it with a
remainder pattern, or let it drop at the end of its scope, as it can for any owned value.

**The restriction has a visible cost.** The `forgets field` error (`T0033`) fires on the most
natural generic signature, `fun get_x<row R>(p: { x: f64, ..R }) -> f64`, whenever a caller
passes a record with a `String` in it, and the only fix is to rewrite the signature in the
equation form.

---

## 1. Design

### 1.1 The rule

For a by-value parameter whose declared type is an open record (`{ f₁: T₁, …, ..R }`) or an
open projection (`Handle.{ f₁, …, ..R }`):

- the argument is moved into the parameter whole;
- inside the body the parameter has the named fields at their declared types and the
  remainder as an owned row `R`;
- the callee owns the fields `R` carries: it may move them out (a remainder pattern
  `..rest`, a spread `{ ..d }`, a return), pass the parameter on by value, or leave them to be
  dropped when the parameter goes out of scope.

The call site needs only that the argument has at least the named fields with matching types.
There is no `Copy` condition on the remainder. The unnamed fields drop with the parameter, in the
same order as any other record (declaration order, as RFC-0071's drop order settles it, #261).

`T0033` is no longer raised for by-value open-row parameters, neither at a concrete call nor when
a generic body forwards its open-row parameter to another by-value open-row function. It keeps
its other use, spreading a record through a reference when its fields are not all `Copy`, and its
documentation is retitled for that rule alone.

### 1.2 Equivalence with the equation form

`{ f: T, ..R }` in a by-value parameter position is defined as `{ ..S }` with the equation
`S = { f: T, ..R }`. Both spellings then accept and reject the same programs. An anonymous
tail (`{ x: f64, .. }`) is the same with a fresh tail name the body cannot mention; the
callee still owns, and drops, what it cannot name.

### 1.3 Positions that do not change

- A reference parameter, `&{ x, ..R }` or `&var { x, ..R }`, never owns the value, forgets
  nothing, and has no `Copy` restriction. This is unchanged.
- Returning or constructing a record from the remainder is unchanged (RFC-0178).
- The rule covers declared functions, methods and closure parameters, where the enclosing
  construct solves the open-row tail; the closure owns the whole argument just as a function
  does. What an anonymous open-row tail means in a return type or a written function type is
  settled by RFC-0181: those positions stay unsupported and report `T0032`.
- A record whose fields are all `Copy` is itself `Copy`, so passing it is a copy and the caller
  keeps its value. The whole-record rule changes nothing there; it matters only for a record with
  a non-`Copy` field.
- `where all R: Copy` keeps its job of letting a body use the row more than once
  (`copy_twice` in RFC-0123). It is no longer needed just to pass the whole parameter on to
  another by-value open-row function.

### 1.4 Generic bodies

An abstract remainder `R` inside a generic body is owned by the body, so passing the whole
parameter to a by-value open-row function (`keep_x(value)` in a `<row R>` function) needs no
bound. The abstract-body rejection that RFC-0121 Open Question 1 tied to RFC-0123 goes away
for this case.

### 1.5 Soundness condition

The rule is sound while every field can be dropped without an obligation. That holds for every
type the language has today. Two situations need care and are left to the RFCs that introduce
them, not decided here:

- **Linear records (RFC-0091).** A linear field must be used exactly once, so a callee generic
  over an unknown remainder cannot drop it. Once linear fields exist, an open-row parameter
  over a remainder that may contain one must be required to consume or return the remainder.
- **Types with a `Drop` impl (RFC-0137 §5, #949).** A by-value parameter whose type is a nominal
  residual of a brand that has a `Drop` impl, such as `Handle.{ fd, ..R }`, receives the whole
  `Handle`, and dropping it needs drop dispatch against a narrowed residual, which is not
  implemented. Until it is, such a parameter is rejected with a diagnostic of its own, a new error
  code allocated at implementation, whose message names `Drop` and #949: "passing `Handle` by value
  to an open row parameter would drop a narrowed `Handle.{ fd }`; drop dispatch against a narrowed
  residual is not implemented (RFC-0137 §5, #949)". A plain record that only contains a `Drop`
  value in its remainder is not affected, because dropping a whole value is ordinary. Today a
  `Drop` impl can only be empty (non-empty bodies are rejected until #261), so this restriction
  guards a behaviour that is not yet observable.

---

## 2. Costs

- **A ratified decision is reversed, and a visibility property is lost.** RFC-0121 §4 settled
  by-value width subtyping on 2026-09-27 and recorded no precedent either way. This RFC changes
  it because the §4 rule forbids what the callee-owns model already makes sound and leaves the
  inline and equation spellings disagreeing. The cost is that a function can now discard a
  non-`Copy` remainder without the signature saying so; see the alternative below.
- **Drop timing becomes observable.** The unnamed fields now drop at the end of the callee's
  scope, not at the caller. That is not visible until destructors run (#261), and it should be
  stated in the spec when they do.
- **Strictly a relaxation.** No program accepted today is rejected. Programs rejected with
  `T0033` become accepted. The spec's `get_x(wide)` expect-fail example and the matching
  fixtures change.

## 3. Alternatives considered

- **Keep RFC-0121 §4 as written.** Safe, and it keeps discards visible, but it leaves the two
  spellings disagreeing and forces the longer equation form for the most natural generic
  signature.
- **Keep narrowing but drop the extras at the call site.** The extras' drop happens in the
  caller, where the callee cannot see or return them, and the inline and equation spellings
  still disagree.
- **Allow it, but require an explicit discard.** The whole-record rule as designed here, plus a
  required `drop(rest)` or `let _ := rest` when a named tail is never used. It keeps §4's
  visibility without its restriction. It needs explicit `drop` (#261) first, and it can be added
  later as a lint or an error without changing anything this RFC decides, so this RFC does not
  mark discards. It is noted on #261 so that it is not lost.
- **Accept a signature heuristic.** An earlier attempt skipped the check when the tail also
  appeared in the return type (metel-core#1470, closed). It guesses at whether the callee
  returns the remainder and needed a patch for two parameters sharing a tail. It does not
  address that the inline form narrows and the equation form does not.

## 4. Changes to existing documents on acceptance

- RFC-0121 §4 and Open Question 1: replace the by-value rule with §1.1, and keep the
  reference-position paragraph.
- `reference/spec/types.md`, `spec.types.generics.open-rows.legality-3` and the width-subtyping
  examples: rewrite for the whole-record rule; the `get_x(wide)` example becomes a passing one.
- `reference/error-codes.md`: `T0033` loses the by-value case and is retitled for the
  spread-through-reference rule; the `Drop`-brand restriction gets a new entry (the next free code
  is `T0036`).
- Fixtures: the `T0033` by-value fixtures and the `where all R: Copy` narrowing fixtures change
  or are removed; new fixtures cover the inline-versus-equation agreement and a callee that
  drops, returns and destructures the remainder.

---

## Open Questions

None.

## References

- RFC-0121 §2, §4 and Open Question 1 — the rule this replaces.
- RFC-0137 §5 — drop dispatch against a narrowed residual.
- RFC-0123 — field-wise row constraints (`all R: A`).
- RFC-0178 — row remainder construction.
- RFC-0091 — linear records.
- metel-core#1469, #1471 (the issue and design question), #1470 (the closed signature heuristic),
  #949 (drop dispatch), #261 (explicit drop).

---

## Decision

**Outcome:** **Accepted** (2026-10-17). A by-value open-row parameter owns the whole argument; `T0033` keeps only the spread-through-reference rule; a by-value parameter over a `Drop`-brand residual is rejected with its own code until #949. No open question remained. Implementation is metel-core#1471 (v0.14.0).
