---
id: rfc-process
title: "RFC Process"
type: process
last_updated: '2026-07-10'
---

# RFC Process

This document did not exist before 2026-07-09 — the lifecycle below had been running as
an implicit convention (directory names only) for 94 RFCs with nothing written down
explaining it. Written down now alongside `INDEX.md`, prompted by two things surfacing
in the same sitting: RFC-0055 sat undiscovered in draft for five weeks while RFC-0092
independently reinvented a large part of it, and RFC-0063 — this project's own concrete
precedent for the failure `3-integrated` exists to catch.

**Correction, 2026-07-10: "nothing written down" above was wrong.** `internal/versioning.md`
(2026-05-21) already had a written RFC-lifecycle section — 6 stages, a `spec_status:
pending/done` field tracking spec-sync — that nobody checked against when this document
was created, so it went un-reconciled for a full day while this document and
`3-integrated` were built independently of it. This is the same failure mode as the
RFC-0055 duplication above, one level up: it happened to *this document's own creation*,
not to an ordinary RFC. `versioning.md`'s RFC-lifecycle section is now retired in favor
of this document; its `spec_status` field is retired in favor of `3-integrated` +
`impl_status`/`impl_tracking`, which do the same job as a real lifecycle stage rather
than a side field. Worth remembering: "check what's already written down" applies to
process documents too, not only to RFC content.

**The RFC-0063 precedent, traced from git history rather than repeated from memory:**
RFC-0063 ("Region Handles" at the time) was accepted, alongside seven siblings —
RFC-0065, 0066, 0067, 0068, 0069, 0073, 0077 — in one commit. Later, while working on
RFC-0066 specifically (individual move-out/drop), it became clear that RFC-0066's own
natural semantics — a value's lifetime can end *before* its backing region's lifetime —
directly broke RFC-0063's founding premise: that one region name simultaneously served
as lifetime tag, disjointness proof, *and* allocation strategy, bundled into a single
identity. All eight accepted RFCs had to be demoted back to under-review in one commit;
three more were flagged for outright retraction as collateral; a new position report and
a new unifying principle (Storage Transparency) were needed to put the cluster back
together. **This was caught by reasoning, not by implementation** — nobody built
anything and hit a wall; someone working through RFC-0066's consequences noticed it
contradicted RFC-0063's own stated invariant. That is exactly a worked-example-style
catch (construct the case where RFC-0066's move-out happens, ask what RFC-0063's
region-name-as-lifetime-tag then means, watch it stop making sense), done informally,
after acceptance, instead of formally, before it. `3-integrated` exists to do this
catch on purpose and earlier, so it costs one RFC's amendment instead of eight RFCs'
joint demotion.

## The lifecycle

```
0-draft → 1-under-review → 2-accepted → 3-integrated → 4-implemented
                                                ↘
                                          5-superseded / 6-refused (from any stage)
```

