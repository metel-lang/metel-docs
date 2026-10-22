---
id: adr-0065
title: "SymbolId Is a Tagged Id, Not a Number in a Range"
date: '2026-10-22'
status: proposed
relates: adr-0038, adr-0041, adr-0054, adr-0063
implements: metel-core#1546
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
| Does anything depend on `SymbolId`'s ordering? | In `metel-frontend`'s library the only consumer of `SymbolId: Ord` is `BindingId`'s own derived `Ord` (`BindingId::Global(SymbolId)`, `identity/mod.rs`). No `BTreeMap`/`BTreeSet` keyed by `SymbolId` and no sort over `SymbolId`s was found. Whether anything sorts `BindingId`s was **not** checked, and the interpreter crate was **not** compiled for this (rustc stopped at the first failing crate). | removed `PartialOrd, Ord` from `SymbolId` and built; reverted |
| Is the number hashed into other ids? | Yes. `InheritedMethodTarget::Nominal(SymbolId)` derives `Hash` and is a `LexicalPath` component, and `LocalId`/`RefId` hash that path. So the `LocalId`s of inherited-default method bodies depend on the numeric `SymbolId` of their nominal target. Declared ids are a declaration's rank in the program's sorted list (`LIMIT-NAME-RESOLUTION-004`), so by that record they shift when a program adds or removes a declaration. The effect on `LocalId` stability was read from the code and the record, **not** demonstrated by an experiment. | read `identity/lexical_path.rs`, `identity/allocate.rs` |
| Who allocates overload ids? | Two sites in `type_checking/overload/mod.rs`: per-module table construction, and the once-per-process core table. | grep `next_overload_symbol` |
| How widely is the constructor used? | 47 non-test `SymbolId(…)` construction sites; 48 files mention `SymbolId` at all; tests mint ids by number (`SymbolId(1000)`). | grep |

Three consequences for the decision. The set of code that *interprets* the number is tiny, so a type
that replaces the number costs mostly mechanical edits, not redesign. The hash dependency means the
type's `Hash` is part of the identity contract, not an implementation detail. And the unchecked items
above are a prerequisite for the migration, not a footnote (see Sequencing).

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

Two kinds cannot collide because they are different variants. The six ranges, `SymbolRange`,
`ALL_RANGES`, the `const` assertions, `allocate_from`, `allocate_down` and the end-of-range panics are
deleted. Each variant's payload keeps only the limit a `u32` has, which is enforced by a checked
increment in the one allocator that owns the variant. `Declared` is not called `User` because the
resolver also interns the non-builtin `std::core` declarations (`Copy`, `Drop`), and splitting std
from user is a separate question (`LIMIT-NAME-RESOLUTION-004`).

### 2. Payloads are private; one module constructs each variant

`SymbolTable` is the only code that builds `Declared`, an allocator owned by the type engine's context
is the only code that builds `BlockLocal`, and the overload module builds the two overload variants.
Outside those, an id can be compared, hashed, matched and passed, not forged from a number. Tests that
minted `SymbolId(1000)` use a `#[cfg(test)]` constructor. Kind tests become matches
(`matches!(id, SymbolId::Overload { .. } | SymbolId::CoreOverload(_))`), and an exhaustive `match` on
`SymbolId` forces a consumer to consider every kind when one is added.

### 3. Overload identity is structural, not counted (recommended; see Open question 1)

An overload definition is identified by the symbol of the overloaded name and its position among that
name's overloads:

- `Overload { group, ordinal }`: `group` is the `Declared` index the resolver already assigns the
  overloaded function's name in that module, `ordinal` its declaration order among the overloads of
  that name. There is no counter, so there is nothing process-global and nothing to reset; a name is
  already unique to its module, so per-module tables cannot collide.
- `CoreOverload(n)`: `n` is the overload's index in the embedded `std::core` declaration order. The
  core table is still built once per process, but its ids no longer depend on a counter's value at the
  moment of first use; they are the same in every process and every compilation.

