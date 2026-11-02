---
id: rfc-0206
title: "Clone and Copy — One Duplication Method"
date: '2026-11-02'
status: under-review
updated: '2026-11-02'
tracking: 'https://github.com/metel-lang/metel-core/issues/1785'
---

> **Extracted from RFC-0080 on 2026-11-02**, the way RFC-0162 was extracted from RFC-0157.
> RFC-0080 keeps `Deref`/`DerefMut`, `Send` and `Sync`, which it is cited for most; this RFC
> carries `Clone` (its §1) and `Clone`'s relationship to `Copy`. It exists because RFC-0080 as
> a whole was blocked on the derive mechanism (RFC-0093) and so could not be integrated, which
> left `Clone` unimplementable for the types that most need it. The wider questions about the
> `Copy`/`Clone` model, where a `Copy` grant is written and how structural types are
> asserted, are RFC-0162's. Nothing here is decided.

> **Status — under review (2026-11-02).** Committed to v0.16.0 as the Clone half of the Copy/Clone settlement; extracted from RFC-0080 §1.

## Summary

`Clone` is the aspect for explicit duplication of an owned value: `fun clone(&self) -> Self`.
`Copy` is `Clone` whose call the compiler inserts at a by-value use, and whose body the
compiler supplies and **seals** as a bitwise copy; a user never writes `clone` for a `Copy`
type, and a type that is `Copy` needs nothing else to be `Clone`. The standard library
provides `Clone` for its types, and how a user-defined type that is not `Copy` gets one is the
open question this RFC owns.

---

## Motivation

`Copy` does not currently give a type a `clone`. Measured against the implementation on
2026-11-02:

```metel
struct P { n: i64 }
extend P: Copy;
fun main() { let p := P { n = 1 }; let q := p.clone(); }   // no method `clone` on `P`
```

