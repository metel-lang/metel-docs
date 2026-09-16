---
id: adr-0055
title: "The Architecture Atlas: Entity Model, Views, Traceability, and Content Discipline"
date: '2026-09-15'
status: proposed
relates: adr-0054
implements: metel-core#1159, metel-core#1141
---

## Context

`#1141` (the Architecture Atlas umbrella) states the problem directly:
architecture documentation drifts from code, ADRs lack current status and
successor links, and there is no reliable way to answer which code
implements which documented constraint. Its own "Desired model" diagram —

```
RFC ──defines language change──► Language Spec ──implemented by──► code
                                      │
                                      ▼
                          Architecture Spec
                           ├─ stage boundaries
                           ├─ data ownership
                           ├─ invariants
                           └─ implementation mappings
                                      │
                                      ▼
                              code + contract tests
```

— names the shape but not the mechanics: what the authoritative
Architecture Spec contains, which of its claims need an `ARCH-*`
requirement, how code cites that requirement, what a fixture proves and how
that proof is checked, how the resulting facts (spec prose, pipeline stages,
data tables, requirements, decisions, code, tests) render as something a
reader can navigate, and which of those facts this atlas chooses to show at
all rather than drowning a reader in every internal type and every
historical decision.

`#1159` scoped a static mockup — no live checker, no generated diagrams,
one stage (`name_resolver.rs`) worked all the way to real depth as the
proof that the model holds, the rest sketched only as far as honesty
allows. That mockup (`design/examples/page-architecture-atlas.html` in
`metel-website`) is now built. This ADR is what it actually decided, made
explicit rather than left implicit in a few hundred HTML comments —
`#1155`'s and `#1156`'s real implementation work needs one place that
states the whole model, not an archaeology project through mockup commit
history.

Three real, working mechanisms already exist in the corpus that this model
extends rather than replaces: the Formal Rule ID scheme
(`spec.<area>.<rule>.legality-N`) and its fixture-embedding via a `.toml`
sidecar's `spec = [...]` array; the RFC lifecycle (7 stages, `docs/rfcs/
tools/rfc.py check`); and `#1154`'s own already-specified generic
requirement framework (`<PREFIX>-<AREA>-<NNN>` IDs, a doc-comment marker
convention, a generic checker). Where this ADR proposes something new, it
says so; where it's naming a decision already implied by `#1154`–`#1158`,
it cites which issue.

## Decision

### 1. The entity model and authority boundary

Eight kinds of fact, each with a stable identity and its own lifecycle —
conflating any two of these into one shape is a mistake this session made
and then had to undo (see §5):

| Entity | ID shape | Lifecycle | Real example |
|---|---|---|---|
| Architecture Spec section | stable spec path and section anchor | canonical current prose; amended and versioned, not statused | `architecture.pipeline.name-resolution` |
| Architecture requirement | `ARCH-<AREA>-NNN` | `implemented / partial / planned / superseded / retired` | `ARCH-RESOLUTION-001` |
| Architecture debt record | `DEBT-<AREA>-NNN` | `open / managed / awaiting-verification / closed / superseded` | `DEBT-RESOLUTION-001` |
| Formal Rule | `spec.<area>.<rule>.legality-N` / `dynamics-N` | canonical once published; amended, not statused | `spec.declarations.variables.immutable-bindings.legality-1` |
| ADR | `ADR-NNNN` | `accepted / active / superseded / rejected` (`#1158` triage) | `ADR-0031` |
| RFC | `RFC-NNNN` | 7-stage (`0-draft` … `3-integrated`) | `RFC-0136` |
| Data-model fact | a type name, keyed | producer/owner/consumers/mutation-rule/invariants, no independent status — it's as current as the code | `TypedModuleGraph` |
| Fixture | a `.mtl` + `.toml` sidecar pair | pass/fail, checked in CI | `neg_14_legacy_equals_binding_separator.mtl` |

