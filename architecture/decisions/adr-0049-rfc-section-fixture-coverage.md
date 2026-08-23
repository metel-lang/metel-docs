---
id: adr-0049
title: "Link Fixtures to RFC Sections and Gate `4-implemented` on Coverage"
date: '2026-08-15'
status: implemented
relates: adr-0040
implements: issue #723
updated: '2026-08-23'
---

> **Status bumped `proposed` → `implemented`, 2026-08-23.** Stale — this document's own
> "Sequencing" section already recorded all six steps landed (steps 1-4 earlier in the
> 2026-08-15 cycle, steps 5-6 on 2026-08-19: CI wiring in both metel-core and
> metel-docs-internal, and the `COVERAGE-BASELINE.json` ratchet), but nobody had updated
> the frontmatter to match. Found while checking whether metel-core#723 (which this ADR
> implements) was already fixed — it was, and had been for four days. Closing #723 in
> the same change.

## Context

`4-implemented`'s entire definition is "spec and interpreter agree" (`PROCESS.md`), and
`rfc.py transition <id> --to implemented` already refuses to run over a stale "Not yet
implemented" spec callout — but nothing checks the half of that claim that actually
matters: that a fixture exists which would fail if the interpreter stopped agreeing.
`#710`'s audit and its prior instances (#656/#658/#668, #712) are repeated cases of
"typechecks, passes review, reaches `4-implemented`-adjacent code — wrong at runtime,
uncaught for a while."

Issue #723 proposed a fix: a fixture-sidecar field naming the RFC it demonstrates, and a
`rfc.py check` rule validating the reference. Investigating that proposal this cycle
(while drafting RFC-0134) found three more of these gaps in one afternoon — RFC-0061 §7
(function types satisfy no aspects; #739), RFC-0082 §1.2/§3 (associated-type projections
don't resolve; #740), RFC-0116 §3 (local aspect impls on records; #581/#239) — and in
every case, **the RFC already had citing fixtures.** A whole-RFC link would have reported
all three covered.

That finding drove the design below through four rounds (recorded across #723's comment
thread; this ADR consolidates them into one document, per this project's own guidance
that a reversal especially needs its reasoning kept, not just its conclusion):

1. Section-level linking, not whole-RFC — the only granularity that would have caught
   any of the three cases above.
2. A baseline run against the real corpus (47 in-scope RFCs, 893 fixtures, 127 normative
   sections), to check the design against reality before committing to it rather than
   guessing at the numbers.
3. That baseline surfaced a fourth finding while reading, not scanning: a fixture citing
   RFC-0116 §3 turned out to be a *negative* fixture proving the section's limitation, not
   a positive one demonstrating it works — which a naive "any citation counts" rule would
   have scored as covered, on the exact RFC already known to be broken.
4. Which forced the exemption mechanism to be typed (`untestable` / `blocked` /
   `elsewhere`) instead of a free-text escape hatch, so a reviewer can tell "this can
   never be tested" apart from "this isn't tested yet" apart from "this is tested, just
   not here" — and so the tool can hold `blocked` entries to the same staleness check it
   already applies to the spec callout.

## Decision

### 1. Fixtures cite RFC *sections*, not RFCs

A new optional key on a fixture's `[options]` sidecar TOML (no new table, no change to
how the fixture runs):

```toml
[options]
rfc = ["rfc-0061§7.2", "rfc-0061§7.4"]
```

**Grammar**, worked out precisely rather than left to the example above to imply:

```
citation   := rfc-id ( "§" section )?
rfc-id     := "rfc-" digit{4}                     ; e.g. rfc-0061
section    := part ( "." part )?
part       := digit+ letter?                      ; e.g. 7, 9c, 3a
```

The letter-suffix case is real, not hypothetical — checked against the corpus while
writing this: `## 9a.`/`9b.`/`9c.` (RFC-0071), `### 3a.` (RFC-0082), `## 2a.` (RFC-0118),
`## 3a.` (RFC-0067a), `### 1a.` (RFC-0110) are all live section headers. An earlier draft
of the Baseline section below used a section-matching regex without the letter-suffix
case and silently undercounted; see the Addendum for the correction. Any coverage tool
built from this grammar needs the same case from the start.

Bare `rfc-NNNN` (no section) stays legal for RFCs with no numbered sections. Section
identifiers are the unit these RFCs are already written in (`## 7.`, `### 9c.`) — no new
authoring convention, only a reference syntax `harness/fixture.rs` learns to parse
alongside the existing `move_check`/`runner`/`prelude` keys, as `Vec<String>` validated
against the grammar above rather than a free-form string.

