---
id: rfc-0096
title: "Auto-Impl Aspects — Compiler-Recognized Structural Aspects"
date: '2026-07-11'
status: draft
target:
---

> **New RFC.** Created despite `rfc.py new`'s overlap warning against RFC-0080, 0061,
> 0093, 0060, and 0081 — checked each first. None of them own this mechanism: RFC-0080
> §3.2/§4.2 and the draft RFC-0089 §2 each independently invoke "the auto-impl pattern"
> for a specific aspect (`Send`, `Sync`, `Linear`) without ever specifying, once, what
> that pattern *is* as a general mechanism; RFC-0061 §5 assumes the same rule propagates
> through arrays without saying where it's defined; RFC-0093 explicitly *excludes*
> auto-impl aspects from its own scope (§2: "`Linear` does not belong on this list...
> no `@derive(Linear)` annotation is needed or meaningful"). This RFC is the missing
> piece those four all assume exists.

## Summary

Three aspects — `Send`, `Sync` (RFC-0080), and `Linear` (RFC-0089, draft) — are
**auto-impl**: the compiler grants them to a type automatically, based on the type's
structure, with no `impl` block and no `@derive` annotation written anywhere. Every
RFC that uses this pattern cites RFC-0080 §3.2 as precedent but none of them — including
RFC-0080 itself — specifies two things this RFC settles:

1. **How the compiler recognizes that a given aspect *is* auto-impl at all.** `AspectDecl`
   has no marker field for it (confirmed empty during issue #238's implementation), and
   no RFC proposes adding one.
2. **The structural-composition algorithm**, stated once instead of three times: how
   "every field is `Send`" generalizes to structs, enums, arrays (RFC-0061 §5), and
   references, and what varies per-aspect versus what's shared.

This RFC does not change what `Send`/`Sync`/`Linear` compute — RFC-0080 §3.2/§4.2 and
RFC-0089 §2's rules are unchanged and are not repeated in full here. It answers *why*
those rules are structured the way they are and *where* a fourth auto-impl aspect,
if one is ever proposed, would have to be added.

---

## Motivation

Grep the accepted and draft RFC corpus for "auto-impl" and three documents assume a
mechanism that's never been written down:

- RFC-0080 §3.2: "`Send` is an auto-aspect: the compiler automatically derives `Send`
  for any type all of whose fields are `Send`." States the rule for `Send` specifically,
  not a general mechanism.
- RFC-0089 §2 (draft): "`Linear`... is an auto-impl aspect, structurally identical in
  category to `Send`/`Sync` (RFC-0080 §3.2's rule)." Explicitly says "same category,"
  which only means something if the category is defined somewhere — it isn't.
  RFC-0093 §2 makes the negative case explicit: `Linear` was *mistakenly* placed on
  the derivable-aspects list in an earlier revision and had to be corrected out, which
  is exactly the kind of mistake a missing formal category invites.
- RFC-0061 §5: "`Send`, `Sync`, and `Drop` propagate through `T[]` structurally via the
  RFC-0060 §4 auto-impl rule" — but RFC-0060 (Aspect Impl Coherence) is about orphan
  rules and overlap detection; it does not define an auto-impl rule at all. This
  citation points at a mechanism that exists in nobody's document.

Without this RFC, a future author proposing a fourth auto-impl aspect has no single
place to check "does this qualify," "what has to be specified," or "what part of the
mechanism is shared versus aspect-specific" — they'd have to reverse-engineer the
answer from three RFCs that each assumed someone else had written it down.

---

## 1. Recognition: a closed, compiler-intrinsic list — not a declaration-level marker

An aspect is auto-impl because the compiler's own source recognizes its identity, the
same way `i64`, `String`, and the rest of `SymbolTable`'s seeded entries are recognized
as primitive types with no textual `struct`/`enum` declaration anywhere (confirmed
during issue #238: primitives need no special-casing in coherence checking precisely
*because* they're ordinary `(std::core, name) -> SymbolId` table entries, not because
of any flag on the entry). Auto-impl aspects are the same kind of fact: `Send`, `Sync`,
and `Linear` are auto-impl because the compiler's aspect-satisfaction check special-
cases those three identities, not because `aspect Send { }`'s declaration in
`stdlib/core.mtl` carries a marker distinguishing it from an ordinary marker aspect.

**This RFC does not add syntax.** `AspectDecl` gains no new field. There is no surface
spelling — no attribute, no keyword — by which a user's own `aspect` declaration could
opt into auto-impl. This is a deliberate design decision, not an oversight this RFC
forgot to fix:

- Every auto-impl aspect proposed anywhere in the RFC corpus (`Send`, `Sync`, `Linear`)
  is a standard-library aspect with compiler-known semantics — sendability and
  linearity are properties the compiler itself reasons about elsewhere (fiber
  boundaries, move/drop checking), not arbitrary user semantics being generalized.
- RFC-0093 already provides the extensible path for "I want this generated
  structurally": `@derive(Aspect)`, resolved through a registered comptime function.
  A hypothetical user-defined auto-impl aspect would have no comptime function to
  register against — auto-impl doesn't ask permission at any use site, it always
  applies — so it cannot be expressed through RFC-0093's mechanism even in principle.
  Making auto-impl user-extensible would require a second, separate extension point
  purely for this, with no motivating use case anywhere in the accepted corpus.

A fourth auto-impl aspect is therefore added to the language the same way a fourth
primitive type would be: by changing the compiler's own source (the recognition list
and the structural rule below), not by a user or library writing a declaration that
requests it.

---

## 2. The shared structural-composition algorithm

Every auto-impl aspect `A` is checked via the same recursive shape, parameterized only
by `A`'s own per-position rule:

```
satisfies(A, T):
    if T is a primitive type:
        return A's primitive rule (for Send/Sync: always true; RFC-0080 §3.1/§4.1)
    if T is a struct or enum:
        return all(satisfies(A, field_type) for field_type in T's fields
                   (all variants' fields, for an enum))
    if T is an array T'[]:
        return satisfies(A, T')                          (RFC-0061 §5)
    if T is &U or &mut U:
        return A's reference rule, applied to U           (aspect-specific — see below)
    otherwise (structural type with no auto-impl rule defined for A):
        A does not apply to T
```

**What's shared:** the traversal itself — recurse into every field of a struct/enum,
every variant of an enum, the element type of an array — terminating at primitives.
This is the piece three RFCs each assumed without stating.

**What's aspect-specific:** the primitive rule and the reference rule. `Send`'s
reference rule and `Sync`'s reference rule are *not* the same function applied to
different aspects — RFC-0080 §3.2 has `&T: Send` iff `T: Sync` (crossing a reference
boundary flips which aspect is being asked about), while §4.2 has `&T: Sync` iff
`T: Sync` (no flip). A future auto-impl aspect must state its own primitive rule and
reference rule explicitly in its own RFC; this RFC does not supply a default for
either, because `Send`/`Sync` already demonstrate the default isn't always "same
aspect, no change."

This RFC does not re-derive or restate `Send`/`Sync`/`Linear`'s actual rules —
RFC-0080 §3.2/§4.2 and RFC-0089 §2 remain the canonical source for those. This section
only names the shared shape so a future RFC proposing a new auto-impl aspect can point
at one place instead of pattern-matching against three.

---

## 3. Coherence

An auto-impl is an ordinary positive impl for coherence purposes: overlap detection
(T0015) and negative-impl override (RFC-0081) both apply to it exactly as they would
to an explicit `impl` block. This is already stated in `declarations.md`'s "Aspect
Implementation Coherence" section (integrated from RFC-0060) and is not changed here.
The orphan rule (RFC-0060 §1) does not apply to auto-impls at all — there is no impl
site to check locality against; the compiler synthesizes the impl wherever the type is
defined, by construction.

---

## 4. What this doesn't cover

- **A general "derive this structurally" mechanism for user aspects.** That's
  RFC-0093 (`@derive(Aspect)`), a distinct, separately-invoked mechanism. See §1 for
  why the two don't merge.
- **Adding a fifth auto-impl aspect.** This RFC establishes where such a proposal
  would live (compiler-recognized identity + this section's algorithm, instantiated
  with that aspect's own primitive/reference rules) — it does not itself propose one.
- **Structural types beyond arrays** (tuples, function types) propagating auto-impl
  aspects. RFC-0061 §6 defers tuples generally; this RFC inherits that gap rather than
  resolving it.

---

## Unresolved Questions

1. **Enum variants with no fields.** A unit variant trivially satisfies any auto-impl
   aspect (the `all(...)` over zero fields is vacuously true) — worth stating
   explicitly once implementation begins, so it isn't rediscovered as a special case.

---

## References

- RFC-0080 (Standard Library Aspects) — `Send`/`Sync`'s own auto-impl rules (§3.2,
  §4.2), unchanged by this RFC; the pattern this RFC generalizes.
- RFC-0089 (Linear Types, draft) — `Linear` as the third auto-impl aspect (§2); the
  citation that made the missing shared definition visible.
- RFC-0093 (Derive Registration) — the user-invoked `@derive(Aspect)` mechanism this
  RFC deliberately does not merge with; §2's correction of `Linear`'s earlier
  mis-classification motivates this RFC's §1.
- RFC-0061 (Structural Aspect Bounds) — array propagation of auto-impl aspects (§5),
  cited here as the array case of §2's shared algorithm.
- RFC-0060 (Aspect Impl Coherence) — overlap detection and orphan rule; §3 states how
  auto-impls participate in coherence (as ordinary positive impls, orphan rule
  inapplicable).
- RFC-0081 (Negative Impls) — the override mechanism for opting a type out of an
  auto-impl rule that would otherwise apply.
- Issue #238 / `src/coherence.rs` — where the absence of an `AspectDecl` auto-impl
  marker was confirmed empty by direct inspection, motivating §1's design decision.

---

## Decision

**Outcome:** *(pending)*
**Target:** *(set when accepted)*
