---
id: rfc-0152
title: "Function-Type Multiplicity Widening"
date: '2026-08-30'
status: integrated
target: v0.13.0
updated: '2026-09-01'
tracking: 'https://github.com/metel-lang/metel-core/issues/901'
coverage:
  "1": { spec: "spec.functions.closures.legality-9" }
  "2": { spec: "spec.functions.closures.legality-15" }
  "3": { spec: "spec.functions.closures.legality-16" }
  "4": { kind: untestable, reason: "Scope-boundary section (not a general Type::Fun subtype lattice; higher-order/contravariant -> RFC-0155). The first-order widening rule it does carry is spec-anchored at legality-9/15/16." }
impl_tracking: 'https://github.com/metel-lang/metel-core/issues/925'
impl_status: not-started
---


> **Status — accepted 2026-08-30**, as a co-requirement of RFC-0134 (the two move to
> `accepted` together). Part of the v0.13.0 closure cluster. RFC-0134 originally proposed
> exact-match multiplicity unification; that was withdrawn as unusable, so this directional
> rule is required, not deferred.

> **Scoped to the first-order case.** A function-typed value flowing into a function-typed
> **argument, `let`/field ascription, or return** slot. The contravariant direction for a
> function type nested inside another, and whether this should become a general `Type::Fun`
> subtype lattice, are **RFC-0155**'s. Below the first level of nesting this RFC requires
> an exact match — a sound under-approximation.


> **Status — integrated (2026-09-01).** Closure cluster spec-integrated (Legality 9/15/16); coverage.spec frontmatter added; fixtures blocked on metel-core#925. Shape: ADR-0052.

## Summary

Function-type multiplicities compose by **one-directional widening**: a function
value may be used where a *less permissive* multiplicity is expected, but not a
more permissive one. A `many`-call function satisfies a `once`-call slot; a
`Copy` function value satisfies a non-`Copy` slot. The reverse is rejected.

The rule applies at **first-order sites** — a function-typed value flowing into a
function-typed argument, a `let`/field ascription or struct-field init, or a
return slot. This is what makes `once fun(T) -> U` usable as an honest upper bound
in a signature without forcing every caller to hand-narrow a perfectly good `many`
closure. RFC-0134's `once` qualifier is not sound-and-usable without it, so the
two RFCs move to `accepted` in the same step.

The *contravariant* direction for a function type nested inside another function
type, and whether this coercion should be generalised into a `Type::Fun` subtype
lattice, are **RFC-0155**'s. Below the first level of nesting this RFC requires an
exact match — a sound under-approximation that rejects only programs a settled
higher-order rule would accept.

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
| mutation (RFC-0153) | `reading` | `mutating` | yes |
| mutation | `mutating` | `reading` | **no** |

Parameter and return types must still match on arity, argument types, and result
type as they do today; only the multiplicity fields gain the ordering. The `use`
axis widening is not new behavior — a `Copy` value is already usable where a move
is expected — this RFC just states it holds for function values through the
multiplicity field rather than by a `Type::Fun`-is-always-`Copy` special case
(which RFC-0134 §1 removes).

**The `mutation` axis** row is added 2026-09-01 with RFC-0153's co-land: `reading` is the
more-permissive value (a `reading` closure is safe wherever a `mutating` one is asked
for). Widening it is **type-level only, with no callability penalty**. A `reading` value
that flows into a `mut (T) -> U` slot keeps its actual runtime behavior; the slot type
only tells the *callee* it may treat `f` as needing exclusive access per call. Because
every widening site in §2 is a first-order by-value / owned position, the callee already
holds the value by value or `&var`.

**Runtime dispatch is on the value's own `call_mutation`, not the slot type** (RFC-0153
§3): a widened `reading` value is invoked on the plain call path — no exclusive borrow,
no in-call flag (it carries none) — exactly as through a `reading` slot. The callee
cannot observe the value's `reading`-ness *through the type system or any API* — that is
what "one-way precision loss" means — but the interpreter also simply does not perform
the `mutating`-call bookkeeping for a value that does not need it. The two statements are
consistent: the type is widened, the runtime is not.