The Architecture Spec is the authoritative current description of the
compiler's architecture. Its sections state the stage boundaries, ownership,
data flow, invariants, and implementation mappings in prose, under stable
paths and anchors. An Atlas page is a generated rendering of that source and
its linked evidence; it is not a second, hand-maintained architecture
document and cannot become the authority by accumulating more UI detail.

An `ARCH-*` requirement and a Formal Rule play the same *role* (the atomic,
individually addressable, checkable claim) for two different *domains* —
architecture and language semantics respectively. An ADR and an RFC play
the same role (narrative decision rationale) for those same two domains.
This ADR does not unify them into one scheme; the domains are different
enough (a compiler's internal shape vs. what a Metel program means) that
forcing one ID space onto both would blur exactly the distinction that
makes each checkable.

The relationship within each domain is correspondingly parallel:

```
Language Spec section ──defines──► Formal Rule ──verified by──► fixture/code
Architecture Spec section ──defines──► ARCH-* ──verified by──► fixture/code
                                         │
                                         └──related to──► ADR/RFC
```

An `ARCH-*` requirement is therefore not a replacement for the prose that
explains an architectural boundary. It is the stable, individually testable
fact that backs a specific Architecture Spec claim. Every requirement has a
`specified by` link to its defining Architecture Spec section; the section
links to the requirements that make its normative claims checkable. Code and
fixtures cite the requirement, not the broad section, so evidence remains
atomic. A reader normally enters through the Architecture Spec section for
the current architectural story, then follows a requirement to inspect its
implementation and evidence.

An `ARCH-*` requirement's real fields, per `#1155`'s own scope and the
survey's specimen, verified against what the mockup actually needed to
express: `status`, `owner`, `implements` (a real, checkable path — not
necessarily a UI link; see §5's `ARCH-RESOLUTION-001` fix, which added the
literal `metel-frontend/src/name_resolver.rs` alongside the cross-link),
`verified by` (named tests/checks, or — see §2 — embedded fixtures),
`specified by` (one Architecture Spec anchor), and `related` (ADRs/RFCs).
An Architecture Spec section carries its prose plus its `ARCH-*` links;
those are source links, not copies of requirement prose. A Data-model fact's
fields: `producer`, `owner`, `consumers`, `mutation rule`, `invariants`, and
`upstream`/`downstream` neighbor links to adjacent facts in the same pipeline
(added to the mockup's `TypedModuleGraph` card specifically because the
survey's own recommendation named it and the mockup didn't have it yet).

### 2. Traceability: code cites the atomic unit, not the rationale

Code, fixtures, and generated output cite the nearest atomic unit
(`ARCH-*` or Formal Rule) when one exists for the claim being made, not the
Architecture Spec section's broad prose or the ADR/RFC that produced it.
The atomic unit links back to its defining spec section and to its ADR/RFC
rationale. The resulting walk — `code → ARCH-*/Formal Rule ←
Architecture/Language Spec section`, with the atomic unit also linking to
its ADR/RFC — is navigable in both directions and is never skipped except by
a stated exception (no atomic unit is warranted; one doesn't exist yet
because its RFC is accepted but not integrated).

This is proposed in full, with rationale, real corpus examples (including
a real gap it found — `ADR-0027` cited directly in `resolve_module()`'s
own source comment despite being superseded by `ADR-0039`), and an
enforcement mechanism, as a candidate `#1157` engineering-standard entry:
https://github.com/metel-lang/metel-core/issues/1157#issuecomment-5682023925.
It is not restated here. What this ADR adds is the piece that standard
depends on but doesn't itself provide: **Decisions needs to be a real
register** (§4) for "ARCH-\* cites ADR" to mean anything more than another
bare citation with nowhere to land.

The enforcement mechanism that standard proposes — a fixture sidecar's
`arch = [...]` array, parallel to the existing `spec = [...]`, read by the
same generation step that already embeds fixtures on spec pages, extended
to embed them on `ARCH-*` requirement pages too — is this ADR's answer to
"how is an architecture requirement's evidence actually checked," not a
separate mechanism. One fixture can carry both arrays; the same source
proving a Formal Rule can be evidence for an architecture requirement.

### 3. Six views, three tiers

The six views are projections over the authoritative Architecture Spec,
requirement and debt registries, code/fixture evidence, and ADR/RFC
registers. They do not define architecture independently. A stage,
data-model, or requirement card must retain a link back to the Architecture
Spec section that is its current narrative source; the Atlas adds navigation
and joined evidence, not a competing prose source.

| Tier | Views | What they show |
|---|---|---|
| Ecosystem | Context, Container | Metel as a whole system and its deployable pieces — unchanged from `#1159`'s original brief. |
| Compiler | Component, Data model | Component: the eight-stage pipeline, always visible, with one stage's full code expanding in place on selection (not a separate Code view — see §5). Data model: one fact record per structure, Glean-shaped, with real up/down neighbor links. |
| Register | Traceability, Decisions | Two cross-cutting join tables, not C4 levels. Traceability: `ARCH-*` requirements, their evidence, and the Health/debt rollup, DO-178C-shaped. Decisions: ADRs, added in this pass (§4) — not part of `#1159`'s original five-view brief. |

This is six views against `#1159`'s originally-scoped five. §5 states why.

### 4. Decisions is a real register, not a citation

An ADR gets a real entry in the Decisions view — its own row, its own
status badge, a `Relates to` list of other ADRs, and (demonstrated on the
one fully-built example, `ADR-0054`) a **"Cited by, in this atlas"**
reverse index: every requirement that actually depends on it. This is what
`#1141`'s own line — "ADRs are decision history supporting the current
spec; they are not the sole current description of architecture" — means
in practice: an ADR is real, citable, and has a lifecycle of its own, but
it is not where a reader normally lands. A reader lands on an Architecture
Spec section for the current description, follows a requirement for its
atomic evidence, and reaches the ADR one hop further only when they want
why.

Decisions is scoped to the ADRs actually cited by content already in this
atlas (eight, currently — `ADR-0026/0027/0031/0038/0039/0041/0048/0054`),
not a mirror of the full collection (54 real entries, per `#1158`). This is
the same discipline as §6, applied to a new entity kind.

### 5. Why Component absorbed Code

C4 frames Component and Code as "the same model read at two levels, not
two separate diagrams to keep in sync" (survey §1). Built as two separate
Atlas *views* — two tabs, two independent pieces of navigation state — they
weren't that in practice. Concretely, and not hypothetically: the first
working version had Code's own inner Structure/Call-graph tab-switcher
fighting the outer view-tab switcher over which piece of state owned
visibility (radio `:checked` on one, URL `:target` on the other), and
produced a reproducible bug — after clicking a function in Structure, the
Call graph tab became permanently unreachable, because the cross-link that
was supposed to reveal it depended on a fragment that clicking Structure
had already claimed for something else. Separately: the reason to read a
stage's code is almost always "in the context of where it sits in the
pipeline," and two navigation-level destinations forced a context switch
neither the reading pattern nor C4 actually asked for.

The fix generalizes past this one bug: **a toggle needs exactly one source
of truth.** Everywhere this mockup has two things that can independently
claim to control the same visibility (an outer tab and an inner tab; an
expand state and a scroll target), they must be driven by genuinely
different state — a `:target` fragment for one, a hidden checkbox for the
other — never two competing uses of the same mechanism. This is a general
principle for `#1156`'s real implementation, not a one-off patch, and
recurred more than once while building this mockup.

Component now shows the pipeline always; selecting a stage expands that
stage's full detail (API, owned data, dependencies, contract tests, open
debt, Structure/Call-graph) in place, collapsing the pipeline out of the
way, with one control back. This still delivers C4's two levels of detail
— it just does it as one view with a state transition, not two views
joined by a link. `#1156` should read the survey's §5 Pipeline
recommendation ("two fixed zoom levels ... the whole pipeline and one
stage drilled in") with this refinement: two *states*, not two *views*.

### 6. Content-selection discipline

Every view in this atlas omits real content on purpose, and the omission
rule differs by view because the thing being selected differs:

- **Code** (Structure/Call graph): a function is elided to a signature-plus-
  doc-comment stub, not a full body, when it's a plain worker (single
  responsibility, no further branching) — Yourdon & Constantine's
  fan-out/complexity test, applied by hand this pass (`resolve_module` and
  `collect_re_exports` were initially mis-elided as workers and corrected
  once the test was actually applied to them, not assumed from their
  names).
