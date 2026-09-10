---
id: adr-0054
title: "Resolved Identity Freeze and Generic Instance Preparation"
date: '2026-09-09'
status: accepted
relates: adr-0041, adr-0042, adr-0048
implements: metel-core#1047
updated: '2026-09-10'
---

> **Amended 2026-09-10** — before implementation began. Three clarifications, all
> aimed at keeping a future incremental-compilation layer *additive* rather than a
> rewrite, at near-zero cost now:
>
> 1. Identity allocation is **structural, not positional** — an ID is a function
>    of what a binding *is* (its owner and lexical path), never of a traversal
>    counter or byte offset. Inserting unrelated text must not renumber anything.
> 2. No field of the durable resolved artifact is keyed by `Span`. Position
>    lookup is a separate **volatile index**, rebuilt per snapshot.
> 3. The frozen IR is **in-memory only** for this delivery; on-disk persistence
>    and cross-process interner stability are explicitly out of scope.
>
> These are folded into the sections below. The invariant, domains, freeze
> boundary, and generics plan are unchanged.

## Context

ADR-0041 established `SymbolId` for globally addressable declarations and moved
important runtime dispatch onto it. It deliberately left lexical locals
name-keyed, and it allowed type-dependent selection to remain distributed across
typechecking, construction, and elaboration. ADR-0042 then sealed selected
identity accessors, but did not create one complete resolved representation.

The result is a collection of partially compatible identity systems:

- global declarations, some calls, types, and methods use `SymbolId`;
- the reference side table records only bare global references; an absent entry
  ambiguously means either a local or an unresolved name;
- normalized qualified paths briefly carry an id, which construction can discard;
- locals, captures, and evaluator activation frames remain name-keyed;
- generic bodies are reconstructed by the interpreter at instantiation time;
- type-dependent member and overload selection still begins from strings.

This blocks complete editor navigation and rename, but it is more importantly a
compiler-boundary problem. A program must not acquire a different meaning because
one later consumer re-resolves a spelling differently from the frontend.

## Decision

Metel has one frontend-owned resolved-identity model. The frontend freezes every
successfully inferred body into an ID-complete representation before construction,
analysis, elaboration, or evaluation consume it.

The governing invariant is:

> After inference has solved a body and the frontend has frozen its resolution,
> no later phase may perform semantic lookup keyed by source spelling.

This is intentionally later than raw parsing or declaration interning. Fields,
methods, variants, overloads, and associated items can require inferred types to
select their target. They may therefore be resolved during inference, but their
output must be IDs. No later phase may reopen a textual environment.

### Identity domains

The domains are distinct newtypes, not aliases of one integer:

```rust
enum BindingId {
    Global(SymbolId),
    Local(LocalId),
}

/// The durable resolved artifact. Every key is an identity or an identity-keyed
/// structure; no field is keyed by `Span` or by `String`.
struct ResolutionMap {
    definitions: HashMap<BindingId, DefinitionInfo>,
    /// A reference site is named by its own identity (`RefId` = owner
    /// `BindingId` + lexical path to the use), not by where it currently sits
    /// in the file. `DefinitionInfo` and each reference record still *carry* a
    /// `Span` as metadata for diagnostics and rendering.
    references: HashMap<RefId, BindingId>,
}

/// Rebuilt cheaply from one parsed snapshot; never persisted, never a semantic
/// input. This is the only structure allowed to be keyed by source position,
/// and it exists solely to answer editor "what is at byte N" queries.
struct PositionIndex {
    // span-sorted spine over the snapshot's definitions and reference sites
}
```

- `SymbolId` remains the canonical identity of a globally addressable
  declaration: module-level values, types, aspects, methods, constructors,
  overload definitions, and imported references resolved to their defining
  declaration.
- `LocalId` identifies parameters, local `let`/`mut` declarations, nested
  functions, loop bindings, pattern bindings, and closure parameters. Shadowed
  bindings always receive distinct IDs.
- `BindingId` is used for value definitions, value uses, lexical frames, and
  captured cells.
- Nominal fields and variants receive their own declaration identities
  (`FieldId`, `VariantId`).
- Structural record/row field spelling is interned as `LabelId`, since a row
  label is not a declaration owned by one nominal type.
- `ModuleId` is separate from `BindingId`; module namespaces are not ordinary
  runtime value bindings. A module-navigation use case must state whether it
  needs a `ModuleId` location rather than coercing modules into the value model.
