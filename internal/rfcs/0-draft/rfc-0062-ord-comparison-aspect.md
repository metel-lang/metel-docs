---
id: rfc-0062
title: "Ord / Eq Comparison Aspects"
date: '2026-06-11'
status: draft
updated: '2026-07-21'
---

> **Status — draft, surveyed against the implementation 2026-07-21.** Partially shipped
> ahead of this RFC and currently unusable for the case that matters; §"Current state"
> below records exactly what exists. The equality half is also entangled with two
> deliberately-open questions elsewhere (`==`'s operand rules, metel-core#279/#263; and
> whether two references compare referents or identity, metel-core#282/#263), so this RFC
> is **not** ready to implement as written.

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

## Current state (surveyed 2026-07-21)

Parts of this RFC shipped ahead of it, and the result is a surface that exists but cannot
be used for primitives — which is every motivating case above.

**Exists:**

- `pub aspect Eq { fun eq(&self, other: &Self) -> boolean; }` — `stdlib/core.mtl:194`,
  exactly as §"`Eq` and `Ord` aspects" proposes.
- A structural blanket impl `extend<T: Eq> T[]: Eq` — `stdlib/core.mtl:436` — plus its
  helper `__eq_array_item<T: Eq>`.
- Working method dispatch: a user type that hand-writes `eq` can be compared, and arrays
  of it compare element-wise (fixture `evaluator/aspects/78_array_eq_structural_impl.mtl`).

**Missing, and the gap that matters:**

- **No primitive impls.** No numeric type, `boolean`, `Char` or `String` implements `Eq`.
- `Ord`, `Ordering`, and the derived helpers do not exist at all.

The consequence is that the machinery already in stdlib does not work for primitives:

| | |
|---|---|
| `1.eq(&2)` | `T0003` no method `eq` on `i64` |
| `[1,2].eq(&[1,2])` | `T0012` `i64` does not implement `Eq` |
| `fun same<T: Eq>(..)` called with `i64` | `T0012` |
| user type with a hand-written impl | works |

So the blanket array impl and every `where T: Eq` bound in stdlib are, today, reachable
only by hand-written user impls. **Adding the primitive `Eq` impls is the single smallest
change that makes the existing surface work**, and it needs no operator changes: it follows
the established `Display`/`to_string` pattern exactly — one `NativeKey`, one host function
switching on the runtime value, and one `extend <prim>: Eq { native(@std.core.eq) … }` block
per primitive (13 of them, mirroring the 13 `Display` impls).

That is deliberately *not* proposed as the next step here — see "Why this is not ready".

---

## Why this is not ready (2026-07-21)

Three things changed after this RFC was drafted, and together they mean the equality half
should not be built as written.

**1. The ideal design is a `PartialEq`/`Eq` split, and it is out of scope.** Open Question 5
asks how floats fit. NaN is reachable in Metel today (`0.0/0.0`, and `n == n` is `false`),
so a single `Eq` aspect covering floats cannot promise reflexivity, and generic code over
`T: Eq` cannot rely on it. Rust's answer — `PartialEq` for everything, `Eq` as a marker
refining it — is the right shape and is **explicitly out of scope for current objectives**.
It also depends on Open Question 1: Metel has no super-aspect mechanism, so `aspect Eq:
PartialEq` cannot be written today. Until that decision is taken, adding primitive `Eq`
impls would bake in the wrong answer at the point where it is most expensive to change —
`std::core`'s public surface.

**2. `==`'s operand rules are open.** metel-core#279 added a guard rejecting `==` on
anything other than the primitive scalars, `boolean`, `String` and `Char`, because it
previously typechecked and then aborted at run time. That guard is deliberately
*direction-neutral*: it does not decide whether `==` should eventually dispatch through
this aspect (option 2 below), and it must not be relaxed by accident.

**3. Reference equality is open.** Whether two references compare referents (Rust) or
identity (Go) is unresolved — see the design note on metel-core#263. Any `Eq` impl covering
references would settle it silently.

**None of these block the *ordering* half.** `Ord`, `Ordering`, and `min`/`max`/`clamp` do
not touch `==`'s rules or reference equality, and floats affect `Ord` only through the same
Open Question 5 (total vs partial order). If this RFC is split, the ordering half is the
part that can move first.

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
5. **Float ordering — and float *equality*.** `f32`/`f64` are not totally ordered (NaN).
   Does `Ord` for floats use a total order (à la Rust `total_cmp`), or are floats
   `PartialOrd` only — implying a separate `PartialOrd`/`PartialEq` split?

   **Sharpened 2026-07-21: this bites `Eq` too, not only `Ord`, and it is the question
   that currently blocks the equality half.** NaN is reachable today (`0.0/0.0`, and
   `n == n` is `false`), so a single `Eq` covering floats cannot promise reflexivity.
   Three answers, and the preferred one is out of scope:

   - *Split `PartialEq`/`Eq` (and `PartialOrd`/`Ord`).* **The ideal design**, and the one
     to adopt eventually. Blocked twice over: it needs the super-aspect mechanism of Open
     Question 1, which does not exist, and it is out of scope for current objectives.
   - *One `Eq`, floats included.* `Eq` means "has an equality operation", not "is an
     equivalence relation". Matches today's `==` exactly and needs no new machinery, but
     bakes a weaker guarantee into `std::core`'s public surface, which is the most
     expensive place to change later.
   - *One `Eq`, floats excluded.* Preserves reflexivity, at the cost of `List<f64>::contains`
     and `[f64].eq(..)` failing while `==` on floats works — a distinction users would find
     arbitrary.

   Because the preferred answer is unavailable and the two fallbacks both cost something
   permanent in a public API, the equality half waits. See "Why this is not ready".

6. **Does the array blanket impl belong to this RFC?** `extend<T: Eq> T[]: Eq` already
   exists in stdlib, written before this RFC and before RFC-0061 (Structural Aspect
   Bounds), which owns blanket impls over structural types. Whether it is this RFC's,
   RFC-0061's, or already-settled precedent for both has never been established, and it is
   currently dead weight — no primitive satisfies its `T: Eq` bound.

## References

- ADR-0038 (overload resolution; why overloads are not exportable), METEL-188
- ADR-0039 (native bindings, value-driven host keys)
- RFC-0057 (stdlib layering; `std::math` scope), METEL-163
- RFC-0061 (structural aspect bounds; blanket-impl coherence)
- Rust `Ord`/`PartialOrd`/`Eq`/`PartialEq`; Haskell `Ord`/`Eq`
