---
id: rfc-0149
title: "Aspect Method Constraint Domain Inclusion"
date: '2026-08-29'
status: under-review
target:
updated: '2026-08-29'
tracking: 'https://github.com/metel-lang/metel-core/issues/895'
---

> **Status — under review (2026-08-29).** Carved from RFC-0129: holds the domain-inclusion semantics, blanket-aware entailment engine, row-bound table, empty-domain rejection, and phase-ordering rule that RFC-0129 defers to ship a minimal structural-equality check in v0.13.0.

## Summary

Replace the structural constraint-equality check of RFC-0129 with **domain
inclusion**: an aspect-method implementation may *weaken* its generic constraints
relative to the aspect declaration, but never *strengthen* them. Inclusion is
proven by a bounded, coherence-aware **entailment relation** `⊢` that consults
reachable blanket and conditional `extend` impls (with RFC-0060/RFC-0081
negative-impl priority), so ordinary weakenings such as `T: Ord` in the aspect
and `T: PartialOrd` in the implementation are accepted rather than rejected as a
conservative wrong-no.

This RFC also settles what RFC-0129 deliberately left out or under-specified:
the row-bound entailment table, empty/contradictory-domain rejection, when an
aspect contract entails a *second* associated-type equality, and the phase
ordering of every one of these checks relative to `Self` / aspect-argument /
associated-type specialization.

## Motivation

RFC-0129 ships in v0.13.0 with a **structural constraint-equality** rule: after
normalization (alpha-renaming, bound reordering, deduplication, inline-vs-`where`
placement), an implementation method's generic-constraint conjunction must be
*identical* to the aspect method's. That is sound — it never admits an
implementation that accepts fewer instantiations than the aspect promises — but
it is needlessly strict. It rejects every one of these safe implementations:

```metel
aspect Inspect {
    fun keep<record T>(value: T) -> T;
}
extend Holder: Inspect {
    fun keep<T>(value: T) -> T { value }          // safe: accepts every record, rejected by RFC-0129
}

aspect CopyOnly {
    fun pass<T: Copy>(value: T) -> T;
}
extend Holder: CopyOnly {
    fun pass<T>(value: T) -> T { value }           // safe: strictly more general, rejected by RFC-0129
}

aspect Ordered {
    fun sort<T: Ord>(items: List<T>) -> List<T>;
}
extend Holder: Ordered {
    fun sort<T: PartialOrd>(items: List<T>) -> List<T> { /* ... */ }  // safe via the Ord: PartialOrd blanket, rejected by RFC-0129
}
```

