---
id: rfc-0206
title: "Clone and ImplicitClone"
date: '2026-11-02'
status: under-review
updated: '2026-11-03'
tracking: 'https://github.com/metel-lang/metel-core/issues/1785'
---

> **Extracted from RFC-0080 on 2026-11-02**, the way RFC-0162 was extracted from RFC-0157, and
> **redesigned on 2026-11-03** after a prior-art survey (architecture/reports/copy-clone-prior-art-survey.md)
> and an adversarial review. It carries `Clone`, and the implicit-duplication marker that replaces
> `Copy`. Where a duplication marker is written is RFC-0207's; the model and its alternatives are
> RFC-0162's. Nothing here is decided.

> **Status — under review (2026-11-03).** Committed to v0.16.0 as the Clone half of the settlement.

## Summary

`Clone` is the aspect for explicit duplication: `fun clone(&self) -> Self`. `ImplicitClone` is a
marker the compiler knows that refines it: a type that is `ImplicitClone` is duplicated by the
compiler at a by-value use, by calling the type's own `clone`, instead of being moved. The marker
is granted only in the type's declaration, and it is the stronger bound: every `ImplicitClone`
type is `Clone`, and the converse does not hold.

```metel
struct Point: ImplicitClone { x: i64, y: i64 }            // implicit; Clone is derived if absent
struct Doc derives Clone { title: String }                // explicit only: d.clone()
struct Cache { data: String, hits: i64 }                  // Clone written by hand (extend Cache: Clone)
```

This replaces the pair `Copy`/`Clone`. The name `Copy` is kept for one minor release as a
deprecated alias for `ImplicitClone`. The explanation of the relationship is one sentence:
*`ImplicitClone` is `Clone` that the compiler calls for you.*

---

## Motivation

`Copy` does not currently give a type a `clone`. Measured against the implementation on
2026-11-02:

```metel
struct P { n: i64 }
extend P: Copy;
fun main() { let p := P { n = 1 }; let q := p.clone(); }   // no method `clone` on `P`
```

