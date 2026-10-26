---
id: LIMIT-NAME-RESOLUTION-004
title: "Builtin SymbolIds are a hard-coded list of 21 names; other std declarations are numbered per program"
summary: "Only 18 builtin types and 3 aspects have fixed ids, kept in Rust beside the `std::core` module file; every other std declaration gets an id from a per-program sorted pass."
scope: "architecture/spec/name-resolution.md#name-resolution"
owner: metel-frontend
discovered_by: "maintainer review of metel-frontend/src/identity/symbols.rs"
disposition: resolved
review: null
---

## Limitation

`SymbolTable::new` pre-seeds exactly 21 `std::core` names as `Builtin` ids: 18 types
(`boolean`, `String`, `Char`, the sized integers and floats, `List`, `Option`,
`Result`, `Range`, `RangeInclusive`) and 3 aspects (`Display`, `Iterable`,
`From`). The list is the `Builtin` enum, declared once by a macro (variant, `std::core` name,
kind); the `SYM_TYPE_*` and `SYM_ASPECT_*` constants are aliases of its variants. There are no
numbers to keep apart any more (ADR-0065). Every other `std::core`
declaration, for example `Copy` and `Drop`, is interned by the name resolver
like user code. `intern_all_symbols` sorts every declaration by `(module path,
name)` before interning (metel-core#1129), so an id does not depend on the
order modules were loaded; but it is the declaration's rank in that sorted list,
so it shifts whenever a program adds or removes a declaration. Code that needs
these std items looks them up by `(module, name)` (`coherence.rs` does this for
`Copy` and `Drop`).

## Impact

- Builtin identity has two sources of truth: the Rust `Builtin` enum here and the
  `std::core` module file (ADR-0039). Adding a std type that the runtime must
  register under a fixed id means editing both; a test checks that each builtin is
  either declared in `std::core` or one of the intrinsic types, so drift is caught,
  not prevented.
- The ids of std declarations outside the 21 are stable for a given program
  whatever the load order, but they are ranks in that program's sorted
  declaration list, so they cannot be treated as well-known across programs.

None of this is observable from a Metel program. It is read from the code, so
there is no reproducing fixture.

## Affects

- `arch.name-resolution.requirement-1`
- `metel-frontend/src/identity/symbols.rs` (`SymbolTable::new`, `Builtin`, the `SYM_*` constants)

## Resolution

Resolved by metel-core#1542, #1546 (PR #1548) and #1559.

- #1542 and #1546: the 21 builtins are one `Builtin` enum, declared once by a `builtins!` macro (variant,
  `std::core` name, kind); the `SYM_*` constants are aliases of its variants, and `SymbolTable::new` and the
  evaluator's lookups read from the enum. After ADR-0065 step 1 the builtins carry no numbers, so the
  hand-numbered ids and the unused reserved ranges are gone. A test checks that each builtin is either
  declared in the embedded `std::core` or one of the 15 intrinsic types (not both, not neither), so the
  enum and `core.mtl` cannot drift unnoticed.
- #1559: every other std declaration is a `Std` id (ADR-0065 Decision 5), numbered from the embedded
  stdlib alone: the module's position in the embedded table and the declaration's rank among that
  module's own sorted `(namespace, name)` keys. It no longer shifts when a program adds or removes a
  declaration, and it is the same in every program and whichever std modules are loaded. User declarations
  stay `Declared`. Code that needs `Copy` or `Drop` still looks them up by `(module, namespace, name)`,
  which is now stable.

What stays by design: the `Builtin` list is written by hand in Rust. Fifteen of its entries are intrinsic
types (`i64`, `String`, ...) that no `core.mtl` declaration describes, so there is nothing to generate them
from, and the other six are checked against `core.mtl` by the drift test. That is the single place a
builtin is added, and a mismatch fails a test; it is not a limitation of the resolver.
