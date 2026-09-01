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
> no `#derive(Linear)` annotation is needed or meaningful"). This RFC is the missing
> piece those four all assume exists.
>
> **Correction (2026-07-11, later the same day):** §1's original text claimed the
> auto-impl list was closed at exactly these three. Wrong — RFC-0090 (Structural
> Records) §1 independently calls `HasField`/`Lacks` "an extension of RFC-0080's
> auto-impl pattern," a fifth document assuming this mechanism, missed on the first
> pass because RFC-0090 sits in a different INDEX.md cluster than RFC-0080/0089/0061.
> §1, §6, References, and Unresolved Question 5 corrected; new §7 explains why
> `HasField`/`Lacks` is related but not simply a fourth instance of §2's algorithm.

## Summary

Three aspects — `Send`, `Sync` (RFC-0080), and `Linear` (RFC-0089, draft) — are
**auto-impl**: the compiler grants them to a type automatically, based on the type's
structure, with no `impl` block and no `#derive` annotation written anywhere. Every
RFC that uses this pattern cites RFC-0080 §3.2 as precedent but none of them — including
RFC-0080 itself — specifies what this RFC settles:

1. **How the compiler recognizes that a given aspect *is* auto-impl at all** (§1).
   `AspectDecl` has no marker field for it (confirmed empty during issue #542's
   implementation), and no RFC proposes adding one.
2. **The structural-composition algorithm** (§2), stated once instead of three times:
   how "every field is `Send`" generalizes to structs, enums, arrays (RFC-0061 §5),
   function pointers, and references, and what varies per-aspect versus what's shared.
3. **How the algorithm applies to generic types** (§3), which it is never actually
   evaluated against directly — an auto-impl on `struct Pair<A, B>` is an implicit,
   compiler-synthesized conditional impl (RFC-0036), not a single eager classification.
4. **That `Drop` is not a fourth member of this set** (§4), correcting a plausible
   misreading of RFC-0061 §5's heading against already-accepted behavior (RFC-0071 §3).
5. **That `HasField`/`Lacks` (RFC-0090) is related but not a fourth *fixed-marker*
   member either** (§7) — a family with an existential satisfaction rule, structurally
   unlike §2's algorithm, and possibly outside the aspect/impl system entirely.

This RFC does not change what `Send`/`Sync`/`Linear` compute — RFC-0080 §3.2/§4.2 and
RFC-0089 §2's rules are unchanged and are not repeated in full here. It answers *why*
those rules are structured the way they are, *how* they extend to generic types no
existing RFC addresses, and *where* a fourth true auto-impl aspect, if one is ever
proposed, would have to be added.

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

## 1. Recognition: a closed, compiler-intrinsic list for single marker aspects

An aspect is auto-impl because the compiler's own source recognizes its identity, the
same way `i64`, `String`, and the rest of `SymbolTable`'s seeded entries are recognized
as primitive types with no textual `struct`/`enum` declaration anywhere (confirmed
during issue #542: primitives need no special-casing in coherence checking precisely
*because* they're ordinary `(std::core, name) -> SymbolId` table entries, not because
of any flag on the entry). Auto-impl aspects are the same kind of fact: `Send`, `Sync`,
and `Linear` are auto-impl because the compiler's aspect-satisfaction check special-
cases those three identities, not because `aspect Send { }`'s declaration in
`stdlib/core.mtl` carries a marker distinguishing it from an ordinary marker aspect.

**This RFC does not add syntax.** `AspectDecl` gains no new field. There is no surface
spelling — no attribute, no keyword — by which a user's own `aspect` declaration could
opt into auto-impl. This is a deliberate design decision, not an oversight this RFC
forgot to fix:

