---
id: rfc-0124
title: "Sequence Types: Fixed Arrays, Slices, and the Growable List"
date: '2026-07-25'
status: under-review
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

> **Status — under review (2026-09-01).** Slice half only after the OQ6/RFC-0133 and RFC-0126 splits; path to acceptance is now RFC-0067 (OQ2) then the mutable-slice spelling (OQ1).

> **Scope assessed as low strategic priority, 2026-09-28.** This RFC's full remaining chain
> — RFC-0067 lifetime anchors, RFC-0122 borrow checking, and (per Open Question 7 below) a
> `Sized`/unsized kind distinction, generalized unsizing coercions, and allocator-backed
> dynamic-sized allocation for a `Box<[T]>`-equivalent — was reviewed end to end and judged
> to carry too many prerequisites, spanning multiple RFCs and milestones out to v0.17.0+, to
> be a near-term focus: `T[]` matching Rust's reference/unsized-kind model in full is not a
> Metel-defining feature under current strategic objectives. This is a priority call, not a
> design reversal — nothing above resolves differently because of it, and it does not affect
> **`metel-core#1296`** (unannotated array literals incorrectly inferring `T[]` instead of
> `[T; N]`), which is a plain implementation bug against the already-`4-implemented`
> RFC-0126, unrelated to this RFC's own open questions.

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
| Does `T[]` need a sigil, or gain lifetime-checking while staying bare? | **added 2026-09-28** — open, sub-question of §Open Questions 2 |
| What would `@a [T]` (Metel's `Box<[T]>` analogue) additionally require? | **added 2026-09-28** — open — §Open Questions 7, deliberately not a near-term priority |

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

   **Sub-question, added 2026-09-28 — does `T[]` need a sigil, or does it stay bare and gain
   lifetime-checking implicitly?** There are two distinct ways to attach an anchor to `T[]`,
   not one:

   **(a) Sigil requirement, Rust-exact.** Introduce an unsized `[T]` payload type — cannot be
   a bare field, local, or return type on its own — and require every use site to spell the
   borrow explicitly, `&[T]` / `&var [T]`, through the existing `Reference`/`MutReference`
   machinery RFC-0067a already established. This reopens RFC-0171's freshly `2-accepted`
   spelling (`[T]` / `[T; N]`, no sigil) before it integrates, or lands as a second syntax
   break on top of it later.

   **(b) Implicit reference semantics, no spelling change.** `T[]` (or `[T]`, per RFC-0171)
   stays bare, but is defined in the type system as inherently carrying a region/lifetime the
   same way `&T` will once anchors exist — checked identically, without a written sigil. This
   is the direction this question already points toward as written above (an anchor attaching
   to the existing spelling), and it costs nothing against RFC-0171.

   What decides between them for Rust — needing `[T]` to compose with more than one pointer
   kind, especially `Box<[T]>` for an owned-but-non-growable heap buffer — may not apply the
   same way here, since `List<T>` already fills "owned, heap, growable" without a separate
   unsized-payload type underneath it. See Open Question 7 for what `(a)`'s `Box<[T]>`
   analogue would additionally require regardless of which way this resolves.

   Concretely demonstrated open today, independent of which way this resolves: a `T[]`
   borrowed from a function-local can be stored in a struct field and returned from the
   function that borrowed it, typechecking and running cleanly with or without
   `--move-check` — the same hole plain `&T`/`&var T` has. `GAP-OWNERSHIP-001` (extended
   2026-09-28) carries a reproduced example for both. `metel-core#274` already bans
   reference-typed (`&T`/`&var T`) struct/enum fields as an interim measure pending this
   RFC-0067 dependency; its ban text is scoped to `&`/`&var` spellings and does not currently
   mention `T[]` — worth checking, whichever of `(a)`/`(b)` above is chosen, that `#274`'s
   restriction (or its replacement) actually covers `T[]`-typed fields too when implemented.
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
7. **Added 2026-09-28 — what would composability with a pointer/allocator type need,
   the way Rust's `[T]` composes under `&[T]`, `Box<[T]>`, `Rc<[T]>`, and `Arc<[T]>`?**
   Metel has no `Box<T>` generic; the nearest analogue is `@a T` (RFC-0063), a built-in
   allocator-tagged pointer type, so the concrete target would be `@a [T]` rather than a
   literal `Box<[T]>`. Checked directly (2026-09-28): no `Sized`/`?Sized`-equivalent kind
   distinction exists anywhere in `metel-frontend`'s type checker, and no `Box` stdlib type
   exists. Beyond Open Question 2's anchor dependency, `@a [T]` would additionally need:

   - **A `Sized`/unsized kind distinction**, entirely absent today. Without it there is no
     way to express "`[T]` may appear as `@a [T]`'s payload but not as a bare field/local" —
     this is the foundational piece, prior to anything else in this list.
   - **A generalized unsizing coercion.** Today's only instance is the one hardcoded check
     for `[T; N] → T[]` (RFC-0053/RFC-0126,
     `reject_dynamic_array_where_sized_expected` in
     `metel-frontend/src/pipeline/type_checking/construction/mod.rs`), not a mechanism that
     composes *through* a wrapper type — coercing `@a [T; N] → @a [T]` means synthesizing the
     fat pointer's length at the coercion site, under the pointer, which nothing today does.
   - **Dynamic-layout allocation**, sized by a runtime length rather than a compile-time
     `size_of::<T>()`. This is the identical primitive RFC-0133 already found missing for
     `List<T>`'s own growth (its two prerequisites "have no owning RFC at all" — Open
     Question 6 above) — the same gap, reachable from a different angle.
   - **`Drop` running with that length available at deallocation time**, to free the right
     byte count and run the right number of element destructors. Blocked on
     `LIMIT-EVALUATION-005` (destructor invocation is not implemented at all yet, planned
     v0.15.0) independent of arrays entirely.

   One asymmetry favors Metel over a from-scratch Rust-style design: `@a T` is already a
   built-in pointer-shaped type constructor, not an ordinary generic struct wearing an
   opt-in `?Sized` bound the way `Box<T>` is — the "does the type system know this wrapper is
   a pointer" half of the problem Rust solves with a trait bound is already true by
   construction for `@a T`.

   See the RFC-level scope note above: this whole composability question is deliberately not
   being pursued as a near-term priority.

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
- RFC-0122 (Borrow Checking), `1-under-review`, target v0.16.0 (corrected 2026-09-28 —
  this line previously cited v0.14.0, stale since `metel-core#847`'s 2026-08-27
  renumbering) — shares the cloning-evaluator problem; Open Question 2 here is its likely
  resolution path. `#847`'s own scope explicitly lists "escape and outlives checking for
  locals, parameters, returns, reborrows and closures," directly reaching Open Question 2's
  escaping-`T[]` example.
- `GAP-OWNERSHIP-001`, extended 2026-09-28 — documents the escaping-reference/escaping-`T[]`
  hole (Open Question 2) as a known, tracked gap resolving against RFC-0122.
- `metel-core#274` — the interim ban on reference-typed struct/enum fields, cited in Open
  Question 2, pending the same RFC-0067 dependency this RFC has.
- `LIMIT-EVALUATION-005` — destructor invocation not implemented, cited in Open Question 7
  as a prerequisite for `@a [T]`'s `Drop` handling, independent of arrays.
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
