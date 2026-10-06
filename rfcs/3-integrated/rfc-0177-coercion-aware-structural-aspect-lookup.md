---
id: rfc-0177
title: "Coercion-Aware Structural Aspect Lookup"
date: '2026-10-06'
status: integrated
coverage:
  "1": { spec: "spec.declarations.structural-aspect-bounds.legality-2" }
updated: '2026-10-06'
tracking: 'https://github.com/metel-lang/metel-core/issues/1296'
impl_tracking: 'https://github.com/metel-lang/metel-core/issues/1296'
impl_status: not-started
---

> **Status — under review (2026-10-06).** The fixed-size array model is settled; review now covers coercion-aware structural lookup.

> **Status — accepted (2026-10-06).** The initial array coercion relation and lookup behavior are settled; user-defined coercions remain out of scope.

> **Status — integrated (2026-10-06).** Integrated the coercion-aware structural lookup contract into the structural aspect specification.

## Summary

Allow structural aspect bounds to discover and apply legal coercions such as [T; N] to [T] when selecting conditional implementations.

---

## Motivation

An array literal is an owning construction and therefore has a fixed-size type
`[T; N]`. The view type `[T]` is produced by borrowing or by the one-way
`[T; N]` → `[T]` coercion. Structural aspect implementations, however, are
registered for the view constructor:

```metel
extend<T: Display> [T]: Display { ... }
```

Today, a call with no syntactic expected type can fail before that coercion is
considered:

```metel
println([1, 2, 3]);
```

The literal is correctly inferred as `[i64; 3]`, but `println`'s `T: Display`
bound is satisfied through the structural `[T]: Display` implementation. If
structural lookup examines only the literal's initial type, it reports that
`[i64; 3]` does not implement `Display`, even though the legal coercion makes
the call valid.

This gap was previously hidden by making unconstrained literals default to
`[T]`. That workaround conflicts with the ownership model and makes an
unannotated mutable literal behave like an immutable borrowed view.

## Goals

- Preserve the intrinsic type of an expression while allowing legal coercions
  to participate in structural aspect-bound satisfaction.
- Make `println([1, 2, 3])` and equivalent generic calls valid without changing
  the ownership or lifetime rules of `[T]`.
- Keep coercion directional and deterministic: `[T; N]` may coerce to `[T]`,
  never in the reverse direction.
- Apply the same rule to nested structural values where an existing coercion
  path is available.

## Non-goals

- Adding new coercions or changing the `[T; N]` / `[T]` representation.
- Making structural values implement aspects unconditionally.
- Defining equality, hashing, ordering, or any aspect-specific semantics.

## 1. Coercion-aware lookup

Structural aspect lookup considers the finite set of types reachable from the
expression's intrinsic type through the language's legal, implicit coercions.

The checker models this with an internal coercion relation rather than with a
special case for arrays. A coercion edge has a source type, a target type, and
an insertion descriptor (for example, an array-to-view borrow). The relation
is directional and is queried only at implicit-coercion sites. It is not a
user-visible trait, and it does not permit user-defined conversion hooks.
The initial relation contains the existing `[T; N]` → `[T]` edge; later
built-in coercions can add edges without changing structural lookup's contract.

This deliberately does not expose Rust's `CoerceUnsized` surface. User-defined
coercions need a separate RFC covering coherence, generic propagation, and
runtime representation before they can be added to the relation.

For each candidate target, lookup checks the structural implementation and its
bounds. A candidate is applicable only when the coercion path and all bounds
are valid; the selected candidate records the coercion that must be inserted at
the use site.

For an array literal, construction therefore proceeds in this order:

1. Infer `[T; N]` from the literal elements.
2. When a surrounding call or bound requires `[T]`, resolve the structural
   implementation against `[T]` through the coercion relation and insert the
   selected `[T; N]` → `[T]` coercion.
3. Keep the literal's own type `[T; N]` for bindings, mutation, move checking,
   and all contexts that do not require a view.

The candidate search must not repeatedly apply coercions or infer through a
cycle. It uses the existing coercion graph, rejects ambiguous equal-cost
paths, and reports the ordinary bound diagnostic when no reachable target has
an applicable implementation. This is lookup behavior, not a new implicit
conversion rule.

## Worked examples

```metel
var values := [1, 2, 3]; // [i64; 3], owning and mutable
values[0] = 9;

println(values);         // borrow/coerce to [i64] for Display
println([1, 2, 3]);      // infer [i64; 3], then coerce for Display
```

An explicitly view-typed binding continues to work through the same coercion:

```metel
let view: [i64] := [1, 2, 3];
```

The reverse direction remains invalid:

```metel
fun needs_fixed(xs: [i64; 3]) { }
let view: [i64] := [1, 2, 3];
needs_fixed(view); // type error: a view has no statically known length
```

## Interaction with structural aspect bounds

The rule applies to conditional implementations for structural constructors,
including array `Display`, `Clone`, and `Eq` implementations. It does not make
`[T; N]` and `[T]` the same type, and it does not cause an aspect implementation
for `[T]` to appear in ordinary type identity or coherence checks for
`[T; N]`. Coherence continues to reason about the declared target constructor;
the coercion is considered only when satisfying a use-site requirement.

## Implementation guidance

The checker should retain the intrinsic type and a selected coercion descriptor
separately. Candidate enumeration must be bounded by the finite built-in
relation, and the selected path must be carried into elaboration so diagnostics
can name both the original expression and the required target. The detailed
candidate-enumeration and diagnostic provenance belong in an ADR; this RFC
specifies only the observable lookup rule and the internal relation's contract.

## Open questions

None for the array coercion case. Generalizing the same mechanism to future
user-defined coercions is out of scope and requires a separate design.
