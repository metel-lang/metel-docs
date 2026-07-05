---
id: rfc-0087
title: "Universal Own Regions"
date: '2026-07-02'
---

> **RETRACTED — 2026-07-05.** Universal own-regions exist to give every binding a
> `Region` instance so that `Outlives` constraints and the `[x, y]` borrow sugar (RFC-0086)
> have something to name. Under the split model (RFC-0088), lifetime anchors *are* binding
> names — `&r T` names the binding `r` directly as the anchor, without any `Region`
> instance attached to `r`. The universal-own-region machinery is therefore unnecessary:
> bindings have scopes the borrow checker tracks, and those scopes are named directly in
> the `<&r>` anchor syntax. All three of its dependencies (RFC-0069, RFC-0085, RFC-0086)
> are also retracted. See `reports/memory-model/lifetimes-vs-regions-2026-07-02.md` §5.

## Summary

RFC-0068 lets a struct opt into an owned region — `struct Parser[own r] { ... }` —
committing to a real, `BumpRegion`-backed arena tied to the struct's own lifetime.
Every other binding, of any type, has no owned region at all; RFC-0069 §3.1 treats its
lifetime as an informal fallback ("the borrow checker treats `r`'s lifetime as the
scope of `parser`'s binding") used only when a struct-owned region has no enclosing
region to sub from.

This RFC replaces that ad hoc fallback with a real default: **every binding of every
type, without declaring anything, owns a `PhantomRegion` (RFC-0085) scoped to its own
binding.** Because `PhantomRegion` allocations are unconditionally elided, this default
has no runtime cost and no observable effect on its own. A struct that explicitly
declares `[own r: BumpRegion]` (or any other real region) still gets that real region
instead — the phantom default only fills the gap for bindings that would otherwise
have nothing.

```metel
fun longest(x: &Str, y: &Str) -> &Str { ... }
```

Under this RFC, `x` and `y` already, automatically, each own a `PhantomRegion` scoped
to their own bindings — the same as any `let` binding, any parameter, any field. No
syntax in this signature changes to get that; it is true by default, the same way
every value already has a drop obligation and a liveness range without the programmer
declaring either. RFC-0086 provides the syntax to *use* this fact to relate two
bindings; this RFC only establishes that the fact exists.

---

## Motivation

### RFC-0069 §3.1 as an ad hoc fallback

RFC-0069 §3.1 already needs the idea that a plain binding has a lifetime equal to its
own scope — but only states it for one narrow case (a struct-owned region constructed
with no enclosing region to sub from), and only so the borrow checker has *something*
to reason about in that case. The idea underneath it — every binding's own scope is a
real, trackable lifetime — is not actually specific to struct-owned regions; it applies
to every binding the borrow checker already computes a liveness range for.

### What RFC-0085 alone could not finish

An earlier design (RFC-0085's own first draft) tried to solve borrow-relating ergonomics
directly, with two purpose-built call-site rules: construct a `PhantomRegion` handle
automatically when a bracket parameter needed one, and admit an existing borrow into a
`PhantomRegion`-tagged type without requiring it to have been allocated there. Both
rules were sound, but both had to be independently justified as exceptions to the
ordinary bracket-channel rules (RFC-0065), scoped narrowly to `PhantomRegion` alone.

Making the own-region universal removes the need for either exception. If every
binding already owns a `PhantomRegion`, there is no "construct one for this call" step
left to justify — the region already exists, the same way a struct's `[own r]` arena
already exists the moment the struct is constructed (RFC-0068 §2). And there is no
"admit this borrow" step left to justify — the borrow was never anything other than a
loan of a binding that already had its own region from the start.

---

## Design

### 1. Default construction

> **Rule.** Every binding — a `let`, a function parameter, a struct field's storage
> for its own value, anything the borrow checker tracks a liveness range for —
> implicitly performs the RFC-0068 §2 construction step (an owned region, created when
> the binding comes into existence, ending when the value is moved out, dropped, or goes
> out of scope) targeting `PhantomRegion`, unless one of the two exceptions in §2
> applies. This region represents the **value's lifetime** — distinct, as §2 Exception B
> explains, from any region the value may be allocated *into*.

This generalizes RFC-0068 §1–§3 from an opt-in struct declaration to the default for
everything. The mechanics are unchanged — construction happens as part of the binding
coming into existence, the region is implicitly in scope for reasoning about that
binding's own lifetime, and it is freed (trivially — see §3) when the binding's scope
ends. What changes is that no `[own r]` needs to be written, and the backing is
`PhantomRegion` rather than `BumpRegion`.

The default own region has **no declared name**. It is not a value the programmer can
hold, pass, or call methods on directly — RFC-0086 is the only way to read it, and it
does so by naming the *binding*, not the region.

### 2. Exceptions — when the default is overridden

> **Exception A — explicit `[own r: R]`.** A struct that declares its own owned region
> explicitly (RFC-0068 §1), for any backing type `R`, gets that real region instead of
> the phantom default. The default only fills the gap when nothing else is declared.

> **Exception B — the binding is itself a region pointer.** A binding of type `@[r] T`
> already has an explicit backing region `r` for what it points into, and this RFC still
> gives the *pointer binding itself* its own default region under §1. The two must not
> be conflated, and the reason is not stylistic: `r` is the **region's** lifetime (how
> long the arena is alive), while the binding's own region is the **value's** lifetime
> (how long this particular value is usable). The value lifetime is bounded by `r` but
> may be strictly shorter, because a region-allocated value can be moved out or dropped
> while `r` continues to hold other allocations (RFC-0066). This distinction is
> load-bearing: a borrow derived from the value is tagged with the *value* lifetime, not
> with `r`, precisely so that individual drop remains possible — tagging it with `r`
> would promise validity as long as the arena lives and so forbid moving the pointee
> before `r` ends. (`[own r]` structs are the one case that resolves to `r` instead:
> they *own* the arena and die with it, so their value lifetime equals `r` — see §5.)

### 3. Zero cost

Because `PhantomRegion` mandates elision (RFC-0085 §1), giving every binding one by
default is unconditionally free — there is no allocation, no drop list entry, no
runtime representation. This is the fact that makes "universal by default" different
from, say, defaulting every binding to an owned `BumpRegion`, which would be an absurd
per-binding cost. A default backed by a region type that is only ever *permitted* to
elide (`AutoRegion`) would not give the same guarantee, since the compiler could
legitimately choose real backing for some allocation sharing a default-region's
lifetime; `PhantomRegion`'s mandatory elision is what makes the default provably free
in every case, not just the common one.

### 4. Interaction with RFC-0069 SubRegion

Because a binding's default own region is a real (if always-elided) `Region`
implementor, it participates in RFC-0069's transitive `Outlives` derivation exactly as
any other owned region would. If a value with its own default region is itself nested
inside another value's scope, the same nesting-derives-`Outlives` reasoning
(RFC-0069 §3.3) applies without any special casing for the phantom backing — nothing
in RFC-0069's derivation depends on what the region actually allocates.

This is what lets RFC-0086's `[x, y]` tag-position sugar be nothing more than an
ordinary multi-way `Outlives` bound between two already-existing regions, rather than a
bespoke relating mechanism: by the time RFC-0086 is invoked, `x` and `y` already have
regions to relate, courtesy of this RFC.

### 5. Interaction with real owned regions

A struct with an explicit `[own r: BumpRegion]` (Exception A) may still be related to
another binding's default phantom region through the same `Outlives` machinery. Mixing
a real region and a phantom one in one relation is not a special case — both are
ordinary `Region` implementors from the borrow checker's point of view; only their
elision guarantees differ, and elision guarantees are not inputs to `Outlives`
reasoning.

---

## Examples

### A plain function, no declarations added

```metel
fun longest(x: &Str, y: &Str) -> &Str { ... }
```

Before this RFC: `x` and `y` have no lifetime a bound could reference at all. After
this RFC: both already own a `PhantomRegion` scoped to their own bindings — nothing in
this signature changed to make that true. (The signature still cannot relate them to
each other without RFC-0086's syntax; this RFC only supplies what RFC-0086 needs to
exist beforehand.)

### A struct opting out of the default

```metel
struct Parser[own r] {
    nodes: @[r] List<AstNode>,
}
```

`Parser`'s own region is `r: BumpRegion` (RFC-0068's existing default backing),
overriding this RFC's phantom default per Exception A. A `Parser` value's own
lifetime-tracking region is real, not elided, because the struct asked for real
storage.

