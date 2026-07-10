---
id: rfc-index
title: "RFC Index"
type: index
last_built: '2026-07-10'
---

# RFC Index

Generated 2026-07-09, last updated 2026-07-10. Not auto-regenerated — rebuild it (or ask
for a rebuild) whenever RFCs are added, moved, or change status; it will drift otherwise.
Grouped by theme, not by number, because number order tells you nothing about what's
related. See `PROCESS.md` for the full lifecycle (a new `3-integrated` stage was added
the same day this index was built) and the working rules adopted alongside this index.

**94 RFCs total.** 27 draft, 1 under review, 17 accepted, 3 integrated (new stage — see
`PROCESS.md`) (48 "live" — need active tracking), 25 implemented, 9 superseded, 12
refused (46 "settled" — reference only). (RFC-0055 moved draft → superseded 2026-07-09,
reconciled into RFC-0092/0093/0095 — see below. **2026-07-10:** the allocator/lifetime
cluster — RFC-0063/0065/0066/0067/0068/0073/0077 — swept from under-review to accepted;
only RFC-0080 remains under review. Same day: RFC-0067a/0078/0083 became the first RFCs
to reach `3-integrated`, merged into `public/reference/spec/`; RFC-0067 renamed to
"Lifetime Anchors"; RFC-0084 refused, having reverted to a no-op.)

---

## ✅ RFC-0055 overlap — reconciled 2026-07-09

