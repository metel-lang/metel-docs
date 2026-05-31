# metel-docs

Shared Metel documentation repository.

This repository is intended to be used as a submodule in:

- `metel`
- `metel-website`

Layout:

- `public/`: external language documentation consumed by the website
- `internal/`: implementation-facing internal docs and RFCs
- `reports/`: design reports and longer-form research notes

Initial merge source:

- `metel/docs/public`, `metel/docs/internal`, `metel/docs/reports`
- website-only public docs from `metel-wiki/docs`

For this initial snapshot, overlapping public files were taken from `metel` and website-only pages were added from `metel-wiki`.

Migration safety:

- `migration/website-pre-submodule/` preserves the pre-submodule `metel-wiki/docs` working tree snapshot so no in-flight website docs edits are lost during the split.