### A region pointer binding

```metel
fun read[r](n: @[r] Node) -> I64 {
    // `r` is the region's lifetime — the arena backing n's pointee.
    // `own(n)` is n's *value* lifetime — how long this particular pointer value is
    // usable, which ends if the pointee is moved out (RFC-0066) even though `r`
    // continues. A borrow derived from `n` is tagged with `own(n)`, not `r`, so that
    // individual drop stays possible (Exception B). Unused here, but present.
    n.val
}
```

---

## Alternatives considered

### Leave RFC-0069 §3.1's fallback as-is, scoped to struct-owned regions only

This is the status quo. Rejected because it leaves RFC-0086 with no foundation to
build on except restating the same fallback logic as a special case of its own sugar —
duplicating a rule that is more honestly stated once, generally, here.

### Default to `AutoRegion` instead of `PhantomRegion`

Rejected per §3: `AutoRegion` is only permitted, not required, to elide, so a
universal default backed by it could not give an unconditional zero-cost guarantee —
some allocation sharing a default region's lifetime might legitimately receive real
backing, at which point "every binding has one of these for free" would no longer be
true in every case.

### Keep RFC-0068's `[own r]` opt-in only, solve ergonomics entirely in RFC-0085

This is what RFC-0085's first draft attempted, with the two call-site rules described
in §Motivation. Rejected in favor of this RFC's single default for the reasons given
there — two independently-justified exceptions to RFC-0065 versus one uniform default.

