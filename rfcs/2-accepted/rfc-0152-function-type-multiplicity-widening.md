---
id: rfc-0152
title: "Function-Type Multiplicity Widening"
date: '2026-08-30'
status: accepted
target: v0.13.0
updated: '2026-08-30'
tracking: 'https://github.com/metel-lang/metel-core/issues/901'
---

> **Split into two halves (2026-08-30 revision).** RFC-0134 originally proposed
> **exact-match** multiplicity unification and named this widening "a strict later
> widening." That exact-match proposal was **withdrawn** on 2026-08-30 — it made
> the `once` qualifier unusable in practice (§3, §4 of RFC-0134). The
> **first-order directional rule** of this RFC (§1, §3 here — `many`-call satisfies
> a `once`-call slot, `Copy` satisfies non-`Copy`, at argument / ascription /
> return sites) is now a **co-requirement of RFC-0134: the two are accepted
> together**, because RFC-0134's `once` qualifier is not sound-and-usable without
> it. What stays with this RFC as its own later question is the **higher-order /
> contravariant** case (§2's nested-function-type direction, Open Question 2) and
> whether the relation should **become a real `Type::Fun` subtype lattice** the
> whole type system reasons over (§4, Open Question 1).

> **Status — first-order half accepted with RFC-0134 (2026-08-30); higher-order
> variance + subtype-lattice question remain open in this RFC.**

> **Status — accepted (2026-08-30).** First-order directional rule (S1, S3) accepted as a co-requirement of RFC-0134 (2026-08-30): RFC-0134's once qualifier is not sound-and-usable without many-satisfies-once at argument/ascription/return sites, and RFC-0134's exact-match alternative was withdrawn. Higher-order/contravariant case (S2, OQ2) and the Type::Fun subtype-lattice question (S4, OQ1) stay open in this RFC and block neither.

## Summary

Function-type multiplicities compose by **one-directional widening**: a function
value may be used where a *less permissive* multiplicity is expected, but not a
more permissive one. A `many`-call function satisfies a `once`-call slot; a
`Copy` function value satisfies a non-`Copy` slot. The reverse is rejected.

**First-order half (§1, §3) — co-requirement of RFC-0134, accepted together.**
The directional rule at argument, `let`/field ascription, struct-field-init, and
return sites is what makes `once fun(T) -> U` usable as an honest upper bound in a
signature without forcing every caller to hand-narrow a perfectly good `many`
closure. RFC-0134's `once` qualifier is not sound-and-usable without it, so it is
not deferred: the two RFCs move to `accepted` in the same step.

**Higher-order half — stays open in this RFC.** The direction for a function type
nested inside another function type's argument (contravariant; §2, Open Question
2) and whether this coercion should become a general `Type::Fun` subtype lattice
(§4, Open Question 1) are this RFC's remaining work and do not block RFC-0134.

This is the function-type analogue of the coercions the language already has —
`&var T` where `&T` is expected, a `Copy` value where a move is expected.

## Motivation

RFC-0134 §3's own worked example: `public fun each<T>(&self, f: once fun(T) -> ())`
promises "I call `f` at most once." A caller holding a `many`, `Copy` closure —
the common case, a closure that captures nothing but reads — cannot pass it,
because exact-match unification sees `many ≠ once`. The caller's options are to
wrap it, to weaken `each`'s signature to `many` (a lie about what `each` does, and
a semver hazard — RFC-0134 §3 spells this out), or to not use `once` in
signatures at all. All three defeat the point of having the qualifier.

Under exact match the qualifier is only safe to write when you can guarantee
*every* caller will have exactly that multiplicity — which for `once` is almost
never. Widening makes `once` in a signature mean what it reads as: an upper bound
the callee respects, that any tighter-or-equal value satisfies.

## Proposal

### 1. The relation

For each multiplicity axis, `many` is the **more permissive** value and `once` is
the **less permissive** one. A function type `F` *widens to* `G` (`F` is usable
where `G` is expected) when, axis by axis, `F`'s value is at least as permissive
as `G`'s:

| Axis | `F` has | `G` (the slot) wants | Widens? |
|---|---|---|---|
| call | `many` | `once` | yes |
| call | `once` | `many` | **no** |
| call | `x` | `x` | yes |
| use (`Copy`-ness) | `many` (Copy) | `once` (non-Copy) | yes |
| use | `once` | `many` | **no** |

Parameter and return types must still match on arity, argument types, and result
type as they do today; only the multiplicity fields gain the ordering. The `use`
axis widening is not new behavior — a `Copy` value is already usable where a move
is expected — this RFC just states it holds for function values through the
multiplicity field rather than by a `Type::Fun`-is-always-`Copy` special case
(which RFC-0134 §1 removes).

### 2. Where it applies, and variance

- **Argument position** — the value flows into the slot: widen as above.
- **`let` / field ascription, struct field init** — same as argument position:
  the value flows into the annotated type.
- **Return position** — the callee produces the value the caller named a type
  for; a callee that returns a *more* permissive function than promised is fine,
  so the direction is unchanged (`many` return satisfies a `once` return slot).
