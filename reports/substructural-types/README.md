# Substructural Types — Design Exploration

This directory holds the active design exploration for Metel's next major
type-system thread: linear/affine/structural typing, brand-based identity, algebraic
effects, and structured concurrency. None of it is ratified. It exists to let several
genuinely interacting design threads grow independently instead of as one unbounded
document — read on for why that mattered enough to reorganize around.

**Start here if you're new to this thread**, in this order:

1. [`linear-types.md`](linear-types.md) — the multiplicity lattice and the `Linear`
   aspect. Read first: almost everything else in this directory assumes it.
2. [`structural-records.md`](structural-records.md) — `record` types, `HasField`, and
   typestate via row-conditional impls.
3. [`brand-types.md`](brand-types.md) — identity (as opposed to state), token-gated
   access, and the second typestate encoding.
4. [`algebraic-effects.md`](algebraic-effects.md) — how continuations, handlers, and
   linear tokens interact with the memory model.
5. [`structured-concurrency.md`](structured-concurrency.md) — fibers, channels, and the
   `Linear` `JoinHandle` that carries the structured "can't abandon a fiber" guarantee
   (`||` dropped 2026-07-07; CSC deferred).
6. [`brand-kind-unification.md`](brand-kind-unification.md) — the cross-cutting one:
   `@a` (allocator tags), `&r` (lifetime anchors), and `'c` (brands) as three
   sigil-selected roles of a single kind. Read after `brand-types.md`; it is that
   document's direct continuation and the proposed answer to RFC-0076 Q2.

Each is a **living document**: updated in place as understanding changes, not
superseded by a new dated file every time something is revised. Substantive changes get
a short note at the point of change rather than a new top-level version. This is
deliberately different from the `reports/strategy/strategic-overview-*` series, which
*is* a dated-snapshot series — see "Conventions" below for when each style applies.

---

## Why this directory exists

Prior to 2026-07-06, this design thread lived as one continuously-growing file
(`reports/memory-model/linear-types-and-structural-records-2026-07-06.md`, now
archived — see `archive/`), and before that, as several independent files that were
deleted (not archived) on 2026-06-28 when 11 memory-model reports were consolidated
into a single narrative. Two of those deleted files —
`archive/substructural-and-separation-types.md` and
`archive/per-field-multiplicities.md` — turned out to still be directly load-bearing:
this session's linear-types and typestate design independently re-derived several
things they had already worked out, without knowing they existed, because they were
gone from the working tree with no index pointing at git history.

That is the failure mode this structure is built to prevent:

1. **Delete-vs-archive inconsistency** — some prior design work was archived, some was
   deleted outright, with no rule governing which. Fixed here: **nothing in this
   directory is ever deleted, only archived**, always with a header explaining what
   superseded it and why it's kept.
2. **No index** — there was no single place listing what design threads existed or how
   they related, so overlap went unnoticed until a document was reread in full. Fixed:
   this file.
3. **No supersession convention** outside the strategic-overview series specifically —
   fixed by the `status`/`supersedes`/`revives` frontmatter fields (below) applied
   uniformly.
4. **Inconsistent Open-Questions formatting** — every document in this directory ends
   with a section literally titled `## Open questions` (or, inside a larger document,
   `## N. Open questions`), for mechanical rollup — see "Open questions across this
   directory" below.
5. **No staleness markers** — every document's frontmatter carries
   `last_synced_against_model`, stating the date it was last checked against the
   accepted RFCs and other living documents it depends on.
6. **Unbounded single-document growth** — the precursor to point 1: a document that
   only ever grows eventually gets consolidated-and-deleted rather than split. Fixed by
   splitting by topic now, while the topics are still distinguishable.

---

## Conventions

**Frontmatter fields**, present on every document in this directory:

```yaml
id: <slug>
title: "<Human title>"
type: report
status: active            # or: archived
last_synced_against_model: 'YYYY-MM-DD'
supersedes: <path or null>   # a specific prior document/section this replaces
revives: <path or null>      # a specific archived document/section this is built from
```

