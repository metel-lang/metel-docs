---
id: rfc-0011
title: "Operator Overloading Aspects"
date: '2026-05-21'
status: draft
---

## Summary

Define the set of aspects that map to built-in operators (`+`, `-`, `*`, `/`, `%`, `==`, `<`, etc.), their method signatures, and how the compiler desugars operator expressions into aspect method calls.

---

## Motivation

Currently, operators are hardcoded for primitive types. User-defined types cannot participate in arithmetic, comparison, or equality expressions. Operator overloading via aspects (Rust/Haskell style) makes user types first-class in expressions without adding new syntax.

Additive safety: this feature can be added without breaking any existing v0.x programs.

Requires: the aspect system (v0.2).

---

## Rows and tuples (inherited from RFC-0151, 2026-11-15)

The language owner moved the remainder of RFC-0151 here: `Eq`, `Ord`/`PartialOrd` and `Hash` for every row. A tuple is
the row of integer labels (RFC-0151, implemented), so the rows' comparison is the tuples' comparison, and this RFC owns
it. Measured 2026-11-15 on `develop`:

- `==`, `!=`, `<`, `<=`, `>`, `>=` accept only primitive operands (numbers, booleans, `String`, `char`); they never
  dispatch through an aspect (`LIMIT-TYPE-CONSTRUCTION-003`). A struct with `Eq` is rejected, and so is
  `(1, 2) == (1, 2)` or `(1, 2) < (1, 3)`.
- `core.mtl` declares `Eq` with a single impl, `[T]: Eq where T: Eq`; primitives have none. There is no `Ord`,
  `PartialOrd` or `Hash` aspect.

What this RFC must therefore settle for rows, beside the operator aspects themselves:

- The `Eq`, `Ord`/`PartialOrd` and `Hash` impls of every row whose field types have them, written like the row `Clone` and
  `Display` impls, comparing fields in canonical label order (integers numerically first, then identifiers), so an
  integer-labelled row compares positionally. A field type without the aspect is `T0012`.
- `==`, `<` and the rest on a tuple and on an anonymous record dispatching through those aspects.
- Where `Ord` and `Hash` come from, since neither aspect exists.

Tracked by metel-core#2031 (`Eq`) and #2044 (`Ord`, `Hash`), blocked on this RFC reaching `3-integrated`.

---

## Open Questions

- **Aspect names**: `Add`, `Sub`, `Mul`, `Div`, `Rem` (Rust-style)? Something else?
- **Return type**: `Add` returns `Self`? Or an associated `Output` type (allows `Vec + Vec = Vec` and `Vec + &Vec = Vec`)?
- **Comparison aspects**: `Eq` (equality, `==`/`!=`) and `Comparable` / `Ord` (ordering, `<`/`<=`/`>`/`>=`) — are these unified or separate?
- **`Display` / `ToString`**: does string interpolation (RFC-0010) depend on a `Display` aspect here? If so, they need to be designed together.
- **Compound assignment** (`+=`, `-=`, etc.): separate `AddAssign` aspects or derived from `Add`?
- **Negation** (`-x`, `!x`): `Neg` and `Not` aspects?
- **Index operator** (`collection[i]`): an `Index` aspect with a method `fn index(self: *Self, i: I) -> T`? Should it panic on out-of-bounds or return `Option<T>`? This is the mechanism needed for `List<T>[i]` (RFC-0054) and future map/set types. If panicking, a separate `IndexChecked` aspect returning `Option<T>` may be warranted alongside it.

---

## Decision

**Outcome:** *(pending)*  
**Target:** *(blank until accepted)*

*(Decision rationale goes here when the RFC is evaluated.)*
