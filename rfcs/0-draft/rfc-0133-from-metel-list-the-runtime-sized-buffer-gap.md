---
id: rfc-0133
title: "From-Metel List: the Runtime-Sized Buffer Gap"
date: '2026-08-13'
status: draft
target:
---

> **Split out of RFC-0124 Open Question 6, 2026-08-13.** RFC-0124 bundled two questions
> with fundamentally different tractability, and the harder one was holding the other
> hostage. Its OQ1/OQ2/OQ4/OQ5 (mutable-slice spelling, the RFC-0067 lifetime-anchor
> dependency, `Value::Array`'s representation, release sequencing) all become actionable
> at a **known point** — when RFC-0067 settles, targeted ~v0.15.0. Its OQ6 — can
> `List<T>` ever be written in Metel source — has **no known path at all**: it needs a
> runtime-sized buffer-allocation primitive that does not exist in Metel's design even on
> paper, with no RFC owning it. Keeping both in one document meant RFC-0124 could not be
> accepted (OQ2 is a stated precondition for its own acceptance) *and* could not be
> scheduled (OQ6 has no schedulable content), so it sat `0-draft` and untargeted from
> 2026-07-25.
>
> **This is the same move made for RFC-0092 → RFC-0132 the same day**, and the third
> instance of the pattern in this corpus (RFC-0012 → RFC-0092/0093/0094/0095 was the
> first): a tractable piece trapped inside a document with an intractable piece does not
> get worked on, and splitting is what frees it. Worth noting as a general lesson rather
> than three coincidences — see `reports/strategy/OBJECTIVES.md` Trigger 30.
>
> **`metel-core#276` tracks this RFC**, not RFC-0124, as of this split. That issue was
> already scoped to OQ6 specifically ("tracks RFC-0124 … Open Question 6"), and was
> unmilestoned the same day to match its own body text, which had said "unmilestoned by
> design" while sitting in the v0.14.0 milestone.

## Summary

`List<T>` is 100% native/Rust-backed today. This RFC does not propose a from-Metel
implementation — it records, in one place, **what would have to exist first**, in
dependency order, so that "is the current native backing permanent, or just default?" has
an honest answer that does not require chasing five RFCs and two source trees.

**No design is proposed here and none should be inferred.** The finding this RFC carries
is that two of the five prerequisites have no owning RFC at all, and that absence is
itself the result, not a citation to go look up.

---

## Motivation

RFC-0124's 2026-08-03 note established that nothing in the RFC record had ever stated, in
so many words, that Metel's three-way sequence split (`[T; N]` / `T[]` / `List<T>`) is
temporary or incomplete. That note is now this RFC's premise rather than a caveat inside a
document about slices.

Concretely, `stdlib/core.mtl` implements every `List` primitive — `new`, `push`, `pop`,
`get`, `set`, `as_slice` — as `native(@std.core.list_*)`, backed by
`Value::Array(Rc<RefCell<Vec<Value>>>)` in the evaluator. There is zero Metel-source
implementation of any kind, **not even growth logic**.

---

## The five prerequisites, in dependency order

*Carried from RFC-0124 OQ6 (a)–(e), verified there against source rather than inferred.*

1. **`[T; N]` can never be the buffer.** `N` is a compile-time literal at every layer —
   grammar (`decimal_int`, `grammar.pest:311,328`), parser (a Rust `u64` baked into the
   AST, `parser/mod.rs:2634-2651`), and type representation
   (`Type::SizedArray(Box<Type>, u64)`, `types/mod.rs:28`). This is a **deliberate,
   permanent commitment**, not an engineering gap: RFC-0053 explicitly rejects
   runtime-sized arrays as "analogous to VLAs in C99, widely considered a design mistake."
   **Independent of const generics.** RFC-0132 §3 proposes `comptime N: u64` (the
   mechanism RFC-0053 deferred, drafted but not yet reviewed — see the correction below),
   and this bears restating precisely regardless of how §3's review lands: any mechanism
   for `N`-as-parameter that stays true to RFC-0053's own rejection of runtime-sized
   arrays must keep `N` a *named compile-time constant*, never a value read at runtime —
   so whatever eventually implements §3 changes nothing here. RFC-0124's OQ3 and this
   question were always independent, not sequential.
   >
   > **Correction, 2026-08-13.** This paragraph previously cited `metel-core#728` as the
   > issue that would land §3. #728 has been closed — it scheduled implementation of a
   > section that had never been reviewed, only drafted during the RFC-0092 split. See
   > `OBJECTIVES.md`'s Priority 7 note for the full reversal.
2. **`T[]` can never be the buffer either.** Since RFC-0126 (`4-implemented`, v0.12.0),
   `T[]` is unconditionally `Copy`, non-owning, and immutable *by design* — "a view is
   `Copy` precisely because it owns nothing." Structurally incapable of being an owning,
   growable buffer.
3. **No runtime-sized buffer-allocation primitive exists in Metel's design, even on
   paper.** RFC-0063 (Allocator Handles, `2-accepted`) is the RFC most often cited as
   "where `List`'s buffer comes from." Checked directly: it never mentions `List` (zero
   matches), and its entire specified surface (`@a T`, `@a expr`, §1–§8) is
   **single-value allocation only**. Its own §9 items 3–4 state, in its own words, that
   the `Alloc` aspect's `alloc` signature is "undecided and unspecified," and that "no
   lower-level primitive layer… exists" for authoring a custom allocator at all — let
   alone one capable of the batch/geometric-growth allocation every comparable growable
   container needs internally. **This prerequisite has no owning RFC.**
4. **No such primitive exists in the evaluator either.** Confirmed against
   `builtins.rs`: no `native_array_with_capacity` / `alloc_n`-shaped primitive exists.
   `List::new()` always starts empty and grows one element at a time via Rust's own
   `Vec::push` reallocation — invisible to, and uncontrollable by, Metel source.
   **Also has no owning RFC.**
5. **RFC-0067's lifetime anchors would be needed** to prove a borrowed `T[]` taken from a
   from-Metel `List` cannot outlive the buffer. RFC-0067 is `1-under-review` (reverted
   from `2-accepted` 2026-08-02), blocked behind RFC-0122 (Borrow Checking,
   `1-under-review`, target v0.14.0) settling first, then its own five open questions.
   Implementation targeted v0.15.0 at the earliest.

**Ownership summary — the actual finding.** (1) and (2) are settled elsewhere and
permanent. (5) is owned by RFC-0067/RFC-0122. **(3) and (4) are owned by nothing**, and
that is what makes this question indefinite rather than merely distant: there is no
document to wait on, no milestone that could contain it, and no dependency chain that
terminates in it.

---

## Prior art: what every comparable growable container is built on

*Carried from RFC-0124's extended prior-art table, which asked the question RFC-0126's own
survey had not: not "what are the three sequence types" but "what is the growable one
built on."*

| | growable | what it is built on |
|---|---|---|
| **Rust** | `Vec<T>` (std, owns, affine, `Drop`) | `RawVec<T, A>` — capacity/growth logic factored out of `Vec` itself, generic over an `Allocator` (`Global` by default, but a real, substitutable parameter) |
| **Zig** | `std.ArrayList(T)` | an explicit `Allocator` handle, set at `.init(allocator)` and threaded through every growth call |
| **C++** | `std::vector<T, Allocator>` | allocator-aware since C++98 — the allocator is the second template parameter, defaulted but always present; every growth operation is specified in terms of `Allocator::allocate`/`deallocate` |

**The pattern that matters:** in every one of these, the growable container's *storage
growth* is factored into a distinct, explicit allocator abstraction — never resolved by
the fixed-size or view types themselves, and never implicit-global-only. This is the shape
RFC-0063 was reaching for, and precisely the part it does not specify (prerequisite 3).

---

## What would close this

Two mutually exclusive outcomes, and this RFC deliberately takes neither:

- **A new RFC specifying a batch/buffer-allocation primitive**, extending RFC-0063 past
  single-value allocation — after which a from-Metel `List<T>` becomes designable, gated
  on prerequisite (5).
- **An explicit decision that native backing is permanent**, not merely default. This is a
  legitimate answer, and cheaper than the above. Nothing in the corpus currently says it,
  which is why the question keeps resurfacing as if it were open when it may not need to
  be.

Either closes `metel-core#276`. What is **not** acceptable is the status quo of carrying
this implicitly as an unstated implementation detail — which is what RFC-0124's
2026-08-03 note was written to stop.

---

## Open Questions

1. **Is a from-Metel `List<T>` actually wanted?** Not asked directly anywhere.
   `reports/strategy/OBJECTIVES.md` Priority 4 lists allocators as "deliberately not
   started," and the interpreter is explicitly a temporary feedback instrument (§1's
   corollary), not the target structure — so "the eventual compiler will need this" is not
   a reason to design it now. It is entirely possible that native backing is the right
   permanent answer and this RFC's real conclusion is prerequisite-free.
