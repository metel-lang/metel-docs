---
id: rfc-0126
title: "T[] as a Copy Borrowed View"
date: '2026-07-27'
status: implemented
target: v0.12.0
updated: '2026-08-03'
impl_tracking: 'https://github.com/metel-lang/metel-core/issues/593'
impl_status: implemented
coverage:
  "1": { spec: "spec.types.arrays.legality-1" }
  "2": { spec: "spec.types.arrays.legality-1" }
  "3": { spec: "spec.types.fixed-size-arrays.legality-1" }
  "4": { spec: "spec.types.fixed-size-arrays.legality-2" }
---

> **Status — draft (2026-07-27).** Split out of RFC-0124 when the role assignment itself
> (`T[]` is a non-owning, immutable, `Copy` view) turned out to already be settled —
> RFC-0054 assigned this role in `4-implemented`, and RFC-0124's own prior-art survey found
> no live alternative. What remains genuinely open — a mutable-slice spelling, the exact
> RFC-0067 lifetime-anchor dependency, `[T; N]` const generics, evaluator representation,
> and release sequencing — stays with RFC-0124, which this RFC does not attempt to resolve.
> Filed now because #578 and #579 are blocked on exactly this question, and #267's fixture
> migration has six fixtures whose only obstacle is it.

> **Status — under review (2026-07-27).** Split from RFC-0124 already stating the settled decision; adversarial review performed same day

> **Status — accepted (2026-07-27).** No open questions of its own remain: both named attack vectors checked with no counterexample found; the third finding (call-site/let-binding migration) verified already solved by RFC-0053

> **Status — integrated (2026-07-27).** Spec merged into types.md/declarations.md with Planned-for-v0.12.0 markers; worked examples against RFC-0053 (already-implemented coercion) and RFC-0071 (Copy/Drop/partial-move) found no unresolved soundness gap, but did surface that stdlib's existing T[]:Clone impl must be rewritten, recorded in Consequences

> **Status — implemented (2026-07-27).** Implemented in metel-core#593, verified independently (640 integration + 122 unit tests, 0 clippy warnings, move-check-count confirms zero T[]-related violations remain)

