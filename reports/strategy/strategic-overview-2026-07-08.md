---
id: strategic-overview-2026-07-08
title: "Language Design — Strategic Overview"
type: report
created_date: '2026-07-08'
---

# Language Design — Strategic Overview

*This document supersedes `strategic-overview-2026-07-06.md`. For the prior state,
see that document.*

*Updated 2026-07-08: the structural-records thread inside Priority 2 matured
substantially — a three-tier struct/record split, validated against four real Rust
`unsafe` patterns rather than constructed examples — and, in the course of that work,
surfaced a previously-unnamed, foundational gap (the derive/comptime execution model)
that every mechanism in this cluster, and possibly several already-accepted RFCs, has
been silently assuming. See "What Changed" and "Honest Assessment" for both halves of
that finding.*

---

## What Changed

Three threads moved since July 6.

**RFC-0067 split, cleanly, into an accepted slice and a narrowed remainder.** The
reference-type/allocator-pointer RFC bundled genuinely independent content (plain
`&T`/`&var T`, address-of, auto-deref, superseding RFC-0043) with genuinely dependent
content (lifetime anchors, which are borrow-checker core; allocator-pointer access,
which needs RFC-0063's `@a T`). Split into RFC-0067a (accepted, Cluster A — no ordering
dependency on the rest of the allocator cluster) and a narrowed RFC-0067 (stays under
review). This directly executes on 07-06's own observation that the reference-type core
doesn't reference `Alloc` at all — RFC-0067a is that observation made concrete and
ratified.

**RFC-0050 (Closure Capture Lists) substantially reworked**, moving from a syntax
sketch to a fully-specified draft: four capture specifiers (`&var`, `move`, bare-ident
clone, `&` read-only reference), an exhaustiveness requirement (once a capture list
exists, every free variable must be enumerated — no partial/implicit mixing), a
resolved scope for "free variable" (outer-scope locals only, explicitly excluding
module-level items), and a build-order split (capture lists for `&var`/clone/`&` are
buildable now against RFC-0067a directly; `move` captures wait on a split-model
successor to the refused RFC-0046).

**The structural-records thread — the substantial one this pass.** Not a small
refinement: a three-tier resolution to a question 07-06 didn't yet know to ask (does
row/multiplicity capability apply to every struct, or is it opt-in, and at what
granularity), four real Rust `unsafe` patterns closed as validating evidence, two loose
ends from earlier in this same thread resolved, and — the most consequential single
finding — a previously-unnamed, foundational gap identified. Each is worth its own
paragraph rather than folding all four into one bullet, since 07-06's own mistake
(treating a large new thread as a subsection of an existing one) is exactly what this
section should not repeat.

*The tier resolution.* Rather than making every struct carry row/brand structure (the
strong version of the "(row, brand)" idea `structural-records.md` §9 first floated), or
leaving structural capability entirely bolted-on with no story for ordinary structs, the
cluster settled on three tiers of increasing commitment: plain `struct` (unchanged,
whole-value only), `derives ToRecord, FromRecord` (on-demand, explicit, zero-cost
conversion to/from the struct's own row — including borrowed variants,
`to_record_mut`/`from_record_mut`, added specifically to unify this tier with the
cluster's earlier `&var`-based drain/restore sketches), and a named-record kind (the
full `(row, brand)` representation, the only tier eligible for row-conditional impls).
`ToRecord`/`FromRecord` are kept as two separate derivable aspects rather than merged,
for a concrete reason: auto-derived `FromRecord` can silently bypass a constructor's
invariants (a `SortedPair`-shaped worked example makes this concrete) in a way a
hand-written one wouldn't — the same reasoning that keeps serde's
`Serialize`/`Deserialize` separate.

*Four real `unsafe` patterns, not constructed illustrations.* `structural-records.md`
§2 and its Example Programs section now carry worked cases showing this model would let
Metel express, safely, four things mainstream systems languages currently need
`unsafe` for: `Rc`/`Arc`'s own internal two-phase teardown (drop the value when strong
hits zero, keep the counters alive until weak also does — real implementations use
`ManuallyDrop` for exactly this); swapping a field's value with no cheap placeholder
available (the problem dedicated crates exist to paper over with an abort-on-panic
guard); piecewise `MaybeUninit`-style struct construction, including its panic-safety
hazard; and a generic, reusable helper splitting a struct's fields into independent
`&var` views across a function boundary — precisely the motivating gap behind Rust's
own unshipped "view types" proposal. This is the kind of validation 07-06 could only
gesture at ("solves a problem no mainstream language solves") — now with specific,
checkable comparison points rather than a general claim.

