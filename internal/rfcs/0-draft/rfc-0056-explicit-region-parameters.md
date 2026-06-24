---
id: rfc-0056
title: "Explicit Region Parameters"
date: '2026-06-05'
status: draft
---

> **⏸ On hold (2026-06-13) — memory-strategy reconsideration.** This RFC extends the region/lifetime model, which is paused pending a survey of non-lifetime safety mechanisms. The aspect/handle design here (OQ-1 resolved, `Regionable` sugar) is sound but inherits the region model's derivative-vs-Rust problem. Do **not** implement. Retained as part of the evaluated "Rust-shaped" branch. See `docs/reports/memory-model/memory-strategy-research-directions.md`.

## Summary

Extend RFC-0025's `region { }` block with explicit region handles. A `Region<'r>` value can be passed as a function parameter, allowing callees to allocate into the caller's region without making the allocation implicit or invisible. This completes the region model: the `region { }` block form handles the common case (the compiler routes allocations implicitly); the explicit handle form handles API boundaries where the caller needs to declare where returned data lives.

The design is directly inspired by Zig's allocator model, where every allocating function takes an explicit `Allocator` parameter. Metel's regions and Zig's allocators are the same concept at different levels of abstraction — both are scoped allocation pools that free all contents atomically. Zig's practice of passing allocators explicitly provides strong evidence that the same discipline works at scale.

Structurally, regions follow the **same philosophy as the concurrency model** (RFC-0003): the `region` block is *language sugar over aspect method calls*, and region strategies (`BumpRegion`, `DebugRegion`, `FixedRegion`) are *aspect implementations selectable by type* — exactly as `spawn { }` is sugar for `Spawnable::spawn` and works over both `Fiber` and `Thread`. The `region` block is to `Regionable` what the `spawn` block is to `Spawnable`.

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

### Aspects and desugaring

Following RFC-0003's model — *syntax desugars to aspect method calls, and any type implementing the aspect participates in the syntax* — the `region` block rests on two aspects. This makes regions structurally identical to `spawn`: a scoped block that desugars to an aspect method taking a closure, with multiple backing implementations selectable by type.

**The allocator aspect** — the capability passed *into* the scope; it carries the lifetime `'r`:

```metel
aspect Region<'r> {
    fun alloc<T>(self, value: T) -> *'r T;
    fun alloc_slice<T>(self, values: T[]) -> *'r T[];
}
```

The lifetime `'r` is the region's scope lifetime. This aspect is the mechanism by which different region implementations are interchangeable as *allocators*.

**The opener aspect** — mirrors `Spawnable`; implemented by each region strategy. Its method opens a scope, hands the closure a `Region<'r>` handle, runs it, tears the arena down, and returns the `RegionFree` result:

```metel
aspect Regionable {
    fun run<'r, R: RegionFree>(f: fun(Region<'r>) -> R) -> R;
}
```

