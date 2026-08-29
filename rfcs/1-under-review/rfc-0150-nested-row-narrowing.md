---
id: rfc-0150
title: "Nested Row Narrowing"
date: '2026-08-29'
status: under-review
target:
updated: '2026-08-29'
tracking: 'https://github.com/metel-lang/metel-core/issues/900'
---

> **Split from RFC-0117 on 2026-08-29.** RFC-0117 (Row Narrowing) narrows a value's
> type when a *whole field* is moved out, at any depth the field is reached. Its
> pre-acceptance review established that narrowing a field *of* a record-typed field
> **in place** — leaving the outer value holding that field at a narrower type — needs a
> recursive residual type system RFC-0117 deliberately avoids. That capability is this
> RFC. RFC-0117 ships flat for v0.13.0; this is the follow-up, targeted alongside
> RFC-0147/0148.

> **Status — under review (2026-08-29).** Split from RFC-0117 pre-acceptance review: nested (recursive) row narrowing needs a residual type grammar, tuple residuals, recursive Drop receiver shapes, and control-flow-join rules that RFC-0117 deliberately excludes. Depends on RFC-0117 + RFC-0147/0148.

## Summary

Extend RFC-0117 so that a **nested partial move** — moving a field out of a
record-typed field, `o.inner.a` — narrows that inner field's type *in place*: `o`
keeps the `inner` label, at the residual type `Inner.{ b }`, giving
`o : Outer.{ inner: Inner.{ b }, tag }`.

Under RFC-0117 alone the only way to narrow through `inner` is to move the whole
`inner` field out as a unit and narrow it as its own value. Nested narrowing makes
the outer type track a partial move that reaches into a subfield, which is what lets a
partially-consumed nested structure be passed, returned, and named without first being
disassembled.

## Motivation

RFC-0117 makes a residual a real type so it can cross function boundaries. That stops
at one level: `fun f(o: Outer.{ tag })` can take an `Outer` that has lost its `inner`
field, but nothing can take an `Outer` that still has `inner` *at a narrower type*.
The natural "consume part of a nested field, keep the rest" pattern — common with
builders, parsers, and staged initialization — has no expression, exactly the gap
RFC-0117 closed for the flat case.

The move checker already tracks nested move paths (`Place` projections like
`o.inner.a`); it joins move state across branches and loops; it rejects moves through
references and array elements. The operational substrate exists. What is missing is the
**type-level** reflection of a nested partial move, and the type-system machinery that
requires.

## What this RFC must define

These are the concrete gaps the RFC-0117 review surfaced. Each is a design question
this RFC has to answer before it can be accepted.

### 1. A residual type grammar for narrowed field types

RFC-0116's branded projection form is a bare label list — `Handle.{ fd }` — where every
listed field keeps its *declared* type. `Outer.{ inner: Inner.{ b }, tag }` is new
syntax: a branded row in which a field's type differs from the declaration. This RFC
must either add that typed-row projection form to the type grammar and its canonical
form, or specify a desugaring (e.g. a branded row paired with an explicit per-field
type map). A prose claim that "a row already maps a label to a type" is not enough —
the surface grammar, the printer, and structural comparison all need the case.

### 2. Recursive type identity

Two nested residuals of the same brand and the same recursively-canonical field map
must compare **equal**, regardless of the narrowing history that produced them
(`o.inner.a` then `o.inner` re-narrowed elsewhere, versus a projection that lands on
the same shape). An anonymous record `{ inner: Inner.{ b }, tag: i64 }` of the same
shape must **not** compare equal — it is brandless (RFC-0137's core invariant). The
rule: identity is `(brand, canonical field map)` computed recursively; history is not
part of it; anonymous records never acquire a brand.

### 3. Tuple-field residuals

RFC-0071 §9a tracks tuple elements like struct fields, so `o.t.0` is a partial move of
`o.t`. RFC-0117 has no residual type for a tuple, so nested narrowing through a
tuple-typed field is currently undefined. This RFC must either define tuple residuals
(a tuple type with per-position present/absent, mirroring row residuals) and fold them
into the recursion, or explicitly reject nested narrowing through a tuple-typed field
until tuple residuals exist. Arrays (element moves banned, RFC-0071) and enum payloads
(consumed whole) stay as RFC-0071 states.

### 4. Recursive `Drop` receiver shapes

RFC-0137 §5 checks a destructor body against a *flat* declared required-field set on
its `drop` receiver. Nesting breaks that: if `Outer: Drop` declares
`fun drop(&var self: Self.{ inner })` and its body reads `self.inner.a`, a shallow
`residual ⊇ { inner }` check would fire `Outer::drop` against `inner: Inner.{ b }`
while the body needs `a`. The required set must become a **receiver shape/tree**, and
the dispatch check must require the current residual's nested field types to satisfy
that shape recursively. This is why this RFC depends on RFC-0147/0148, which introduce
the narrowed-`drop`-receiver syntax the shape is declared in.

### 5. Control-flow joins for nested residuals

RFC-0117's flat rule is already path-sensitive (a field moved on one branch is
conservatively moved after the join). Nesting compounds it: after
`if (c) { let a = o.inner.a; }` the type of `o` must be the conservative join —
`Outer.{ inner: Inner.{ b }, tag }`, treating `a` as gone because one path took it —
and loop-carried nested moves must participate in the move checker's existing fixpoint.
This RFC must lift those join/fixpoint rules into the spec for the nested case.

