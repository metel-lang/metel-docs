---
id: rfc-0213
title: "Super-Aspects"
date: '2026-11-04'
status: under-review
updated: '2026-11-04'
tracking: 'https://github.com/metel-lang/metel-core/issues/1796'
---

> **Split from RFC-0168 on 2026-11-04.** RFC-0168 defines the equality model and, in one section,
> the super-aspect relation. The `Copy`/`Clone` settlement (RFC-0206, RFC-0212) needs the relation
> and not the equality model, so the relation is its own RFC; RFC-0168 depends on it. The text of
> the relation below is RFC-0168's, kept in substance, with the derivation rule added. Nothing here
> is decided.

> **Status — under review (2026-11-04).** first draft opened for review

## Summary

An aspect declaration may list one or more direct super-aspects after its name:

```metel
pub aspect Ord: Eq {
    fun cmp(&self, other: &Self) -> Ordering;
}
aspect ImplicitClone: derived Clone, !Drop;   // sketch: requires Clone (derived with it), excludes Drop
```

The relation `A: B` is nominal and transitive: a proof of `T: A` also proves `T: B`; an
implementation of `A` requires a coherent `B` for the same type; negative implementations stay
local. A super-aspect entry may be negative (`!B`): no type satisfies both aspects (section 3).
A super-aspect entry marked `derived` is derived together with the sub-aspect (section 4); an unmarked
entry is only an obligation.

---

## Motivation

- **RFC-0168** needs `Eq: PartialEq`.
- **The `Copy`/`Clone` settlement** needs `ImplicitClone: Clone`, so that every implicit-copy type is
  explicitly copyable by construction and `T: ImplicitClone` entails `T: Clone` in the checker and in
  the abstract analysis of generic bodies. Today the abstract-variable satisfaction query consults
  only its explicit assumption set and does not discover super-aspects
  (`type_engine/mod.rs`, `infer_type_satisfies_aspect`).
- **Without the relation** each special aspect needs its own built-in entailment, which is the kind of
  exception RFC-0212 removes.

---

## 1. The relation