- **Call graph** specifically: a node is omitted entirely, not just elided,
  when it's a direct leaf call with no further branching whose full
  information already lives in Structure (`decl_pub_name`) — different
  from eliding a body, since the node itself adds nothing the graph's shape
  needs.
- **Data model**: a type gets its own card only if it's a pipeline-boundary
  representation or has real cross-module reference fan-in — not every
  internal struct (`GlobTier` doesn't have one; it's internal to one
  file's own logic, not a boundary type).
- **Decisions**: an ADR is included only if something already shown in the
  atlas cites it (§4) — and, per the `#1157` standard (§2), a citation
  doesn't imply a requirement should be minted: `ADR-0048` (the frontend/
  interpreter crate split) stays a direct citation from nowhere in
  particular, because a Cargo workspace boundary isn't the kind of durable,
  cross-stage invariant `#1157`'s own existing line reserves an `ARCH-*`
  id for.
- **Debt**: every open Architecture debt record appears in Traceability's
  Health/debt rollup and on each affected stage or requirement; resolved
  records remain reachable from that history but do not occupy the active
  rollup. A debt is included because it has a live owner and remediation or
  acceptance state, not merely because a temporary implementation detail
  exists.
- **Stage detail**: one stage (`name_resolver`) is built to full real
  depth; the other seven are visible only as pipeline nodes with no detail
  page. This is the sharpest of the deliberate omissions and the one most
  likely to be mistaken for an oversight — it isn't; it's `#1159`'s own
  "before implementation" scope, deliberately not stretched to cover a
  second stage just to look more complete.

