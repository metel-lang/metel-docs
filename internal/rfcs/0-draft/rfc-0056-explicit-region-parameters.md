---
id: rfc-0056
title: "Explicit Region Parameters"
date: '2026-06-05'
status: draft
---

## Summary

Extend RFC-0025's `region { }` block with explicit region handles. A `Region<'r>` value can be passed as a function parameter, allowing callees to allocate into the caller's region without making the allocation implicit or invisible. This completes the region model: the `region { }` block form handles the common case (the compiler routes allocations implicitly); the explicit handle form handles API boundaries where the caller needs to declare where returned data lives.

The design is directly inspired by Zig's allocator model, where every allocating function takes an explicit `Allocator` parameter. Metel's regions and Zig's allocators are the same concept at different levels of abstraction — both are scoped allocation pools that free all contents atomically. Zig's practice of passing allocators explicitly provides strong evidence that the same discipline works at scale.

---

## Motivation

RFC-0025 makes the `region { }` block the primary interface. Inside the block, allocations are implicit — the programmer writes normal code and the compiler routes heap allocations to the region's bump allocator. This works well when all allocating code is textually inside the block.

It breaks down when allocating work is delegated to a called function:

```metel
let result = region {
    let items = build_items();   // ← where do these go?
    summarise(items)
};
```

`build_items()` allocates. Under the current model, those allocations go to the current region only if `build_items` is inlined or if the compiler can prove all allocations happen inside the block. For a non-inlined, non-trivial function, the allocation destination is ambiguous. The function signature gives no indication of where its returned pointers live.

**The Zig insight:** Zig solves exactly this problem. Every function that allocates takes an `std.mem.Allocator` parameter. The caller decides where the memory comes from; the function is agnostic. This makes the memory lifetime visible at the API boundary — the type system encodes it. The same discipline should apply to Metel regions.

**Secondary motivations from the Zig comparison:**

1. *Region as capability.* Holding a `Region<'r>` is the *capability* to allocate into `'r`. Functions that do not need to allocate do not take the parameter; functions that do, declare it. The signature is self-documenting.

2. *Multiple region strategies.* Zig has several allocator implementations (arena, fixed-buffer, page, general-purpose, debug). Metel regions should similarly be polymorphic — a `Region` aspect allows different backing implementations to be swapped at the call site (bump for production, debug-checking for tests).

3. *Explicit OOM.* RFC-0025 §Region growth describes automatic growth (the region chains blocks). Whether a region can ever fail to allocate — and how that failure is surfaced — is unspecified. Zig's allocators return errors on OOM. This RFC must answer the question.

---

## Proposal

### The `Region` aspect

`Region<'r>` is an aspect that any region implementation must satisfy:

```metel
aspect Region<'r> {
    fun alloc<T>(self, value: T) -> *'r T;
    fun alloc_slice<T>(self, values: T[]) -> *'r T[];
}
```

The lifetime `'r` is the region's scope lifetime (introduced by the enclosing `region { }` block or by a `region 'r { }` labelled block). The aspect is the mechanism by which different region implementations are interchangeable.

### Obtaining an explicit handle

Inside a `region 'r { }` block, `Region::handle()` produces a `Region<'r>` value:

```metel
let result = region 'r {
    let reg = Region::handle();       // Region<'r>
    let items = build_items(reg);     // items: *'r Items
    summarise(items)
};
```

The handle is a lightweight token — it carries no data beyond the capability to allocate into `'r`. It can be passed to any function that accepts `Region<'r>` or `impl Region<'r>`.

### Passing a region to callees

Functions that allocate into a caller-provided region declare it as a parameter:

```metel
fun build_items(reg: impl Region<'_>) -> *'_ Items {
    let list = reg.alloc(Items { ... });
    // ... populate list
    list
}
```

The anonymous lifetime `'_` means "some region I was given by the caller." The returned pointer lives in whichever region was passed. At the call site:

```metel
region 'r {
    let reg = Region::handle();
    let items = build_items(reg);    // items: *'r Items
    summarise(items)
}
```

The caller controls the lifetime. The callee is lifetime-agnostic.

### Built-in region implementations

Three implementations ship in `std::alloc`:

| Type | Backing | Use case |
|---|---|---|
| `BumpRegion` | Chained heap blocks (RFC-0025 default) | General use; zero per-object overhead |
| `FixedRegion<N>` | Stack-allocated `[u8; N]` | Small, bounded allocations; no heap touch |
| `DebugRegion` | Heap blocks with use-after-free detection | Test and debug builds |

All implement `Region<'r>`. The production default is `BumpRegion`; tests should use `DebugRegion`.

### Region nesting and composition

A region may allocate from another region's backing storage — a child region whose lifetime is strictly shorter than the parent:

```metel
region 'outer {
    let outer_reg = Region::handle();
    let permanent = outer_reg.alloc(PermanentData { ... });

    region 'inner {
        let inner_reg = Region::handle();
        let scratch = inner_reg.alloc(ScratchData { ... });
        // scratch freed when 'inner exits
    }

    // permanent still live
}
```

