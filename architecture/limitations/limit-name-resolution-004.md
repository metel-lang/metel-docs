---
id: LIMIT-NAME-RESOLUTION-004
title: "Builtin SymbolIds are a hard-coded list of 21 names; other std declarations are numbered per program"
summary: "Only 18 builtin types and 3 aspects have fixed ids, kept in Rust beside the `std::core` module file; every other std declaration gets an id from a per-program sorted pass."
scope: "architecture/spec/name-resolution.md#name-resolution"
owner: metel-frontend
discovered_by: "maintainer review of metel-frontend/src/identity/symbols.rs"
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
like user code. `intern_all_symbols` sorts every declaration by `(module path,
name)` before interning (metel-core#1129), so an id does not depend on the
order modules were loaded; but it is the declaration's rank in that sorted list,
so it shifts whenever a program adds or removes a declaration. Code that needs
these std items looks them up by `(module, name)` (`coherence.rs` does this for
`Copy` and `Drop`).

## Impact

- Builtin identity has two sources of truth: the Rust table here and the
  `std::core` module file (ADR-0039). Adding a std type that the runtime must
  register under a fixed id means editing both.
- The ids of std declarations outside the 21 are stable for a given program
  whatever the load order, but they are ranks in that program's sorted
  declaration list, so they cannot be treated as well-known across programs.
- The reserved ranges document an intent that the code does not use.

None of this is observable from a Metel program. It is read from the code, so
there is no reproducing fixture.

## Affects

- `arch.name-resolution.requirement-1`
- `metel-frontend/src/identity/symbols.rs` (`SymbolTable::new`, the `SYM_*` constants)

<!-- limit.py:markers:start -->
- [`metel-frontend/src/identity/symbols.rs::new`](https://github.com/metel-lang/metel-core/blob/482a47de2a50db592c02804b14155c2310a76bb5/metel-frontend/src/identity/symbols.rs#L81)
<!-- limit.py:markers:end -->

## Resolution

None yet. Generating the fixed ids from the `std::core` declarations, or
dropping the fixed ids in favour of name lookup everywhere, would remove the
second source of truth.
