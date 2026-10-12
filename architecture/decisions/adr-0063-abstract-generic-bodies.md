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

The frontend retains an immutable abstract typed body for every generic
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

Impl-method body binders are lexical identities derived from the resolved
method-group symbol and a definition ordinal within that group. Their parameter,
local and reference identities are owned by that body binder, not by the shared
runtime selection symbol. Only another definition of the same group advances
the ordinal; whitespace and unrelated declarations do not. Reordering variants
is a structural edit and may change their identities. Construction reads these
binders through the existing transient span bridge. This does not change runtime
method selection or eliminate its separate flattened-symbol limitation.

Lowering-expanded inherited defaults retain a separate inference-fact snapshot
for each generated definition, even though their diagnostic source spans are
shared. Construction reads that snapshot rather than whichever copied body was
inferred last. An inherited body has a lexical owner derived from
the resolved source aspect method, nominal target identity or record-target group, canonical implementation
module and a pair-local variant ordinal. The implementation module prevents
cross-module collisions between disjoint variants. Its locals are allocated
under that owner while source-global references preserve their frozen resolution.
This is identity allocation for generated declarations, not renewed semantic
resolution or symbolic body reconstruction by an analysis consumer.

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

The abstract closure type retains its callable signature and owned environment
types separately. A callable signature alone cannot recover capture ownership;
using inference's provisional function-use axis would misclassify Copy capture
environments. Local aliases and nested captures preserve the environment
contract. Omitted capture lists retain definition-time free-local entry facts,
with a separate snapshot for each closure even when transitive uses share source
spans. They require Copy evidence rather than silently treating an unlisted
non-Copy capture as a legal clone.

### Ownership consumer

Move checking walks the abstract operations using the same place/control-flow
model as concrete typed bodies. Its aspect queries use only declared facts and
structural entailments. An unbounded parameter is not `Copy`; a parameter granted
`Copy` is. A row is structurally `Copy` only when every known field and its unknown
tail have the required evidence. Borrowing versus consumption is recorded at the
typed call boundary, not rediscovered by resolving methods on placeholders.

Definition-time path selections retain static-member owner and enum-variant
identities, including bare unit variants resolved from an expected type. Method
contracts retain the receiver mode of the selected conditional definition, not
the last registered method with that spelling. Prelude nominal identities are
resolved in their declaring `std::core` module when schemes enter inference.
Built-in array length retains a borrowing operation; a temporary array still
consumes its construction inputs. Contextual integer indices retain the literal's
`u64` expectation without converting arbitrary signed bindings.

Zero-label row subtraction is a typed equality shared by preparation and
ownership. Pattern preparation follows those equivalence classes and chooses a
decomposition granting the requested fields, including chained and alternate
equations. Removing every known head leaves its exact abstract tail. Body-only
associated projections receive definition-local parameters with their originating
aspect/member relationship; declared member bounds resolve in the aspect's
declaring module. If inference combines distinct associated results into one
solved variable, all projection origins survive the handoff. Ownership grants
are the intersection of those origins' declared bounds, never whichever member
was visited last. The intersection compares resolved aspect identities, not alias
spellings. This prevents branch-order-dependent `Copy` permission without
asserting an equality between otherwise independent associated members. None of
these parameters alter caller-visible quantifiers.

Method-definition retention does not depend on the caller-polymorphism test.
A method's declared parameter can occur only in a closure or another body
operation, so a monomorphic callable signature still retains a definition-local
binder and its positive/negative bounds. The richer call-visible scheme, when
present, supplies its additional row and associated-equality facts separately.
Definition-only row equations also retain their source/remainder relation when
neither row is a caller quantifier; otherwise a body-local closure could lose a
field-wise ownership grant merely because its enclosing method is static.

Record-target aspect methods also retain definition-local bodies, independently
of calls and runtime reconstruction. Their abstract `Self` remains distinct from
the target's row tail: the target describes fields but may accept a nominal
receiver. In particular, field-wise `Copy` evidence cannot grant nominal `Copy`,
and method-owned generic names cannot be aliased to the enclosing receiver.
At a bounded generic method call, inference retains the solved instantiated
callable contract; this carries a method-owned variable's resolved enclosing
argument into ownership analysis without re-instantiating it or sampling a
caller.
For a blanket implementation, the target `T` freezes as the implementation
binder's abstract parameter rather than an identity-less nominal spelling. Its
ownership analysis therefore uses the declared parameter facts directly.
An open record-kind parameter retains the fields proved by its bound and an
opaque self tail for a trailing-discard record pattern with no remainder
binding; this retains no claim about unnamed fields or an independently
bindable remainder.
Their destructuring operations retain the pattern-specific field/tail shape
selected by inference, not a replacement type for `Self`. A nominal record
shape is instantiated from its carried declaration identity and its fields
keep their `FieldId` selections; no bare-name lookup supplies that shape.
Unknown nominal
destructor absence remains a pending ownership obligation; a structural shape
or field-wise `Copy` cannot discharge it. Candidate provenance follows the
selected declaration across registry merges, not its module-local solver
variable numbers.

Open nominal-projection parameters retain their selected head fields as
definition-only row facts. This lets a generic body type-check and analyze
`receiver.field` from the declared residual shape without adding a structural
row requirement to the caller-visible scheme or erasing the nominal projection
contract at call sites.

