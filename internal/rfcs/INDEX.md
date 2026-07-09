---
id: rfc-index
title: "RFC Index"
type: index
last_built: '2026-07-09'
---

# RFC Index

Generated 2026-07-09. Not auto-regenerated — rebuild it (or ask for a rebuild) whenever
RFCs are added, moved, or change status; it will drift otherwise. Grouped by theme, not
by number, because number order tells you nothing about what's related. See
`PROCESS.md` for the full lifecycle (a new `3-integrated` stage was added the same day
this index was built) and the working rules adopted alongside this index.

**94 RFCs total.** 27 draft, 8 under review, 14 accepted, 0 integrated (new stage — see
`PROCESS.md`) (49 "live" — need active tracking), 25 implemented, 9 superseded, 11
refused (45 "settled" — reference only). (RFC-0055 moved draft → superseded 2026-07-09,
reconciled into RFC-0092/0093/0095 — see below.)

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

## Region / Allocator / Lifetime cluster (under review — Phase 3's actual blocker)

The cluster the roadmap has been trying to get to "accepted, ready to implement" for
weeks. Internally consistent as of the 2026-07-05/07 rewrites; the remaining work is
sequencing and final sign-off, not open design questions.

- **RFC-0063** — Allocator Handles — the allocator half of the old "region handles"
  premise. Central to the whole cluster.
- **RFC-0065** — Allocator and Lifetime Ergonomics — elision rules for both channels.
  Depends on RFC-0063 + RFC-0067.
- **RFC-0066** — Region Pointer Extraction — individual drop/move-out; the RFC that
  triggered the whole cluster-wide split.
- **RFC-0067** — Lifetime Anchors and Allocator-Pointer References — the narrowed
  remainder after RFC-0067a was split out and accepted separately.
- **RFC-0067a** *(accepted)* — Reference Types — plain `&T`/`&mut T`, auto-deref. No
  allocator/borrow-checker dependency; already sequenced into Cluster A.
- **RFC-0068** — Struct-Owned Allocators — primary-constructor syntax
  (`struct Foo(@a: BumpAlloc)`).
- **RFC-0073** — AutoAlloc — renamed from AutoRegion; SubRegion interaction dropped.
- **RFC-0077** — Allocator Generics — `<A: Alloc>` impl headers, variance for `@a T`.
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
- **RFC-0078** — Bottom Type `!`.
- **RFC-0079** — `Perhaps<T>` and `Result<T, E>`.
- **RFC-0081** — Negative Impls — `impl !Aspect for Type`.
- **RFC-0082** — Associated Types.
- **RFC-0083** — Public Value Exports.
- **RFC-0084** — Fixed-Size Array Syntax `T[N]` — supersedes RFC-0053's syntax only.

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

**Refused (11):** RFC-0025, 0028, 0046-0048, 0051, 0056, 0069, 0085-0087 — mostly the
earlier region/lifetime model iterations that didn't survive the 2026-07-05 split, plus
RFC-0046 (linear closure capture, blocking RFC-0050's `move` half).

---

## Maintenance note

This file is a manual snapshot, not a generated artifact — there's no script producing
it. If RFCs move between directories or new ones land, this drifts silently. Treat
"last_built" in the frontmatter as the trust boundary: anything changed after that date
isn't reflected here yet.
