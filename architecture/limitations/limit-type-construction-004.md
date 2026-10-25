---
id: LIMIT-TYPE-CONSTRUCTION-004
title: "Construction finds module-level values and their schemes by name"
summary: "Module-level values and the inference SchemeEnv are keyed by spelling in construction; everything a binding names is keyed by identity."
scope: "architecture/spec/type-construction.md#type-construction"
owner: metel-frontend
discovered_by: "metel-core#1570 step 3 scoping (corpus measurement of SchemeEnv keys)"
disposition: known
review: null
---

## Limitation

Construction resolves locals, nested generic functions, struct fields, types, aspects and
top-level declarations by identity. Module-level values (functions, builtins, top-level
`let`/`var`) are still found by name: `ConstructCtx::module_values` and `module_fn_decls` are seeded
from the inference output `SchemeEnv`, a `HashMap<String, TypeScheme>`, and a callee reads its scheme
from it by spelling. The two maps are exempted in `check_no_semantic_name_lookup.py`'s scan with this
record as the retirement condition.

The blocker is a path callee such as `List::new`: path normalization stamps no symbol on a
`Type::method` path, so the use site has no identity to look the scheme up by. Measured over the
integration corpus, about 15,000 of the `SchemeEnv` entries built are such joined keys, against
imported names (~58%) and `std::core` items (~40%), which can carry an id from where they are
produced.

## Impact

Internal. A module-level value whose spelling is shadowed or aliased is resolved correctly today by
the name resolver's own tables before construction; the name-keyed read happens after that, on a
spelling the resolver already accepted.

## Affects

- `arch.type-construction.requirement-13`
- `metel-frontend/src/pipeline/type_checking/construction/mod.rs` (`module_values`, `module_fn_decls`, `lookup_module`)

## Resolution

None yet; metel-core#1604 (not yet scheduled) is the work: path normalization stamps the impl-method symbol on
`Type::method` paths, the inference output carries an origin `BindingId`, and the two maps go.
