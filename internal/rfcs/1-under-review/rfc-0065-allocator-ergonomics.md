---
id: rfc-0065
title: "Allocator and Lifetime Ergonomics"
date: '2026-06-27'
updated: '2026-07-06'
---

> **Status — under review.** Rewritten 2026-07-05. The original RFC specified elision
> for the bracket channel (`@[r]` → `@`). Under the split model the bracket channel is
> gone: allocators live in the value channel `()`, lifetime anchors in the type channel
> `<>`. This RFC restates elision for both. Depends on RFC-0063 (Allocator Handles) and
> RFC-0067 (Lifetime Anchors and Allocator-Pointer References). Do not implement before RFC-0063 is resolved.
>
> **Updated 2026-07-06:** added §1a, elision for RFC-0063's new tag-only allocator
> parameters (`<@a>`). Reuses the existing single-input/self/ambiguous structure of
> §2 rather than introducing a third rule set.

## Summary

RFC-0063 and RFC-0067 specify the core allocator and lifetime-anchor systems in explicit
form. This RFC adds elision layers that make the common cases annotation-free:

1. **Allocator elision** (§1) — bare `@` without a name resolves to the unique
   in-scope allocator; two or more forces an explicit name.
2. **Tag-only allocator elision** (§1a) — the same bare `@`, when no value-channel
   allocator is in scope at all, resolves to a fresh compile-time-only tag rather
   than a type error.
3. **Lifetime anchor elision** (§2) — the common one-to-one and self-anchor cases
   need no explicit `<&r>` declaration.

All three rules share one invariant: **elision is legal only when the compiler can
determine the unique correct answer**; ambiguity is always a compile error, never a
silent choice.

---

## 1. Allocator elision

If exactly one allocator is in scope, the name after `@` may be dropped:

```metel
BumpAlloc::scoped((@a) -> {
    let x = @Node { val: 1 };     // @a Node — `a` is the sole allocator
    let y = @List::Cons { head: x, tail: @List::Nil {} };
});
```

`@` alone always implies allocation; it never means "address-of" (that is `&`). Elision
applies in both type position and expression position:

```metel
// type position
fun build_node(@a: BumpAlloc, val: i64) -> @Node { ... }
//                                          ^^^^^ == @a Node

// expression position
let node = @Node { val: 1 };   // == @a Node { val: 1 }
```

**Two or more allocators.** When two or more allocators are in scope, every `@` must be
named. The disambiguation is forced at the source level — the compiler never silently
picks one:

```metel
fun transfer<A: Alloc, B: Alloc>(@src: A, @dst: B, val: @src T) -> @dst T {
    @dst val: T   // explicit: two allocators, both must be named
}
```

**Static allocators.** `Heap` and `LocalHeap` are always accessible by name and may be
used explicitly (`@Heap expr`) anywhere. They enter the elision candidate set only when
they appear as declared parameters in the current function or scope:

```metel
fun store(@h: Heap, val: T) -> @h T {
    @val   // h is the sole allocator in scope; elides to @h T
}
```

This keeps heap allocations visible — a bare `@` inside a `BumpAlloc::scoped` block
always resolves to the scoped allocator, never to a heap that happens to be importable.

---

## 1a. Tag-only allocator elision

RFC-0063's tag-only allocator parameter (`<@a>`) has its own elision layer, reusing
§1's `@` sigil rather than introducing a new one. The two rules are distinguished by
whether a real value-channel allocator is in scope at the point `@` appears:

- If one is in scope, bare `@` names it (§1, unchanged).
- If none is in scope, bare `@` introduces a fresh, compile-time-only tag-only
  parameter instead of being a type error.

```metel
fun identity(val: @Node) -> @Node { val }
// no (@a: A) parameter anywhere in scope — @ here elides a fresh <@a>,
// exactly as if the signature had been fun identity<@a>(val: @a Node) -> @a Node
```

Relating the elided tag across multiple positions follows the same structure as
lifetime anchor elision (§2), because a tag-only parameter and a lifetime anchor are
both, mechanically, a bare compile-time name with no runtime companion:

**Single input, no relation needed.** One input position carrying the tag; the
elided output tag is that same one (compare §2 Rule 2):

```metel
fun identity(val: @Node) -> @Node { val }
```

**Two independent tag-only positions get independent tags by default** (compare §2
Rule 1) — there is no assumption that two separately-elided `@` positions refer to
the same allocator:

```metel
fun pair(a: @Node, b: @Node) -> ()
// two distinct, unrelated elided tags — nothing forces them to match
```

