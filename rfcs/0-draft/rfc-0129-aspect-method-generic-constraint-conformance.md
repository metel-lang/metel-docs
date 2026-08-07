---
id: rfc-0129
title: "Aspect Method Generic Constraint Conformance"
date: '2026-08-05'
status: draft
target:
---

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
`!Drop` row follows RFC-0071's normative mutual-exclusion rule. Projection-derived
equalities and the full negative-row calculus remain open questions below.

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

1. **Entailment implementation and extensibility.** The implementation must include
   language-defined implications such as `Copy => !Drop`; it must not inherit them
   incidentally from `type_satisfies_aspect` or the aspect registry. Decide the specified
   representation and extension point for this proof relation as new accepted RFCs add
   implications.
2. **Negative and mixed bounds.** The table requires positive/negative row implication
   where incompatible field types make a negative predicate follow. Specify the remaining
   mixed-conjunction implications required at first implementation and which are
   conservatively rejected until a later RFC extends the proof relation.
3. **Associated-type equality implication.** Dropping an equality requirement is already
   permitted by domain inclusion. Decide whether an aspect contract can entail another
   equality through a declared associated-type relation; that needs projection
   normalization not presently specified for generic declaration comparison.
4. **Row-bound inclusion with closed rows.** The direction is clear for open rows, but the
   exact relation among closed bounds, label-only fields, negative row bounds, and
   differently typed labels needs a complete table and fixtures before acceptance.
5. **Method `where` clauses on aspect declarations.** Implementation methods already have a
   `where` clause representation; aspect-method declarations currently store only inline
   generic parameters. Decide whether this RFC merely normalizes the forms already
   accepted, or also extends aspect method syntax to accept `where` clauses. The latter is
   syntax work and should not be smuggled in as a comparator detail.
6. **Contradictory domains.** If a declaration admits contradictory constraints such as
   `T: Copy + Drop`, its domain is empty and therefore is a subset of every implementation
   domain. Decide whether such constraints are rejected when declared or whether vacuous
   conformance is intentional and diagnosed separately.

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
- metel-core#617 — implementation follow-up for generic constraint-domain conformance.

---

## Decision

**Outcome:** *(pending)*
**Target:** *(set when accepted)*
