---
id: strategy-process
title: "Strategic Overview Process"
type: process
status: active
last_reviewed: '2026-08-01'
---

# Strategic Overview Process

**Companion to `OBJECTIVES.md`, mirroring `internal/rfcs/PROCESS.md`'s role for the RFC
lifecycle.** `AGENTS.md`'s "Strategic Planning" section states the *what* and *when* —
the living-doc/dated-snapshot split, and that triggering a new snapshot is event-based.
This document states the *how*: the methodology ten cycles (2026-06-29 through
2026-08-01) converged on by imitation, never written down until now, extracted directly
from what those ten files actually did rather than from what they claimed to do.

**Founding case study.** This document itself is the first artifact of the very process
it describes done consciously rather than tacitly: the 2026-08-01 cycle was run, then
its own methodology was analyzed and written up at the operator's request, specifically
because "this process emerged naturally but was never documented" — a smaller-scale
version of the same drift `PROCESS.md` (RFC side) exists to prevent, applied to itself.

---

## 1. The two-layer split, restated precisely

- **`OBJECTIVES.md`** is current-state, updated in place. Its §2 priorities *table* is
  **overwritten** each cycle — it answers "what is true right now," not "what has this
  document ever said." Its §2 prose subsections and §3 triggers are **append-only** —
  see §3 below for why that distinction is deliberate, not an accident.
- **`strategic-overview-YYYY-MM-DD.md`** is the point-in-time narrative record. It is
  never edited after the fact except to fix an error found the same day (matching the
  same-day-correction pattern this series already uses inside single cycles).
- **`OBJECTIVES.md` §0, added 2026-08-01, has the same split inside one section.** "At a
  glance" is overwritten each cycle — a 5-8 line answer to "what are we doing and why,"
  for someone operating at the architectural level who should not have to read
  everything below it to find out. Its "Operator directives" subsection is append-only,
  and is the **one place operator intent enters this process as a first-class input**
  rather than being reconstructed after the fact from a decision made mid-conversation
  about something unrelated (which is how it worked before 08-01 — real steering
  moments like the RFC-0090/RFC-0100 splits only got recorded because the same agent
  happened to write the next overview). **Log a directive the moment it's made, in any
  conversation, not only during a cycle** — proactive capture, not only when the
  operator explicitly says "log this as a directive." Every cycle checks §2's derived
  priorities against this section explicitly and must **flag, not silently resolve**,
  any place they disagree — the process synthesizes from the corpus, but the operator's
  stated intent is not just one more input to be weighed against it.

## 2. Verification discipline — the load-bearing rule

**Every claim in a dated overview is checked against a primary source, never restated
from memory, from a prior cycle's file, or from an RFC's own frontmatter without
cross-checking the code or the tracker it claims to describe.** This is the single rule
that makes these documents worth more than a status meeting's notes, and it has never
once been skipped across ten cycles — but it has also never been written down, so each
new cycle has had to infer it by noticing how much verification the previous ones did.

Concretely, "primary source" means:

- **A grammar or code claim** → read the actual `.pest`/`.rs` file, or run the
  interpreter against a constructed `.mtl` repro. Not "the RFC says this is how it
  parses." (Example: `HasField`'s bound syntax was checked directly against
  `grammar.pest` and found never to have parsed at all, 07-23.)
- **An RFC lifecycle claim** → read the file's own frontmatter directly, and run
  `rfc.py index --rebuild-registry` yourself before quoting `REGISTRY.md`'s tallies,
  rather than trusting the checked-in copy is current. (`rebuild_registry()` runs
  automatically on `rfc.py transition`/`impl_status`/`supersede`, so it is *usually*
  fresh — but "usually" is not "checked," and a cycle that quotes a stale tally without
  having caused or verified the regeneration itself is one grep away from being wrong.)
- **An issue-tracker claim** ("Priority N has zero open issues") → query the tracker
  directly (`tea issues list`), don't infer it from an RFC's `impl_tracking` field,
  which can lag or be absent even when real tracked work exists.
- **A "this branch/commit is merged" claim** → `git log`/`git merge-base
  --is-ancestor` on the actual ref, not on what a PR's UI state claims.
- **A "this file hasn't changed since X" claim** → `git log -- <path>`, not an
  `updated:` frontmatter field, which can itself go stale (this is exactly the failure
  mode Trigger 16 caught in RFC-0097).

