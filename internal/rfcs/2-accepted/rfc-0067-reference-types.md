---
id: rfc-0067
title: "Lifetime Anchors and Allocator-Pointer References"
date: '2026-06-28'
updated: '2026-07-10'
status: accepted
---

> **Status — under review.** Rewritten 2026-07-05 for the split model. Split again
> 2026-07-07: the plain `&T` / `&mut T` rename and auto-deref (the original RFC-0067's
> §1/§3/§4/§7) had no dependency on affine types, the borrow checker, or allocators, and
> has been accepted separately as **RFC-0067a** and sequenced into Cluster A. What remains
> here — lifetime anchors, allocator-pointer (`@a T`) auto-deref and coercion, and move-out
> — genuinely needs both: anchors are borrow-checker core (scope/liveness tracking is what
> "is anchor `r` still valid" means), and the allocator-pointer sections need `@a T` to
> exist (RFC-0063). This stays Phase 3 in `reports/implementation/roadmap-2026-07-07.md`,
> unchanged from before the split.
>
> Depends on RFC-0067a (base `&T` / `&mut T`, which this RFC extends with anchors —
> no further reference-type syntax to invent), RFC-0063 (Allocator Handles), and RFC-0071
> (Ownership and Move Semantics). Amends RFC-0044 (Explicit Receiver Semantics).
>
> Note on a related but distinct independence claim: `reports/strategy/strategic-overview-2026-07-06.md`
> observes that "the reference-type core (ordinary borrows, lifetime-anchor elision, RFC-0067's
> own body minus §5) ... don't reference `Alloc` at all." That is a true and useful claim about
> independence from *allocators* specifically — lifetime anchors don't need `@a T` to make sense.
> It is not the same claim as this split makes, which is independence from the *borrow checker*.
> Lifetime anchors need the borrow checker's scope/liveness machinery even though they don't need
> `Alloc` — which is exactly why anchors (§1 below) stay in this document rather than moving to
> RFC-0067a alongside the allocator-independent, borrow-checker-independent rename.
>
> **Updated 2026-07-06:** §2's coercion paragraph (originally §5) says explicitly why it is
> safe only for borrows, not owned values, cross-referencing RFC-0066 §3a and RFC-0063 §4.

> **Status — accepted (2026-07-10).** Phase 0 ratification sweep: split model consistency-checked (RFC-0063 sec9 items 1/2/5 synced with roadmap-2026-07-07 Phase 0 decision; RFC-0066/0068 stale titles fixed); sweeping the cluster from under-review to accepted per reports/implementation/roadmap-2026-07-07.md Phase 0.

## Summary

Specify **lifetime anchors** — the compile-time names that bound a borrow's validity scope —
on top of the `&T` / `&mut T` reference types from RFC-0067a. A borrow `&r T` carries anchor
`r`, a binding whose scope determines how long the borrow remains valid. Anchors are separate
from allocators: the allocator says where a value lives; the lifetime anchor says how long a
particular borrow of it is valid.

This RFC also specifies how allocator pointers (`@a T`, RFC-0063) participate in auto-deref and
coerce to plain references, and how move-out from `@a T` is expressed.

---

## Motivation

RFC-0043's `*T` / `*mut T` model (now RFC-0067a's `&T` / `&mut T`) accumulates friction when
combined with the allocator system. The extraction examples in RFC-0066 show it most clearly:

```metel
// clone extraction — pre-auto-deref
let copy: @Heap Config = (*(&src)).clone();
```

Two visible `*` operations obscure a conceptually simple "borrow this value and clone it."
The same sigil marked allocator-pointer move-out, regular-pointer dereference, and the type
notation for non-owning references, all at once.

Reference types and auto-deref resolve this:

```metel
// clone extraction — with reference types and allocator auto-deref
let copy: @Heap Config = src.clone();
```

Lifetime anchors solve a separate problem: naming how long a borrow is valid. The pre-split
unified `Region` model tried to answer this using the allocator itself as the lifetime; that
broke once a value could be moved out of or dropped from a region while the region continued
holding other allocations (RFC-0066), which is why anchors are their own concept here rather
than folded back into `@a`.

---

## 1. Lifetime anchors

Every borrow carries a **lifetime anchor** — the name of a binding whose scope bounds the
borrow's validity. The anchor appears directly after `&` in type position:

```metel
&r T       // immutable borrow of T; valid while binding r is alive
&r mut T   // mutable borrow of T; valid while binding r is alive
```

The anchor groups with `&`; `mut` qualifies the reference after it. A borrow `&r T` does not
know or care whether `T` was allocated in allocator `r` — `r` is a binding name, and the
borrow is valid for exactly as long as `r` is in scope.

**Anchors are type-level only.** In expression position, write `&val` and `&mut val` (RFC-0067a
§2). The anchor is inferred from the expected type; explicit anchors never appear on
expressions. This matches Rust's design: lifetimes annotate types, not terms.

