---
id: allocators-as-emergent-synthesis
title: "Allocators as an Emergent Synthesis, Not a Primitive"
type: report
status: active
last_synced_against_model: '2026-07-20'
supersedes: null
revives: null
---

# Allocators as an Emergent Synthesis, Not a Primitive

*Living document — updated in place, not a point-in-time snapshot.*

*Exploration, not a decision. Nothing here is ratified, and nothing here refuses or
supersedes the allocator RFC cluster (RFC-0063/0065/0066/0067/0068/0073/0077) — see
§6 for why keeping those intact is load-bearing to this very argument. This document
proposes that the allocator feature, as currently designed, is largely a **synthesis
of more primitive features** — context parameters, brands, an owned box type, and the
borrow checker — rather than a foundational feature in its own right, and works out
what follows for sequencing and for a real narrowness risk in the current design. It
is the direct continuation of `brand-kind-unification.md`, which already established
one half of the claim (that `@a` allocator tags are a brand role); read that first.*

---

## 1. The thesis

The current allocator design (RFC-0063 and its cluster) is a single, standalone,
paper-complete feature: the `Alloc` aspect, the `@a T` owned-and-tagged type, the
`@a expr` allocation form, allocator parameters `(@a: A)` in the value channel,
tag-only parameters `<@a>`, disjointness, sendability, and the lifetime-anchor
interaction that lets the borrow checker prove a value doesn't outlive its allocator.

**Decompose it against features that either exist, are planned, or are conspicuously
absent, and very little that is genuinely allocator-specific remains.** Each column
below is a *general* capability; "allocators" is what you get when you point all of
them at storage:

