---
id: LIMIT-NAME-RESOLUTION-003
title: "The SymbolId space is split between three allocators by convention, with no cross-check"
summary: "User, overload and block-local ids share one `u32` split into ranges by convention; nothing guards the boundaries or overflow, and the table's map is public."
scope: "architecture/spec/name-resolution.md#name-resolution"
owner: metel-frontend
discovered_by: "maintainer review of metel-frontend/src/symbols.rs"
disposition: known
review: null
---

## Limitation

`SymbolId` is a `u32` newtype whose range is partitioned by comment
(`symbols.rs`): builtins occupy 1-99, `1000 +` is the name resolver's, and
`0x4000_0000 +` is the overload allocator's. A third allocator, in
`typeinference`, hands block-local struct/enum ids from the *top* of the `u32`
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
- `metel-frontend/src/symbols.rs` (`SymbolTable`, `USER_SYM_START`, `OVERLOAD_SYM_START`)
- `metel-frontend/src/typeinference/mod.rs` (`fresh_local_type_id`)

## Resolution

None yet. Typed allocators (one owner for the whole space, with range checks
and a private `map`) would turn the convention into an invariant.
