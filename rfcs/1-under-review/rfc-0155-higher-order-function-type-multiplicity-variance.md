---
id: rfc-0155
title: "Higher-Order Function-Type Multiplicity Variance"
date: '2026-08-30'
status: under-review
target:
updated: '2026-08-30'
tracking: 'https://github.com/metel-lang/metel-core/issues/904'
---

> **Split from RFC-0152 (2026-08-30).** RFC-0152 was accepted as the *first-order*
> directional coercion only — a function-typed value flowing into a function-typed
> argument, `let`/field ascription, or return slot, where `many` satisfies `once`
> and `Copy` satisfies non-`Copy`. Everything RFC-0152 left open moved here so
> RFC-0152 could be accepted clean rather than "partially implemented": the
> *contravariant* direction when a function type is nested inside another function
> type, and the larger question of whether the coercion should be generalised into
> a real `Type::Fun` subtype lattice the whole checker reasons over.

> **Status — under review (2026-08-30).** Split from RFC-0152 on 2026-08-30 to carry deferred higher-order/contravariant variance and the Type::Fun subtype-lattice question, so RFC-0152's first-order half could be accepted clean as a co-requirement of RFC-0134.

## Summary

RFC-0152 settled that a function value of multiplicity `m` is usable where a
required multiplicity `r` is expected when `m` is at least as permissive as `r`
(`many` ≥ `once` on the call axis; `Copy` ≥ non-`Copy` on the use axis), at
**first-order** sites — argument, ascription, return. This RFC settles the two
things it deliberately did not:

1. **Higher-order variance.** When a function type appears *inside another
   function type's parameter*, the direction flips (contravariance): a slot
   `g: fun(once fun(T) -> U) -> V` should reject an argument of type
   `fun(many fun(T) -> U) -> V` and accept `fun(once fun(T) -> U) -> V`, the
   reverse of the first-order rule. Nested in a *return* position it does not
   flip. Depth-`n` alternation follows the usual co-/contravariant parity. This
   RFC either specifies that rule in full or commits to permanently restricting
   widening to first-order function-typed slots (RFC-0152's current
   implementation boundary).

2. **Whether it becomes a real subtype lattice.** RFC-0152 §4 is explicit that it
   is a decidable axis-wise coercion between two *concrete* function types, with
   no `⊤`/`⊥` function type, no variance annotations, and no bounded
   quantification. Generalising it — so a signature can abstract over "any
   function at least this permissive" — is a `Type::Fun` subtyping relation with
   its own inference, constraint-solving, and interaction with RFC-0121-style row
   / structural polymorphism. That is this RFC's to accept or refuse.

## Motivation

First-order widening is enough for RFC-0134's own stdlib signatures (`each`,
`map`, `fold` — the callback is a direct parameter, never nested). Higher-order
combinators are where the nested case bites: a function that takes *another*
function which itself takes a callback (`fun retry(op: fun(fun() -> Result) -> Result)`)
cannot be checked soundly without a settled contravariance rule, and today
RFC-0152 simply does not widen there — an exact match is required at any nesting
depth below the first. That is a safe under-approximation (it only rejects
programs that would be sound), but it is a cliff: `once`/`many` annotations stop
composing exactly where higher-order code needs them most.

The lattice question is separate and larger. Without it, `once`/`many` can only
ever be written as concrete qualifiers on concrete function types; a library
cannot say "give me anything callable at least once" as a bound and have both
`once` and `many` callers satisfy it through a named abstraction rather than
site-by-site coercion. Whether that is worth a real subtyping relation — versus
the marker-aspect model (below), versus just living without it — is the call this
RFC has to make.

## Design space

### A. Contravariance rule

The standard rule: a function type's parameter positions are contravariant, its
return position covariant, and this composes through nesting by parity. Applied
to the multiplicity axes:

- **Argument-of-argument** (even depth from the outermost slot): direction flips
  — the nested slot wants a *more* permissive function than the value supplies.