| Allocator machinery | General feature it's an instance of | Status of that general feature |
|---|---|---|
| `(@a: A)` param + elision + §1b call-site inference | **context parameters** (Kotlin-style: a value a call tree needs, resolved by type from scope, ambiguity is an error) | **no RFC exists at all** |
| `@a T`'s instance-level tag; disjointness; sendability; provenance | **brands** (`'c`) — per-instance rigid erased identity | draft (RFC-0076), unsettled |
| `@a T` being owned/affine/moved, extracted via RFC-0066 | an owned **`Box`-like** pointer type + the **borrow checker** checking it outlives `a` | borrow checker unbuilt; box type unspecified |
| `@a expr` → `a.alloc(expr)`; the `Alloc` aspect; the four stdlib allocators | an **ordinary aspect** + library values implementing it | aspects implemented; this part is just library code |

If this holds, "allocators" is not a language primitive. It is context-parameters +
brands + box + borrow-checker, aimed at storage, with a thin library (`Alloc`) on top
and some sugar (`@`) over the seams.

---

## 2. Being precise about which half each primitive replaces

The seductive-but-wrong version of this thesis is "context parameters could replace
allocators." They cannot, on their own — and getting this precise is what separates a
real simplification from an over-unification.

**Context parameters replace the *threading*, and nothing else.** A Kotlin context
parameter is resolved by type from scope, is shared (borrow-shaped), and is *not*
affine or move-tracked. That describes the allocator *handle* `a` being passed down a
call tree exactly. It describes the allocated *values* `@a T` not at all — those are
owned, affine, and move-tracked, which is the box + brand + borrow-checker column, not
the context-parameter column. So context parameters retire the `(@a: A)` ergonomics
(and everything RFC-0065 §1/§1b spend their effort on) and stop there.

**Brands replace the *tag*, and this is `Box<T, instance-brand>`, not
`Box<T, AllocType>`.** Rust's `Box<T, A>` parameterizes over an allocator *type*.
Metel's `@a T` parameterizes over an allocator *instance* — two `BumpAlloc` instances
give distinguishable tags. That instance-vs-type distinction is not incidental; it *is*
the reason brands have to exist as their own kind (`brand-kind-unification.md` §1 makes
exactly this point from the other direction). So the correct framing of the user
observation "allocators become `Box<T, allocatorBrand>`" is precise and right, with the
word *brand* — not *type* — carrying the whole load. `@a T` = an owned box of `T`
carrying the brand of instance `a`; disjointness is "different brands can't alias" (a
brand property), sendability is "the brand's `Send`-ness" (a brand property).

**The borrow checker is what makes any of it sound**, and it is not replaced by
anything — it is the checker that verifies the branded box doesn't outlive the anchor
`a`. It was always going to be built; the point is that it, not an allocator-specific
subsystem, is what does the actual allocator safety work.

---

## 3. What genuinely remains allocator-specific after decomposition

Almost nothing at the language level:

- The `Alloc` aspect and its (still-unspecified, RFC-0063 §9 item 3) `alloc` method —
  but an aspect is not language machinery, it is library surface.
- The `@` **sugar** — `@a expr` for `a.alloc(expr)`, `@a T` for the branded-box type.
  Sugar is worth having, but it is not a semantic primitive; it is spelling.
- The **move-out / extraction** semantics (RFC-0066): converting `@a T` back to a
  plain, storage-erased `T`. This is the one piece with real semantic content that
  isn't obviously just brands-off-a-box — and even it is really "drop the brand,
  affine-move the payload," which is a records/linear-types operation
  (`ToRecord`/`FromRecord`-shaped, per RFC-0091), not an allocator operation. It lives
  in the substructural tower already.

The residue that is *irreducibly* allocator-specific is: the sugar, and the library.
That is a strikingly small amount of dedicated language machinery for what is currently
a seven-RFC cluster.

---

## 4. The narrowness risk this exposes

The design was built synthesis-first: the allocator cluster was fully specified before
any of context-parameters, brands, the box type, or the borrow checker existed. That
ordering baked allocator-specific assumptions into the *primitives'* territory:

- The `@` value-channel parameter is an allocator-specific spelling of what, seen
  generally, is a context parameter serving one of many possible uses (logging,
  capabilities, DI, config — none of which get a channel today). An allocator-specific
  param syntax earns its complexity once; a general context-parameter feature earns the
  same complexity across every ambient-value use case. Committing to the narrow
  spelling first risks discovering later that the general feature wanted a different
  shape, and now there are two.
- The tag-only parameter `<@a>` was, in RFC-0063's own words, "a compile-time-only
  name, erased at runtime, with no paired value parameter and no `Alloc` bound" —
  designed *without noticing it is already a brand* (`brand-kind-unification.md` calls
  this out explicitly). That is the narrowness risk already having materialized once:
  a general primitive re-invented under an allocator-specific name because the general
  primitive didn't exist yet to reach for.

The fear is therefore well-founded: **the current allocator design is plausibly
over-specified as a standalone feature, and some of its machinery is general-purpose
primitives wearing allocator-specific clothing.**

---

## 5. The strategic consequence: allocators are an acceptance test, and come last

Two things follow.

**Sequencing.** If allocators are context-params + brands + box + borrow-checker + a
library, they cannot be built until all of those exist. That makes allocators the
*last* major subsystem, not an early one — which flips the current
`roadmap-2026-07-07.md` ordering (allocators in Phase 3, the substructural tower
deferred to Stage B *after* it). It also confirms, from a completely different angle,
the instinct to gate allocator implementation on the borrow checker, records/views,
linear types, lifetimes, and brands all landing first. Allocators aren't being
*delayed*; they are *downstream by construction*.

**Role.** The allocator cluster should be reframed from "the flagship feature" to
"the flagship **acceptance test**." Its value is no longer "the deepest thing the
language is about" — it is "the concrete, worked-out synthesis that proves the general
primitives are sufficient." Restated as a falsifiable question the project can actually
answer once brands and context-parameters are real:

> **Can `Heap`, `BumpAlloc`, `@a T`, disjointness, and sendability all be rebuilt as
> (context parameter) + (allocator-instance brand) + (owned box) + (borrow-checked
> lifetime), with only the `Alloc` aspect and `@`-sugar as allocator-specific residue?
> If yes, allocators need almost no dedicated language machinery. If no, the part that
> resists the rebuild is exactly what is genuinely allocator-specific and worth keeping
> as a dedicated feature.**

Either answer is a win: "yes" shrinks the language, "no" tells you precisely and
minimally what allocators actually need that nothing else provides.

---

## 6. The counter-argument, and why the RFC cluster must stay intact

This reframe is intellectually cleaner but **strategically riskier**, and the risk is
worth stating as plainly as the thesis.

The current allocator design's one great virtue is that it *works standalone on paper*:
every hard question — disjointness, sendability, move-out, anchor interaction — is
answered in one concrete place. Dissolving it into context-params + brands bets
allocators on two features that are *both less settled than the allocator design
itself*. Brands especially: RFC-0076 has open questions, and this directory's own
watch list (`OBJECTIVES.md` Trigger 2) is already watching for identity-brands and
allocator-brands turning out more separate than the unification hopes. Convert one
paper-complete design into a two-deep chain of unsettled-on-unsettled and the whole
tower risks staying paper indefinitely.

**Mitigation, and it is not optional: do not refuse or gut the allocator RFCs.** Keep
them exactly as they are, and change only their *stated role* — from "accepted design
awaiting implementation" to "the acceptance test the primitives must reconstruct." The
cluster is the concrete target that keeps the general-primitive work honest: at every
step you can ask "does this rebuild `BumpAlloc` correctly?" and get a real answer,
instead of drifting into abstractions that unify beautifully and build nothing. The
decomposition is a lens for *sequencing and de-risking* the primitives, never a license
to delete the worked example that makes them checkable.

---

## 7. The concrete gap this surfaces

**There is no RFC for context parameters, anywhere in the corpus.** If this reframe is
right, a general context-parameter feature is now on the critical path for allocator
ergonomics — and it is completely unwritten, unlike brands (RFC-0076, at least draft)
and the borrow checker (specified as the RFC-0063/0067 checker stage). That is a bigger
hole than any open allocator question, and probably the first thing to capture as its
own draft RFC: a context-parameter mechanism, explicitly general (not allocator-only),
with the resolution rules (by-type, ambiguity-is-error) that RFC-0065's `@`-elision
already prototypes in allocator-specific form, and an explicit note that the allocator
`(@a: A)` channel is intended to become one instance of it rather than a parallel
mechanism.

---

## References

- `brand-kind-unification.md` — establishes the brand half of §1's decomposition (`@a`
  is a brand role); this document is its continuation.
- `brand-types.md`, `linear-types.md`, `structural-records.md` — the substructural
  primitives the move-out/extraction residue (§3) actually belongs to.
- `internal/rfcs/0-draft/rfc-0076-rc-brands.md` — brands; the tag half of the synthesis.
- `internal/rfcs/2-accepted/rfc-0063-allocator-handles.md` and its cluster — the
  synthesis being decomposed; kept intact as the acceptance test (§6).
- `internal/rfcs/2-accepted/rfc-0065-allocator-ergonomics.md` §1/§1b — the
  allocator-specific prototype of the context-parameter resolution rules (§7).
- `reports/implementation/roadmap-2026-07-07.md` — the phase ordering §5 argues should
  flip; not yet rewritten (deferred pending a firm re-sequencing decision).
- `reports/strategy/OBJECTIVES.md` Priorities 2/3 — where this document's conclusion is
  reflected in the living priority narrative.
