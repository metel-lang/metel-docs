---
id: rfc-0168
title: "Equality Model and Super-Aspects"
date: '2026-09-09'
status: draft
---

## Summary

Replace the current single `Eq` comparison aspect with two aspects:

- `PartialEq` supplies equality operations that may be non-reflexive.
- `Eq: PartialEq` is an explicit marker that promises reflexive equality.

This RFC also introduces *super-aspects*: a declaration-level refinement relation
between aspects. A value satisfying a sub-aspect bound also satisfies each of its
super-aspect bounds. It is deliberately not general type subtyping or a runtime
conversion.

Finally, `==` and `!=` are defined as calls to `PartialEq`, rather than as a
separate intrinsic comparison system. Floats implement `PartialEq` but not `Eq`;
references compare their referents, not their storage identity.

---

## Motivation

RFC-0062 introduced `Eq` as the proposed common comparison surface. Its
implementation survey found a more fundamental problem: a single equality aspect
cannot accurately describe both integers and floating-point values. NaN is a
reachable floating-point value for which `x == x` is false. Generic code which
requires equality suitable for deduplication, keys, or equivalence reasoning must
be able to exclude that case.

The current situation also has two independent equality mechanisms:

- `Eq::eq` exists for user-defined types and structural arrays, but primitives do
  not implement it.
- `==` and `!=` are intrinsic and accept only selected primitive types.

That split means a generic `T: Eq` cannot express the ordinary equality operation,
and making primitives implement the existing `Eq` would give floats a misleading
contract. It would also leave operator behaviour separate from the abstraction
generic code uses.

The right model needs an implication relation: `T: Eq` should make `T: PartialEq`
available. Metel currently has aliases for *sets of bounds* (RFC-0039), but no way
for one nominal aspect to refine another. This RFC introduces the smallest such
mechanism needed for equality and future comparison aspects.

---

## Goals

- Make equality available to generic code through one normal aspect surface.
- State the difference between equality that can observe NaN and equality that is
  safe to treat as reflexive.
- Make `==` and `!=` follow the same dispatch and coherence rules as named
  equality operations.
- Provide nominal, transitive aspect refinement without introducing general
  subtyping.
- Settle reference comparison before references become a broadly usable feature.

## Non-goals

- General operator overloading. RFC-0011 remains the home for that larger design.
- Heterogeneous comparison such as `T == U`; this RFC uses `Self` on both sides.
- A full `PartialOrd` / `Ord` design, ordering of floating-point values, or the
  `Ordering` API proposed by RFC-0062.
- Automatic synthesis of equality implementations. RFC-0093 will eventually
  provide derive registration; this RFC only defines what such a derive must emit.
- Reference or object identity comparison. That needs a separate operation with a
  representation-independent contract.

---

## Design

### Equality aspects

`std::core` declares the following aspects:

```metel
pub aspect PartialEq {
    fun eq(&self, other: &Self) -> boolean;

    fun ne(&self, other: &Self) -> boolean {
        return !self.eq(other);
    }
}

pub aspect Eq: PartialEq;
```

`PartialEq` owns the operation because an equality relation can be useful even
when it is not reflexive. `ne` has a default body so implementations need only
define `eq`; an implementation may override it when that is observably useful.

`Eq` has no methods of its own. It is a statement by the implementation author
that the `PartialEq::eq` implementation is reflexive for values of the type:

```text
for every valid value x of T: x.eq(&x) == true
```

It is a semantic contract, like the intended laws of other standard aspects; the
compiler cannot generally prove it. The standard library and derives must not
implement `Eq` for a type whose equality can violate this law.

An ordinary equatable user type is implemented explicitly in two steps:

```metel
extend Ticket: PartialEq {
    fun eq(&self, other: &Ticket) -> boolean {
        return self.id == other.id;
    }
}

extend Ticket: Eq;
```

The separate `Eq` implementation is intentional. Implementing `PartialEq` never
silently promotes a type to the stronger contract.

### Super-aspects

An aspect declaration may list one or more direct super-aspects after its name:

```metel
pub aspect Ord: Eq {
    fun cmp(&self, other: &Self) -> Ordering;
}
```

