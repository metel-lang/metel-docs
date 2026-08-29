---
id: rfc-0129
title: "Aspect Method Generic Constraint Conformance"
date: '2026-08-05'
status: under-review
target:
updated: '2026-08-23'
tracking: 'https://github.com/metel-lang/metel-core/issues/617'
---

> **Status — under review (2026-08-23).** Real substantiated proposal (entailment table, primary proposal) but 6 open open questions block acceptance -- OQ1-6 none resolved. Its own References section already names #617 as the implementation follow-up.
> **Update 2026-08-29:** OQ1-6 resolved, then revised across two adversarial review rounds. Round 1 widened OQ6's conflict set and relaxed OQ1 (adding an interim "reachable-blanket" entailment rule). Round 2 broke that rule — unsound against an explicit negative impl, under-specified for multi-premise / constructor-target blankets — plus a wrong-no in the multi-label row decomposition. **Current position:** blanket-derived entailment *and* blanket-derived empty-domain detection are **deferred to metel-core#895**; the first implementation uses only the tabled rules (a conservative wrong-no for blanket-only weakenings; a tracked vacuous-conformance gap for blanket-only empty domains). Row decomposition corrected (closed row = singleton domain entailing each contained typed-open atom); associated-type disequality is proven-concrete, not syntactic; record-kind + non-local-aspect added to the conflict set. OQ2/OQ3 deferred extensions: #895; OQ5 `where`-syntax: #896. Committed to **v0.13.0** via metel-core#617. **A fresh acceptance review should confirm the #895 retreat is acceptable for v0.13.0** and re-check the non-blanket conflict shapes.

## Summary

Define how generic constraints in an aspect method and its implementation relate, including record kind, aspect bounds, row bounds, and substitutability.

## Motivation

An aspect declaration is a promise made to every caller constrained by that aspect. An
`extend Type: Aspect` block supplies the implementation behind that promise. Method-name
completeness alone is insufficient: if the implementation accepts fewer generic
instantiations than the aspect declaration, a generic caller can make a call the aspect
admits but the implementation rejects or cannot type-check safely.

