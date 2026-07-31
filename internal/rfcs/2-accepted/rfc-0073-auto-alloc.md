---
id: rfc-0073
title: "AutoAlloc"
date: '2026-06-29'
updated: '2026-07-10'
status: accepted
---

> **Status — under review.** Syntax and terminology updated 2026-07-05. Renamed from
> `AutoRegion` to `AutoAlloc`; all `@[r]` → `@a` syntax updated; `BumpRegion` →
> `BumpAlloc` throughout; SubRegion interaction removed (RFC-0069 retracted). The
> semantic contract — what the compiler is allowed to do and what it must guarantee — is
> unchanged. Depends on RFC-0063 (Allocator Handles), RFC-0065 (Allocator Ergonomics),
> RFC-0066 (Allocated Value Extraction), RFC-0071 (Ownership and Move Semantics), and
> RFC-0072 (Negative Bounds).

> **Status — accepted (2026-07-10).** Phase 0 ratification sweep: split model consistency-checked (RFC-0063 sec9 items 1/2/5 synced with roadmap-2026-07-07 Phase 0 decision; RFC-0066/0068 stale titles fixed); sweeping the cluster from under-review to accepted per reports/implementation/roadmap-2026-07-07.md Phase 0.

## Summary

Every existing stdlib allocator requires a deliberate choice:

| Type | What the programmer commits to |
|------|-------------------------------|
| `Heap` | Global heap; indefinite lifetime; sendable |
| `LocalHeap` | Thread-local heap; indefinite lifetime |
| `BumpAlloc` | Bump arena; scoped; `T: !Drop` for move-out |

`AutoAlloc` makes none of these commitments. The programmer expresses **what** — a
scoped lifetime, ownership structure, and borrow relationships — and the compiler decides
**how** to implement the allocation. The type system enforces drop safety and borrow
validity identically to any other allocator. The allocation strategy is the compiler's
concern.

```metel
AutoAlloc::scoped((@a) -> {
    let node = @a Node { val: 1 };   // compiler allocates node however it sees fit
    let list = @a List::from([node]);
    process(&list);
});   // compiler ensures all drop obligations are met before scope exits
```

---

## Motivation

### The "what vs how" principle

The allocator system separates two concerns: the programmer names an allocator and the
type system uses that name to enforce lifetime structure. For `BumpAlloc` and `Heap`,
the programmer also commits to the runtime detail — the specific allocator — because
that commitment carries meaningful performance contracts.

For many use cases, that commitment is unnecessary. A function building a temporary
graph, collecting intermediate results, or constructing a response structure cares about
lifetime structure — values staying valid until processed, proper destruction when done,
no use-after-free — but has no opinion on whether those values land on the stack, in a
bump arena, or on the heap. Requiring the programmer to choose anyway is boilerplate.

`AutoAlloc` is the escape hatch: use the allocator system for lifetime tracking, defer
the allocator decision entirely.

### What explicit allocators are still for

The explicit allocator types remain valuable precisely because their choice is a
semantic commitment:

- **`BumpAlloc`** is chosen when bulk-free guarantees and `T: !Drop` discipline are the
  point.
- **`Heap`** is chosen when values must outlive any particular scope or cross fiber
  boundaries.
- **`Rc`/`Arc`** (RFC-0074) are chosen when shared ownership is required.

`AutoAlloc` is for when none of those points apply and the programmer just wants
lifetime tracking.

---

## Design

### The allocator interface

`AutoAlloc` implements the `Alloc` aspect (RFC-0063 §1):

```metel
extend AutoAlloc: Alloc {
    type AllocationError = !;
}
```

`AllocationError = !` declares the allocator infallible.

### Creation

Two forms, identical to `BumpAlloc` (RFC-0063 §5):

**Closure-scoped:**

```metel
AutoAlloc::scoped((@a) -> {
    let x = @a HeavyValue::compute();
    use(&x);
});
```

**Variable-scoped:**

