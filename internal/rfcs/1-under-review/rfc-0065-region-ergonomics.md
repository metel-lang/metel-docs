---
id: rfc-0065
title: "Region Ergonomics"
date: '2026-06-27'
---

> **Status — draft, design-only.** Depends on RFC-0063 (Region Handles). Specifies the
> annotation-reduction layer on top of the core region system: elision rules and call-site
> inference that eliminate bracket ceremony in the common single-region case. Do **not**
> implement before RFC-0063 is resolved.

## Summary

RFC-0063 establishes the core region system — `@[r] T`, the bracket parameter channel, and
sendability — in fully explicit form: every region argument is written out. This RFC adds
two rules that make the common single-region case annotation-free:

1. **`@`-position elision** — bare `@` anywhere in a type or expression resolves to the
   unique in-scope region;
2. **call-site deep-threading inference** — omitting the bracket argument at a call site
   auto-fills from the unique region handle in lexical scope.

Both rules share one invariant: **elision is legal only when exactly one region is in scope;
two or more forces an explicit name.**

Region-tagged borrows (`&[r] T`, `&mut [r] T`) are **never elided** in signatures. A bare
`&T` in a signature always means a plain borrow with no region tag; if the region matters,
`&[r] T` must be written explicitly.

---

## 1. All-position elision

If exactly one region is in the bracket channel, the explicit tag `[r]` may be dropped in
`@`-bearing type and expression positions:

| Sugar | Expands to | When legal |
| `@T` | `@[r] T` | Always — `@` always implies a region pointer |

### 1.1 `@` positions

Bare `@` always elides the single region tag. The same rule applies in both **type position**
and **expression position**:

```metel
// return type
fun build_node[region](val: i64) -> @Node { … }
//                                  ^^^^^ == @[region] Node

// parameter
fun concat[region](left: @Rope, right: @Rope) -> @Rope { … }
//                       ^^^^^                   ^^^^^  == @[region] Rope

// struct / enum field
enum Rope[r] {
    Leaf { bytes: @String },           // == @[r] String
    Node { left: @Rope, right: @Rope, len: u64 },  // == @[r] Rope
}

// expression position — @expr allocates into the sole in-scope region
let node = @Node { val: 1, next: null };
//         ^^^^^^^^^^^^^^^^^^^^^^ == @[region] Node { val: 1, next: null }

let list = @List::Cons { head: 1, tail: @List::Cons { head: 2, tail: @List::Nil {} } };
//         all @-prefixed sub-expressions allocate into [region]
```

Expression-position elision follows the same single-region invariant as type-position
elision: illegal with two or more regions in scope (§1.2).

### 1.2 Two-or-more regions

With two or more regions in scope the bare forms are illegal; every tag must be named.
This is the same discipline as Rust's lifetime-elision ambiguity rule:

```metel
fun copy_list<[src, dst: Outlives<src>]>(v: &[src] List<u32>) -> @[dst] List<u32> { … }
//  ^^^^^^^^^                                ^^^^^^^^^^^^^^^^^    ^^^^^^^^^^^^^^^^^
//  two regions → all tags explicit
```

`@[region] Node` (named) is always the full explicit form; `@Node` is sugar legal only
under single-region elision. Tools may always render the inferred tag.

---

## 2. Call-site deep-threading inference

At a call to a function that declares a region parameter, an omitted bracket argument
auto-fills from the **unique region handle in lexical scope** at the call site:

```metel
fun build_list[region](vals: i64[]) -> @[region] Node {
    let mut head = @[region] Node { val: vals[0], next: null };
    for (let i in 1..array_len(vals)) {
        head = build_node(vals[i]);      // [region] inferred: sole handle in scope
    }
    head
}

Region::scoped([region]() -> {
    let list = build_list(data);         // [region] inferred
    let list = build_list[region](data); // explicit — always available
});
```

> **Interaction with `@[r] expr`.** The allocation expression `@[r] expr` (RFC-0063 §1)
> addresses the value-threading problem for allocation: functions that allocate via
> `@[region] expr` do not need the caller to thread the runtime handle as a value argument.
> Call-site bracket inference (this section) handles the remaining case — functions that
> declare `[region]` in their bracket channel for reasons other than allocation (naming the
> region tag in return types, `Outlives` bounds, etc.) still benefit from omitting the
> bracket argument at call sites.

Rules:

1. **One** handle in scope → omitted `[…]` resolves to it. `f(args)` ≡ `f[that_handle](args)`.
2. **Two or more** handles in scope → bracket required: `f[which](args)`. Omitting it is an
   error naming the candidates.