This introduces an aspect-refinement relation. If `A: B` is declared, an
implementation or generic bound proving `T: A` also proves `T: B`. The relation
is transitive: if `A: B` and `B: C`, then `T: A` proves `T: C`.

For an explicit implementation `extend T: A`, every direct and transitive
super-aspect obligation must be satisfied. In the `Eq` example, `extend T: Eq`
is well-formed only when a coherent `T: PartialEq` implementation is available.
The implementation remains explicit; the compiler does not manufacture a
`PartialEq` implementation from an `Eq` marker or infer an `Eq` marker from an
implementation body.

Super-aspects are nominal declarations, not aliases. In particular, this:

```metel
aspect Key = Eq + Hash;
```

remains RFC-0039's transparent shorthand for a compound *bound*. It creates no
new implementation target and supplies no implication from `Key` to either
aspect. In contrast, `Eq: PartialEq` gives `Eq` its own nominal implementation
target and a durable semantic law.

The compiler rejects a cycle in the super-aspect graph, including an indirect
cycle. A super-aspect must name an already visible aspect. The initial design
permits only aspects, not aspect aliases, in the declaration list; aliases can
continue to be expanded where bounds are written.

This relation is not general subtyping: values do not have an `Eq` runtime type
which can be coerced to a `PartialEq` runtime type. It only expands what an
aspect bound proves to the type checker and what methods are available through
that proof.

#### Interaction with negative implementations

RFC-0081's negative implementations remain direct assertions. Positive
super-aspect satisfaction is transitive, while negative satisfaction is not:

- `T: Eq` implies `T: PartialEq`.
- `T: !PartialEq` makes `T: Eq` inconsistent and therefore forbidden.
- `T: !Eq` does not imply `T: !PartialEq`.

Any direct contradiction after super-aspect closure is a coherence error. This
keeps the meaning of a negative implementation local while preserving the
logical requirement imposed by a super-aspect.

### Equality operators

The language defines equality operators in terms of `PartialEq`:

```text
left == right  =>  PartialEq::eq(&left, &right)
left != right  =>  PartialEq::ne(&left, &right)
```

This notation specifies dispatch, not a new user-visible static-call spelling.
The operands are evaluated exactly once, from left to right, then shared-borrowed
for the call. Equality therefore does not move either operand. Type checking
requires the operand type to implement `PartialEq`; since the initial interface
uses `Self`, both operands have the same type.

The existing primitive intrinsic comparison implementation becomes the native
body behind the corresponding `PartialEq` implementations. There must be no
second intrinsic fallback once this migration lands: a call written as `.eq` and
one written as `==` have the same selected implementation and result.

This is a deliberately narrow first application of RFC-0011's operator
desugaring direction. Arithmetic, ordering, indexing, and any custom operator
syntax remain governed by that RFC.

### Standard implementations

The standard library provides both `PartialEq` and `Eq` for booleans, characters,
integers, strings, and other primitive value types whose equality is reflexive.
Floating-point types provide `PartialEq` only. Their `eq` implementation uses the
language's existing floating-point comparison semantics, including `NaN != NaN`.

Composite types may provide conditional implementations when all compared parts
meet the corresponding bound. For example, array equality is split from the
existing blanket implementation into the conceptual pair:

```metel
extend<T: PartialEq> T[]: PartialEq { /* element-wise equality */ }
extend<T: Eq> T[]: Eq;
```

Exact syntax for generic extensions follows the implementation grammar; the
important rule is that structural `Eq` is available only when every compared
component is itself `Eq`. Future derives follow the same rule rather than
assuming every field is reflexively equal.

### Reference equality

`&T` and `&var T` receive `PartialEq` conditionally when `T: PartialEq`.
Their equality compares the referenced values, not the address, allocation, or
borrow origin. They receive `Eq` when `T: Eq`.

This makes equality stable across the language's ownership and future storage
representation work: two references to equal values compare equal even when they
refer to different places. It also prevents a pointer-like identity observation
from accidentally becoming part of generic equality.

If identity comparison is needed later, it must be a separately named operation
with a contract that says what counts as the same place and how it behaves for
relocatable or internally referenced values. It is not an `Eq` implementation.