The common thread: omission is always argued from a real, checkable
property of the thing being omitted (a fan-out count, a boundary crossing,
an existing citation), never from "this seemed like enough content." A
future automated version of any of these (content-selection tooling for
Code/Data-model is itself future work, not scoped here) should implement
the actual test named, not approximate it.

### 7. PROC-* shares infrastructure with this atlas, not its views

`#1142` (Operations Spec and Project Process Atlas) is a real, already-
scoped sibling initiative, not an open question this atlas can settle by
default. Its own text states the split precisely: "Architecture Spec:
implementation stages, data models, code boundaries, and invariants" vs.
"Operations Spec: documentation generation, CI, releases, deployment,
scripts, tooling, repository handoffs, and operational guarantees." That
split holds, for reasons concrete enough to state as a decision rather than
leave open:

- `#1142`'s own worked example, `PROC-RELEASE-001`, `Implements:
  .github/workflows/release.yml, metel-website/.github/workflows/
  deploy.yml` — spans two repositories. It is not a fact about one
  Architecture Atlas component; it is a fact about the relationship
  between a tag in one repo and a deployment in another. Structurally the
  same reason Traceability and Decisions are registers rather than being
  hung off individual C4 nodes.
- Three of `#1142`'s six planned views have no natural component home:
  **Repository handoff map** (source-of-truth and version-pointer handoffs
  *between* `metel-core`/`metel-docs`/`metel-docs-internal`/
  `metel-website` — a different axis than "what depends on what at
  runtime"), **CI map** (a workflow like `rfc-check.yml` runs orthogonally
  to every pipeline stage, not owned by one), and **Tooling inventory**
  (most scripts, e.g. release tooling or doc generators, aren't owned by a
  single component either).
