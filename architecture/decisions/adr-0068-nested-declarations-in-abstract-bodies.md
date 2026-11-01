---
id: adr-0068
title: "A Generic Body's Nested Declarations Are Analysed, Not Skipped"
date: '2026-11-01'
status: accepted
relates: adr-0054, adr-0063, adr-0067
implements: metel-core#1732
---

## Context

ADR-0063 retains a generic definition's body as an *abstract body* so `--move-check` can analyse it at
the definition, without instantiating it. A generic body is constructed only when it is instantiated, so
the abstract body is the one place its ownership can be checked ahead of a call.

The statement translation of an abstract body accepts a plain `let`, `var` or expression statement and
refuses everything else. A generic function whose body declares a nested `fun`, `struct` or `enum` is
therefore `I0011` under `--move-check`, although the concrete check accepts the same function
(metel-core#1732). `I0011` is the defensive "this body could not be analysed" outcome (ADR-0063), and a
corpus test (`every_generic_body_in_the_corpus_is_analyzed`) fails on any unanalysed generic body, so such
a body cannot enter the fixture corpus either.

The obvious fix, translating the declaration to nothing, is **unsound for a `fun`**. A function declared in
a block sees none of the enclosing function's locals or type parameters (RFC-0195), so omitting it does
not disturb the parent's analysis. But the nested function's *own* body is then never analysed:
`fun f<T>(x: T) { fun g(s: String) -> i64 { let a := s; let b := s; 0 } … }` is accepted, while the same
`g` inside a non-generic function is `T0019`. The nested body is not constructed ahead of time (its parent
is generic), so nothing else would have checked it.

A block-local `struct` or `enum` fails earlier, for a different reason, covered under Decision 2.

## Decision

### 1. A nested `fun` is its own abstract definition

A nested function cannot capture the parent's bindings or type parameters (RFC-0195), so it can be
analysed in isolation, exactly as a top-level generic is. When a generic definition's abstract body is
prepared, the definition's body is searched for nested `fun` declarations at any depth, through blocks,
closures and other nested functions. Each is given the abstract signature and abstract body a top-level
function gets, from the scheme already filed under its local binder and the module's resolved inference
facts (which are keyed by span, so the parent's facts cover the nested body).

- The results are retained on the parent's `TypedFunDecl` as a flat list of nested definitions.
- The parent's own abstract block omits the declaration. A call to the nested function resolves through
  its scheme, as a call to any function does.
- `--move-check` analyses each retained nested definition with a fresh flow state, after the parent. A
  nested definition that cannot be prepared is `I0011`, as for any generic body, so nothing is skipped.
- A non-generic parent is unchanged: its nested functions are constructed with it and analysed as typed
  declarations.

### 2. A block-local `struct` or `enum` has member identities

Field and variant selections in an abstract body are retained as `FieldId` and `VariantId`, which the
`MemberTable` interns before inference from the module-level type declarations, keyed by
`(owning SymbolId, member name)`. A block-local type has no such owner: its id is a registry-minted
`BlockLocal(n)`, assigned in the order inference meets the declarations. Its registry entries are stamped
with no member ids (`stamp_member_ids`: "Block-local types … stay `None`"), so a selection on one records
no fact, and a unit-variant path on one records no path fact because the owner name is resolved against
the module scope only.

The `MemberTable` gains a second key kind for members of block-local types: `(declaration span, member
name)`. `collect_members` finds block-local `struct` and `enum` declarations in function bodies and interns
their fields and variants (variant fields qualified by variant, as for module-level enums). When
inference registers a block-local type it stamps the entries from the table by the declaration's span,
and the static-path fact resolves a local owner through the scope inference is in, before the module
scope. A declaration span, unlike `BlockLocal(n)`, is the same on every compilation and in every
reconstruction of a generic body, so the ids are stable.

### 3. Order of change

Two changes, each green on its own: nested `fun` (Decision 1), then block-local members (Decision 2).
Decision 1 closes the soundness gap and needs nothing from Decision 2. Until both land, a generic body
with a block-local type stays `I0011`, never a silent pass.

## Alternatives considered

- **Omit the declaration from the abstract block.** Rejected: unsound for a `fun`, as above.
- **A statement kind for a local function** whose body the parent's flow analysis enters in isolation.
  Rejected: every consumer of the abstract block would have to implement "analyse this under a fresh,
  detached state", where a separate definition already has exactly that meaning.
- **Reject nested declarations in generic bodies.** Rejected: RFC-0195 specifies them, and the concrete
  check accepts them.
- **Key local members by the registry's `BlockLocal(n)`.** Rejected: the number depends on the order
  inference meets declarations, and a reconstructed generic body registers its local types again under new
  numbers.
- **Wait for block-local types to carry their ids on every type (metel-core#1735).** Not needed: abstract
  bodies need the *selection* ids, which the table and the registry's declaration span provide. #1735 is
  the larger registry change and stays separate.

## Verified before deciding

Each of these was checked against the code or by experiment, not assumed.

- **Nested bodies are only reachable here.** A generic function's body is `FunBody::Generic` until
  instantiation, so a nested `fun` in it has no `TypedDecl`. Confirmed by the unsound experiment: the
  nested double move passed.
- **The nested scheme and facts exist.** A nested function has a scheme filed under its local binder
  (ADR-0066), and the expression, path and field facts are recorded module-wide by span, so the parent's
  facts cover the nested body. A call to a nested function from the parent's abstract body already gave the
  right verdicts (a use-after-move of the parent's own value is `T0019`).
- **Every place an abstract body is prepared sees the body AST.** The three preparation sites (generic
  free function, impl method, let-bound generic closure) each hold the `FunDecl` being prepared.
- **Ownership facts for a local type work.** A probe of `registry.abstract_nominal_aspect` on the
  registered ids: a block-local `struct` and a generic one answer `Copy = Some(false)`; a block-local
  `record` answers `None` (conditional), which `retain_nominal_ownership` already records as
  `Conditional`, the same as for a module-level record. No change needed there.
- **The two missing facts are the two named in the errors.** `nominal field selection identity is not
  retained` is `definition_nominal_fields` having no entry for the span, because the stamped
  `FieldId` is `None`; `value path selection contract is not retained` is
  `record_definition_static_path` failing to resolve a local owner name.

## Consequences

- A generic function with a nested `fun`, `struct` or `enum` is analysed by `--move-check` with the same
  verdicts as the concrete check, including inside the nested function.
- `TypedFunDecl` grows a field, and `analyze_generic_definition` analyses more than one body per
  definition. The abstract-body model is otherwise unchanged.
- `MemberTable` is still built once before inference and immutable after; it just holds more keys.
- The completeness test keeps its meaning: no generic body is left unanalysed.

## Open questions

- **Whether a nested function that is itself generic should be reported once per instantiation of its
  parent.** It is not: it is analysed once, at the definition, like any generic.
- **Nested functions in the default method of an aspect.** Aspect default methods are prepared at a fourth
  site (`construct_decl`'s inherited-method path); the discovery walk takes the `FunDecl` the site holds,
  so it should apply unchanged, and the implementation adds a fixture to confirm it.
