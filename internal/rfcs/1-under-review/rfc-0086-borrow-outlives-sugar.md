---
id: rfc-0086
title: "Outlives-of-Bindings Sugar"
date: '2026-07-02'
---

> **Status — under review, speculative.** Depends on RFC-0063 (Region Handles), RFC-0067
> (Reference Types), RFC-0069 (Sub-Region Typing), RFC-0085 (PhantomRegion), RFC-0087
> (Universal Own Regions). Purely a syntax layer: every rule here reads a fact RFC-0087
> already establishes (every binding owns a region) and expresses a relationship between
> two such regions using the ordinary `Outlives` bound RFC-0063 §3.2 already defines.
> Nothing here introduces new semantics, and no new token is introduced: it generalizes an
> existing rule — that a name in tag position denotes a region — to accept
> addressable-lvalue paths (RFC-0067 §2), not just declared region parameters, and a list
> of them. The bracket slot itself is the only surface for referring to a binding's
> region. Revised from an earlier draft that spelled this with the `Outlives<x, y>` aspect
> sitting directly in tag position (see §Alternatives); a further revision generalized
> tag contents from bare identifiers to addressable paths so field/array reborrows
> compose without a new special case.

## Summary

RFC-0087 gives every binding an owned region by default — including `x: &Str` and
`y: &Str` in an ordinary function signature. What is still missing is a way to *say
something* about the relationship between two such regions without declaring a new,
separately-named bracket parameter and rewriting every involved parameter's type
through it.

This RFC adds that syntax by generalizing an existing rule instead of introducing a new
one. A region-tag position (after `@`, `&`, or `&mut`, or as an explicit bracket
argument) has always resolved a single name to a region. This RFC extends that lookup:

1. an **addressable-lvalue path** (RFC-0067 §2 — a named binding, a field access, an
   array index, or a chain of these) denotes its own region (RFC-0087), whether or not
   it is a declared region parameter;
2. a tag position may hold a **list** of paths, denoting the tightest region all of
   them outlive — their meet, under the existing `Outlives` partial order (RFC-0063
   §3.2).

```metel
fun longest(x: &Str, y: &Str) -> &[x, y] Str {
    if x.len() > y.len() { x } else { y }
}
```

