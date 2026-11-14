---
id: rfc-0231
title: "Row Predicates"
date: '2026-11-14'
status: draft
---

## Summary

A **row predicate** is a structural property of a row's labels that the compiler decides by inspecting them, and that a
program can use as a bound: "this row's integer labels are exactly `.0 .. .N-1`". Two are proposed, `Dense` and `Tuple`:

```metel
fun cons<A, record R: Tuple>(a: A, t: R) -> ...        // R is a closed row of dense integer labels (RFC-0125, Option A)
extend<record R: Tuple> R: Marker;                      // an impl for tuples only
```

A predicate is an **aspect granted to a row by its shape**, the way `Send` and `Sync` are granted by a type's fields (the
`auto` property, RFC-0096). It is not a new kind of type, has no checked construction and no brand, and a row that satisfies it
is the same row: every record operation applies to it unchanged. A row that stops satisfying it (a partial move that leaves a
gap, RFC-0151 section 4a) simply no longer does, with no rule to say so.

This is the piece RFC-0125's Option A and RFC-0151's section 5a depend on. It is deliberately **not** a refinement-type feature:
RFC-0202 already uses that name for nominal value types with a checked constructor, and a label-set predicate needs none of
that. It is a design draft. Nothing here is accepted.

---

## Motivation

Two designs in review need the same statement, "the integer labels of this row are dense":

- **RFC-0151 section 5a** names the property, `Tuple`, as a derived fact used to print `(A, B)` and to choose a dense layout.
  It leaves open whether the property can be written in a program.
- **RFC-0125's Option A** writes positional operations (`cons`, `tail`, `append`, `zip`) as comptime functions over a row that
  carries it. Its `Tuple` argument is the property above, and its mixed-row form needs the weaker "the integer labels are
  dense" (`Dense`), so that a call's argument list `.{ .0, .1, .x }` can be shifted without touching `.x`.

Row bounds (RFC-0118, RFC-0189) cannot say it. They state presence, absence and type of *named* labels (`.{ .x: f64, !token,
.. }`); "the integer labels form a gap-free prefix of the integers" quantifies over an unbounded set. The quantifier of
RFC-0123 (`..R: A`) ranges over a row's field *types*, not over its label set. So the statement has no spelling today, and each
RFC would otherwise invent its own.

### Why not RFC-0202

RFC-0202 (draft) is `type Percent := i64 satisfying (0 <= self && self <= 100)`: a distinct **nominal** type, entered only by a
checked construction, whose predicate is a comptime-evaluable expression over a **value**. Row predicates differ on every point:

| | RFC-0202 `satisfying` | Row predicate |
|---|---|---|
| What is constrained | a value | the label set of a row, a type-level object |
| Identity | a new nominal type | none; the row is the same type |
| How it is established | a checked construction, `try_from` | inspection of a closed row; a declared bound otherwise |
| Subtyping | not a subtype of the base | the row is the row; a bound, not a conversion |
| Decidable | by running a comptime predicate | always, by finite label-set rules |

Keeping the words apart matters: calling a row predicate a refinement type would suggest a checked constructor and a nominal
identity it does not have. RFC-0202's non-goal of flow-sensitive refinement (its section 4, and RFC-0142's occurrence-typing
discussion) is also this RFC's: nothing here narrows a type by a test.

---

## Proposal

### 1. Two predicates

| Predicate | Holds for a row when | Examples |
|---|---|---|
| `Dense` | its **integer** labels are exactly `.0 .. .N-1` for some `N ≥ 0`; identifier labels are unconstrained | `.{ .0: A, .1: B }`, `.{ .0: A, .x: C }`, `.{}`; not `.{ .0: A, .2: C }` |
| `Tuple` | it is **closed**, `Dense`, and has **no identifier labels** | `.{ .0: A, .1: B }`, `.{}`; not `.{ .0: A, .x: C }`, not an open row |

`Tuple` implies `Dense`. A closed row satisfies or fails each by inspection of its labels; the empty row satisfies both. Both
are declared in the standard library, so a program cannot declare another (section 6 asks whether it should).

### 2. A predicate is an aspect granted by shape

The language already has the mechanism: an aspect granted with no impl, from the structure of the type, with a negative impl
to opt out (the `auto` property: *granted structurally with no entry; a type opts out with a negative impl*; std only,
reserved; the aspects are `Send` and `Sync`). `Dense` and `Tuple` are aspects of the same kind, granted from a row's label set
instead of its field types. That gives them, with no new construct:

- **Bounds**, positive and negative: `R: Tuple`, `R: !Tuple`, and the `+` and `where` forms of RFC-0040.
- **Impl selection**: `extend<record R: Tuple> R: A` is a row-conditional impl (RFC-0121) whose condition is a predicate.
- **Coherence**: two impls whose predicates are disjoint (`Tuple` and `!Tuple`) do not overlap; others overlap as RFC-0060's
  rules already decide. A predicate is a function of a finite label set, so disjointness is decidable.
