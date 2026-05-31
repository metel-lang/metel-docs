# metel-docs

Shared Metel documentation repository.

This repository is intended to be used as a submodule in:

- `metel`
- `metel-website`

Authoritative layout:

- `public/`: external language documentation published by the website
- `internal/`: implementation-facing internal docs and RFCs
- `reports/`: design reports and longer-form research notes

The top-level docs that used to mirror `public/` have been removed so there is a single source of truth for the public docs tree.

Migration safety:

- `migration/website-pre-submodule/` preserves the pre-submodule `metel-wiki/docs` working tree snapshot so no in-flight website docs edits are lost during the split.
