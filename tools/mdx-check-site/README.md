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

Concretely: `getting-started`, `reference`, and `release-notes`
go under `versioned_docs/version-0.0.0-check/`, with a placeholder
`versioned_sidebars/version-0.0.0-check-sidebars.json` (`{}`) and
`versions.json` (`["0.0.0-check"]`). `blog` goes under `docs/blog` instead --
the blog plugin isn't part of docs versioning at all, so it isn't affected by any of
this and builds the same way regardless.

## What it checks, and what it deliberately doesn't

Builds exactly the four content directories `metel-website` actually publishes
(`blog`, `getting-started`, `reference`, `release-notes` — `rfcs/` is excluded here
too, matching `metel-website`'s own config, since it isn't public-facing yet). Link
validation (`onBrokenLinks`/`onBrokenAnchors`) is turned off on purpose: that's a
different, separately covered concern, and this check exists specifically for
MDX-compile failures. A broken link failing this job would cry wolf on something
else's problem.

Config here (`markdown.format: 'detect'`, `future.v4`, the docs/blog paths, the
`rfcs/**` exclude) is adapted directly from `metel-website/docusaurus.config.ts`
rather than hand-rolled, for the same reason the versioned-docs structure above
matters -- an earlier hand-rolled version silently missed a known-bad file for a
config-shape reason that took real effort to isolate. Keep this file's `presets`
block in sync if `metel-website`'s own docs/blog/markdown config ever changes.
Cosmetic settings (theme, navbar, footer, site metadata) are left at whatever's
simplest, since they don't affect whether content compiles.

## Running it locally

```bash
mkdir -p versioned_docs/version-0.0.0-check docs/blog
cp -r ../../getting-started ../../reference ../../release-notes \
    versioned_docs/version-0.0.0-check/
cp -r ../../blog/* docs/blog/
npm install
npm run build
```

The CI workflow (`.github/workflows/check-mdx.yml`) does this same copy + build on
every PR.