- **Argument-of-return** / **return-of-argument** (odd depth): flips again.
- **Struct fields** stay invariant at every depth, as RFC-0152 already fixes for
  the first-order case.

Open sub-questions: whether the first implementation supports any nesting at all
or formally caps widening at first-order (making deeper mismatches a hard exact-
match requirement, documented rather than incidental); and how this interacts
with RFC-0125's variadic `|...Ts| -> R` parameter packs, where "position" is a
range rather than a fixed slot.

### B. General `Type::Fun` subtype lattice

The maximal version: introduce `⊤`/`⊥` function types (or bound the axes with a
two-point lattice per axis and take the product), allow the relation to appear in
bounds (`f: F where F <: many fun(T) -> U`), and thread it through inference as a
constraint rather than an at-the-site check. Costs: a new subtyping judgement the
rest of the checker must respect, decidability and coherence obligations, and a
collision with RFC-0121 row polymorphism if both try to own "structural
flexibility for callable things."

Minimal alternative: no lattice; keep RFC-0152's concrete-to-concrete coercion
forever, and route any "abstract over permissiveness" need through generics with
an explicit multiplicity type parameter if that is ever specified.

### C. Marker-aspect model

RFC-0153's Alternatives section sketches the multiplicity axes as **independent
marker aspects** on a per-closure anonymous type — `Callable<A, R>` plus
orthogonal `CallMany` / `CallShared`, auto-implemented per RFC-0096. Under that
model this entire RFC dissolves: higher-order variance becomes ordinary
aspect-bound variance, and "any function at least this permissive" is just a bound
`where F: Callable<A, R>` with no `CallMany` requirement. It is the cleaner end
state for the erased (`dyn`) case and a direct input to metel-core#893. The
question is whether to adopt it for the static case too, or keep the flat
`Type::Fun` field model RFC-0152 / RFC-0134 use and treat markers as the `dyn`-only
view.

## Non-Goals

- The first-order directional rule — **RFC-0152**, accepted.
- The `once`/`many` inference and call-consumption semantics — **RFC-0134**.
- The mutation axis (`reading`/`mutating`) mechanics — **RFC-0153**. Whatever
  variance rule this RFC picks applies to that axis identically once it lands.

## Open Questions

1. Full contravariance vs. a permanent first-order cap — which does the first
   implementation commit to?
2. Is there a concrete program in the planned stdlib (v0.13–v0.17) that needs
   nested widening, or is the cap free until higher-order combinators are actually
   written?
3. Lattice (B) vs. marker aspects (C) vs. neither — and does that choice belong
   here or with metel-core#893 / RFC-0121?
4. Interaction with RFC-0125 variadic parameter packs.

## References

- **RFC-0152 (Function-Type Multiplicity Widening), `2-accepted`** — the
  first-order rule this RFC extends; §2's nested-function-type bullet and §4's
  "not a general subtype lattice" statement are the exact scope handed here.
- **RFC-0134 (Closure Call Capability), `2-accepted`** — defines the
  `call_multiplicity` / `use_multiplicity` fields and the `once`/`many` qualifier
  these variance rules range over.
- **RFC-0153 (Closure Mutation Axis)** — third axis; its Alternatives section is
  design-space option C.
- **RFC-0121 (Open Rows)** / **metel-core#893 (`dyn Callable`)** — where a
  structural / erased answer to "callable how many times" would live if the
  lattice question resolves that way.
- **RFC-0061 §7** — `Callable` and the function-pointer aspects.
- **RFC-0125** — variadic `|...Ts| -> R` parameter packs; Open Question 4.

---

## Decision

**Outcome:** *(pending — draft, split from RFC-0152 on 2026-08-30 so that RFC's
first-order half could be accepted without an open higher-order tail. Not urgent:
RFC-0152's first-order cap is a sound under-approximation, so nothing is unsound
while this is open — higher-order `once`/`many` mismatches are simply rejected
until a rule is chosen.)*
**Target:** *(set when accepted; no earlier than the first higher-order closure
combinator in the stdlib needs it.)*