Found while building this index, resolved the same day: RFC-0055 ("Comptime," draft
since 2026-06-05) had gone undiscovered through this session's entire RFC-0092/0093/
0094 drafting, because no index existed to check against. Its foundational execution
model (`comptime let`, `comptime fun`'s restrictions, `comptime if`) was real and
missing from RFC-0092 — folded into RFC-0092 §0. Its recursion/allocation/error-message
open questions are now RFC-0092 Open Questions 6-8. Its aspect-inspection question
(OQ-4) is answered more precisely by RFC-0093's `@derive(Aspect)` registration. Its
`@cfg`-collapses-into-`comptime if` observation independently corroborates RFC-0095's
Open Question 4 rather than needing merging into it. RFC-0055 is now superseded
(`5-superseded/rfc-0055-comptime.md`) — kept as the first concrete proof that
`INDEX.md` and the check-before-opening-a-new-RFC rule (`PROCESS.md`) earn their keep.

---

## Comptime / Derive cluster (draft — the newest, least settled cluster)

All v0.5+, none implemented, none accepted. This is where the RFC-0055 overlap (above)
was found and reconciled, and where this session did most of its work.

- **RFC-0089** — Linear Types — multiplicity lattice, `Linear` auto-impl aspect. Depends
  on RFC-0071 (accepted). Partial consumption now routes through RFC-0090's `ToRecord`,
  not a bespoke mechanism (revised 2026-07-09).
- **RFC-0090** — Structural Records — Rows and Tiers — `HasField`/`Lacks`, `record`
  type-former, three-tier capability model. No dependency on comptime.
- **RFC-0091** — Linear Records — per-field multiplicity, automatic-downgrade partial
  consumption, the `uses(fd)` Drop mechanism. Depends on RFC-0089 + RFC-0090.
- **RFC-0092** — Comptime Core — `type`-as-value, `typeinfo`, single-declaration
  `emit`, plus (as of the RFC-0055 reconciliation) the base `comptime let`/`fun`/`if`
  execution model. Dependency root of 0093/0094.
- **RFC-0093** — Derive Registration — `@derive(Aspect)` as request + registration.
  Depends on RFC-0092. RFC-0080's `Clone` derive depends on this. Answers RFC-0055's
  aspect-inspection open question.
- **RFC-0094** — Comptime Metaprogramming — generalized `emit`, comptime-callable
  parsing, diagnostics, body-reflection scoping. Depends on RFC-0092 only; independent
  of RFC-0093.
- **RFC-0095** — Attributes and Metadata — `@` syntax, attributes as comptime-visible
  metadata. Mostly independent; only §2 depends on RFC-0092.
- **RFC-0062** — Ord/Eq Comparison Aspects — `Eq`/`Ord`/`Ordering` in `std::core`.
  RFC-0093's Derivable Aspects table assumes these exist; not cross-checked against
  RFC-0062's actual signatures.
- **RFC-0011** — Operator Overloading Aspects — operator desugaring. RFC-0093 notes
  derived `Eq`/`Ord` depend on this.
- **RFC-0039** — `aspect` Alias Syntax — vehicle for RFC-0089's `Affine` alias
  (`!Copy + !Linear`). Small, standalone.

## Region / Allocator / Lifetime cluster (accepted 2026-07-10 — ratified, Phase 3's dependency now clear)

The cluster the roadmap tried to get to "accepted, ready to implement" for weeks. Ratified
2026-07-10 via a consistency pass before sweeping: RFC-0063 §9 items 1/2/5 (allocator
teardown discipline, `drop` interaction, partial consumption) were still written up as
open/blocking, even though `reports/implementation/roadmap-2026-07-07.md`'s Phase 0 had
already resolved them in a separate document three days earlier and never synced back —
now fixed in RFC-0063 itself. RFC-0066 and RFC-0068's frontmatter titles/filenames also
still said "Region ..." after the rest of the cluster renamed region → allocator; renamed
to match (`rfc-0066-allocated-value-extraction.md`, `rfc-0068-struct-owned-allocators.md`),
plus a few stale cross-reference bugs (a self-contradictory syntax note, a wrong section
number, a backwards RFC-0067a split direction).

- **RFC-0063** *(accepted)* — Allocator Handles — the allocator half of the old "region
  handles" premise. Central to the whole cluster.
- **RFC-0065** *(accepted)* — Allocator and Lifetime Ergonomics — elision rules for both
  channels. Depends on RFC-0063 + RFC-0067.
- **RFC-0066** *(accepted)* — Allocated Value Extraction — individual drop/move-out; the
  RFC that triggered the whole cluster-wide split. Renamed from "Region Pointer
  Extraction" 2026-07-10 to match how every other RFC already referred to it.
- **RFC-0067** *(accepted)* — Lifetime Anchors — the narrowed remainder after RFC-0067a
  was split out and accepted separately. Renamed 2026-07-10 from "Lifetime Anchors and
  Allocator-Pointer References" (`rfc-0067-lifetime-anchors.md`) — the dropped half of
  the title duplicated RFC-0063/RFC-0066's own naming.
- **RFC-0067a** *(integrated 2026-07-10)* — Reference Types — plain `&T`/`&mut T`,
  auto-deref. No allocator/borrow-checker dependency; already sequenced into Cluster A.
  Integrated into `public/reference/spec/types.md` and `expressions.md`; gained a new
  §3a (type-directed value-copy-out) resolving a gap found writing the worked examples.
  Not yet implemented — tracked at the RFC's `impl_tracking` link.
- **RFC-0068** *(accepted)* — Struct-Owned Allocators — primary-constructor syntax
  (`struct Foo(@a: BumpAlloc)`). Renamed from "Struct-Owned Regions" 2026-07-10.
- **RFC-0073** *(accepted)* — AutoAlloc — renamed from AutoRegion; SubRegion interaction
  dropped.
- **RFC-0077** *(accepted)* — Allocator Generics — `<A: Alloc>` impl headers, variance
  for `@a T`.
- **RFC-0074** *(draft)* — Shared Pointers (Rc/Arc) — blocked on RFC-0076 (brand
  introduction mechanism unresolved).
- **RFC-0075** *(draft, parked)* — Region Inference — deliberately deferred until
  real annotation-burden data exists.
- **RFC-0076** *(draft)* — Brand Types — phantom identity parameters; RFC-0074 and
  RFC-0090's tier-3 `(row, brand)` idea both depend on this.

## Aspect system core (accepted — the stable foundation)

Nothing open here; these are the load-bearing accepted RFCs everything else cites.

- **RFC-0008** — Aspect Objects — `dyn Aspect`, vtable dispatch.
- **RFC-0036** — Conditional Impl Blocks.
- **RFC-0037** — Return-Position `impl Aspect`.
- **RFC-0060** — Aspect Impl Coherence — orphan rule, overlap detection, auto-impl.
  Prerequisite for most of the above and below.
- **RFC-0061** — Structural Aspect Bounds — `T[]`/tuples/function-type bounds.
- **RFC-0071** — Ownership and Move Semantics — affine-by-default foundation.
- **RFC-0072** — Negative Bounds — `T: !Aspect`.
- **RFC-0078** *(integrated 2026-07-10)* — Bottom Type `!` — subtyping, coercion, match
  exhaustiveness, inhabited-singleton coercion, `-> !` returns. Integrated into
  `public/reference/spec/types.md`; §4.2's stale pre-split allocator syntax fixed first.
  Not yet implemented.
- **RFC-0079** — `Perhaps<T>` and `Result<T, E>`.
- **RFC-0081** — Negative Impls — `impl !Aspect for Type`.
- **RFC-0082** — Associated Types.
- **RFC-0083** *(integrated 2026-07-10)* — Public Value Exports (`pub let`). Integrated
  into `public/reference/spec/modules.md`. Motivating example rewritten — the original
  `heap`/`local_heap` case is obsolete under the ratified allocator design (RFC-0063/0065
  reference them by type name, no instance value needed); replaced with exported-constant
  examples. Not yet implemented.
## Linear closures / concurrency

- **RFC-0049** *(draft)* — `linear fun` Type System — unconsumed-scope-exit, `Drop`
  interaction, subtyping vs. plain `fun`.
- **RFC-0050** *(draft)* — Closure Capture Lists — `&mut`/`move`/clone/`&` specifiers.
  `&mut`/clone/`&` buildable now; `move` waits on a split-model successor to refused
  RFC-0046.
- **RFC-0003** *(draft)* — Concurrency Model — fiber handles, channels, `select`,
  `Send`.
- **RFC-0064** *(draft, retracted)* — Structured Fork-Join Parallelism — the `||`
  combinator dropped; its one guarantee relocated onto `JoinHandle<T>`.

## Small, mostly standalone syntax/ergonomics items

- **RFC-0004** — `main()` return type — should it return `Result`?
- **RFC-0005** — Warn on unreachable match arms — **empty stub, no content written.**
- **RFC-0014** — Panic Recovery.
- **RFC-0015** — Unwrap Syntax — `.yolo()` vs. a keyword (resolved in practice by
  accepted RFC-0079, which specifies `.yolo()` as a method; this RFC may be
  supersedable).
- **RFC-0017** — Language Edition System.
- **RFC-0026** — Unsafe Blocks — deferred, depends on a stable memory-safety model
  (RFC-0028, refused — needs re-pointing at whatever supersedes it).
- **RFC-0027** — C FFI.
- **RFC-0033** — Field-Level Mutability — additive `let` field annotation.
- **RFC-0038** — `impl Aspect` in Struct Fields / Existential Types.
- **RFC-0052** *(draft, on hold)* — Lifetime System — held pending the memory-strategy
  reconsideration.

---

## Settled (reference only — not part of active tracking)

**Implemented (25):** RFC-0006, 0007, 0010, 0018-0023, 0030-0032, 0034, 0035, 0040-0045,
0053, 0054, 0057-0059.

**Superseded (9):** RFC-0001 (→ later pointer work), RFC-0002 (aspect bound syntax),
RFC-0009 (module system → RFC-0030), RFC-0012 (→ RFC-0092/0093/0094/0095), RFC-0013
(integer overflow), RFC-0016 (stdlib foundation), RFC-0024 (linear types → RFC-0028,
which was then refused — RFC-0089 re-homes this), RFC-0029 (module system gaps),
RFC-0055 (comptime → RFC-0092/0093/0095, reconciled 2026-07-09 — see above).

**Refused (12):** RFC-0025, 0028, 0046-0048, 0051, 0056, 0069, 0084, 0085-0087 — mostly
the earlier region/lifetime model iterations that didn't survive the 2026-07-05 split,
plus RFC-0046 (linear closure capture, blocking RFC-0050's `move` half), plus RFC-0084
(refused 2026-07-10 — reverted in place to reaffirm RFC-0053's `[T; N]`/`[expr; N]`
exactly, with nothing left of its own to propose).

---

## Maintenance note

This file is a manual snapshot, not a generated artifact — there's no script producing
it. If RFCs move between directories or new ones land, this drifts silently. Treat
"last_built" in the frontmatter as the trust boundary: anything changed after that date
isn't reflected here yet.
