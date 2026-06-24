---
id: rfc-0025
title: "Region Allocation"
date: '2026-05-24'
---

> **⏸ On hold (2026-06-13) — memory-strategy reconsideration.** The region/lifetime approach is paused pending a survey of non-lifetime safety mechanisms (mutable value semantics, generational references, Perceus reference counting). On review, this model's runtime mechanism is essentially `bumpalo`, and its only non-library differentiator (invisible lifetimes) is a softened reimplementation of Rust's model. Do **not** implement. The design is retained as the evaluated "Rust-shaped" branch. See `docs/reports/memory-model/memory-strategy-research-directions.md`.

## Summary

Introduce `region { }` as a block expression that provides bump-allocation from a contiguous heap block. All allocations inside the block go to the region's backing allocator and share a single lifetime `'r` — they are freed atomically when the block exits. No per-object tracking, no reference counting overhead for region-internal values. The block form is the primary interface: it is an expression, handles the region's linearity automatically, and introduces a named lifetime that the compiler can use for inference. `region { }` is the first step of Metel's lifetime system: it is the mechanism by which the programmer declares a lifetime scope without writing a lifetime annotation.

---

## Motivation

Linear types (RFC-0028) give per-object control over allocation and deallocation — the right model for resources with independent lifetimes. It is a poor fit for workloads that allocate many short-lived objects that all become irrelevant at the same point:

- Parsing: an AST built for one source file, discarded once lowered
- Request handling: all per-request state freed when the response is sent
- Graph analysis: scratch nodes and edge lists freed after the algorithm completes
- Game frame: all per-frame allocations freed at frame end

For these patterns, per-object `free()` is not just redundant — it is slower than freeing the entire backing block at once. Region allocation (arena / bump allocation) is the standard solution.

The deeper motivation: regions are also the lowest-cost entry point into Metel's planned lifetime system. A `region { }` block is a visible scope boundary. The compiler infers that everything allocated inside has lifetime `'r` — the programmer declares the scope, the compiler derives the lifetimes. This delivers most of the safety benefit of a lifetime system (no dangling region-internal pointers) with near-zero annotation burden.

---

## Proposed Design

### The `region { }` block

`region { }` is a block expression. Its last expression is its value, which must satisfy `RegionFree` — it must not contain any pointers into the region's backing storage.

```metel
let summary = region {
    let graph = build_graph(edges);   // region-allocated
    compute_summary(@graph)           // returns a plain value — RegionFree
};
// graph and all region-internal allocations freed atomically here
```

`region { expr }` desugars to a call to the `Regionable::run` aspect method — `Regionable::run((_reg) -> { expr })` — exactly as `spawn { expr }` desugars to `Spawnable::spawn` (RFC-0003). The backing strategy defaults to `BumpRegion`. In the bare form no handle is visible: the block scope manages the region's linearity automatically, with no `region.free()` to call. An explicit handle may be bound in the header (`region reg { expr }`) and the strategy chosen (`region reg: DebugRegion { expr }`); the `Regionable` opener aspect, the `Region<'r>` allocator aspect, and handle binding are defined in RFC-0056.

### Implicit allocation

Inside a `region { }` block, heap allocations go to the region's bump allocator rather than the general heap. The programmer writes the same code; the compiler redirects pointer-producing operations (`&x`, `&mut x`, struct construction stored via pointer) to the region's backing block.

```metel
region {
    let node = Node { id: 0, edges: [] };   // bump-allocated
    let p: *Node = &node;                   // *'r Node — region-internal pointer
    process(@p)
}
// node, p freed atomically
```

`Region::alloc(value: T) -> *T` is available as an explicit form when the allocation intent should be visible in the source, but it is not required.

### Region growth

When the region's backing block is exhausted, it automatically grows by allocating a new block and chaining it to the previous one. The region is a linked list of fixed-size blocks; allocation continues transparently from the new block. This is more ergonomic than panicking or returning `Perhaps::None` — the programmer declares a scope boundary, not a capacity limit. The initial block size is a hint; growth is automatic.

### The exit constraint

The block's return type must be `Send` — the interim approximation for "contains no region-internal pointers." The compiler enforces this at the block boundary using the existing `Send` marker.

```metel
// Send — can escape the block:
//   Int, Float, boolean, String — primitive value types
//   Arc<T> where T: Send — reference-counted, Send if inner is
//   structs and enums whose fields are all Send

// NOT Send — type error to return:
//   *T, *mut T — raw pointers are never Send
//   any struct containing a raw pointer
```

`Send` is a conservative approximation. It rejects some valid programs: a `*T` pointing to data allocated entirely outside the region is safe to return, but is not `Send`. This over-rejection is acceptable for the interpreter stage. The full `RegionFree<'r>` marker (RFC-0051) will be more precise: only pointers tagged with the current region's `'r` are rejected, while non-region raw pointers and `@T` handles are allowed to escape. Until RFC-0051 lands, `Send` is the enforced constraint.

