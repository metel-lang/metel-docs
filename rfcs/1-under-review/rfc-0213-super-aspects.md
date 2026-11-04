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
aspect ImplicitClone: derived Clone;          // sketch: the derivation of ImplicitClone derives Clone
```

The relation `A: B` is nominal and transitive: a proof of `T: A` also proves `T: B`; an
implementation of `A` requires a coherent `B` for the same type; negative implementations stay
local. A super-aspect entry may be marked `derived`, which makes the derivation of the sub-aspect
also derive the super-aspect when the type lacks it. Without the mark an entry only requires.

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
from the sub-aspect's impl unless the relation is marked `derived`.

## 3. Negative implementations

RFC-0081's negative impls stay direct assertions. Positive satisfaction is transitive, negative is
not:
- `T: A` implies `T: B`.
- `T: !B` makes `T: A` inconsistent, and is a coherence error.
- `T: !A` does not imply `T: !B`.

Any direct contradiction after super-aspect closure is a coherence error. Exclusions between aspects
(RFC-0212 section 3) are closed the same way.

## 4. Derivation through a `derived` relation

`aspect A: derived B` states that the derivation of `A` also derives `B` for a type that has no `B`:

1. `struct P derives A` derives `B` as well, exactly as `struct P derives A, B` would.
2. Derivation is idempotent per type and aspect: `derives A, B` is valid and derives `B` once.
3. A written `extend P: B` together with `derives A` overlaps the derived `B` and is an error
   (`T0015`); a type that wants to write its own `B` lists `A` in the colon list instead of `derives`.
4. `B` must have a derivation (RFC-0207), or the entry is an error at the aspect's declaration.
5. An unmarked entry (`Eq: PartialEq`) never derives: the type brings its own `PartialEq`, which may be
   custom.

This is what lets `derives ImplicitClone` mean `: ImplicitClone derives Clone` (RFC-0206) without a
rule specific to either aspect.

---

## 5. Worked examples

```metel
aspect PartialEq { fun eq(&self, other: &Self) -> boolean; }
aspect Eq: PartialEq;                        // requires only
struct Id { n: i64 }
extend Id: PartialEq { … }
extend Id: Eq;                               // ok: PartialEq exists
struct Bad { n: i64 }
extend Bad: Eq;                              // error: no PartialEq for Bad

aspect ImplicitClone: derived Clone;
struct Point derives ImplicitClone { x: i64 }          // derives Clone too
struct Cache: ImplicitClone { n: i64 }
extend Cache: Clone { fun clone(&self) -> Cache { … } }   // ok: the colon form takes the author's Clone
struct Both derives ImplicitClone { n: i64 }
extend Both: Clone { … }                     // error T0015: overlaps the derived Clone
```

## 6. Alternatives considered

- **No relation; a built-in entailment per aspect.** Rejected: an exception per aspect.
- **Aspect aliases as the relation.** Rejected by RFC-0168: an alias creates no implementation target.
- **Always derive super-aspects.** Rejected: `Eq` must be able to sit over a custom `PartialEq`.
- **A separate `provides` clause with a body** (an earlier draft of RFC-0206 and RFC-0207). Rejected:
  it needs a selection rule over overlapping impls and an equality law between two bodies.

## Relationship to existing RFCs

- **RFC-0168** — the equality model, which depends on this RFC.
- **RFC-0212** — properties of an aspect declaration; `implicit via` needs the relation.
- **RFC-0206** — `ImplicitClone: derived Clone`.
- **RFC-0207** — the `derives` clause and the derivations this rule builds on.
- **RFC-0081 / RFC-0060** — negative impls and coherence, extended by section 3.
- **RFC-0039** — aspect aliases, unchanged.

## Open questions

1. **The mark's spelling** (`derived`, as sketched, or another).
2. **`dyn` and object safety** for an aspect with super-aspects.
3. **Diamonds** (`A: B, C` with `B: D` and `C: D`): presumably one proof of `D`; to be specified.
4. **Associated items and default methods** of a super-aspect, and whether a sub-aspect may override
   a default.
5. **Generic aspects** (`aspect A<T>: B<T>`).
6. **Where the abstract analysis consults the relation,** and how it composes with assumption sets.

---

## Decision

**Outcome:** *(pending)*
