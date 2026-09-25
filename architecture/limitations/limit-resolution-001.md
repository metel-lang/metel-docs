---
id: LIMIT-RESOLUTION-001
title: "Resolved-identity model is in-memory only"
summary: "Resolved identities exist only in memory; nothing persists them across processes."
scope: "architecture/spec/resolution.md#resolution"
owner: metel-frontend
discovered_by: "ADR-0054 (2026-09-10 amendment)"
disposition: accepted
review: "revisit once an incremental-compilation or persistent-server design is actually proposed"
---

## Limitation

The resolved-identity model (`ResolutionMap`, the interned identity tables) is
in-memory only for this delivery. On-disk persistence and cross-process
interner stability are explicitly out of scope — stated directly in
ADR-0054's own 2026-09-10 amendment, not inferred.

## Impact

An incremental-compilation or persistent-LSP-server design that wants
identities to survive a process restart cannot rely on this model directly
today; every process re-derives identities from scratch on load.

## Affects

- `arch.resolution.requirement-1`
- `arch.resolution.requirement-2`

<!-- limit.py:markers:start -->
- [`metel-frontend/src/identity.rs::ResolutionMap`](https://github.com/metel-lang/metel-core/blob/482a47de2a50db592c02804b14155c2310a76bb5/metel-frontend/src/identity.rs#L237)
<!-- limit.py:markers:end -->

## Resolution

None yet. ADR-0054 frames this as a deliberate, cheap-now/expensive-later
sequencing choice, not an oversight — revisit once a concrete incremental
or persistent-server consumer exists.