If a claim cannot be verified this way in the time available, the overview says so
explicitly ("not yet inspected in detail," "reasoned about, not tested") rather than
presenting it with the same confidence as a verified one. Precedent: PR review briefs
in this project already distinguish "tested" from "reasoned about" for exactly this
reason; dated overviews hold themselves to the same bar.

## 3. Trigger lifecycle rules

- **Append, never rewrite.** A trigger's original wording stays exactly as written,
  even when later found incomplete or wrong. A closure or update is a **new dated
  paragraph appended after** the original text, prefixed with its own status marker.
  This is what lets a future cycle audit whether a trigger's *original* framing held up
  — rewriting it in place would erase the evidence.
- **Status markers**: ⬜ open, ✅ fired/resolved/closed, 🟡 fired repeatedly / partially
  resolved / needs its own nuance that doesn't fit the binary. Use 🟡 rather than forcing
  a trigger that's genuinely mixed into ✅ or ⬜.
- **A closure requires the *strongest available* resolution, not the minimal one that
  technically satisfies the falsifier's letter.** Precedent: Trigger 24's falsifier
  named "one tracked issue against RFC-0116" specifically; when RFC-0115 (not RFC-0116)
  filed the first issue, the trigger recorded that as a **partial** trip and stayed open
  until RFC-0116 itself reached `3-integrated` the same day, and later `4-implemented`.
  Don't close a trigger on a technicality it wasn't really asking about.
- **A trigger that turns out refuted or complicated should say so precisely, including
  the caveat that limits the good news.** Precedent: Trigger 21 (worry: Priority 5 will
  expand to fill available effort) was not simply marked "refuted" when Priority 5's
  backlog stayed flat — the entry names the *actual* mechanism (bugs found while
  building Priority 2, not the ranking pulling effort there) and flags that this may not
  replicate without the same forcing function present next time.
- **New triggers get the next sequential number**, appended after the last one, never
  renumbered. Cross-reference by number in the dated overview, not by paraphrase alone.
- **Archive once genuinely stale, added 2026-08-01.** Once a trigger has been ✅/🟡
  closed for at least two review cycles *and* is not the primary subject of an active
  priority's own narrative section, move its full text (verbatim, unrenumbered) to
  `triggers-archive.md` and leave a one-line stub in its place here pointing to it. This
  is purely for scannability — nothing is deleted, and the append-only rule above still
  applies inside the archive file itself. Precedent for the exception: Trigger 6 stayed
  in `OBJECTIVES.md` despite being closed, because Priority 1's narrative section is
  built around narrating it directly; moving it would sever that context. A trigger
  closed *this* cycle or last cycle stays put regardless of length — "at least two
  cycles" is deliberately conservative, so a trigger doesn't get archived before anyone
  has had a chance to notice if its closure was premature.

## 4. The dated overview's structural template

Every cycle since 2026-07-01 has converged on the same five-part shape. Use it,
including the parts that feel like overhead on a quiet cycle — a cycle with little to
report is exactly when skipping the honest-assessment section is most tempting and most
likely to hide that nothing happened.

1. **Framing paragraph** (in the doc's opening italics, not a numbered section): what
   makes *this* cycle's shape different from the last one, and what the right skeptical
   question is for it. **This is not a fixed template question** — 07-23's was "did this
   depth constitute progress or an elaborate form of not starting" (a pure-design week);
   08-01's was "does a week of real building change what the standing risk says" (an
   engineering week). Pick the question the cycle's own shape actually raises, state it
   explicitly, and answer it in §2 rather than letting the narrative imply an answer.
2. **"What actually happened"** — numbered, evidence-cited, in chronological or
   dependency order. This is the only section allowed to just report; every other
   section must evaluate.
3. **"Honest assessment"** — prose, self-critical, answering the framing question
   directly. Refuses easy credit: if something worked, say what mechanism actually
   produced it (see the Trigger 21 precedent in §3) rather than crediting the
   nearest-sounding intention. Names misses plainly (RFC-0122 missing its own stated
   bar, 08-01) rather than letting them pass unremarked because the cycle's headline
   result was otherwise strong.
4. **"Verified findings worth carrying forward"** — bullets, each independently
   checkable, each stating *how* it was checked, not just what was found.
