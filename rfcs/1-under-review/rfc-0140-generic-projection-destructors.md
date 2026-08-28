---
id: rfc-0140
title: "Generic-Projection Destructors"
date: '2026-08-28'
status: under-review
target:
updated: '2026-08-28'
tracking: 'https://github.com/metel-lang/metel-core/issues/884'
---

> **New RFC, opened 2026-08-28 alongside RFC-0139 out of the same design discussion on
> RFC-0137 §5 / `metel-core#858`.** RFC-0139 (Row-Polymorphic Self-Views) is the general
> mechanism — a lower-bounded row parameter in receiver position. This RFC is its one
> concrete application: letting `Drop::drop` declare its required field set on its
> signature instead of the compiler inferring it from the destructor body.
>
> **Framing: additive, not a replacement.** RFC-0137 §5 already specifies row-bounded
> `Drop` dispatch with a *body-inferred* required set. This RFC adds a third way to
> author the same dispatch, and dissolves RFC-0137's Open Question 2 (transitive
> required-set through helper calls) for destructors that adopt it. Nothing in
> `metel-core#858` is blocked on this RFC; it can follow RFC-0137 §5 by a release or
> more.
>
> **Overlap check (`INDEX.md` records cluster + `REGISTRY.md`, manual):**
> - **RFC-0137 §5** owns the dispatch *rule* (residual row ⊇ required set). This RFC
>   changes only where the required set *comes from*, not the rule.
> - **RFC-0139** owns the `<row R>` receiver mechanism this RFC specializes to `drop`.
>   Hard dependency.
> - **RFC-0071 §7** is the blanket "no partial move of a `Drop` value" rule RFC-0137 §5
>   already supersedes; this RFC inherits that supersession unchanged.
> - **RFC-0109** owns the fixed-projection receiver form, which is the middle rung of the
>   three-form ladder below.
> - **RFC-0121** is the row-kind dependency, reached transitively through RFC-0139.

> **Status — under review (2026-08-28).** Substantiated primary proposal (three-form ladder, unchanged move-check rule, worked examples) with explicit blocking open questions; additive to RFC-0137 §5. Tracking: metel-core#884.

## Summary

`Drop::drop` may declare its receiver as a lower-bounded row parameter:

```metel
extend Handle: Drop {
    fun drop<row R>(&var self: Self.R) where R: { fd, .. } {
        sys_close(self.fd)
    }
}
```

This destructor is valid against **any** residual of `Handle` whose row still contains
`fd`. A partial move that leaves `fd` intact (`let n = h.name;`) is permitted; one that
removes `fd` is rejected. The required field set is `{ fd }` because the signature
*says so* — the compiler does not read the body to find out.

`Drop::drop` now has three authoring forms, one dispatch rule underneath:

| Form | Required field set | Partial move of a `Drop` value |
|---|---|---|
| `fun drop(&var self)` | the full declared row | always rejected (RFC-0071 §7 status quo) |
| `fun drop(&var self: Self.{ fd })` *(RFC-0109 + RFC-0137)* | `{ fd }`, exact | allowed iff residual ⊇ `{ fd }` |
| `fun drop<row R>(&var self: Self.R) where R: { fd, .. }` *(this RFC)* | `{ fd }`, lower bound | allowed iff residual ⊇ `{ fd }` |

The move-check rule — **residual row ⊇ required set** — is identical in all three rows.
Only the *source* of the required set differs: the whole row / a fixed projection / a
declared lower bound. RFC-0137 §5's body-inference is a fourth source of the same set,
compatible with all of these.

---

## Motivation

RFC-0137 §5 computes a `Drop` impl's required field set by static analysis of the
destructor body — "the union of fields the destructor actually reads, conservatively
across every branch." Its Open Question 2 concedes the hard part: when the destructor
calls a helper method, that set must compose transitively across the call, which is
"real, call-graph-level work, closer to effect inference than ordinary type-checking."

Making the required set a **declared contract** on the `drop` signature removes three
problems at once:

1. **No transitive body analysis.** Each helper method the destructor calls states its
   own receiver lower bound (RFC-0139 §2). Composition is a local containment check per
   call site, not a fixed point over the type's method graph. RFC-0137 OQ2 is dissolved,
   not solved.
