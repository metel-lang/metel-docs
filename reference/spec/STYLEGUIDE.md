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
detail to work into the sentence — it's a sign the claim needs a `> **Planned for...**`
callout (a real future feature, honestly labeled) or, inside a rigor block, a typed
exemption (see below). Never narrow or hedge a claim to quietly match a known bug.

**When citing an issue, RFC, or PR by number, read it.** An old paraphrase, or a
similar-sounding title, is not the same as confirming it actually says what you're about
to cite it for — this has gone wrong for real (a `blocked` exemption once cited a closed,
unrelated issue this way).

## Prose conventions

**Availability**, at the top of a section introducing something not present since v0.1:

```markdown
> **Availability:** Since v0.8.0.
> **Availability:** Matching-error `?` since v0.1.0. `From`-based error coercion since v0.4.0.
```

**Changed**, when a later release altered established behavior — cite the RFC if one
drove it:

```markdown
> **Changed in v0.11.0 (RFC-0111): `None` and `Some` are ordinary variants of `Perhaps<T>`, not literals.**
```

**Planned**, for a real, accepted-but-unbuilt future feature — the honest way to describe
something that doesn't exist yet. Never blend this into ordinary descriptive prose as if
it already works:

```markdown
> **Planned for v0.13.0 (RFC-0122): shared XOR exclusive — a place may have any number of `&T` borrows, or exactly one `&var T`, never both.**
```

**Cross-references** between spec files: plain relative markdown links —
`[Modules — Visibility](modules.md#visibility)`.

**Error-code references** link into `error-codes.md`'s own anchors (an em-dash in the
heading becomes a double-hyphen in the slug, e.g. `#t0002--annotation-required`) — check
the anchor actually exists before linking to it; a typo'd one silently renders as dead
text, not a build failure, unless it happens to be caught by Docusaurus's own
broken-anchor detector.

