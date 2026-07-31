---
title: "Metel Memory Model — Overview"
date: '2026-06-28'
rfcs: [0063, 0064, 0065, 0066, 0067, 0068, 0069, 0071]
---

> **Status — current.** This report describes the memory model as specified by the
> RFC-006x cluster (accepted) and RFC-0071 (integrated 2026-07-24, target v0.12.0). It supersedes all prior memory-model
> exploration documents. Refer to the individual RFCs for normative detail; this report
> gives the unified narrative and worked examples.

## Design philosophy

Metel's memory model rests on one principle: **every lifetime annotation is the name of a
real allocator object visible in scope.** There are no phantom lifetime parameters, no
abstract `'a` the programmer never wrote. When the compiler says "value escapes the scope
of `region`," it is naming the actual variable.

Three properties follow from this choice and no incumbent language offers all three together:

1. **Lifetime tags are real objects.** Errors name them; diagnostics point at them; the
   programmer can call methods on them.
2. **The same tag that bounds a pointer's lifetime proves it cannot race.** Two pointers
   with distinct region tags provably cannot alias — no separation calculus needed.
3. **Allocators are swappable library values.** The region behind any `@[r] T` is an
   ordinary value implementing a runtime interface. Different arenas (bump, pool, GC stub)
   plug into the same type system position.

---

## 1. Region kinds

All memory allocation goes through a region. There is no allocation expression outside of
one. A region is any value implementing the region allocator interface — an ordinary runtime
contract for allocation and drop. The interface requires one associated type: `AllocationError`,
the error type an allocation may produce. Assigning `!` declares the region infallible (OOM
panics; no error handling required). Fallible regions assign a concrete error type and
allocation expressions at those sites return `Result<@[r] T, AllocationError>`. The system
is open: pool allocators, slab allocators, stack arenas, and other custom types all qualify.
The four stdlib regions cover the common cases and are all infallible (`AllocationError = !`):

| Region | Lifetime | Move-out | Sendable |
|---|---|---|---|
| `Heap` | Indefinite | Always safe | Yes |
| `LocalHeap` | Indefinite, thread-local | Always safe | No |
| `BumpRegion` | Scoped, bump arena | `T: !Drop` only | No |
| `AutoRegion` | Scoped, bump arena + drop list | Always safe | No |

### 1.1 Heap

`Heap` is the global heap. Values allocated into `Heap` are freed individually when their
last owner is dropped. `@[Heap] T` is sendable across fibers.

```metel
use Heap;
let s = @[Heap] String { bytes: "hello" };  // heap-allocated, sendable
```

`Box<T>` is retired — `@[Heap] T` is self-documenting and does the same job directly.

`Arc<T>` remains, but as `Arc<T>[Heap]`: shared ownership with atomic refcount, sendable.
`Arc<T>[LocalHeap]` is the non-atomic counterpart, not sendable — no separate `Rc` type
is needed because the region tag already encodes thread-locality.

### 1.2 LocalHeap

`LocalHeap` is a thread-local heap. Values allocated into it are individually freed, but
the tag is non-sendable — the allocator is tied to the creating thread.

```metel
use LocalHeap;
let cache = @[LocalHeap] HashMap::new();  // thread-local, not sendable
```

### 1.3 Scoped regions — `BumpRegion`, `AutoRegion`, and custom allocators

`BumpRegion` is the stdlib scoped bump arena: O(1) allocation and O(1) bulk-free when the
region drops. Move-out requires `T: !Drop`. Pointers tagged with a scoped region are **not
sendable** — a fiber may outlive the region.

`AutoRegion` is the stdlib scoped region with a drop list: move-out is always safe because
the allocator tracks live slots with `Drop` implementations and calls their destructors
before reclaiming memory. When all allocations are `T: !Drop`, `AutoRegion` behaves
identically to `BumpRegion`.

`BumpRegion` and `AutoRegion` are two implementations of the region interface. A custom
scoped allocator — a pool, a slab, a stack arena — may be used in the same bracket channel
position and carries the same lifetime and sendability rules: the tag is non-sendable, and
the allocator's own drop governs when memory is reclaimed.

A scoped region can be created in two ways:

**Closure-scoped** — `BumpRegion::scoped` delimits the region's lifetime with a closure
boundary. Nothing carrying the tag may escape:

```metel
BumpRegion::scoped([r]() -> {
    let node = @[r] Node { val: 1, next: null };
    process(&node);
    // r freed here; node is gone
});
```

