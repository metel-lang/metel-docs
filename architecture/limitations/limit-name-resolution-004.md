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

## Resolution

Narrowed by metel-core#1542; the record stays open. The 21 builtins are now one `Builtin` enum,
declared once by a `builtins!` macro (variant, fixed id, `std::core` name, kind); its discriminants
are the ids, the `SYM_*` constants are aliases of them, and `SymbolTable::new` and the evaluator's two
lookups read from the enum, so the three hand-kept copies are one and a duplicate id does not compile.
A test checks that each builtin is either declared in the embedded `std::core` or one of the 15
intrinsic types (not both, not neither), so the enum and `core.mtl` can no longer drift unnoticed.

Still open: the ids are still hand-numbered in the macro list (not generated from the `std::core`
declarations), the reserved ranges 19-49, 53-99 and 100-999 are still unused, and every other std
declaration is still numbered per program from the sorted declaration list. Dropping the fixed ids in
favour of name lookup everywhere, or generating them, would close it.
