---
id: rfc-0124
title: "Sequence Types: Fixed Arrays, Slices, and the Growable List"
date: '2026-07-25'
status: draft
target:
updated: '2026-08-03'
---

> **Marked temporary and incomplete, 2026-08-03.** Nothing in the RFC record before this
> note stated, in so many words, that Metel's current three-way sequence-type split
> (`[T; N]` / `T[]` / `List<T>`) is temporary or incomplete — the closest is this RFC
> itself, still `draft`, with no `target`. This note exists to make that explicit and
> durably tracked, independent of whether or when this RFC is ever accepted.
> **`List<T>` today is 100% native/Rust-backed**: every primitive operation in
> `stdlib/core.mtl` (`new`, `push`, `pop`, `get`, `set`, `as_slice`) is
> `native(@std.core.list_*)`, backed by `Value::Array(Rc<RefCell<Vec<Value>>>)` in the
> evaluator (`src/evaluator/mod.rs`, `src/evaluator/builtins.rs`) — zero Metel-source
> implementation of any kind, not even the growth logic. This is not asserted here as the
> intended final shape; it is recorded because nothing in the accepted design record yet
> supplies what a from-Metel `List` would need to exist instead. See Open Question 6
> below, added the same day, for exactly what is missing and in what order it would need
> to be solved. **This is deliberately not being resolved or shipped in v0.12.0** — no
> `target` is set on this RFC, and none should be inferred from RFC-0126 or anything else
> shipping nearby. The only thing this note commits to is that the gap is now named and
> cited in one place, rather than silently carried forward as an unstated implementation
> detail. Read together with the corrected RFC-0067 citation below (References) and
> RFC-0126's own 2026-08-03 correction note.

