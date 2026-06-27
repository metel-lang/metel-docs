---
id: rfc-0063
title: "Region Handles"
date: '2026-06-24'
---

> **Status — draft, design-only.** This RFC consolidates the region-related half of
> `docs/reports/memory-model/capability-region-synthesis.md` into a single normative
> proposal and adopts the **bracket parameter channel** syntax (region handles declared in
> `[...]`, value parameters in `(...)`). It depends on the reference-capability core
> (`&mut`/`&`, RFC TBD) and inherits the open interpreter-first question recorded in §11.
> Do **not** implement pending resolution of that question and of the capability-core RFC.

> **Vocabulary note.** This RFC uses `@[r] T` as the notation for a region-allocated
> pointer (the type returned by `r.alloc()`). This is **not** a capability; see §2. The
> arena/substructural reports call the same type `*iso`; substitute freely.

## Summary

A **region** is an allocation arena with a scope. Its **handle** — an ordinary runtime value
of type `&mut Region` you can call `.alloc` on — does double duty: its *name* becomes a
**lifetime tag** carried on a pointer (`@[region] T`), and that same tag serves as a
**static disjointness witness** (two pointers with different tags provably cannot alias —
see RFC-0064 for the fork-join application).

Regions are the **exclusive allocation mechanism**. The two reference **capabilities** —
`&mut T` (exclusive mutable borrow) and `&T` (shared read borrow) — are orthogonal to
allocation entirely: they are temporary loans of an already-allocated value, not owners of
memory.

This RFC specifies:

1. the distinction between **region pointers** (result of allocation, affine by default)
   and **borrow capabilities** (`&mut`/`&`);
2. region tags on pointer types (`@[r] T`) and their effect on sendability;
3. the **bracket parameter channel** — region handles and abstract region tags declared in
   `[...]`, distinct from value parameters in `(...)`;
4. two **elision/inference rules** — return-position elision and call-site **deep-threading
   inference** — that keep the common single-region case annotation-free;
5. the sendability consequences of the tag;
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
merging all three into a single bare name in the bracket channel and adding inference so
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

`Arc<T>` is the one stdlib wrapper that adds semantics beyond the region tag: shared
ownership via refcount. It is region-polymorphic — `Arc::new` infers the region from
context (§4.2) — and its sendability follows from the tag:

- `Arc<T>[Heap]` — atomic refcount, sendable across fibers.
- `Arc<T>[LocalHeap]` — non-atomic refcount, not sendable; the tag already guarantees
  single-thread access, so the cheaper implementation is sound.

The second form subsumes `Rc<T>` from the Rust model: the non-sendability that justified
a separate `Rc` type is already encoded in `[LocalHeap]`, so no additional type is needed.
`Box<T>` is **retired** — `@[Heap] T` is self-documenting and direct heap allocation is
written `Heap.alloc(v)` with no sugar needed.

---

## 2. Region pointers and borrow capabilities

Metel has three pointer types. Only two are **capabilities**:

| type | role | sendable |
|---|---|---|
| `@[r] T` | **region pointer** — plain affine result of `r.alloc()`; *not a capability* | yes if `[Heap]`/`[LocalHeap]`; no if `[r]` scoped |
| `&mut T` | **capability** — exclusive mutable borrow | no (always local) |
| `&T` | **capability** — shared read borrow | no (always local) |

### Region pointers are not a capability

`@[r] T` is the type returned by `r.alloc()`. Its "owned" nature — the guarantee that
exactly one live reference to this allocation exists — comes from **affine move semantics**,
not from a named capability: the pointer is non-`Copy`, so moving it leaves no duplicate
behind. This is the same position Rust takes: owned values are the *default* state of any
non-`Copy` type; `&mut`/`&` are the capabilities layered on top.

The capabilities (`&mut`, `&`) are pure *access-mode* qualifiers on borrows. They say who
may touch a value and for how long; they say nothing about allocation or memory ownership.

### Borrowing: temporary downgrade and reconstitution

A region pointer can be **temporarily borrowed** for the duration of a call or block:

```metel
let n: @[r] Node = r.alloc(Node { val: 1, next: null });

let v: i64 = n.val;           // shared borrow &Node — many readers, concurrent-safe
n.val = 2;                    // exclusive borrow &mut Node — one writer
// borrows expire; n is the sole live pointer again
```

The borrow checker enforces that the `&mut` borrow is exclusive (no other live borrow during
it) and that no borrow outlives its source. When all borrows expire the region pointer is
whole again, and if `[r]` is a scoped region, it recovers its non-sendable status.

