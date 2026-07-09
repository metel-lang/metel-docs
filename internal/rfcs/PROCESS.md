---
id: rfc-process
title: "RFC Process"
type: process
last_updated: '2026-07-09'
---

# RFC Process

This document did not exist before 2026-07-09 — the lifecycle below had been running as
an implicit convention (directory names only) for 94 RFCs with nothing written down
explaining it. Written down now alongside `INDEX.md`, prompted by two things surfacing
in the same sitting: RFC-0055 sat undiscovered in draft for five weeks while RFC-0092
independently reinvented a large part of it, and RFC-0063 — this project's own concrete
precedent for the failure `3-integrated` exists to catch.

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
anything not yet implemented — 14 RFCs currently sit here with no further gate before
"implemented," which is exactly the gap that let RFC-0063's history happen: a design can
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

**4-implemented.** Built against the integrated spec, not against the accepted RFC text
directly — by the time something reaches this stage, "the spec" and "the RFC" should
agree, because §3-integrated is what makes them agree.

**5-superseded / 6-refused.** Terminal states, reachable from any stage. Superseded RFCs
keep a pointer to what replaced them; refused RFCs are kept as historical record with
the refusal reason. Living reports (`reports/substructural-types/*.md` and similar) are
not superseded when an RFC is extracted from them — they remain the exploratory source
material, cross-referenced from the RFC, per the existing convention.

## Backlog this creates

The 14 currently-accepted RFCs (RFC-0008, 0036, 0037, 0060, 0061, 0067a, 0071, 0072,
0078, 0079, 0081, 0082, 0083, 0084 — see `INDEX.md`) have not been through
`3-integrated` under this definition; they were accepted before this stage existed. This
is not retroactively re-litigated all at once — it's a real backlog, sized honestly as
14 RFCs' worth of spec-integration-plus-worked-examples work, to be worked through over
time rather than blocking anything immediately.

## Working rules, adopted 2026-07-09

**Check `INDEX.md` before opening a new RFC.** RFC-0055 (Comptime, draft since
2026-06-05) already covered a large fraction of what RFC-0092/0093/0094 ended up
specifying independently, discovered only after the fact because nothing was checked
against it first. This is the single highest-leverage rule here — it's what would have
prevented the concrete, expensive failure that prompted this whole document.

**Every dated strategic-overview snapshot does a triage pass, not just narration.**
Explicitly call out stale drafts, dangling dependency pointers (e.g. an RFC still
depending on something now-refused), and mergeable/supersedable RFCs each cycle — not
just what moved, but what should move and hasn't.

**Prune open questions inside RFC bodies harder.** Only genuinely blocking questions
stay inline. RFC-0012 accumulated 18 open questions before being split — most weren't
blocking anything, they just made the document read as permanently unfinished. If a
question isn't load-bearing for acceptance, it either gets resolved, cut, or moved
somewhere it won't be re-read on every pass.

## Before opening a new RFC

1. Check `INDEX.md`'s thematic groupings for anything adjacent.
2. If nothing turns up there but the topic feels like it should have prior art, grep
   `internal/rfcs/` directly — the index is a manual snapshot and may already be stale.
3. If a real overlap is found, reconcile it as part of the same piece of work, not as a
   follow-up — an unreconciled overlap discovered later costs more than a few extra
   minutes checking now.

## Tooling

`internal/rfcs/tools/rfc.py` (stdlib-only Python, no dependencies) mechanizes the parts
of this process that don't need judgment:

- `rfc.py new "Title" -d "description"` — creates a draft with the next free number,
  and runs a TF-IDF/cosine-similarity check against every existing RFC first, printing
  anything above a similarity threshold before you commit to writing it. Caught the
  RFC-0055/RFC-0092 case in testing (0.47 similarity) — this is the automated version
  of "check `INDEX.md` before opening a new RFC," not a replacement for actually reading
  what it flags.
- `rfc.py transition <id> --to <stage> -r "reason"` — `git mv`s to the right directory,
  updates frontmatter (`status`, `updated`), inserts a dated status blockquote, and
  fixes any other file's literal path references to the old location. Runs `check`
  afterward automatically.
- `rfc.py supersede <id> --by <ids> -r "reason"` — the same, plus `superseded_by`. Does
  not write the reconciliation content (what carried forward, what didn't) — that still
  needs a human, or an agent, to actually think about it.
- `rfc.py check` — validates frontmatter status matches directory, no duplicate RFC
  ids, no dangling `internal/rfcs/N-stage/rfc-....md` path references anywhere in the
  repo. Read-only. Running it against this repo for the first time found, and a
  follow-up fixed, 21 pre-existing problems predating this document: 19 older RFCs
  using ad hoc status vocabulary ("incorporated", "active", "deferred") never
  standardized against the lifecycle names above, normalized to match; and dangling
  path references, which turned out to be far more widespread than the first pass
  found — the initial path-reference regex silently failed to match multi-hyphen
  directory names like `1-under-review`, so references into that whole directory were
  never actually checked until the regex itself was fixed. Once corrected, 20 dangling
  references surfaced (not 2) across the RFC-0025/0028/0046/0047/0048/0050/0051 cluster
  plus RFC-0006/0049/0052 — all now fixed. `rfc.py check` reports clean as of
  2026-07-09.
- `rfc.py index --check-drift` — compares every RFC's own `updated`/`date` frontmatter
  against `INDEX.md`'s `last_built`; flags anything changed since. Read-only.
- `rfc.py index --suggest-placement <id>` — cosine similarity between an RFC and each
  `INDEX.md` cluster section's combined text; suggests where it belongs rather than
  deciding it. Verified against three existing placements (RFC-0091, RFC-0074, RFC-0003)
  and agreed with the manual choice in all three.

None of this replaces the `3-integrated` phase's actual judgment work (is the design
sound, do the worked examples really stress-test the interaction) — it only makes the
procedural half (move the file correctly, don't lose a cross-reference, don't forget to
check for an existing RFC first) hard to get wrong by accident.