3. **None** in scope but the callee needs one → the usual "no region available" error;
   establish a region via `Region::scoped` or `let r = Region::new()`, import `Heap`, or
   pass the region explicitly.

The resolution is always a single named handle the compiler can surface in diagnostics and
hovers. The explicit form `f[region](args)` is preferred wherever more than one region is
nearby or where the allocation context is worth making visible.

**Static handles and the inference candidate set.** `Heap` and `LocalHeap` are always
accessible by name — `@[Heap] T`, `@[LocalHeap] T`, and explicit bracket arguments like
`make_node[Heap](v)` work anywhere without any import. However, they enter the inference
candidate set **only when explicitly imported**:

```metel
use Heap;
```

This gives three clean scenarios:

```metel
// 1. Heap imported, no scoped region — Heap is the sole candidate
use Heap;
let a = Arc::new(Config { workers: 4 }); // infers [Heap] → @[Heap] Config ✓

// 2. No Heap import, inside a scoped region — [region] is the sole candidate
Region::scoped([region]() -> {
    let n = make_node(1);  // infers [region] ✓
});

// 3. Heap imported, inside a scoped region — two candidates → explicit required
use Heap;
Region::scoped([region]() -> {
    let n = make_node(1);           // error: ambiguous — Heap or region?
    let n = make_node[region](1);   // @[region] Node ✓
    let n = make_node[Heap](1);     // @[Heap] Node ✓ — visible escape from the arena
});
```

Scenario 2 is the key improvement over a prelude-resident model: arena-heavy code that
does not import `Heap` gets clean single-candidate inference inside scoped blocks with no
ambiguity errors. Scenario 3 preserves the forced acknowledgement that a `Heap` allocation
escapes the arena — but only when the programmer has explicitly opted `Heap` into the
candidate set.

> **Scope of inference.** These rules fill *region* arguments only — the region analogue of
> type-argument inference. Generalising `[…]` to arbitrary context parameters is out of
> scope.

---

## 3. What the programmer actually writes

With both rules active, the region annotation surface is minimal. Below is a full
single-region API written without elision on the left and with elision on the right:

```
── without elision (RFC-0063 explicit) ──────────────────────────┐  ── with elision ──────────────────────────────────────────────┐
                                                                  │                                                               │
struct Header[r] {                                                │  struct Header[r] {                                           │
    name:  @[r] String,                                           │      name:  @String,                                         │
    value: @[r] String,                                           │      value: @String,                                         │
}                                                                 │  }                                                            │
                                                                  │                                                               │
fun parse_header[region](                                         │  fun parse_header[region](                                    │
    line: String,                                                 │      line: String,                                            │
) -> Perhaps<@[region] Header> {                                  │  ) -> Perhaps<@Header> {                                      │
    @[region] Header { name: …, value: … }                        │      @Header { name: …, value: … }                           │
}                                                                 │  }                                                            │
                                                                  │                                                               │
fun find_header[r](                                               │  fun find_header[r](                                          │
    req:  &[r] Request,                                           │      req:  &[r] Request,                                      │
    name: String,                                                 │      name: String,                                            │
) -> Perhaps<@[r] String>                                         │  ) -> Perhaps<@String>                                        │
```

The `[r]` bracket channel is still written on the function and struct — that is the
declaration that a region exists. Elision applies only to `@`-bearing positions inside
field and parameter types. Region-tagged borrows (`&[r] T`) are written explicitly in all
positions; a bare `&T` always means a plain borrow with no region information.

Static handles (`[Heap]`, `[LocalHeap]`) are always accessible by name and are never
subject to elision. They participate in inference only when explicitly imported (§2).

Region tags surface in written code in exactly three places:

1. **function and type declarations** — `[region]` in the bracket channel;
2. **multi-region code** — all tags named, `Outlives` bounds written;
3. **static handle annotations and explicit region borrows** — `@[Heap] T`, `&[r] T`,
   `&[Heap] T`.

---

## 4. Unresolved questions

1. **Closures and `[region]() -> {}`.** The `Region::scoped` callback uses the bracket
   channel on a closure literal; the exact grammar for region parameters on closure types and
   values is left to the closure RFC (RFC-0050).

---

## References

- RFC-0063 (Region Handles) — core system this RFC builds on.
- RFC-0050 (Closure Capture Lists) — closure grammar for `[region]() -> {}`.
