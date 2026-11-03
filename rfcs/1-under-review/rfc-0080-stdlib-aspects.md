---
id: rfc-0080
title: "Standard Library Aspects — Deref, Send, Sync"
date: '2026-07-01'
updated: '2026-11-02'
status: under-review
tracking: 'https://github.com/metel-lang/metel-core/issues/805'
---

> **Tracking added retroactively (2026-08-23).** This RFC reached under-review before
> the tracking-issue requirement existed (PROCESS.md, 2026-08-23); filed metel-core#805
> (design-settlement, blocked on RFC-0093's derive mechanism, same v0.13.1 comptime/
> derive foundation chain split out 2026-08-23). Also backfilled the missing `status`
> frontmatter field itself, absent until now.

> **Narrowed 2026-11-02: `Clone` moved to RFC-0206.** §1 (`Clone`, its relationship to
> `Copy`, the derive of §1.3 and the region-pointer note of §1.4) is now RFC-0206, so that
> `Clone` and the `Copy ⟹ Clone` blanket are no longer held behind the derive mechanism
> (RFC-0093) this RFC's §1.3 waited on. What remains here, `Deref`/`DerefMut`, `Send` and
> `Sync`, does not depend on derive; the section numbers 2 to 6 are unchanged so existing
> citations (`§3.2`, `§4.2`) still point at the same text. Citations of §1 now read RFC-0206.

> **Status — under review.** It was moved back from accepted on 2026-07-09 because §1.3 (now
> RFC-0206 §4) specified a derive spelling the then-governing RFC rejected, and it stayed
> there while the derive mechanism (RFC-0093) was unsettled. That derive moved with `Clone`,
> so what is left here no longer depends on it. It still depends on RFC-0060 (coherence) and,
> for the auto-impl rule of §3.2 and §4.2, on RFC-0096.

## Summary

Three aspects are referenced as pre-existing throughout the cluster without formal definition:

- **`Deref` / `DerefMut`** — dereference coercion; allows smart pointers to be used as references.
- **`Send`** — marker aspect: a value is safe to transfer across fiber boundaries.
- **`Sync`** — marker aspect: a shared reference to a value is safe across fiber boundaries.

This RFC provides the formal specification for each. `Clone`, which this RFC first
defined, is RFC-0206.

---

## 1. Clone

Moved to **RFC-0206 (Clone and ImplicitClone)** on 2026-11-02: the `Clone`
aspect (formerly §1.1), `Copy` as `Clone` with a sealed bitwise body (formerly §1.2), the
derive (formerly §1.3, now RFC-0206 §4) and the allocator note (formerly §1.4, now
RFC-0206 §5).

---

## 2. Deref and DerefMut

### 2.1 Deref

`Deref` is the aspect for types that can be transparently dereferenced to a target
type. Smart pointers implement `Deref` to allow access to their contents without
explicit unwrapping.

```metel
aspect Deref {
    type Target;

    fun deref(self: &Self) -> &Target;
}
```

`Target` is the type produced by dereferencing. The compiler applies deref coercions
implicitly: when a `T: Deref<Target = U>` appears where `&U` is expected, `.deref()`
is inserted.

### 2.2 DerefMut

`DerefMut` extends `Deref` with mutable access:

```metel
aspect DerefMut: Deref {
    fun deref_mut(self: &var Self) -> &var Target;
}
```

`Deref` is a supertrait of `DerefMut`. Any `DerefMut` implementation must also provide
a `Deref` implementation with the same `Target`. The compiler applies `DerefMut`
coercions when `&var U` is expected and `T: DerefMut<Target = U>`.

### 2.3 Coercion rules

Deref coercions are applied in the following positions:

- Function call arguments: `f(smart_ptr)` coerces when `f` expects `&Target`.
- Method call receivers: `smart_ptr.method()` coerces to `&Target` to find the method.
- Explicit borrow: `&smart_ptr` coerces to `&Target`.

Coercions are applied at most once per position. The compiler does not chain coercions
across multiple `Deref` impls.

### 2.4 Standard impls

`Rc<T, 'b>` and `Arc<T, 'b>` implement `Deref` but not `DerefMut` — shared
ownership precludes unique mutable access through a shared pointer. `get_mut` and
`try_unwrap` (RFC-0074 §2.4–2.5) are the explicit mechanisms for mutation.

```metel
extend<T, brand 'b> Rc<T, 'b>: Deref {
    type Target = T;
    fun deref(self: &Rc<T, 'b>) -> &T { ... }
}

extend<T, brand 'b> Arc<T, 'b>: Deref {
    type Target = T;
    fun deref(self: &Arc<T, 'b>) -> &T { ... }
}
```

---

## 3. Send

### 3.1 Definition

`Send` is a marker aspect with no methods. A type `T: Send` is safe to transfer across
fiber boundaries — it may be moved from one fiber's stack to another's without data
races or unsoundness.

```metel
aspect Send { }
```

`Send` appears as a bound on fiber-crossing operations. Any function that transfers a
value to another fiber requires `T: Send`.

### 3.2 Auto-impl

`Send` is an auto-aspect: the compiler automatically derives `Send` for any type all
of whose fields are `Send`. Under closed-world coherence (RFC-0060):

- Primitive types (`i64`, `u64`, `f64`, `boolean`, `String`, `!`, ...) are `Send`.
- A struct or enum is `Send` if every field type is `Send`.
- `&T` is `Send` if `T: Sync`.
- `&var T` is `Send` if `T: Send`.

No `#derive(Send)` annotation is needed; the compiler applies the rule automatically.