---

## Migration and implementation plan

1. Add super-aspect graph validation and transitive bound satisfaction to aspect
   resolution and coherence checking. Add fixtures for direct, transitive,
   missing-super-aspect, cycle, and negative-implementation cases.
2. Declare `PartialEq` and redefine `Eq` as its marker refinement. Migrate each
   existing `extend T: Eq { fun eq ... }` to `PartialEq`, then add a separate
   `Eq` marker only where its law holds. In particular, split the existing array
   blanket implementation.
3. Add native `PartialEq` implementations for all eligible primitive types and
   fixtures for floats and NaN.
4. Lower `==` and `!=` through `PartialEq`, with evaluation-order, borrow, and
   user-defined-dispatch fixtures. Remove the primitive-only intrinsic typing
   path only after parity is demonstrated.
5. Amend RFC-0062 so its ordering design can declare `Ord: Eq` if it retains a
   total-order contract. That decision is intentionally not made by this RFC.

The source break is controlled and appropriate before Metel's stable release:
existing custom `Eq` implementations move their `eq` method to `PartialEq` and
add `extend T: Eq;` when valid. Ordinary source expressions using `==` and `!=`
retain their spelling.

---

## Alternatives considered

### Keep a single `Eq` aspect

Rejected. It either lies about floating-point reflexivity or denies generic code
an equality operation for floats. A marker refinement captures the distinction
without encoding special exclusions into every equality-consuming API.

### Keep equality operators intrinsic

Rejected. It preserves the current mismatch between generic equality and surface
syntax, and it prevents user-defined types from participating in ordinary
equality. Using normal aspect dispatch gives equality the same coherence model as
the rest of the language.

### Make `Eq` automatically imply an implementation of `PartialEq`

Rejected. `Eq` has no implementation body from which `eq` could be derived.
More importantly, an explicit `PartialEq` implementation keeps the observable
comparison algorithm and the stronger law separate and reviewable.

### Use an aspect alias for `Eq + PartialEq`

Rejected. An alias is a convenient bound spelling, but cannot state that `Eq` is
semantically stronger than `PartialEq`, constrain implementations, or make a
`T: Eq` bound expose `PartialEq` methods.

### Compare references by identity

Rejected for language equality. Identity is a distinct question from value
equality and would couple `==` to storage representation and future relocation
choices. A later explicit identity API can make that trade-off visible.

---

## Open questions

1. Should the implementation spell a marker extension as `extend T: Eq;`, or
   require an empty body for uniformity with non-marker extensions? The RFC
   prefers the semicolon form if the parser can support it cleanly.
2. Does `ne` remain overridable, or should it be permanently defined as `!eq` to
   make equality laws easier to reason about? The default is sufficient for the
   initial implementation; an override should be retained only with a concrete
   performance or interoperability use case.
3. Which existing aggregate and standard-library types receive conditional
   `PartialEq`/`Eq` implementations in the first migration? Arrays are already
   present; the inventory should be made alongside the standard-library audit.
4. When RFC-0062 resumes, should `Ord: Eq` be required, and should it introduce
   a separate `PartialOrd` for floats? This RFC supplies the mechanism but does
   not decide ordering semantics.

---

## References

- [RFC-0062 — Ord / Eq Comparison Aspects](../0-draft/rfc-0062-ord-comparison-aspect.md)
- [RFC-0011 — Operator Overloading Aspects](../1-under-review/rfc-0011-operator-overloading.md)
- [RFC-0039 — Aspect Alias Syntax](../1-under-review/rfc-0039-aspect-alias-syntax.md)
- [RFC-0081 — Negative Implementations](../4-implemented/rfc-0081-negative-impls.md)
- [RFC-0093 — Derive Registration](../1-under-review/rfc-0093-derive-registration.md)
- [Rust Reference — operator expressions](https://doc.rust-lang.org/reference/expressions/operator-expr.html)
- [Rust `PartialEq` documentation](https://doc.rust-lang.org/std/cmp/trait.PartialEq.html)
- [Rust `Eq` documentation](https://doc.rust-lang.org/std/cmp/trait.Eq.html)