### 2. Where it applies

- **Argument position** — the value flows into the slot: widen as above.
- **`let` / field ascription, struct field init** — same as argument position:
  the value flows into the annotated type. **This is a coercion into the field's declared
  (invariant) type, not a relaxation of the field's variance** — the two statements below
  are consistent. It is a deliberate, one-way **precision loss**: a `reading` closure
  stored into a `mut`-typed field is thereafter *observed* as `mut`, so every later read
  of that field yields a `mut` value that callers must invoke under exclusive access even
  though the underlying closure never mutates. Sound, but the author chose the field's
  type; there is no automatic re-narrowing.
- **Return position** — the callee produces the value the caller named a type
  for; a callee that returns a *more* permissive function than promised is fine,
  so the direction is unchanged (`many` return satisfies a `once` return slot). Same
  precision-loss caveat: a `fun … -> mut () -> U` that returns a `reading` closure hands
  the caller a `mut` value.
- **Struct fields** stay invariant, like every other field type — see the ascription
  bullet for how init nonetheless coerces into that invariant type.
- **A function type nested inside another function type** — *out of scope here.*
  Widening applies only at the top level of the slot being checked; a
  multiplicity mismatch on a function type that is itself an argument or return of
  another function type requires an exact match under this RFC. The contravariant
  rule that would relax it is **RFC-0155**.

### 3. Inference interaction

RFC-0134 §2 infers a closure literal's own call multiplicity from its body. That
inferred type is the *most permissive* type the closure actually has; widening
then lets it flow into any equal-or-less-permissive slot. Inference never needs
to *guess* a narrower multiplicity to make a call site work — it infers the true
one and widening does the rest. A `once`-body closure still cannot reach a `many`
slot, because it genuinely is not callable twice; that rejection is preserved.

Following RFC-0134's `many`-default rule, a closure literal's
own type is `many` / `reading` by default, or whatever a written qualifier or an
**expected type** supplies (RFC-0134 §2's 2026-09-01 amendment — an ascribed / return /
field slot, *including a typed block's tail expression*, supplies the qualifier; the
literal is not default-`many`-then-failed). Widening then applies to that resulting
*value* type wherever it and the slot still differ. So the two mechanisms compose:
expected-type checking first fixes the literal's type; widening covers any remaining
permissiveness gap.

**`if` / `match` join.** A conditional's type is the **least-permissive** of its arm
types under this RFC's order (`once` ≤ `many` on the call axis; `mutating` ≤ `reading` on
the mutation axis; non-`Copy` ≤ `Copy`), with each arm widened to it. `if c { g } else {
[s] () -> T { s } }` where `g: once () -> T` has type `once () -> T` — the `else` literal
is `many` by default and widens `many → once` into the join. A join that would need to
*narrow* an arm (one arm genuinely `once`, the context wanting `many`) is the ordinary
rejection. When neither arm's multiplicity is fixed (both default), the join keeps the
default. This is the same greatest-lower-bound rule the type checker already uses for
ordinary types in a conditional.

Three edge cases:

- **An arm whose multiplicity is still an unresolved inference variable at join time.**
  The join does not force it. The GLB is recorded as a *constraint* on that variable
  (`m_arm ≤ m_join`, discharged when the variable resolves — the same
  constraint-alongside-unification machinery RFC-0134 §3 describes for a function-typed
  parameter whose side is an `InferType::Var`). If it never resolves, ordinary
  ambiguity-error rules apply; the join adds nothing new.
- **A nested tail.** When an arm is itself an `if` / `match`, its type is that inner
  conditional's own join, computed first; the outer join then treats it as one arm type.
  An expected type on the outer conditional flows inward to each arm, including through
  the nested one, before the join — so `let f: once () -> T := if a { g } else if b { h }
  else { || … }` fixes every leaf literal at `once` by expected type, and the joins are
  then trivial.
