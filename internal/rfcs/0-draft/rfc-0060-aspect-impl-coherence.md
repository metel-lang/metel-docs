---
id: rfc-0060
title: "Aspect Implementation Coherence and the Orphan Rule"
date: '2026-06-10'
status: draft
spec_status: pending
---

## Summary

Define a coherence discipline for aspect implementations so that every
`(aspect, type)` pair has at most one implementation across the whole program,
independent of module load order. This RFC proposes an **orphan rule** (an
`impl Aspect for Type` is permitted only when the aspect or the type is local to
the implementing module), **overlap detection** (two impls of the same aspect
for the same type are a compile error), and a fix to the cross-module type
registry merge that currently drops methods.

---

## Motivation

Metel today places no restriction on where an aspect may be implemented: any
module can write `impl SomeAspect for SomeType` for a type and aspect both
declared elsewhere. There is no coherence or overlap check. This is unsound in
three concrete ways.

### 1. Order-dependent runtime dispatch

Aspect methods are stored in the runtime registry keyed by
`(type_name, aspect_name, method)`. A later registration overwrites an earlier
one (`RuntimeRegistry::register_aspect_method` does `methods.insert(...)`). If
two modules each provide `impl Display for Foo`, the impl that "wins" depends on
the topological order in which modules are registered. The same program can
behave differently depending on import structure.

### 2. The type registry merge silently drops methods

`TypeDefinitionRegistry::merge_from` seeds a module's registry from its
dependencies using `or_insert_with`, keyed by **type name**. `method_scheme_env`
is `HashMap<TypeName, HashMap<MethodName, …>>`. When the current module and a
dependency both have an entry for the same type name — exactly the situation an
orphan impl creates — the merge keeps one module's inner method map and discards
the other's, rather than unioning them. Methods that exist in the program become
invisible to type checking in one of the modules. This is a latent correctness
bug, not merely an ambiguity.

### 3. Collision with `SymbolId` dispatch

Aspect dispatch is migrating to `SymbolId` identity (METEL-152, and the call
dispatch work in METEL-181). Coherence is a precondition for that model: a
`SymbolId` names one declaration, but without an orphan/overlap rule there can be
two equally valid impl methods for the same `(type, aspect, method)`. Identity-
based dispatch cannot disambiguate what the language itself leaves ambiguous.

Most languages with aspect/trait-style abstraction solve this with a coherence
rule. Metel needs an explicit answer before the standard library and
`SymbolId`-keyed dispatch are built on the current incoherent base.

---

## Background: current behaviour

- `impl Aspect for Type` type-checks regardless of where `Type` or `Aspect` is
  declared. `infer_decl`'s `Impl` arm derives the target type name and registers
  methods with no locality check.
- `TypeDefinitionRegistry::register_aspect_impl` keys on `(target, aspect)` and
  pushes; nothing detects a second impl for the same pair.
- `RuntimeRegistry::register_aspect_method` overwrites on a repeated
  `(type, aspect, method)`.
- `merge_from` unions registries by type-name key with `or_insert_with`, which
  does not merge inner method maps.
- The public spec says nothing about where an aspect may be implemented or about
  conflicting implementations.

---

## Design

### 1. Orphan rule

An `impl Aspect for Type` is permitted only if **at least one of** the following
is declared in the same module as the `impl` block:

- the aspect (`Aspect`), or
- the type constructor (`Type` — the struct or enum, ignoring its type
  arguments).

Built-in aspects (`Display`, `From`, `Iterable`) and built-in types
(`i64`, `String`, `List`, `Perhaps`, `Result`, …) count as belonging to
`std::core`. User code therefore may write `impl Display for MyStruct` (type is
local) and `impl MyAspect for i64` (aspect is local), but **not**
`impl Display for i64` (both foreign) — that impl may live only in `std::core`.

