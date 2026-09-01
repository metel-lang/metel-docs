---
id: rfc-0159
title: "Abstract Regions and a Dedicated Identity Channel"
date: '2026-09-01'
status: under-review
target:
updated: '2026-09-01'
tracking: 'https://github.com/metel-lang/metel-core/issues/920'
---

> **Promoted from the internal exploration `reports/substructural-types/abstract-regions-and-identity-channel.md`
> (metel-docs-internal), 2026-09-01.** That report is a living design study; this RFC is
> the tracked, reviewable form of the *direction* it proposes. It is **direction-setting,
> not a syntax proposal** — every concrete grammar in it is a candidate, and §"Syntax is
> deferred" records why the obvious delimiter (`[]`) is unavailable. Nothing here changes
> RFC-0067, RFC-0076, RFC-0121, RFC-0137, or RFC-0143 on acceptance; it commits the
> project to a **cross-RFC prototype** (§10) whose §"Gates" must pass before any of those
> RFCs is rewritten against this model.

> **Status — under review (2026-09-01).** promoted from internal exploration; direction-setting cross-RFC RFC with acceptance gates

## Summary

Metel's angle-bracket parameter channel is accumulating semantically distinct forms — an
ordinary type `<T>`, a record-kinded type `<record T>`, a row `<row R>`, a pack `<..Ts>`,
a lifetime anchor `<&r>` (RFC-0067), a fresh rigid identity `<brand 'b>` (RFC-0076), and,
in RFC-0143's current draft, a storage identity `<storage s>`. One visually uniform list
now asks the reader to hold several different declaration, inference, substitution,
variance, freshness, and escape rules at once.

This RFC proposes a direction that reduces the *semantic* taxonomy rather than just
moving the load to a new delimiter:

1. **Abstract lifetime regions.** Replace RFC-0067's binding-specific anchors (a lifetime
   name *is* a real outer binding) with abstract regions chosen at the call site — the
   signature states a relationship, not a reference to the callee's lexical names.
2. **One region-index substrate.** Lifetimes, brands, and storage identities become
   *roles* over a single `RegionIndex` mechanism: shared machinery (erased names, binding
   and substitution, non-escape checking, fresh-existential introduction, equality
   constraints, variance metadata, origin diagnostics), **distinct** capability and
   relation algebras (a lifetime may be shortened and unified; a brand is rigid and
   generative; a storage identity is rigid and carries a validity extent).
3. **A dedicated channel.** `<>` answers *"what type or shape?"*; a separate non-type
   channel answers *"which identity or validity region?"*; the use position (`&r T`,
   `T@r`, a branded nominal type) says which role the index plays.

**Syntax is out of scope here.** The report writes region parameters `[r]` provisionally;
this RFC does **not** reserve `[]` — it collides with RFC-0050 closure capture lists and
with postfix `T[]` arrays. Delimiter choice follows the semantic model, not the reverse.

---

## Motivation

### The angle channel is overloaded

`<T>`, `<record T>`, `<row R>`, `<..Ts>`, `<&r>`, `<brand 'b>`, `<storage s>` all share
one bracket pair and one comma-separated list. Some of that is presentational — a
record-kinded type is still a type, a pack and a row are both shape-like — but the
lifetime, brand, and storage forms genuinely differ from types in how they are declared,
inferred, substituted, ordered, kept fresh, and prevented from escaping. Teaching
"generics" as one thing is already dishonest, and RFC-0143 adds a third identity-like
kind to the same list.

### A different delimiter alone buys nothing

Splitting `<>` in two only helps if the split *exposes a smaller taxonomy*. The
hypothesis under test: **types and shapes** (one question — *what representation?*) versus
**region indices** (one question — *which identity or validity region?*). If lifetimes,
brands, and storage identities are coherent instances of one non-type index mechanism,
the split is a real simplification; if programmers must routinely spell out which
sub-kind they mean, it is just a second heterogeneous list.

### Abstract lifetimes are the enabling change

RFC-0067's binding-specific anchor —

```metel
fun first<&items, T>(items: &items List<T>) -> &items T
```

— keeps diagnostics concrete but ties every lifetime relationship to a manufactured
lexical binding. The counterfactual:

```metel
fun first[r]<T>(items: &r List<T>) -> &r T
```

`r` is an abstract region the caller supplies. For multiple inputs it becomes essential:

```metel
fun choose[r]<T>(condition: Bool, x: &r T, y: &r T) -> &r T
```

