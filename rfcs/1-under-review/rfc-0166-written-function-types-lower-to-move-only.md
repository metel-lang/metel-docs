---
id: rfc-0166
title: "Written Function Types Lower to Move-Only"
date: '2026-09-03'
status: under-review
target: v0.13.0
updated: '2026-09-03'
tracking: 'https://github.com/metel-lang/metel-core/issues/946'
---

> **Status — draft (2026-09-03).** Split from RFC-0163 (`2-accepted`) so the
> urgent, design-agnostic part of it ships in v0.13.0 while the rest is
> rescheduled to v0.17.0 to co-design with RFC-0162 (Copy-model design space).
> This RFC is deliberately small: one rule, one deletion, no new keyword, no new
> type-model state. It re-litigates nothing — the design space is RFC-0163's.

> **Status — under review (2026-09-03).** Split from RFC-0163 the same day;
> tracking metel-core#946, milestoned v0.13.0. Content is RFC-0163's own
> alternative D, stated minimally — nothing here is new design.

## Summary

A **written function type** — `|T| -> U` in a signature, field, alias, or
return — has concrete **`Move`** use-multiplicity (RFC-0134 §4). A function value
that RFC-0134 proved `Copy` (a named function, a capture-free closure, a closure
whose captures are all `Copy`) is **accepted into a written function-type slot by
moving**; its `Copy`-ness is not carried by the written type and is not recovered
downstream. Nested function types match the use axis **exactly**, exactly as
`once` / `var` do.

This replaces the frontend's current guess — `typeinference`'s synthetic
Copy-to-Move normalization — with an explicit, minimal rule. It adds **no `copy`
qualifier**, **no `Erased` state**, and reserves no keyword. Those are RFC-0163,
rescheduled to v0.17.0.

---

## Motivation