- Interned spelling (`NameId`/`LabelId`) may survive parsing and inference as
  source metadata or as input to an ID-keyed constraint. It is never a textual
  map key after parsing. The interner is owned by the resolver, handed to the
  frozen artifact by value, and treated as immutable thereafter.
- `RefId` names a reference site: its owner `BindingId` plus the lexical path to
  the use within that owner's body. It is the durable key for the reference
  table, so that resolved facts survive edits elsewhere in the file.

### Allocation is structural, not positional

Every ID is a deterministic function of *what the entity is*, never of where its
text sits or the order a traversal reached it:

- `SymbolId` — `(canonical module path, declared name, overload disambiguator)`.
  The overload disambiguator is the declaration's ordinal *among declarations
  sharing that name in that module*, not a file offset or a global counter.
- `LocalId` — `(owner BindingId, lexical path)`, where the lexical path is the
  chain of structural positions from the owning body to the binding
  (`param 0`, `block 2 / let "x" / pattern field "y"`). Shadowing produces
  distinct paths and therefore distinct IDs without a counter.
- `FieldId` / `VariantId` — `(owning SymbolId, declared member name)`.
- `LabelId` / `NameId` — interned spelling; equal spellings intern equal.
- `InstanceKey` — as defined below; its `TypeId`s are themselves interned
  structurally.

Consequences that later phases and tests may rely on:

- Inserting, deleting, or reformatting text that does not change the structural
  position of a binding leaves its ID unchanged.
- Editing one function body cannot change any ID outside it.
- Two runs over the same resolved module graph produce identical IDs regardless
  of file iteration order or parallelism.

`LocalId` and `SymbolId` are therefore deterministic and stable for one resolved
module graph. This decision still makes no promise that *structural* edits
(renaming a binding, moving a declaration between modules, reordering overloads)
preserve IDs; and it does not build the query/invalidation engine, cross-run
interner persistence, or on-disk artifact format that full incremental
compilation needs. Those remain a later decision. Structural allocation and the
`Span`-free durable artifact are the parts that are cheap now and expensive to
retrofit, so they are settled here; the rest is deliberately deferred and, given
these two, becomes an additive layer.

### Resolution freeze

The pipeline is:

```text
parse AST (source spelling)
  → declaration + lexical resolution
  → inference and constraint solving
  → resolution freeze
  → ID-complete typed/resolved IR
  → construction / move-check / borrow-check / elaboration / evaluation
```

At the freeze boundary, every successful semantic use carries the relevant
identity:

- global and local value uses carry `BindingId`;
- types and aspects carry their declaration IDs;
- direct calls carry a callable ID; overload selection has selected one;
- methods carry a method ID and dispatch evidence;
- nominal field and variant operations carry `FieldId`/`VariantId`;
- structural operations carry interned label IDs;
- module-qualified paths preserve their resolved global ID and original spelling.

An unresolved use is explicit diagnostic state, never a missing identity that a
later phase is allowed to guess from its name.

Source spellings remain available for diagnostics, source rendering,
documentation, and reflection metadata. An explicitly specified user-facing
dynamic reflection API may look up metadata by name, but it is not an evaluator
or compiler-resolution escape hatch.

The frozen IR is an in-memory artifact produced fresh by each analysis run. This
delivery does not define a serialized on-disk form, a schema version, or an
interner that is stable across processes. A later incremental-compilation layer
adds those; nothing here should encode assumptions that block it, but neither is
it built now.

### Generics and monomorphization preparation

Generic declarations are resolved templates, not untyped runtime bodies.
Lexical bindings and globally resolvable references in a template already carry
IDs. Type-dependent selections retain interned IDs until a concrete
instantiation is inferred.

Every evaluator-visible instance follows:

```text
resolved generic template
  → concrete arguments
  → inference
  → resolution freeze
  → frozen ID-complete instance
  → evaluation
```

The instance identity is extensible:

```rust
struct InstanceKey {
    generic: SymbolId,
    type_arguments: Vec<TypeId>,
    // future comptime/non-type arguments are part of this key
}
```

This ADR requires an instance cache boundary and frozen-instance representation,
but does not require whole-program specialization collection. Core issue #288
consumes this representation to implement full demand-driven frontend
monomorphization: reachable concrete calls seed a worklist, cached instances
break recursion, and rewritten calls target concrete specializations.