*Two loose ends closed, not carried forward.* `linear-types.md`'s Option C aliasing
question — what type does a pre-downgrade borrow have afterward, blocking Option C
since this cluster's inception — now has a candidate answer, arrived at as a side
effect of designing the tier-2 conversions: the shrunk row type, sound because `&var`
already guarantees no other alias exists to observe the stale type. Promising, not
proven — no soundness argument is written down, only a mechanism plus several examples
that exercise it without incident. Separately, `structural-records.md`'s own internal
tension between §1/§3 (implicit `HasField`-bound satisfaction) and §8 (flagging that
same implicitness as an open, Go-style concern) is resolved: the tier system already
answers it, by distinguishing bound satisfaction (stays implicit — it grants no
capability, just lets a generic function accept a matching type) from
capability-granting mechanisms (impls, conversion, multiplicity — gated behind the
tiers). Both were small, self-contained fixes, but both had been sitting unresolved
inside already-written content, which is worth naming rather than quietly patching.

*The foundational gap: the derive/comptime execution model.* Every mechanism
catalogued above — `derives Linear`, `derives ToRecord, FromRecord`, and
`structural-records.md` §2's `uses (fd)` field-usage declarations — assumes a
derive/compile-time-execution mechanism that no document in this cluster actually
specifies. On inspection this bundles three genuinely different things: auto-trait-style
structural composition (`Send`/`Sync`/`Linear` — likely already covered by RFC-0080, not
yet re-checked), derive-as-codegen (`ToRecord`/`FromRecord` — a closed,
compiler-hardcoded list versus an open, library-extensible meta-programming facility, an
entirely unaddressed feature in its own right), and static analysis over function bodies
(§2's field-usage checking, possibly an application of `algebraic-effects.md`'s
already-planned effect system rather than a fourth new mechanism). This is a genuine
scope increase, not a decrease — see "Honest Assessment."

---

## RFC State

One real transition since July 6: **RFC-0067a** (new, accepted) carries the
reference-type core out of the narrowed **RFC-0067** (stays under review). **RFC-0050**
stays draft but is substantially more complete than 07-06's snapshot. No other RFC
changed lifecycle stage this pass — the structural-records/comptime work is
exploratory, in `reports/substructural-types/`, and has not yet been proposed as RFC
text at all.

---

## The Design/Implementation Gap — unchanged in kind, larger in one specific place

The interpreter still has no borrow checker, no allocator, no move-semantics
enforcement — identical to every report in this series so far. What's new is not the
shape of the gap but its size in one specific location: the derive/comptime foundation
identified this pass is not a refinement of already-scoped work, it's newly-discovered
scope. 07-06 sized the structural-records initiative at "comparable to the memory-model
split" based on row unification, coherence extension, and the width-subtyping question.
The derive-as-codegen fork (closed compiler-hardcoded list vs. open meta-programming
facility) is, on its own, potentially comparable in size to *that entire estimate* — a
full extensibility model for the compiler, not a line item inside an already-budgeted
feature. This should be read as 07-06's sizing turning out to be an underestimate, not
as new information that changes what's urgent (nothing here is on Phase 3's critical
path — see below), but the honest scale of "if this is pursued to completion" needs
restating upward.

**The floor is still unaffected.** RFC-0063 §9 item 5 is still satisfied by
`linear-types.md` §3's Option B alone — narrow, no row kind, no derive mechanism
required. Everything discussed this pass, including the newly-discovered comptime gap,
sits above that floor, exactly where 07-06 already drew the line between "what's
required" and "what's aspirational."

---

## Honest Assessment — is this actually worth it?

07-06 asked this about structural records and linear types generally. This pass has
enough new, specific evidence to answer more precisely, and the answer splits by tier
rather than being one verdict for the whole thread.

