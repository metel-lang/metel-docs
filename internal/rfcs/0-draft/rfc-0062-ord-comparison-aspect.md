---
id: rfc-0062
title: "Ord / Eq Comparison Aspects"
date: '2026-06-11'
status: draft
spec_status: pending
---

## Summary

Introduce comparison aspects in `std::core` — `Eq` for equality and `Ord` for
total ordering — plus an `Ordering` enum. This gives the standard library and
user code a way to abstract over "values that can be compared" instead of being
limited to the primitive numeric types the `<`, `>`, `==` operators are
hard-wired for today.

The immediate driver is `std::math` (`min`, `max`, `clamp`) and `List<T>`
ergonomics (`sort`, `contains`, `min`/`max`), all of which are currently blocked:
they need a comparison bound, but no such aspect exists, and per-type overloads
cannot be exported across module boundaries (METEL-188).

---

## Motivation

Sprint 23 added the first `List<T>` ergonomics (`map`/`filter`/`fold`/`find`/
`concat`) — all of which need only closures, not comparison. The next tier does
need comparison:

- `std::math`: `min(a, b)`, `max(a, b)`, `clamp(x, lo, hi)` over any ordered
  type. Implemented monomorphically they would be `min(i64, i64)` /
  `min(f64, f64)` overloads, but overload sets do not flow through imports
  (ADR-0038, METEL-188), so a `std::math::min` overload pair is not importable.
  A single generic `fun min<T: Ord>(a: T, b: T) -> T` is importable and correct.
- `List<T>`: `contains(value)` needs `Eq`; `sort()`, `min()`, `max()` need
  `Ord`. These were deliberately deferred from METEL-160 pending this aspect.
- User code: any generic container or algorithm that orders or dedupes values.

Today `<`, `<=`, `==`, … are intrinsic operators defined only on the primitive
numeric types, `boolean`, `Char`, and `String`. There is no way to write
`fun max<T: Ord>(a: T, b: T) -> T` because `T` has no comparison surface.

---

## Design

### `Ordering`

```metel
pub enum Ordering {
    Less,
    Equal,
    Greater,
}
```

A small `std::core` enum, the result of a three-way comparison. It can carry its
own ergonomic methods (`is_lt`, `is_eq`, `reverse`, …) in a follow-up.

### `Eq` and `Ord` aspects

Split equality from ordering (the Rust/Haskell model), so types that are
equatable but not orderable are expressible:

```metel
pub aspect Eq {
    fun eq(&self, other: &Self) -> boolean;
}

pub aspect Ord {
    fun cmp(&self, other: &Self) -> Ordering;
}
```

`Ord` does not declare `Eq` as a supertrait in the first cut (Metel has no
super-aspect mechanism yet — see Open Questions); the two are independent bounds.
Derived helpers (`lt`/`le`/`gt`/`ge` on `Ord`, and `min`/`max` free functions)
build on `cmp`.

### Primitive impls

`std::core` provides `Eq` and `Ord` impls for every primitive that the operators
already compare: the numeric types, `boolean`, `Char`, and `String`. These are
host-backed (`native(@std.core.cmp)` / `native(@std.core.eq)`), formatted by the
runtime value the same way the `Display`/`From` impls already are (one key, the
host switches on the runtime value — ADR-0039).

### Relationship to the built-in operators

Two options, to be settled during implementation:

1. **Operators stay intrinsic; aspects mirror them.** `<`/`==` remain
   hard-wired on primitives; `Eq`/`Ord` are a parallel, aspect-based surface used
   only through bounds. Simplest; minor duplication (a primitive defines
   comparison "twice", but both route to the same host comparison).
2. **Operators desugar to aspect methods.** `a < b` lowers to
   `Ord::cmp(&a, &b) is Less`, `a == b` to `Eq::eq(&a, &b)`. Unifies the two
   surfaces and makes operators work on any `Ord`/`Eq` type for free, but
   touches the typechecker's operator handling and the evaluator's `eval_binop`,
   and raises the question of operator overloading for user types.

This RFC proposes starting with option 1 (parallel surface) to unblock
`std::math` and `List` ergonomics without a binop-lowering rework, and tracking
option 2 (operator overloading via `Eq`/`Ord`) as a follow-up once the aspect
surface is proven.

### What this unblocks

```metel
// std::math
pub fun min<T: Ord>(a: T, b: T) -> T {
    match a.cmp(&b) { Ordering::Greater => b, _ => a }
}
pub fun max<T: Ord>(a: T, b: T) -> T {
    match a.cmp(&b) { Ordering::Less => b, _ => a }
}
pub fun clamp<T: Ord>(x: T, lo: T, hi: T) -> T { min(max(x, lo), hi) }

// List<T> (std::core)
impl List<T> {
    pub fun contains(self, value: T) -> boolean where T: Eq { … }
    pub fun max(self) -> Perhaps<T> where T: Ord { … }
    // sort: see Open Questions (needs a mutable in-place or returning form)
}
```

Aspect bounds on methods (`where T: Eq`) already work (sprint 17 / RFC aspect
bounds); the generic-method machinery to evaluate them landed in sprint 23.

---

## Interaction with other work

- **Overload exportability (METEL-188):** this RFC is the *alternative* to
  exportable overloads for the numeric-helper use case — a single generic
  bounded function instead of an overload set. The two are complementary.
- **`std::math` (METEL-163):** blocked on this; `std::math` should land as
  generic `Ord`-bounded functions once `Ord` exists, not as i64-only stopgaps.
- **`List<T>` ergonomics (METEL-160):** `contains`/`sort`/`min`/`max` are the
  second tranche, gated on `Eq`/`Ord`.
- **Structural aspect bounds (RFC-0061):** arrays/tuples of `Ord` elements being
  `Ord` is the same blanket-impl question deferred there.

## Open Questions

1. **Super-aspects.** Should `Ord` require `Eq` (`aspect Ord: Eq`)? Metel has no
   super-aspect syntax; adding one is its own small RFC. First cut: independent.
2. **Derivation.** Can `Eq`/`Ord` be auto-derived for user structs/enums
   (field/variant-wise), à la `#[derive(Ord)]`? Without derivation, user types
   must hand-write `cmp`. Likely a fast follow.
3. **`sort` shape.** In-place `sort(&mut self)` vs returning `sorted(self) ->
   List<T>`; depends on the mutation story for `List`.
4. **Operator desugaring.** Adopt option 2 (operators over `Eq`/`Ord`) and, if
   so, does that open user-defined operator overloading generally?
5. **Float ordering.** `f32`/`f64` are not totally ordered (NaN). Does `Ord` for
   floats use a total order (à la Rust `total_cmp`), or are floats `PartialOrd`
   only — implying a separate `PartialOrd`/`PartialEq` split?

## References

- ADR-0038 (overload resolution; why overloads are not exportable), METEL-188
- ADR-0039 (native bindings, value-driven host keys)
- RFC-0057 (stdlib layering; `std::math` scope), METEL-163
- RFC-0061 (structural aspect bounds; blanket-impl coherence)
- Rust `Ord`/`PartialOrd`/`Eq`/`PartialEq`; Haskell `Ord`/`Eq`
