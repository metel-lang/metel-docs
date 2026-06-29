---
id: rfc-0073
title: "AutoRegion"
date: '2026-06-29'
---

> **Status — under review.** Depends on RFC-0063 (Region Handles), RFC-0065 (Region
> Ergonomics), RFC-0066 (Region Pointer Extraction), RFC-0071 (Ownership and Move
> Semantics), and RFC-0072 (Negative Bounds). Introduces `AutoRegion` as a stdlib region
> that delegates allocation strategy entirely to the compiler, preserving lifetime
> relationships while freeing the programmer from allocator decisions.

## Summary

Every existing stdlib region requires a deliberate allocator choice:

| Type | What the programmer commits to |
|---|---|
| `Heap` | Global heap; indefinite lifetime; sendable |
| `LocalHeap` | Thread-local heap; indefinite lifetime |
| `BumpRegion` | Bump arena; scoped; `T: !Drop` for move-out |

`AutoRegion` makes none of these commitments. The programmer expresses **what** — a
scoped lifetime, ownership structure, and borrow relationships — and the compiler decides
**how** to implement the allocation. The type system enforces lifetime relationships and
drop safety identically to any other region. The allocation strategy is the compiler's
concern.

```metel
AutoRegion::scoped([r]() -> {
    let node = @[r] Node { val: 1 };   // compiler allocates node however it sees fit
    let list = @[r] List::from([node]);
    process(&list);
});   // compiler ensures all drop obligations are met before scope exits
```

---

## Motivation

### The "what vs how" principle

The region system is built around a clean separation: the programmer names a region and
the type system uses that name to enforce lifetime relationships. The name is a lifetime
tag; the allocator behind it is a runtime detail. For `BumpRegion` and `Heap`, the
programmer also commits to the runtime detail — the specific allocator — because that
commitment carries meaningful performance contracts.

For many use cases, that commitment is unnecessary. A function building a temporary
graph, collecting intermediate results, or constructing a response structure cares about
lifetime structure — values staying valid until processed, proper destruction when done,
no use-after-free — but has no opinion on whether those values land on the stack, in a
bump arena, or on the heap. Requiring the programmer to choose anyway is boilerplate:
a decision with a correct default but no useful signal.

`AutoRegion` is the escape hatch: use the region system for lifetime tracking, defer the
allocator decision entirely.

### What explicit regions are still for

The explicit region types remain valuable precisely because their allocator choice is a
semantic commitment, not a preference:

- **`BumpRegion`** is chosen when the programmer wants bulk-free guarantees and is
  willing to enforce `T: !Drop` to get them. The performance contract is the point.
- **`Heap`** is chosen when values must outlive any particular scope or cross fiber
  boundaries. The indefinite lifetime is the point.
- **`Rc`/`Arc`** (RFC-0074) are chosen when shared ownership is required. The reference
  count is the point.

`AutoRegion` is for when none of those points apply and the programmer just wants
lifetime tracking.

---

## Design

### The region allocator interface

`AutoRegion` implements the region allocator interface (RFC-0063 §1.1):

```metel
impl Region for AutoRegion {
    type AllocationError = !;
}
```

`AllocationError = !` declares the region infallible. The compiler is responsible for
selecting a strategy that succeeds; OOM within an `AutoRegion` scope panics rather than
returning an error to the programmer. This is the correct contract: the programmer has
surrendered the allocation decision, so they cannot meaningfully handle allocation
failure from a specific strategy they did not choose.

### Creation

Two forms, identical to `BumpRegion` (RFC-0063 §1):

**Closure-scoped:**

```metel
AutoRegion::scoped([r]() -> {
    let x = @[r] HeavyValue::compute();
    use(&x);
});
```

**Variable-scoped:**

```metel
let r = AutoRegion::new();
let x = @[r] HeavyValue::compute();
use(&x);
drop(r);
```

The bracket channel, `@`-position elision (RFC-0065), and call-site inference all work
identically to any other region.

### The compiler's latitude

Within an `AutoRegion` scope, the compiler is free to implement any allocation strategy
or combination of strategies, subject to the guarantees in §Design/Guarantees. The
compiler may:

- **Stack-allocate** values that provably do not escape the current stack frame, even
  when the region tag `r` is threaded into called functions, as long as the borrow
  checker guarantees those functions cannot retain a pointer past the frame's lifetime.
- **Arena-allocate** groups of allocations with compatible lifetimes, bulk-freeing when
  the region drops.
- **Heap-allocate** individual values when escape analysis cannot guarantee stack safety
  or arena placement.
- **Inline** values into their containing struct's storage when the layout permits.
- **Elide** allocations entirely for values that are immediately consumed and have no
  observable address.
- **Combine strategies** within a single `AutoRegion` scope — some values on the stack,
  others in an arena, others on the heap — based on per-value analysis.

The strategy is an implementation detail. The programmer must not rely on which strategy
is chosen for any given allocation; this is not part of the language's observable
semantics. In particular, taking the address of a region-allocated value and comparing it
to stack or heap ranges is not a defined operation.

### Guarantees

The compiler's latitude is bounded by the following guarantees, which hold regardless of
which strategy is chosen:

**Soundness.** Every `@[r] T` pointer is valid for the full declared lifetime of `r`.
No strategy may produce a dangling pointer that the borrow checker accepts.

**Drop completeness.** Every value allocated into an `AutoRegion` that implements `Drop`
has its destructor called exactly once — either when the value is moved out of the region
(at which point the caller owns the destructor obligation) or when the region itself is
dropped. No `T: Drop` value is silently leaked.

**Drop ordering.** Destructors run in reverse-declaration order, consistent with
RFC-0071 §5. The ordering is the same as if all allocations had been stack-allocated
local bindings in the order they were created.

**Move-out safety.** Moving a value out of an `AutoRegion` (RFC-0066 §2) is always safe.
No `T: !Drop` restriction applies — the compiler is responsible for correctly managing
the destructor obligation when a value is moved out, regardless of which backing strategy
was used for that slot.

**Observational equivalence.** For any program that compiles with `AutoRegion`, replacing
every `@[r] T` allocation with an equivalent `@[Heap] T` allocation produces a program
with identical observable behavior (same values, same drop order, same panics). The
compiler's chosen strategy must not alter observable behavior.

### Sendability

`@[r] T` where `r` is an `AutoRegion` binding is never sendable, regardless of which
backing strategy the compiler selects. The scoped tag is non-sendable by the existing
rule (RFC-0063 §4). This is intentional: the compiler may use stack allocation, which is
inherently tied to the current fiber's stack. The non-sendable guarantee is statically
unconditional — the programmer cannot accidentally send a value whose backing may be on
the stack.

When cross-fiber data is needed, `@[Heap] T` or `@[Arc] T` (RFC-0074) are the correct
choices.

### Interaction with SubRegion (RFC-0069)

`AutoRegion` participates in SubRegion typing identically to any other region. The
compiler's strategy selection must respect `Outlives` relationships: if `r: SubRegion<R>`,
no `@[r] T` allocation may outlive the outer region `R`, regardless of backing strategy.

### Interaction with struct-owned regions (RFC-0068)

`[own r]` struct declarations may use `AutoRegion` as the backing allocator. The struct's
constructor creates the `AutoRegion`; the struct's destructor drops it, which satisfies
all drop obligations for the region's allocations before the struct's own storage is freed.

```metel
struct Cache[own r] {
    entries: @[r] List<CacheEntry>,
}
```

The backing allocator for `[own r]` is the subject of a separate open question (see
§Unresolved questions). Until that question is resolved, `[own r]` continues to desugar
to `BumpRegion`. The relationship described above is illustrative.

---

## The stdlib regions

| Type | Lifetime | Allocator decision | Move-out | Sendable |
|---|---|---|---|---|
| `Heap` | Indefinite | Programmer (global heap) | Always safe | Yes |
| `Arc` | Indefinite, atomic RC | Programmer (RFC-0074) | Always safe | Yes |
| `LocalHeap` | Indefinite, thread-local | Programmer (thread-local heap) | Always safe | No |
| `Rc` | Indefinite, non-atomic RC | Programmer (RFC-0074) | Always safe | No |
| `AutoRegion` | Scoped | **Compiler** | Always safe | No |
| `BumpRegion` | Scoped, bump arena | Programmer (bump arena) | `T: !Drop` only | No |