`supersedes` and `revives` are different relationships: *supersedes* means the named
document should no longer be read as current (and should itself carry an archival
header pointing forward); *revives* means this document's content originates from an
archived document but that archived document is still worth reading as historical
record in its own right (it isn't wrong, just superseded in form).

**Living documents vs. point-in-time snapshots.** Everything in this directory is a
living document — updated in place, changelog notes instead of new files. The
`reports/strategy/strategic-overview-*` series is the opposite kind on purpose: each
dated file is a snapshot of a strategic assessment at a point in time, meant to be
compared against its predecessor, not merged into it. Don't import that pattern here;
don't import this directory's pattern there.

**Archive, never delete.** `archive/` holds documents superseded by something in this
directory. Every archived document keeps its original content in full, with a header
block explaining: when it was archived, why, what superseded it, and — when the
original used pre-split-model syntax (`*T`/`own T`/`@[r] T` region brackets, the
"region" vocabulary itself) — an explicit note not to read the syntax as current.

**Standard "Open questions" section.** Every document ends with one, even when short.
This is what makes the rollup below possible without rereading every file in full.

---

## Cohesion map — how these six threads actually relate

These were not designed as one system and then split up; they were explored somewhat
independently and are being reconciled here, in the open, rather than pretending the
reconciliation already happened. The genuine connective tissue, as currently
understood:

- **`Linear` (linear-types.md)** is the substrate. A `Linear` value with no `Drop`
  fallback is what makes a token "must be consumed" rather than merely "droppable" —
  every token in `brand-types.md` and `algebraic-effects.md` is one lattice point or
  another from this document's §1, not a separate concept each time.
- **Typestate has two competing encodings**, not one: `structural-records.md` §5 (row-
  conditional impls, tracks *what state*) and `brand-types.md` §Typestate (phantom
  parameter, tracks *what state* **and** *which instance*). `brand-types.md` §3 works
  through the comparison and its considerations — but **which is canonical is not decided;
  too early** (a 2026-07-07 consolidation toward brands was reopened as premature).
- **Token-gated access (`brand-types.md`)** is where brands and `Linear` meet:
  `JoinToken`/`RcToken`/`HandlerToken` are brand-identified, and `brand-types.md` §2
  argues they sit at *different* points on the `Linear`-types lattice (`JoinToken` must
  be `Linear`; `RcToken`/`HandlerToken` only need to be affine) — a distinction neither
  RFC-0076 nor `linear-types.md` stated on its own. (Whether `RcToken` becomes the
  canonical shared-mutation path over `get_mut` is an open question — a 2026-07-07
  consolidation was reopened as premature.)
- **Effects (`algebraic-effects.md`)** consume both of the above: `HandlerToken` for
  handler-state exclusivity (brands), and a still-unsolved static check for `Linear`
  values captured in continuations (§12.3 there) that belongs partly in
  `linear-types.md` too and isn't cross-referenced from there yet.
- **Structured concurrency (`structured-concurrency.md`)**: the `\|\|` combinator is
  **dropped** (2026-07-07, and it stays dropped) — concurrency is `spawn` + `Chan` +
  `select`. *How* the structured "cannot silently abandon a fiber" guarantee is carried —
  a `Linear` `spawn` handle (leading candidate, `linear-types.md` §2) vs. a standalone
  `fork`/`JoinToken<'b>` vs. an affine handle with no static guarantee — is an **open
  question**, reopened as premature to decide. The Capture Separation Calculus lost its
  only consumer with `\|\|` and is deferred.
- **Brand-kind unification (`brand-kind-unification.md`)** is the cross-cutting thread:
  it takes `brand-types.md` §4's observation (a scoped allocator handle already *is* a
  brand) and generalizes it into a claim that `@a`, `&r`, and `'c` are one kind under
  three sigils. It is the only document here that reaches *outside* this directory as its
  primary subject — its content lives as much in the allocator/lifetime cluster (RFC-0063,
  RFC-0067, `../memory-model/lifetimes-vs-regions-2026-07-02.md`) as in brands — and it is
  the concrete example of the convergence the next paragraph asks about, resolved for the
  identity sub-question specifically rather than for the cluster as a whole. (Added
  2026-07-07:) `structural-records.md` §9 proposes a fourth surface use of the same
  identity kind — ordinary struct/enum nominal identity — reached from the opposite
  direction (asking whether named types could be a special case of structural types,
  rather than the reverse §1 already commits to); see that section for why this doesn't
  reopen §7's declined "records as the foundation" verdict, only reuses the identity tag
  §7 already establishes is unavoidable.