The lifetime system (RFC-0052) enforces `'outer: 'inner` (outer outlives inner). A `*'inner T` cannot escape into the `'outer` scope.

### OOM handling

Whether a region signals OOM is implementation-defined:

- `BumpRegion` and `FixedRegion` never return errors — they grow (bump) or trap (fixed) on exhaustion. This is consistent with RFC-0025's "automatic growth" model.
- `DebugRegion` may optionally inject OOM to test error paths.
- A hypothetical `FallibleRegion` wraps any `Region` and returns `Result<*'r T, OomError>` from `alloc`. This is the Zig model for explicit OOM handling.

The `alloc` method on the base `Region` aspect does not return `Result`. Fallible allocation is an opt-in wrapper, not the default. Rationale: most Metel programs target environments where OOM means process death, and making every allocation a `Result` would be an ergonomic burden without benefit.

---

## Relationship to RFC-0025

RFC-0025 defines the `region { }` block and implicit allocation. This RFC is additive — it introduces explicit handles alongside the implicit model. The implicit model (compiler-routed allocations) remains the default for code that does not need to delegate allocation to callees.

The two forms are unified: implicit allocations inside a `region 'r { }` block and explicit `reg.alloc(...)` calls go to the same backing allocator.

---

## Alternatives Considered

**Fully implicit regions (RFC-0025 status quo).** The compiler infers allocation destinations based on control flow and lifetime analysis. This is ergonomic for simple cases but fails at API boundaries — the function signature carries no information about where returned data lives. Non-starter for library code.

**Rust-style lifetime annotations without explicit handles.** Lifetime annotations on return types (`*'r T`) encode where data lives, but without an explicit region parameter, the caller has no mechanism to *choose* the destination at the call site. You need both: the lifetime annotation (for type safety) and the region parameter (for control).

**Always-explicit (Zig model).** Every `region { }` block produces a mandatory handle; implicit allocation is not supported. Ergonomically worse for the common case (all allocating code is textually inside the block) without additional safety benefit. Metel's implicit default is justified.

---

## Open Questions

### OQ-1 — Handle syntax

`Region::handle()` as a free call inside a `region` block is convenient but not obviously connected to the enclosing block's lifetime. Alternatives:
- `region 'r` as a let binding: `let reg = region 'r { ... }` — no good because `region { }` is already an expression.
- Compiler magic: `Region::current()` — always refers to the nearest enclosing region. Simpler syntax but less explicit.
- Explicit scope syntax: `region 'r reg { ... }` — the handle name is declared in the block header. Less familiar but maximally explicit.

### OQ-2 — `impl Region` vs `Region<'r>` in function signatures

Using `impl Region<'_>` as a parameter type is ergonomic but hides the concrete region implementation from the callee's perspective. If a function needs to allocate into two different regions, it must take two `impl Region<'_>` parameters with distinct anonymous lifetimes. Whether the anonymous lifetime syntax is sufficient for this, or whether explicit naming is required, needs design work.

### OQ-3 — Thread safety

`Region<'r>` as defined is single-threaded (the lifetime `'r` is scoped to a fiber or stack frame). A `SharedRegion<'r>` with interior synchronisation (for allocating across fibers into a shared region) is not covered by this RFC. Interaction with Metel's concurrency model is deferred.

### OQ-4 — `FixedRegion` and stack allocation

`FixedRegion<N>` is backed by `[u8; N]` on the stack. This requires knowing `N` at compile time, which in turn requires comptime (RFC-0055). `FixedRegion` cannot be fully specified before comptime is available.

### OQ-5 — The `DebugRegion` detection model

How does `DebugRegion` detect use-after-free? Options: poison memory on region exit (like Zig's `GeneralPurposeAllocator`), maintain a separate metadata map, or use guard pages. The implementation model affects performance and the kind of bugs detected. This is deferred to the implementation RFC.

---

## Timing Recommendation

This RFC depends on RFC-0025 (region blocks), RFC-0052 (lifetime system), and the `impl Aspect` parameter syntax (RFC-0035). It can be designed in parallel with the lifetime system since the two are complementary. Implementation should follow the lifetime system's first stage (syntax and pointer tracking).

---

## References

- RFC-0025: `docs/internal/rfcs/1-under-review/rfc-0025-region-allocation.md` — `region { }` blocks, implicit allocation, `RegionFree`
- RFC-0052: `docs/internal/rfcs/0-draft/rfc-0052-lifetime-system.md` — `*'r T`, region lifetime `'r`, `RegionFree<'r>`
- RFC-0051: `docs/internal/rfcs/1-under-review/rfc-0051-regionfree-exit-constraint.md` — exit constraint
- RFC-0055: `docs/internal/rfcs/0-draft/rfc-0055-comptime.md` — required for `FixedRegion<N>` (OQ-4)
- Zig allocator documentation: https://ziglang.org/documentation/master/#Choosing-an-Allocator
- Language spec: `docs/public/spec.md`

---

## Decision

**Outcome:** *(pending)*
**Target:** *(set when accepted)*

*(Decision rationale goes here when the RFC is evaluated.)*
