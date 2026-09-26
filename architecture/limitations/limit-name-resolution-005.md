---
id: LIMIT-NAME-RESOLUTION-005
title: "Symbol identity is a (module, name-string) key, so distinct declarations can share one SymbolId"
summary: "`ResolvedNames.symbols` keys ids by module path and a name string: every declaration kind shares that key space, and a method's key drops its impl's type arguments, so different impls collide."
scope: "architecture/spec/name-resolution.md#name-resolution"
owner: metel-frontend
discovered_by: "maintainer review of metel-frontend/src/identity/symbols.rs and `ResolvedNames.symbols`; reproduced as metel-core#1228 and #1229"
disposition: known
review: null
---

## Limitation

The canonical symbol table, exposed as `pub symbols: HashMap<(Vec<String>,
String), SymbolId>` on `ResolvedNames` (a copy of `SymbolTable::map`), maps a
module path and a **name string** to an id. Anything that maps to the same key
gets the same `SymbolId`, and `intern_all_symbols` does not check for a clash:

1. **One key space for every declaration kind.** Functions, structs, enums,
   aspects, `let`/`mut` globals and type aliases are keyed by their bare name
   (`decl_any_name`). A struct and a function both called `Foo` in one module
   share an id, and `definitions.entry(id).or_insert(span)` keeps only the first
   declaration's span, so a second declaration is invisible to goto-definition.
   I found no runtime misbehaviour for this pair (a struct `Foo` and `fun Foo`,
   used locally and through an import, both behave correctly): the registries
   that consume the id happen to be per-kind.
2. **A method's key drops its impl's type arguments.** `method_symbol_name`
   builds `Target::Aspect::method` (or `Target::method`) from the target's *base
   name*. `extend W<i64>: Tag { fun t … }` and `extend W<String>: Tag { fun t … }`
   both produce `W::Tag::t`, so both methods receive one `SymbolId` and the
   id-keyed method registry keeps whichever was registered last.

3. **Methods are not overloaded, so a repeated name collides even inside one
   impl.** Two methods called `m` in one `extend S` block, whatever their
   parameter types, share `S::m` and one id; the later definition replaces the
   earlier. Free functions are different: each overloaded *definition* gets its
   own id from the overload allocator (`LIMIT-NAME-RESOLUTION-002`), and only the
   bare *name* shares one table entry.

## Impact

Cases 2 and 3 are silent wrong results, reproduced against current `develop`.
Case 2: with the two impls above, `W { v = 1 }.t()` and `W { v = "s" }.t()` both
return the *last* impl's value, and swapping the blocks swaps the answer (also
for inherent `extend` blocks and through a generic bound); coherence accepts the
program (`metel-core#1228`). Case 3: `extend S { fun m(&self, x: i64) …; fun
m(&self, x: String) … }` is accepted and only the `String` method exists
(`s.m(5)` then fails to typecheck), and two `m()` methods with identical
signatures are accepted with no duplicate error, the second running (free
functions get `T0011` for the same mistake; `metel-core#1229`). Case 1 has no
observed runtime effect today but is the same weakness: identity is a string
key, not the declaration.

## Affects

- `arch.name-resolution.requirement-1`
- `arch.resolution.requirement-1`
- [`metel-frontend/src/pipeline/name_resolution/name_resolver.rs::intern_all_symbols`](https://github.com/metel-lang/metel-core/blob/006a9aafdcb4bc9c7328ad882c08d32737058a51/metel-frontend/src/pipeline/name_resolution/name_resolver.rs#L336)
- [`metel-frontend/src/pipeline/name_resolution/name_resolver.rs::decl_any_name`](https://github.com/metel-lang/metel-core/blob/006a9aafdcb4bc9c7328ad882c08d32737058a51/metel-frontend/src/pipeline/name_resolution/name_resolver.rs#L421)
- [`metel-frontend/src/pipeline/name_resolution/name_resolver.rs::method_symbol_name`](https://github.com/metel-lang/metel-core/blob/006a9aafdcb4bc9c7328ad882c08d32737058a51/metel-frontend/src/pipeline/name_resolution/name_resolver.rs#L255)
- `metel-frontend/src/identity/allocate.rs` (method-symbol lookup)

<!-- limit.py:markers:start -->
- [`metel-frontend/src/pipeline/name_resolution/name_resolver.rs::decl_any_name`](https://github.com/metel-lang/metel-core/blob/006a9aafdcb4bc9c7328ad882c08d32737058a51/metel-frontend/src/pipeline/name_resolution/name_resolver.rs#L420)
- [`metel-frontend/src/pipeline/name_resolution/name_resolver.rs::intern_all_symbols`](https://github.com/metel-lang/metel-core/blob/006a9aafdcb4bc9c7328ad882c08d32737058a51/metel-frontend/src/pipeline/name_resolution/name_resolver.rs#L335)
- [`metel-frontend/src/pipeline/name_resolution/name_resolver.rs::method_symbol_name`](https://github.com/metel-lang/metel-core/blob/006a9aafdcb4bc9c7328ad882c08d32737058a51/metel-frontend/src/pipeline/name_resolution/name_resolver.rs#L254)
<!-- limit.py:markers:end -->

## Resolution

None yet; the bugs are `metel-core#1228` and `metel-core#1229`. The fix is to key a method by its
declaration (for example the impl's position or a canonical form of its target
type including arguments) and to make `intern_all_symbols` reject or
disambiguate two declarations that map to one key.
