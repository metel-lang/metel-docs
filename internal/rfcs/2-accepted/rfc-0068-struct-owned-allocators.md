---
id: rfc-0068
title: "Struct-Owned Allocators"
date: '2026-06-28'
updated: '2026-07-10'
status: accepted
---

> **Status — under review.** Rewritten 2026-07-05. The original RFC used `[own r]` in
> the bracket channel. Under the split model the bracket channel is gone; struct allocator
> ownership is expressed via **primary constructor syntax**: `struct Foo(@a: BumpAlloc)`.
> The allocator parameter `a` is declared in the value channel `()` with the `@` prefix;
> it is created at construction and freed at drop. The `own` keyword is dropped. Depends
> on RFC-0063 (Allocator Handles), RFC-0065 (Allocator Ergonomics), RFC-0067 (Lifetime
> Anchors and Allocator-Pointer References). Introduces struct-owned allocators.
>
> **Corrected 2026-07-10, ratification pass:** the RFC-0067 cross-reference above still
> said "(Reference Types)" — RFC-0067's own title after the 2026-07-07 split is "Lifetime
> Anchors and Allocator-Pointer References"; "Reference Types" is RFC-0067a. This RFC's
> own References section already used the correct title; only this blockquote was stale.
> File renamed from `rfc-0068-struct-owned-regions.md` to
> `rfc-0068-struct-owned-allocators.md` to match the title, for the same reason as
> RFC-0066's rename.

> **Status — accepted (2026-07-10).** Phase 0 ratification sweep: split model consistency-checked (RFC-0063 sec9 items 1/2/5 synced with roadmap-2026-07-07 Phase 0 decision; RFC-0066/0068 stale titles fixed); sweeping the cluster from under-review to accepted per reports/implementation/roadmap-2026-07-07.md Phase 0.

## Summary

RFC-0063 establishes two allocator relationships: a function receives an allocator as a
value parameter and allocates into it; or a scope owns an allocator locally. Both treat
the allocator as externally supplied.

This RFC adds a third form: a struct may declare an **owned allocator** in its primary
constructor. The allocator is created when the struct is constructed and freed when the
struct is dropped. Within the struct's `impl` blocks, the allocator name is in scope and
may be used to allocate into the struct's arena and to tag borrows.

---

## Motivation

The existing forms do not provide a way to tie an allocator's lifetime to a struct's
lifetime. The two natural workarounds both have friction:

**`BumpAlloc::scoped` around the struct.** The struct must be contained within the
closure; nothing allocated in the scoped allocator can escape. This inverts ownership —
the scope owns the struct rather than the struct owning its arena.

**Passing the allocator as a parameter.** The allocator is threaded in from the call
site. The struct cannot allocate in its own arena from methods that do not receive the
handle, and the caller manages the allocator's lifetime separately from the struct's.

The canonical motivating pattern is any structure that builds up arena-allocated data
incrementally — a parser constructing an AST, a query planner building a plan graph. In
all of these the allocator's natural lifetime is the object's lifetime.

---

## 1. Declaration — primary constructor syntax

An owned allocator is declared by including an `@`-prefixed parameter in the struct's
primary constructor position:

```metel
struct Parser(@a: BumpAlloc) {
    source: String,
    nodes:  @a List<AstNode>,
}
```

`(@a: BumpAlloc)` declares that `Parser` owns an allocator of type `BumpAlloc` named
`a`. The name `a` is available within the struct's `impl` blocks as both the runtime
allocator handle and the compile-time tag appearing in field types (`@a List<AstNode>`).

The owned allocator does not appear in `Parser`'s external type — from the call site,
the type is just `Parser`. The allocator is a private implementation detail of the
struct.

A struct may declare at most one owned allocator.

---

## 2. Construction and drop

Construction creates the arena implicitly. No explicit allocator handle is passed by
the caller:

```metel
let parser = Parser::new(source);
```