**Tiers 1 and 2 (plain `struct`; `derives ToRecord, FromRecord`) clear the bar 07-06
was cautious about, on the strength of real validating evidence, not just internal
coherence.** The four `unsafe`-pattern closures aren't hypothetical — `Rc`/`Arc`'s
two-phase teardown, the placeholder-swap problem, `MaybeUninit` construction, and the
view-types gap are documented, real pain points in the language this project is most
directly positioned against. That's a materially stronger form of evidence than 07-06
had (which argued from Austral's positioning and a general "no mainstream language
solves this" claim). Cost-wise, tiers 1/2 are also cheap by construction: no row-kind,
no unification algorithm, no borrow-checker dependency — ordinary aspect derivation,
reusing RFC-0080's existing pattern (pending the RFC-0080 re-check flagged above) rather
than inventing new type-system machinery.

**Tier 3 (the named-record kind) and the brand-kind-unification/comptime work behind it
remain exactly the unproven, paper-only territory 07-06 was right to be cautious
about — arguably more so, now that the derive-as-codegen fork is visible.** Tier 3 has
no settled syntax marker, depends on brand-kind-unification's identity-tag-reuse claim
holding up under a role-crossing matrix that isn't even enumerated yet, and its
coherence/visibility hazards (brand-vs-row impl priority, private-field leakage) are
narrowed but not closed. The comptime/derive-as-codegen question adds a second,
independent axis of risk on top of that. RFC-0075 (region inference) remains the
project's own cautionary tale for exactly this shape of failure — plausible on paper,
expensive against a real implementation — and it applies with at least as much force
here as 07-06 already argued, now with a bigger unknown (the derive mechanism) added to
the pile.

**The right verdict is therefore split, not uniform:** pursue tiers 1/2 with real
confidence — they're validated, cheap, and arguably ready to be pulled forward in the
implementation sequence (see Priorities). Continue treating tier 3,
brand-kind-unification, the typestate fork, and the comptime/derive question as paced
exploration, explicitly not gating anything, with the derive-as-codegen fork
specifically flagged as larger than 07-06's original sizing assumed. Both halves of
this verdict follow from the same discipline 07-06 already established — separate
what's proven from what's promising — applied to a thread that has now split into two
halves with genuinely different risk profiles.

---

## Priorities

Retains 07-06's three-tier structure; refines Priority 2 to reflect the tier split, and
notes RFC-0067a as executed progress on Priority 1.

### Priority 1 — Ratify the allocator/lifetime cluster's design

Unchanged in substance from 07-06, with one piece of actual progress: RFC-0067a is
accepted, out of the narrowed RFC-0067's way. The remaining sweep (RFC-0088 or amending
RFC-0063 directly, retracting RFC-0069/RFC-0085/RFC-0087, the rest of the cluster back
to accepted) is still unactioned.

### Priority 2 — Linear and structural types, now explicitly two sub-tracks

**2a — the floor, plus tiers 1/2, cheap and validated:** `linear-types.md` §3's Option B
(unchanged, still the only thing the RFC-0063 §9 item 5 deadline requires) and
`structural-records.md`'s tier 1/2 split. Worth reconsidering whether tier 1/2
specifically belong in Cluster A's implementation sequencing rather than bundled into
Stage B/C by an assumption `reports/implementation/roadmap-2026-07-07.md` made before
the tier split existed — they need no borrow checker and no allocator to exist. This is
a concrete, checkable question the next roadmap revision should answer, not a permanent
verdict here.

**2b — the fuller vision, unchanged in pacing, larger in estimated size:** tier 3,
brand-kind-unification, the row-vs-brand typestate fork, and the newly-discovered
derive/comptime question. Stays paced-not-urgent, exactly as 07-06 recommended for the
whole thread — the only change is that "budget for it at the scale of the memory-model
split" (07-06's own sizing) should now be read as a floor on the estimate, not a
ceiling, given the derive-as-codegen fork's scope.

### Priority 3 — Lower-level memory API and unsafe blocks

Unchanged from 07-06. Nothing this pass affects this priority's reasoning or ranking.

---

## What Would Change This Assessment

**If re-reading RFC-0080 shows it does not naturally extend to derive-as-codegen**
(only to auto-trait-style structural composition), that confirms the derive/comptime
foundation is a genuinely new feature, not an extension of accepted work — and should
prompt scoping it as its own initiative before tier 3 or brand-kind-unification proceed
much further, since both currently assume some answer to it.

**If a real scenario forces the brand-kind-unification role-crossing matrix to resolve
and reveals identity brands and allocator/lifetime brands are more separate than
hoped**, tier 3's core premise (reusing the same tag) weakens, and the named-record kind
may need its own, dedicated identity mechanism after all — a real cost increase
specific to tier 3, not to tiers 1/2.

**If Phase 3 implementation experience shows tier 1/2's drain/restore patterns are
needed constantly in real allocator/resource code**, that's concrete evidence for
pulling tier 1/2 into Cluster A's sequencing sooner, per the open placement question
above — not just a confirmation that the tier split was a good idea in the abstract.

**Everything in 07-06's own "What Would Change This Assessment" still applies
unchanged** — implementation pressure on Option B/C, a comparable language shipping
first, RFC-0039's independent prioritization, a concrete user-authored-allocator need —
none of it was resolved or superseded this pass.