- The marker-discovery domains `#1154` already specifies are disjoint by
  design, not by oversight: Architecture markers scan Rust doc comments in
  `metel-frontend/src/**`/`metel-interpreter/src/**`; Operations markers
  scan `.github/workflows/**`, scripts, `package.json`, Cargo binaries —
  no overlap.

What *is* shared, and correctly so: the ID scheme, marker convention, and
generic checker (`#1154`, built once); the Atlas shell/routing/traversal
plumbing (`#1156`'s own scope note: each spec family's views render
*through* shared plumbing, not a forked copy of it). And where a process
fact genuinely relates to an architecture one, it's a citation, not a
merge — `#1142`'s own requirement schema already carries a `related
Architecture Spec IDs` field, the identical pattern this ADR uses for
ADR↔ARCH (§2, §4), reused rather than reinvented for a third pair of
domains.

### 8. Drift detection, in both directions

The fixture `spec = [...]`/`arch = [...]` mechanism (§2) catches one shape
of drift: evidence that used to exist and stopped. It does not catch the
two directions that actually matter for a living spec — the prose claiming
something the code no longer does, and the code doing something the prose
never mentions. Five further mechanisms, each grounded in something already
real in the corpus rather than proposed cold:

**Prose claims something the code no longer does:**

- **ADR status propagation to every citer.** `ADR-0027`→`ADR-0039` (§2's
  own motivating example) was found by manual audit, not by a mechanism —
  which is the argument for building one. ADRs already carry real,
  structured `status`/`supersedes` frontmatter. A purely structural
  checker — no semantic understanding required — walks every real citation
  of an ADR ID (an `ARCH-*` `related` field, a code marker, a Decisions
  entry's `Relates to`) and flags any whose cited ADR's *current* status is
  `superseded`. This is `#1158`'s missing other half: triage assigns
  status; this is what makes the assignment's consequences visible
  everywhere the ADR is cited, without another manual audit like this
  one's.
- **Signature/shape staleness, not just path existence.** `#1154`'s
  checker validates that an `Implements` path *exists*; nothing validates
  that the content at that path still matches what the requirement's prose
  claims (a field list, a signature). This atlas's own mockup is a live
  instance of the risk it names: every transcription in the Structure tab
  is a hand-authored snapshot with no step re-checking it against current
  `HEAD`. The precedent to extend is real and already running —
  `metel-docs-internal`'s `check-examples.yml`/`check_doc_examples.py`
  already validates doc *examples* against real behavior; the same
  approach (re-extract the cited signature via `syn` or `cargo doc
  --output-format json` at generation time, fail on a mismatch) applies
  directly to architecture transcriptions.

**Code does something the prose never mentions:**

- **Unmapped-code discovery for Architecture, matching what Operations
  already commits to.** `#1142`'s own acceptance criteria require that
  every discovered operational asset be "mapped or explicitly classified
  ... with a rationale." `#1154`/`#1155` specify forward validation
  (marker → real requirement exists) but not this reverse check for the
  Architecture family. Closing that asymmetry means every `pub` boundary in
  a marked source tree either carries a `//! Architecture:` marker or an
  explicit exemption — reusing the exact `// arch-exempt: <reason>`
  convention already proposed in the `#1157` citation-layering entry,
  rather than inventing a second one.
- **A staleness signal that doesn't require semantic understanding.**
  Neither mechanism above catches a test that still exists and still
  passes but no longer tests what the prose claims — a real limit, not a
  gap to engineer around. The cheap, honest fallback: track, per
  requirement, the commit it was last confirmed against (`ADR-0054`'s own
  dated amendments are exactly this pattern, just not machine-read yet).
  If the implementing path's git history has commits after that date with
  no corresponding Architecture Spec or requirement touch, surface a new
  Health category — `stale`,
  distinct from `missing evidence` — not a hard CI failure (too noisy for
  pure refactors that change nothing a requirement claims), a visible
  prompt for re-confirmation instead.

