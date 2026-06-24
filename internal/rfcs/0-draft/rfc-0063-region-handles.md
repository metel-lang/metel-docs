---
id: rfc-0063
title: "Region Handles"
date: '2026-06-24'
---

> **Status — draft, design-only.** This RFC consolidates the region-related half of
> `docs/reports/memory-model/capability-region-synthesis.md` into a single normative
> proposal and adopts the **bracket parameter channel** syntax (region handles declared in
> `[...]`, value parameters in `(...)`). It depends on the reference-capability core
> (`*own`/`*mut`/`*`, RFC TBD) and inherits the open interpreter-first question recorded in
> §11. Do **not** implement pending resolution of that question and of the capability-core
> RFC.

> **Vocabulary note.** Following the synthesis report, the unique-owner capability is written
> `*own` (the arena/substructural reports call it `*iso`). They denote the same capability —
> unique, mutable, sendable. Examples elsewhere in the discussion used `*iso`; substitute
> freely.

## Summary

A **region** is an allocation arena with a scope. Its **handle** — an ordinary runtime value
of type `&mut Region` you can call `.alloc` on — does double duty: its *name* becomes a
**lifetime tag** carried on a capability (`*own[region] T`), and that same tag serves as a
**static disjointness witness** for fork-join parallelism (two values with different tags
provably cannot alias).

Regions are not the safety mechanism — reference capabilities are. The region handle is a
*tag a capability can carry*, naming a real object in scope rather than an inferred,
phantom lifetime variable.

This RFC specifies:

1. region tags on capabilities (`*own[r] T`) and what they mean on each capability;
2. the **bracket parameter channel** — region handles and abstract region tags declared in
   `[...]`, distinct from value parameters in `(...)`;
3. two **elision/inference rules** — return-position elision and call-site **deep-threading
   inference** — that keep the common single-region case annotation-free;
4. the sendability and fork-join consequences of the tag;
5. the static-vs-runtime enforcement question that remains open.

---

## Motivation

The paused lifetime branch (RFC-0052) put a Rust-style inferred lifetime `'a` at the centre
of memory safety. Two complaints sank it: the lifetimes were phantom (nothing in scope you
could point at), and diagnostics had to explain a variable the programmer never wrote.

Region handles answer both. Every lifetime tag is the **name of an allocator object visible
in scope**, so:

- single-region checking reduces to *liveness of a named variable* — "is `region` still in
  scope here?" — which the compiler already computes, and errors name the actual region
  (`*own[region] value escapes the scope of region`) instead of an abstract `'a`;
- the tag that bounds a value's lifetime **also** proves it cannot race, so structured
  parallelism over region data is free of any separate separation calculus.

The cost the earlier exploration kept hitting was *verbosity*: a region threaded through a
signature was named three times (binder, handle type, result tag). This RFC removes that by
merging the binder and the handle into one bracket-channel parameter and adding inference so
deep threading needs no ceremony.

---

## 1. Regions as tags, not the mechanism

The reconciliation with the paused branch is a change of *role*, not a reversal:

- **Old role:** the region was *the* memory mechanism and an inferred whole-program lifetime
  `'r` was the safety device. Memory safety *was* lifetime inference.
- **New role:** the **reference capability** is the safety device. The region is one
  *allocation strategy* among several (`Heap`, `LocalHeap`, scoped `Region`), and its handle
  is reused as a **lifetime tag on a capability**.

So regions are demoted from "the mechanism" to "a tag one of the capabilities carries." A
single annotation does triple duty:

- **the capability** (`*own`, `*mut`, `*`) says *who may touch it and whether it sends*;
- **the region tag** (`[r]`) says *how long it lives*, named after a visible handle;
- **the tag, again**, gives fork-join a *static disjointness proof* — different tags cannot
  alias, so parallel access is race-free by construction.

```metel
let a: *own[r1] Counter = r1.alloc(Counter { value: 0 });
let b: *own[r2] Counter = r2.alloc(Counter { value: 0 });
a.inc() || b.inc();   // [r1] ∩ [r2] = ∅ statically → parallel for free
```

That dual use — *lifetime bound* and *disjointness witness* in one symbol — is the
load-bearing novelty.

---

## 2. Region tags on capabilities

A region tag is written in brackets immediately after the capability sigil: `*own[r] T`.
The tag is **meaningful only on the sendable capabilities**; on borrow capabilities it is
redundant (they are already non-sendable and non-escaping).

| capability | no tag | `[r]` (scoped) | `[Heap]` (static) |
|---|---|---|---|
| `*own T` (unique, mutable) | sendable | scope-bound, **not** sendable | sendable |
| `*mut T` (mutable borrow) | local | local (tag redundant) | local |
| `*T` (read borrow) | local | local (tag redundant) | local |

The tag's job is to **remove** sendability by binding a value to a non-static scope: a
scoped region tag makes an otherwise-sendable `*own` non-sendable (§6). A static tag
(`Heap`, `LocalHeap`) or no tag leaves it sendable.