**Desugaring** (parallel to RFC-0003's `spawn` table):

| Syntax | Desugars to |
|---|---|
| `region { BODY }` | `Regionable::run((_reg) -> { BODY })` — default strategy `BumpRegion` |
| `region reg { BODY }` | `Regionable::run((reg) -> { BODY })` |
| `region 'r reg { BODY }` | `Regionable::run((reg) -> { BODY })` with `'r` named for annotations |
| `region reg: DebugRegion { BODY }` | `DebugRegion::run((reg) -> { BODY })` — strategy selected |

**Strategy selection mirrors `Fiber` vs `Thread`.** In RFC-0003, `spawn { }` produces a `Fiber<T>` or a `Thread<T>` depending on the declared type, because both implement `Spawnable`. Here, `region { }` runs on `BumpRegion`, `DebugRegion`, or `FixedRegion<N>` depending on the strategy named in the header, because all implement `Regionable`:

```metel
let f: Fiber<Int>  = spawn { compute() };        // M:N fiber        (RFC-0003)
let t: Thread<Int> = spawn { compute() };        // OS thread        (RFC-0003)

region reg { ... }                    // BumpRegion — the default
region reg: DebugRegion { ... }       // use-after-free detection
region reg: FixedRegion<4096> { ... } // stack-backed (needs RFC-0055)
```

**One structural difference from `spawn`.** `spawn`'s closure takes no argument and the handle (`Fiber<T>`) comes *out* — it escapes and is joined later. A region's closure takes the `Region<'r>` handle *in*, and only a `RegionFree` value comes *out* — the handle is a scoped, linear, non-`Send` capability that must not escape. This is the difference between "the handle escapes and is the result" (fibers) and "the handle is scoped and the result escapes past it" (regions), and it is exactly why the region closure is `(reg) -> R` rather than `() -> T`.

### Obtaining an explicit handle

The handle is bound **in the block header** — there is no magic free function. Both the lifetime name `'r` and the handle name are optional and independent: name `'r` only when a type annotation needs to mention it, name the handle only when you allocate explicitly or pass it to a callee (see OQ-1, resolved).

```metel
region { ... }                 // nothing named: implicit allocation only (common case)
region reg { ... }             // handle bound as reg: Region<'_>; lifetime anonymous
region 'r { ... }              // lifetime named (for *'r T annotations); no handle
region 'r reg { ... }          // both: reg: Region<'r>
region reg: DebugRegion { ... }// handle bound, backing strategy chosen
```

```metel
let result = region 'r reg {      // reg: Region<'r>, bound in the header
    let items = build_items(reg);  // items: *'r Items
    summarise(items)
};
```

The handle is a lightweight token — it carries no data beyond the capability to allocate into `'r`. It can be passed to any function that accepts `Region<'r>` or `impl Region<'r>`.

**Callback form.** The same scope is also available as a higher-order call — this *is* the opener aspect method `Regionable::run` (see "Aspects and desugaring"). The handle arrives as an explicit closure parameter. Use it when the scope is itself a value (passed to a combinator, selected at runtime, or constructed by a library):

```metel
let result = Region::run((reg) -> {            // reg: Region<'r>; defaults to BumpRegion
    summarise(build_items(reg))                // RegionFree result escapes
});

let report = DebugRegion::run((reg) -> { ... });   // strategy selected via the aspect impl
```

The block is sugar over this call: `region 'r reg { BODY }` desugars to `Regionable::run((reg) -> { BODY })`. `Region::run` is the convenience entry that defaults to `BumpRegion`; calling `Strategy::run` on a concrete strategy selects it, exactly as `spawn` selects `Fiber` vs `Thread`. Both the block and callback forms are supported; the block is the default for ordinary lexical scopes.

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
region 'r reg {
    let items = build_items(reg);    // items: *'r Items
    summarise(items)
}
```

The caller controls the lifetime. The callee is lifetime-agnostic.

### Built-in region implementations

Three strategies ship in `std::alloc`. Each implements `Regionable` (so it participates in the `region { }` syntax, like `Fiber`/`Thread` with `spawn`) and provides a `Region<'r>` handle to the scope body:

| Type | Backing | Use case |
|---|---|---|
| `BumpRegion` | Chained heap blocks (RFC-0025 default) | General use; zero per-object overhead |
| `FixedRegion<N>` | Stack-allocated `[u8; N]` | Small, bounded allocations; no heap touch |
| `DebugRegion` | Heap blocks with use-after-free detection | Test and debug builds |

All implement `Regionable` + `Region<'r>`. The production default — selected by a bare `region { }` — is `BumpRegion`; tests should use `region reg: DebugRegion { }`. New strategies are added simply by implementing the two aspects; no compiler change is needed, exactly as a new `Spawnable` type plugs into `spawn`.

### Region nesting and composition

A region may allocate from another region's backing storage — a child region whose lifetime is strictly shorter than the parent:

```metel
region 'outer outer_reg {
    let permanent = outer_reg.alloc(PermanentData { ... });

    region 'inner inner_reg {
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

### OQ-1 — Handle syntax ✓ Resolved

**Decision:** The handle is bound in the **block header**, not produced by a magic free function. `Region::handle()` / `Region::current()` are dropped. The header carries an optional lifetime name and an optional handle name, independently: `region { }`, `region reg { }`, `region 'r { }`, `region 'r reg { }`. The backing strategy may be ascribed: `region reg: DebugRegion { }`.

A **callback form** is also supported — `Region::run((reg) -> { ... })`, or `Strategy::run((reg) -> { ... })` to pick a backing — where the handle is an explicit closure parameter. This callback is the opener aspect method `Regionable::run` (see "Aspects and desugaring"); the block is sugar over it: `region 'r reg { BODY }` ≡ `Regionable::run((reg) -> { BODY })`. The block is the default for lexical scopes; the callback is for when the scope is itself a value.

**Rationale:** binding the handle in the header makes its provenance explicit (it is a normal binding, not a reach-into-context call) and keeps the lifetime name and handle name optional so the common case stays annotation- and handle-free. Supporting both forms resolves the block-vs-callback tension from RFC-0025 (which rejected a callback-*only* design) without losing the higher-order use cases.

**Rejected alternatives:** `Region::handle()` free call (provenance unclear, not connected to the enclosing lifetime); `Region::current()` compiler magic (even less explicit); `let reg = region 'r { ... }` binding form (`region { }` is already a value-producing expression, so this is ambiguous).

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