`[x, y]` names `x` and `y` — ordinary values, already in scope — and the tag position
they sit in resolves to a region both of their own regions (RFC-0087) outlive. `x` and
`y` keep their plain, untagged types; the relationship is written exactly once, where
it is actually needed. No aspect name is involved: `Outlives` itself is untouched by
this RFC and keeps its one existing job, a bound written after a colon on an
already-named region (`dst: Outlives<src>`, RFC-0063 §3.2). This RFC only teaches the
tag position itself — the slot `[r]` already occupies in `&[r] T` — to accept paths
and lists of them, not just declared region parameters.

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
fun longest(x: &Str, y: &Str) -> &[x, y] Str { ... }
```

The second form is not a different capability from the first — RFC-0087 already
guarantees `x` and `y` have regions to relate; this RFC is exclusively about not
needing to invent and thread a name for the bound to attach to.

---

## Design

### 1. `[p1, p2, ...]` in tag position

> **Grammar.** A region-tag position — directly after `&`, `&mut`, or `@`, or inside an
> explicit `[...]` bracket position — accepts a comma-separated list of
> **addressable-lvalue paths** (RFC-0067 §2: named bindings, field accesses, array
> indexing, and chains thereof). This is a widening of the existing list-of-names form:
> a bare name is the one-step path, so the prior behavior is the degenerate case.
> Arbitrary expressions are still excluded — only paths that are themselves addressable
> (and therefore borrowable) may name a region.

> **Name resolution.** Each `p1, p2, ...` must be an addressable-lvalue path (RFC-0067
> §2) already in scope at the point of use. Two kinds resolve differently:
> - If `pi` is (or ends in) a declared region (a bracket-channel parameter, `Heap`,
>   `LocalHeap`, or any other region-kinded name), it denotes that region directly —
>   exactly the existing rule, unchanged.
> - If `pi` is an addressable value path (a parameter, `let`, field access, or array
>   index — not a type or region name), it denotes `own(pi)` — the **value's lifetime**
>   RFC-0087 gives that lvalue (or the real region a struct's explicit `[own r]`
>   supplies, since such a struct owns its arena and dies with it — RFC-0087 §5). For a
>   `@[r] T` pointer, `own(pi)` is the value's lifetime, which is bounded by but
>   distinct from `r` (the pointee can be moved out or dropped while `r` continues —
>   RFC-0066, RFC-0087 §2 Exception B); only `[own r]` structs resolve to `r`.
>
> These are different kinds of paths to begin with (region parameters and value bindings
> already occupy different namespaces for typechecking purposes), so resolution is
> unambiguous: the compiler already knows which kind `pi` is before deciding what it
> denotes. `own(p)` is metalinguistic notation in this RFC for "the region `p` denotes";
> it is not a language token, and it needs none — the bracket slot `[p]` is the only
> surface that ever refers to it.

> **Semantics.** A tag position holding `p1, p2, ...` denotes a region `a` such that
> `own(p1): Outlives<a>`, `own(p2): Outlives<a>`, …, chosen as the tightest such `a` —
> i.e., the meet of `own(p1)`, `own(p2)`, … under the existing `Outlives` partial order
> (RFC-0063 §3.2), where `own(pi)` is the region `pi` denotes under the resolution rule
> above. A single path is the degenerate case of this rule (the meet of one region is
> itself, i.e. `own(p)`), which is exactly the existing single-name tag behavior — this
> RFC is a strict generalization, not a special case bolted alongside it.

> **Meet well-formedness.** The meet is not computed as an explicit lattice operation; it
> is the solution of a constraint set. The desugaring introduces a fresh region variable
> `a` and emits `own(pi): Outlives<a>` for each operand; the region-inference solver
> (which RFC-0063's borrow checker runs regardless) solves `a` to its greatest feasible
> scope — and that greatest solution *is* the meet. Because every operand is in scope at
> the use site (a precondition of the syntax), the use site's scope is always a common
> lower bound of the operands' regions, so the constraint set is always satisfiable and
> the meet always exists. Operationally the solver picks the deepest scope nested inside
> every operand's region — their greatest common lower bound under the `Outlives` order,
> resting on RFC-0069 §3.3's nesting structure. Failure, when it occurs, is never
> meet-existence: it is the function body failing to produce a value that outlives `a`,
> which the existing borrow check reports. Two residual questions are governed by
> RFC-0069, not this RFC: that the scope model yields a unique greatest lower bound (i.e.
> the nesting structure is tree-shaped), and the interaction of the static handles `Heap`
> / `LocalHeap` with the per-binding scope lattice.

> **Desugaring.** `[p1, p2, ...]` desugars to introducing a fresh, anonymous bracket
> parameter `[a: PhantomRegion]` together with the bounds `own(p1): Outlives<a>`,
> `own(p2): Outlives<a>`, …, exactly as if those bounds had been written explicitly. The
> single-path form `[p]` is just `own(p)` (the degenerate meet). The paths' own declared
> types are **not** rewritten — they stay exactly as written (`x: &Str`, not `x: &[a] Str`),
> because the bound is stated against `own(pi)`, a fact already true of `pi` regardless of
> what its surface type says.

No admission or coercion step is needed here: `own(pi)` already exists for every
addressable lvalue `pi` by RFC-0087, so relating it to a fresh `a` is exactly the same
operation as relating any two already-existing named regions — nothing about `pi`'s
borrow needs to be retroactively treated as belonging anywhere it doesn't already,
structurally, belong.

### 2. Independent relation groups

Each **distinct set** of paths used in a tag position produces its own independent
synthesized tag. A function may relate more than one group without interference:

```metel
struct Pair { left: &Str, right: &Str }

fun combine(w: &Str, x: &Str, y: &Str, z: &Str) -> Pair {
    Pair {
        left:  pick_longer[w, x](w, x),
        right: pick_longer[y, z](y, z),
    }
}

fun pick_longer(a: &Str, b: &Str) -> &[a, b] Str {
    if a.len() > b.len() { a } else { b }
}
```

The tags synthesized for `[w, x]` and `[y, z]` are unrelated — `w`/`x` are never
constrained against `y`/`z`.

Every occurrence of a tag position naming the same set of paths (order-independent)
within one function resolves to the same synthesized tag — writing `[x, y]` twice does
not produce two unrelated regions.

### 3. Where it may and may not appear

- Addressable-lvalue paths (RFC-0067 §2) are accepted — named bindings, field accesses,
  array indexing, and chains thereof. Arbitrary expressions are not; the contents must
  themselves be addressable (and therefore borrowable). This generalizes the prior
  identifiers-only form, so `[self.field]` and `[arr[i]]` are now permitted where they
  are addressable.
- A path may not appear inside its own declaration's constraint — a tag position
  referencing `x` and `y` can only do so once both are already in scope at the point of
  use, so it is legal in a return type (after the full parameter list is bound) or in a
  later local binding, never in an earlier parameter's own type.
- Directed `Outlives` between two *declared region parameters* (the case that actually
  arises, e.g. `transfer`'s `[src, dst: Outlives<src>]`) is unchanged and uses
  RFC-0063 §3.2's existing syntax; this RFC adds nothing there. A directed relation
  between two *binding* regions is not something the sugar expresses, and no separate
  token is provided for it — it has not been shown to correspond to anything a program
  needs to state.

---

## Examples

### Primary case

```metel
fun longest(x: &Str, y: &Str) -> &[x, y] Str {
    if x.len() > y.len() { x } else { y }
}

