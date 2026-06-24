---
id: rfc-0063
title: "Region Handles"
date: '2026-06-24'
---

> **Status — draft, design-only.** This RFC consolidates the region-related half of
> `docs/reports/memory-model/capability-region-synthesis.md` into a single normative
> proposal and adopts the **bracket parameter channel** syntax (region handles declared in
> `[...]`, value parameters in `(...)`). It depends on the reference-capability core
> (`*mut`/`*`, RFC TBD) and inherits the open interpreter-first question recorded in §11.
> Do **not** implement pending resolution of that question and of the capability-core RFC.

> **Vocabulary note.** This RFC uses `*own[r] T` as the notation for a region-allocated
> pointer (the type returned by `r.alloc()`). This is **not** a capability; see §2. The
> arena/substructural reports call the same type `*iso`; substitute freely.

## Summary

A **region** is an allocation arena with a scope. Its **handle** — an ordinary runtime value
of type `&mut Region` you can call `.alloc` on — does double duty: its *name* becomes a
**lifetime tag** carried on a pointer (`*own[region] T`), and that same tag serves as a
**static disjointness witness** for fork-join parallelism (two pointers with different tags
provably cannot alias).

Regions are the **exclusive allocation mechanism**. The two reference **capabilities** —
`*mut T` (exclusive mutable borrow) and `*T` (shared read borrow) — are orthogonal to
allocation entirely: they are temporary loans of an already-allocated value, not owners of
memory.

This RFC specifies:

1. the distinction between **region pointers** (result of allocation, affine by default)
   and **borrow capabilities** (`*mut`/`*`);
2. region tags on pointer types (`*own[r] T`) and their effect on sendability;
3. the **bracket parameter channel** — region handles and abstract region tags declared in
   `[...]`, distinct from value parameters in `(...)`;
4. two **elision/inference rules** — return-position elision and call-site **deep-threading
   inference** — that keep the common single-region case annotation-free;
5. the sendability and fork-join consequences of the tag;
6. the static-vs-runtime enforcement question that remains open.

---

## Motivation

The paused lifetime branch (RFC-0052) put a Rust-style inferred lifetime `'a` at the centre
of memory safety. Two complaints sank it: the lifetimes were phantom (nothing in scope you
could point at), and diagnostics had to explain a variable the programmer never wrote.

Region handles answer both. Every lifetime tag is the **name of an allocator object visible
in scope**, so:

- single-region checking reduces to *liveness of a named variable* — "is `region` still in
  scope here?" — which the compiler already computes, and errors name the actual region
  (`value escapes the scope of region`) instead of an abstract `'a`;
- the tag that bounds a pointer's lifetime **also** proves it cannot race, so structured
  parallelism over region data is free of any separate separation calculus.

The cost the earlier exploration kept hitting was *verbosity*: a region threaded through a
signature was named three times (binder, handle type, result tag). This RFC removes that by
merging the binder and the handle into one bracket-channel parameter and adding inference so
deep threading needs no ceremony.

---

## 1. Regions as the exclusive allocation mechanism

All memory allocation goes through region handles. There is no allocation expression that
operates outside of a region — no `new expr`, no implicit heap allocation. Every pointer
to heap-allocated data carries a region tag naming the allocator it came from.

The three allocation regions the stdlib provides:

- **`Region`** — scoped bump arena; values freed in O(1) when the region drops.
- **`Heap`** — the static global heap; values freed individually when the last owner drops.
- **`LocalHeap`** — thread-local heap; not sendable across fibers.

`Box<T>` and `Arc<T>` are thin wrappers over `Heap.alloc(T)`, not independent allocation
mechanisms. `Box::new(v)` is sugar for `Heap.alloc(v)`; `Arc::new(v)` is sugar for
`Heap.alloc(v)` plus a refcount. Their types (`Box<T>` = `*own[Heap] T`,
`Arc<Config>[Heap]`) carry the tag explicitly.

---

## 2. Region pointers and borrow capabilities

Metel has three pointer types. Only two are **capabilities**:

| type | role | sendable |
|---|---|---|
| `*own[r] T` | **region pointer** — plain affine result of `r.alloc()`; *not a capability* | yes if `[Heap]`/`[LocalHeap]`; no if `[r]` scoped |
| `*mut T` | **capability** — exclusive mutable borrow | no (always local) |
| `*T` | **capability** — shared read borrow | no (always local) |

### Region pointers are not a capability

`*own[r] T` is the type returned by `r.alloc()`. Its "owned" nature — the guarantee that
exactly one live reference to this allocation exists — comes from **affine move semantics**,
not from a named capability: the pointer is non-`Copy`, so moving it leaves no duplicate
behind. This is the same position Rust takes: owned values are the *default* state of any
non-`Copy` type; `&mut`/`&` are the capabilities layered on top.

