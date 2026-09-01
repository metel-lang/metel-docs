---
id: rfc-0124
title: "Sequence Types: Fixed Arrays, Slices, and the Growable List"
date: '2026-07-25'
status: under-review
target:
updated: '2026-09-01'
tracking: 'https://github.com/metel-lang/metel-core/issues/932'
---

> **Open Question 6 split out to RFC-0133, 2026-08-13 — and that is what unblocks this
> RFC.** This document bundled two questions with fundamentally different tractability.
> OQ1/OQ2/OQ4/OQ5 (mutable-slice spelling, the RFC-0067 dependency, `Value::Array`'s
> representation, sequencing) all become actionable at a **known point** — when RFC-0067
> settles, targeted ~v0.15.0. OQ6 (can `List<T>` be written in Metel source) has **no
> known path**: two of its five prerequisites have no owning RFC at all. Carrying both
> meant this RFC could neither be accepted — OQ2 is a stated precondition for its own
> acceptance — nor scheduled, since OQ6 had no schedulable content. It sat `0-draft` and
> untargeted from 2026-07-25 as a direct result.
>
> **This RFC's remaining scope is the slice half**, and its path is now clear rather than
> indefinite: settle OQ2's RFC-0067 dependency (the acceptance precondition), then OQ1's
> mutable-slice spelling. OQ3 is answered by citation (RFC-0132 §3); OQ4 is being decided
> in `metel-core#277`, which owns the representation change. The title's "and the Growable
> List" is retained as history — that half now lives in RFC-0133.
>
> Same split performed on RFC-0092 → RFC-0132 the same day, and on RFC-0012 →
> RFC-0092/0093/0094/0095 before that. Third instance of one pattern: a tractable piece
> trapped in a document with an intractable piece does not get worked on.

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

> **Status — under review (2026-09-01).**

## Summary

Metel has three sequence types — `[T; N]`, `T[]`, and `List<T>`. RFC-0126 settled the role
assignment (`T[]` is a borrowed view, `Copy`, produced only by borrowing; array literals type
as `[T; N]`). What that RFC left open, and what this one is now scoped to:

| open question | status here |
|---|---|
| Is there a mutable slice, and how is it spelled? | open — §Open Questions 1 |
| Exact dependency on RFC-0067's lifetime anchors | open — §Open Questions 2 |
| Does `[T; N]: Copy` need const generics to leave the typechecker's hardcoded case (#263)? | **answered 2026-08-13 by RFC-0132 §3** — §Open Questions 3 |
| `Value::Array`'s evaluator representation | open — §Open Questions 4 |
| Release sequencing against #579 and #267 | open — §Open Questions 5 |
| Can `List<T>` ever be built from `[T; N]`/`T[]` alone, or is native backing structurally permanent? | **moved to RFC-0133, 2026-08-13** — no longer this RFC's |

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
   **Answered by reference, 2026-08-13 — yes, and the mechanism now has an RFC.**
   **RFC-0132 §3** (Comptime Execution Model) specifies comptime-known non-type generic
   parameters — `extend<T: Copy, comptime N: u64> [T; N]: Copy;` — which is exactly what
   this question asks for and what RFC-0053 deferred to "a future RFC." This question
   therefore resolves by citation rather than needing design work here. Two caveats worth
   carrying: RFC-0132 §3.1 spells it `comptime N: u64`, **not** RFC-0053's guessed
   `<const N: u64>` (deliberate — Metel takes Zig's staging model, so `comptime` and
   `const` would be two words for one concept); and RFC-0132 §3.4 excludes computed
   arities (`[T; N + 1]`), which nothing in this RFC needs. See also RFC-0132 OQ5, which
   asked whether the array half of #263 is genuinely unblocked by §3 alone or also needs
   RFC-0061's structural-impl machinery — checked against the built interpreter and found
   already fixed (GitHub #581 and #239, not the stale Codeberg "#296/#353" this sentence
   itself cited until this correction), narrowing but not fully closing that risk. RFC-0132
   OQ6 is the dependency in the reverse direction: if this
   RFC revisits `[T; N]`'s role more broadly, §3 should follow that rather than precede it.
4. **Is `Value::Array`'s `Rc<RefCell<Vec>>` representation retained?** A borrowed slice needs
   no refcounting. Keeping it may simplify the tree-walking evaluator, at the cost of
   representing something the type system would no longer admit once RFC-0126 lands.
5. **Which release, and in what order against #579/#267?** RFC-0126's migration argues for
   landing early (it unblocks six of #267's fixtures directly); the dependency on RFC-0067
   (Open Question 2 above) argues for later, at least for a mutable-slice variant. The
   sequencing decision that matters is against **#579**, since move checking is what would
   otherwise bake in the pre-RFC-0126 model permanently.
6. **~~Can `List<T>` ever be implemented in Metel source from `[T; N]` and `T[]` alone?~~
   Moved to RFC-0133 (From-Metel List: the Runtime-Sized Buffer Gap), 2026-08-13.**
   RFC-0133 is normative and carries the full finding: the five prerequisites in
   dependency order, the prior-art table on what every comparable growable container is
   built on, and the ownership summary — of which the load-bearing part is that **two of
   the five prerequisites (a runtime-sized buffer-allocation primitive in the design, and
   one in the evaluator) have no owning RFC at all.** That absence is what makes the
   question indefinite rather than merely distant, and it is why it was holding this RFC
   hostage: there is no document to wait on and no milestone that could contain it.

   Deliberately **not** duplicated here. The content was 45 lines of source-verified
   findings (file:line citations into `grammar.pest`, `parser/mod.rs`, `types/mod.rs`,
   `builtins.rs`); keeping a second copy in a second `0-draft` document is precisely the
   staleness this corpus has been bitten by repeatedly — see `PROCESS.md` on RFC-0067's
   "description of its own staleness that was itself stale." One copy, in RFC-0133.

   Two things worth keeping visible from it, because they bear on *this* RFC's remaining
   questions rather than RFC-0133's: **(1)** `[T; N]` can never be a growable buffer
   regardless of const generics, so Open Question 3's resolution (RFC-0132 §3) does not
   move RFC-0133 at all — the two were always independent, not sequential; **(2)** `T[]`
   is structurally incapable of it too, since RFC-0126 made it an unconditionally `Copy`,
   non-owning view. Neither existing array type can back a growable list, which is why
   RFC-0133 needs a new primitive rather than a new combination of existing ones.

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
