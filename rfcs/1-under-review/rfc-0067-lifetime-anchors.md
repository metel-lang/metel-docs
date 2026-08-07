---
id: rfc-0067
title: "Lifetime Anchors"
date: '2026-06-28'
updated: '2026-08-02'
status: under-review
target: v0.15.0
---

> ## ⚠ Implementing this RFC carries an inherited obligation
>
> *Added 2026-08-01, from RFC-0122 §2d.*
>
> **A temporary language restriction exists solely because this RFC is unimplemented,
> and implementing it is the event that removes the restriction.** Reference-typed
> struct and enum fields (`struct Holder { r: &P }`) are rejected, because rejecting a
> stored reference that outlives its referent requires relating **two independent
> lifetimes**, and no scope-based rule can do that — an anchor is exactly the capability
> that can. Rather than block all borrow checking on this RFC, RFC-0122 bans stored
> references and checks local borrows without them.
>
> **So implementing anchors must also lift that ban**, and lifting it is more than
> deleting a check: RFC-0122 §2b.2's outlives rule was *specified* scope-based on the
> assumption stored references do not exist, and admitting them means revisiting that
> specification. Both halves are tracked as **metel-core#274**. See RFC-0122 §2d for the
> full reasoning; this pointer exists so the obligation surfaces here rather than
> depending on someone remembering it.

> ## Targeted at v0.15.0 — and what has to happen first
>
> *Set 2026-08-02 by operator decision. Recorded here with its critical path because a
> target on an RFC that is `1-under-review` with five open questions is a plan, not a
> schedule, and stating only the date would hide that.*
>
> **The chain, each link genuinely blocking the next:**
>
> 1. **RFC-0122 (Borrow Checking) must settle first — it is targeted at v0.14.0**, the
>    release immediately before this one, which is what makes v0.15.0 reachable at all. It
>    is `1-under-review` with three blocking gaps of its own (§2b) — the outlives rule is unspecified, and this RFC's
>    §1 was designed before any checker existed. Anchors *name* a validity scope; until
>    RFC-0122 fixes what a validity scope is, question 1 below cannot be answered.
> 2. **This RFC's five open questions resolve**, chiefly whether §1's lexical framing
>    ("valid for exactly as long as `r` is in scope") survives RFC-0122 §2.2's NLL
>    last-use liveness. That is a real design question, not editing.
> 3. **`2-accepted` → `3-integrated`**, which per `public/rfcs/PROCESS.md` is also the
>    first point an implementation issue may be filed — so **no tracked implementation
>    work exists for this RFC yet, deliberately**, and none should be created before then.
> 4. **Implementation, in v0.15.0**, which also discharges **metel-core#274** — the
>    temporary reference-typed-struct-field ban, milestoned to v0.15.0 alongside this,
>    exists solely because this RFC is unimplemented and is lifted by implementing it.
>
> **The one tracked artifact carrying the v0.15.0 milestone today is #274**, not this
> RFC, because #274 is a concrete interpreter change and this is still a design document.
> If v0.15.0 arrives and #274 is still open, that is the signal that this chain stalled.

