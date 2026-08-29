---
id: rfc-0129
title: "Aspect Method Generic Constraint Conformance"
date: '2026-08-05'
status: implemented
target:
updated: '2026-08-29'
tracking: 'https://github.com/metel-lang/metel-core/issues/617'
coverage:
  "1": { spec: "spec.declarations.aspects.implementing-an-aspect.legality-12" }
  "2": { spec: "spec.declarations.aspects.implementing-an-aspect.legality-13" }
  "3": { spec: "spec.declarations.aspects.implementing-an-aspect.legality-13" }
  "4": { spec: "spec.declarations.aspects.implementing-an-aspect.legality-14" }
impl_tracking: 'https://github.com/metel-lang/metel-core/issues/617'
impl_status: implemented
---

> **Status — under review (2026-08-23).** Real substantiated proposal. Its own
> References section names #617 as the review-accept-implement tracker.
> **Cut to a minimal interim 2026-08-29.** The original proposal compared generic
> constraints by **admissible-domain inclusion** (`D_aspect ⊆ D_impl`) with a
> bounded entailment relation. Six open questions and three adversarial review
> rounds showed the entailment relation needs real design — it has to consult
> reachable blanket impls with coherence-aware negative-impl priority to accept
> ordinary weakenings like `T: Ord` → `T: PartialOrd` soundly. Rather than grow
> v0.13.0, that whole part is carved into **RFC-0149 (Aspect Method Constraint
> Domain Inclusion)**, scheduled for v0.15.0. What remains here, and ships in
> **v0.13.0** via #617, is a sound minimum: after normalization the
> implementation method's generic-constraint conjunction must be **structurally
> equal** to the aspect method's, with record kind included. This fixes the
> metel-core#616 unsoundness (an implementation could silently add `record T`)
> and conservatively rejects safe widening as a wrong-no until RFC-0149 lands.

> **Status — accepted (2026-08-29).** Minimal structural-equality rule (record kind included, resolved-identity comparison) accepted for v0.13.0; admissible-domain inclusion and the entailment engine are RFC-0149. Four adversarial review rounds, no open blockers.

> **Status — integrated (2026-08-29).** Minimal structural-equality rule integrated into reference/spec/declarations.md (implementing-an-aspect legality-12..14), blocked-exempt pending implementation. Domain inclusion is RFC-0149.