**Forcing two positions to share a tag requires an explicit declaration** (compare
§2 Rule 4 — ambiguity is a compile error, not a silent choice):

```metel
fun same_arena<@a>(x: @a Node, y: @a Node) -> @a Node { x }
// explicit: x, y, and the return all share tag `a`
```

**Extraction is never part of this elision.** Tag-only elision only ever produces
`@_ T` (some tag, generic or explicit) — never plain `T`. A signature with no `@` at
all (e.g. `fun identity(val: Node) -> Node`) is unaffected by this section: it
denotes a genuinely untagged parameter, and passing an `@a T` argument to it is
governed by RFC-0066 §3a (explicit ascription required; never implicit), not by
elision. The presence or absence of `@` on a plain type is exactly what distinguishes
"preserve whatever storage flows in" (`@Node`) from "requires already-extracted
ownership" (`Node`).

---

## 2. Lifetime anchor elision

Explicit `<&r>` declarations and `&r T` / `&r mut T` annotations in signatures are
needed only when the compiler cannot infer the anchor relationship. Four rules cover the
common cases:

**Rule 1 — Each elided `&` input gets a distinct fresh anchor.**

```metel
fun process(&Str, &i64) -> ()
// each & gets its own anonymous anchor; no relationship between them
```

**Rule 2 — Single input anchor propagates to output.**

```metel
fun first_char(&Str) -> &Char
// one input anchor → output uses the same anchor; no declaration needed
```

**Rule 3 — `&self` / `&mut self` wins as the output anchor.**

```metel
fun get(&self, key: &Key) -> &Val
// self anchor wins over key; return borrow valid for self's lifetime
```

**Rule 4 — Ambiguous → compile error, explicit `<&r>` required.**

```metel
fun longest(&Str, &Str) -> &Str
// two distinct anchors; which one bounds the return? compile error.

fun longest<&r>(&r Str, &r Str) -> &r Str { ... }
// explicit: both inputs and the output share the same anchor
```

These four rules together eliminate anchor annotations from the vast majority of
function signatures. Explicit `<&r>` declarations appear only at the handful of points
where the anchor relationship genuinely matters and is not derivable from structure.

---

## 3. What the programmer actually writes

With both rules active, the annotation surface is minimal. A full single-allocator API,
without elision on the left and with elision on the right:

```
── explicit (RFC-0063 + RFC-0067) ──────────────────────────────────┐  ── with elision ──────────────────────────────────────────────┐
                                                                     │                                                               │
struct Header<&a> {                                                  │  struct Header<&a> {                                          │
    name:  @a String,                                                │      name:  @String,                                         │
    value: @a String,                                                │      value: @String,                                         │
}                                                                    │  }                                                            │
                                                                     │                                                               │
fun parse_header(@a: BumpAlloc,                                      │  fun parse_header(@a: BumpAlloc,                              │
    line: String,                                                    │      line: String,                                            │
) -> Perhaps<@a Header> {                                            │  ) -> Perhaps<@Header> {                                      │
    @a Header { name: ..., value: ... }                              │      @Header { name: ..., value: ... }                        │
}                                                                    │  }                                                            │
                                                                     │                                                               │
fun find_header<&a>(@a: BumpAlloc,                                   │  fun find_header(@a: BumpAlloc,                               │
    req:  &a Request,                                                │      req:  &Request,                                          │
    name: String,                                                    │      name: String,                                            │
) -> Perhaps<&a String> { ... }                                      │  ) -> Perhaps<&String> { ... }                                │
```

The allocator parameter is still declared — that is the decision point where an
allocation strategy is named. Elision applies to the `@`-bearing type positions inside
the signature and the `&`-bearing positions that follow from it.

---

## 4. Unresolved questions

1. **Closures.** The grammar for allocator parameters on closure literals
   (`BumpAlloc::scoped((@a) -> { ... })`) is left to RFC-0050 (Closure Capture Lists).

---

## References

- RFC-0063 (Allocator Handles) — allocator parameters, `@a T`, `@a expr`, and the
  tag-only parameter form (§4) this section elides.
- RFC-0066 (Allocated Value Extraction) — §3a: why a plain, `@`-free `T` never
  implicitly accepts an `@a T` argument, which is what distinguishes it from the
  elided tag-only form here.
- RFC-0067 (Lifetime Anchors and Allocator-Pointer References) — lifetime anchors, `&r T`, `&r mut T`, anchor elision rules.
- RFC-0050 (Closure Capture Lists) — closure grammar for `(@a) -> {}`.
