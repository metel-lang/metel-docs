---
id: rfc-0097
title: "Orphan Rule for Bare-Parameter Blanket Impls"
date: '2026-07-11'
status: implemented
target:
updated: '2026-07-14'
impl_tracking: 'https://codeberg.org/metel-lang/metel-core/issues/269'
impl_status: implemented
---

> **New RFC.** Created despite `rfc.py new`'s overlap warning against RFC-0060, 0061,
> 0081, 0036, and 0035 — checked each first. RFC-0035 (`impl Aspect` in *parameter*
> position, implemented) is unrelated — a different feature entirely. The other four
> are genuinely adjacent but none resolve this: RFC-0060 §1 (Orphan Rule) defines
> locality only in terms of "the outermost type constructor of `Type`," and RFC-0060's
> *own* §3/§5 worked examples (`extend<T: Foo> T: Bar`) use exactly the case where no
> such constructor exists, without §1 ever being revisited to say what happens then.
> RFC-0036 (Conditional Impl Blocks) — the RFC that would normally own this syntax —
> never shows this form in any of its own examples either. Found while following up on
> RFC-0096 (opened the same day, same review pass): once auto-impl aspects made clear
> how much of the RFC corpus assumes "the auto-impl pattern" without one document
> owning it, checking blanket impls' own orphan-rule treatment surfaced the same shape
> of gap.

> **Status — accepted (2026-07-13).** Reviewed: the RFC is small, well-scoped, and closes a genuine gap in RFC-0060's own worked examples. Resolving Unresolved Question 1 (should RFC-0036 get a dedicated example) by keeping this RFC's own S2 examples as authoritative and updating RFC-0036's existing cross-reference (declarations.md) rather than duplicating content into RFC-0036 itself.

> **Status — integrated (2026-07-13).**

> **Status — implemented (2026-07-14).**

## Summary