**0-draft.** A design sketch. May be thorough or a one-paragraph stub (RFC-0005 is
currently the latter — that's fine, drafts are allowed to be incomplete). No obligation
to check for conflicts yet, but see "Before opening a new RFC" below.

**1-under-review.** Has a substantiated primary proposal, not just an option list — real
engagement has happened, but real open questions remain that block acceptance. RFCs move
here when they've earned it, not on a schedule.

**2-accepted.** The design is settled: no more open questions block it, alternatives have
been weighed and one chosen. This is where RFC lifecycle has stopped, historically, for
anything not yet implemented — 14 RFCs sat here with no further gate before
"implemented" when this stage was introduced (2026-07-09; 13 as of 2026-07-10, after the
allocator/lifetime cluster's ratification sweep, RFC-0067a/0072/0078/0081/0082/0083
moving on to `3-integrated`, and RFC-0079/0084 leaving by refusal instead) — which is
exactly the gap
that let RFC-0063's history happen: a design can
be accepted on paper and still be wrong in ways nobody notices until it's checked against
everything else that's also accepted, or in flight alongside it.

**3-integrated *(new)*.** The RFC's content is incorporated into `public/reference/spec/`
— not just cross-referenced from RFC text, actually merged into the language reference —
and detailed worked examples are written combining this RFC's feature with other
already-integrated features, specifically hunting for soundness gaps at the
intersection, not just re-checking the RFC in isolation. **Critically, per the RFC-0063
precedent above: this cross-checking must also cover sibling RFCs still moving through
the same cluster, not only work that has already reached `3-integrated` itself.**
RFC-0063 and RFC-0066 were developing concurrently, in the same tightly-coupled cluster,
neither settled independently of the other — "checked against everything already
integrated" alone would not have caught their conflict, because by a strict reading
neither had gotten there yet. A worked example combining a still-in-flight sibling RFC's
consequences with this RFC's own stated invariants counts, and is often exactly where
this kind of contradiction lives. Exit criterion: no known unsoundness or contradiction
between this RFC and the rest of the currently-integrated spec, *and* no known
contradiction with sibling RFCs still active in the same cluster. If a worked example
surfaces a real problem (as happened repeatedly this session — the comptime/structural-
records circular dependency, the `Linear` auto-impl-vs-derive miscategorization,
RFC-0080 shipping syntax RFC-0012 had already rejected), that's this phase doing its
job, not a failure of it — the RFC goes back for amendment rather than proceeding to
implementation carrying the problem forward.

**Additional exit criterion, added 2026-07-31 — an RFC that changes existing syntax
must sweep prose, not only code.** RFC-0115 renamed the struct-literal field separator
from `:` to `=` and migrated 566 sites across `stdlib/` and `tests/`. It never touched
documentation, so for two months the RFCs, the reports and the public blog post kept
teaching syntax that no longer compiled — and it cost real time when RFC-0071 §3's stale
example was about to be copied into an implementation task (metel-core#298).

Concretely, for any RFC that changes the spelling of something already written down:

- **Sweep `internal/rfcs/`, `reports/` and `public/` in the same change as the code
  migration**, not as a follow-up. Prose examples are what implementers reach for first,
  so a stale one is not cosmetic.
- **Do not use a blind regex.** Three separate sweeps have now corrupted files this way:
  `fun clone(self: &T)` rewritten to `self = &T`, `type Item: Display` to `type Item =
  Display`, and — during metel-core#298 itself — a parameter list `part_b: &pb var [i64]`
  rewritten as an initializer. A field separator and a type annotation are spelled alike;
  only context tells them apart. Scope by code-fence language too: a ```rust fence
  describing the interpreter's own AST must not be swept as if it were Metel.
- **Verify by compiling, not by reading.** Extract at least one complete example from the
  swept prose and run it. That is what confirmed metel-core#298's sweep.
- **Watch for line endings.** At least one file in this repository is CRLF; a
  read/split/join in Python will silently rewrite every line of it.
- **Decide the treatment of dated documents explicitly.** A published blog post is not
  wrong *for its date*, but a reader today will copy what it shows. metel-core#298
  corrected the syntax in place, on the grounds that a code sample is an instruction
  rather than a historical claim. Superseded and refused RFCs, and `reports/archive/`,
  were deliberately left alone — those are records of what was thought, not guidance.

**Additional exit criteria, added 2026-07-10 — implementation-tracking, not just spec
text.** Landing in the spec is exactly the moment a real gap opens between "what the spec
says" and "what the interpreter does," and nothing before this tracked that gap
explicitly. Modeled on Swift Evolution's convention (every accepted proposal document
itself carries an `Implementation:` field — a compiler version, or "Not yet implemented"
— updated as the compiler catches up) rather than Rust's or TC39's multi-implementation
tracking (a single-engine language doesn't need a per-engine comparison table, just an
honest single status). Concretely:

- **A linked implementation-tracking task must exist before an RFC enters
  `3-integrated`.** `rfc.py transition <id> --to integrated` refuses to run without
  `--tracking <tracking task/URL>` — the same discipline as Rust's rule that no feature
  ships behind `#![feature(x)]` without an open tracking issue, enforced mechanically
  rather than left to memory.
- **Every RFC frontmatter gains two fields once integrated:** `impl_status`
  (`not-started` / `in-progress` / `implemented`) and `impl_tracking` (the task link).
  These are the RFC's own Swift-Evolution-style status field — a reader of the RFC sees
  both "is the design settled" (the lifecycle `status`) and "does the interpreter
  actually do this yet" (`impl_status`) without cross-referencing a second system.
  `rfc.py impl-status <id> --set in-progress|implemented` updates it as work proceeds;
  `rfc.py transition <id> --to implemented` sets it to `implemented` automatically.
- **Inline markers in `public/reference/spec/*.md` are required, not optional, at every
  section the RFC touches** — they are **public availability markers first**, with a
  narrow exception for future-facing features: a `Planned for vX.Y.Z` marker may also
  include the RFC id so implementation drift can still be tracked against a stable
  design handle. The spec must say what version first ships a feature, whether the
  current text is future-facing, and when behavior changed; it must not require the
  reader to open an RFC file just to learn whether the feature exists. Use versioned
  wording at the point of use (for example `> **Available in v0.11.0.** ...`,
  `> **Changed in v0.11.0.** ...`, or `> **Planned for v0.11.0 (RFC-0123).** ...`), not
  just a global status field. A reader of the spec directly, not the RFC, still needs
  to see it; a single central table would miss exactly the reader this exists for.
- **The callout must be exactly one line (2026-07-11)** — no continuation lines in the
  blockquote, whatever explanatory detail doesn't fit gets cut, not wrapped. This is
  specifically so that removing it, once the RFC reaches `4-implemented`, is an
  unambiguous single-line deletion — no risk of leaving orphaned prose behind or having
  to work out where a multi-line callout ends. The lifecycle tool may still verify that
  an integrated RFC's content has been merged into the spec, but the public-facing spec
  text still talks first in terms of released or planned versions. Issue numbers and
  tracking links stay out of the spec entirely; the RFC id is allowed only inside a
  future-facing availability marker. Removing a future-facing callout, once the feature
  ships, still happens in the same change that moves the RFC to `4-implemented`, not as
  a separately rememberable follow-up.

**Not retroactive.** The 25 RFCs already `4-implemented` before 2026-07-10 predate this
convention and are not required to carry `impl_status`/`impl_tracking` after the fact —
`rfc.py check` only enforces this from `3-integrated` onward, matching this document's
existing policy of not re-litigating the pre-existing accepted backlog (below) all at
once. It started applying in full the same day, once RFC-0067a/0072/0078/0081/0082/0083
became the first RFCs to actually reach `3-integrated` under this definition.

**4-implemented.** Built against the integrated spec, not against the accepted RFC text
directly — by the time something reaches this stage, "the spec" and "the RFC" should
agree, because §3-integrated is what makes them agree.

**When to transition to `4-implemented`, added 2026-07-12.** This stage's own definition
says what it means but never said when to flip it — three rules, settled alongside
`metel-core`'s branching/release rework:

- **Trigger: at issue-close, not at `develop`-merge or release.** Run
  `rfc.py transition <id> --to implemented` in the same session/commit that closes the
  Codeberg issue implementing it, on that issue's own branch — the same "update it when
  it's true, not batched for later" discipline the changelog follows
  (`metel-core/AGENTS.md`). The release gate's RFC-state check (`rfc.py check` clean,
  `impl_status`/`impl_tracking` correct) is a *verification* that this already happened,
  not the trigger; finding a problem there means the transition was missed earlier, not
  that it is now due.

  *Revised 2026-07-28:* originally written as "at issue-close, not at sprint-close", with
  the verification assigned to the sprint-close gate. `metel-core` retired the `sprint/N`
  branch tier (see its `AGENTS.md` § "Why `sprint/N` was retired"); the verification moved
  to the release gate. The trigger itself is unchanged — it was always issue-close.
- **An RFC implemented across multiple issues waits for the last one.** Not previously
  addressed. `impl_status` stays `in-progress` until the final tracked issue closes;
  `impl_tracking` points at whichever issue is understood to be that last one (or a
  parent/tracking issue covering all of them) — not just the first issue opened.
  Transitioning on partial coverage would claim the spec and interpreter agree when they
  don't yet.
- **A bug found later in already-`4-implemented` behavior does not roll the stage back.**
  File it as an ordinary bug issue and fix forward. `4-implemented` is a statement about
  a point in time — spec and interpreter agreed when this was declared — not a live
  guarantee that gets revoked the moment a bug surfaces, the same way a shipped feature
  with a later-found bug doesn't get "unshipped."

**5-superseded / 6-refused.** Terminal states, reachable from any stage. Superseded RFCs
keep a pointer to what replaced them; refused RFCs are kept as historical record with
the refusal reason. Living reports (`reports/substructural-types/*.md` and similar) are
not superseded when an RFC is extracted from them — they remain the exploratory source
material, cross-referenced from the RFC, per the existing convention.

## Backlog this creates

The 14 currently-accepted RFCs that existed when this stage was introduced (RFC-0008,
0036, 0037, 0060, 0061, 0067a, 0071, 0072, 0078, 0079, 0081, 0082, 0083, 0084 — see
`INDEX.md`) had not been through `3-integrated` under this definition; they were
accepted before this stage existed. This is not retroactively re-litigated all at
once — it's a real backlog, sized honestly, to be worked through over time rather than
blocking anything immediately.

**Updated 2026-07-10:** RFC-0067a, RFC-0078, and RFC-0083 became the first three to move
through it — merged into `public/reference/spec/` (`types.md`, `expressions.md`,
`modules.md`), each gaining `impl_status`/`impl_tracking` and a linked tracking task. All
three surfaced real problems while writing the worked examples this stage requires,
confirming the stage does what it was built for: RFC-0067a's own text removed the
explicit dereference operator without specifying how to read a plain value out of a
reference (fixed, extending RFC-0066 §3a's type-directed-binding pattern); RFC-0083's
motivating example turned out to be obsolete under the ratified allocator design and was
rewritten; and a pre-existing, unrelated contradiction between `types.md` and
`expressions.md` over `&var`-on-field-paths (RFC-0045, already implemented, was reflected
in one file but not the other) was caught and fixed along the way. 6 RFCs remain in the
backlog: RFC-0008, 0036, 0037, 0060, 0061, 0071. (RFC-0079 and RFC-0084 left the backlog
by refusal rather than integration, same day — both had reverted to proposing nothing
beyond what already exists.)

**Updated 2026-07-11:** RFC-0060 (Aspect Impl Coherence) integrated on its own, ahead of
implementing issue #238 (the coherence pipeline this RFC specifies) — deliberately, since
every prior integration this pass had found a real problem, and this RFC cross-references
two already-integrated RFCs (RFC-0072, RFC-0081) plus two still-unsettled ones (RFC-0036,
RFC-0080). Merged into `declarations.md` as a new "Aspect Implementation Coherence"
section; two forward-references in "Negative Bounds"/"Negative Impls" that had been
written anticipating this integration now point here instead of saying "accepted, not yet
integrated." Also surfaced a real, unrelated staleness bug: `error-codes.md` never
actually documented T0009-T0012 despite the interpreter using them, and two still-draft
RFCs (RFC-0032, RFC-0033) had recommended error codes (T0013, T0014) that were both
already claimed by other, unrelated shipped features by the time anyone checked — T0014
is what RFC-0060 itself needed, so RFC-0033's stale recommendation was flagged in place
rather than silently left to collide. 5 RFCs remain in the backlog: RFC-0008, 0036, 0037,
0061, 0071.

**Updated again, same day:** RFC-0072 (Negative Bounds), RFC-0081 (Negative Impls), and
RFC-0082 (Associated Types) followed RFC-0067a/0078/0083 into `3-integrated` — merged
into `public/reference/spec/declarations.md`. All three needed real fixes first, not
just formalities: RFC-0072's own examples still used pre-split bracket-channel allocator
syntax (`@[r] T`); RFC-0081 pointed to `#[derive(Send)]` and RFC-0012, both retired
(now `@derive`/RFC-0093); RFC-0082 still named the allocator aspect `Region` and used
`@[r] expr`, and its §7 amended RFC-0069's `SubRegion`, a concept that no longer exists
anywhere in the ratified design — marked historical-only rather than integrated, not
silently carried forward as if still current. A pre-existing gap from the *previous*
integration pass was also caught here: `declarations.md`'s "Receiver Forms" section
still described `*T`/`*mut T` pointers, missed when RFC-0067a's `&T`/`&var T` rename
touched `types.md` and `expressions.md` but not this file.

## Working rules, adopted 2026-07-09

**Check `INDEX.md` before opening a new RFC.** RFC-0055 (Comptime, draft since
2026-06-05) already covered a large fraction of what RFC-0092/0093/0094 ended up
specifying independently, discovered only after the fact because nothing was checked
against it first. This is the single highest-leverage rule here — it's what would have
prevented the concrete, expensive failure that prompted this whole document.

**Every dated strategic-overview snapshot does a triage pass, not just narration, and
reads from/writes back to `reports/strategy/OBJECTIVES.md`.** Explicitly call out stale
drafts, dangling dependency pointers (e.g. an RFC still depending on something
now-refused), and mergeable/supersedable RFCs each cycle — not just what moved, but what
should move and hasn't. Before writing one: `OBJECTIVES.md` did not exist before
2026-07-09 because nothing in this repo persisted long-term priorities or open triggers
between dated snapshots — each strategic-overview only referenced the previous one in
prose, so "what are we currently prioritizing" had to be reconstructed by finding
whichever dated file was most recent. Now: check its open triggers (§3) against real
progress, update its priorities (§2) in place, add anything new, append to its review
log (§4), and only then decide whether a new dated narrative snapshot is warranted (see
"Triggering a new strategic overview" below — this document changing is not always
itself sufficient reason for one).

**Triggering a new strategic overview stays event-based, not calendar-based** —
matching the actual history (07-01 → 07-05 → 07-06 → 07-08, each written at a real
inflection point). Natural triggers: a cluster's `3-integrated` backlog has real
candidates ready, `rfc.py check`/`index --check-drift` reports meaningful drift, or
enough has changed that `OBJECTIVES.md` no longer reflects reality. Do not tie this to
a specific lifecycle transition (e.g. `3-integrated` promotions) — that conflates a
planning document with a technical soundness-checking gate, which is `3-integrated`'s
own concern (above), performed whenever a promotion is actually attempted, not deferred
to wait for the next planning cycle.

**Prune open questions inside RFC bodies harder.** Only genuinely blocking questions
stay inline. RFC-0012 accumulated 18 open questions before being split — most weren't
blocking anything, they just made the document read as permanently unfinished. If a
question isn't load-bearing for acceptance, it either gets resolved, cut, or moved
somewhere it won't be re-read on every pass.

**Brief design review adversarially (adopted 2026-07-26).** Whoever reviews an RFC — for
`1-under-review`, for acceptance, or for `3-integrated`'s worked-example soundness hunt —
is asked to **break the design, and told which decisions to attack**, not asked whether it
looks reasonable. Three things belong in that request. **Name the specific choices the
reviewer should attempt to falsify, and state that they are not settled merely because the
author wrote them down** — otherwise a reviewer reads the RFC's own rationale as the
premise and checks only internal consistency, which by construction cannot surface a wrong
decision; RFC-0063 was internally consistent throughout. **Supply what has already gone
wrong in this cluster**, because the useful prior is where this design has been wrong
before, not where a fresh reader would look. **Ask for a counterexample rather than an
opinion** — a worked example that produces a contradiction, in the same form
`3-integrated` already requires. Say explicitly that an honest all-clear is an acceptable
outcome, so that a reviewer with nothing to report does not manufacture something; an
invented objection costs a real amendment cycle to disprove. This is the design-stage
instance of the same practice `metel-core`'s `AGENTS.md` specifies for branch review, and
the two should stay recognisably the same discipline.

## Specification rules, adopted 2026-07-14

These rules govern what belongs in `public/reference/spec.md` and
`public/reference/spec/*.md` once RFC content is integrated.

**The spec is normative; RFCs are design history.** The public spec states what the
language is. RFCs explain how a design was reached, what alternatives were rejected,
and what is still under review. Once integrated, the spec should stand on its own.

**Only integrated content belongs in the spec.** `2-accepted` is not enough. Until an
RFC reaches `3-integrated`, the public spec does not grow text for it beyond a
version-based future-availability marker where genuinely needed.

**The spec describes behavior, not motivation.** Public spec text should define syntax,
static semantics, dynamic behavior, and availability. Design rationale, historical
notes, trade-off discussion, and issue triage stay in RFCs, reports, changelog notes,
or internal docs unless they are needed to prevent a reader from misreading the rule.

**Every language-visible feature must specify all three layers.** A spec addition is
not complete unless it covers:
- syntax: what source forms are accepted;
- static semantics: name resolution, typing, validity constraints, and compile-time
  errors where relevant;
- runtime behavior: evaluation order, side effects, produced values, and runtime
  failures where relevant.

**New syntax does not silently weaken old syntax.** If a proposal removes, narrows, or
steals a previously valid source form, that has to be called out explicitly in the RFC
and settled as a design decision before integration. "Rare in practice" is not enough
on its own.

**Surface-syntax RFCs must prove adjacent interactions, not only the happy path.**
Grammar changes are checked against nearby syntax, precedence, existing parses,
destructuring forms, type syntax, overload behavior, and evaluation-order consequences.
The integration examples should stress the collision boundaries, not just showcase the
feature working in isolation.

**Examples in the spec should carry weight.** Prefer examples that pin down ambiguity,
edge conditions, or interaction rules over examples that merely restate the obvious.
An example that would not catch a misunderstanding is usually documentation garnish,
not spec work.

**Public availability is version-based only.** The public spec may say `Since vX.Y.Z.`,
`Changed in vX.Y.Z: ...`, or `Planned for vX.Y.Z.` It must not mention RFC ids, issue
numbers, tracking links, or other internal process artifacts. Availability is a product
question, not a lifecycle question.

**If spec text and interpreter behavior differ, that is a defect to resolve, not a
state to normalize.** Either the implementation is fixed to match the spec, or the spec
is corrected deliberately in the same work. The public spec must not drift into
describing a half-remembered or aspirational language.

**The spec entry point must match the section files.** `public/reference/spec.md`
cannot describe an older language model than the detailed sections it links to. When a
cluster materially changes the language model, the top-level overview needs the same
update pass, not a deferred "later" cleanup.

## Before opening a new RFC

1. Check `INDEX.md`'s thematic groupings for anything adjacent.
2. Check `REGISTRY.md` for the exact current corpus and status/path inventory.
3. If nothing turns up there but the topic feels like it should have prior art, grep
   `internal/rfcs/` directly — the registry is exact, but the right adjacent RFC may
   still sit in a cluster you weren't expecting.
4. If a real overlap is found, reconcile it as part of the same piece of work, not as a
   follow-up — an unreconciled overlap discovered later costs more than a few extra
   minutes checking now.

## Tooling

`internal/rfcs/tools/rfc.py` (stdlib-only Python, no dependencies) mechanizes the parts
of this process that don't need judgment:

- `rfc.py new "Title" -d "description"` — creates a draft with the next free number,
  and runs a TF-IDF/cosine-similarity check against every existing RFC first, printing
  anything above a similarity threshold before you commit to writing it. Caught the
  RFC-0055/RFC-0092 case in testing (0.47 similarity) — this is the automated version
  of "check the curated map plus the exact registry before opening a new RFC," not a
  replacement for actually reading what it flags.
- `rfc.py transition <id> --to <stage> -r "reason" [--tracking LINK]` — `git mv`s to the
  right directory, updates frontmatter (`status`, `updated`), inserts a dated status
  blockquote, and fixes any other file's literal path references to the old location.
  Rebuilds `REGISTRY.md` and runs `check` afterward automatically. `--to integrated`
  refuses to run without `--tracking`, and sets `impl_status: not-started` alongside it;
  `--to implemented` sets `impl_status: implemented`.
- `rfc.py impl-status <id> --set not-started|in-progress|implemented [--tracking LINK]`
  — updates `impl_status` (and optionally `impl_tracking`) on an RFC already at
  integrated or implemented, without moving it, and rebuilds `REGISTRY.md`. The
  day-to-day command for recording implementation progress between transitions.
- `rfc.py supersede <id> --by <ids> -r "reason"` — the same, plus `superseded_by`. Does
  not write the reconciliation content (what carried forward, what didn't) — that still
  needs a human, or an agent, to actually think about it. Rebuilds `REGISTRY.md`.
- `rfc.py check` — validates frontmatter status matches directory, no duplicate RFC
  ids, no dangling `internal/rfcs/N-stage/rfc-....md` path references anywhere in the
  repo, that generated `REGISTRY.md` matches the current RFC corpus exactly, that the
  curated `INDEX.md` mentions every current RFC at least once, and (since 2026-07-10,
  not retroactive — see above) that any RFC at
  `3-integrated` has `impl_tracking` set, `impl_status` set to a valid value and not
  already `implemented`, and that `public/reference/spec/` references the RFC at all;
  an RFC at `4-implemented` with `impl_status` present is checked for consistency
  (`implemented`) but not required to have the field at all. Read-only. Running it
  against this repo for the first time found, and a follow-up fixed, 21 pre-existing
  problems predating this document: 19 older RFCs using ad hoc status vocabulary
  ("incorporated", "active", "deferred") never standardized against the lifecycle names
  above, normalized to match; and dangling path references, which turned out to be far
  more widespread than the first pass found — the initial path-reference regex silently
  failed to match multi-hyphen directory names like `1-under-review`, so references into
  that whole directory were never actually checked until the regex itself was fixed.
  Once corrected, 20 dangling references surfaced (not 2) across the
  RFC-0025/0028/0046/0047/0048/0050/0051 cluster plus RFC-0006/0049/0052 — all now
  fixed. A later pass (2026-07-10) also found and fixed two RFCs whose own frontmatter
  title/filename still said "Region ..." after the rest of the allocator cluster
  renamed region → allocator (RFC-0066, RFC-0068) — `check` doesn't catch stale titles
  itself, that was found by reading the cluster before ratifying it. `rfc.py check`
  reports clean as of 2026-07-10.
- `rfc.py index --rebuild-registry` — regenerates `REGISTRY.md` from the current RFC
  corpus. This is the exact state inventory, meant to be machine-trustworthy.
- `rfc.py index --check-drift` — checks whether generated `REGISTRY.md` still matches the
  current RFC corpus exactly, and whether curated `INDEX.md` still mentions every current
  RFC at least once. Read-only.
- `rfc.py index --suggest-placement <id>` — cosine similarity between an RFC and each
  `INDEX.md` cluster section's combined text; suggests where it belongs rather than
  deciding it. Verified against three existing placements (RFC-0091, RFC-0074, RFC-0003)
  and agreed with the manual choice in all three.

None of this replaces the `3-integrated` phase's actual judgment work (is the design
sound, do the worked examples really stress-test the interaction) — it only makes the
procedural half (move the file correctly, don't lose a cross-reference, don't forget to
check for an existing RFC first) hard to get wrong by accident.
