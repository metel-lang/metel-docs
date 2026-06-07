---
id: rfc-0007
title: "Compiler-Compatible Primitive Type System"
date: '2026-05-21'
status: accepted
---

## Summary

Redefine Metel's primitive type system to be sized, explicit, and compiler-compatible. The original scope (adding `UInt`) is subsumed into a broader redesign that introduces sized integer and float types, `Byte`, and `Char`, redefines `Array` as a low-level building block, and lays the groundwork for a future `String` rewrite on top of `Char` arrays.

This RFC is motivated by the System F elaboration work (METEL-123), which requires that all IR nodes carry explicit bit-width information and that all coercions are explicit — something the current `Int`/`Float`/`String` primitives cannot support.

---

## Motivation

The current primitive types (`Int`, `Float`, `boolean`, `String`) are semantically adequate for the interpreter but unsuitable as a compiler IR foundation:

- `Int` and `Float` have no declared bit width. The elaborator cannot emit typed literals (`42i64` vs `42i32`) or insert explicit coercion nodes without knowing the width at every point.
- There is no unsigned integer type, making array indexing, bit manipulation, and low-level operations awkward or impossible without workarounds.
- `Array[T]` is defined at a high semantic level with no specified memory layout. A compiler needs a low-level, fixed-layout array type to reason about allocation and element access.
- `String` is opaque. A compiler cannot reason about its representation without a defined relationship to underlying character or byte arrays.
- There is no `Char` type, leaving character-level string operations and Unicode handling underdefined.
- There is no `Byte` type, making byte-level I/O and binary data representation awkward.

The System F IR requires typed literals and explicit coercions at every node. This RFC defines the type vocabulary that makes that possible.

---

## Type System Design

This RFC establishes the exact-width primitive type system that shipped in the interpreter:

- **Lowercase numeric types** (`i8`, `i32`, `u64`, `f32`, etc.): exact bit-width types for low-level code, systems programming, and IR.
- **`Char`** as a distinct primitive scalar value type.

Ergonomic aliases (`Int`, `Float`, `Byte`) were part of the original design discussion but were deferred from the implemented scope.

---

## Proposed Types

### Sized integer types

| Type  | Width  | Signed |
|-------|--------|--------|
| `i8`  | 8-bit  | yes    |
| `i16` | 16-bit | yes    |
| `i32` | 32-bit | yes    |
| `i64` | 64-bit | yes    |
| `u8`  | 8-bit  | no     |
| `u16` | 16-bit | no     |
| `u32` | 32-bit | no     |
| `u64` | 64-bit | no     |

The originally proposed ergonomic alias `Int` for `i64` was deferred and is not part of the implemented surface of this RFC.

### Sized float types

| Type  | Width                |
|-------|----------------------|
| `f32` | 32-bit IEEE 754      |
| `f64` | 64-bit IEEE 754      |

The originally proposed ergonomic alias `Float` for `f64` was deferred and is not part of the implemented surface of this RFC.

### Byte

The originally proposed semantic alias `Byte` for `u8` was deferred and is not part of the implemented surface of this RFC.

### Char

