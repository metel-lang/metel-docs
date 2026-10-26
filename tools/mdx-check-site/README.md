# mdx-check-site

Not a real website. A minimal Docusaurus scaffold, checked in so CI can run a real
`docusaurus build` against ``'s current content on every PR, without needing
`metel-website`'s own (private) repo or any of its secrets.

## Why this exists

`tools/check_doc_examples.py` (metel-core) verifies that the *Metel code* inside a
` ```metel ` fence actually runs. It has no idea whether the *document* around that
fence is valid input to the thing that actually renders it. Two bugs slipped through
as a result, both invisible until `metel-website` tried to build a real release:

- An HTML comment (`<!-- doc-example: ... -->`) in a `.mdx` tutorial — MDX parses
  `<...>` as JSX, and `<!--` isn't valid JSX at all.
- A marker's own `reason=` text containing a literal `/* ... */` — this one is
  stranger: MDX's own compile step succeeds, producing JS with the comment's text
  spliced in as a JS comment, and it's *that* JS that fails to parse (the nested
  `/*`/`*/` closes and reopens the comment early). A plain MDX-compile check misses
  this; only a real Docusaurus build (which bundles the compiled output through
  webpack) catches it.

## The non-obvious part: content must go under `versioned_docs/`, not `docs/`

Found the hard way verifying this checker actually works: Docusaurus's docs plugin
compiles content placed directly under `docs/` (the "current version" path) more
leniently than content under `versioned_docs/version-X/` -- the exact `<!-- -->`
tutorial bug above builds *successfully* under `docs/` and only fails under
`versioned_docs/`, for a reason never fully isolated in Docusaurus's own docs
plugin. `metel-website` sets `includeCurrentVersion: false` and only ever builds
through `versioned_docs/`, so that's the path that has to match here for this check
to mean anything -- confirmed by deliberately reintroducing both fixed bugs and
checking this scaffold actually reports the same failure `metel-website`'s own build
did before they were fixed.

Concretely: `getting-started`, `reference`, `release-notes`, `architecture`, `operations`, `status` and `rfcs`
go under `versioned_docs/version-0.0.0-check/`, with a placeholder
`versioned_sidebars/version-0.0.0-check-sidebars.json` (`{}`) and
`versions.json` (`["0.0.0-check"]`). `blog` goes under `docs/blog` instead --
the blog plugin isn't part of docs versioning at all, so it isn't affected by any of
this and builds the same way regardless.

## What it checks, and what it deliberately doesn't

It builds the content `metel-website` publishes (`blog`, `getting-started`, `reference`,
`release-notes`, `architecture`, `operations`, `status` and the public stages of `rfcs`) with the
website's own `docs.exclude` list, so a page the real site leaves out is left out here too, and
drafts are excluded as in a production build. Two things fail the job:

- **MDX that does not compile**, the original purpose (the two bugs found cutting v0.12.1).
- **A broken link** (`onBrokenLinks: "throw"`, as on the real site; metel-core#698). The v0.14.0
  staging deploy failed twice on exactly this: a published page linking a `draft: true` page, and
  links into RFC stages the site does not publish. Neither was visible here while links were
  ignored. Both are now reproduced: a page linking a draft, and a page linking
  `rfcs/0-draft/...`, each fail the build with the source page named.

The stub `src/pages/index.md` exists only so the layout's home link (`/`) resolves, as it does on
the real site, which has a landing page.

### What it does not catch

It is derived from `metel-website/docusaurus.config.ts` and omits, on purpose, everything that
does not decide whether content compiles or links resolve: the theme and prism customisation, the
navbar and footer, `sidebars.ts`, the `raw-mtl-loader` plugin, and **every remark and rehype plugin**
of the website (the architecture, spec-marker, error-code-link and table plugins). So it cannot see:

- a link that a website plugin *creates* or *rewrites* and that is broken (the error-code and
  spec-xref links), or a plugin that throws on content it does not understand;
- a `sidebars.ts` entry that names a page which does not exist, or a published page that no
  sidebar lists;
- the footer links, which depend on which snapshots exist (`newestBaseWith`);
- anything about the unreleased view (`INCLUDE_NEXT`) or the Mermaid theme.

Those are caught by `metel-website`'s own build, which is why a docs change that passes here can
still fail the staging deploy. Narrowing that gap means moving a plugin's behaviour into this
scaffold, which is not worth it until a plugin-induced failure actually happens.

### Keeping it in step with the website

The config here (`markdown.format`, `future.v4`, `onBrokenLinks`, the docs paths and the `exclude`
list) is adapted directly from `metel-website/docusaurus.config.ts`, and the `@docusaurus/*`
versions in `package.json` match the website's. `metel-website` is private, so this repository
cannot read it; the check runs the other way: the website's own CI reads this directory (the docs
submodule is public) and fails if `onBrokenLinks`, `markdown.format`, the `exclude` list or the
Docusaurus versions differ (`scripts/check-mdx-site-drift.mjs` there). A change to either side
that is not mirrored fails the website's `plugin-tests` job, not a release.

## Running it locally

```bash
mkdir -p versioned_docs/version-0.0.0-check docs/blog
cp -r ../../getting-started ../../reference ../../release-notes \
    ../../architecture ../../operations ../../rfcs ../../status \
    versioned_docs/version-0.0.0-check/
cp -r ../../blog/. docs/blog/
npm install
npm run build
```

The CI workflow (`.github/workflows/check-mdx.yml`) does this same copy + build on
every PR.
