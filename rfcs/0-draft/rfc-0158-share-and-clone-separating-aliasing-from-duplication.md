---
id: rfc-0158
title: "Share and Clone: Separating Aliasing from Duplication"
date: '2026-08-31'
status: draft
target:
---

> **Split out of RFC-0157 (Copy and Clone Model Re-analysis), 2026-08-31.** RFC-0157's
> Axis B has two cuts: by *cost* (cheap `Copy` vs expensive `Clone`) and by *meaning*
> (produce an independent value vs. produce another handle to shared state). The
> cost cut is RFC-0157's subject. The meaning cut is this RFC's — it is orthogonal to
> the implicit-copy question, has its own concrete beneficiary (`Rc`/`Arc` legibility),
> and can be adopted on its own, so it is tracked separately at the reviewer's
> suggestion.

## Summary

`.clone()` in Metel means two different things depending on the receiver:

- `vec.clone()` — allocate a new backing buffer and deep-copy; the result is an
  **independent** value, no aliasing created.
- `rc.clone()` — increment a reference count and return another `Rc` to the **same
  cell** (RFC-0076: brand-preserving — the result carries the input's brand). Aliasing
  *is* the point.

Both go through one `Clone` aspect (RFC-0080) with identical spelling. RFC-0080's own
text is already inconsistent about which of the two `Clone` is: §1.1 says `.clone()`
"produces a new **independent** owned value," §1.2 lists "incrementing a reference
count" as a valid `Clone` impl. The brand system (RFC-0076) tracks the aliasing
relationship precisely *in the types*; the surface syntax gives the reader nothing.

This RFC splits `Clone` into two aspects:

- **`Dup`** — `fun dup(self: &Self) -> Self`, an independent owned value. This is what
  RFC-0080 §1.1 describes.
- **`Share`** — `fun share(self: &Self) -> Self`, another handle to the same underlying
  state; the result aliases `self`. Implemented only by handle-category types (`Rc`,
  `Arc`, and future ones), never blanket-derived, never implied by `Copy`.

At a call site, `x.dup()` says "no new aliasing" and `h.share()` says "aliasing now
exists" — the fact RFC-0076's brands encode in the type, made visible in the code.

---

## Motivation

**The conflation is a real legibility cost.** Reading `let b := a.clone();` tells you
nothing about whether `b` and `a` now share mutable state. For an `Rc` they do; for a
`Vec` they don't; the line looks the same. In code that mixes owned aggregates and
`Rc`-shared graph nodes — exactly the code `Rc` exists for — every `.clone()` is a small
puzzle. RFC-0076 built an entire brand system to answer "does this alias that" at the
type level; the surface syntax should not actively obscure the same question.

**The existing spec is self-contradictory.** RFC-0080 §1.1: "`.clone()` … produces a new
**independent** owned value." RFC-0080 §1.2: a `Clone` impl may be "incrementing a
reference count." An `Rc::clone` that increments a count and hands back a co-owner of the
same cell is not independent by any reading. One of the two statements has to give; this
RFC resolves it by saying §1.1 is the definition of `Dup`, and refcount-bump aliasing is
a different operation, `Share`.

**Prior art is converging here.** Rust's 2024–2026 ergonomic-ref-counting work
(RFC 3680 and successors) introduces a `Share`/`Claim`-style trait precisely to mark
"the kind of `.clone()` that produces an alias to the same underlying value," separate
from `Clone`-as-duplication (see RFC-0157's Prior art section). C++'s `shared_ptr` copy
constructor is the same operation under the same name-collision, and is a routine source
of "I didn't mean to extend that lifetime" bugs.

**It is cheap and orthogonal.** This split touches no rule about implicit copy, move
semantics, `Copy`/`Drop`, or closure capture. It is a rename-and-narrow of one stdlib
aspect. It can land before, after, or entirely independently of RFC-0157's larger
questions.

---

## Background: how duplication and sharing work today

Checked against RFC-0080 (`1-under-review`), RFC-0076 (`1-under-review`), RFC-0074
(`0-draft`):

- **`Clone`** (RFC-0080 §1): `aspect Clone { fun clone(self: &Self) -> Self; }`. Blanket
  `extend<T: Copy> T: Clone { fun clone(self: &T) -> T { *self } }`. Derivable
  (`#derive(Clone)`) for a struct/enum whose fields are all `Clone`; the derived impl
  clones each field. Region pointers `@[r] T` deliberately do **not** get a blanket
  `Clone` (§1.4) — a fresh region allocation must be explicit.
- **`Rc<T, 'b>` / `Arc<T, 'b>`** (RFC-0074, RFC-0076 §"Shared pointer alias analysis"):
  `clone` is specified as **brand-preserving** — `let b := a.clone();` gives `b` the same
  brand as `a`, i.e. the type system records that `b` aliases `a`'s cell. `Rc::new`
  produces a fresh brand. So `Rc::clone` is already, formally, the aliasing operation —
  it just shares the `Clone` name and aspect with `Vec::clone`.
- **`Copy`** (RFC-0080 §1.2): implies `Clone` via the bitwise blanket. A `Copy` value is
  trivially independent when duplicated — there is no shared backing to alias.

---

## Proposal

### 1. Two aspects

```metel
aspect Dup {
    fun dup(self: &Self) -> Self;      // independent owned value; no aliasing
}

aspect Share {
    fun share(self: &Self) -> Self;    // another handle to the same state; result aliases self
}
```

`Dup` is `Clone` renamed and given the meaning RFC-0080 §1.1 already states. Everything
RFC-0080 §1 says about `Clone` — the `&Self` receiver, the caller retaining the original,
`#derive`, the region-pointer carve-out — carries over to `Dup` unchanged.

`Share` is new and deliberately narrow:

- **Only handle-category types implement it** — `Rc`, `Arc`, and any future type whose
  whole purpose is shared access to one underlying value. Not `Vec`, `String`, `Map`, or
  user structs.
- **Never blanket-derived, never implied by `Copy`.** There is no `#derive(Share)` and no
  `extend<T: Copy> T: Share`.
- **The result aliases `self`.** Where brands apply (RFC-0076), `share` is
  brand-preserving exactly as `Rc::clone` is specified today; that clause moves verbatim
  from "`Rc: Clone`" to "`Rc: Share`".

### 2. `Copy` implies `Dup`, not `Share`

```metel
extend<T: Copy> T: Dup {
    fun dup(self: &T) -> T { *self }
}
```

Unchanged from RFC-0080 §1.2's blanket, minus the name. `Copy` says nothing about
`Share` — a `Copy` type has no shared backing for a second handle to point at.

### 3. What happens to `Clone`

Three options; this RFC recommends **(a)**:

- **(a) Remove `Clone`.** Mechanical migration: `x.clone()` → `x.dup()` for every value
  type; `rc.clone()` / `arc.clone()` → `.share()`. The rewrite is decidable from the
  receiver type. Gate behind an edition (RFC-0017) or a deprecation window so existing
  code keeps compiling through the transition.
- **(b) Keep `Clone` as a deprecated alias for `Dup`.** Less churn, but leaves the
  misleading spelling available forever and does nothing for the `Rc` case, which is the
  one that actually misleads.
- **(c) Keep `Clone` as an umbrella bound** — `Clone` becomes shorthand for `Dup + Share`
  wherever a caller genuinely doesn't care which they get. Risks re-conflating the two at
  exactly the call sites where the distinction matters; only worth it if a real generic
  use case for "either duplication or sharing" shows up.

### 4. Derive, `Send`/`Sync`, `Drop`

- `#derive(Dup)` replaces `#derive(Clone)`, same rule (all fields `Dup`). No
  `#derive(Share)`.
- `Send`/`Sync` unchanged: `Rc: !Send` so `Rc::share` stays thread-local; `Arc: Send`.
- `Drop` unchanged: `share` incrementing a count and `dup` allocating are both orthogonal
  to RFC-0071's `Drop` rules. (RFC-0157's D3 — `Copy` excludes `Drop` — is a separate
  question this RFC does not touch.)

---

## Relationship to existing RFCs

- **RFC-0157 (Copy and Clone Model Re-analysis, `0-draft`)** — parent. This RFC is
  RFC-0157's "Axis B, second cut" pulled out. Orthogonal to RFC-0157's implicit-copy
  axis (A1/A2/A3) and to `Copy`↔`many` (RFC-0135); composes with any outcome there.
  RFC-0157 keeps a one-paragraph pointer here.
- **RFC-0080 (Stdlib Aspects — Clone, Deref, Send, Sync, `1-under-review`)** — this RFC
  amends §1: `Clone` becomes `Dup`, and a new `Share` aspect is added for handle types.
  §1.1's "independent owned value" wording becomes correct-by-construction rather than
  contradicted by §1.2.
- **RFC-0074 (Shared Pointers — Rc and Arc, `0-draft`) / RFC-0076 (Rc Brands,
  `1-under-review`)** — `Rc`/`Arc` implement `Share`, not `Dup`/`Clone`. RFC-0076's
  brand-preserving-`clone` clause becomes the definition of `Rc::share`. No change to the
  brand machinery itself; this is the surface verb it was always describing.
- **RFC-0071 (Ownership and Move Semantics, `3-integrated`)** — unaffected. `Drop`,
  affine moves, and `--move-check` are orthogonal.
- **RFC-0039 (aspect Alias Syntax, `0-draft`)** — *not* related despite the name;
  RFC-0039 is about naming compound aspect *bounds*, nothing to do with a `Share`/alias
  operation. Noted to prevent a future mix-up.
- **RFC-0017 (Language Edition System, `0-draft`)** — the migration vehicle for option
  (a), if editions are the chosen gate.

---

## Open Questions

1. **Spelling.** `share` / `alias` / `ref` / `handle` for the method; `Share` / `Alias`
   for the aspect. `share` reads well for `Rc` but less so if the category ever widens.
2. **One `Share` aspect or a small family?** `Rc` and `Arc` differ only in atomicity and
   `Send`-ness, which the existing `Send`/`Sync` bounds already capture, so one aspect
   looks right — but a future `Weak::upgrade` (fallible) or a copy-on-write handle would
   not fit `fun share(self: &Self) -> Self` and might want their own.
3. **Does a future COW `String`/`Vec` count as `Dup` or `Share`?** If Metel ever adds
   copy-on-write value types (RFC-0157 lists this as an alternative it does not pursue),
   `s.dup()` on a COW string is observably independent but physically shares until
   mutation. Probably still `Dup` (the sharing is unobservable), but worth stating.
4. **Migration mechanism and default name.** Edition gate vs. deprecation window; and
   whether the kept everyday name is `dup` or `clone` (keeping `clone` for the
   independent-copy case and adding only `share` is a smaller diff but keeps a name whose
   meaning this RFC argues is misleading).
5. **Where this lands.** Fold into RFC-0080 as an amendment, keep as this standalone RFC,
   or attach to RFC-0074/0076. Standalone for now; a reviewer may prefer to merge it into
   RFC-0080's §1.

---

## Decision

**Outcome:** *(pending)*
**Target:** *(set when accepted)*