### 6. Interaction with RFC-0119 round-tripping

For `o : Outer.{ inner: Inner.{ b }, tag }`, `o.to_record()` should produce
`{ inner: Inner.{ b }, tag: i64 }` — the nested residual field type carried through —
not `{ inner: Inner, tag: i64 }` (which would silently widen) and not a loss of the
nesting. This requires residual field types to be legal inside an anonymous record row,
and RFC-0119's "current row" rule to recurse. `from_record` back to the full nominal
type stays widening / `Construct` territory (RFC-0114) unless the record is already
full.

### 7. Termination domain

`R(T)` — a type's residual count — is defined only over finite, statically-known
product type trees. References and allocator pointers are atomic (a pointer is scalar
for narrowing). Enums, arrays, and function types are atomic unless a future RFC
supplies a residual form. A generic field's `R` is not expanded until the parameter is
concrete, and a nested field move through an unconstrained type parameter is illegal
absent a row or field bound. Recursive nominal types by value are already uninhabitable,
so the tree is finite.

## Non-Goals

- Flat narrowing (whole-field moves) — RFC-0117.
- Widening a nested residual back — RFC-0114's row-completion / `Construct`, one level
  or many.
- Borrowed nested narrowing (`&var` views) — RFC-0109 / RFC-0119.
- Abstracting over *which* nested residual a function accepts — that is row
  polymorphism, RFC-0121.

## Open Questions

1. **Typed-row projection syntax vs. desugaring** (§1). Add `Type.{ f: T', .. }` to the
   grammar, or keep the surface list-only and represent nested residuals purely
   internally as `(brand, field-type-map)`? The latter avoids grammar churn but makes
   a nested residual unnameable in a signature — which defeats RFC-0117's own reason
   for existing, one level down.
2. **Tuple residuals now or defer** (§3). Defining them is a self-contained piece
   (tuple type + per-position presence); rejecting nested narrowing through tuples is a
   one-line restriction. Which for the first cut?
3. **Depth cap.** Is there a practical need to bound nesting depth for the analysis, or
   does the finite type tree make that a non-issue?

## References

- RFC-0117 (Row Narrowing) — the flat rule this extends; its Open Question 3 and §3
  name this RFC as the recursive follow-up
- RFC-0137 (Nominal Types as Branded Rows, `3-integrated`) — the `(brand, row)`
  representation and §5 row-bounded `Drop` dispatch this must make recursive
- RFC-0147 / RFC-0148 — narrowed `drop` receiver forms; §4's recursive receiver shape
  is declared in their syntax, so this RFC is scheduled after them
- RFC-0116 (Anonymous Record Types) — the type-former; §1's typed-row projection form
  is an addition to its grammar
- RFC-0071 (Ownership and Move Semantics, `3-integrated`) — §9a tuple-element tracking
  (§3), the move-checker join/fixpoint behavior (§5), and §7's `Drop` partial-move ban
- RFC-0119 (Record Conversions) — `to_record` / `from_record`; §6's recursion
- RFC-0114 (Constructor Aspect and Canonical Construction) — nested widening
- RFC-0121 (Open Rows) — abstracting over residuals, out of scope

---

## Decision

**Outcome:** *(pending — split from RFC-0117 2026-08-29; the seven items above are the
design surface, several depending on RFC-0147/0148 which are themselves not yet
accepted.)*
**Target:** *(set when accepted; expected alongside or after RFC-0147/0148.)*
