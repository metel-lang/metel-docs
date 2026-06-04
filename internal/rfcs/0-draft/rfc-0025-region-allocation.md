---
id: rfc-0025
title: "Region Allocation"
date: '2026-05-24'
status: draft
---

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

`region { expr }` desugars to `Region::scope(fun() { expr })`. The `Region` value is never visible to the programmer — the block scope handles its linearity automatically. There is no `Region::new`, no `region.free()`, no explicit handle to manage.

### Implicit allocation

Inside a `region { }` block, heap allocations go to the region's bump allocator rather than the RC heap. The programmer writes the same code; the compiler redirects pointer-producing operations (`&x`, `&mut x`, struct construction stored via pointer) to the region's backing block.

```metel
region {
    let node = Node { id: 0, edges: [] };   // bump-allocated
    let p: *Node = &node;                   // *'r Node — region-internal pointer
    process(@p)
}
// node, p freed atomically
```

`Region::alloc(value: T) -> *T` is available as an explicit form when the allocation intent should be visible in the source, but it is not required.

### The `RegionFree` exit constraint

The block's return type must satisfy `RegionFree` — "contains no region-internal pointers." The compiler enforces this at the block boundary.

`RegionFree` is a marker aspect auto-derived for types that contain no `*'r T` fields:

```metel
// RegionFree — can escape the block:
//   Int, Float, Bool, String — primitive value types
//   Arc<T> — reference-counted, not region-internal
//   unique *T allocated outside the block — not tagged 'r
//   structs and enums whose fields are all RegionFree

// NOT RegionFree — type error to return:
//   *Node allocated inside the block — tagged *'r Node
//   any struct that contains such a pointer
```

For now, `RegionFree` is approximated by the existing `Send` bound: since `*T` and `*mut T` are not `Send`, region-internal pointers cannot escape the block. This is conservative — some safe values are rejected. When region lifetimes (`*'r T`) are introduced, `RegionFree<'r>` replaces `Send` as the exit constraint and becomes precise: only pointers tagged with the current region's `'r` are rejected; heap-backed `unique *T` and other non-region pointers may escape freely.

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

This is the bridge to the full lifetime system: once abstract lifetime variables are introduced on function signatures, `'r` in `region 'r { }` becomes a concrete named lifetime that participates in the general constraint system.

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
    let big = Region::alloc(BigStruct { ... });   // *'outer BigStruct

    let result = region 'inner {
        let scratch = Region::alloc(Scratch { ... });   // *'inner Scratch
        compute(@big, @scratch)   // @big borrows 'outer — valid; @scratch borrows 'inner
        // scratch freed here; big is still live
    };

    finish(@big, result)
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

| Surface syntax | Desugars to |
|---|---|
| `region { expr }` | `Region::scope(fun() { expr })` |
| `region 'r { expr }` | `Region::scope_named::<'r>(fun() { expr })` |
| `Region::alloc(v)` inside block | bump-allocates `v` in current region's backing block |
| `&x` inside block | takes address of `x` in region memory → `*'r T` |

---

## Relationship to the lifetime system

`region { }` is the first concrete step of Metel's staged lifetime system:

- **This RFC**: `region { }` block introduces lifetime `'r`; `RegionFree` (approximated by `Send`) enforces scope exit. Programmer writes zero lifetime annotations for the common case.
- **Region lifetime extension**: `*'r T` becomes a distinct type; `RegionFree<'r>` replaces `Send` as the exit constraint; `@'r T` (storable read references tagged with `'r`) are introduced. Struct and function signatures may carry `'r` when needed.
- **Full lifetime system**: abstract lifetime variables on function signatures for cross-region and cross-function borrow relationships. `'r` from `region 'r { }` participates in the general constraint system.

Each step is additive. Nothing in this RFC forecloses the later layers.

---

## Alternatives Considered

### Explicit `Region::scope` callback only

The previous design used `Region::scope(fun(r) { r.create(value) })`. The `region { }` block is strictly more ergonomic: no callback syntax, no explicit region handle, no `r.create()`, no `move fun` required for closure interaction. The block desugars to the same thing internally.

### Per-object linear allocation only

Linear types handle objects with independent lifetimes. For batch-lifetime workloads, per-object `free()` is correct but slower than bulk deallocation. Regions are complementary, not a replacement.

### GC / tracing collector

A garbage collector eliminates manual memory management entirely but introduces pause times and runtime overhead. Regions are a zero-overhead alternative for bounded-lifetime workloads.

---

## Open Questions

1. **`RegionFree` vs `Send` as interim exit constraint.** The `Send` bound is conservative — values containing `unique *T` from outside the region are rejected even though they are safe to return. Introducing `RegionFree` as a distinct marker earlier (before full region lifetime tagging) would be more precise. Is the conservatism acceptable until region lifetimes arrive, or should `RegionFree` be defined now as a separate marker that `Send` implies but does not equal?

2. **Implicit vs explicit allocation.** Should allocation inside `region { }` be fully implicit (all heap allocations redirect to the bump allocator), or should only `Region::alloc(value)` calls allocate from the region? Fully implicit is more ergonomic but requires the compiler to identify all allocation sites. Explicit `Region::alloc` is less magical but more verbose.

3. **Region growth.** If the region's backing block is exhausted, does `Region::alloc` panic, return `Perhaps::None`, or automatically grow by allocating a new block? A growable region (linked list of blocks) is more ergonomic; a fixed-size region is simpler and predictable.

4. **Named region types.** Should a programmer be able to define a typed region (`struct FrameArena: Region`) for documentation and API clarity? Or is `Region` always anonymous and the named lifetime in `region 'r { }` sufficient?

5. **`region 'r { }` syntax timing.** The named lifetime form requires the lifetime system to be at least partially in place. Is `region 'r { }` introduced with this RFC (as syntax that is parsed but whose `'r` is a no-op until lifetimes land), or deferred to the region-lifetime extension RFC?

---

## References

- RFC-0028: memory and reference model — `Region` is a linear type; linear checker applies inside the block
- RFC-0043: regular pointers (incorporated) — `&x` inside a region block produces a region-internal pointer
- RFC-0003: concurrency model (resolved) — `Region` is not `Send`; single-fiber primitive
- RFC-0006: closure capture semantics — closures inside `region { }` blocks; move capture of region handles
- RFC-0026: unsafe blocks — Option B (direct `Region::new`/`free`) requires unsafe context
- Lifetime proposal: `docs/reports/memory-model/lifetime-system-proposal.md` — §4.1 and §6.1 for the region-lifetime integration design
- Cluster report: `docs/reports/memory-model/rfc-cluster-memory-model.md`
- Prior art: Cyclone regions, Rust `bumpalo` crate, Zig `std.mem.Allocator`