Nominal ownership queries retain coherence evidence alongside the body. During
migration, the handoff can prove absence of nominal `Copy`/`Drop` candidates by
resolved type identity, including blanket and record-target candidates. A missing
declared grant is not proof that a conditional destructor cannot apply. Existing
name-keyed positive impl tables do not preserve concrete target patterns or
aspect identities. Registration therefore separately retains resolved target and
aspect identities for unrestricted impls: a nongeneric target, or a bijection
between unconstrained impl parameters and all target arguments. Concrete, nested
or repeated arguments, kind restrictions and conditions cannot certify this
universal fact. Every conditional or negative candidate also retains its aspect
identity, including aliases; record-target candidates block only record kinds.
Unproved candidates remain pending rather than granting ownership permission or
destructor absence. Ownership consumes the retained result; it
does not repeat registry selection on symbolic samples.
An unproved field-wise `Copy` candidate on a nominal `record` is the narrow
consuming exception: the operation records a move, never a `Copy` grant. This
keeps generic ownership conservative while conditional destructor absence stays
pending.
Conditional nominal candidates additionally retain polarity and resolved aspect
conditions indexed by target argument, not impl parameter declaration order.
Named-struct match patterns retain their resolved struct and field identities
with the solved binding types, so the frozen body never depends on the parser's
pre-inference ambiguous one-segment pattern spelling.
Tuple patterns retain their recursive shape and consumer operations descend
through tuple projections, rather than moving the enclosing scrutinee merely
because one element binds.
Inference creates nominal impl receivers with the resolved target declaration
identity, including inherited default methods. This identity survives into the
abstract body even for consuming receivers; ownership does not recover it by
looking up a receiver's spelling.
Named receiver calls use that identity to select method signatures, candidate
schemes and their declaration spans, and receiver modes. A caller's imports
must not redirect a known receiver to a different same-named declaration.
For a bijection of ordinary impl parameters and target arguments, inline and
ordinary `where` aspect-only conditions can be discharged or disproved by the
definition's retained positive or negative parameter grants. All conditions are
conjunctive, including repeated `where` constraints on one parameter. A disproved
condition defeats unknown siblings; missing or contradictory grants remain unknown.
An applicable negative impl overrides positive blanket candidates. A positive
grant requires an applicable positive candidate and disproved negative candidates;
absence requires every positive candidate to be disproved, or an applicable
negative override. An unproved condition never proves destructor absence.
Specialized targets, kind restrictions, row equations, field-wise conditions and
associated bindings remain pending in this proof slice; every unsupported
candidate blocks a conditional proof.
Absence concerns the builtin ownership aspects: graph coherence's orphan rule
prevents an importing module from adding builtin `Copy` or `Drop` to a foreign
nominal type, and the type-owning module registers its complete declarations
before freezing. A later same-named local marker is not a builtin ownership grant.

The current shared flow lattice has textual roots. The abstract consumer adapts
resolved binding identities into injective internal root keys and translates
them to source names only when rendering diagnostics. This adapter does not
resolve names or merge shadowed bindings. Completed abstract-definition visits
are recorded explicitly in the analysis report. During migration an unsupported
operation or entailment rolls back the attempted analysis before the legacy path
runs; partial results are not reported as a completed abstract-body check.

Written callable boundaries retain an explicit callable-view operation: its
operand retains the closure's environment and evaluation effects, while its
result retains the declared function type. Ownership consumes the source once
and uses the destination multiplicity for subsequent slot uses, never recovering
capture-derived `Copy` through an erased environment. This represents the
existing first-order callable conversion, not a general coercion rule.

Declared value boundaries retain solved source/target pairs, including multiple
boundaries at the same span. Abstract read-copy requires this evidence and a
definition-time `Copy` proof for the peeled referent, and observes rather than
moves its source. A mutable-to-shared reference view at an ordinary declared
boundary consumes its source reference instead. Neither operation substitutes
for call-site reborrowing or recovers ownership evidence from runtime types.

Sized-array-to-view boundaries retain a distinct view operation: source places
are observed, while temporary construction inputs are consumed once. The view
is unconditionally `Copy`; the sized owner still requires field-wise element
`Copy`. View copying does not grant ownership of indexed elements. A retained
zero-length array with a bottom element may enter its declared view without
sampling the generic target element type.
At calls, the retained selected signature supplies the expected view type.
Array dispatch additionally retains the receiver kind, so receiver conversion
does not invent mutable access or move the owning array. Explicit call type
arguments constrain fresh callee identities during inference rather than
being recovered from empty literal elements during reconstruction.

For implicit parameters, definition-inferred obligations also participate in
the judgment where the language already specifies their inference. The artifact
does not change the legality rules for explicitly declared parameters.

The final migration removes symbolic AST reconstruction from ownership analysis
for all definitions in the implemented language. Absence of skip warnings alone is not enough: tests
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

Completion of #273 requires analysis of every valid body in the currently
implemented language, including unused generic definitions and embedded standard
library bodies. There is no permanent supported subset or best-effort success
mode. Pending operations and legacy reconstruction are migration work, not
accepted exclusions.

Under `--move-check`, successful analysis means every body was checked and no move
violation was found. An unexpected inability to analyze stops execution with a
distinct compiler-analysis diagnostic. It is not a demonstrated `T0019` move
violation. Reports may retain partial findings and unchecked-body details for
tooling, but an incomplete report cannot authorize execution under this flag.
Default mode remains unchanged.

The diagnostic is a defensive safeguard against implementation regressions or a
future feature lacking ownership integration, not a substitute for eliminating
the current gaps. Conservative loop-analysis precision remains #272's concern;
it is distinct from failing to analyze a body.

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
   enforce the completeness contract, and update limitation/architecture
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