A violating impl is a compile-time error (proposed `T0014`, "orphan
implementation").

Rationale: this is the well-established rule that guarantees a module can only
add impls it "owns" one half of, which is sufficient to make global coherence
checkable without whole-program overlap analysis at every site.

### 2. Overlap detection

Two implementations of the same aspect for the same type constructor anywhere in
the program are a compile-time error (proposed `T0015`, "conflicting
implementation"), reported with both impl spans. With the orphan rule in place,
overlap can only occur within a single module or between a module and
`std::core`, so detection is local and cheap.

This RFC's first cut treats the type constructor (e.g. `List`) as the overlap
key and does **not** attempt to allow non-overlapping generic impls such as
`impl Aspect for List<i64>` plus `impl Aspect for List<String>`. Parameterised
overlap (and the negative reasoning it requires) is deferred; see Non-Goals.

### 3. Fix the registry merge

`merge_from` must union per-type method maps rather than keep one wholesale.
Concretely, for `method_env` / `method_scheme_env` / `method_receiver_env`
(maps of `TypeName → MethodName → …`), merging two entries for the same type
must merge the inner maps. With the orphan rule and overlap detection in force,
a method-name collision in that inner merge is itself a coherence violation and
should surface as `T0015` rather than silently picking one.

### 4. Runtime dispatch

Once coherence holds, `RuntimeRegistry` registration for a given
`(type, aspect, method)` is unique by construction; the current
overwrite-on-insert becomes a debug assertion (a second registration is a bug,
not a valid override). This aligns with the `SymbolId`-keyed dispatch direction.

---

## Diagnostics

| Code | Meaning | Reported at |
|---|---|---|
| `T0014` | Orphan implementation: neither the aspect nor the type is local | the `impl` block |
| `T0015` | Conflicting implementation: a second impl of the same aspect for the same type | both impl spans |

Both are new error codes and require an entry in
`docs/public/reference/error-codes.md`.

---

## Alternatives Considered

### A — No orphan rule; global overlap check only

Allow impls anywhere but reject programs where two impls overlap. This permits
useful cross-module impls but makes coherence a whole-program property: adding a
module can break an unrelated module, and separate compilation / incremental
checking cannot guarantee coherence locally. **Rejected** — the orphan rule
gives the same safety with local, predictable errors.

### B — "Newtype only" (no foreign impls at all)

Forbid implementing any foreign aspect for any foreign type, with no escape
hatch, forcing wrapper types. Simpler but more restrictive than the orphan rule
and unnecessary — the orphan rule already prevents the incoherent cases.
**Rejected** as needlessly limiting.

### C — Last-impl-wins (status quo, made explicit)

Define dispatch as "the last-registered impl wins by module topological order."
**Rejected** — order-dependent semantics are a footgun, defeat `SymbolId`
dispatch, and contradict Metel's design preference for no hidden behaviour.

---

## Interaction with other work

| Work | Relationship |
|---|---|
| METEL-152 (aspect `SymbolId`) | Coherence is the precondition that makes `SymbolId` aspect dispatch unambiguous. |
| METEL-181 (callable `SymbolId` dispatch) | Should assume coherence; the overwrite path becomes an assertion. |
| METEL-185 (type-registry `SymbolId` rekeying) | The `merge_from` fix here should be folded in so the rekeyed registries union correctly. |
| RFC-0036 (conditional impls) | Conditional/parameterised impls interact with overlap; this RFC defers parameterised overlap to stay compatible. |

---

## Non-Goals

- Parameterised/negative overlap reasoning (`impl A for List<i64>` vs
  `impl A for List<String>`). First cut keys overlap on the type constructor.
- Coherence across separately compiled packages / a future package system. This
  RFC scopes coherence to the single program's module graph.
- Specialisation (more-specific impls overriding general ones).
- Changing how inherent (non-aspect) methods are resolved.

---

## Resolved / Open Questions

Open for the decision discussion:

1. **Should built-in types/aspects be treated as `std::core`-local for the
   orphan rule?** (Proposed: yes — only `std::core` may impl built-in aspects on
   built-in types.)
2. **Is type-constructor-level overlap acceptable for v1**, deferring
   parameterised impls, or must generic non-overlapping impls be allowed from
   the start?
3. **Error vs. warning for orphan impls during a migration period** — is any
   existing code (including the current virtual `std::core`) relying on orphan
   impls that must be migrated first?

---

## References

- `metel-interpreter/src/typeinference/mod.rs` — `register_aspect_impl`,
  `merge_from`, `method_scheme_env`
- `metel-interpreter/src/evaluator/mod.rs` — `register_aspect_method`,
  `get_aspect_method` / `get_aspect_method_by_id`
- `docs/public/reference/spec/declarations.md` — aspects and `impl` blocks
- RFC-0036: conditional `impl` blocks
- METEL-152: `SymbolId`-keyed aspect dispatch
- METEL-181, METEL-185: dispatch and registry `SymbolId` migration