**Variable-scoped** — `let r = BumpRegion::new()` binds the arena to a variable. The binding
name `r` is the type-level tag. The arena is freed when `r` is dropped — explicitly via
`drop(r)` or implicitly at the end of its scope. This form is more flexible: the region
can span multiple function calls and be dropped early:

```metel
let r = BumpRegion::new();
let list = build_list[r](data);   // [r] threaded explicitly
process(&list);
drop(r);                          // arena freed here; list is invalid from this point
```

`BumpRegion::scoped` is equivalent to a block with an implicit drop:

```metel
BumpRegion::scoped([r]() -> { body });
// ≡
{ let r = BumpRegion::new(); body }
```

The closure form is preferred when the arena scope aligns with a single block; the `let`
form when the lifetime spans multiple statements or needs early release.

---

## 2. Pointer and reference types

Metel has three pointer/reference types with distinct roles:

| Type | Role | Affine | Sendable |
|---|---|---|---|
| `@[r] T` | Region pointer — owned allocation | yes | if `[Heap]`/`[LocalHeap]` |
| `&T` | Shared reference — non-exclusive borrow | no | no |
| `&mut T` | Exclusive reference — mutable borrow | no | no |

### 2.1 Region pointers `@[r] T`

`@[r] T` is the result of allocating `T` into region `r`. It is affine (non-`Copy` by
default), so moving it leaves no duplicate behind. The tag `[r]` names the arena and
determines sendability and disjointness.

Affine ownership is specified in RFC-0071: values move by default; `Copy` is opt-in and
mutually exclusive with `Drop`; exactly one live owner exists at all times. Region pointers
are non-`Copy` by construction — this is what makes region lifetime and disjointness
guarantees sound.

References (`&T`, `&mut T`) are orthogonal to allocation: they are temporary loans of an
already-allocated value, not owners of memory.

### 2.2 Reference types `&T` and `&mut T`

`&T` allows any number of simultaneous shared readers. `&mut T` is exclusive — no other
reference to the same location may be live while it exists. `&mut T` coerces to `&T`.
There is no explicit dereference operator; all value access is through auto-deref (§5).

### 2.3 Region-tagged borrows `&[r] T`

When a region pointer is borrowed in a function signature, the double-sigil `& @[r] T` is
noisy. `&[r] T` is accepted shorthand for `& @[r] T` — a shared borrow of a value in
region `r`. Similarly `&mut [r] T` for exclusive borrows.

`&[r] T` coerces to plain `&T` where the region tag is not needed. In signatures, `&[r]
T` names the region for lifetime tracking; `&T` is what callers that don't need the tag
observe after coercion.

A bare `&T` in a signature always means a plain borrow with no region tag — it **never**
silently expands to `&[r] T`.

---

## 3. Allocation

### 3.1 The allocation expression

`@[r] expr` is the allocation expression. It is a language primitive — not a method call —
that the compiler lowers to a call through the runtime handle. The bracket `[r]` names both
the compile-time tag and the runtime arena.

The return type depends on the region's `AllocationError` associated type:

- **Infallible** (`r::AllocationError = !`): type is `@[r] T`. OOM panics; no error handling
  required. All four stdlib regions are infallible.
- **Fallible** (`r::AllocationError = E`): type is `Result<@[r] T, E>`. Callers propagate
  with `?` or handle explicitly.

```metel
// infallible (BumpRegion, AutoRegion, Heap, LocalHeap) — type is @[r] Node
let node = @[r] Node { val: 1, next: null };

// fallible custom arena — type is Result<@[pool] Node, AllocationFailed>
let node = @[pool] Node { val: 1, next: null }?;
```

### 3.2 Type-directed allocation

When a `let` binding declares type `@[r] T`, the right-hand side may be a bare `T`
expression — the declared type drives allocation:

```metel
let node: @[r] Node = Node { val = 1, next = null };  // equivalent to @[r] Node { … }
```

This eliminates redundant repetition of `@[r]` when the type annotation is already present.

### 3.3 The bracket parameter channel

Functions and structs declare region parameters in a dedicated `[…]` channel, separate from
value parameters `(…)`:

```metel
fun build_node[region](val: i64) -> @[region] Node {
    @[region] Node { val, next: null }
}
```

The same name serves as binder, runtime handle, and result tag simultaneously. The handle
is accessible for other region operations (`r.free(ptr)`, `r.reset()`, etc.) while
`@[region] expr` remains the idiomatic allocation form.

Multiple regions and `Outlives` bounds:

```metel
fun transfer<T>[src, dst: Outlives<src>](val: @[src] T) -> @[dst] T {
    @[dst] val
}
```

`[dst: Outlives<src>]` reads "`dst` outlives `src`" — the destination region lives longer
than the source.

