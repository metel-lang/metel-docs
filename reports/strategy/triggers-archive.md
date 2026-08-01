---
id: strategy-triggers-archive
title: "Strategic Triggers — Archive"
type: report
---

# Strategic Triggers — Archive

Closed or superseded triggers relocated from `OBJECTIVES.md` §3, once resolved for at
least two review cycles and no longer load-bearing for an active priority's own
narrative section — see `PROCESS.md`'s archiving rule. Numbering matches
`OBJECTIVES.md` exactly: these are the same triggers, moved verbatim, never renumbered
or rewritten. `OBJECTIVES.md` §3 keeps a one-line stub pointing here for each.

Trigger 6 stays in `OBJECTIVES.md` itself despite being closed, because Priority 1's own
narrative section is built around narrating it directly — moving it would sever that
context. Archiving is about scannability, not about how definitively something closed.

---

1. ✅ **Fired, 2026-07-09.** Re-reading RFC-0080 confirmed it did not naturally extend to
   derive-as-codegen — `Clone`'s derive was one hardcoded example, and its Unresolved
   Questions never mentioned a general mechanism. Directly caused the RFC-0012 →
   RFC-0092/0093/0094/0095 split.

5. ✅ **Fired and resolved, 2026-07-10.** The former Priority 1 moved. This trigger did its
   job: it named the pattern that was actually happening (L3 activity masking L2 inaction)
   and caused the check that led to ratification.

8. 🟡 **Fired repeatedly; the mechanism works.** Twelve RFCs moved through `3-integrated` and
   each surfaced a real problem while writing worked examples — RFC-0067a's missing
   value-extraction rule, RFC-0083's obsolete motivating example, a pre-existing
   `types.md`/`expressions.md` contradiction over `&var` field paths, RFC-0072's stale
   bracket-channel examples, RFC-0081's dangling `#[derive]` reference, RFC-0082 amending a
   retracted RFC's dead concept. Of the original backlog only RFC-0008 remains, still gated on
   `dyn Aspect` having no consumer. Superseded as a watch item by Trigger 13.

11. ✅ **Re-evaluated and closed, 2026-07-15.** The analogy to the former Priority 1 does not
    hold: the frontier layer is demand-gated in both source documents, blocks only
    user-authored custom allocators, and RFC-0026 needs a rewrite anyway. Signal retained in
    Priority 6's form.

12. ✅ **Fired and resolved, 2026-07-15.** The six RFCs at `3-integrated` all reached
    `4-implemented` within four days — the fastest resolution any trigger here has had.
    Cleanest evidence yet that naming a stall explicitly is what gets it moved.

16. ✅ **Fired and resolved same day, 2026-07-20.** RFC-0097's frontmatter claimed
    `implemented` while `coherence.rs::outermost_id` had no deliberate branch for a bare
    blanket-impl target. Resolved by landing the real check rather than downgrading the
    frontmatter; zero regressions, since the fix only made an already-correct outcome
    deliberate.

17. ✅ **Opened 2026-07-20; answered 2026-07-21 — both, in that order.** Would the next cycle
    move a higher-ranked priority, or would reference/deref ergonomics churn keep substituting
    for it? It did both: RFC-0107/0108/0110 were implemented and RFC-0111 was opened *and*
    implemented — all ergonomics, with records and allocators untouched — and then the cluster
    was named and corrected within the same cycle, sweeping RFC-0089/0090/0091/0109 to review
    and writing RFC-0113 from nothing. Recorded honestly rather than as a clean win: **the
    correction happened because the trigger was read back, not because the priority was
    followed.** Superseded going forward by Trigger 20, which measures the same thing without
    depending on someone remembering to re-read this file.