> **Note (2026-07-11):** this rule is `Send`'s own instance of a shared mechanism —
> how the compiler recognizes an aspect as auto-impl at all, and the general
> structural-composition algorithm this per-field/per-reference rule follows — now
> formalized once in RFC-0096, rather than each auto-impl aspect restating it. This
> section's actual rule is unchanged.

### 3.3 Opting out

A type that must not be `Send` despite the auto-impl rule must use a negative impl
(RFC-0081): `extend MyType: !Send;`. The negative impl overrides any blanket that
would otherwise apply.

Relying on absence of a positive impl is insufficient when the auto-impl rule would
otherwise fire. `Rc<T, 'b>` is the canonical example: its reference count is an
integer, which is `Send` — so the auto-impl would grant `Rc<T>: Send`. The negative
impl prevents this (RFC-0074 §2.6).

### 3.4 Region pointers

Sendability of `@[r] T` depends on the region type. General principle: a region
pointer is `Send` when the underlying region is globally accessible and `T: Send`.
Per-region rules:

| Region | `@[r] T: Send`? | Reason |
|---|---|---|
| `Heap` | Yes, when `T: Send` | Global allocator; accessible from any fiber |
| `LocalHeap` | No | Thread-local allocator; pointer invalid on another fiber |
| `BumpRegion` / `AutoRegion` | Deferred to RFC-0003 | Depends on whether the region handle has been transferred |

---

## 4. Sync

### 4.1 Definition

`Sync` is a marker aspect with no methods. A type `T: Sync` may be accessed through a
shared reference from multiple fibers simultaneously.

```metel
aspect Sync { }
```

The defining relationship between `Send` and `Sync`:

> `T: Sync` if and only if `&T: Send`.

A type is `Sync` precisely when sharing a reference to it across fibers is safe.

### 4.2 Auto-impl

`Sync` is an auto-aspect under the same closed-world rules as `Send`:

- Primitive types are `Sync`.
- A struct or enum is `Sync` if every field type is `Sync`.
- `&T` is `Sync` if `T: Sync`.
- `&var T` is `Sync` if `T: Sync`.

> See §3.2's 2026-07-11 note — RFC-0096 formalizes the shared mechanism this and
> `Send`'s rule both instantiate.

### 4.3 Standard impls

`Rc<T, 'b>` provides no `Sync` impl. A shared reference `&Rc<T>` used from multiple
fibers would race on the non-atomic reference count.

`Arc<T, 'b>` is both `Send` and `Sync` when `T: Send + Sync`:

```metel
extend<T: Send + Sync, brand 'b> Arc<T, 'b>: Send {}
extend<T: Send + Sync, brand 'b> Arc<T, 'b>: Sync {}
```

Both conditions are required: `Sync` of `T` because any fiber may read through `&T`;
`Send` of `T` because any fiber may be the last to drop, running `T`'s destructor.

---

## 5. Interactions

| Relationship | Rule |
|---|---|
| `ImplicitClone` implies `Clone` | RFC-0206 §2 (a compiler rule: the implicit copy calls the type's `clone`) |
| `Copy` and `Drop` are mutually exclusive | RFC-0071 |
| `DerefMut` requires `Deref` | Supertrait |
| `T: Sync` iff `&T: Send` | Definition of `Sync` |
| `Arc<T>: Send + Sync` when `T: Send + Sync` | §4.3 |

---

## 6. Relationship to RFC-0003

RFC-0003 (Concurrency Model, under review) specifies the fiber API and the rules for crossing
fiber boundaries. `Send` and `Sync` are the type-system vocabulary those rules are
written in. This RFC provides the vocabulary; RFC-0003 provides the grammar. This RFC
does not depend on RFC-0003 and may be accepted independently.

---

## Unresolved Questions

1. **Region-parameterised `Clone`.** Moved to RFC-0206 §5 with `Clone`.

2. **`BumpRegion` / `AutoRegion` sendability.** The sendability of pointers into
   scoped regions depends on whether the region handle itself is transferred. The full
   rule is deferred to RFC-0003.

3. **Deref coercion chaining.** A single level of transitive deref (e.g., `Box<Rc<T>>`
   coercing to `&T` in two steps) may be useful. Currently prohibited; may be revisited
   when the full coercion system is specified.

---

## References

- RFC-0060 (Aspect Impl Coherence) — closed-world coherence required for `Send`/`Sync`
  auto-impl rules.
- RFC-0096 (Auto-Impl Aspects, under review) — the general recognition rule and shared
  structural-composition algorithm §3.2/§4.2 are instances of.
- RFC-0097 (Orphan Rule for Bare-Parameter Blanket Impls, implemented) — the `Clone`
  blanket, now RFC-0206 §2, is the motivating example for its orphan-rule formalization.
- RFC-0081 (Negative Impls) — mechanism for overriding auto-impl when a type must not
  have `Send` or `Sync` despite its fields being `Send`/`Sync`.
- RFC-0071 (Ownership and Move Semantics) — `Copy`/`Drop` mutual exclusion; move
  semantics.
- RFC-0206 (Clone and ImplicitClone) — `Clone`, extracted from this RFC.
- RFC-0074 (Shared Pointers) — `Rc<T>: !Send`, `!Sync`; `Arc<T>: Send + Sync`;
  `Deref` impls for `Rc` and `Arc`; `get_mut` and `try_unwrap` as the mutation API.
- RFC-0003 (Concurrency Model, under review) — fiber boundary crossing; consumer of `Send`
  and `Sync` bounds.
- RFC-0093 (Derive Registration, under-review as of 2026-08-23) — governs the derive
  syntax/mechanism `Clone`'s derive depends on; that derive moved with `Clone` to RFC-0206,
  so this RFC no longer waits on it. (Superseded RFC-0012, which originally specified this, on
  2026-07-09.)