**Fixture kind is read from the existing `[expect]` block, not duplicated onto the
citation.** A fixture already declares whether it's positive or negative via
`expect.status` (`"success"` vs. `"typecheck_error"` and friends) — the §2 mandate below
("kind-matched fixture") cross-references that existing field against what the cited
section specifies, rather than adding a second place to say the same thing that could
drift from the first.

**The existing prose-comment citation stays, as a human-readable mirror, not the source
of truth.** 107 fixtures already open with a comment like `// RFC-0082 §3a: ...` — the
sidecar `rfc =` key becomes what tooling reads, but the comment isn't deleted on
migration. Same split already adopted for the RFC side (§3 below): frontmatter for
machines, inline text for a reader mid-document. Cost accepted, not hidden: the two can
drift (a corrected section number updated in one and not the other) exactly the way a
spec callout can go stale. **Required in v1, not deferred** — see §4's drift check below.
An earlier draft of this paragraph called that check "worth doing eventually," which is
the same failure this whole design exists to stop: a known gap, named and then scheduled
for a future with nothing forcing it to arrive. Reversed on direct instruction rather than
left as written.

### 2. The mandate: every normative section of a `4-implemented` RFC needs ≥1 passing,
### kind-matched fixture

Not "every fixture cites an RFC" — parser regressions and internal-error guards
legitimately cover nothing, and most of the corpus has no sidecar at all today. The rule
runs the other direction: **every normative section**, at the point an RFC transitions to
`4-implemented`, **needs at least one fixture whose kind matches what the section
specifies** — a section describing behavior needs a fixture that runs and asserts; a
section specifying an *absence* (e.g. RFC-0061 §7.3, "aspects function pointers do not
implement") is correctly covered by a `neg_*`/`expect`-error fixture, and requiring a
positive one for it would be incoherent. This directly answers #723's own open question
(positive-only vs. typecheck-only fixtures): match the fixture kind to the section kind,
don't mandate one shape for both.

**Non-normative sections are exempt by name, not by hand**: Summary, Motivation,
Background, Prior Art, Alternatives Considered, Open Questions, References, Decision.
Only numbered proposal sections carry the mandate.

### 3. What remains gets a typed exemption, not a free-text one

**An earlier draft of this section showed the YAML floating on its own, never fitted into
an actual RFC file, and never gave the inline half of §1's frontmatter/inline split a
concrete syntax the way §1 did for fixtures.** That left "how does a section declare
itself untestable" answerable in concept but not in practice — fixed here with a full
worked example, both halves, matching a real RFC's actual frontmatter fence:

```yaml
---
id: rfc-0061
title: "Structural Aspect Bounds"
date: '2026-07-01'
status: implemented
coverage:
  "3": { kind: elsewhere, reason: "coherence overlap check", ref: "metel-frontend/src/coherence.rs::impls_actually_overlap tests" }
  "4b": { kind: blocked, reason: "no mutation-qualifier syntax exists yet", ref: "rfc-0134" }
  "7.3": { kind: untestable, reason: "claim is about compiler-internal representation" }
---
```

`coverage` is a new top-level frontmatter key, keyed by section number (the same strings
§1's citation grammar validates against), sitting alongside `id`/`status`/`impl_status`
exactly the way those already do — frontmatter is what `rfc.py check` reads, per §1's own
"machines read frontmatter" split.

**The inline half**, for a reader mid-document rather than a tool — reusing the dated
status-blockquote convention RFC files already carry (RFC-0061 itself has five), scoped
to one section instead of the whole document, placed directly under the section heading
it exempts:

```markdown
### 7.3 Aspects function pointers do not implement

> **Coverage: untestable** (see frontmatter). This section's claim is about
> compiler-internal representation, not observable behavior.
```

No new convention invented for either half — the frontmatter key follows `impl_status`'s
own precedent, the inline callout follows the dated-blockquote precedent already used
throughout this exact RFC. Same drift risk as §1's fixture-side mirror, same answer: §4's
drift check (below) covers this pairing too, not only the fixture/sidecar one — required
in v1 for the identical reason that one is.

Three kinds, each resolving differently, which is exactly why one free-text reason can't
carry them:

| kind | means | resolves how |
|---|---|---|
| `untestable` | permanently outside what a fixture can observe (internal representation, non-functional claims) | never — a standing fact about the section |
| `blocked` | testable in principle, blocked on a dependency that doesn't exist yet | closes when the dependency lands |
| `elsewhere` | tested, but not via an `.mtl` fixture (e.g. a Rust unit test) | already satisfied — needs its pointer kept alive |

`untestable` is the category worth a human eye, since "this can't be tested" is the
easiest claim in the scheme to reach for instead of writing the fixture — the coverage
report surfaces it as its own called-out list rather than folding it into "exempt, done."

### 4. Validation, reusing precedent already in `rfc.py` rather than inventing new checks

- Every cited section exists in the target RFC — catches renumbering drift (RFC-0134's
  own sections were renumbered twice in one week during this cycle).
- Every cited RFC exists and is not superseded/refused.
- The citing fixture actually passes and is not disabled.
- `blocked` entries' `ref` resolves to a real, currently-open RFC or issue, and **must
  fail `check` once that ref closes or lands** — the same failure mode `rfc.py` already
  catches for the "Not yet implemented" spec callout going stale
  (`spec_not_implemented_refs`), applied to a second surface rather than reinvented.
- **The sidecar `rfc =` citation and the fixture's own prose-comment citation agree**,
  wherever the fixture has both. Not deferred: §1 introduces two citations of the same
  fact (frontmatter/sidecar as source of truth, inline text for a reader) specifically
  because that split is useful, and every other place this design uses that same split
  (RFC frontmatter vs. its inline callout) gets a staleness check in this list. Leaving
  this one instance uncovered would mean the newest citation surface in the whole design
  is the one surface allowed to drift silently — parse the RFC id and section out of the
  fixture's leading comment (same `RFC-\d{4}(§section)?` shape already used for the
  Baseline scan above) and diff it against the sidecar's `rfc =` list at the same
  `rfc.py check` pass that validates the sidecar itself, not a later one.
- **The RFC-side `coverage` frontmatter entry and its inline callout agree**, the same
  check as above applied to §3's own frontmatter/inline split rather than only the
  fixture-side one. The previous bullet already claimed this list covered "every other
  place this design uses that same split" — true only once this bullet exists to make it
  true, added alongside the worked example in §3 rather than left as a claim the checker
  doesn't yet back up.
- `elsewhere` entries' `ref` resolves to a real path, where reachable.

### 5. The gate

`rfc.py transition <id> --to implemented` refuses to run if a normative section has
neither a qualifying fixture nor a typed exemption — mirroring the existing refusal over
a stale "Not yet implemented" callout. **This refusal is unconditional on reachability**:
if the fixture corpus can't be found, that is treated as "not verified," not as "pass" —
see §6, which is where this would otherwise have quietly stopped being true.

### 6. Cross-repo reach — reachability degrades differently for `check` and for the gate

`rfc.py`'s `REPO_ROOT` is the `metel-docs-internal` checkout (`docs/` when embedded as
metel-core's submodule); `metel-interpreter/tests/` lives one level up, in the *parent*
repo, reachable only when docs-internal is checked out as metel-core's submodule.

**An earlier draft of this section applied one rule to both commands, and that rule was
wrong for the gate.** `rfc.py check` degrading to a skip + warning when the corpus isn't
reachable is legitimate — matching the precedent `strategy.py`'s
`report_unscoped_issues` already set for its own optional network dependency, and there's
nothing to enforce without data. But applying that same degrade to
`rfc.py transition --to implemented` means the gate silently passes exactly when it can't
verify anything — and unreachable is the *common* case, not the exception: every
`rfc.py transition` in this project's actual history has run from a bare
`metel-docs-internal` checkout, `metel-interpreter/tests` never present. Worse, docs-
internal's own CI can *structurally never* reach the fixtures at all — metel-core embeds
`docs` as its submodule, not the other way around — so a gate that degrades on
unreachability could never enforce anything from docs-repo CI, ever, by construction, not
as an edge case.

**Split instead:**

- `rfc.py check` — degrades to skip + warning when unreachable, as originally proposed.
  Informational, run in contexts that legitimately don't have the fixture corpus.
- `rfc.py transition <id> --to implemented` — **refuses to run** when the fixture corpus
  isn't reachable, with a message naming what's missing, rather than silently passing.
  Reachability is established either by the metel-core submodule embedding, or an
  explicit override (an environment variable or flag naming a sibling metel-core
  checkout) for a maintainer who has one checked out elsewhere.

**Consequence worth stating outright, not left implicit: this changes the operating
workflow, not just the tool.** `--to implemented` can no longer be run from a bare
`metel-docs-internal` checkout with nothing else on disk — including from within
`metel-docs-internal`'s own CI — the way every other stage transition still can. It must
run from a context with real access to `metel-interpreter/tests`: a metel-core checkout
with the submodule embedded, or the override path above. Sequencing step 5's "CI job in
metel-core" is where the gate's actual enforcement has to live, for exactly this reason;
"`rfc.py check` added to the docs repo's own CI" is the informational command, which will
correctly run in degraded mode there every time — that's expected, not a gap.

### 7. Retroactive, via baseline + ratchet — a deliberate reversal of #723's original position

#723's own text argued against retroactivity, citing `PROCESS.md`'s precedent (the 25
pre-2026-07-10 `4-implemented` RFCs, the 14 pre-existing accepted RFCs, both explicitly
not re-litigated). That is overridden here, deliberately: the RFCs found lying about
their status this cycle (RFC-0061, RFC-0082, RFC-0116) are all already `4-implemented`,
which is exactly the population "not retroactive" would leave untouched.

