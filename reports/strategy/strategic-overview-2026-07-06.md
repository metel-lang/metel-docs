---
id: strategic-overview-2026-07-06
title: "Language Design — Strategic Overview"
type: report
created_date: '2026-07-06'
---

# Language Design — Strategic Overview

*This document supersedes `strategic-overview-2026-07-05.md`. For the prior state,
see that document. The archives in `reports/archive/` cover the earlier session
history.*

*Updated 2026-07-06 (second pass): the priority ordering below is revised. Linear and
structural types are promoted from a paced, sequenced-after-ratification initiative to
the second overall priority, ahead of allocator-specific low-level design work — the
region/lifetime decoupling that used to make the latter urgent no longer holds. See
"The Design/Implementation Gap," "Honest Assessment," and "Priorities" for the
reasoning and its consequences.*

---

## What Changed

Two threads moved since July 5. One is small and contained — the storage
preservation principle (tag-only allocator parameters, RFC-0063 §4/RFC-0065
§1a/RFC-0066 §3a/RFC-0067 §5, `reports/memory-model/lifetimes-vs-regions-2026-07-02.md`
§12) — closing a real gap in the allocator cluster's call-site semantics that had gone
unaddressed since the split model itself. It's already reflected in the RFC text; there
is nothing further to report here.

The second is not small, and it's the one worth a strategic read.

**The genesis.** A single deferred question in RFC-0063 §9 — should allocators be
`Linear` rather than ordinary affine values, with `.free()` as the only way to
discharge them? — was deliberately *not* pursued as a separate RFC when first raised,
specifically to avoid scope explosion. It was recorded as an open question with an
explicit "no urgency" note, alongside three companion questions (the still-unspecified
`Alloc.alloc` method signature, `drop`'s interaction with a linear discipline, and the
unsafe-primitive layer custom allocator authoring would eventually need).

**What actually happened next.** Working out *how* `Linear` and partial consumption
could be designed — not whether to build them yet — surfaced a chain of prior art the
project had already half-built and half-forgotten: RFC-0024 (Linear Types, superseded)
had already worked out exactly-once consumption and compositional propagation years
before this thread started; RFC-0049 had already documented the exact `drop`/linearity
failure mode a naive design would reintroduce; RFC-0080/0081's `Send`/`Sync`
auto-impl-plus-negative-impl pattern turned out to be the ready-made template for
`Linear` as an aspect. Pursuing the one genuinely open question in that chain — how to
handle a struct with more than one linear field — led somewhere larger: a proposal for
**structural records** (`record { ... }`, `HasField`/`Lacks` structural bounds, open
row-polymorphic generics, typestate via row-conditional impls, a standalone
`NonLinear<T>` operator, and keyword sugar unifying `copy`/`linear`/`affine` declaration
syntax with RFC-0072's negative bounds and RFC-0039's still-draft aspect-alias syntax).

All of it is captured in one place:
`reports/memory-model/linear-types-and-structural-records-2026-07-06.md`. It is now the
single largest exploratory document in the repo outside the memory-model position
report itself — nine sections, worked example programs, and fourteen explicitly
unresolved questions, one of them (§5.7) a direction *considered and declined* on the
record rather than merely left open.

**Nothing here is ratified, and nothing changes RFC-0063's core surface.** The RFC's
already-under-review content is unaffected; only its §9 open-questions list grew, from
four items to five, with a pointer to the new report. The scope growth is real, but it
is scoped to *exploration*, not to anything currently blocking or gating other work.

---

## RFC State

Unchanged from July 5 in every count that matters — no RFC moved between accepted,
under review, or draft this session. What changed is which already-accepted RFCs turned
out to be quietly load-bearing for something well beyond their original motivation:

- **RFC-0072 (Negative Bounds)** and **RFC-0080/RFC-0081 (Stdlib Aspects / Negative
  Impls)** — accepted for `Copy`/`Drop` exclusion and `Send`/`Sync` auto-derivation
  respectively — turn out to be the entire mechanism `Linear` and `Affine` need. No new
  aspect-system primitive is required for either; both compose out of what's already
  accepted.
