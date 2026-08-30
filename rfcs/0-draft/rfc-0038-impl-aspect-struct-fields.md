---
status: draft
id: rfc-0038
title: "impl Aspect in Struct Fields and Existential Types"
date: '2026-06-01'
deferred_from: rfc-0035 (Q4)
---

> **Spelling note (2026-08-30).** The anonymous parameter/return-position keyword
> is now `extends Aspect`, not `impl Aspect` (RFC-0130, `3-integrated`). This RFC
> keeps the `impl Aspect` spelling below as the historical name of the feature it
> discusses; a future revision that picks this design up should read every
> `impl Aspect` here as `extends Aspect`. RFC-0130 does not change what this RFC
> proposes — only the surface keyword for the parameter-position form.

## Summary

Design `impl Aspect` (spelled `dyn Aspect` to distinguish from parameter-position sugar) in struct fields, enabling existential types with vtable-based dispatch. RFC-0035 restricted `impl Aspect` to parameter position and deferred struct fields. This RFC designs existential types.

---

## Motivation

Without `dyn Aspect` in struct fields, there is no way to store heterogeneous collections or fields of unknown concrete type:

```metel
// Cannot currently write: a struct that holds any Printable value
struct Wrapper { val: impl Display }

// Nor: a heterogeneous list of Printable values
let items: impl Display[] = [1, "hello", true]
```

Both require the concrete type to be **erased** at the storage site. The value is stored as a pointer to the data plus a pointer to a vtable for the aspect — i.e. a fat pointer / trait object. This is a runtime mechanism that does not exist in the interpreter today.

---

## Open Questions

### Q1 — Storage model: fat pointer vs heap-allocated box

**Option A — Fat pointer (recommended):** An existential value is two words: a pointer to the data and a pointer to the vtable. The data lives wherever it was originally allocated. No additional heap allocation.

**Option B — Boxed:** The value is heap-allocated and the existential is a single pointer to a heap object that includes both the data and the vtable.

**Proposal: Option A** for efficiency. Heap allocation should be explicit in Metel, not a hidden cost of using an aspect bound in a struct field.

### Q2 — Syntax: `impl Aspect` vs `dyn Aspect` vs a new keyword

**Option A — `dyn Aspect` for existential, `impl Aspect` only for parameter position (recommended):** Using distinct syntax for the two concepts avoids confusion. `impl Aspect` always means "monomorphised, type erased only at the syntax level". `dyn Aspect` means "runtime-dispatched, vtable-backed existential". This mirrors the Rust distinction.

**Option B — Overload `impl Aspect`:** `impl Aspect` in struct fields means existential. Same syntax, different semantics based on position.

**Proposal: Option A.** Overloading the same syntax for two fundamentally different runtime behaviours (monomorphised vs heap/vtable) is a serious source of confusion.

### Q3 — Aspect methods on existential values

Given `let w: Wrapper = ...`, can you call `w.val.display()`?

**Proposal:** Yes. The vtable stores the function pointers for all aspect methods. Calling an aspect method on a `dyn Aspect` value dispatches through the vtable.

### Q4 — Equality, hashing, and other cross-existential operations

Given two `dyn Comparable` values, can you compare them for equality even if they are different concrete types?

**Proposal:** Comparison between two `dyn Aspect` values is only defined if the aspect's method signature accepts `Self`. Cross-type comparison (comparing an `Int`-backed and a `Float`-backed `dyn Comparable`) is a type error — the typechecker must reject it. This requires the `Self` constraint to flow through the existential, which is a non-trivial typechecker extension — detailed design deferred to implementation.

---

## Decision

**Outcome:** Draft — open for review

All questions above need resolution before implementation. **Note:** This RFC requires runtime changes (vtable support in the evaluator) and is intentionally lower priority than RFC-0036 and RFC-0037.