### Named region lifetime

A `region { }` block introduces an anonymous lifetime `'_` for the region scope. When the lifetime needs to be named — for annotating a struct or function signature that borrows from the region — the block accepts an explicit lifetime label:

```metel
region 'r {
    let p: *'r Node = Region::alloc(Node { ... });
    let view = NodeView { node: p };   // struct parameterised by 'r
    process(@view)
    // process returns a RegionFree value; view and p freed here
}
```

Named region lifetimes are the exception, not the rule. Most `region { }` blocks never need a name — the anonymous lifetime is sufficient and the compiler infers it. The name surfaces only when a struct or function signature needs to carry the lifetime explicitly.

The `region 'r { }` syntax is parsed and accepted now. Until region lifetimes are fully introduced, the `'r` label is a no-op — it is recorded but not yet enforced as a distinct lifetime type. This allows code to be written with named region lifetimes today and become precise as the lifetime system lands, without a syntax change.

This is the bridge to the full lifetime system: once abstract lifetime variables are introduced on function signatures, `'r` in `region 'r { }` becomes a concrete named lifetime that participates in the general constraint system.

### Named region types

A programmer may define a named region **strategy** for documentation and API clarity — the region analogue of defining a custom `Spawnable` type (RFC-0003):

```metel
linear struct FrameArena: Regionable { /* wraps BumpRegion */ }
linear struct RequestArena: Regionable { /* wraps BumpRegion */ }
```

A named region type is a `linear struct` that implements `Regionable` (and provides a `Region<'r>` handle to the scope body), exactly like the built-in `BumpRegion`/`DebugRegion` strategies defined in RFC-0056 — typically by wrapping `BumpRegion` for its backing. It participates in the `region { }` syntax by being named in the header, just as a custom `Spawnable` type plugs into `spawn { }`:

```metel
fun render(reg: impl Region<'_>) -> Frame { ... }   // any arena

region reg: FrameArena { render(reg) }               // this arena, by name
```

It behaves identically to a bare `region { }` block (which uses the default `BumpRegion`) but carries a distinct type name that documents intent and lets APIs be scoped to a specific arena. The bare block uses `BumpRegion`; a named type is the explicit alternative when the arena identity matters at API boundaries. No compiler change is needed to add one — implementing the aspect is enough.

### `region { }` is an expression

The block produces a value. It composes naturally with let-bindings, function arguments, and control flow:

```metel
// Let-binding
let tokens = region { tokenise(source) };

// Directly in a function argument
process(region { build_graph(edges) });

// As one arm of a match
let result = match mode {
    Mode::Fast => region { fast_parse(src) },
    Mode::Full => region { full_parse(src) },
};
```

### Nested regions

Nested `region { }` blocks each introduce a distinct lifetime. A pointer from an outer region (`*'r1 T`) is valid inside the inner block and may be passed out of it — the outer region outlives the inner. A pointer from the inner region (`*'r2 T`) cannot escape the inner block.

```metel
region 'outer {
    let big: *BigStruct = Region::alloc(BigStruct { ... });   // *'outer BigStruct

    let result = region 'inner {
        let scratch: *Scratch = Region::alloc(Scratch { ... });   // *'inner Scratch
        compute(big, scratch)   // big is *'outer — valid inside inner; scratch is *'inner
        // scratch freed here; big is still live
    };

    finish(big, result)
}
// big freed here
```

### Option B — direct allocation in `unsafe`

Inside `unsafe { }` blocks (RFC-0026), a `Region` value may be created and used directly without the block scope:

```metel
unsafe {
    let region = Region::new(65536);
    let tokens = region.alloc(tokenise(source));
    let tree   = region.alloc(parse(tokens));
    let result = lower(tree);
    region.free();
    // tokens and tree are now invalid — programmer's responsibility
    result
}
```

This is a performance escape hatch. No `RegionFree` enforcement, no lifetime tagging. Use-after-free is possible and undetected. Requires explicit `unsafe` to make the absence of guarantees visible.

### `Region` is not `Send`

The backing block is single-fiber. `Region` does not implement `Send` and cannot cross fiber boundaries or be captured by `spawn { }`. Region allocation is a single-fiber primitive. For multi-fiber scratch work, each fiber creates its own `region { }` block.

### Interaction with closures (RFC-0006)

A `region { }` block may contain closures. A closure inside the block captures values as normal. If the closure captures a region-internal pointer, it is itself not `RegionFree` and cannot escape the block — the same constraint applies.

Move-capture of a region-internal value into a closure that escapes the block is a type error.

---

## Desugaring reference