Mechanism: generate `COVERAGE-BASELINE.json` recording today's per-section state across
all 47 in-scope RFCs. The gate fires on **change** — any new `--to implemented`
transition, and any RFC whose coverage *decreases* against baseline. Pre-existing gaps
become an explicit burn-down list, triaged section-by-section into "needs a fixture,"
`blocked`, `untestable`, or `elsewhere` — which is what §3's typed exemption exists to
receive, not a separate initiative.

## Baseline (2026-08-15) — measured against the real corpus before this ADR was written

Run as a throwaway, uncommitted script against 47 in-scope RFCs (`3-integrated` +
`4-implemented`) and 893 fixture files:

- **25 of 47 RFCs (53%) have zero citing fixtures at all**, under today's whole-RFC,
  prose-comment convention.
- Of the 22 that do have citations, only 12 already carry a `§N`/`section N` hint in
  prose — near-free to migrate. The other 10 are RFC-id-only and need real annotation
  work.
- **Of those 12, every single one has at least one normative section with zero direct
  citation.** Not "some RFCs have gaps" — 100% of the RFCs where section-level analysis
  is possible today already show one. RFC-0061: sections 3–7 uncited. RFC-0071 (the
  ownership model itself): direct citations on only 2 of 8 sections.
- The RFC-0116 §3 false positive (§ Context, item 3) was found during this run, not
  hypothesized in advance.

