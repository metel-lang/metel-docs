---
status: active
id: rfc-0037
title: "Return-Position impl Aspect"
date: '2026-06-01'
deferred_from: rfc-0035 (Q3)
---

## Summary

Design `impl Aspect` in function return position, where the return type is opaque but known to satisfy the aspect. RFC-0035 accepted `impl Aspect` in parameter position and deferred return-position. This RFC designs the return-position case.

---

## Motivation

Without return-position `impl Aspect`, functions that produce values of a type the caller should not need to name must expose a concrete type:

```metel
fun make_sorter() -> impl Comparable { ... }
fun identity(x: impl Display) -> impl Display { x }  // return type related to param?
```

This leaks implementation details and makes it impossible to change the return type without breaking callers.

---

## Open Questions

### Q1 — Semantics: opaque type or existential?

**Option A — Opaque monomorphised type (recommended):** The return type is a fresh anonymous type variable, fixed at the call site by the function's body. The caller knows only that it satisfies the aspect. The concrete type is determined at compile time (no heap allocation, no vtable). Each call to the function returns the same concrete type.

**Option B — Existential / dynamic dispatch:** The return value is boxed and dispatched through a vtable. Any type satisfying the aspect may be returned, even different types on different code paths. Requires heap allocation.

**Proposal: Option A.** Existential dispatch belongs to a separate dynamic-dispatch feature. Opaque types are the simpler, more predictable model and do not require the runtime to support vtables.

### Q2 — Can the return type relate to a parameter type?

```metel
fun identity(x: impl Display) -> impl Display { x }
```

Is the return `impl Display` the same type as the parameter `impl Display`, or a fresh independent type?

**Option A — Independent (simpler, recommended for this RFC):** Each `impl Aspect` in a signature is always independent. The above compiles only if the body's return type unifies with a fresh type variable bounded by `Display`. Since the body returns `x` (of the parameter's anonymous type), unification succeeds implicitly — no special rule needed.

**Option B — Named linkage:** Allow syntax like `fun identity(x: impl Display) -> impl(x) Display` to explicitly link the return type to a parameter. Deferred as a further extension.

**Proposal: Option A.** Linkage falls out naturally from unification without special syntax in the common case. Named linkage can be added later if needed.

### Q3 — Can two return-position `impl Aspect` in one signature be different types?

```metel
fun pair() -> (impl Display, impl Display) { ... }
```

**Option A — Each is independent (consistent with RFC-0035 Q2, recommended):** Each `impl Display` is a fresh type variable. The two elements of the tuple may be different concrete types.

**Option B — They must be the same type.**

**Proposal: Option A** for consistency with RFC-0035's parameter-position rule.

### Q4 — Interaction with type inference for the caller

The caller receives a value whose type is opaque. Can they call aspect methods on it?

**Proposal:** Yes. The caller knows the value satisfies the declared aspect and may call any method defined by that aspect. The concrete type is not nameable by the caller.

---

## Decision

**Outcome:** Draft — open for review

All questions above need resolution before implementation. Once accepted, this extends RFC-0035 to cover return-position `impl Aspect`.
