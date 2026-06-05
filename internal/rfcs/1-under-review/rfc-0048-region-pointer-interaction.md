---
id: rfc-0048
title: "Region × Pointer Interaction"
date: '2026-06-04'
---

## Summary

Address three underspecified interactions between the region allocation system (RFC-0025) and the pointer model (RFC-0028): what happens when `@T` boxing occurs inside a `region { }` block, how `RegionFree` is derived and enforced before region lifetimes land, and what the criteria are for which allocations inside a region are redirected to the bump allocator.

---

## Background

RFC-0025 states that "heap allocations inside `region { }` go to the region's bump allocator." RFC-0028 introduces `@T` as an owning heap pointer and `*T` as a non-owning alias. The two RFCs do not address how these pointer forms interact with the region allocator, and RFC-0025's `RegionFree` enforcement is defined in terms of region lifetimes (`*'r T`) that are not yet tracked by the type system.

---

## Open Questions

### OQ-1 — `@T` boxing inside a region

RFC-0025 says heap allocations inside `region { }` are redirected to the bump allocator. `@x` is a heap-allocating operation. The question: does `@x` inside a `region { }` allocate from the region, or from the general heap?

**Option A — `@x` inside a region goes to the general heap (no redirect):**

`@T` carries its own independent lifetime via its linear handle. Region-redirecting it would mean the `@T` handle's backing allocation is freed when the region exits — but the `@T` handle might outlive the region. These are incompatible. The simplest rule: `@x` always allocates from the general heap, inside or outside a region.

Region allocation is for non-owning, region-lifetime data (`*T` aliased references, structs accessed via `*'r T`). `@T` is outside that scope.

Tradeoff: clear and safe; no region-escape issue. The programmer uses `Region::alloc(v)` for region-managed allocation and `@v` for general-heap allocation — two distinct tools with distinct lifetimes.

**Option B — `@x` inside a region goes to the region (with escape prevention):**

The `@T` handle becomes a `@'r T` — a region-owned owning pointer. It is not `RegionFree` and cannot escape the block. When the region exits, the allocation is freed automatically along with everything else. The `@T` handle is effectively consumed at region exit.

Tradeoff: allows region-allocated linked structures and trees without a manual free pass. More complex: `@T` and `@'r T` become distinct types; the `@'r T` handle is linear but its lifetime is controlled by the region rather than explicit consumption. Requires region lifetimes to be properly enforced.

**Recommendation:** Option A for now, revisited when region lifetimes (`*'r T`) are introduced.

---

### OQ-2 — Interim exit constraint ✓ Resolved

**Decision: `Send` is used as the interim exit constraint (RFC-0025).**

The full `RegionFree<'r>` marker is deferred to RFC-0051 and lands with region lifetimes. Until then, the `region { }` block's return type must be `Send`. This is conservative — non-region `*T` pointers are also not `Send` and cannot escape — but is safe and requires no new machinery. See RFC-0051 for the precise `RegionFree<'r>` design.

---
### OQ-3 — Implicit allocation scope and criteria

RFC-0025 says "heap allocations go to the region's bump allocator" and lists `&x`, `&mut x`, and "struct construction stored via pointer" as redirected operations. The criteria for what counts as a redirectable allocation are underspecified.

Specifically:

- Does `@x` redirect? (Addressed in OQ-1 — proposed: no.)
- Does constructing a struct that fits in a register redirect? (A small struct might be stack-allocated by the compiler regardless.)
- Does `Arc::new(v)` inside a region redirect? (`Arc<T>` is reference-counted and must outlive the region — it should not redirect.)
- Does calling a function that internally heap-allocates redirect? (Indirect allocation through function calls is not visible at the call site.)

**Proposed rule:** Only direct pointer-producing expressions in the surface syntax are redirected: `&x`, `&mut x`, and `Region::alloc(v)`. `@x` is not redirected (general heap). `Arc::new` is not redirected (Arc manages its own allocation). Indirect allocations inside called functions are not redirected — the called function sees the current allocator context, which the runtime propagates implicitly.

This requires the runtime/compiler to maintain a "current allocator" thread-local or calling-convention slot that `region { }` entry sets to the bump allocator and exit resets. Functions that allocate transparently use the current allocator. This is the standard arena-per-thread model.

---

## Constraints

- The `@T` decision (OQ-1) must compose with RFC-0047 (owning pointer completeness) — particularly OQ-2 there (`*T` from `@T`) which asks if `&(*p)` produces a region-internal pointer when `p` is a `@T` inside a region.
- `RegionFree` interim enforcement (OQ-2) must not reject programs that would be valid under the full region lifetime system.
- The implicit allocation rule (OQ-3) must be implementable in the interpreter without a full lifetime system.

---

## References

- RFC-0025: `docs/internal/rfcs/1-under-review/rfc-0025-region-allocation.md` — `RegionFree`, implicit allocation, named region lifetimes
- RFC-0028: `docs/internal/rfcs/1-under-review/rfc-0028-memory-and-reference-model.md` — `@T`, `*T`, pointer model
- RFC-0047: owning pointer completeness — `@T` addressability interacts with region allocation
- Lifetime proposal: `docs/reports/memory-model/lifetime-system-proposal.md` — §4.1 region lifetime integration