> **Note on bracket syntax.** Whether the *type-level* tag stays `[r]` or moves to another
> delimiter (it currently reads close to array indexing) is parked — see the region-syntax
> discussion. This RFC keeps `[r]` for type tags. The two are grammatically disjoint anyway:
> a tag follows a capability sigil or type (type context); array indexing follows a value
> (expression context).

`Arc<T>` and `Box<T>` carry the same tag in their type (`Arc<Config>[Heap]`,
`Box<Counter>[Heap]`); `Box`/`Arc`/`Rc` are ordinary stdlib structs parameterised by the
region they allocate into, defaulting to `Heap`.

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
fun build_node[region: &mut Region](val: i64) -> *own Node {
    region.alloc(Node { val, next: null })
}
```

This replaces the old three-mention form
`fun build_node[R](region: &mut Region[R], val) -> *own[R] Node`: the abstract binder `R`,
the handle parameter, and the relating type `Region[R]` collapse into one declaration. The
region is named **once**.

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

The abstract form is the handle-less degenerate case of the same feature — it is exactly the
old `[R]` clause, now spelled with a name the reader can point at. A struct **never** holds a
`&mut Region`; it only needs the tag, so structs always use the abstract form.

### 3.3 Multiple regions and `Outlives`

Relating two regions uses both names plus a bound in the bracket channel:

```metel
fun transfer<T>[src: &mut Region, dst: &mut Region where dst: Outlives[src]](
    val: *own[src] T,
) -> *own[dst] T {
    dst.alloc(*val)
}
```

`Outlives[src]` itself names a region in brackets, so the notation stays uniform. `src` and
`dst` are handle-form here because `transfer` reads from one and allocates into the other.

---

## 4. Elision and inference

Two rules keep the common case annotation-free. Both share one principle: **a region may be
omitted only when exactly one region is in scope to fill it; two or more is a hard error that
forces an explicit name.**

### 4.1 Return-position elision

If exactly one region is in the bracket channel, a bare capability tag in the return type
binds to it:

```metel
fun build_node[region: &mut Region](val: i64) -> *own Node { … }
//                                              ^^^^^^^^ == *own[region] Node
```

With two or more regions in scope, the bare form is illegal and every result tag must be
named (`*own[dst] T` in §3.3). This is the same discipline as Rust's lifetime-elision
ambiguity rule.

`*own[region] Node` (named) remains the **idiomatic** form for readability; bare `*own Node`
is sugar legal only under single-region elision. Tools may always render the inferred tag.

### 4.2 Call-site **deep-threading** inference

At a call to a function that declares a region parameter, an omitted bracket argument
auto-fills from the **unique region handle in lexical scope** at the call site:

```metel
fun build_list[region: &mut Region](vals: Slice<i64>) -> *own[region] Node {
    let mut head = region.alloc(Node { val: vals[0], next: null });
    for v in vals[1..] {
        head = build_node(v);   // region inferred: the sole handle in scope is `region`
    }
    head
}

Region::scoped(fun[region: &mut Region]() {
    let list = build_list(data);     // region inferred again
    let list = build_list[region](data);  // explicit form — always available
});
```

Rule:

1. If the caller has **exactly one** region handle in lexical scope, an omitted `[...]` at a
   call resolves to it. `f(args)` ≡ `f[that_handle](args)`.
2. If **two or more** region handles are in scope, the bracket is **required**:
   `f[which](args)`. Omitting it is an error naming the candidates.
3. If **none** is in scope but the callee needs one, that is the usual "no region available"
   error (allocate a `Region::scoped` or pass `Heap`).

This recovers ceremony-free deep threading (the `build_node(v)` call above needs no
`[region]`) without making region flow invisible: the resolution is always a single named
handle the compiler can surface in diagnostics and hovers. The explicit `f[region](args)`
form stays available and is preferred wherever more than one region is nearby or where making
the allocation context visible aids the reader.

> **Scope of inference.** Deep-threading inference fills *region* arguments only. It is the
> region analogue of type-argument inference, not a general implicit-parameter mechanism;
> generalising `[...]` to arbitrary context parameters (allocators, capabilities, effect
> handlers) is explicitly **out of scope** for this RFC.

---

## 5. What the programmer actually writes

Most code sees no region annotations at all. The capability is defaulted/inferred and the tag
is inferred from the allocation site (`r.alloc(..)` → `*own[r] ..`), exactly as a type is
inferred from a constructor:

```metel
fun main() {
    let b = Box::new(Counter { value: 0 });   // Box<Counter>[Heap] — inferred
    let a = Arc::new(Config { workers: 4 });  // Arc<Config>[Heap]
    Region::scoped(fun[region: &mut Region]() {
        let n = region.alloc(Node { val: 1 }); // *own[region] Node — tag inferred
        process(n) || work_elsewhere();        // disjoint tags → parallel for free
    });                                         // region drops; n freed in O(1)
}
```

Region tags surface explicitly only in three places:

1. **functions that allocate into a caller-supplied region** — handle form
   `[region: &mut Region]` (§3.1);
2. **region-polymorphic / multi-region library code** — the multi-name bracket channel with
   `Outlives` bounds (§3.3);
3. **structs holding a pointer into a region they do not own** — abstract-tag form
   `struct Parser[region] { … }` (§3.2).

These are exactly the cases where the paused branch wrote `'a` / `<'a, 'b: 'a>`. The
difference: every name is a parameter or handle the reader can point at, and the common
single-region case needs no clause.

---

## 6. Sendability and concurrency

The capability and the tag together decide what crosses a fiber boundary:

```
fiber boundary  :  *own T  /  Arc<T>  /  Chan endpoint   — sendable; ownership transfers
                   *own[region] T                        — REJECTED at send (scope-bound)