This is the shape ADR-0063 already uses for impl-method bodies ("the resolved method-group symbol and
a definition ordinal within that group"), and it carries the same caveat: reordering overloads of one
name is a structural edit and changes their ids. It fixes `LIMIT-NAME-RESOLUTION-002` and makes
ADR-0054's reproducibility statement true for overloads.

### 4. Ordering and hashing are specified, not incidental

`Hash` is derived and is part of the identity contract: `InheritedMethodTarget::Nominal(SymbolId)`
feeds it into `LocalId`/`RefId` hashes, so a change to the derived hash changes those ids' values
once, at the migration. `Ord` is kept only while `BindingId` derives it; if no sort over `BindingId`
exists (Sequencing, step 1) both derives are removed, so no code can come to depend on the order of
kinds, which carries no meaning.

## Consequences

**Gained.** A kind collision is not expressible. The numeric ranges and their checks stop being a
maintained invariant. Debug output names the kind (`Declared(1042)`, not `SymbolId(1042)`), which
helps read the `{id:?}` messages the evaluator and `abstract_bodies.rs` already print. Overload ids
become reproducible per graph, closing `LIMIT-NAME-RESOLUTION-002`, and `core_overload_table` stops
depending on call order.

**Cost.** The id grows from 4 to 12 bytes with the structural overload variant (8 without it), in a
type that is a hash key and stored widely; this has not been measured and should be before the
migration is accepted. The `SymbolId(n)` constructor disappears from 47 sites and the tests that use
it. The numeric values of `LocalId`/`RefId` for inherited-default bodies change once. Anything that
pins a literal id value in a test changes with it.

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
from bits, so it is Alternative A with a better lock. It is the credible fallback if the size
measurement in the Cost paragraph goes badly.

**C. One newtype per kind (`TypeSymbol`, `FunctionSymbol`, …).** The strongest static typing, since a
function can demand the kind it needs. But most of the 48 files that mention `SymbolId` handle several
kinds uniformly (registries keyed by id, `callee_id`), so they would become generic or enum-typed
anyway; this is Decision 1 spread over more types.

**D. A per-compilation counter for overloads, with `CoreOverload` as a separate variant.** The smaller
change for `LIMIT-NAME-RESOLUTION-002`: `Overload(u32)` from an allocator that restarts per graph.
Reproducible only if the order in which overload tables are built is itself deterministic, which is
one more thing to keep true. See Open question 1.

## Open questions

1. **Overload identity: structural `{ group, ordinal }` (Decision 3) or a per-graph counter
   `Overload(u32)` (Alternative D)?** Structural has no ordering dependency but needs the overloaded
   name to have a `Declared` symbol in every case, which has not been verified (the resolver's
   `overloaded_names` suggests it does; a module that defines overloads of a name it also imports is the
   case to check) and makes the id 12 bytes. The counter keeps the id at 8 bytes but depends on table
   build order. Recommended: structural, if the check passes.
2. **Is `Ord` kept on `SymbolId`?** Only if something orders `BindingId`s. The audit left that open.
3. **Should `Declared` be split into std and user now?** `LIMIT-NAME-RESOLUTION-004` argues std
   declarations should have stable ids across programs, which a `Std(u32)` variant could give, but that
   is the separate generation-from-`core.mtl` work and is left out here.
4. **Does the size matter?** A measurement of `SymbolId`'s share of a representative compile's memory
   (the type registry and the runtime symbol registry hold the most) decides between Decision 1 as
   written and Alternative B.

## Sequencing

Each step is independently reviewable and leaves the suite green; none is started by this ADR.

1. **Close the unchecked audit items.** Build the whole workspace, interpreter included, with
   `Ord` removed from `SymbolId` and list what breaks; check whether any `BindingId` is sorted;
   check the overloaded-name case in Open question 1; measure the size (Open question 4). This
   settles Open questions 1, 2 and 4 and amends this ADR before any code changes.
2. **Introduce the enum behind the existing surface.** `SymbolId` becomes the enum with `Declared`,
   `BlockLocal` and `Builtin`; `USER_SYM_START` and the `SYM_*` constants keep working through
   constructors, the ranges are removed, and `Overload`/`CoreOverload` stay a single temporary variant
   fed by the existing counter. Regenerate any test that pinned an inherited-default `LocalId` value.
3. **Split the overload ids** per Decision 3 (or Alternative D), delete the process-global counter and
   close `LIMIT-NAME-RESOLUTION-002`.
4. **Retire the range machinery and its tests**, replace them with the tests of the new invariants (no
   cross-kind collision by construction; core overload ids identical across two compilations in one
   process; overload ids identical across two builds of the same graph), and update Engineering
   Standards 2 and 11.
