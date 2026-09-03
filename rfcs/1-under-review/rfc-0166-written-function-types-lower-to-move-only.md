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

**Every syntactically written `|T| -> U` type node** — anywhere a type is
written, and every function-type node nested inside another — has concrete
**`Move`** use-multiplicity (RFC-0134 §4). A function value that RFC-0134 proved
`Copy` (a named function, a capture-free closure, a closure whose captures are
all `Copy`) is **accepted into a written function-type slot by moving** — this is
RFC-0152's existing first-order `Copy → Move` direction, now stated. Its
`Copy`-ness is not carried by the written type and is not re-derived downstream.
Below the first function level the use axis matches **exactly**, as `once` /
`var` already do.

The change against the frontend is precise: **specify** the `TypeExpr::Fun` →
`Move` lowering and the first-order `Copy → Move` acceptance (today's
unexplained "conservative placeholder refined during construction"); **delete**
the one `nested_fun_axes_match` exception that lets a written nested function
type reconcile with an inferred `Copy` one; **leave** the symmetric
generic-scheme acceptance as documented debt for RFC-0163 to remove. It adds **no
`copy` qualifier**, **no `Erased` state**, and reserves no keyword — those are
RFC-0163, rescheduled to v0.17.0.

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

### What "written function type" means

Lowering is defined recursively over the **written type expression**, not the
resolved `Type`:

- **Every syntactically written `TypeExpr::Fun` node lowers to `use_multiplicity
  = Move`** — its outer node and every function-type node nested inside it
  (a parameter, return, element, or field of another function type). This is
  positional and total: it applies in a parameter type, a `let` / `var`
  annotation, an ascription, a declared function / method return, a struct or
  enum field type, a written aggregate element type (`(|i64| -> i64,)`), a
  generic type argument (`W<|i64| -> i64>`), an alias body, an aspect method
  signature, and a `?` slot under a declared return.
- **A bare type parameter (`F`) is opaque** — it is not a `TypeExpr::Fun` node,
  so nothing lowers; `F` binds to the argument's resolved type verbatim.
- **A transparent alias and a resolved associated-type projection carry their
  already-lowered axis through expansion** — `type Cb := |i64| -> i64` makes
  `Cb` a written function type wherever it is used; `type W<T> := (T,); f: W<|i64|
  -> i64>` lowers the tuple element.
- **An inferred function value keeps RFC-0134's capture-derived
  `use_multiplicity`.** Lowering is a property of the *declared slot type*, never
  a retyping of the value. A closure literal constructed in a written context
  still has the capability its captures give it; the `Copy → Move` step (below)
  happens *at the boundary*, when the value flows into the slot — the value's own
  type is unchanged.

### Compatibility

There is one compatibility rule, directional and first-order:

**A `Copy` function value is accepted into a written (`Move`) function-type slot
by moving.** `map(add_one)` type-checks — `add_one` (concrete `Copy`) moves into
`f: |T| -> U`. Inside the callee `f` is move-only: callable, movable, not
duplicable. If `map` returns `f` (`-> |T| -> U`), the caller receives a move-only
value; the callback's `Copy`-ness is dropped at the parameter boundary and is
**not** re-derived downstream — construction must not inspect a value's origin to
restore `Copy` behind a written function type.

This is RFC-0152's existing first-order `Copy → Move` direction, made explicit and
sanctioned rather than left as an unexplained guess. Below the first function
level the use axis matches **exactly**, exactly as RFC-0152 already requires for
`once` / `var`. RFC-0155's higher-order variance question is untouched.

### The frontend change

Concretely, against `metel-frontend/src/typeinference/mod.rs`:

- **Keep, and specify:** `TypeExpr::Fun` lowering to the `Move` placeholder
  (`InferType::Fun(.., Move, ..)`); and the first-order `Copy → Move` acceptance
  — `unify_seq`'s `(Move, Copy)` normalization and `unify`'s first-order `use_ok`
  direction. These stop being "a conservative placeholder refined during
  construction" and become the stated rule above.
- **Delete:** the `(UseMultiplicity::Move, UseMultiplicity::Copy)` exception in
  `nested_fun_axes_match`. That is the one line permitting a written (`Move`)
  nested function type to reconcile with an inferred `Copy` one *below* the first
  nesting — precisely the accidental nested latitude RFC-0152 forbids for the
  other two axes. After this, nested use-axis matching is `au == bu` only.
