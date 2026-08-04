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

## Open Questions

- **Aspect names**: `Add`, `Sub`, `Mul`, `Div`, `Rem` (Rust-style)? Something else?
- **Return type**: `Add` returns `Self`? Or an associated `Output` type (allows `Vec + Vec = Vec` and `Vec + &Vec = Vec`)?
- **Comparison aspects**: `Eq` (equality, `==`/`!=`) and `Comparable` / `Ord` (ordering, `<`/`<=`/`>`/`>=`) — are these unified or separate?
- **`Display` / `ToString`**: does string interpolation (RFC-0010) depend on a `Display` aspect here? If so, they need to be designed together.
- **Compound assignment** (`+=`, `-=`, etc.): separate `AddAssign` aspects or derived from `Add`?
- **Negation** (`-x`, `!x`): `Neg` and `Not` aspects?
- **Index operator** (`collection[i]`): an `Index` aspect with a method `fn index(self: *Self, i: I) -> T`? Should it panic on out-of-bounds or return `Perhaps<T>`? This is the mechanism needed for `List<T>[i]` (RFC-0054) and future map/set types. If panicking, a separate `IndexChecked` aspect returning `Perhaps<T>` may be warranted alongside it.

---

## Decision

**Outcome:** *(pending)*  
**Target:** *(blank until accepted)*

*(Decision rationale goes here when the RFC is evaluated.)*
