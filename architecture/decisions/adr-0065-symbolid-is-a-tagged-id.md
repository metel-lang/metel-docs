---
id: adr-0065
title: "SymbolId Is a Tagged Id, Not a Number in a Range"
date: '2026-10-22'
status: accepted
relates: adr-0038, adr-0041, adr-0054, adr-0063
implements: metel-core#1546
updated: '2026-10-22'
---

## Context

`SymbolId` is `pub struct SymbolId(pub u32)`. Several allocators share that one number space, and
what a symbol *is* (a builtin, a declaration, an overload definition, a block-local type) is
recovered by asking which numeric range the number falls in.

metel-core#1542 made that safe without changing it. `identity/symbols.rs` now declares six named
ranges, a `const` assertion rejects ranges that overlap or are out of order, each allocator panics at
the end of its range instead of crossing into the next, and the 21 builtins are one `Builtin` enum.
That removed the silent-collision hazard (`LIMIT-NAME-RESOLUTION-003`). It did not remove the
convention: a range is still a rule that the code must keep, and the kind of an id is still read off
its value. One site does so today (`metel-interpreter/src/evaluator/mod.rs`, `id.0 >=
OVERLOAD_SYM_START`).

Engineering Standard 11 names the stronger form, a compiler-enforced type, in which a collision
between kinds cannot be written. This ADR decides whether to take it and what shape it has.

A second problem sits in the same type. Overload-definition ids come from a process-global
`AtomicU32` (`LIMIT-NAME-RESOLUTION-002`), so the value an overload receives depends on what was
compiled earlier in the process and on thread interleaving. ADR-0054 states that two runs over the
same resolved module graph produce identical ids regardless of file iteration order or parallelism;
overload ids do not meet that. The counter is process-wide because the embedded `std::core` overload
table is built once per process (`core_overload_table`, a `OnceLock`) and its ids must be identical in
every module, which a counter that restarts per compilation cannot give. #1546 proposed fixing both
together, because the fix to the second problem is a new kind of id.

## Audit: what depends on the number

Done against `develop` at the merge of #1547. Method is stated so the result can be re-run; what was
*not* checked is stated with it.

| Question | Finding | Method |
|---|---|---|
| Does code branch on the numeric value? | One site: the evaluator's `id.0 >= OVERLOAD_SYM_START`, selecting the error for a missing overload value. | grep for `.0` on `SymbolId`-typed bindings, `OVERLOAD_SYM_START`, `USER_SYM_START` outside `symbols.rs` |
| Does anything depend on `SymbolId`'s ordering? | No. With `PartialOrd, Ord` removed from `SymbolId` and from `BindingId` (the only type whose derive needed it, via `BindingId::Global(SymbolId)`), the whole workspace builds, interpreter and every test target included, except four `sort()` calls on `BindingId` in `identity/tests.rs` (lines 130, 150, 339, 487), which normalise a set of ids before comparing it. No production code and nothing in `metel-interpreter` orders ids. | removed both derives and ran `cargo build --workspace --all-targets --keep-going`, then `cargo build -p metel --all-targets`; reverted |
| Is the number hashed into other ids? | Yes. `InheritedMethodTarget::Nominal(SymbolId)` derives `Hash` and is a `LexicalPath` component, and `LocalId`/`RefId` hash that path. So the `LocalId`s of inherited-default method bodies depend on the numeric `SymbolId` of their nominal target. Declared ids are a declaration's rank in the program's sorted list (`LIMIT-NAME-RESOLUTION-004`), so by that record they shift when a program adds or removes a declaration. The effect on `LocalId` stability was read from the code and the record, **not** demonstrated by an experiment. | read `identity/lexical_path.rs`, `identity/allocate.rs` |
| Who allocates overload ids? | Two sites in `type_checking/overload/mod.rs`: per-module table construction, and the once-per-process core table. | grep `next_overload_symbol` |
| Does every overloaded name have a `Declared` symbol, including across imports? | Yes. The resolver interns every named top-level declaration, `Fun` included, under `(module, name)` and `intern` dedups on that key, so same-named functions in one module share exactly one id and the same name in two modules gets two. A throwaway test (discarded) resolved two modules each defining `f` twice and got `f` = 1000 and `a::f` = 1002, one entry per defining module. An imported overload entry already carries the *declaring* module's ids, and a module that declares its own `fun` of that name shadows imported groups entirely, so a group id is always the defining module's. Overloads are top-level free functions only; impl methods are not in the table. | read `intern_all_symbols`, `decl_any_name`, `build_overload_table`; scratch test |
| Is the resolver's symbol map reachable where the table is built? | In the module-graph path, yes: `check_one_module` holds `names: &ResolvedNames` and passes `Some(&names.symbols)` into `check_impl_with_report`, which builds the table. But `build_overload_table` and `build_table_from_decls` take only declarations and a registry and group by name *string*; the symbols are not passed to them today. The structural id therefore needs `symbols` added to those signatures. The `Option` is `None` only in `check_impl`, which is `#[allow(dead_code)]`. | read `type_checking/mod.rs` |
| What does a larger id cost? | Measured as an upper bound. `SymbolId` widened to a 16-byte, 16-aligned `u128` (larger than the 12-byte enum) needed only five casts inside `symbols.rs` and the evaluator's one range test to compile. On a generated program of 1,200 structs, 2,400 ordinary functions, 80 overload definitions (40 overloaded names) and about 880 calls (`metel`, debug build, check plus run), peak memory over three runs each was 138.3 MB (137.9, 138.2, 138.8) against 140.0 MB (139.5, 140.1, 140.4): +1.7 MB, about +1.2%, with no change in run time (about 25 s either way). One program and one build profile; the data layout, not the profile, drives this. | `big_symbolid.mtl`; Python `resource.getrusage` on the child |
| How widely is the constructor used? | 47 non-test `SymbolId(…)` construction sites; 48 files mention `SymbolId` at all; tests mint ids by number (`SymbolId(1000)`). | grep |