- **Note as debt, do not touch for v0.13.0:** the symmetric `use_ok` in
  generic-scheme construction (`use1 == use2 || use1 == Copy || use2 == Copy`,
  guarded by `!generic_axes`). It is monomorphization-deferred scaffolding — the
  concrete direction is enforced at each call site. RFC-0163's "one resolved
  directional relation" removes it at v0.17.0; RFC-0166 leaves it exactly as is
  and states that it does.
- **Unchanged:** the aspect check — `InferType::Fun` satisfies `Copy` iff its
  `use_multiplicity` is `Copy`, so a written function type (`Move`) does not, and
  a closure literal with all-`Copy` captures does. RFC-0166 does not change what
  a function value satisfies; it only fixes what a *written type* lowers to.

The compatibility matrix these produce:

| Site | `Copy` value → written `\|T\| -> U` | inferred `Copy` nested under written `\|T\| -> U` | `Move` value → written `\|T\| -> U` |
| --- | --- | --- | --- |
| direct argument / `let` / return (first-order) | accepted, becomes `Move` | — | accepted |
| nested (param/return/element of a function type) | **rejected** (was accepted via the deleted exception) | **rejected** | rejected unless `au == bu` |
| generic scheme checking with type vars | permissive (debt; concrete direction enforced at the call site) | permissive (debt) | permissive (debt) |

### Explicitly out of scope (RFC-0163, v0.17.0)

- **`copy |T| -> U`** — the positive assertion "this callable may be duplicated."
  Not added here; a body that needs to duplicate a callback cannot express it
  through a written function type until v0.17.0 (see Migration).
- **The `Erased` third state** — "capability unknown" as distinct from "proven
  move-only." Under this RFC a written function type is simply `Move`.
- **The `copy` keyword reservation** — deliberately **not** made here. This is a
  choice with a cost: `copy` is a valid identifier today in a `let` / `var`
  binding, a parameter, a generic parameter, a function / method / type-alias
  name, a struct field, an enum variant, a pattern binding, and an `import … as`
  alias — and the repository already has at least one `let copy`. RFC-0163 at
  v0.17.0 reserves `copy` and runs the full identifier-position sweep; that is a
  **keyword-breaking release for the `copy` identifier**, not an additive change.
  Native / raw-dotted paths keep their own keyword-permissive grammar and are out
  of that sweep. Accepted as a bounded, deferred break to keep this RFC to one
  semantic rule.
- **Per-node `written` provenance, the coercion table, the join expected-context
  rule, generic-rigidity scoping** — RFC-0163 §J1–J5, resolved in the v0.17.0
  window. RFC-0166 needs none of it: with no `copy` and no `Erased`, every
  written function-type node lowers to the same value (`Move`), so there is
  nothing per-node to disambiguate.

---

## Migration

Hard switch, one sweep (Metel has no public users). Runs after the RFC-0050 /
RFC-0153 corpus sweeps.

- **Bodies that duplicated a bare-typed callback.** A signature `f: |T| -> U`
  whose body does `let a := f; let b := f;` (or otherwise uses `f` by value more
  than once) compiled today because the frontend normalised the written type to
  concrete `Copy`. Under this RFC `f` is move-only and the second use is a
  use-after-move.

  This is a **checked-mode migration.** Non-copyability of a written function
  type is a move-checker property (RFC-0166 does not add move tracking to plain
  type-checking); the default evaluator still deep-clones by-value uses, so an
  offending body keeps *running* until `--move-check` is on. The sweep therefore
  runs the move checker **explicitly over the whole corpus** with `--move-check`,
  and **"no user generic function body is recorded as move-unchecked"** is a
  release criterion (the move checker skips a generic body when it cannot rebuild
  its scheme; those bodies must be checkable or restructured, not left silent).

  There is **no `copy` spelling** to fix a flagged body with until RFC-0163 at
  v0.17.0. The remedies available in v0.13.0:
  - restructure so `f` is used by value once — call it (a `many` `reading` call
    is a shared borrow, not a consume, so repeated *calls* are already fine; the
    error is a repeated *by-value move*), then move / store / return it;
  - take a generic `<F>` parameter — pass-through / storage only; `F` cannot be
    *called* without RFC-0161's callable bound.

  A function value is **not `Clone`** (a closure satisfies no `Clone` aspect —
  RFC-0134), so `.clone()` is **not** a remedy. Expected to be rare —
  signatures that only call `f` (any number of times), or store / move / return
  it once, need no change; located by the `--move-check` sweep.

---

## Forward compatibility