> **Status — implemented (2026-08-29).** Structural-equality generic-constraint conformance implemented and merged to metel-core develop (PR #897, #617); fixtures under typechecking/aspects/stage21_* cite RFC-0129 sections 1-4.

## Summary

Define, for v0.13.0, when an aspect-method implementation's generic constraints
conform to the aspect method's: signature shape after specialization, and
**structural equality** of the normalized generic-constraint conjunction
(record kind included). Admissible-domain inclusion — allowing the implementation
to weaken constraints — is RFC-0149.

## Motivation

An aspect declaration is a promise made to every caller constrained by that
aspect. An `extend Type: Aspect` block supplies the implementation behind that
promise. Method-name completeness alone is insufficient: if the implementation
accepts fewer generic instantiations than the aspect declaration, a generic
caller can make a call the aspect admits but the implementation rejects or cannot
type-check safely.

The gap surfaced while fixing the pre-existing inconsistency where an aspect
implementation could add methods the aspect never declared (metel-core#541). The
first attempted signature-conformance check (PR #616) had two opposite failures:

```metel
// It rejected a safe implementation...
aspect Inspect {
    fun keep<record T>(value: T) -> T;
}
struct Holder {}
extend Holder: Inspect {
    fun keep<T>(value: T) -> T { value }
}

// ...and it failed to reject an unsafe one.
aspect AnyValue {
    fun keep<T>(value: T) -> T;
}
extend Holder: AnyValue {
    fun keep<record T>(value: T) -> T { value }
}
```

The first is safe: every record admitted by `Inspect::keep` is a valid
instantiation of the unconstrained implementation. The second is not: a caller
with only an `AnyValue` bound may call `keep(1)`, while the implementation
requires a record.

The fully general rule is **admissible-domain inclusion** — the implementation
must accept every instantiation the aspect admits, and may accept more. Proving
that inclusion soundly requires an entailment relation that reasons about
reachable blanket impls and negative-impl coherence (see RFC-0149). For v0.13.0
this RFC ships the sound subset that needs none of that machinery: require the
normalized constraint conjunctions to be **equal**, with record kind included so
neither direction of `<T>` ↔ `<record T>` slips through. Safe widening
(`<record T>` → `<T>`, `T: Copy` → `<T>`) is rejected as a conservative wrong-no
until RFC-0149.

## Goals

1. Define when an implementation method's generic constraints conform to an
   aspect method's, for v0.13.0: normalized structural equality, record kind
   included.
2. Keep signature shape (receiver form, ordinary parameter count and types,
   result type) required to match after `Self`, aspect-argument, and
   associated-type specialization.
3. State which source-level differences are irrelevant: alpha-renaming, bound
   reordering, duplicate bounds, and inline-vs-`where` placement.
4. Give an implementable diagnostic boundary: a non-conforming implementation is
   reported at the `extend` method declaration, before that method is registered
   for aspect dispatch.

## Non-Goals

- **Admissible-domain inclusion** (letting the implementation weaken
  constraints), the entailment relation, the row-bound entailment table,
  empty/contradictory-domain rejection, and their phase ordering. All of that is
  **RFC-0149**.
- Adding new generic-constraint syntax. `where` clauses on aspect-method
  *declarations* are metel-core#896.
- Aspect inheritance or a general subtyping hierarchy.
- Changing conditional-`extend` selection, coherence, or orphan rules (RFC-0036,
  RFC-0060).
- Relaxing receiver, ordinary parameter-type, or result-type conformance.

## Terms

For a method with generic parameters `G`, its **admissible domain** is the set of
concrete type-argument tuples that satisfy all constraints on `G` — conjunctive
across record kind, positive and negative aspect bounds, row bounds, and
associated-type equality bindings.

The general conformance condition, which **RFC-0149** formalizes, is
`D_aspect ⊆ D_impl` (the implementation accepts a superset). This RFC ships a
sound approximation of it: the normalized constraint conjunctions must be
**equal**, which implies `D_aspect = D_impl ⊆ D_impl`.

## Primary proposal

### 1. Method signatures remain specialized and shape-compatible

Before generic constraints are compared, the compiler specializes the aspect
method using the `extend` block's target type, aspect arguments, and
associated-type definitions. `Self`, an aspect parameter, and an associated type
therefore compare against their concrete implementation meanings. Method-generic
parameter names compare alpha-equivalently.

Receiver form, ordinary parameter count and types, and result type must remain
equal after this specialization. This RFC changes only how method-generic
constraints are compared.

### 2. Constraints compare by structural equality after normalization

After §1 specialization and §3 normalization to canonical conjunctive form, the
implementation method conforms iff its generic-constraint conjunction is
**identical** to the aspect method's. Identity is over **resolved canonical
atoms** — every aspect, type, associated-type, and row-label reference stands for
the entity name resolution and §1 specialization bind it to, never its source
spelling. Two atoms that print the same but resolve to different entities (an
aspect `Printable` that is `a::Printable` on the aspect side and `b::Printable`
on the `extend` side) are **not** identical.

The atoms compared, per corresponding generic parameter:

- the same **record-kind requirement**. `GenericParam.is_record` is part of the
  comparison (the metel-core#616 fix); §3 first folds a `where`-clause record
  marker into that flag, so the binder and `where` spellings compare equal.
- the same set of positive and negative **aspect bounds**, by resolved aspect
  identity and resolved type arguments.
- the same set of **row bounds**, by resolved label and resolved field type.
- the same set of **associated-type equality bindings**. A binding is identified
  by its **resolved projection key** — `(resolved aspect, associated-type name)`
  applied to the parameter — and two bindings are the same iff their projection
  keys are equal *and* their right-hand sides are equal under normal type
  equality after §1 specialization (alias expansion included). A binding whose
  projection or right-hand side is still unresolved, or resolves differently on
  the two sides, is **not** the same binding.

Adding a constraint (strengthening) and removing one (weakening) are **both**
rejected. Weakening is sound in principle — RFC-0149 will accept it — but is a
wrong-no here.

```metel
aspect CopyOnly {
    fun pass<T: Copy>(value: T) -> T;
}
extend Holder: CopyOnly {
    fun pass<T: Copy>(value: T) -> T { value }   // valid: identical
    // fun pass<T>(value: T) -> T { value }      // rejected here; RFC-0149 accepts it
}

aspect AnyValue {
    fun pass<T>(value: T) -> T;
}
extend Holder: AnyValue {
    fun pass<T: Copy>(value: T) -> T { value }   // rejected: strengthening (unsound)
}
```

### 3. Normalize source spelling before checking equality

Normalization first **resolves and specializes**: every identifier in a bound is
replaced by the entity it resolves to in its own scope, and §1's `Self` /
aspect-argument / associated-type substitution is applied. The §2 equality check
runs on the result — it never compares raw identifiers or pretty-printed text.

The following then do not change a method's admissible domain and must not affect
conformance:

- alpha-renaming method generic parameters (`T` versus `U`);
- reordering independent conjunctive bounds;
- duplicate bounds;
- placing a constraint inline or in a method `where` clause, where that syntax is
  available; and
- writing the record kind at the generic binder (`<record T>`) versus in a
  `where` clause. RFC-0118 record-kinds the parameter from either position;
  canonicalization computes the effective `GenericParam.is_record` from both
  before §2 compares it.

The comparison is over the whole generic parameter tuple, not one independent
list per parameter. A bound may mention another method generic parameter, for
example `T: From<U>`; the compiler must preserve that relation when normalizing.

### 4. Diagnostics and dispatch

A non-conforming implementation is a type error on the implementing method
declaration. It must not be registered as satisfying the aspect, and it must not
contribute to aspect method dispatch. The diagnostic names the aspect method and
the differing constraint, for example:

```text
`Holder::pass` does not match the generic constraints of `AnyValue::pass`:
aspect declares `T` with no bound, implementation requires `T: Copy`
```

A rejected weakening should additionally point at RFC-0149:

```text
`Holder::keep` weakens generic parameter `T` (`record T` → `T`); constraint
weakening is not supported in v0.13.0. See the RFC-0149 proposal for the planned
domain-inclusion rule.
```

## Alternatives considered

### Admissible-domain inclusion now (the original RFC-0129 proposal)

Compare by `D_aspect ⊆ D_impl` so the implementation may weaken constraints.
This is the right long-term rule, but a sound inclusion check must derive
entailments like `T: Ord ⊢ T: PartialOrd` from reachable blanket impls while
honoring an explicit `extend X: !PartialOrd` (RFC-0060/RFC-0081), plus a complete
row-bound table and an explicit empty-domain rule. Three adversarial review
rounds established that this is a real design piece, not a comparator detail.
Deferred to **RFC-0149** (v0.15.0) rather than grown inside v0.13.0.

### Require the implementation to repeat the aspect constraints verbatim

A stricter form of equality that also forbids the normalization in §3. Predictable
but forces duplication and makes source spelling part of the ABI. Rejected;
§3 normalization is kept.

### Permit arbitrary differences and defer failures to method-body checking

Accepts an implementation that needs `record T` for an aspect method callable
with any `T`. The aspect-bound caller is type-checked against the declaration, so
a bad call can reach an implementation whose body relies on a property the caller
did not prove. Rejected as unsound — this is exactly the metel-core#616 hole this
RFC closes.

## Open questions

*All six original open questions were resolved 2026-08-29, then the resolutions
were reworked across three adversarial review rounds into **RFC-0149**. This RFC
keeps only the parts that need no entailment relation, so it has no open
questions of its own. For the record, where each went:*

1. **Entailment implementation and extensibility** → RFC-0149 §2–§3 (bounded,
   coherence-aware relation `⊢`).
2. **Negative and mixed bounds** → RFC-0149 §4 (row table) and §2.
3. **Associated-type equality implication** → RFC-0149 §6 (single projection
   step; amends RFC-0082).
4. **Row-bound inclusion with closed rows** → RFC-0149 §4 (full table with
   fixtures).
5. **Method `where` clauses on aspect declarations** → normalize-only here (§3);
   the syntax extension is metel-core#896.
6. **Contradictory domains** → RFC-0149 §5 (empty-domain rejection) and §7
   (phase ordering). Not reachable under this RFC's equality rule: an
   unsatisfiable aspect conjunction is simply matched verbatim by a conforming
   implementation, which RFC-0149 diagnoses.

## References

- RFC-0149 — Aspect Method Constraint Domain Inclusion. The general
  `D_aspect ⊆ D_impl` rule, the entailment relation, the row-bound table,
  empty-domain rejection, and phase ordering. Supersedes §2 of this RFC when it
  lands (v0.15.0). Absorbs the former metel-core#895 scope.
- RFC-0034 — aspect bounds are conjunctive predicates on generic parameters.
- RFC-0036 — conditional `extend` blocks; this RFC does not change their
  selection or coherence conditions.
- RFC-0040 — enforcement of function aspect bounds at call sites.
- RFC-0071 — `Copy` and `Drop` mutual exclusion.
- RFC-0082 — associated types and equality constraints in aspect signatures.
- RFC-0118 — record kind and row bounds; this RFC relies on its distinction
  between a plain type parameter and a record-kinded one.
- metel-core#541 — aspect implementation method-set and signature conformance
  repair.
- metel-core#616 — the PR whose signature comparator this RFC corrects (record
  kind omitted; equality rejected valid widening — the latter stays a wrong-no
  until RFC-0149).
- metel-core#617 — this RFC's review-accept-implement tracking issue (v0.13.0).
- metel-core#896 — `where` clauses on aspect-method declarations (Open Question
  5's syntax piece, deliberately not in this RFC).

---

## Decision

**Outcome:** **Accepted, integrated, and implemented 2026-08-29.** Scope cut to
normalized structural equality with record kind included; admissible-domain
inclusion and the entailment relation moved to RFC-0149. Integrated into
`reference/spec/declarations.md` as
`spec.declarations.aspects.implementing-an-aspect.legality-12`–`legality-14`, and
implemented in the frontend typechecker via metel-core#897 (#617), with fixtures
under `typechecking/aspects/stage21_*`.
**Target:** v0.13.0, via metel-core#617.