This need not force `x` and `y` to carry the *same* concrete lifetime — a region inference
engine may pick a region contained in both. So `r` is flexible and ordered (it can be
shortened) — already a signal that an abstract lifetime is not the same semantic object
as a rigid brand. Abstract lifetimes buy compositionality (function types, closures,
aspect methods, higher-order combinators quantify over relationships without a lexical
binding per relationship); they cost a stronger constraint solver, more variance rules,
higher-ranked quantification, and less immediately concrete errors.

---

## The substrate: one mechanism, three roles

The viable unification is **not** "lifetimes, brands, and storage are interchangeable."
It is that they share a region-index substrate and differ in capability:

| Role | Equality | Ordering | Freshness / rigidity | Extra meaning |
|---|---|---|---|---|
| **Lifetime** region | may be unified by constraints | may be shortened; participates in `outlives` | normally flexible | set / interval of valid program points |
| **Brand** region | equality only | lexical non-escape; no ordinary shortening | fresh and rigid | nominal provenance / instance identity |
| **Storage** region | rigid instance equality | has a validity extent | fresh per allocator instance | allocator capability + selected handle family |

**Shared:** erased compile-time names; parameter binding and substitution; scope /
non-escape checking; fresh existential introduction; equality constraints; variance
metadata; diagnostics that expose an inferred origin.

**Must not be shared:**
- two lifetime variables may acquire a common *shorter* solution; two distinct brands
  must never unify merely because their scopes overlap;
- two storage identities stay distinct even when their allocators have the same
  implementation type;
- only a storage-capable region may select `T@r`'s handle family; only a lifetime-capable
  region may qualify `&r T`; a brand used as an invariant token must not inherit lifetime
  covariance.

The compiler may implement this as one indexed mechanism with role capabilities. The
surface documentation still teaches borrowing, branding, and placement as separate
operations — mechanism unification is useful; pretending the operations are identical is
not.

### Ordering is not identity equality

Abstract lifetimes need a direct way to state ordering (keyword form illustrative):

```metel
fun shorten[long, short]<T>(value: &long T) -> &short T
where long outlives short
```

This ordering **must not** leak into brand or storage equality: distinct rigid brands
`b1`/`b2` never make `Rc[b1]<T>` and `Rc[b2]<T>` interchangeable, and `Node@s1` /
`Node@s2` stay distinct even if `s1 outlives s2` or both use `BumpAlloc`. Storage
*validity* may still depend on lifetime ordering (a handle cannot outlive the allocator
capability it depends on), so the model carries **two axes**: *which region is this?*
(rigid equality for storage and brands) and *for how long is it usable?* (an extent
constraint). This preserves the allocator/lifetime split's central correction — a value's
lifetime may end before its backing allocator's — and must not recreate the rejected
claim that allocator identity *is* value lifetime.

---

## Syntax is deferred

For exploration the report writes region-index parameters `[r]` and type/shape
parameters `<>`:

```metel
fun first[r]<T>(items: &r List<T>) -> &r T
fun same[s](x: Node@s, y: Node@s) -> Node@s
struct Rc[b]<T> { … }
forall[b] fun(BrandToken[b]) -> R          // higher-ranked introduction
```

**`[]` is not available.** The 2026-07 allocator/lifetime split deliberately freed it for
RFC-0050 closure capture lists, and Metel already uses postfix `T[]` for arrays. Even
where a declaration-header index list is grammatically distinguishable, the same visual
channel would mean capture set, array type, or region arguments by position.

This RFC therefore does **not** reserve `[]`. Candidate channels, to be chosen only after
the semantic model settles:

- a different dedicated delimiter;
- a visibly partitioned generic list — `<T; r>`;
- a declaration clause — `where identity r` / `where lifetime r` / `where storage s`;
- implicit region binders, with explicit syntax limited to higher-ranked cases;
- contextual reuse of `[]` **only** if worked examples show it stays readable next to
  capture lists and array types.

RFC-0050's Resolved Question 4 is updated in parallel to record this contention.

---

## Introduction sites and inference

- **Borrow elision unchanged.** `fun head<T>(items: &List<T>) -> &T` still works: each
  elided input introduces a region, one input propagates to the output, a receiver wins
  for methods, ambiguity forces an explicit relationship. The inferred entities are
  abstract regions, not aliases for source binding names.
- **Allocator bindings introduce a rigid storage region automatically.** `fun make<A:
  Alloc>(arena: A, value: Node) -> Node@arena` needs no `[arena]` binder; `arena` is both
  the runtime capability and shorthand for its storage region. RFC-0143's `T@_` preserves
  one unknown storage region with no binder. Only APIs relating *several* abstract storage
  positions need an explicit index (`fun same[s](x: Node@s, y: Node@s) -> Node@s`).
