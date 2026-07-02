---
id: rfc-0085
title: "PhantomRegion"
date: '2026-07-02'
---

> **Status — under review.** Depends on RFC-0063 (Region Handles), RFC-0073 (AutoRegion).
> Defines the `PhantomRegion` type only — a `Region` implementor whose allocations are
> unconditionally elided. It is infrastructure for RFC-0087 (Universal Own Regions),
> which gives every binding one of these by default, and RFC-0086 (Outlives-of-Bindings
> Sugar), which provides syntax to relate them. This RFC does not itself define any
> call-site inference or borrow-admission rule; earlier drafts did, and folding that
> responsibility into RFC-0087 instead is why they no longer appear here (see
> §Alternatives).

## Summary

`PhantomRegion` is an ordinary stdlib type implementing the `Region` aspect
(RFC-0063 §1.1), distinguished from `AutoRegion` by one additional, unconditional
guarantee: every allocation into a `PhantomRegion` is elided; none may ever produce
real backing storage.

```metel
// stdlib definition
struct PhantomRegion { /* compiler-managed; carries no runtime state */ }

impl Region for PhantomRegion {
    type AllocationError = !;
}
```

That guarantee is the entire content of this RFC. It exists as a building block: later
RFCs use "constructing a `PhantomRegion` is always free and has no observable effect"
to justify giving one to every binding by default (RFC-0087) and to let borrows be
related through it without ceremony (RFC-0086). This RFC does not attempt to solve the
borrow-relating ergonomics problem itself — it only establishes that the type doing so
is real, not phantom in the RFC-0052 sense, and costs nothing.

---

## Motivation

### Why a bare lifetime parameter is the wrong building block

Relating two independently-scoped borrows needs *some* nameable thing to hang an
`Outlives` bound on. Rust's answer, a bare lifetime parameter (`fn f<'a>(...)`), is not
backed by anything — not a value, not something constructed, not anything with even a
conceptual runtime presence. RFC-0063's own motivation section names this precisely as
the failure mode of the abandoned lifetime branch (RFC-0052): "the lifetimes were
phantom (nothing in scope you could point at)." Whatever mechanism ends up relating two
borrows in Metel needs to be a real region, not a second, parallel naming system.

### Why not just use `AutoRegion`

`AutoRegion` (RFC-0073) is only *permitted* to elide — the compiler may also choose
real stack, arena, or heap backing for a given allocation. Any later mechanism that
wants to treat "constructing this region" as unconditionally free, or wants to
retroactively relate an already-existing borrow to a region without moving or
reallocating anything, needs that to be *guaranteed*, not merely possible. Depending
on which strategy `AutoRegion` happens to pick for a given allocation is exactly the
unobservable implementation detail RFC-0073 says a program must not depend on
(§Design/Observational equivalence). A distinct type with mandatory elision as a fixed
contract avoids depending on that unobservable choice.

---

## Design

### 1. The `PhantomRegion` type

`PhantomRegion` implements `Region` with the same shape as `AutoRegion`
(RFC-0073 §Design) and adds exactly one restriction, stated as a mandatory compiler
obligation rather than a permitted latitude:

> **Mandatory elision.** Every `@[r] expr` where `r: PhantomRegion` must be elided —
> the compiler must not place the resulting value on the stack as an addressable slot,
> in an arena, or on the heap; the value must not have an observable address and must
> not outlive the expression that consumes it. If the compiler cannot prove elision is
> possible for a given allocation, that allocation is a compile error.

This is a strengthening, not a divergence, of RFC-0073 §Design/The compiler's
latitude, which already permits `AutoRegion` to "elide allocations entirely for values
that are immediately consumed and have no observable address." `PhantomRegion` takes
the one `AutoRegion` strategy that has zero runtime footprint and makes it the *only*
strategy, rather than one option among several.

```metel
fun scratch[r: PhantomRegion]() -> I64 {
    let n = @[r] Node { val: 1, next: null };   // ✓ — consumed immediately, elided
    n.val
}

fun leaky[r: PhantomRegion]() -> @[r] Node {
    @[r] Node { val: 1, next: null }             // ✗ — escapes; cannot be elided
}
```

```
error: allocation cannot be elided in a `PhantomRegion`
  --> src/main.mt:6:5
   |
