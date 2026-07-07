---
id: integrated-language-overview-2026-07-07
title: "Language Direction — High-Level Planning Overview"
type: report
created_date: '2026-07-07'
---

# Language Direction — High-Level Planning Overview

*A high-level, point-in-time synthesis to steer **mid-to-long-term development and design
direction** — not a spec, not a tutorial, not a feature showcase. It answers three
planning questions: what are we converging on, what is actually on the critical path
versus deferrable, and where should effort go over the coming stretch. Feature-level
detail and code examples live in the RFCs and in `../substructural-types/`; this document
deliberately stays above them.*

*Nothing here is uniformly ratified. The single most important framing fact for planning:
**the design is roughly two major threads ahead of the implementation.** The interpreter
still deep-clones values and has no borrow checker, no allocator, and no move-semantics
enforcement. Every "future" layer below is a design destination, not running code.*

---

## 1. What we are converging on

A systems language organized around two axes most languages fuse or omit: **where a value
lives** (allocators as first-class values) and **how a value may be used** (an affine-by-
default substructural discipline, with `Linear` at the strict end and `Copy` opt-in). On
top sits an ordinary modern surface — aspects, enums with exhaustive matching,
`Perhaps`/`Result`, generics, pattern matching — governed by **Storage Transparency**:
code that does not allocate or borrow carries no storage annotation, so the common case
reads like any modern language and the annotation budget concentrates exactly where a real
storage or resource decision is made.

The positioning is credible and specific: linear-types-plus-regions is a proven
neighborhood (Austral), structural typing is proven (TypeScript), and the *combination* —
row-polymorphic products with a per-field ownership discipline, plus concrete
binding-named lifetime errors instead of abstract `'a` — is the actual differentiation
claim. The strongest evidence the core is sound is that powerful properties fall out of
single rules rather than being bolted on (one-shot continuations from affinity; a record
inheriting `Linear` from any linear field; the structured-concurrency guarantee that
*could* fall out of a linear handle — one of the open options in §4).

---

## 2. The stack, by maturity and dependency

The planning-relevant view is not "what features exist" but "what is settled, what depends
on what, and what can be built independently." Four layers, foundation to frontier:

| Layer | Contents | Maturity | Gates / needs | Build-independent? |
|---|---|---|---|---|
| **L0 Core type system** | aspects + auto-impls, negative bounds/impls, associated types, `Perhaps`/`Result`, bottom type, exhaustiveness | **accepted** | — | Yes — already the stable base |
| **L1 Ownership** | affine-by-default, move-once, `Copy`/`Drop` exclusion, drop order, partial moves | **accepted (RFC-0071)** | L0 | Yes |
| **L2 Allocators + lifetimes** | `@a T` allocators as values, `&r` lifetime anchors, storage transparency, sendability, disjointness | **designed, under review** — awaiting ratification (RFC-0088) | L1 | Mostly — the reference-type/borrow-checker core does **not** reference `Alloc` |
| **L3 Substructural + identity** | `Linear` aspect, structural records, brands, brand-kind unification | **exploration only, no RFC** | L1/L2 for framing; brands increasingly load-bearing | Partially — one narrow piece has a deadline (below) |
| **L4 Frontier** | algebraic effects, concurrency (fibers/channels), user-authored allocators (unsafe layer) | **draft / proposed** | L4 effects need runtime continuation-capture; user allocators need an unsafe layer that doesn't exist | No — each blocked on something absent |

The critical structural fact: **L2's allocator/lifetime split decoupled allocator detail
from the borrow-checker core.** Post-split, getting the borrow checker right no longer
requires getting low-level allocator plumbing right — only a specific extension does. That
moves a lot of L2/L4 allocator work *off* the critical path, and moves L3's linear work
*onto* it (via the one deadline below).

---

## 3. Critical path vs. deferrable

**On the critical path (blocks implementation of L1/L2):**

- **Ratified RFC text for the L2 cluster** (RFC-0088, sweeping RFC-0063/65/66/67/68/73/77
  back to accepted, retracting 0069/0085/0087). Not because allocator *runtime* work is
  urgent, but because Phase 2–4 implementation needs settled text to build against.
- **Partial consumption of a linear struct** (RFC-0063 §9 item 5) — the *one* piece of L3
  with a real clock. It has to be settled before move-semantics and borrow-checker
  implementation (Phase 3 steps 1–2), because it concerns the same partial-move mechanism
  those steps build regardless. It is already satisfied by a **narrow** mechanism (explicit
  residual extraction over a closed field list — no row kind, no unification), and must
  stay scoped that narrowly on purpose.

**Deferrable without blocking anything:**

- **Low-level allocator API / unsafe layer** (RFC-0063 §9 items 3–4, RFC-0026). The four
  stdlib allocators can be implemented directly in the interpreter's host language (the
  existing stdlib already does this). This layer only gates *user-authored* custom
  allocators — real, but nothing else depends on it.
- **The rest of L3's tower** — open-row generics, records-as-type-former, structural
  typestate, the brand-kind unification write-up. Explicitly decoupled from the deadline.
- **L4 effects and concurrency** — effects need runtime work that doesn't exist; concurrency
  is a coherent design but not gating.

---

## 4. Direction-shaping decisions (and what they mean for the roadmap)

One firm decision, and a deliberate choice *not* to make three others yet:

- **`||` fork-join dropped (RFC-0064 retracted).** Concurrency is `spawn` + `Chan<T>` +
  `select`. *Planning effect:* removes a whole second concurrency mechanism and the Capture
  Separation Calculus that propped it up — less to build, less to teach. The one accepted
  cost: no in-place parallelism over arena data (parallelizing means a heap round-trip),
  deferred and revivable only on real workload demand. *Open sub-question:* how the
  structured "cannot silently abandon a fiber" guarantee is carried (a `Linear` `spawn`
  handle is the leading candidate) is not yet decided.