**A refinement to the mechanism already proposed:**

- **Cross-check a fixture's own embedded comment against its sidecar.** A
  `.mtl` fixture's real inline comment (`// RFC-0136: ...`) and its
  `.toml` sidecar's `spec`/`arch` arrays are two independent statements of
  the same fact, written by hand at different times. A cheap lint diffing
  them catches the copy-paste case — comment cites one rule, sidecar cites
  another — for free, in every fixture that already has both.

Priority, not sequencing by section order: ADR-status propagation is the
highest value for the cost — purely structural, needs nothing beyond data
that's already real and typed, and directly closes a gap this ADR's own
research found by hand. Signature staleness is the mechanism that most
directly answers "documentation drift" in the usual sense, but it's real
engineering (a source-level extractor), not a lint, and should be scoped
as its own follow-up rather than bundled into `#1154`'s first pass.

### 9. Architecture debt is a first-class, reconcilable exception record

Requirement status and Health are not a debt register. `partial` says how
much of a requirement currently holds; `missing evidence`, `stale`, and
unmapped-code findings say what the checker or audit can see. None records
whether a shortfall was deliberately accepted, who owns it, which work is
meant to remove it, or whether that work has actually closed the condition.
An Architecture debt record supplies that missing durable fact without
weakening the requirement it affects.

A debt record has the stable identity `DEBT-<AREA>-NNN`. It keeps three
independent dimensions, rather than overloading one status field:

| Dimension | Values | Meaning |
|---|---|---|
| Origin | `accepted-temporary` / `discovered` | Was the deviation consciously accepted before it was fixed, or found by a checker, audit, incident, or reader afterwards? |
| Lifecycle | `open / managed / awaiting-verification / closed / superseded` | Does the condition still exist, is there a resolution plan, and has its exit condition been verified? |
| Acceptance | `unaccepted / accepted-temporary / waived` | May the current deviation remain while open? A waiver requires an explicit ADR or issue and is not a silent expiry of temporary acceptance. |

An `accepted-temporary` record requires its accepting ADR or issue,
rationale, owner, and a mandatory review-by date. A `discovered` record
requires its discoverer (check, audit, incident, or reader), observation
date, and an owner after triage. A Health finding from §8 is a candidate, not
an automatic debt record: triage either creates a `discovered` record,
resolves the finding, or records a justified exemption. This keeps checker
noise from becoming permanent project inventory.

Every record carries a `scope` (one Architecture Spec section), a precise,
testable `condition`, `affects` (zero or more `ARCH-*` requirements plus the
relevant code, stage, or data-model facts), and an `exit condition` with its
verification evidence. `affects` may be empty for an unmapped-code finding:
the record still has a Spec-section scope so discovery can precede minting a
new requirement.

Resolution is a set of typed links, not free-form remediation prose. Each
link names its target, role, and whether it is required for closure:

| Target | Roles | Terminal signal |
|---|---|---|
| Issue | `tracks` / `implements` | issue is closed |
| Architecture requirement | `successor-contract` / `implements` | requirement is `implemented` (or another explicitly named terminal status) |
| Fixture or check | `verifies` | named evidence passes |
| ADR | `accepts` / `waives` | explicit decision, never closure evidence by itself |

The record also declares `closure policy: all-required | any-required`.
`all-required` is the normal case: an independent issue may implement the
work, a following `ARCH-*` entry may state the durable successor contract,
and a fixture or check proves the debt's exit condition. A record may use an
issue alone or a successor requirement alone when that is genuinely its full
resolution path, but it must still name verification evidence; closing a
tracker is not proof that the condition disappeared.

