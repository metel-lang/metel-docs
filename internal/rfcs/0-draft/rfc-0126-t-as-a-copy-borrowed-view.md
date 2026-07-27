---
id: rfc-0126
title: "T[] as a Copy Borrowed View"
date: '2026-07-27'
status: draft
target:
---

> **Status — draft (2026-07-27).** Split out of RFC-0124 when the role assignment itself
> (`T[]` is a non-owning, immutable, `Copy` view) turned out to already be settled —
> RFC-0054 assigned this role in `4-implemented`, and RFC-0124's own prior-art survey found
> no live alternative. What remains genuinely open — a mutable-slice spelling, the exact
> RFC-0067 lifetime-anchor dependency, `[T; N]` const generics, evaluator representation,
> and release sequencing — stays with RFC-0124, which this RFC does not attempt to resolve.
> Filed now because #290 and #291 are blocked on exactly this question, and #310's fixture
> migration has six fixtures whose only obstacle is it.

## Summary

`T[]` becomes a **borrowed view over a contiguous run owned by someone else**: a pointer and
a length, owning nothing, immutable, produced only by borrowing a `List<T>`, a `[T; N]`, or
another slice. Because it owns nothing, it is `Copy` — the same argument RFC-0071 §9 q3
already accepted for `&T`. Array literals retype from `T[]` to `[T; N]`, since a literal has
a statically known length and owns its elements, which is the fixed-array case.

This is RFC-0124 §2.2 and §2.4 verbatim, extracted because nothing else in RFC-0124 needs to
be true for this part to be right.

---

## Motivation

### The immediate blocker

