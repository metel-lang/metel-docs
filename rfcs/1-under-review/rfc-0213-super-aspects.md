---
id: rfc-0213
title: "Super-Aspects"
date: '2026-11-04'
status: under-review
updated: '2026-11-05'
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
aspect Copy: derived Clone, !Drop;            // sketch: Clone derived with it, Drop excluded (and Linear, RFC-0089, once it exists)
```

The relation `A: B` is nominal and transitive: a proof of `T: A` also proves `T: B`; an
implementation of `A` requires a coherent `B` for the same type; negative implementations stay
local. A super-aspect entry may be negative (`!B`): no type satisfies both aspects (section 3).
A super-aspect entry marked `derived` is derived together with the sub-aspect (section 4); an unmarked
entry is only an obligation.

---

## Motivation

- **RFC-0168** needs `Eq: PartialEq`.
- **The `Copy`/`Clone` settlement** needs `Copy: Clone`, so that every implicit-copy type is
  explicitly copyable by construction and `T: Copy` entails `T: Clone` in the checker and in
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

## 3. Negative implementations and exclusions

RFC-0081's negative impls stay direct assertions. Super-aspects add one closure rule and one declared check:
- **Positive:** `T: A` implies `T: B` for each super-aspect `B` of `A`. This is used by the checker and the abstract
  analysis, and it is the whole of the closure in v0.16.0.
- **Exclusion (a negative entry, `aspect A: B, !C`):** no type may be granted both `A` and `C`. It is a **grant-time
  check only** (decided 2026-11-05): a grant of the second is reported at that grant (RFC-0060), naming both, and the
  exclusion is symmetric and need be declared on one side only. It generalises RFC-0071 §4 and replaces the
  `excludes` property of an earlier draft of RFC-0212. `Copy` excludes `Drop` (and `Linear` once it exists) by this
  entry; the justification is operational (RFC-0089 section 1).
- **No downward propagation:** `T: !A` does not imply `T: !B`.

Any direct contradiction (a grant of an excluded pair, or an impl of `A` for a type with an explicit `T: !B` where `A`
requires `B`) is a coherence error.

1. **An exclusion is not evidence for disjointness.** Overlap of two impls is decided by the existing comparison of
   their explicit bounds. `extend<T: Copy> W<T>: A` and `extend<T: Drop> W<T>: A` are not proven disjoint by the
   exclusion and are `T0015` unless the author writes explicit disjoint bounds (`T: Copy` and `T: !Copy`).
2. **A negative super entry is part of the aspect's contract at the grant:** deleting it is a language change that lets
   one type be granted both aspects.
3. **Priority before closure.** If a negative impl wins over a blanket positive impl for a type (RFC-0060 section 5),
   a positive impl of a sub-aspect for that type whose super-aspect now fails is a coherence error, and a blanket
   sub-aspect impl is inapplicable at that type. Closure never resurrects the base.

**Deferred extension: disjointness evidence.** A later minor may use exclusions as evidence for disjointness, with the
derived negatives (`T: A` entails `T: !C`; the contrapositive `T: !B` entails `T: !A` for sub-aspects of `B`) and the
rule that absence is not negation (an unknown is never a proof of `!Drop`; a grant on a concrete named type is
checked in its defining module, where the orphan rule closes the impl set for the aspects of std). Adding it is
monotone (pairs that were `T0015` become accepted and no accepted program changes), but the exclusions then become a
public coherence contract and removing one can break other libraries, which is why v0.16.0 leaves it out (the fourth
adversarial review rated it high risk and no surveyed language does it: Rust hardcodes `Copy` against `Drop` and has
only explicit negative impls).

## 4. Derivation of super-aspects

A super-aspect entry is an **obligation** unless it is marked `derived`. The mark says that the
derivation recipe of the sub-aspect includes the super-aspect, because the sub-aspect's law is stated
over the super-aspect's methods (`Eq` over `PartialEq`, `Copy` over `Clone`). The aspect's
author marks it, **but only std aspects may carry the mark in v0.16.0** (decided 2026-11-05); a user aspect's
entry is always an obligation, and its author writes both impls by hand, as in Rust. `Copy: derived Clone` is the
settlement's one use; `Eq: derived PartialEq` (RFC-0168) is the other std case. A `derived` on a user aspect is an
error.

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

**Why a mark.** This is a conservative generation policy, not a proof that a hand-written base is unsound (a
hand-written `PartialEq` can satisfy its laws perfectly). `derives Eq` generates `Eq` together with the field-wise
`PartialEq` the compiler also wrote, so reflexivity follows from every field being `Eq` (RFC-0168); the policy
declines to trust a relationship between a generated marker and a base the compiler never saw. Generating both does
not prove their laws unconditionally either: field implementations keep their contracts. That argument is about
aspects whose law ties them to a super-aspect. It does not hold for a
super-aspect that is an independent capability (`Error: Display`: deriving `Error` should not write the
author's message), so the default is an obligation and the aspect's author opts in.

**The mark is part of the aspect's contract,** as an exclusion is (section 3). Adding `derived` to an
entry can introduce generation of `B` and turn existing written `B` impls into `T0015`; removing it can
remove the `B` that made downstream `derives A` valid. Both are breaking changes to the aspect.

**Known novelty, and why it is std only.** Haskell and Rust require the superclass instance to exist and never generate it from the subclass's
derivation (Swift generates a missing one, as `Hashable` does for `Equatable`). A generic per-edge mark that
makes the sub-aspect's derivation generate a super-aspect is a less established combination: it is judged moderate
risk because it changes downstream generated impl sets when added or removed (see above). Restricting it to std
confines the unproven combination to the aspects the settlement needs, and leaves its compatibility breakage under
std's own change policy. Opening it to user aspects is an addition and forecloses nothing (open question 9).

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

aspect Copy: derived Clone, !Drop;
copy struct Point { x: i64 }                 // = derives Copy: derives the marker and its Clone
struct Cache { n: i64 }
extend Cache: Clone { fun clone(&self) -> Cache { … } }   // ok: not Copy; a custom duplicate is explicit-only
copy struct Both { n: i64 }
extend Both: Clone { … }                     // error T0015: overlaps the Clone that Copy brings
struct Dup derives Clone, Copy { n: i64 }
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
- **RFC-0206** — `Copy: derived Clone, !Drop`.
- **RFC-0089** — the lattice whose exclusions (`Copy` with `Drop`, `Copy` with `Linear`) this relation expresses.
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

8. **Per-field customisation of a derive.** `derives Clone` with one field's behaviour overridden
   (`derives Clone { hits = reset }`) would keep the template, and so projections, while changing one
   field. It is the lighter alternative to a written row-generic impl (RFC-0214, RFC-0216) for the
   common case; whether it is worth a clause form is open (RFC-0207).
9. **Opening `derived` to user aspects.** Only std aspects may carry the mark in v0.16.0. Reopen it when a real
   user aspect needs its derivation to generate a super-aspect and writing both impls by hand is a demonstrated
   cost; the compatibility rules of this section (the mark is part of the aspect's contract) then apply to that
   aspect's author.

---

## Decision

**Outcome:** *(pending)*
