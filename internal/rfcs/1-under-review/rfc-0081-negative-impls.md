---
id: rfc-0081
title: "Negative Impls"
date: '2026-07-01'
---

> **Status — under review.** Depends on RFC-0060 (Aspect Impl Coherence) and
> RFC-0072 (Negative Bounds). Introduces `impl !Aspect for Type` as the mechanism
> for library authors to declare that a type definitively does not implement an
> aspect, overriding any blanket impl that would otherwise grant it.

## Summary

RFC-0072 introduced negative *bounds* — what callers assert at use sites
(`T: !Send`). This RFC introduces negative *impls* — what library authors declare
at definition sites (`impl !Send for Rc<T>`). The two features are complementary
and cover different positions in the type system:

| | Where written | What it says |
|---|---|---|
| Negative bound `T: !Aspect` | Function/type signature | The caller must supply a `T` that does not implement `Aspect` |
| Negative impl `impl !Aspect for T` | Impl block | `T` definitively does not implement `Aspect`, regardless of blanket impls |

Negative impls are needed because blanket impls can inadvertently grant an aspect
to a type that must not have it. Under closed-world coherence (RFC-0060), absence
of a positive impl is sufficient to prove `T: !Aspect` when no applicable blanket
exists. But when a blanket *does* exist, an explicit negative impl is required to
override it.

---

## 1. Syntax

A negative impl is written like a positive impl, with `!` before the aspect name:

```metel
impl<T, brand 'b> !Send for Rc<T, 'b> {}
impl<T, brand 'b> !Sync for Rc<T, 'b> {}
```

The body must be empty. Negative impls carry no method implementations — they are
declarations of non-implementation, not definitions of behaviour.

---

## 2. Semantics

### 2.1 Priority over blanket impls

A negative impl takes priority over any positive blanket impl that would otherwise
apply. If both a blanket `impl<T: Foo> Bar for MyType<T>` and a negative
`impl !Bar for MyType<T>` exist, the negative impl wins: `MyType<T>: !Bar` for
all `T`.

This is the property that makes negative impls necessary. Without them, adding a
blanket impl to the stdlib could silently grant aspects to types that are unsound
to have them.

### 2.2 Finality

A negative impl is final. No positive impl may coexist with a negative impl for
the same type and aspect. The compiler rejects any combination of:

- `impl Bar for MyType` and `impl !Bar for MyType` in the same scope.
- A blanket `impl<T: Foo> Bar for T` and `impl !Bar for MyType` is allowed — the
  negative impl overrides the blanket — but a *concrete* positive impl and a negative
  impl for the same type is a coherence error.

### 2.3 Interaction with negative bounds

A negative bound `T: !Aspect` at a use site is satisfied when:

1. There is an explicit negative impl `impl !Aspect for T`, OR
2. There is no positive impl (concrete or blanket) that covers `T` under
   closed-world coherence (RFC-0060).

Negative impls make the second condition reliable in the presence of blanket impls:
they ensure that a type that must not have an aspect cannot accidentally acquire one.

### 2.4 Inheritance is not negated

A negative impl does not propagate to supertypes or subtypes. `impl !Send for Rc<T>`
makes `Rc<T>: !Send`; it does not make `Arc<T>: !Send` or affect any other type.

---

## 3. Coherence

Negative impls follow the same orphan rules as positive impls. A negative impl
`impl !Aspect for Type` is permitted only when either the aspect or the type is
defined in the current module (or the current stdlib). This prevents downstream
code from negating impls it did not define.

Standard coherence rules from RFC-0060 apply. A negative impl conflicts with a
concrete positive impl for the same type — this is a compile error. A negative impl
overrides a blanket positive impl — this is the intended use case.

---

## 4. When negative impls are needed

Negative impls are needed exactly when:

1. A blanket positive impl exists that covers the target type, AND
2. The target type must not have the aspect.

If no blanket covers the type, absence of a positive impl is sufficient under
closed-world coherence (RFC-0060) — no negative impl is needed.

The primary use case in Metel's stdlib is sendability of smart pointers:

```metel
// Blanket: structs with all-Send fields are Send (auto-impl, RFC-0060)
// Arc<T> satisfies this when T: Send + Sync — intentional
// Rc<T> would satisfy this if its fields were Send — but its field is a
// non-atomic integer, which IS Send by value. The auto-impl would therefore
// incorrectly grant Rc<T>: Send. A negative impl is required to prevent this.

impl<T, brand 'b> !Send for Rc<T, 'b> {}
impl<T, brand 'b> !Sync for Rc<T, 'b> {}
```

---

## 5. Relationship to RFC-0072

RFC-0072 (Negative Bounds) explicitly deferred negative impls (RFC-0072 §5.1). This
RFC is the companion that completes the picture. The two RFCs together cover:

- RFC-0072: negative bounds in signatures — `fun f<T: !Send>(x: T)`
- RFC-0081: negative impls in definitions — `impl !Send for Rc<T>`

Both are needed for a complete negative aspect system. RFC-0072 can be accepted
independently; RFC-0081 is a separate acceptance.

---

## Unresolved Questions

1. **Negative impls for non-marker aspects.** This RFC's examples are all marker
   aspects (no methods). Whether a negative impl should be permitted for an aspect
   with methods is deferred. The body-must-be-empty rule already prevents method
   definitions, which is the right constraint for markers; for aspects with methods,
   a negative impl would be unusual and its interaction with method resolution is
   unclear.

2. **Negative impls and derived aspects (RFC-0012).** Whether `#[derive(Send)]` on
   a type that has a negative impl in scope is a compile error or silently loses is
   deferred to RFC-0012.

---

## References

- RFC-0060 (Aspect Impl Coherence) — orphan rules and closed-world coherence;
  negative impls override blanket impls within the coherence system.
- RFC-0072 (Negative Bounds) — companion RFC; negative bounds at use sites.
- RFC-0074 (Shared Pointers) — primary consumer; `impl !Send for Rc<T>` and
  `impl !Sync for Rc<T>` prevent unsound fiber transfer.
- RFC-0080 (Stdlib Aspects) — `Send` and `Sync` auto-impl rules that make
  negative impls necessary for `Rc<T>`.
