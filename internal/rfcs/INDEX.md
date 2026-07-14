---
id: rfc-index
title: "RFC Index"
type: index
last_built: '2026-07-14'
---

# RFC Index

Generated 2026-07-09, last updated 2026-07-10. Not auto-regenerated — rebuild it (or ask
for a rebuild) whenever RFCs are added, moved, or change status; it will drift otherwise.
Grouped by theme, not by number, because number order tells you nothing about what's
related. See `PROCESS.md` for the full lifecycle (a new `3-integrated` stage was added
the same day this index was built) and the working rules adopted alongside this index.

**103 RFCs total.** 31 draft, 1 under review, 13 accepted, 3 integrated (new stage — see
`PROCESS.md`) (48 "live" — need active tracking), 32 implemented, 10 superseded, 13
refused (53 "settled" — reference only). **2026-07-13:** RFC-0036 (Conditional Impl
Blocks) implemented (issue #241) — see its entry below for a correctness bug found and
fixed during review (conditional-impl satisfaction wasn't consulted outside direct
method dispatch) and two coherence-negation fixtures restored after the original
implementation had incorrectly skipped them as unsupported. RFC-0037 (Return-Position
`impl Aspect`) also implemented the same day (issue #240) — see its entry below for a
real `TypeVar`-generator aliasing bug and a fully-disconnected opacity-enforcement
mechanism found and fixed during review.
RFC-0061 (Structural Aspect Bounds) also integrated the same day, ahead of implementing
issue #245 — see its entry below for three real, previously-uncalled-out implementation
bugs found during integration that block any structural impl from working today.
RFC-0097 (Orphan Rule for Bare-Parameter Blanket Impls) accepted and integrated the
same day (issue #269) — the narrow gap RFC-0036's own integration had flagged as
deferred. Also, three sibling surface-syntax
RFCs opened from the same review — RFC-0098 (Surface Keyword Renames, amends
RFC-0032/0042/0044/0067A's surface syntax only, no semantic change), RFC-0099
(Dot-Separated Module Paths, `::` → `.`), RFC-0100 (Constructor-Call Construction,
struct literals → call syntax, really a general-keyword-arguments RFC); see "Small,
mostly standalone syntax/ergonomics items" below. **2026-07-14:** both RFC-0099 and
RFC-0100's own disambiguation questions were reviewed and resolved — RFC-0099 rejected
capitalization-based path disambiguation after it failed against real fixture code, in
favor of name-resolution-time resolution, and also respelled turbofish (`::<` → `.<`)
alongside its own `::` → `.` change; RFC-0100's keyword-argument/ascription grammar
collision (not previously identified) was found and resolved via `arg_list` reordering.
That review also produced a fourth sibling, RFC-0101 (Grammar-Enforced Naming Case
Conventions) — PascalCase types, camelCase `fun` declarations, snake_case everything
else, enforced as a real compile-time rule — scoped as its own RFC rather than folded
into RFC-0100, whose ambiguity it narrows but doesn't fully resolve on its own. A fifth,
RFC-0102 (Bodyless Extend Blocks for Marker Aspects and Negative Impls), followed from
using RFC-0098's new `extend Type: Aspect` syntax directly — `extend Type: Aspect;` /
`extend Type: !Aspect;` as sugar for an empty body, mirroring `fun_decl`'s own existing
`(block | ";")` alternative, no new semantic category. A sixth, RFC-0103 (Bodyless
Aspect Declarations and Struct-Embedded Aspect Lists), followed directly from
RFC-0102 — a bodyless spelling for the aspect *declaration* itself (`aspect Copy2;`,
pure sugar, no permanence attached), plus embedding RFC-0102's aspect list straight
into a struct/enum's own declaration. RFC-0098, 0099, 0100, and 0102 all moved
`0-draft` → `2-accepted` the same day, after this review resolved every open question
each RFC had — RFC-0102 additionally retired the old `extend Type: !Aspect { }` braces
spelling outright (bodyless is now mandatory for negative impls, not just sugar),
matching this project's precedent for retiring a strictly-superseded spelling
(RFC-0100, RFC-0042) rather than keeping two. RFC-0103 went through several more
revisions: positive struct/enum-embedded items no longer require a `marker` keyword
outright — every positive aspect now declares a checked, module-wide *obligation*
discharged by an ordinary `extend` block elsewhere, once it was clear the
no-escape-hatch concern only applies to items the list itself tries to implement
inline; a third idea (letting an `extend` block share a real body across multiple
aspects) was split out into a seventh sibling, RFC-0104 (Multi-Aspect Extend Blocks
with Shared Bodies), since it doesn't depend on anything specific to RFC-0103; and
finally the `marker` keyword itself was dropped outright once the obligation model
made its permanence guarantee moot — RFC-0103's bodyless-declaration sugar (§1) now
inherits exactly RFC-0102's own weaker "currently has zero methods" rule instead.
RFC-0101 and RFC-0104 remain `0-draft`, not assumed to land with the others.
**2026-07-12:** RFC-0081 (Negative Impls)
implemented on sprint/26 (issue #264) — syntax, finality, and the orphan rule are done
and tested; priority over blanket impls is a property of RFC-0036 (issue #241), not
that RFC's own implementation yet — but negative-bound consultation is now covered,
since RFC-0072 (Negative Bounds) was also implemented the same day (issue #243):
enforcement at all function-call and generic-literal-construction sites, by inverting
the same `impl_aspect_env_has` lookup the positive-bound check already uses.
**2026-07-13:** RFC-0082 (Associated Types) implemented on sprint/26 (issue #242) —
real `T::AssocType` projection resolution (both at generic call sites and inside
still-abstract function bodies), equality-constrained bounds, impl-completeness
checking, and bare-name sugar in both directions; §6 object safety remains blocked
on RFC-0008 (`dyn Aspect`, no consumer yet). (RFC-0055 moved draft → superseded 2026-07-09,
reconciled into RFC-0092/0093/0095 — see below. **2026-07-10:** the allocator/lifetime
cluster — RFC-0063/0065/0066/0067/0068/0073/0077 — swept from under-review to accepted;
only RFC-0080 remains under review. Same day: RFC-0067a/0078/0083 became the first RFCs
to reach `3-integrated`, merged into `public/reference/spec/`; RFC-0067 renamed to
"Lifetime Anchors"; RFC-0084 and RFC-0079 refused, both redundant with — or, for
RFC-0079's `?`-operator text, factually superseded by — already-shipped behavior.
RFC-0072/0081/0082 followed into `3-integrated` the same day, each with its own stale
pre-split/dangling-reference fixes first — see `PROCESS.md`'s backlog note. **2026-07-11:**
RFC-0060 (Aspect Impl Coherence) integrated on its own, ahead of implementing issue #238
— see the Aspect system core section below. RFC-0080 stays under review (moved there
2026-07-09 over `#[derive]` syntax, `4d1ec42`, unrelated to the point below — a stale
non-worktree checkout of `main` elsewhere on disk still shows it as accepted, but this
branch's own history is ahead of that checkout and is authoritative). Implementing
issue #238 exposed that RFC-0080/0089/0061 each cite "the auto-impl pattern" without
any one of them owning it as a mechanism, so RFC-0096 was opened to formalize the
recognition rule and the shared structural-composition algorithm — no behavior change
to `Send`/`Sync`/`Linear`. Same review pass, a follow-up question about blanket impls
surfaced a second, related gap: RFC-0060 §1's orphan rule has no answer for
`impl<T: Bound> Aspect for T` — a bare-parameter blanket, the exact form RFC-0060's
own §3/§5 and RFC-0080 §1.2 all use as their running example, but never revisited by
§1 itself. RFC-0097 opened to formalize it. RFC-0067a (Reference Types) implemented in
`metel-core` the same day, moving `3-integrated` → `4-implemented` — the first RFC
from this session's integration pass to complete that step; its §3a amended once more
to state that read-copy fires at `return`/tail-expression positions too and that
read-copy/write-through/auto-deref all chain through multiple reference layers, both
gaps found only by the implementation's own regression tests. **2026-07-12:** RFC-0083
(Public Value Exports) moved `3-integrated` → `5-superseded`, folded into RFC-0092 §0a
— see the RFC-0083 fold note below. The 4 remaining in `3-integrated` are
RFC-0060/0072/0081/0082 (RFC-0078 also left `3-integrated` already, for
`4-implemented`, alongside RFC-0067a on 2026-07-11).)

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

## ✅ RFC-0083 folded into RFC-0092 — 2026-07-12

RFC-0083 (Public Value Exports, `pub let`) had reached `3-integrated` requiring `pub
let` initializers to be "constant expressions," a concept it never specified itself —
it deferred that definition to RFC-0092, while RFC-0092 only carried the connection as
a pending open question ("added 2026-07-11"). Neither RFC actually owned the
restriction it depended on. Surfaced while deciding whether to implement Codeberg issue
#235 (RFC-0083's tracking issue): implementing `pub let` as drafted would have meant
building a bespoke restricted evaluator now, then reconciling it against `comptime let`
later once RFC-0092 lands. Resolved instead by folding RFC-0083 into RFC-0092 §0a:
public value exports are `pub` applied to `comptime let`, not a parallel mechanism.
Issue #235 closed unimplemented. RFC-0083 is now superseded
(`5-superseded/rfc-0083-public-value-exports.md`); `public/reference/spec/modules.md`'s
`pub let` section (added when RFC-0083 integrated) was reverted to its pre-integration
wording ("public value exports are not supported in the current version"), since the
feature is no longer backed by a settled RFC — the mechanism now lives in draft-stage
RFC-0092 instead, gated on that RFC's own v0.5+ timeline (a real cost, noted in
RFC-0092's own Timing Recommendation).

---

## Comptime / Derive cluster (draft — the newest, least settled cluster)

All v0.5+, none implemented, none accepted. This is where the RFC-0055 overlap (above)
was found and reconciled, and where this session did most of its work.

- **RFC-0089** — Linear Types — multiplicity lattice, `Linear` auto-impl aspect. Depends
  on RFC-0071 (accepted). Partial consumption now routes through RFC-0090's `ToRecord`,
  not a bespoke mechanism (revised 2026-07-09). `Linear`'s auto-impl categorization
  now depends on RFC-0096 for the shared mechanism it's an instance of.
- **RFC-0090** — Structural Records — Rows and Tiers — `HasField`/`Lacks`, `record`
  type-former, three-tier capability model. No dependency on comptime. §1 calls
  `HasField` an extension of RFC-0080's auto-impl pattern; RFC-0096 §7 (2026-07-11)
  works out that it's a family with existential satisfaction, not the same mechanism
  as `Send`/`Sync`/`Linear`, and flags two gaps RFC-0090 itself leaves open
  (whether `HasField` goes through impl coherence at all; a string-literal bound
  argument `grammar.md` doesn't cover).
- **RFC-0091** — Linear Records — per-field multiplicity, automatic-downgrade partial
  consumption, the `uses(fd)` Drop mechanism. Depends on RFC-0089 + RFC-0090.
- **RFC-0092** — Comptime Core — `type`-as-value, `typeinfo`, single-declaration
  `emit`, plus (as of the RFC-0055 reconciliation) the base `comptime let`/`fun`/`if`
  execution model, plus (as of the RFC-0083 fold, 2026-07-12) `pub` on `comptime let`
  for public value exports (§0a). Dependency root of 0093/0094.
- **RFC-0093** — Derive Registration — `@derive(Aspect)` as request + registration.
  Depends on RFC-0092. RFC-0080's `Clone` derive depends on this. Answers RFC-0055's
  aspect-inspection open question. Deliberately excludes auto-impl aspects
  (`Send`/`Sync`/`Linear`) from its scope — see RFC-0096.
- **RFC-0096** — Auto-Impl Aspects — formalizes the recognition rule (closed,
  compiler-intrinsic list, not a declaration-level marker) and the shared
  structural-composition algorithm that RFC-0080 §3.2/§4.2 and RFC-0089 §2 each
  independently invoke as "the auto-impl pattern" without either owning it. Opened
  2026-07-11 while implementing issue #238 (Aspect Impl Coherence pipeline), which
  confirmed `AspectDecl` carries no such marker today. Fleshed out same day: §3
  covers generic types (an auto-impl on a generic struct/enum is an implicit
  RFC-0036 conditional impl, never evaluated eagerly); §4 corrects a plausible
  misreading of RFC-0061 §5's heading — `Drop`'s array-only propagation is not a
  fourth instance of this mechanism, since RFC-0071 §3 already makes `Drop` opt-in
  for structs/enums. Also found, in passing, that RFC-0050 independently derived
  the same closure-capture `Send` rule without citing a shared source — a fourth
  uncited instance of the pattern this RFC names. **Corrected later 2026-07-11:** §1's
  "closed list of three" claim was itself wrong — RFC-0090 §1 independently calls
  `HasField`/`Lacks` an extension of this same pattern, missed on the first pass
  (different INDEX.md cluster). New §7 explains why it's related but not a fourth
  fixed-marker instance (a parameterized family with existential, not universal,
  satisfaction — possibly outside the impl/coherence system entirely). 6 Unresolved
  Questions recorded (unit variants, raw pointers, `Linear`'s missing reference rule,
  the RFC-0061 §5 heading fix, whether the fixed-marker category is expected to grow,
  whether `HasField` goes through coherence at all). No behavior change to
  `Send`/`Sync`/`Linear` themselves.
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
- **RFC-0067a** *(implemented 2026-07-11)* — Reference Types — plain `&T`/`&mut T`,
  auto-deref. No allocator/borrow-checker dependency; already sequenced into Cluster A.
  Integrated into `public/reference/spec/types.md` and `expressions.md`; gained a new
  §3a (type-directed value-copy-out) resolving a gap found writing the worked examples.
  Implemented in `metel-core` (issue #236); §3a amended the same day to state that
  read-copy fires at `return`/`break`/tail-expression positions too (not just `let`/
  ascription) and that read-copy, write-through, and auto-deref all chain through
  multiple reference layers — both found only once the implementation's own regression
  tests exercised a `&&T`-shaped case.
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

The load-bearing accepted RFCs everything else cites. One open item as of 2026-07-11
(RFC-0097, below) — a narrow gap found by scrutiny, not a design problem with the
cluster itself. **Resolved 2026-07-13**: RFC-0097 integrated (issue #269 tracks
implementation).

- **RFC-0008** — Aspect Objects — `dyn Aspect`, vtable dispatch.
- **RFC-0061** *(integrated 2026-07-13)* — Structural Aspect Bounds — `T[]`/tuples/
  function-type bounds. Depends on RFC-0060 (integrated) and RFC-0036 (implemented,
  2026-07-13) — both landed, so implementation is now unblocked. Integrated into
  `public/reference/spec/declarations.md` as a new "Structural Aspect Bounds" section
  right after Aspect Implementation Coherence (also corrected that section's own
  stale "not yet implemented" banner to reflect #238/#243/#264's partial progress).
  No error-code collision (reuses T0012, consistent with RFC-0036's precedent).
  Found during integration, by direct testing against current source rather than
  assumption: contrary to what this RFC's dependents (and the anticipatory `RFC-0061`
  comments already in `construction.rs`/`registry.rs` from #233) assumed, structural
  impls are NOT in a safe "parses fine, just missing real semantics" state today —
  three independent bugs (an unconditional internal-error crash in `inference.rs` for
  any non-named impl target, a hardcoded array-method-call gate that blocks aspect
  dispatch on arrays before it's ever attempted, and a registry pass that silently
  skips registering structural targets) block ANY structural impl from working at
  all, regardless of whether it declares its own generics. Flagged as groundwork
  issue #245 must fix first — not a gap in this RFC's own content. §5 (auto-impl
  propagation through arrays) and §7.2 (function-pointer auto-derived aspects) are
  marked not-yet-implemented pending the auto-impl mechanism itself, which doesn't
  exist for any type yet (confirmed: zero references anywhere in source) — the same
  blocker RFC-0060 §4's own auto-impl rule already has.
- **RFC-0071** — Ownership and Move Semantics — affine-by-default foundation.
- **RFC-0036** *(implemented 2026-07-13, was integrated 2026-07-13)* — Conditional Impl
  Blocks — `impl Aspect for Type<T> where T: Bound`, both inline and `where`-clause
  forms. Integrated into `public/reference/spec/declarations.md` right after the basic
  `impl Aspect for Type` example. Fixed a stale error-code collision while integrating:
  the RFC's own §4 example used `T0013`, already claimed (ambiguous aspect
  method/associated-type resolution) by the time this integrated — corrected to reuse
  `T0012` instead, per RFC-0072's own precedent for the negative-bound direction.
  Explicitly defers bare-parameter blanket impls (`impl<T: Bound> Aspect for T`) to
  RFC-0097 (now integrated, 2026-07-13) — every example in this RFC targets a
  genuinely named type. Worked
  example checks composition with RFC-0082's equality-constrained bounds (both are the
  same `Bound` structure, so no new machinery needed). Implemented (issue #241):
  registry/inference/construction bound-gated impl support, coherence disjointness
  detection (including syntactic negation, §3.1), use-site bound enforcement at every
  point the aspect is required. Independent review found and fixed a real gap the
  implementation's own self-report missed: conditional-impl satisfaction was only
  consulted for direct method dispatch on the receiver, not when the conditionally-
  implementing type was passed through an *unrelated* generic function's own bound —
  such calls were unconditionally rejected regardless of whether the bound actually
  held. Also restored two coherence-negation fixtures (this RFC's own §3.1 examples)
  that the implementation had skipped on a mistaken belief the parser didn't support
  `!Aspect` bounds — it does, at every level (inline, `where`-clause, and impl-level
  polarity). This resolves the "priority over blanket impls"/"blanket-impl-aware
  discharge" blockers noted in RFC-0060, RFC-0072, and RFC-0081's own entries below —
  #244 (2026-07-13) landed that remaining work; see those RFCs' own entries.
- **RFC-0037** *(implemented 2026-07-13, was integrated 2026-07-13)* — Return-Position
  `impl Aspect` — opaque, monomorphised-per-function return types. Integrated into
  `public/reference/spec/declarations.md` right after the parameter-position `impl
  Aspect` shorthand. Worked example checks composition with RFC-0082 (Associated
  Types): a function returning `impl Container` still resolves `Container::Item`
  correctly through the caller's method calls, since the opaque type is a real
  concrete type internally, erased only from the caller's naming surface. Implemented
  (issue #240): per-quantified-var opaque metadata, linked/unlinked discrimination,
  definition-time bound checking, and real opacity enforcement (T0018) checked
  incrementally per-constraint rather than once at the end of solving (see ADR-0044 —
  the end-of-solve version can't tell a legitimate `impl Aspect`-to-`impl Aspect`
  pass-through apart from an actual violation). Independent review found and fixed a
  real `TypeVar`-generator bug that aliased independent opaque-returning calls once
  three or more appeared in one scope, and that the opacity check itself had been
  left entirely disconnected (never called) despite existing in the source.
- **RFC-0060** *(integrated 2026-07-11)* — Aspect Impl Coherence — orphan rule, overlap
  detection, closed-world assumption, auto-impl, negative-impl priority. Integrated
  ahead of implementing issue #238 (the coherence pipeline it specifies), on its own,
  since it cross-references two already-integrated RFCs. Integrated into
  `public/reference/spec/declarations.md` as a new section; two forward-references in
  Negative Bounds/Negative Impls that had anticipated this now point here. Surfaced a
  real, unrelated bug: RFC-0033's recommended error code (T0014) was already claimed
  by this RFC's own orphan-rule error — flagged in RFC-0033 rather than silently
  colliding. `impl_status: in-progress` as of 2026-07-12 (issue #244) — orphan rule,
  concrete-impl overlap (#238), and negative-vs-concrete-positive conflict (#264) are
  done. **Correction 2026-07-13:** the closed-world negative-bound discharge line item
  here previously cited RFC-0072/#243 as the blocker — #243 landed 2026-07-12 (issue
  #243, negative bounds now enforced) but only for the concrete-impl-only case, per its
  own explicit scope; the blanket-impl-aware half of discharge this section describes
  was blocked on RFC-0036/#241, the same as blanket-impl disjointness/priority.
  **Update 2026-07-13 (later):** RFC-0036/#241 has now landed (implemented), so both
  are unblocked — actually wiring the blanket-impl-aware discharge and disjointness/
  priority logic remains open under this issue (#244). Auto-impl rules
  (RFC-0080/RFC-0096) remain unblocked-but-unimplemented on their own timeline,
  unrelated to #241.
  **Update 2026-07-13 (later still):** #244 landed — blanket-impl-aware negative-bound
  discharge (both polarities, at struct/enum literal construction and RFC-0082 assoc-
  type completeness), blanket-vs-concrete overlap detection (via a shape-crossing
  compatibility check replacing the old exact-key grouping), and negative-impl
  priority over a blanket positive impl (a new `neg_impl_env` registry table) are all
  implemented now, without disturbing the existing negative-vs-concrete-positive
  conflict rule (RFC-0081 §2.2/#264). Only §4 auto-impl rules remain unimplemented.
- **RFC-0097** *(integrated 2026-07-13)* — Orphan Rule for Bare-Parameter Blanket
  Impls. RFC-0060 §1's orphan rule assumes every impl target has an outermost type
  constructor to check — but a bare-parameter blanket (`impl<T: Bound> Aspect for T`,
  the exact form RFC-0060 §3/§5 and RFC-0080 §1.2 all use as their own running
  example) has none. Formalizes that target-locality is vacuously unsatisfiable for
  this shape, so such an impl is permitted only via the aspect side; no new syntax,
  no new error code (reuses T0014), no new overlap-detection machinery (the
  orphan-rule fix alone confines any one aspect's bare-parameter blanket to a single
  module). Opened 2026-07-11, same review pass as RFC-0096. Integrated into
  `public/reference/spec/declarations.md`, expanding the existing "not covered by
  this section" deferral note (added while integrating RFC-0036) into full spec
  content with its three worked examples. Not yet implemented (issue #269) —
  `coherence.rs`'s `outermost_id` has no explicit case for "target is the impl's own
  generic parameter" today; it happens to often return `None` for one by incidental
  name-resolution failure, not by a deliberate check, the same fragile-by-accident
  pattern #241 and #245 each had to fix for their own target shapes.
- **RFC-0072** *(implemented 2026-07-12, was integrated 2026-07-10)* — Negative Bounds
  — `T: !Aspect`. Integrated into `public/reference/spec/declarations.md`; its own
  stale bracket-channel allocator examples (`@[r] T`) fixed first. Implemented (issue
  #243): enforcement at all four function-call-expression branches plus generic
  struct/enum literal construction, by inverting the same lookup the positive-bound
  check already uses (this also means negative impls, RFC-0081/#264, are correctly
  consulted for free). §2.3 Copy-implies-!Drop implemented as a narrow, name-literal
  override, per the RFC's own "do not generalize" wording. **Update 2026-07-13:**
  that shared lookup was `impl_aspect_env_has` at the time #243 landed — since
  corrected, while implementing RFC-0036/#241, to `type_satisfies_aspect`, which also
  consults conditional impls (`impl_aspect_env_has` alone can't see those, so a
  negative bound against a conditionally-implementing type was being evaluated
  incorrectly until this fix). Blanket-impl-aware discharge (RFC-0060 §3's fuller
  closed-world form) was blocked on RFC-0036/#241; that dependency has now landed,
  unblocking it. **Update 2026-07-13 (later):** #244 landed the discharge/priority
  logic itself — the `TODO(#241)` comments at each check site are resolved.
- **RFC-0078** *(implemented 2026-07-12)* — Bottom Type `!` — subtyping, coercion, match
  exhaustiveness, inhabited-singleton coercion, `-> !` returns. Integrated into
  `public/reference/spec/types.md`; §4.2's stale pre-split allocator syntax fixed first.
  Implemented in metel-core sprint/25 (issue #234): `!` surface syntax (grammar),
  `panic(msg)` native, general uninhabited-variant exhaustiveness (subsuming
  `Result<T, !>` as the general rule's special case rather than a hardcoded one),
  inhabited-singleton coercion, and `-> !` divergence checking. §4.2 (allocator
  collapse) intentionally out of scope — depends on RFC-0063's allocator syntax,
  not yet implemented.
- **RFC-0081** *(implemented 2026-07-12, was integrated 2026-07-10)* — Negative
  Impls — `impl !Aspect for Type`. Syntax, finality (conflict with a concrete
  positive impl), and the orphan rule are implemented and tested (issue #264).
  Negative-bound consultation (SS2.3) is now implemented too (issue #243,
  RFC-0072/2026-07-12): `T: !Aspect` checking inverts the same
  `impl_aspect_env_has` lookup (since corrected to `type_satisfies_aspect`, see
  RFC-0072's entry above), which already excludes negative impls, so this
  composes correctly with no extra work. Priority over blanket impls (SS2.1) was
  a property of RFC-0036 (issue #241) — that RFC is now implemented (2026-07-13),
  and `register_aspect_impl` already refuses to register a negative impl as
  positive, so this composes correctly. **Update 2026-07-13 (later):** #244 landed
  the dedicated priority check itself (a `neg_impl_env` registry table consulted by
  `type_satisfies_aspect` before either positive path) — a concrete negative impl now
  overrides a blanket positive impl for its exact instantiation, without disturbing
  the existing negative-vs-concrete-positive conflict rule (§2.2/#264, confirmed by
  a regression this fix initially introduced and then corrected).
- **RFC-0082** *(implemented 2026-07-13, was integrated 2026-07-10)* — Associated
  Types. Integrated into `public/reference/spec/declarations.md`; stale
  `Region`/`@[r]` naming corrected to `Alloc`/`@a`, and §7 (amending retracted
  RFC-0069's `SubRegion`) marked historical-only rather than integrated. Implemented
  (issue #242): §1/§1.1/§1.2 declaration + bound enforcement + bare-name sugar
  (in both directions — explicit `T::AssocType` and an aspect's own bare-name
  method signatures, for concrete impls and generic dispatch alike), §2 impl
  completeness (new error code T0017), §3/§3a real projection resolution with
  ambiguity detection (T0013), §4 equality constraints
  (`Aspect<AssocType = Concrete>`). §6 object safety remains unimplemented —
  blocked on RFC-0008 (`dyn Aspect`), which has no consumer yet.
- **RFC-0083** *(superseded 2026-07-12, was integrated 2026-07-10)* — Public Value
  Exports (`pub let`). Reached `3-integrated` requiring "constant expression"
  initializers, a concept it never specified — deferred to RFC-0092, which only had it
  as an open question. Folded into RFC-0092 §0a instead of implementing as drafted; see
  the RFC-0083 fold note above. `modules.md`'s `pub let` section reverted to
  pre-integration wording. Codeberg issue #235 (tracking) closed unimplemented.

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
- **RFC-0015** — Unwrap Syntax — `.yolo()` vs. a keyword (resolved in practice: `.yolo()`
  is already implemented as a method, though as an interpreter special case rather than
  real dispatch — RFC-0079, which formalized this, was refused 2026-07-10 as redundant
  with already-shipped behavior; the dispatch fix is tracked at
  https://app.clickup.com/t/86cap1wzb, not by this RFC).
- **RFC-0017** — Language Edition System.
- **RFC-0026** — Unsafe Blocks — deferred, depends on a stable memory-safety model
  (RFC-0028, refused — needs re-pointing at whatever supersedes it).
- **RFC-0027** — C FFI.
- **RFC-0033** — Field-Level Mutability — additive `let` field annotation.
- **RFC-0038** — `impl Aspect` in Struct Fields / Existential Types.
- **RFC-0052** *(draft, on hold)* — Lifetime System — held pending the memory-strategy
  reconsideration.
- **RFC-0098** *(accepted 2026-07-14)* — Surface Keyword Renames — `extend Type` /
  `extend Type: Aspect` (reordered target-first, Swift precedent — not `impl X with Y`
  as first drafted), `pub` → `public`, `mut` → `var` (bindings, reference types, and
  reference expressions together). Three independent, purely lexical renames with no
  semantic change. Amends RFC-0032/0042/0044/0067A's surface syntax only — each
  already-implemented RFC's actual semantics (field-visibility enforcement, binding
  mutability, reference/auto-deref behavior, receiver dispatch) are untouched. Opened
  2026-07-13, accepted 2026-07-14.
- **RFC-0099** *(accepted 2026-07-14)* — Dot-Separated Module Paths — `::` → `.` for import/export,
  static/module, and enum-variant paths, and `::<` → `.<` for turbofish. Not a pure
  rename: `.` already means field/method access (RFC-0045), so this RFC has to settle a
  real disambiguation rule before the grammar change is well-formed. Capitalization-
  based disambiguation (Option A) was reviewed and rejected — it fails on real fixture
  code (`std::core::Perhaps::Some`, and the RFC's own worked example) since module path
  segments are lowercase, same as values; resolved at name-resolution time instead
  (Option B), reusing the existing `Expr::ResolvedPath` pattern already in the codebase.
  Turbofish (RFC-0023), found as a third, separate use of `::` this RFC also addresses,
  is respelled `.<` rather than left as `::<` (a "same disambiguation guarantee, just
  spelled to match" token substitution, not a new ambiguity). Amends RFC-0030's path
  grammar, reserved path roots (`root::`/`std::`/`self::`/`super::` → `.`-spelled), and
  RFC-0023's turbofish syntax. Opened 2026-07-13, accepted 2026-07-14.
- **RFC-0100** *(accepted 2026-07-14)* — Constructor-Call Construction — `Type { field: value }` struct
  literals → `Type(field: value)` call-shaped construction. Real deliverable is general
  keyword arguments for function calls, not a struct-only rename — struct construction
  is just the first consumer. Like RFC-0099, not a pure addition: keyword arguments
  collide with the existing type-ascription expression (RFC-0023) at the grammar level
  (`Foo(bar: Baz)` is ambiguous between a keyword argument and an ascribed positional
  argument) — resolved by reordering `arg_list` to try a keyword-argument shape before
  falling through to plain `expr`, at the cost of no longer being able to write a bare
  ascribed variable as an unparenthesized positional call argument. Pattern-matching
  destructuring explicitly keeps its current `{ field }` syntax (deliberate asymmetry,
  not an oversight — see the RFC's own §4). Old literal syntax retired outright rather
  than kept as a second spelling, following RFC-0042's own precedent against permanent
  transition aliases. Opened 2026-07-13, accepted 2026-07-14.
- **RFC-0101** *(draft)* — Grammar-Enforced Naming Case Conventions — PascalCase for type
  declarations (struct/enum/aspect/generic params) and enum variants, camelCase for
  `fun` declarations (free functions, methods, associated functions), SCREAMING_CASE for
  constants (module-level, immutable `let` bindings — no dedicated `const` keyword
  needed, since the grammar already distinguishes `let` from `let mut`), snake_case for
  everything else that introduces a name (function-local `let` bindings, parameters,
  struct fields) — enforced as a real compile-time check (a post-parse AST pass, not
  literally embedded in `grammar.pest`), not just a style convention. PascalCase-types,
  snake_case-bindings, and the (currently unused) constants row all need zero renames
  across `stdlib/` and the test suite; camelCase-for-`fun` is the one real, active
  change, requiring a full rename pass across every existing function and method.
  Surfaced from reviewing RFC-0100's keyword-argument/ascription collision, but
  deliberately scoped as its own RFC rather than folded into that one — it's a general
  readability property, and does *not* rescue RFC-0099's own disambiguation question
  (module path segments share casing with
  values, an orthogonal problem). Opened 2026-07-14.
- **RFC-0102** *(accepted 2026-07-14)* — Bodyless Extend Blocks for Marker Aspects and
  Negative Impls — `extend Type: Aspect;` / `extend Type: !Aspect;` (no braces) as
  sugar for an empty-bodied `extend` block, valid in exactly the situations an empty
  body is already accepted today (positive impls, when every method has a default
  body or the aspect declares none, the true marker-aspect case). Pure desugaring, no
  new semantic category — mirrors `fun_decl`'s existing `(block | ";")` alternative.
  **For negative impls, the bodyless form isn't optional sugar — the old
  `extend Type: !Aspect { }` braces spelling is retired outright**, since a negative
  impl's body is never meaningfully non-empty (nothing `{ }` could say that `;`
  doesn't), matching this project's own precedent (RFC-0100, RFC-0042) for retiring a
  strictly-superseded spelling rather than keeping two. §5 extends the aspect clause
  to a comma-separated, per-item-polarity list for the same bodyless case
  (`extend Type: A, B, !C;`, desugaring to N independent single-aspect blocks; any
  negative item forces the whole list bodyless), reusing RFC-0036's existing `bound`
  grammar directly — strictly scoped to bodyless/empty-bodied extends, since a shared
  non-empty body across multiple aspects has no principled disambiguation and isn't
  attempted. Depends on RFC-0098's `extend Type: Aspect` grammar shape. Opened
  2026-07-14, accepted 2026-07-14.
- **RFC-0103** *(draft)* — Bodyless Aspect Declarations and Struct-Embedded Aspect
  Lists — two additions on top of RFC-0102. A bodyless spelling for the aspect
  *declaration* itself (`aspect Copy2;` — pure sugar for `aspect Copy2 { }`, legal
  whenever the braced form already would be, no permanence guarantee attached, unlike
  an earlier draft's dropped `marker` keyword). And a struct/enum-embedded aspect
  list (`struct Token: Copy2, Serializable, !Send { value: String }`) reusing
  RFC-0102 §5's `extend_aspect_list`, where struct/enum bodies stay fields-only:
  negative items are fully satisfied by the list itself, while every positive item
  declares a checked, module-wide *obligation* discharged by an ordinary,
  separately-editable `extend` block elsewhere — revised from an earlier draft that
  rejected positive items outright, once it was clear the "no escape hatch" concern
  only applies to items the list itself tries to implement inline. A still-earlier
  `marker` keyword (permanently gating which positive items the list alone could
  satisfy) was dropped outright once every positive item became an obligation
  uniformly — the permanence guarantee it offered stopped being load-bearing.
  Depends on RFC-0102. Opened 2026-07-14.
- **RFC-0104** *(draft)* — Multi-Aspect Extend Blocks with Shared Bodies — split out
  of an earlier draft of RFC-0103's own struct/enum-embedding section, since it's a
  separate feature that doesn't depend on anything there. Lifts RFC-0102 §5's
  bodyless-only restriction for `extend` blocks specifically: `extend A: Aspect3,
  Aspect4 { ... }` with a real, shared, non-empty body. Disambiguation reuses a
  tolerance that already exists in today's single-aspect impl checking (extra methods
  beyond what an aspect requires already become ordinary inherent methods,
  uncontested) — generalized to multiple aspects by checking each one's own
  required-method coverage independently against the same shared pool. The one new
  rule: if two named aspects in the same list declare a method with the identical
  name, the whole combination is rejected outright rather than guessing or
  introducing a qualified-declaration syntax. Depends on RFC-0102. Opened 2026-07-14.

---

## Settled (reference only — not part of active tracking)

**Implemented (25):** RFC-0006, 0007, 0010, 0018-0023, 0030-0032, 0034, 0035, 0040-0045,
0053, 0054, 0057-0059.

**Superseded (9):** RFC-0001 (→ later pointer work), RFC-0002 (aspect bound syntax),
RFC-0009 (module system → RFC-0030), RFC-0012 (→ RFC-0092/0093/0094/0095), RFC-0013
(integer overflow), RFC-0016 (stdlib foundation), RFC-0024 (linear types → RFC-0028,
which was then refused — RFC-0089 re-homes this), RFC-0029 (module system gaps),
RFC-0055 (comptime → RFC-0092/0093/0095, reconciled 2026-07-09 — see above).

**Refused (13):** RFC-0025, 0028, 0046-0048, 0051, 0056, 0069, 0079, 0084, 0085-0087 —
mostly the earlier region/lifetime model iterations that didn't survive the 2026-07-05
split, plus RFC-0046 (linear closure capture, blocking RFC-0050's `move` half), plus
RFC-0084 (refused 2026-07-10 — reverted in place to reaffirm RFC-0053's
`[T; N]`/`[expr; N]` exactly, with nothing left of its own to propose), plus RFC-0079
(refused 2026-07-10 — most of `Perhaps<T>`/`Result<T, E>` was already implemented and
spec'd by the time it was written, and its `?`-operator section was factually wrong
relative to already-shipped `From`-based coercion; real remaining gaps tracked at
https://app.clickup.com/t/86cap1wzb).

---

## Maintenance note

This file is a manual snapshot, not a generated artifact — there's no script producing
it. If RFCs move between directories or new ones land, this drifts silently. Treat
"last_built" in the frontmatter as the trust boundary: anything changed after that date
isn't reflected here yet.