### Recursive types are region-parameterised

Because regions handle all allocation, a type that contains a pointer to itself must declare
which region those pointers live in. Embedding a naked inline value would be infinite size;
a region pointer breaks the cycle:

```metel
enum List<T>[r] {
    Cons { head: T, tail: @[r] List<T> },
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
// list : @[r] List<i64>
```

There is no `own expr` allocation shorthand. The region parameter on `List` is not optional
— it is the honest statement that the list's nodes live somewhere, and the caller decides
where.

### The region tag

The tag `[r]` in `@[r] T` is the name of the allocating region handle. It is **not part
of the capability** — it is a component of the pointer *type*, naming the scope that owns
the backing memory. The tag:

- determines **sendability**: scoped `[r]` → not sendable; static `[Heap]` → sendable (§6);
- serves as a **disjointness witness**: distinct tags → cannot alias (RFC-0064 builds
  structured fork-join on top of this property).

Borrow types (`&mut T`, `&T`) do not carry a region tag: they are already non-sendable and
non-escaping by construction, so the tag would be redundant.

> **Note on bracket syntax.** Whether the type-level tag stays `[r]` or moves to another
> delimiter (it currently reads close to array indexing) is parked — see the region-syntax
> discussion. The two are grammatically disjoint: a tag follows a pointer sigil (type
> context); array indexing follows a value (expression context).

### Comparison with `Box<T, A>`

`@[r] T` is structurally similar to Rust's `Box<T, A>` (unstable allocator API): both are
affine owned pointers that carry the allocator so the correct `free` is invoked on drop, and
both are distinct from `&T` / `&mut T` borrows. The difference is that Rust's `A` is a
**type** — two boxes from two different arena instances share the type `Box<T, BumpArena>`.
The tag in `@[r] T` names a specific **instance**. Three concrete consequences follow.

**Lifetime safety without a second annotation.** To get static lifetime safety from a scoped
arena in Rust, you must borrow the allocator and thread a phantom lifetime through every
containing type:

```rust
struct Parser<'a> {
    input: Box<str, &'a BumpArena>,
    pos: usize,
}
```

`'a` is a phantom parameter with no correspondent in scope. In Metel, the region handle is
the lifetime source — when `region` drops, all `@[region] T` values are statically invalid,
and errors name the real variable rather than an abstract `'a`.

**Static disjointness between allocator instances.** `Box<T, BumpArena>` is the same type
regardless of which arena instance allocated the value; the compiler cannot prove two boxes
don't alias. `@[r1] T` and `@[r2] T` are distinct types, and that distinction is a
compile-time proof of non-aliasing. RFC-0064's fork-join parallelism is built on this
property: data from two different regions can be handed to two fibers with no locks and no
runtime checks.

**Sendability encoded in the tag.** With `Box<T, A>`, sendability depends on `T: Send + A:
Send` — a scoped arena could accidentally implement `Send`. With `@[r] T` the rule is
structural: `[Heap]` → sendable, `[LocalHeap]` → thread-local only, scoped `[region]` →
never sendable. The same rule unifies `Arc` and `Rc`: `Arc<T>[Heap]` uses atomic refcounting
and is sendable; `Arc<T>[LocalHeap]` uses non-atomic refcounting and is not — one type, two
behaviors, no separate `Rc`.

`@[r] T` is therefore not sugar around `Box<T, A>`. It could lower to a structure shaped
like `Box<T, A>` at the IR level, but the tag operates at the instance level rather than the
type level, which is what makes the three properties above expressible.

---

## 3. The bracket parameter channel

A function (or struct, or closure) has up to three parameter channels, in this order:

```
fun name <type params> [region params] (value params) -> ReturnType
```

A region parameter is a **plain name** in `[...]`. It is implicitly a `&mut Region`
handle — available as a runtime value to call `.alloc` on, and used as a type-level tag on
pointer types. No type annotation is written:

```metel
fun build_node[region](val: i64) -> @[region] Node {
    region.alloc(Node { val, next: null })
}
```

The name serves all three roles at once: binder, runtime handle, and result tag.

Functions that only need to *name* a region — to relate input and output tags without
allocating — use the same form; they simply never call `.alloc`:

```metel
fun summarise[region](n: @[region] Node) -> i64 { n.val }
```

Structs use `[region]` as a type parameter when they hold a pointer into a region they do
not own:

```metel
struct Parser[region] {
    input: @[region] str,
    pos:   usize,
}
```

