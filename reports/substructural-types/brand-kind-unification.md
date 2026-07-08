---
id: brand-kind-unification
title: "Unifying the Identity Kinds: Allocator Tags, Lifetime Anchors, and Brands"
type: report
status: active
last_synced_against_model: '2026-07-07'
supersedes: null
revives: null
---

# Unifying the Identity Kinds: Allocator Tags, Lifetime Anchors, and Brands

*Living document — updated in place, not a point-in-time snapshot.*

*Exploration, not a decision. Nothing here is ratified. This document proposes that
`@a` (allocator tags, RFC-0063), `&r` (lifetime anchors, RFC-0067), and `'c` (brands,
RFC-0076) are three sigil-distinguished roles of a **single underlying kind**, and that
making this deliberate — rather than leaving it as a recurring coincidence — answers
RFC-0076's open question Q2 ("brand kind vs. lifetime kind"). Read `brand-types.md`
first: this is its direct continuation, and `brand-types.md` §4 (why regions don't need
explicit brands) is the observation this document generalizes. The background model is
`../memory-model/lifetimes-vs-regions-2026-07-02.md` (the allocator/lifetime split);
every claim here assumes it.*

---

## 1. The thesis, and where the language already commits to it

The proposal is one sentence: **`@a`, `&r`, and `'c` name the same kind of thing — a
rigid, erased, per-instance compile-time identity — and the sigil is a semantic role
selector, not three unrelated syntaxes that happen to look alike.**

This is not speculative. The design already does exactly this in one place, without
having named it. RFC-0063 §6:

```metel
struct Parser<&a> {
    input: @a String,   // `a` in the storage role
    pos:   u64,
}
```

> The `&a` anchor and the `@a` allocator parameter use the same name — the binding `a`
> is both the runtime allocator and the compile-time lifetime anchor bounding the
> struct's validity.

One identity `a`, worn simultaneously as `@a` (storage role) and `&a` (borrow-anchor
role). The two sigils are two views of one binding. This document's contribution is to
(a) recognize this as an instance of a general pattern, (b) fold the third member —
`'c` brands proper — into the same story, and (c) promote the coincidence to a stated
principle so a future fourth member of the family inherits the rules instead of
re-litigating them.

The motivation for making it deliberate is the same failure mode this directory's
`README.md` was built to prevent: the tag-only allocator parameter `<@a>` (RFC-0063 §4)
was designed as "a compile-time-only name, erased at runtime, with no paired value
parameter and no `Alloc` bound" — which is a brand in every respect — *without anyone
noticing it is a brand*. Three names for one mechanism, re-derived independently, is
exactly what a stated principle prevents.

---

## 2. The one kind: rigid, fresh, erased, binding-anchored identity

All three roles already share the full set of core properties. They are not merely
similar; in one case (non-escape) one is already *specified in terms of* another.

- **Rigidity** — two distinct introduction sites never unify. `'b ≠ 'c` (RFC-0076
  §Brand rigidity); two `BumpAlloc` bindings have distinct tags (RFC-0063 §2,
  "instance-level vs. type-level tags"); two named anchors `&s`, `&t` are never silently
  merged (RFC-0067 §2).
- **Freshness** — each introduction site is distinct from every other.
- **Erasure** — no runtime representation; the identity is a compile-time property used
  for checking and optimization only. (For `@a` this is true of the *tag*; the
  accompanying allocator *handle* is a separate axis — see §4.)
- **Binding-anchored in the common case** — the name is a real variable in scope. This
  is what preserves the "concrete errors" property: diagnostics say *"value outlives
  `a`"* pointing at a binding, never an abstract `'a` the programmer never wrote
  (`../memory-model/memory-model-overview.md` §Design philosophy;
  `../memory-model/lifetimes-vs-regions-2026-07-02.md` §4).
- **Scoped non-escape** — a value carrying the identity cannot outlive the scope that
  introduced it. Here the roles are not just parallel: RFC-0076 §Brand rigidity defines
  brand non-escape *by delegating to the lifetime mechanism* — "enforced by the existing
  lifetime rules: the brand's scope is the block." One role is already a special case of
  another.

**Inference and elision are the same operation.** Brand inference (`a.clone()` infers
the same brand as `a`, RFC-0076 §Brand inference) and anchor elision (an elided output
anchor becomes the sole input anchor, RFC-0065 §2 / RFC-0067 §2) both do one thing:
infer an *unwritten* identity from context, while never merging two *distinct written*
identities. The property that looked like it might separate anchors from brands —
"anchors get unified, brands don't" — dissolves on inspection: neither ever merges two
distinct written names, and both freely infer an unwritten one. The dissolution is
itself evidence for the unification.

