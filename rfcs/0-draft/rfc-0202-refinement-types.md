---
id: rfc-0202
title: "Refinement and Smart-Constructor Types"
date: '2026-11-01'
status: draft
---

## Summary

A **refinement type** is a type alias with an invariant:

```metel
type Percent := i64 satisfying (0 <= self && self <= 100);
```

It is a distinct nominal type (like a newtype, RFC-0200), but its only way in is a *checked*
construction. The invariant is evaluated once, at construction; afterwards the type is the
proof. Literals are checked at compile time through comptime evaluation (RFC-0132).

---

## Motivation

Today a smart constructor requires a one-field struct whose field is kept private:

```metel
pub struct Percent { value: i64 }
extend Percent {
    pub fun new(v: i64) -> Result<Percent, String> { ... }
}
```

That works, but the invariant is invisible to the compiler and to readers (it is buried in a
function body), every such type repeats the same boilerplate, literals pay a runtime check, and
the usual accessors (`unwrap`, ordering, arithmetic) must be rewritten by hand.

---

## Design

### 1. Declaration

```metel
type Name := Base satisfying (predicate);
```

`satisfying` is a contextual keyword. `self` in the predicate is the candidate value. The
predicate must be a **comptime-evaluable, side-effect-free expression** (RFC-0132's `comptime
fun` restrictions apply), so it can run at compile time and never has effects.

(`where` is not used: it already introduces aspect and row bounds, and overloading it for a
value predicate would be ambiguous.)

### 2. Generated surface

```metel
Percent::try_from(n: i64) -> Result<Percent, RefineError>   // runtime check
Percent::unchecked(n: i64) -> Percent                         // unsafe-marked; see below
p.get() -> i64                                                // read the base value
```

`RefineError` carries the failing predicate's source text and the offending value (Display).
`unchecked` is gated behind `unsafe` (RFC-0026) or restricted to the declaring module.

### 3. Literal checking

A literal of the base type in a context expecting the refined type is evaluated at compile time:

```metel
apply_discount(200, 15);      // ok: 0 <= 15 <= 100 holds
apply_discount(200, 150);     // error: 150 does not satisfy `0 <= self && self <= 100`
```

Non-literal values use `try_from`.

### 4. Flow-sensitive refinement (non-goal in this RFC)

The type system does **not** track facts (`if (n >= 0) { ... }` does not give `n` a refined
type). That would require a proof engine. Refinement is checked at construction only.

### 5. Operations

- A refined type has the base type's aspects only if derived (`deriving (Eq, Ord, Hash,
  Display)`), same mechanism as RFC-0200.
- Arithmetic is **not** forwarded: `Percent + Percent` can leave the range. Provide
  total-by-construction operations (`checked_add -> Option<Percent>`) or hand-write.
- Narrowing is free: `Percent` to `i64` is `get()`. Widening is `try_from`.
- A refinement can be refined further (`type Half := Percent satisfying (self <= 50)`); the
  predicates conjoin.

### 6. Example

```metel
type Port := i64 satisfying (1 <= self && self <= 65535) deriving (Eq, Display);

fun listen(p: Port) { ... }

fun main() {
    listen(8080);                                       // literal: checked now
    match (Port::try_from(read_int())) {
        Ok { value } => listen(value),
        Err { value } => println("bad port: ${value}"),
    }
}
```

---

## Interactions

- **RFC-0200 (newtypes):** a refinement is a newtype plus a predicate; `deriving` is shared.
- **RFC-0132 / RFC-0092 (comptime):** the predicate and literal check run through comptime.
- **RFC-0170 / RFC-0165 (literal types, unions):** `Port` could be seen as a large union of
  literal types; refinement avoids enumerating it.
- **RFC-0142 (checked arithmetic):** `checked_*` results feed `try_from`.
- **RFC-0119 (record conversions):** `try_from` follows the same naming; fallible direction.
- **RFC-0201 (pattern synonyms):** a partial synonym over a refined type gives `match` support.
- **RFC-0160 (aliases):** plain aliases stay transparent; only `satisfying` introduces identity.

---

## Alternatives considered

1. **Status quo** (private field + `new`). Fully expressible today; this RFC is ergonomics and
   compile-time literal checking.
2. **Full refinement/dependent types** (Liquid Haskell). Rejected: needs an SMT-style solver and
   a stable core surface (see roadmap *Compiler-ready pipeline*).
3. **Only literal types** (RFC-0170). Cannot express ranges.

---

## Open Questions

1. Is a `satisfying` keyword preferable to attribute syntax (`#refine(0 <= self && self <= 100)`)?
2. Must the predicate be total (never panics)? If it can overflow or divide by zero, what happens
   at compile time?
3. Does `unchecked` need `unsafe` (RFC-0026 is still a draft), or is module-private enough?
4. Do `Copy`/`Clone`/`Drop` of the refined type follow the base type unconditionally?
5. How are refined types represented in generic code (`List<Percent>`)? Zero-cost erasure is the
   goal; whether `try_from` in a loop is hoisted is an optimisation question.

---

## Decision

**Outcome:** *(pending)*