```

A value is sendable iff its capability is sendable **and** its tag is static (`Heap`) or
absent. `*own[region] T` fails the send check **by construction** — the precise property the
paused branch needed `RegionFree`/`Send` approximations to express. A fiber may outlive the
region, so it can never hold a borrow into one.

---

## 7. The tag as a disjointness witness (fork-join)

Because region-bound values are non-sendable, `spawn` alone cannot parallelise over them —
you would first have to copy to `Heap` or wrap in `Arc`, defeating the region. **Structured
fork-join is the one construct that escapes this**, because it is structured: `||` guarantees
both sides finish before the expression returns, *inside* the region's scope, so handing each
side a borrow into the region is sound — the borrow cannot outlive the join.

```metel
Region::scoped(fun[region: &mut Region]() {
    let t = build[region](…);                       // *own[region] Node — non-sendable
    let (ls, rs) = sum(&t.left) || sum(&t.right);   // borrows into region, in parallel — sound
});                                                 // both halves provably finished before drop
```

Safety here needs **no separation calculus**: two distinct tags ⇒ provably disjoint memory
(`[r1] ∩ [r2] = ∅`), and `*mut` is already exclusive, so two parallel branches are safe iff
each independently type-checks against the ordinary rules. `||` is a sealed library
combinator over the M:N scheduler (`join<A,B>(a, b) -> (A, B)` with `e₁ || e₂` as sugar); the
tag **is** the proof.

---

## 8. Diagnostics

Single-region checking reduces to liveness of a named variable. Errors name the real region:

```
error: `*own[region] value` escapes the scope of `region`
  --> ...
   |  the value is allocated in `region`, which is dropped here
```

instead of explaining an abstract `'a` the programmer never wrote. This dissolves the
diagnostic problem the paused branch most feared, for the common case.

The hard case is unchanged: when regions arrive from outside (`transfer`, `Outlives`,
multi-region structs), the constraint machinery is the old `<'a, 'b: 'a>` story under a new
spelling — escape analysis is escape analysis. The *frequency* of hitting that path drops a
lot; its *difficulty* does not.

---

## 9. The one-sentence identity

> *A memory model where every lifetime annotation is the name of a real allocator object you
> can see in scope, the same annotation that bounds a value's lifetime also proves it cannot
> race, and the allocator behind it is an ordinary, swappable library value.*

Three things no incumbent offers together: lifetime tags that are real objects (not Rust's
phantom `'a`), tags reused as fork-join disjointness witnesses (neither Rust nor Pony nor
Vale does this), and Zig-style swappable allocators carrying a *static* lifetime (Zig has the
allocators but no static safety).

---

## 10. Worked signatures (reference)

```metel
// 1. single-region allocator — return elided
fun build_node[region: &mut Region](val: i64) -> *own Node {
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

// 4. deep threading — inference fills the in-scope handle
fun build_list[region: &mut Region](vals: Slice<i64>) -> *own[region] Node {
    let mut head = region.alloc(Node { val: vals[0], next: null });
    for v in vals[1..] { head = build_node(v); }   // [region] inferred
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

2. **Bracket delimiter for *type-level* tags.** `*own[r] T` reads close to array indexing.
   Parked here; tracked in the region-syntax discussion. Does not affect the parameter-channel
   design of §3–4 (parameter brackets and type-tag brackets can be decided independently).

3. **`Outlives` bound syntax in the bracket channel.** `[dst: &mut Region where dst:
   Outlives[src]]` is proposed; an inline form (`[src, dst: Outlives[src]]`) may read better
   and needs a decision.

4. **Closures and `fun[region: &mut Region]()`.** The `Region::scoped` callback uses the
   bracket channel on a closure literal; the exact grammar for region parameters on closure
   types and values is left to the closure RFC (RFC-0050).

5. **Interaction with default regions.** `Box::new`/`Arc::new` default to `[Heap]`. How an
   ambient default region composes with deep-threading inference (does an in-scope scoped
   `Region` shadow `Heap` for un-annotated allocations?) needs specification.

---

## References

- `docs/reports/memory-model/capability-region-synthesis.md` — source synthesis (§1–10).
- `docs/reports/memory-model/arena-handles-as-lifetime-annotations.md` — the region layer in
  full, including the original `[R]` clause this RFC supersedes.
- `docs/reports/memory-model/substructural-and-separation-types.md` — the capability core.
- RFC-0052 (Lifetime System, on hold) — the phantom-lifetime approach this supersedes.
- RFC-0050 (Closure Capture Lists), RFC-0049 (Linear `fun` Type System) — adjacent.
