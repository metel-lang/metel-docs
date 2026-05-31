# metel-docs

Shared Metel documentation repository.

This repository is intended to be used as a submodule in:

- `metel`
- `metel-website`

Authoritative layout:

- `public/getting-started/`: entry points and example-driven introductory docs
- `public/reference/`: the language reference, error codes, and spec sub-sections
- `public/release-notes/`: versioned change logs and release history
- `internal/`: implementation-facing internal docs and RFCs
- `reports/`: design reports and longer-form research notes

The old flat public-docs layout has been split into these buckets so the website can keep the public surface readable without duplicating content.

Migration safety:

- `migration/website-pre-submodule/` preserves the pre-submodule `metel-wiki/docs` working tree snapshot so no in-flight website docs edits are lost during the split.