The gap surfaced while fixing the pre-existing inconsistency where an aspect implementation
could add methods the aspect never declared (metel-core#541). The first attempted
signature-conformance check compared method-generic constraints for equality. That has two
opposite failures:

```metel
// Equality rejects a safe implementation.
aspect Inspect {
    fun keep<record T>(value: T) -> T;
}

struct Holder {}

extend Holder: Inspect {
    fun keep<T>(value: T) -> T { value }
}

// Equality also fails to state why this direction is unsafe.
aspect AnyValue {
    fun keep<T>(value: T) -> T;
}

extend Holder: AnyValue {
    fun keep<record T>(value: T) -> T { value }
}
```

The first implementation is safe: every record admitted by `Inspect::keep` is also a
valid instantiation of the unconstrained implementation. The second is not: a caller with
only an `AnyValue` bound may call `keep(1)`, while the implementation requires a record.

This is not special to `record`. Aspect bounds, negative bounds, row bounds, and
associated-type equality bindings all constrain the set of legal type arguments. The
language needs one rule for their relation in an aspect method and its implementation,
rather than treating spelling equality as a proxy for substitutability.

## Goals

1. Define when an implementation method's generic constraints conform to an aspect
   method's generic constraints.
2. Cover the existing constraint language: record kind, positive and negative aspect
   bounds, row bounds, and associated-type equality bindings.
3. State which source-level differences are irrelevant, including alpha-renaming and the
   placement of a constraint in an inline list or `where` clause.
4. Give an implementable diagnostic boundary: rejected narrowing must be reported at the
   `extend` method declaration, before that method is registered for aspect dispatch.

## Non-Goals

- Adding new generic-constraint syntax, aspect inheritance, or a general subtyping
  hierarchy.
- Changing conditional-`extend` selection, coherence, or orphan rules (RFC-0036 and
  RFC-0060).
- Defining open rows or row-conditional implementations (RFC-0121).
- Relaxing receiver, ordinary parameter-type, or result-type conformance. Those are not
  constraint-domain questions.

## Terms

For a method with generic parameters `G`, its **admissible domain** is the set of tuples of
concrete types that satisfy all constraints on `G`. Constraints are conjunctive: an
argument tuple must satisfy every positive/negative aspect bound, record-kind requirement,
row bound, and associated-type equality binding that applies to it.

An aspect declaration is the caller-facing contract. Its admissible domain is `D_aspect`.
The implementation method has domain `D_impl`. The conformance condition considered by
this RFC is:

```text
D_aspect ⊆ D_impl
```

Equivalently, the aspect declaration's constraints must entail the implementation's
constraints. This is input-side substitutability: the implementation may accept more
instantiations, but never fewer.

## Primary proposal

### 1. Method signatures remain specialized and shape-compatible

Before generic constraints are compared, the compiler specializes the aspect method using
the `extend` block's target type, aspect arguments, and associated-type definitions.
`Self`, an aspect parameter, and an associated type therefore compare against their
concrete implementation meanings. Method-generic parameter names compare
alpha-equivalently.

Receiver form, ordinary parameter count and types, and result type must remain equal after
this specialization. This RFC changes only the relation between method-generic
constraints.

### 2. Constraints compare by domain inclusion, not spelling equality

The implementation must accept every generic instantiation the aspect admits. Removing a
constraint weakens it and is valid; adding a constraint strengthens it and is rejected.

```metel
aspect CopyOnly {
    fun pass<T: Copy>(value: T) -> T;
}

extend Holder: CopyOnly {
    fun pass<T>(value: T) -> T { value }       // valid
}

aspect AnyValue {
    fun pass<T>(value: T) -> T;
}

extend Holder: AnyValue {
    fun pass<T: Copy>(value: T) -> T { value } // invalid
}
```

The same rule applies to record kind and row bounds:

```metel
aspect HasCoordinates {
    fun x<record T: { x: f64, y: f64, .. }>(value: T) -> f64;
}

extend Holder: HasCoordinates {
    fun x<record T: { x: f64, .. }>(value: T) -> f64 { value.x } // valid
}
```

The aspect's open `{ x: f64, y: f64, .. }` bound entails the implementation's weaker
`{ x: f64, .. }` bound. Reversing them is invalid. A plain `<T>` implementation is also
valid for the aspect above; it accepts every record, though its body cannot rely on row
fields without another source of proof.

### 3. Normalize source spelling before checking inclusion

The following do not change a method's admissible domain and must not affect conformance:

- alpha-renaming method generic parameters (`T` versus `U`);
- reordering independent conjunctive bounds;
- duplicate bounds; and
- placing a constraint inline or in a method `where` clause, where that syntax is
  available.

The comparison is over the whole generic parameter tuple, not one independent list per
parameter. A bound may mention another method generic parameter, for example
`T: From<U>`; the compiler must preserve that relation when normalizing and proving
inclusion.

### 4. Diagnostics and dispatch

A narrowing implementation is a type error on the implementing method declaration. It
must not be registered as satisfying the aspect, and it must not contribute to aspect
method dispatch. The diagnostic should name the aspect method and the constraint that is
not entailed, for example:

```text
`Holder::pass` narrows generic parameter `T`: aspect `AnyValue::pass` permits a
non-Copy type, but this implementation requires `Copy`
```

## Entailment basis and cases

The inclusion judgement needs a small, explicit entailment relation rather than an
unbounded theorem prover. It must nevertheless honor every semantic implication already
made normative by accepted RFCs. Registry implementation details must not silently define
that relation.

The intended baseline is:

| Aspect contract entails | Implementation requirement | Result |
|---|---|---|
| no constraint | no constraint | yes |
| `record T` | no constraint | yes |
| no constraint | `record T` | no |
| `T: Copy + Display` | `T: Display` | yes |
| `T: Display` | `T: Copy + Display` | no |
| `T: Copy` | `T: !Drop` | yes |
| `record T: { x: f64, y: f64, .. }` | `record T: { x: f64, .. }` | yes |
| `record T: { x: f64, .. }` | `record T: { x: f64, y: f64, .. }` | no |
| `record T: { x: i64, .. }` | `record T: !{ x: f64 }` | yes |
| `T: Deref<Target = U>` | `T: Deref` | yes |
| `T: Deref` | `T: Deref<Target = U>` | no |
| `T: Deref<Target = U>` | `T: Deref<Target = U>` | yes |
| `T: !Copy` | no constraint | yes |
| no constraint | `T: !Copy` | no |

An omitted requirement is always entailed. In particular, an associated-type equality may
be omitted by the implementation, while an implementation may not add one. The `Copy` to
`!Drop` row follows RFC-0071's normative mutual-exclusion rule.

### A bounded, deliberately incomplete proof relation (resolves Open Question 1)

The entailment relation `⊢` is a **bounded set of directed rules**, defined here and
extended only by a normative RFC that introduces a new implication (with fixtures). It is
a **sound but deliberately incomplete** proof of `D_aspect ⊆ D_impl`: the semantic
inclusion may hold in cases these rules do not derive, and those are **conservatively
rejected** (a wrong-no), not accepted.

The comparator must never call `type_satisfies_aspect(concrete_type, aspect)` — that
answers "does concrete type `X` satisfy aspect `A`", a different question from "does
constraint `P` entail constraint `Q`" — and, **for first implementation, must not derive
entailments from reachable blanket/conditional impls at all** *(retreated 2026-08-29
after a second adversarial review — the interim rule `extend<G: P> G: A ⇒ (P ⊢ A)` was
unsound against an explicit negative impl `extend X: !A` overriding the blanket
(RFC-0060/RFC-0081), and under-specified for multi-premise (`extend<G: P + Q> G: A`) and
constructor-target (`extend<G: P> Box<G>: A`) blankets. A weakening that holds only
because of a reachable blanket is a wrong-no here; blanket-derived entailment, done
soundly with negative-impl priority, is deferred to `metel-core#895`)*.

After §1 specialization and §3 normalization to canonical conjunctive form, the
comparator **accepts `D_aspect ⊆ D_impl` when** every atom of `D_impl`'s conjunction is
either

1. syntactically present in `D_aspect`'s conjunction (identity), or
2. the head of a rule whose premises are all present in `D_aspect`'s conjunction.

The rule set, complete for first implementation:

- **Conjunction elimination** — `P ∧ Q ⊢ P`; `P ∧ Q ⊢ Q`. (This is what makes "an
  omitted requirement is entailed" a rule rather than a special case.)
- **`Copy(T) ⊢ !Drop(T)`** — RFC-0071 §4, the only positive-aspect ⇒ negative-aspect rule.
- **Row rules** — the row table below, after multi-label decomposition.
- **Identity for associated-type equality** — `Deref<Target = U>(T) ⊢ Deref<Target = U>(T)`
  after specialization; and, by conjunction elimination, `⊢ Deref(T)`. No rule derives one
  equality from another (Open Question 3).

No transitive search, no chaining; no rule that inspects concrete types not present as
constraint atoms (Open Question 2); no reachable-impl consultation for entailment
(deferred, above). An `impl` atom that is neither present nor a rule head is **not
entailed** — the narrowing is rejected (§4).

### Row-bound entailment (resolves Open Question 4)

Row-bound forms (RFC-0118): open `{ l: T, .. }` ("has at least"), closed `{ l: T }`
("has exactly"), label-only `{ l, .. }` ("has `l` at any type"), negative `!{ l }` /
`!{ l: T }`. Each denotes a set of concrete rows; `bound_a ⊢ bound_i` iff
`Dom(bound_a) ⊆ Dom(bound_i)`.

**Normalize multi-label bounds to per-label atoms first** *(added 2026-08-29 after an
adversarial review — the table below is stated per single label, and Open Question 4's
completeness claim needs the multi-label forms reduced to it, not left implicit):*

- `{ a: A, b: B, .. }` → `{ a: A, .. } ∧ { b: B, .. }`
- `!{ a, b }` → `!{ a } ∧ !{ b }`
- `!{ a: A, b: B }` → `!{ a: A } ∧ !{ b: B }`
- `{ a, b, .. }` (label-only) → `{ a, .. } ∧ { b, .. }`
- `{ a: A, b: B }` (closed) stays one atom on the **aspect** side — closedness is a
  property of the whole row, not decomposable — but a closed aspect bound is a singleton
  domain `{ the row `{ a: A, b: B }` }`, so it entails **every impl atom that single row
  satisfies**: each contained typed-open atom (`{ a: A, .. }`, `{ b: B, .. }`), each
  contained label-only atom (`{ a, .. }`), and each negative atom the row does not
  violate (`!{ c }` for `c ∉ {a, b}`, `!{ a: X }` for `X ≠ A`). It matches a closed impl
  bound only when that bound is the identical row. *(This per-label-open case was
  missing in the first revision — `record T: { x: f64, y: f64 } ⊢ record T: { x: f64, .. }`
  is a safe weakening and must be provable.)*

Each resulting atom is then checked by the table. So `!{ secret, token } ⊢ !{ secret }`
(drop an atom, conjunction elimination), `!{ x: f64, y: i64 } ⊢ !{ x: f64 }` likewise,
and closed `{ x: f64, y: f64 } ⊢ open `{ x: f64, .. }` (the singleton row has `x: f64`).

| Aspect row bound | Implementation row bound | Result | Reason |
|---|---|---|---|
| open `{ x: f64, y: f64, .. }` | open `{ x: f64, .. }` | yes | fewer required fields on the impl side |
| open `{ x: f64, .. }` | open `{ x: f64, y: f64, .. }` | no | aspect admits rows lacking `y` |
| closed `{ x: f64 }` | open `{ x: f64, .. }` | yes | the one closed row satisfies the open bound |
| open `{ x: f64, .. }` | closed `{ x: f64 }` | no | aspect admits `{ x: f64, z: … }` |
| closed `{ x: f64, y: f64 }` | closed `{ x: f64 }` | no | distinct exact rows; disjoint domains |
| closed `{ x: f64 }` | closed `{ x: f64 }` | yes | identical |
| closed `{ x: f64 }` | `!{ y }` (any `y ≠ x`) | yes | the closed row has no `y` |
| closed `{ x: f64 }` | `!{ x: g }` (`g ≠ f64`) | yes | the closed row's `x` is `f64`, not `g` |
| open `{ x: i64, .. }` | `!{ x: f64 }` | yes | a label has one type — `x: i64` ⇒ not `x: f64` |
| open `{ x: f64, .. }` | `!{ y }` | no | aspect admits rows that also carry `y` |
| open `{ x: f64, .. }` | label-only `{ x, .. }` | yes | requiring `x: f64` ⊆ requiring `x: _` |
| label-only `{ x, .. }` | open `{ x: f64, .. }` | no | aspect admits `x: i64` |
| label-only `{ x, .. }` | label-only `{ x, .. }` | yes | identical |
| `!{ x }` | `!{ x }` | yes | identical |
| `!{ x }` | `!{ x: f64 }` | yes | "no `x` at all" ⊆ "no `x` at `f64`" |
| `!{ x: f64 }` | `!{ x }` | no | aspect admits `x: i64`, which has label `x` |
| no row bound | any row bound | no | aspect admits every row |
| any row bound | no row bound | yes | conjunction elimination |

Rule of thumb: **open⇒open follows the field-subset direction**; **a closed aspect bound
is a singleton domain** that entails any impl bound that single row satisfies; **a closed
impl bound is entailed only from an identical closed aspect bound**; **a negative impl
bound is entailed from a positive/closed aspect bound that provably cannot carry that
label (or that label at that type)**. Fixtures: one per row, positive for `yes`, a
`T0012` at the `extend` method declaration for `no`.

## Alternatives considered

### Exact constraint equality

This is simple to implement, but rejects safe implementations such as `<record T>` in the
aspect and `<T>` in the implementation. It makes a source spelling an artificial part of
the ABI despite the implementation accepting every call the aspect permits. Rejected.

### Require the implementation to repeat the aspect constraints verbatim

This is a stricter form of equality. It is predictable but duplicates a declaration whose
purpose is to state a caller-facing lower bound, not an implementation limitation. It also
prevents an implementation from being genuinely more general. Rejected for the same
reason.

### Permit arbitrary differences and defer failures to method-body checking

This accepts an implementation that needs `record T` for an aspect method callable with
any `T`. The aspect-bound caller is type-checked against the declaration, so a bad call can
reach an implementation whose body relies on a property the caller did not prove. Rejected
as unsound.

## Open questions

*All six resolved 2026-08-29, then revised twice the same day after two adversarial
review rounds (original text kept, resolutions appended and marked where each review
moved them, per the append-only convention). Round 1 found three empty-domain shapes
Open Question 6's first pass missed and an over-strict Open Question 1 rule; the interim
fix added a "reachable-blanket" entailment rule. Round 2 broke that rule (unsound against
an explicit negative impl; under-specified for multi-premise and constructor-target
blankets) and a wrong-no in the multi-label row decomposition. **Current position:**
blanket-derived entailment — and blanket-derived empty-domain detection — are **deferred
to `metel-core#895`**; the first implementation uses only the tabled rules, accepting a
conservative wrong-no when a weakening holds only via a reachable blanket. Items 2, 3,
and now the blanket cases have that owning tracker. A fresh acceptance review should
confirm the retreat is acceptable for v0.13.0 and re-check the row decomposition and the
widened non-blanket conflict shapes.*

1. **Entailment implementation and extensibility.** The implementation must include
   language-defined implications such as `Copy => !Drop`; it must not inherit them
   incidentally from `type_satisfies_aspect` or the aspect registry. Decide the specified
   representation and extension point for this proof relation as new accepted RFCs add
   implications.
   **Resolved 2026-08-29, revised twice the same day after two adversarial reviews.** The
   relation is a **bounded, sound-but-incomplete** set of directed rules — conjunction
   elimination, `Copy(T) ⊢ !Drop(T)`, the row table with multi-label decomposition,
   associated-type identity — defined in "A bounded, deliberately incomplete proof
   relation" above. Extended only by a normative RFC that introduces a new implication
   (with fixtures). The comparator does **not** call
   `type_satisfies_aspect(concrete_type, aspect)` and, for first implementation, does
   **not** derive entailments from reachable blanket/conditional impls: round 1 said "no
   registry at all" was too strict (a `T: A ⇒ T: P` weakening valid only via a reachable
   `extend<G: P> G: A` is safe); round 2 showed the interim `P ⊢ A` rule was unsound
   against an explicit `extend X: !A` (RFC-0060/RFC-0081) and under-specified for
   `extend<G: P + Q> G: A` and `extend<G: P> Box<G>: A`. Net: blanket-derived entailment
   is a wrong-no at first implementation, deferred — done soundly, with negative-impl
   priority, full-premise-conjunction extraction, and bare-parameter targets only — to
   `metel-core#895`.
2. **Negative and mixed bounds.** The table requires positive/negative row implication
   where incompatible field types make a negative predicate follow. Specify the remaining
   mixed-conjunction implications required at first implementation and which are
   conservatively rejected until a later RFC extends the proof relation.
   **Resolved 2026-08-29.** Required at first implementation: (a) the row table's
   positive/closed ⇒ negative rows above (a label carries one type; a closed row has no
   other labels), with `!{ a, b, … }` decomposed to `!{ a } ∧ !{ b } ∧ …` first; (b)
   `Copy(T) ⊢ !Drop(T)`; (c) atom-wise checking of mixed conjunctions — each `impl` atom
   (positive or negative) is proved independently against the aspect conjunction, with no
   cross-atom inference. **Conservatively rejected** until a normative RFC extends the
   relation: any implication requiring reasoning about concrete types not present as atoms
   (blanket-derived `Ord ⇒ PartialOrd` and the like — see Open Question 1's retreat),
   implications from associated-type relations, and negative-row implications outside the
   per-label type-conflict and decomposition cases above. Deferred-extension tracker:
   `metel-core#895`.
3. **Associated-type equality implication.** Dropping an equality requirement is already
   permitted by domain inclusion. Decide whether an aspect contract can entail another
   equality through a declared associated-type relation; that needs projection
   normalization not presently specified for generic declaration comparison.
   **Resolved 2026-08-29 — identical or omitted only.** The only associated-type rules
   are: an equality present identically on both sides after §1 specialization is entailed;
   an equality omitted by the implementation is entailed (conjunction elimination); an
   equality **added** by the implementation is rejected. Deriving one equality *from
   another* through a declared associated-type relation (projection normalization —
   computing `T::X` via the aspect's own associated-type definitions) is **not** in this
   RFC and such a difference is conservatively rejected. Deferred to a future RFC amending
   RFC-0082; tracker `metel-core#895`.
4. **Row-bound inclusion with closed rows.** The direction is clear for open rows, but the
   exact relation among closed bounds, label-only fields, negative row bounds, and
   differently typed labels needs a complete table and fixtures before acceptance.
   **Resolved 2026-08-29, multi-label case added and corrected the same day across two
   adversarial reviews.** The table is "Row-bound entailment (resolves Open Question 4)"
   in "Entailment basis and cases" above — the multi-label normalization step (`{ a, b, .. }`
   and `!{ a, b }` split to per-label atoms; a closed aspect row treated as a singleton
   domain that entails each contained typed-open / label-only / non-violated-negative
   atom — round 2 found the first pass omitted the typed-open case, a wrong-no) followed
   by the single-label table (open/closed, label-only,
   negative, both directions), each row with a required fixture (a positive test for
   `yes`, a `T0012` at the `extend` method declaration for `no`). *(The first version
   tabled only single-label forms and claimed completeness; multi-field negative bounds
   like `!{ secret, token } ⊢ !{ secret }` had no rule.)*
5. **Method `where` clauses on aspect declarations.** Implementation methods already have a
   `where` clause representation; aspect-method declarations currently store only inline
   generic parameters. Decide whether this RFC merely normalizes the forms already
   accepted, or also extends aspect method syntax to accept `where` clauses. The latter is
   syntax work and should not be smuggled in as a comparator detail.
   **Resolved 2026-08-29 — normalize-only.** This RFC does not add `where` clauses to
   aspect-method declarations (explicit Non-Goal: no new generic-constraint syntax). §3's
   canonicalization already flattens inline and `where` placement to one conjunctive form,
   so an implementation method that *does* use a `where` clause compares correctly against
   an aspect method's inline-only bounds. Extending aspect-method syntax to accept `where`
   is separate syntax work, tracked at `metel-core#896`, and does not gate this RFC.
6. **Contradictory domains.** If a declaration admits contradictory constraints such as
   `T: Copy + Drop`, its domain is empty and therefore is a subset of every implementation
   domain. Decide whether such constraints are rejected when declared or whether vacuous
   conformance is intentional and diagnosed separately.
   **Resolved 2026-08-29 — reject at the declaration; conflict set revised twice the same
   day across two adversarial reviews.** A method (aspect or `extend`) whose
   generic-constraint conjunction is unsatisfiable is a type error **at that method's own
   declaration**, independent of conformance — an uninhabited signature is a bug
   regardless of who implements it, and vacuous `∅ ⊆ D_impl` conformance would let any
   implementation "satisfy" a nonsense aspect method. Unsatisfiability is detected over a
   **closed set of syntactic conflict shapes**:

   - `A(T) ∧ !A(T)` for the same aspect; `Copy(T) ∧ Drop(T)` (RFC-0071 §4).
   - a **positive row bound of any kind** — open `{ l: A, .. }`, closed `{ l: A }`, or
     label-only `{ l, .. }` — conjoined with a negative bound over the **same label** that
     it violates: `!{ l }`, or `!{ l: A }` when the positive bound pins `l` to `A`.
     (Round 1's version said only "a *closed* row conjoined with…", missing
     `{ x: f64, .. } ∧ !{ x }`.)
   - a closed row conjoined with a positive-field atom it lacks; `{ l: A } ∧ { l: B }`
     with `A ≠ B` provably distinct concrete types.
   - two associated-type equality atoms `Assoc = X` and `Assoc = Y` for the same
     `(T, Aspect, Assoc)` projection where `X` and `Y` are **provably distinct concrete
     types after §1 specialization** — an associated type is uniquely fixed per
     implementing type (RFC-0082). Two equalities whose right-hand sides are distinct
     *method generic parameters* (`Deref<Target = U> ∧ Deref<Target = V>`) are **not** a
     conflict: they constrain `U = V` and are satisfiable. *(Round 2 finding — the first
     pass read `X ≠ Y` syntactically.)*
   - a `record T` requirement conjoined with a positive aspect bound `T: A` where `A` is
     non-local and no reachable impl makes any anonymous record an `A` — nominal structs
     do not satisfy the row bound and records cannot satisfy `A`, so the domain is empty.
     Scoped to the current module graph (a *local* aspect with a reachable record impl is
     satisfiable). *(Round 2 finding.)*

   **Not detected at first implementation** *(round 2 retreat)*: an empty domain that
   arises **only** via a reachable blanket — e.g. `T: Copy + !Tag` given a reachable
   `extend<T: Copy> T: Tag` with no negative override. Detecting this soundly needs the
   same negative-impl-priority reasoning the deferred blanket-entailment rule needs;
   both go to `metel-core#895`. Until then, such a declaration is accepted and any
   implementation conforms vacuously — a known, tracked limitation, not silent.

   A contradiction outside these shapes is conservatively **accepted** rather than risk a
   false positive, matching the "small explicit relation, no theorem prover" stance.

## References

- RFC-0034 — aspect bounds are conjunctive predicates on generic parameters and establish
  which methods a generic body may use.
- RFC-0036 — conditional `extend` blocks; this RFC does not change their selection or
  coherence conditions.
- RFC-0040 — enforcement of function aspect bounds at call sites.
- RFC-0071 — `Copy` and `Drop` mutual exclusion; in particular, `Copy` implies `!Drop`.
- RFC-0082 — associated types and equality constraints in aspect signatures.
- RFC-0118 — record kind and row bounds; this RFC relies on its distinction between a
  plain type parameter and a record-kinded one.
- RFC-0121 — open rows and row-conditional implementations; out of scope, but its row
  relations constrain the future entailment design.
- metel-core#541 — aspect implementation method-set and signature conformance repair.
- metel-core#617 — this RFC's review-accept-implement tracking issue (v0.13.0).
- metel-core#895 — deferred entailment-relation extensions (Open Questions 2 and 3):
  concrete-type-derived implications, negative-row calculus beyond the tabled cases, and
  projection-derived associated-type equality.
- metel-core#896 — `where` clauses on aspect-method declarations (Open Question 5's
  syntax piece, deliberately not in this RFC).

---

## Decision

**Outcome:** *(pending — Open Questions 1–6 resolved 2026-08-29, revised across two
adversarial review rounds; blanket-derived entailment and blanket-only empty-domain
detection retreated to `metel-core#895`. The remaining gate is an acceptance review
confirming that retreat is acceptable for v0.13.0 and re-checking the non-blanket
conflict shapes and the row decomposition.)*
**Target:** *(set when accepted; committed to v0.13.0 via metel-core#617.)*