> **Narrowed 2026-07-27.** The role assignment this RFC argued for — `T[]` is a non-owning,
> immutable, `Copy` borrowed view — turned out to already be settled (RFC-0054 said so in
> `4-implemented`; nothing in this RFC's own prior-art survey found a live alternative), so
> it was split out as **RFC-0126** rather than left waiting on the questions below. This RFC
> now covers only what RFC-0126 does not decide: a mutable-slice spelling, the exact RFC-0067
> lifetime-anchor dependency, `[T; N]` const generics, evaluator representation, and release
> sequencing. Read RFC-0126 first — this document assumes its decision.

## Summary

Metel has three sequence types — `[T; N]`, `T[]`, and `List<T>`. RFC-0126 settled the role
assignment (`T[]` is a borrowed view, `Copy`, produced only by borrowing; array literals type
as `[T; N]`). What that RFC left open, and what this one is now scoped to:

| open question | status here |
|---|---|
| Is there a mutable slice, and how is it spelled? | open — §Open Questions 1 |
| Exact dependency on RFC-0067's lifetime anchors | open — §Open Questions 2 |
| Does `[T; N]: Copy` need const generics to leave the typechecker's hardcoded case (#263)? | open — §Open Questions 3 |
| `Value::Array`'s evaluator representation | open — §Open Questions 4 |
| Release sequencing against #579 and #267 | open — §Open Questions 5 |
| Can `List<T>` ever be built from `[T; N]`/`T[]` alone, or is native backing structurally permanent? | open, deliberately unresolved here — §Open Questions 6 |

---

## Motivation

RFC-0126 already argues the case for the view/`Copy` role assignment and the measured
migration cost — that material is not repeated here. What remains is genuinely undecided,
and none of it blocks accepting RFC-0126 on its own: a mutable-slice spelling can be added
later without revisiting whether `T[]` is `Copy`; the RFC-0067 dependency affects *when*
slices can be proven sound, not *what* they are; `[T; N]`'s const-generic story is orthogonal
to `T[]` entirely; representation is an evaluator detail; and sequencing is scheduling.

**RFC-0122 has an open question about "observability on a cloning evaluator."** Same root
cause as this RFC's neighbourhood, reached from the borrow checker's side — RFC-0126 landing
narrows it, but the lifetime-anchor dependency below (Open Question 2) is what actually
resolves it.

---

## Prior art (extended from RFC-0126)

RFC-0126 §Prior art already established that every language in Metel's neighbourhood
converges on fixed/view/growable, with growable living in the library. What that table
didn't ask is *what the growable one is built on* — extending it with that column is
directly relevant to Open Question 6 below:

| | fixed | view | growable | what the growable one is built on |
|---|---|---|---|---|
| **Rust** | `[T; N]` value, `Copy` if `T: Copy` | `&[T]` borrowed fat pointer, `Copy` | `Vec<T>` — std, owns, affine, `Drop` | `RawVec<T, A>` — capacity/growth logic factored out of `Vec` itself, generic over an `Allocator` type parameter (`Global` by default, but a real, substitutable parameter, not hidden) |
| **Zig** | `[N]T` value | `[]T` fat pointer view | `std.ArrayList(T)` — std | holds an explicit `Allocator` handle, set at `.init(allocator)` and threaded through every growth call (the exact allocator-storage shape has varied across Zig versions — flagging this as the one detail here not independently re-verified against a specific release; the structural point, an explicit allocator parameter rather than an implicit global one, holds either way) |
| **C++** | `T[N]`, `std::array` | `std::span` (C++20) | `std::vector<T, Allocator = std::allocator<T>>` | allocator-aware since C++98 — the allocator is the vector's second template parameter, defaulted but always present, and every growth operation is specified in terms of `Allocator::allocate`/`deallocate` |

**The pattern that matters for Open Question 6:** in every one of these, the growable
container's *storage growth* is factored out into a distinct, explicit allocator
abstraction — never resolved by the fixed-size or view types themselves, and never
implicit-global-only by default. This is the same shape RFC-0063 was reaching for (the
`Alloc` aspect, `@a T`) — but, checked directly, RFC-0063 only specifies single-value
allocation, never the batch/geometric-growth allocation this table shows every comparable
`List`-equivalent actually needs. That gap is Open Question 6(c) below.

---

## Open Questions

1. **Is there a mutable slice, and how is it spelled?** `&var`-flavoured, or does mutation
   require going through `List<T>`? RFC-0045's `&var`-on-field-paths and RFC-0110's explicit
   dereference are the neighbouring decisions. RFC-0126 makes `T[]` immutable outright; this
   question is only about whether a *separate* mutable-view type is worth adding, not about
   reopening that immutability.
2. **What is the relationship to RFC-0067's lifetime anchors?** A slice is the first type
   whose validity is scoped to another value's lifetime. This RFC probably *depends* on
   RFC-0067 rather than merely touching it — confirming that is a precondition for this
   RFC's own acceptance, independent of RFC-0126, which does not require it (a `Copy` view's
   validity story can be as simple as "elaborated code never outlives the loop that borrowed
   it" until this question is answered).
3. **Does `[T; N]` need const-generic `N`?** Today only literal arities parse — measured
   2026-07-25, `extend<T: Copy> [T; 2]: Copy;` works and `[T; N]` does not. Without const
   generics, "fixed arrays are `Copy` when their elements are" cannot be written in stdlib
   and stays hardcoded (#263), the same situation #581 and RFC-0061 describe for structural
   impls. Unaffected by RFC-0126, which changes `T[]`'s role, not `[T; N]`'s.
4. **Is `Value::Array`'s `Rc<RefCell<Vec>>` representation retained?** A borrowed slice needs
   no refcounting. Keeping it may simplify the tree-walking evaluator, at the cost of
   representing something the type system would no longer admit once RFC-0126 lands.
5. **Which release, and in what order against #579/#267?** RFC-0126's migration argues for
   landing early (it unblocks six of #267's fixtures directly); the dependency on RFC-0067
   (Open Question 2 above) argues for later, at least for a mutable-slice variant. The
   sequencing decision that matters is against **#579**, since move checking is what would
   otherwise bake in the pre-RFC-0126 model permanently.
6. **Can `List<T>` ever be implemented in Metel source from `[T; N]` and `T[]` alone, or
   does — and will — it always require a native primitive?** Not answerable today, and not
   close. Five gaps stack in dependency order, nearest-to-solvable first:
   a. `[T; N]`'s `N` is a compile-time literal at every layer of the stack — grammar
      (`decimal_int = @{ ASCII_DIGIT+ }`, `grammar.pest:311,328`), parser (bakes a Rust
      `u64` into the AST, `parser/mod.rs:2634-2651`), type representation
      (`Type::SizedArray(Box<Type>, u64)`, `types/mod.rs:28`). This is not an engineering
      gap that more work closes: RFC-0053 explicitly rejects runtime-sized arrays as
      "analogous to VLAs in C99, widely considered a design mistake" (rfc-0053:122), and
      even RFC-0092's future `comptime let` (itself deferred, unimplemented) would only
      make `N` a *named compile-time* constant, never a value read at runtime the way a
      growing `push` needs. **`[T; N]` can never be the buffer a growable `List` grows
      into**, regardless of how far const-generics work (Open Question 3 above) ever goes
      — that question and this one are independent, not sequential.
   b. Since RFC-0126 (`4-implemented`, target v0.12.0), `T[]` is unconditionally `Copy`,
      non-owning, and immutable *by design* — "a view is `Copy` precisely because it owns
      nothing" (rfc-0126:124-126) — structurally incapable of ever being an owning,
      growable buffer. Neither existing array type can be `List`'s backing storage.
   c. **No runtime-sized buffer-allocation primitive exists in Metel's design, even on
      paper — corrected here 2026-08-03.** RFC-0063 (Allocator Handles, `2-accepted`) is
      the RFC most often cited, including previously by this RFC's own References section
      below, as "where `List`'s buffer comes from." Checked directly: RFC-0063 never
      mentions `List` (zero matches), and its entire specified surface (`@a T`, `@a expr`,
      §1-§8) is single-value allocation only. Its own §9 items 3-4 state, in its own words,
      that the `Alloc` aspect's `alloc` method signature is **"undecided and unspecified,"**
      and that **"no lower-level primitive layer... exists"** for authoring a custom
      allocator at all — let alone one capable of the batch/geometric-growth allocation
      every comparable growable container in Metel's neighbourhood needs internally (see
      the Prior art section above). `reports/strategy/OBJECTIVES.md`'s own tracking table
      lists allocators' engineering state, project-wide, as "deliberately not started."
   d. Confirmed independently from the runtime side: no `native_array_with_capacity` /
      `alloc_n`-shaped primitive exists anywhere in `builtins.rs` today. `List::new()`
      always starts empty and grows one element at a time via Rust's own `Vec::push`
      reallocation — invisible to, and uncontrollable by, Metel source.
   e. Even with (a)-(d) solved, a from-Metel `List<T>` would need RFC-0067's lifetime
      anchors, to prove a borrowed `T[]` taken from it cannot outlive the buffer — and
      RFC-0067 is not close: reverted 2026-08-02 from `2-accepted` back to
      `1-under-review`, now blocked on RFC-0122 (Borrow Checking, itself `1-under-review`,
      target v0.14.0) settling first, then RFC-0067's own five open questions, before it
      can even reach `3-integrated`. Implementation is targeted v0.15.0 at the earliest,
      and RFC-0067's own header states that no tracked implementation work exists for it
      yet, deliberately, and none should be created before then.
   **None of (a)-(e) is this RFC's to resolve.** (a)-(b) are settled elsewhere and
   permanent; (c)-(d) have no owning RFC at all — that absence is itself the finding, not
   a citation to make; (e) is owned by RFC-0067/RFC-0122. Recorded here, left to whichever
   later RFC actually proposes a from-Metel `List`, so that "is the current three-way
   split final" has one place a future reader finds the honest answer, rather than
   reconstructing it by chasing five RFCs and two source trees.

---

## References

- **RFC-0126 (T[] as a Copy Borrowed View), `4-implemented` (#593)** — split from this RFC;
  the role assignment, prior art, and migration-cost estimate live there. Its implementation
  is concrete evidence for this RFC's own Open Question 1 below: `int_01_statistics.mtl`'s
  bubble sort needed a real algorithm rewrite, not just a retype, because no mutable-slice
  spelling exists yet.
- RFC-0054 (Standard `List<T>` Type), `4-implemented` — assigned growth to `List<T>` and
  declared `T[]` the immutable read-only view; RFC-0126 is that assignment taken at face
  value.
- RFC-0071 (Ownership and Move Semantics), `3-integrated` — §2's `Copy` rules are what
  RFC-0126 unblocks.
- RFC-0122 (Borrow Checking), `1-under-review`, target v0.14.0 — shares the
  cloning-evaluator problem; Open Question 2 here is its likely resolution path.
- RFC-0067 (Lifetime Anchors), `1-under-review` (reverted from `2-accepted` 2026-08-02;
  corrected here 2026-08-03 — this line and RFC-0126's own References both cited the
  stale status) — the likely dependency for slice validity (Open Question 2) and, more
  deeply, for Open Question 6(e). Now blocked on RFC-0122 settling first; implementation
  targeted v0.15.0, not before.
- RFC-0063 (Allocator Handles), `2-accepted` — **not, on inspection, where a `List<T>`'s
  buffer comes from** (corrected 2026-08-03: RFC-0063 never mentions `List`, and its
  specified surface is single-value allocation only; its own §9 items 3-4 call the
  `Alloc.alloc` signature "undecided and unspecified" and state no lower-level primitive
  layer exists for custom allocators at all). Cited here only as the nearest existing
  design a batch/buffer-allocation primitive would need to extend — see Open
  Question 6(c).
- Issues #579 (sequencing, Open Question 5), #581 (structural impls, related to Open
  Question 3 via the `[T; N]` blanket), #263 (`[T; N]`'s hardcoded `Copy` rule, Open
  Question 3).

---

## Decision

**Outcome:** *(pending)*
**Target:** *(set when accepted)*
