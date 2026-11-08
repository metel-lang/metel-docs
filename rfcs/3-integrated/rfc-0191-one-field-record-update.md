---
id: rfc-0191
title: "One-Field Record Update"
date: '2026-10-29'
status: integrated
updated: '2026-11-08'
tracking: 'https://github.com/metel-lang/metel-core/issues/1663'
coverage:
  "1": { kind: blocked, reason: "The replacement rule is not implemented until the checker gains the presence query.", ref: "metel-core#1663" }
  "2": { kind: blocked, reason: "The interactions become fixtures of the implementation.", ref: "metel-core#1663" }
impl_tracking: 'https://github.com/metel-lang/metel-core/issues/1663'
impl_status: not-started
---

> **Status — under review (2026-10-29).** design drafted; tracked by metel-core#1663 (Records and surface syntax); one open question (replacement marker)

> **Status — accepted (2026-11-08).** Reviewed 2026-11-07: no marker at the site; examples in the dotted spelling and = assignment; replaced fields must be Discard (effective with linear); named records re-brand with Type(..{ ..r, .x = 5 }) and Type(..r, x = 5) stays an error in v0.16.0.

> **Status — integrated (2026-11-08).** Integrated 2026-11-07: spec open-rows legality-4 states addition, replacement and rejection (blocked-exempt on metel-core#1663); worked examples and sibling cross-check recorded.

## Summary

A record literal that spreads a record may also **replace** one of its fields, when the checker
can see that the field is present and the replacement has the field's type.

```metel
let s := { .a = 1, .b = 2 };
let t := { ..s, .a = 10 };       // { .a: i64, .b: i64 }: today T0012
```

Spread stays additive for an absent label (RFC-0178 §2, unchanged). A written label that is
**known present** in the spread's row becomes a replacement; a label that is neither known
present nor known absent stays `T0012`. The result type is the spread's type: a replacement
never changes a field's type and never changes the set of fields.

This amends RFC-0178 §2 ("no override") and its alternative 5. It adds no syntax.

---

## Motivation

There is no expression meaning "this record, with `a` replaced". Found while writing
record-heavy examples (metel-core#1640):

```metel
let u := { .a = 10, ..s };       // T0012: record spread already contains field `.a`
```

The two ways around it today are both worse than the one-expression form every other
language with record literals has:

- **Assign through a `var`.** `var t := s; t.a = 10;` turns an expression into two
  statements and forces a `var` binding for a value that is never mutated again.
- **Destructure and rebuild.** `let { .a: _, ..rest } := s; { ..rest, .a = 10 }`. On an open row
  this also needs the removal to be provable (`R: { .a, .. }`, or an equation), which the
  replacement does not conceptually need: it is replacing a field it already knows is there.

The case is common in functional style (a pipeline step returns its input with one field
changed) and in the typestate code RFC-0178 was written for (a step that changes a counter or
a status but not the row).

### Why RFC-0178 refused it, and what that leaves

RFC-0178 rejected "spread with override, last wins" because it "breaks the row invariant that
a label occurs once, and would make the literal's type depend on whether a label was present,
undecidable for an abstract row without a presence fact". Both objections are about the
**unrestricted** form, where the written label may be present or absent and the result differs.

Two restrictions remove them:

1. **The label must be known present** (entailed by a concrete row, a row bound, or an
   equation, the same facts RFC-0178 already reads for absence). Then "present or absent" is
   never undecided: it is proven, or the literal is rejected as before.
2. **The replacement has the field's type.** Then the literal's row is the spread's row, so the
   one-occurrence invariant holds trivially and the type does not depend on the replacement.

---

## 1. The rule

In a record literal with a spread `..e` (RFC-0178 §2), each written label `x = v` is judged
against the spread's row, in this order:

| the spread's row | `x = v` means | result row |
|---|---|---|
| proves `x` **absent** | an added field (RFC-0178, unchanged) | spread row plus `x: typeof(v)` |
| proves `x` **present**, with type `T` | a **replacement** | the spread row, unchanged |
| proves neither | rejected, `T0012`, naming the label and the missing fact | none |

A replacement requires `typeof(v)` to be `T`, by the same unification any field initializer
uses. A different type is a type mismatch against `T` (`T0001`), not a retyping.

```metel
fun discount<record R: { .price: i64, .. }>(line: { ..R }) -> { ..R } {
    { ..line, .price = line.price * 9 / 10 }      // price known present: replacement
}

fun priced<record R: !{ .price }>(line: { ..R }) -> { ..R, .price: i64 } {
    { ..line, .price = 100 }                      // price known absent: addition
}
```

Position is not significant: `{ .price = 0, ..line }` and `{ ..line, .price = 0 }` are the same
literal, as for every other initializer. At most one spread per literal still holds
(`GAP-TYPES-008`); several written labels may each be additions or replacements independently.

### Evaluation and ownership

Initializers evaluate left to right as written (RFC-0178 §2) and the ordinary move rules apply
to them; the update adds one rule, about the replaced field.

- **The replaced field is not moved into the result.** Spreading an owned record moves every
  field except the replaced ones; each replaced field's old value is dropped, as the old value
  of an assignment is. A replaced field with a `Drop` impl therefore runs its destructor, the
  same as `s.a = v` on an owned place.
- **The right-hand side may read the source like any other initializer.** After the spread has
  consumed `line`, reading a `Copy` field is accepted (`{ ..line, .total = line.price * 2 }`
  runs today) and reading a non-`Copy` field is a use of a moved value (`T0019`). The discount
  example above reads `line.price`, a `Copy` field, so it is accepted.
- **Spreading through a reference** requires every field of the spread's row **that is not
  replaced** to be `Copy` (RFC-0178 §2, narrowed by the replaced labels). A replaced field is
  never copied out, so it need not be `Copy`.
- **Discard (decided 2026-11-07).** A replaced field's old value is dropped, so when the spread record is not known `Discard`
  (RFC-0089: a linear record, or one holding a parameter-dependent field) every replaced field must itself be `Discard`;
  replacing a linear field is an error, as assigning to one is. This takes effect with the `linear` release: every type is `Discard` in
  v0.16.0. The destructor of a replaced `Drop` field runs when destructor invocation is implemented (LIMIT-EVALUATION-005, #261).

### Records only

As in RFC-0178 the rule is for anonymous records and nominal `record`s. The result is the
spread's row, **anonymous**: the brand is not carried (RFC-0178, "No re-branding"). A function that
must return a branded value reconstructs it through its constructor (RFC-0178 §3): for a named record, `Type(..{ ..r, .x = 5 })`
(RFC-0100's spread, alone). The call form takes no replacement itself: `Type(..r, x = 5)` stays an error in v0.16.0 (decided
2026-11-07), and extending it with this rule is a small additive change later.

`struct` has no spread today (`P { ..s, a = 10 }` is a parse error) because its row is private
to its module. This RFC does not change that; an update form for `struct` would be a member
function the module writes, not a language feature.

---

## 2. Interactions

- **RFC-0178 §2.** The "no override" sentence is replaced by the table above. Alternative 5 is
  amended: the unrestricted form stays rejected; this RFC is the restricted subset.
- **RFC-0173 (rigid generic parameters).** No row is unified with another. Presence and the field's type
  are read from the same declared bounds and equations as absence; nothing is inferred.
- **RFC-0189 (negative row bounds).** `!x` proves absence (an addition); `x`, `x: T` prove
  presence. A bound with neither leaves `x` undetermined and the literal is rejected as before.
- **RFC-0221 (dotted labels, integrated).** A field of an anonymous record is `.a`; the examples use that spelling. The rule is
  independent of it.
- **Field assignment.** `s.a = v` on an owned `var` place is unchanged and still the way to
  mutate in place. The update form builds a new record and does not require `var`.
- **RFC-0117 / RFC-0137 (narrowing).** The result is a fresh anonymous record; no narrowing
  state carries over from the spread source.

---

## Alternatives Considered

1. **Status quo (document destructure-and-rebuild).** Zero language change. Rejected as the end
   state because the idiom needs a provable removal on open rows, and for a concrete record it
   restates every other field.
2. **A distinct update form (`s.with { a = e }`, `s with { a = e }`, `{ s | a = e }`).** Keeps
   spread purely additive and makes the replacement visible at the site. Costs a new keyword or
   sigil for something the literal already almost says, and a second place the row-fact
   machinery must be wired (the update needs the same presence entailment). See Open question.
3. **Spread with override, last wins (JS/Elm), unrestricted.** Rejected by RFC-0178 and still: the
   literal's type would depend on presence, and a typo'd label silently adds a field.
4. **Type-changing update** (`{ ..s, .a = "x" }` where `.a: i64`, result has `.a: String`). It makes
   the result row differ from the spread's for abstract rows (`R` would no longer be the
   remainder). Rejected here; it is a separate feature if wanted, and needs removal plus
   addition, which RFC-0178 already composes (`let { .a: _, ..rest } := s; { ..rest, .a = "x" }`).
5. **Replacement only for a place (`s.{ a = e }` as a copy-modify of `s`).** Reads as a view
   (RFC-0178 alternative 2) and cannot consume a temporary.

---

## Open question

**Should a replacement be marked at the site?** *Resolved 2026-11-07 (language owner): no marker.* `{ ..s, .a = e }` is an addition or a
replacement depending on `typeof(s)`, as in Elm, OCaml, JS and Rust record update. The risk (a reader cannot tell which from the literal, and a type
change to `s` can turn one into the other) is limited: the result always contains `.a`, a retyping is rejected, and a wrong guess is a type error, never
silent misbehaviour, except for a `Drop` field replaced instead of kept. A marker (`x := e`, `x <- e`) was rejected: RFC-0183 narrowed `:=` to introduction, and a new
initializer operator is a larger decision than the problem warrants.

---

## Worked examples (integration, 2026-11-07)

They become fixtures of the implementation (metel-core#1663); a hit means a contradiction.

```metel
let s := { .a = 1, .b = 2 };
let t := { ..s, .a = 10 };                                  // replacement: row { .a: i64, .b: i64 }
let u := { .a = 10, ..s };                                  // the same literal, position is free
fun discount<record R: { .price: i64, .. }>(line: { ..R }) -> { ..R } { { ..line, .price = line.price * 9 / 10 } }
fun priced<record R: !{ .price }>(line: { ..R }) -> { ..R, .price: i64 } { { ..line, .price = 100 } }   // addition
let p := Point(..{ ..r, .x = 5 });                          // a named record: RFC-0100's spread, alone
```

1. **Rejections.** `{ ..s, .c = 1 }` where `s`'s row proves neither `.c` present nor absent (an open row with no fact) is `T0012`; `{ ..s, .a = "x" }` where
   `.a: i64` is `T0001`; two spreads stay `GAP-TYPES-008`.
2. **Ownership.** Spreading an owned `s` moves every field but `.a` and drops the old `.a`; reading a `Copy` field after the spread is accepted and a non-`Copy` field is `T0019`;
   spreading `*r` needs every non-replaced field `Copy` (`T0033` otherwise).
3. **Siblings.** Presence facts come from a concrete row, `{ .a, .. }` or `{ .a: T, .. }`; absence facts from `!{ .a }` or RFC-0189's `!.a` entry. `Type(..r, x = 5)` stays an error (RFC-0100).

Exit check: no contradiction with the integrated spec (open rows, spread, move and drop) or with RFC-0189, RFC-0221 and RFC-0100.

---

## Specification impact

Spec text lands only at `3-integrated`. `reference/spec/types.md` (anonymous records, "collisions
do not override") and `reference/spec/expressions.md` (record literal typing) change; the
`T0012` case "present in the spread" splits into the table's three rows. No new error code: a
retyped replacement is `T0001`, an undetermined label stays `T0012`, a non-`Copy` field read
through a reference stays `T0033`.

## Implementation notes

- Checker: the spread arm of record-literal inference already queries the row for absence; it
  gains a presence-and-type query on the same facts and chooses addition or replacement per
  label. No new inference.
- Runtime: build the record from the spread's fields minus the replaced labels, plus the written
  ones; the replaced values are dropped in the order the fields appear in the row.
- Compiled profile: layout is the spread's layout; a replacement is an in-place store into the
  moved record.

## References

- RFC-0178 (Row Remainder Construction), §2 and alternative 5: the rule this amends.
- RFC-0173 (Generic bodies are checked against their declared bounds): why presence is a stated fact.
- RFC-0189 (Per-Label Negative Row Bounds): the absence facts.
- RFC-0183: the meaning of `:=`, relevant to the marker alternative.
- metel-core#1640: the report.

---

## Decision

**Outcome:** *(pending)*
