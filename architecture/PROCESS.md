---
id: architecture-process
title: "Architecture Atlas Process"
type: process
last_updated: '2026-09-22'
---

# Architecture Atlas Process

This document did not exist before 2026-09-22. The Atlas — `arch-*` requirement
evidence, `LIMIT-*`/`GAP-*` limitation records, and the tooling that generates and
checks them — grew across [ADR-0055](https://github.com/metel-lang/metel-docs/blob/main/architecture/decisions/adr-0055-architecture-integrity-records.md),
[ADR-0056](https://github.com/metel-lang/metel-docs/blob/main/architecture/decisions/adr-0056-architecture-atlas-reader.md),
[ADR-0057](https://github.com/metel-lang/metel-docs/blob/main/architecture/decisions/adr-0057-language-gap-records.md), and a run of metel-core issues
(#1162, #1180, #1191, #1219, #1234, #1236, #1247) each adding one more layer of
generation, one more invariant, one more delimited region. Every individual piece is
documented somewhere — an ADR section, a tool docstring, a PR description — but nobody
had written down the *whole* pipeline in one place, and the pieces had started to
interlock in ways that are only obvious if you were there when each one landed: which
generator owns which region of which file, which check runs in which repo's CI and why,
which merge strategy is load-bearing for a link that already exists. This is that
document. It is a map of what already exists and why, not a new decision — where it
states a rule, that rule is enforced by code cited alongside it, and where it flags
something as incomplete, that incompleteness is real, not a hedge.

**Why the Atlas exists at all**, stated plainly because it motivates several rules
below: this project's current phase prioritizes features distinctive to Metel over
polishing or adding QOL features to what already exists. That means real limitations —
performance boundaries, unsupported cases, deliberate shortcuts, gaps between the spec
and the implementation — accumulate faster than they get closed. The Atlas is the
mechanism that keeps that accumulation *honest and traceable* rather than silent: a
limitation gets a record with an owner and a disposition instead of living only in a
maintainer's memory or a stale code comment, and the tooling below exists to keep those
records from drifting away from the code they describe.

## The three record kinds

| Kind | Where | Shape | Governing ADR |
|---|---|---|---|
| `arch-*` | inline anchor inside `architecture/spec/*.md` | one Architecture Spec section, many stable `{#anchor}` claims — same storage pattern as the Language Spec's Formal Rules | ADR-0055 §2 |
| `LIMIT-*` | own file, `architecture/limitations/limit-<area>-<nnn>.md` | standalone lifecycle: discovery, disposition, ownership, review, resolution | ADR-0055 §4 |
| `GAP-*` | own file, `architecture/gaps/gap-<area>-<nnn>.md` | same shape as `LIMIT-*`, but describes the Language Spec's own boundary, not the implementation's | ADR-0057 (**still `status: proposed`** — see "Known incompleteness" below) |

The sorting test between the two record kinds (ADR-0057 §2): *would a fully correct
implementation of the current Language Spec still have this behaviour?* Yes → the spec
itself doesn't promise otherwise, so it's a `GAP-*`. No → the spec promises something the
code doesn't yet deliver, so it's a `LIMIT-*`. Both → file both, cross-linked under
`affects`. Neither (the spec is clear and the code is simply wrong) → that's a bug, filed
as an issue, not a record of either kind.

## Record schema (`LIMIT-*` / `GAP-*`)

Frontmatter: `id`, `title`, `summary`, `scope`, `owner`, `discovered_by`, `disposition`,
`review` (required once `disposition: accepted`), plus the optional scheduling pair
`planned_for: vX.Y.Z` / `rfc: RFC-NNNN[, ...]` a Language Spec chapter's one-line marker
renders from. Body: `## Limitation`/`## Gap`, `## Impact`, `## Affects`, `## Resolution`.

**Disposition vocabulary** (`known`, `accepted`, `mitigated`, `planned`, `resolved`,
`superseded`) and the rules `check_architecture.py` enforces on it:

- `accepted` requires a `review` date.
- `resolved` requires real exit evidence in `## Resolution`, not a placeholder — for a
  `GAP-*` specifically, that means an `affects` RFC at stage `3-integrated` or
  `4-implemented`; a closed issue alone is never enough for either kind.
- `planned` requires an RFC in `affects` or an issue reference in `## Resolution`
  (`GAP-*`); `LIMIT-*`'s own `planned` check is looser (schema only, no forced RFC
  linkage) — this asymmetry is real, not an oversight described elsewhere in this
  document, and is worth knowing before assuming the two kinds are checked identically.
- `known`/`accepted`/`mitigated`/`planned` count as **active** for every "does a marker
  still make sense" check below (constant: `GAP_ACTIVE_DISPOSITIONS` /
  `LIMIT_ACTIVE_DISPOSITIONS`, same four values, separately named per tool); `resolved`
  and `superseded` do not.

Code and fixtures cite `arch-*` records or Formal Rules — never a `LIMIT-*`/`GAP-*` id
directly — with exactly one narrow, deliberate exception: the `// limit:` marker (Level
3, below), which is a coordinate, never a claim of success, and is therefore not the
"code asserting it satisfies this" case ADR-0055 §4 forbids.

## The evidence pipeline: four independent, coexisting layers

This is the part that had become genuinely entangled — four separate mechanisms, added
in four separate efforts, all writing generated content into the same family of
markdown files. They are independent (none requires another to be present) and they are
carefully scoped to never write into the same span of a file, but nothing said that
plainly until now.

### Layer 0 — `arch-implements` / `arch-verifies`

The foundation (ADR-0055 §2, §6). A `// arch-implements: ["arch.<path>.requirement-N"]`
or `// arch-verifies: [...]` comment, placed **directly above** the Rust item (or, in a
`.pest` file, the grammar rule) it cites — only comments and attributes may sit between
the marker and its item; anything else is a hard `ValueError`, not a silent skip onto
the wrong item. `generate_architecture_evidence.py` resolves every citation into the
Architecture Spec's `implements` / `verified by` requirement-table cells as commit-pinned
GitHub links. A side missing evidence instead carries an `implements exemption` /
`verification exemption` row (`kind: untestable | elsewhere | blocked`, ADR-0055-adjacent,
metel-core#1193).

`last_reviewed` (metel-core#1191) rides beside this: a hand-typed commit SHA the tooling
only ever *audits*, never writes — it flags when the cited code was touched by a commit
after that SHA, over exactly the item's own line range, not the whole file. The tool
never refreshes it for you; that's deliberate; see its own docstring for the full
reasoning about not automating the human-attention step.

**Item scope, and a real asymmetry to know about:** Layer 0's marker resolver (`following_item`
/ the `ITEM` regex) is `fn`-only — its own original, narrower scope. Layer 3 below needed
a broader one (`following_named_item` / `NAMED_ITEM`: `fn`/`static`/`const`/`struct`/
`enum`/`trait`) and got it, but Layer 0 was never widened to match. An `arch-implements`
marker placed directly above a `static` today hard-fails ("citation must directly precede
its item; found `static ...` in between") rather than silently latching onto the wrong
`fn` — safe, but still a real gap: nothing currently lets an architecture requirement cite
a `static`/`const`/`struct`/`enum`/`trait` the way a limitation marker now can. Worth
unifying the two regexes if this is ever hit for real.

### Layer 1 — skipped-fixture `LIMIT-*` citations (metel-core#1219)

`check_architecture.py --core <metel-core checkout>` cross-checks an integration
fixture's `skip` reason: it must cite the `LIMIT-*` record it reproduces, or be marked
plainly exempt (a fixture that's ahead of an accepted-but-unbuilt RFC, with no current
spec divergence to track). The reverse direction is checked too, warn-only: an active
limitation with no citing skipped fixture and no named `metel-core#` reproduction is
"unevidenced." Without `--core` (a bare metel-docs checkout structurally cannot reach
`metel-interpreter/tests`, which lives one level up inside metel-core), this whole layer
degrades to an informational skip — never a failure.

### Layer 2 — hand-typed `path::symbol` resolution (metel-core#1236 level 2)

A record's `## Affects` may hand-type a bullet of the shape `` `path/to/file.rs::symbol` ``
(with or without a markdown link already around it). `generate_architecture_evidence.py`
finds that named item in the cited metel-core file (`find_named_item` /
`resolve_named_citation`, reusing the same `function_extent`/`following_rule` machinery
Layer 0 uses) and rewrites the bullet in place into a commit-pinned link — same
`function_extent`-derived line, refreshed every run. A bare path with no `::symbol`
is left completely untouched; that's the escape hatch for a citation too broad or too
informal to resolve to one item. This layer needed no ADR: it only resolves text a human
already wrote by hand in `## Affects`, and ADR-0055 §4's prohibition is about *code*
citing a limitation record, which this layer's mechanism never does.

### Layer 3 — `// limit:` code markers (metel-core#1236 level 3 / #1247)

The newest layer, and the only one that required amending ADR-0055 (§4's blockquote
amendment, 2026-09-22, chartered by metel-core#1247) — because it is the first mechanism
that lets *code* carry a `LIMIT-*` id at all. A `// limit: ["LIMIT-X-001", ...]` comment,
placed with the exact same "directly precedes its item, only comments/attributes between"
rule as Layer 0, but against the *broader* `NAMED_ITEM` scope (`fn`/`static`/`const`/
`struct`/`enum`/`trait` — this is in fact where that broader scope was first built; Layer 0
simply hasn't caught up to it, see above).

The marker is **a coordinate, not a contract** — it never claims the limitation is
handled, only that this is where it currently lives. That's why it doesn't reopen
ADR-0055 §4's original guarantee: that guarantee was about code asserting *success*, and
a `// limit:` marker asserts the opposite, in a visibly distinct vocabulary from
`arch-implements`.

`generate_architecture_evidence.py` resolves every live marker into a **delimited, fully
machine-owned subsection** of the record's `## Affects`:

```markdown
<!-- limit.py:markers:start -->
- [`metel-frontend/src/pipeline/type_checking/overload.rs::NEXT_OVERLOAD_SYM`](https://github.com/.../overload.rs#L34)
<!-- limit.py:markers:end -->
```

regenerated from scratch every run, the same way Layer 0's `implements`/`verified by`
cells already are. This is the general **delimited-generated-region convention** this
codebase's docs tooling now uses in three places — `rfc.py:fixtures:start/end`,
`rfc.py:origins:start/end`, `limit.py:markers:start/end` — the rule each one follows
being: an HTML comment pair; the tool owns everything between the two comments
unconditionally; nothing hand-written can appear there and survive a regeneration; the
tool never touches anything *outside* the pair. Any future generator writing into a
shared file should reuse this pattern rather than invent a new one.

Layer 3 coexists with Layer 2 **completely independently** — a record's `## Affects` may
freely mix hand-written bullets, Layer-2-resolved links, and the Layer-3 block, and
neither layer requires the other to be present. This was not free: Layer 2's bullet
scanner (`AFFECTS_BULLET.finditer`) has no inherent way to know not to also match
bullets living *inside* Layer 3's delimited block (identically shaped: a backtick-quoted
`path::symbol` wrapped in a markdown link) — a real cross-contamination bug, found and
fixed in the same PR that built Layer 3,
by computing the delimited block's span first and excluding any Layer-2 match that falls
inside it (`Level2Level3BoundaryTests` pins the fix).

`GAP-*` is **deliberately out of scope for Layer 3** — a gap is a Language Spec concept
(ADR-0057), and metel-core's Rust source has nothing to mark for a gap in what the spec
*itself* says. Only `LIMIT-*` records get the marker mechanism.

**Drift detection**, the other half of Layer 3: `limit_ids_ever_marked()` walks
`git log -p -G 'limit:' -- '*.rs' '*.pest'` (current branch history) and flags any
`LIMIT-*` id that was once cited by a marker and is no longer cited by *any* current one.
This is a finding, never a silent drop — whether that means the limitation is resolved or
the marker merely moved elsewhere is a human judgment the tooling deliberately does not
make. A record still cited by a live marker but whose disposition has fallen out of the
active set is flagged the other way too (marker and disposition disagreeing about whether
the limitation is still live).

**What Layer 3 cannot anchor to, today:** only the six `NAMED_ITEM` kinds above — never
an enum-variant field, a struct field, or a match arm buried inside a large,
many-unrelated-concerns dispatch function. Hit for real in metel-core#1248: `Call::callee_id`
(an enum-variant field) and two limitations sitting inside `infer_expr`/`infer_stmt`
(functions handling many unrelated statement/expression kinds, where marking the whole
function would misstate how narrow the actual cause is) were left unmarked for exactly
this reason — 10 of 27 tracked limitations in that pass, full reasoning per-record in
that PR's description.

## The Language Spec's own atlas — a sibling system

Everything above governs the **Architecture** Spec (`architecture/spec/*.md`, `arch-*`,
`LIMIT-*`). The **Language** Spec (`reference/spec/*.md`, Formal Rules, RFCs) has its own
older, larger, independently-governed sibling system, built around `rfcs/tools/rfc.py`
and documented in full in `rfcs/PROCESS.md` (the RFC lifecycle: `0-draft` through
`4-implemented`, `5-superseded`/`6-refused`). This document does not re-derive that —
`rfcs/PROCESS.md` is 700 lines and is the actual authority on it. What belongs *here* is
naming the sibling clearly enough that its shape stops being mysterious from this side,
correcting a real undercount the section above made, and documenting the one place the
two systems actually touch.

**Formal Rules ("rigor blocks") are the Language Spec's `arch-*` counterpart:** a stable
`{#id}` anchor (`spec.<path>.legality-N` / `.dynamics-N`) inline in Language Spec prose,
coverage-linked to the RFC(s) that specify it and the fixture(s) that test it — the same
inline-anchored, path-addressed shape ADR-0055 §2 explicitly borrowed for `arch-*`. `rfc.py`
regenerates two delimited spans per rigor block, not one:

```
<!-- rfc.py:origins:start -->   -- which RFC(s) specify this rule ("Referenced by: ...")
<!-- rfc.py:origins:end -->
<!-- rfc.py:fixtures:start -->  -- which fixture(s) test it ("Tested by: ..."), or an
<!-- rfc.py:fixtures:end -->       exemption instead (untestable / elsewhere / blocked --
                                    the same three-kind vocabulary Layer 0's implements/
                                    verification exemptions use)
```

**Correction to the count above:** "The delimited-generated-region convention... used in
three places" undercounted it. `rfc.py` alone owns three marker *kinds* — `origins`,
`fixtures`, and `exemption:rendered` (the exemption's own rendered reason text, a fourth
delimited region sharing the fixtures slot's role when there's no fixture to point at) —
each appearing in every rigor block, across both `reference/spec/*.md` **and**
`reference/error-codes.md` since metel-core#981 gave error codes the identical rigor-block
treatment (their own `{#id}`, origins, fixtures/exemption). `limit.py`'s single `markers`
kind (Layer 3, above) is the newest, not the only other, member of this family. Anyone
extending any of these should read `rfc.py`'s own marker-rewriting functions first — the
"only comments between the marker and what it owns, never touch outside the pair" rule is
identical everywhere, but the exact regeneration mechanics differ in ways worth copying
correctly rather than re-deriving.

**The fixture viewer rides inside the `fixtures` slot, not beside it:** each `Tested by`
entry can carry a `<details class="spec-fixture" data-fixture="<base64 JSON>">` payload —
the fixture's source, its expected outcome, and its GitHub link, base64-encoded inline so
the website can render a collapsible, self-contained fixture viewer with no extra fetch
(metel-core#944/#974, website substrate: overloading the `Details` swizzle on
`data-fixture`). It is generated by the exact same `rfc.py` pass that writes the
`fixtures` marker pair, not a separate tool.

**Two more code-owned, `--check`-gated generators live in metel-core, not metel-docs** —
the same split shape as this document's own Layer 0-3 (code owns markers/source of truth;
the docs generator or a metel-core binary renders into metel-docs; CI on both sides
gates drift):

- `metel-frontend/src/bin/gen_grammar.rs` (metel-core#720) generates
  `reference/spec/grammar.md`'s formal-grammar block directly from `grammar.pest` via
  `pest_meta`, using a sidecar (`grammar-doc.toml`) to say which rules get their own
  documented section (`named`), which are pure syntax sugar to inline recursively
  wherever referenced (`inline`), and which are pest-internal plumbing no documented rule
  should reference at all (`omit` — a documented rule that somehow does is treated as a
  sidecar mistake, not silently rendered). `--check` is the CI drift gate (metel-core CI's
  "grammar.md up to date" job).
- `metel-frontend/src/bin/check_stdlib_docs.rs` (metel-core#718) checks — deliberately
  does not generate — `reference/spec/runtime.md`'s builtin/method tables against
  `stdlib/*.mtl`'s real declarations, bidirectionally (a documented row with no matching
  declaration, and a real public declaration missing its row, both fail) plus a
  signature-shape check (a row whose *documented calling form* — free function vs.
  method — doesn't match the real declaration, the exact bug class metel-core#714 was).
  Deliberately narrow scope, not "every public declaration": `stdlib/*.mtl` has no
  structured place prose descriptions could come from, so full table generation was
  rejected as inventing content from nothing (metel-core CI's "runtime.md matches stdlib
  declarations" job).

**Governing ADRs**, for anyone who needs the actual decision record rather than this
summary: ADR-0049 (`status: implemented`) links fixtures to RFC sections and gates
`4-implemented` on coverage; ADR-0050 (`status: proposed` — **still not accepted**,
exactly the same caveat as ADR-0057 above, flagged here rather than assumed settled)
anchors that coverage to the rigor blocks' own stable IDs instead of RFC sections, which
is the shape `rfc.py` actually implements today; ADR-0051 (`status: proposed`) retired the
old `metel-docs-internal` → `metel-docs` sync in favor of the direct-submodule layout this
whole document already assumes.

### Where the two atlases actually touch

One real, load-bearing intersection, not a loose analogy: a Language Spec chapter may
carry a one-line pointer to an **Architecture** Atlas record —
`> **Gap** GAP-X-001` or `> **Limitation** LIMIT-X-001` (metel-core#1235,
`check_architecture.py`'s `SPEC_LIMIT_MARKER_RE`, deliberately label-generic — it accepts
either label in either spec tree). The website renders the record's summary and its
`planned_for`/`rfc` chips into that line at build time; the chapter text never copies them
by hand, so they cannot go stale independently of the record. Real example
(`reference/spec/functions.md:930`):

```
> **Limitation** LIMIT-EVALUATION-005: closure environments are not destroyed
> until destructors run.
```

**The section-level rollup is asymmetric, and that asymmetry is real, not an
inconsistency to fix:** `## Known gaps` + `<!-- records:gaps -->` (listing every `GAP-*`
in scope) appears only in Language Spec chapters (`reference/spec/*.md`); `## Known
limitations` + `<!-- records:limitations -->` appears only in Architecture Spec pages
(`architecture/spec/*.md`) — each tree's own rollup, of its own record kind, per ADR-0057
§3. The one-line inline pointer above is the *only* mechanism that crosses trees: a
`LIMIT-*` (architecture-owned) can be inline-cited from a Language Spec chapter when it's
concrete and user-visible enough to mention in spec prose (the destructors example above
is exactly this — a real implementation limitation, filed under `architecture/limitations`,
mentioned inline in `reference/spec/functions.md` because a Metel programmer reading about
closures needs to know it). The reverse (a `GAP-*` inline-cited from an Architecture Spec
page) is equally legal by the same generic regex, just not yet exercised in the current
corpus.

## `git_ref()`: the evidence-pinning heuristic, and its known blind spot

Every generated link needs a commit SHA to point at. Using the checkout's raw `HEAD`
would mean **every** unrelated metel-core commit rewrites **every** generated link's SHA
on the next regeneration — pure churn, no informational content. `git_ref()` instead
resolves to *the most recent commit that changed a citation marker's own occurrence
count* (a `--pickaxe-regex -S 'arch-|limit:'` search over `*.rs`/`*.pest`), so a routine
core change that touches none of the cited code leaves every existing link alone.

**This was a real, concretely wrong bug** until metel-docs#201 (2026-09-22): the pickaxe
pattern was `arch-` only, so a commit that *only* added `// limit:` markers — changing
zero `arch-` occurrences — resolved to whatever earlier commit last touched an
`arch-implements`/`arch-verifies` marker instead. Every citation's *line number* is
always read from the checkout's *current* file content, so the bug paired a correct,
freshly-computed line number with a stale ref whose file, at that older commit, did not
have that line shifted yet — a link that resolves on GitHub, just to the wrong line.
Caught by manually diffing a generated link's target against `git show <ref>:<path>`
rather than trusting `--check`'s own agreement with its own bug; two regression tests
(`GitRefTests`) now pin the fix.

**The fix narrows the gap; it does not close it.** `git_ref()` is a proxy for "did the
cited item's line number move," not a direct measurement of it — a commit that shifts a
cited item's line by inserting or removing an unrelated line above it, with *no* change
in either marker kind's occurrence count, is still outside what this heuristic catches.
This is a known, accepted limitation of the tool itself (not yet — and maybe never —
worth a `LIMIT-*` record of its own, since it's about the Atlas tooling rather than the
language implementation), and the next person extending the marker vocabulary with a
third kind should widen this same pickaxe pattern rather than rediscover the bug fresh.

## CI wiring across two repositories

The code and its markers live in metel-core; the generated evidence text lives in
metel-docs. Two repositories, two CI jobs, checking *different* things, not mirrors of
each other:

- **metel-docs' `architecture-check.yml`** checks out metel-core's `develop` branch
  (never `main` — per the branch model, `main` only syncs at releases and carries none
  of the current markers) at `fetch-depth: 0` (required: the generator resolves
  `last_reviewed` staleness and `git_ref()` from history, which a shallow checkout can't
  answer), then runs `generate_architecture_evidence.py --core metel-core --check`
  followed by `check_architecture.py --check`. This answers: *is metel-docs' evidence
  current for the real state of metel-core's integration branch, right now?*
- **metel-core's "Architecture evidence" job** runs the same generator the other
  direction — against its own current commit, using its `docs` submodule (a gitlink
  pinned to one specific metel-docs commit) for the tool and the record files. This
  answers: *is the evidence text at the docs submodule's pinned commit still accurate for
  MY code, right now?*

The `docs` gitlink is a normal tracked file entry — **nothing auto-updates it.** A
metel-core PR that shifts a marker-adjacent line will fail metel-core's own CI job until
someone bumps the gitlink to a metel-docs commit that already contains regenerated
evidence for that PR's exact content. This is why marker-adding metel-core work always
needs a metel-docs regeneration *landed first*, never squeezed into the same PR — the
regenerated markdown physically lives in the other repository.

## The standard landing sequence

Worked out in practice landing metel-core#1247/#1248 (17 real `// limit:` markers); write
it down so the next marker-adding change doesn't have to re-derive it by trial and error:

1. If new generator behavior is needed (a new marker vocabulary, a bug fix like the
   `git_ref()` one above), land that metel-docs tooling PR **first, alone.**
2. Write the metel-core markers. Verify locally before opening a PR: run the metel-docs
   generator's `--check` with `--core` pointed at the metel-core branch — this is exactly
   what metel-docs' own CI will check later, so failures surface here, not there.
3. Land the metel-core PR **with a real merge commit, never squash** (see below for why
   this specifically matters here). Confirm with
   `git merge-base --is-ancestor <branch-tip-sha> origin/develop` that the exact commit
   the next step will generate links against is actually reachable.
4. Regenerate metel-docs evidence against metel-core's now-merged tip (`git_ref()`
   resolves to it automatically, since it's the most recent marker-count-changing
   commit) and land that as its own metel-docs PR. Its CI checks against metel-core's
   `develop` directly, so this step is red until step 3 has actually landed — the two
   can never be reordered.
5. Bump metel-core's `docs` gitlink to the new metel-docs `main`. Confirm metel-core's
   own "Architecture evidence" CI job goes green — this is the first point either repo's
   CI has checked the *paired, exact* state end to end.

## Merge commit vs. squash: why it is load-bearing here

Both repositories' established convention is a real two-parent merge commit (verified
directly: `git cat-file -p` on metel-core#1246 and metel-docs#198/#199's merge SHAs each
show two parents). Squash-merging discards the original feature-branch commit and
creates a brand-new SHA on the target branch; the original commit becomes unreachable
once its branch is deleted, and GitHub eventually garbage-collects unreachable commits.

This matters *specifically* for this system, more than it would for an ordinary PR,
because generated evidence hardcodes a real commit SHA into a rendered GitHub blob URL —
squash-merging a PR that markers were generated against silently rots every link that
points at it. Caught mid-flight landing #1247/#1248: metel-docs#200/#201 were
accidentally squash-merged (low-impact there, since nothing links *to* a metel-docs
commit) before switching to `--merge` for metel-core#1248 and the metel-docs/metel-core
PRs after it, where it mattered.

## Known incompleteness — read before assuming any of this is finished

Stated plainly rather than smoothed over, because this document's whole point is to stop
rules from hiding:

- **ADR-0057 is still `status: proposed`, not accepted.** The entire `GAP-*` apparatus
  described above — schema, checker rules, the sorting test — is running ahead of its own
  governance formally closing. Anyone relying on `GAP-*` as settled should check that
  ADR's current status first.
- **Layer 0's `arch-implements`/`arch-verifies` cannot cite anything but a bare `fn`**,
  while Layer 3's `// limit:` can cite `fn`/`static`/`const`/`struct`/`enum`/`trait`. The
  two were never unified; see "Layer 0" above.
- **No marker kind can anchor to a struct/enum-variant field, or to a specific case
  inside a large multi-purpose dispatch function.** Concretely blocks precise citation
  for at least three real limitations today (metel-core#1248's description has the full
  list and reasoning per case).
- **`git_ref()` is a proxy, not a proof** — see its own section above. A line shift with
  no marker-count change of either kind is still invisible to it.
- **`check_architecture.py`'s two "conditional policy" checks** (accepted needs a review
  date; resolved needs real exit evidence) are still, deliberately, two ad hoc
  field-presence rules — ADR-0055 §6 explicitly declines to bring in a declarative rule
  engine (the prior-art survey's own recommendation) until real reconciliation-rule
  volume justifies it. Anyone about to add a third or fourth conditional rule should
  notice that this is close to the threshold ADR-0055 named, not just add another
  `if` branch without comment.
- **No reader or UI exists** (ADR-0056, deliberately deferred until real records exist to
  design a navigation model around). Everything in this document is source-of-record and
  checker output only — a maintainer's Markdown files, a script's exit code and stdout.
- **ADR-0050 is also still `status: proposed`, not accepted** — the Language Spec's own
  coverage model (rigor blocks' stable IDs as the coverage anchor, not RFC sections) that
  `rfc.py` already implements today is, like `GAP-*`, running ahead of its own governance
  formally closing. Same caveat as ADR-0057, worth repeating rather than assuming settled
  because it was mentioned once already.

## Where the authoritative detail actually lives

This document is a map, not a replacement for any of the following — when in doubt,
these are the sources of truth, in the order that usually resolves a question fastest:

- **`architecture/tools/check_architecture.py`**'s own module docstring and inline
  comments — the exact, current list of every check it runs.
- **`architecture/tools/generate_architecture_evidence.py`**'s own module docstring and
  inline comments — the exact, current mechanics of every layer above.
- [ADR-0055](https://github.com/metel-lang/metel-docs/blob/main/architecture/decisions/adr-0055-architecture-integrity-records.md) — the base charter:
  `arch-*`, `LIMIT-*`, the integrity-tooling decision, and (via its 2026-09-22 amendment)
  Layer 3's charter.
- [ADR-0056](https://github.com/metel-lang/metel-docs/blob/main/architecture/decisions/adr-0056-architecture-atlas-reader.md) — why there is no reader yet.
- [ADR-0057](https://github.com/metel-lang/metel-docs/blob/main/architecture/decisions/adr-0057-language-gap-records.md) — the `GAP-*` charter (still
  `proposed`).
- **`rfcs/PROCESS.md`** — the Language Spec's own, much larger sibling process document
  (the RFC lifecycle in full: 700 lines, this document's own stylistic model). Start there
  for anything about RFC stages, `rfc.py` subcommands, or the coverage/exemption
  mechanics only summarized in "The Language Spec's own atlas" above.
- **`rfcs/tools/rfc.py`**'s own module docstring — the exact, current subcommand list and
  what each one checks or regenerates (origins, fixtures, exemptions, `REGISTRY.md`/
  `INDEX.md` drift, milestone tracking).
- **`metel-frontend/src/bin/gen_grammar.rs`** / **`check_stdlib_docs.rs`** (metel-core) —
  their own module doc comments give the exact, current mechanics of `grammar.md`
  generation and the `runtime.md`/stdlib correspondence check, respectively.
- [ADR-0049](https://github.com/metel-lang/metel-docs/blob/main/architecture/decisions/adr-0049-rfc-section-fixture-coverage.md) — RFC-section fixture coverage (`status: implemented`).
- [ADR-0050](https://github.com/metel-lang/metel-docs/blob/main/architecture/decisions/adr-0050-spec-anchored-legality-coverage.md) — rigor-block-anchored coverage, the shape
  `rfc.py` actually implements today (still `proposed`).
