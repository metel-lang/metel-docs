---
id: rfc-0059
title: "Symbol Definition Index in ResolvedNames"
date: '2026-06-10'
status: implemented
spec_status: pending
---

## Summary

Add a `definitions: HashMap<SymbolId, Span>` field to `ResolvedNames`,
populated during the name resolution pass, so that later pipeline stages and
external consumers such as the LSP can map any resolved symbol to the source
location where it was declared.

---

## Motivation

`ResolvedNames.symbols` maps `(module_path, name) → SymbolId`. That is
sufficient for name lookup, but it answers only "does this name exist and what
is its id?" — not "where was it declared?".

Two workstreams need the reverse direction:

**LSP goto-definition** (LSP bootstrapping report §5). The language server
receives a cursor position, resolves the identifier under the cursor to a
`SymbolId` via `ident_at`, and must then jump to the defining span. Without a
definitions map it has no way to find that span short of re-walking every
module's AST.

**METEL-180: call resolution around SymbolId**. When call sites are rewritten
to carry a resolved callee identity (`SymbolId`) rather than a surface name,
diagnostics for unresolved calls, ambiguous overloads, and "no matching
overload" errors need to print the candidate declaration sites. Those sites are
the defining spans stored in this index.

The name resolution pass already walks every top-level declaration and has the
declaration span available on the AST node. Storing it in a map at that point
has negligible cost and no downstream coupling.

---

## Design

### New field on `ResolvedNames`

```rust
pub struct ResolvedNames {
    // existing fields …
    pub symbols: HashMap<(Vec<String>, String), SymbolId>,
    pub pub_surface: HashMap<Vec<String>, HashSet<String>>,
    // …

    /// Maps each resolved SymbolId to the span of its declaration.
    pub definitions: HashMap<SymbolId, Span>,
}
```

### Population

The name resolver already iterates every top-level declaration while building
`symbols`. For each declaration that produces a `SymbolId`, insert
`definitions.insert(id, decl.span())`.

Covered declaration kinds:

| Declaration | `SymbolId` source | Span |
|---|---|---|
| Free function `fun f(…)` | existing symbol allocation | `FunDecl::name.span` |
| Type declaration `type T = …` | existing symbol allocation | `TypeDecl::name.span` |
| Aspect declaration `aspect A { … }` | existing symbol allocation | `AspectDecl::name.span` |
| `let` binding (top-level) | existing symbol allocation | `LetDecl::name.span` |
| Impl method `impl T { fun m(…) }` | new: allocate `SymbolId` for each method | `FunDecl::name.span` inside impl |
| Aspect impl method | new: allocate `SymbolId` for each method | same |

Inherent method and aspect method symbols are currently **not** allocated as
top-level `SymbolId`s in the name resolver — they live in the
`TypeDefinitionRegistry` keyed by `(type_name, method_name)` string pairs.
This RFC introduces `SymbolId` allocation for method declarations as a
prerequisite for the definitions map to cover them.

This method-symbol allocation is the same work that METEL-180 requires to
support identity-based dispatch. The two tasks share the allocation step; they
can be implemented together or in either order without conflict.

### `TypeDefinitionRegistry` extension

For field and variant definitions (needed for hover and goto-definition on
struct fields and enum variants), remove the `#[allow(dead_code)]` annotations
from the spans that are already present on `FieldDef` and `VariantDef` in
`ast/mod.rs`:

```rust
pub struct FieldDef {
    pub name: String,
    pub ty: Type,
    pub span: Span,   // name token span — remove #[allow(dead_code)]
}

pub struct VariantDef {
    pub name: String,
    pub fields: Vec<FieldDef>,
    pub span: Span,   // name token span — remove #[allow(dead_code)]
}
```

**Span invariant:** `FieldDef::span` and `VariantDef::span` store the **name
identifier token span only** — not the full field or variant declaration.
This is the correct target for goto-definition (jump to the name, not the
opening brace of a record variant) and for diagnostics. Hover does not use
`definitions`; it reaches the full declaration through the typed AST, so
there is no need to store the wider span here.

The LSP report (§8) already notes these annotations as minor cleanup; this
RFC formalises the span invariant alongside the removal.

### `MetelError::primary_span()` accessor

The error type exposes `start`/`end`/`filename` on parse and type error
variants but offers no uniform accessor. Add:

