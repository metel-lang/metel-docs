---
id: rfc-0147
title: "Projection-Receiver Destructors"
date: '2026-08-28'
status: under-review
target:
updated: '2026-08-28'
tracking: 'https://github.com/metel-lang/metel-core/issues/887'
---

> **New RFC, opened 2026-08-28 out of a design discussion on the "Drop dispatch against a
> narrowed residual" spec section (`reference/spec/ownership.md`, from RFC-0137) and
> `metel-core#858`. Split 2026-08-28 into the *projection* form (this RFC) and the
> *row-parametric* form (RFC-0148), so each depends only on the feature RFC it actually
> needs.**
>
> **This RFC and the 2026-08-28 amendment to RFC-0137 §5 are one design change.**
> RFC-0137 §5 (and its integrated
> `spec.ownership.drop-dispatch-against-a-narrowed-residual.legality-1`) previously
> *computed* a `Drop` impl's required field set from the destructor body — a fixed point
> over `self`-method calls, resolved 2026-08-25. That was amended: **the required set is
> now declared on the `drop` receiver type.** This RFC covers the **fixed projection**
> form of that receiver — `fun drop(&var self: Self.{ fd })` — and carries the
> `drop`-specific rules (body check, move-check relaxation, `dyn Aspect` checkpoint,
> one-impl-per-type) and the rationale for the change. The *row-parametric* form
> (`fun drop<row R>(&var self: Self.R) where R: { fd, .. }`) is **RFC-0148**, and depends
> on RFC-0146 → RFC-0121 rather than on RFC-0109.
>
> **Overlap check (`rfc.py new` similarity + `INDEX.md` + `REGISTRY.md`):**
> - **RFC-0109 (Self-View Narrowing, `1-under-review`, `metel-core#842`, v0.13.0)** —
>   supplies the residual-typed `self` receiver (`view V for S { a }`, `self: &V` =
>   `self: &S.{ a }`, and the anonymous `self: &S.{ a }` form). **Hard dependency.**
> - **RFC-0137 (`3-integrated`) §5** / `reference/spec/ownership.md` own the dispatch
>   *rule*, amended 2026-08-28 to the declared-receiver required set this RFC's fixed
>   form plugs into.
> - **RFC-0148 (Row-Parametric Destructors)** — the parametric generalization; shares
>   this RFC's move-check rule, dispatch, and `dyn Aspect` checkpoint verbatim.
> - **RFC-0072 (Negative Bounds, implemented)** — `!Drop`; unaffected by which form a
>   `Drop` impl is authored in (§2).
> - **RFC-0008 (Aspect Objects, `2-accepted`; slice 1 implemented, `metel-core#865`)** —
>   the `dyn Aspect` drop-pointer and the coercion checkpoint this RFC's declared set
>   feeds.

