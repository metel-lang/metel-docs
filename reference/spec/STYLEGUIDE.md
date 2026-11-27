# Spec Styleguide

A practical reference for writing or editing anything in `reference/spec/` (and,
where noted, `reference/error-codes.md`). Covers general spec prose, code examples, and
the Legality Rule / Dynamic Semantics rigor-block mechanism, plus error-codes.md's
parallel fixture-citation mechanism (ADR-0050 §9 / metel-core#981).

This directory is published: it's mirrored out of this (`metel-docs`) repo into the
language website via a git submodule (ADR-0051 retired the earlier
`metel-docs-internal` → `metel-docs` two-repo split — this repo is the single source
now, no `public/` prefix). Content elsewhere in this repo (`architecture/`, `rfcs/`)
does *not* make that trip and isn't reachable from the published site — don't link to it
from anything in here, or from anything in `metel-core` that ends up rendered (a fixture
sidecar's `reason=` text, e.g.). Reference an ADR or a metel-core-only doc (like
`metel-interpreter/docs/testing.md`) by name/number in plain text instead of a markdown
link.

## General principles

**Verify every claim against the real interpreter before writing it, or before leaving
existing prose as-is.** Don't take a sentence on faith just because it's already there —
several real bugs have been found this way, not hypothesized: a documented error-code
anchor that never existed, an `as` cast described as "numeric" when it actually dispatches
through `From` for any type, a turbofish rule that claimed enforcement the interpreter
doesn't actually do, a private-struct field-visibility claim that turned out to be false
once someone actually tried it cross-module. Existing text having survived past review is
not evidence it's still correct.

**State the accepted design, never a present-day bug or limitation, in ordinary prose.**
If a described behavior isn't actually true of the current interpreter, that's not a
detail to work into the sentence — it's a sign the claim needs a `> **Gap**` / `> **Limitation**`
marker citing the record that tracks it (see below) or, inside a rigor block, a typed
exemption (see below). Never narrow or hedge a claim to quietly match a known bug.

**When citing an issue, RFC, or PR by number, read it.** An old paraphrase, or a
similar-sounding title, is not the same as confirming it actually says what you're about
to cite it for — this has gone wrong for real (a `blocked` exemption once cited a closed,
unrelated issue this way).

## Layout: chapters, pages and sections

A chapter is one file (`lexical.md`) or, when it outgrows one page, a directory (`declarations/`). A directory
holds an `index.md` with the chapter's heading, its introduction and its closing `## Known gaps` section, and
one page per topic beneath it; a topic with parts of its own is a directory too (`declarations/aspects/index.md`
beside `dyn.md`, `coherence.md`). A page starts at `#` and its sections nest `##`, `###`, `####`; a rule block is
`#####` and is not a level. Each page carries `sidebar_position` frontmatter, which orders it in the sidebar.

A rule's id is `spec.<chapter>.<section>.<rule>` and does not depend on the page, so moving a section never
renames a rule and links are written `page.md#spec...`.

Keep the hierarchy shallow in size, not in depth: a **section** holds at most 250 lines of its own text and 12
rules, a **page** at most 600 lines, and no heading goes below `####` (`spec_lint.py`: `section-size`,
`page-size`, `heading-depth`; the pages that predate the rule are in the baseline). A section over the limit is
split into subsections, or the subsections into pages. To split a chapter into pages use the tool, which keeps
every anchor and rewrites every link by anchor:

```bash
python3 tools/spec_split.py skeleton reference/spec/<chapter>.md > plan.toml   # edit: group sections into pages
python3 tools/spec_split.py apply plan.toml --dry-run
python3 tools/spec_split.py apply plan.toml && python3 tools/spec_split.py check-links
python3 rfcs/tools/rfc.py index --write-spec-origins   # then the checks of "Verifying before you ship"
```

## Prose conventions

**No version provenance.** The spec states the language as it is. It has no `Availability`, `Since vX` or
`Changed in vX` callouts, and a rule's paragraph reads as true today, unconditionally. When a feature shipped and
how a behaviour changed live in the changelog and in the RFC that drove it (linked from the generated "Referenced
by" backlinks), and a reader on an older release reads the versioned docs snapshot cut for it. The one
version-bearing marker is for what is *not yet true*:

```markdown
> **Planned for v0.17.0 (RFC-0123).** One sentence on what ships and where it applies.
```

A `Planned for` marker is a single line, written under the heading or rule it qualifies, valid while the version
is still ahead of the release in progress, and deleted in the change that ships the feature. It may name its RFC so
drift against the design stays trackable. Nothing else in the spec carries a version.

**No internal numbers in the text.** RFC, ADR, issue and PR numbers, and `GAP-*` / `LIMIT-*` ids, do not appear in
the spec's prose, rules, tables or headings. The exception is the tracking marker (`Gap`, `Limitation`, `Pending`,
`Planned for`), which cites the record that tracks what is not yet true. Say what a thing does, and let the
generated backlinks carry the provenance. `rfcs/tools/spec_lint.py` enforces this and the limits below.

**Accepting a lint finding.** A finding that is right is fixed. One that predates a rule is grandfathered by the
baseline (`reference/spec/SPEC-LINT-BASELINE.json`, which only shrinks). A single justified exception is written
next to the text, on the line before the paragraph, quote or heading it covers, or, for a rule block, right after
the rule's `last_reviewed` line (where `rfc.py` keeps it):

```markdown
<!-- spec-lint: allow limit-in-prose reason="the return type is not yet known at that point of inference, not a limit" -->
```

This works for every rule. The reason is required and must explain why the finding is correct, `RULE` must be a rule
name from `spec_lint.py`, and an allow that covers nothing is itself a finding. After a rule's `last_reviewed` line it
covers the whole rule block; never put it inside the block's text. `rfc.py index --write-spec-origins` moves a comment
between rules to that spot, so write it there. `spec_lint.py --allows` lists every exception with its reason.

**Keep paragraphs and quotes short.** A prose paragraph or list item is at most 120 words and a quote block at most
60. Split a long paragraph by claim, and move a long rationale out of a quote into prose or into the rule it
explains.

**State claims in rule blocks, and cite them from prose.** A sentence that states what is an error or an error code
belongs in a Legality Rule or Dynamic Semantics block, and the prose around it links that rule's id. A section that
has rules links at least one of them from its prose, so a reader of the discursive text finds the formal claim.

**Gap** and **Limitation**, for something the spec cannot promise yet — an accepted but
unbuilt feature, a behavior the implementation lacks, a boundary the spec excludes. A
limit is never described in ordinary prose and never carries its own version, RFC or
issue: it is one marker line that cites the record tracking it (`architecture/gaps/` for a
spec gap, `architecture/limitations/` for an implementation shortfall against the spec,
ADR-0057):

```markdown
> **Gap** GAP-OWNERSHIP-001
> **Limitation** LIMIT-EVALUATION-005: closure environments are not destroyed until destructors run.
```

**Pending**, for the transient case: a part of the spec that is not implemented *yet*, because
the spec text landed first and the code follows in the same milestone, or because a limit was
found while implementing and is being fixed now. It is one marker line that cites the issue
tracking the work, and it has no record, disposition or review date:

```markdown
> **Pending** metel-core#1480 the new form is accepted by the checker but not yet by the evaluator.
```

The marker is valid while the issue is **open** and has a **milestone**. When the issue closes
the marker is stale and CI fails until it is removed; the release gate refuses to tag while a
marker's issue in that release's milestone is still open. If the part is instead deliberately left
unimplemented in a shipped version, convert the marker to a `Gap` or `Limitation` record, which
is the only path that leaves it in a release. Prose beside a `Pending` marker (its own paragraph
and the one before it) is not flagged by the limit-phrasing lint.

A fixture that documents the same not-yet-built part is skipped with `skip = "pending: #1234"`
(a `[options]` or top-level `skip` in its sidecar) instead of a `LIMIT-*` citation. The same rule
applies: valid while the issue is open and has a milestone, a failure once it is closed.

**Release gate.** `/cut-release` runs `check_architecture.py --release-gate <milestone> --core .`.
It refuses a tag while any pending marker or `pending:` fixture cites an issue still open in the
milestone being released, an issue with no milestone, a closed or missing issue, or one it could
not verify (GitHub unreachable: a gate cannot pass what it could not verify, unlike the everyday
check, which skips an unreachable API). A pending part that is not done at release is implemented
(the marker leaves with the issue), moved to a later milestone, or converted to a record.

*Before* (spec written ahead of the code): a `GAP-*` record is filed, and has to be resolved and
retired days later. *After*: the paragraph that states the behaviour, followed by the one marker
above; when the issue closes, delete the marker line. No record is written.

The site renders the record's one-line `summary` (or the sentence written after the ID,
when a rule needs its own wording), a link to the record, and chips from its `tracked_by`
(issue links) and `rfc` fields. Write the marker where the limit applies: under the rule or heading it
qualifies. `check_architecture.py` requires each marker to cite an existing, active
record of the kind its label names, and every active `GAP-*` to be cited in the chapter
its `scope` names. If no record exists yet, write one; do not describe the limit in prose.
`rfcs/tools/spec_lint.py` flags limit phrasing ("not yet", "deferred to", "not supported", "planned", "in this release", "under review") outside a marker as `limit-in-prose`; a new one fails CI (see "Accepting a lint finding").