The capabilities (`*mut`, `*`) are pure *access-mode* qualifiers on borrows. They say who
may touch a value and for how long; they say nothing about allocation or memory ownership.

### Borrowing: temporary downgrade and reconstitution

A region pointer can be **temporarily borrowed** for the duration of a call or block:

```metel
let n: *own[r] Node = r.alloc(Node { val: 1, next: null });

let v: i64 = n.val;           // shared borrow *Node — many readers, concurrent-safe
n.val = 2;                    // exclusive borrow *mut Node — one writer
// borrows expire; n is the sole live pointer again
```

The borrow checker enforces that the `*mut` borrow is exclusive (no other live borrow during
it) and that no borrow outlives its source. When all borrows expire the region pointer is
whole again, and if `[r]` is a scoped region, it recovers its non-sendable status.

### Recursive types are region-parameterised

Because regions handle all allocation, a type that contains a pointer to itself must declare
which region those pointers live in. Embedding a naked inline value would be infinite size;
a region pointer breaks the cycle:

```metel
enum List<T>[r] {
    Cons { head: T, tail: *own[r] List<T> },
    Nil {},
}

// allocation — every node goes in the same region
let list = r.alloc(List::Cons {
    head: 1,
    tail: r.alloc(List::Cons {
        head: 2,
        tail: r.alloc(List::Nil {}),
    }),
});
// list : *own[r] List<i64>
```

There is no `own expr` allocation shorthand. The region parameter on `List` is not optional
— it is the honest statement that the list's nodes live somewhere, and the caller decides
where.

### The region tag

The tag `[r]` in `*own[r] T` is the name of the allocating region handle. It is **not part
of the capability** — it is a component of the pointer *type*, naming the scope that owns
the backing memory. The tag:

- determines **sendability**: scoped `[r]` → not sendable; static `[Heap]` → sendable (§6);
- serves as a **disjointness witness** for fork-join: distinct tags → cannot alias → parallel
  for free (§7).

Borrow types (`*mut T`, `*T`) do not carry a region tag: they are already non-sendable and
non-escaping by construction, so the tag would be redundant.

> **Note on bracket syntax.** Whether the type-level tag stays `[r]` or moves to another
> delimiter (it currently reads close to array indexing) is parked — see the region-syntax
> discussion. The two are grammatically disjoint: a tag follows a pointer type (type
> context); array indexing follows a value (expression context).

---

## 3. The bracket parameter channel

A function (or struct, or closure) has up to three parameter channels, in this order:

```
fun name <type params> [region params] (value params) -> ReturnType
```

A region parameter takes one of **two forms**, distinguished by whether it carries a runtime
handle:

### 3.1 Handle form — `[region: &mut Region]`

The bracketed name is **both** the region tag **and** a borrowable runtime handle of type
`&mut Region`. Use it when the function allocates into the region. The name is in scope in
the body as an ordinary value:

```metel
fun build_node[region: &mut Region](val: i64) -> *own[region] Node {
    region.alloc(Node { val, next: null })
}
```

The region is named **once**: the abstract binder, the handle value, and the result tag all
collapse into the single `[region: &mut Region]` declaration.

### 3.2 Abstract-tag form — `[region]`

The bracketed name is a region tag with **no runtime handle**. Use it when you only need to
*name* a region — to relate input and output tags, or to tag a struct field pointing into a
region the value does not own. There is no value to `.alloc` on:

```metel
// only names a region; does not allocate into it
fun summarise[region](n: *own[region] Node) -> i64 { n.val }

// struct holding a pointer into a region it does not own
struct Parser[region] {
    input: *own[region] str,
    pos:   usize,
}
```

A struct **never** holds a `&mut Region`; it only needs the tag. The abstract form is the
handle-less degenerate case — the old `[R]` clause, now spelled with a name the reader can
point at.

### 3.3 Multiple regions and `Outlives`

Relating two regions uses both names plus a bound in the bracket channel:

```metel
fun transfer<T>[src: &mut Region, dst: &mut Region where dst: Outlives[src]](
    val: *own[src] T,
) -> *own[dst] T {
    dst.alloc(*val)
}
```

`Outlives[src]` itself names a region in brackets, keeping the notation uniform. `src` and
`dst` are handle-form here because `transfer` reads from one and allocates into the other.

---

## 4. Elision and inference

Two rules keep the common case annotation-free. Both share one principle: **a region may be
omitted only when exactly one region is in scope to fill it; two or more is a hard error
that forces an explicit name.**