```rust
impl MetelError {
    pub fn primary_span(&self) -> Option<Span>;
}
```

This is a mechanical addition with no behavioural change. It is included in
this RFC because it is a prerequisite for LSP diagnostics conversion, and the
dead-code cleanup in `FieldDef`/`VariantDef` belongs in the same commit.

---

## Interaction with METEL-180

METEL-180 redesigns call resolution so that after typechecking every call site
carries a `SymbolId` callee identity. That work requires:

1. Overload sets indexed by `SymbolId` rather than `(type, name)` string pairs.
2. `SymbolId`s for methods as well as free functions.

Point 2 is shared with this RFC. The method-symbol allocation introduced here
feeds both METEL-180 (callee identity at call sites) and this RFC (definition
spans). Coordinate the two tasks to avoid double-touching the name resolver in
the same sprint.

Recommended sequencing: implement the `SymbolId` allocation for methods as
part of this RFC, then METEL-180 builds on that foundation when rewriting call
resolution.

---

## Re-export behaviour

Goto-definition on a re-exported name always navigates to the **original
definition**, not to the re-export site. This falls out naturally from how
`SymbolTable::intern` already works: `ImportBinding` carries `source_module`
and `source_name` pointing at the original defining module, and `intern` keys
on that pair — so two imports of the same re-exported symbol produce the same
`SymbolId`. `definitions[id]` therefore always returns the original span.

This matches the behaviour of Rust, TypeScript, and most production language
servers. Re-export sites are not recorded in `definitions`; a future
find-references RFC can address navigation to re-export declarations if that
need arises.

---

## Non-Goals

- Storing use-site references (`references` rather than `definitions`; deferred
  to a later LSP RFC on find-references).
- Goto-definition for built-in / stdlib symbols. `StdPrelude` symbols have no
  source file; they map to a synthetic span or nothing until stdlib is
  represented as real source (METEL-181).

---

## Alternatives Considered

### A — Derive the span on demand by re-walking the AST

Instead of storing definitions at resolution time, LSP consumers walk the
`TypedModuleGraph` to find the declaration whose name span contains the query
offset.

**Rejected.** It duplicates span-search logic in the LSP, couples the LSP to
AST node shapes, and repeats work already done during resolution. A single
`HashMap` lookup is simpler and faster.

### B — Store spans only in the typed AST, not in `ResolvedNames`

`TypedFunDecl` and similar nodes already carry spans. The LSP could walk the
typed graph.

**Rejected for goto-definition.** Goto-definition needs to reach the
*definition* span of a symbol referenced anywhere — including at call sites in
other modules where the typed AST records the use span, not the definition
span. The `definitions` map in `ResolvedNames` is the single cross-module
source of truth.

### C — Separate `DefinitionIndex` struct populated in a post-resolution pass

A dedicated pass after name resolution reads `ResolvedNames.symbols` and the
untyped AST to build the index.

**Rejected.** The name resolver already has the declaration AST nodes and
their spans in hand while inserting into `symbols`. A separate pass re-walks
the same nodes for no benefit. One pass is cleaner.

---

## Implementation Notes

- `ResolvedNames` construction is in `name_resolver.rs`. The new field
  requires a `HashMap::new()` in the initialiser and `insert` calls at each
  declaration site.
- Removing `#[allow(dead_code)]` on `FieldDef::span` and `VariantDef::span`
  may expose unused-field warnings elsewhere; address them at the same time.
- The `MetelError::primary_span()` accessor is one `match` arm per error
  variant in `error/mod.rs`. It produces `Some(Span)` for variants that
  already carry span data and `None` for internal/contextual errors that do
  not.
- No changes to the typechecker, elaborator, or evaluator are required by this
  RFC. `ResolvedNames` is passed through those stages unchanged.

---

## References

- LSP bootstrapping report: `metel-lsp/docs/reports/lsp-bootstrapping-analysis.md` §5, §3, §8
- METEL-180: Redesign call resolution around SymbolId after overload selection
- METEL-181: Unify builtin and std::core modeling with the normal module pipeline
- `name_resolver.rs` `ResolvedNames` struct and resolution pass
- `symbols.rs` `SymbolId` and `SymbolTable`
- `error/mod.rs` `MetelError` variants