RFC-0134 gives every function value a use-multiplicity axis: `Copy` when its
captures are `Copy`, otherwise move-only. Written function *types* can spell
`once` and `var` but **cannot spell this third axis**, so `|T| -> U` has no
defined meaning on it. The frontend currently papers over the gap: `typeinference`
lowers a written function type to a move placeholder and then carries a
Copy-to-Move special case in `unify_seq`, in nested matching, and in generic
construction that lets a concrete `Copy` value slip through. That behavior is
invisible in the language, is a special case one refactor away from becoming a
general nested-widening rule (which would violate RFC-0152's "exact below the
first nesting"), and forces the compiler to decide an unstated language question.

The v0.13.0 closure cluster (RFC-0050 / RFC-0134 / RFC-0152 / RFC-0153 /
RFC-0157) landed and *exposed* this gap. It should not ship unpatched. But the
full fix — a third `Type::Fun` state, a `copy` qualifier, provenance tracking —
is large, still has open mechanism questions (RFC-0163 §J1–J5), and is coupled to
a decision Metel has not made: whether regular values keep implicit `Copy` at all
(RFC-0162 Axis A). This RFC ships the part that is safe under *every* such
decision.

---

## Proposal

### Rule

1. **A written function type lowers to concrete `Move`.** `f: |T| -> U`,
   `-> |T| -> U`, `type Cb := |T| -> U`, and a `|T| -> U`-typed field all give
   `f` (and any binding they type) a move-only function value. `let a := f; let
   b := f;` is a use-after-move error.

2. **A `Copy` function value is accepted where `Move` is required, by moving.**
   Passing `add_one` (concrete `Copy`) to `map(f: |T| -> U)` type-checks: the
   value is moved into `f`. This is the ownership lattice — `Copy` outranks
   `Move` in permissions — not a special rule. Inside the callee `f` is
   move-only; it may be called and moved, not duplicated.

3. **`Copy`-ness is forgotten at the boundary and not re-derived.** A written
   function type carries no record that the value behind it was `Copy`. If `map`
   returns `f` (`-> |T| -> U`), the caller receives a move-only value even though
   a `Copy` callable went in. Construction must not inspect a move-only
   function value's origin to recover `Copy`; the deleted normalization
   (below) stays deleted.

4. **Nested function types match the use axis exactly.** A function type that is
   a parameter, return, element, or field *of another function type* matches
   bare ↔ bare only, exactly as `once` / `var` are matched below the first
   nesting (RFC-0152). There is no `copy` to create a mismatch and no erasure
   at a nested position. This keeps RFC-0152 untouched and leaves RFC-0155's
   higher-order variance question entirely open.

### Deletion

`typeinference`'s synthetic Copy-to-Move mismatch handling — the named
move-placeholder normalization **and** its siblings in `unify_seq`, nested
matching, and generic construction — is **deleted, not gated**. After this rule
there is no Copy-to-Move path: a written function type is `Move`, a `Copy` value
moves into it, done.

### Explicitly out of scope (RFC-0163, v0.17.0)

- **`copy |T| -> U`** — the positive assertion "this callable may be duplicated."
  Not added here; a body that needs to duplicate a callback cannot express it
  through a written function type until v0.17.0 (see Migration).
- **The `Erased` third state** — "capability unknown" as distinct from "proven
  move-only." Under this RFC a written function type is simply `Move`.
- **The `copy` keyword reservation** — **not** made here (per the decision to
  keep this RFC minimal). v0.17.0's RFC-0163 carries the keyword reservation and
  its one-off `copy`-as-identifier corpus sweep.
- **Per-node `written` provenance, the coercion table, the join expected-context
  rule, generic-rigidity scoping** — RFC-0163 §J1–J5, resolved in the v0.17.0
  window.

---

## Migration

Hard switch, one sweep (Metel has no public users). Runs after the RFC-0050 /
RFC-0153 corpus sweeps.

- **Bodies that duplicated a bare-typed callback.** A signature `f: |T| -> U`
  whose body does `let a := f; let b := f;` compiled today because the frontend
  normalised the written type to concrete `Copy`. Under this RFC it is a
  use-after-move error, and there is **no `copy` spelling yet** to fix it with.
  The fixes available in v0.13.0: take a generic `<F>` parameter (pass-through /
  storage only, cannot call without RFC-0161), `.clone()` at the duplication
  site if the concrete type is `Clone`, or restructure to call `f` once. The
  `copy |T| -> U` parameter that restores the direct spelling arrives with
  RFC-0163 at v0.17.0. Located by the move checker over the swept corpus;
  expected to be rare — signatures that only call, store, move, or return `f`
  once need no change.

---

## Forward compatibility

- **Refinement, not replacement.** When RFC-0163 lands, `Move` at a written
  function type *refines* to `Erased` (identical use-site behavior — call, move,
  no copy, no acceptance into `copy` — plus the future-`move` distinction and the
  representation invariant). No source program that compiled under this RFC fails
  under RFC-0163.
- **`copy` is purely additive.** RFC-0163 adds the qualifier's *meaning*; this
  RFC reserves nothing, so v0.17.0 also does the keyword reservation and its
  sweep. A v0.13.x–v0.16.x program may use `copy` as an identifier and will need
  a rename at v0.17.0; accepted as a small, bounded break.
- **If RFC-0162 adopts P2 (no implicit `Copy` at all)**, both this rule and
  RFC-0163 are moot — there is no implicit copyability to forget. This RFC's rule
  is still harmless in that world (a bare function type is move-only, which is
  what P2 makes *everything*).

---

## Relationship to existing RFCs

- **RFC-0163 (Function-Type Use-Multiplicity Surface, `2-accepted`, rescheduled
  v0.17.0, #936)** — this RFC is its conservative v0.13.0 slice. RFC-0163 keeps
  its full design (the `Erased` state, `copy` qualifier, per-node `written`
  provenance, coercion table); this RFC ships rules 1–4 above, which RFC-0163
  refines rather than restates.
- **RFC-0134 (Closure Call Capability, `4-implemented`)** — owns
  `use_multiplicity` on `Type::Fun`. This RFC only fixes what a *written* function
  type lowers to; capture-derived capability for closure *values* is unchanged.
- **RFC-0152 (Function-Type Multiplicity Widening, `4-implemented`)** —
  untouched. Rule 4 keeps the use axis exactly matched below the first nesting,
  like `once` / `var`.
- **RFC-0155 (Higher-Order Function-Type Multiplicity Variance, unscheduled)** —
  untouched and unweakened; there is no erasure or `copy`↔bare relation for it
  to have to accommodate.
- **RFC-0162 (Copy and Clone Model — Regular-Value Design Space, `1-under-review`,
  v0.17.0)** — the coupled decision. This RFC is chosen to be sound under every
  RFC-0162 Axis-A position (P0 / P1 / P4) and harmless under P2. RFC-0163's full
  surface waits for that decision.
- **RFC-0161 (Callable Object Contract, `1-under-review`)** — a generic `<F>`
  parameter (a Migration workaround here) cannot be *called* without RFC-0161's
  callable bound.

---

## Decision

**Outcome:** *(pending — `0-draft`. Split from RFC-0163 on 2026-09-03 to
decouple the urgent frontend fix from the v0.17.0 Copy-model work. The rule is
RFC-0163's own conservative alternative (D), stated minimally; no design space is
reopened.)*
**Target:** v0.13.0 — deletes the `typeinference` Copy-to-Move guess exposed by
the closure cluster. Nothing here blocks the rest of v0.13.0.
