---
id: rfc-0065
title: "Region Ergonomics"
date: '2026-06-27'
---

> **Status — draft, design-only.** Depends on RFC-0063 (Region Handles). Specifies the
> annotation-reduction layer on top of the core region system: elision rules and call-site
> inference that eliminate bracket ceremony in the common single-region case. Do **not**
> implement before RFC-0063 is resolved and §4.1 of this RFC is settled.

## Summary

RFC-0063 establishes the core region system — `@[r] T`, the bracket parameter channel, and
sendability — in fully explicit form: every region argument is written out. This RFC adds
two rules that make the common single-region case annotation-free:

1. **return-position elision** — bare `@` in a return type resolves to the unique in-scope
   region;
2. **call-site deep-threading inference** — omitting the bracket argument at a call site
   auto-fills from the unique region handle in lexical scope.

Both rules share one invariant: **elision is legal only when exactly one region is in scope;
two or more forces an explicit name.**

---

## 1. Return-position elision

If exactly one region is in the bracket channel, a bare `@` in the return type binds to it:

```metel
fun build_node[region](val: i64) -> @Node { … }
//                                  ^^^^^ == @[region] Node
```

With two or more regions in scope the bare form is illegal; every result tag must be named
(`@[dst] T`). This is the same discipline as Rust's lifetime-elision ambiguity rule.

`@[region] Node` (named) is the **idiomatic** form; bare `@Node` is sugar legal only under
single-region elision. Tools may always render the inferred tag.

---

## 2. Call-site deep-threading inference

At a call to a function that declares a region parameter, an omitted bracket argument
auto-fills from the **unique region handle in lexical scope** at the call site:

```metel
fun build_list[region](vals: Slice<i64>) -> @[region] Node {
    let mut head = region.alloc(Node { val: vals[0], next: null });
    for v in vals[1..] {
        head = build_node(v);            // [region] inferred: sole handle in scope
    }
    head
}

Region::scoped(fun[region]() {
    let list = build_list(data);         // [region] inferred
    let list = build_list[region](data); // explicit — always available
});
```

Rules:

1. **One** handle in scope → omitted `[…]` resolves to it. `f(args)` ≡ `f[that_handle](args)`.
2. **Two or more** handles in scope → bracket required: `f[which](args)`. Omitting it is an
   error naming the candidates.
3. **None** in scope but the callee needs one → the usual "no region available" error;
   establish a `Region::scoped` or pass `Heap` explicitly.

The resolution is always a single named handle the compiler can surface in diagnostics and
hovers. The explicit form `f[region](args)` is preferred wherever more than one region is
nearby or where the allocation context is worth making visible.

**Ambient static handles.** `Heap` and `LocalHeap` are prelude-resident and always in the
inference candidate set:

```metel
// outside any Region::scoped — Heap is the only candidate
let a = Arc::new(Config { workers: 4 }); // infers [Heap] → @[Heap] Config ✓

// inside a scoped region — Heap and region are both candidates → must be explicit
Region::scoped(fun[region]() {
    let n = make_node(1);           // error: ambiguous — Heap or region?
    let n = make_node[region](1);   // @[region] Node — stays in scope
    let n = make_node[Heap](1);     // @[Heap] Node — escapes the scope
});
```

The ambiguity error inside a scoped region is intentional: allocating onto `Heap` there
means the value escapes the arena, which is worth a moment's thought.

> **Scope of inference.** These rules fill *region* arguments only — the region analogue of
> type-argument inference. Generalising `[…]` to arbitrary context parameters is out of
> scope.

---

## 3. What the programmer actually writes

With both rules active, most code sees no region annotations beyond the allocation call
itself:

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
   channel (RFC-0063 §3);
2. **region-polymorphic / multi-region library code** — multiple names with inline
   `Outlives` bounds (RFC-0063 §3.2);
3. **types holding a pointer into a region they do not own** — `struct Parser[region] { … }`
   (RFC-0063 §3), including all recursive types.

---

## 4. Unresolved questions

1. **Static handle priority in inference.** When a local region handle and an ambient static
   handle (`Heap`, `LocalHeap`) are both in scope, the current rule treats them as equal
   candidates and forces an explicit bracket. An alternative is to give local handles
   priority, so that a single local `region` shadows `Heap` and `make_node(v)` inside a
   scoped block silently allocates into the arena. This restores a "defaults to arena"
   convenience but removes the forced acknowledgement that a `Heap` allocation escapes the
   scope. Decision deferred; both readings are compatible with the rule structure of §2.

2. **Closures and `fun[region]()`.** The `Region::scoped` callback uses the bracket channel
   on a closure literal; the exact grammar for region parameters on closure types and values
   is left to the closure RFC (RFC-0050).

---

## References

- RFC-0063 (Region Handles) — core system this RFC builds on.
- RFC-0050 (Closure Capture Lists) — closure grammar for `fun[region]()`.