`T: Clone` rejects such a `P`, and a bodyless `extend P: Clone;` is rejected because the method is
required. A `Copy` struct that needs a `Clone` must hand-write one, and there is no derive. Five
integration fixtures carry a hand-written `clone` callback as scaffolding for exactly this
(metel-core#270).

Three further facts shaped this design:

- **Coverage holes.** `&T` and `[T]` are `Copy` but not `Clone` (`&i64` fails `T: Clone` with
  `T0012`), and array `clone` does not call the element's `clone` while record `clone` does. A
  rule of the form "every `Copy` type is `Clone`" cannot be left to std.
- **The interpreter ignores written clones.** It deep-clones every by-value use, so a hand-written
  `clone` never runs on an implicit copy today.
- **Rust's pair has a documented friction.** `Copy: Clone` requires both impls, `Clone` may diverge
  from the copy, and derive over-approximates generic bounds (the `Copy` documentation says so).

The survey found one precedent that fits: Mojo's `Copyable` (explicit, one hook) with an
`ImplicitlyCopyable` marker that refines it, "ensuring only one definition for the logic of how a
type is copied", and Swift's rule that copyability is fixed on the declaration.

---

## 1. `Clone`

```metel
aspect Clone {
    fun clone(self: &Self) -> Self;
}
```

`clone` returns a new owned value of the same type and the caller keeps the original; no move
occurs. The contract is Rust's: *another value of this type*. A reference or a view is cloned by
cloning the reference or view, not the referent. A handle that aliases shared state is `Share`
(RFC-0158), a separate aspect, and is not `Clone` unless its type says so.

A type gets a `Clone` by writing one (`extend T: Clone { … }`), by a `derives Clone` request
(RFC-0207), or, for an `ImplicitClone` type with neither, by compiler derivation (section 2).

---

## 2. `ImplicitClone`

`ImplicitClone` is a compiler-known marker aspect. It has no methods and cannot be implemented
with `extend`. It is the stronger bound: `T: ImplicitClone` accepts fewer types than `T: Clone`.

**Legality.**
1. *Granted only in the declaration.* A named type is `ImplicitClone` only if its declaration lists
   it in the colon list (RFC-0207): `struct Point: ImplicitClone { … }`. An `extend T: ImplicitClone;`
   is an error with a fix-it that moves it. No refinement of the condition is possible.
2. *It requires `Clone`.* The type must have a `Clone` for every instantiation at which it is
   `ImplicitClone`. If the type has a `Clone` (written or `derives Clone`) that one is used. If it has
   none, the compiler derives one (field-wise, each field cloned, under `Clone`'s own condition).
   There is exactly one `Clone` impl, so there is no overlap and no priority rule.
3. *The predicate is exact and conjunctive.* For an instantiation `T<A>`, `T<A>: ImplicitClone`
   holds when every field's type is `ImplicitClone`, and `T<A>: Clone` holds, and the type is not
   `Drop`. It is evaluated per instantiation, so `struct View<T>: ImplicitClone { r: &T }` is
   `ImplicitClone` for every `T`. A written `Clone` covering narrower instantiations makes
   `ImplicitClone` hold only there; the error appears where an implicit copy is needed.
4. *The implicit copy is the call.* A by-value use of an `ImplicitClone` value is `x.clone()` with
   the call inserted. A type that is not `ImplicitClone` is moved. A written `clone` is therefore
   run at an implicit copy (Mojo's choice), and nothing is sealed to a bitwise body.
5. *`Drop` excludes it, and only it.* A type that implements `Drop` cannot be `ImplicitClone`.
   `Clone` on a `Drop` type is allowed.
6. *Entailment is built in.* `T: ImplicitClone` entails `T: Clone` in the checker and in the abstract
   analysis of generic bodies, as a compiler rule and not as a super-aspect declaration.

**Built-in kinds are compiler rules, not impls.**

| Kind | `ImplicitClone` | `Clone` |
|---|---|---|
| Integers, floats, `boolean`, `Char`, unit | yes (a compiler list) | the value, guaranteed |
| Shared references `&T`, views `[T]` | yes, for every `T` | the reference or view copied, guaranteed |
| `&var T` | never | none |
| Tuples, `[T; N]`, records | when every part is | field-wise, guaranteed whenever `ImplicitClone` |
| Closures | when every capture is (RFC-0134 §1) | by captures, guaranteed |
| Written function types | move-only (RFC-0166) | none |
| `String`, `List`, `Option`, `Result` | no | the std impls of §3 |

The unit type joins the list, which fixes the disagreement between the bound and the move checker
(metel-core#1784). Because the compiler guarantees `Clone` for every `ImplicitClone` built-in kind,
the coverage holes of the Motivation cannot recur.

**The effect contract.** An implicit copy runs user code, so a `clone` on an `ImplicitClone` type
is expected to be cheap, total and free of observable side effects. The first implementation states
the contract and does not check it. The design reserves an effect bound: once Metel's effect system
exists, `ImplicitClone` requires its `Clone` to satisfy a stated effect bound, and a type whose
`clone` does not cannot be `ImplicitClone`. No lint is specified before then, because detecting an
allocating or panicking body without effect information would be guesswork.

---

## 3. Standard `Clone` impls

Measured on 2026-11-02:

| Type | `Clone` today | Plan |
|---|---|---|
| Primitives, `String` | yes | unchanged |
| `[T; N]` | yes, but it does not call the element's `clone` | field-wise through the element's `clone`; the discrepancy with records is a defect to fix |
| Anonymous records | yes, field-wise: `extend<record R> { ..R }: Clone where ..R: Clone` (RFC-0123) | unchanged |
| Named `record` | yes today, the same field-wise impl | takes a `derives Clone` or `: ImplicitClone` entry like a `struct`; a plain `record P` is not cloneable |
| Tuples | **no** | a structural arm, hardcoded like tuple `Copy` (metel-core#263), until variadic generics (metel-core#794) |
| `Option`, `Result`, `List` | **no** | `extend<T: Clone> Option<T>: Clone`, and the same for the others (metel-core#270) |
| A named `struct` or `enum` | only if the user writes one | section 4 |
| `&T`, `[T]`, closures | not `Clone` today | by the built-in rules of section 2 |

---

## 4. `Clone` for a user type

- **Written:** `extend P: Clone { fun clone(&self) -> P { … } }`, always available and the way to
  customise (skip a cache field, reset a counter).
- **Derived:** `struct P derives Clone { … }`. The derived `clone` clones each field, so it is deep
  for owning fields, and a field type without `Clone` makes the entry an error at the declaration.
  The derived impl applies at an instantiation when every field's type is `Clone` there (the exact
  condition of RFC-0207 section 2), which is what lets `View<T> { r: &T }` be `ImplicitClone` for
  every `T`.
  For an enum it matches the active variant. Written and derived impls of the same aspect for one
  type overlap and are an error.
- **Implied by `ImplicitClone`:** section 2, rule 2.
- **Not automatic.** A type with none of these has no `Clone`: whether a named type may be
  duplicated is a statement about what it means, not a consequence of its fields, so an
  accidental `Clone` (for example on a handle type whose fields happen to be `Clone`) is not
  provided.

The derivation itself is native in the first implementation, as it already is for records; a
comptime derivation replaces the native one when RFC-0092 and RFC-0093 allow.

---

## 5. Names and migration

- **`Clone`** keeps its name and its Rust contract.
- **`ImplicitClone`** replaces `Copy`. `Copy` remains for one minor release as a deprecated alias
  that is accepted wherever `ImplicitClone` is, with a warning and a fix-it that rewrites
  `extend X: Copy;` to the colon-list entry and `T: Copy` to `T: ImplicitClone`.
- **The function-type qualifier** `copy` and the keyword `once` (RFC-0163, RFC-0134) keep their
  spelling. The qualifier now names the property whose aspect is `ImplicitClone`; the mismatch is
  recorded, and a shipped qualifier is not renamed here.
- **Generic code** should bound on `Clone` and call `.clone()`; `T: ImplicitClone` is for code
  that needs by-value reuse of a type. This is Mojo's guidance for `ImplicitlyCopyable`.
- **`Share`** (RFC-0158) is unaffected, since the name `Clone` stays.

---

## 6. Implementation staging

- Derived and built-in clones keep the interpreter's existing fast path, which is observationally
  the same.
- An implicit copy of a type with a hand-written `Clone` calls it. This is new behaviour: the
  evaluator must dispatch to the written `clone` at by-value uses of such types.
- The move check and the abstract analysis treat an implicit copy as a call to `T::clone` under
  the entailment of section 2, rule 6.
- The std repairs are the array and tuple `Clone`, the reference and view cases, the unit fix, and
  #270's `Option`, `Result` and `List`.

---

## 7. Worked examples

```metel
struct Point: ImplicitClone { x: i64, y: i64 }
let a := Point { x = 1, y = 2 };
let b := a;                    // a.clone() inserted; a is still valid
let c := a;

struct Wrapper<T>: ImplicitClone { v: T }
// Wrapper<i64>: ImplicitClone and Clone; Wrapper<String>: neither (String is not ImplicitClone);
// Wrapper<NoClone>: neither

struct Id: ImplicitClone derives Clone { n: i64 }          // accepted: the derived Clone is the one used

struct Cache: ImplicitClone { data: i64, hits: i64 }
extend Cache: Clone { fun clone(&self) -> Cache { Cache { data = self.data, hits = 0 } } }
// accepted: the written clone runs at every implicit copy of a Cache

struct H { fd: i64 }
extend H: Drop { fun drop(&var self) { } }
extend H: Clone { fun clone(&self) -> H { H { fd = dup(self.fd) } } }     // Clone on a Drop type: fine
// struct H2: ImplicitClone { fd: i64 } with extend H2: Drop { … }       // error: Drop excludes ImplicitClone

extend Point: ImplicitClone;                                // error: granted only in the declaration
```

---

## 8. Alternatives considered

- **`Copy` and `Clone` linked by `provides` with overlapping impls** (the earlier draft of this RFC
  and RFC-0207). Rejected after the adversarial review: it needs a selection rule over overlapping
  impls, an uncheckable equality invariant between two bodies, an R1-to-R2 migration that negative
  bounds break, and RFC-0168's super-aspects.
- **A sealed bitwise body.** Rejected: a user-writable hook is what makes the refinement meaningful,
  and an effect bound can restrict it later.
- **An explicit duplication operator and no implicit marker** (`copy x`). Set aside: it moves the
  question to which types may be implicit anyway, since generic numeric code needs a bound.
- **A bound `T: ImplicitClone` that accepts any `Clone` type.** Rejected: it would make the same name
  mean two things and let the author of a generic function consent for a type that never opted in.
- **Inference of implicitness from fields** (Swift's default for structs). Rejected: it brings back
  the hazard that adding a field flips every use from copy to move.

---

## Relationship to existing RFCs

- **RFC-0162** — the model, the design space and the survey; this RFC is its accepted-direction
  specification of the two aspects.
- **RFC-0207** — the colon list and the `derives` clause that carry the grant and the derivation.
- **RFC-0071 §2** — states the one predicate; its `Copy` becomes `ImplicitClone`.
- **RFC-0134 / RFC-0163 / RFC-0166** — closures and function types: copyable by captures; the `copy`
  qualifier; written function types move-only.
- **RFC-0158** — `Share`, unchanged.
- **RFC-0080** — the source of `Clone`; it keeps `Deref`, `Send` and `Sync`.
- **RFC-0093 / RFC-0092** — the derive mechanism and comptime that replace the native derivation.
- **RFC-0097** — the orphan rule for bare-parameter blanket impls; no longer needed for this.
- **Effects design** — the future bound on an implicit `clone`.

## Open questions

1. **The exact effect bound** and when `ImplicitClone` starts to enforce it (with the effect system).
2. **How long the `Copy` alias lasts** (one minor release is proposed).
3. **Allocator-placed values and `Clone`.** Out of scope; the allocator RFCs (RFC-0063, RFC-0139) own
   them.
4. **A scoped implicit mode** for generic code over `Clone` types, if `.clone()` proves too noisy;
   deferred with the effects work.
5. **Primitive declarations.** The compiler list becomes primitive struct declarations if std
   gains them.

---

## Decision

**Outcome:** *(pending)*