6  |     @[r] Node { val: 1, next: null }
   |     ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ this value escapes the function
   |
   = note: `PhantomRegion` requires every allocation to be eliminated at compile time
   = help: use `AutoRegion` if the compiler should choose a real backing strategy,
           or `BumpRegion`/`Heap` for an explicit one
```

Because elision is mandatory rather than permitted, `PhantomRegion` inherits
RFC-0073's guarantees (soundness, drop completeness, drop ordering, move-out safety,
observational equivalence) as trivial consequences: an allocation proven to have no
observable address and no need to outlive its consuming expression has no distinct
drop obligation, ordering, or move-out case beyond what already applies to a plain
local value.

**Sendability.** `@[r] T` for `r: PhantomRegion` is never sendable, by the same rule as
`AutoRegion` (RFC-0073 §Sendability) — trivially, since nothing backed by a
`PhantomRegion` value can outlive the expression that produced it, let alone cross a
fiber boundary.

**Construction and use.** `PhantomRegion` is an ordinary region otherwise:
`PhantomRegion::new()`, `PhantomRegion::scoped([a]() -> { ... })`, and the bracket
channel all work exactly as they do for any other `Region` implementor. A bracket
parameter `[a: PhantomRegion]` is a fully explicit, standalone declaration a programmer
may still write directly — this RFC does not restrict its use to any particular
context. What later RFCs add is a *default* (RFC-0087) and *sugar* for referring to
that default (RFC-0086); neither changes what is written in this section.

---

## Alternatives considered

### Bare lifetime parameters (`'a`)

Rejected per §Motivation: reintroduces phantom annotations and a second, unrelated
naming system alongside regions.

### A usage-inferred "virtual" classification

An earlier draft of this proposal classified an ordinary bracket parameter `[a]` as
"virtual" purely from whether the function body ever wrote `@[a] expr`, with no new
stdlib type at all. Rejected: it made a parameter's capabilities an emergent, silently
revisable property of the function body rather than a fact visible at the declaration —
the exact kind of exception the bracket channel is meant to avoid. A concrete type
fixes this by making the guarantee a fact about the type, not about how a given
function happens to use a name.

### Folding call-site inference and borrow admission into this RFC

An earlier draft of this RFC also specified two call-site rules directly: automatic
construction of a `PhantomRegion` handle when a bracket parameter of that type was
omitted at a call site, and admission of an already-existing plain borrow into a
`PhantomRegion`-tagged reference type without requiring the referent to be literally
allocated there. Both rules were sound, but both existed only to serve one specific
use case — relating two ordinary function parameters — and reasoning about them
required treating "constructing a `PhantomRegion` is free" as license for two separate,
independently-justified exceptions to RFC-0065's ordinary call-site rules.

RFC-0087 replaces both with a single default: every binding, not just ones behind an
explicitly-declared bracket parameter, gets an owned `PhantomRegion` automatically.
Under that default, "construct one for me" and "let my existing borrow count as
already having one" are not separate rules to justify — they are true by construction
for every value, all the time. This RFC keeps only the piece both of those rules
depended on: that `PhantomRegion` is safe to construct and relate without runtime
consequence in the first place.

---

## Unresolved questions

1. **Struct and impl-block `PhantomRegion` parameters as an explicit choice.** A
   struct or impl block may declare `[a: PhantomRegion]` explicitly today, the same as
   any other region-typed bracket parameter. Whether there is a distinct ergonomic gap
   here once RFC-0087's default exists is deferred until that RFC's own scope
   (functions and bindings, not struct fields) is evaluated in practice.

2. **Closures capturing `PhantomRegion`-tagged borrows.** Whether a closure may itself
   declare `[a: PhantomRegion]` in its capture-list bracket channel is deferred until
   RFC-0050 (Closure Capture Lists, still in draft) is further along.

---

## References

- RFC-0063 (Region Handles) §1.1 — the `Region` aspect this RFC implements; the
  compile-time-only identity of the region system that makes mandatory elision a
  coherent guarantee rather than a special case.
- RFC-0073 (AutoRegion) — the permitted-elision guarantee this RFC strengthens into a
  mandatory one; the five guarantees `PhantomRegion` inherits as trivial consequences;
  the non-sendability rule reused unchanged.
- RFC-0087 (Universal Own Regions) — uses this type as the default backing for every
  binding's implicit own region.
- RFC-0086 (Outlives-of-Bindings Sugar) — the syntax for relating the regions RFC-0087
  gives every binding by default.
