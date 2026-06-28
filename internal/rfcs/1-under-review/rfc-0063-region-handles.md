---
id: rfc-0063
title: "Region Handles"
date: '2026-06-24'
---

> **Status — draft, design-only.** This RFC consolidates the region-related half of
> `docs/reports/memory-model/capability-region-synthesis.md` into a single normative
> proposal and adopts the **bracket parameter channel** syntax (region handles declared in
> `[...]`, value parameters in `(...)`). It depends on RFC-0071 (Ownership and Move
> Semantics) for the affine ownership model that makes region lifetime guarantees sound.
> Annotation-reduction ergonomics (elision, call-site inference) are deferred to RFC-0065.
> The region system is purely compile-time: the interpreter uses a single uniform allocator
> for all regions regardless of region type, and enforces region lifetime constraints via
> the borrow checker rather than at runtime.

> **Vocabulary note.** This RFC uses `@[r] T` as the notation for a region-allocated
> pointer (the result of `@[r] expr`). This is **not** a capability; see §2. The
> arena/substructural reports call the same type `*iso`; substitute freely.

## Summary

A **region** is an allocation arena with a scope. Its **handle** — an ordinary runtime value
of type `&mut Region` you can call `.alloc` on — does double duty: its *name* becomes a
**lifetime tag** carried on a pointer (`@[region] T`), and that same tag serves as a
**static disjointness witness** (two pointers with different tags provably cannot alias).

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
4. the sendability consequences of the tag.

Annotation-reduction ergonomics (return-position elision, call-site deep-threading
inference) are specified separately in RFC-0065 and are not required to implement this core.

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
signature was named three times (binder, handle type, result tag). The bracket parameter
channel removes that by merging all three into a single bare name.

---

## 1. Regions as the exclusive allocation mechanism

All memory allocation goes through region handles. There is no allocation expression that
operates outside of a region — no `new expr`, no implicit heap allocation. Every pointer
to heap-allocated data carries a region tag naming the allocator it came from.

A region is any value that implements the **region allocator interface** — an ordinary runtime
contract for allocation, deallocation, and drop. The region system is open: any type
satisfying the interface may be used as a region handle in the bracket channel. Pool
allocators, slab allocators, stack arenas, and domain-specific stores all fit without
language changes.

The three regions the stdlib provides as defaults:

- **`Region`** — scoped bump arena; values freed in O(1) when the region drops.
- **`Heap`** — the static global heap; values freed individually when the last owner drops.
- **`LocalHeap`** — thread-local heap; not sendable across fibers.

**Creating a scoped region.** A `Region` can be brought into scope in two ways:

1. **Closure-scoped** — `Region::scoped([r]() -> { … })` passes the region handle to a
   closure via the bracket channel; the arena is freed when the closure returns. Nothing
   carrying the tag `r` may escape the closure.

2. **Variable-scoped** — `let r = Region::new()` binds the region to `r`. The binding name
   `r` becomes the type-level tag — the same name that appears in `@[r] T`, `&[r] T`, and
   bracket parameters throughout the code. The arena is freed when `r` is dropped: either
   explicitly via `drop(r)`, or implicitly when `r` goes out of lexical scope. The borrow
   checker rejects any live `@[r] T` or `&[r] T` at the point of drop.

`Region::scoped` is equivalent to a block with an implicit drop at the end:

```metel
Region::scoped([r]() -> { body });
// ≡
{ let r = Region::new(); body }  // r dropped at end of block
```

The closure form creates a visible syntactic boundary signalling the block is arena-managed.
The `let` form is more flexible: the region can span multiple function calls, be passed as a
bracket argument, or be dropped early. Both forms use the same underlying arena type.

`Arc<T>` is the one stdlib wrapper that adds semantics beyond the region tag: shared
ownership via refcount. It is region-polymorphic — the region is supplied at the call site —
and its sendability follows from the tag:

- `Arc<T>[Heap]` — atomic refcount, sendable across fibers.
- `Arc<T>[LocalHeap]` — non-atomic refcount, not sendable; the tag already guarantees
  single-thread access, so the cheaper implementation is sound.

The second form subsumes `Rc<T>` from the Rust model: the non-sendability that justified
a separate `Rc` type is already encoded in `[LocalHeap]`, so no additional type is needed.
`Box<T>` is **retired** — `@[Heap] T` is self-documenting and direct heap allocation is
written `@[Heap] expr`.

