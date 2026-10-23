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

Cases 2 and 3 no longer give wrong results. Case 2: `W { v = 1 }.t()` and `W { v = "s" }.t()` each
answer from their own impl, for aspect impls, inherent `extend` blocks and through a generic bound
(`metel-core#1228`, checked again at `metel-core#1229`). Case 3: a repeated method name in one
`extend` block, whatever the parameter types, or in one aspect impl or `aspect` declaration, is
`T0034`, as is the same name in two inherent blocks that can apply to one receiver
(`metel-core#1322`, `metel-core#1229`). Neither was fixed by changing the key: `method_symbol_name`
still builds `W::Tag::t` for both impls, so the weakness is structural and shows up wherever a
consumer relies on the id alone. Case 1 has no observed runtime effect: identity is a string key, not
the declaration.

## Affects

- `arch.name-resolution.requirement-1`
- `arch.resolution.requirement-1`
- `metel-frontend/src/pipeline/name_resolution/name_resolver/mod.rs::intern_all_symbols`
- `metel-frontend/src/pipeline/name_resolution/name_resolver/mod.rs::decl_any_name`
- `metel-frontend/src/pipeline/name_resolution/name_resolver/mod.rs::method_symbol_name`
- `metel-frontend/src/identity/allocate.rs` (method-symbol lookup)

## Resolution

None yet for the key. The symptoms were closed one at a time: different instantiations of a generic
type keep separate method behaviour (`metel-core#1228`), and a name defined twice where both definitions
can apply to one receiver is `T0034` (`metel-core#1322` for inherent blocks, `metel-core#1229` for
aspect impls and aspect declarations). What remains is to key a method by its declaration (for example
the impl's position or a canonical form of its target type including arguments) and to make
`intern_all_symbols` reject or disambiguate two declarations that map to one key.