1. An aspect lists direct super-aspects after its name: `aspect A: B, C`. Each must be a visible
   aspect. The initial design permits only aspects, not aliases (`aspect Key = Eq + Hash;` stays
   RFC-0039's transparent shorthand for a bound and supplies no implication).
2. The relation is transitive. If `A: B` and `B: C`, a proof of `T: A` proves `T: C`.
3. A cycle, direct or indirect, is rejected.
4. It is not subtyping. No runtime coercion exists from `A` to `B`; the relation only expands what a
   bound proves to the checker and which methods are available through that proof.
5. Through a bound `T: A`, the methods of every super-aspect of `A` are callable on `T`.

## 2. Implementations

For an explicit `extend T: A`, every direct and transitive super-aspect obligation must be satisfied
by a coherent impl for `T`, written or derived (section 4). The compiler does not manufacture one
from the sub-aspect's impl by the compiler; deriving is the job of `derives` (section 4).

## 3. Negative implementations

RFC-0081's negative impls stay direct assertions. Coherence and, later, the obligation solver (metel-core#1813)
share one **signed closure**; in v0.16.0 only coherence uses it:
- **Positive:** `T: A` implies `T: B` for each super-aspect `B` of `A`.
- **Exclusion:** `T: A` entails `T: !C` for each negative entry `!C` of `A`, and symmetrically
  `T: C` entails `T: !A`.
- **Contrapositive:** `T: !B` entails `T: !A` for each sub-aspect `A` of `B`, so an explicit `T: !B`
  makes an impl of `A` for `T` a coherence error.
- **No downward propagation:** `T: !A` does not imply `T: !B`.

Any direct contradiction after the closure is a coherence error.

1. **Coherence uses the syntactic closure only.** Super entries and exclusions come from aspect
   declarations, which exist before type checking, so no solved facts are needed. Two impls are disjoint
   when a positive requirement of one is excluded, directly or by entailment, by a negative requirement
   of the other. `extend<T: ImplicitClone> W<T>: A` and `extend<T: Drop> W<T>: A` are disjoint because
   `ImplicitClone` excludes `Drop`.
2. **Absence is not negation.** "No impl of `C` exists" never proves `T: !C`. In generic code `!C` comes
   only from a bound or an entailment. A grant on a concrete named type is checked in its defining
   module, where the orphan rule closes its impl set for the aspects of std (`Drop`), so
   `ImplicitClone` on a `Drop` type is a coherence error at the grant. Unknown stays unknown and is never
   a proof of `!Drop`.
3. **Priority applies before closure.** If a negative impl wins over a blanket positive impl for a type
   (RFC-0060 section 5), the closure is computed from the facts after that choice. A positive impl of a
   sub-aspect for that type whose super-aspect now fails is a coherence error, and a blanket
   sub-aspect impl is inapplicable at that type. Closure never resurrects the base.
4. **A negative super entry is part of the aspect's contract.** Deleting it is a language change: it can
   turn disjoint impls into `T0015` and lets one type satisfy both aspects.

A negative entry in the super list (`aspect A: B, !C`) declares an exclusion: no type satisfies both
`A` and `C`. A grant of the second is reported at that grant (RFC-0060), naming both; `T: A` entails
`T: !C`; the exclusion is symmetric and need be declared on one side only. It generalises RFC-0071 §4
and replaces the `excludes` property of an earlier draft of RFC-0212.

## 4. Derivation of super-aspects

A super-aspect entry is an **obligation** unless it is marked `derived`. The mark says that the
derivation recipe of the sub-aspect includes the super-aspect, because the sub-aspect's law is stated
over the super-aspect's methods (`Eq` over `PartialEq`, `ImplicitClone` over `Clone`). The aspect's
author marks it; std decides the first set.

1. **Unmarked entry** (`aspect Error: Display`, the default, as in Rust and Haskell): `derives A` requires
   the super-aspect to exist for the type, written or derived by its own `derives`. There is no overlap
   and no `T0015`.
2. **Marked entry** (`aspect Eq: derived PartialEq`): `struct P derives A` derives `A` and every marked
   super-aspect `B` of `A` (transitively), exactly as `struct P derives A, B, …` would. A written
   `extend P: B` for an aspect the `derives` generates overlaps and is an error (`T0015`). The
   fix-it offers: delete the impl; or write `A` by hand instead of deriving it, using `extend P: A;`
   when `A` has no methods, or the colon list when `A` is `declared` and has no methods (RFC-0207
   section 1); a method-bearing `A` is simply written by hand.
3. A marked super-aspect without a derivation (RFC-0207) makes the `derives` an error with a fix-it:
   write that super-aspect by hand, then list `A` in the colon list if `A` is `declared` and method-less,
   or write `A` by hand otherwise.
4. Derivation is idempotent per type and aspect: `derives A, B` is valid and derives `B` once.
5. `struct P: A` (the colon list) generates nothing: every positive super-aspect, marked or not, must
   already exist for `P`, or it is an error naming the missing one (section 2).

**Why a mark.** A derived marker is sound only over a derived base: `derives Eq` justifies `Eq` because
the compiler also wrote the field-wise `PartialEq`, so reflexivity follows from every field being `Eq`
(RFC-0168). Deriving `Eq` over a hand-written `PartialEq` would assert a law for an `eq` the compiler
never saw. That argument is about aspects whose law ties them to a super-aspect. It does not hold for a
super-aspect that is an independent capability (`Error: Display`: deriving `Error` should not write the
author's message), so the default is an obligation and the aspect's author opts in.

**The mark is part of the aspect's contract,** as an exclusion is (section 3). Adding `derived` to an
entry can introduce generation of `B` and turn existing written `B` impls into `T0015`; removing it can
remove the `B` that made downstream `derives A` valid. Both are breaking changes to the aspect.

**Diamonds.** `A: B, C` with `B: D` and `C: D` has one obligation `D`, deduplicated by aspect identity
and arguments; a marked path derives it once.

## 5. Worked examples

```metel
aspect PartialEq { fun eq(&self, other: &Self) -> boolean; }
aspect Eq: derived PartialEq;                // derives PartialEq with it
struct Id { n: i64 }
extend Id: PartialEq { … }
extend Id: Eq;                               // ok: PartialEq exists
struct Bad { n: i64 }
extend Bad: Eq;                              // error: no PartialEq for Bad

aspect ImplicitClone: derived Clone, !Drop;
struct Point derives ImplicitClone { x: i64 }          // derives Clone too
struct Cache: ImplicitClone { n: i64 }
extend Cache: Clone { fun clone(&self) -> Cache { … } }   // ok: the colon form, with a hand-written Clone
struct Both derives ImplicitClone { n: i64 }
extend Both: Clone { … }                     // error T0015: overlaps the derived Clone; write `: ImplicitClone`
struct Dup derives Clone, ImplicitClone { n: i64 }
extend Dup: Clone { … }                      // error T0015: overlaps the derived Clone
```

## 6. Alternatives considered

- **No relation; a built-in entailment per aspect.** Rejected: an exception per aspect.
- **Aspect aliases as the relation.** Rejected by RFC-0168: an alias creates no implementation target.
- **Derive only the super-aspects that are missing.** Rejected: which impls the compiler generated would depend on what else is in the module, and a derived marker would sit over an impl the compiler never saw.
- **A uniform rule: `derives A` derives every positive super-aspect.** Tried and reversed on 2026-11-04: it over-derives independent capabilities (`Error: Display`) and makes an aspect with a non-derivable super non-derivable. The mark restores the Rust and Haskell default (an obligation) and lets a law-bearing super opt in.
- **A separate `provides` clause with a body** (an earlier draft of RFC-0206 and RFC-0207). Rejected:
  it needs a selection rule over overlapping impls and an equality law between two bodies.

## Relationship to existing RFCs

- **RFC-0168** — the equality model, which depends on this RFC.
- **RFC-0212** — properties of an aspect declaration; `implicit` needs the relation.
- **RFC-0206** — `ImplicitClone: Clone, !Drop`.
- **RFC-0207** — the `derives` clause and the derivations this rule builds on.
- **RFC-0081 / RFC-0060** — negative impls and coherence, extended by section 3.
- **RFC-0039** — aspect aliases, unchanged.

## Open questions

1. **The spelling of a negative entry** (`!Drop` in the list, as sketched) and of the `derived` mark.
2. **`dyn` and object safety** for an aspect with super-aspects.
3. **Diamonds:** resolved in section 4 (one obligation, deduplicated).
4. **Associated items and default methods** of a super-aspect, and whether a sub-aspect may override
   a default.
5. **Generic aspects** (`aspect A<T>: B<T>`).
6. **Where the abstract analysis consults the relation,** and how it composes with assumption sets.
7. **An opt-in for deriving a sub-aspect over a hand-written super-aspect.** A marked super-aspect (section 4)
   is derived with its sub-aspect, so a sub-aspect whose marked super is written by hand (`derives Ord`
   over a written `Eq`, if `Ord` marked `Eq`) is `T0015` and the author writes the sub-aspect by hand.
   Two candidates, to be taken up when a real case appears:
   - *`given`:* `struct T derives Hash given PartialEq, Eq` lists the super-aspects written by hand.
     Each must be a transitive positive super of the derived aspect and must already have a written
     impl; everything unlisted is derived as before. The header still shows what is generated, and the
     entry is the author's vouch for the law that links the two (the compiler checks only that the base
     exists).
   - *A callable derived body:* the derivation is exposed so that a written impl can delegate to it
     (a delegating call such as `Ord::derived(self, other)`, spelled as the aspect's own method; `Hash` is
     only an example and its API is RFC-0176's) and adjust one field, which is the usual real need. It belongs with
     comptime derivation (RFC-0092, RFC-0093).
   Not provided now: a derived `Ord` over a custom `eq` is wrong whenever the custom `eq` ignores a
   field, and the marked-super rule removes that footgun. Rejected shape: letting the colon list carry
   method-bearing aspects (it reverses RFC-0207 section 1 and makes the list redundant with `extend`).

---

## Decision

**Outcome:** *(pending)*
