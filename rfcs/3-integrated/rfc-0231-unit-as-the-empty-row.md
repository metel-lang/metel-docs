---
id: rfc-0231
title: "Unit as the Empty Row"
date: '2026-11-14'
status: integrated
updated: '2026-11-14'
tracking: 'https://github.com/metel-lang/metel-core/issues/2024'
coverage:
  "1": { kind: blocked, reason: "Implementation of the unification is metel-core#2024; the rules are in reference/spec/types.md (tuples legality-2, legality-3, dynamics-1) and carry no fixtures until then.", ref: "metel-core#2024" }
  "2": { kind: untestable, reason: "Section 2 states the internal representation of the empty row; no source fixture can observe whether the checker keeps a separate unit node." }
  "3": { spec: "spec.ownership.narrowing.legality-4" }
impl_tracking: 'https://github.com/metel-lang/metel-core/issues/2024'
impl_status: not-started
---

> **Status — accepted (2026-11-14).** Accepted 2026-11-14: representation, the spec conflict on empty residuals, impl target and display settled; implemented before RFC-0151.

> **Status — integrated (2026-11-14).** Integrated 2026-11-14: spec types.tuples legality-2/3 and dynamics-1 (blocked-exempt on metel-core#2024), planned notes on the ownership chapter's empty-residual statements; worked examples recorded.

## Summary

`()` is the empty closed row `.{}`. The primitive unit type is retired as a separate type, and the two spellings denote one type
with one value.

```metel
fun f() -> () { .{} }                 // fails today: cannot unify `.{ }` with `()`
let u: .{} := ();                     // fails today for the same reason
```

This was section 6 of RFC-0151 (tuples as numeric-label rows). It is a separate RFC because the change is large enough to be
reviewed on its own, and it **is implemented before RFC-0151**: with `()` already the empty row, the zero-arity tuple needs no
conversion, and RFC-0221's stated reliance on the unification is true before the tuple work builds on it.

It also **changes a sentence of the integrated spec**: the ownership chapter says an empty residual "neither becomes `Unit`". An
anonymous empty residual becomes `()`; a branded empty residual `Name.{}` stays branded and distinct (section 3).

---

## Motivation

- **One type, two spellings.** `()` is a primitive type with its own literal, and `.{}` is the empty anonymous record. Every rule
  that holds for one has to be restated for the other, and a program can write both and get a type error between them.
- **RFC-0221 states a reliance on the unification** (an empty brace group is the same value whether it is read as a block or as a
  record). **Measured 2026-11-14: the compiler has not unified them**, so that reliance describes the design and is not yet true.
- **RFC-0151.** A tuple of no elements is the empty row. With the unit type separate, the zero-arity case of the tuple sugar needs
  a conversion at exactly one place; this RFC removes that place by landing first.
- **Two small defects the split causes.** `println(())` is an internal error today (`I0001: method call on non-struct type ()`)
  because the unit value has no `Display`, while `println(.{})` prints `{}`; and `extend (): A` is rejected ("cannot `extend`
  the unit type: this block's methods could never be found") while `extend .{}: A` is accepted.

---

## Proposal

### 1. One type, one value

**`()` is the empty closed row `.{}`.**

- **Type.** `()` and `.{}` are the same type. `-> ()`, `Result<(), E>` and a closed empty row are interchangeable. The tuple sugar
  has arity 0 as well: no elements give `.{}`. A function with no return annotation, an empty block, a block with no tail, a
  braceless `if` without `else`, and a `break` with no value all have this type.
- **Value.** The unit value is the empty anonymous record. A literal `()` and an empty record literal `.{}` denote it.
- **Patterns.** `()` and `.{}` match it, and both are irrefutable.
- **Impls.** `extend (): A` is accepted as a spelling of `extend .{}: A`. Writing both is an overlap error (`T0015`). The empty row
  is also covered by every row impl whose condition holds vacuously (`extend<record R> .{ ..R }: Copy where ..R: Copy;`), so
  `Copy` and `Clone` of `()` come from the row impls and need no separate built-in.
- **Printing.** The type prints as `()`. The value prints as `()` as well: the record `Display` has one special case, for the empty
  row, so the type and the value print the same way, and `println(())` stops being an internal error.
- **Surface.** There is no `Unit` name in the standard library today, so nothing user-facing is renamed. `unit_lit` and
  `unit_type` remain in the grammar as spellings of the empty row, and `match () { … }` keeps working.

This accepts strictly more programs than today: `.{}` where `()` is expected now type-checks.

### 2. Representation

The empty row is `Type::Record(vec![])` and the empty record value (`Value::Record { fields: empty, type_id: None }`). `Type::Unit`,
`InferType::Unit` and `Value::Unit` are deleted, so there is no second representation of one value. A helper `Value::unit()`
returns the empty anonymous record. An empty `HashMap` allocates nothing, so the value stays cheap. How the checker represents
the empty row is recorded in an ADR.

### 3. The empty residual: what changes in the integrated spec

The ownership chapter currently states, in the residual algebra and in narrowing legality-4, that an empty residual does not become
`Unit`: "neither empty form is `Unit`", and "no empty-residual rule … coerces the result to `Unit`". With one type, the first half
of that is no longer true:

| Empty residual | Today | After this RFC |
|---|---|---|
| anonymous (`.{}`, all fields of an anonymous record moved out) | a type that is **not** `()`; `take(r)` with `take(x: ())` is `T0001` | **is `()`**; `take(r)` type-checks |
| branded (`Name.{}`, all fields of a non-empty struct moved out) | a branded type, not `.{}` and not `()` | **unchanged**: it keeps its brand, so it is not `()` |

The branded case does not move because the brand is part of the type (RFC-0137), and the runtime keeps it apart: a branded empty
residual is a record whose `type_id` is set, and `()` is the anonymous empty record. The second sentence of the spec ("a branded
empty residual does not become an anonymous record") stays true.

Two fixtures assert the old behaviour (`empty_residual_unit_checked` and `empty_residual_unit_default`, which cite narrowing
legality-4): an anonymous empty residual passed to a `()` parameter expects `T0001`. They flip to accepted when this RFC is
implemented, and a new fixture keeps the branded case rejected.

---

## Worked examples (integration)

Each combines this RFC with an integrated feature or a sibling RFC, looking for a contradiction. None was found; the one
contradiction, with the ownership chapter, is section 3 and is resolved there.

| Example | Result |
|---|---|
| `fun f() { }` then `let b: () := f();` and `let c: .{} := f();` | both accepted: the block has type `.{}` |
| `let u := (); let e := .{}; let v: () := e;` | accepted; one type |
| `Result<(), E>` and `Result<.{}, E>` | the same type; `impl X for Result<(), E>` beside `impl X for Result<.{}, E>` is an overlap (`T0015`) |
| `extend (): A` beside `extend .{}: A` | `T0015` (RFC-0225, RFC-0221: one impl target) |
| `extend (): Display` beside std's `extend<record R> .{ ..R }: Display where ..R: Display` | overlap, as `extend .{}: Display` is today; not a new rule |
| `match (()) { () => … }` and `match (.{}) { .{} => … }` | both irrefutable, both accepted |
| `println(())` | prints `()` (today: internal error) |
| an anonymous record with its only field moved out, passed to `fun take(x: ())` | accepted (today: `T0001`); `Name.{}` of a struct passed to the same parameter stays `T0001` (RFC-0137, RFC-0211) |
| `Copy` and `Clone` of `()` | from the row impls, vacuously; `T: Copy` accepts `()` as it does today |
| a custom `Drop` for `()` | rejected, as for any anonymous record (RFC-0116 section 3); unit never had one |
| the zero-arity tuple `()` of RFC-0151 and its `Tuple` property | the empty row has the property and prints `()` (RFC-0151 section 5a) |
| `x == y` with `x, y: ()` | unchanged: `==` requires a primitive operand today for `()` and for `.{}` alike |

---

## Changes on acceptance

- **Spec, types chapter.** The primitive table's `()` row, the Tuples section ("`()` is the zero-element tuple") and the two
  statements that an empty row "is not `Unit`" (the projection section and the record-pattern remainder) change; new rules in the
  Tuples section state the unification, the impl target and the display.
- **Spec, ownership chapter.** The residual algebra and narrowing legality-4 gain the anonymous-empty-residual-is-`()` statement;
  the built-in-kinds lists of `Copy` and `Clone` drop "the unit type", which the row impls now cover.
- **Fixtures.** The two empty-residual fixtures flip; a branded-empty-residual fixture and a fixture per rule above are added.
- **RFC-0221.** Its stated reliance on the unification is true.

---

## Size

The change is internal. Measured on the metel-core checkout on 2026-11-07 and 2026-11-14, `Type::Unit` and `InferType::Unit` appear
in 14 files (32 sites), and `Value::Unit` 44 times, 26 of them in `evaluator/mod.rs` and 12 in `builtins.rs`. The grammar has
`unit_type` and `unit_lit`. No impl and no overload set in `core.mtl` or the fixtures distinguishes `()` from `.{}`; the only
fixtures that depend on the distinction are the two above.

---

## Interactions

- **RFC-0151:** the zero-arity case of the tuple sugar, and the `Tuple` property of the empty row (RFC-0151 section 5a).
- **RFC-0221 (implemented):** its stated reliance becomes true. **RFC-0225 (implemented):** `.{` is the introducer; `.{}` is the
  empty literal.
- **RFC-0116:** anonymous record types, of which the empty row is the degenerate case; no custom `Drop`.
- **RFC-0137, RFC-0117, RFC-0211:** branded rows keep a branded empty residual distinct; an anonymous empty residual is `()`.
- **RFC-0123:** the row impls that now cover `()`.

---

## Open questions

All resolved as of 2026-11-14.

1. ~~**Representation.**~~ **Resolved:** the empty row is `Type::Record(vec![])` and the empty record value; `Type::Unit`,
   `InferType::Unit` and `Value::Unit` are deleted, with a `Value::unit()` helper. No `Value::Unit` fast path, to avoid two
   representations of one value.
2. ~~**Overload sets and impl pairs that distinguish `()` from `.{}`.**~~ **Resolved:** none exist in the standard library or the
   fixtures; the only fixtures that depend on the distinction are the two empty-residual fixtures, which flip.
3. ~~**Order against RFC-0151.**~~ **Resolved:** this RFC is implemented first. RFC-0151's implementation depends on it; it does not
   depend on RFC-0151.
4. ~~**`extend (): A`.**~~ **Resolved:** accepted as a spelling of `extend .{}: A`; writing both is `T0015`.
5. ~~**Display of the empty value.**~~ **Resolved:** `()`, as one special case in the record `Display`, so type and value print alike.
6. ~~**The spec statement that an empty residual is not `Unit`.**~~ **Resolved:** section 3: an anonymous empty residual is `()`; a
   branded one stays branded; the two fixtures flip and a branded-residual fixture keeps the distinction.

---

## Decision

**Outcome:** *(pending)*