Lifecycle is deliberately asymmetric with tracker status:

```
open → managed → awaiting-verification → closed
  ↑          │              │
  └──────────┴──────────────┘  tracker reopens, regresses, or verification fails
                    │
                    └────────→ superseded (a successor debt explicitly replaces it)
```

When all required issue and successor-`ARCH-*` links reach their terminal
signals, reconciliation marks the record *ready for verification* and raises
a finding unless its lifecycle is `awaiting-verification`; it does not close
it. Closure requires the record's own exit-condition evidence. If a linked
issue reopens, a successor requirement regresses, or evidence fails,
reconciliation marks the record divergent and preserves the event in its
history. A human confirms lifecycle transitions, so the checker never
silently rewrites an accountability record; it records observed tracker state
and makes disagreement between the declared lifecycle and linked work
actionable.

Debt does not become a third Register view. Traceability's Health area is
the active debt ledger and reconciliation queue: it shows open and managed
records, debt awaiting verification, and divergent records such as “issue
closed, debt unverified” or “closed debt, successor requirement regressed.”
It supports facets for `tracked by issue`, `resolved by ARCH-*`, origin,
acceptance, owner, and overdue review. Stage and requirement cards show
their affected open debt; issues and `ARCH-*` entries expose backlinks to all
debt they track or resolve. Resolved and superseded records remain reachable
as history but do not occupy the active rollup.

Code and fixtures continue to cite `ARCH-*` or Formal Rules, never a
`DEBT-*` record. Debt records govern remediation and accountability; they
are not semantic or architectural contracts and cannot be used as evidence
that a requirement holds.

## Alternatives Considered

**Rely on periodic manual audit for drift, no automated mechanism.**
Rejected — §8's own motivating case (`ADR-0027`→`ADR-0039`) is a real
instance of exactly this failing silently until this ADR's own research
happened to catch it by hand. A mechanism that runs on every change is the
point; an audit that runs when someone remembers to is what's already
failing.

**Make the Atlas itself the authoritative architecture documentation.**
Rejected — an interactive projection is useful for joins, filtering, and
evidence traversal, but it is not a stable home for the current narrative
description of a stage or invariant. It would duplicate the prose that
`#1155` is scoped to write, and any divergence between a hand-authored Atlas
card and that prose would recreate the drift this work exists to prevent.
The Architecture Spec remains authoritative; the Atlas renders it together
with requirements, code, fixtures, and decisions.

**Represent debt only as a requirement status or a free-form stage-card
note.** Rejected — `partial` and `planned` cannot say whether a deviation
was deliberately accepted or independently discovered, who is accountable,
or when it expires. A hand-authored “open debt” note is neither enumerable
nor enforceable, and therefore cannot support the Health view or a review
workflow.

**Attach `PROC-*` requirements directly to Architecture Atlas components
instead of a separate Process Atlas.** Considered directly, prompted by a
real question about this ADR, not a strawman. Rejected — see §7:
`PROC-RELEASE-001` alone (spanning two repositories) has no single
component to attach to, and three of `#1142`'s six planned views (repo
handoff map, CI map, tooling inventory) describe facts with no component
shape at all. The shared-infrastructure instinct behind the question is
correct and is already real (`#1154`/`#1156`); it argues for one framework
under two content sets, not one content set.

**One unified `ARCH-*`/ADR scheme, no separate Decisions register.**
Rejected — §1 states why domains stay separate; §4 restates it specifically
against merging Decisions into the Traceability ledger, since an ADR's
lifecycle and a requirement's health are different shapes of fact.