**Issue references** inline in prose: `metel-core#NNN` (e.g. "Since v0.12.1
(metel-core#664)").

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

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0115](../../rfcs/4-implemented/rfc-0115-field-initializer-separator.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<p class="rigor-backlink"><em>Tested by</em></p>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoic3VjY2VzcyJ9LCJmaWxlcyI6W3sibmFtZSI6IjQzX3Nob3J0aGFuZF9maWVsZC5tdGwiLCJzb3VyY2UiOiIvLyBTaG9ydGhhbmQgZmllbGQgaW5pdGlhbGlzYXRpb246IGBQb2ludCB7IHgsIHkgfWAgZGVzdWdhcnMgdG8gYFBvaW50IHsgeCA9IHgsIHkgPSB5IH1gLlxuXG5zdHJ1Y3QgUG9pbnQgeyB4OiBpNjQsIHk6IGk2NCB9XG5cbnN0cnVjdCBOYW1lZCB7IG5hbWU6IFN0cmluZywgdmFsdWU6IGk2NCB9XG5cbmZ1biBtYWtlX3BvaW50KHg6IGk2NCwgeTogaTY0KSAtPiBQb2ludCB7XG4gICAgUG9pbnQgeyB4LCB5IH1cbn1cblxuZnVuIG1haW4oKSB7XG4gICAgLy8gQmFzaWMgc2hvcnRoYW5kOiBib3RoIGZpZWxkcy5cbiAgICBsZXQgeCA6PSAzO1xuICAgIGxldCB5IDo9IDc7XG4gICAgbGV0IHAgOj0gUG9pbnQgeyB4LCB5IH07XG4gICAgYXNzZXJ0KHAueCA9PSAzKTtcbiAgICBhc3NlcnQocC55ID09IDcpO1xuXG4gICAgLy8gTWl4ZWQ6IHNob3J0aGFuZCBhbmQgZXhwbGljaXQuXG4gICAgbGV0IHgyIDo9IDEwO1xuICAgIGxldCBwMiA6PSBQb2ludCB7IHggPSB4MiwgeSA9IDIwIH07XG4gICAgYXNzZXJ0KHAyLnggPT0gMTApO1xuICAgIGFzc2VydChwMi55ID09IDIwKTtcblxuICAgIC8vIFNob3J0aGFuZCB2aWEgZnVuY3Rpb24gdGhhdCB1c2VzIGl0IGludGVybmFsbHkuXG4gICAgbGV0IHAzIDo9IG1ha2VfcG9pbnQoNSwgNik7XG4gICAgYXNzZXJ0KHAzLnggPT0gNSk7XG4gICAgYXNzZXJ0KHAzLnkgPT0gNik7XG5cbiAgICAvLyBTdHJpbmcgZmllbGQuXG4gICAgbGV0IG5hbWUgOj0gXCJoZWxsb1wiO1xuICAgIGxldCB2YWx1ZSA6PSA0MjtcbiAgICBsZXQgbiA6PSBOYW1lZCB7IG5hbWUsIHZhbHVlIH07XG4gICAgYXNzZXJ0KG4udmFsdWUgPT0gNDIpO1xuICAgIGFzc2VydChuLm5hbWUubGVuKCkgPT0gNSk7XG59XG4ifV0sImhyZWYiOiJodHRwczovL2dpdGh1Yi5jb20vbWV0ZWwtbGFuZy9tZXRlbC1jb3JlL2Jsb2IvdjAuMTMuMC9tZXRlbC1pbnRlcnByZXRlci90ZXN0cy9pbnRlZ3JhdGlvbi9zb3VyY2VzL2V2YWx1YXRvci9zdHJ1Y3RzLzQzX3Nob3J0aGFuZF9maWVsZC5tdGwiLCJuYW1lIjoiNDNfc2hvcnRoYW5kX2ZpZWxkLm10bCJ9"></details>
<!-- rfc.py:fixtures:end -->

##### Dynamic Semantics {#spec.declarations.structs.instantiation-and-field-access.dynamics-1}

A shorthand field `ident` in a struct literal evaluates identically to `ident = ident`. ...

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0115](../../rfcs/4-implemented/rfc-0115-field-initializer-separator.md)_</span>
<!-- rfc.py:origins:end -->

<!-- rfc.py:fixtures:start -->
<p class="rigor-backlink"><em>Tested by</em></p>
<details class="spec-fixture" data-fixture="eyJleHBlY3QiOnsiY29kZSI6bnVsbCwiY29sIjpudWxsLCJjb250YWlucyI6bnVsbCwibGluZSI6bnVsbCwic3RhdHVzIjoic3VjY2VzcyJ9LCJmaWxlcyI6W3sibmFtZSI6IjQzX3Nob3J0aGFuZF9maWVsZC5tdGwiLCJzb3VyY2UiOiIvLyBTaG9ydGhhbmQgZmllbGQgaW5pdGlhbGlzYXRpb246IGBQb2ludCB7IHgsIHkgfWAgZGVzdWdhcnMgdG8gYFBvaW50IHsgeCA9IHgsIHkgPSB5IH1gLlxuXG5zdHJ1Y3QgUG9pbnQgeyB4OiBpNjQsIHk6IGk2NCB9XG5cbnN0cnVjdCBOYW1lZCB7IG5hbWU6IFN0cmluZywgdmFsdWU6IGk2NCB9XG5cbmZ1biBtYWtlX3BvaW50KHg6IGk2NCwgeTogaTY0KSAtPiBQb2ludCB7XG4gICAgUG9pbnQgeyB4LCB5IH1cbn1cblxuZnVuIG1haW4oKSB7XG4gICAgLy8gQmFzaWMgc2hvcnRoYW5kOiBib3RoIGZpZWxkcy5cbiAgICBsZXQgeCA6PSAzO1xuICAgIGxldCB5IDo9IDc7XG4gICAgbGV0IHAgOj0gUG9pbnQgeyB4LCB5IH07XG4gICAgYXNzZXJ0KHAueCA9PSAzKTtcbiAgICBhc3NlcnQocC55ID09IDcpO1xuXG4gICAgLy8gTWl4ZWQ6IHNob3J0aGFuZCBhbmQgZXhwbGljaXQuXG4gICAgbGV0IHgyIDo9IDEwO1xuICAgIGxldCBwMiA6PSBQb2ludCB7IHggPSB4MiwgeSA9IDIwIH07XG4gICAgYXNzZXJ0KHAyLnggPT0gMTApO1xuICAgIGFzc2VydChwMi55ID09IDIwKTtcblxuICAgIC8vIFNob3J0aGFuZCB2aWEgZnVuY3Rpb24gdGhhdCB1c2VzIGl0IGludGVybmFsbHkuXG4gICAgbGV0IHAzIDo9IG1ha2VfcG9pbnQoNSwgNik7XG4gICAgYXNzZXJ0KHAzLnggPT0gNSk7XG4gICAgYXNzZXJ0KHAzLnkgPT0gNik7XG5cbiAgICAvLyBTdHJpbmcgZmllbGQuXG4gICAgbGV0IG5hbWUgOj0gXCJoZWxsb1wiO1xuICAgIGxldCB2YWx1ZSA6PSA0MjtcbiAgICBsZXQgbiA6PSBOYW1lZCB7IG5hbWUsIHZhbHVlIH07XG4gICAgYXNzZXJ0KG4udmFsdWUgPT0gNDIpO1xuICAgIGFzc2VydChuLm5hbWUubGVuKCkgPT0gNSk7XG59XG4ifV0sImhyZWYiOiJodHRwczovL2dpdGh1Yi5jb20vbWV0ZWwtbGFuZy9tZXRlbC1jb3JlL2Jsb2IvdjAuMTMuMC9tZXRlbC1pbnRlcnByZXRlci90ZXN0cy9pbnRlZ3JhdGlvbi9zb3VyY2VzL2V2YWx1YXRvci9zdHJ1Y3RzLzQzX3Nob3J0aGFuZF9maWVsZC5tdGwiLCJuYW1lIjoiNDNfc2hvcnRoYW5kX2ZpZWxkLm10bCJ9"></details>
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

### Link prose to the rule it restates

Whenever a Legality Rule or Dynamic Semantics block restates a claim the prose already
makes, link the prose words into the block's id — a normal part of writing or editing a
section, not a special case reserved for a few sections judged to need it:

```markdown
Zero-field structs [may omit braces entirely](#spec.declarations.structs.instantiation-and-field-access.legality-2).
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
