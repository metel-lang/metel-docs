---
id: LIMIT-NAME-RESOLUTION-003
title: "The SymbolId space is split between three allocators by convention, with no cross-check"
summary: "User, overload and block-local ids share one `u32` split into ranges by convention; nothing guards the boundaries or overflow, and the table's map is public."
scope: "architecture/spec/name-resolution.md#name-resolution"
owner: metel-frontend
discovered_by: "maintainer review of metel-frontend/src/identity/symbols.rs"
disposition: resolved
review: null
---

## Limitation

`SymbolId` is a `u32` newtype whose range is partitioned by comment
(`symbols.rs`): builtins occupy 1-99, `1000 +` is the name resolver's, and
`0x4000_0000 +` is the overload allocator's. A third allocator, in
`type_engine`, hands block-local struct/enum ids from the *top* of the `u32`
space counting down (`fresh_local_type_id`, `saturating_sub`). The three are
independent, and only a unit test asserts one boundary (`second.0 <
OVERLOAD_SYM_START`). At runtime:

- `SymbolTable::intern` advances with `next_id += 1` on a `u32`: it panics on
  overflow in a debug build and wraps in a release build;
- the overload counter's `fetch_add` wraps silently;
- nothing checks that the resolver's range stays below `OVERLOAD_SYM_START` or
  that the two ascending allocators stay clear of the descending one;
- `SymbolTable.map` is a `pub` field, so code outside the type can insert an id
  that bypasses `intern` and the counter entirely.

## Impact

Purely theoretical at realistic sizes: the resolver range would have to reach
about 1.07 billion declarations before it met the overload range. The risk is
structural, not practical: identity uniqueness rests on three allocators
respecting comment-level ranges, so a future change that adds a fourth
allocator, widens a range or inserts into `map` directly has no safety net.
There is no observable symptom, so no reproducing fixture.

## Affects

- `arch.name-resolution.requirement-1`
- `metel-frontend/src/identity/symbols.rs` (`SymbolId`, `SymbolTable`, `BlockLocalAllocator`, `allocate_overload`)
- `metel-frontend/src/pipeline/type_checking/type_engine/mod.rs` (`fresh_local_type_id`)

## Resolution

Resolved by metel-core#1542. `identity/symbols.rs` declares the whole space as six named ranges
(builtin types, builtin aspects, stdlib reserved, user, overload, block-local) and rejects, with a
`const` assertion, ranges that overlap, are empty or are out of order, so editing one into its
neighbour is a compile error. Each allocator now stops at the end of its range instead of crossing
it: `SymbolTable::intern` asserts it stays inside the user range, the overload counter allocates
through `allocate_from` (a checked `fetch_update` that panics instead of wrapping), and the type
engine's descending block-local allocator, which used `saturating_sub` and would have reused one id
forever at the bottom, uses `allocate_down` over its own range (the record's third allocator, now
bounded below as well as above). `SymbolTable.map` is private, with `map()` and `into_map()`. Tests
cover the range check, each allocator's exhaustion and the table seeding.

What #1542 did not do, and what replaced it: it left the kind of a `SymbolId` to be recovered by
inspecting the number (the evaluator tested `id.0 >= OVERLOAD_SYM_START`). ADR-0065 step 1
(metel-core#1546, PR #1548) removed that: `SymbolId` is now an enum whose variants are the kinds
(`Builtin`, `Declared`, `BlockLocal`, `Overload`), so a collision between kinds cannot be written, and
the six ranges, `SymbolRange`, the `const` assertions, `allocate_from` and `allocate_down` described
above were deleted. The payloads are private index types, minted only by `SymbolTable`,
`BlockLocalAllocator` and `allocate_overload`, each of which panics at the end of its index space
instead of wrapping. The evaluator's range test is a match on the `Overload` kind. The `Overload`
kind is still one variant fed by the process-global counter; splitting it is step 2
(`LIMIT-NAME-RESOLUTION-002`).
