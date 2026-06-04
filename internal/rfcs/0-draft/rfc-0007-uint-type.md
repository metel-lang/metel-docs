---
id: rfc-0007
title: "Compiler-Compatible Primitive Type System"
date: '2026-05-21'
status: draft
---

## Summary

Redefine Metel's primitive type system to be sized, explicit, and compiler-compatible. The original scope (adding `UInt`) is subsumed into a broader redesign that introduces sized integer and float types, `Byte`, and `Char`, redefines `Array` as a low-level building block, and lays the groundwork for a future `String` rewrite on top of `Char` arrays.

This RFC is motivated by the System F elaboration work (METEL-123), which requires that all IR nodes carry explicit bit-width information and that all coercions are explicit — something the current `Int`/`Float`/`String` primitives cannot support.

---

## Motivation

The current primitive types (`Int`, `Float`, `Bool`, `String`) are semantically adequate for the interpreter but unsuitable as a compiler IR foundation:

- `Int` and `Float` have no declared bit width. The elaborator cannot emit typed literals (`42i64` vs `42i32`) or insert explicit coercion nodes without knowing the width at every point.
- There is no unsigned integer type, making array indexing, bit manipulation, and low-level operations awkward or impossible without workarounds.
- `Array[T]` is defined at a high semantic level with no specified memory layout. A compiler needs a low-level, fixed-layout array type to reason about allocation and element access.
- `String` is opaque. A compiler cannot reason about its representation without a defined relationship to underlying character or byte arrays.
- There is no `Char` type, leaving character-level string operations and Unicode handling underdefined.
- There is no `Byte` type, making byte-level I/O and binary data representation awkward.

The System F IR requires typed literals and explicit coercions at every node. This RFC defines the type vocabulary that makes that possible.

---

## Type System Design

This RFC establishes a two-tier primitive type system:

- **Uppercase types** (`Int`, `Float`, `Byte`, `Char`): ergonomic, generic-use types. Under the hood they map to a specific sized type, but the programmer does not need to manage bit widths when using them. Suitable for most application code.
- **Lowercase types** (`i8`, `i32`, `u64`, `f32`, etc.): exact bit-width types for low-level code, systems programming, and IR. All casts between lowercase types are explicit in both directions.

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

`Int` is a permanent ergonomic alias for `i64`. It is not deprecated. Code that does not care about bit widths uses `Int`; code that does uses `i64` directly.

### Sized float types

| Type  | Width                |
|-------|----------------------|
| `f32` | 32-bit IEEE 754      |
| `f64` | 64-bit IEEE 754      |

`Float` is a permanent ergonomic alias for `f64`.

### Byte

`Byte` is a semantic alias for `u8`. They are the same type — no coercion is needed between them. The distinction is intent: `Byte` reads as "raw memory byte or I/O unit"; `u8` reads as "8-bit unsigned integer". Both names are valid in all positions.

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

The `as` keyword is the casting operator. It desugars to the `From` aspect implementation. Both widening and narrowing casts between numeric types require an explicit `as`:

```metel
let x: i32 = 42;
let y: i64 = x as i64;   // widening: explicit
let z: i32 = y as i32;   // narrowing: explicit, may lose information
```

`Int` and `Float` (as aliases for `i64` and `f64`) participate in the same cast rules as their underlying types.

`*mut T` coerces to `*T` implicitly (per RFC-0043). All other coercions between numeric types are explicit.

### `as?` — fallible narrowing cast

`as?` is a fallible cast that desugars to `TryFrom`. It returns `Option[T]` (or `Result[T, CastError]` — exact return type TBD). Use when the value may not fit in the target type:

```metel
let big: i64 = 300;
let small: Option[i8] = big as? i8;   // nope if out of range
```

`as?` is valid for any `as` cast — the compiler may warn when `as?` is used for casts that cannot fail (e.g., widening).

---

## Overflow Semantics

**In debug builds**: integer overflow panics. This applies to all integer types — both uppercase (`Int`) and lowercase (`i8`, `u64`, etc.).

**In release builds**: integer overflow wraps (two's complement wrapping for signed, modular arithmetic for unsigned).

This matches the Rust model. The rationale: overflow is almost always a bug; panicking in debug catches it early. Wrapping in release avoids the overhead of overflow checks in production code where the programmer has already validated inputs.

Float overflow follows IEEE 754 semantics (infinity / NaN) in both build modes — no panicking.

---

## Array Indexing

The direct index type for `[T]` and `[T; N]` is `u64`. Negative values are statically rejected at the index site.

```metel
let arr: [Int; 4] = [1, 2, 3, 4];
let i: u64 = 2;
let x = arr[i];        // ok
// let y = arr[-1];    // type error: negative literal is not u64
```

`Int` (i.e., `i64`) does not implicitly coerce to `u64`. Indexing with an `Int` variable requires an explicit `as u64` cast, which is an intentional friction point: direct array indexing is a low-level operation. Higher-level collection types (e.g., `List[T]`) will provide ergonomic iteration and access patterns that avoid raw index arithmetic.

---

## Relationship to other work

- **RFC-0013 (Int overflow semantics)**: subsumed by this RFC. The overflow decision (panic/debug, wrap/release) applies to all integer types.
- **METEL-123 (System F elaboration)**: the System F IR requires typed literals and explicit coercions at every node. This RFC defines the type vocabulary that makes that possible. The two pieces of work must be designed in coordination.

---

## Decision

**Outcome:** Accepted (pending implementation)
**Target:** *(pending milestone assignment)*

### Resolved decisions

| # | Question | Decision |
|---|----------|----------|
| D1 | Naming convention | Two-tier: uppercase (`Int`, `Float`, `Byte`, `Char`) for ergonomic use; lowercase (`i8`–`i64`, `u8`–`u64`, `f32`, `f64`) for exact bit-width. |
| D2 | `Int` and `Float` retention | Permanent aliases for `i64` and `f64`. Not deprecated. |
| D3 | Overflow semantics | Panic in debug, wrapping in release. Applies to all integer types. Float follows IEEE 754. |
| D4 | Casting operator | `as` for explicit casts (widening and narrowing), desugars to `From`. |
| D5 | Fallible narrowing | `as?` operator, desugars to `TryFrom`, returns `Option[T]`. |
| D6 | Array model | `[T]` slices and `[T; N]` fixed arrays. `Array[T]` desugars to `[T]`. No heap allocation in the type. |
| D7 | Array indexing type | `u64`. Direct indexing is intentionally low-level; higher-level collections provide ergonomic access. |
| D8 | `Byte` vs `u8` | Same type, two names. `Byte` signals intent; no coercion needed. |