`Char` represents a Unicode scalar value (equivalent to Rust's `char`). Its underlying representation is `u32`, but it is a distinct type — a `Char` is not a `u32` and is not a `Byte`. Proposed operations: `to_u32()`, `from_u32()` (fallible, returns `Option[Char]`), and character classification predicates (`is_alphabetic()`, `is_digit()`, etc.).

### Array (redefined)

`Array[T]` desugars to either a slice `[T]` or a fixed-size array `[T; N]` — it does not introduce heap allocation in the type itself.

Two concrete forms:

- `[T]` — a dynamically-sized slice: a fat pointer carrying a pointer and a length. No ownership over allocation.
- `[T; N]` — a fixed-size array with compile-time known length. Lives on the stack unless explicitly placed elsewhere.

`Array[T]` in user-facing code desugars to `[T]` (the slice form) unless the context provides a compile-time length, in which case `[T; N]` may be inferred. Element access is bounds-checked by default.

### String (deferred)

`String` is redefined conceptually as a sequence of `Char` values backed by a UTF-8 `[Byte]` array. The implementation rewrite is explicitly deferred: `String` cannot be properly redefined until `Char`, `Byte`, and the low-level `Array` representation are settled. This RFC records the intent and the dependency so that future `String` work does not conflict with the primitive type decisions made here.

---

## Casting Rules

### `as` — explicit cast

The `as` keyword was already part of the language before this RFC. Within the implemented scope of RFC-0007, `as` continues to be the explicit cast operator for cross-sized numeric conversions:

```metel
let x: i32 = 42;
let y: i64 = x as i64;   // widening: explicit
let z: i32 = y as i32;   // narrowing: explicit, may lose information
```

`*mut T` coerces to `*T` implicitly (per RFC-0043). All other coercions between numeric types are explicit.

### `as?` — fallible narrowing cast

`as?` was discussed during this RFC but deferred from the implemented scope. The intended design was a fallible cast desugaring to `TryFrom`, returning `Option[T]` (or `Result[T, CastError]`):

```metel
let big: i64 = 300;
let small: Option[i8] = big as? i8;   // nope if out of range
```

This operator did not ship as part of RFC-0007's implementation.

---

## Overflow Semantics

**In debug builds**: integer overflow panics. This applies to all implemented integer types (`i8` through `i64`, `u8` through `u64`).

**In release builds**: integer overflow wraps (two's complement wrapping for signed, modular arithmetic for unsigned).

This matches the Rust model. The rationale: overflow is almost always a bug; panicking in debug catches it early. Wrapping in release avoids the overhead of overflow checks in production code where the programmer has already validated inputs.

Float overflow follows IEEE 754 semantics (infinity / NaN) in both build modes — no panicking.

---

## Array Indexing

The direct index type for `[T]` and `[T; N]` is `u64`. Negative values are statically rejected at the index site.

```metel
let arr: [i64; 4] = [1, 2, 3, 4];
let i: u64 = 2;
let x = arr[i];        // ok
// let y = arr[-1];    // type error: negative literal is not u64
```

`i64` does not implicitly coerce to `u64`. Indexing with an `i64` variable requires an explicit `as u64` cast, which is an intentional friction point: direct array indexing is a low-level operation. Higher-level collection types (e.g., `List[T]`) will provide ergonomic iteration and access patterns that avoid raw index arithmetic.

---

## Relationship to other work

- **RFC-0013 (Int overflow semantics)**: subsumed by this RFC. The overflow decision (panic/debug, wrap/release) applies to all integer types.
- **METEL-123 (System F elaboration)**: the System F IR requires typed literals and explicit coercions at every node. This RFC defines the type vocabulary that makes that possible. The two pieces of work must be designed in coordination.

---

## Decision

**Outcome:** Accepted

### Resolved decisions

| # | Question | Decision |
|---|----------|----------|
| D1 | Naming convention | Exact-width lowercase numeric types (`i8`–`i64`, `u8`–`u64`, `f32`, `f64`) shipped. `Char` shipped as a distinct primitive type. The proposed ergonomic aliases `Int`, `Float`, and `Byte` were deferred. |
| D2 | `Int` and `Float` retention | Deferred. The implemented surface uses `i64` and `f64` directly. |
| D3 | Overflow semantics | Panic in debug, wrapping in release. Applies to all integer types. Float follows IEEE 754. |
| D4 | Casting operator | `as` remained the language's explicit cast operator. RFC-0007 extended its use to the shipped exact-width numeric conversions; it did not introduce `as`. |
| D5 | Fallible narrowing | Deferred. `as?` was discussed but did not ship in the implemented surface of this RFC. |
| D6 | Array model | `[T]` slices and `[T; N]` fixed arrays. `Array[T]` desugars to `[T]`. No heap allocation in the type. |
| D7 | Array indexing type | `u64`. Direct indexing is intentionally low-level; higher-level collections provide ergonomic access. |
| D8 | `Byte` vs `u8` | Deferred. Only `u8` shipped in the implemented surface of this RFC. |
| D9 | Unsuffixed integer literal type | Polymorphic: the literal `42` takes on any integer type demanded by its context. Falls back to `i64` when context leaves the type unconstrained. Suffixed forms (`42i32`, `42u8`) are always exactly typed. Same rule for float literals: `3.14` is polymorphic over float types, defaulting to `f64`. |
