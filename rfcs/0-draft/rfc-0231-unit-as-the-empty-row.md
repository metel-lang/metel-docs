---
id: rfc-0231
title: "Unit as the Empty Row"
date: '2026-11-14'
status: draft
---

## Summary

`()` is the empty closed row `.{}`. The primitive unit type is retired as a separate type, and the two spellings denote one type
with one value.

```metel
fun f() -> () { .{} }                 // fails today: cannot unify `.{ }` with `()`
let u: .{} := ();                     // fails today for the same reason
```

This was section 6 of RFC-0151 (tuples as numeric-label rows). It is extracted because it is independent of the tuple work: a
tuple's row view needs `()` to be the empty row, but nothing in the tuple desugaring needs the unification to land first, and
the change is large enough to be reviewed on its own. It is a design draft. Nothing here is accepted.

---

## Motivation

- **One type, two spellings.** `()` is a primitive type with its own literal, and `.{}` is the empty anonymous record. Every rule
  that holds for one has to be restated for the other, and a program can write both and get a type error between them.
- **RFC-0221 states a reliance on the unification** (an empty brace group is the same value whether it is read as a block or as a
  record). **Measured 2026-11-14: the compiler has not unified them**, so that reliance describes the design and is not yet true.
- **RFC-0151.** A tuple of no elements is the empty row. With the unit type separate, the zero-arity case of the tuple sugar needs
  a conversion at exactly one place.

---

## Proposal

**`()` is the empty closed row `{}`.** The two spellings denote one type with one value:

- **Type.** `()` and `.{}` are the same type. `-> ()`, `Result<(), E>` and a closed empty row are interchangeable. The tuple sugar has
  arity 0 as well: no elements give `.{}`.
- **Value.** The unit value is the empty record. A literal `()` and an empty record literal `.{}` denote it, and an empty block, or
  a block with no tail, has this type.
- **Patterns.** `()` and `.{}` match it.
- **One impl target.** `extend (): A` and `extend .{}: A` name the same target, so writing both is an overlap error (`T0015`).
- **Printing.** The type prints as `()`.
- **Surface.** There is no `Unit` name in the standard library today, so nothing user-facing is renamed.

This accepts strictly more programs than today: `.{}` where `()` is expected now type-checks. The one program it can reject is an
overload set or a pair of impls that distinguished `()` from `.{}`.

---

## Size

The change is internal. Measured on the metel-core checkout on 2026-11-07, `Type::Unit` and `InferType::Unit` appear 32 times in
14 files and `Value::Unit` 44 times, and the grammar has `unit_type` and `unit_lit`. How the checker represents the empty row is
an ADR matter.

---

## Interactions

- **RFC-0151:** the zero-arity case of the tuple sugar, and the `Tuple` property of the empty row (RFC-0151 section 5a).
- **RFC-0221 (implemented):** its stated reliance becomes true.
- **RFC-0225 (implemented):** the `.{` introducer; `.{}` is the empty literal.
- **RFC-0116:** anonymous record types, of which the empty row is the degenerate case.

---

## Open questions

1. **Representation.** One representation for the empty row in the checker and the runtime (an ADR), and whether `Value::Unit` is
   kept as a fast path for it.
2. **Overload sets and impl pairs** that distinguish `()` from `.{}` today, if any exist in the standard library or the fixtures.
3. **Order against RFC-0151.** Whether this lands before, with, or after the tuple work; neither depends on the other.

---

## Decision

**Outcome:** *(pending)*
