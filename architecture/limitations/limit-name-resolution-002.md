---
id: LIMIT-NAME-RESOLUTION-002
title: "Overload SymbolIds come from a process-global counter that is never reset"
summary: "Free-function overload ids are allocated from a static counter shared by every compilation in the process, so their values depend on what was compiled before."
scope: "architecture/spec/name-resolution.md#name-resolution"
owner: metel-frontend
discovered_by: "maintainer review of metel-frontend/src/identity/symbols.rs"
disposition: known
review: null
---

## Limitation

`SymbolTable` allocates declared ids from its own per-table counter, so a
fresh `SymbolTable` restarts at index 0. Overload-definition ids are
different: `type_checking/overload` draws them from
`static NEXT_OVERLOAD_SYM: AtomicU32`, initialised to 0 and advanced by
`allocate_overload` (a compare-exchange loop that panics rather than wraps).
Nothing resets it. Its
own comment gives the reason ("keeps ids unique across the whole graph so the
evaluator's symbol registry never collides"), but the scope is the whole
process, not one compilation.

## Impact

Overload ids are unique but not reproducible: the values a compilation receives
depend on how many overload definitions earlier compilations in the same process
allocated (a test binary, or a long-lived tool that compiles repeatedly), and on
thread interleaving when compilations run in parallel. `SymbolId`s are never
shown to a Metel programmer, so no program behaves differently; the effect is
on anything that would key or snapshot by id. It also means the "stable
`SymbolId`" that `arch.type-construction.requirement-10` says is stamped on a
call is stable within one compilation only. It compounds `LIMIT-RESOLUTION-001`:
these ids could not be persisted or compared across runs even if the rest of
the identity model could.

ADR-0054 states that two runs over the same resolved module graph "produce
identical IDs regardless of file iteration order or parallelism"; overload ids
do not meet that, because the counter is process-wide. (`LocalId`s and the
resolver's own `SymbolId`s do.)

This is read from the code; it is not observable from a Metel program, so there
is no reproducing fixture.

## Affects

- `arch.name-resolution.requirement-1`
- `arch.type-construction.requirement-10`
- `metel-frontend/src/pipeline/type_checking/overload/mod.rs::NEXT_OVERLOAD_SYM`

## Resolution

None yet. A per-compilation allocator (owned by the `SymbolTable`, or by the
overload table's builder) would make the ids reproducible.

metel-core#1542 made the counter safe at the end of its range, and ADR-0065 step 1 (metel-core#1546,
PR #1548) made its ids their own kind (`SymbolId::Overload`), but neither changed its process-global
scope. The embedded `std::core`
overload table is built once per process and its ids must be identical in every module, which is why
a plain per-compilation counter does not work. Splitting that table's ids (deterministic, from
declaration order) from user overload ids (per-graph) is part of the tagged-`SymbolId` proposal in
metel-core#1546.