---

## 3. The sigil is a semantic role selector, not decoration

Calling the sigils "purpose-clarifying" undersells what they do. Each sigil does two
load-bearing jobs on top of bare identity, and getting either wrong should be a type
error — which is what makes the sigils *the roles* rather than annotations on the roles.

**Job 1 — the sigil selects the relation algebra available on that name.** Bare
distinctness (`=` / `≠`) is the floor every role has; each role adds structure:

| Sigil | Role | Relations beyond `=` | Source |
|---|---|---|---|
| `'c` | bare identity (Rc cell, capability token, typestate instance) | none — distinctness only | RFC-0076 |
| `@a` | storage tag | scope-**nesting** (wellformedness: `b` encloses `a`) | RFC-0077 §3 |
| `&r` | borrow anchor | **outlives** ordering (`&t: &s`) | RFC-0067 §2 |

A bare brand supports only "same or different." A storage tag additionally participates
in a nesting relation (used for `@a @b T` wellformedness). A borrow anchor additionally
participates in a full outlives lattice. The base kind is therefore *maximally rigid*
(equality only); each role *relaxes* it by adding a compatible ordering — the role adds
structure, it never removes rigidity.

**Job 2 — the sigil interprets "distinctness" into a domain.** Two distinct names mean
different things per role:

| `x ≠ y` under sigil | Means |
|---|---|
| `'b ≠ 'c` | **logical** non-identity — two Rc brands could even be the same heap address; the brand tracks logical identity, not physical |
| `@b ≠ @c` | **physical** non-aliasing — the disjointness witness (RFC-0063 §2) |
| `&s ≠ &t` | **distinct borrow scopes** — no derivable outlives relation |

Same structural relation (distinctness), three interpretations. Disjointness, in
particular, is not a separate primitive — it is `@`-role distinctness *interpreted as
memory non-aliasing*. This is why removing or swapping a sigil cannot be a no-op: it
changes both which relations typecheck and what distinctness means.

---

## 4. The orthogonal axis that must stay separate: value vs. erased

The unification must not swallow one genuine distinction: **whether the identity is
accompanied by a runtime value.** `@a` in the declaration `(@a: BumpAlloc)` carries a
runtime handle you allocate through (`@a expr` desugars to `a.alloc(expr)`, RFC-0063
§3); `&r`, `'c`, and the tag-only `<@a>` carry nothing. Brands are erased and *cannot*
allocate — this is precisely why `Rc`/`Arc` need explicit brands (no handle) while
scoped allocators do not (the handle is the brand), `brand-types.md` §4.

This has-value distinction is what the parameter *channel* already encodes, and it is
**orthogonal** to the role sigil. Two independent annotations:

- **sigil** = which role (storage `@` / borrow `&` / bare identity `'`)
- **channel** = whether a runtime value accompanies the identity (`()` value channel vs.
  `<>` type channel)

| Form | Sigil / role | Channel | Runtime value? |
|---|---|---|---|
| `(@a: BumpAlloc)` | `@` storage | `()` value | Yes — the allocator handle |
| `<@a>` | `@` storage | `<>` type | No — tag only (RFC-0063 §4) |
| `<&r>` | `&` borrow | `<>` type | No |
| `brand 'c` | `'` identity | `<>` type | No (optionally a zero-size `PhantomBrand<'c>`) |

The failure mode to avoid is collapsing these two axes and concluding "`@` sometimes has
a value and sometimes doesn't." It always plays the same role; the *channel* is what says
whether a handle rides along. Keeping the axes separate is what lets the value-carrying
allocator handle stay firmly outside the brand unification — the handle can never be a
brand (brands are erased; allocation needs a value), but the *tag* the handle casts is a
brand like any other.

---

## 5. What the unification resolves

- **RFC-0076 Q2 ("brand kind vs. lifetime kind")** — answered directly: **same kind,
  sigil-distinguished.** Not "share a syntactic kind by coincidence," but "one kind, with
  the sigil selecting role."
- **RFC-0076 Q1 (brand introduction mechanism) — reframed, not left open in a vacuum.**
  Q1 asks whether fresh brands come from rank-2 quantification (`brand { }`,
  `forall<brand 'b>`) or "a simpler rule (each binding of a brand-parameterised type gets
  a fresh brand)." The unification supplies the answer from the allocator/anchor side,
  where that simpler rule is *already how it works*: **binding-fresh is the default**;
  the rank-2 `brand { }` block is the escape hatch for the one case with no binding to
  anchor (anonymous Rc-cell identity, two arenas minted inside a generic function). The
  allocator and anchor worlds are the existence proof that binding-fresh introduction is
  sufficient for the common case.
