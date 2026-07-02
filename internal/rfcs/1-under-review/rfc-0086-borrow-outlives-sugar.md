---
id: rfc-0086
title: "Outlives-of-Bindings Sugar"
date: '2026-07-02'
---

> **Status — under review, speculative.** Depends on RFC-0063 (Region Handles), RFC-0069
> (Sub-Region Typing), RFC-0076 (Brand Types), RFC-0085 (PhantomRegion), RFC-0087
> (Universal Own Regions). Purely a syntax layer: every rule here reads a fact
> RFC-0087 already establishes (every binding owns a region) and expresses a
> relationship between two such regions using the ordinary `Outlives` bound RFC-0063
> §3.2 already defines. Nothing here introduces new semantics; it introduces a new
> way to *name* the operands of an existing one. More speculative than RFC-0085 or
> RFC-0087: naming an already-bound value directly in a region-tag position has no
> precedent elsewhere in the accepted corpus except the allocation-site brand
> inference of RFC-0076. Read RFC-0085 and RFC-0087 first.

## Summary

RFC-0087 gives every binding an owned region by default — including `x: &Str` and
`y: &Str` in an ordinary function signature. What is still missing is a way to *say
something* about the relationship between two such regions without declaring a new,
separately-named bracket parameter and rewriting every involved parameter's type
through it.

This RFC adds that syntax:

```metel
fun longest(x: &Str, y: &Str) -> &Outlives<x, y> Str {
    if x.len() > y.len() { x } else { y }
}
```

`Outlives<x, y>` names `x` and `y` — ordinary values, already in scope — and produces
a region that both of their own regions (RFC-0087) outlive. `x` and `y` keep their
plain, untagged types; the relationship is written exactly once, where it is actually
needed. This is nothing more than RFC-0063 §3.2's existing `Outlives<R>` bound, applied
to the regions RFC-0087 already gave `x` and `y`, with a naming convention that lets
the bound refer to the *bindings* instead of requiring a separately declared region
parameter for the bound to sit on.

---

## Motivation

### What RFC-0087 supplies and what is still missing

RFC-0087 makes it true that `x` and `y` each own a region. It does not provide any way
to write that down in a signature — there is still no syntax that lets a return type
say "bounded by whichever of `x`, `y` is shorter." Filling that gap with a fresh,
separately-declared bracket parameter (the fully explicit RFC-0085/RFC-0063 form) works,
but requires a name that exists for no reason other than to be that bound's anchor, and
requires rewriting both `x`'s and `y`'s parameter types to mention it.

### The gap, concretely

```metel
// Fully explicit — a name (`a`) exists purely to be an anchor,
// and x, y's types are rewritten to mention it:
fun longest[a: PhantomRegion](x: &[a] Str, y: &[a] Str) -> &[a] Str { ... }

// What this RFC allows instead — x, y keep their own plain types;
// the relationship is stated once, where it is consumed:
fun longest(x: &Str, y: &Str) -> &Outlives<x, y> Str { ... }
```

The second form is not a different capability from the first — RFC-0087 already
guarantees `x` and `y` have regions to relate; this RFC is exclusively about not
needing to invent and thread a name for the bound to attach to.

---

## Design

### 1. `Outlives<name, name, ...>` in tag position

> **Grammar.** `Outlives<n1, n2, ...>` may appear anywhere a region tag is expected —
> directly after `&`, `&mut`, or `@`, or inside an explicit `[...]` bracket position.
> Each `n1, n2, ...` must be an identifier naming a binding already in scope at the
> point of use — a value (parameter or `let`), not a type or region name.

> **Semantics.** Let `own(n)` denote the region RFC-0087 gives binding `n` by default
> (or the real region a struct's explicit `[own r]` supplies, if `n`'s type declared
> one — RFC-0087 §5). `Outlives<n1, n2, ...>` denotes a region `a` such that
> `own(n1): Outlives<a>`, `own(n2): Outlives<a>`, …, chosen as the tightest such `a` —
> i.e., the meet of `own(n1)`, `own(n2)`, … under the existing `Outlives` partial
> order (RFC-0063 §3.2). This is not a new relation; it is the same `Outlives` bound
> already used for two explicitly-named regions, computed over the regions RFC-0087
> already attached to `n1`, `n2`, ….