**What this map does not yet resolve**, tracked as its own item below: whether all six
of these are headed toward one coherent proposal or toward two-or-three independent
RFCs that happen to share a lattice. Nobody has taken a position on the *whole* question
yet, including this README — though `brand-kind-unification.md` now takes one for the
narrow slice of it concerning identity kinds, arguing those three converge.

---

## Open questions across this directory

Rolled up from each document's own `## Open questions` section — read the source
document for the reasoning behind each entry, not just the one-line summary here.

**From `linear-types.md`:**
- Present the four-point multiplicity lattice explicitly, or keep `Linear` documented
  as a flat per-struct property with the lattice as internal justification only.
- `Linear` as an auto-impl marker aspect, mutual exclusion with `Copy`/`Drop`,
  `drop<T: !Linear>` — leading candidates, not ratified.
- Struct-only `linear`/`affine` keyword sugar — leaning yes, not ratified.
- Partial consumption: Option B (explicit residual extraction) as the floor, Option C
  (automatic downgrade) as a separately-pursued fuller vision — revised leaning, not
  ratified.
- The aliasing question for Option C (what type does a pre-downgrade borrow have
  afterward) — unresolved; blocks Option C specifically.
- `NonLinear<T>`'s exact surface syntax — unresolved.
- Multiplicity polymorphism (`Guarded<T, Cap>`) — noted as a real later extension, not
  attempted.
- Whether residual/record typing replaces RFC-0071 §7's affine partial-move mechanism
  generally, or stays linear/record-scoped only.

**From `structural-records.md`:**
- Ship closed `record` types only, or also open `<row R>` generics immediately —
  recommend closed-only first.
- Plain-record style vs. OCaml-object style — recommend plain records.
- Width-subtyping-requires-`Copy` rule — proposed with no precedent to verify against;
  no `AllCopy`-shaped bound designed yet.
- Implicit vs. explicit-opt-in structural satisfaction — genuinely open.
- Transitive field-usage checking when a `Drop` body calls helper methods — unresolved.
- Row-conditional impl coherence extension — asserted tractable, not worked out.
- Phantom-parameter typestate vs. row-conditional-impl typestate — which is canonical,
  or do both stay? **Open, too early to decide** (a 2026-07-07 consolidation toward
  brands was reopened as premature); considerations recorded in `brand-types.md` §3.
- (Added 2026-07-07, §9) Brand-vs-row impl coherence priority — no specificity rule
  between an ordinary brand-keyed impl and a row-keyed blanket impl is written down.
- (Added 2026-07-07, §9) Private-field leakage into cross-module structural matching —
  `HasField`/`Lacks` need a public-only row projection when checked from outside the
  declaring module; not designed, not addressed anywhere else in this cluster.

**From `brand-types.md`:**
- The five unresolved questions from RFC-0076 itself (brand introduction mechanism,
  brand kind vs. lifetime kind, brand inference at function boundaries, `RcToken`/`Arc`
  across fiber boundaries, brand equality across modules) — restated, not re-litigated.
- Should RFC-0076 state token multiplicities explicitly (`Linear` for `JoinToken`,
  affine for `RcToken`/`HandlerToken`) once `linear-types.md`'s aspect design is further
  along.
- Is a brand-parameterized record worth designing, to give row-conditional typestate the
  identity dimension it currently lacks.
- Do brands and row-conditional impls end up as two permanent typestate mechanisms, or
  should one be recommended? **Open, too early to decide** (§3 records the considerations).
- Does `RcToken` become the canonical shared-mutation path over `get_mut`? **Open** — a
  2026-07-07 consolidation toward `RcToken` was reopened as premature; the two answer
  different questions (`RcToken`: exclusive write to aliased cells; `get_mut`: dynamic
  uniqueness), so this needs deciding, not defaulting.

**From `algebraic-effects.md`:**
- `^ clean` as an explicit annotation forbidding active borrows at effect-performance
  sites, vs. relying on the current implicit sendability-forces-synchronous constraint.
