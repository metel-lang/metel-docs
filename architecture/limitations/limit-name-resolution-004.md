---
id: LIMIT-NAME-RESOLUTION-004
title: "Builtin SymbolIds are a hard-coded list of 21 names; other std declarations are order-assigned"
summary: "Only 18 builtin types and 3 aspects have fixed ids, kept in Rust beside the `std::core` module file; every other std declaration gets whatever id the load order yields."
scope: "architecture/spec/name-resolution.md#name-resolution"
owner: metel-frontend
discovered_by: "maintainer review of metel-frontend/src/symbols.rs"
disposition: known
review: null
---

## Limitation

`SymbolTable::new` pre-seeds exactly 21 `std::core` names at fixed ids: 18 types
(`boolean`, `String`, `Char`, the sized integers and floats, `List`, `Perhaps`,
`Result`, `Range`, `RangeInclusive`) and 3 aspects (`Display`, `Iterable`,
`From`). The list is Rust constants (`SYM_TYPE_*`, `SYM_ASPECT_*`) plus one
`map.insert` per name. The ranges 19-49, 53-99 and 100-999 are reserved "for
future stdlib types/aspects/expansion" and are unused. Every other `std::core`
declaration, for example `Copy` and `Drop`, is interned by the name resolver
like user code and receives whatever id the module load order produces; code that
needs them looks them up by `(module, name)` (`coherence.rs` does this for
`Copy` and `Drop`).

## Impact

- Builtin identity has two sources of truth: the Rust table here and the
  `std::core` module file (ADR-0039). Adding a std type that the runtime must
  register under a fixed id means editing both.
- The ids of std declarations outside the 21 are stable within a run but depend
  on resolution order, so they cannot be treated as well-known across programs.
- The reserved ranges document an intent that the code does not use.

None of this is observable from a Metel program. It is read from the code, so
there is no reproducing fixture.

## Affects

- `arch.name-resolution.requirement-1`
- `metel-frontend/src/symbols.rs` (`SymbolTable::new`, the `SYM_*` constants)

## Resolution

None yet. Generating the fixed ids from the `std::core` declarations, or
dropping the fixed ids in favour of name lookup everywhere, would remove the
second source of truth.