- **RFC-0039 (`aspect` Alias Syntax)** — still draft, not accepted, not even under active
  consideration before this thread — is now the concrete vehicle for naming `Affine` as
  `!Copy + !Linear` instead of writing the compound bound out at every call site. This
  report takes no position on advancing RFC-0039 itself; it only notes that the `Affine`
  alias is cheap the moment RFC-0039 is.
- **RFC-0024 (Linear Types, superseded), RFC-0046 (Linear Closure Capture, refused), and
  RFC-0049 (`linear fun` type system, draft, orphaned)** — sitting in `4-superseded/`,
  `5-refused/`, and an unattached draft respectively — turn out to already contain
  correct, directly reusable answers (exactly-once consumption, compositional
  propagation, the `drop`-without-cleanup hazard) that this thread had to rediscover
  rather than being handed. Worth flagging as a retrieval problem, not just a happy
  accident: material this directly relevant sitting three statuses away from "active" is
  exactly the kind of thing that gets re-derived at real cost if nobody happens to go
  looking.

The accepted (14), under-review (12), and draft/parked lists from July 5 otherwise
stand unchanged — see that document for the full table.

---

## The Design/Implementation Gap — now with a second axis

The gap named on July 1 and recalibrated on July 5 hasn't narrowed: the interpreter
still has no borrow checker, no allocator, no move-semantics enforcement. It still
deep-clones values and leans on reference counting internally. That much is identical
to two reports ago.

What's new is a **scope axis** layered on top of the existing **time axis**. The July 5
overview's own warning — *"every additional design session before implementation begins
extends the feedback gap... RFC-0075 is the concrete example"* — was written about the
memory-model split itself. It applies with at least equal force to the new thread,
because in scope, "structural records" is not a subsection of the memory model. It is,
if pursued to completion, comparable to the memory-model split's own scale: that
redesign took a multi-day crisis, produced a from-scratch position report, and rewrote
seven RFCs. The structural-records exploration has already produced a nine-section
report with its own unresolved row-unification algorithm, its own coherence extension,
and its own open width-subtyping-vs-ownership question — the shape of a second major
design initiative, not an afternoon's addendum to the first.

The one piece of good news: **the actual deadline this whole thread was tracking is
unaffected by any of this growth.** RFC-0063 §9 item 5 — partial consumption of a
linear struct must be settled before RFC-0071/RFC-0067 implementation begins (Phase 3
steps 1–2) — is satisfied by the report's own narrow mechanism (§4.2/§4.3: a phantom
marker on a closed, already-known field list, no row kind, no unification algorithm).
The open-row, `record`-as-type-former, typestate vision in §5 is explicitly decoupled
from that deadline in the report's own build-order recommendation (§5.4). The scope
expansion is real; the urgency has not expanded with it, and it must not be allowed to.

**A further refinement: the scope axis isn't evenly distributed across the memory-model
thread.** The split that separated allocators from lifetime anchors
(`lifetimes-vs-regions-2026-07-02.md`) did more than rename `Region` to `Alloc` — it
removed the reason allocator-level detail used to be urgent in the first place. Under
the old, unified region model, getting the region concept right *was* getting lifetimes
right, because one concept carried both jobs. Post-split, that's no longer true: the
reference-type core (ordinary borrows, lifetime-anchor elision, RFC-0067's own body
minus §5) and the borrow checker's core liveness/exclusivity logic don't reference
`Alloc` at all — only a specific extension does (allocator-pointer auto-deref, RFC-0067
§5; allocator-scope wellformedness, RFC-0077 §3). That means allocator-specific
low-level design — the still-unspecified `Alloc.alloc` method signature and the
unsafe-primitive layer custom allocator authoring would need (RFC-0063 §9 items 3–4) —
is further from the critical path than this document's own first-pass framing assumed.
Linear/structural types is closer to it, not farther: item 5's resolution feeds
directly into move-semantics and borrow-checker implementation (Phase 3 steps 1–2 in
`rfc-implementation-breakdown-2026-07-01.md`), which is not optional and not decoupled
from anything. See "Priorities" for what this changes in practice.

---

## Honest Assessment — is this actually worth it?

**The strategic case for it is real, not manufactured enthusiasm.** Two independent
observations support that:

- **Linear types are a proven positioning for a systems language, not a speculative
  one.** Austral exists, today, specifically as a systems language whose entire
  identity is linear types plus regions, deliberately without a Rust-scale borrow
  checker — and it has real recognition in PL circles for exactly that combination.
  Metel's own trajectory — regions rethought as allocators, lifetime concerns split out
  from them, and now a fine-grained exactly-once discipline layered on top — arrives at
  a strikingly similar neighborhood without having set out to copy anyone. That's a
  meaningfully different, and more credible, story than deciding up front to chase a
  competitor's headline feature.
- **Structural records solve a problem no mainstream systems language actually
  solves.** The Rust typestate/builder pattern is universal in practice and reinvented
  by hand in every crate that needs it — there is no shared vocabulary, only a
  convention built from phantom types nobody's compiler understands as a pattern.
  `HasField`-style structural bounds plus row-conditional impls (§5.5) would make that a
  first-class mechanism rather than a folklore technique.

**The actual differentiation claim is the combination, not either piece alone.**
Structural typing by itself has real precedent (TypeScript). Linear types by themselves
have real precedent (Austral). A language offering *both at once* — structural,
row-polymorphic products with a fine-grained, per-field ownership discipline that
composes automatically (a record inherits `Linear` from any field that has it) and
*reverts* automatically (§4.4's `NonLinear<T>` and the residual-typing mechanism both
fall out of the same composition rule once nothing linear remains, no separate
mechanism needed) — is not a combination this assessment is aware of any shipping
systems language offering. That is worth being precise about as the claim: not "records"
or "linear types," but the fact that they compose cleanly enough to fall out of a single
rule, which is itself evidence the underlying design is sound rather than a pile of
independently-plausible features bolted together.

**The case against moving fast on it is exactly as strong, and comes from this
project's own track record.** RFC-0075 (region inference) is the concrete, on-the-books
example of a memory-model feature that "looked plausible on paper" and became
speculative the moment it needed to survive contact with a real borrow checker. Row
polymorphism specifically — new type variables, a genuinely new unification algorithm,
a coherence extension for row-conditional impls, a width-subtyping-vs-ownership rule
with (by the exploratory report's own admission, §6) no existing precedent to check it
against — is at least as exposed to that failure mode as region inference was, and
arguably more, since it would be new type-system machinery rather than a refinement of
existing machinery.

**A late but important refinement to this assessment, worth stating precisely rather
than just asserted.** Allocator-specific design work is less urgent than this
document's own first pass assumed, for a concrete, checkable reason: the four stdlib
allocators (`Heap`, `LocalHeap`, `BumpAlloc`, `AutoAlloc`) don't need a Metel-level
`unsafe`/raw-memory feature to exist at all. They can be implemented directly in the
interpreter's host language, the same way the existing stdlib already does this —
`native(@std.core.list_new)` and its neighbors in `core.mtl` are exactly this pattern
already in production. A Metel-level unsafe-blocks feature and a specified
`Alloc.alloc` signature (RFC-0063 §9 items 3–4) are specifically what would let *user*
code write its own allocator — a real feature, but a strictly optional one that
nothing else in this assessment depends on. Combined with the reference-type/borrow-
checker decoupling above, this means Linear/structural types and allocator-specific
low-level plumbing were never actually competing for the same attention — one sits on
the critical path implied by Phase 3 steps 1–2, the other gates nothing at all. Treating
them as though they were on the same track, as this document's first pass did, understated
the case for the former and overstated the urgency of the latter.

**Verdict:** pursue it, because the opportunity is real and specific, not because
"more design" is free. But it has to be pursued on its own timeline, explicitly
separated from the one deadline that actually exists — which the exploratory report
already does, and this overview's job is to make sure that separation holds at the
project-planning level too, not just inside one report's own internal structure.

---

## Priorities

Revised into three explicit tiers this pass, replacing the previous Track A/B framing
— not because Track A/B was wrong, but because it left allocator-specific work and
structural/linear types implicitly competing for the same sequencing slot when they
no longer do.

### Priority 1 — Ratify the allocator/lifetime cluster's design

Unchanged from July 5's still-unactioned priority #1: write RFC-0088 (or amend
RFC-0063 directly), retract RFC-0069/RFC-0085/RFC-0087, sweep RFC-0063/0065/0066/
0067/0068/0073/0077 back to accepted. This stays first not because allocator
*implementation* is urgent — the point above is precisely that it isn't as urgent as
assumed — but because Phase 2–4 implementation work needs settled RFC *text* to build
against, independent of how the runtime pieces end up sequenced.