### Evaluator model

The evaluator consumes identity, not name lookup:

```text
BindingId::Global(SymbolId) → global/module value registry
BindingId::Local(LocalId)   → current activation-frame slot or captured cell
```

The same `LocalId` is valid across recursive invocations because each invocation
has a distinct frame. A closure capture selects the appropriate enclosing frame
cell by local ID. Names are retained only for presentation and deliberately
specified reflection.

## Implementation plan

This is one delivery under metel-core#1047. The commits may be staged, but the
issue is not complete until all steps and the invariant are delivered.

1. Define the ID newtypes, the complete `ResolutionMap`, the separate
   `PositionIndex`, source metadata, and the structural allocation rules above.
   Add adversarial resolver fixtures first, including one that inserts blank
   lines and reformats whitespace around a declaration and asserts every ID is
   unchanged, and one that edits a function body and asserts no ID outside it
   moves.
2. Extend lexical resolution to allocate `LocalId`s and explicitly classify all
   value references as global, local, or unresolved. Preserve qualified-path
   global identities.
3. Intern member/type/label spellings and rekey inference registries and
   constraints so type-dependent resolution selects IDs without `String` keys.
4. Introduce the resolution-freeze output and make typed declarations,
   parameters, patterns, expressions, calls, member access, captures, and
   generic templates carry their required IDs.
5. Migrate tooling to the shared resolution map: definition for locals and
   qualified paths first, then references/rename as consumers of the same map.
6. Migrate move/borrow analysis, construction, and elaboration to the frozen
   representation; remove their semantic spelling lookups.
7. Migrate evaluator frames and capture storage to `LocalId`, global values to
   `SymbolId`, and delete name-keyed evaluator fallback paths.
8. Add frozen generic instances and `InstanceKey` caching, replacing runtime
   generic-body reconstruction. Hand the representation to issue #288 for
   frontend-wide monomorphization.
9. Seal resolver-only name-keyed APIs and delete transitional compatibility
   paths. Prefer a structural guarantee — the frozen IR's public types simply do
   not carry `String` or `Span` in key position — with a CI architecture check
   as the backstop against new post-freeze semantic name lookups, not the
   primary defence.

## Acceptance criteria

- Every resolved reference has explicit global/local identity; absence cannot
  mean both local and unresolved.
- No post-freeze compiler, analysis, or evaluator registry performs semantic
  lookup by `String` or source spelling.
- No field of the durable `ResolutionMap` or the frozen IR is keyed by `Span`;
  the only position-keyed structure is the rebuilt-per-snapshot `PositionIndex`.
- IDs are allocated structurally: a fixture inserting blank lines and
  reformatting whitespace around a declaration leaves every `SymbolId`,
  `LocalId`, `RefId`, `FieldId`, and `VariantId` unchanged, and a fixture
  editing one function body changes no ID outside that body.
- The frozen IR retains IDs for global/local values, type-dependent member
  selections, qualified paths, nominal members, and structural labels.
- Runtime behavior is preserved for shadowing, nested closures, mutable
  captures, recursion, nested functions, loops, pattern bindings,
  imports/re-exports/globs, overloads, qualified paths, and generic bodies.
- Generic instances are inferred and frozen before evaluation, never rebuilt
  through name lookup.
- User diagnostics retain original spelling and source spans.
- A future monomorphizer can consume `InstanceKey` and the frozen-instance
  representation without creating a second generic-body path.

## Consequences

- The LSP, evaluator, and future compiler consume one resolution truth rather
  than maintaining separate identity mechanisms.
- This deliberately supersedes ADR-0041's stopping point of name-keyed locals
  and its distributed type-dependent resolution output.
- The migration is broad: registries, typed AST, generic construction, and
  evaluator environments all change together. It is therefore tracked as one
  issue with strict end-state verification, not as independently shipped feature
  slices.
- Full frontend monomorphization remains separately tracked by metel-core#288,
  but its prerequisite representation and evaluator correctness boundary land
  here.
- Incremental compilation stays a later decision, but structural allocation and
  the `Span`-free durable artifact — the parts that are cheap to settle now and
  costly to retrofit once fixtures and IDs proliferate — are fixed here, so that
  a future query/invalidation/persistence layer is additive rather than a
  re-issue of this migration.