### 4.1 Return-position elision

If exactly one region is in the bracket channel, a bare `*own` in the return type binds to
it:

```metel
fun build_node[region: &mut Region](val: i64) -> *own Node { … }
//                                              ^^^^^^^^ == *own[region] Node
```

With two or more regions in scope, the bare form is illegal and every result tag must be
named (`*own[dst] T` in §3.3). This is the same discipline as Rust's lifetime-elision
ambiguity rule.

`*own[region] Node` (named) remains the **idiomatic** form for readability; bare `*own Node`
is sugar legal only under single-region elision. Tools may always render the inferred tag.

### 4.2 Call-site deep-threading inference

At a call to a function that declares a region parameter, an omitted bracket argument
auto-fills from the **unique region handle in lexical scope** at the call site:

```metel
fun build_list[region: &mut Region](vals: Slice<i64>) -> *own[region] Node {
    let mut head = region.alloc(Node { val: vals[0], next: null });
    for v in vals[1..] {
        head = build_node(v);   // [region] inferred: sole handle in scope
    }
    head
}

Region::scoped(fun[region: &mut Region]() {
    let list = build_list(data);             // [region] inferred
    let list = build_list[region](data);     // explicit — always available
});
```

Rules:

1. **One** region handle in scope → omitted `[…]` resolves to it. `f(args)` ≡
   `f[that_handle](args)`.
2. **Two or more** handles in scope → bracket is required: `f[which](args)`. Omitting it is
   an error naming the candidates.
3. **None** in scope but the callee needs one → the usual "no region available" error;
   establish a `Region::scoped` or pass `Heap` explicitly.

The resolution is always a single named handle the compiler can surface in diagnostics and
hovers. The explicit `f[region](args)` form is preferred wherever more than one region is
nearby or where making the allocation context visible aids the reader.

> **Scope of inference.** Deep-threading inference fills *region* arguments only — the
> region analogue of type-argument inference. Generalising `[…]` to arbitrary context
> parameters is explicitly out of scope for this RFC.

---

## 5. What the programmer actually writes

Most code sees no region annotations. The tag is inferred from the allocation site
(`r.alloc(..)` → `*own[r] T`), exactly as a type is inferred from a constructor:

```metel
fun main() {
    let b = Heap.alloc(Counter { value: 0 });  // *own[Heap] Counter
    let a = Heap.alloc(Config { workers: 4 }); // *own[Heap] Config — Arc::new sugar
    Region::scoped(fun[region: &mut Region]() {
        let n = region.alloc(Node { val: 1 }); // *own[region] Node
        process(n) || work_elsewhere();        // disjoint tags → parallel for free
    });                                        // region drops; n freed in O(1)
}
```

Region tags surface explicitly only in three places:

1. **functions that allocate into a caller-supplied region** — handle form
   `[region: &mut Region]` (§3.1);
2. **region-polymorphic / multi-region library code** — the multi-name bracket channel with
   `Outlives` bounds (§3.3);
3. **types holding a pointer into a region they do not own** — abstract-tag form
   `struct Parser[region] { … }` (§3.2), including all recursive types.

---

## 6. Sendability and concurrency

The region tag decides what crosses a fiber boundary:

```
fiber boundary  :  *own[Heap] T  /  Arc<T>  /  Chan endpoint   — sendable
                   *own[region] T                               — REJECTED (scope-bound)
```

A region pointer is sendable iff its tag is static (`[Heap]`, `[LocalHeap]`) or absent. A
scoped `[region]` tag makes the pointer non-sendable by construction — a fiber may outlive
the region, so it can never hold a pointer into one. No `RegionFree`/`Send` approximations
are needed; the tag is the check.

---

## 7. The tag as a disjointness witness (fork-join)

Because scoped region pointers are non-sendable, `spawn` alone cannot parallelise over them
— you would first have to copy to `Heap` or wrap in `Arc`, defeating the region.
**Structured fork-join is the one construct that escapes this**, because it is structured:
`||` guarantees both sides finish before the expression returns, *inside* the region's
scope, so handing each side a borrow into the region is sound — the borrow cannot outlive
the join.

```metel
Region::scoped(fun[region: &mut Region]() {
    let t = build(…);                            // *own[region] Node — non-sendable
    let (ls, rs) = sum(&t.left) || sum(&t.right); // borrows into region, in parallel
});                                              // both halves finished before drop
```

Safety needs **no separation calculus**: two distinct tags ⇒ provably disjoint memory
(`[r1] ∩ [r2] = ∅`), and `*mut` is already exclusive, so two parallel branches are safe iff
each independently type-checks against the ordinary rules. `||` is a sealed library
combinator (`join<A,B>(a, b) -> (A, B)` with `e₁ || e₂` as sugar); the tag **is** the
proof.