let s1 = String::from("short");
let s2 = String::from("a bit longer");
let result = longest(&s1, &s2);
// own(s1) and own(s2) already exist (RFC-0087). The [x, y] tag in the callee's
// signature asks for a region both outlive; `result` is checked against it exactly
// as it would be against any other named region tag.
```

### Local binding, not just return position

```metel
fun combine(x: &Str, y: &Str) {
    let picked: &[x, y] Str = if x.len() > y.len() { x } else { y };
    process(picked);
}
```

### Field-path operand

```metel
struct Cursor[a] { source: &[a] Str, pos: USize }

fun rest[a](c: &[a] Cursor) -> &[c.source] Str {
    // [c.source] denotes own(c.source), which is a — the region that backs
    // the cursor's source field. A bare [a] would mean the same thing here;
    // the path form earns its keep when the field's region is not otherwise named.
    slice_from(c.source, c.pos)
}
```

For a struct that is **not** region-parameterized (`struct Cursor { source: &Str }`),
what `own(c.source)` denotes is governed by RFC-0087's per-binding default and
RFC-0069's `Outlives` derivation, not by this RFC; see §Unresolved Q1.

### Mixing a real owned region with a default one

```metel
struct Parser[own r] { nodes: @[r] List<AstNode> }

fun pick[s](p: &[s] Parser, other: &Str) -> &[p, other] AstNode { ... }
```

`p`'s own region is `r` (real, from `Parser`'s explicit `[own r]`, per RFC-0087 §5);
`other`'s own region is a default `PhantomRegion`. `[p, other]` relates them the same
way regardless — the resolution rule in §1 doesn't distinguish real from phantom
operands, only value paths from declared regions.

---

## Alternatives considered

### Spelling this with the `Outlives` aspect in tag position (original draft)

The original draft of this RFC spelled the same mechanism as `Outlives<x, y>`, with the
aspect name itself sitting where a region tag goes:

```metel
fun longest(x: &Str, y: &Str) -> &Outlives<x, y> Str { ... }
```

This was rejected on review for a categorical reason, not a cosmetic one. Everywhere
else `Outlives` appears in the accepted corpus, it is a *bound* — it sits after a colon,
constraining an already-named region (`dst: Outlives<src>` in RFC-0063 §3.2 and
RFC-0077's `transfer`; `impl<R: Region> Outlives<R> for SubRegion<R>` in RFC-0069). It
never itself occupies the tag slot that `dst` or `SubRegion<R>` occupies. Putting
`Outlives<x, y>` directly in tag position overloaded the same identifier with two
different grammatical roles — predicate-on-an-existing-name everywhere else,
region-producing-expression here — distinguished only by which slot it sat in.

That draft also inherited a second, narrower problem downstream of the first:
`Outlives<R>` as a bound reads "the parameter this appears on outlives `R`" (the
*longer*-lived side), while the same spelling in tag position denoted the *shorter*-lived
meet of its arguments — the opposite direction, spelled identically, disambiguated only
by position. This was flagged as an open question in the original draft and never
resolved; the current design resolves it for free, since there is no longer a shared
token to disambiguate.

The revision keeps `Outlives` exclusively in its one existing role and instead
generalizes the tag-position name-lookup rule itself (§1). That rule already had direct
precedent — a bare name in tag position denoting a region — so the revision needed no
outside analogy to justify it, unlike the original draft, which had to appeal to
RFC-0076's allocation-site brand inference as the closest existing precedent for an
implicit, undeclared tag.

### A `region(p)` projection primitive (intermediate draft)

An intermediate draft introduced a named `region(p)` primitive — "the region `p`
denotes" — and treated the bracket list as sugar over it (`[p]` = `region(p)`,
`[x, y]` = `meet(region(x), region(y))`). Retracted: the bracket slot already *is* the
surface for a path's region (single name = degenerate meet), and once the meet is framed
as constraint-solving rather than a lattice operation, there is no operation left that
needs the projection named. The only case that would have justified a separate token —
a directed `Outlives` between two *binding* regions — does not correspond to anything a
program needs to state (directed `Outlives` that arises in practice is between declared
region parameters, already handled by RFC-0063 §3.2). The notation `own(p)` is retained
purely as metalinguistic shorthand in this RFC's desugaring, matching RFC-0087's
terminology; it is not a language token.

### Identifiers only, paths deferred (intermediate draft)

An intermediate revision restricted tag contents to bare identifiers and deferred
`self.field`-style paths. Rejected in favor of accepting addressable-lvalue paths
(RFC-0067 §2) directly: the region a path denotes is well-defined for any addressable
lvalue, so accepting paths is a grammar widening of an existing rule rather than a new
special case, and it removes a seam — `longest` would have worked while `peek` into a
borrowed struct's field would not — that would otherwise make the sugar feel partial.
Constraining the contents to *addressable* paths (not arbitrary expressions) preserves
the property that only things which can themselves be borrowed may name a region.

### A single ambient `own` region per function

An earlier direction considered generalizing RFC-0068's `[own r]` to be automatic for
every function as a single reserved marker — one ambient `PhantomRegion` per call, no
bracket-channel declaration at all. Rejected in favor of naming bindings directly: a
single ambient tag cannot express two unrelated relation groups in the same function
(§2's `Pair` example), and `[x, y]` is no more verbose for the common single-group case.
RFC-0087's per-*binding* default (rather than per-function) is what makes this RFC's
finer granularity possible.

### Fully bare inference with no name anywhere

Inferring the relationship without writing anything — the RFC-0075 inter-function
shape — was rejected again here for the same reason it was rejected there: it hides
the contract from the signature. This RFC's syntax stays visible specifically to avoid
that failure mode; `[x, y]` is a small addition to the return type, not a disappearance
of the whole relationship.

### Requiring RFC-0085's fully explicit form always

Remains fully available. A function author can always fall back to an explicit
`[a: PhantomRegion]` bracket parameter with `x` and `y`'s types rewritten to `&[a] Str`,
if this sugar's restrictions (§3) don't fit.

---

## Unresolved questions

1. **Path operands into unparameterized structs.** §1 now accepts addressable-lvalue
   paths, so `[c.source]` denotes `own(c.source)`. The open question is not syntactic
   but semantic: for a struct *not* region-parameterized
   (`struct Cursor { source: &Str }`), what `own(c.source)` denotes and whether it is
   the region a return-borrow needs is governed by RFC-0087's per-field default (still
   under review) and RFC-0069's `Outlives` derivation. Structs that are
   region-parameterized (`struct Cursor[a] { source: &[a] Str }`) are unambiguous:
   `own(c.source)` = `a`.

2. **Cross-closure references.** Whether a tag position may name a binding captured
   from an enclosing scope, rather than only the current function's own parameters and
   locals, is deferred until RFC-0050 (Closure Capture Lists, still in draft) is
   further along — the same open point as RFC-0087 §Unresolved Q3.

3. **Diagnostics.** Error messages must be phrased in terms of the original surface
   paths (`x`, `y`, `c.source`) and which one actually determined the tightest bound,
   not the synthesized anonymous tag introduced by desugaring. Exact format deferred to
   implementation.

4. **Canonicalization across nested scopes.** §2 states that repeated occurrences of
   the same path-set resolve to the same tag. The precise rule when occurrences are
   inside different nested blocks (e.g., one inside a loop body, one at the function's
   top level) is deferred to implementation.

5. **Meet existence — resolved (residuals in RFC-0069).** §1 (Meet well-formedness)
   resolves this: the meet is the greatest solution of the desugar's `Outlives<a>`
   constraints, found by region inference, and always exists for co-in-scope operands
   (the use-site scope is a satisfiability witness). The remaining questions — unique
   greatest lower bounds (tree-shaped nesting) and `Heap`/`LocalHeap` in the scope
   lattice — belong to RFC-0069.

---

## References

- RFC-0063 (Region Handles) §2 — the single-name tag-position lookup rule this RFC
  generalizes; §3.2 — the existing `Outlives<R>` bound, reused unchanged as the
  semantics underlying the desugaring, never itself placed in tag position.
- RFC-0067 (Reference Types) §2 — defines the addressable-lvalue paths this RFC accepts
  as tag contents; only paths that are themselves addressable (and therefore borrowable)
  may name a region.
- RFC-0069 (Sub-Region Typing) §3.3 — the transitive `Outlives` derivation that lets
  mixed real/phantom relations (§Examples, fourth example) resolve without special
  casing, and on which meet well-formedness (§1) rests.
- RFC-0085 (PhantomRegion) — the type backing the synthesized tag this RFC's
  desugaring introduces.
- RFC-0087 (Universal Own Regions) — establishes an own region for every binding `n`
  (written `own(n)` in this RFC's desugaring); this RFC is entirely downstream of that
  fact and adds no semantics of its own beyond syntax for referring to it.
