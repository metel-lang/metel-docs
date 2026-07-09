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
independently reinvented a large part of it, and several accepted RFCs have historically
turned out wrong only once someone tried to build against them (RFC-0075 is this
project's own repeated cautionary tale for that failure).

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
"implemented," which is exactly the gap that let RFC-0075's failure mode happen: a
design can be accepted on paper and still be wrong in ways nobody notices until
implementation is attempted, or until it's checked against everything else that's also
accepted.

**3-integrated *(new)*.** The RFC's content is incorporated into `public/reference/spec/`
— not just cross-referenced from RFC text, actually merged into the language reference —
and detailed worked examples are written combining this RFC's feature with other
already-integrated features, specifically hunting for soundness gaps at the
intersection, not just re-checking the RFC in isolation. Exit criterion: no known
unsoundness or contradiction between this RFC and the rest of the currently-integrated
spec. If a worked example surfaces a real problem (as happened repeatedly this
session — the comptime/structural-records circular dependency, the `Linear`
auto-impl-vs-derive miscategorization, RFC-0080 shipping syntax RFC-0012 had already
rejected), that's this phase doing its job, not a failure of it — the RFC goes back for
amendment rather than proceeding to implementation carrying the problem forward.

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
