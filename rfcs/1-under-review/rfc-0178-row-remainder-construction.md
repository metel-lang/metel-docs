---
id: rfc-0178
title: "Row Remainder Construction"
date: '2026-10-06'
status: under-review
updated: '2026-10-06'
tracking: 'https://github.com/metel-lang/metel-core/issues/1399'
---

> **Status — under review (2026-10-06).**

## Summary

Open rows (RFC-0121) let a signature name *the rest* of a record, and a `where` equation
(`R = { token: Token, ..Rest }`) names what is left after removing a field. Nothing in the
language lets a generic **body** produce or consume a value of that remainder. This RFC
adds the two missing value-level forms, each the mirror of a form that already exists at
the type level:

- a **rest pattern** that binds the unnamed remainder of a record — `{ token, ..rest }` —
  which moves the named fields out and gives the rest an owner;
- a **row spread** in a record literal that places a record's fields into a new one —
  `{ ..rest, auth = a }`.

With both, the typestate step that RFC-0121 §3 uses as its motivating example can be
written:

```metel
extend<row R, row Rest> Session<..R> where R = { token: Token, ..Rest } {
    fun authenticate(self) -> Session<..Rest> {
        let { token: _, ..rest } := self.data;      // rest : { ..Rest }
        Session { id = self.id, data = rest }
    }
}
```

Today that body cannot be written; the only fixture for the signature guards it with
`panic`.

---

## Motivation

RFC-0121 §2 chose "extension is a literal, removal is a decomposition": the new label goes
in the row literal, and removal is stated by an equation that names both halves. That
settled the *types*. It left the body as `{ ... }`.