- The linear-value-in-continuation static check (§12.3) — needed for soundness once
  `Linear` exists, not yet specified precisely, not yet cross-referenced from
  `linear-types.md`.
- `HandlerToken<'b, E>` for handler-state exclusivity — sketched in RFC-0076 against
  this report's evidence-passing model; not yet reconciled in either direction.
- Koka's `fun`/`ctl`/`final ctl` split and evidence-passing — not adopted, not
  rejected; flagged as the highest-value borrow from prior art if effect syntax
  becomes an actual RFC.
- Whether `effect`/`handle`/`resume` should become its own RFC, and how it sequences
  against the rest of this cluster.

**From `structured-concurrency.md`** (rewritten 2026-07-07 — `\|\|` dropped; the
structured-guarantee mechanism is reopened as premature to settle):
- **Which mechanism carries the join guarantee** — a `Linear` `spawn` handle (leading
  candidate) vs. a standalone `fork`/`JoinToken<'b>` vs. an affine handle with no static
  guarantee. The central open question now that `\|\|` is gone.
- Is in-place data parallelism (the one capability dropping `\|\|` gave up) worth
  restoring later? Only real workload demand should revive CSC + liberalized `spawn`.
- ~~General CSC vs. narrow stdlib-primitive disjointness~~ / ~~RFC-0064's own open
  questions~~ — moot: `\|\|` dropped, CSC demoted to deferred.
- Liberalized `spawn` capturing `&mut T` under capture-set disjointness, and `sep{}`
  surface syntax — both deferred with CSC; relevant only if in-place parallelism returns.

**From `brand-kind-unification.md`:**
- Kind unification vs. deliberate separateness — unify `@a`/`&r`/`'c` as one kind
  (sigils preserved at the surface) or keep three kinds for role-incompatibility-for-free.
  Leaning unify-at-the-mechanism-level, not ratified.
- The per-role relation algebra (common equality core + `@`-nesting + `&`-outlives) is
  asserted formalizable but not written down.
- Which role-crossings are legal — `@a`↔`&a` is clearly wanted (RFC-0063 §6 already does
  it); the rest of the crossing matrix is unenumerated.
- Cross-module identity (shared with `brand-types.md` / RFC-0076 Q5) — one visibility
  rule for all three roles, or three.
- Whether it lands as an RFC-0076 amendment, a new RFC, or stays exploratory.
- (Added 2026-07-07, item 6, from `structural-records.md` §9) A candidate fourth surface
  use — struct/enum nominal identity as another instance of the `'c` role — and the
  nesting question it raises: is `@a T` where `T` itself carries an identity brand a
  role-crossing, or just composition of the same role at two levels? Not distinguished
  from a crossing yet, not resolved.

**Cross-cutting, not owned by any single document:**
- Whether this whole cluster (linear types, structural records, brands, effects,
  structured concurrency, brand-kind unification) converges on one coherent proposal or
  splits into several independent RFCs — see "What this map does not yet resolve" above.
  `brand-kind-unification.md` argues the three identity kinds specifically do converge;
  it takes no position on the cluster as a whole.
- The tracked, deadline-bound item this entire cluster still has to satisfy before
  RFC-0071/RFC-0067 implementation begins: RFC-0063 §9 item 5, partial consumption of a
  linear struct. `linear-types.md` §3's Option B is what currently satisfies it — see
  that document's closing section for the exact claim.

---

## Related material outside this directory

- `internal/rfcs/1-under-review/rfc-0063-allocator-handles.md` §9 — the tracked,
  deadline-bound open questions this cluster's design work is answering.
- `reports/memory-model/lifetimes-vs-regions-2026-07-02.md` — the accepted position on
  the allocator/lifetime split that every document here assumes as background.
- `internal/rfcs/0-draft/rfc-0076-rc-brands.md` — the RFC `brand-types.md` is
  commentary on.
- `internal/rfcs/0-draft/rfc-0064-fork-join-parallelism.md` — **retracted 2026-07-07**
  (the `\|\|` combinator this defined is dropped); `structured-concurrency.md` §3 records
  where its structured guarantee went (a `Linear` `JoinHandle`).
- `reports/strategy/strategic-overview-2026-07-06.md` — why this whole cluster is
  currently prioritized above the lower-level allocator/unsafe-blocks work.