---

## 8. Diagnostics

Single-region checking reduces to liveness of a named variable. Errors name the real region:

```
error: value escapes the scope of `region`
  --> ...
   |  the value is allocated in `region`, which is dropped here
```

instead of explaining an abstract `'a` the programmer never wrote. This dissolves the
diagnostic problem the paused branch most feared, for the common case.

The hard case is unchanged: when regions arrive from outside (`transfer`, `Outlives`,
multi-region structs), the constraint machinery is the old `<'a, 'b: 'a>` story under a new
spelling — escape analysis is escape analysis. The *frequency* of hitting that path drops
significantly; its *difficulty* does not.

---

## 9. The one-sentence identity

> *A memory model where every lifetime annotation is the name of a real allocator object you
> can see in scope, the same annotation that bounds a pointer's lifetime also proves it
> cannot race, and the allocator behind it is an ordinary, swappable library value.*

Three things no incumbent offers together: lifetime tags that are real objects (not Rust's
phantom `'a`), tags reused as fork-join disjointness witnesses (neither Rust nor Pony nor
Vale does this), and Zig-style swappable allocators carrying a *static* lifetime (Zig has
the allocators but no static safety).

---

## 10. Worked signatures (reference)

```metel
// 1. single-region allocator — return tag written explicitly
fun build_node[region: &mut Region](val: i64) -> *own[region] Node {
    region.alloc(Node { val, next: null })
}
let n = build_node[r](42);     // n : *own[r] Node

// 2. two-region transfer — naming mandatory
fun transfer<T>[src: &mut Region, dst: &mut Region where dst: Outlives[src]](
    val: *own[src] T,
) -> *own[dst] T { dst.alloc(*val) }
let moved = transfer[a, b](node);

// 3. struct holding a region pointer — abstract-tag form, no handle
struct Parser[region] { input: *own[region] str, pos: usize }
fun parse[region: &mut Region](src: *own[region] str) -> *own[region] Parser {
    region.alloc(Parser { input: src, pos: 0 })
}

// 4. recursive type — region parameter required
enum List<T>[r] {
    Cons { head: T, tail: *own[r] List<T> },
    Nil {},
}
fun build_list[region: &mut Region](vals: Slice<i64>) -> *own[region] List<i64> {
    let mut acc = region.alloc(List::Nil {});
    for v in vals.rev() {
        acc = region.alloc(List::Cons { head: v, tail: acc });
    }
    acc
}

// 5. deep threading — inference fills the in-scope handle
fun build_node[region: &mut Region](val: i64) -> *own[region] Node {
    region.alloc(Node { val, next: null })
}
fun build_chain[region: &mut Region](vals: Slice<i64>) -> *own[region] Node {
    let mut head = region.alloc(Node { val: vals[0], next: null });
    for v in vals[1..] { head = build_node(v); }  // [region] inferred
    head
}
```

---

## 11. Unresolved questions

1. **Static vs runtime enforcement of the tag (the decisive open item).** The region tag is
   a compile-time escape analysis, which re-commits to the static direction the
   interpreter-first reconsideration argued against. The intended resolution is to make the
   tag **runtime-enforced in the interpreter** (a region-generation check) that a future
   compiler **elides** where escape analysis proves it safe — turning the one re-incurred
   concern into the capabilities↔generational-references bridge. This must be settled before
   implementation.

2. **Bracket delimiter for type-level tags.** `*own[r] T` reads close to array indexing.
   Parked; tracked in the region-syntax discussion. Does not affect the parameter-channel
   design of §3–4.

3. **`Outlives` bound syntax in the bracket channel.** `[dst: &mut Region where dst:
   Outlives[src]]` is proposed; an inline form (`[src, dst: Outlives[src]]`) may read better
   and needs a decision.

4. **Closures and `fun[region: &mut Region]()`.** The `Region::scoped` callback uses the
   bracket channel on a closure literal; the exact grammar for region parameters on closure
   types and values is left to the closure RFC (RFC-0050).

---

## References

- `docs/reports/memory-model/capability-region-synthesis.md` — source synthesis (§1–10).
- `docs/reports/memory-model/arena-handles-as-lifetime-annotations.md` — the region layer in
  full, including the original `[R]` clause this RFC supersedes.
- `docs/reports/memory-model/substructural-and-separation-types.md` — the capability core.
- RFC-0052 (Lifetime System, on hold) — the phantom-lifetime approach this supersedes.
- RFC-0050 (Closure Capture Lists), RFC-0049 (Linear `fun` Type System) — adjacent.