- **`<@a>` (RFC-0063 §4) is retro-explained** as precisely a storage-role brand with no
  accompanying value — the `@`-sigil counterpart of a bare `'c`. It stops being a bespoke
  allocator feature and becomes one cell of a 2×N table (§4).
- **Variance becomes per-role, not per-type.** RFC-0077 §4 specifies variance separately
  for `@a T`, `&r T`, `&r mut T`. Under the unification, covariance-in-the-tag falls out
  of the role's relation algebra (nesting for `@`, outlives for `&`) rather than being
  restated for each type former.

---

## 6. The real cost: separate kinds give role-incompatibility for free

The honest counterargument, stated at full strength: **three separate kinds make
role-crossing impossible by construction.** Using a `&r` where a `'c` is expected is a
kind mismatch the elaborator rejects mechanically, with no extra rule. Unify the kinds
and that safety has to be *re-imposed* through the sigil check — the unified elaborator
must actively forbid `x ≠ y` interpretations from leaking across roles, where separate
kinds forbade it for free.

Two things make this cost acceptable rather than decisive:

1. **Controlled role-crossing is wanted, and the design already relies on it.** RFC-0063
   §6's `a`-as-both-`@a`-and-`&a` is a deliberate, useful crossing — the allocator's
   identity *reused* as its contents' borrow anchor. Three separate kinds would forbid
   this or force a conversion bridge between them. The sigil check is therefore not a tax
   paid to recover safety separateness gave for free; it is the mechanism that makes
   *intentional* crossings expressible while keeping accidental ones illegal. Separate
   kinds can't express the crossing at all.

2. **Prior art shows the shared kind is workable, and that the missing piece is exactly
   the sigil.** Haskell's `runST :: (forall s. ST s a) -> a` uses a single rank-2 rigid
   type variable `s` as a state-thread identity — a brand in a "region" role, with no
   separate brand kind (cited in RFC-0076 §References). Cyclone's region variables `'r`
   and Rust's lifetimes `'a` are the *same syntactic kind* serving region-vs-borrow roles
   in different languages. Most pointedly, **GhostCell** (Yanovski et al. 2021, cited in
   RFC-0076) repurposes a Rust *lifetime* as a brand — because Rust has no brand kind, the
   brand role is implemented *by* the lifetime kind. That trick is notoriously subtle
   precisely because the lifetime is secretly doing identity, not liveness, with nothing
   in the syntax saying so. Metel's sigil distinction is exactly what would make
   GhostCell's implicit role-punning explicit and legible: same kind underneath, but the
   role is named and checked.

The counterargument is real and belongs on the record; it is not fatal.

---

## 7. Recommendation

**Adopt the unification at the mechanism / metatheory level**, and write it up as the
RFC-0076 Q2 answer: one kind (rigid, erased, binding-anchored identity), three
sigil-selected roles that each pick a relation algebra (§3, Job 1) and a distinctness
interpretation (§3, Job 2), plus an orthogonal has-value axis (§4) that keeps the
value-carrying allocator handle outside the unification.

**Do not surface "it's all one kind" as a user-facing concept.** The win is implementer
economy — one freshness / erasure / rigidity / non-escape checker instead of three — and
a predictable surface grammar (`@` storage, `&` borrow, `'` identity). Users should keep
thinking in three concepts; the unification is what lets *the compiler* think in one, and
what guarantees a future member of this family inherits all the rules for free. Pitched as
"there is really only one thing," it would read as metatheory imperialism leaking into
ergonomics; pitched as "three roles of one mechanism," it is an economy the user never has
to see.

Two pieces need genuine design work before this is real, and neither is a syntax detail:

- **Formalize the per-role relation algebra** so `@` provably adds nesting and `&`
  provably adds outlives on top of a common equality core — rather than each being
  hand-specified per type former as RFC-0077 §4 does today.
- **Keep the value/no-value axis (§4) formally distinct from the role axis.** If the two
  ever blur, `@` reads as "sometimes valued," which is exactly the confusion the tag-only
  `<@a>` form already had to be introduced to dispel.