> **Status — under review (2026-08-28).** Substantiated primary proposal (fixed-projection form of RFC-0137 §5's declared-receiver `Drop` required set, the `drop`-specific rules, worked examples) with explicit blocking open questions. Paired with the 2026-08-28 amendment to RFC-0137 §5. On the v0.13.0 path with RFC-0109 and RFC-0137. Tracking: metel-core#887.

## Summary

`Drop::drop` may declare its `&var self` receiver as a **fixed field projection** of
`Self`:

```metel
extend Handle: Drop {
    fun drop(&var self: Self.{ fd }) {
        sys_close(self.fd)
    }
}
```

The fields the receiver projection names — here `{ fd }` — are the `Drop` impl's
**required field set**. A partial move that leaves `fd` intact (`let n = h.name;`) is
permitted; one that removes `fd` is rejected. The compiler does not read the body to find
out.

`Drop::drop` then has two authoring forms in this RFC (a third, row-parametric, is
RFC-0148):

| Form | Required field set | Partial move of a `Drop` value |
|---|---|---|
| `fun drop(&var self)` | the whole declared row | always rejected (RFC-0071 §7 status quo) |
| `fun drop(&var self: Self.{ fd })` *(this RFC; receiver via RFC-0109)* | `{ fd }`, exact | allowed iff residual ⊇ `{ fd }` |
| `fun drop<row R>(&var self: Self.R) where R: { fd, .. }` *(RFC-0148)* | `{ fd }`, lower bound | allowed iff residual ⊇ `{ fd }` |

The dispatch rule — **residual row ⊇ required set** — is the spec's
(`spec.ownership.drop-dispatch-against-a-narrowed-residual.dynamics-1`), identical for
all forms. There is no body-derived set — RFC-0137 §5's amendment of 2026-08-28 removed
it.

---

## Motivation

Until 2026-08-28, RFC-0137 §5 (and its integrated `…legality-1`) computed a `Drop` impl's
required field set by static analysis of the destructor body: "the union of the fields
its destructor body reads directly and, recursively, the required sets of every
`self`-method it calls" — a fixed point over one type's own method set, "closer to effect
inference than ordinary type-checking" (RFC-0137 §5, as it then read).

RFC-0137 §5 was amended to make the required set a **declared contract** on the `drop`
signature instead. Three properties the computed form did not have motivated the change:

1. **No fixed-point computation.** Each `self`-method the destructor calls states its own
   declared receiver row. Composition is a local containment check per call site. The
   compiler never walks the type's method graph to a fixed point to know what a
   destructor requires.
2. **No action-at-a-distance.** With the computed form, adding a `self.name` read to a
   `drop` body (or to a helper it calls) silently shrinks the set of partial moves that
   are legal *elsewhere in the program*. With a declared set, that read is either within
   the declared row (no effect elsewhere) or a compile error at the read — the legality
   of far-away partial moves only changes through a visible signature edit.
3. **Explicit opt-in to narrowing tolerance.** A destructor that needs the whole value
   says so by taking `&var self` (form 1). A destructor that tolerates narrowing states
   exactly how much. The author decides; the compiler does not infer intent from
   whatever the body happens to touch.

This mirrors RFC-0071's settled position that `Copy` is *declared*, never derived — the
same reasoning applied to "which fields does teardown require."

The declared set is also directly what the spec's **`dyn Aspect` coercion checkpoint**
(`…legality-2`) needs: coercing a `Drop`-implementing value to `dyn Aspect` is rejected
when the value's current row does not satisfy the impl's required set. With the computed
form that set is a whole-body analysis result; with the declared form it is right there
in the signature the checkpoint is already looking at.

---

## 1. Syntax

The `drop` method's `&var self` receiver may be annotated with a field projection of
`Self` (RFC-0116 §4 projection type; as a receiver, via RFC-0109 — a named
`view V for Self { … }` used as `self: &var V`, or the anonymous `self: &var Self.{ … }`
form RFC-0109 §2 defines):

```
"fun" "drop" "(" "&var" "self" (":" "Self" "." "{" field-list "}")? ")" block
```

- A bare `&var self` receiver (no projection) means the whole declared row.
- `&self` (shared) is not a valid destructor receiver; only `&var self`, matching the
  `std::core::Drop` aspect signature.
- The projection must be non-empty and every field it names must exist on `Self`.

---

## 2. Static semantics

**Required field set (`spec.ownership.drop-dispatch-against-a-narrowed-residual.legality-1`
/ `legality-3`).** The fields named by the `drop` receiver's projection; the whole
declared row if the receiver is bare `&var self`.

**Body check (`…legality-4`).** The destructor body may read or write only fields in the
declared receiver row, and may call a `self`-method only when that method's own declared
receiver row is satisfied by the `drop` receiver's declared row. Each is a local check at
the access or call site — no whole-body or call-graph analysis.

**Move-check rule (spec `…dynamics-1`, substance unchanged).** At each partial-move site
of a value whose type is a `Drop`-implementing struct (or a residual of one), under
`--move-check`: the partial move is permitted iff the resulting residual row ⊇ the
required field set; otherwise it is rejected with
`MoveViolationKind::PartialMoveOfDropType` — same error code and message as today, only
the triggering condition relaxed from "always, for any `Drop` type" (RFC-0071 §7) to
"only when a required field would be gone."

**`dyn Aspect` coercion checkpoint (spec `…legality-2`, unchanged).** Coercing a value of
this type to any `dyn Aspect` is rejected when the value's current row does not satisfy
the required field set. The declared projection *is* that set; no extra analysis at the
coercion site.

**`!Drop` and `Copy`/`Drop` exclusion are unaffected.** A projected `drop` receiver does
not change *whether* the type implements `Drop`; it only changes which partial moves of
it are legal. RFC-0072's `!Drop` bound and the spec's "`Copy` and `Drop` are mutually
exclusive" rule see the type exactly as they do for the bare form.

---

## 3. One `Drop` impl per type — the forms are a choice, not an overload

A type has at most one `Drop` impl (`reference/spec/declarations.md`, Aspect
Implementation Coherence). The forms are alternative ways to *write* that one impl,
selected by the author. No overloading, no dispatch ambiguity, no coherence question
introduced by this RFC.

A generic `Drop` impl (`extend<T> Pair<T>: Drop`) may use a projected `drop` receiver;
per RFC-0137 §7 the projection is a fixed set of field names and must not depend on `T`.
This RFC does not resolve RFC-0137's Open Question 6 (whether a `Drop` impl *conditional*
on `T`'s own `Drop`-ness needs pre-substitution reasoning) — it inherits that question's
"verification pending `metel-core#261`" status unchanged.

---

## 4. Relationship to the integrated spec and to RFC-0148

`reference/spec/ownership.md`'s "Drop dispatch against a narrowed residual" is the
normative section, amended 2026-08-28 in lockstep with RFC-0137 §5. This RFC does not
change that rule; it is the `drop`-specific reading of it for a **fixed** projected
receiver, and carries the rationale for the amendment.

- **RFC-0148 (Row-Parametric Destructors)** generalizes the fixed projection to a
  lower-bounded row parameter (`fun drop<row R>(&var self: Self.R) where R: { fd, .. }`).
  It shares this RFC's §2 rules verbatim; the only difference is that the required set is
  a parameterized lower bound rather than a fixed list. RFC-0148 depends on RFC-0146 →
  RFC-0121; this RFC does not.
- The `Drop` half of RFC-0137 slice 2 (`metel-core#858`) implements **this** form for
  v0.13.0 — depends on RFC-0109 (`metel-core#842`), same milestone. It must **not**
  implement the old body-computed required set.

---

## Out of Scope

- **Whole-body destructor semantics, drop order, explicit `drop(x)`** — `metel-core#261`
  / RFC-0071 (3/4). This RFC does not make any `drop` body run; it governs which partial
  moves and `dyn` coercions the checker permits ahead of that.
- **Widening a residual before it is dropped** — the spec's "Widening" / RFC-0114's
  `construct` path.
- **The row-parametric receiver form** — RFC-0148.
- **RFC-0137 Open Question 6** (generic-conditional `Drop`) — inherited, not resolved
  here (§3).

---

## Open Questions

1. **Depends on RFC-0109.** *(Blocked on a dated dependency.)* This RFC cannot be
   accepted before RFC-0109's residual-typed `self` receiver is settled. Both are on
   v0.13.0 (`metel-core#842` / `metel-core#827`).
2. **Does RFC-0148 subsume this form?** A fixed projection is a `Self.R` with `R` never
   otherwise mentioned and an exact-width `where` clause. Keeping the fixed spelling as
   its own form has value: it needs no `row` kind and can ship in v0.13.0 while RFC-0148
   waits on RFC-0121. Decide whether both spellings coexist permanently or the fixed one
   becomes sugar once RFC-0148 lands. Mirrors RFC-0146 Open Question 5.
3. **`reject_inert_destructor` interaction.** Today (`metel-core#292`/`#261`) a non-empty
   `drop` body is rejected outright. The declared-receiver required set does not depend
   on the body, so `fun drop(&var self: Self.{ fd, name }) {}` with an *empty* body is
   still checkable and meaningful — the *projection* is the contract — which lets
   `metel-core#858`'s reject-path test be written before destructor invocation lands
   (`let n = h.name;` still rejected because `{ fd }` ⊉ `{ fd, name }`). Confirm this is
   the intended interaction and the gate is otherwise unchanged until `#261`.
4. **Coercion-checkpoint diagnostics.** The spec's `…legality-2` rejects a too-narrow
   `dyn Aspect` coercion; with the declared form the message can name the `drop`
   receiver's own projection. Worth specifying the diagnostic shape, or leave to
   implementation.

---

## References

- `reference/spec/ownership.md` — "Drop dispatch against a narrowed residual"
  (`…legality-1` declared-receiver required set, `…legality-3` permitted receiver forms,
  `…legality-4` body containment check, `…dynamics-1` dispatch rule, `…legality-2` `dyn
  Aspect` coercion checkpoint); "`Drop`", "`Copy` and `Drop` are mutually exclusive",
  "Partial moves", "Widening"
- RFC-0109 (Self-View Narrowing, `1-under-review`, `metel-core#842`, v0.13.0) — the
  residual-typed `self` receiver; **hard dependency**
- RFC-0137 (Nominal Types as Branded Rows, `3-integrated`) — §5 (amended 2026-08-28 to
  the declared-receiver required set this RFC's fixed form plugs into; Open Question 2
  superseded there), §7 (generic structs), Open Question 6 (generic-conditional `Drop`,
  inherited unresolved)
- RFC-0148 (Row-Parametric Destructors, `1-under-review`) — the parametric
  generalization; shares §2 verbatim, depends on RFC-0146 → RFC-0121 instead of RFC-0109
- RFC-0071 (Ownership and Move Semantics, `3-integrated`, partial-move tracking not yet
  implemented, `metel-core#858`) — §7 blanket partial-move-with-`Drop` ban (superseded in
  design by the spec section), `Copy`/`Drop` exclusion
- RFC-0116 (Anonymous Record Types, implemented) — §4 projection type the receiver is
  annotated with
- RFC-0072 (Negative Bounds, implemented) — `!Drop`, unaffected by form choice
- RFC-0008 (Aspect Objects, `2-accepted`; slice 1 `metel-core#865`, coercion
  `metel-core#863`) — the `dyn Aspect` drop-pointer and coercion checkpoint
- `metel-core#858` — RFC-0137 slice 2 (move-triggered narrowing/widening, row-bounded
  `Drop` dispatch); implements this form for v0.13.0
- `metel-core#261` — RFC-0071 (3/4): drop order and explicit drop; destructor invocation
  must land before any `drop` body runs
- `metel-core#292` — the `reject_inert_destructor` gate (non-empty `drop` bodies rejected
  until `#261`); Open Question 3

---

## Decision

**Outcome:** *(pending)*
**Target:** *(set when accepted)*