The `region` block is sugar over the `Regionable::run` aspect method (RFC-0056), mirroring how `spawn { }` is sugar over `Spawnable::spawn` (RFC-0003). Region strategies (`BumpRegion`, `DebugRegion`, `FixedRegion<N>`) are the `Regionable` implementations; a bare block uses `BumpRegion`, and the closure receives the `Region<'r>` handle (`_reg` when the header binds no name).

| Surface syntax | Desugars to |
|---|---|
| `region { expr }` | `Regionable::run((_reg) -> { expr })` — strategy `BumpRegion` |
| `region 'r { expr }` | `Regionable::run((_reg) -> { expr })`, lifetime `'r` named for annotations |
| `region reg { expr }` | `Regionable::run((reg) -> { expr })` — handle bound (RFC-0056) |
| `region reg: S { expr }` | `S::run((reg) -> { expr })` — strategy `S` selected (RFC-0056) |
| `reg.alloc(v)` inside block | bump-allocates `v` in `reg`'s backing block → `*'r T` |
| `&x` inside block | takes address of `x` in region memory → `*'r T` |

---

## Relationship to the lifetime system

`region { }` is the first concrete step of Metel's staged lifetime system:

- **This RFC**: `region { }` block introduces lifetime `'r`; `RegionFree` (approximated by `Send`) enforces scope exit. Programmer writes zero lifetime annotations for the common case.
- **Region lifetime extension**: `*'r T` becomes a distinct type; `RegionFree<'r>` replaces `Send` as the exit constraint. Struct and function signatures may carry `'r` when needed. This is also when safe borrowing of linear values via `*T` becomes possible.
- **Full lifetime system**: abstract lifetime variables on function signatures for cross-region and cross-function borrow relationships. `'r` from `region 'r { }` participates in the general constraint system.

Each step is additive. Nothing in this RFC forecloses the later layers.

---

## Alternatives Considered

### Explicit `Region::scope` callback only

The previous design used `Region::scope(fun(r) { r.create(value) })`. The `region { }` block is strictly more ergonomic: no callback syntax, no explicit region handle, no `r.create()`, no `move fun` required for closure interaction. The block desugars to the same thing internally — now `Regionable::run` (RFC-0056).

This rejected *callback-only* as the design. RFC-0056 reintroduces the callback as an explicit **secondary** form (`Regionable::run((reg) -> { ... })`) for cases where the scope must be a value — passed to a combinator, selected at runtime, or built by a library. The block remains the default and the canonical desugaring target; the callback is opt-in, not mandatory.

### Per-object linear allocation only

Linear types handle objects with independent lifetimes. For batch-lifetime workloads, per-object `free()` is correct but slower than bulk deallocation. Regions are complementary, not a replacement.

### GC / tracing collector

A garbage collector eliminates manual memory management entirely but introduces pause times and runtime overhead. Regions are a zero-overhead alternative for bounded-lifetime workloads.

---

## Resolved Questions

1. **Exit constraint ✓ Resolved** — `Send` is used as the interim exit constraint. Conservative: raw `*T` pointers are never `Send` so they cannot escape even if non-region-internal. The precise `RegionFree<'r>` marker is deferred to RFC-0051 and lands with region lifetimes.

2. **Implicit vs explicit allocation ✓ Resolved** — Fully implicit. All heap allocations inside `region { }` redirect to the bump allocator automatically. `Region::alloc(value)` remains available as an explicit form for clarity, but is not required.

3. **Region growth ✓ Resolved** — Auto-grow. When the backing block is exhausted, the region allocates a new block and chains it. The programmer declares a scope boundary, not a capacity limit. Growth is transparent.

4. **Named region types ✓ Resolved** — Supported. A `linear struct` may implement the `Region` aspect to define a named region type (`struct FrameArena: Region`). Useful for documentation and API scoping.

5. **`region 'r { }` syntax timing ✓ Resolved** — Parsed now. The `'r` label is accepted syntactically in this RFC. Until region lifetimes are fully introduced, the label is recorded but not enforced as a distinct lifetime type. No syntax change required when lifetimes land.

---

## References

- RFC-0028: memory and reference model — `Region` is a linear type; linear checker applies inside the block
- RFC-0043: regular pointers (incorporated) — `&x` inside a region block produces a region-internal pointer
- RFC-0003: concurrency model (resolved) — `Region` is not `Send`; single-fiber primitive
- RFC-0006: closure capture semantics — closures inside `region { }` blocks; move capture of region handles
- RFC-0026: unsafe blocks — Option B (direct `Region::new`/`free`) requires unsafe context
- RFC-0051: RegionFree exit constraint — full `RegionFree<'r>` marker replacing `Send`; lands with region lifetimes
- Lifetime proposal: `docs/reports/memory-model/lifetime-system-proposal.md` — §4.1 and §6.1 for the region-lifetime integration design
- Cluster report: `docs/reports/memory-model/rfc-cluster-memory-model.md`
- Prior art: Cyclone regions, Rust `bumpalo` crate, Zig `std.mem.Allocator`
