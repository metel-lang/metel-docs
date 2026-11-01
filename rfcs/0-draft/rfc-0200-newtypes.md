---
id: rfc-0200
title: "Newtypes with Aspect Forwarding"
date: '2026-11-01'
status: draft
---

## Summary

A `newtype` declares a **distinct nominal type with exactly one field**, and may list aspects
to **forward** to the inner type:

```metel
newtype UserId := i64 deriving (Eq, Ord, Hash, Display);
newtype Meters := f64 deriving (Eq, Ord, Add, Sub, Display);
```

A newtype is a thin form of `struct`: same representation as the inner type, but a different
type identity. Forwarded aspects are derived mechanically. Every other aspect must be
implemented by hand, so a newtype never silently inherits behaviour.

---

## Motivation

Type aliases (RFC-0160) are transparent, so `type UserId := i64` offers no protection against
passing a `Meters` where a `UserId` is expected. The workaround is a one-field `struct`, but
each aspect (`Eq`, `Ord`, `Hash`, `Display`, `Add`, ...) then needs a hand-written forwarding
`extend` block, which is exactly the boilerplate that causes people to skip the wrapper.

Branded rows (RFC-0137) already give every struct nominal identity, and `#derive` (RFC-0093)
provides the mechanism for generating impls. What is missing is the declaration form that
combines them.

---

## Design

### 1. Declaration

```metel
newtype Name<generics> := InnerType deriving (Aspect, ...);
```

`:=` follows RFC-0136's rule: `Name` is a *kept* name introduced next to its definition.
`deriving (...)` is optional.

### 2. Meaning

`newtype UserId := i64;` is equivalent to:

```metel
struct UserId { inner: i64 }
```

with the extra guarantees below. The construction/extraction surface is fixed so that no
tuple-struct syntax is needed (RFC-0151 and RFC-0100 are undecided):

```metel
let id := UserId::wrap(42);
let n: i64 := id.unwrap();         // consuming
let r: &i64 := id.inner_ref();     // borrowing
```

`wrap` and `unwrap` are compiler-generated associated functions; the field name `inner` is
reserved and not otherwise accessible outside the declaring module.

### 3. Forwarded aspects

`deriving (A, B)` generates `extend UserId: A { ... }` by delegating each method to the inner
type's impl. The rules:

1. **Self-returning methods are re-wrapped.** `Add::add(self, rhs: Self) -> Self` becomes
   `UserId::wrap(self.inner + rhs.inner)`.
2. **Methods mentioning the inner type elsewhere are rejected** at derive time with a
   diagnostic naming the method (for example an aspect method returning `i64` is ambiguous
   between "the inner" and "an unrelated i64").
3. **The inner type must implement the aspect**; otherwise the derive fails at the newtype
   declaration, not at a later use.
4. **Associated types** are forwarded unchanged unless they equal the inner type, in which case
   they become the newtype.
5. **`Copy`/`Clone`/`Drop`** follow RFC-0162's outcome; until it settles, `deriving` of these is
   permitted only when the inner type has them, and `Drop` is never forwarded (a newtype with
   no destructor of its own simply drops its field).

### 4. Not forwarded by default

A newtype does **not** implicitly implement any aspect, convert to/from the inner type, or
auto-deref to it. The point is that `Meters + UserId` fails to compile.

### 5. Example

```metel
newtype Meters := f64 deriving (Eq, Ord, Add, Display);

extend Meters {
    pub fun to_feet(&self) -> f64 { self.inner_ref() * 3.28084 }
}

fun main() {
    let a := Meters::wrap(3.5);
    let b := Meters::wrap(1.5);
    println(a + b);                   // 5.0 (Add + Display forwarded)
    println(a + 2.0);                 // error: expected Meters, found f64
}
```

---

## Interactions

- **RFC-0160 (aliases):** aliases are transparent; newtypes are opaque. They are complementary.
- **RFC-0137 (branded rows):** a newtype's brand is its name; it is a one-field row.
- **RFC-0093 (derive):** `deriving` is sugar over a comptime derive of a forwarding impl.
- **RFC-0119 (record conversions):** `wrap`/`unwrap` is the one-field special case.
- **RFC-0202 (refinement types):** a refined type is a newtype with an invariant; the two should
  share `wrap`/`unwrap` naming but differ in that refinement's constructor is fallible.
- **RFC-0162 / RFC-0158 (Copy/Clone/Share):** forwarding of duplication aspects depends on that
  settlement.
- **RFC-0076 (brands):** generic brands remain a separate mechanism; a newtype brand is static
  and nominal.

---

## Alternatives considered

1. **Plain struct plus `#derive(Forward(Add))`.** No new keyword, but the single-field
   representation guarantee and the `wrap`/`unwrap` surface would then be conventions.
2. **Tuple-struct syntax** (`struct UserId(i64);`). Blocked on RFC-0151 / RFC-0100.
3. **Implicit forwarding of all aspects** (Rust's `Deref` newtype pattern). Rejected: defeats the
   purpose.

---

## Open Questions

1. Should `deriving` support *via* a different type (`deriving (Ord via Reverse<i64>)`), as in
   Haskell's `DerivingVia`?
2. Can a newtype wrap a record, a closure, or a row? Rows interact with RFC-0137's partial
   moves; the conservative answer is "only types, not rows".
3. Is a generic newtype (`newtype Tagged<T, Tag> := T`) allowed, and does it make phantom
   `Tag` parameters first-class?
4. Does the `wrap` / `unwrap` naming clash with RFC-0119's `to_record` / `from_record`?
5. Should `deriving` accept `Default` and `FromStr`-style constructors?

---

## Decision

**Outcome:** *(pending)*
