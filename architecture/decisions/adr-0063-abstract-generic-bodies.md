---
id: adr-0063
title: "Reusable Abstract Typed Generic Bodies"
date: '2026-10-09'
status: accepted
relates: ADR-0054, ADR-0058, ADR-0060, ADR-0062
implements: metel-core#273
---

## Context

Generic definitions are checked against their declared bounds, but their durable
body is still source AST. The optional move checker reconstructs that AST with
symbolic sample arguments to obtain typed operations. This repeats semantic
resolution and loses facts that the definition checker already established.
The current corpus contains twenty unchecked user bodies: inherited method
bounds, return-only parameters, inferred operator requirements, nested captures,
row remainder writes/destructuring, field-wise Clone and nominal projections.
The samples are not concrete specializations and must not become the contract
between frontend analyses.

ADR-0058 remains authoritative for definition-time legality; ADR-0060 remains
authoritative for unknown row ownership. ADR-0054 defines lexical/global identity
and resolution freeze. None of these requires concrete monomorphization before
a generic definition can be ownership-checked.

## Decision

### Artifact and lifecycle

The frontend retains an immutable abstract typed body for every supported generic
definition, including unused definitions. It is owned by the declaration or
closure's lexical identity and produced once from solved definition-time facts.
Consumers cannot run inference, change substitutions, reconstruct source AST, or
choose a convenient concrete implementation to interpret this artifact.

The artifact has a signature, a declared-fact environment, and typed operations
and control flow. Abstract types use binder-local parameter identities, distinct
from solver `TypeVar`s and from concrete runtime `Type`s. Alpha-renaming solver
variables does not change the artifact. Parameter references in nested bodies
identify the owning binder as well as the parameter within it; they must not
capture an equally numbered parameter from another binder.

Explicit parameter positions follow source declaration order, not the solver's
sorted quantifier vector. Implicit parameters use structural signature/body
origins. Tests include non-monotonic solver-variable renaming that reverses the
quantifier vector; equality must not depend on allocation numbers.

Concrete types preserve existing nominal identity and structure. Known fields,
unknown row tails, residual brands, references, function multiplicity/mutation,
associated projections and abstract parameters remain distinct. Unknown tails
are never replaced by empty records and unresolved types are never replaced by
`Never` or `Unit` merely to complete this artifact.

Inference collects type and semantic-selection facts while checking the
definition. Once solved, the handoff freezes its remaining legitimate generic
variables into abstract parameter references. Construction lowers the body from
those facts without emitting new constraints or re-solving the definition.
Source positions may join temporary inference/handoff records; durable artifacts
use structural node and binding identities, with spans as diagnostic provenance,
not semantic lookup keys.

### Declared facts and operations

The fact environment retains positive and negative aspect grants with aspect
identity and type arguments; associated-type projections/equalities; row kinds,
known field types, equations and remainder relations; field-wise grants and
their exclusions; typed negative field requirements; and opaque-return facts.
Impl/struct and enclosing-body facts are retained alongside method-owned facts.
These are entailments of the declaration, not grants inferred from later callers.

Implicitly generic definitions also retain obligations established by their own
definition check, including operator and capture requirements. An inferred
numeric requirement on an unannotated argument is not an explicit `T: Copy`
grant. These inferred obligations remain distinct from explicit rigid parameter
bounds and must never be strengthened using facts from a later concrete call.

Typed operations retain operand/result types, binding/place identities, field
selections, receiver/argument ownership modes, branch/loop/exit structure, and
closure capture-entry types and multiplicity. A method selected through an
abstract grant carries the resolved requirement and abstract signature. A
type-dependent field or conditional selection carries the proven field/row facts
and selection obligation. It does not use a global bare-name lookup and does not
pick one of several concrete implementations during ownership analysis.

Calls retain the callee's resolved identity or abstract callable contract and
the instantiated abstract parameter modes. Recursive and mutually recursive
references point to declarations; they do not recursively embed copies of bodies.
Nested definitions and closures retain enclosing abstract parameters and lexical
captures. Captured residuals use their entry shape, not a shape widened later in
the body (ADR-0062).

### Ownership consumer

Move checking walks the abstract operations using the same place/control-flow
model as concrete typed bodies. Its aspect queries use only declared facts and
structural entailments. An unbounded parameter is not `Copy`; a parameter granted
`Copy` is. A row is structurally `Copy` only when every known field and its unknown
tail have the required evidence. Borrowing versus consumption is recorded at the
typed call boundary, not rediscovered by resolving methods on placeholders.

For implicit parameters, definition-inferred obligations also participate in
the judgment where the language already specifies their inference. The artifact
does not change the legality rules for explicitly declared parameters.

The final migration removes symbolic AST reconstruction from ownership analysis
for supported definitions. Absence of skip warnings alone is not enough: tests
must assert that bodies were visited, ownership violations were detected, and
valid abstract bodies remained valid across concrete calls.

### Other consumers and specialization boundary

The artifact is frontend-owned, not a move-check-only AST. Later analyses can
reuse its types, declared facts, selections, and control flow. Concrete
specialization can substitute parameters and discharge deferred selections while
preserving declaration and lexical identity.

Core #1053 owns concrete `InstanceKey`/cache boundaries and evaluator-visible
frozen instances. It must consume or extend this artifact rather than inventing
a competing generic-body representation. Core #288 owns specialization
collection, concrete body materialization and call rewriting. Neither is a
prerequisite for this definition-time analysis. Runtime reconstruction remains
in place until those issues replace it; abstract bodies are not runtime values.

### Incomplete analysis

This ADR does **not** decide whether incomplete analysis rejects the program or
returns an explicitly qualified result. That policy remains an open decision in
#273. Migration must preserve current behavior until the decision is settled;
an inability to analyze is not a demonstrated `T0019` move violation.

## Alternatives Considered

**Check only concrete specializations.** Does not check unused definitions and
makes generic legality depend on callers. It remains useful as a differential
check, not as the definition's ownership contract.

**Repair all symbolic samples and retain reconstruction permanently.** Fixes
individual failures but retains duplicated semantic resolution and a second
fact-recovery boundary. Transitional repairs may keep existing behavior working;
they are not this issue's end state.

**Put solver variables into concrete `Type`.** Blurs the existing pass boundary
and allows analyses to consume unresolved inference state. Abstract parameters
are immutable binder references, not unknowns to solve.

**Build ownership-only summaries without typed operations.** Loses reusable
expression/call facts and makes later consumers repeat definition checking.

## Delivery and Verification

Delivery is staged, but #273 remains open until the whole contract holds:

1. Introduce immutable abstract types and freeze solved generic signatures into
   binder-local parameter references. Retain them on frontend declarations.
2. Retain the complete declared-fact environment and definition-time expression,
   selection, place and control-flow facts; construct abstract bodies once.
3. Cover impl/method/enclosing generics, closures/captures and cross-module
   identity; migrate move checking to the artifact and remove reconstruction.
4. Verify every measured skip and paired positive/negative ownership cases,
   settle any incomplete-analysis policy, and update limitation/architecture
   records only when their claims are demonstrated.

Tests cover alpha-renaming, distinct binders, return-only parameters, borrowed
and owned abstract types, unknown/closed tails, field-wise grants, associated
types, inherited bounds, conditional methods, projections, restoration, nested
captures, unused definitions, recursion and module collisions. Differential
tests compare abstract ownership decisions with valid concrete specializations
without treating one convenient instantiation as proof about all parameters.

The debug/release workspace suites, strict Clippy, formatting and docs gates
remain required. This delivery does not enable move checking by default, add
borrow checking, or resolve the independent loop-analysis limits in core #272.