2. **No action-at-a-distance.** Under body-inference, adding a `self.name` read to a
   `drop` body silently shrinks the set of partial moves that are legal *elsewhere in the
   program*. With a declared bound, that read is either within the bound (no effect
   elsewhere) or a compile error at the read — the legality of far-away partial moves
   only ever changes through a visible signature edit.
3. **Explicit opt-in to narrowing tolerance.** A destructor that needs the whole value
   says so by taking `&var self` (rung 1). A destructor that tolerates narrowing states
   exactly how much. The author decides; the compiler does not infer intent from
   whatever the body happens to touch this week.

This mirrors RFC-0071's settled position that `Copy` is *declared*, never derived — the
same reasoning applied to "which fields does teardown require."

---

## 1. Syntax

Exactly RFC-0139's receiver-row form, with `drop` as the method and `std::core::Drop` as
the aspect:

```
"fun" "drop" "<" "row" ident ">" "(" "&var" "self" ":" "Self" "." ident ")"
    "where" ident ":" "{" field-list "," ".." "}" block
```

- The `where` lower bound is **mandatory** for `drop<row R>` — a destructor with an
  empty required set that still has a non-empty body is meaningless, and one with an
  empty body should use rung 1 (`fun drop(&var self) {}`, the type-level-only
  declaration, RFC-0071 §5 / the `reject_inert_destructor` gate).
- `&self` (shared) is not a valid destructor receiver; only `&var self` (matching the
  `std::core::Drop` aspect signature today).

---

## 2. Static semantics

**Body check (RFC-0139 §2, unchanged).** The destructor body is checked once against
`self: Self.<lower-bound-row>`. Every `self.<field>` read or write must be in the `where`
lower bound; every `self.helper(...)` call must have `helper`'s own receiver lower bound
⊆ this `where` bound.

**Move-check rule (RFC-0137 §5, unchanged in substance).** At each partial-move site of a
value whose type is a `Drop`-implementing struct (or a residual of one), under
`--move-check`:

- Let `req` be the destructor's declared `where` lower bound.
- The partial move is permitted iff the resulting residual row ⊇ `req`.
- Otherwise it is rejected with `MoveViolationKind::PartialMoveOfDropType` — same error
  code and message as today; only the condition that triggers it is relaxed from
  "always, for any `Drop` type" (RFC-0071 §7) to "only when a required field would be
  gone."

**`!Drop` and `Copy`/`Drop` exclusion are unaffected.** Adopting the parametric form does
not change *whether* the type implements `Drop`; it only changes which partial moves of
it are legal. RFC-0072's `!Drop` bound and RFC-0071 §4's `Copy`/`Drop` mutual exclusion
see the type exactly as they do for rungs 1 and 2.

---

## 3. No per-residual monomorphization

`R` is erased (RFC-0139 §3). There is exactly one compiled destructor body, checked
against the lower bound. A call site / drop site with a wide residual and one with a
narrow residual invoke the same body.

Once destructor invocation lands (`metel-core#261`), the drop glue calls that single
body. The fields absent from a given residual are, by the body check, fields the
destructor provably never names — so there is nothing to specialize and nothing unsound
to read. The parametric form is not more expensive at runtime than the fixed-projection
form; it is a signature-ergonomics choice, not a codegen one.

---

## 4. One `Drop` impl per type — the forms are a choice, not an overload

A type has at most one `Drop` impl (RFC-0060 coherence). The three forms in the Summary
are alternative ways to *write* that one impl, selected by the author. There is no
overloading, no dispatch ambiguity, and no coherence question introduced by this RFC.

A generic `Drop` impl (`extend<T> Pair<T>: Drop`) may use `drop<row R>`; per RFC-0137 §7
and RFC-0139 §4 the `where` lower bound is a fixed set of field names and must not depend
on `T`.

---

## 5. Relationship to RFC-0137 §5

RFC-0137 §5 stays the section that establishes row-bounded `Drop` dispatch and supersedes
RFC-0071 §7. This RFC is an **alternative declaration surface** for the required set that
section already defines:

- If RFC-0137 §5 ships first with body-inference (the `metel-core#858` plan), this RFC
  later adds `drop<row R>` as an opt-in form. The move-check rule does not change, so it
  is a pure addition — no migration, no behavior change for existing `Drop` impls.
- RFC-0137 Open Question 2 (transitive required-set through helper calls) is marked
  **resolved-by-RFC-0140** for any destructor that adopts the parametric form:
  composition becomes local via RFC-0139's per-callee bounds. Body-inference destructors
  still carry OQ2 as originally stated.
