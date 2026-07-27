---
id: rfc-0124
title: "Sequence Types: Fixed Arrays, Slices, and the Growable List"
date: '2026-07-25'
status: draft
target:
updated: '2026-07-27'
---

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
| Does `[T; N]: Copy` need const generics to leave the typechecker's hardcoded case (#299)? | open — §Open Questions 3 |
| `Value::Array`'s evaluator representation | open — §Open Questions 4 |
| Release sequencing against #291 and #310 | open — §Open Questions 5 |

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
   and stays hardcoded (#299), the same situation #296 and RFC-0061 describe for structural
   impls. Unaffected by RFC-0126, which changes `T[]`'s role, not `[T; N]`'s.
4. **Is `Value::Array`'s `Rc<RefCell<Vec>>` representation retained?** A borrowed slice needs
   no refcounting. Keeping it may simplify the tree-walking evaluator, at the cost of
   representing something the type system would no longer admit once RFC-0126 lands.
5. **Which release, and in what order against #291/#310?** RFC-0126's migration argues for
   landing early (it unblocks six of #310's fixtures directly); the dependency on RFC-0067
   (Open Question 2 above) argues for later, at least for a mutable-slice variant. The
   sequencing decision that matters is against **#291**, since move checking is what would
   otherwise bake in the pre-RFC-0126 model permanently.

---

## References

- **RFC-0126 (T[] as a Copy Borrowed View), `0-draft`** — split from this RFC; the role
  assignment, prior art, and migration-cost estimate now live there.
- RFC-0054 (Standard `List<T>` Type), `4-implemented` — assigned growth to `List<T>` and
  declared `T[]` the immutable read-only view; RFC-0126 is that assignment taken at face
  value.
- RFC-0071 (Ownership and Move Semantics), `3-integrated` — §2's `Copy` rules are what
  RFC-0126 unblocks.
- RFC-0122 (Borrow Checking), `0-draft` — shares the cloning-evaluator problem; Open
  Question 2 here is its likely resolution path.
- RFC-0067 (Lifetime Anchors), `2-accepted` — the likely dependency for slice validity
  (Open Question 2).
- RFC-0063 (Allocator Handles), `2-accepted` — where a `List<T>`'s buffer ultimately comes
  from.
- Issues #291 (sequencing, Open Question 5), #296 (structural impls, related to Open
  Question 3 via the `[T; N]` blanket), #299 (`[T; N]`'s hardcoded `Copy` rule, Open
  Question 3).

---

## Decision

**Outcome:** *(pending)*
**Target:** *(set when accepted)*