- **Diagnostics**: an unsatisfied bound is `T0012`, whose note names the cause, as RFC-0211's residual notes do: ``.{ .0: A,
  .2: C }` is not a `Tuple`: the integer label `.1` is missing``.

The one difference from `Send`: a row cannot opt out of a shape fact. `extend .{ .0: A }: !Tuple` would contradict inspection, so
it is an error (open question 1).

### 3. How a predicate is decided

- **A closed row**: by inspecting its labels. No annotation, no proof, no solver.
- **An abstract or open row**: only by a declared bound. A parameter `record R: Tuple` is `Tuple`; `.{ .0: A, ..R }` with `R:
  Dense` says nothing about the whole row, because `R` is a row whose labels start where they start. The shift that relates
  them is exactly what RFC-0125 computes (a comptime function or a built-in operator), not a rule of this RFC.
- **After a narrowing**: the residual is a new closed row and its predicates are decided afresh by inspection. A partial move
  that leaves a gap leaves a row that is not `Tuple`; one that removes a suffix leaves one that is. No rule is needed.

Nothing is decided by a test in the program: `if t.len() == 2` does not make `t` a two-tuple (the same non-goal as RFC-0202).

### 4. What a predicate does not change

- **Type identity.** `(A, B)` and `.{ .0: A, .1: B }` are one type; a predicate adds no brand and no distinct type.
- **Operations.** A row satisfying `Tuple` has every operation of a record: projection, spread, narrowing, field access,
  `Copy`, `Clone`, `Display`. A function that takes `R: Tuple` takes a record and uses it as one.
- **Layout and printing.** RFC-0151 section 5a states them in terms of `Tuple`. This RFC supplies the property; the permission
  to store a `Tuple` densely, and the `(A, B)` rendering, stay there.

### 5. What it enables

- **RFC-0125, Option A**: `comptime fun cons<A, record R: Tuple>(...)`, and the mixed-row form over `Dense`. The result type of
  such a function is still RFC-0125's open point.
- **Arity-generic impls** over tuples where a row impl cannot be written structurally, by naming `Tuple` in the bound.
- **The `(…)` sugar**: it constructs, matches and writes exactly the rows with the predicate.

### 6. Not proposed

- **User-declared predicates.** A predicate defined by a comptime function over a row's `TypeInfo` (RFC-0132) would let a program
  state its own shape facts, and is where this RFC and RFC-0202's `satisfying` would meet. It needs a termination story for the
  comptime function and a coherence rule for predicates the compiler cannot compare. Left to a later RFC.
- **A length predicate** (`Len(N)`, "non-empty"). It needs a compile-time integer in a bound, which is const generics
  (RFC-0053 deferred them; #1811 waits on RFC-0132's compile-time `N`). `tail` states non-emptiness structurally today
  (`.{ .0: A, ..R }`).
- **Predicates over field types** beyond what row bounds already say.

---

## Interactions

- **RFC-0151**: supplies the `Tuple` property its section 5a names; this RFC makes it a bound.
- **RFC-0125**: Option A's prerequisite (ii).
- **RFC-0118, RFC-0123, RFC-0189**: the row-bound language this extends by one kind of atom, a label-set predicate.
- **RFC-0096**: the `auto` property it reuses. **RFC-0121**: row-conditional impls and coherence.
- **RFC-0202**: a different feature, kept apart (Motivation). **RFC-0142**: the flow-sensitive non-goal is shared.
- **RFC-0211, RFC-0214**: a residual's predicates are decided afresh; an impl for a residual may name one.
- **RFC-0209** (row templates): a template over rows can name a predicate in its condition.

---

## Alternatives considered

1. **A new bound class** with its own expression language (`where labels(R) = 0..n`). More general, and a second language for
   conditions beside aspects; the aspect route gets bounds, negation, impl selection and coherence at once.
2. **General refinement types over rows** (value predicates, an SMT-style solver). Rejected as RFC-0202 rejects it: it needs a
   solver, and label-set predicates are decidable without one.
3. **Label arithmetic** (`.[L + 1]` in RFC-0188's label variables), stating a shift inside the row syntax. It addresses RFC-0125's
   renumbering, not the predicate, and depends on RFC-0188. It composes with this RFC.
4. **Nothing**: RFC-0125's Options B and C need no predicate, and RFC-0151's `Tuple` stays an internal fact.

---

## Open questions

1. **The `auto` property, or a new one?** `auto` allows a type to opt out by a negative impl; a shape fact has no opt-out. Reuse
   `auto` and make the negative impl of a shape predicate an error, or add a property (`shape`) for aspects decided by structure
   alone?
2. **Names.** `Tuple` collides with the word for the type former and, if a program defines its own `Tuple`, with that.
   `Dense` is vague outside rows. Are `Positional` and `Sequence` better, and is a name that shadows legal?
3. **Open rows.** `Dense` of `.{ .0: A, ..R }` is undecidable. Should a bound on `R` ever imply something about the whole row,
   or is a bound only ever written on the whole row?
4. **Non-`record` parameters.** Row bounds attach to `record R`. May a predicate bound appear on a parameter that is not a row,
   and is it then simply unsatisfied?
5. **User-declared predicates** (section 6): in scope for a follow-on, or never?
6. **Length.** If RFC-0125's result types need a length, this RFC needs const generics; if they do not, it does not.
7. **Error text.** The `T0012` note for an unsatisfied predicate names the missing label; for an open row it must say the row is
   open.

---

## Implementation notes

- The standard library declares `Dense` and `Tuple`; the compiler grants them from a row's label set and implements the one rule
  that `Tuple` implies `Dense`. Bounds, negative bounds, impl selection and coherence reuse the aspect machinery, so no new
  bound class is needed.
- No new syntax in the first stage. A predicate is written as an aspect.
- Fixtures: each predicate on closed rows (satisfied, gap, identifier label, open), a bound on a parameter, an impl over
  `Tuple`, disjoint impls (`Tuple` and `!Tuple`), the residual after a partial move, and the error note.

---

## Decision

**Outcome:** *(pending)*
