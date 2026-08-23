---
id: adr-0050
title: "Anchor Coverage to Stable IDs on Legality/Dynamic-Semantics Blocks, Not RFC Sections"
date: '2026-08-19'
status: proposed
relates: adr-0049
implements: issue #767
updated: '2026-08-23'
---

> **Path note, 2026-08-23 (ADR-0051 step 4).** This document's `public/reference/spec/`
> references (§ throughout) describe the corpus at its former location in
> `metel-docs-internal`. That content, and `rfc.py`, now live in `metel-docs` with the
> `public/` segment dropped (`reference/spec/`, `rfcs/`) — not rewritten body-wide here,
> since this ADR is still `proposed` and unimplemented; whoever builds it should read
> paths as relative to `metel-docs`, not this repo.

## Context

Developed in conversation, not from a tracked report; the tracking issue (#767) was filed
after the design settled, recording it before that context was lost rather than after.

[[adr-0049]] anchors coverage to *RFC* sections: a fixture cites `rfc-NNNN§section`, and
every normative section of a `4-implemented` RFC needs at least one kind-matched fixture.
That design already found real bugs (RFC-0061/0082/0116 looking covered while badly
undertested) and is working as intended. But it has a structural limit, visible in this
project's own history rather than hypothesized: RFC-0022's original text turned out to be
wrong on two claims (semicolon requirement, statement-position restriction), and because
RFC files are additive-only — corrections live as dated blockquotes bolted onto text
that's now known to be stale — the *fact* of what's actually true today has to be
re-established by reading a correction note, not the section itself. Multiply that by
however many RFCs eventually touch the same behavior over the language's life (a second
RFC refining what a first one established, a bug fix that changes semantics with no new
RFC at all), and coverage keeps getting tracked against documents that are each
individually frozen, none of which is allowed to just say what's true right now.

It also has a coverage gap ADR-0049 can't see by construction: content that was never the
subject of a numbered RFC — pre-RFC-era language, or a later editorial addition to the
spec — falls outside the mandate entirely, because the mandate is keyed off RFC
citations, and there is no RFC to cite.

Both problems have the same root cause: the coverage anchor is a historical process
document, not the place where current truth is supposed to live. The RFC lifecycle
already has a stage that says as much — `3-integrated` means an RFC's content has been
merged into the live spec, not just cross-referenced from it. This ADR takes that stage's
own premise seriously: once integrated, the spec section *is* the current fact, and
coverage should be checked against it, not against the RFC that originated it.

Reached while comparing what other language ecosystems do for spec rigor: ECMAScript/
test262's `esid` mechanism cites a stable HTML anchor rather than a positional section
number, specifically to survive spec reorganization without the citation going stale —
directly relevant, since ADR-0049 already hit RFC-0134's sections being renumbered twice
in one week. And the Ferrocene Language Specification's per-construct structure —
Syntax / Legality Rules / Dynamic Semantics / Examples — is a concrete answer to "prose
alone isn't precise enough to gate on," which Metel's current discursive spec is. Notably,
Ferrocene itself was built as a *separate* document from the Rust Reference for four years
(2021–2025) — but only because it started outside the Rust Project, funded for compiler
certification by an organization that didn't own the Reference. The moment it was donated
into the same governance as the Reference, the Rust Project's own stated next step was to
merge the two into one document, not keep syncing them by hand. Metel has no such
organizational split to inherit — building a permanently-parallel rigor document here
would manufacture the drift problem Rust is now spending effort to undo, with none of the
historical excuse that produced it there.

## Decision

### 1. Stable IDs live only on Legality Rules and Dynamic-Semantics blocks