---

## 4. Region ergonomics

The explicit form is always available. Two rules make the common single-region case
annotation-free (RFC-0065).

### 4.1 `@`-position elision

When exactly one region is in scope, bare `@` in type or expression position elides the
tag:

```metel
// explicit
fun parse[region](line: String) -> @[region] Header { @[region] Header { … } }

// with elision
fun parse[region](line: String) -> @Header { @Header { … } }
```

With two or more regions in scope, all tags must be named — the elision rule never applies.

### 4.2 Call-site inference

An omitted bracket argument at a call site auto-fills from the unique region handle in
lexical scope:

```metel
BumpRegion::scoped([r]() -> {
    let node = build_node(42);      // [r] inferred
    let node = build_node[r](42);   // explicit — always valid
});
```

Two or more candidates → explicit bracket required; the error names all candidates.

### 4.3 `Heap` and `LocalHeap` import model

`Heap` and `LocalHeap` are always accessible by name — `@[Heap] T` works anywhere. They
enter the **inference candidate set** only when explicitly imported:

```metel
use Heap;
```

This gives three clean scenarios:

```metel
// 1. Heap imported, no arena — Heap is the sole candidate
use Heap;
let cfg = @Config { workers: 4 };   // infers [Heap]

// 2. No import, inside arena — arena is the sole candidate
BumpRegion::scoped([r]() -> {
    let node = make_node(1);        // infers [r]
});

// 3. Both imported and arena in scope — explicit required
use Heap;
BumpRegion::scoped([r]() -> {
    let node = make_node[r](1);     // explicit
    let cfg  = make_node[Heap](1);  // explicit — visible heap escape
});
```

---

## 5. Extracting values from region pointers

Given `ptr: @[r] T`, two families of extraction are available (RFC-0066, RFC-0067).

### 5.1 Borrow-deref

Obtain a temporary loan without consuming the pointer. Unconditional — any region kind,
any `T`. Auto-deref handles most cases:

```metel
let node = @[r] Node { val: 1, next: null };
let v = node.val;          // auto-deref: @[r] Node → Node, read field
node.val = 2;              // auto-deref for write
node.process(args);        // auto-deref for method dispatch

let b: &Node     = &node;      // explicit shared borrow — &[r] Node, coerces to &Node
let m: &mut Node = &mut node;  // explicit exclusive borrow
```

There is no explicit dereference operator in safe code. Auto-deref applies in field access,
method dispatch, and deref coercions.

### 5.2 Move-out

Move-out consumes `ptr` and returns `T`. Safety depends on the region kind.

**`@[Heap] T`** — always safe. The heap tracks allocations individually; the slot is freed
without calling `T::drop` again.

**Non-heap `@[r] T`** — constrained by `T`'s Drop status when the allocator uses bulk
deallocation. Bulk-deallocating allocators (e.g. `BumpRegion`) reclaim all slots at once when
the region drops; a vacated slot is orphaned and the allocator cannot skip destructor calls
it does not individually track.

| T | Non-heap move-out |
|---|---|
| `T: Copy` | copies out; slot intact; `ptr` remains valid |
| `T: !Drop` | moves out; slot orphaned; safe (no destructor to double-call) |
| `T: Drop` | compile error (Option A, recommended); avoids double-drop hazard |

**Type-directed move-out** — when a `let` binding declares type `T` and the source is
`@[r] T`, move-out is implicit:

```metel
let ptr = @[r] Node { val: 1, next: null };
let node: Node = ptr;   // move-out; same constraints as explicit form
```

**Type ascription** — for explicit move-out in any expression position:

```metel
let node = ptr: Node;    // ascription drives move-out
process(ptr: Node);      // move-out at call site
```

### 5.3 Clone extraction

When move-out from a scoped arena is unavailable (`T: Drop`, Option A), clone into a
target region. Auto-deref dispatches `clone()` through `@[r] T` to `T::clone`:

```metel
let copy: @[Heap] Config = src.clone();   // auto-deref; clone into Heap
```

---

## 6. Struct-owned regions

A struct may declare an **owned region** `[own r]` — an arena whose lifetime equals the
struct's (RFC-0068):

```metel
struct Parser[own r] {
    source: String,
    nodes:  @[r] List<AstNode>,
}
```

`r` is internal — the external type is just `Parser`, not `Parser[r]`. The compiler
desugars `[own r]` to `BumpRegion::new()` in the constructor and a drop of the arena in the
struct's destructor.

Within `impl Parser`, `r` is implicitly in scope. Methods have access to two distinct
lifetimes:

