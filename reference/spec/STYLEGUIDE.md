# Spec Styleguide

A practical reference for writing or editing anything in `public/reference/spec/` (and,
where noted, `public/reference/error-codes.md`). Covers general spec prose, code
examples, and the Legality Rule / Dynamic Semantics rigor-block mechanism specifically.

This directory is published: it's mirrored out of this repo's `public/` into the public
`metel-docs` repo and from there into the language website. Nothing outside `public/`
(this repo's `architecture/`, `internal/`, `reports/`) makes that trip — don't link to
those from anything in here, the link will be dead on the real site even though it
resolves fine in this repo. Reference an ADR or an internal report by name/number in
plain text instead of a markdown link.

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

##### Dynamic Semantics {#spec.declarations.structs.instantiation-and-field-access.dynamics-1}

A shorthand field `ident` in a struct literal evaluates identically to `ident = ident`. ...

<!-- rfc.py:origins:start -->
<span class="rigor-backlink">_Referenced by: [rfc-0115](../../rfcs/4-implemented/rfc-0115-field-initializer-separator.md)_</span>
<!-- rfc.py:origins:end -->

</details>

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
<!-- rfc.py:exemption kind="blocked" ref="metel-core#775" reason="Argument unification against an explicitly pinned type parameter is not yet implemented: instantiate_scheme_with_turbofish never receives the call's actual argument types." -->
```

- `kind` — `untestable` (permanent, structural: no program could ever violate it),
  `blocked` (testable in principle, blocked on a real dependency), or `elsewhere` (tested,
  but not via an `.mtl` fixture — e.g. a Rust unit test).
- `reason` — required, free text.
- `ref` — required for `blocked`/`elsewhere`: an RFC id (`rfc-0121`) or a GitHub issue
  (`metel-core#775`). A `blocked` ref gets checked: an RFC-shaped one locally against its
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

## Verifying before you ship

- `rfc.py check` (`public/rfcs/tools/rfc.py`) — structural checks (id grammar, drift,
  exemption well-formedness, the live issue-ref check) always run. Fixture-coverage
  counting additionally needs `metel-interpreter/tests` reachable
  (`METEL_CORE_ROOT=/path/to/metel-core`, or run from inside a metel-core checkout).
- `rfc.py index --write-spec-origins` after touching a block's text, its citing RFC's
  `coverage:` frontmatter, or its exemption trigger.
- `rfc.py index --check-drift` — confirms every generated slot matches what regeneration
  would produce.
- A real `docusaurus build` (`tools/mdx-check-site/`, see its own README) — confirms an
  anchor or cross-reference actually renders and resolves, not just that the markdown
  parses. Catches a dead link before a reader does.
- If a claim touches real interpreter behavior, run it: build `metel-core` and try the
  program the claim describes. Don't cite a fixture, or write a claim, you haven't
  watched pass yourself.