Not on the spec file, not on discursive prose sections, not on Syntax or Examples blocks.
Syntax is redundant with `grammar.pest` — citing an ID there would just duplicate what the
grammar file already states unambiguously. Examples are illustrative, not a source of
claims; nothing should cite one as the thing under test. Legality Rules (static,
compile-time claims — "a private field cannot be accessed outside its module") and
Dynamic Semantics (runtime-behavior claims — "indexing a `SizedArray` with an in-bounds
literal returns the element") are the two normative categories eligible for an ID.
**Kind-matching is per-block, not per-category** — a Legality Rule claiming an absence
needs a negative fixture, but so does a Dynamic Semantics block claiming an error
condition ("indexing out of bounds panics at runtime" is dynamic semantics *and* a
negative fixture); a Dynamic Semantics block claiming a value needs a positive one. This
is the identical per-claim match ADR-0049 §2 already runs against `expect.status`,
restated here rather than replaced by a Legality-is-negative/Dynamics-is-positive
shortcut, which is not actually true. Restricting IDs to exactly these two block kinds
keeps the citable surface equal to the enforceable surface — no chapter-level or
prose-level ID that would invite the same coarse-granularity failure ADR-0049's Context
section (whole-RFC coverage) already found once.

**The dividing line itself is narrower than "static claim vs. runtime claim," checked
against the actual FLS source rather than assumed from its blog post.** Fetched
`expressions.rst` directly (`rust-lang/fls`, the file backing
`spec.ferrocene.dev/expressions.html`) for two contrasting real sections:

- **Division**'s Dynamic Semantics states the panic as a literal numbered step of its own
  evaluation procedure: *"If unsigned integer division is performed and the right operand
  is 0, then the operation results in a panic."* — the construct's own behavior.
- **Indexing**'s Dynamic Semantics has no panic clause at all. `a[i]` is specified purely
  as four steps ending in `Index::index(&indexed, indexing)` (or `IndexMut::index_mut`) —
  because `[T]`'s indexing is generic over any `Index`-implementing type, and
  bounds-check-then-panic is a property of `[T]`'s specific `Index` *implementation*,
  documented wherever that impl lives, not repeated at the generic index-expression site
  it's merely dispatched through.

**The real rule: Dynamic Semantics documents exactly what a construct's own evaluation
does, and nothing that's actually the behavior of something it delegates to.** "Can this
fail" doesn't decide the category by itself — whether the failure is *this construct's
own* or *something it calls out to* does. This matters concretely for the
`SizedArray`-indexing example above: verified directly against `construction.rs`
(`Expr::Index` handling) that Metel's indexing is a built-in AST construct, not dispatched
through a generic user-implementable trait the way Rust's `Index`/`IndexMut` are — no
`Index`/`IndexMut` trait exists anywhere in `metel-frontend`/`metel-interpreter`. So the
bounds-panic behavior *is* the index expression's own evaluation, matching Rust's division
case rather than its indexing case, and the example stands as originally written. Worth
re-checking against source rather than assuming for any future example pulled from a
language whose indexing (or whatever construct) *is* trait-genericized, since the same
question would land differently there.

### 2. Granularity is the block author's deliberate choice, not derived automatically

A trivial rule stays one block, one ID, one fixture obligation. A rule covering several
independently-wrong-able cases should be split into sibling blocks specifically so the
coverage report can say "this exact case is untested," not "this general area has at
least one fixture, the rest unknown" — which is the same imprecision ADR-0049 was built to
eliminate at the RFC-section level, recurring one level down if section-sized blocks were
the only unit available. This puts the coverage-planning judgment where the domain
knowledge already is — the person writing the rule — rather than leaving a downstream
test-writer to infer test-case boundaries from prose. No mechanical rule decides when to
split; it's the same authorial judgment a well-designed unit-test suite already requires,
just written once, in the spec, instead of re-derived per fixture.

**Not FLS's own granularity, deliberately — but the ceiling isn't closed off, and it
splits into two different questions worth keeping separate.** FLS assigns a stable ID
(`:dp:` — "declarative point") to *every individual clause*, automatically, because it's a
compiler-certification document where each normative sentence needs independent audit
traceability by regulatory requirement. That bar doesn't apply here — ADR-0050 is solving
staleness and coverage-signal quality, not producing a certification traceability matrix
— so §2 keeps splitting as a deliberate authorial choice rather than an automatic default.
Whether *finer than block* stays reachable later, if it's ever wanted, depends on which of
two things "finer" means:

- **More, smaller headed blocks** — a one-sentence Legality Rule gets its own heading and
  its own ID. Already fully supported by §3's verified anchor mechanism as written; this
  is just splitting applied more aggressively, nothing new to build or test.
- **Inline anchors inside continuous prose, FLS's actual shape** — its `:dp:` role tags a
  clause *within* a paragraph without forcing a heading per sentence, which is how FLS
  gets per-clause IDs without every section becoming a wall of one-line headings. **Now
  checked against a real build, not left open.** Two candidate syntaxes, appended
  mid-paragraph to a real spec file (`declarations.md`) rather than a fabricated one:

  - **Pandoc-style bracketed span** (`[clause text]{#id}`) — **not supported.** Renders as
    inert, literal text; `[this clause has an inline id]{#spec.declarations...}` appears
    verbatim in the rendered page, brackets and braces included, and no `id` attribute is
    created anywhere. FLS's own syntax is reStructuredText-specific and has no working
    equivalent in this Markdown/MDX toolchain.
  - **A raw HTML/JSX span** (`<span id="...">clause text</span>`) — **works cleanly.**
    MDX compiles straight through to JSX, so an explicit `<span>` needs no special
    support: the `id` attribute round-trips exactly (dot-heavy IDs included, no
    corruption), the span's text renders normally with no leaked markup, and a `#id`
    fragment link to it resolves to the right element.

  So inline, sub-paragraph anchoring *is* possible here — just via a literal `<span id=
  "...">`, not FLS's own bracket syntax. Worth knowing before reaching for it: an inline
  `<span>` has no heading of its own, so nothing about §3's `{#custom-id}` *heading*
  mechanism (table-of-contents entries, the heading-level anchor link icon) comes along
  for free — it's a plainer, more minimal anchor than the block-level one.

### 3. ID grammar, and the anchor mechanics it has to survive

**Verified against the real renderer, not assumed.** metel-docs-internal builds through
Docusaurus (`tools/mdx-check-site`, adapted directly from `metel-website`'s own config);
Docusaurus supports an explicit heading ID natively via `## Heading {#custom-id}`, no
plugin needed. Ran a real `docusaurus build` with several candidate ID shapes appended,
rather than trust the syntax on documentation alone:

- `{#plain-id-test}` → `id=plain-id-test`. Clean.
- `{#with.dot.test}` → `id=with.dot.test`. Clean — dots round-trip exactly.
- `{#with:colon:test}` → `id=with:colon`, and the literal `{#with:colon:test}` leaks into
  the *visible* rendered heading text. Colons are silently corrupted, not rejected — worse
  than a build failure, since nothing would flag it.
- `{#spec:structs.field-visibility.legality-1}` (the original candidate grammar) →
  `id=spec.field-visibility.legality-1`, dropping `structs` entirely and merging the colon
  into a dot on top of it. Confirms the corruption is real on the actual shape this ADR
  needs, not just the isolated colon test.

**Correction: the test above was appended to `structs.md`, which doesn't exist anywhere in
this repo** — `public/reference/spec/` has no such file (struct declarations actually live
under `declarations.md`'s `## Structs` section); a shell `cat >>` against a path that
doesn't exist creates it rather than failing, so the build unknowingly ran against a file
fabricated on the spot, not real spec content. Caught while setting up a later, unrelated
test in this same ADR and re-checked immediately rather than left standing: re-ran the
identical heading-ID test appended for real to `declarations.md`, a real, existing spec
file. Same result — `{#spec.declarations.heading-retest.legality-1}` → `id=` matching
exactly, no corruption. The colon/dot finding above holds; only the file it was
demonstrated against was wrong, and is corrected here rather than silently fixed.

Decided from that evidence: **the grammar's `spec:` prefix separator becomes `spec.`, and
no ID may contain a colon anywhere.** Letters, digits, hyphens, and dots are all confirmed
safe.

```
id       := "spec." file "." section "." kind "-" n
file     := the spec file's stem, e.g. "declarations", "modules", "expressions" -- scoped to
            public/reference/spec/ (a flat directory today; see Consequences)
section  := kebab-case slug of the full heading breadcrumb down to the block's
            immediate enclosing section, e.g. "field-visibility", or
            "generics.bounds.where-clauses" if nested three deep
kind     := "legality" | "dynamics"
n        := digit+ letter*, sequential within file+section+kind, starting at 1
letter   := present only on a block produced by splitting an existing one
```

Example: `spec.declarations.field-visibility.legality-1` alongside
`spec.declarations.field-visibility.dynamics-1` in the same discursive section.

`section` is the full breadcrumb, not just the immediate heading's own text — two
same-named subsections nested under different parents (two "Examples" headings in one
file, say) would otherwise mint colliding IDs. It's still cosmetic in the sense that
matters for drift: for a human reading a citation, not re-derived by tooling, so
rewording any heading in the breadcrumb doesn't require touching existing IDs, the same
way `esid` doesn't re-derive from prose either. `n` is never reused once assigned, even if
the block is later removed; gaps in the sequence are expected, matching how ADR-0049
already tolerates gaps in section citations elsewhere. An ID, once minted, is permanent —
the same additive-only discipline ADR-0049 §8 applies to RFC checklists, extended one
level down to individual rule blocks.

A letter suffix, not a fresh `n`, marks a split child deliberately — `legality-1a`/
`legality-1b` reads as "these two came from one" at a glance, where `legality-1`/
`legality-2` would look like two independent rules that happened to land next to each
other. `letter*` (not a single optional letter) covers re-splitting an already-split
child too — `legality-1a` splitting again produces `legality-1aa`/`legality-1ab`, one more
letter appended rather than a new punctuation mark invented for the second level. Settled
here rather than left open: extending the existing suffix scales to arbitrary depth
without a grammar revision each time, and it's a strict extension of the one-letter case
already decided above, not a competing design.

**Rigor blocks live inside a `<details>` container, one per discursive section, at
the end of that section's prose and examples — not scattered inline between sentences.**
The container groups every Legality/Dynamic-Semantics block belonging to one discursive
section together, visually set apart from the surrounding "fluent" prose:

```markdown
Shorthand and explicit fields may be mixed freely within one literal.

<details>
<summary>Formal rules</summary>

##### Legality Rule {#spec.declarations.structs.instantiation-and-field-access.legality-1}

...

##### Dynamic Semantics {#spec.declarations.structs.instantiation-and-field-access.dynamics-1}

...

</details>

### Methods
```

**Collapsed by default — closed, not `open`.** That wasn't always safe: the stock
Docusaurus `<details>` has a real gap where a fragment link into a *closed* one does not
auto-expand it, checked directly against Docusaurus's own tracker rather than assumed —
[facebook/docusaurus#7165](https://github.com/facebook/docusaurus/issues/7165) reports
exactly this and is closed **"working as intended,"** not fixed. This ADR originally
defaulted every block to `open` to sidestep that gap, at a real cost: every rigor block
started expanded on every page regardless of whether a reader wanted to see it, so a
section's prose read as mostly formal-rules boilerplate rather than the discursive text it
actually is.

metel-website now renders `<details>` through its own component
(`src/theme/Details`, replacing @docusaurus/theme-classic's stock one — needed independently,
to fix a real animation bug in the stock component's open/close transition), which made the
anchor gap directly fixable instead of worked around: on mount and on `hashchange`, it
checks whether the page's current `#anchor` lives inside its own content and, if so, opens
itself and re-scrolls (correcting the browser's own scroll-to-hash, which ran against the
still-collapsed layout). Content is always in the DOM regardless of open/collapsed state —
never conditionally rendered — so `document.getElementById` finds the target either way;
only the block's *visibility* needed correcting. Verified against a real browser dispatching
an actual click and a real hash navigation, not just the CSS in isolation. A reader who
lands via citation link sees the target block open; every other block on the page, and every
other reader, sees the section's prose first.

**This also settles where a block goes, closing a real placement bug found while
reviewing delegated work.** Landing rigor blocks immediately after the specific sentence
they formalize — rather than after the section's prose and examples are both complete —
means the block gets spliced between two sentences that belong together, or between a
worked example and the prose introducing it. One container at the true end of the section
has no such ambiguity: everything discursive comes first, uninterrupted, then one visually
distinct block holds the section's formal rules.

**Grouping every rule at section-end costs the reader something once a container holds
several blocks: which prose sentence a given rule formalizes stops being obvious from
proximity alone.** Piloted a fix rather than deciding this in the abstract — a plain
markdown link from the exact prose words that state a claim, into the existing `{#...}`
id of the rule that formalizes it:

```markdown
Zero-field structs [may omit braces entirely](#spec.declarations.structs.instantiation-and-field-access.legality-2).
These two forms are [equivalent](#spec.declarations.structs.instantiation-and-field-access.dynamics-2):
```

No new anchor type and no ADR-0049 §1 exception — prose still never gets its own id, it
only links *into* ids that already exist, so this is pure markdown, verified against a
real build the same way every other anchor claim in this ADR has been.

**The rule, settled after the pilot: link every time a formal rule restates something the
prose already says; never invent prose solely to create a link target.** The pilot above
treated this as sparing, sentence-by-sentence judgment — reserved for sections where the
correspondence wasn't already obvious from proximity, deliberately not applied to every
sentence or every rule. A full editorial pass across all five migrated spec files
(2026-08-20) found the opposite in practice: proximity alone stops being enough the moment
a container holds more than one block, and nearly every discursive section already states
its rule's claim in some form somewhere nearby — eighteen more links landed cleanly in one
pass, none of them requiring new prose. The working rule going forward is therefore closer
to mechanical than the pilot framed it: **whenever a Legality Rule or Dynamic Semantics
block restates a claim the prose already makes, link it** — this is now a normal part of
migrating or editing a section, not a special case reserved for a few sections judged to
need it.

**The one real judgment call left is unchanged from the pilot's own finding: not every rule
has a matching sentence.** `legality-3` in the Instantiation and Field Access section ("a
struct with fields cannot omit its constructor fields") still has none — the prose only
ever discusses the zero-field case — and stays unlinked rather than forcing a connection,
or inventing prose, that doesn't already exist. That gap is a legitimate finding of doing
this exercise, not a defect in the linking mechanism — worth someone deciding later whether
the prose should say it too, out of scope for this ADR.

### 3a. Each rigor block backlinks to the RFC(s) that established it — generated, not authored

ADR-0049 §1's `rfc =` citation used to answer "why does this fixture exist" just by being
read. §7 above already named the cost of retiring it: that answer becomes "recoverable by
finding which RFC's `coverage` frontmatter points at the same `spec.` ID" — one hop away
instead of inline, accepted at the time rather than solved. Closing that gap for real means
a spec block needs to say which RFC(s) established it, without recreating the exact
duplication problem §7 designed the `spec =` migration to eliminate in the first place: if
a human hand-types "(established by RFC-0115)" onto the block, that is a second citation of
a fact the RFC's own frontmatter already states once, with nothing keeping the two in sync.

**Generated, the same way `REGISTRY.md` and `COVERAGE-BASELINE.json` already are — not
hand-authored, and not a new mechanism invented for this.** `rfc.py` already computes the
full RFC→spec-id mapping to produce §5's coverage summary; inverting it to "which RFC(s)
currently link to this spec-id" is the same data, read the other direction. `rfc.py index`
gains `--write-spec-origins`, mirroring `--write-coverage-baseline`'s existing shape, and
`--check-drift` gains the same coverage: a hand-edited or stale backlink fails CI exactly
the way a stale `REGISTRY.md` already does.

**Placed inline in the spec file, not a separate index — a real reader-facing choice, not
the lower-risk default.** A separate generated file would have been simpler to build (no
partial-file regeneration to get right, no risk of colliding with hand-authored prose) but
a reader browsing the rendered page would need to know a second file exists and go look
something up in it. Decided in favor of visibility: the backlink lives at the exact point a
reader would want it, right under the rule it names, at the cost of solving partial
regeneration inside an otherwise hand-authored file — new territory for this toolchain,
where every existing generated artifact is a whole file, never a slot inside one written by
a person.

**The slot is delimited by an explicit marker pair, not a fixed position or a heading
attribute**, so regeneration can rewrite exactly its own content and nothing else:

```markdown
##### Legality Rule {#spec.declarations.structs.instantiation-and-field-access.legality-1}

A struct-literal field initializer is `ident`, optionally followed by `= expr`. ...

<!-- rfc.py:origins:start -->
_Referenced by: [rfc-0115](../../rfcs/4-implemented/rfc-0115-field-initializer-separator.md)_
<!-- rfc.py:origins:end -->
```

A heading-attribute approach (packing the origin RFCs into `{#...legality-1 origins="..."}`)
was considered and rejected: it would keep the generated fact out of the rendered page
entirely, which is exactly the outcome the inline-over-index decision above was made to
avoid — a backlink nobody can see isn't a backlink. HTML comments in a plain `.md` file are
safe here, checked against real precedent already in this exact file rather than assumed —
`declarations.md` already carries `<!-- doc-example: ... -->` markers today (the corpus's
existing `doc-example: skip`/`expect-fail` convention) and builds cleanly; the risk
`tools/mdx-check-site`'s own README documents (`<!--` isn't valid JSX, so a raw HTML
comment breaks a `.mdx` file) is specific to `.mdx`, and every spec file is plain `.md`.

`--write-spec-origins` inserts a fresh marker pair for any rigor block that doesn't have
one yet, immediately after that block's own text; for a block with zero current origins
(genuinely pre-RFC content, ADR-0050's own Context section names this as real, not
hypothetical), the slot regenerates empty — no fabricated "not yet linked" text, since an
absent origin is a normal, valid state here, not a gap to apologize for. Multiple origins
list flatly (`_Referenced by: rfc-0115, rfc-0134_`) rather than asserting an
established/refined-by narrative the tool has no way to actually verify from the data it
has.

**Applied uniformly, unlike §3's prose-links.** §3's rule (link whenever the prose already
makes the same claim) still needs a person to notice the match and write the link inline —
mechanical in *when* to apply it, but not in *how*. Generating a backlink costs nothing per
block once the mechanism exists, so there's no authorial judgment involved at all; every
rigor block gets a slot regardless.

**Sequenced after the migration has real data to show, not now.** At 31/275 sections
spec-anchored, most blocks would regenerate an empty slot — correct, but not yet
demonstrating the value this exists for. Building `--write-spec-origins` fits naturally
alongside the rest of ADR-0050 §5's tooling (Sequencing step 3); running it for real is
worth doing once a few more backlog-sweep batches (#769) have landed.

### 4. A block split always reopens both children as uncovered

If `legality-1` already has a citing fixture and is split into `legality-1a`/`legality-1b`,
neither child inherits the parent's coverage — both start as uncovered until re-cited,
even though "morally" the existing fixture probably still covers one of them. The
alternative — assume coverage carries over — creates coverage the ratchet mechanism
(ADR-0049 §7's baseline+ratchet, extended to this surface per §8 below) can't see: a split
would silently make the tracked corpus *less* precise while reporting full coverage,
exactly the failure mode this whole design exists to close. Reopening forces whoever
performs the split to immediately re-triage and re-cite, which is the one moment they
still have full context for the decision.

### 5. Two independently-checkable invariants, not one transitive chain

- **RFC → spec-id.** Every RFC that has reached `3-integrated` must cite at least one
  `spec.` ID per normative claim it integrates (many-to-many: one RFC may touch several
  blocks, several RFCs may converge on one block — the same cardinality ADR-0049's
  `rfc-NNNN§section` citations already handle).
- **spec-id → fixture.** Every Legality/Dynamic-Semantics block needs at least one
  passing, kind-matched fixture citing its ID — a direct re-anchoring of ADR-0049 §2's
  mandate from RFC section to spec block. Not unconditional — a block can carry a typed
  exemption instead; see §6.
- **Both checks additionally require the citation resolves to a real, existing block.**
  The equivalent of ADR-0049 §4's "every cited section exists in the target RFC" check,
  extended to this surface: a `spec =` sidecar entry or a `coverage:` frontmatter entry
  naming an ID with no corresponding block in any spec file is a problem in its own
  right, not silently treated as either satisfied or absent. Catches a typo'd ID and a
  citation left dangling after a block is deleted — the same failure ADR-0049 §4 already
  catches on the RFC side, missing here without this bullet.

Validating these separately, rather than resolving the full chain in one pass, means a
broken link reports as exactly what's broken — a dangling RFC citation is a different
failure than an uncovered spec block — instead of one compound failure that hides which
half is the actual problem. `rfc.py check` gains two new problem classes, the same shape
as the drift checks ADR-0049 §4 already runs, not a new architecture.

### 6. Typed exemptions extend to spec-ids, same three kinds

§5's "needs ≥1 fixture" mandate is not unconditional — it inherits ADR-0049 §3's typed
exemption wholesale, reattached to a `spec.` ID instead of an RFC section, rather than
inventing a second exemption scheme:

| kind | means | resolves how |
|---|---|---|
| `untestable` | permanently outside what a fixture can observe | never — a standing fact about the block |
| `blocked` | testable in principle, blocked on a dependency that doesn't exist yet | closes when the dependency lands |
| `elsewhere` | tested, but not via an `.mtl` fixture (e.g. a Rust unit test) | already satisfied — needs its pointer kept alive |

Without this, the first genuinely-untestable Legality or Dynamic-Semantics block anyone
writes either blocks the gate forever or gets a fabricated fixture written just to
satisfy the mandate — the exact failure ADR-0049 §3 exists to prevent at the RFC level,
recurring at the finer grain if left unaddressed here. `untestable` keeps ADR-0049 §3's
own visible-list treatment (surfaced separately in the coverage report, not folded into
"exempt, done") for the identical reason: it's the easiest kind to reach for instead of
writing the fixture, so it stays the one a reviewer sees called out.

**Settled against a real build and a real corpus edit, not left for a future pilot.** The
exemption's `kind`/`reason`/`ref` triple lives as one hand-authored HTML comment
immediately after the block's own prose — not a heading attribute (no room for three
fields) and not a separate fenced block (would float, disconnected from the id it exempts):

```markdown
##### Legality Rule {#spec.functions.turbofish.legality-2}

The call's arguments must unify with their pinned types exactly as they would with an
inferred one.

<!-- rfc.py:exemption kind="blocked" ref="metel-core#775" reason="Argument unification
against an explicitly pinned type parameter is not yet implemented..." -->
```

`rfc.py index --write-spec-origins` — already the entrypoint that regenerates every rigor
block's origins/fixtures backlink — generates a third slot from this trigger, rendered
visibly on the page the same way origins/fixtures already are:

```markdown
<!-- rfc.py:exemption:rendered:start -->
<span class="rigor-backlink">_Exempt from fixture coverage — blocked on metel-core#775:
..._</span>
<!-- rfc.py:exemption:rendered:end -->
```

The trigger comment itself is never rewritten — only its generated mirror is — the same
one-source-of-truth relationship the origins span already has to RFC frontmatter, just
sourced from a per-block marker instead of a cross-file scan. `rfc.py check` validates the
triple (`kind` is one of the three; `blocked`/`elsewhere` require a `ref`) and, for a
`blocked` exemption whose `ref` names a GitHub issue rather than an RFC, checks it live
against the issues API — no secret required, since a public repo's single-issue GET is
anonymous-readable; degrades to skipping that one ref, never to failing the build, on any
network hiccup. Runs unconditionally, not gated behind the fixture-corpus reachability §5's
other checks need, so it fires from a bare docs-internal checkout too, not only from inside
metel-core. First real instance, and the worked example above: `spec.functions.turbofish.
legality-2` (`public/reference/spec/functions.md`).

**The rule that matters more than the mechanism: a rigor block always states the accepted
design, never the present-day bug.** Found the hard way — an earlier draft of
`spec.functions.turbofish.legality-2`'s own rule text was rewritten to describe *current,
broken* behavior directly ("it is not currently unified... `identity::<i64>('hello')` is
accepted today rather than rejected") instead of stating what turbofish is supposed to do
and exempting the gap. That's backwards. This ADR's own Context section already establishes
that the spec is where current truth lives — and for an accepted design that isn't
implemented yet, the *design* is the current truth, not the bug standing in front of it.
Weakening a rule's claim to match a known bug is the same failure mode §6's opening
paragraph already names for fixtures — fabricating one just to satisfy the mandate — just
committed against prose instead of tests. When a block's claim doesn't hold today: state the
claim as designed, and give it a `blocked` exemption. Never narrow the claim to fit reality.

**And once written, a `blocked` `ref` has to stay right, not just present.** The same
turbofish exemption's `ref` originally cited a different, already-*closed* issue
(metel-core#401) — accepted at write time because it *sounded* related (an old RFC
paraphrase used similar words), not because anyone re-read what it actually said. Reading it
directly showed it was closed and about a different mechanism entirely (ambiguous-literal
resolution, not turbofish-specific unification). The live issue-ref check above exists
specifically because that class of mistake is otherwise invisible until someone happens to
re-read the referenced issue by hand — but it only catches a blocker that's since *closed*,
not one that was *wrong from the start*. Getting the ref right at write time — read the
issue, don't trust a paraphrase of it — is still not optional.

### 7. `spec =` migrates in per-citation and retires the `rfc =` entry it supersedes

A fixture's sidecar today carries `rfc = ["rfc-0061§7.2"]` (ADR-0049 §1). Once the block
that citation points at has been assigned a `spec.` ID, the citation moves:

```toml
# before migration
[options]
rfc = ["rfc-0061§7.2"]

# after migration
[options]
spec = ["spec.declarations.field-visibility.legality-1"]
```

Not two permanent fields — `rfc =` is retired for that entry, not kept alongside `spec =`
indefinitely. Two citations of the same fact, both required to stay in sync forever, is
exactly the drift risk this whole ADR exists to design out; keeping `rfc =` around
unconditionally would recreate at the fixture layer the identical duplication problem this
ADR's Context section already rejected at the document layer (Ferrocene-vs-Reference). The
migration is per-*citation*, not per-file: a fixture that cites several sections can have
some already migrated (`spec =`) and some still pointing at content that hasn't reached
`3-integrated`
yet (`rfc =`) — both fields can coexist on one fixture during the transition, just never
as two live citations of the *same* fact.

This does cost something, stated plainly rather than glossed over: "why does this fixture
exist" stops being answerable by reading the fixture alone once its citation migrates.
That answer still exists — it's recoverable by finding which RFC's `coverage` frontmatter
(§8) points at the same `spec.` ID — but it's now one hop away instead of inline. Accepted
because the alternative is a citation pair with no natural moment to ever stop syncing,
and because the direct provenance line matters most for an already-closed RFC, which is
exactly the case §8's RFC→spec-id link still preserves.

### 8. A new gate on `--to integrated`, and the three-phase citation lifecycle it produces

**Not a permanent fallback — migration is mandatory, triggered by an RFC lifecycle event
that already exists, rather than left to a separate schedule or to whether anyone happens
to revisit the content.** An earlier draft of this section grandfathered every
`3-integrated`+ RFC indefinitely, migrating only on regression, the same way ADR-0049 §7
grandfathers its own pre-existing coverage gaps. Reconsidered: that leaves no forcing
function at all for content nobody happens to touch again, which is precisely the
population most exposed to the RFC-0022 problem this ADR exists to close — a claim that's
stable specifically *because* nobody revisits it is exactly the claim most likely to still
be sitting on a frozen, uncorrectable citation indefinitely.

**The fix: gate the `3-integrated` transition itself, not just `4-implemented`.**
`rfc.py transition <id> --to integrated` — a new gate; ADR-0049 §5 only ever gated
`--to implemented` — refuses to complete unless every *existing* `rfc =` citation for that
RFC has been migrated to `spec =`, minting a rigor block and an ID for each cited claim as
needed. Scoped to what the RFC actually claims, not the whole spec file around it — the
same per-claim granularity §1/§2 already use everywhere else, not a mandate to
rigor-block-ify an entire file just because one RFC touches a corner of it. Deliberately
narrow in one more way: this gate checks that *existing* citations migrate, not that the
RFC has achieved full coverage — that remains ADR-0049 §5's `--to implemented` gate's job,
unchanged, so integration and full implementation stay two separately-gated claims rather
than collapsing into one.

**Three phases result, with no permanent escape hatch in any of them:**

- **Pre-integration**: cite via `rfc =` (ADR-0049 §1, entirely unchanged). This is
  deliberately left alone — it's the phase that's already found real bugs this session
  (RFC-0022, RFC-0030, #757/#758), because a fixture can exist and disagree with an RFC's
  text *before* that text is locked down as the spec's own. Gating fixture-writing on
  spec-integration here would remove the mechanism that made those findings possible.
- **At integration**: `rfc.py transition <id> --to integrated` refuses to complete until
  every existing citation for that RFC is migrated (§7's per-citation mechanics apply
  unchanged — `rfc =` retired, `spec =` takes over, for each citation individually). A
  claim with no existing fixture yet has nothing to migrate and doesn't block the
  transition — its rigor block gets minted later, on demand, by the next bullet.
- **Post-integration**: no *new* fixture may cite the RFC via `rfc =` — `rfc.py check`
  flags a new `rfc =` entry naming an already-`3-integrated`+ RFC as a problem in its own
  right. A claim that reached integration with no fixture, and so had nothing to migrate,
  gets its rigor block and ID minted the first time someone actually adds a test for it —
  covering exactly the case the integration gate above can't, since there was nothing yet
  to force at that moment.

**The backlog this produces is bounded, not open-ended.** RFCs already sitting at
`3-integrated` when this ADR lands didn't pass through the new gate — it didn't exist yet
— so they're a fixed, enumerable, one-time sweep (Sequencing below), not a permanently
grandfathered population and not an ongoing background project. Every RFC that integrates
*after* this ADR lands migrates itself automatically as a condition of that transition, so
the backlog never grows again once the one-time sweep closes it out.

**Migration splits into two tracks with different risk profiles regardless of when it's
triggered, kept as separate steps below rather than one combined step.** Restructuring
existing discursive prose into rigor blocks is real authorial judgment — deciding what a
section's actual Legality Rules and Dynamic-Semantics claims are, not derivable
mechanically from the prose — the identical judgment ADR-0049 §8 already required for the
Coverage Checklist rollout, one level finer. Migrating an *already-existing* citation once
its target has been assigned an ID, by contrast, is close to mechanical and follows the
exact scripted-plus-human-reviewed shape ADR-0049 §1 already used for its own citation
migration. Conflating the two into one step would either over-trust the mechanical half
(fine) or under-trust the judgment half (risky) — Sequencing keeps them apart on purpose,
whether the trigger is the one-time backlog sweep or an individual RFC's own integration.

## Consequences

- Section granularity moves one level finer than ADR-0049's RFC-section anchor, which is
  the point — but it also means more IDs to mint and more per-block obligations than the
  RFC-section model had. That is deliberate friction, the same trade ADR-0049's Consequences section
  already accepted at the RFC-section level, now paid once more.
- A correction to observed behavior (the RFC-0022 shape) becomes a single edit to the
  relevant spec block, inherited by every RFC that ever cited it — the specific problem
  this ADR exists to close, measured against real history rather than hypothesized.
- Splitting a block is a strictly-monitored operation, not a free editorial choice: it
  always reopens coverage (§4), so it should be done deliberately, not casually, by
  whoever has fixture-writing capacity in the same change.
- No baseline or pilot numbers are included here, unlike ADR-0049's Baseline/Pilot
  sections — there is no real corpus to measure yet, since no spec file has a rigor block
  or an ID today. Fabricating illustrative numbers here would repeat the exact mistake
  ADR-0049's own Addendum sections spent three corrections fixing (a scratch estimate
  standing in for a measured one); Sequencing step 2 below produces the real baseline
  instead.
- `file` in §3's grammar is a bare stem with no directory component, checked directly
  against the real tree rather than assumed: `public/reference/spec/` is the only
  directory of its kind in the repo, and it's flat — nine files, no subdirectories. The
  grammar is scoped to that one directory on that basis; a bare stem stays collision-free
  as long as it stays true. If the spec ever grows a second directory or subdirectories of
  its own, `file` would need a path segment added — a grammar revision to make then,
  against a real second directory, not a hypothetical one to design around now.
- `--to integrated` becomes a heavier, slower gate to pass, the same deliberate trade
  ADR-0049 already accepted for `--to implemented`. An RFC will sit longer at
  pre-integration status while someone does the rigor-block-and-citation-migration work,
  because integrating an RFC and spec-anchoring its existing coverage are now the same
  act rather than two separately-scheduled ones. Accepted for the same reason ADR-0049
  accepted the equivalent cost at the later stage: real friction is the point, not a side
  effect, and it's what keeps the backlog in §8 from reopening after the one-time sweep
  closes it.

## Sequencing

1. ~~File the tracking issue; set `implements:` above.~~ Done — #767. (§3's
   anchor-mechanics question is already resolved too, verified against a real build rather
   than left for this step.)
2. **Pilot**: restructure 2–3 sections of one small, already-well-fixture-covered spec
   file into rigor-block form, mint real IDs, and migrate a handful of real citations
   end to end by hand. Matches the project's standing discipline of piloting before
   scaling (ADR-0049's own Baseline/Pilot sections), and is where this ADR's real numbers
   come from — deliberately not fabricated ahead of time in the Consequences section
   above. Picking an already-well-covered file keeps the pilot's own verification cheap
   and a pilot failure low-cost.
3. `rfc.py` support, built against the pilot's real data rather than a guess: parse
   `spec.` IDs, add the `spec =` sidecar key (§7), implement the two independent checks
   (§5), the typed-exemption handling (§6), the split-reopens-coverage bookkeeping (§4),
   and the migration-completeness check §8's new gate depends on (every `rfc =` citation
   for the RFC being transitioned has a `spec =` counterpart). Building the checker before
   scale-out, not after, is what let ADR-0049 catch its own three section-count bugs early
   rather than post-rollout.
4. **Turn the self-maintaining mechanism on before touching the backlog**: wire §8's new
   gate into `rfc.py transition --to integrated`, and add the "no new `rfc =` citation on
   an already-`3-integrated`+ RFC" rule to `rfc.py check`. Deliberately sequenced ahead of
   step 5 — every RFC that integrates from this point on migrates itself as a condition of
   that transition, so the one-time sweep below is clearing a backlog that has already
   stopped growing, not chasing one still accumulating underneath it.
5. **One-time backlog sweep**: every RFC already sitting at `3-integrated`+ when this ADR
   lands didn't pass through step 4's gate, so it's a fixed, enumerable population to
   clear explicitly — not an open-ended background project. For each: restructure its
   claims into rigor blocks (real authorial judgment, the identical kind ADR-0049 §8
   already required for the Coverage Checklist rollout — batch-delegatable, but every
   batch independently re-read against the original prose and the fixture suite re-run
   after each batch, the standing discipline this project has now needed twice for real,
   not a precaution taken once and dropped), then migrate its existing `rfc =` citations
   to `spec =` (mechanical once the blocks exist, but human-confirmed per citation rather
   than rewritten 1:1 — a single coarse RFC section can now correspond to several finer
   blocks, and an existing fixture may only really cover one of them, the same accuracy
   trap ADR-0049's own pilot caught twice at the coarser grain, RFC-0082 §3 and
   RFC-0116 §3). Prioritize the RFCs backing content still open in `COVERAGE-BASELINE.json`
   (RFC-0032/0034/0040) first, since sweeping there pays off an existing debt rather than
   adding ceremony to already-solid areas.
6. Re-key `COVERAGE-BASELINE.json` incrementally as the sweep proceeds: a migrated RFC's
   gap entries move to `spec.` keys at the moment it's swept; everything not yet reached
   stays RFC-keyed, so the ratchet is never checked against a baseline that's
   half-migrated and half-stale.
7. Wire §5's gate composition into `rfc.py transition --to implemented`, per RFC as each
   one's own claims are actually re-anchored — not a single global cutover, so the gate's
   behavior never changes for the whole corpus at once.
8. Build `rfc.py index --write-spec-origins` (§3a) and run it for real once a few more
   backlog-sweep batches (#769) have landed — at the population size the migration has
   today, most blocks would regenerate an empty slot, correct but not yet demonstrating
   what the backlink is for.