5. **"New and updated triggers"** — numbered against `OBJECTIVES.md`'s own trigger
   numbers, each with a one-line pointer to what it's watching for and why it matters
   now specifically (not a restatement of the trigger's full text).
6. **"References"** — every RFC, issue, and prior overview the cycle actually touched,
   so a future cycle can re-verify without re-deriving.

Frontmatter: `id: strategic-overview-YYYY-MM-DD`, `title: "Language Design — Strategic
Overview"`, `type: report`, `created_date: 'YYYY-MM-DD'`. Unchanged since 2026-06-29;
kept identical across all ten cycles so the series is mechanically identifiable.

## 5. Running a cycle, in order

Matches `OBJECTIVES.md`'s own "How to use this document" list; this expands each step
with the verification discipline from §2:

0. **Steering checkpoint, added 2026-08-01 — always runs, before any research or
   re-verification starts.** State plainly, in a few sentences: what changed since
   `last_reviewed` that's likely to matter, and where §2's priorities currently seem to
   stand as a result. Then ask explicitly whether the operator wants to redirect before
   the cycle proceeds — don't just proceed and let them correct the finished artifact
   afterward, which is how every cycle before 08-01 worked and is strictly more
   expensive to redo. This runs *every* cycle, even a quiet one with nothing contentious
   to flag — the check itself is cheap, and skipping it on the cycles that look quiet is
   exactly when an operator's actual redirect would be missed silently. If the operator
   redirects, treat that redirect as a new entry in §0's Operator Directives before
   continuing, not as a one-off instruction that only affects this cycle's prose.
1. **Check §3's open triggers against real progress since `last_reviewed`**, verifying
   each against a primary source (§2 above), not against what the previous cycle's
   narrative implied would happen. Mark fired/closed with a dated, evidence-cited
   append (§3); leave genuinely untouched triggers alone rather than padding them with
   a "still open" restatement that adds no information.
2. **Re-verify §2's priorities table against current RFC/`REGISTRY.md` state and the
   issue tracker directly** — not "restated unchanged." Rebuild `REGISTRY.md` first if
   there's any doubt it reflects today's transitions.
3. **Add any new triggers this cycle surfaced**, sequentially numbered, each stating
   what it's watching for and what would resolve it (a falsifier, where one is
   nameable — see Trigger 24/25's precedent for what a good falsifier looks like:
   specific, dated, and harder to satisfy on a technicality than it looks).
4. **Append one line to §4's review log** — dense, specific, citing issue/RFC/commit
   identifiers, not a summary of the summary. The review log is itself append-only and
   has never had an entry removed or shortened after the fact.
5. **Update `last_reviewed`** in `OBJECTIVES.md`'s frontmatter.
6. **Then** decide whether a dated narrative snapshot is warranted — per `AGENTS.md`
   and `internal/rfcs/PROCESS.md`, this stays event-based (a real inflection point:
   a milestone closing, a cluster reaching `3-integrated` in force, `rfc.py check`
   reporting meaningful drift, or `OBJECTIVES.md` visibly no longer matching reality),
   not calendar-based. **Triggering stays human-prompted by deliberate choice, not
   historical accident** (decided 2026-08-01, when this document was written): every
   cycle so far started because an operator asked for one, and that is judged
   preferable to an agent unilaterally deciding a strategic review is warranted in the
   middle of unrelated work. If a natural trigger fires while doing something else,
   name it to the operator and let them decide whether to run the cycle now — don't
   run it unasked and don't stay silent about noticing it either.
7. If a dated snapshot is warranted, write it per §4's template, then commit both files
   together (the living doc's updates and the new dated file reference each other and
   should land in one commit) and, in `metel-core`, bump the `docs` submodule pointer
   the same way any other docs change does.

## 6. What this process is not

- **Not a replacement for `internal/rfcs/INDEX.md`** (RFC-level thematic state) or
  `internal/rfcs/PROCESS.md` (RFC lifecycle mechanics) — `OBJECTIVES.md` is the layer
  above both, tracking *why* priorities are what they are, not RFC-by-RFC status.
  Restated here because it is easy to let a strategic overview re-derive RFC lifecycle
  facts `REGISTRY.md` already states authoritatively, rather than just citing it.
- **Not a venue for doing design work.** A strategic overview evaluates and
  synthesizes; it does not itself resolve open RFC questions. When a cycle's research
  surfaces a real design finding (e.g. a grammar bug, a missing dependency), the finding
  gets fixed in the RFC it belongs to, and the overview *reports* that it did — it
  doesn't carry the fix itself as prose living only in the overview.
- **Not calendar-scheduled**, and not a checklist to run through mechanically without
  the verification and honest-assessment discipline in §§2–4 — a cycle that updates
  `OBJECTIVES.md`'s dates without re-verifying its claims is worse than not running one,
  because it launders staleness into an apparently-fresh `last_reviewed` date.
