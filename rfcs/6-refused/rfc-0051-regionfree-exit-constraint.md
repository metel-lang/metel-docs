---
id: rfc-0051
title: "RegionFree Exit Constraint"
date: '2026-06-04'
---

> **⏸ On hold (2026-06-13) — memory-strategy reconsideration.** `RegionFree<'r>` only has meaning if region lifetimes are adopted; it is paused with the rest of the region/lifetime model pending the mechanism survey. See `docs/reports/memory-model/memory-strategy-research-directions.md`.

## Summary

Define the `RegionFree<'r>` marker aspect that gates the return type of `region { }` blocks, replacing the interim `Send` approximation used in RFC-0025. `RegionFree<'r>` is precise: it rejects only values that contain pointers tagged with the current region's lifetime `'r`, while allowing non-region raw pointers, `@T` handles, and other non-Send-but-safe values to escape the block. This RFC lands with the region lifetime layer — the point at which `*'r T` becomes a distinct type tracked by the type system.

---

## Motivation

RFC-0025 uses `Send` as the interim exit constraint for `region { }` blocks. This is safe but conservative: `*T` raw pointers are never `Send`, so a pointer to data allocated entirely outside the region cannot escape the block even though it is safe to do so. Two concrete cases are rejected incorrectly:

```metel
let external: Int = 42;
let p: *Int = &external;   // p points outside the region

let result = region {
    let scratch = Region::alloc(ScratchData { ... });
    process(scratch, p);
    p   // ERROR: *Int is not Send — but p is not region-internal
};
```

```metel
let result = region {
    let owned: @Buffer = @Buffer::alloc(1024);
    // @Buffer is Send if Buffer: Send, but *T inside Buffer's fields may not be
    // The over-rejection depends on Buffer's internal representation
    owned
};
```

The interim `Send` approximation is acceptable for the interpreter stage. The full `RegionFree<'r>` marker is needed before the compiler milestone, where these false rejections become a usability problem.

---

## Proposed Design

### `RegionFree<'r>` marker aspect

```metel
aspect RegionFree<'r> { }
```

`RegionFree<'r>` means "contains no pointers tagged with lifetime `'r`." It is parameterised by the region's lifetime to support nested regions: a value may be `RegionFree<'inner>` (safe to escape the inner block) while not being `RegionFree<'outer>` (unsafe to escape the outer block).

Auto-derivation rules:

```
// RegionFree<'r> — can escape the block with lifetime 'r:
//   primitive value types (Int, Float, boolean, String)
//   *T where T is not tagged 'r  (non-region raw pointer)
//   *mut T where T is not tagged 'r
//   @T (owning pointer) — always RegionFree<'r> for any 'r
//   Arc<T> — always RegionFree<'r>
//   structs/enums whose fields are all RegionFree<'r>

// NOT RegionFree<'r> — type error to return:
//   *'r T (pointer produced inside the region block)
//   *mut 'r T
//   any struct/enum containing such a pointer
```

### Block exit enforcement

`region { expr }` desugars to `Region::scope(fun() { expr })` where the return type of the closure is constrained to `RegionFree<'r>`. When `region 'r { }` is used with a named lifetime, the constraint is `RegionFree<'r>` with that specific `'r`. For anonymous `region { }` blocks, the lifetime is anonymous (`'_`) and the constraint is inferred.

### Relationship to `Send`

`RegionFree<'r>` and `Send` are orthogonal. A value can be:
- `Send` but not `RegionFree<'r>` — not possible in practice (region-internal pointers are not `Send` either)
- `RegionFree<'r>` but not `Send` — a `*T` to external data: safe to escape the region, but not safe to send across fibers
- Both `Send` and `RegionFree<'r>` — `Arc<T: Send>`, primitive types, etc.
- Neither — a `*'r T` region-internal pointer

The block exit check transitions from `Send` to `RegionFree<'r>` when this RFC lands. No source-level changes required for programs that only return `Send` types — they satisfy both constraints. Programs that return non-`Send`, non-region `*T` values become valid after this RFC lands.

### Nested regions

For nested `region 'outer { region 'inner { expr } }`, the exit check for the inner block uses `RegionFree<'inner>`. A value that is `RegionFree<'inner>` (does not alias inner-region memory) can escape the inner block. Whether it can also escape the outer block depends on `RegionFree<'outer>`.

A pointer from the outer region (`*'outer T`) is `RegionFree<'inner>` — it does not alias inner memory — but not `RegionFree<'outer>`. This is the mechanism by which outer-region pointers may be used inside inner blocks but cannot escape the outer block.

---

## Staging

This RFC depends on:
1. **Region lifetimes (`*'r T` as a distinct type)** — the type system must tag pointers with their region's lifetime for `RegionFree<'r>` to be checkable. Until then, `Send` serves as the approximation.
2. **`region 'r { }` enforcement** — the `'r` label is currently a no-op (RFC-0025). When region lifetimes land, `'r` becomes a concrete lifetime variable that participates in type-checking.

`RegionFree<'r>` is the bridge between the region allocation layer (RFC-0025) and the full lifetime system. It is the first use of a lifetime-parameterised aspect in Metel.

---

## Open Questions

### OQ-1 — Auto-derivation for generic types

For a generic type `struct Wrapper<T> { inner: T }`, is `Wrapper<T>: RegionFree<'r>` when `T: RegionFree<'r>`? The auto-derivation rule should propagate through generic parameters: `Wrapper<T>` is `RegionFree<'r>` iff all fields are `RegionFree<'r>`, which for a field of type `T` requires `T: RegionFree<'r>`.

This means generic functions that return values from a region must carry a `RegionFree<'r>` bound on their type parameters — similar to how `Send` bounds propagate. Whether this is required explicitly or inferred is an open question.

### OQ-2 — `RegionFree` without a lifetime parameter (current-region shorthand)

Inside a `region { }` block, `RegionFree` without a lifetime parameter could mean "free of the current region's lifetime" — a shorthand for the most common case. This avoids requiring the programmer to name the lifetime just to write a bound. Whether this shorthand is desirable or creates confusion with the parameterised form is open.

---

## References

- RFC-0025: `docs/public/rfcs/6-refused/rfc-0025-region-allocation.md` — region allocation, interim `Send` constraint
- RFC-0028: `docs/public/rfcs/6-refused/rfc-0028-memory-and-reference-model.md` — `@T`, `*T`, `Send` model
- RFC-0046: `docs/public/rfcs/6-refused/rfc-0046-linear-closure-capture.md` — closures in regions gated by `Send` until this RFC lands
- RFC-0048: `docs/public/rfcs/6-refused/rfc-0048-region-pointer-interaction.md` — region × pointer interaction; OQ-2 resolved by this RFC
- Lifetime proposal: `docs/reports/memory-model/lifetime-system-proposal.md` — §4.1 region lifetime integration