RFC-0071 §2 makes fixed-size arrays `Copy` when their elements are. Implementing that
(issue #290) requires answering whether `T[]` is `Copy`, and the question is currently
undecidable from the RFC record alone:

- As a *view*, `T[]` should be `Copy` — a shared reference is `Copy` in every language that
  has both, and duplicating a view grants no capability the holder lacked.
- As an *owning buffer* — what the implementation does today — `T[]` must **not** be `Copy`:
  copying the handle would alias one buffer under two owners, which is exactly what
  ownership exists to prevent.

RFC-0054 (`4-implemented`) already answered this: it assigned growth to `List<T>` and
declared `T[]` "the immutable/read-only array type," a view. The implementation never
followed — `T[]` is mutable, owns its buffer, and is deep-copied on every binding. #290
cannot write a `Copy` rule for `T[]` that survives until that gap closes.

### Measured state, 2026-07-25 (carried over from RFC-0124)

Against the interpreter at `develop`:

| | RFC-0054 states | implementation does |
|---|---|---|
| `T[]` mutability | immutable / read-only | **mutable** — `a[0] = 9` is accepted |
| `List::as_slice` | "view … no copy" | returns the same `Rc`, but the binding deep-clones it |
| `T[]` assignment | unstated | **deep copy**, O(n), on every binding |

`native_list_as_slice` genuinely returns the shared `Rc`, so the no-copy claim holds for one
statement — and is then undone by `deep_clone_value` at the binding site
(`evaluator/mod.rs:1300`). The net effect is value semantics purchased by copying the whole
buffer every time it is named.

### Why the immutability break is smaller than it looks

Measured directly against the corpus, 2026-07-25: `stdlib/` contains **zero**
index-assignments through a sequence, and the whole test corpus contains **17**, across nine
fixtures — most of which exist precisely to test index assignment, `&var` lvalue paths, or
explicit dereference, and several of which are about sized arrays rather than `T[]`. The
literal-retyping migration (`T[]` → `[T; N]` at every array-literal site) is the real cost
here, not the mutability rule — and it is a type change the compiler finds by refusing to
build, not a silent behavioral change, which is the safer direction of migration error.

### Why this unblocks more than #290

**#291's move checking** currently has no rule for `T[]` at all beyond "not `Copy`," which is
why six fixtures in #310's corpus migration are stuck: they reuse an array binding in ways
that are only illegal under the current owning-buffer model. Once `T[]` is a view, those
fixtures need no source changes — the violations disappear because the premise that made
them violations is gone.

**Deep-copy-on-binding is the cost ownership exists to remove.** RFC-0071 §1 says values
move. Building move checking on an evaluator that deep-clones arrays leaves those copies in
place behind the feature meant to eliminate them — ownership enforced statically while the
runtime keeps paying as though it were not there. (Removing the clones themselves is
evaluator work, tracked separately — this RFC only removes the type-level obstacle to it.)

---

## Prior art

Every language in Metel's neighbourhood — no GC, ownership tracked, systems-facing —
converges on the same split, with the growable container in the *library* rather than the
language:

| | fixed | view | growable |
|---|---|---|---|
| **Rust** | `[T; N]` value, `Copy` if `T: Copy` | `&[T]` borrowed fat pointer, `Copy` | `Vec<T>` — std, owns, affine, `Drop` |
| **Zig** | `[N]T` value | `[]T` fat pointer view | `std.ArrayList(T)` — std |
| **C++** | `T[N]`, `std::array` | `std::span` (C++20) | `std::vector` — std |

Two languages take the other road, and both pay for it in ways Metel cannot afford:

- **Go** — `[]T` is a copyable header that *aliases* its backing array. Copying is cheap and
  sharing is silent; the resulting aliasing bugs are among the most reported in the language.
  This is the model Metel currently approximates, minus the sharing, which deep copying
  hides.
- **Swift / D** — value semantics on the growable type itself, affordable only with COW plus
  refcounting (Swift) or a GC (D). Metel has neither, and RFC-0071 is a commitment not to
  acquire one.

A borrowed view is `Copy` precisely because it owns nothing; an owning container is affine
precisely because it does. Once ownership is tracked, a type that both owns and is freely
duplicable has no coherent place — which is exactly the corner `T[]` occupies today.

---

## Decision proper

### `T[]` — a borrowed slice

`T[]` is a view: a pointer and a length, owning nothing, valid only as long as its referent.

- **`Copy`, unconditionally.** Duplicating a view grants no capability its holder lacked —
  the same argument already accepted for `&T` (RFC-0071 §9 q3). This is not conditional on
  `T: Copy`, because a view of a `T` never holds a `T` — it holds a location.
- **Owns nothing**, so it has no `Drop` and never frees.
- **Immutable.** A mutable view, if the language wants one, is a separate spelling — left to
  RFC-0124 (open question 1 there), not decided here.
- **Produced by borrowing** something that owns: a `List<T>`, a `[T; N]`, or another slice.
  Never produced directly by a literal.

### Array literals retype to `[T; N]`

`[1, 2, 3]` produces `[i64; 3]`, not `T[]`: a literal has a statically known length and owns
its elements, which is the fixed-array case, already `Copy` when `T` is (RFC-0071 §2, #290).
Slices arise only from borrowing.

### What this does not decide

- Whether a mutable slice exists, and how it is spelled.
- The exact dependency on RFC-0067's lifetime anchors for slice validity — RFC-0124 still
  owns confirming that relationship before its own acceptance.
- Whether `[T; N]`'s `Copy` rule needs const generics to leave the typechecker's hardcoded
  special case (#299) — orthogonal to this RFC, since `[T; N]`'s `Copy`-when-`T`-is-`Copy`
  rule is unchanged by anything here.
- `Value::Array`'s evaluator representation (`Rc<RefCell<Vec>>` today) — an implementation
  choice, not a type-system one.
- Release sequencing against #291 and #310 — a scheduling question, addressed by whoever
  actually lands this, not by this document.

---

## Consequences

**RFC-0071's `Copy` table becomes writable for `T[]`.** `[T; N]` is `Copy` when `T` is
(unchanged); `T[]` is `Copy` unconditionally as a view; `List<T>` never is. #290's blocked
question is answered.

**#310's six deferred fixtures need no source changes.** Their violations were reports that
an array binding was reused in a way the owning-buffer model forbids; under the view model,
reuse of a `Copy` value is legal by construction.

**#291's move checking gains a real rule for `T[]`** instead of the current default
(everything not explicitly `Copy` is affine), closing the gap that made those six fixtures
look like defects in the corpus rather than in the rule.

**Every array-literal-typed binding and signature changes type**, in `stdlib/` and the test
corpus. This is found by the compiler (a type mismatch, not a silent behavior change) and is
the one real migration cost here — see "Why the immutability break is smaller than it looks"
above for the measured scope.

**Deep-copy-on-binding is not removed by this RFC.** The evaluator may keep cloning after
this lands; that remains true regardless of `T[]`'s `Copy` status, since the evaluator does
not yet act on the `Copy`/move distinction at all (RFC-0071 #291's own scope note: move
checking is a static pass, clone-elision is later, separate work). This RFC removes the
type-level argument that `T[]` cannot be a view — it does not itself make the runtime faster.

---

## References

- RFC-0054 (Standard `List<T>` Type), `4-implemented` — assigned growth to `List<T>` and
  declared `T[]` the immutable read-only view. This RFC is that assignment, finally taken at
  face value.
- RFC-0124 (Sequence Types), `0-draft` — the RFC this was split from; still owns the mutable-
  slice spelling, the RFC-0067 dependency, `[T; N]` const generics, representation, and
  sequencing.
- RFC-0071 (Ownership and Move Semantics), `3-integrated` — §2's `Copy` rules are what this
  unblocks; §9 q3 is the `&T`-is-`Copy` precedent this RFC extends to views generally.
- RFC-0067 (Lifetime Anchors), `2-accepted` — the likely dependency for slice validity,
  confirmed by RFC-0124 rather than here.
- Issues #290 (blocked on this question), #291 (move checking has no `T[]` rule without
  this), #310 (six fixtures blocked on this specifically), #299 (`[T; N]`'s own hardcoded
  `Copy` rule, unaffected by this RFC).

---

## Adversarial review — for whoever reviews this before acceptance

Two decisions here are not settled merely because this document states them, per PROCESS.md:

1. **"`Copy` unconditionally, because a view holds a location, not a `T`."** Attack this
   directly: is there a `T` for which handing out unlimited, unrestricted copies of a
   *location* is unsafe even though the location itself is inert data? Consider `T` types
   whose *aspect methods* assume single-writer access reached only through the slice — does
   `Copy`-ness of the view leak a capability through some method-dispatch path this RFC
   didn't consider, rather than through the raw pointer-and-length itself?
2. **"The immutability break is smaller than it looks, because only 17 index-assignments
   exist today."** This is a static grep over the current corpus, not a proof about what the
   corpus needs. Attack it: does the *absence* of index-assignment through `T[]` today reflect
   that nobody needs it, or that nobody has written it yet because there was no reason to
   reach for a growable-in-place array when `List<T>` already exists? A counterexample would
   be a realistic program shape that *wants* in-place index assignment through a shared view
   rather than through `List<T>`, which this measurement cannot rule out by counting.

An honest "no counterexample found" on either point is an acceptable review outcome.

---

## Decision

**Outcome:** *(pending)*
**Target:** *(set when accepted)*