- Every single, fixed marker aspect proposed anywhere in the RFC corpus (`Send`,
  `Sync`, `Linear`) is a standard-library aspect with compiler-known semantics —
  sendability and linearity are properties the compiler itself reasons about
  elsewhere (fiber boundaries, move/drop checking), not arbitrary user semantics
  being generalized. (`HasField`/`Lacks`, RFC-0090, is *not* a fixed marker aspect at
  all — it's a parameterized family with a different satisfaction shape; see §7. It
  doesn't reopen this bullet's point, since it isn't a counterexample to "fixed
  marker aspects stay closed" — it was never in that category.)
- RFC-0093 already provides the extensible path for "I want this generated
  structurally": `#derive(Aspect)`, resolved through a registered comptime function.
  A hypothetical user-defined auto-impl aspect would have no comptime function to
  register against — auto-impl doesn't ask permission at any use site, it always
  applies — so it cannot be expressed through RFC-0093's mechanism even in principle.
  Making auto-impl user-extensible would require a second, separate extension point
  purely for this, with no motivating use case anywhere in the accepted corpus.

A fourth *fixed marker* auto-impl aspect is therefore added to the language the same
way a fourth primitive type would be: by changing the compiler's own source (the
recognition list and the structural rule below), not by a user or library writing a
declaration that requests it. This says nothing about families like `HasField` — §7
covers those on their own terms, not as an exception carved out of this rule.

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
        return satisfies(A, T')                          (RFC-0061 §5.1/§5.2)
    if T is &U or &mut U:
        return A's reference rule, applied to U           (aspect-specific — see below)
    if T is fun(...) -> _  (a bare function pointer, not a closure):
        return A's function-pointer rule — typically a fixed constant, not a
        recursion, since a bare function pointer carries no captured state to
        recurse into (RFC-0061 §7.2: Send/Sync both unconditionally `Yes`)
    otherwise (structural type with no auto-impl rule defined for A):
        A does not apply to T
```

**What's shared:** the traversal itself — recurse into every field of a struct/enum,
every variant of an enum, the element type of an array — terminating at primitives.
This is the piece three RFCs each assumed without stating.

**What's aspect-specific:** the primitive rule, the reference rule, and the
function-pointer rule. `Send`'s reference rule and `Sync`'s reference rule are *not*
the same function applied to different aspects — RFC-0080 §3.2 has `&T: Send` iff
`T: Sync` (crossing a reference boundary flips which aspect is being asked about),
while §4.2 has `&T: Sync` iff `T: Sync` (no flip). A future auto-impl aspect must
state its own primitive rule, reference rule, and function-pointer rule explicitly in
its own RFC; this RFC does not supply a default for any of the three, because
`Send`/`Sync` already demonstrate the default isn't always "same aspect, no change."
`Linear` (RFC-0089) does not state a reference rule at all — see Unresolved Question 3.

This RFC does not re-derive or restate `Send`/`Sync`/`Linear`'s actual rules —
RFC-0080 §3.2/§4.2 and RFC-0089 §2 remain the canonical source for those. This section
only names the shared shape so a future RFC proposing a new auto-impl aspect can point
at one place instead of pattern-matching against three.

---

## 3. Generic types: an auto-impl is an implicit conditional impl

§2's algorithm is written as if `T` is always fully concrete. It isn't — most real
uses involve a generic struct or enum:

```metel
struct Pair<A, B> { a: A, b: B }
```

`Pair`'s own declaration has no concrete `A`/`B` to recurse into, so `satisfies(Send,
Pair<A, B>)` cannot be decided once, eagerly, at the struct's declaration site. An
auto-impl on a generic type is equivalent to an implicit, compiler-synthesized
**conditional impl** (RFC-0036) that is never spelled by any author:

```metel
// never written by anyone; the compiler behaves as if this exists
extend<A: Send, B: Send> Pair<A, B>: Send { }
```

and it is checked exactly the way RFC-0036 §2.1 checks any conditional impl: at every
point the aspect is actually required — a bound check, a fiber-crossing call, another
auto-impl's own recursive descent into `Pair` as someone else's field — using whatever
bounds are in scope at that point, not resolved once at `Pair`'s declaration.

Concretely, inside generic code:

```metel
fun send_it<T: Send>(x: Pair<T, i64>) {
    cross_fiber(x);   // ok — Pair<T, i64>: Send, because T: Send and i64: Send
}

fun send_it_unbounded<T>(x: Pair<T, i64>) {
    cross_fiber(x);   // error — T carries no Send bound; the auto-impl's
                       // condition on A is not established in this scope
}
```

matching RFC-0036 §2.3: the compiler does not infer which bounds a generic function
needs for its auto-impl-dependent operations to type-check — the author states them,
same as for any other conditional impl. Auto-impl means the *impl itself* is never
written by hand; it does not mean generic code is exempt from stating the conditions
under which it holds.

**Concrete instantiations need no bound lookup at all** — `Pair<Handle, i64>` (with
`Handle: !Send`, say) is resolved by direct recursive evaluation of §2's algorithm
against the concrete field types, with no generic machinery involved. The conditional-
impl framing above only matters when `T`'s own concrete type isn't known yet at the
point being checked.

---

## 4. `Drop` is not a fourth instance of this pattern

RFC-0061 §5 groups `Send`, `Sync`, and `Drop` together under one heading, "Auto-Impl
Propagation," for arrays. Taken at face value alongside RFC-0080/RFC-0089, this reads
as if `Drop` is a fourth auto-impl aspect belonging in §1's recognized set. It is not,
and conflating the two would misstate already-accepted behavior:

- **For structs and enums, `Drop` is opt-in — never auto-derived.** RFC-0071 §3 is
  explicit: "Types without a `Drop` impl are reclaimed by recursively dropping their
  fields, with no user-defined logic." A struct containing a `Drop` field does *not*
  thereby satisfy `T: Drop` as a bound — its fields are unconditionally dropped in
  declaration order regardless, but the struct itself only gains a `Drop` impl (and
  the ability to run its own destructor logic, per RFC-0071 §3's example) if a user
  writes `extend Struct: Drop` by hand. Running §2's `satisfies` algorithm for `Drop`
  against a struct would give the wrong answer.
- **RFC-0061 §5.3's array rule is a narrow, deliberate exception, not a generalization.**
  `T[]: Drop` is auto-derived when `T: Drop` specifically because arrays cannot receive
  a user-written `extend T[]: Drop` at all (structural types are `std::core`-owned for
  orphan-rule purposes, RFC-0061 §1) — the only way `T[]: !Drop` can ever be
  established, which RFC-0066 §2.2's move-out-of-region permission needs, is
  structurally. This necessity does not exist for structs and enums, which can always
  receive an explicit `impl Drop`, so nothing forces (or permits) the same structural
  shortcut there.

`Send`, `Sync`, and `Linear` are true instances of this RFC's mechanism: the compiler
grants the aspect itself, as an ordinary positive impl (§5, below), to *any* structurally
qualifying type, struct/enum included. `Drop`'s array rule instead answers a narrower
question — whether resources need cleaning up — using the same recursive shape by
coincidence of arrays' constrained position, not because `Drop` joined the recognized
set in §1. RFC-0061 §5's heading should be read with this distinction in mind; a
follow-up documentation fix narrowing that heading (or splitting `Drop`'s subsection out
from "Auto-Impl Propagation") is tracked as Unresolved Question 4 rather than made here,
to keep this RFC's own diff from touching an already-accepted RFC's structure.

---

## 5. Coherence

An auto-impl is an ordinary positive impl for coherence purposes: overlap detection
(T0015) and negative-impl override (RFC-0081) both apply to it exactly as they would
to an explicit `impl` block. This is already stated in `declarations.md`'s "Aspect
Implementation Coherence" section (integrated from RFC-0060) and is not changed here.
The orphan rule (RFC-0060 §1) does not apply to auto-impls at all — there is no impl
site to check locality against; the compiler synthesizes the impl wherever the type is
defined, by construction.

---

## 6. What this doesn't cover

- **A general "derive this structurally" mechanism for user aspects.** That's
  RFC-0093 (`#derive(Aspect)`), a distinct, separately-invoked mechanism. See §1 for
  why the two don't merge.
- **Adding a fourth *fixed marker* auto-impl aspect (beyond `Send`/`Sync`/`Linear`).**
  This RFC establishes where such a proposal would live (compiler-recognized identity
  + §2's algorithm, instantiated with that aspect's own primitive/reference/
  function-pointer rules) — it does not itself propose one. (`HasField`/`Lacks` is
  not this — see §7.) Whether *this* category should stay closed at exactly three is
  Unresolved Question 5.
- **Tuples.** RFC-0061 §6 defers all tuple aspect impls, auto-impl included, pending a
  per-arity or variadic-generics design; this RFC inherits that gap rather than
  resolving it. (Function pointers are *not* in this category — see below.)
- **Raw pointer types** (`Pointer`/`MutPointer` in the AST — not RFC-0080's region
  pointers `@[r] T`, which have their own bespoke, region-dependent rule at RFC-0080
  §3.4/§4.3, nor closures, covered below). No RFC states a `satisfies` rule for these
  at all; see Unresolved Question 2.
- **Closures' captured-state rule.** *Not* an open gap — RFC-0050 §"Interaction with
  concurrency" already independently derives "a closure is `Send` only if all its
  captured values are `Send`," which is exactly §2's struct/enum case applied to a
  closure's anonymous capture record. It arrived at the same rule this RFC states
  generically without citing a shared source — a fourth instance of the pattern this
  RFC's Motivation describes, found while drafting this section. Worth a cross-link
  from RFC-0050 to this RFC once accepted, but no content of RFC-0050's own is wrong.

---

## 7. `HasField`/`Lacks`: a related but distinct case

RFC-0090 §1 calls `HasField<"name", T>`/`Lacks<"name">` "an extension of RFC-0080's
auto-impl pattern: one marker aspect *family* instead of one aspect, same machinery."
That's right in spirit — no `impl`, no `#derive`, structural satisfaction — but wrong
in one respect worth naming precisely: it is not "the same machinery" as §2's
algorithm, and treating it as a fourth instance of §1's closed list would be a
category error in the other direction from `Drop`'s (§4).

**It's a family, not a fixed aspect.** `Send` is one aspect, checked once. `HasField`
is parameterized over an arbitrary field-name *and* an arbitrary type — an unbounded
number of distinct bounds (`HasField<"x", f64>`, `HasField<"token", String>`, ...),
not a fixed identity a compiler `match` could enumerate the way `SYM_ASPECT_SEND`
does. §1's "closed list" framing describes *fixed marker aspects*; `HasField` was
never a candidate for that list, not an exception carved out of it.

**Its satisfaction rule is existential, not universal.** §2's algorithm is
`all(satisfies(A, field) for field in T's fields)` — *every* field must qualify.
`HasField<"x", f64>`'s rule is "does `T` have *a* field named `x` of type `f64`" —
one specific, named field checked for presence, not every field checked against a
recursive condition. These are different quantifiers over the same `typeinfo`/row
data, not one algorithm parameterized two ways.

**It may not go through the aspect/impl system at all.** `Send`/`Sync`/`Linear` are
each a real `aspect` declaration in `stdlib/core.mtl` that the compiler recognizes by
identity and then substitutes §2's algorithm for the normal impl lookup. RFC-0090
never shows a textual `aspect HasField<Name, T> { }` declaration anywhere, and
explicitly states Tier 2 (`derives ToRecord, FromRecord`) has "no impl or coherence
exposure." That suggests `HasField`/`Lacks` bounds may be checked directly against a
type's row by the typechecker, never entering `impl_aspect_env`/coherence at all —
in which case it sits *outside* the category this RFC recognizes, rather than being
governed by it. RFC-0090 does not settle this explicitly either; not resolved here.

**A further, unrelated observation made while checking this:** `HasField<"x", f64>`'s
own bound-position syntax (RFC-0090's worked examples, e.g. `T: HasField<"x", f64>`)
puts a string literal (`"x"`) where `grammar.md`'s `BoundList → Type ("+" Type)*`
only ever allows a `Type`. Nothing in RFC-0090, RFC-0036, or this RFC's own review
extends the grammar to admit a literal argument in bound position. This is a gap in
RFC-0090's own syntax, not this RFC's mechanism — flagged here only because it was
noticed in the course of checking whether `HasField` belongs in §1's list, not
because this RFC is the right place to resolve it.

---

## Unresolved Questions

1. **Enum variants with no fields.** A unit variant trivially satisfies any auto-impl
   aspect (the `all(...)` over zero fields is vacuously true) — worth stating
   explicitly once implementation begins, so it isn't rediscovered as a special case.

2. **Raw pointer types have no stated rule anywhere.** `Pointer`/`MutPointer` fall
   into §2's `otherwise` branch by default (no rule defined, so no auto-impl aspect
   ever applies to them structurally) — but no RFC has ever said this is the intended
   behavior versus an oversight. Given raw pointers carry no compiler-tracked aliasing
   information, "never auto-derived, always requires an explicit (likely `unsafe`)
   impl" is the plausible answer, but it should be stated by whichever RFC actually
   specifies raw pointers' semantics, not assumed silently here.

3. **`Linear` states no reference rule.** RFC-0089 §2 never says whether `&T`/`&var T`
   is ever `Linear` for any `T`. Intuitively no — a reference borrows without owning
   the underlying multiplicity-1 resource, so multiplicity shouldn't transfer through
   a reference at all — but §2 of *this* RFC requires every auto-impl aspect to state
   its own reference rule explicitly, and RFC-0089 doesn't. This RFC does not resolve
   RFC-0089's gap on its behalf; flagged here so RFC-0089 picks it up before acceptance.

4. **RFC-0061 §5's heading conflates `Drop` with the true auto-impl aspects.** §4
   above explains why `Drop`'s array-only rule isn't a fourth instance of this
   mechanism. Whether to retitle RFC-0061 §5 (e.g. splitting `Drop` into its own
   subsection outside "Auto-Impl Propagation") is a documentation fix to an
   already-accepted RFC, deliberately left for a separate, focused change rather than
   folded into this RFC's own acceptance.

5. **Is the *fixed-marker* auto-impl category expected to grow past three?**
   (Originally asked as "is the auto-impl list expected to grow past three" — answer
   turned out to be yes in a different sense: `HasField`/`Lacks` already extends the
   *pattern*, but as a family, not a fourth fixed marker, per §7. The question as
   originally meant — a fourth `Send`-shaped single aspect — is still open.) §1 argues
   this narrower category is closed because every proposed member so far is a
   standard-library aspect with compiler-known semantics (fiber-safety, linearity)
   rather than arbitrary user semantics. If a real fourth fixed-marker candidate is
   ever proposed, whether the *compiler's* internal representation should be a
   hardcoded match over exactly `{Send, Sync, Linear}` or an open (but still
   user-inaccessible) internal registry is an implementation choice this RFC does not
   need to settle in advance.

6. **Does `HasField`/`Lacks` go through the aspect/impl coherence system at all?**
   §7 flags this as unresolved by RFC-0090 itself. If it does, RFC-0097's
   bare-parameter orphan-rule work may need a family-aware generalization (a
   `HasField<"x", T>` impl's "target" is arguably the field-name literal, which fits
   neither this RFC's nor RFC-0097's notion of a target type at all). If it doesn't,
   this RFC's own recognition category (§1) is simply inapplicable to it, and no
   further coordination is needed. Belongs to whichever RFC ends up specifying
   `HasField`'s own coherence story, not decided here.

7. **RFC-0105 (draft) surfaces a concrete implementation requirement on this RFC,
   inherited from the split-out struct/enum-embedded aspect-list
   obligation model.** §5 above already says "an auto-impl is an ordinary positive
   impl for coherence purposes" — RFC-0105 takes that literally: each auto-impl
   determination (`Send`/`Sync`/`Linear`) must be made visible through the *same*
   aspect-implementation registry an ordinary `extend` block populates (a real
   registered entry — for a generic type, the conditional-impl-bounds entry §3 above
   already describes as the intended shape), not merely through a `satisfies(A, T)`
   query consulted only by direct bound-checking. Without this, RFC-0105's own
   obligation check would have no way to discharge a struct/enum-embedded positive
   `Send`/`Sync`/`Linear` item — no `extend` block for those aspects is ever written,
   so a registry-based lookup finds nothing unless this RFC's implementation puts an
   entry there itself. This RFC's own §5 already implies the answer; this question
   just makes the implementation obligation explicit before this RFC is accepted,
   rather than leaving it implicit in a sentence about coherence.

---

## References

- RFC-0080 (Standard Library Aspects) — `Send`/`Sync`'s own auto-impl rules (§3.1-
  §3.2, §4.1-§4.2), unchanged by this RFC; the pattern this RFC generalizes. §7.2
  (via RFC-0061) supplies the function-pointer rule cited in §2.