- **`r`** — the struct's own lifetime (the arena).
- **`s`** — the duration of a particular borrow of the struct, introduced per-method.

```metel
impl Parser {
    // s = borrow duration; r = Parser's lifetime (implicit, always in scope)
    fun push[s](self: &mut [s] Parser, node: AstNode) -> &[r] AstNode {
        let ptr = @[r] node;   // allocation requires &mut self
        &ptr                   // valid for r, not just s
    }

    fun root[s](self: &[s] Parser) -> &[r] AstNode {
        &self.nodes.head       // borrow into Parser's arena
    }
}
```

Allocation into the owned region requires `&mut self`; shared `&[s] self` can read but not
allocate.

---

## 7. Sub-region typing

When a struct with `[own r]` is itself allocated into an existing region `R`, the compiler
types `r` as `SubRegion<R>` (RFC-0069). `SubRegion<R>` carries the constraint `R:
Outlives<r>` automatically — no annotation needed at the call site:

```metel
BumpRegion::scoped([outer]() -> {
    let parser = @[outer] Parser::new(src);
    // parser's owned region r : SubRegion<outer>
    // outer: Outlives<r>  — automatic

    let node: &[r] AstNode = parser.root();
    // borrow checker knows r is bounded by outer
});
```

Nesting composes via `Outlives` transitivity: if `r: SubRegion<outer>` and a sub-parser's
arena is `s: SubRegion<r>`, then `outer: Outlives<s>` is derived for free.

---

## 8. Sendability

The region tag is the complete sendability rule:

| Tag | Sendable |
|---|---|
| `[Heap]` | yes — global heap, fiber-safe |
| `[LocalHeap]` | no — thread-local |
| scoped `[r]` | no — arena may be freed before the fiber terminates |

A value is sendable iff its tag is `[Heap]`. The same rule distinguishes `Arc<T>[Heap]`
(atomic refcount, sendable) from `Arc<T>[LocalHeap]` (non-atomic, not sendable) — one
type, two behaviors, no separate `Rc`.

---

## 9. Disjointness and parallelism

Two pointers with distinct region tags name distinct arenas and therefore cannot alias.
This is a compile-time fact, not a runtime check. It is the foundation on which structured
parallelism over region data can be built: a parallel combinator that keeps both branches
inside the region's scope would be race-free purely from the borrow checker's ordinary
`&mut` exclusivity rule, with no separation calculus required.

The `||` structured fork-join combinator that exploits this property is specified in
RFC-0064, which is **deferred** until the core region cluster stabilises.

---

## 10. Worked example — HTTP request parser

```metel
struct Request[own r] {
    method:  &[r] String,
    path:    &[r] String,
    headers: @[r] List<Header>,
}

impl Request {
    fun parse[s](self: &mut [s] Request, raw: String) {
        let parts = raw.split(" ");
        self.method  = @[r] parts[0];
        self.path    = @[r] parts[1];
        self.headers = @[r] List::Nil {};
    }

    fun add_header[s](self: &mut [s] Request, line: String) {
        let h = @[r] Header::parse(line);   // allocated into Request's arena
        self.headers = @[r] List::Cons { head: h, tail: self.headers };
    }

    fun find_header[s](self: &[s] Request, name: &str) -> Perhaps<&[r] String> {
        // returns borrow valid for Request's lifetime, not just this call
        find_in_list(&self.headers, name).map(|h| &h.value)
    }
}

fun handle(raw: String) -> Response {
    let mut req = Request::new();
    req.parse(raw);
    // req's arena (r) is automatically SubRegion of nothing here —
    // r lives as long as req lives on the stack

    let content_type = req.find_header("Content-Type");
    route(req, content_type)
    // req dropped here; r freed; all &[r] borrows invalid past this point
}
```

Key points visible in the example:
- `r` never appears at the call site — it is internal to `Request`
- `&[r] String` returned from `find_header` is valid for as long as `req` is alive
- The arena is freed when `req` drops — no explicit cleanup
- No `Heap` import needed for request-scoped data; inference finds `r` automatically

---

## RFC index

| RFC | Title | Status |
|---|---|---|
| RFC-0063 | Region Handles | accepted |
| RFC-0064 | Structured Fork-Join Parallelism | deferred |
| RFC-0065 | Region Ergonomics | accepted |
| RFC-0066 | Region Pointer Extraction | accepted |
| RFC-0067 | Reference Types | accepted |
| RFC-0068 | Struct-Owned Regions | accepted |
| RFC-0069 | Sub-Region Typing | accepted |
| RFC-0071 | Ownership and Move Semantics | accepted |