Every attempt to fill the body fails at present (metel-core#1399):

- Building the result from the whole, `Session { id = self.id, data = self.data }`, is
  rejected. Declared parameters are rigid (RFC-0173), so `{ token: Token, ..Rest }` is not
  `{ ..Rest }`, and no coercion removes a field.
- Writing a removed label back (`value.data.token := ...`) is rejected by design: a
  remainder cannot regain a label by assignment inside the generic definition.
- There is no value-level spelling of "this record without `token`". A record pattern's
  bare `..` discards the rest rather than binding it, and a record literal has no
  `..`-form at all (`{ ..p, id = 1 }` is a parse error), even though the same tail is
  written freely in a record *type* (`{ ..R, id: i64 }`).

The consequence is that the headline use of open rows — typestate over a row, where a step
consumes a field and returns the session at a smaller row — is expressible in its
signature and inexpressible in its implementation. The symmetric operation, extending a
record by a field inside a generic body (`{ ..R, auth: String }` as a *value*), has the
same gap. Concrete rows are unaffected: with known fields a literal can be rebuilt by
hand. The problem exists only for an abstract row, where the fields are not nameable.

### Why it needs a design, not a patch

Ownership makes this more than a syntax gap. The remainder is not a view: when
`token` leaves a record, the other fields must still have exactly one owner, and the
fields that were taken must not be reachable again. RFC-0121's width-subtyping rule already
refuses to silently forget a non-`Copy` field and points to "an explicit
`where R = { .., ..Rest }` decomposition, which keeps `Rest` visible and owned" as the
alternative. This RFC supplies the operation that makes that sentence true: a way to *take*
`Rest` as an owned value.

---

## Goals

- A generic body can take an abstract row apart and put one together, with the result typed
  by the row facts the signature already states.
- The operation is ownership-sound: every field of the source is either moved to a named
  binding, moved into the remainder, or (if `Copy`) copied; none is forgotten.
- The new syntax mirrors syntax that exists, so it is learnable from the type-level forms.
- Rows keep their invariant — a label occurs at most once — and the checker can prove it
  without runtime tests.

## Non-goals

- Label polymorphism (selecting a field by a label *variable*). That is RFC-0175; this RFC
  is the fixed-label case it builds on.
- Iterating a row's fields (RFC-0174).
- Narrowing *inside* a field (RFC-0150).
- Changing what `{ x: T, ..R }` as a *type* means, or the by-value width-subtyping rule.

---

## Proposal

### 1. Rest pattern: `..name` in a record pattern

A record pattern may end in `..name`, binding every field the pattern did not name, as a
record:

```metel
let { token, ..rest } := value;          // value : { token: Token, extra: i64, flag: boolean }
// token : Token, rest : { extra: i64, flag: boolean }
```

This is the record counterpart of the array pattern's `..name`, and a refinement of the
record pattern's existing bare `..` (which still discards). It follows the same
irrefutability rule as the existing record pattern: it matches any record that has the
named fields.

**Typing.** The binder's type is the source row minus the named fields.

- For a concrete row this is the concrete record of the remaining fields.
- For an abstract row it is determined by the facts in scope:
  1. if the scrutinee is typed `{ f1: T1, .., ..R }` directly, the remainder is `{ ..R }`;
  2. if the scrutinee is typed `{ ..S }` and the declaration states `S = { f1: T1, .., ..Rest }`
     for exactly the named fields, the remainder is `{ ..Rest }`;
  3. otherwise the pattern is rejected with the missing entailment named ("`token` is not
     known to be present in `R`; add a bound or an equation"). A bound `R: { token, .. }`
     proves presence but names no remainder, so it is not enough.

  The named fields' types are taken from the facts as well, so a bound with a field of
  unknown type binds it at the bound's type.

**Ownership.** Matching moves the scrutinee. Each named field moves into its binder (or is
copied if `Copy`, or dropped immediately for `_`); `..name` takes every other field as one
owned record. The scrutinee is consumed as a whole, so no residual of it remains. Matching
a *reference* (`&{ ..R }`) is a separate question (Open Question 3).

**Nominal types.** The scrutinee may be an anonymous record or a nominal `record` (whose
fields are all public). The remainder is always an **anonymous** record: the brand is not
carried over, because it would no longer describe the value. A `struct` is rejected —
its row is private to its module and the pattern would leak it — and a type implementing
`Drop` is rejected, since taking its fields apart would bypass its destructor.

### 2. Row spread: `..expr` in a record literal

A record literal may contain `..expr` among its field initializers, placing every field of
`expr` into the new record:

```metel
{ ..rest, auth = a }          // rest : { ..R }  ⇒  { ..R, auth: String }
```

This is the value-level form of the type-level tail `{ ..R, auth: String }`; the position of
`..expr` among the initializers is not significant, matching record field order everywhere
else.

**Typing.** The literal's row is the union of the spread's row and the written labels.
It is well-formed only if no label occurs twice, so each written label must be proven
**absent** from the spread's row:

- if the spread's row is concrete, by inspection;
- if it is abstract, by a negative bound (`row R: !{ auth }`) or by an equation that
  decomposed it — a remainder `Rest` from `R = { token: Token, ..Rest }` is absent `token`
  by the row invariant, since `R` contains `token` once.

A literal whose absence cannot be shown is rejected (`T0012`, naming the label). A written
label that is *present* in the spread is rejected too: there is **no override** — a
spread adds fields, and replacing one is a field assignment (`r.x := v`) on an owned
value, as today. At most one spread per literal.

**Ownership.** Spreading an owned record moves its fields into the result; the source is
consumed, as in §1. Spreading through a reference is allowed only if every field in the
spread's row is `Copy` (provably, for an abstract row: `where all R: Copy`) — the same
test and the same reason as RFC-0121's by-value width-subtyping rule — and otherwise is
rejected with a `T0033`-style message pointing at an explicit clone.

**Evaluation order.** Initializers, including `..expr`, are evaluated left to right as
written; the spread's fields then join the explicitly written ones in the new record.

### 3. Worked examples

The typestate step (signature unchanged from RFC-0121):

```metel
extend<row R, row Rest> Session<..R> where R = { token: Token, ..Rest } {
    fun authenticate(self) -> Session<..Rest> {
        let { token: _, ..rest } := self.data;      // §1 case 2: rest : { ..Rest }
        Session { id = self.id, data = rest }
    }
}
```

The reverse step, adding a field (the equation here is for the *result*):

```metel
extend<row R: !{ token }> Session<..R> {
    fun with_token(self, t: Token) -> Session<{ ..R, token: Token }> {
        Session { id = self.id, data = { ..self.data, token = t } }   // §2: token ∉ R
    }
}
```

A generic utility, taking one known field out and handing back the rest:

```metel
fun take_id<row R>(r: { id: i64, ..R }) -> (i64, { ..R }) {
    let { id, ..rest } := r;      // §1 case 1
    (id, rest)
}
```

Must **not** compile:

```metel
fun bad<row R>(r: { ..R }) -> i64 {
    let { id, ..rest } := r;      // error: `id` is not known to be present in `R`
    id
}

fun bad2<row R>(r: { ..R }, a: String) -> { ..R, auth: String } {
    { ..r, auth = a }             // error: `auth` is not known to be absent from `R`
}

fun bad3<row R>(r: &{ ..R }) -> { ..R } {
    { ..r }                       // error: cannot copy the fields of `R` out of a reference
}
```

### 4. Interactions

- **RFC-0173 (rigid parameters).** Neither form relaxes rigidity: `R` is never unified with
  `Rest`. The remainder type comes from a stated fact (a bound's tail or an equation) and
  presence/absence are entailments checked against the declared bounds, so a body that
  builds `{ ..Rest }` is accepted exactly when its signature promises it. The checker
  already carries decompositions as symbolic facts through a body; this RFC uses them.
- **RFC-0121 width subtyping.** Unchanged. The spread through a reference reuses its `Copy`
  rule rather than introducing a second one.
- **RFC-0137 / RFC-0117 (narrowing).** A pattern that moves fields out of a *nominal*
  value is a whole-value move here, so it does not produce a residual; partial moves keep
  their existing field-by-field narrowing. Moving every field out of a value (the
  degenerate empty remainder) is the case metel-core#1398 tracks and must behave
  consistently with it.
- **RFC-0175 (label polymorphism).** `drain_field<label L, row R, T>` is the §1 pattern with
  a label variable in place of `token`. This RFC fixes the semantics for a known label so
  that RFC-0175 only has to add the variable.
- **Array rest patterns.** `[a, ..rest]` already binds the remainder of an array; the
  record form is deliberately the same shape.

---

## Alternatives considered

1. **A removal operator or method (`r.without(token)`, `R \ token`).** Rejected for the
   reasons RFC-0121 §2 gave against row subtraction, and because a method needs a label as
   an argument (RFC-0175's label kind) to be generic, whereas a pattern names the label as
   syntax and needs nothing new in the type system.
2. **Remainder projection, `self.data.{ ..Rest }`.** Reuses the existing `.{ }` projection,
   and avoids a new pattern form. But projection *views* a value without moving it (the
   residual is of the same brand, and the original keeps its other fields), so it answers a
   different question: it would leave `token` in the source, with the ownership puzzle this
   RFC exists to solve. It also gives no way to bind the *removed* field, which a typestate
   step usually needs.
3. **Update-only, as Elm settled on.** Assignment to existing fields works today; what is
   missing is changing the *set* of fields. Not enough for typestate.
4. **Copy-only remainder.** Allow the forms only when the remainder is `Copy`. This is the
   by-value width-subtyping rule and rules out the interesting case: a session or a handle
   whose remainder owns a buffer.
5. **Spread with override (JS/Elm-style, last wins).** Rejected: it breaks the row
   invariant that a label occurs once, and would make the literal's type depend on
   whether a label was present — undecidable for an abstract row without a presence
   fact.

---

## Open Questions

1. **Spelling of the spread.** `{ ..rest, auth = a }` mirrors the type-level
   `{ ..R, auth: String }`. The alternative is trailing-only (`{ auth = a, ..rest }`),
   Rust-like, which the type-level form does not require. Leading position is proposed
   because record order is not significant; confirm it does not collide with range
   expressions (`..x`) inside a record literal's initializer position.
2. **Is "remainder lacks the decomposed label" already a derived fact?** §2 relies on it.
   If the current checker records only the equation, absence must be derived from the row
   invariant at the point of the spread, and the implementation should say so explicitly.
3. **Patterns against a reference.** `let { x, ..rest } := &r` could yield `x : &T` and
   `rest : &{ ..Rest }`, a borrowed view of the remainder — the shape RFC-0175 sketches
   for `drain_field` (`(T, &var { ..R })`). That needs the borrow rules of RFC-0122 for the
   `&var` case and is deferred; this RFC covers owned scrutinees only.
4. **More than one spread.** Two spreads need pairwise disjointness of two abstract rows,
   which a negative bound can express only per label. Deferred; at most one in this RFC.
5. **Nominal result.** Should a remainder be able to re-acquire a brand — rebuilding a
   `Session` from a destructured `Session`'s fields? As proposed the user writes the
   constructor call (`Session { … }`) explicitly, which keeps construction invariants in
   one place (see RFC-0114).
6. **Tuples.** If tuples become numeric-label rows (RFC-0151), `(a, ..rest)` should mean
   the same thing; whether `..rest` over a tuple yields a re-indexed tuple is that RFC's call.

---

## Specification impact

Spec text lands only at `3-integrated`. Sections affected: record pattern grammar and
exhaustiveness (`expressions.md`), record literal grammar and typing (`types.md`
Anonymous Records, Open rows), and the partial-move rules (`ownership.md`). New
diagnostics reuse `T0012` (presence/absence not entailed) and `T0033` (copying through a
reference); no new code is proposed. The "known limit" entry for a derived remainder in
the Records and Rows reference is removed on implementation.

## Implementation notes

- Grammar: `field_pat_list` gains `..ident` beside bare `..`; record literals gain a spread
  initializer. Both mirror `row_tail` and the array `rest_pat`.
- Checker: presence/absence entailments reuse the row-fact machinery from RFC-0173's
  implementation; the remainder type is read from the same facts the equation already
  records.
- Runtime: a rest pattern builds a new record from the unnamed fields; a spread builds one
  from the spread's fields plus the written ones. Layout is known statically after
  monomorphization, so the compiled profile needs no dynamic row.

---

## Decision

**Outcome:** *(pending)*