- RFC-0089 (Linear Types) — `Linear` as the third auto-impl aspect (§2); the
  citation that made the missing shared definition visible. Does not state a
  reference rule (Unresolved Question 3).
- RFC-0093 (Derive Registration) — the user-invoked `#derive(Aspect)` mechanism this
  RFC deliberately does not merge with; §2's correction of `Linear`'s earlier
  mis-classification motivates this RFC's §1.
- RFC-0061 (Structural Aspect Bounds) — array propagation of `Send`/`Sync` (§5.1-5.2,
  the array case of §2's shared algorithm) and function-pointer rules (§7.2, §2's
  function-pointer case); §5.3's `Drop` rule is the subject of this RFC's §4.
- RFC-0060 (Aspect Impl Coherence) — overlap detection and orphan rule; this RFC's
  own §5 states how auto-impls participate in coherence (as ordinary positive impls,
  orphan rule inapplicable).
- RFC-0081 (Negative Impls) — the override mechanism for opting a type out of an
  auto-impl rule that would otherwise apply.
- RFC-0036 (Conditional Impl Blocks) — §3's use-site checking model, which §3 of this
  RFC relies on directly to explain auto-impl for generic types.
- RFC-0071 (Ownership and Move Semantics) — §3's "Drop is opt-in, fields still drop
  recursively" rule, the basis for this RFC's §4 correction.
- RFC-0050 (Closure Capture Lists, `2-accepted` as of 2026-09-01) — independently derives
  the same captured-state `Send` rule this RFC's §6 names as a fourth, uncited instance of
  the pattern.
- Issue #542 / `src/coherence.rs` — where the absence of an `AspectDecl` auto-impl
  marker was confirmed empty by direct inspection, motivating §1's design decision.
- RFC-0090 (Structural Records) — §1's `HasField`/`Lacks` auto-derivation,
  the fifth document assuming this RFC's pattern, missed on the first drafting pass;
  the subject of this RFC's §7.
- RFC-0105 (Struct-Embedded Aspect Lists, draft) — inherits the split-out requirement
  originally developed while RFC-0103 still bundled this syntax: auto-impl determinations
  must be injected into the same
  aspect-implementation registry ordinary `extend` blocks populate, not exposed only
  via a `satisfies`-style query, so RFC-0105's struct/enum-embedded obligation check
  never needs to special-case `Send`/`Sync`/`Linear` by name.

---

## Decision

**Outcome:** *(pending)*
**Target:** *(set when accepted)*
