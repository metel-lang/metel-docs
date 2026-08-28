---
id: rfc-0147
title: "Generic-Projection Destructors"
date: '2026-08-28'
status: under-review
target:
updated: '2026-08-28'
tracking: 'https://github.com/metel-lang/metel-core/issues/887'
---

> **New RFC, opened 2026-08-28 alongside RFC-0146 out of a design discussion on the
> "Drop dispatch against a narrowed residual" spec section
> (`reference/spec/ownership.md`, from RFC-0137) and `metel-core#858`.** RFC-0146
> (Row-Polymorphic Self-Views) is the general mechanism — a lower-bounded row parameter
> in receiver position. This RFC is its one concrete application: `Drop::drop`.
>
> **This RFC and the 2026-08-28 amendment to RFC-0137 §5 are one design change.**
> RFC-0137 §5 (and its integrated
> `spec.ownership.drop-dispatch-against-a-narrowed-residual.legality-1`) previously
> *computed* a `Drop` impl's required field set from the destructor body — a fixed point
> over `self`-method calls, resolved 2026-08-25. That was amended: **the required set is
> now declared on the `drop` receiver type.** RFC-0109 (Self-View Narrowing) supplies the
> fixed named-view form of that receiver; this RFC supplies the parametric `<row R>` form
> and carries the `drop`-specific rules (body check, move-check relaxation, `dyn Aspect`
> checkpoint, one-impl-per-type) and the rationale for the change. The dispatch rule
> (residual row ⊇ required set) and the `dyn Aspect` checkpoint (`…legality-2`) are
> unchanged. Nothing in `metel-core#858` is blocked on *this* RFC — the fixed form needs
> only RFC-0109 + the amended §5 — but the `Drop` half of #858 should not implement the
> old body-computed set.
>
> **Overlap check (`rfc.py new` similarity + `INDEX.md` + `REGISTRY.md`):**
> - **RFC-0146** owns the `<row R>` receiver mechanism this RFC specializes to `drop`.
>   Hard dependency.
> - **RFC-0137 (`3-integrated`) §5** / `reference/spec/ownership.md` own the dispatch
>   *rule*, amended 2026-08-28 to the declared-receiver required set this RFC's
>   parametric form plugs into.
> - **RFC-0072 (Negative Bounds, implemented)** — `!Drop`; unaffected by which form a
>   `Drop` impl is authored in (§2).
> - **RFC-0049 (`linear fun` Type System, draft)** — flagged by similarity for touching
>   `Drop`-on-closures; no interaction (closures have no named residual and no `drop`
>   signature to annotate).
> - **RFC-0008 (Aspect Objects, `2-accepted`; slice 1 implemented, `metel-core#865`)** —
>   the `dyn Aspect` drop-pointer and the coercion checkpoint this RFC's declared bound
>   feeds.

