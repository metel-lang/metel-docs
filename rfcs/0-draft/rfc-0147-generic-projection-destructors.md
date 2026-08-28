---
id: rfc-0147
title: "Generic-Projection Destructors"
date: '2026-08-28'
status: draft
target:
---

> **New RFC, opened 2026-08-28 alongside RFC-0146 out of a design discussion on the
> integrated spec's "Drop dispatch against a narrowed residual" section
> (`reference/spec/ownership.md`, from RFC-0137) and `metel-core#858`.** RFC-0146
> (Row-Polymorphic Self-Views) is the general mechanism — a lower-bounded row parameter
> in receiver position. This RFC is its one concrete application: letting `Drop::drop`
> declare its required field set on its signature instead of the compiler computing it
> from the destructor body.
>
> **Framing: an alternative declaration surface, not a new rule.** The integrated spec
> already fixes row-bounded `Drop` dispatch and *computes* the required set — including,
> as of 2026-08-25, transitively through `self`-method calls
> (`spec.ownership.drop-dispatch-against-a-narrowed-residual.legality-1`). This RFC adds
> a way to *state* that set instead, and keeps the dispatch rule
> (`…dynamics-1`) and the `dyn Aspect` coercion checkpoint (`…legality-2`) untouched.
> Nothing in `metel-core#858` is blocked on this RFC; it can follow slice 2 by a release
> or more.
>
> **Overlap check (`rfc.py new` similarity + `INDEX.md` + `REGISTRY.md`):**
> - **RFC-0146** owns the `<row R>` receiver mechanism this RFC specializes to `drop`.
>   Hard dependency.
> - **RFC-0137 (`3-integrated`)** / `reference/spec/ownership.md` own the dispatch
>   *rule*; this RFC changes only where the required set comes from.
> - **RFC-0072 (Negative Bounds, implemented)** — `!Drop`; unaffected by which form a
>   `Drop` impl is authored in (§2).
> - **RFC-0049 (`linear fun` Type System, draft)** — flagged by similarity for touching
>   `Drop`-on-closures; no interaction (closures have no named residual and no `drop`
>   signature to annotate).
> - **RFC-0008 (Aspect Objects, `2-accepted`; slice 1 implemented, `metel-core#865`)** —
>   the `dyn Aspect` drop-pointer and the coercion checkpoint this RFC's declared bound
>   feeds.

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

`Drop::drop` then has three authoring forms, one dispatch rule underneath:

| Form | Required field set | Partial move of a `Drop` value |
|---|---|---|
| `fun drop(&var self)` | the full declared row | always rejected (RFC-0071 §7 status quo) |
| `fun drop(&var self: Self.{ fd })` *(via RFC-0109 named view)* | `{ fd }`, exact | allowed iff residual ⊇ `{ fd }` |
| `fun drop<row R>(&var self: Self.R) where R: { fd, .. }` *(this RFC)* | `{ fd }`, lower bound | allowed iff residual ⊇ `{ fd }` |

The dispatch rule — **residual row ⊇ required set** — is the integrated spec's
(`spec.ownership.drop-dispatch-against-a-narrowed-residual.dynamics-1`), identical for
all three. Only the *source* of the required set differs: the whole row / a fixed
residual / a declared lower bound. The spec's body-computed set is a fourth source of
the same set, and the default when a `drop` impl uses neither projection form.

---

## Motivation

The integrated spec computes a `Drop` impl's required field set by static analysis of
the destructor body: "the union of the fields its destructor body reads directly and,
recursively, the required sets of every `self`-method it calls"
(`…legality-1`). That is real call-graph work — a fixed point over one type's own method
set, "closer to effect inference than ordinary type-checking" (RFC-0137 §5).

Making the required set a **declared contract** on the `drop` signature is an
alternative with three properties the computed form does not have:

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

`reference/spec/ownership.md`'s "Drop dispatch against a narrowed residual" stays the
normative section. This RFC is an **alternative declaration surface** for the required
set that section defines:

- If slice 2 (`metel-core#858`) ships the body-computed form first, this RFC later adds
  `drop<row R>` as an opt-in form. The dispatch rule and the coercion checkpoint do not
  change, so it is a pure addition — no migration, no behavior change for existing
  `Drop` impls.
- The spec's transitive-`self`-method composition (`…legality-1`) stays as the rule for
  a destructor authored in form 1 with a non-empty body. A destructor in the parametric
  form declares its bound instead of having it computed; the two must agree where both
  could be computed (the declared bound must be ⊇ what the body would require), which the
  §2 body check already enforces.
- `reference/spec/ownership.md` should gain a one-line forward pointer to this RFC at
  that section when this RFC is accepted, the way the section already forward-points the
  `dyn Aspect` checkpoint.

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
   `drop` body is rejected outright, so no destructor reads any field and every computed
   required set is trivially empty. Under that gate, `drop<row R> where R: { fd, .. }`
   with an *empty* body is still checkable and meaningful — the *bound* is the contract —
   which lets `metel-core#858`'s reject-path test be written before destructor
   invocation lands: `drop<row R>(&var self: Self.R) where R: { fd, name, .. } {}` then
   `let n = h.name;` is still rejected. Confirm this is the intended interaction and the
   gate is otherwise unchanged until `#261`.
4. **Grammar for a generic `Drop` impl's two `where` clauses.** `extend<T: Bound>
   Pair<T>: Drop` already has a type `where`; `drop<row R> where R: { … }` adds a row
   `where`. One combined clause or two — pick one.
5. **Coercion-checkpoint diagnostics.** The spec's `…legality-2` rejects a too-narrow
   `dyn Aspect` coercion; with the declared form the message can name the destructor's
   own `where` clause. Worth specifying the diagnostic shape, or leave to implementation.

---

## References

- `reference/spec/ownership.md` — "Drop dispatch against a narrowed residual"
  (`…legality-1` computed required set, `…dynamics-1` dispatch rule, `…legality-2` `dyn
  Aspect` coercion checkpoint); "`Drop`", "`Copy` and `Drop` are mutually exclusive",
  "Partial moves", "Widening"
- RFC-0146 (Row-Polymorphic Self-Views, draft) — the receiver-row mechanism this RFC
  specializes to `drop`; hard dependency
- RFC-0137 (Nominal Types as Branded Rows, `3-integrated`) — §5 (design history for the
  spec section above), §7 (generic structs), Open Question 6 (generic-conditional
  `Drop`, inherited unresolved)
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