- **Brand / region introduction creates a fresh rigid index** (`region b { … }` — keyword
  open). Higher-ranked introduction must have a form (`forall[b] fun(BrandToken[b]) ->
  R`); a channel that is elegant first-order but incoherent under `forall` is incomplete.

---

## Relationship to existing RFCs

- **RFC-0067 (Lifetime Anchors, `1-under-review`)** — this RFC **contradicts its
  binding-specific premise**, not only its spelling. Adopting the direction requires a
  replacement or substantial rewrite covering abstract-region inference, subtyping,
  variance, higher ranks, existential escape, and diagnostics. RFC-0067a's implemented
  reference-type core (`4-implemented`) is untouched — the change is the explicit-lifetime
  layer above it.
- **RFC-0076 (Brand Types, `1-under-review`)** — its open brand-kind question gains a
  candidate answer: brands and lifetimes share a substrate and channel but **not**
  flexibility or variance. This narrows `brand-kind-unification.md`'s stronger
  "one rigid, binding-anchored kind" thesis — abstract lifetime regions are neither
  necessarily rigid nor binding-anchored.
- **RFC-0143 (Allocator Placement / Storage Identity, `1-under-review`)** — it need not
  introduce `<storage s>` as another `<>` kind: an allocator binding supplies its own
  storage region, `T@_` covers the identity-preserving common case, and rare relational
  APIs use the general index channel. `T@a`, `place expr`, and handle families stay
  allocator-specific. This is a reduction *only if* the region system already exists for
  lifetimes and brands; RFC-0143 stays a concrete acceptance test, not a dependant of an
  unconstrained universal identity theory.
- **RFC-0121 (Open Rows, `1-under-review`) / RFC-0118** — rows stay structural shape
  parameters in `<>`; `record T` / `row R` are not region indices. Moving identity out of
  `<>` keeps the real record/row distinction while removing three identity-like categories
  from its list.
- **RFC-0137 (Nominal Types as Branded Rows, `3-integrated`)** — the direct mixed case: a
  branded nominal identity plus a structural row. A separate index channel makes that
  product visible instead of two adjacent generic arguments; it is also the key
  readability test for the ordering of the two channels.
- **RFC-0050 (Closure Capture Lists, `1-under-review`, v0.13.0)** — holds `[]`. This RFC
  does not contest it; RFC-0050 RQ4 is updated to note this exploration exists and that
  the identity channel will take a delimiter other than `[]` (or prove contextual reuse).

---

## Options, including doing nothing

- **A — keep binding-specific anchors and the current `<>` channel.** Concrete
  diagnostics, least ambitious checker, small ordinary code via elision. Cost: a
  heterogeneous generic channel and weak composition for higher-order lifetime
  relationships.
- **B — abstract lifetimes, all binders still in `<>`.** Gains compositional lifetimes,
  spends no delimiter, but does nothing for teachability — types, shapes, flexible
  lifetimes, rigid brands, storage identities stay visually adjacent.
- **C — abstract lifetimes + a dedicated region-index channel.** The main proposal.
  Strongest taxonomy, cleanest structural-vs-identity split; commits to two parameter
  lists and to solving the delimiter problem.
- **D — a declaration clause, not an argument delimiter.** `fun same(x: Node@s, y: Node@s)
  -> Node@s where identity s`. Progressive disclosure, no new delimiter; weaker for
  nominal types whose explicit identity argument must sometimes appear at a type
  application, and for higher-ranked forms. May complement C rather than replace it.

---

## Gates — what must pass before any normative RFC is rewritten

A small checker model or a detailed worked-example suite must answer all of:

1. **Single-input propagation** — `&T -> &T` infers one abstract region, no source binders.
2. **Receiver propagation** — an elided method result uses the receiver region.
3. **Common-region choice** — `choose(x, y)` computes a sound common *shorter* region, not
   identical input origins.
4. **Ordering** — a returned `&short T` is accepted only when the `outlives` relation is
   provable.
5. **Higher ranks** — `forall[r]` prevents a region-indexed value escaping.
6. **Brand rigidity** — two fresh `Rc` brands never unify through lifetime shortening.
7. **Storage rigidity** — two `BumpAlloc` values of the same type produce distinct `Node@s`.
8. **Mixed extent and identity** — a storage handle borrowed for less time than the
   storage exists keeps its rigid storage identity.
