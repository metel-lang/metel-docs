// Minimal Docusaurus config, purpose-built to catch one thing: does the content
// under  still compile as MDX? See this directory's own README.md for why
// this exists and what it deliberately doesn't check.
//
// Adapted directly from metel-website/docusaurus.config.ts rather than
// hand-rolled from scratch -- an earlier hand-rolled version silently failed to
// reproduce a known-bad file (a stray HTML comment in a .mdx tutorial) that the
// real site's build does reject, for a config-shape reason never fully isolated.
// Copying the real config's docs/markdown/blog options verbatim and only
// stripping cosmetic settings (theme, navbar, footer, site metadata) avoids
// re-introducing that gap. Keep this in sync if metel-website's own
// markdown/docs/blog config ever changes.
const { GlobExcludeDefault } = require("@docusaurus/utils");

/** @type {import('@docusaurus/types').Config} */
module.exports = {
  title: "mdx-check-site",
  url: "http://localhost",
  baseUrl: "/",
  organizationName: "metel-lang",
  projectName: "metel-wiki",
  // Same as metel-website: a broken link fails the build (metel-core#698). The v0.14.0 staging deploy
  // failed twice on exactly this, a published page linking a `draft: true` page and links into RFC
  // stages the site does not publish, and neither was visible here while this was "ignore".
  onBrokenLinks: "throw",
  markdown: {
    format: "detect",
  },
  future: {
    v4: true,
  },
  i18n: {
    defaultLocale: "en",
    locales: ["en"],
  },
  presets: [
    [
      "classic",
      {
        docs: {
          path: "docs",
          includeCurrentVersion: false,
          sidebarPath: false,
          exclude: [
            ...GlobExcludeDefault,
            "rfcs/0-draft/**",
            "rfcs/1-under-review/**",
            "rfcs/2-accepted/**",
            "rfcs/6-refused/**",
            "rfcs/index.md",
            "rfcs/REGISTRY.md",
            "rfcs/PROCESS.md",
            "rfcs/tools/**",
            "rfcs/examples/**",
            "reference/spec/STYLEGUIDE.md",
            "architecture/decisions/**",
            "architecture/reports/**",
            "architecture/tools/**",
          ],
        },
        blog: {
          path: "docs/blog",
          routeBasePath: "blog",
          showReadingTime: true,
        },
        theme: {
          customCss: require.resolve("./src/css/empty.css"),
        },
      },
    ],
  ],
};