- **A diverging arm** (`panic()`, `return`, any `!`-typed expression). It does **not**
  contribute to the GLB: `!` coerces to any type, so a diverging arm imposes no
  multiplicity floor. `if c { g } else { panic("x") }` has exactly `g`'s type, qualifier
  included. Only if *every* arm diverges is the conditional itself `!`.

### 4. Not a general subtype lattice

This is a directional coercion at the top-level sites in §2, not the introduction
of a `Type::Fun` subtyping relation the whole type system reasons over. There is
no `⊤`/`⊥` function type, no variance annotations, no bounded quantification. The
relation is decidable by axis-wise comparison of two concrete function types.
Whether it should *become* a real subtyping relation later — for abstracting over
"any function at least this permissive," and the marker-aspect model
(`Callable<A, R>` + orthogonal `CallMany` / `CallShared`, sketched in RFC-0153's
Alternatives) under which the whole coercion dissolves into bound-subsetting — is
**RFC-0155**, together with the higher-order variance question.

## Non-Goals

- **Higher-order variance and the subtype-lattice question — RFC-0155.** The
  contravariant direction for nested function types, whether to cap widening at
  first-order permanently, and whether to generalise the coercion into a real
  `Type::Fun` subtyping relation (or the marker-aspect model) all live there.
- The mutation axis — RFC-0153. When it lands, it joins this relation as a third
  axis with the same `many`-permits-`once` direction; nothing here needs to
  change to accommodate it, which is RFC-0134 §3's forward-compatibility
  constraint holding.
- Subtyping for anything other than the top-level multiplicity fields of an
  otherwise exactly-matching function type.
- Coercion *inserting* a runtime adapter. Widening is a static permission; the
  value is unchanged.

## Open Questions

1. **Is the `use`-axis widening ever observable separately?** RFC-0134 argues
   `call = once ⟹ use = once` (a call-once closure owns a non-`Copy` capture).
   If the implication is total, the `use` row of §1's table never fires
   independently of an ordinary `Copy`-where-move coercion, and this RFC only
   really adds the `call` row. Non-blocking — worth confirming before speccing the
   `use` row as its own rule rather than a corollary.
2. **Diagnostics.** When `once fun` is passed where `many fun` is required, the
   error should say "this function may only be called once" and point at the
   inferred `once` and the requiring signature — not a bare unification failure.

*(Higher-order variance and "should this become a subtype lattice," which were
Open Questions here before the 2026-08-30 split, are now RFC-0155's. Timing vs
RFC-0134 is resolved: they are accepted together — see the status note.)*

## References

- **RFC-0134 (Closure Call Capability)** — co-requirement. §3's "Decision" cites
  this RFC's first-order rule as the multiplicity-matching semantics; §4's
  `call_multiplicity` / `use_multiplicity` fields on `Type::Fun` are what it
  orders.
- **RFC-0154 (Pipe Notation for Closures and Function Types)** — the base
  function-type spelling (`|A, B| -> C`); examples here still use the current
  `(T) -> U` and are spelling-agnostic.
- **RFC-0155 (Higher-Order Function-Type Multiplicity Variance)** — everything
  split out of this RFC on 2026-08-30: contravariant nesting, the first-order cap,
  the `Type::Fun` subtype-lattice question, the marker-aspect model.
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

**Outcome:** Accepted 2026-08-30, as a co-requirement of RFC-0134. RFC-0134's
`once` qualifier is not sound-and-usable without the `many`-satisfies-`once`
direction at first-order sites, and RFC-0134's exact-match alternative was
withdrawn, so the two moved to `accepted` together. The higher-order /
contravariant case and the "become a real `Type::Fun` subtype lattice" question
were split out to **RFC-0155** on the same day, so this RFC carries no open
blocking question — the two remaining Open Questions are spec-refinements, not
gates.

**Target:** v0.13.0 (tracks RFC-0134, metel-core#269; tracker metel-core#901).