> **Status — under review.** Rewritten 2026-07-05 for the split model. Split again
> 2026-07-07: the plain `&T` / `&var T` rename and auto-deref (the original RFC-0067's
> §1/§3/§4/§7) had no dependency on affine types, the borrow checker, or allocators, and
> has been accepted separately as **RFC-0067a** and sequenced into Cluster A. What remains
> here — lifetime anchors, allocator-pointer (`@a T`) auto-deref and coercion, and move-out
> — genuinely needs both: anchors are borrow-checker core (scope/liveness tracking is what
> "is anchor `r` still valid" means), and the allocator-pointer sections need `@a T` to
> exist (RFC-0063). This stays Phase 3 in `reports/implementation/roadmap-2026-07-07.md`,
> unchanged from before the split.
>
> **Renamed 2026-07-10** from "Lifetime Anchors and Allocator-Pointer References" to
> "Lifetime Anchors" — the RFC's own content is split roughly 1/3 anchors (§1) to 2/3
> allocator-pointer interaction (§2-3), but "Allocator-Pointer References" duplicated
> RFC-0063/RFC-0066's own naming rather than describing what's distinctive about this
> RFC specifically. File renamed from `rfc-0067-reference-types.md` to
> `rfc-0067-lifetime-anchors.md` to match.
>
> Depends on RFC-0067a (base `&T` / `&var T`, which this RFC extends with anchors —
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

> **Dependency corrected 2026-07-24: this RFC depends on RFC-0122 (Borrow Checking), not
> the reverse.** RFC-0122's first draft described itself as supplying rules "for RFC-0067's
> anchors," which had the relation backwards.
>
> `&r T` names the scope that bounds a borrow's validity. **That name denotes nothing
> without a checker that enforces it**, whereas a checker needs no user-written anchors to
> do most of its work: shared-XOR-exclusive is a question about which borrows coexist at a
> program point and never consults a validity *name*, and local outlives checking is
> scope-based. This RFC's own text agrees — `<&r>` declarations "appear only when the
> relationship is ambiguous," with elision (RFC-0065 §2) covering the common cases. A
> disambiguator for the minority case cannot be the foundation.
>
> **Consequence: this RFC should be re-examined against RFC-0122's rules before it is
> implemented, rather than treated as constraining them.** It was accepted 2026-06-28,
> before any checker was specified, so its anchor model was designed against an absence.
>
> ~~**Also stale, found in the same pass:** nine occurrences of `&var` / `&r var`,
> predating RFC-0098…~~ **Withdrawn 2026-08-02 — this was corrected and the note outlived
> it.** The docs-wide `mut`→`var` sweep (metel-core#604, 2026-08-01) converted every one;
> this file now contains ten `&var` occurrences and **zero** `&mut`, i.e. the current
> spelling throughout. RFC-0122's header repeated the claim and is corrected in the same
> pass. *Recorded rather than deleted because of how it survived: a later reader verified
> the **count** (nine → ten) without re-checking the **assertion** the count was attached
> to, which is the exact failure `public/rfcs/PROCESS.md`'s verification rule is meant
> to prevent.*

> **Status — under review (2026-08-02).** Accepted 2026-06-28 before any borrow checker was specified; its own header records that the anchor model was 'designed against an absence' and should be re-examined against RFC-0122's rules before implementation. RFC-0122 now specifies NLL liveness, per-field granularity, T0020 diagnostics, and a stored-reference ban whose removal this RFC triggers (#274) — none checked against SS1. 'Unresolved questions: None' replaced with five real ones.

## Summary

Specify **lifetime anchors** — the compile-time names that bound a borrow's validity scope —
on top of the `&T` / `&var T` reference types from RFC-0067a. A borrow `&r T` carries anchor
`r`, a binding whose scope determines how long the borrow remains valid. Anchors are separate
from allocators: the allocator says where a value lives; the lifetime anchor says how long a
particular borrow of it is valid.

This RFC also specifies how allocator pointers (`@a T`, RFC-0063) participate in auto-deref and
coerce to plain references, and how move-out from `@a T` is expressed.

---

## Motivation

RFC-0043's `*T` / `*mut T` model (now RFC-0067a's `&T` / `&var T`) accumulates friction when
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
&r var T   // mutable borrow of T; valid while binding r is alive
```

The anchor groups with `&`; `var` qualifies the reference after it. A borrow `&r T` does not
know or care whether `T` was allocated in allocator `r` — `r` is a binding name, and the
borrow is valid for exactly as long as `r` is in scope.

**Anchors are type-level only.** In expression position, write `&val` and `&var val` (RFC-0067a
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
let node = @a Node { val = 1, next = Perhaps::None };

let v = node.val;      // auto-deref: @a Node → Node, read field
node.val = 2;          // auto-deref: @a Node → Node, write field
node.method(args);     // auto-deref: dispatches on Node
```

**Explicit borrows** through an allocator pointer produce an anchor-carrying reference. The
anchor is the binding being borrowed:

```metel
let r: &node T   = &node;      // shared borrow; anchor = `node` binding
let m: &node var T = &var node; // exclusive borrow; anchor = `node` binding
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
let ptr = @a Node { val = 1 };
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

*Rewritten 2026-08-02. This section previously read "None," which was true when written
(2026-06-28) and false from 2026-07-24 onward, when RFC-0122 first specified a checker.
An anchor names a borrow's validity scope; **what a validity scope is, and how it is
computed, is now decided by RFC-0122 rather than assumed by this RFC** — and none of
those decisions existed when §1 was designed. Every question below is a place where §1
made an assumption that a specified checker has since either settled differently or not
yet settled at all.*

**1. Does §1's anchor model survive NLL liveness?** RFC-0122 §2.2 specifies borrows live
from creation to **last use**, not to end of scope. §1 defines an anchor as "a binding
whose scope bounds the borrow's validity" and says a borrow "is valid for exactly as long
as `r` is in scope" — which is a **lexical** statement. Under NLL a borrow can end well
before its anchor's scope does. Either the anchor is a *bound* on validity rather than an
equality (probably right, and §1's wording needs changing), or the two models genuinely
disagree. **This is the load-bearing question; the others are downstream of it.**

**2. What granularity does an anchor bind at?** RFC-0122 §2.1 settled conflict detection
as per-field for statically-named fields and whole-value through a dynamic index. §1 is
silent — `&r T` names a binding, not a place. Whether `&r p.x` and `&r p.y` are one anchor
or two is unspecified and matters for exactly the disjoint-field borrows RFC-0109 wants.

**3. Do anchors have anything to say at all, given the stored-reference ban?** RFC-0122
§2d bans reference-typed struct fields **specifically because** relating two independent
lifetimes needs anchors, and marks implementing this RFC as the event that lifts the ban
(metel-core#274). So this RFC's most concrete consumer is a restriction that does not yet
exist. §1 was written with no such consumer in view, and should be re-read asking whether
its `<&r>` declaration form is what #274's lifting actually needs.

**4. Is `<&r>` still the right declaration surface?** It does not parse today
(`[P0001] expected generic_param`, verified 2026-08-02) so nothing constrains it yet. But
RFC-0122's diagnostics (§2.5, `T0020`) name *bindings and their extending uses*, never an
abstract region — if anchors are the user-facing spelling of the same concept, the two
notations should be checked for agreement before either ships.

**5. Does §1's lifetime-ordering bound (`<&s, &t: &s>`) have a checker to enforce it?**
RFC-0122 specifies shared-XOR-exclusive and an outlives rule, but §2b.2 records that the
outlives rule is *itself* unspecified. An ordering bound between two anchors is strictly
more than either. Nothing in the corpus currently computes it.

---

**Closed — borrow coercion depth.** A borrow of `@a T` coerces to `&T` at coercion sites
(function arguments, return expressions, annotated `let` bindings). No coercion is inserted in
unannotated expression positions where no expected type is known. Matches Rust's deref-coercion
rules.

---

## References

- RFC-0067a (Reference Types) — `&T` / `&var T`, address-of, auto-deref, and the RFC-0043
  supersession this RFC builds on. Split off 2026-07-07 as the allocator/borrow-checker
  independent slice of the original RFC-0067.
- RFC-0043 (Regular Pointers) — superseded by RFC-0067a.
- RFC-0044 (Explicit Receiver Semantics) — `&self` / `&var self` receivers.
- RFC-0063 (Allocator Handles) — `@a T`; allocator-tagged owned pointers this RFC borrows
  from. §4's tag-only parameter is the owned-value counterpart to this RFC's borrow coercion
  (§2).
- RFC-0065 (Allocator Ergonomics) — elision rules for lifetime anchors and allocator tags.
- RFC-0066 (Allocated Value Extraction) — move-out and borrow forms updated by §3 of this RFC.