9. **Variance** — lifetime covariance cannot make an invariant brand or storage identity
   substitutable.
10. **Rows plus identity** — a branded-row example stays readable with both channels present.
11. **Inference visibility** — diagnostics/tooling can name an inferred region's origin and
    constraints without forcing it into source.
12. **Grammar pressure** — declarations, applications, arrays, indexing, and closure
    captures stay unambiguous under whichever delimiter is chosen.

The decisive failure is **not** "the prototype needs several internal region classes" —
that is expected. It is programmers having to state those classes explicitly by routine,
or one class's inference rules making another unsound or unpredictable. Either invalidates
the "one dedicated channel simplifies the language" claim.

---

## Recommendation

Pursue this as a **cross-RFC prototype**, not as an amendment to any single RFC. The
prototype uses a neutral internal `RegionIndex` representation with explicit capabilities
(lifetime ordering, rigid identity, storage selection), runs the Gates, and *then* picks a
delimiter.

If the Gates pass: replace binding-specific anchors with abstract lifetime regions;
reserve one non-`<>` channel for region/identity indices; keep `<>` for types and shapes;
lower brands and storage identities onto rigid region-index instances; infer and elide the
channel in common code; keep role-specific type syntax (`&r T`, `T@r`, branded nominal
types) rather than exposing a universal region calculus everywhere.

If they fail: keep the concepts separate and address the `<>` overload through elision and
declaration clauses. A failed semantic unification is evidence against a dedicated
channel — not a reason to keep the punctuation while multiplying explicit kind markers
inside it.

---

## Open Questions

1. Are lifetime regions sets of program points, lexical intervals, or another ordered
   object in Metel's checker model?
2. Does one region index carry a *set of capabilities*, or are lifetime / brand / storage
   distinct kinds sharing only implementation infrastructure?
3. Can a storage region serve directly as a lifetime upper bound while staying distinct
   from the shorter lifetime of an individual allocated value?
4. Should explicit region arguments ever appear at ordinary call sites, or only in type
   signatures and higher-ranked forms?
5. **The delimiter** — what notation carries a dedicated region-index channel without
   conflicting with arrays (`T[]`), indexing, closure captures (RFC-0050), metadata `@`,
   and record syntax? (`<T; r>`, `where identity r`, a new delimiter, or contextual `[]`.)
6. Does `Rc[b]<T>` put identity before type because it is semantically prior, or does a
   final syntax need a less disruptive ordering?
7. Can role inference from `&r`, `T@r`, and branded type slots produce precise errors, or
   must declarations say `lifetime` / `storage` / `brand` explicitly?
8. Is the general introduction form named `region`, `identity`, or kept role-specific
   (`brand`, allocator binding, inferred borrow)?
9. How are anonymous / existential region indices represented in public API types and
   diagnostics?
10. What is the minimal prototype that can falsify the shared-channel claim before any
    normative RFC is rewritten?

---

## References

- `reports/substructural-types/abstract-regions-and-identity-channel.md` (metel-docs-internal)
  — the living exploration this RFC promotes; source of the substrate table, the Gates,
  and the Open Questions.
- `reports/substructural-types/brand-kind-unification.md` — the earlier
  one-rigid-binding-kind thesis this direction narrows and re-tests under abstract
  lifetimes.
- `reports/memory-model/lifetimes-vs-regions-2026-07-02.md` — the allocator/lifetime split
  and the binding-specific-anchor decision this challenges; also where `[]` was freed for
  capture lists.
- **RFC-0067 (Lifetime Anchors), `1-under-review`** — the binding-specific premise this
  contradicts; a rewrite target if the Gates pass.
- **RFC-0067a (Reference Types), `4-implemented`** — the reference-type core, untouched.
- **RFC-0076 (Brand Types), `1-under-review`** — brand-kind question gets a candidate
  answer here.
- **RFC-0143 (Allocator Placement, Storage Identity…), `1-under-review`** — may drop
  `<storage s>` as a separate `<>` kind; stays a concrete acceptance test.
- **RFC-0121 (Open Rows), `1-under-review`** / **RFC-0137 (Nominal Types as Branded Rows),
  `3-integrated`** — rows stay in `<>`; RFC-0137 is the mixed structural + identity
  readability test.
- **RFC-0050 (Closure Capture Lists), `1-under-review`** — holds `[]`; RQ4 updated in
  parallel.

---

## Decision

**Outcome:** *(pending)*
**Target:** *(set when accepted)*
