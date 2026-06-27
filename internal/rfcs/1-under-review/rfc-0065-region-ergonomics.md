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
three rules that make the common single-region case annotation-free:

1. **all-position elision** — bare `@` (or `&`/`&mut` on a region-parameterised type)
   anywhere in a type resolves to the unique in-scope region;
2. **call-site deep-threading inference** — omitting the bracket argument at a call site
   auto-fills from the unique region handle in lexical scope.

Both rules share one invariant: **elision is legal only when exactly one region is in scope;
two or more forces an explicit name.**

---

## 1. All-position elision

If exactly one region is in the bracket channel, the explicit tag `[r]` may be dropped in
**any type position** — return types, parameter types, struct/enum field types, and local
variable annotations. The two surface forms that elide are:

| Sugar | Expands to | When legal |
| `@T` | `@[r] T` | Always — `@` always implies a region pointer |
| `&T` / `&mut T` | `&[r] T` / `&mut [r] T` | Only when `T` itself requires a region parameter |

### 1.1 `@` positions

Bare `@` always elides the single region tag:

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
```

### 1.2 `&` / `&mut` positions

Bare `&T` or `&mut T` elide the region tag **only when `T` is a region-parameterised
type** (i.e., `T` itself has a `[r]` bracket parameter). For primitive or region-free
types the bare `&` remains a plain borrow:

```metel
fun rope_len[r](rope: &Rope) -> u64 { … }
//                    ^^^^^  == &[r] Rope — Rope[r] requires a region ✓

fun validate[r](req: &Request, cfg: &Config) -> boolean { … }
//                   ^^^^^^^^     ^^^^^^^^
//                   &[r] Request (Request[r] ✓)   &Config — Config has no region param ✓
```

This disambiguates without extra syntax: the type itself tells the compiler whether `&T`
carries a region.

### 1.3 Two-or-more regions

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
    let mut head = region.alloc(Node { val: vals[0], next: null });
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
Region::scoped([region]() -> {
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

With both rules active, the region annotation surface is minimal. Below is a full
single-region API written without elision on the left and with elision on the right:

```
── without elision (RFC-0063 explicit) ──────────────────────────┐
                                                                  │
struct Header[r] {                  struct Header[r] {            │
    name:  @[r] String,                 name:  @String,           │
    value: @[r] String,                 value: @String,           │
}                                   }                             │
                                                                  │
fun parse_header[region](           fun parse_header[region](     │
    line: String,                       line: String,             │
) -> Perhaps<@[region] Header>      ) -> Perhaps<@Header>         │
                                                                  │
fun find_header[r](                 fun find_header[r](           │
    req:  &[r] Request,                 req:  &Request,           │
    name: String,                       name: String,             │
) -> Perhaps<@[r] String>           ) -> Perhaps<@String>         │
```

The `[r]` bracket channel is still written on the function and struct — that is the
declaration that a region exists. Only the **uses** of that region inside field and
parameter types are elided. `String` parameters and `&Config` borrows carry no region tag
because `String` is a plain value type and `Config` has no region parameter.

Static handles (`[Heap]`, `[LocalHeap]`) are always written explicitly; they are not
bracket parameters and are never subject to elision.

Region tags surface in written code in exactly three places:

1. **function and type declarations** — `[region]` in the bracket channel;
2. **multi-region code** — all tags named, `Outlives` bounds written;
3. **static handle annotations** — `@[Heap] T`, `&[Heap] T`.

---

## 4. Unresolved questions

1. **Static handle priority in inference.** When a local region handle and an ambient static
   handle (`Heap`, `LocalHeap`) are both in scope, the current rule treats them as equal
   candidates and forces an explicit bracket. An alternative is to give local handles
   priority, so that a single local `region` shadows `Heap` and `make_node(v)` inside a
   scoped block silently allocates into the arena. This restores a "defaults to arena"
   convenience but removes the forced acknowledgement that a `Heap` allocation escapes the
   scope. Decision deferred; both readings are compatible with the rule structure of §2.

2. **Closures and `[region]() -> {}`.** The `Region::scoped` callback uses the bracket
   channel on a closure literal; the exact grammar for region parameters on closure types and
   values is left to the closure RFC (RFC-0050).

---

## References

- RFC-0063 (Region Handles) — core system this RFC builds on.
- RFC-0050 (Closure Capture Lists) — closure grammar for `[region]() -> {}`.
