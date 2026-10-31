---
id: adr-0067
title: "A Written Type Name Resolves to an Identity, Not a Spelling"
date: '2026-10-31'
status: accepted
relates: adr-0054, adr-0065, adr-0066
implements: metel-core#1612, metel-core#1735
---

## Context

ADR-0054 and ADR-0066 moved construction from spellings to identities: a value use resolves to a
`BindingId`, a scheme is read through the binding a use site resolved to, a field through its `FieldId`.
What construction still finds by spelling is the one thing the AST gives no identity for, **a name written
inside a type annotation**:

- **Generic parameter names.** `ConstructCtx::generic_params: HashMap<String, TypeVar>` and about fifteen
  definition-scoped maps in `calls.rs`, `expressions.rs`, `patterns.rs` and `declarations.rs`. A bound check
  reads a parameter back by the spelling it was declared with.
- **Written block-local type names.** `local_struct_ids: Vec<HashMap<String, SymbolId>>`, read by
  `written_type_id`, the single place a written type name becomes a `SymbolId` for a block-local
  declaration. The annotation converter reaches it through `AssocResolveCtx::local_types`.

Each read carries a `resolution-freeze-allow` exemption in `check_no_semantic_name_lookup.py` (27 in the
frontend). Both are safe today only because the spelling is unique within one definition or scope; this is
design debt, not a known misresolution.

It is not a local fix because `TypeExpr::Named(String, Vec<TypeExpr>)` carries neither a span nor a
resolution. The identity pass keys a use by `(owner, LexicalPath)` and records it against the use's span
(`BindingSpans`); a written `T` has no span, so there is nothing to record and nothing for construction to
look up. The conversion `TypeExpr -> InferType` is shared by inference, the registry and construction, so a
change here crosses the inference boundary.

## Decision

A written type name gets a span, a resolution recorded against that span, and a binder to resolve to.

### 1. `TypeExpr::Named` carries a span

`Named` gains the span of the written name. It is the key the identity pass records the resolution under,
exactly as for a value reference. This lands first, as its own change with no behaviour change: the
parser fills the span, every existing pattern and constructor is updated, and nothing reads it yet.
Synthesised `Named` nodes (a lowered `impl Aspect` parameter, a lowered projection base) carry the span of
the source they were lowered from, so a diagnostic and a resolution still land somewhere real.

### 2. A generic parameter is a binder

A type, row or record parameter becomes a definition of a new identity, `TypeParamId`, keyed structurally
like `LocalId` (ADR-0054 amendment): `(owner, LexicalSeg::Generic(ordinal))`, where `owner` is the
declaring item (function, struct, enum, aspect, impl) and `ordinal` is the parameter's position in that
item's generic list. The ordinal is part of the declaration, so reordering unrelated statements does not
renumber it, and a parameter keeps its identity under reformatting.

`GenericParam` carries a definition span. The identity pass walks the generics before the signature and
records a `Definition` for each, then records a reference for every written `Named` whose name is a
parameter in scope. Scope follows the language: a method sees its `impl`'s parameters and its own, an
inner `fun` does not see the enclosing function's (RFC-0195), a closure sees the enclosing function's.

A resolved written type name is one of two things, so the table is a closed set rather than an
`Option`:

```text
TypeRes::Param(TypeParamId)   // a generic parameter in scope
TypeRes::Item(SymbolId)       // a struct, enum, alias or aspect, module-level or block-local
```

A name that resolves to neither is an unresolved reference, reported where it is today (`T0002`-class
unknown type); it does not fall back to a spelling lookup after the freeze.

### 3. Block-local type declarations resolve the same way

> **Outcome (2026-10-31).** Not done under #1612; see [Implementation outcome](#implementation-outcome).
> The sketch below assumed the identity pass could give a block-local type a `SymbolId`. Those ids
> are minted by the registry, so a written name resolves to a *declaration span* and construction
> maps the span to the registry's id.

A block-local `struct` or `enum` already has a `SymbolId`. The identity pass resolves a written name
that denotes one to `TypeRes::Item(symbol)` at its span, so `written_type_id` reads the table and
`local_struct_ids` is deleted. The annotation converter takes the resolution table in place of
`AssocResolveCtx::local_types`.

### 4. Construction and the converter read the table

`ConstructCtx::generic_params` and the definition-scoped maps are re-keyed from `String` to
`TypeParamId`. The `TypeExpr -> InferType` converter takes the span-keyed `TypeRes` table; a `Named` with a
span looks up its resolution and builds the type variable, the nominal type or the alias from it. Callers
that have no table (a registry building a declared signature before any body exists) resolve generic
parameters through the declaration's own parameter list, which is the same ordinal-keyed identity, not a
spelling.

