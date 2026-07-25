---
id: rfc-0124
title: "Sequence Types: Fixed Arrays, Slices, and the Growable List"
date: '2026-07-25'
status: draft
target:
---

## Summary

Metel has three sequence types — `[T; N]`, `T[]`, and `List<T>` — and only two roles are
clearly assigned. RFC-0054 gave growth to `List<T>` and declared `T[]` "the immutable/
read-only array type", a *view*. The implementation never followed: `T[]` is mutable, owns
its buffer, and is deep-copied on every binding.

This RFC finishes RFC-0054's split by making the representation match the assigned roles:

| type | role | ownership | `Copy` |
|---|---|---|---|
| `[T; N]` | fixed-size sequence | owns, value semantics | when `T: Copy` |
| `T[]` | borrowed view of a contiguous run | owns nothing | yes — it is a shared reference |
| `List<T>` | growable sequence | owns | no — affine, `Drop` |

**The base type is not a growable container.** That is `List<T>`'s job and has been since
RFC-0054. `T[]` is demoted from an owning buffer to a borrowed slice.

---

## Motivation

### The immediate blocker

RFC-0071 §2 makes fixed-size arrays `Copy` when their elements are. Implementing that
(issue #290) requires answering whether `T[]` is `Copy`, and **the question is currently
undecidable**:

- As a *view*, `T[]` should be `Copy` — a shared reference is `Copy` in every language that
  has both, and duplicating a view grants no capability the holder lacked.
- As an *owning buffer*, `T[]` must **not** be `Copy` — copying the handle would alias one
  buffer under two owners, which is exactly what ownership exists to prevent.

Today it is the second; RFC-0054 says it is the first. Neither document can be followed
without contradicting the other, and #290 cannot write a rule that will survive.

### Measured state, 2026-07-25

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

### Why this is not merely tidy

**Deep-copy-on-binding is the cost ownership exists to remove.** RFC-0071 §1 says values
move. Building move checking (#291) on an evaluator that deep-clones arrays leaves those
copies in place behind the feature meant to eliminate them — ownership enforced statically
while the runtime keeps paying as though it were not there.

**RFC-0122 has an open question about "observability on a cloning evaluator."** Same root
cause, reached from the borrow checker's side. Fixing sequences addresses both.

---

## 1. Prior art

Every language in Metel's neighbourhood — no GC, ownership tracked, systems-facing —
converges on the same three-way split, with the growable container in the *library* rather
than the language:

| | fixed | view | growable |
|---|---|---|---|
| **Rust** | `[T; N]` value, `Copy` if `T: Copy` | `&[T]` borrowed fat pointer, `Copy` | `Vec<T>` — std, owns, affine, `Drop` |
| **Zig** | `[N]T` value | `[]T` fat pointer view | `std.ArrayList(T)` — std |
| **C++** | `T[N]`, `std::array` | `std::span` (C++20) | `std::vector` — std |

Two languages take the other road, and both pay for it in ways Metel cannot:

- **Go** — `[]T` is a copyable header that *aliases* its backing array. Copying is cheap and
  sharing is silent; the resulting aliasing bugs are among the most reported in the language.
  This is the model Metel currently approximates, minus the sharing, which deep copying hides.
- **Swift / D** — value semantics on the growable type itself, affordable only with COW plus
  refcounting (Swift) or a GC (D). Metel has neither, and RFC-0071 is a commitment not to
  acquire one.

**The pattern is not arbitrary.** A borrowed view is `Copy` precisely because it owns
nothing; an owning container is affine precisely because it does. Once ownership is tracked,
a type that both owns and is freely duplicable has no coherent place — which is exactly the
corner `T[]` occupies today.

---

## 2. The proposal

### 2.1 `[T; N]` — fixed-size, value semantics

Unchanged in spirit from RFC-0071 §2: a value type, `Copy` when `T: Copy`, moved otherwise.
It owns its elements inline.

### 2.2 `T[]` — a borrowed slice

`T[]` becomes a **view over a contiguous run owned by someone else**: a pointer and a length,
owning nothing, valid only as long as its referent.

- **`Copy`.** Duplicating a view grants no capability its holder lacked — the same argument
  RFC-0071 §9 q3 already accepted for `&T`.
- **Owns nothing**, so it has no `Drop` and never frees.
- **Immutable**, as RFC-0054 intended. A mutable view, if wanted, is a separate spelling —
  see open question 1.
- Produced by borrowing something that owns: a `List<T>`, a `[T; N]`, or another slice.

This is the change of substance. Everything else follows from it.

### 2.3 `List<T>` — the owner

Unchanged in role: it owns its buffer, is affine under RFC-0071, and gains `Drop` when
destructors land (#292). `as_slice` becomes what its name and RFC-0054 already promised — a
borrow, not a copy.

### 2.4 What an array literal produces

`[1, 2, 3]` produces a `[i64; 3]`, not a `T[]`: a literal has a statically known length and
owns its elements, which is the fixed-array case. Slices arise from borrowing, never from a
literal. This matches Rust and Zig, and is the main source of migration churn (§4).

---

## 3. Consequences

**RFC-0071's `Copy` table becomes writable.** `[T; N]` is `Copy` when `T` is; `T[]` is `Copy`
unconditionally as a view; `List<T>` never is. #290's blocked question is answered, and the
warning now in RFC-0071 §2 — that the one array form stdlib can express is the one that must
not be written — disappears along with the type it describes.

**Deep-copy-on-binding can go.** Passing a sequence becomes a move (`List<T>`), a copy of a
fixed array of known size, or a copy of a two-word view. None is O(n) per binding.

**RFC-0122's cloning-evaluator question narrows.** Aliasing becomes visible in the type
system instead of hidden behind deep copies, which is a precondition for a borrow checker
observing anything useful.

**`List<T>` needs `Drop` to free.** Today nothing frees because nothing owns. This ties the
RFC to #292 and, further out, to RFC-0063's allocators.

---

## 4. Migration cost, stated plainly

This is not a small change, and the estimate should not be buried:

- **Array literals change type**, from `T[]` to `[T; N]`. Every literal-typed binding and
  signature in `stdlib/` and the test corpus is affected. RFC-0115's separator migration
  touched 566 sites and was mechanical; this one changes *types* rather than tokens, so the
  compiler finds the sites instead of a regex — slower to fix, but far safer.
- **A slice needs a lifetime story.** A view outliving its owner is a use-after-free. Metel
  has RFC-0067 (lifetime anchors, `2-accepted`) and RFC-0122 (borrow checking, `0-draft`);
  this RFC depends on that machinery and should not pretend otherwise.
- **`T[]` stops being mutable**, so `a[0] = 9` through a slice no longer compiles. Such code
  moves to `List<T>` or to a mutable-view spelling.

**Doing nothing also has a cost**, which is why this is filed now rather than after v0.12.0:
every issue built on the current model — #290's `Copy` rules, #291's move checking, #292's
drop — encodes the assumption that a sequence both owns and is freely copied.

---

## Open Questions

1. **Is there a mutable slice, and how is it spelled?** `&var`-flavoured, or does mutation
   require going through `List<T>`? RFC-0045's `&var`-on-field-paths and RFC-0110's explicit
   dereference are the neighbouring decisions.
2. **What is the relationship to RFC-0067's lifetime anchors?** A slice is the first type
   whose validity is scoped to another value's lifetime. This RFC probably *depends* on
   RFC-0067 rather than merely touching it; that needs confirming before acceptance.
3. **Does `[T; N]` need const-generic `N`?** Today only literal arities parse — measured
   2026-07-25, `extend<T: Copy> [T; 2]: Copy;` works and `[T; N]` does not. Without const
   generics, "fixed arrays are `Copy` when their elements are" cannot be written in stdlib
   and stays hardcoded, the same situation #296 and RFC-0061 describe for structural impls.
4. **Which release?** The migration argues for early; the dependency on RFC-0067/RFC-0122
   argues for later. Sequencing against **#291** is the decision that matters, since move
   checking is what would otherwise bake in the current model.
5. **Is `Value::Array`'s `Rc<RefCell<Vec>>` representation retained?** A borrowed slice needs
   no refcounting. Keeping it may simplify the tree-walking evaluator, at the cost of
   representing something the type system would no longer admit.
6. ~~Does anything depend on `T[]` being mutable today?~~ **Measured 2026-07-25: almost
   nothing.** `stdlib/` contains **zero** index-assignments through a sequence, and the whole
   test corpus contains **17**, across nine fixtures — most of which exist precisely to test
   index assignment, `&var` lvalue paths, or explicit dereference, and several of which are
   about sized arrays rather than `T[]`. Making slices immutable is therefore a far smaller
   break than the type change in §4; the literal-typing migration dominates the cost, not the
   mutability rule.

---

## References

- RFC-0054 (Standard `List<T>` Type), `4-implemented` — assigned growth to `List<T>` and
  declared `T[]` the immutable read-only view. This RFC finishes what it started.
- RFC-0071 (Ownership and Move Semantics), `3-integrated` — §2's `Copy` rules are what this
  unblocks; §1's move-by-default is what deep-copy-on-binding contradicts.
- RFC-0122 (Borrow Checking), `0-draft` — shares the cloning-evaluator problem.
- RFC-0067 (Lifetime Anchors), `2-accepted` — the likely dependency for slice validity.
- RFC-0063 (Allocator Handles), `2-accepted` — where a `List<T>`'s buffer ultimately comes
  from.
- Issues #290 (blocked on this question), #291 (would bake in the current model), #296
  (structural impls, related via the `[T; N]` blanket).

---

## Decision

**Outcome:** *(pending)*
**Target:** *(set when accepted)*