`extend<T: Bound> T: Aspect` — a **bare-parameter blanket impl**, where the target is
literally the impl's own generic parameter, not a named struct or enum wrapping it —
appears throughout the accepted RFC corpus (RFC-0080 §1.2's `impl<T: Copy> Clone for
T`; RFC-0060 §3/§5's own `extend<T: Foo> T: Bar` example, used repeatedly to explain
closed-world discharge and negative-impl priority) with no RFC ever specifying two
things:

1. **Whether it's syntactically distinct from an ordinary conditional impl.** RFC-0036
   only ever shows `extend<T: Bound> Container<T>: Aspect` — a real named type
   wrapping `T`. It never shows or discusses `for T` alone.
2. **How the orphan rule (RFC-0060 §1) applies when the target has no outermost type
   constructor at all.** A bare type parameter isn't a struct or enum — it isn't
   "local" to any module, including the one declaring the impl. RFC-0060 §1's wording
   assumes every target has such a constructor to check.

This RFC settles both: no new syntax is needed (§1), and target-locality is *vacuously
unsatisfiable* for a bare-parameter target — such an impl is permitted only through the
aspect side of the orphan rule (§2). This has a clean, checkable consequence for
overlap detection (§3) that requires no new machinery.

---

## Motivation

RFC-0060 §3 ("Closed-World Assumption") and §5 ("Negative Impl Priority") both use
`extend<T: Foo> T: Bar` as their running example for how blanket impls interact with
negative bounds and negative impls — the *exact* bare-parameter form. RFC-0080 §1.2
ships a concrete instance of it as `Clone`'s canonical blanket:

```metel
extend<T: Copy> T: Clone {
    fun clone(self: &T) -> T { *self }
}
```

None of these citations trace back to RFC-0036 for the form's legitimacy, and RFC-0036
itself — despite being "Conditional Impl Blocks," the RFC that should own this — only
ever demonstrates the target as a genuinely named, parameterized type:

```metel
extend<T: Bound> Type<T>: Aspect { ... }        // RFC-0036 §1 — every example looks like this
extend<T: Comparable + Printable> SortedList<T>: Printable { ... }   // §2.2
extend<T: Copy> Wrapper<T>: Serialize { ... }  // §3.1
```

`Type<T>`/`SortedList<T>`/`Wrapper<T>` all have a real, nameable outermost constructor
— a struct declared somewhere with a fixed declaring module. RFC-0060 §1's orphan rule
is written entirely in terms of that constructor's locality: "the outermost type
constructor of `Type` (i.e., the struct or enum, ignoring type arguments)." A bare `T`
has no struct or enum to point at. Applying §1 literally to `impl<T: Copy> Clone for
T` produces an undefined question, not a wrong answer — the rule simply doesn't say
what "the outermost type constructor of `T`" means when `T` is the impl's own
parameter rather than a reference to a declared type.

This is the same shape of gap RFC-0096 found for auto-impl aspects: multiple accepted
documents lean on a construct's legitimacy without any one of them formally granting
it. The difference here is narrower — one rule (orphan-rule locality), one construct
(bare-parameter targets) — but the same fix pattern applies: name the gap precisely,
then close it without touching what already works.

---

## 1. Recognition: no new syntax, a semantic distinction only

A bare-parameter blanket impl is recognizable purely structurally, from the impl's own
existing shape — no grammar change is needed. `TypeExpr::Named(name, args)` already
represents a bare identifier as `Named("T", [])`; parsing `for T` requires nothing
`for Container<T>` doesn't already parse. The distinction that matters is semantic, not
syntactic:

> An impl `extend<G1: B1, ..., Gn: Bn> Target: Aspect` is a **bare-parameter blanket**
> exactly when `Target` is itself one of `G1..Gn` — the impl's own generic parameter,
> referenced with no wrapping type constructor — rather than a named struct or enum
> (whether or not that struct/enum is itself parameterized over `G1..Gn`).

This holds regardless of *which* parameter, or how many others the impl declares:
`extend<A, B: Bound> B: Aspect` is a bare-parameter blanket over `B` exactly the same
way `extend<T: Bound> T: Aspect` is over `T` — the presence of an unrelated parameter
`A` changes nothing about `B`'s own target-locality question.

---

## 2. Orphan rule: target-locality is vacuously false

A bare type parameter is not declared in any module — it has no fixed identity outside
the impl that introduces it, unlike a struct or enum, which is declared exactly once,
somewhere, and is either local to the impl's module or isn't. There is nothing for
"local to this module" to mean for a bare parameter, in any module, including the
impl's own and including `std::core`.

**Consequence:** for a bare-parameter blanket impl, the orphan rule (RFC-0060 §1)
reduces to checking only the aspect side. The impl is permitted exactly when the
aspect is local to the impl's own module — including the `impl` living in `std::core`
and naming one of `std::core`'s own aspects, which is simply the ordinary case of that
rule, not a separate exception: every aspect in this codebase (`Display`, `Clone`,
`Eq`, and so on) is a real `aspect` declaration living in some real module, `std::core`
included, so "the aspect is local to the impl's module" already covers it without a
parenthetical carve-out. It is never permitted on the strength of the target, because
the target side of the check is permanently unsatisfiable for this shape of impl.

```metel
// std::core, RFC-0080 §1.2 — permitted: Clone is local to std::core
extend<T: Copy> T: Clone { fun clone(self: &T) -> T { *self } }

// hypothetical user module — permitted: MyAspect is local here
aspect MyAspect { fun tag(self) -> String; }
extend<T: Copy> T: MyAspect { fun tag(self) -> String { "copyable" } }

// hypothetical user module — REJECTED (T0014): Display is foreign,
// and a bare-parameter target can never be local, anywhere
extend<T: Copy> T: Display { fun to_string(self) -> String { "?" } }
```

This is a narrower rule than RFC-0061 §1's own fix for a structurally similar problem.
RFC-0061 faced targets with no *declared* constructor either (`T[]`, tuples, function
types) and resolved it by fiat: structural type constructors are *owned by
`std::core`* for orphan purposes — i.e., always locally satisfiable, but only in one
specific place. This RFC's answer is the opposite polarity: a bare parameter is owned
by *no* module, `std::core` included — always locally unsatisfiable, everywhere. The
difference is real, not arbitrary: `T[]` names a fixed, singular type former that
`std::core` can sensibly be said to own; a bare impl parameter `T` isn't a type former
at all — it's a placeholder for literally any type, so no module could coherently own
it without that "ownership" meaning every type is local to that module, which would
gut the orphan rule entirely.

---

## 3. Overlap detection: no new machinery required

With §2's rule in force, a bare-parameter blanket impl of a given aspect can only ever
exist in that aspect's own declaring module (or, for a built-in aspect, in
`std::core`) — no other module can pass the orphan check for one. Two bare-parameter
blankets of the same aspect can therefore only coexist within that single module,
which is exactly the case RFC-0060 §2 and RFC-0036 §3.1 already handle: overlap is
checked when there exists a concrete instantiation satisfying both impls' bound sets,
using syntactic negation to establish disjointness. Nothing here needs a new rule —
§2's orphan-rule fix is what *confines* bare-parameter blanket overlap to a single
module in the first place, which is the property RFC-0060 §2 already relies on to
call overlap detection "local."

Concretely: `extend<T: Copy> T: Clone` in `std::core` cannot be contested by a second,
competing bare-parameter `Clone` blanket from any user module, because no user module
can ever pass §2's orphan check for `Clone` (a foreign aspect to them). The only way a
concrete type's `Clone` could still conflict with the blanket is the ordinary case
RFC-0080 §1.2 already describes in prose — a type separately implementing `Clone`
directly while also being `Copy` — which is caught by the *existing*, general overlap
rule (a concrete impl and an applicable blanket for the same type always overlap),
with no bare-parameter-specific handling needed.

---

## 4. What this doesn't cover

- **Conditional impls for a genuinely named, parameterized target**
  (`extend<T: Bound> Container<T>: Aspect`) — RFC-0060 §1's existing wording already
  works for these; `Container` has a real outermost constructor to check. This RFC
  only concerns the case where the target *is* the parameter, not a type built from it.
- **Structural type constructors as targets** (`T[]`, tuples, function types) —
  already resolved by RFC-0061 §1 ("owned by `std::core`"), a different fix for a
  visually similar but structurally distinct problem (see §2's contrast, above).
- **Whether bare-parameter blankets should be restricted or discouraged for other
  reasons** (API design, specialization conflicts with future language features) — out
  of scope; this RFC only closes the orphan-rule gap for a construct the corpus
  already uses.

---

## Unresolved Questions

1. **Should RFC-0036 be amended to show this form explicitly?** This RFC resolves the
   orphan-rule question but doesn't add worked examples to RFC-0036 itself. Whether
   RFC-0036 gets a dedicated example section for bare-parameter blankets, or whether
   this RFC's own examples (§2) are considered sufficient once accepted, is left open.

2. **Multiple bare parameters as the target simultaneously.** `impl<T: Bound> Aspect
   for T` names one parameter as the target. Whether any construct could sensibly name
   more than one (there is no target syntax that would do this — `Target` is a single
   `TypeExpr`) is not a real question, included only to record that it was considered
   and dismissed as inapplicable, not overlooked.

---

## References

- RFC-0060 (Aspect Impl Coherence, implemented) — §1's orphan rule, whose wording this
  RFC extends to bare-parameter targets; §3/§5's own examples are what exposed the gap.
- RFC-0036 (Conditional Impl Blocks, implemented) — the syntax this RFC's target form
  is an instance of; never shows the bare-parameter case in its own examples.
- RFC-0080 (Standard Library Aspects, under review) — §1.2's `Clone` blanket, the
  concrete motivating example.
- RFC-0061 (Structural Aspect Bounds, implemented) — §1's "structural constructors are
  owned by `std::core`" fix, the closest existing precedent, contrasted in §2.
- RFC-0096 (Auto-Impl Aspects, draft) — opened the same review pass; the auto-impl
  recognition gap that prompted checking blanket impls' own orphan-rule treatment.

---

## Decision

**Outcome:** Accepted
**Target:** v0.10.0 (sprint-26, issue #269)
