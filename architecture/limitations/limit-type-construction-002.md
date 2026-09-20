---
id: LIMIT-TYPE-CONSTRUCTION-002
title: "Overload sets are not exportable across modules"
summary: "Overload sets are seeded by two different mechanisms; exporting them across modules (METEL-188) is future work."
scope: "architecture/spec/type-construction.md#type-construction"
owner: metel-frontend
discovered_by: "ADR-0038"
disposition: planned
review: null
---

## Limitation

An "exportable overload sets" mechanism — overloads carried in
`GlobalExports`, resolved through ordinary imports like any other
declaration — is future work, tracked as METEL-188. Today the graph-import
path and the single-program path (which performs no imports) seed overload
sets through two different mechanisms rather than one shared one, because
the shared mechanism doesn't exist yet.

## Impact

A module cannot re-export or extend another module's overload set through
an ordinary import; only the declaring module's own resolution can dispatch
into it by `SymbolId`.

## Affects

- `arch.type-construction.requirement-1` (`GlobalExports`)
- `arch.name-resolution.requirement-1` (`SymbolId` assignment for
  overloaded declarations)

## Resolution

None yet — tracked as METEL-188. If it lands, ADR-0038 states the
graph-path seeding becomes an ordinary import and the single-program path
keeps its existing seeding unchanged.
