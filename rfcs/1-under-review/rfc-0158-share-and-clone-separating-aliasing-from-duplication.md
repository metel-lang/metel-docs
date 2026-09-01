---
id: rfc-0158
title: "Share and Clone: Separating Aliasing from Duplication"
date: '2026-08-31'
status: under-review
target:
updated: '2026-08-31'
tracking: 'https://github.com/metel-lang/metel-core/issues/919'
---

> **Split out of RFC-0157 (Copy and Clone Model Re-analysis), 2026-08-31, then narrowed
> the same day.** RFC-0157's strategic conclusion is: don't spend divergence budget on the
> regular-value model — keep `Copy`/`Clone` and their Rust-familiar ergonomics, minus a
> couple of retro-compat artifacts. This RFC is one of those artifact removals. It does
> **not** rename anything and does **not** touch implicit-copy behavior. It adds one
> narrow aspect, `Share`, and tightens what `Clone` is allowed to mean, so that "did I
> just create an alias" stops being invisible at `Rc`/`Arc` call sites.

> **Status — under review (2026-08-31).** purely-additive Share aspect; ready for review alongside RFC-0157

## Summary

`Clone` today is specified inconsistently. RFC-0080 §1.1: `.clone()` "produces a new
**independent** owned value." RFC-0080 §1.2: a `Clone` impl may be "incrementing a
reference count." Those describe two different operations:

- **duplication** — `vec.clone()` allocates a new backing buffer; the result is
  independent, no aliasing created.
- **aliasing** — `rc.clone()` bumps a refcount and returns another handle to the **same
  cell** (RFC-0076: brand-preserving). Aliasing *is* the point.

This RFC keeps `Copy` and `Clone` exactly as they are for duplication, and moves aliasing
out into its own aspect:

- **`Clone`** — unchanged in every respect except that it now means *only* independent
  duplication (RFC-0080 §1.1). The §1.2 "incrementing a reference count" reading is
  reassigned to `Share`.
- **`Share`** *(new)* — `fun share(self: &Self) -> Self`, another handle to the same
  underlying state; the result aliases `self`. Implemented only by handle-category types
  (`Rc`, `Arc`, future ones), never blanket-derived, never implied by `Copy` or `Clone`.

`vec.clone()` is untouched. `rc.clone()` becomes `rc.share()`. At a call site, `x.clone()`
now reliably means "independent" and `h.share()` means "aliasing now exists" — the fact
RFC-0076's brands already encode in the type, made visible in the code.

No rename, no change to `Copy`, no change to implicit-copy behavior, no `#derive` change,
no edition break for value types. The only migration is `Rc`/`Arc` call sites, and `Rc`
is still `0-draft`.

---

## Motivation

**The conflation is a real legibility cost.** `let b := a.clone();` tells you nothing
about whether `b` and `a` now share mutable state. For an `Rc` they do; for a `Vec` they
don't; the line looks identical. In exactly the code `Rc` exists for — owned aggregates
mixed with shared graph nodes — every `.clone()` is a small puzzle. RFC-0076 built a whole
brand system to answer "does this alias that" at the type level; the surface syntax should
not work against it.

**The existing spec contradicts itself** (RFC-0080 §1.1 vs §1.2, quoted above). One of the
two has to give. This RFC resolves it in the direction that costs nothing familiar:
`Clone` keeps the §1.1 meaning every Rust programmer already has for it, and the refcount
case moves to a new name.

