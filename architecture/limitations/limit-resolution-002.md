---
id: LIMIT-RESOLUTION-002
title: "Inference-time type lookup falls back to a name-approximate, cross-module search"
summary: "Inference falls back to a name-based, cross-module type lookup where the declaration id is missing, which can confuse same-named types."
scope: "architecture/spec/resolution.md#resolution"
owner: metel-frontend
discovered_by: "metel-core#1216 limitation analysis; `typeinference/mod.rs` `resolve_type_key_broad`"
disposition: known
review: null
---

## Limitation

The typed IR does not carry a declaration's `SymbolId` on every type spelling
that inference and the checks around it see. Where a value's `Type::Named`
spelling has no reliable module context (for example a value that arrived
through a function return), `TypeDefinitionRegistry::resolve_type_key_broad`
accepts "a bare declared name from *any* module" as a last resort. About
twenty call sites use it: field access and visibility checks, enum info,
method and scheme lookup, and constraint-solving hooks. Its own comment says
this is the pre-#1060 name-keyed behaviour, kept "until the id rides on the
typed node" and cites `metel-core#1052`, which is now closed; the id has not
yet been threaded through these sites.

## Impact

Two modules that declare a type with the same name can be confused. Reproduced
against current `develop`: with `a::Item { x }` and `b::Item { y }`, field
access on a value returned from `a::make()` fails with `T0003` (`no field `x`
on `Item``) once `b` is also imported, while the same program passes when only
`a` is imported. The symptom is tracked as `metel-core#1222`.

This does not contradict `arch.resolution.requirement-1`, which is scoped to
phases *after* inference has solved a body and the resolution is frozen; the
fallback lives in the inference-time registry, before that freeze.

## Affects

- `arch.resolution.requirement-1`
- [`metel-frontend/src/typeinference/mod.rs::resolve_type_key_broad`](https://github.com/metel-lang/metel-core/blob/2aa2c5729e26ccba73bcc69fe338f0941ffc4966/metel-frontend/src/typeinference/mod.rs#L2383)

## Resolution

None yet. Removing the fallback means carrying the declaration id on the typed
IR's type spellings; the user-visible bug is `metel-core#1222`.