### 3.2 Multiple regions and `Outlives`

Bounds go inline on the parameter, analogous to type parameter bounds (`<T: Eq>`):

```metel
fun transfer<T>[src, dst: Outlives[src]](val: @[src] T) -> @[dst] T {
    dst.alloc(*val)
}
```

`Outlives[src]` names a region in brackets, keeping the notation uniform.

---

## 4. Elision and inference

Two rules keep the common case annotation-free. Both share one principle: **a region may be
omitted only when exactly one region is in scope to fill it; two or more is a hard error
that forces an explicit name.**

### 4.1 Return-position elision

If exactly one region is in the bracket channel, a bare `@` in the return type binds to it:

```metel
fun build_node[region](val: i64) -> @Node { … }
//                                  ^^^^^ == @[region] Node
```

With two or more regions in scope, the bare form is illegal and every result tag must be
named (`@[dst] T` in §3.3). This is the same discipline as Rust's lifetime-elision
ambiguity rule.

`@[region] Node` (named) remains the **idiomatic** form for readability; bare `@Node` is
sugar legal only under single-region elision. Tools may always render the inferred tag.

### 4.2 Call-site deep-threading inference

At a call to a function that declares a region parameter, an omitted bracket argument
auto-fills from the **unique region handle in lexical scope** at the call site:

```metel
fun build_list[region](vals: Slice<i64>) -> @[region] Node {
    let mut head = region.alloc(Node { val: vals[0], next: null });
    for v in vals[1..] {
        head = build_node(v);   // [region] inferred: sole handle in scope
    }
    head
}

Region::scoped(fun[region]() {
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

**Ambient static handles.** `Heap` and `LocalHeap` are prelude-resident static region
handles that are always in the inference candidate set, as if implicitly in scope at every
call site. This gives `Box::new` — a plain region-polymorphic function — the right default
behaviour without any special-casing:

```metel
// outside any Region::scoped — Heap is the only candidate
let a = Arc::new(Config { workers: 4 }); // infers [Heap] → @[Heap] Config ✓

// any region-polymorphic function shows the same behaviour
fun make_node[region](val: i64) -> @[region] Node { … }

// inside a scoped region — Heap and region are both candidates → must be explicit
Region::scoped(fun[region]() {
    let n = make_node(1);           // error: ambiguous — Heap or region?
    let n = make_node[region](1);   // @[region] Node — stays in scope
    let n = make_node[Heap](1);     // @[Heap] Node — escapes the scope
});
```

The ambiguity error inside a scoped region is intentional: allocating onto `Heap` there
means the value escapes the arena, which is worth a moment's thought. No default-parameter
mechanism is needed; the inference rules are the policy.

> **Scope of inference.** Deep-threading inference fills *region* arguments only — the
> region analogue of type-argument inference. Generalising `[…]` to arbitrary context
> parameters is explicitly out of scope for this RFC.

---

## 5. What the programmer actually writes

Most code sees no region annotations. The tag is inferred from the allocation site
(`r.alloc(..)` → `@[r] T`), exactly as a type is inferred from a constructor:

```metel
fun main() {
    let b = Heap.alloc(Counter { value: 0 });  // @[Heap] Counter
    let a = Arc::new(Config { workers: 4 });   // infers [Heap] → @[Heap] Config
    Region::scoped(fun[region]() {
        let n = region.alloc(Node { val: 1 }); // @[region] Node
    });                                        // region drops; n freed in O(1)
}
```

Region tags surface explicitly only in three places:

1. **functions that allocate into a caller-supplied region** — `[region]` in the bracket
   channel (§3);
2. **region-polymorphic / multi-region library code** — multiple names with inline
   `Outlives` bounds (§3.2);
3. **types holding a pointer into a region they do not own** — `struct Parser[region] { … }`
   (§3), including all recursive types.

---

## 6. Sendability and concurrency

The region tag decides what crosses a fiber boundary:

```
fiber boundary  :  @[Heap] T  /  Arc<T>[Heap]  /  Chan endpoint   — sendable
                   @[LocalHeap] T  /  Arc<T>[LocalHeap]             — thread-local only
                   @[region] T                                       — REJECTED (scope-bound)