> **Desugaring.** `Outlives<n1, n2, ...>` used in a signature desugars to introducing a
> fresh, anonymous bracket parameter `[a: PhantomRegion]` together with the bounds
> `own(n1): Outlives<a>`, `own(n2): Outlives<a>`, …, exactly as if those bounds had
> been written explicitly against each `ni`'s already-existing own-region. `n1`'s,
> `n2`'s, … own declared parameter types are **not** rewritten — they stay exactly as
> written (`x: &Str`, not `x: &[a] Str`), because the bound is stated against `own(ni)`,
> a fact that is already true of `ni` regardless of what its surface type says.

No admission or coercion step is needed here, unlike an earlier draft of this RFC
(§Alternatives): `own(ni)` already exists for every `ni` by RFC-0087, so relating it
to a fresh `a` is exactly the same operation as relating any two already-existing
named regions — nothing about `ni`'s borrow needs to be retroactively treated as
belonging anywhere it doesn't already, structurally, belong.

### 2. Independent relation groups

Each **distinct set** of names passed to `Outlives<...>` produces its own independent
synthesized tag. A function may relate more than one group without interference:

```metel
struct Pair { left: &Str, right: &Str }

fun combine(w: &Str, x: &Str, y: &Str, z: &Str) -> Pair {
    Pair {
        left:  Outlives<w, x> pick_longer(w, x),
        right: Outlives<y, z> pick_longer(y, z),
    }
}
```

`Outlives<w, x>` and `Outlives<y, z>` are unrelated tags — `w`/`x` are never
constrained against `y`/`z`.

Every occurrence of `Outlives<...>` naming the same set of bindings (order-independent)
within one function resolves to the same synthesized tag — writing `Outlives<x, y>`
twice does not produce two unrelated regions.

### 3. Where it may not appear

- Only identifiers naming already-bound values are accepted — not arbitrary
  expressions, and not `self.field`-style paths (deferred, §Unresolved).
- A name may not appear inside its own declaration's constraint — `Outlives<x, y>`
  can only reference bindings already in scope at the point of use, so it is legal in
  a return type (after the full parameter list is bound) or in a later local binding,
  never in an earlier parameter's own type.

---

## Examples

### Primary case

```metel
fun longest(x: &Str, y: &Str) -> &Outlives<x, y> Str {
    if x.len() > y.len() { x } else { y }
}

let s1 = String::from("short");
let s2 = String::from("a bit longer");
let result = longest(&s1, &s2);
// own(s1) and own(s2) already exist (RFC-0087). Outlives<x, y> in the callee's
// signature asks for a region both outlive; `result` is checked against it exactly
// as it would be against any other named region tag.
```

### Local binding, not just return position

```metel
fun combine(x: &Str, y: &Str) {
    let picked: &Outlives<x, y> Str = if x.len() > y.len() { x } else { y };
    process(picked);
}
```

### Mixing a real owned region with a default one

```metel
struct Parser[own r] { nodes: @[r] List<AstNode> }

fun pick[s](p: &[s] Parser, other: &Str) -> &Outlives<p, other> AstNode { ... }
```

`p`'s own region is `r` (real, from `Parser`'s explicit `[own r]`, per RFC-0087 §5);
`other`'s own region is a default `PhantomRegion`. `Outlives<p, other>` relates them
the same way regardless — the bound doesn't distinguish real from phantom operands.

---

## Alternatives considered

### Borrow admission into a synthesized tag (earlier draft of this RFC)