### Rollout

Three changes, each green on its own:

1. Spans on `TypeExpr::Named`. No behaviour change.
2. `TypeParamId`, the binder definitions and references in the identity pass, and construction re-keyed.
   Deletes the generic-parameter exemptions.
3. Block-local type names resolved through the table. Deletes `local_struct_ids` and the last exemption,
   and removes the type-parameter and written-type-name allowance from the scan.

Done when no `resolution-freeze-allow` remains in `construction/` other than field-label maps (a label is
a name by nature, and `FieldId` already keys by owner plus name).

## Alternatives considered

- **Resolve in a side pass that rewrites `Named("T")` into a resolved node before construction.**
  A smaller diff, but it leaves two representations of one type annotation (parsed and resolved) that must
  be kept in step, and every consumer of the parsed form (the formatter, the language server, doc tooling)
  keeps seeing the unresolved one. A span on the node serves all of them.
- **Fix only block-local type names.** Small and safe, but leaves the generic-parameter exemptions, which
  are nearly all of the debt, and the issue's done condition unmet.
- **Key `TypeParamId` by position in the source (a span or offset).** Rejected by the ADR-0054 amendment:
  an identity is a function of what an entity is, never of where its text sits.

## Consequences

- A generic parameter cannot be confused with another of the same spelling in a different definition, and
  a shadowing block-local type cannot capture a written name that means an outer one.
- `TypeExpr::Named` grows a field, so every pattern over it changes once (about 140 sites in 27 files).
  This is the cost of the uniform answer; the first change carries it alone so review is mechanical.
- Tooling gains a free result: a written type name becomes a position-index hit, so go-to-definition and
  find-references work on `T` and on a local type name the way they already do for values.
- The inference export path (`GlobalExports`, ADR-0022) still crosses modules by name; this ADR does not
  change it.

## Open questions

- **Associated-type projections.** `T::Item` lowers to `Projection { base: Named("T") }`. The base resolves
  to the parameter; whether the associated-type name itself gets an identity is #242's question and is out
  of scope here.
- **`impl`-header parameters.** An `impl<T> Trait for Wrapper<T>` binds `T` for its methods. This ADR keys
  it to the `impl` as owner; if the registry already interns impls under a different identity, that
  identity is the owner.

## Implementation outcome

Steps 1 and 2 landed under metel-core#1612, in seven changes, each green on its own and none changing
behaviour:

- `TypeExpr::Named` carries the span of the written name (#1728), wrapped in `NameSpan` whose `Debug`
  prints no position, because row-bound entailment compares annotations by their rendering.
- The identity pass resolves a written generic-parameter name to a `TypeParamId` (#1729), keyed by the
  owning declaration, the list the parameter was written in (`Container`, `Own`, or `Synthesised` for the
  parameter lowering adds for an `impl Aspect` parameter type) and its position.
- A `TypeScheme` carries `param_ids`, index-aligned with `param_names` (#1730). This is the one place a
  parameter's spelling is paired with its identity. Lowering's `_ImplT{n}` names now count per function so
  the identity pass can declare the same parameter by the same name.
- Construction resolves a written generic name through a `GenericScope` (#1731); the bound checks read
  their arguments through an id-keyed `GenericArgs`.
- A `struct`'s or `enum`'s parameters (#1733) and an aspect's (#1734) have identities, keyed by the type's
  `SymbolId` or the method's declaration span.

The type-parameter tables ride on `BindingSpans`, so no `FrozenIdentity`, `TypeCtx` or evaluator
signature changed. No generic-parameter spelling lookup is left in `construction/`.

### Step 3 is deferred (metel-core#1735)

The sketch in decision 3 is not a change confined to construction. Block-local type ids are minted by the
registry (`archived_local_type_id_declared_at`), and a type that names a block-local type often carries no
nominal id: the registry converts struct field templates and enum info with no block-local scope. Construction's
by-name scope compensates. With the block-local branch of `written_type_id` removed, 13 tests fail and about 700
lookups in the suite reach it, through eight name-only wrappers.

The prerequisite is on the inference side: stamp block-local ids where inference and the registry create the
types, so the id travels on the type as it does for a module-level one. Then the identity pass's resolution
of a written name to its declaration span (prototyped; reusable) covers the sites that write a name, and
`local_struct_ids` and the last exemption can go. That is tracked in metel-core#1735.

The by-name scope mirrors the block structure, so the innermost declaration wins as lexical scope requires:
this is design debt, not a known misresolution.