2. **Does the batch-allocation primitive belong to RFC-0063, or to a new RFC?** RFC-0063
   is `2-accepted`; extending an accepted RFC's specified surface is an amendment, not a
   new document, and `PROCESS.md` has no rule covering which is preferred when the
   extension is this large. (Note RFC-0063 is also in the 7-RFC allocator cluster that
   Trigger 29 flags as untouched since 2026-07-10 — an amendment there is not obviously
   cheaper than a new RFC.)
3. **Does `Value::Array`'s eventual representation** (decided by `metel-core#277`, which
   now also owns RFC-0124's OQ4) constrain this at all, or is a from-Metel `List` free to
   specify its own storage regardless of what the current native one uses?

---

## References

- **RFC-0124 (Sequence Types), `0-draft`** — this RFC's source; its OQ6 is now here in
  full. RFC-0124 retains the slice/representation/sequencing questions, which become
  actionable when RFC-0067 settles.
- **RFC-0054 (Standard `List<T>` Type), `4-implemented`** — assigned growth to `List<T>`
  and declared `T[]` the immutable read-only view.
- **RFC-0126 (`T[]` as a Copy Borrowed View), `4-implemented`** (v0.12.0) — prerequisite
  (2); its `Copy` view is structurally incapable of backing a growable buffer.
- **RFC-0053 (Fixed-Size Array Type), `4-implemented`** — prerequisite (1); its rejection
  of runtime-sized arrays is what makes that prerequisite permanent rather than pending.
- **RFC-0132 (Comptime Execution Model), `0-draft`** — §3's `comptime N: u64` makes `N` a
  named compile-time constant; explicitly **does not** affect prerequisite (1).
- **RFC-0063 (Allocator Handles), `2-accepted`** — prerequisite (3); the nearest existing
  design a batch-allocation primitive would extend, and **not** currently the source of
  `List`'s buffer despite frequent citation as such.
- **RFC-0067 (Lifetime Anchors), `1-under-review`** — prerequisite (5).
- `metel-core#276` — tracks this RFC (retargeted from RFC-0124 on 2026-08-13).
- `metel-core#277` — `Value::Array` representation; see Open Question 3.

---

## Decision

**Outcome:** *(pending)*
**Target:** *(none, deliberately — see the ownership summary above; this RFC should not
receive a target until Open Question 1 is answered)*