An earlier draft of this RFC — written before RFC-0087 existed — specified the
desugaring as "admitting" `x`'s and `y`'s actual borrows into a freshly synthesized
`PhantomRegion`, treating the admission as a coercion that added a compile-time-only
constraint. That formulation required its own soundness argument (leaning on
`PhantomRegion`'s mandatory elision) independent of anything else in the region
system. With RFC-0087 in place, `x` and `y` already have real regions of their own
before `Outlives<x, y>` is ever written, so the same result now falls out of the
ordinary `Outlives` bound with no separate admission step to justify.

### A single ambient `own` region per function

An earlier direction considered generalizing RFC-0068's `[own r]` to be automatic for
every function as a single reserved marker — one ambient `PhantomRegion` per call, no
bracket-channel declaration at all. Rejected in favor of naming bindings directly: a
single ambient tag cannot express two unrelated relation groups in the same function
(§2's `Pair` example), and `Outlives<x, y>` is no more verbose for the common
single-group case. RFC-0087's per-*binding* default (rather than per-function) is what
makes this RFC's finer granularity possible.

### Fully bare inference with no name anywhere

Inferring the relationship without writing anything — the RFC-0075 inter-function
shape — was rejected again here for the same reason it was rejected there: it hides
the contract from the signature. This RFC's syntax stays visible specifically to avoid
that failure mode; `Outlives<x, y>` is a small addition to the return type, not a
disappearance of the whole relationship.

### Requiring RFC-0085's fully explicit form always

Remains fully available. A function author can always fall back to an explicit
`[a: PhantomRegion]` bracket parameter with bounds written against `own(x)`, `own(y)`
directly, if this sugar's restrictions (§3) don't fit.

---

## Unresolved questions

1. **Naming collision with the existing `Outlives<R>` bound.** RFC-0063 §3.2's
   `Outlives<R>` is a bound meaning "the parameter this appears on outlives `R`" — the
   *longer*-lived side. This RFC's `Outlives<n1, n2, ...>` produces the *shorter*-lived
   meet of its arguments — the opposite direction, spelled the same way, distinguished
   only by appearing in a bound position versus a tag-producing position. Whether this
   is acceptable (disambiguated by position) or needs a distinct name (`Meet<...>`,
   `ShortestOf<...>`) is unresolved and should be settled before this leaves draft.

2. **Struct fields and paths.** `Outlives<self.field, y>` or similar path expressions
   are not supported by §3; only bare identifiers are. Whether this should extend to
   field paths is deferred, consistent with RFC-0087's own deferral of per-field
   defaults beyond whole bindings.

3. **Cross-closure references.** Whether `Outlives<...>` may name a binding captured
   from an enclosing scope, rather than only the current function's own parameters and
   locals, is deferred until RFC-0050 (Closure Capture Lists, still in draft) is
   further along — the same open point as RFC-0087 §Unresolved Q3.

4. **Diagnostics.** Error messages must be phrased in terms of the original surface
   names (`x`, `y`) and which one actually determined the tightest bound, not the
   synthesized anonymous tag introduced by desugaring. Exact format deferred to
   implementation.

5. **Canonicalization across nested scopes.** §2 states that repeated occurrences of
   the same name-set resolve to the same tag. The precise rule when occurrences are
   inside different nested blocks (e.g., one inside a loop body, one at the function's
   top level) is deferred to implementation.

---

## References

- RFC-0063 (Region Handles) §3.2 — the existing `Outlives<R>` bound this RFC reuses
  unchanged; see §Unresolved Q1 for the naming tension between the two.
- RFC-0069 (Sub-Region Typing) §3.3 — the transitive `Outlives` derivation that lets
  mixed real/phantom relations (§Examples, third example) resolve without special
  casing.
- RFC-0076 (Brand Types) — precedent for a per-site implicit, undeclared tag
  (allocation-site brand inference); the closest existing analogue to referencing an
  automatically-established fact by naming a value rather than declaring a parameter.
- RFC-0085 (PhantomRegion) — the type backing the synthesized tag this RFC's
  desugaring introduces.
- RFC-0087 (Universal Own Regions) — establishes `own(n)` for every binding `n`; this
  RFC is entirely downstream of that fact and adds no semantics of its own beyond
  syntax for referring to it.