---

## Unresolved questions

1. **Scope for primitive/scalar types.** Whether every binding of a plain scalar type
   (`I64`, `Bool`) meaningfully needs its own default region, or whether the compiler
   may simply never materialize the bookkeeping for types that provably can never
   participate in an `Outlives` relation, is left as an implementation latitude. The
   specification in §1 is universal; an implementation is free to prove large classes
   of bindings never need the fact tracked at all.

2. **Multiple owned regions per struct.** RFC-0068 §8.1 defers whether a struct may
   declare more than one owned region (`[own r, own s]`). This RFC's default applies
   per-binding, not per-struct-declared-region, so it does not depend on that question
   being resolved, but the interaction should be revisited once RFC-0068 §8.1 is.

3. **Closures.** Whether a closure's captured bindings retain their own default region
   from the enclosing scope, or receive a fresh one scoped to the closure, is deferred
   until RFC-0050 (Closure Capture Lists, still in draft) is further along — the same
   open point as RFC-0086 §Unresolved Q3.

---

## References

- RFC-0063 (Region Handles) — the `Region` aspect and bracket channel this RFC's
  default own region participates in like any other region.
- RFC-0068 (Struct-Owned Regions) §1–§3 — the construction, implicit-scope, and "own"
  semantics this RFC generalizes from an opt-in struct declaration to a universal
  default; §8.1 — the still-deferred multiple-owned-region question noted in
  §Unresolved Q2.
- RFC-0069 (Sub-Region Typing) §3.1 — the ad hoc fallback this RFC replaces with a
  general rule; §3.3 — the transitive `Outlives` derivation this RFC's default regions
  participate in without modification.
- RFC-0085 (PhantomRegion) — the type used as the default backing, and specifically
  its mandatory-elision guarantee, which is what makes a universal default affordable.
- RFC-0086 (Outlives-of-Bindings Sugar) — the syntax that reads the fact this RFC
  establishes.