Nothing here has a deadline. Unlike RFC-0063 §9 item 5 (partial consumption, which gates
Phase 3 implementation), this is a *consolidation* of already-shipped-in-spirit
mechanisms; it changes how they are explained and checked, not what any of them do
individually. It should be pursued when the brand cluster (RFC-0076) is next opened, as
its Q2 answer, not on its own clock.

---

## Open questions

1. **Kind unification vs. deliberate separateness (§6)** — the central decision. Leaning
   toward unification-at-the-mechanism-level with the three sigils preserved at the
   surface, for the reasons in §6–§7, but the role-incompatibility-for-free argument for
   keeping them separate is real and not yet weighed by anyone but this document.
2. **The per-role relation algebra (§3, §7)** — a common equality core plus role-added
   nesting (`@`) and outlives (`&`) is asserted to be formalizable, but no actual
   judgement/lattice is written down. Until it is, the sigil-as-selector claim is a
   sketch.
3. **Which role-crossings are legal (§6)** — RFC-0063 §6's `@a`↔`&a` crossing is
   clearly wanted. Is `'c`↔`@a` (a bare brand promoted to a storage tag) ever meaningful,
   or `'c`↔`&r` (a brand used as a borrow anchor)? No enumeration of the legal crossing
   matrix exists; §6 only establishes that *some* crossing must be expressible.
4. **Cross-module identity (`brand-types.md` §6 item 5 / RFC-0076 Q5)** — the equality/
   visibility rule for an opaque identity returned from a library function is needed by
   *every* role (an opaque `@a T` return has the same question as an opaque `Rc<T, 'b>`).
   Whether one rule serves all three roles, or each needs its own visibility treatment,
   is unresolved — and is a reason the unification matters practically, not just
   aesthetically: solve it once, not three times.
5. **Whether this is written up standalone or folded into the RFC-0076 Q2 resolution
   directly** — a project-planning question. This document argues it is the Q2 answer;
   whether it lands as an amendment to RFC-0076, a new RFC, or stays exploratory until
   the brand cluster is next opened is not decided here.
6. **A candidate fourth surface use, and a new nesting question it raises (added
   2026-07-07, from `structural-records.md` §9).** That document proposes ordinary
   struct/enum nominal identity as another surface use of the `'c` role — not a new
   kind, per this document's own recommendation (§7) to keep the unification at the
   mechanism level. That immediately raises a crossing case item 3 didn't anticipate:
   `@a T` where `T` itself now carries an identity brand is a *storage* brand wrapping a
   value whose own type carries an *identity* brand — composition of the same kind at
   two levels, not obviously a "crossing" in item 3's sense at all, but not yet
   distinguished from one either. Whether nesting needs its own rule, or falls out of
   §3's per-role relation algebra once that's formalized, is open. (Narrowed
   2026-07-08, `structural-records.md` §10: this surface use, and the nesting question
   it raises, only arise for the opt-in *named record* kind — an ordinary `struct`
   never carries this identity tag at all, so the nesting question is scoped to
   `@a T` where `T` is specifically a named record, not any struct.)

---

## Example — one identity, three sigils

Illustrative only — see `README.md`'s status note on the whole directory. The point is
that `a` below is a *single* identity appearing in all three roles, distinguished only by
sigil, exactly as RFC-0063 §6 already permits for the first two.

```metel
// `a` introduced once, as a value-carrying storage identity (has a handle):
fun build<'c>(@a: BumpAlloc, seed: Rc<Node, 'c>) -> Parser<&a> {
    //         ^^ @  = storage role, value channel: `a` is the allocator handle
    //                                       'c = bare-identity role: seed's cell brand

    let input: @a String = @a seed.describe();   // @a  — allocate into a's arena
    let view:  &a String = &input;               // &a  — borrow anchored to a's scope
    //         ^^ same `a`, borrow-anchor role, no value: the tag's shadow

    Parser { input, pos: 0 }
    // Parser<&a>: the struct's validity is bounded by `a` — storage identity reused
    // as the returned struct's lifetime anchor (RFC-0063 §6, already legal today).
}

// A pure relay needs the storage identity but no handle — the tag-only form,
// i.e. an @-role brand with no accompanying value (RFC-0063 §4 / §4 above):
fun forward<@a>(val: @a Node) -> @a Node { val }
```

Reading the sigils as one kind: `a` is a rigid erased identity; `@a` asks for its
storage/disjointness interpretation *and* (in the value channel) its handle; `&a` asks
for its borrow-scope interpretation and no handle; a bare `'c` would ask for its logical
distinctness alone. Three questions, one name.