Each implementation admits a **superset** of the type arguments the aspect
declaration admits, so no aspect-bound caller can reach a call the implementation
rejects. The purpose of the aspect declaration's constraints is to state a
caller-facing *lower bound*, not to pin the implementation's generality. RFC-0129
names this gap and defers it here (its Open Questions 1–4 and 6, and
metel-core#895).

Closing it properly needs three things RFC-0129 keeps out of v0.13.0:

1. a **directed entailment relation** rather than syntactic identity;
2. that relation must **consult reachable impls** — `Ord ⊢ PartialOrd` holds only
   because a blanket `extend<T: Ord> T: PartialOrd` exists, and only while no
   reachable `extend X: !PartialOrd` overrides it; and
3. a **complete row-bound table** and an explicit **empty-domain** rule, because a
   domain-inclusion check that cannot see `∅ ⊆ D_impl` would let any
   implementation vacuously "satisfy" an uninhabited aspect method.

## Goals

1. Define aspect-method generic-constraint conformance as `D_aspect ⊆ D_impl`
   (admissible-domain inclusion), superseding RFC-0129's structural equality.
2. Specify the entailment relation `⊢` that proves inclusion: its tabled base
   rules, its blanket-impl-derived rules, and its termination.
3. Give the complete row-bound entailment table (open, closed, label-only,
   negative; both directions) with fixtures.
4. Specify empty/contradictory-domain rejection at a method declaration,
   including the blanket-derived empty domains RFC-0129 cannot detect.
5. Decide whether an aspect contract can entail a second associated-type equality
   through a declared associated-type relation.
6. Fix the **phase ordering**: state, for every check above, whether it runs at
   aspect declaration, per specialized `extend`, or both — and where it sits
   relative to `Self` / aspect-argument / associated-type specialization.

## Non-Goals

- New generic-constraint syntax. `where` clauses on aspect-method *declarations*
  are metel-core#896, not this RFC.
- Aspect inheritance or a general nominal subtyping hierarchy.
- Changing conditional-`extend` selection, coherence, or orphan rules (RFC-0036,
  RFC-0060) — this RFC *reads* the reachable-impl set those rules define; it does
  not change it.
- Relaxing receiver, ordinary-parameter, or result-type conformance. RFC-0129 §1
  keeps those equal after specialization and this RFC does not touch them.
- A general theorem prover. `⊢` stays a bounded, enumerable relation; anything it
  cannot derive is a conservative wrong-no, reported as a narrowing error, never
  silently accepted.

## Terms

Carried from RFC-0129. For a method with generic parameters `G`, its **admissible
domain** is the set of concrete type-argument tuples that satisfy all constraints
on `G`. Constraints are conjunctive: record-kind requirement, positive and
negative aspect bounds, row bounds, and associated-type equality bindings.

The aspect declaration's domain is `D_aspect`; the specialized implementation
method's domain is `D_impl`. This RFC's conformance condition is

```text
D_aspect ⊆ D_impl
```

— input-side substitutability: the implementation may accept more instantiations,
never fewer.

## Proposal

### 1. Domain inclusion replaces structural equality

RFC-0129 §1 (specialization and shape-compatibility) and §3 (spelling
normalization) are unchanged and run first. This RFC replaces RFC-0129 §2: after
§1 specialization and §3 normalization to canonical conjunctive form, the
implementation method conforms iff

```text
D_aspect's constraint conjunction  ⊢  every atom of D_impl's constraint conjunction
```

Removing a constraint (weakening) is valid whenever `⊢` derives the remaining
atoms; adding a constraint (strengthening) is valid only if the added atom is
itself entailed by the aspect conjunction. An atom that is neither present nor
derivable is **not entailed**, and the implementation method is rejected exactly
as in RFC-0129 §4 (a type error on the `extend` method declaration; the method is
not registered for aspect dispatch).

### 2. The bounded entailment relation `⊢`

`⊢` is a **bounded, enumerable set of directed rules**, defined here and extended
only by a normative RFC that adds a new implication with fixtures. It is a
**sound** proof of `D_aspect ⊆ D_impl` and **deliberately incomplete**: semantic
inclusion may hold where the rules do not derive it, and those cases are
conservatively rejected.

The comparator must never call `type_satisfies_aspect(concrete_type, aspect)` —
that answers "does concrete type `X` satisfy aspect `A`", a different question
from "does constraint `P` entail constraint `Q`".

**Base rules** (the RFC-0129 table, retained):

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

- **Conjunction elimination** — `P ∧ Q ⊢ P`; `P ∧ Q ⊢ Q`. This is what makes "an
  omitted requirement is entailed" a rule rather than a special case, including an
  omitted associated-type equality.
- **`Copy(T) ⊢ !Drop(T)`** — RFC-0071 §4, the only fixed positive-aspect ⇒
  negative-aspect rule.
- **Associated-type identity** — `Deref<Target = U>(T) ⊢ Deref<Target = U>(T)`
  after §1 specialization, and by conjunction elimination `⊢ Deref(T)`. An
  equality *added* by the implementation is not entailed (rejected). Deriving a
  *second* equality is §6.
- **Row rules** — §4, after multi-label decomposition.

### 3. Blanket-derived entailment

This is the core of what RFC-0129 defers. Beyond the base rules, `⊢` derives an
aspect atom from a **reachable blanket or conditional `extend`**.

**Reachable-impl set.** The set of `extend` impls visible in the current module
graph under RFC-0036/RFC-0060 coherence — the same set conditional-`extend`
selection and negative-bound resolution already consult. This RFC reads it; it
defines no new visibility.

**Derivation rule (blanket).** Given a reachable

```metel
extend<G: P₁ + P₂ + … + Pₙ> G: A          // target is the bare parameter G
```

then `P₁(T) ∧ P₂(T) ∧ … ∧ Pₙ(T) ⊢ A(T)`, provided:

- **Bare-parameter target only.** The impl target is exactly the generic
  parameter `G`, not a constructor application (`Box<G>`, `List<G>`, …). A
  constructor target does not license `Pᵢ(T) ⊢ A(T)` for an arbitrary `T`.
- **Full premise conjunction.** *Every* bound `Pᵢ` on `G` — inline and `where`,
  including further row and associated-type bounds — must appear in `D_aspect`'s
  conjunction (each `Pᵢ` itself checked by `⊢`, recursively, under §7's depth
  bound). A partial premise match does not fire the rule.
- **Negative-impl priority (coherence).** The rule is **disabled for aspect `A`
  entirely** if the reachable-impl set contains *any* negative impl of `A` —
  `extend X: !A` or a conditional `extend<…> Y: !A` (RFC-0060/RFC-0081). A
  reachable negative impl means some `A`-shaped type is deliberately carved out,
  so no blanket premise universally entails `A`. This is deliberately coarse: it
  is sound, and it still admits the overwhelmingly common case (`Ord ⊢
  PartialOrd`, `Eq ⊢ PartialEq`, …) where nobody writes a negative impl.

**Bounded chaining.** Blanket rules compose: `Copy ⊢ Clone ⊢ …` is derived by a
fixed-point walk over the finite directed graph whose nodes are aspects and whose
edges are the reachable bare-parameter blankets. The walk terminates because the
aspect set is finite and each edge is visited once (same shape as RFC-0137's
Drop-dispatch fixpoint). A depth limit is not required for soundness but an
implementation may cap it and report the deeper case as a conservative wrong-no.

**Conditional-`extend` premises.** A reachable `extend<G: P> G: A` whose own
`where` clause references `Self` or associated types is admitted only after §7
specialization makes those concrete; if they remain abstract the rule does not
fire.

This subsection **supersedes RFC-0129 Open Question 1's retreat** and folds in the
"concrete-type-derived implications" bullet of metel-core#895.

### 4. Row-bound entailment

Row-bound forms (RFC-0118): open `{ l: T, .. }` ("has at least"), closed
`{ l: T }` ("has exactly"), label-only `{ l, .. }` ("has `l` at any type"),
negative `!{ l }` / `!{ l: T }`. Each denotes a set of concrete rows;
`bound_a ⊢ bound_i` iff `Dom(bound_a) ⊆ Dom(bound_i)`.

**Normalize multi-label bounds to per-label atoms first:**

- `{ a: A, b: B, .. }` → `{ a: A, .. } ∧ { b: B, .. }`
- `!{ a, b }` → `!{ a } ∧ !{ b }`
- `!{ a: A, b: B }` → `!{ a: A } ∧ !{ b: B }`
- `{ a, b, .. }` (label-only) → `{ a, .. } ∧ { b, .. }`
- `{ a: A, b: B }` (closed) stays one atom on the **aspect** side — closedness is
  a property of the whole row, not decomposable — but a closed aspect bound is a
  **singleton domain** `{ the row `{ a: A, b: B }` }`, so it entails **every impl
  atom that single row satisfies**: each contained typed-open atom
  (`{ a: A, .. }`, `{ b: B, .. }`), each contained label-only atom (`{ a, .. }`),
  and each negative atom the row does not violate (`!{ c }` for `c ∉ {a, b}`,
  `!{ a: X }` for `X ≠ A`). It matches a closed impl bound only when that bound is
  the identical row.

Each resulting atom is then checked by the table:

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

Rule of thumb: **open⇒open follows the field-subset direction**; **a closed
aspect bound is a singleton domain** that entails any impl bound that single row
satisfies; **a closed impl bound is entailed only from an identical closed aspect
bound**; **a negative impl bound is entailed from a positive/closed aspect bound
that provably cannot carry that label (or that label at that type)**. Fixtures:
one per row, positive for `yes`, a `T0012` at the `extend` method declaration for
`no`.

Negative-row implications *outside* the per-label type-conflict and decomposition
cases above (deeper reasoning about negative row bounds conjoined with other row
bounds) remain a conservative wrong-no; they are the "negative-row calculus"
bullet folded in from metel-core#895.

### 5. Empty and contradictory domains

A method — aspect *or* `extend` — whose generic-constraint conjunction is
**unsatisfiable** is a type error **at that method's own declaration**,
independent of conformance. An uninhabited signature is a bug regardless of who
implements it, and vacuous `∅ ⊆ D_impl` conformance would let any implementation
"satisfy" a nonsense aspect method.

Unsatisfiability is detected over a **closed set of conflict shapes**:

- `A(T) ∧ !A(T)` for the same aspect; `Copy(T) ∧ Drop(T)` (RFC-0071 §4).
- a **positive row bound of any kind** — open `{ l: A, .. }`, closed `{ l: A }`,
  or label-only `{ l, .. }` — conjoined with a negative bound over the **same
  label** that it violates: `!{ l }`, or `!{ l: A }` when the positive bound pins
  `l` to `A`.
- a closed row conjoined with a positive-field atom it lacks; `{ l: A } ∧ { l: B }`
  with `A` and `B` **provably distinct concrete types** (§8).
- two associated-type equality atoms `Assoc = X` and `Assoc = Y` for the same
  `(T, Aspect, Assoc)` projection where `X` and `Y` are **provably distinct
  concrete types after §7 specialization** (RFC-0082 fixes an associated type
  uniquely per implementing type). Two equalities whose right-hand sides are
  distinct *method generic parameters* (`Deref<Target = U> ∧ Deref<Target = V>`)
  are **not** a conflict — they constrain `U = V` and are satisfiable.
- a `record T` requirement conjoined with a positive aspect bound `T: A` for which
  the reachable-impl set (§3) contains **no impl making any anonymous record an
  `A`** — nominal structs do not satisfy the row bound and no record satisfies
  `A`, so the domain is empty. This applies whether `A` is local or non-local;
  the earlier "non-local only" scoping was a false negative — a *local* aspect
  with no reachable record impl has the same empty domain. If open-world
  assumptions later allow a downstream record impl, this rule weakens to "warn",
  but under the current closed-module-graph model it is a hard error.
- an empty domain arising **only via a reachable blanket** — e.g.
  `T: Copy ∧ !Tag` given a reachable `extend<T: Copy> T: Tag` and no reachable
  negative `Tag` impl. Detected with the same §3 machinery: if `⊢` derives
  `Copy(T) ⊢ Tag(T)` then `Copy(T) ∧ !Tag(T)` is unsatisfiable. This is the
  blanket-derived empty domain RFC-0129 explicitly cannot catch.

A contradiction **outside** these shapes is conservatively **accepted** rather
than risk a false positive, matching the "bounded relation, no theorem prover"
stance. Any such accepted-but-suspicious case is reported as a lint, not an
error.

### 6. Associated-type equality implication

RFC-0129 permits only *identical or omitted* associated-type equalities. This RFC
adds one derivation: an aspect contract entails a second equality
`T::X::Y == V` from `T::X == U ∧ U::Y == V` when both premise equalities are
present in `D_aspect` after §7 specialization and `X`, `Y` resolve through
declared associated-type relations (RFC-0082). No search beyond a single
projection step; a chain longer than one step is a conservative wrong-no.

This needs projection normalization for generic-declaration comparison, which
RFC-0082 does not currently specify. **This RFC amends RFC-0082** to define it for
this use, folding in the "projection-derived associated-type equality" bullet of
metel-core#895. Deriving one equality from an *unrelated* declared relation
remains out of scope.

### 7. Phase ordering

Every check above is defined **after** RFC-0129 §1 specialization, which
substitutes the `extend` block's target type for `Self`, its aspect arguments,
and its associated-type definitions into the aspect method signature. This RFC
makes the ordering explicit because §3's blanket premises, §5's conflict shapes,
and §6's projections can all depend on those substitutions:

1. **At aspect declaration.** Run §5's conflict detection on the aspect method's
   *own* conjunction, using only shapes that need no `Self` / aspect-argument /
   associated-type resolution (`A ∧ !A`, `Copy ∧ Drop`, per-label row conflicts
   between two literal bounds, two literal-concrete associated-type equalities).
   A conjunction unsatisfiable here is an error on the aspect, before any
   `extend`.
2. **Per specialized `extend`, after §1.** Re-run §5 for every shape whose
   satisfiability depends on the specialization — a `record T ∧ T: A` where `A`
   or the reachable record-impl set is only known once `Self` is concrete; a
   blanket-derived empty domain whose blanket premise mentions an associated
   type; associated-type equalities whose right-hand sides are only concrete
   after specialization. Then run §1–§4 conformance (`D_aspect ⊢ D_impl`) and §6.
3. **Reachable-impl queries (§3, §5's blanket and record-impl shapes) run in
   phase 2 only**, against the module graph as seen from the `extend` site.

An aspect method that is satisfiable in the abstract but uninhabited for a
particular `extend`'s specialization fails **at that `extend`**, not at the
aspect declaration. This resolves the round-3 finding that a single
declaration-time conflict check is too coarse for `Self`- and
associated-type-dependent constraints.

### 8. Mechanization

The relation and its side-conditions are stated as procedures so an
implementation and its fixtures agree on the boundary:

- **"Provably distinct concrete types."** Two types `X`, `Y` are provably
  distinct iff, after §7 specialization, both are closed (no free method-generic
  parameter, no unresolved projection) and are not syntactically equal modulo the
  normal type-equality relation (alias expansion, tuple/row canonicalization).
  If either still contains a free parameter or an unresolved projection, they are
  **not** provably distinct and the conflict/`no` does not fire (conservative
  accept for §5, conservative wrong-no for §4's `{ l: A } ⊬ { l: B }`).
- **The reachable-impl query.** Input: an aspect `A` and, for the blanket rule, a
  candidate premise conjunction. Output: (a) the set of reachable bare-parameter
  blankets `extend<G: P̄> G: A`; (b) a boolean "any reachable negative impl of
  `A`". Both computed from the same coherence-resolved impl set
  conditional-`extend` selection uses (RFC-0036/RFC-0060), evaluated at the
  `extend` site. No transitive impl search beyond the §3 blanket graph.
- **Chaining termination.** The §3 fixed-point walk maintains a visited set of
  aspects; it halts when no new aspect is added. Worst case linear in the number
  of reachable bare-parameter blankets.
- **Diagnostics.** A rejected narrowing names the aspect method and the specific
  unentailed atom, as in RFC-0129 §4. A phase-2 empty-domain error names the
  `extend` and the conflicting pair. A phase-1 empty-domain error names the
  aspect method.

## Alternatives considered

### Keep structural equality (RFC-0129 as shipped)

Sound and simple, but permanently rejects safe widening (`<record T>` → `<T>`,
`Ord` → `PartialOrd`) and makes a source spelling part of the aspect ABI. RFC-0129
accepts this only as an interim; this RFC exists to remove it.

### Blanket-derived entailment without negative-impl priority

`extend<G: P> G: A ⇒ (P ⊢ A)` unconditionally. Unsound: a reachable
`extend Special: !A` (RFC-0060/RFC-0081) means `Special` is a `P` type that is not
an `A` type, so `P ⊄ A`. Rejected — this was the round-2 finding that sent the
rule back to the tracker. §3's "disabled if any reachable negative impl of `A`"
is the sound recovery.

### Per-premise (partial) blanket matching

Fire `P ⊢ A` when *some* of a multi-premise blanket's bounds are present in
`D_aspect`. Unsound whenever the missing premise is the one that excludes a
counterexample. §3 requires the full premise conjunction.

### Full first-order entailment / a theorem prover

Complete but unbounded, unpredictable, and its failures are hard to explain at a
declaration site. Rejected in favor of a bounded, enumerable relation whose
non-derivations are conservative wrong-nos.

## Open questions

1. **Chaining depth cap.** §3's fixed-point walk terminates without a cap. Should
   the first implementation still impose a small depth limit (e.g. 4) and report
   deeper chains as wrong-nos, to bound worst-case analysis time on pathological
   impl graphs? Leaning yes, configurable.
2. **Open-world record impls.** §5's `record T ∧ T: A` empty-domain rule is a hard
   error under the closed-module-graph model. If Metel later admits downstream
   `extend`s that the defining crate cannot see, this must weaken to a warning.
   Decide whether to spell the weaker rule now (behind the closed-world
   assumption) or when open-world `extend` is actually on the table.
3. **`!Drop` beyond `Copy`.** The only positive⇒negative base rule is
   `Copy ⊢ !Drop`. Are there others that should be tabled now (e.g. a primitive
   scalar aspect ⊢ `!Drop`), or does every other such implication wait for its
   own RFC amendment as §2 requires?
4. **Interaction with RFC-0121 open rows.** §4's table is written against
   RFC-0118 row bounds. RFC-0121 (v0.14.0) generalizes rows; confirm the table
   rows survive unchanged or schedule a follow-up amendment.

## References

- RFC-0129 — Aspect Method Generic Constraint Conformance. Ships structural
  constraint equality in v0.13.0; this RFC replaces §2 of it with domain
  inclusion and resolves its Open Questions 1–4 and 6.
- RFC-0034 — aspect bounds are conjunctive predicates on generic parameters.
- RFC-0036 / RFC-0060 — conditional `extend` selection and impl coherence; this
  RFC reads the reachable-impl set they define.
- RFC-0060 / RFC-0081 — negative impls and their priority over blankets; §3's
  negative-impl-priority condition.
- RFC-0071 — `Copy` / `Drop` mutual exclusion; `Copy ⊢ !Drop`.
- RFC-0080 — standard aspects and blanket impls (v0.13.1); the blanket rules of
  §3 become useful once these exist.
- RFC-0082 — associated types and equality constraints; §6 amends it with
  projection normalization for generic-declaration comparison.
- RFC-0118 — record kind and row bounds; §4's table.
- RFC-0121 — open rows and row-conditional implementations (v0.14.0); Open
  Question 4.
- RFC-0137 — nominal types as branded rows; its Drop-dispatch fixpoint is the
  shape of §3's chaining walk.
- metel-core#541 — aspect implementation method-set and signature conformance
  repair; the origin of RFC-0129 and this RFC.
- metel-core#617 — RFC-0129's review-accept-implement tracker (v0.13.0).
- metel-core#895 — folded into this RFC (concrete-type-derived implications,
  negative-row calculus, projection-derived associated-type equality); its
  tracker is rescoped to this RFC.
- metel-core#896 — `where` clauses on aspect-method declarations; independent.

---

## Decision

**Outcome:** *(pending — carved from RFC-0129 on 2026-08-29 to hold the
domain-inclusion semantics, the blanket-aware entailment engine, the row-bound
table, empty-domain rejection, associated-type equality implication, and the
phase-ordering rule. RFC-0129 ships structural equality in v0.13.0 without any of
this. Needs a review pass on §3's negative-impl-priority soundness argument and
§7's phase split before acceptance.)*
**Target:** *(set when accepted; scheduled for v0.15.0 via the rescoped
metel-core#895 tracker.)*
