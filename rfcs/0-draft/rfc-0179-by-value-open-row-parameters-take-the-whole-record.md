---
id: rfc-0179
title: "By-value open-row parameters take the whole record"
date: '2026-10-16'
status: draft
---

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

**RFC-0121 §4 and RFC-0137 disagree about the call boundary.** RFC-0137 states that a caller
must match a parameter's row exactly and that there is no implicit truncation at the call
boundary; narrowing happens only through an explicit move or projection. RFC-0121 §4's
by-value width subtyping is an implicit truncation at exactly that boundary, and it needs a
`Copy` rule to stay sound only because the fields are forgotten there.

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
There is no `Copy` condition on the remainder, and `T0033` is no longer raised for by-value
open-row parameters.

### 1.2 Equivalence with the equation form

`{ f: T, ..R }` in a by-value parameter position is defined as `{ ..S }` with the equation
`S = { f: T, ..R }`. Both spellings then accept and reject the same programs. An anonymous
tail (`{ x: f64, .. }`) is the same with a fresh tail name the body cannot mention; the
callee still owns, and drops, what it cannot name.

### 1.3 Positions that do not change

- A reference parameter, `&{ x, ..R }` or `&var { x, ..R }`, never owns the value, forgets
  nothing, and has no `Copy` restriction. This is unchanged.
- Returning or constructing a record from the remainder is unchanged (RFC-0178).
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
- **Types with a `Drop` impl (RFC-0137 §5, #949).** A projection-tailed parameter such as
  `Handle.{ fd, ..R }` receives the whole `Handle`, and dropping it needs drop dispatch against
  a narrowed residual, which is not implemented. Until it is, a projection-tailed by-value
  parameter whose brand implements `Drop` keeps being rejected, with a message that says why.

---

## 2. Costs

- **A ratified decision is reversed.** RFC-0121 §4 settled by-value width subtyping on
  2026-09-27 and recorded no precedent either way. This RFC changes it because the §4 rule
  forbids what the callee-owns model already makes sound, and because it contradicts RFC-0137.
- **Drop timing becomes observable.** The unnamed fields now drop at the end of the callee's
  scope, not at the caller. That is not visible until destructors run (#261), and it should be
  stated in the spec when they do.
- **Strictly a relaxation.** No program accepted today is rejected. Programs rejected with
  `T0033` become accepted. The spec's `get_x(wide)` expect-fail example and the matching
  fixtures change.

## 3. Alternatives considered

- **Keep RFC-0121 §4 as written.** Safe, but it leaves the two spellings disagreeing and keeps
  the implicit truncation that RFC-0137 rules out.
- **Keep narrowing but drop the extras at the call site.** It makes the extras' drop explicit,
  but the drop happens in the caller where the callee cannot see or return them, and it keeps
  the implicit truncation.
- **Accept a signature heuristic.** An earlier attempt skipped the check when the tail also
  appeared in the return type (metel-core#1470, closed). It guesses at whether the callee
  returns the remainder and needed a patch for two parameters sharing a tail. It does not
  address that the inline form narrows and the equation form does not.

## 4. Changes to existing documents on acceptance

- RFC-0121 §4 and Open Question 1: replace the by-value rule with §1.1, and keep the
  reference-position paragraph.
- `reference/spec/types.md`, `spec.types.generics.open-rows.legality-3` and the width-subtyping
  examples: rewrite for the whole-record rule; the `get_x(wide)` example becomes a passing one.
- `reference/error-codes.md`: `T0033` loses the by-value case.
- Fixtures: the `T0033` by-value fixtures and the `where all R: Copy` narrowing fixtures change
  or are removed; new fixtures cover the inline-versus-equation agreement and a callee that
  drops, returns and destructures the remainder.

---

## Open Questions

1. **How is dropping the remainder written when explicit drop exists?** An open-row parameter
   that deliberately discards its remainder reads the same as one that forgot it. Explicit
   `drop` is #261; whether a lint or a required `drop(rest)` is wanted is open.
2. **Does the Drop-impl restriction in §1.5 need its own diagnostic code?** Today it would
   reuse the existing message path; a dedicated one may be clearer once #949 is scheduled.

## References

- RFC-0121 §2, §4 and Open Question 1 — the rule this replaces.
- RFC-0137 — branded rows, the call-boundary rule, and drop dispatch against a residual (§5).
- RFC-0123 — field-wise row constraints (`all R: A`).
- RFC-0178 — row remainder construction.
- RFC-0091 — linear records.
- metel-core#1469, #1471 (the issue and design question), #1470 (the closed signature heuristic),
  #949 (drop dispatch), #261 (explicit drop).

---

## Decision

**Outcome:** *(pending)*
