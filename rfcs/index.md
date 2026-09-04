---
title: "Design"
---

# Design

Every non-trivial change to Metel goes through an RFC (Request for Comments) before it
ships — a written proposal covering the motivation, the design, and the alternatives
considered, not just the final decision. This section publishes them.

An RFC moves through a fixed lifecycle:

```
0-draft → 1-under-review → 2-accepted → 3-integrated → 4-implemented
                                                ↘
                                          5-superseded / 6-refused (from any stage)
```

Only RFCs that have reached **Integrated** (merged into the language specification) or
**Implemented** (shipped) are published here, along with **Superseded** ones kept for
historical record. Earlier stages (draft, under review, accepted) aren't published yet —
the design can still change meaningfully at those stages, and a public RFC id is
permanent once minted.

- **Integrated** — the design is settled and already part of the spec.
- **Implemented** — settled, in the spec, and shipped in a release.
- **Superseded** — replaced by a later RFC; kept for context on how a decision evolved.

Use the sidebar to browse by category.