- **`Move` → `Erased` is a refinement — as a proof obligation, not an
  assertion.** RFC-0163's own F4 / H8 analysis establishes that `Move` and
  `Erased` impose identical *source-observable* use behavior in a language with
  no exact-`move` spelling (call, move, never copy, never accepted into `copy`);
  they differ only in the representation invariant and a future `move` qualifier,
  neither source-visible. So refinement *should* be source-transparent — but
  RFC-0163 also makes `Erased ≠ Move` deliberate, preserves generic types
  verbatim, and matches nested exactly. That combination is demonstrated, not
  assumed: **RFC-0166's `3-integrated` fixture set is the refinement regression
  corpus**, and passing it unchanged under RFC-0163's model (generic
  pass-through, aliases, associated projections, higher-order callbacks, joins,
  fields, returns) is an acceptance criterion for RFC-0163's own `3-integrated`.
- **Not reserving `copy` is a deferred break, not an additive change.** RFC-0163
  at v0.17.0 reserves `copy` and does the full identifier-position sweep; a
  v0.13.x–v0.16.x program that used `copy` as an identifier needs a rename then.
  Bounded (the sweep is mechanical, no public users) and deliberate — the cost of
  keeping this RFC to one semantic rule. Reserving now would be strictly cheaper
  in isolation; it is deferred because the `copy` *meaning* and its `once` / `var`
  contextual-family question belong with RFC-0163.
- **If RFC-0162 adopts P2 (no implicit `Copy` at all)**, both this rule and
  RFC-0163 are moot — there is no implicit copyability to forget. This RFC's rule
  is still harmless in that world (a bare function type is move-only, which is
  what P2 makes *everything*).

---

## Relationship to existing RFCs

- **RFC-0163 (Function-Type Use-Multiplicity Surface, `2-accepted`, rescheduled
  v0.17.0, #936)** — this RFC is its conservative v0.13.0 slice. RFC-0163 keeps
  its full design (the `Erased` state, `copy` qualifier, per-node `written`
  provenance, coercion table); this RFC lowers every written function-type node
  to `Move`, which RFC-0163 refines to `Erased` rather than restates.
- **RFC-0134 (Closure Call Capability, `4-implemented`)** — owns
  `use_multiplicity` on `Type::Fun`. This RFC only fixes what a *written* function
  type lowers to; capture-derived capability for closure *values*, and what a
  function value satisfies as an aspect (`Copy` iff `use_multiplicity == Copy`,
  never `Clone`), are unchanged.
- **RFC-0152 (Function-Type Multiplicity Widening, `4-implemented`)** — untouched.
  This RFC's first-order `Copy → Move` acceptance *is* RFC-0152's existing rule,
  now stated; the use axis is matched exactly below the first nesting, exactly as
  RFC-0152 already requires for `once` / `var` (the deleted `nested_fun_axes_match`
  exception was the one place that was not true).
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

## Lifecycle

- **`3-integrated`** adds a `spec.functions.first-class-functions` Legality Rule
  block for: written-function-type lowering (recursive, per node, `Move`); the
  first-order `Copy → Move` acceptance; nested exact matching; `Copy`-ness not
  re-derived. Fixtures — a `Copy` named function into `map(f: |T| -> U)` (accepted,
  comes back move-only when returned); a move-only closure into the same `map`; a
  use-after-move on a duplicated bare callback (`--move-check`); an inferred
  `Copy` closure rejected against a *nested* written function slot (the deleted
  exception); an alias / generic-argument / associated-projection written function
  type erasing at a first-order boundary and matching exactly nested. This set is
  also RFC-0163's `Move → Erased` refinement regression corpus.
- **`4-implemented`**: state the `TypeExpr::Fun → Move` lowering and the
  first-order `Copy → Move` acceptance; **delete** the
  `(Move, Copy)` exception in `nested_fun_axes_match`; leave the symmetric
  generic-scheme `use_ok` as documented debt; the `--move-check` corpus sweep with
  its "no move-unchecked user generic body" release criterion; the `.clone()`
  advice is *not* offered (function values are not `Clone`).

## Decision

**Outcome:** *(pending — `1-under-review`, tracking metel-core#946. Split from
RFC-0163 on 2026-09-03 to decouple the urgent frontend fix from the v0.17.0
Copy-model work. The rule is RFC-0163's own conservative alternative D, stated
minimally against the actual `typeinference` mechanisms; no design space is
reopened. An adversarial review (2026-09-03) added the recursive lowering scope,
the precise keep/delete/debt breakdown of the frontend change, the checked-mode
migration framing, and the `Move → Erased` proof obligation.)*
**Target:** v0.13.0 — removes the `typeinference` Copy-to-Move guess exposed by
the closure cluster. Nothing here blocks the rest of v0.13.0.