**Prior art is converging here.** Rust's 2024–2026 ergonomic-ref-counting work introduces
a `Share`/`Claim`-style trait precisely to mark "the `.clone()` that produces an alias,"
separate from `Clone`-as-duplication (see RFC-0157's Prior art). `Arc::clone` looking
identical to `Vec::clone` is a documented Rust papercut — people `#derive(Clone)` and
deep-copy by accident, or see `.clone()` in a hot loop and misread the cost. Adopting the
split tracks where Rust is going; it is *less* surprising to a Rust programmer over time,
not more.

**It is cheap and orthogonal.** No rule about implicit copy, move semantics, `Copy`,
`Drop`, or closure capture changes. It is one new aspect plus a one-line tightening of
`Clone`'s definition, and it composes with any outcome of RFC-0157 or RFC-0135.

---

## Background: how duplication and sharing work today

Checked against RFC-0080 (`1-under-review`), RFC-0076 (`1-under-review`), RFC-0074
(`0-draft`):

- **`Clone`** (RFC-0080 §1): `aspect Clone { fun clone(self: &Self) -> Self; }`. Blanket
  `extend<T: Copy> T: Clone { fun clone(self: &T) -> T { *self } }`. Derivable
  (`#derive(Clone)`) for a struct/enum with all-`Clone` fields. Region pointers `@[r] T`
  deliberately get no blanket `Clone` (§1.4).
- **`Rc<T, 'b>` / `Arc<T, 'b>`** (RFC-0074, RFC-0076): `clone` is specified as
  **brand-preserving** — `let b := a.clone();` gives `b` the same brand as `a`, i.e. the
  type system records that `b` aliases `a`'s cell; `Rc::new` gives a fresh brand. So
  `Rc::clone` is *already* the aliasing operation — it just shares the `Clone` name.
- **`Copy`** (RFC-0080 §1.2): implies `Clone` by the bitwise blanket. A `Copy` value has
  no shared backing to alias.

---

## Proposal

### 1. The `Share` aspect (new)

```metel
aspect Share {
    fun share(self: &Self) -> Self;   // another handle to the same state; result aliases self
}
```

- **Only handle-category types implement it** — `Rc`, `Arc`, and any future type whose
  purpose is shared access to one underlying value. Not `Vec`, `String`, `Map`, or user
  structs.
- **Never blanket-derived, never implied.** No `#derive(Share)`; no `extend<T: Copy> T:
  Share`; `Clone` does not imply `Share` and `Share` does not imply `Clone`.
- **The result aliases `self`.** Where brands apply (RFC-0076), `share` is
  brand-preserving — RFC-0076's current "`Rc::clone` preserves the brand" clause becomes
  "`Rc::share` preserves the brand," verbatim.

### 2. `Clone` tightened, not changed

`Clone` keeps its aspect definition, its `&Self` receiver, `#derive(Clone)`, the
`extend<T: Copy> T: Clone` blanket, and the `@[r] T` carve-out — all exactly as RFC-0080
§1 has them. The only edit: RFC-0080 §1.2's "incrementing a reference count" example is
removed as a description of `Clone`; that behavior is `Share`. `.clone()` now means
independent duplication with no exceptions, matching §1.1 and matching Rust.

### 3. `Rc` / `Arc` implement `Share`, not `Clone`

`Rc<T, 'b>` and `Arc<T, 'b>` drop their `Clone` impl and gain a `Share` impl. `rc.clone()`
→ `rc.share()`. The migration is decidable from the receiver type and small — `Rc` is
`0-draft`, so this can be a plain cutover rather than an edition-gated one.

*Alternative for review:* have `Rc`/`Arc` implement **both**, with `clone()` a
deprecated alias for `share()` through one release, purely to soften the transition for
Rust muscle memory. Recommended only if the cutover proves noisy in practice.

### 4. Unchanged

`Copy`; the `Copy: Clone` blanket; `#derive(Clone)`; implicit-copy behavior at by-value
use sites; `Drop` rules; `Send`/`Sync` (`Rc: !Send` so `Rc::share` stays thread-local,
`Arc: Send`); all value-type `.clone()` call sites.

---

## Relationship to existing RFCs

- **RFC-0157 (Closure Capture Default (Move), `2-accepted`; regular-value analysis split to RFC-0162)** — parent. RFC-0157's
  recommendation is "no divergence on the regular-value model"; this RFC is one of the two
  artifact removals it does endorse (the other being relaxing the `Copy`+`Drop` ban).
  Orthogonal to RFC-0157's P0/P1/P2/P3 and to RFC-0135.
- **RFC-0080 (Stdlib Aspects — Clone, Deref, Send, Sync, `1-under-review`)** — amended:
  §1.2 loses the refcount example; a new §1.x defines `Share`. §1.1's "independent owned
  value" becomes true without qualification.
- **RFC-0074 (Shared Pointers — Rc and Arc, `0-draft`) / RFC-0076 (Rc Brands,
  `1-under-review`)** — `Rc`/`Arc` implement `Share`. RFC-0076's brand-preserving-`clone`
  clause becomes the definition of `Rc::share`; the brand machinery itself is unchanged.
- **RFC-0039 (aspect Alias Syntax, `1-under-review`)** — *not* related despite the name;
  RFC-0039 names compound aspect *bounds*. Noted to prevent a mix-up.
- **RFC-0135 (Multiplicity for Ordinary Types, `1-under-review`)** — independent. If
  RFC-0135's `Copy`→`many` rename does not proceed (RFC-0157's recommendation), `Share` is
  unaffected; if it does, `Share` sits beside `many` the same way it sits beside `Copy`.
- **RFC-0071 (Ownership and Move Semantics, `3-integrated`)** — unaffected.

---

## Open Questions

1. **Spelling.** `share` / `alias` / `handle` for the method; `Share` / `Alias` for the
   aspect. `share` reads well for `Rc`.
2. **One `Share` aspect or a small family?** `Rc` vs `Arc` differ only in atomicity /
   `Send`, already captured by existing bounds, so one aspect looks right — but a future
   fallible `Weak::upgrade` would not fit `fun share(self: &Self) -> Self`.
3. **Cutover vs. deprecated alias for `Rc`/`Arc`** — §3's alternative. Decide from how
   much real code (fixtures, stdlib) types `rc.clone()` today.
4. **Does a future COW `String`/`Vec` (RFC-0157 lists this as an unpursued alternative)
   count as `Clone` or `Share`?** Probably `Clone` — the sharing is unobservable — but
   worth stating if that path is ever taken.

---

## Decision

**Outcome:** *(pending)*
**Target:** *(set when accepted)*
