---
id: rfc-0152
title: "Function-Type Multiplicity Widening"
date: '2026-08-30'
status: under-review
target:
updated: '2026-08-30'
tracking: 'https://github.com/metel-lang/metel-core/issues/901'
---

> **Deferred from RFC-0134 §3.** RFC-0134 decides multiplicity unification is
> **exact match** for its first implementation — `many fun(T) -> U` does *not*
> satisfy a slot that asks for `once fun(T) -> U`, "even though something callable
> any number of times trivially satisfies" a call-once requirement (§3, §4). It
> names this as a real ergonomic cost and calls the fix "a strict later
> widening." This RFC is that widening.

> **Status — under review (2026-08-30).** Deferred from RFC-0134 §3: replace exact-match multiplicity unification with a one-directional widening (many-call satisfies once-call, Copy satisfies non-Copy).

## Summary

Replace RFC-0134's exact-match unification of function-type multiplicities with a
**one-directional widening**: a function value may be used where a *less
permissive* multiplicity is expected, but not a more permissive one. A
`many`-call function satisfies a `once`-call slot; a `Copy` function value
satisfies a non-`Copy` slot. The reverse is rejected, exactly as it is under
exact match today.

This is the function-type analogue of the coercions the language already has —
`&var T` where `&T` is expected, a `Copy` value where a move is expected — and it
is what makes `once fun(T) -> U` usable as an honest upper bound in a signature
without forcing every caller to hand-narrow a perfectly good `many` closure.

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
4. **Timing vs RFC-0134.** Land together (RFC-0134 accepts with widening built
   in), or strictly after (RFC-0134 ships exact-match, this relaxes it)? RFC-0134
   is written for the latter; confirm that is still the intent.

## References

- **RFC-0134 (Closure Call Capability)** — §3 defers this widening; §4's
  `call_multiplicity` / `use_multiplicity` fields on `Type::Fun` are what it
  orders. §3a's `fun(T) -> U` spelling is assumed.
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

**Outcome:** *(pending — draft, opened 2026-08-30, deferred from RFC-0134 §3. The
first-order relation (§1) is straightforward; the open questions are higher-order
variance, whether the `use` axis adds anything over ordinary `Copy` coercion, and
whether this lands with or after RFC-0134.)*
**Target:** *(set when accepted; with or just after RFC-0134.)*
