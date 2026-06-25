---
id: rfc-0064
title: "Structured Fork-Join Parallelism"
date: '2026-06-25'
---

> **Status — draft, design-only.** This RFC specifies the `||` structured fork-join
> combinator and its interaction with region pointers. It depends on RFC-0063 (Region
> Handles) for the region tag and sendability rules.

## Summary

Scoped region pointers (`@[region] T`) are non-sendable — a spawned fiber may outlive the
region that backs them. **Structured fork-join** is the one construct that safely escapes
this restriction: the `||` combinator guarantees both branches complete before the
expression returns, so borrows into a scoped region handed to each branch cannot outlive
the region's scope.

Safety requires no separation calculus. The region tag that already bounds a pointer's
lifetime doubles as a **disjointness witness**: two pointers with distinct tags provably
cannot alias, so parallel branches that each hold a borrow into a different sub-tree are
race-free by type.

---

## Motivation

The natural parallelism primitive — `spawn` — cannot parallelize over scoped region data:

```metel
Region::scoped(fun[region: &mut Region]() {
    let t = build(…);                     // @[region] Node — non-sendable
    spawn(fun() { process(&t.left); });   // error: @[region] T is not sendable
});
```

Copying to `Heap` before spawning defeats the point of the arena. A structured join avoids
the problem by keeping both branches lexically inside the region's scope, so the soundness
argument reduces to *scope containment* rather than *send safety*.

---

## 1. The `||` combinator

`||` is a sealed library combinator with signature:

```metel
fun join<A, B>(a: fun() -> A, b: fun() -> B) -> (A, B)
```

with `e₁ || e₂` as syntactic sugar for `join(fun() { e₁ }, fun() { e₂ })`.

**Guarantee:** both closures complete before `join` returns. Neither closure can be
`spawn`ed independently; the combinator is the only entry point.

Because both branches finish before the expression returns, any borrow handed to a branch
cannot outlive its source — the join is a hard synchronisation point that is always inside
the enclosing scope.

---

## 2. The tag as a disjointness witness

Two pointers with distinct region tags cannot alias:

```
[r1] ∩ [r2] = ∅   (regions are disjoint address ranges by construction)
```

This is not an assertion to verify at runtime — it follows from the allocation model: each
region is an independent bump arena, and the tag names the arena. Distinct tags mean
distinct arenas, which means distinct memory.

Combined with the exclusivity of `&mut`, two parallel branches are safe iff each branch
independently type-checks against the ordinary borrow rules:

```metel
Region::scoped(fun[region: &mut Region]() {
    let t = build(…);                             // @[region] Node
    let (ls, rs) = sum(&t.left) || sum(&t.right); // &Node borrows, disjoint sub-trees
});                                               // both branches done before region drops
```

`sum` takes a shared borrow `&Node`. Both calls hold borrows simultaneously, which is
sound because shared borrows are non-exclusive — any number of `&T` borrows may coexist.
An `&mut` borrow to the same node in both branches would be rejected by the ordinary
exclusivity rule, catching the race statically.

---

## 3. What the programmer does not need to write

No separation logic annotations, no proof obligations, no effect systems. The tag **is**
the proof: the compiler checks that each branch type-checks in isolation, and the disjoint-
tag guarantee ensures the two isolated checks compose into a sound parallel execution.

The fork-join safety argument has three components, all already enforced before this RFC
adds anything:

1. **Scope containment** — `||` is always inside the region's scope; the join is the sync
   point (§1).
2. **Disjoint memory** — distinct region tags imply disjoint arenas (§2).
3. **Borrow exclusivity** — `&mut` is already exclusive; two branches cannot both hold a
   mutable borrow to the same value (RFC-0063 §2).

---

## 4. Interaction with `spawn`

`spawn` and `||` are not interchangeable. `spawn` detaches: the spawned fiber may outlive
the call site, so it cannot hold borrows into a scoped region. `||` is structured: neither
branch detaches, so borrows are sound.

The distinction is enforced by the sendability rule (RFC-0063 §6): `spawn` requires its
closure to be sendable, which excludes any closure that captures `@[region] T` or a borrow
into one. `||` does not require sendability — it requires only that both closures finish
before the combinator returns, which is a structural guarantee, not a type-level one.

---

## 5. Unresolved questions

1. **Nesting.** `||` inside `||` is the natural way to build a parallel tree traversal.
   The type rules compose straightforwardly, but the runtime scheduling (work-stealing vs.
   fixed thread pool) is left to the implementation. This RFC takes no position.

2. **Error handling across branches.** If one branch panics, what happens to the other?
   The join must not return until both branches have either completed or been cancelled.
   The exact semantics (propagate first panic, collect all panics, etc.) are deferred to
   the panic/error RFC.

3. **`||` on non-region data.** Nothing prevents using `||` with `@[Heap] T` or plain
   values — it is a general combinator. This RFC focuses on the region-pointer case because
   that is where the disjointness witness does work; the general case has no new safety
   obligations.

---

## References

- RFC-0063 (Region Handles) — region tags, sendability, borrow capabilities.
- `docs/reports/memory-model/capability-region-synthesis.md` — original synthesis.