Allocation is a **language expression**: `@[r] expr` allocates `expr` into region `r` and
produces a value of type `@[r] T`. This desugars to `r.alloc(expr)`; the bracket channel
still carries the runtime handle, so other region operations (`free`, `reset`, and any
future methods) remain callable as `r.method(…)`. The allocation expression is the common
case and deserves first-class syntax; other uses of the handle are available when needed.

---

## 2. Region pointers and borrow capabilities

Metel has three pointer types. Only two are **capabilities**:

| type | role | sendable |
|---|---|---|
| `@[r] T` | **region pointer** — affine result of `@[r] expr`; *not a capability* | yes if `[Heap]`/`[LocalHeap]`; no if `[r]` scoped |
| `&mut T` | **capability** — exclusive mutable borrow | no (always local) |
| `&T` | **capability** — shared read borrow | no (always local) |

### Region pointers are not a capability

`@[r] T` is the type produced by `@[r] expr`. Its "owned" nature — the guarantee that
exactly one live reference to this allocation exists — comes from **affine move semantics**,
not from a named capability: the pointer is non-`Copy`, so moving it leaves no duplicate
behind. This is the same position Rust takes: owned values are the *default* state of any
non-`Copy` type; `&mut`/`&` are the capabilities layered on top.

The capabilities (`&mut`, `&`) are pure *access-mode* qualifiers on borrows. They say who
may touch a value and for how long; they say nothing about allocation or memory ownership.

### Borrowing: temporary downgrade and reconstitution

A region pointer can be **temporarily borrowed** for the duration of a call or block:

```metel
let n = @[r] Node { val: 1, next: null };

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
let list = @[r] List::Cons {
    head: 1,
    tail: @[r] List::Cons {
        head: 2,
        tail: @[r] List::Nil {},
    },
};
// list : @[r] List<i64>
```

The region parameter on `List` is not optional — it is the honest statement that the list's
nodes live somewhere, and the caller decides where.

### The region tag

The tag `[r]` in `@[r] T` is the name of the allocating region handle. It is **not part
of the capability** — it is a component of the pointer *type*, naming the scope that owns
the backing memory. The tag:

- determines **sendability**: scoped `[r]` → not sendable; static `[Heap]` → sendable (§6);
- serves as a **disjointness witness**: distinct tags → cannot alias.

Borrow types (`&mut T`, `&T`) do not carry a region tag for sendability or disjointness
purposes — they are already non-sendable and non-escaping by construction. However, when
borrowing a region pointer in a function signature the double-sigil `&@[r] T` is
unnecessarily noisy. As a notation convenience, `[r]` may appear directly after `&` or
`&mut` as shorthand:

| Sugar | Expands to | Meaning |
|---|---|---|
| `&[r] T` | `&@[r] T` | shared borrow of a region-`r` value |
| `&mut [r] T` | `&mut @[r] T` | exclusive borrow of a region-`r` value |

The `@` vs `&`/`&mut` prefix still carries the ownership distinction — `@[r] T` is an
affine owned pointer, `&[r] T` is a temporary loan of one.

### Allocation expressions and type-directed binding

`@[r] expr` is the allocation expression. The `@[r]` prefix is a language construct, not a
method call; the compiler lowers it to `r.alloc(expr)` using the runtime handle from the
bracket channel.

When a `let` binding carries an explicit type annotation of `@[r] T`, the right-hand side
may be a bare `T` expression — the declared type drives allocation, eliminating the need to
repeat `@[r]` on the right:

```metel
// inferred — @[r] on the right-hand side
let node = @[r] Node { val: 1, next: null };

// type-directed — @[r] T in the annotation, bare T on the right
let node: @[r] Node = Node { val: 1, next: null };

// both forms are equivalent; the inferred form is idiomatic for local bindings,
// the type-directed form is preferred when the type annotation is already present
// for documentation purposes
```

Type-directed allocation applies at the binding level only. Nested fields and sub-expressions
require an explicit `@` (or `@[r]` when elision does not apply) — the rule does not recurse
through struct literals. This keeps every allocation site visible with a consistent single
sigil; RFC-0065 elision already reduces the annotation cost in the single-region case to a
bare `@`.

> **Note on bracket syntax.** `@[r] T` is unambiguous: `[r]` follows the `@` sigil in type
> or expression position, whereas array indexing follows a value. The two contexts are
> grammatically disjoint; no delimiter change is needed.

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
compile-time proof of non-aliasing: data from two different regions provably cannot
alias, with no locks and no runtime checks required.

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

A region parameter is a **name**, optionally followed by a type annotation, in `[...]`. The
name serves all three roles at once: binder, runtime handle, and result tag.