Recommended migration order, following from these numbers: the 12 RFCs with existing
section hints first, then the 10 RFC-only citations, then the 25 with nothing at all —
which is really the harder, separate question of whether a feature has *any* test
independent of RFC linking, closer to #721's scope than this one.

### Addendum (2026-08-15, later the same day) — pass-rate check, and a correction

**Full integration suite run: 785 passed, 0 failed, 0 ignored, 70.15s.** This was the one
validation-check listed under Decision §4 not yet actually checked — whether any of the
107 RFC-citing fixtures are silently disabled or currently failing, which would mean the
coverage gaps found above are additionally masked rather than simply uncovered. Neither
is true: nothing in the corpus is `#[ignore]`d, and everything passes. The gaps found are
real gaps, not gaps hidden behind broken fixtures — the design doesn't need a
fix-failing-fixtures-first step ahead of migration. (785 `#[test]` functions against 893
`.mtl` files is expected, not a second discrepancy: some fixtures share one
directory-level harness function rather than one function each.)

**Correction: the normative-section count above undercounts.** Found while writing §1's
grammar precisely for the pilot: the scratch script's section-matching regex didn't
handle letter-suffixed sections (`9a`, `9c`, `3a`, ...), which are real and used across
five RFCs (see §1). Corrected count: **134 normative sections**, not 127. The per-RFC
findings above (25 zero-coverage RFCs, the 12/10 split, RFC-0061's sections 3–7 uncited)
are unaffected — none of them depended on the buggy total — but the total itself was
wrong as first written, and is corrected here rather than silently.

## Pilot (2026-08-15) — real citations for the four highest-stakes RFCs

Before rolling the design out corpus-wide, ran it for real against RFC-0061, RFC-0082,
RFC-0071, and RFC-0116 — all four either already known to have gaps this cycle, or under
the current Copy-coherence epic (`#741`). This landed the `options.rfc` sidecar key in
`harness/fixture.rs` for real (`metel-core#742`) and cited 28 of the 29 grep-matched
fixtures across the four RFCs, by section. Full integration suite green throughout
(785 passed, 0 failed, 0 ignored), checked after every RFC's batch, not once at the end.

**The pilot found a real bug in its own tooling before it shipped.** The citation
validator's grammar check (`id.len() == 9`) was wrong — `"rfc-0061"` is 8 characters —
and rejected every citation on first run. Fixed before the commit landed. Small, but
exactly the kind of thing "run it for real" is supposed to catch that a design document
alone cannot.

**One fixture excluded, not just left uncited — a false positive found by reading, the
same way the RFC-0116 §3 one was.** `stage16_03_copy_implies_not_drop.mtl` mentions
"RFC-0071" but, read closely, tests RFC-0072 §2.3's `Copy ⟹ !Drop` implication; its own
comment cites RFC-0071 §4 only as historical context for why an older version of the
test no longer works. Citing it for RFC-0071 would have repeated the exact shape of
mistake §3's typed-exemption mechanism exists to catch, at smaller scale and with nobody
watching for it a second time.

**Two citations landed that are accurate but incomplete, and now need the exemption
mechanism §3 (above) specifies once RFC frontmatter carries it — recorded here so they
aren't lost between this pilot and that landing:**

- **RFC-0082 §3's only real citation covers checking position only.**
  `74_projection_call_site_resolution.mtl` uses `let v: i64 = peek(b)`, which works. Its
  own header comment claims resolution happens "at each call site" — that overclaims
  relative to `#740`: inference position (`let v = peek(b)`) is confirmed broken. The
  citation is correct as far as it goes; without a companion `blocked` entry pointing at
  `#740`, §3 would read as fully covered when half of it isn't.
- **RFC-0116 §3's citation covers only the non-local-aspect-rejection half of what §3
  grants.** `stage5_neg_19_record_does_not_satisfy_aspect_bound.mtl` correctly proves
  records satisfy no impl-based aspect today — but §3 also grants local aspect impls in
  principle, and that half is still broken (`#581`/`#239`), with no passing fixture,
  because it doesn't work. Same shape as RFC-0082 §3 above: citation accurate, coverage
  incomplete, exemption needed to say so rather than let the citation imply otherwise.

**RFC-0071's citation count is not a coverage claim, stated plainly rather than
implied.** 7 of 8 grep-matched fixtures cited (after excluding the false positive above)
covers only the subset of fixtures that happen to say "RFC-0071" by name in a comment.
Sections 1 (values move by default), 3 (`Drop`), 5 (drop order), 6 (explicit drop), and 8
(allocator interaction) almost certainly have real, uncredited coverage elsewhere in the
much larger `move_check/`/`structs/` fixture corpus that this pilot did not go looking
for — that search is real remaining work, not a gap this pilot closes.

Draft PR: `metel-core#742`.

## The checker is built and run (2026-08-15) — real `rfc.py check` output, and a third correction to the section count

Sequencing step 2, landed for real in `rfc.py` (not a scratch script this time): section
parsing, both citation surfaces, both frontmatter/inline drift checks, `blocked`-ref
staleness, a per-RFC coverage summary in `check`, and the `--to implemented` gate in
`cmd_transition`. All three behaviors verified by actually running them, not by reading
the code: `check` reports real problems and a real coverage summary; `transition rfc-0061
--to implemented` correctly refuses, naming the exact uncovered sections
(`1.1, 4.1, 5, 6, 7, 7.1, 7.2, 7.4`); the same command with `METEL_CORE_ROOT` pointed at a
nonexistent path refuses for a different, correct reason (unreachable, not "0 uncovered
sections"); `check` under the same unreachable condition degrades to the informational
skip §6 specifies rather than refusing.

**Building it for real caught a second bug in the section-count figure this document has
now stated three times.** First run: 7 problems, every one of them "cites `§N.M`/`§Na`,
but that section doesn't exist" — against sections this document's own Pilot section had
just finished citing by hand, read directly from the RFC text. The citations were right;
the checker's own section-header regex was wrong. It required a trailing period after
every section number (`\.\s+`), which is only true of top-level headers (`## 7. Function
Types`) — a subsection header (`### 7.1 \`Callable\``) has no second period, straight from
number to title. Every subsection in the corpus had been silently failing to match, not
just the letter-suffixed ones the earlier correction caught. Fixed (period now optional,
not required) and rerun clean.

**The real, corrected total: 200 normative sections across the 47 in-scope RFCs, not
134 and not 127.** Both earlier figures undercounted; this one is measured by the actual
checker rather than a scratch script, against the same section-existence logic the `check`
command and the `--to implemented` gate both now run on every invocation — there is no
longer a separate "baseline script" whose regex can drift from what's actually enforced,
which is what let the first two corrections happen unnoticed until someone read the RFC
text by hand. Per-RFC coverage, for reference: only the four pilot RFCs have any section
citations yet (RFC-0061 5/13, RFC-0082 6/11, RFC-0071 3/12, RFC-0116 4/6); the other 43
in-scope RFCs show 0 of N, exactly as expected — Sequencing step 3 (the remaining ~79 of
107 existing prose citations, plus the 25 RFCs with none at all) hasn't run yet.

### 8. Sectionless RFCs: a coverage checklist appended, not the body rewritten

**22 of the 47 in-scope RFCs (47%) have zero `## N.`/`### N.M` headers at all** —
`rfc_normative_sections()` returns nothing for them, so they appear on neither the
covered nor the uncovered side of the coverage summary. Not a handful of edge cases;
nearly half the corpus. Found while reviewing the Codex delegation above, not designed
for in advance.

**Two options considered and rejected before this one:**

- **Rewrite the RFC body into numbered sections.** Rejected: it breaks the one
  convention this project has held to without exception through every correction made
  under this ADR — corrections are additive and dated (RFC-0061 carries five separate
  status blockquotes; RFC-0134's Summary got a withdrawal note, not a silent edit), never
  a rewrite of the original text. `4-implemented`'s whole meaning is "spec and
  interpreter agree" against a specific, frozen text; restructuring that text later
  leaves "agree against what" ambiguous, and rewriting risks subtly misstating what a
  given RFC actually decided, checked against nothing since there's no diff-of-meaning
  reviewer.
- **Treat a sectionless RFC as one implicit section (`§0`), satisfied by any single
  citation.** Proposed as a checker-side fix requiring no document edits at all — then
  rejected on direct challenge: it reintroduces, for these 22, exactly the
  coarse-granularity failure this whole design exists to close. Whole-RFC coverage is
  what let RFC-0061/RFC-0082/RFC-0116 look fully covered while badly undertested before
  section-level citation existed; collapsing 22 RFCs back to one citable unit each is the
  identical mistake, not a smaller version of it.

**Decision: append a dated "Coverage Checklist" section to the end of each sectionless
RFC, breaking its normative claims into separately-citable numbered items, and leave
every word of the original document exactly as written.**

```markdown
## Coverage Checklist (added 2026-08-18, not part of the original RFC)

Retroactive breakdown of this RFC's distinct normative claims, for ADR-0049 citation
purposes only. The prose above is unchanged and remains the historical record.

1. Match arms may be blocks, not just single expressions.
2. A block arm's tail value is the arm's result, matching a non-block arm.
```

This needs no checker changes at all — `rfc_normative_sections()` already matches any
`## N.` header regardless of where in the file it sits, so a checklist appended at the
end is picked up by the exact same regex that reads a real RFC's own numbered sections.
It gets what the `§0` option couldn't: as many separately-citable claims as the RFC
actually makes, so "covered" keeps meaning what it means everywhere else in this design.
And it gets what a rewrite couldn't: the original text is untouched, dated, and
independently reviewable against the checklist rather than replaced by it.

**Writing an accurate checklist is exactly as much real judgment as writing real section
headers would have been** — reading the RFC, reading what's actually implemented, not
listing claims that aren't really there. This section buys a lower-risk *shape* for that
work, not a cheaper one. Given the accuracy bar already established (two false positives
already caught and corrected in citation work under this same ADR), this should run the
same way prior steps did: pilot 2-3 RFCs first, confirm the checker treats them
correctly and a spot-check holds up, before deciding whether the remaining ~19 go to a
human, to Codex under the same reviewed-not-trusted discipline as Sequencing step 3, or
some split of both.

### Pilot (2026-08-18) — three RFCs, and a format bug caught immediately by running it

Piloted on RFC-0006 (Closure Capture Semantics), RFC-0018 (Match Arm Blocks), RFC-0126
(`T[]` as a Copy Borrowed View) — 4 claims each, chosen for a spread of size and prior
familiarity, matching how every prior step under this ADR has been piloted before
scaling.

**First draft used the wrong markdown construct, and this section's own claim two
paragraphs up ("needs no checker changes at all") was checked against that draft and
found not to hold.** The initial checklists wrote each claim as an ordinary numbered
*list* item (`1. text`). `rfc_normative_sections()` matches header *lines*
(`## N.`/`### N.M`), not list items — a plain numbered list is invisible to it. Running
`rfc.py check` immediately after writing the first draft showed all three RFCs still
absent from the coverage summary, exactly as before the checklists existed, which is
what caught it. Fixed by giving each claim its own `### N. <short title>` header, prose
underneath — same information, header-shaped instead of list-shaped. Confirmed correct
by rerunning: all three RFCs appeared with 4/4 normative sections (0 initially cited, as
expected — the checklist itself doesn't cite anything).

**One real citation added to close the loop end to end, not left as untested design.**
`typechecking/functions/stage7_02_match_arm_blocks.mtl` — already read in full, already
known to exercise all four RFC-0018 claims (a block arm with a computed tail, a
no-tail/unit block arm, a bare-expression arm mixed with a block arm in the same
`match`, and pattern bindings used inside each block) — cited against all four new
sections. Full integration suite green (785/0/0) and `rfc.py check` shows
`rfc-0018: 4/4 normative sections covered`, the first sectionless RFC in the corpus to
reach real, checker-confirmed full coverage under this mechanism.

RFC-0006 and RFC-0126 have checklists but no citations yet — deliberately left for the
next pass rather than rushed to make the pilot look more finished than it is.

### 9. `"*"`: a whole-RFC exemption, for a sectionless RFC with nothing to check

**Found while scaling §8 to the rest of the sectionless corpus.** Two of the 19 —
RFC-0058 (`SourceProvider` trait for the module loader) and RFC-0059 (an internal
`SymbolId -> Span` index) — are pure internal-compiler-architecture RFCs with no
Metel-language surface at all. §8's checklist mechanism assumes the RFC has *some*
number of distinct, fixture-testable claims to break out as sections; these two have
none — every sentence in them is about Rust types and internal data structures, not
observable language behavior. Writing a `### 1. <title>` checklist section for one for
the sole purpose of giving a per-section `untestable` exemption something to attach to
produces a section that exists only to be exempted, not because the RFC actually has a
first claim — the exact manufactured-content smell §8's own rejected "treat as one
implicit §0" option was turned down for, just reached by a different path.

First attempt did exactly that anyway (checker-conforming, but backwards: shaping the
RFC to fit the checker's assumptions instead of teaching the checker the RFC's actual
shape) — caught on review and reverted in favor of fixing `rfc.py` itself.

**Decision: `coverage: { "*": { kind, reason, ref? } }` in frontmatter is a distinct,
whole-RFC form of §3's typed exemption**, valid only when the RFC has zero real
`## N.`/`### N.M` sections (checked; flagged as a problem if combined with real
sections, or with other section-keyed entries in the same block — either means `"*"`
is being reached for on an RFC §8's mechanism actually fits). It reports in the
coverage summary as `<rfc-id>: whole-RFC exemption (<kind>) -- no normative sections`
rather than being silently absent the way an un-exempted sectionless RFC is (§8's
original motivating problem) or requiring a checklist section that doesn't correspond
to a real distinct claim.

`rfc.py`'s `coverage_check_problems()` special-cases `"*"` in its per-RFC summary loop,
short-circuiting before the "no sections, skip" branch that made the first attempt's
`"1"`-keyed workaround necessary in the first place. `COVERAGE_FM_ENTRY_RE`'s existing
`[^"]+` section-key pattern already accepted `"*"` as a bare string with no grammar
change needed — only the summary logic was blind to it.

**§8 vs. `"*"`, which to use:** §8's checklist is for a sectionless RFC that *does* have
distinct, separately-citable claims — the original text just doesn't happen to use
numbered headers. `"*"` is for the rarer case where there is nothing to break out at
all: the whole document is compiler-internal implementation detail, and inventing a
"§1: whole-RFC scope is compiler-internal" section would itself be the kind of
retroactive claim-that-isn't-really-there §8 already warns writing an accurate
checklist requires avoiding.

## Consequences

- Section granularity is the load-bearing property of this design — a whole-RFC gate
  would have shipped and caught none of the three defects that motivated it. That is
  measured above, not assumed.
- It catches **zero** coverage, not **weak** coverage. Nothing mechanical can tell
  whether a fixture meaningfully exercises a section versus name-dropping it; section
  granularity narrows the gap and makes gaming visible in review, but review remains the
  actual mitigation. The failure mode of a coverage mandate is confident false
  assurance — which is what `4-implemented` already produces without one.
- Real friction added to every future transition to `4-implemented`, and to the
  retroactive burn-down. That is the intent, not a side effect, but it will be felt most
  at the `untestable` exemption, which is why that category gets its own visible list
  rather than disappearing into "exempt."
- `rfc.py check` gains two new staleness classes to track (`blocked` refs that have
  closed; `elsewhere` refs whose path has moved), on top of the "Not yet implemented"
  callout check it already runs — same shape, larger surface.
- The docs repo's own CI never runs `rfc.py check` at all today (only `check-examples`
  and `check-mdx`). Per §6's split, this doesn't put the gate itself at risk — the gate
  can only ever run where the fixtures are reachable, which structurally excludes
  docs-repo CI regardless of what runs there. It does mean citation typos/staleness go
  uncaught between metel-core CI runs unless docs-repo CI also runs `rfc.py check`
  (informational, degrades to warning there) — worth adding, lower stakes than it read
  before §6 was corrected.
- 107 of 897 fixtures already cite an RFC in a first-line comment today — a scripted,
  human-reviewed migration can pre-populate roughly 12% of the sidecar work for free.

## Sequencing

1. `rfc =` sidecar key + `harness/fixture.rs` parsing (small, metel-core)
2. **Checker, including the prose/sidecar drift check (§4)** + baseline generation
   (already run once as a throwaway; needs a committed, non-scratch version). The drift
   check ships with the checker itself, not after it — it has nothing to check until
   step 3 creates citations for it to compare, but the code for it lands here, in the
   same PR as the rest of the checker, not a follow-up.
3. Migrate the 107 existing comment citations, scripted + human-reviewed — this is the
   step that makes the drift check's first real comparison possible, and it should run
   clean against every citation this step produces before step 3 is considered done.
4. `rfc.py transition --to implemented` gate
5. CI job in metel-core; `rfc.py check` added to the docs repo's own CI
6. Burn-down against baseline, using the typed exemption to record what can't close yet

### Steps 5 and 6 landed (2026-08-19)

Steps 1-4 landed earlier in this cycle (Backlog 2, RFC-0007 through RFC-0106's 19
sectionless RFCs). Steps 5 and 6 had not — metel-core's `rfc-check` CI job already ran
`rfc.py check`, but only for the structural checks §4 lists; the coverage summary itself
was purely informational (§5's `problems` list never included an uncovered section on its
own), so nothing about coverage was actually gated, and it was informational only, no
ratchet against a committed baseline. **Two real gaps found closing this out, not just the
missing wiring:**

- **`rfc.py check` has always exited 0 regardless of what it printed.** `main()` called
  `args.func(args)` and discarded the return value; `cmd_check` returned its `problems`
  list but nothing ever inspected it. Every CI run of the `rfc-check` job, since it was
  added, has printed failures (when there were any) and still reported success to
  GitHub — the job existed but could never fail a PR. Fixed: `main()` now exits 1 when
  the top-level `check` invocation returns a non-empty `problems` list — scoped to that
  one call site specifically, not `cmd_check`'s return value in general, since
  `transition` also calls `cmd_check(args)` internally just to print post-transition
  state, and that inner call must not turn a successful transition into a failing
  process exit over some unrelated pre-existing problem elsewhere in the corpus.
- **metel-docs-internal's own CI never ran `rfc.py check` at all** — only metel-core's
  did. Added as a new job there (`rfc-check.yml`), which correctly degrades to the §6
  informational skip (verified directly: a genuinely bare checkout with no
  `metel-interpreter` sibling reports "no problems found" plus the skip note, exit 0) —
  real coverage enforcement still only happens where the fixture corpus actually lives,
  in metel-core's CI, exactly as §6 specifies.

**The ratchet (step 6)**, implemented as designed in §7: `public/rfcs/COVERAGE-BASELINE.json`
(`rfc.py index --write-coverage-baseline` writes it) records, per RFC, the section ids
already uncovered as of today — 5 RFCs, all already individually tracked: RFC-0022 §2
(metel-core#750), RFC-0032 §4-8 (metel-core#753/#754), RFC-0034 §5 (metel-core#755),
RFC-0053 §4 (metel-core#757; RFC-0053's other gap, metel-core#758, isn't a checklist item
so isn't part of this baseline), and RFC-0040 §7 (pre-existing, predates this cycle's
work, not yet triaged to a tracking issue). `check` now fails if any RFC's uncovered set
gains a section beyond what the baseline already grandfathers in — verified directly, both
that a real regression is caught (temporarily dropping a citation from an already-covered
section) and that the clean baseline state passes.
