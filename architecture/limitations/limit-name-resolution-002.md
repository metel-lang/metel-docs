---
id: LIMIT-NAME-RESOLUTION-002
title: "Overload SymbolIds come from a process-global counter that is never reset"
summary: "Free-function overload ids are allocated from a static counter shared by every compilation in the process, so their values depend on what was compiled before."
scope: "architecture/spec/name-resolution.md#name-resolution"
owner: metel-frontend
discovered_by: "maintainer review of metel-frontend/src/symbols.rs"
disposition: known
review: null
---

## Limitation

`SymbolTable` allocates user declarations from its own per-table counter, so a
fresh `SymbolTable` restarts at `USER_SYM_START`. Overload-definition ids are
different: `typechecker/overload.rs` draws them from
`static NEXT_OVERLOAD_SYM: AtomicU32`, initialised to `OVERLOAD_SYM_START`
(`0x4000_0000`) and advanced with a `Relaxed` `fetch_add`. Nothing resets it. Its
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
- [`metel-frontend/src/typechecker/overload.rs::NEXT_OVERLOAD_SYM`](https://github.com/metel-lang/metel-core/blob/4155d94ccbc5b1657799f3537515610f3bb139c3/metel-frontend/src/typechecker/overload.rs#L35)

<!-- limit.py:markers:start -->
- [`metel-frontend/src/typechecker/overload.rs::NEXT_OVERLOAD_SYM`](https://github.com/metel-lang/metel-core/blob/4155d94ccbc5b1657799f3537515610f3bb139c3/metel-frontend/src/typechecker/overload.rs#L34)
<!-- limit.py:markers:end -->

## Resolution

None yet. A per-compilation allocator (owned by the `SymbolTable`, or by the
overload table's builder) would make the ids reproducible.