> **Corrected 2026-08-03.** This RFC's own References section (and RFC-0124's) cited
> RFC-0067 (Lifetime Anchors) as `2-accepted`. Checked directly against
> `public/rfcs/1-under-review/rfc-0067-lifetime-anchors.md`: RFC-0067 was reverted to
> `1-under-review` on 2026-08-02 — one day before this correction — with a newly-written
> blocking chain (RFC-0122 must settle first, then RFC-0067's own five open questions)
> before it can reach `3-integrated`; implementation is now targeted v0.15.0. This does
> not change anything this RFC decided — confirming the RFC-0067 dependency was always
> RFC-0124's to own, not this RFC's ("What this does not decide," above) — it only fixes
> a stale citation so a reader following this RFC's own References does not act on an
> already-superseded status. See RFC-0124's 2026-08-03 note for the fuller context this
> correction is part of.

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
(issue #578) requires answering whether `T[]` is `Copy`, and the question is currently
undecidable from the RFC record alone:

- As a *view*, `T[]` should be `Copy` — a shared reference is `Copy` in every language that
  has both, and duplicating a view grants no capability the holder lacked.
- As an *owning buffer* — what the implementation does today — `T[]` must **not** be `Copy`:
  copying the handle would alias one buffer under two owners, which is exactly what
  ownership exists to prevent.

RFC-0054 (`4-implemented`) already answered this: it assigned growth to `List<T>` and
declared `T[]` "the immutable/read-only array type," a view. The implementation never
followed — `T[]` is mutable, owns its buffer, and is deep-copied on every binding. #578
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

### Why this unblocks more than #578

**#579's move checking** currently has no rule for `T[]` at all beyond "not `Copy`," which is
why six fixtures in #267's corpus migration are stuck: they reuse an array binding in ways
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
its elements, which is the fixed-array case, already `Copy` when `T` is (RFC-0071 §2, #578).
Slices arise only from borrowing.

### The migration this implies is already solved, by RFC-0053, at every expected-type position

Retyping literals to `[T; N]` looks at first like a large migration on its own, independent
of the index-assignment cost above: `stdlib/` and the corpus are full of generic functions
taking a bare `T[]` parameter (`filter<T>(arr: T[], ...)`, `map_arr`, `fold`, `zip_with`, and
92 declarations shaped like them corpus-wide), called with an **unannotated** literal-derived
binding — `let nums = [1, 2, 3]; filter(nums, pred)`. Under this RFC, an unannotated `[1, 2,
3]` infers to `[i64; 3]` (nothing pressures it toward `T[]`), so if literal retyping were the
only thing that changed, `filter(nums, pred)` would be a fresh type mismatch — and so would
every annotated binding that explicitly asks for `T[]` (`let nums: i64[] = [1, 2, 3];`, the
dominant style actually used in the corpus), unless the annotation itself can force the
literal there too.

Both are already solved, because **RFC-0053 (`4-implemented`) already decided the general
mechanism**: "`[T; N]` coerces implicitly to `T[]`. The reverse is a type error." Verified
directly — not just re-read — that this fires at **both** shapes the corpus actually uses,
unrelated to anything this RFC changes:

```metel
// (a) the annotated let-binding — the corpus's dominant style
fun main() {
    let nums: i64[] := [1, 2, 3];   // literal coerces at the binding itself
    assert(nums.len() == 3);
}
```

```metel
// (b) an unannotated value passed where T[] is expected — the generic-call-argument case
fun sum<T>(arr: T[]) -> i64 {
    var total := 0;
    for (x in arr) { total += 1; }
    total
}
fun main() {
    let fixed: [i64; 3] := [1, 2, 3];
    assert(sum(fixed) == 3);   // coerces at the call, today, before this RFC exists
}
```

The coercion is general over *any* expected-type position — a `let`/`var` target, a function
argument, a generic instantiation — not specific to call sites. RFC-0053 wrote it for the
*old* model, where it was a cheap copy ("the runtime representation is identical, coercion is
free and correct"). Under this RFC's model, the same coercion becomes a **borrow** instead of
a copy — which is not a new mechanism to build, it is exactly what §2.2 above already says
produces a `T[]` ("produced by borrowing... a `[T; N]`"). The existing coercion node is the
implementation of that borrow, wherever it fires; this RFC does not need to invent one. What
it does *not* settle is whether that borrow is sound for every possible callee (one that
stashes the view somewhere longer-lived than the call) — that is RFC-0124's lifetime-anchor
dependency (Open Question 2 there), not a new gap this RFC introduces.

### What this does not decide

- Whether a mutable slice exists, and how it is spelled.
- The exact dependency on RFC-0067's lifetime anchors for slice validity — RFC-0124 still
  owns confirming that relationship before its own acceptance.
- Whether `[T; N]`'s `Copy` rule needs const generics to leave the typechecker's hardcoded
  special case (#263) — orthogonal to this RFC, since `[T; N]`'s `Copy`-when-`T`-is-`Copy`
  rule is unchanged by anything here.
- `Value::Array`'s evaluator representation (`Rc<RefCell<Vec>>` today) — an implementation
  choice, not a type-system one.
- Release sequencing against #579 and #267 — a scheduling question, addressed by whoever
  actually lands this, not by this document.

---

## Consequences

**RFC-0071's `Copy` table becomes writable for `T[]`.** `[T; N]` is `Copy` when `T` is
(unchanged); `T[]` is `Copy` unconditionally as a view; `List<T>` never is. #578's blocked
question is answered.

**#267's six deferred fixtures need no source changes.** Their violations were reports that
an array binding was reused in a way the owning-buffer model forbids; under the view model,
reuse of a `Copy` value is legal by construction.

**#579's move checking gains a real rule for `T[]`** instead of the current default
(everything not explicitly `Copy` is affine), closing the gap that made those six fixtures
look like defects in the corpus rather than in the rule.

**Every array-literal-typed binding and signature changes type**, in `stdlib/` and the test
corpus. This is found by the compiler (a type mismatch, not a silent behavior change) and is
the one real migration cost here — see "Why the immutability break is smaller than it looks"
above for the measured scope.

**`stdlib/core.mtl`'s existing `T[]: Clone` impl becomes unsound and must be rewritten,
found while writing this RFC's spec-integration worked examples (`declarations.md`'s
"Standard array impls").** Today it is:

```metel
extend<T: Clone> T[]: Clone {
    fun clone(&self) -> Self {
        var out: List<T> := List::new();
        for (item in self) { out.push(item.clone()); }
        return out.as_slice();   // <- a view into a local that is about to go out of scope
    }
}
```

Under the current owning-buffer model this is safe only because `as_slice`'s result is
deep-copied at the binding/return boundary regardless (RFC-0124's measured-state table), so
`out`'s deallocation never matters — the copy already happened. Once `T[]` is a genuine
borrowed view with no such copy-on-return, this function returns a view into `out`, which is
freed the moment `clone` returns: a dangling reference. More fundamentally, **`T[]: Clone`
cannot be implemented at all under the view model** — `Clone::clone(&self) -> Self` must
produce a `Self` (a `T[]`), and a `T[]` can only ever borrow from something that already
exists and outlives it; `clone` has nothing pre-existing to borrow from, only a buffer it
just allocated. The only coherent `clone` for a `Copy`, non-owning view is the trivial one
(`fun clone(&self) -> Self { *self }`, identical to what `Copy` already gives for free), and
whether that's worth keeping as an explicit impl at all — rather than just relying on `Copy`
— is a call for whoever implements this RFC, not decided here. **This does not reopen this
RFC's own decision; it is a required consequence of it**, and is recorded here so it is not
rediscovered as a bug after implementation lands.

**Deep-copy-on-binding is not removed by this RFC.** The evaluator may keep cloning after
this lands; that remains true regardless of `T[]`'s `Copy` status, since the evaluator does
not yet act on the `Copy`/move distinction at all (RFC-0071 #579's own scope note: move
checking is a static pass, clone-elision is later, separate work). This RFC removes the
type-level argument that `T[]` cannot be a view — it does not itself make the runtime faster.

---

## Worked example — intersection with RFC-0071 (Ownership and Move Semantics, `3-integrated`)

A `Drop`-implementing struct with a `T[]` field, read twice:

```metel
struct Wrapper { data: i64[], tag: String }
extend Wrapper: Drop { fun drop(self) {} }

fun main() {
    let w := Wrapper { data = [1, 2, 3], tag = "x" };
    let d := w.data;
    let d2 := w.data;   // today: T0019, use of moved value `w.data`
}
```

Verified today (before this RFC): reusing `w.data` reports exactly one move violation, as
expected under the current owning-buffer model — `T[]` isn't `Copy` yet. Once this RFC lands
and `T[]` is `Copy`, the same code has zero violations, with no special-casing anywhere:
`Wrapper` implementing `Drop` while holding a `Copy` field is the ordinary, already-handled
shape partial-move tracking needs regardless (a `Drop` struct with any mix of `Copy` and
non-`Copy` fields), not a new interaction this RFC introduces. No soundness gap found at this
intersection.

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
- RFC-0067 (Lifetime Anchors), `1-under-review` (reverted 2026-08-02; see correction note
  above) — the likely dependency for slice validity, confirmed by RFC-0124 rather than
  here.
- RFC-0053 (Fixed-Size Arrays), `4-implemented` — already decided and already live: `[T; N]`
  coerces implicitly to `T[]`, including at generic call sites. This RFC's call-site migration
  cost rides on that coercion rather than needing a new one.
- Issues #578 (blocked on this question), #579 (move checking has no `T[]` rule without
  this), #267 (six fixtures blocked on this specifically), #263 (`[T; N]`'s own hardcoded
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

**Reviewed 2026-07-27.** Both points above checked directly against the codebase, not just
re-read:

1. **No counterexample found.** `T[]` is immutable by this RFC's own decision, and nothing in
   the type system dispatches a `&var self` method through an immutable binding (the `&var` →
   `&` coercion is already one-way elsewhere in this codebase). There is no path from "holds a
   `Copy` view" to "can reach mutable access," so the capability-leak attack does not land.
2. **Independently re-measured, not re-read.** 9 fixtures, matching the RFC's count exactly;
   site count came out at 22 rather than 17 by naive grep, explainable by counting method (one
   of the 22 is a negative test that is *supposed* to reject the assignment, supporting the
   RFC's framing rather than undermining it). One counted fixture
   (`evaluator/types/13_sized_array_extended.mtl`) mutates a `[i64; 3]`, already fixed-size and
   irrelevant to this RFC either way — if anything the true `T[]`-specific surface is smaller
   than stated. This substantially confirms the measurement.

A third issue turned up that neither attack vector named: whether `[T; N]` → `T[]` is coercible
at a call site, since 92 corpus-wide function declarations take a bare `T[]` parameter and the
common call shape passes a literal-derived binding. **Already resolved by RFC-0053**
(`4-implemented`) — see "The migration this implies is already solved, by RFC-0053, at every
expected-type position" above. Verified live at both the `let`-binding and the generic-call-
argument shape, not just documented.

---

## Decision

**Outcome:** Accepted. `T[]` becomes a non-owning, immutable, unconditionally-`Copy` view
produced only by borrowing; array literals type as `[T; N]`. No open questions of its own
remain — both named attack vectors in the adversarial review above were checked directly
against the codebase and neither lands, and the migration-cost concern the review itself
surfaced (call-site and `let`-binding retyping) is already solved, live, by RFC-0053.
**Target:** v0.12.0 — the same milestone as #578, #579, and #267, which this RFC unblocks.

---

## Coverage Checklist (added 2026-08-18, not part of the original RFC)

Retroactive breakdown of this RFC's distinct normative claims, as headed sections for
citation purposes only. The document above is unchanged and remains the
historical record.

### 1. `T[]` is `Copy` unconditionally

Regardless of the element type — a `T[]` binding may be used again after being read or
passed elsewhere, the same way any `Copy` value can.

### 2. `T[]` has no `Drop` and owns nothing

A struct field of type `T[]` may be read more than once even when the struct itself
implements `Drop`.

### 3. An array literal types as `[T; N]`, not `T[]`

`[1, 2, 3]` is `[i64; 3]`.

### 4. A `[T; N]` coerces implicitly to `T[]`, never the reverse

At any position expecting `T[]` — an annotated `let`/`var` binding, or a generic
function's `T[]`-typed parameter.