### Priority 2 — Linear and structural types (promoted)

The floor is unchanged: resolve RFC-0063 §9 item 5 using only the closed mechanism
from `linear-types-and-structural-records-2026-07-06.md` §4.2/§4.3 — a phantom marker
over a statically-known, finite field list, no row kind or unification algorithm
required — since it has a real clock (Phase 3 steps 1–2) and should stay scoped that
narrowly on purpose.

What changes this pass is everything *above* that floor. The fuller vision — `record`
as a real type-former, `HasField`/`Lacks`, open `<row R>` generics, typestate via
row-conditional impls, standalone `NonLinear<T>`, `copy`/`linear`/`affine` keyword
sugar, the `Affine` alias — is no longer treated as paced-and-sequenced-after
allocator ratification. **The previous pass's sequencing advice — ratify the cluster
before investing further in this thread — is retracted, not merely superseded:** it
was based on treating allocator design and structural/linear-types design as
contending for the same attention, which the reference-type/borrow-checker decoupling
above shows isn't the case. This thread can and should proceed in parallel with
Priority 1, not after it.

If it's eventually taken to an actual RFC, budget for it at the scale of the
memory-model split, not as a quick follow-on — the exploratory report's own §6 cost
list (row unification, coherence extension, an unprecedented width-subtyping rule) is
the honest sizing, not an afterthought to be resolved in passing.

### Priority 3 — Lower-level memory API and unsafe blocks (demoted further)

RFC-0063 §9 items 3–4 — the still-unspecified `Alloc.alloc` method signature, and the
unsafe-primitive layer (RFC-0026, revived and re-anchored) that a real implementation
of it and of custom allocator authoring generally would need. This drops below "no
urgency waiting on the allocator layer": it doesn't gate the allocator/lifetime
cluster's ratification, doesn't gate Phase 2–4 implementation, and doesn't gate
anything in Priority 2 either. The four stdlib allocators can be implemented in the
interpreter's host language directly, with no Metel-level unsafe feature required at
all. This priority is specifically about enabling *user-authored* custom allocators —
real, but the one item on this whole list that nothing else depends on.

### Unchanged from July 5

`pub let` (RFC-0083) and array syntax (RFC-0084) as mechanical residuals, and
RFC-0064/RFC-0076 as concurrency/brand-type follow-on. None of this was displaced by
the new thread or the reprioritization; see the July 5 document for full detail,
still current.

---

## What Would Change This Assessment

**If Phase 3 implementation experience shows partial-consumption or typestate patterns
are needed far more often than expected in real allocator/resource code**, that is a
signal to pull Track B forward, not just a confirmation that it was a nice idea.
Implementation pressure is exactly the kind of evidence paper review cannot produce —
the same reasoning that governs whether RFC-0075 is ever revisited applies here.

**If Track A's narrow mechanism proves insufficient once real code is written against
it** — in particular, if callers genuinely need partially-consumed residuals to cross
function boundaries rather than staying local to one function — that would be concrete
evidence the open-row version isn't purely speculative, and should be re-prioritized
accordingly rather than left on the "someday" track by default.

**If RFC-0039 is independently prioritized for unrelated reasons** (compound bounds
elsewhere in the type system getting unwieldy, say), the `Affine` alias becomes a cheap
side effect rather than something this project has to justify building RFC-0039 for on
its own.

**If a comparable language ships a similar structural-plus-linear combination first**,
the differentiation window this overview is arguing for narrows. This can't be
forecast precisely, but it's worth naming as the one external risk to the "worth
pursuing" verdict that has nothing to do with Metel's own design or implementation
choices.

**If a concrete need for user-authored custom allocators emerges** — a library wanting
a specialized pool allocator, say — Priority 3 (the low-level memory API and unsafe
blocks) gets re-promoted from "nothing depends on it" back up, independent of
everything else in this document. That's the one thing that would change specifically
that ranking; it doesn't touch the Priority 1/2 reasoning at all.