- **Three consolidations were explored and deliberately reopened as premature (2026-07-07):**
  typestate → brands, shared mutation → `RcToken`, and the join guarantee → a linear handle.
  Each has a leaning (brands are cheaper and cover state-plus-identity; `RcToken` and
  `get_mut` answer different questions; a linear handle reuses existing machinery), but all
  three are **left open on purpose** — they are L3/L4 questions the MVP doesn't touch, and
  the discipline to not over-decide them now is itself part of the direction. *Planning
  effect:* nothing about these gates the MVP, and keeping open-`<row R>` generics off the
  critical path holds regardless of how typestate eventually resolves.
- **The one thing to watch across all three:** their natural leanings all point *toward
  brands*, so if they are eventually taken, brand-inference maturity (§5) becomes the
  pivotal ergonomic risk. That is a reason to get real implementation feedback before
  committing, not a reason to commit now.

---

## 5. Roadmap risk register

Prioritized by how much each could derail the plan, not by technical depth.

| Risk | Kind | Affects | Stance |
|---|---|---|---|
| **Overreach vs. implementation** — design is ~2 threads ahead of running code; several key interactions are only answerable by real programs (the RFC-0075 lesson) | Process | Everything | **Highest.** The antidote is building, not more design. |
| **Pervasive brands × immature inference** — brands already appear in `Rc`/tokens/typestate/effects, inference at function boundaries is unresolved (RFC-0076 Q3), and brands are the least-mature layer; bad inference reintroduces abstract names in errors, the exact thing L2 eliminated. Becomes *pivotal* if the §4 consolidations toward brands are eventually taken | Ergonomics | L3, and the "concrete errors" pitch | Treat as a precondition before leaning further on brands, not a follow-on. |
| **Linear-tower viability** — linear values in collections, across `?`/early-return, and captured in closures (the last refused with no replacement) are unaddressed; without them, "Metel has linear types" means only single local bindings | Feasibility | L3 linear layer | Open. May force scoping linearity down to capability-token shapes. |
| **Ergonomic cost under-counted** — "common case is annotation-free" holds for callers, not for library authors carrying `@a`/`<&r>`/`brand`/`Linear`/bounds at once | Adoption | Library/infra code | Only real code answers it — another reason to build. |
| **Perf/concurrency tension** — scoped allocators aren't sendable, and with `||` gone arena data has no parallel story at all | Design | Concurrency + arena users | Accepted trade for now; revive in-place parallelism only on demand. |
| **Effects: most load-bearing, least baked** — "testable IO without mocks" is the flagship pitch but has no RFC and needs continuation-capture the runtime lacks | Sequencing | L4 | Sequence behind the runtime work it requires; don't let the pitch pull it forward. |

---

## 6. Recommended sequencing

The through-line: **freeze a minimum viable subset and build it, because paper design has
hit diminishing returns and every remaining high-value question needs implementation
feedback.**

- **Phase A — settle L2 text and build the MVP.** Ratify the allocator/lifetime cluster
  (RFC-0088). Resolve partial consumption with the narrow mechanism only. Then implement the
  subset that is already a real language and has the fewest open interactions: **affine
  ownership + the four stdlib allocators (host-implemented) + lifetime anchors + aspects** —
  i.e. L0+L1+L2 *without* linear types, brands, records, or effects. Goal: real programs
  running, which is the only source of the feedback everything else waits on.
- **Phase B — let implementation feedback decide the L3 tower.** With real resource/
  allocator code in hand, test whether the linear tower earns its cost (the collections/`?`/
  closures questions) and mature brand inference as the keystone it now is. Pull open-row
  generics forward only if genuine duck-typing demand appears.
- **Phase C — frontier, gated on their prerequisites.** Effects behind the runtime's
  continuation-capture work; user-authored allocators behind the unsafe layer; the
  brand-kind unification as cleanup; in-place data parallelism only if workloads demand it.

Keep the exploratory tower (L3/L4) growing on paper only as far as the one real deadline
(partial consumption) requires, and no farther ahead of the runtime than that.

---

## 7. Signals that would change this plan

- **Implementation shows partial-consumption or typestate patterns are needed far more
  than expected** → pull the L3 tower forward; that is evidence paper review can't produce.
- **The narrow partial-consumption mechanism proves insufficient in real code** (residuals
  need to cross function boundaries) → the open-row version stops being speculative.
- **A concrete need for user-authored custom allocators emerges** → re-promote the unsafe
  layer (Priority 3) independently of everything else.
- **A comparable language ships a similar structural-plus-linear combination first** → the
  differentiation window narrows; the one external risk to the "worth pursuing" verdict.
- **The meta-risk realized:** if each planning cycle keeps *extending the design* instead of
  freezing and building, the overreach risk compounds. The discipline to stop designing is
  itself the most important planning decision here.

---

## References

- `strategic-overview-2026-07-06.md` — priorities, the differentiation claim, and the
  design/implementation gap this document operationalizes for planning.
- `../memory-model/lifetimes-vs-regions-2026-07-02.md` — the L2 allocator/lifetime split.
- `../substructural-types/README.md` — index and cohesion map for the L3 exploration
  (linear types, structural records, brands, brand-kind unification, effects, structured
  concurrency), including the `||` drop and the typestate/shared-mutation/join-guarantee
  questions left open as premature.
- `rfc-implementation-breakdown-2026-07-01.md` — the phased implementation order Phase A/B/C
  above map onto.
