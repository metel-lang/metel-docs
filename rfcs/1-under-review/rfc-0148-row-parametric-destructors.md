---
id: rfc-0148
title: "Row-Parametric Destructors"
date: '2026-08-28'
status: under-review
target:
updated: '2026-08-28'
tracking: 'https://github.com/metel-lang/metel-core/issues/888'
---

> **New RFC, split from RFC-0147 on 2026-08-28.** RFC-0147 (Projection-Receiver
> Destructors) originally covered both the fixed projected `drop` receiver
> (`fun drop(&var self: Self.{ fd })`) and the row-parametric one
> (`fun drop<row R>(&var self: Self.R) where R: { fd, .. }`). Those depend on different
> feature RFCs — RFC-0109 for the fixed form, RFC-0146 → RFC-0121 for the parametric
> one — and land in different releases, so they are separate RFCs. RFC-0147 keeps the
> fixed form, the `drop`-specific rules, and the rationale for RFC-0137 §5's amendment;
> this RFC is the parametric generalization.
>
> **Overlap check (`rfc.py new` similarity + `INDEX.md` + `REGISTRY.md`):**
> - **RFC-0147 (Projection-Receiver Destructors, `1-under-review`, `metel-core#887`)** —
>   the sibling this was split from. Its §2 (required set, body check, move-check rule,
>   `dyn Aspect` checkpoint, one-impl-per-type) applies here **verbatim**; this RFC only
>   adds the parameterized spelling of the required set.
> - **RFC-0146 (Row-Polymorphic Self-Views, `1-under-review`, `metel-core#886`)** — the
>   `<row R>` receiver mechanism this RFC specializes to `drop`. **Hard dependency**;
>   transitively **RFC-0121 (Open Rows, `metel-core#792`)** for the `row` kind.
> - **RFC-0137 (`3-integrated`) §5** / `reference/spec/ownership.md` — the dispatch rule
>   (amended 2026-08-28); unchanged by this RFC.
> - **RFC-0109** — not a dependency of this RFC (it is RFC-0147's).

> **Status — under review (2026-08-28).** Split from RFC-0147 2026-08-28; substantiated proposal (row-parametric drop receiver, deltas from RFC-0147 spelled out, worked example) with explicit blocking open questions. Committed to **v0.14.1** (issue #888) — the "row-polymorphism consumers" point release, shared with its dependency RFC-0146, after RFC-0121's v0.14.0. Tracking: metel-core#888.

## Summary

`Drop::drop` may declare its `&var self` receiver as a **lower-bounded row parameter**:

```metel
extend Handle: Drop {
    fun drop<row R>(&var self: Self.R) where R: { fd, .. } {
        sys_close(self.fd)
    }
}
```

One destructor is then valid against **every** residual of `Handle` whose current row
contains at least `fd` — the fixed projection form (RFC-0147) writes one destructor per
exact residual width; this writes one for the whole lower-bounded family. The lower bound
`{ fd, .. }` is the `Drop` impl's required field set. `R` is compile-time-only and
**erased** — one compiled destructor body, no per-residual specialization.

Everything else is RFC-0147: the dispatch rule (`residual row ⊇ required set`,
`spec.ownership.drop-dispatch-against-a-narrowed-residual.dynamics-1`), the destructor
body check (`…legality-4`), the move-check relaxation, the `dyn Aspect` coercion
checkpoint (`…legality-2`), one `Drop` impl per type, and `!Drop` / `Copy`-exclusion
being unaffected. This RFC changes only how the required set is *spelled*.

---

## Motivation

RFC-0147's fixed projection `fun drop(&var self: Self.{ fd })` requires the caller's
residual to be *exactly* `.{ fd }`-or-wider and forces a destructor author who wants to
tolerate several residual widths to pick one. A destructor that genuinely only needs
`{ fd }` and does not care what else is present should say exactly that once:

```metel
fun drop<row R>(&var self: Self.R) where R: { fd, .. }   // "at least fd; the rest is not my concern"
```

This is the `Drop::drop` instance of RFC-0146's row-polymorphic receiver — the same
lower-bounded row parameter, in the one method where the required-set contract also
drives move-checking and `dyn Aspect` coercion. It is a signature-ergonomics addition on
top of RFC-0147, not a new dispatch rule.

---

## 1. Syntax

Exactly RFC-0146's receiver-row form, with `drop` as the method and `std::core::Drop` as
the aspect:

```
"fun" "drop" "<" "row" ident ">" "(" "&var" "self" ":" "Self" "." ident ")"
    "where" ident ":" "{" field-list "," ".." "}" block
```

- The `where` lower bound is **mandatory** and must carry the trailing `..` (RFC-0118's
  open-bound marker). A `drop<row R>` with no `where` clause permits no `self.<field>`
  access at all — reject it, or lint and treat as the bare `&var self` form.
- `&self` (shared) is not a valid destructor receiver; only `&var self`.

---

## 2. Static semantics — deltas from RFC-0147 §2

RFC-0147 §2 applies unchanged with "the declared receiver row" read as **the `where`
lower bound**. Only two points are specific to the parametric form:

- **Erasure.** `R` is a type-checker fiction (RFC-0146 §3). There is exactly one compiled
  destructor body, checked once against the lower bound. A drop site with a wide residual
  and one with a narrow residual invoke the same body; the fields absent from a given
  residual are, by the body check, fields the destructor provably never names — nothing
  to specialize, nothing unsound to read. Not more expensive at runtime than RFC-0147's
  fixed form.
- **Use-site.** At a partial-move or `dyn Aspect` coercion site, `R` is unified with the
  value's statically known residual row; the operation is well-typed iff that row ⊇ the
  `where` lower bound. No implicit narrowing.

---

## 3. Generic structs

A generic `Drop` impl (`extend<T> Pair<T>: Drop`) may use `drop<row R>`. Per RFC-0137 §7
and RFC-0146 §4 the `where` lower bound is a fixed set of field names and must not depend
on `T`. RFC-0137 Open Question 6 (a `Drop` impl *conditional* on `T`'s own `Drop`-ness)
is inherited unresolved, exactly as in RFC-0147 §3.

---

## Out of Scope

- Everything RFC-0147 puts out of scope (whole-body destructor semantics, drop order,
  explicit `drop(x)`, widening, RFC-0137 OQ6).
- **The fixed projection form** — RFC-0147.
- **Running different destructor code per residual shape** — explicitly rejected; `R` is
  erased, one body.
- **Row parameters outside the receiver** — RFC-0146 Out of Scope, inherited.

---

## Open Questions

1. **Depends on RFC-0146 → RFC-0121.** *(Blocked on a dated dependency.)* This RFC cannot
   be accepted before RFC-0146 is, and RFC-0146 before RFC-0121 (v0.14.0). Both this RFC
   and RFC-0146 are milestoned **v0.14.1**, the point release after RFC-0121's v0.14.0;
   RFC-0147's fixed form covers the `Drop` narrowed-receiver need in v0.14.0.
2. **Does this subsume RFC-0147's fixed form?** A fixed `Self.{ fd }` receiver is
   `Self.R where R: { fd }` with an exact (no `..`) bound and `R` unused. Decide whether
   the fixed spelling stays permanently (it needs no `row` kind, ships a release earlier)
   or becomes sugar once this RFC lands. Mirrors RFC-0146 Open Question 5 and RFC-0147
   Open Question 2 — one decision, recorded in all three.
3. **Grammar for a generic `Drop` impl's two `where` clauses.** `extend<T: Bound>
   Pair<T>: Drop` already has a type `where`; `drop<row R> where R: { … }` adds a row
   `where`. One combined clause or two — pick one. (Specific to the parametric form, so
   it lives here rather than in RFC-0147.)

---

## References

- RFC-0147 (Projection-Receiver Destructors, `1-under-review`, `metel-core#887`) — the
  sibling; its §2 rules and rationale apply here verbatim
- RFC-0146 (Row-Polymorphic Self-Views, `1-under-review`, `metel-core#886`) — the
  `<row R>` receiver mechanism this RFC specializes to `drop`; **hard dependency**
- RFC-0121 (Open Rows, `1-under-review`, `metel-core#792`) — the `row` kind, reached
  through RFC-0146
- RFC-0137 (Nominal Types as Branded Rows, `3-integrated`) — §5 dispatch rule (amended
  2026-08-28), §7 generic structs, Open Question 6
- `reference/spec/ownership.md` — "Drop dispatch against a narrowed residual"
  (`…legality-1` / `…legality-3` / `…legality-4` / `…dynamics-1` / `…legality-2`)
- RFC-0118 (Row Bounds, implemented) — the `{ …, .. }` open-bound spelling the `where`
  clause reuses
- `metel-core#858` — RFC-0137 slice 2; **not** blocked on this RFC (RFC-0147's fixed form
  covers the `Drop` narrowed-receiver need, in v0.14.0)
- `metel-core#261` — destructor invocation; must land before any `drop` body runs

---

## Decision

**Outcome:** *(pending)*
**Target:** *(set when accepted)*