- **A function type nested inside another function type's argument** —
  contravariant, so the direction flips: a parameter `g: fun(once fun(T) -> U) -> V`
  accepts an argument `fun(many fun(T) -> U) -> V` **no**, accepts
  `fun(once fun(T) -> U) -> V` yes... *(this is the standard higher-order variance
  question and is Open Question 2 — the table above is the first-order case only)*.
- **Struct fields** stay invariant, like every other field type.

### 3. Inference interaction

RFC-0134 §2 infers a closure literal's own call multiplicity from its body. That
inferred type is the *most permissive* type the closure actually has; widening
then lets it flow into any equal-or-less-permissive slot. Inference never needs
to *guess* a narrower multiplicity to make a call site work — it infers the true
one and widening does the rest. A `once`-body closure still cannot reach a `many`
slot, because it genuinely is not callable twice; that rejection is preserved.

### 4. Not a general subtype lattice

This is a directional coercion at the sites in §2, not the introduction of a
`Type::Fun` subtyping relation the whole type system reasons over. There is no
`⊤`/`⊥` function type, no variance annotations, no bounded quantification. The
relation is decidable by axis-wise comparison of two concrete function types.
Whether it should *become* a real subtyping relation later (for e.g. abstracting
over "any function at least this permissive") is explicitly out of scope and
belongs with RFC-0121-style row/structural polymorphism if anywhere.

If the multiplicity axes were instead **marker aspects** on a per-closure
anonymous type (`Callable<A, R>` + orthogonal `CallMany` / `CallShared`, sketched
in RFC-0153's Alternatives section), this whole RFC dissolves: widening becomes
ordinary bound satisfaction — a slot requiring marker set `M` accepts any value
whose markers `⊇ M`. That is the cleaner end state for the erased (`dyn`) case
and is an input to metel-core#893; it does not remove the need for *some* widening
rule in the field model this RFC and RFC-0134 actually use.

## Non-Goals

- The mutation axis — RFC-0153. When it lands, it joins this relation as a third
  axis with the same `many`-permits-`once` direction; nothing here needs to
  change to accommodate it, which is RFC-0134 §3's forward-compatibility
  constraint holding.
- Subtyping for anything other than the multiplicity fields of an otherwise
  exactly-matching function type.
- Coercion *inserting* a runtime adapter. Widening is a static permission; the
  value is unchanged.

## Open Questions

1. **Is the `use`-axis widening ever observable separately?** RFC-0134 argues
   `call = once ⟹ use = once` (a call-once closure owns a non-`Copy` capture).
   If the implication is total, the `use` row of §1's table never fires
   independently of an ordinary `Copy`-where-move coercion, and this RFC only
   really adds the `call` row. Worth confirming before speccing the `use` row as
   its own rule.
2. **Higher-order variance** (§2). Nail down the direction for a function type
   appearing in argument vs return position of another function type, and whether
   the first implementation supports it at all or restricts widening to
   first-order function-typed slots.
3. **Diagnostics.** When `once fun` is passed where `many fun` is required, the
   error should say "this function may only be called once" and point at the
   inferred `once` and the requiring signature — not a bare unification failure.
4. **Timing vs RFC-0134.** *Resolved 2026-08-30 — land together.* RFC-0134's
   exact-match proposal was withdrawn as unusable; the first-order rule here (§1,
   §3) is a co-requirement and moves to `accepted` in the same step as RFC-0134.
   RFC-0134's prose has been updated to match (its §3 "Decision" now cites this
   rule rather than deferring it). Only the higher-order half (OQ2) and the
   subtype-lattice question (OQ1) remain deferred, and they are this RFC's, not
   RFC-0134's.

## References

- **RFC-0134 (Closure Call Capability)** — co-requirement. §3's "Decision" cites
  this RFC's first-order rule as the multiplicity-matching semantics; §4's
  `call_multiplicity` / `use_multiplicity` fields on `Type::Fun` are what it
  orders.
- **RFC-0154 (Pipe Notation for Closures and Function Types)** — the base
  function-type spelling (`|A, B| -> C`); examples here still use the current
  `(T) -> U` and are spelling-agnostic.
- **RFC-0153 (Closure Mutation Axis)** — the third axis this relation will also
  order, on the same direction.
- **RFC-0135 (Multiplicity for Ordinary Types)** — `Copy` as `many` for by-value
  use; the `use` axis of §1 is that reframing applied to function values.
- **RFC-0067a (Reference Types)** — precedent: `&var T` widens to `&T` at the
  same kinds of sites, a directional coercion rather than a subtype lattice.
- **RFC-0061 §7** — `Callable` and the function-pointer aspects; a `dyn Callable`
  (metel-core#893) would need its own answer to "callable how many times," which
  this relation informs but does not settle.

---

## Decision

**Outcome:** *(first-order half — §1, §3 — proposed for acceptance alongside
RFC-0134, 2026-08-30. It is a co-requirement: RFC-0134's `once` qualifier is
unusable without the `many`-satisfies-`once` direction, and RFC-0134's exact-match
alternative was withdrawn. The higher-order / contravariant case (§2, Open
Question 2) and the "become a real `Type::Fun` subtype lattice" question (§4, Open
Question 1) stay open in this RFC and do not block acceptance of the first-order
half or of RFC-0134.)*
**Target:** *(first-order half tracks RFC-0134's milestone. Higher-order half set
when that question is settled.)*
