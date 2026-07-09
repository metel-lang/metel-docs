---
id: rfc-0047
title: "Owning Pointer Model Completeness"
date: '2026-06-04'
---

## Summary

Address three gaps in RFC-0028's `@T` owning pointer model: mutability and write-through rules, taking a raw `*T` from an owning pointer, and teardown of recursive `@T` structures. These are not new features — they are underspecified aspects of `@T` that block correct implementation of any non-trivial code using owning pointers.

---

## Background

RFC-0028 establishes `@T` as the unique owning heap pointer. It defines `@x` (boxing), `*p` (dereference), auto-deref at field access and method calls, and the linear handle semantics. Three concrete scenarios are not covered:

1. Writing a new value through an owning pointer.
2. Taking a non-owning `*T` alias to the contents of an `@T`.
3. Freeing a recursive structure whose nodes are linked via `Perhaps<@T>`.

---

## Open Questions

### OQ-1 — `@T` write-through

RFC-0028 shows reading through `@T` via auto-deref. It does not specify whether assignment through `@T` is valid.

**Option A — `@T` is always mutable (write-through allowed):**

```metel
let p: @Int = @42;
*p = 100;   // write through owning pointer — valid
```

`@T` implies sole ownership, and sole ownership implies the right to mutate. No `@mut T` distinction. This matches Rust's `Box<T>` — if you own it, you can mutate it.

Tradeoff: simple; sole ownership makes aliased mutation impossible by construction.

**Option B — mutability is a property of the binding, not the pointer type:**

```metel
let mut p: @Int = @42;
*p = 100;   // valid — binding is mut
let q: @Int = @42;
*q = 100;   // type error — binding is not mut
```

Consistent with how `mut` works elsewhere in Metel. Mutation requires a `mut` binding at the point of use.

Tradeoff: adds `mut` friction. Since `@T` is always unique (no aliasing possible), the restriction does less safety work than `mut` does for `*mut T`.

### OQ-2 — `*T` from `@T` (addressability)

Can you take a raw non-owning pointer to the contents of an owning pointer?

```metel
let p: @Buffer = @Buffer::alloc(1024);
let raw: *Buffer = &(*p);   // is this valid?
```

This is useful for passing to functions that take `*T` without consuming the handle.

**Option A — allowed:**

`&(*p)` is valid. The resulting `*Buffer` is valid for as long as `p` is live. Without a lifetime system, the programmer is responsible for not using `raw` after `p` is consumed. Under the full lifetime system, `raw`'s lifetime would be bounded by `p`'s.

Tradeoff: useful; matches how you'd use `Box<T>` in Rust (`.as_ref()`). Unsound without lifetimes (dangling pointer possible), so should require `unsafe` until the lifetime system enforces validity.

**Option B — not allowed until lifetimes:**

`&(*p)` is a type error. The only way to use the contents is through auto-deref at field/method call sites, which is always bounded by the call expression's lifetime. This is conservative but eliminates a class of dangling pointer bugs.

Tradeoff: more restrictive; forces consume-and-return patterns for functions that would otherwise take `*T`.

**Option C — allowed in unsafe only (until lifetimes):**

`&(*p)` is valid inside `unsafe { }` (RFC-0026). Once the lifetime system lands, it becomes safe with appropriate annotation.

### OQ-3 — Recursive `@T` teardown

```metel
linear struct Node {
    value: Int,
    next: Perhaps<@Node>,
}
```

`Node` contains `Perhaps<@Node>`, which is itself linear (because `@Node` is linear). When a `Node` is destructured or goes out of scope, the `next` field must be consumed. Without guidance, the programmer must write a manual recursive traversal:

```metel
fun free_list(node: Node) {
    match node.next {
        Perhaps::Some(next) => free_list(*next),   // *next moves out of @Node and frees handle
        Perhaps::None => {},
    }
    drop(node);
}
```

The key questions:

**OQ-3a — Does `drop(p: @Node)` recursively free?**

If `@T` has a built-in `Drop` that calls `Drop::drop` on the inner `T` before freeing the allocation, and `Node` implements `Drop` to consume `next`, the teardown is automatic. The programmer implements `Drop::drop` for `Node`, which handles `next`, and calling `free(p)` or letting `p` go out of scope handles the rest.

Is `@T`'s built-in drop behaviour defined? RFC-0028 §2.3 says "If the inner type is linear, its `Drop::drop` is called before the allocation is released (if implemented)" — but this only applies if `Drop` is implemented. If `Node` does not implement `Drop` and has a linear field `Perhaps<@Node>`, the linearity checker fires on scope exit. The programmer is forced to write an explicit free function or implement `Drop`.

**OQ-3b — Is there a derived `Drop` mechanism for recursive structures?**

Could the compiler auto-derive a `Drop` for `linear struct Node` that recursively frees all linear fields? This would work for tree/list types without programmer-written traversal. The risk: it silently calls `free` on all reachable nodes without giving the programmer a hook for custom cleanup.

---

## Constraints

- `@T` is always linear — whatever write-through rule is chosen must not require cloning or branching on the handle.
- The `*T` from `@T` question interacts with RFC-0048 (region pointers) — any rule must compose with the region model.
- Recursive teardown interacts with RFC-0028 §1.9 (`Drop`). The answer here must be consistent with the Drop aspect semantics.

---

## References

- RFC-0028: `docs/internal/rfcs/6-refused/rfc-0028-memory-and-reference-model.md` — §2 (Owning Pointers), §1.8–1.9 (drop/Drop)
- RFC-0043: pointer addressability rules — incorporated into RFC-0028
- RFC-0048: region × pointer interaction — `@T` in regions depends on OQ-2
- RFC-0026: unsafe blocks (deferred) — OQ-2 Option C depends on unsafe