Three consequences for the decision. The set of code that *interprets* the number is tiny (one range
test; the 16-byte build needed five casts in `symbols.rs` and that one test), so a type that replaces the
number costs mostly mechanical edits, not redesign. The hash dependency means the type's `Hash` is part
of the identity contract, not an implementation detail. And the size is not a reason to hold back.

Still not checked: the `LocalId`-stability effect of the hash dependency was read from the code and
`LIMIT-NAME-RESOLUTION-004`, not reproduced, and nothing pins a literal `LocalId` or `SymbolId` value
outside the tests that were found by the build above (a search for tests asserting a numeric id was not
made beyond that).

## Decision

### 1. `SymbolId` is an enum whose variants are the kinds

```rust
pub enum SymbolId {
    Builtin(Builtin),                          // the #1542 enum; replaces the SYM_* range
    Declared(u32),                             // the name resolver's SymbolTable; ascending
    BlockLocal(u32),                           // the type engine's block-local struct/enum ids
    CoreOverload(u32),                         // index into the embedded std::core overload table
    Overload { group: u32, ordinal: u32 },     // see 3
}
```

Two ids of different kinds cannot be equal because they are different variants. Uniqueness *within*
a kind is a separate property that the kind's allocator provides (see Decision 2). The six ranges, `SymbolRange`,
`ALL_RANGES`, the `const` assertions, `allocate_from`, `allocate_down` and the end-of-range panics are
deleted. Each variant's payload keeps only the limit a `u32` has, which is enforced by a checked
increment in the one allocator that owns the variant. `Declared` is not called `User` because the
resolver also interns the non-builtin `std::core` declarations (`Copy`, `Drop`), and splitting std
from user is a separate question (`LIMIT-NAME-RESOLUTION-004`).

### 2. Payloads are private; one module constructs each variant

`SymbolTable` is the only code that builds `Declared`, `BlockLocalAllocator` is the only code that
builds `BlockLocal`, and the overload module builds the two overload variants through a crate-private
function. Outside those, an id can be compared, hashed, matched and passed, not forged from a number.

Each allocator is responsible for uniqueness within its kind, and the scope of that guarantee is the
scope of the allocator: one `SymbolTable` per resolved graph for `Declared`; the registry chain that
`check_graph` builds in module order for `BlockLocal`, whose allocator `merge_from` carries forward so
a module's first local type does not reuse a dependency's id; one process-global counter for the
temporary `Overload` variant until step 2. Making an allocator and minting from it is public for
`SymbolTable` and `BlockLocalAllocator` (a second table or allocator mints equal ids by construction),
so what the types rule out is forging a specific index, not creating a second allocator. Tests that
minted `SymbolId(1000)` use a `#[cfg(test)]` constructor. Kind tests become matches
(`matches!(id, SymbolId::Overload { .. } | SymbolId::CoreOverload(_))`), and an exhaustive `match` on
`SymbolId` forces a consumer to consider every kind when one is added.