```

A region pointer is sendable iff its tag is `[Heap]`. `[LocalHeap]` is thread-local: the
value exists on the heap but cannot cross a fiber boundary. A scoped `[region]` tag is
non-sendable by construction — a fiber may outlive the region. No `RegionFree`/`Send`
approximations are needed; the tag is the check.

The same rule unifies `Arc` and `Rc`: `Arc<T>[Heap]` is sendable and uses atomic refcount
operations; `Arc<T>[LocalHeap]` is non-sendable and can use non-atomic operations. The
region tag is the only distinction — no separate `Rc` type is needed.

---

## 7. Diagnostics

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

## 8. The one-sentence identity

> *A memory model where every lifetime annotation is the name of a real allocator object you
> can see in scope, the same annotation that bounds a pointer's lifetime also proves it
> cannot race, and the allocator behind it is an ordinary, swappable library value.*

Three things no incumbent offers together: lifetime tags that are real objects (not Rust's
phantom `'a`), tags that double as disjointness witnesses enabling fork-join parallelism
(RFC-0064; neither Rust nor Pony nor Vale offers this), and Zig-style swappable allocators
carrying a *static* lifetime (Zig has the allocators but no static safety).

---

## 9. Worked signatures (reference)

```metel
// 1. single-region allocator — return tag written explicitly
fun build_node[region](val: i64) -> @[region] Node {
    region.alloc(Node { val, next: null })
}
let n = build_node[r](42);     // n : @[r] Node

// 2. two-region transfer — naming mandatory
fun transfer<T>[src, dst: Outlives[src]](val: @[src] T) -> @[dst] T {
    dst.alloc(*val)
}
let moved = transfer[a, b](node);

// 3. struct holding a region pointer
struct Parser[region] { input: @[region] str, pos: usize }
fun parse[region](src: @[region] str) -> @[region] Parser {
    region.alloc(Parser { input: src, pos: 0 })
}

// 4. recursive type — region parameter required
enum List<T>[r] {
    Cons { head: T, tail: @[r] List<T> },
    Nil {},
}
fun build_list[region](vals: Slice<i64>) -> @[region] List<i64> {
    let mut acc = region.alloc(List::Nil {});
    for v in vals.rev() {
        acc = region.alloc(List::Cons { head: v, tail: acc });
    }
    acc
}

// 5. deep threading — inference fills the in-scope handle
fun build_node[region](val: i64) -> @[region] Node {
    region.alloc(Node { val, next: null })
}
fun build_chain[region](vals: Slice<i64>) -> @[region] Node {
    let mut head = region.alloc(Node { val: vals[0], next: null });
    for v in vals[1..] { head = build_node(v); }  // [region] inferred
    head
}
```

---

## 10. Unresolved questions

1. **Static vs runtime enforcement of the tag (the decisive open item).** The region tag is
   a compile-time escape analysis, which re-commits to the static direction the
   interpreter-first reconsideration argued against. The intended resolution is to make the
   tag **runtime-enforced in the interpreter** (a region-generation check) that a future
   compiler **elides** where escape analysis proves it safe — turning the one re-incurred
   concern into the capabilities↔generational-references bridge. This must be settled before
   implementation.

2. **Bracket delimiter for type-level tags.** `@[r] T` reads close to array indexing.
   Parked; tracked in the region-syntax discussion. Does not affect the parameter-channel
   design of §3–4.

3. **Static handle priority in inference.** When a local region handle and an ambient
   static handle (`Heap`, `LocalHeap`) are both in scope, the current rule treats them as
   equal candidates and forces an explicit bracket. An alternative is to give local handles
   priority, so that a single local `region` shadows `Heap` and a call like
   `make_node(v)` inside a scoped block silently allocates into the arena. This restores
   a "defaults to arena" convenience but removes the forced acknowledgement that a `Heap`
   allocation escapes the scope. Decision deferred; both readings are compatible with the
   rule structure of §4.2.

4. **Closures and `fun[region]()`.** The `Region::scoped` callback uses the bracket channel
   on a closure literal; the exact grammar for region parameters on closure types and values
   is left to the closure RFC (RFC-0050).

---

## References

- `docs/reports/memory-model/capability-region-synthesis.md` — source synthesis (§1–10).
- `docs/reports/memory-model/arena-handles-as-lifetime-annotations.md` — the region layer in
  full, including the original `[R]` clause this RFC supersedes.
- `docs/reports/memory-model/substructural-and-separation-types.md` — the capability core.
- RFC-0052 (Lifetime System, on hold) — the phantom-lifetime approach this supersedes.
- RFC-0050 (Closure Capture Lists), RFC-0049 (Linear `fun` Type System) — adjacent.
- RFC-0064 (Structured Fork-Join Parallelism) — builds the `||` combinator on the
  disjointness witness property of region tags.