**Cross-references** between spec files: plain relative markdown links —
`[Modules — Visibility](modules.md#visibility)`.

**Error-code references** link into `error-codes.md`'s own anchors (an em-dash in the
heading becomes a double-hyphen in the slug, e.g. `#t0002--annotation-required`) — check
the anchor actually exists before linking to it; a typo'd one silently renders as dead
text, not a build failure, unless it happens to be caught by Docusaurus's own
broken-anchor detector.

**Issue and RFC references** do not appear inline in prose (see "No internal numbers in the text" above); only a
tracking marker cites a record.

## Code examples

Fenced ` ```metel ` blocks are real, standalone Metel source, checked by
`tools/check_doc_examples.py` (metel-core) against the real interpreter — not
illustrative pseudo-code. Two markers opt a block out of that check, each requiring a
real `reason`, not a placeholder:

```markdown
<!-- doc-example: skip reason="elided body -- illustrates the signature only, not runnable" -->
<!-- doc-example: expect-fail reason="demonstrates that helper() is not visible from outer() -- the type error is the point" -->
```

`skip` for a fragment that was never meant to run (an elided body, a syntax illustration
with no real backing files); `expect-fail` for an example whose entire point is the error
it produces. Reach for one of these rather than silently letting an example go unchecked
some other way.

## Legality Rule / Dynamic Semantics blocks

Two kinds get a stable id — nothing else does, not the spec file, not discursive prose,
not `Syntax` (redundant with `grammar.pest`), not `Examples` (illustrative, not a source
of claims):

- **Legality Rule** — a static, compile-time claim ("a private field cannot be accessed
  outside its module").
- **Dynamic Semantics** — a runtime-behavior claim ("indexing a `SizedArray` out of
  bounds panics at runtime").

**The dividing line**: Dynamic Semantics documents exactly what a construct's *own*
evaluation does — never the behavior of something it merely delegates to. "Can this fail"
does not decide the category; whether the failure is *this construct's own* or *something
it calls out to* does.

### Where a block lives

At the end of its section's prose and examples — never spliced between sentences — inside
one `<details>` container per discursive section, collapsed by default:

```markdown
Shorthand and explicit fields may be mixed freely within one literal.

