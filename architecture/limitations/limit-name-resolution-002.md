---
id: LIMIT-NAME-RESOLUTION-002
title: "Overload SymbolIds come from a process-global counter that is never reset"
summary: "Free-function overload ids are allocated from a static counter shared by every compilation in the process, so their values depend on what was compiled before."
scope: "architecture/spec/name-resolution.md#name-resolution"
owner: metel-frontend
discovered_by: "maintainer review of metel-frontend/src/identity/symbols.rs"
disposition: resolved
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
- `metel-frontend/src/pipeline/type_checking/overload/mod.rs::OverloadIds`

## Resolution

Resolved by ADR-0065 step 2 (metel-core#1546, PR #1551). There is no counter any more, so there is
nothing process-global to reset. An overload definition's id is derived from the program:

- in a user module, `SymbolId::Overload { group, ordinal }`: `group` is the overloaded name's
  `Declared` symbol in the module that defines it (the table builder now takes the resolver's
  `symbols`), `ordinal` the definition's position among that name's overloads in source order. The id
  is a function of those two values, so the same program is numbered the same way however many times it
  is compiled, and two modules that overload one name get different ids because their groups differ;
- in the embedded `std::core`, `SymbolId::CoreOverload(n)`: `n` is the definition's index in the core
  table's declaration order. The table is still built once per process (every module must see the same
  ids), but its ids no longer depend on a counter's value at first use. Groups are walked in first-seen
  order, not `HashMap` order, so `n` does not depend on a per-process hash seed.

Exit evidence: `overload_ids_do_not_depend_on_what_was_compiled_earlier_in_the_process`
(`type_checking/tests.rs`) compiles a multi-module program, then an unrelated one, then the first again,
and requires identical overload ids in every module's table. Applied alone to the pre-change code it fails
with "the same program was numbered differently the second time it was compiled", which is the behaviour
this record described. Further tests in `overload/tests.rs` cover source-position numbering, distinct ids
across modules, dense in-order core ids that are identical on a rebuild, and an internal error for an
overloaded name with no resolved symbol.

What this fixes of ADR-0054's promise: two runs over the same resolved module graph now produce
identical overload ids too. A consequence worth knowing: reordering the overloads of one name changes
their ids, as reordering impl variants does under ADR-0063 (ADR-0065 Decision 6).