The allocator is created as part of the `Parser` value. The compiler synthesises the
construction (a call to `BumpAlloc::new()`) and the destruction (drop of the allocator
after the struct's fields are dropped).

**Drop order.** Fields are dropped first in declaration order; the owned allocator is
freed after all fields are dropped. This ensures that any `@a T` pointers stored as
fields are unreachable before the bulk free occurs. The borrow checker rejects any live
`&r T` borrow into the struct's allocator at the point the struct is dropped.

---

## 3. Implicit scope in `impl` blocks

Inside any `impl Parser` block, `a` is implicitly in scope as the allocator binding.
Methods may use `@a` to allocate and `&r T` anchored to method parameters:

```metel
extend Parser {
    fun new(source: String) -> Parser {
        Parser { source, nodes: @a List::Nil {} }
        //                      ^^ a in scope; allocates into the new arena
    }

    fun push_node(&mut self, node: AstNode) -> &self AstNode {
        let ptr = @a node;   // allocate into Parser's arena
        self.nodes = @a List::Cons { head: ptr, tail: self.nodes };
        &ptr
    }

    fun root(&self) -> &self AstNode {
        &self.nodes.head   // borrow into Parser's arena; valid for self's lifetime
    }
}
```

`a` is never written in the impl block header — it is always implicit for structs that
declare `(@a: AllocType)`.

---

## 4. Two lifetimes in method signatures

Every method on a struct with an owned allocator has access to two distinct lifetimes:

- **The struct's own lifetime** — the allocator `a` lives exactly as long as the struct.
  Borrows anchored to `self` in return position (`&self T`) are valid for the struct's
  entire lifetime, not just for the duration of any particular borrow of it.
- **The borrow duration** — how long a particular borrow of the struct (`&self Parser`)
  is held. This is tracked by the borrow checker from the calling scope; it need not be
  named unless it appears in the return type.

```metel
fun root(&self) -> &self AstNode { ... }
// &self AstNode: valid for the struct's own lifetime (RFC-0067 §1 — `self` is the anchor)
// The borrow of Parser used to call `root` may expire; the returned ref stays valid
// as long as `parser` (the binding) is alive.
```

This mirrors Rust's two-lifetime method pattern (`&'this self` vs `'arena`).

---

## 5. Allocation requires exclusive access

`@a expr` inside a method requires `&mut self`, since allocation mutates the arena:

```metel
fun push(&mut self, node: AstNode) -> &self AstNode { ... }   // ✓
fun peek(&self) -> &self AstNode { ... }                       // ✓ — read-only
fun push_shared(&self, node: AstNode) -> &self AstNode { ... } // ✗ — cannot allocate through shared borrow
```

Methods with shared `&self` may read and borrow from the arena but may not allocate
into it.

---

## 6. Interaction with allocator ergonomics (RFC-0065)

When a method has only the implicit allocator `a` in scope and no other allocator, the
elision rule from RFC-0065 applies: bare `@` elides to `@a`.

```metel
extend Parser {
    fun init(&mut self) {
        self.nodes = @List::Nil {};   // elides to @a List::Nil {}
    }
}
```

---

## 7. Unresolved questions

1. **Multiple owned allocators.** Whether `struct Foo(@a: BumpAlloc, @b: BumpAlloc)` —
   two owned arenas — should be permitted is deferred until a concrete use case
   establishes the need. The straightforward reading is coherent; the added complexity
   is not yet justified.

2. **Allocator type flexibility.** The primary constructor syntax binds the allocator
   type statically at declaration time (`BumpAlloc` in the example). Whether the struct
   should be parameterizable over the allocator type — `struct Foo<A: Alloc>(@a: A)` —
   is deferred.

---

## References

- RFC-0063 (Allocator Handles) — allocator values; `@a expr`; sendability.
- RFC-0065 (Allocator Ergonomics) — `@`-elision; two-or-more allocator discipline.
- RFC-0067 (Lifetime Anchors) — `&r T` / `&r mut T`; `&self` denotation in return types.