**Declaration.** When a function needs to name an anchor explicitly (because elision is
ambiguous), it declares it in the type-parameter channel `<>` with the `&` prefix:

```metel
fun longest<&r>(&r Str, &r Str) -> &r Str { ... }
```

Elision rules (RFC-0065 §2) cover the common cases; `<&r>` declarations appear only when the
relationship is ambiguous.

**Lifetime ordering bounds.** When two anchors have no structural relationship the borrow
checker can derive, a `: &s` bound in the `<>` declaration expresses that the right-hand side
is the shorter-lived anchor:

```metel
fun pick<&s, &t: &s>(&s Str, &t Str) -> &t Str { ... }
// &t: &s means t outlives s; t is the shorter-lived anchor
```

---

## 2. Allocator pointer access

`@a T` participates in auto-deref (RFC-0067a §3). It is treated as a one-level owner over `T`:
field access and method dispatch deref through the allocator pointer transparently.

```metel
let node = @a Node { val: 1, next: null };

let v = node.val;      // auto-deref: @a Node → Node, read field
node.val = 2;          // auto-deref: @a Node → Node, write field
node.method(args);     // auto-deref: dispatches on Node
```

**Explicit borrows** through an allocator pointer produce an anchor-carrying reference. The
anchor is the binding being borrowed:

```metel
let r: &node T   = &node;      // shared borrow; anchor = `node` binding
let m: &node mut T = &mut node; // exclusive borrow; anchor = `node` binding
```

In practice the anchor is almost always elided and inferred from context. The explicit form
appears in type signatures when the anchor must be named.

**Coercion.** A borrow of `@a T` — written `&node` where `node: @a T` — coerces to plain `&T`
in positions where the allocator tag and anchor are not needed. The coercion is implicit at
function arguments, return expressions, and annotated `let` bindings.

**This coercion is sound precisely because it applies to borrows, not owned values.** `&node`
never had move/ownership rights over the allocation in the first place — it is a temporary
loan — so dropping the tag from the *borrow's* type discards nothing the reference held. This
does **not** extend to `node` itself: passing the owned `node` (no `&`) to a plain, `@`-free
`T` parameter is a completely different, and much more consequential, operation — it would
require extraction (move-out, RFC-0066 §3), which is lossy (the allocator slot is vacated) and
sometimes illegal (`T: Drop` on a bulk-deallocating allocator, RFC-0066 §2.2.3). RFC-0066 §3a
specifies that this never happens implicitly, by analogy with this section's borrow coercion —
the two look similar at a glance (both "drop the tag") but the owned case has no free
equivalent, which is why it is opt-in (explicit ascription) rather than automatic. RFC-0063 §4's
tag-only parameter is the mechanism for passing an *owned* `@a T` through generic code without
paying extraction's cost — see that section for the counterpart to this one.

---

## 3. Move-out from `@a T`

Move-out is the consuming operation that extracts `T` from `@a T`, destroying the allocator
pointer. Since there is no `*ptr` any more (RFC-0067a removed the explicit dereference
operator), move-out is expressed via type context:

**Type-directed** — when a `let` binding or return position declares type `T` and the source
is `@a T`, the compiler performs move-out implicitly:

```metel
let ptr = @a Node { val: 1 };
let node: Node = ptr;    // move-out: ptr consumed, Node returned
```

**Type ascription** — drives move-out in any expression position:

```metel
let node = ptr: Node;       // ascription in let — ptr consumed
process(ptr: Node);         // ascription at call site — ptr consumed
```

Move-out semantics and constraints (heap always safe, scoped allocators require `T: !Drop` for
bulk-deallocating kinds) are specified in RFC-0066.

---

## Unresolved questions

None.

**Closed — borrow coercion depth.** A borrow of `@a T` coerces to `&T` at coercion sites
(function arguments, return expressions, annotated `let` bindings). No coercion is inserted in
unannotated expression positions where no expected type is known. Matches Rust's deref-coercion
rules.

---

## References

- RFC-0067a (Reference Types) — `&T` / `&mut T`, address-of, auto-deref, and the RFC-0043
  supersession this RFC builds on. Split off 2026-07-07 as the allocator/borrow-checker
  independent slice of the original RFC-0067.
- RFC-0043 (Regular Pointers) — superseded by RFC-0067a.
- RFC-0044 (Explicit Receiver Semantics) — `&self` / `&mut self` receivers.
- RFC-0063 (Allocator Handles) — `@a T`; allocator-tagged owned pointers this RFC borrows
  from. §4's tag-only parameter is the owned-value counterpart to this RFC's borrow coercion
  (§2).
- RFC-0065 (Allocator Ergonomics) — elision rules for lifetime anchors and allocator tags.
- RFC-0066 (Allocated Value Extraction) — move-out and borrow forms updated by §3 of this RFC.