**Keep Component and Code as separate views, fix only the state-management
bug.** Rejected (§5) — the bug was a symptom; the deeper mismatch (reading
code without pipeline context is rarely what's wanted) would have
persisted with the navigation state fixed correctly.

**Leave ADRs citation-only, add no register.** Rejected (§4) — doesn't
provide the reverse lookup `#1141`'s own diagram and the Traceability
kicker already commit to wanting.

**Build all eight stages to the same depth as `name_resolver`, for
completeness.** Rejected for this pass (§6) — `#1159` is explicitly a
design pass before implementation; seven more full stage write-ups is real
inventory work that belongs to `#1155`, not to proving the model holds
once.

## Consequences

- `#1155` owns the authoritative, versioned Architecture Spec sections and
  their stable anchors. It must link each normative architectural claim to
  its `ARCH-*` requirements, while each requirement records its defining
  section. `#1156` consumes that source rather than recreating its prose.
- `#1156` needs routes for Architecture Spec sections and a route and nav
  slot for Decisions in addition to the original five (for example,
  `/architecture/spec/pipeline/name-resolution`,
  `/architecture/requirements/ARCH-RESOLUTION-001`, and
  `/architecture/decisions/ADR-0054`). Every Atlas card derived from a
  requirement or stage needs a return link to the source spec section. It
  also needs to implement Component/Code as one view with a state
  transition, not two views — building straight from the survey's table
  without this ADR would plausibly reproduce the exact navigation bug §5
  describes.
- `#1154`'s generic checker gains one real scope addition once the
  `#1157` standard (referenced, not restated, in §2) is accepted: the
  `arch = [...]` fixture-sidecar field and the citation lint. Both are
  additive to `#1154`'s already-specified marker/checker design, not a
  fork of it.
- `#1155`, writing the real Architecture Spec content, should treat this
  ADR's entity-field list (§1) and content-selection tests (§6) as the
  schema and the inclusion criteria respectively. The prose-and-atomic-rule
  relationship is intentional: a section remains readable without opening
  every requirement, while every normative claim that needs machine-checked
  evidence has a stable `ARCH-*` link. These criteria were derived by
  actually building one stage to real depth against them, not proposed cold.
- Decisions' scope (§4) needs real, ongoing curation as `#1155` adds more
  `ARCH-*` content — it is not a set-once list, and will need re-auditing
  each time a new requirement cites an ADR not yet in the register.
- `#1154`'s checker gains two further real scope additions from §8, beyond
  the fixture-sidecar/citation-lint pair already noted above:
  ADR-status-propagation and Architecture-side unmapped-code discovery
  (matching the reverse check `#1142` already commits to). The Health view
  (`#1156`) gains a fifth category, `stale`, alongside `implemented`/
  `partial`/`planned`/`missing evidence` — a signal, not a build failure.
  Signature/shape staleness checking (§8) is real engineering, not a lint,
  and should be scoped as its own follow-up issue rather than assumed as
  part of `#1154`'s first pass.
- `#1154` and `#1156` also gain the debt flow in §9: checkers and audits
  emit Health findings; human triage creates or updates `DEBT-*` records;
  the generic checker validates their identifiers, required provenance,
  links, closure policy, and overdue `review by` dates. It reconciles issue
  state, successor-`ARCH-*` status, and verification evidence against the
  declared debt lifecycle, producing a finding rather than silently closing
  a record. Overdue debt is a visible Health signal, not an automatic status
  transition or a hard claim that the underlying requirement no longer
  holds.
- `#1156` renders open, managed, awaiting-verification, and divergent debt
  as Traceability/Health ledger facets, with backlinks from affected stages,
  requirements, and tracking issues. It does not add a seventh Atlas view or
  treat the mockup's free-form “Open debt” text as canonical data; the
  Architecture Spec and debt registry remain the source.
- `#1142` (the Process Atlas) is unaffected in scope by this ADR — it
  keeps its own six planned views, per §7 — but should build on the same
  `#1154`/`#1156` shared plumbing this atlas does, not a parallel copy of
  it. This resolves the survey's own §7 open question (PROC-*'s visual
  language) as "shared framework, independent views," rather than leaving
  it open.