`T: Clone` rejects such a `P` ("does not implement `Clone`"), and a bodyless
`extend P: Clone;` is rejected because the method is required. So a `Copy` struct that needs
a `Clone` must hand-write one, and there is no derive to write it for you. Five integration
fixtures carry a hand-written `clone` callback as scaffolding for exactly this (metel-core#270).

RFC-0080 §1.2 specified the fix, a blanket impl `Copy ⟹ Clone`, and it was never built,
because the RFC it lives in is `1-under-review` and its §1.3 derive waits on RFC-0093 and
RFC-0092. This RFC takes `Clone` out of that dependency chain.

---

## 1. `Clone` (from RFC-0080 §1.1)

```metel
aspect Clone {
    fun clone(self: &Self) -> Self;
}
```

`clone` takes a shared reference and returns a new, independent owned value. The caller keeps
the original; no move occurs. `Clone` means independent duplication only: a handle that
aliases shared state is `Share` (RFC-0158), not `Clone`.

## 2. `Copy` is `Clone` that the compiler calls (from RFC-0080 §1.2)

For a `Copy` type the compiler supplies `clone`, and the body is a bitwise copy:

```metel
extend<T: Copy> T: Clone {
    fun clone(self: &T) -> T { *self }
}
```

This is RFC-0080 §1.2's blanket, stated as the definition of `Copy` and not as a convenience
beside it. Four rules follow.

1. **The body is sealed.** It is compiler-provided and always bitwise. A user-written `clone`
   called implicitly would run arbitrary code at every copy (hidden cost, hidden panics and
   effects, an awkward interaction with `Drop`), which is RFC-0162's D1 in its worst form.
2. **A `Copy` type cannot have a custom `Clone`.** `extend P: Clone { … }` for a `Copy` `P`
   overlaps the blanket and is an error, with a message that says the `Clone` of a `Copy`
   type is always the bitwise copy.
3. **The implicit call is the definition.** `let b := a` for a `Copy` type is `let b := a.clone()`
   with the call inserted. A type that is not `Copy` is moved instead, and is `Clone` only if
   it says so.
4. **A type needs only `: Copy`** (however the grant is written, RFC-0162 Axis C): there is no
   `derive(Clone, Copy)` pair.

`T: Copy` must therefore entail `T: Clone` wherever bounds are reasoned about, including the
abstract analysis of a generic body, so that `x.clone()` and a second use of `x` both work
under `T: Copy`. The blanket's target is its own bare parameter `T`, which the orphan rule
admits only because `Clone` is local to `std::core` (RFC-0097). The interpreter already
deep-clones at every by-value use, so this makes existing behaviour the definition, with move
checking as the restriction. A lint on a redundant `.clone()` of a `Copy` value is natural and
is left to the implementation.

## 3. Standard `Clone` impls

Measured on 2026-11-02:

| Type | `Clone` today | Plan |
|---|---|---|
| Primitives, `String` | yes | unchanged |
| `[T; N]` | yes (including `[String; 2]`) | unchanged |
| Anonymous records | yes, field-wise: `extend<record R> { ..R }: Clone where ..R: Clone` (RFC-0123) | unchanged |
| Named `record` | yes today, the same field-wise impl | takes a header entry like a `struct` (§4 and RFC-0162): `record P: Clone`; a plain `record P` is not cloneable |
| Tuples | **no** (`T: Clone` rejects `(i64, i64)`; `.clone()` reports "cannot infer receiver type") | a structural arm, hardcoded like tuple `Copy` (metel-core#263), until variadic generics (metel-core#794) |
| `Option`, `Result`, `List` | **no** | `extend<T: Clone> Option<T>: Clone`, and the same for the others (metel-core#270) |
| A named `struct` or `enum` | only if the user writes one | §4 |
| A `Copy` type | **no, but should be** | §2 |
| Closures and function types | not measured | `Clone` if and only if `Copy` (§2); a non-`Copy` closure is not `Clone` |

## 4. `Clone` for a user type that is not `Copy`

RFC-0080 §1.3 specified `#derive(Clone)`, field-wise, which depends on the derive mechanism
(RFC-0093) and so on comptime (RFC-0092). The options, taken together with RFC-0162's
question 8:

- **(a) Hand-written**, as today. Always available, verbose, and the baseline.
- **(b) `#derive(Clone)`** (RFC-0080 §1.3): the derived impl calls `.clone()` on each field
  and assembles the result; for an enum it matches the active variant. Blocked on RFC-0093 and
  reopens the worry about copyness-like behaviour hidden behind a derive, though `Clone` is an
  explicit call and hides no use-site behaviour.
- **(c) A header entry with a derived body**: `struct P: Clone { … }`, field-wise. It reuses
  the header RFC-0162 proposes for `Copy`, and is the first use of its direction that header
  aspects later accept aspects with methods. It needs the field-wise machinery (a native hook,
  as records use now, and comptime later).
- **(d) Automatic availability**, as for records and arrays: `Clone` whenever every field is
  `Clone`. No use-site behaviour changes. The cost is the API-stability hazard: adding a field
  with no `Clone` removes the method from the type.

### Proposed direction: (c), with (a) kept (language owner's lean, 2026-11-02)

A named `struct` or `enum` states that it is cloneable in its header, and the compiler
supplies a field-wise body; a type with no such entry is not `Clone` unless the user writes
the impl by hand. Not yet decided.

```metel
struct Doc: Clone { title: String, tags: List<String> }   // field-wise clone, derived
struct Handle { fd: i64 }                                 // not Clone: nothing says it may be
```

Why (c) rather than the others:

- **Not (d).** Whether a named type can be duplicated is a statement about what it means, not
  a consequence of its field types. `Handle` owns a resource, yet every field is `Clone`, so
  under (d) it would become cloneable by accident. Adding a field with no `Clone` would also
  remove `.clone()` for callers, a break that shows up in their code, not at the declaration.
  Records and arrays can be automatic because they are structural and carry no declared
  identity.
- **Not (b).** It puts the fact in an attribute away from the header, the indirection
  RFC-0162 declines for `Copy`, and it waits on RFC-0093 and RFC-0092.
- **(c) is opt-in and local.** A missing `Clone` on a field is an error at the declaration.
  It mirrors `extend P: Clone`, follows the position taken for `Copy`, and can ship before
  comptime because the field-wise body is native (as it already is for records). When comptime
  lands the same header entry can use a library-written body.

The rules (c) would need are open questions 6 to 9 below.

## 5. Pointers into allocators

RFC-0080 §1.4 said a region pointer `@[r] T` is not `Clone` by default, because cloning one
would need a fresh allocation. That text predates the refusal of the region cluster
(RFC-0025 and others) and its replacement by the allocator system (RFC-0063). The matching
statement for an allocator-placed value, and whether `Clone` carries an allocator parameter,
are open and are not settled here.

---

## Relationship to existing RFCs

- **RFC-0080** — the source. It keeps `Deref`, `Send` and `Sync`, and points here for §1.
- **RFC-0162** — the `Copy`/`Clone` model. This RFC is its Axis B position (B1s, one method,
  `Copy` sealed) written as a specification, and the home of its question 8.
- **RFC-0158** — `Share`, the aliasing duplication that `Clone` is narrowed away from.
- **RFC-0071 §2** — defines `Copy`; its "bitwise-copyable" wording is what §2 here sharpens.
- **RFC-0097** — the orphan rule that admits the blanket's bare-parameter target.
- **RFC-0207** — the header-grant mechanism that §4(c) (`struct P: Clone`) uses.
- **RFC-0093 / RFC-0092** — the derive mechanism and comptime core §4(b) waits on.
- **metel-core#270, #741, #263, #794** — the std impls, the `Copy` decisions, tuple `Copy`
  and variadic generics.

## Open questions

1. **`Clone` for user types** (§4): (a) to (d); the proposed direction is (c) with (a) kept,
   its rules being questions 6 to 9.
2. **How sealing is enforced.** Decided 2026-11-02: a coherence rule that rejects a second
   `Clone` for a `Copy` type. The alternative, the `Copy` aspect declared as granting a sealed
   `clone` (RFC-0162's C5 grant modes), stays a possible follow-up RFC and blocks nothing here.
3. **Bound entailment.** Not a design choice: `T: Copy ⟹ T: Clone` must hold in the checker's
   bound reasoning and in the abstract analysis of generic bodies. It is implementation scope.
4. **Allocators** (§5). Not settled here; nothing in v0.16.0 depends on it.
5. **Tuples before variadic generics.** Decided 2026-11-02: a hardcoded arm, with the same
   migration problem as tuple `Copy` (metel-core#263, #794).
6. **`: Copy, Clone` in one header.** `Copy` already gives `Clone` through the sealed blanket
   (§2), so the pair is redundant. Proposed: an error, to keep one spelling; the alternative
   is a warning.
7. **Header `: Clone` against a hand-written impl.** Proposed: they conflict, as a header
   `Copy` grant and a second `Copy` impl do in RFC-0162. A hand-written `extend P: Clone`
   (to skip a cache field, say) is for a type with no `: Clone` entry.
8. **What the derived body does.** Proposed: it calls `clone` on each field, so it is deep for
   owning fields, and a field type without `Clone` makes the header entry an error at the
   declaration. An enum's body matches the active variant.
9. **Generic types.** Proposed: reuse RFC-0162's R1, so `Clone` is conditional on every type
   parameter that occurs in a field being `Clone`, with an `extend` allowed to widen it.
   Decided 2026-11-02, following RFC-0162's R1 for `Copy`; R2 is not taken.

---

## Decision

**Outcome:** *(pending)*