<details>
<summary>Formal rules</summary>

##### Legality Rule {#spec.declarations.structs.instantiation-and-field-access.legality-1}

A struct-literal field initializer is `ident`, optionally followed by `= expr`. ...

<!-- rfc.py:last_reviewed 3b5f8e02ba5c01e56fe960064a697f6247f0ced7 -->

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0115](../../rfcs/4-implemented/rfc-0115-field-initializer-separator.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<details class="rigor-fixtures-toggle" open>
<summary>Tested by (3)</summary>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoic3VjY2VzcyJ9LCJmaWxlcyI6W3sibmFtZSI6IjQzX3Nob3J0aGFuZF9maWVsZC5tdGwiLCJzb3VyY2UiOiIvLyBTaG9ydGhhbmQgZmllbGQgaW5pdGlhbGlzYXRpb246IGBQb2ludCB7IHgsIHkgfWAgZGVzdWdhcnMgdG8gYFBvaW50IHsgeCA9IHgsIHkgPSB5IH1gLiBUaGUgYnJhY2Vcbi8vIGxpdGVyYWwgaXMgd3JpdHRlbiBpbiBpdHMgdHlwZSdzIG93biBgZXh0ZW5kYCBibG9ja3MsIHRoZSBvbmx5IHBsYWNlIGl0IGlzIGxlZ2FsIChSRkMtMDEwMCBzZWN0aW9uIDMpLlxuXG5zdHJ1Y3QgUG9pbnQgeyB4OiBpNjQsIHk6IGk2NCB9XG5cbnN0cnVjdCBOYW1lZCB7IG5hbWU6IFN0cmluZywgdmFsdWU6IGk2NCB9XG5cbmV4dGVuZCBQb2ludCB7XG4gICAgLy8gQmFzaWMgc2hvcnRoYW5kOiBib3RoIGZpZWxkcy5cbiAgICBmdW4gZnJvbV9wYXJ0cyh4OiBpNjQsIHk6IGk2NCkgLT4gUG9pbnQge1xuICAgICAgICBQb2ludCB7IHgsIHkgfVxuICAgIH1cblxuICAgIC8vIE1peGVkOiBzaG9ydGhhbmQgYW5kIGV4cGxpY2l0LlxuICAgIGZ1biBtaXhlZCh4OiBpNjQpIC0+IFBvaW50IHtcbiAgICAgICAgUG9pbnQgeyB4LCB5ID0gMjAgfVxuICAgIH1cbn1cblxuZXh0ZW5kIE5hbWVkIHtcbiAgICAvLyBTdHJpbmcgZmllbGQuXG4gICAgZnVuIG9mKG5hbWU6IFN0cmluZywgdmFsdWU6IGk2NCkgLT4gTmFtZWQge1xuICAgICAgICBOYW1lZCB7IG5hbWUsIHZhbHVlIH1cbiAgICB9XG59XG5cbmZ1biBtYWluKCkge1xuICAgIGxldCBwIDo9IFBvaW50Ojpmcm9tX3BhcnRzKDMsIDcpO1xuICAgIGFzc2VydChwLnggPT0gMyk7XG4gICAgYXNzZXJ0KHAueSA9PSA3KTtcblxuICAgIGxldCBwMiA6PSBQb2ludDo6bWl4ZWQoMTApO1xuICAgIGFzc2VydChwMi54ID09IDEwKTtcbiAgICBhc3NlcnQocDIueSA9PSAyMCk7XG5cbiAgICBsZXQgbiA6PSBOYW1lZDo6b2YoXCJoZWxsb1wiLnRvX3N0cmluZygpLCA0Mik7XG4gICAgYXNzZXJ0KG4udmFsdWUgPT0gNDIpO1xuICAgIGFzc2VydChuLm5hbWUubGVuKCkgPT0gNSk7XG59XG4ifV0sImhyZWYiOiJodHRwczovL2dpdGh1Yi5jb20vbWV0ZWwtbGFuZy9tZXRlbC1jb3JlL2Jsb2IvdjAuMTYuMC9tZXRlbC1pbnRlcnByZXRlci90ZXN0cy9pbnRlZ3JhdGlvbi9zb3VyY2VzL2V2YWx1YXRvci9zdHJ1Y3RzLzQzX3Nob3J0aGFuZF9maWVsZC5tdGwiLCJuYW1lIjoiNDNfc2hvcnRoYW5kX2ZpZWxkLm10bCJ9"></details>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoic3VjY2VzcyJ9LCJmaWxlcyI6W3sibmFtZSI6ImFfZ2VuZXJpY19pbXBsX2Fzc29jaWF0ZWRfZnVuY3Rpb25faXNfY2FsbGVkX2J5X2l0c190eXBlX3BhdGgubXRsIiwic291cmNlIjoiLy8gbWV0ZWwtY29yZSMxODg4OiBhbiBhc3NvY2lhdGVkIGZ1bmN0aW9uIG9mIGEgZ2VuZXJpYyBgZXh0ZW5kPFQ+YCBibG9jaywgY2FsbGVkIHRocm91Z2ggdGhlIHR5cGUgcGF0aCxcbi8vIGlzIGNoZWNrZWQgYXQgdGhlIGNhbGwgYWdhaW5zdCB0aGUgY29uY3JldGUgdHlwZSBhcmd1bWVudHMgKGl0IHVzZWQgdG8gYmUgSTAwMDkpLlxuc3RydWN0IEJveDxUPiB7IHY6IFQgfVxuXG5leHRlbmQ8VD4gQm94PFQ+IHtcbiAgICBmdW4gd3JhcCh2OiBUKSAtPiBCb3g8VD4geyBCb3ggeyB2ID0gdiB9IH1cbiAgICBmdW4gdHdpY2UoZmlyc3Q6IFQsIHNlY29uZDogVCkgLT4gUGFpcjxUPiB7IFBhaXIoZmlyc3QgPSBmaXJzdCwgc2Vjb25kID0gc2Vjb25kKSB9XG4gICAgZnVuIGFnYWluKHY6IFQpIC0+IEJveDxUPiB7IEJveCB7IHYgfSB9XG59XG5cbnN0cnVjdCBQYWlyPFQ+IHsgZmlyc3Q6IFQsIHNlY29uZDogVCB9XG5cbmZ1biBtYWluKCkge1xuICAgIGFzc2VydChCb3g6OndyYXAoNSkudiA9PSA1KTtcbiAgICBhc3NlcnQoQm94Ojp3cmFwKHYgPSA2KS52ID09IDYpO1xuICAgIGFzc2VydChCb3g6OmFnYWluKFwic1wiKS52ID09IFwic1wiKTtcbiAgICBsZXQgcCA6PSBCb3g6OnR3aWNlKHNlY29uZCA9IDIsIGZpcnN0ID0gMSk7XG4gICAgYXNzZXJ0KHAuZmlyc3QgPT0gMSAmJiBwLnNlY29uZCA9PSAyKTtcbn1cbiJ9XSwiaHJlZiI6Imh0dHBzOi8vZ2l0aHViLmNvbS9tZXRlbC1sYW5nL21ldGVsLWNvcmUvYmxvYi92MC4xNi4wL21ldGVsLWludGVycHJldGVyL3Rlc3RzL2ludGVncmF0aW9uL3NvdXJjZXMvZXZhbHVhdG9yL3N0cnVjdHMvYV9nZW5lcmljX2ltcGxfYXNzb2NpYXRlZF9mdW5jdGlvbl9pc19jYWxsZWRfYnlfaXRzX3R5cGVfcGF0aC5tdGwiLCJuYW1lIjoiYV9nZW5lcmljX2ltcGxfYXNzb2NpYXRlZF9mdW5jdGlvbl9pc19jYWxsZWRfYnlfaXRzX3R5cGVfcGF0aC5tdGwifQ=="></details>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoic3VjY2VzcyJ9LCJmaWxlcyI6W3sibmFtZSI6InYwXzE2XzBfc3VyZmFjZV9zdGFnZV90b2dldGhlci5tdGwiLCJzb3VyY2UiOiIvLyBUaGUgdjAuMTYuMCBzdXJmYWNlIHN0YWdlIChtZXRlbC1jb3JlIzE4NjgpOiBgcHViYCwgYD1gIGFzIGEgc3RhdGVtZW50LCBjYWxsLWZvcm0gY29uc3RydWN0aW9uIHdpdGggbm9taW5hbCBicmFjZXMga2VwdCBmb3IgYVxuLy8gdHlwZSdzIG93biBgZXh0ZW5kYCBibG9ja3MgKFJGQy0wMTAwLCAjMjE5OS8jMjIwMCksIGtleXdvcmRcbi8vIGFyZ3VtZW50cyBhdCBldmVyeSBjYWxsLCBkb3R0ZWQgcm93IGxhYmVscywgbmVnYXRpdmUgcm93LWJvdW5kIGVudHJpZXMgYW5kIHJlcGxhY2VtZW50IGluIGEgcmVjb3JkIHNwcmVhZCxcbi8vIGluIG9uZSBwcm9ncmFtLCBzbyBhIGNvbnRyYWRpY3Rpb24gYmV0d2VlbiBhbnkgdHdvIG9mIHRoZW0gaXMgYSBmYWlsdXJlIGhlcmUuXG5wdWIgc3RydWN0IFJlYWRpbmcgeyBwdWIgc2Vuc29yOiBpNjQsIHZhbHVlOiBpNjQgfVxuXG5leHRlbmQgUmVhZGluZyB7XG4gICAgcHViIGZ1biBuZXcoc2Vuc29yOiBpNjQsIHZhbHVlOiBpNjQpIC0+IFJlYWRpbmcgeyBSZWFkaW5nIHsgc2Vuc29yLCB2YWx1ZSB9IH1cbiAgICBwdWIgZnVuIHNjYWxlZCgmc2VsZiwgYnk6IGk2NCwgb2Zmc2V0OiBpNjQpIC0+IGk2NCB7IHNlbGYudmFsdWUgKiBieSArIG9mZnNldCB9XG59XG5cbnB1YiBzdHJ1Y3QgQ291bnRlciB7IG46IGk2NCB9XG5cbmV4dGVuZCBDb3VudGVyIHtcbiAgICBmdW4gbmV4dCgmdmFyIHNlbGYpIC0+IGk2NCB7XG4gICAgICAgIHNlbGYubiA9IHNlbGYubiArIDE7XG4gICAgICAgIHNlbGYublxuICAgIH1cbn1cblxucHViIGVudW0gRXZlbnQgeyBTYW1wbGUgeyBpZDogaTY0LCBsZXZlbDogaTY0IH0sIElkbGUgfVxuXG5yZWNvcmQgRnJhbWU8cmVjb3JkIFI+IHsgc2VxOiBpNjQsIGRhdGE6IC57IC4uUiB9IH1cblxuZXh0ZW5kPHJlY29yZCBSOiAueyAudGFnOiBpNjQsICEuZHJvcCwgLi4gfT4gRnJhbWU8Li5SPiB7XG4gICAgZnVuIGtpbmQoJnNlbGYpIC0+IGk2NCB7IDEgfVxufVxuXG5leHRlbmQ8cmVjb3JkIFI6IC57ICEudGFnLCAuLiB9PiBGcmFtZTwuLlI+IHtcbiAgICBmdW4ga2luZCgmc2VsZikgLT4gaTY0IHsgMiB9XG59XG5cbmZ1biBjbGFtcDxyZWNvcmQgUjogLnsgLmxldmVsOiBpNjQsICEuc2VjcmV0LCAuLiB9PihyOiBSKSAtPiBpNjQgeyByLmxldmVsIH1cblxuZnVuIGRlc2NyaWJlKGU6IEV2ZW50KSAtPiBpNjQge1xuICAgIG1hdGNoIChlKSB7XG4gICAgICAgIEV2ZW50OjpTYW1wbGUgeyBpZCwgbGV2ZWwgfSA9PiBpZCAqIDEwMCArIGxldmVsLFxuICAgICAgICBFdmVudDo6SWRsZSA9PiAwLFxuICAgIH1cbn1cblxuZnVuIG1haW4oKSB7XG4gICAgLy8gb3JkaW5hcnkgZmFjdG9yeSBjYWxscywgcG9zaXRpb25hbCBhbmQga2V5d29yZCwgaW4gZWl0aGVyIG9yZGVyXG4gICAgbGV0IGEgOj0gUmVhZGluZzo6bmV3KHNlbnNvciA9IDEsIHZhbHVlID0gNSk7XG4gICAgbGV0IGIgOj0gUmVhZGluZzo6bmV3KHZhbHVlID0gNiwgc2Vuc29yID0gMik7XG4gICAgYXNzZXJ0KGEuc2Vuc29yICsgYi5zZW5zb3IgPT0gMyk7XG5cbiAgICAvLyBrZXl3b3JkIGFyZ3VtZW50cyBvbiBhIG1ldGhvZCBjYWxsLCBpbiBhIGRpZmZlcmVudCBvcmRlciB0aGFuIGRlY2xhcmVkXG4gICAgYXNzZXJ0KGEuc2NhbGVkKG9mZnNldCA9IDMsIGJ5ID0gMikgPT0gMTMpO1xuXG4gICAgLy8gYD1gIGlzIGEgc3RhdGVtZW50OyBjb21wb3VuZCBvcGVyYXRvcnMgYW5kIGZvci11cGRhdGUgY2xhdXNlc1xuICAgIHZhciB0b3RhbCA6PSAwO1xuICAgIGZvciAodmFyIGkgOj0gMDsgaSA8IDM7IGkgKz0gMSkgeyB0b3RhbCA9IHRvdGFsICsgaTsgfVxuICAgIGFzc2VydCh0b3RhbCA9PSAzKTtcblxuICAgIC8vIGRvdHRlZCBsYWJlbHM6IGEgcmVjb3JkIGxpdGVyYWwsIGEgcGF0dGVybiwgYSB0eXBlXG4gICAgbGV0IHNhbXBsZSA6PSAueyAuaWQgPSA3LCAubGV2ZWwgPSA0IH07XG4gICAgbGV0IC57IC5pZCwgLmxldmVsIH0gOj0gc2FtcGxlO1xuICAgIGFzc2VydChpZCA9PSA3ICYmIGxldmVsID09IDQpO1xuXG4gICAgLy8gZW51bSBzdHJ1Y3QtdmFyaWFudCBidWlsdCBhbmQgZGVzdHJ1Y3R1cmVkIHdpdGggbm9taW5hbCBicmFjZXNcbiAgICBhc3NlcnQoZGVzY3JpYmUoRXZlbnQ6OlNhbXBsZShsZXZlbCA9IDQsIGlkID0gNykpID09IDcwNCk7XG4gICAgYXNzZXJ0KGRlc2NyaWJlKEV2ZW50OjpJZGxlKSA9PSAwKTtcblxuICAgIC8vIGEgcmVjb3JkIHNwcmVhZCByZXBsYWNpbmcgYSBwcmVzZW50IGZpZWxkIGFuZCBhZGRpbmcgYW4gYWJzZW50IG9uZVxuICAgIGxldCBidW1wZWQgOj0gLnsgLi5zYW1wbGUsIC5sZXZlbCA9IHNhbXBsZS5sZXZlbCArIDEsIC5ub3RlID0gMSB9O1xuICAgIGFzc2VydChidW1wZWQubGV2ZWwgPT0gNSAmJiBidW1wZWQuaWQgPT0gNyAmJiBidW1wZWQubm90ZSA9PSAxKTtcblxuICAgIC8vIGEgbmVnYXRpdmUgcm93LWJvdW5kIGVudHJ5IHNlbGVjdHMgdGhlIGltcGw7IGEgYm91bmQgd2l0aCBhIG5lZ2F0aXZlIGVudHJ5IGFjY2VwdHMgdGhlIHJlY29yZFxuICAgIGxldCB0YWdnZWQgOj0gRnJhbWUoc2VxID0gMSwgZGF0YSA9IC57IC50YWcgPSA5IH0pO1xuICAgIGxldCBwbGFpbiA6PSBGcmFtZShzZXEgPSAyLCBkYXRhID0gLnsgLmNvdW50ID0gMyB9KTtcbiAgICBhc3NlcnQodGFnZ2VkLmtpbmQoKSA9PSAxICYmIHBsYWluLmtpbmQoKSA9PSAyKTtcbiAgICBhc3NlcnQoY2xhbXAoLnsgLmxldmVsID0gOCwgLmV4dHJhID0gMSB9KSA9PSA4KTtcblxuICAgIC8vIGEgY29uc3RydWN0aW9uIGNhbGwgd2hvc2UgYXJndW1lbnRzIGNhcnJ5IHNpZGUgZWZmZWN0cyBldmFsdWF0ZXMgdGhlbSBhcyB3cml0dGVuXG4gICAgdmFyIGNvdW50ZXIgOj0gQ291bnRlcihuID0gMCk7XG4gICAgbGV0IGZpcnN0IDo9IFJlYWRpbmcodmFsdWUgPSBjb3VudGVyLm5leHQoKSwgc2Vuc29yID0gY291bnRlci5uZXh0KCkgKiAxMCk7XG4gICAgYXNzZXJ0KGZpcnN0LnZhbHVlID09IDEgJiYgZmlyc3Quc2Vuc29yID09IDIwKTtcbn1cbiJ9XSwiaHJlZiI6Imh0dHBzOi8vZ2l0aHViLmNvbS9tZXRlbC1sYW5nL21ldGVsLWNvcmUvYmxvYi92MC4xNi4wL21ldGVsLWludGVycHJldGVyL3Rlc3RzL2ludGVncmF0aW9uL3NvdXJjZXMvZXZhbHVhdG9yL2ludGVncmF0aW9uL3YwXzE2XzBfc3VyZmFjZV9zdGFnZV90b2dldGhlci5tdGwiLCJuYW1lIjoidjBfMTZfMF9zdXJmYWNlX3N0YWdlX3RvZ2V0aGVyLm10bCJ9"></details>
</details>
<!-- rfc.py:fixtures:end -->

##### Dynamic Semantics {#spec.declarations.structs.instantiation-and-field-access.dynamics-1}

A shorthand field `ident` in a struct literal evaluates identically to `ident = ident`. ...

<!-- rfc.py:last_reviewed 3b5f8e02ba5c01e56fe960064a697f6247f0ced7 -->

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0115](../../rfcs/4-implemented/rfc-0115-field-initializer-separator.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<p class="rigor-backlink"><em>Tested by</em></p>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoic3VjY2VzcyJ9LCJmaWxlcyI6W3sibmFtZSI6IjQzX3Nob3J0aGFuZF9maWVsZC5tdGwiLCJzb3VyY2UiOiIvLyBTaG9ydGhhbmQgZmllbGQgaW5pdGlhbGlzYXRpb246IGBQb2ludCB7IHgsIHkgfWAgZGVzdWdhcnMgdG8gYFBvaW50IHsgeCA9IHgsIHkgPSB5IH1gLiBUaGUgYnJhY2Vcbi8vIGxpdGVyYWwgaXMgd3JpdHRlbiBpbiBpdHMgdHlwZSdzIG93biBgZXh0ZW5kYCBibG9ja3MsIHRoZSBvbmx5IHBsYWNlIGl0IGlzIGxlZ2FsIChSRkMtMDEwMCBzZWN0aW9uIDMpLlxuXG5zdHJ1Y3QgUG9pbnQgeyB4OiBpNjQsIHk6IGk2NCB9XG5cbnN0cnVjdCBOYW1lZCB7IG5hbWU6IFN0cmluZywgdmFsdWU6IGk2NCB9XG5cbmV4dGVuZCBQb2ludCB7XG4gICAgLy8gQmFzaWMgc2hvcnRoYW5kOiBib3RoIGZpZWxkcy5cbiAgICBmdW4gZnJvbV9wYXJ0cyh4OiBpNjQsIHk6IGk2NCkgLT4gUG9pbnQge1xuICAgICAgICBQb2ludCB7IHgsIHkgfVxuICAgIH1cblxuICAgIC8vIE1peGVkOiBzaG9ydGhhbmQgYW5kIGV4cGxpY2l0LlxuICAgIGZ1biBtaXhlZCh4OiBpNjQpIC0+IFBvaW50IHtcbiAgICAgICAgUG9pbnQgeyB4LCB5ID0gMjAgfVxuICAgIH1cbn1cblxuZXh0ZW5kIE5hbWVkIHtcbiAgICAvLyBTdHJpbmcgZmllbGQuXG4gICAgZnVuIG9mKG5hbWU6IFN0cmluZywgdmFsdWU6IGk2NCkgLT4gTmFtZWQge1xuICAgICAgICBOYW1lZCB7IG5hbWUsIHZhbHVlIH1cbiAgICB9XG59XG5cbmZ1biBtYWluKCkge1xuICAgIGxldCBwIDo9IFBvaW50Ojpmcm9tX3BhcnRzKDMsIDcpO1xuICAgIGFzc2VydChwLnggPT0gMyk7XG4gICAgYXNzZXJ0KHAueSA9PSA3KTtcblxuICAgIGxldCBwMiA6PSBQb2ludDo6bWl4ZWQoMTApO1xuICAgIGFzc2VydChwMi54ID09IDEwKTtcbiAgICBhc3NlcnQocDIueSA9PSAyMCk7XG5cbiAgICBsZXQgbiA6PSBOYW1lZDo6b2YoXCJoZWxsb1wiLnRvX3N0cmluZygpLCA0Mik7XG4gICAgYXNzZXJ0KG4udmFsdWUgPT0gNDIpO1xuICAgIGFzc2VydChuLm5hbWUubGVuKCkgPT0gNSk7XG59XG4ifV0sImhyZWYiOiJodHRwczovL2dpdGh1Yi5jb20vbWV0ZWwtbGFuZy9tZXRlbC1jb3JlL2Jsb2IvdjAuMTYuMC9tZXRlbC1pbnRlcnByZXRlci90ZXN0cy9pbnRlZ3JhdGlvbi9zb3VyY2VzL2V2YWx1YXRvci9zdHJ1Y3RzLzQzX3Nob3J0aGFuZF9maWVsZC5tdGwiLCJuYW1lIjoiNDNfc2hvcnRoYW5kX2ZpZWxkLm10bCJ9"></details>
<!-- rfc.py:fixtures:end -->

</details>

The example above shows one citing fixture, rendered as a plain `<p>Tested by</p>` label.
A rule with several citations wraps them instead (metel-core#979), graded by count so the
common case stays unobtrusive: 2-3 fixtures render inside an `open`-by-default `<details
class="rigor-fixtures-toggle"><summary>Tested by (N)</summary>`, closeable but visible;
4+ renders the same wrapper collapsed by default. This is generated the same as the
single-fixture case — never hand-write the wrapper or its `open` attribute.

### Methods
```

### ID grammar

```
id       := "spec." file "." section "." kind "-" n
file     := the spec file's stem (declarations, modules, expressions, ...)
section  := kebab-case slug of the full heading breadcrumb, e.g.
            "generics.bounds.where-clauses" if nested three deep
kind     := "legality" | "dynamics"
n        := digit+ letter*, sequential within file+section+kind, starting at 1
letter   := present only on a block produced by splitting an existing one
```

Letters, digits, hyphens, and dots only — no colons (Docusaurus silently corrupts a colon
in a heading id instead of rejecting it, which is worse). An id, once minted, is
permanent; `n` is never reused, even after the block it named is deleted.

### Granularity: split, don't bundle

A rule covering several independently-wrong-able cases should be its own block, not
folded into a shared one — so the coverage report can say "this exact case is untested,"
not "this general area has *a* fixture, the rest unknown." No mechanical rule decides
when to split; it's the same authorial judgment a well-designed test suite already
requires.

**A block split always reopens every child as uncovered**, even though the old fixture
probably still covers one of them — re-triage and re-cite immediately, while the context
for the decision is still fresh.

Worked example: `spec.functions.turbofish.legality-1` split into `legality-1` (pinning +
bound-checking, already fixture-tested) and `legality-2` (argument unification against
the pinned type) once it became clear the merged id was hiding that only half its claim
was actually true.

### Terseness

A Legality Rule or Dynamic Semantics block states a bare testable claim; it doesn't
explain it. Rationale, motivating examples, and prose walkthroughs belong in the
section's discursive prose above the `<details>` — link the rule's id into that prose
("Link prose to the rule it restates", below) instead of re-explaining the claim inside
the block. A block that mostly restates its own section's prose, just in more words, is a
sign the prose already carries the claim and the block should shrink to what's left: the
part that's actually checkable.

Two things belong in the marker above a block, never folded into its own prose:

- **A limit or a plan** — a `Gap` / `Limitation` / `Pending` / `Planned for` marker. A block's own paragraph
  reads as true today, unconditionally, with no version or RFC in it; historical framing belongs in the changelog.
- **A cross-reference to a related rule** — link its id (`[legality-9](#...)`) rather than
  restating what that rule says.

There's no fixed word budget: a rule specifying an exact algorithm (a structural-equality
normalization, a fixed resolution stage order) legitimately needs the words that name
each step, and padding that out to hit a number would make it worse, not better. What
actually marks a block worth trimming is restating content its own section's prose
already carries, motivating *why* the rule exists rather than just stating it, or walking
through an example instead of pointing at one in the prose above. If trimming reveals the
block was bundling more than one independently-wrong-able claim, split it (above) rather
than leaving the bundle merely shorter.

### Link prose to the rule it restates

Whenever a Legality Rule or Dynamic Semantics block restates a claim the prose already
makes, link the prose words into the block's id — a normal part of writing or editing a
section, not a special case reserved for a few sections judged to need it:

```markdown
A zero-field struct [is built by call, like any other](#spec.declarations.structs.instantiation-and-field-access.legality-2).
```

Plain markdown, no new anchor type. Skip it only when a rule genuinely has no matching
sentence in the prose — don't invent prose solely to create a link target.

### Backlinks: generated, never hand-written

Up to three HTML-comment-delimited slots per block, all regenerated by
`rfc.py index --write-spec-origins`:

```markdown
<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0115](../../rfcs/4-implemented/rfc-0115-field-initializer-separator.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<span class="rigor-backlink">_Tested by: [43_shorthand_field.mtl](https://github.com/metel-lang/metel-core/blob/main/metel-interpreter/tests/integration/sources/evaluator/structs/43_shorthand_field.mtl)_</span>
<!-- rfc.py:fixtures:end -->
```

Never hand-edit the content between a `start`/`end` pair — origins comes from the citing
RFC's own `coverage:` frontmatter, fixtures from the fixture corpus's `spec =` citations.
`rfc.py index --check-drift` catches a hand-edited or stale slot.

### Review checkpoint: hand-typed, the opposite of a backlink

A block with a citing fixture carries one more line, right after its prose and *outside*
the generated marker pairs above (which `--write-spec-origins` rewrites wholesale, so
anything living inside them would never survive a regeneration):

```markdown
<!-- rfc.py:last_reviewed 512e55f4512665d9745d6aefdc357e1b23b1f8b4 -->
```

The opposite of the backlinks above: `rfc.py` never writes this, only audits it
(metel-core#1192, same model as metel-core#1191 for the Architecture Spec). It records
the metel-core commit as of which a human confirmed the citing fixture(s) still
demonstrate this rule's prose. `rfc.py check` flags the block once its citing
fixture's `.toml`/`.mtl` is touched by a later commit — re-read the fixture against the
rule, then bump the SHA by hand. A field the tool refreshed for you would give no forcing
function at all, since accepting its diff would take no more attention than a merge
conflict.

### Exemptions: state the design, not the bug

A block doesn't need a fixture if it carries a typed exemption instead — one
hand-authored trigger line, right after the block's own prose:

```markdown
<!-- rfc.py:exemption kind="blocked" ref="metel-core#753" reason="Depends on a `..` rest pattern for struct field patterns, which doesn't exist in the grammar (record_pattern has no rest form)." -->
```

- `kind` — `untestable` (permanent, structural: no program could ever violate it),
  `blocked` (testable in principle, blocked on a real dependency), or `elsewhere` (tested,
  but not via an `.mtl` fixture — e.g. a Rust unit test).
- `reason` — required, free text.
- `ref` — required for `blocked`/`elsewhere`: an RFC id (`rfc-0121`) or a GitHub issue
  (`metel-core#753`). A `blocked` ref gets checked: an RFC-shaped one locally against its
  current stage, an issue-shaped one live against the GitHub API (no secret required — a
  public repo's single-issue GET is anonymous-readable). A confirmed-closed blocker fails
  `rfc.py check`.

`rfc.py index --write-spec-origins` renders the exemption the same way it renders
origins/fixtures — never hand-write that rendered span either.

This is the same "state the design, not the bug" principle from General Principles above,
made concrete: if turbofish is supposed to unify its arguments against a pinned type but
doesn't yet, the block says arguments must unify — and gets a `blocked` exemption citing
the real gap. It does *not* get rewritten to say "arguments aren't currently unified."
Weakening a claim to match a known bug is the same failure fabricating a fixture would
be — just committed against prose instead of tests.

## Error codes (error-codes.md)

`reference/error-codes.md` gets the same fixture-citation and rendering mechanism as
Legality Rule / Dynamic Semantics blocks (above), reused rather than duplicated, with
three deliberate differences (ADR-0050 §9 / metel-core#981):

- **Id comes from the heading, not a minted `{#...}` anchor.** A code's section is
  `### T0003 — Undefined name`; `rfc.py` derives the citable id `T0003` straight from
  that heading text (`^### (?P<code>[A-Z]\d{4}) — .+$`). No ID grammar to hand-author,
  and no way for the id and the heading to drift apart.
- **No origins slot.** A rigor block's `Referenced by: [rfc-NNNN]` backlink comes from an
  RFC's `coverage:` frontmatter pointing *at* the block; an error code has no equivalent
  upstream citer, so only the fixtures marker and an optional exemption trigger ever
  appear under a code's heading — never an origins block.
- **Coverage and display are two separate counts, not one.** *Coverage* is automatic and
  free: every fixture's own `[expect].code` in the whole corpus counts as proof that code
  is real, whether or not anyone ever cites it. *Display* is curated: only a fixture whose
  sidecar explicitly names the code via `error = ["T0003"]` gets rendered as this code's
  inline viewer. A code can be covered with nothing displayed (real, just not curated
  yet) — that's a named gap for `rfc.py check` to report, not silently "untested." Split
  from `spec =` on purpose: `error =` and `spec =` are different citation *axes* (evidence
  for a diagnostic vs. evidence for a language rule) even when the same fixture earns
  both.

**A fixture's viewer, rendered on error-codes.md, links back to the formal rule it also
demonstrates.** When a citing fixture's sidecar carries its own `spec = [...]` (ADR-0050)
alongside the `error =` that got it here, `rfc.py` embeds that as a `specLinks` field in
the same payload — the metel-website side (`SpecFixtureView.tsx`) renders it as an
always-visible "Also demonstrates: …" line back to the Legality Rule / Dynamic Semantics
block. Per-fixture, not a comprehensive code-to-rule index — a code with 20 citing
fixtures where only 3 happen to also cite a spec block shows the backlink on those 3
only. Never rendered on a spec page's own fixture viewer (the fixture is already sitting
under that exact rule there — the backlink would be circular). #977's own code ↔ prose
linking (the reverse direction: a bare code mention in spec prose, or a fixture's
`expect` chip, linking *to* error-codes.md) is separate and already shipped.

Everything else is identical to the rigor-block mechanism: one `<details
class="spec-fixture">` viewer per citing fixture, the same `<!-- rfc.py:fixtures:start
/end -->` markers, the same graded Tested-by wrapping by citation count, and the same
`blocked` / `untestable` / `elsewhere` exemption vocabulary and trigger-line syntax for a
code with no fixture (a phantom or long-superseded code gets `untestable` with the
reason spelled out — see T0026-T0030's split history for a worked example of splitting a
bundled heading once mixed status came to light, same principle as "Granularity: split,
don't bundle" above).

**A new `error = [...]`-style sidecar key needs a matching change in metel-core's
`harness/fixture.rs`, not just here.** `rfc.py` and the Rust integration-test harness are
two independent parsers of the same fixture sidecar TOML — the harness rejects any
`[options]` key it doesn't recognize, so a citation key that only rfc.py knows about
passes `rfc.py check` cleanly and then panics every fixture using it in `cargo test`. See
`metel-interpreter/docs/testing.md` (metel-core) for the sidecar key reference and this
gotcha in full.

## Verifying before you ship

- `rfc.py check` (`rfcs/tools/rfc.py`) — structural checks (id grammar, drift, exemption
  well-formedness, the live issue-ref check) always run, for both spec rigor blocks and
  error-codes.md. Fixture-coverage counting additionally needs `metel-interpreter/tests`
  reachable (`METEL_CORE_ROOT=/path/to/metel-core`, or run from inside a metel-core
  checkout) — it reports spec-block and error-code coverage as two separate counts.
- `rfc.py index --write-spec-origins` after touching a block's text, its citing RFC's
  `coverage:` frontmatter, or its exemption trigger — or an error code's citing fixture or
  exemption trigger in error-codes.md, same command, same flag.
- `rfc.py index --check-drift` — confirms every generated slot in both reference/spec/
  and error-codes.md matches what regeneration would produce.
- A real `docusaurus build` (`tools/mdx-check-site/`, see its own README) — confirms an
  anchor or cross-reference actually renders and resolves, not just that the markdown
  parses. Catches a dead link before a reader does.
- If a claim touches real interpreter behavior, run it: build `metel-core` and try the
  program the claim describes. Don't cite a fixture, or write a claim, you haven't
  watched pass yourself.

## Known gaps section

Every chapter ends with a `## Known gaps` heading whose only content is the marker
`<!-- records:gaps -->`. The website renders the chapter's active `GAP-*` records
there from the records themselves (ADR-0057), each linking to its own page, so do
not write entries by hand. Record content (title, one-line `summary`, disposition)
lives in `architecture/gaps/`. `check_architecture.py` enforces the heading and
marker.