**Default (no annotation).** A bare name defaults to a **non-fallible** region — allocation
panics on OOM rather than returning `Result<T, _>`. The concrete type is determined by the
call site — whether it resolves to a scoped `Region`, `Heap`, or `LocalHeap` handle:

```metel
fun build_node[region](val: i64) -> @[region] Node {
    @[region] Node { val, next: null }
}
```

The name `region` is used directly in the allocation expression. The runtime handle is also
available by name for other operations — `region.free(ptr)`, `region.reset()`, etc. — but
allocation is written as `@[region] expr`, not `region.alloc(expr)`.

**Explicit type annotation.** To constrain a parameter to a specific allocator, annotate
with `:` — the same form as type parameter bounds:

```metel
fun build_on_heap[r: Heap](val: i64) -> @[r] Node {
    @[r] Node { val, next: null }
}
```

The annotation is any type that implements the region allocator interface — `Heap`,
`LocalHeap`, `Region`, or a custom allocator type. Fallible allocators require an explicit
annotation; a bare parameter never silently introduces a fallible allocation path.

Functions that only need to *name* a region — to relate input and output tags without
allocating — use the same form; they simply never use `@[region] expr`:

```metel
fun summarise[region](n: @[region] Node) -> i64 { n.val }
```

Structs use `[region]` as a type parameter when they hold a pointer into a region they do
not own:

```metel
struct Parser[region] {
    input: @[region] String,
    pos:   u64,
}
```

### 3.2 Multiple regions and `Outlives`

Bounds go inline on the parameter, using `<>` for consistency with type parameter bounds
(`<T: Eq>`):

```metel
fun transfer<T>[src, dst: Outlives<src>](val: @[src] T) -> @[dst] T {
    @[dst] *val
}
```

`Outlives<src>` reads as "`dst` outlives `src`" and uses angle brackets so the bound form
is uniform across both channels: `<T: Trait>` and `[r: Outlives<other>]`.

---

## 4. Sendability and concurrency

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

## 5. Diagnostics

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
spelling — escape analysis is escape analysis. The frequency of hitting that path drops
significantly with RFC-0065's inference; its difficulty does not.

---

## 6. The one-sentence identity

> *A memory model where every lifetime annotation is the name of a real allocator object you
> can see in scope, the same annotation that bounds a pointer's lifetime also proves it
> cannot race, and the allocator behind it is an ordinary, swappable library value.*

Three things no incumbent offers together: lifetime tags that are real objects (not Rust's
phantom `'a`), tags that double as disjointness witnesses (distinct region tags prove
non-aliasing — a foundation for structured parallelism), and Zig-style swappable
allocators carrying a *static* lifetime (Zig has the allocators but no static safety).

---

## 7. Worked signatures (reference)

```metel
// 1. single-region allocator
fun build_node[region](val: i64) -> @[region] Node {
    @[region] Node { val, next: null }
}
let n = build_node[r](42);     // n : @[r] Node

// 2. two-region transfer — naming mandatory
fun transfer<T>[src, dst: Outlives<src>](val: @[src] T) -> @[dst] T {
    @[dst] *val
}
let moved = transfer[a, b](node);

// 3. struct holding a region pointer
struct Parser[region] { input: @[region] String, pos: u64 }
fun parse[region](src: @[region] String) -> @[region] Parser {
    @[region] Parser { input: src, pos: 0 }
}

// 4. recursive type — region parameter required
enum List<T>[r] {
    Cons { head: T, tail: @[r] List<T> },
    Nil {},
}
fun build_list[region](vals: i64[]) -> @[region] List<i64> {
    let mut acc = @[region] List::Nil {};
    for (let i in 0..array_len(vals)) {
        acc = @[region] List::Cons { head: vals[i], tail: acc };
    }
    acc
}

// 5. type-directed binding — annotation drives allocation, no @[r] on the right
let node: @[r] Node = Node { val: 42, next: null };
```

---

## 8. Unresolved questions

None.

---

## References

- `docs/reports/memory-model/memory-model-overview.md` — narrative overview of the full
  region system built on this RFC.
- RFC-0052 (Lifetime System, on hold) — the phantom-lifetime approach this supersedes.
- RFC-0064 (Structured Fork-Join Parallelism, deferred) — builds the `||` combinator on
  the disjointness witness property of region tags.
- RFC-0065 (Region Ergonomics) — return-position elision and call-site inference on top of
  this core.
- RFC-0066 (Region Pointer Extraction) — how to obtain `T` or `&T` from `@[r] T`.