---

## Alternatives considered

### `AutoRegion` as bump arena with drop tracking (previous design)

The previous version of this RFC defined `AutoRegion` as a specific allocator: a bump
arena that additionally maintains a drop list to track `T: Drop` allocations and call
their destructors at region drop. This is a valid design and fills the gap left by
`BumpRegion`'s `T: !Drop` restriction.

It is not the right design for the intended purpose. A bump-plus-drop-list `AutoRegion`
gives the programmer a specific performance contract (arena allocation, bounded overhead
per `T: Drop` slot) that they may not want and did not ask for. The present design does
not constrain the compiler to any strategy; if a bump-plus-drop-list turns out to be the
optimal choice for a given program, the compiler is free to use it — but the programmer
does not need to know or care.

### Make `AutoRegion` an opt-in mode on `BumpRegion`

A `BumpRegion<Strategy>` type parameter could select between strict mode (the current
`T: !Drop` restriction) and auto mode (compiler-managed drop tracking). This conflates
two decisions: the choice to use a bump arena (a concrete allocator) and the choice to
delegate drop management. They are independent. Keeping them as separate types is cleaner.

### Infer the region automatically without naming it

Rather than requiring `AutoRegion::scoped([r]() -> { ... })`, the compiler could infer
a compiler-managed region for all allocations in a scope without any annotation.
This is appealing but removes the programmer's ability to name the region tag — which is
precisely what makes lifetime errors legible. The explicit name `r` is the feature, not
the burden. `AutoRegion` keeps it.

---

## Unresolved questions

1. **Minimum optimization requirement.** This RFC specifies what the compiler is
   *allowed* to do, not what it is *required* to do. A correct but unoptimized
   implementation that heap-allocates every `AutoRegion` slot is semantically valid.
   Whether the language should mandate a minimum optimization effort — e.g., "the
   compiler must attempt stack allocation for values that provably do not escape their
   stack frame" — is a language/specification question distinct from soundness. Deferred.

2. **Observability of strategy choice.** The RFC states that the strategy is unobservable,
   but does not define what "observable" means precisely. If a program takes the address
   of a region-allocated value (via unsafe) and dereferences it after the region drops, the
   behavior is undefined regardless of strategy — this is consistent with the general model.
   A precise definition of the observability boundary is deferred to the unsafe semantics RFC.

3. **Interaction with const evaluation and comptime (RFC-0055).** Whether `AutoRegion`
   is usable in comptime contexts, and what "compiler-managed allocation" means at compile
   time, is unspecified. Deferred.

4. **Backing allocator for `[own r]` structs.** How the programmer specifies whether
   `[own r]` uses `BumpRegion`, `AutoRegion`, or another region type is an open question
   not addressed here. Deferred to a future RFC.

5. **Debug vs release strategy stability.** Programs that use `unsafe` to observe
   allocation addresses may behave differently under debug (heap-only fallback) and
   release (stack allocation) builds. The RFC does not address whether the strategy must
   be stable across build modes, or whether strategy instability between builds is
   acceptable. Deferred to the unsafe semantics RFC.

---

## References

- RFC-0063 (Region Handles) — region allocator interface; `@[r] expr`; bracket channel;
  sendability rules.
- RFC-0065 (Region Ergonomics) — `@`-position elision; call-site inference; both apply
  to `AutoRegion` identically.
- RFC-0066 (Region Pointer Extraction) — move-out semantics; `AutoRegion` always
  permits move-out regardless of `T: Drop` status.
- RFC-0068 (Struct-Owned Regions) — `[own r]` interaction.
- RFC-0069 (Sub-Region Typing) — `SubRegion<R>` applies to `AutoRegion` without change;
  the compiler's strategy must respect `Outlives` relationships.
- RFC-0071 (Ownership and Move Semantics) — `Drop` aspect; drop ordering that the
  compiler must preserve regardless of backing strategy.
- RFC-0072 (Negative Bounds) — `T: !Drop`; not required for `AutoRegion` move-out (the
  compiler handles drop tracking regardless of strategy).
