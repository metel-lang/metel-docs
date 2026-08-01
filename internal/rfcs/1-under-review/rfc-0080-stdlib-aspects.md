---
id: rfc-0080
title: "Standard Library Aspects — Clone, Deref, Send, Sync"
date: '2026-07-01'
updated: '2026-07-09'
---

> **Status — under review.** Moved back from accepted 2026-07-09: §1.3 specified
> derive using `#[derive(Clone)]`, a syntax RFC-0012 (Attributes, Metadata, Macros, and
> Derived Aspects, under review) explicitly rejects in its own Alternatives Considered
> section in favour of either `@derive(...)` or the `derives` keyword. An accepted RFC
> using a syntax the governing RFC rejects is an inconsistency, not a settled precedent.
> §1.3 used `derives Clone` at this point; see the update immediately below for its
> current, further-revised spelling.
>
> **Update (same day, later):** RFC-0012 settled on Path D (comptime derive) as its
> recommended mechanism, with `derives Clone` as Path D's stable surface syntax — so
> §1.3's spelling was briefly confirmed rather than provisional. That confirmation did
> not last the day: RFC-0012 §9 retired the `derives` keyword entirely in favour of
> `@derive(Aspect, ...)`, an attribute on the struct/enum itself, reused (disambiguated
> by attachment target) to also register the comptime function that implements a given
> aspect's derive. §1.3 now uses `@derive(Clone)`.
>
> **Update (2026-07-09, later still):** RFC-0012 was itself split into four smaller
> RFCs and superseded (`internal/rfcs/5-superseded/rfc-0012-derived-aspects.md`). The
> derive mechanism `Clone`'s §1.3 depends on now lives in **RFC-0093 (Derive
> Registration)**. The *mechanism* underneath `@derive(Clone)` remains unaccepted:
> RFC-0093 stays draft (its Open Questions 1-4 — `emit` soundness, registration
> coherence, who may register for a given aspect, required function signature — are
> load-bearing enough to block acceptance). Re-promote this RFC to accepted once
> RFC-0093 reaches acceptance, or sooner if RFC-0093's blocking open questions turn out
> not to affect `Clone`'s specific derive (they concern the general mechanism, not this
> RFC's four aspects, which do not depend on which path implements derive). Depends on
> RFC-0071 (Ownership and Move Semantics) and RFC-0060 (Aspect Impl Coherence).
> Formally specifies four aspects that are assumed pre-existing across the
> accepted and under-review region RFC cluster (RFC-0063–0079) but have never been
> defined. The sendability aspects (`Send`, `Sync`) rely on closed-world coherence from
> RFC-0060 and on the auto-impl mechanism owned by RFC-0096.

## Summary

Four aspects are referenced as pre-existing throughout the region RFC cluster without
formal definition:

- **`Clone`** — explicit duplication of an owned value.
- **`Deref` / `DerefMut`** — dereference coercion; allows smart pointers to be used as references.
- **`Send`** — marker aspect: a value is safe to transfer across fiber boundaries.
- **`Sync`** — marker aspect: a shared reference to a value is safe across fiber boundaries.

This RFC provides the formal specification for each.

---

## 1. Clone

### 1.1 Definition

`Clone` is the aspect for types that support explicit duplication. Calling `.clone()`
on a `T: Clone` produces a new independent owned value of type `T`; the original value
remains valid.

```metel
aspect Clone {
    fun clone(self: &Self) -> Self;
}
```

`clone` takes a shared reference and returns a new owned value. The caller retains the
original; no move occurs.

### 1.2 Relationship to Copy

Every `Copy` type is also `Clone`. The blanket impl clones by bitwise copy:

```metel
extend<T: Copy> T: Clone {
    fun clone(self: &T) -> T { *self }
}
```

`Clone` types that are not `Copy` run user-defined logic — allocating a new backing
buffer, deep-copying a list, incrementing a reference count. The distinction between
`Copy` (implicit, free) and `Clone` (explicit, potentially expensive) is preserved.

> **Note (2026-07-11):** this blanket's target is the impl's own bare parameter `T`,
> not a named type wrapping it — a form RFC-0036 (Conditional Impl Blocks) never
> shows in its own examples, and one the orphan rule (RFC-0060 §1) has no stated
> answer for either, since `T` has no outermost type constructor to check. RFC-0097
> (draft) formalizes both: no new syntax needed, and this impl is permitted here only
> because `Clone` itself is local to `std::core` — never on the strength of `T`.

### 1.3 Derive

`Clone` may be derived for any struct or enum whose fields all implement `Clone`. The
derived impl calls `.clone()` on each field and assembles the result:

```metel
@derive(Clone)
struct Point { x: f64, y: f64 }

// Generated:
extend Point: Clone {
    fun clone(self: &Point) -> Point {
        Point { x: self.x.clone(), y: self.y.clone() }
    }
}
```

For enums, the derived impl matches the active variant and clones its fields.

### 1.4 Clone and region pointers

`@[r] T` — a region pointer — does not implement `Clone` by default. Cloning a region
pointer would require a fresh allocation into the same or another region; the caller
must make that explicit. No blanket `extend @[r] T: Clone` is provided.

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

No `@derive(Send)` annotation is needed; the compiler applies the rule automatically.

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
| `Copy` implies `Clone` | Blanket impl: clone by bitwise copy |
| `Copy` and `Drop` are mutually exclusive | RFC-0071 |
| `DerefMut` requires `Deref` | Supertrait |
| `T: Sync` iff `&T: Send` | Definition of `Sync` |
| `Arc<T>: Send + Sync` when `T: Send + Sync` | §4.3 |

---

## 6. Relationship to RFC-0003

RFC-0003 (Concurrency Model, draft) specifies the fiber API and the rules for crossing
fiber boundaries. `Send` and `Sync` are the type-system vocabulary those rules are
written in. This RFC provides the vocabulary; RFC-0003 provides the grammar. This RFC
does not depend on RFC-0003 and may be accepted independently.

---

## Unresolved Questions

1. **Region-parameterised `Clone`.** Whether `Clone` should carry a region parameter —
   `fun clone[r](self: &Self) -> @[r] Self` — to allow deep cloning into a
   caller-specified region is deferred. The current definition returns a value without
   a region tag, which is appropriate for `Copy` and stack-local types but limiting for
   heap-allocated types where the destination region matters.

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
- RFC-0096 (Auto-Impl Aspects, draft) — the general recognition rule and shared
  structural-composition algorithm §3.2/§4.2 are instances of.
- RFC-0097 (Orphan Rule for Bare-Parameter Blanket Impls, implemented) — §1.2's `Clone`
  blanket is the motivating example for its orphan-rule formalization.
- RFC-0081 (Negative Impls) — mechanism for overriding auto-impl when a type must not
  have `Send` or `Sync` despite its fields being `Send`/`Sync`.
- RFC-0071 (Ownership and Move Semantics) — `Copy`/`Drop` mutual exclusion; move
  semantics; `Clone` as the explicit duplication primitive.
- RFC-0074 (Shared Pointers) — `Rc<T>: !Send`, `!Sync`; `Arc<T>: Send + Sync`;
  `Deref` impls for `Rc` and `Arc`; `get_mut` and `try_unwrap` as the mutation API.
- RFC-0003 (Concurrency Model, draft) — fiber boundary crossing; consumer of `Send`
  and `Sync` bounds.
- RFC-0093 (Derive Registration, draft) — governs the derive syntax/mechanism `Clone`'s
  §1.3 depends on; this RFC's move back to under-review pending that resolution.
  (Superseded RFC-0012, which originally specified this, on 2026-07-09.)