### 3. Overload identity is structural, not counted

An overload definition is identified by the symbol of the overloaded name and its position among that
name's overloads:

- `Overload { group, ordinal }`: `group` is the `Declared` index the resolver already assigns the
  overloaded function's name in that module, `ordinal` its declaration order among the overloads of
  that name. There is no counter, so there is nothing process-global and nothing to reset; a name is
  already unique to its module, so per-module tables cannot collide.
- `CoreOverload(n)`: `n` is the overload's index in the embedded `std::core` declaration order. The
  core table is still built once per process, but its ids no longer depend on a counter's value at the
  moment of first use; they are the same in every process and every compilation.

Construction requires passing the resolver's `symbols` map into `build_overload_table` (it is not an
input today; see the audit). This is the shape ADR-0063 already uses for impl-method bodies ("the resolved method-group symbol and
a definition ordinal within that group"), and it carries the same caveat: reordering overloads of one
name is a structural edit and changes their ids. It fixes `LIMIT-NAME-RESOLUTION-002` and makes
ADR-0054's reproducibility statement true for overloads.

### 4. Ordering and hashing are specified, not incidental

`Hash` is derived and is part of the identity contract: `InheritedMethodTarget::Nominal(SymbolId)`
feeds it into `LocalId`/`RefId` hashes, so a change to the derived hash changes those ids' values
once, at the migration. `PartialOrd` and `Ord` are **not** derived on `SymbolId`, and are removed from
`BindingId` with it: the audit found nothing outside four test sorts that needs them, and an order over
kinds carries no meaning that code should come to rely on. The four test sites compare sets and use a
sorted-by-debug-string or hash-set comparison instead.

### 5. `Declared` is not split into std and user now

A `Std(u32)` variant would promise ids that are stable across programs, and they are not: today they
are ranks in each program's sorted declaration list (`LIMIT-NAME-RESOLUTION-004`). Stability needs the
ids generated from `core.mtl`, which is separate work. Adding the variant later is cheap, because an
exhaustive `match` on `SymbolId` lists every consumer that must handle a new kind. The cost of waiting is
a second one-time shift in the derived `Hash`, and so in the `LocalId` values of inherited-default
bodies; the audit found nothing that persists or pins those values, and ids cannot be persisted
(`LIMIT-RESOLUTION-001`). The split is made in the same change that generates the std ids.

### 6. The overload ordinal is edit-sensitive, and that is accepted

Reordering the overloads of one name changes their ids. This is not a new property: `Declared` ids are a
declaration's rank in the sorted list and already shift when a program adds or removes any declaration,
so an ordinal within one name's overloads is strictly more stable than they are. ADR-0054's guarantee
(the same resolved graph yields the same ids) holds; a reordered source is a different graph. ADR-0063
accepts the same property for impl-method bodies. Deriving the ordinal from parameter types would mean
hashing types that may contain type variables and named types, which brings back collision guards and a
larger id to buy stability nothing needs. If an incremental or caching layer later keys by `SymbolId`
across edits, it should cache on the declaration, not on the id.

## Consequences

**Gained.** A kind collision is not expressible. The numeric ranges and their checks stop being a
maintained invariant. Debug output names the kind (`Declared(1042)`, not `SymbolId(1042)`), which
helps read the `{id:?}` messages the evaluator and `abstract_bodies.rs` already print. Overload ids
become reproducible per graph, closing `LIMIT-NAME-RESOLUTION-002`, and `core_overload_table` stops
depending on call order.

**Cost.** The id grows from 4 to 12 bytes with the structural overload variant (8 without it), in a
type that is a hash key and stored widely. Measured as an upper bound with a 16-byte id, the effect on
peak memory of a large generated program was about +1.2% and none on run time (see the audit). The `SymbolId(n)` constructor disappears from 47 sites and the tests that use
it. The numeric values of `LocalId`/`RefId` for inherited-default bodies change once. Anything that
pins a literal id value in a test changes with it.

**Found by adversarial review (step 1, metel-core#1548) and fixed there.** Two defects survived the
design and the first test run. (1) `allocate_overload` was public and took the caller's counter, so
code outside the crate could mint `Overload(n)` for any `n`; it is crate-private, with `compile_fail`
doctests guarding it. (2) Block-local ids restarted at index 0 in every module, so two modules each
registered a different local type as `BlockLocal(0)` and the later `struct_env.insert` overwrote the
earlier definition in the shared registry. The old numeric ids repeated across modules in the same way,
and no program was observed to give a wrong answer, but the metadata is kept after a block closes for
runtime generic-body reconstruction (#1307), which is exactly the reader that would have found the wrong
entry. `merge_from` now moves the allocator past the one it merges. The lesson recorded here: the enum
rules out a collision between kinds, not between two allocators of one kind, so each allocator's scope
has to be stated and tested.

**Not changed.** `LIMIT-NAME-RESOLUTION-005` (a symbol is a `(module, name)` key, so distinct
declarations such as impl methods with different type arguments can share one id) is a different
problem and is not addressed; a tagged id makes it easier to fix later (a `Method` kind) but does not
fix it. Declared ids are still a rank in the sorted declaration list (`LIMIT-NAME-RESOLUTION-004`).
Overload resolution remains exact-match and compile-time-only (ADR-0038); nothing here moves it toward
runtime dispatch.

## Alternatives considered

**A. Keep the declared, checked ranges (the state after #1542).** Safe, and it costs nothing more. Its
limit is the one this ADR starts from: the kind is read off a value, and the guarantee is a rule the
code keeps. It also leaves `LIMIT-NAME-RESOLUTION-002` open, since the counter is the range's
allocator. Right choice if the migration's cost is judged to outweigh the gain.

**B. A private `u32` with the kind in the high bits and checked constructors.** Keeps the id at 4
bytes and `Copy`, and makes a cross-kind collision unconstructible outside the module. It does not
give an exhaustive `match`, the payload is capped (about 2^28 per kind), and the kind is still decoded
from bits, so it is Alternative A with a better lock. The size measurement did not go badly, so
it is no longer needed as a fallback; it remains the cheaper option if the exhaustive `match` is judged
not worth having.

**C. One newtype per kind (`TypeSymbol`, `FunctionSymbol`, …).** The strongest static typing, since a
function can demand the kind it needs. But most of the 48 files that mention `SymbolId` handle several
kinds uniformly (registries keyed by id, `callee_id`), so they would become generic or enum-typed
anyway; this is Decision 1 spread over more types.

**D. A per-compilation counter for overloads, with `CoreOverload` as a separate variant.** The smaller
change for `LIMIT-NAME-RESOLUTION-002`: `Overload(u32)` from an allocator that restarts per graph.
Reproducible only if the order in which overload tables are built is itself deterministic, which is
one more thing to keep true. Not chosen: the audit found the structural form workable, so the counter's
ordering dependency can be avoided outright.

## Questions raised and how they were settled

Settled by the audit:

1. **Overload identity** is structural `{ group, ordinal }` (Decision 3). Every overloaded name has a
   `Declared` symbol in its defining module, imports carry the declaring module's ids and shadowing is
   total, so the group id cannot collide; the only added work is passing `symbols` to the table builder.
2. **`Ord` is dropped** (Decision 4); only four test sorts used it.
3. **Size does not decide it.** About +1.2% peak memory at a 16-byte upper bound.

Decided after the audit (Decisions 5 and 6):

4. **`Declared` is not split into std and user now.** Revisit with the `core.mtl` id generation.
5. **The edit-sensitive overload ordinal is accepted.**

Nothing is open. A later change to any of these amends this ADR.

## Sequencing

Each step is independently reviewable and leaves the suite green; none is started by this ADR.

0. **Audit** (done, recorded above). It settled the former open questions 1, 2 and 4.
1. **Introduce the enum behind the existing surface.** *Done: metel-core#1546, PR #1548.* `SymbolId` becomes the enum with `Declared`,
   `BlockLocal` and `Builtin`; `USER_SYM_START` and the `SYM_*` constants keep working through
   constructors, the ranges are removed, `Ord` is removed from `SymbolId` and `BindingId` and the four
   test sorts are rewritten, and `Overload`/`CoreOverload` stay a single temporary variant fed by the
   existing counter. Replace the evaluator's range test with a match. Regenerate any test that pinned an
   inherited-default `LocalId` value.
2. **Split the overload ids** per Decision 3. *Done: metel-core#1546, PR #1551.* Pass `symbols` into `build_overload_table`, introduce
   `Overload { group, ordinal }` and `CoreOverload(n)`, delete the process-global counter and close
   `LIMIT-NAME-RESOLUTION-002`.
3. **Retire the range machinery and its tests**, replace them with the tests of the new invariants (no
   cross-kind collision by construction; core overload ids identical across two compilations in one
   process; overload ids identical across two builds of the same graph), and update Engineering
   Standards 2 and 11.