```metel
let a = AutoAlloc::new();
let x = @a HeavyValue::compute();
use(&x);
drop(a);
```

The `@`-elision (RFC-0065) and call-site inference all work identically to any other
allocator.

### The compiler's latitude

Within an `AutoAlloc` scope, the compiler may implement any allocation strategy,
subject to the guarantees below. The compiler may:

- **Stack-allocate** values that provably do not escape the current stack frame.
- **Arena-allocate** groups of allocations with compatible lifetimes, bulk-freeing when
  the allocator drops.
- **Heap-allocate** individual values when escape analysis cannot guarantee stack or
  arena placement.
- **Inline** values into their containing struct's storage when the layout permits.
- **Elide** allocations entirely for values that are immediately consumed.
- **Combine strategies** within a single scope — some values on the stack, others in an
  arena, others on the heap.

The strategy is an implementation detail the programmer must not rely on.

### Guarantees

**Soundness.** Every `@a T` pointer is valid for the full declared scope of `a`.

**Drop completeness.** Every value allocated into an `AutoAlloc` that implements `Drop`
has its destructor called exactly once — either when moved out (obligation transfers) or
when the allocator drops.

**Drop ordering.** Destructors run in reverse-declaration order, consistent with
RFC-0071 §5.

**Move-out safety.** Moving a value out of an `AutoAlloc` (RFC-0066 §2) is always safe
for all `T`, including `T: Drop`. The compiler manages destructor obligations regardless
of backing strategy.

**Observational equivalence.** Replacing every `@a T` allocation with `@Heap T`
produces a program with identical observable behavior.

### Sendability

`@a T` where `a` is an `AutoAlloc` binding is never sendable, regardless of backing
strategy. The compiler may use stack allocation, which is inherently tied to the current
fiber's stack.

---

## Stdlib allocator summary

| Type | Lifetime | Allocator decision | Move-out | Sendable |
|------|----------|-------------------|----------|----------|
| `Heap` | Indefinite | Programmer (global heap) | Always safe | Yes |
| `Arc` | Indefinite, atomic RC | Programmer (RFC-0074) | Always safe | Yes |
| `LocalHeap` | Indefinite, thread-local | Programmer (thread-local heap) | Always safe | No |
| `Rc` | Indefinite, non-atomic RC | Programmer (RFC-0074) | Always safe | No |
| `AutoAlloc` | Scoped | **Compiler** | Always safe | No |
| `BumpAlloc` | Scoped, bump arena | Programmer (bump arena) | `T: !Drop` only | No |

---

## Unresolved questions

1. **Minimum optimization requirement.** A correct but unoptimized implementation that
   heap-allocates every `AutoAlloc` slot is semantically valid. Whether the language
   should mandate a minimum optimization effort is deferred.

2. **Observability of strategy choice.** A precise definition of the observability
   boundary (relevant to unsafe code) is deferred to the unsafe semantics RFC.

3. **Interaction with const evaluation and comptime (RFC-0055).** Whether `AutoAlloc`
   is usable in comptime contexts is unspecified. Deferred.

4. **Debug vs release strategy stability.** Whether the strategy must be stable across
   build modes is deferred to the unsafe semantics RFC.

---

## References

- RFC-0063 (Allocator Handles) — `Alloc` interface; `@a expr`; sendability rules.
- RFC-0065 (Allocator Ergonomics) — `@`-elision; call-site inference; both apply
  to `AutoAlloc` identically.
- RFC-0066 (Allocated Value Extraction) — move-out semantics; `AutoAlloc` always
  permits move-out regardless of `T: Drop` status.
- RFC-0068 (Struct-Owned Allocators) — `(@a: AutoAlloc)` interaction (deferred).
- RFC-0071 (Ownership and Move Semantics) — `Drop` aspect; drop ordering the compiler
  must preserve regardless of backing strategy.
- RFC-0072 (Negative Bounds) — `T: !Drop`; not required for `AutoAlloc` move-out.