> **Status — under review (2026-08-28).** Substantiated primary proposal (parametric `<row R>` form of RFC-0137 §5's declared-receiver `Drop` required set, three-form ladder, worked examples) with explicit blocking open questions. Paired with the 2026-08-28 amendment to RFC-0137 §5. Tracking: metel-core#887.

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
*says so* — the compiler does not read the body to find out, and does not compute a
fixed point over `self`-method calls.

`Drop::drop` has three authoring forms, one dispatch rule underneath:

| Form | Required field set | Partial move of a `Drop` value |
|---|---|---|
| `fun drop(&var self)` | the full declared row | always rejected (RFC-0071 §7 status quo) |
| `fun drop(&var self: Self.{ fd })` *(via RFC-0109 named view)* | `{ fd }`, exact | allowed iff residual ⊇ `{ fd }` |
| `fun drop<row R>(&var self: Self.R) where R: { fd, .. }` *(this RFC)* | `{ fd }`, lower bound | allowed iff residual ⊇ `{ fd }` |

The dispatch rule — **residual row ⊇ required set** — is the spec's
(`spec.ownership.drop-dispatch-against-a-narrowed-residual.dynamics-1`), identical for
all three. The only difference between the forms is how the required set is spelled:
the whole row (default), a fixed residual, or a lower-bounded row parameter. There is no
body-derived set — RFC-0137 §5's amendment of 2026-08-28 removed it.

---

## Motivation

Until 2026-08-28, RFC-0137 §5 (and its integrated `…legality-1`) computed a `Drop`
impl's required field set by static analysis of the destructor body: "the union of the
fields its destructor body reads directly and, recursively, the required sets of every
`self`-method it calls". That is real call-graph work — a fixed point over one type's
own method set, "closer to effect inference than ordinary type-checking" (RFC-0137 §5,
as it then read).

RFC-0137 §5 was amended to make the required set a **declared contract** on the `drop`
signature instead. Three properties the computed form did not have motivated the change:

1. **No fixed-point computation.** Each helper method the destructor calls states its
   own receiver lower bound (RFC-0146 §2). Composition is a local containment check per
   call site. The compiler never has to walk the type's method graph to a fixed point to
   know what a destructor requires.
2. **No action-at-a-distance.** With the computed form, adding a `self.name` read to a
   `drop` body (or to a helper it calls) silently shrinks the set of partial moves that
   are legal *elsewhere in the program*. With a declared bound, that read is either
   within the bound (no effect elsewhere) or a compile error at the read — the legality
   of far-away partial moves only changes through a visible signature edit.
3. **Explicit opt-in to narrowing tolerance.** A destructor that needs the whole value
   says so by taking `&var self` (form 1). A destructor that tolerates narrowing states
   exactly how much. The author decides; the compiler does not infer intent from
   whatever the body happens to touch.

This mirrors RFC-0071's settled position that `Copy` is *declared*, never derived — the
same reasoning applied to "which fields does teardown require."

The declared bound is also directly what the spec's **`dyn Aspect` coercion checkpoint**
(`…legality-2`) needs: coercing a `Drop`-implementing value to `dyn Aspect` is rejected
when the value's current row does not satisfy the impl's required set. With the computed
form that set is a whole-body analysis result; with the declared form it is right there
in the signature the checkpoint is already looking at.

---

## 1. Syntax

Exactly RFC-0146's receiver-row form, with `drop` as the method and `std::core::Drop` as
the aspect:

```
"fun" "drop" "<" "row" ident ">" "(" "&var" "self" ":" "Self" "." ident ")"
    "where" ident ":" "{" field-list "," ".." "}" block
```

- The `where` lower bound is **mandatory** for `drop<row R>` — a destructor with an
  empty required set that still has a non-empty body is meaningless, and one with an
  empty body should use form 1 (`fun drop(&var self) {}`, the type-level-only
  declaration; see `reference/spec/ownership.md` "`Drop`" and the interpreter's
  `reject_inert_destructor` gate, `metel-core#292`).
- `&self` (shared) is not a valid destructor receiver; only `&var self`, matching the
  `std::core::Drop` aspect signature.

---

## 2. Static semantics

**Body check (RFC-0146 §2, unchanged).** The destructor body is checked once against
`self: Self.<lower-bound-row>`. Every `self.<field>` read or write must be in the `where`
lower bound; every `self.helper(...)` call must have `helper`'s own receiver lower bound
⊆ this `where` bound.

**Move-check rule (spec `…dynamics-1`, substance unchanged).** At each partial-move site
of a value whose type is a `Drop`-implementing struct (or a residual of one), under
`--move-check`:

- Let `req` be the destructor's declared `where` lower bound.
- The partial move is permitted iff the resulting residual row ⊇ `req`.
- Otherwise it is rejected with `MoveViolationKind::PartialMoveOfDropType` — same error
  code and message as today; only the condition that triggers it is relaxed from
  "always, for any `Drop` type" (RFC-0071 §7) to "only when a required field would be
  gone."

**`dyn Aspect` coercion checkpoint (spec `…legality-2`, unchanged).** Coercing a value
of this type to any `dyn Aspect` is rejected when the value's current row does not
satisfy `req`. The declared bound *is* `req`; no extra analysis at the coercion site.

**`!Drop` and `Copy`/`Drop` exclusion are unaffected.** Adopting the parametric form
does not change *whether* the type implements `Drop`; it only changes which partial moves
of it are legal. RFC-0072's `!Drop` bound and the spec's "`Copy` and `Drop` are mutually
exclusive" rule see the type exactly as they do for forms 1 and 2.

---

## 3. No per-residual monomorphization

`R` is erased (RFC-0146 §3). There is exactly one compiled destructor body, checked
against the lower bound. A drop site with a wide residual and one with a narrow residual
invoke the same body.

Once destructor invocation lands (`metel-core#261`), the drop glue calls that single
body. The fields absent from a given residual are, by the body check, fields the
destructor provably never names — so there is nothing to specialize and nothing unsound
to read. The parametric form is not more expensive at runtime than form 2; it is a
signature-ergonomics choice, not a codegen one.

---

## 4. One `Drop` impl per type — the forms are a choice, not an overload

A type has at most one `Drop` impl (`reference/spec/declarations.md`, Aspect
Implementation Coherence). The three forms in the Summary are alternative ways to *write*
that one impl, selected by the author. No overloading, no dispatch ambiguity, no
coherence question introduced by this RFC.

A generic `Drop` impl (`extend<T> Pair<T>: Drop`) may use `drop<row R>`; per RFC-0137 §7
and RFC-0146 §4 the `where` lower bound is a fixed set of field names and must not depend
on `T`. This RFC does not resolve RFC-0137's Open Question 6 (whether a `Drop` impl
*conditional* on `T`'s own `Drop`-ness needs pre-substitution reasoning) — it inherits
that question's "verification pending `#261`" status unchanged.

---

## 5. Relationship to the integrated spec

`reference/spec/ownership.md`'s "Drop dispatch against a narrowed residual" is the
normative section, amended 2026-08-28 in lockstep with RFC-0137 §5 to state the
declared-receiver required set. This RFC does not change that rule; it defines the
**parametric `<row R>` form** of the declared receiver and the `drop`-specific details
the spec section states only briefly.

- The fixed form (`fun drop(&var self: Self.{ fd })`, RFC-0109 named view) needs no
  `row` kind and is implementable with the amended §5 alone. The `Drop` half of slice 2
  (`metel-core#858`) should implement *that*, not the old body-computed set. This RFC's
  parametric form is a later addition on top, gated on RFC-0146.
- There is **no body-computed set** to reconcile against: RFC-0137 §5's amendment
  removed it, and Open Question 2's 2026-08-25 fixed-point resolution is marked
  superseded there. A destructor's body is checked *against* its declared receiver row
  (§2), not mined for one.
- `reference/spec/ownership.md` may gain a one-line forward pointer to this RFC for the
  parametric spelling once this RFC is accepted; the fixed-form rule is already in the
  section.

---

## Out of Scope

- **Whole-body destructor semantics, drop order, explicit `drop(x)`** — `metel-core#261`
  / RFC-0071 (3/4). This RFC does not make any `drop` body run; it only governs which
  partial moves and `dyn` coercions the checker permits ahead of that.
- **Widening a residual before it is dropped** — the spec's "Widening" / RFC-0114's
  `construct` path.
- **Running different destructor code per residual shape** — explicitly rejected. `R` is
  erased; there is one body.
- **Row parameters outside the receiver** — RFC-0146 Out of Scope, inherited.
- **RFC-0137 Open Question 6** (generic-conditional `Drop`) — inherited, not resolved
  here (§4).

---

## Open Questions

1. **Depends on RFC-0146.** *(Blocked on a dated dependency.)* Which itself depends on
   RFC-0121 or a carve-out. This RFC cannot be accepted before RFC-0146 is.
2. **Do forms 2 and 3 both survive?** The fixed-residual form (RFC-0109 named view, or a
   bare `Self.{ fd }` receiver) needs no `row` kind and could ship with slice 2; the
   parametric form waits on RFC-0146. Decide whether the fixed form stays a distinct
   spelling (lets narrowing-tolerant destructors exist before RFC-0121 lands) or is
   folded into the parametric form as sugar once both are available. Mirrors RFC-0146
   Open Question 5.
3. **`reject_inert_destructor` interaction.** Today (`metel-core#292`/`#261`) a non-empty
   `drop` body is rejected outright. The declared-receiver required set does not depend
   on the body, so `drop<row R> where R: { fd, .. }` with an *empty* body is still
   checkable and meaningful — the *bound* is the contract — which lets `metel-core#858`'s
   reject-path test be written before destructor invocation lands:
   `drop<row R>(&var self: Self.R) where R: { fd, name, .. } {}` then `let n = h.name;`
   is still rejected. Confirm this is the intended interaction and the gate is otherwise
   unchanged until `#261`.
4. **Grammar for a generic `Drop` impl's two `where` clauses.** `extend<T: Bound>
   Pair<T>: Drop` already has a type `where`; `drop<row R> where R: { … }` adds a row
   `where`. One combined clause or two — pick one.
5. **Coercion-checkpoint diagnostics.** The spec's `…legality-2` rejects a too-narrow
   `dyn Aspect` coercion; with the declared form the message can name the destructor's
   own `where` clause. Worth specifying the diagnostic shape, or leave to implementation.

---

## References

- `reference/spec/ownership.md` — "Drop dispatch against a narrowed residual"
  (`…legality-1` declared-receiver required set, `…dynamics-1` dispatch rule,
  `…legality-2` `dyn Aspect` coercion checkpoint); "`Drop`", "`Copy` and `Drop` are
  mutually exclusive", "Partial moves", "Widening"
- RFC-0146 (Row-Polymorphic Self-Views, `1-under-review`) — the receiver-row mechanism
  this RFC specializes to `drop`; hard dependency
- RFC-0137 (Nominal Types as Branded Rows, `3-integrated`) — §5 (amended 2026-08-28 to
  the declared-receiver required set this RFC's parametric form plugs into; Open
  Question 2 superseded there), §7 (generic structs), Open Question 6
  (generic-conditional `Drop`, inherited unresolved)
- RFC-0071 (Ownership and Move Semantics, `3-integrated`, partial-move tracking not yet
  implemented, `metel-core#858`) — §7 blanket partial-move-with-`Drop` ban (superseded
  in design by the spec section), `Copy`/`Drop` exclusion
- RFC-0109 (Self-View Narrowing, `1-under-review`, `metel-core#842`) — the fixed-residual
  receiver form (form 2)
- RFC-0072 (Negative Bounds, implemented) — `!Drop`, unaffected by form choice
- RFC-0008 (Aspect Objects, `2-accepted`; slice 1 `metel-core#865`, coercion
  `metel-core#863`) — the `dyn Aspect` drop-pointer and coercion checkpoint
- RFC-0121 (Open Rows, `1-under-review`, `metel-core#792`) — row-kind dependency, reached
  through RFC-0146
- `metel-core#858` — RFC-0137 slice 2 (move-triggered narrowing/widening, row-bounded
  `Drop` dispatch); not blocked on this RFC
- `metel-core#261` — RFC-0071 (3/4): drop order and explicit drop; destructor invocation
  must land before any `drop` body runs
- `metel-core#292` — the `reject_inert_destructor` gate (non-empty `drop` bodies rejected
  until `#261`); Open Question 3

---

## Decision

**Outcome:** *(pending)*
**Target:** *(set when accepted)*
