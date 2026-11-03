---
id: rfc-0206
title: "Clone and Copy — One Duplication Method"
date: '2026-11-02'
status: accepted
updated: '2026-11-02'
tracking: 'https://github.com/metel-lang/metel-core/issues/1785'
---

> **Extracted from RFC-0080 on 2026-11-02**, the way RFC-0162 was extracted from RFC-0157.
> RFC-0080 keeps `Deref`/`DerefMut`, `Send` and `Sync`, which it is cited for most; this RFC
> carries `Clone` (its §1) and `Clone`'s relationship to `Copy`. It exists because RFC-0080 as
> a whole was blocked on the derive mechanism (RFC-0093) and so could not be integrated, which
> left `Clone` unimplementable for the types that most need it. The wider questions about the
> `Copy`/`Clone` model, where a `Copy` grant is written and how structural types are
> asserted, are RFC-0162's and RFC-0207's.

> **Status — accepted (2026-11-02).** The `Clone` half of the Copy/Clone settlement, v0.16.0 (metel-core#1785), accepted together with RFC-0162 and RFC-0207; extracted from RFC-0080 §1.

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

RFC-0080 §1.2 specified the fix, a blanket impl `Copy ⟹ Clone`, and it was never built;
this RFC states it as the super-aspect `Copy: Clone` (RFC-0168) with an emitted impl,
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

`Copy` is a super-aspect of `Clone` (RFC-0168), and its derivation emits the `Clone` impl, with a
bitwise body:

```metel
header derivable aspect Copy: Clone {
    // emitted by `derives Copy`; the only Clone a Copy type has
    provide Clone { fun clone(&self) -> Self { *self } }
}
```

A `derives Copy` entry therefore does two things: it checks every field and generates the `Copy`
fact, and it emits `extend T: Clone` with this body for the same type, under the same condition.
Four rules follow.

1. **The body is sealed.** It is compiler-provided and always bitwise. A user-written `clone`
   called implicitly would run arbitrary code at every copy (hidden cost, hidden panics and
   effects, an awkward interaction with `Drop`), which is RFC-0162's D1 in its worst form.
2. **A `Copy` type cannot have a custom `Clone`.** `extend P: Clone { … }` for a type with
   `derives Copy` overlaps the `Clone` the derivation emitted and is an error, with a message that
   says the `Clone` of a `Copy` type is always the bitwise copy. No dedicated coherence rule is
   needed.
3. **The implicit call is the definition.** `let b := a` for a `Copy` type is `let b := a.clone()`
   with the call inserted. A type that is not `Copy` is moved instead, and is `Clone` only if
   it says so.
4. **A type needs only `derives Copy`** (however the grant is written, RFC-0162 Axis C): there is no
   `derive(Clone, Copy)` pair, and `derives Copy, Clone` is an overlap error.

`T: Copy` entails `T: Clone` by the super-aspect relation, so `x.clone()` and a second use of `x`
both work under `T: Copy`, in the checker and in the abstract analysis of a generic body, with no
special rule. A refining `extend<T> W<T>: Copy;` widens the condition of the emitted `Clone` as
well, so the two carry one `where`. For a target with no declaration (a primitive, a tuple, an
array, an anonymous record) there is no derivation to emit the impl; the super-aspect obligation
is met by the `Clone` impls std already has (§3), and the tuple arm (§3) completes it. The
interpreter already deep-clones at every by-value use, so this makes existing behaviour the
definition, with move checking as the restriction. A lint on a redundant `.clone()` of a `Copy`
value is natural and is left to the implementation.

**Dependency.** Super-aspects are RFC-0168's, a draft. The first implementation may realise
`Copy: Clone` and the emitted impl as a compiler-known relation with the same observable behaviour
and move to RFC-0168's mechanism when it lands; the surface does not change.

## 3. Standard `Clone` impls

Measured on 2026-11-02:

| Type | `Clone` today | Plan |
|---|---|---|
| Primitives, `String` | yes | unchanged |
| `[T; N]` | yes (including `[String; 2]`) | unchanged |
| Anonymous records | yes, field-wise: `extend<record R> { ..R }: Clone where ..R: Clone` (RFC-0123) | unchanged |
| Named `record` | yes today, the same field-wise impl | takes a `derives` entry like a `struct` (§4 and RFC-0162): `record P derives Clone`; a plain `record P` is not cloneable |
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
- **(c) A `derives` entry with a derived body**: `struct P derives Clone { … }`, field-wise.
  `Clone` is a `derivable aspect` requested by `derives`, and not `header`, so it can also be
  written by hand (RFC-0207). It needs the field-wise machinery (a native hook, as records use
  now, and comptime later).
- **(d) Automatic availability**, as for records and arrays: `Clone` whenever every field is
  `Clone`. No use-site behaviour changes. The cost is the API-stability hazard: adding a field
  with no `Clone` removes the method from the type.

### Accepted direction: (c), with (a) kept (2026-11-02)

A named `struct` or `enum` states that it is cloneable with a `derives` clause in its header, and
the compiler supplies a field-wise body; a type with no such entry is not `Clone` unless the user writes
the impl by hand.

```metel
struct Doc derives Clone { title: String, tags: List<String> }   // field-wise clone, derived
struct Handle { fd: i64 }                                 // not Clone: nothing says it may be
```

Why (c) rather than the others:

- **Not (d).** Whether a named type can be duplicated is a statement about what it means, not
  a consequence of its field types. `Handle` owns a resource, yet every field is `Clone`, so
  under (d) it would become cloneable by accident. Adding a field with no `Clone` would also
  remove `.clone()` for callers, a break that shows up in their code, not at the declaration.
  Records and arrays can be automatic because they are structural and carry no declared
  identity.
- **Not (b).** It puts the request in an attribute away from the header, the indirection
  RFC-0162 declines for `Copy`, and it waits on RFC-0093 and RFC-0092. The `derives` clause
  replaces the request half of `#derive` (RFC-0207).
- **(c) is opt-in and local.** A missing `Clone` on a field is an error at the declaration.
  It follows the position taken for `Copy` (the declaration states the fact), keeps derived
  distinct from written (`derives` against `extend`), and can ship before comptime because the
  field-wise body is native (as it already is for records). When comptime lands the same clause
  can use a library-written body.

The rules (c) needs are fixed under "Rules fixed at acceptance" below.

## 5. Pointers into allocators

RFC-0080 §1.4 said a region pointer `@[r] T` is not `Clone` by default, because cloning one
would need a fresh allocation. That text predates the refusal of the region cluster
(RFC-0025 and others) and its replacement by the allocator system (RFC-0063). The matching
statement for an allocator-placed value, and whether `Clone` carries an allocator parameter,
belong to the allocator RFCs (RFC-0063, RFC-0139) and are out of scope here; nothing in the
first implementation depends on them.

---

## Relationship to existing RFCs

- **RFC-0080** — the source. It keeps `Deref`, `Send` and `Sync`, and points here for §1.
- **RFC-0162** — the `Copy`/`Clone` model. This RFC is its Axis B position (B1s, one method,
  `Copy` sealed) written as a specification, and the home of its question 8.
- **RFC-0158** — `Share`, the aliasing duplication that `Clone` is narrowed away from.
- **RFC-0071 §2** — defines `Copy`; its "bitwise-copyable" wording is what §2 here sharpens.
- **RFC-0168** — super-aspects, the relation `Copy: Clone` rests on (a draft; dependency).
- **RFC-0097** — the orphan rule that admitted RFC-0080 §1.2's blanket; no longer needed for this.
- **RFC-0207** — the declaration kinds and the `derives` clause that §4(c) (`struct P derives Clone`) uses.
- **RFC-0093 / RFC-0092** — the derive mechanism and comptime core §4(b) waits on.
- **metel-core#270, #741, #263, #794** — the std impls, the `Copy` decisions, tuple `Copy`
  and variadic generics.

## Rules fixed at acceptance

1. **`Clone` for user types** (§4): option (c) with (a) kept: `struct P derives Clone`, or a
   hand-written `extend P: Clone` for a type with no `derives Clone` entry. `derives Clone` needs
   `Clone` declared a `derivable aspect` (RFC-0207).
2. **Sealing** is an overlap: a second `Clone` for a type with `derives Copy` collides with the
   one the derivation emitted. `derives Copy, Clone` is therefore an error, with no separate rule.
3. **Bound entailment.** `T: Copy ⟹ T: Clone` is the super-aspect rule of RFC-0168, in the
   checker and in the abstract analysis of generic bodies.
4. **Allocators** (§5): out of scope.
5. **Tuples before variadic generics:** a hardcoded arm, with the same migration problem as tuple
   `Copy` (metel-core#263, #794).
6. **`derives Clone` against a hand-written impl:** a coherence overlap error.
7. **What the derived body does:** it calls `clone` on each field, so it is deep for owning
   fields, and a field type without `Clone` makes the `derives` entry an error at the declaration.
   An enum's body matches the active variant.
8. **Generic types:** `Clone` is conditional on every type parameter that occurs in a field being
   `Clone` (RFC-0162's R1), with an `extend` allowed to widen it. R2, the exact condition, is the
   intended outcome of RFC-0209 and accepts everything R1 accepts, so moving to it is compatible.

---

## Decision

**Outcome:** accepted 2026-11-02 (language owner), with RFC-0162 and RFC-0207 as one set.

**Accepted:** `Copy` is `Clone` that the compiler calls, with a sealed bitwise body; the standard
`Clone` impls of §3; `derives Clone` for user types with hand-written `extend` kept; the rules
above.

**Deferred, with homes:** the exact generic condition (RFC-0209), enum bodies by comptime
(RFC-0210, RFC-0174), allocator-placed values (RFC-0063, RFC-0139).

**Target:** v0.16.0 (metel-core#1785).