- RFC-0137 §5's prose should gain a forward pointer to this RFC when this RFC is
  accepted, the same way §5 already forward-points RFC-0114 for widening.

---

## Out of Scope

- **Whole-body destructor semantics, drop order, explicit `drop(x)`** — `metel-core#261`
  / RFC-0071 (3/4). This RFC does not make any `drop` body run; it only governs which
  partial moves the move checker permits ahead of that.
- **Widening a residual before it is dropped** — RFC-0114's `construct` path.
- **Running different destructor code per residual shape** — explicitly rejected. `R` is
  erased; there is one body.
- **Row parameters outside the receiver** — RFC-0139 Out of Scope, inherited.
- **`dyn Aspect` `Drop`-pointer interaction** (RFC-0008 §"a pointer to the `Drop`
  destructor") — a `dyn` value erases the residual shape, so a parametric destructor
  reached through a trait object may need the runtime row representation RFC-0137 §8
  flags. Same open flag as RFC-0137's; not resolved here.

---

## Open Questions

1. **Depends on RFC-0139.** *(Blocked on a dated dependency.)* Which itself depends on
   RFC-0121 or a carve-out. This RFC cannot be accepted before RFC-0139 is.
2. **Do rungs 2 and 3 both survive?** The fixed-projection form (`self: Self.{ fd }`,
   RFC-0109 + RFC-0137) needs no `row` kind and could ship with RFC-0137 §5; the
   parametric form waits on RFC-0139. Decide whether the fixed form is kept as a distinct
   spelling (lets narrowing-tolerant destructors exist before RFC-0121 lands) or folded
   into the parametric form as sugar once both are available. Mirrors RFC-0139 Open
   Question 5.
3. **Does the `reject_inert_destructor` gate need adjustment?** Today
   (`metel-core#292`/`#261`) a non-empty `drop` body is rejected outright, so no
   destructor reads any field and every required set is trivially empty. Under that gate,
   `drop<row R> where R: { fd, .. }` with an empty body is checkable and meaningful (the
   *bound* is the contract; the empty body trivially satisfies it), which lets
   `metel-core#858`'s reject-path fixture be written now:
   `drop<row R>(&var self: Self.R) where R: { fd, name, .. } {}` then `let n = h.name;`
   is still rejected. Confirm this is the intended interaction and that the gate stays
   otherwise unchanged until `#261`.
4. **Interaction with a generic `Drop` impl's own `where` clause.** `extend<T: Bound>
   Pair<T>: Drop` already has a `where` for the *type* bound; `drop<row R> where R: {
   … }` adds a *row* `where`. Confirm the grammar composes cleanly (two `where` clauses,
   or one with mixed constraints) and pick one.

---

## References

- RFC-0139 (Row-Polymorphic Self-Views, under review) — the receiver-row mechanism this RFC
  specializes to `drop`; hard dependency
- RFC-0137 (Nominal Types as Branded Rows, under review) — §5 row-bounded `Drop`
  dispatch (the rule this RFC re-sources), §7 generic structs, Open Question 2 (dissolved
  here for the parametric form)
- RFC-0071 (Ownership and Move Semantics, `3-integrated`, partial-move tracking not yet
  implemented) — §7 blanket partial-move-with-`Drop` ban (superseded via RFC-0137 §5),
  §4 `Copy`/`Drop` exclusion, §5 `Drop` declaration
- RFC-0109 (Self-View Narrowing, draft) — the fixed-projection receiver form (rung 2)
- RFC-0072 (Negative Bounds, implemented) — `!Drop`, unaffected by form choice
- RFC-0060 (Aspect Impl Coherence, implemented) — one `Drop` impl per type
- RFC-0121 (Open Rows, under review) — row-kind dependency, reached through RFC-0139
- RFC-0008 (Aspect Objects, deferred) — the `dyn` `Drop`-pointer flag in Out of Scope
- `metel-core#858` — RFC-0137 slice 2 (row-bounded `Drop` dispatch) implementation issue;
  not blocked on this RFC
- `metel-core#261` — RFC-0071 (3/4): drop order and explicit drop; destructor invocation
  must land before any `drop` body runs
- `metel-core#292` — the `reject_inert_destructor` gate (non-empty `drop` bodies rejected
  until `#261`); Open Question 3

---

## Decision

**Outcome:** *(pending)*
**Target:** *(set when accepted)*
