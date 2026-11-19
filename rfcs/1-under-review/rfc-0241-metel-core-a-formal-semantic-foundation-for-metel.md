---
id: rfc-0241
title: "Metel-Core: A Formal Semantic Foundation for Metel"
date: '2026-11-17'
status: under-review
updated: '2026-11-19'
tracking: 'https://github.com/metel-lang/metel-core/issues/2095'
---

> **Status — under review (2026-11-19).** Committed to the roadmap as the Core representation theme (2026-11-19, #2095)

## Summary

This RFC proposes **Metel-Core**, a minimal, explicitly typed language that serves as the formal semantic foundation of Metel.
Metel-Core would define the computational, typing, ownership and memory-access semantics of Metel independently of its
user-facing syntax and of any implementation.

The RFC also proposes a long-term strategy for formalizing Metel-Core in Lean 4, with the eventual goal of machine-checked
soundness properties. The formalization is developed **alongside** Metel's evolution, not as a verification effort undertaken
after the design is complete.

The objectives are:

1. A precise mathematical definition of Metel's semantics.
2. A framework for evaluating language-design proposals, especially ownership and borrowing.
3. Machine-checked proofs of type soundness and memory safety.
4. Executable reference implementations of language algorithms.
5. Support for an eventual self-hosted Metel compiler, without tying the formal specification to the compiler's implementation
   language.

Metel-Core is proposed first as a formal language. This draft also explores making it the compiler's own typed representation
layer, so that the formal model and the implementation share one calculus and cannot drift apart, and so that the compiler can
grow toward compiled code in layers without waiting on the borrow checker (section 7). That direction is exploratory; its
design choices are open (Open questions 25 to 33).

This is a design draft, direction-setting and not syntax. It fixes the architecture and the research goals and does not attempt
to finalize the calculus. Nothing here is accepted. Implementation: not started.

---

## Motivation

### 1. The need for a formal semantic model

Metel includes or proposes several features whose interactions are hard to reason about informally:

- Affine ownership and move semantics.
- Partial moves and structural ownership.
- Shared and exclusive borrowing.
- Structural disjointness of places.
- Non-lexical borrow lifetimes.
- Origins and validity dependencies.
- Generative brands and resource identities.
- Library-defined reference abstractions.
- Algebraic effects and effectful allocation.

Each can be described through implementation rules and examples. Their interaction raises questions that informal reasoning
answers badly:

- Under what conditions can two exclusive references coexist?
- What information must be preserved when a partially borrowed value crosses a function boundary?
- How can a library safely construct references to memory it manages?
- How can an arena expose independently mutable allocations without runtime borrow checking?
- What exactly does an origin parameter guarantee?
- Which guarantees belong to the type system, and which are obligations of unsafe library code?

A formal model gives one framework for these questions. Features become explicit rules that can be checked against stated
invariants, instead of intuition or compiler behavior.

### 2. Formalization as a language-design tool

The formalization is not only meant to verify a finished language. It should help develop it. Formalizing a feature often
exposes assumptions that stay implicit otherwise. Formalizing library-defined references, for example, may show that the
language has to distinguish:

1. The identity of a memory allocation.
2. The authority to access that allocation.
3. The conditions under which the allocation remains valid.

These are related and not interchangeable. A formal model can make the distinctions explicit and ground the language constructs
that correspond to them.

### 3. Long-term compiler independence

Metel's long-term goal includes self-hosting: the production compiler written in Metel. The semantic specification should
therefore not depend on a particular compiler implementation. A Lean formalization can remain the authoritative reference model
while the compiler evolves independently, so that implementation decisions can change without changing the semantic definition.

---

## Proposal

### 1. Architecture

Three conceptual layers:

```text
         Surface Metel
               |
               | Elaboration
               v
          Metel-Core
               |
               | Operational semantics
               v
        Abstract Machine
```

**Surface Metel** is the user-facing language: type inference, syntactic sugar, user-facing borrowing syntax, generic
abstractions, high-level control flow, and other features that may be elaborated into simpler representations. It need not expose
every distinction Metel-Core represents internally.

**Metel-Core** is a smaller language with explicit typing and operationally meaningful constructs. It represents the essential
semantics of Metel while minimizing unrelated syntactic complexity. Potential characteristics:

- Explicit type annotations.
- Explicit ownership operations.
- Explicit place projections.
- Explicit borrowing and reborrowing operations.
- Explicit origin and dependency information.
- A small collection of primitive computational constructs.

It should be expressive enough to represent the relevant behavior of Surface Metel without reproducing every surface feature.
The degree of explicitness is an open question: a move could be an explicit operation or follow from a consuming expression, and
loan creation and termination could be explicit in Metel-Core while implicit in Surface Metel.

**The abstract machine** defines how Metel-Core programs execute, with enough state to express and verify the safety guarantees.
Potential components: heap allocations and allocation identities, values and local environments, initialization and ownership
state, places and their projections, active access permissions or loans, resource validity and destruction, evaluation state.
It need not correspond to a physical machine or to the production compiler's runtime representation. Its purpose is a precise
definition of program behavior.

### 2. Initial language scope

Metel-Core is developed incrementally. Formalizing the whole language at once would add complexity and make it hard to isolate
the source of a proof failure.

#### Stage 1: basic computation and ownership

- Primitive values and operations.
- Local bindings.
- Function calls.
- Struct construction and field projection.
- Affine values.
- Moves and partial moves.
- Initialization and destruction.

This stage establishes the relation between values, places and ownership. A central question is how ownership is represented in
the formal machine: encoded in typing environments, as explicit ownership state in the abstract machine, or as static ownership
judgments combined with dynamic resource state. The model has to support partially initialized aggregate values.

#### Stage 2: borrowing and structural access

Shared and exclusive access, place-based borrowing, structural disjointness, reborrowing, suspension of parent access, and
non-lexical loan liveness. Two exclusive borrows of disjoint fields are permitted:

```text
let left = &var value.left;
let right = &var value.right;
```

The formalization has to define why these accesses are compatible. Overlapping exclusive accesses have to be rejected or
otherwise prevented. The rules account for nested projections and reborrowing instead of treating every borrow of a composite as
indivisible.

#### Stage 3: origins and validity dependencies

Origins express dependencies between values and the storage or resources they rely on. The notation `@a` below names an origin
and is illustrative:

```text
fun borrow<@a>(value: &T@a) -> &T@a
```

The model distinguishes the **validity** of a reference from the **permission to access** its target. A reference may depend on
several resources remaining valid without borrowing all of them exclusively. This matters for custom allocators and
library-defined reference types.

#### Stage 4: brands and generalized access

Generative brands, provisionally written `'b`, represent resource-domain identities. The three notions have different roles:

- **Brands** identify generatively distinct resources or domains.
- **Origins** express validity dependencies.
- **Access witnesses** establish authority to access particular memory locations.

A brand shared by two pointers does not imply that they refer to the same allocation. A shared brand does not establish that
they refer to distinct allocations either. The formalization has to preserve both facts.

### 3. Library-defined references

A principal motivation for Metel-Core is a rigorous foundation for library-defined reference abstractions.

#### 3.1 General idea

Instead of making every reference abstraction a compiler primitive, Metel could expose a minimal set of trusted access
operations and let libraries build reference-like types from them. The surface types `&T@a` and `&var T@a` could correspond
conceptually to `Ref<T, @a>` and `RefMut<T, @a>`, containing or depending on compiler-tracked access witnesses. The exact
representation and public API are not specified here.

#### 3.2 Access witnesses

An access witness represents authority to access a target under specified permissions:

```text
AccessWitness<T, @a, Shared>
AccessWitness<T, @a, Exclusive>
```

A witness carries or preserves enough information to establish:

- The identity of the accessed allocation or place.
- The permitted form of access.
- The validity dependencies of the target.
- The relationship to any parent access authority.

The model has to prevent safe code from manufacturing incompatible access permissions. Potential primitive operations: acquiring
access from an owned place, projecting access onto a field, reborrowing existing access, and establishing access through an
explicitly unsafe operation. The trusted primitive API is kept as small as practical.

#### 3.3 Separating access from validity

Take an arena allocator holding several allocations. A mutable reference to one allocation depends on the arena staying alive. It
should not necessarily need exclusive access to the whole arena. So: **the resources required to keep an access valid are not
necessarily the resources being borrowed.** Metel-Core's semantics represents this separation explicitly.

### 4. Arena allocation as a motivating case study

An arena allocator tests the model. Take a copyable pointer type `ArenaPtr<T, 'b>`, whose brand associates it with an arena
domain. Two copies of an `ArenaPtr` may refer to the same allocation, so the brand alone cannot justify constructing independent
exclusive references from arbitrary pointers.

#### 4.1 Affine allocation authority

A possible solution is an affine allocation handle `ArenaBox<T, 'b, @a>`. It owns the authority to access one arena allocation:
the arena owns the storage, and the handle is unique authority over a particular allocation.

```text
let first = arena.alloc_owned(10);
let second = arena.alloc_owned(20);

let a = first.borrow_mut();
let b = second.borrow_mut();
```

Both exclusive references are valid at once because the handles stand for distinct allocations. The implementation has to
guarantee that independent live handles never confer conflicting exclusive authority over one allocation.

#### 4.2 Validity dependencies

An `ArenaBox` also depends on its arena staying valid. A borrowing operation could be written, illustratively:

```text
fun borrow_mut<@self>(
    self: &var Self@self
) -> &var T@(self | a)
```

The result depends on both the borrow of the handle and the arena's storage validity. The formalization should help decide
whether the dependency is best represented by explicit origin unions, type-level validity constraints, storage-dependency
declarations, or another mechanism.

#### 4.3 Proof obligations

A sound implementation has to establish:

- Unique authority for each owned allocation handle.
- No duplication of affine allocation authority.
- Stability of the underlying storage while references exist.
- Prevention of premature arena destruction or reset.
- Correct handling of reborrowing.
- Compatibility of exclusive accesses to distinct allocations.

### 5. Lean 4 formalization strategy

#### 5.1 Declarative specification

Begin with declarative definitions: inductive definitions of syntax and types, typing and ownership judgments, well-formedness
judgments, operational transition relations, heap and access-state invariants. Declarative judgments say which programs and
operations are valid independently of how a compiler decides it.

#### 5.2 Executable algorithms

Where practical, also define executable checking algorithms in Lean, and prove that successful checking corresponds to the
declarative typing relation. Illustrative, not complete Lean:

```text
def checkExpr (env : Env) (expr : Expr) :
    Except CheckError Ty := ...

theorem checkExpr_sound
    (h : checkExpr env expr = .ok ty) :
    HasType env expr ty := ...
```

The executable model can serve as a reference implementation for testing the production compiler.

#### 5.3 Soundness properties

The first proof effort targets foundational properties:

- **Preservation.** A well-typed machine state that takes a valid step stays well-typed and satisfies the required invariants.
- **Progress.** A well-typed program is in an accepted final state or can make progress, subject to the language's explicit error
  and effect semantics.
- **Memory safety.** Safe programs cannot access destroyed or invalid storage, read uninitialized values, use moved values, or
  violate exclusive-access guarantees. These may need explicit invariants beyond preservation and progress.

#### 5.4 Trusted operations and unsafe code

The formalization distinguishes (1) guarantees established by the safe language, (2) preconditions required by unsafe operations,
and (3) obligations of libraries implementing unsafe abstractions. An unsafe operation that establishes an access witness is not
treated as universally sound without its preconditions. The model states the trusted assumptions explicitly. A later effort could
verify that particular unsafe library implementations satisfy them.

### 6. Relationship to the production compiler

**Independent reference model.** The Lean formalization stays independent of the production compiler. The compiler can eventually
be written in Metel while Lean continues to define the reference semantics, and the two projects evolve with different priorities.

**Differential testing.** Executable Lean algorithms can be compared with the compiler on the same test programs:

```text
          Test Program
             /     \
            v       v
    Lean Reference  Metel Compiler
            \       /
             v     v
          Compare Results
```

This finds discrepancies between the implementation and the model. It is not a proof that the compiler is correct.

**Metel-Core as a typed IR** (exploratory). Metel-Core, or a representation close to it, could be an intermediate representation
in the production compiler, so that a small checker validates the output of elaboration and inference:

```text
Surface Metel -> Inference and Elaboration -> Typed Metel-Core
              -> Metel-Core Checker -> Lowering and Code Generation
```

A checker implemented and verified in Lean could establish properties of accepted Metel-Core programs. It would not verify the
backend, and it would not show that elaboration preserves the meaning of Surface Metel. Using it in a strictly standalone
self-hosted toolchain needs further architectural decisions. Section 7 develops this direction in more detail. It stays
exploratory.

### 7. Metel-Core as the compiler's representation layer

Section 6 left use as a compiler IR as a possible later direction. This section sets out what that direction would involve and
why it may be worth taking early. It does not decide the calculus; the unresolved choices are listed as options and in Open
questions 25 to 33.

The motivating observation is that the formal calculus and the compiler's IR need not be two things. One Core with an
executable reference evaluator is what ties the formal model to the implementation (the differential testing of section 6),
and it gives the compiler a place to run checks that do not depend on inference state. It also lets compiled execution be
reached in layers, each of which erases the checks of the layer above, without the borrow checker or the origin machinery as a
prerequisite (section 7.5).

#### 7.1 Layers

| Layer | Content | Checks that run on it |
|---|---|---|
| L0 Surface AST | parse tree | syntax |
| L1 Typed surface | the typed AST of today: surface-shaped, for diagnostics | type errors |
| **L2 Metel-Core** | desugared and fully type-annotated; closures with explicit environments; dispatch explicit; no inference state | a well-formedness lint; the formalized judgments |
| L3 Instances | monomorphised and keyed (the "Instance preparation" roadmap theme) | none |
| **L4 Ownership-explicit** | moves, copies, clones and drops as explicit operations, with drop flags | move check, then borrow, origin and linear checks as they are settled |
| L5 Backend | bytecode, C, wasm or an engine bridge | none |

Each lowering is a function. A statement that it preserves meaning is a candidate proof obligation (milestone 8). The existing
pattern of a witness type per completed pass (`ElaboratedModuleGraph` records that elaboration ran) generalizes to one witness
per layer.

#### 7.2 The implementation today (observed 2026-11-19)

From `metel-frontend` (`data/typed_ast.rs`, `pipeline/`):

- There is no core IR. The interpreter evaluates the typed AST directly, and elaboration only resolves `MethodDispatch` per
  call site.
- A generic body is checked at its definition for diagnostics but is not typed once for use: a `GenericClosure` keeps its body
  untyped "for runtime re-evaluation at each call site's concrete type", and generic function bodies are reconstructed per
  instance at runtime (`construct_generic_body`). The generic-body defects tracked from metel-core#1704 (a reconstruction with
  empty inference facts) look like one class with this as the cause. That is a hypothesis to verify, not an established fact.
- Identity is partial. `Ident`, `Path`, `FieldAccess` and `Call` carry `Option` identities that are `None` when no identity
  context was available, and method dispatch can be chosen by a declaration span (`impl_site`) and a name.
- Surface forms leak into typed nodes: `Cast` holds a `TypeExpr`, and closures hold surface parameters.
- Some of Core already exists: coercions are explicit (`SingletonCoerce`, `RowCoerce`, `DynCoerce`), closures carry their call
  multiplicity and mutation, and places are a distinct node (`TypedPlace`).
- Row types (`Record`, `OpenRecord`, `SymbolicRow`) and reference types (`Reference`, `MutReference`) are ordinary types; the
  reference types have no region slot.

#### 7.3 Design rules for Metel-Core

- **Total.** Every identity is present. A missing one is an internal error from the lint. Names live in a side table for
  printing only.
- **No inference state and no surface types.** Every binder and node carries a resolved type.
- **Definite dispatch.** A call targets a function identity or a dictionary projection, never a name or a span.
- **Structured.** Loops, `break`, `continue` and `return` stay as labelled constructs. A control-flow graph belongs to L4, if
  and when borrow checking needs one.
- **A dynamic meaning for moves.** Semantics over a store of locations, where a move leaves its slot uninitialized. The static
  move check is then the statement that no accepted program reads an uninitialized slot.
- **Reserved extension points, not features.** A region slot on reference types (to be filled by whatever RFC-0159 settles),
  a predicate slot on types (section 7.9, RFC-0202), effects entering only through `call`, and rows kept in the type language.

#### 7.4 Sketch

Illustrative only; neither the constructs nor their spelling are proposed here.

```text
types   t ::= prim | Named(NominalId, ts) | Record(row) | Array t | Sized(t, n)
            | Ref(q, t)                 q in {shared, excl}; later Ref(q, region, t)
            | Fun(call_mult, call_mut, ts -> t) | Dyn(aspect) | Never
            | a | forall a. D* -> t     reserved in the datatype; see 7.7

terms   e ::= lit | local(LocalId) | global(FunId, ts, dicts)
            | let x : t = e in e
            | call(e, es)               the only place effects can later enter
            | closure(FunId, env*)      explicit environment, capture modes resolved
            | ctor / proj(FieldId) / variant(VariantId, es)
            | match e { p => e }        nested patterns kept; first match wins
            | loop / break / continue / return     labelled, structured
            | coerce(kind, e)           Singleton / Row / Dyn
            | dict(InstId, dicts) | dict_proj(d, MethodId)

places  p ::= local | proj(p, FieldId) | index(p, e) | deref(e)
ops       read(p)   ref(q, p)   assign(p, e)
```

Desugarings worth stating: `?` becomes `match` plus `return`; operators and method calls become `call` of a resolved function
identity; a `GenericClosure` becomes a type abstraction around a closure, typed once; `dyn` is an existential package of a
dictionary and a value, introduced by `DynCoerce`; `&<rvalue>` (`RefTemp`) becomes a `let` of a temporary plus a `ref`; a panic
is `Never`, consistent with panics being uncatchable (RFC-0153 section 1a).

#### 7.5 Ownership as a filter, not a prerequisite

If the language has value semantics, a checker is a filter and not an input to code generation: a program accepted by any
checker means the same under the reference semantics. Ownership analysis then becomes an optimization layer (in-place moves
instead of copies) and a safety layer, and a compiled profile need not wait on it.

- References that cannot be stored need no lifetimes and compile to plain pointers. A borrow checker later is a pass that only
  rejects programs.
- Drop order is observable, so it needs move tracking. Dynamic drop flags are the fallback until static analysis exists.
- Linear checking is check-only and erased at code generation.

The theorem shape this suggests for the first proof effort: a well-typed, move-checked Core program never reads an
uninitialized slot. This section does not replace Stages 2 to 4. Borrowing, origins and brands remain the formalization's
substance. It says that the compiler's progress toward compiled code is not gated on them.

#### 7.6 Staging

Each step can ship on its own:

1. **Define Core and its lint**, lowered from the typed AST, with a textual dump. The interpreter is untouched.
2. **A Core evaluator**, run differentially against the existing fixture corpus, which acts as the oracle. The spec's numbered
   Legality and Dynamic Semantics rules and the fixtures that cite them are the link between the formal rules and the
   implementation. The same evaluator is what compile-time execution needs before any code generation exists (the Comptime
   theme, RFC-0132). It also gives the "Runtime value semantics" theme a place to make copying and moving explicit.
3. **Explicit ownership operations (L4)**, with move checking re-expressed over them, which is where "Move check default-on"
   would get cheaper.
4. **Instances and a thin backend** for a subset: the "Instance preparation" and "Compiled kernel experiment" themes, with the
   borrow checker absent and drops tracked dynamically. "Compiled profile v0" is not this step: its exit includes the compiled
   Godot bridge, which waits on the freeze and Interop.

None of this depends on the core-surface freeze, because Core is internal.

#### 7.7 Options for generics (none chosen)

| Option | What it is | For | Against |
|---|---|---|---|
| A. Polymorphic Core | System F with dictionary parameters; each generic body typed once | removes the reconstruction defect class; clean to formalize; dictionaries are the "stored ownership interfaces" of the Abstract ownership solver theme | the checker must emit a witness for every bound use, which it does not today; largest work item |
| B. Monomorphic-only Core | Core exists per instance only, taken from the existing reconstruction | cheapest; reuses what exists | the defect class stays in L1 |
| C. A, then monomorphization as a pass | polymorphic L2, specialization as L2 to L3 | the principled end state | same cost as A |

One way to keep A or C reachable while starting at B: put the quantifier and dictionary nodes in the Core datatype from the
start, have the first lowering emit only monomorphic instances, and have the lint reject the reserved nodes until they are
enabled. A side effect is that a reconstructed instance that has lost a type then fails the lint loudly instead of being wrong
silently. The formalization could stage the same way: a simply typed calculus with records, closures and a store first, then
polymorphism and dictionaries. Whether to do this is Open question 25.

#### 7.8 Roadmap placement (decided 2026-11-19)

These are scheduling decisions, taken by the language owner, and they bind the roadmap, not the calculus. Every design choice
in this RFC, including Open questions 25 to 33, stays open. Tracked in metel-core#2095.

1. **Core representation is a theme in `next`**, ordered directly after Move check default-on. It holds steps 1 and 2 of
   section 7.6 (Core and its lint; the Core evaluator run differentially against the fixture corpus). Step 3 is its own theme,
   **Ownership-explicit core**, ordered after Comptime.
2. **Runtime value semantics (metel-core#277) is folded into Core representation.** The evaluator that stops deep-cloning is the
   Core evaluator. The separate milestone is closed.
3. **Instance preparation and Compiled kernel experiment are pulled ahead of Borrow checking** (both move from `later` to
   `next`). Compiled profile v0 itself stays behind the freeze, for the reason in section 7.6 step 4.
4. **The roadmap has an explicit design lane.** Themes whose exit is accepted RFCs may have their settlement run in parallel with
   the implementation chain once their design prerequisites are met; implementation then joins the chain at the theme's numbered
   position. The numbered order stays the single priority order.

The resulting order after Move check default-on is: Core representation, Comptime, Structural kinds after comptime,
Ownership-explicit core, Instance preparation, Compiled kernel experiment, then Reference rules (B0), Borrow checking and the
effects, storage and freeze themes as before.

#### 7.9 Refinement as a later Core extension (exploratory)

RFC-0202 (predicates and refinement types, under review, metel-core#2098) is the surface design. This section records where its
extension points, a flow-sensitive refinement and a decision procedure, would sit on Metel-Core, and what Core has to leave room
for now. Nothing here is decided and none of it is built.

**What RFC-0202 already fixes.** A predicate is a pure, total, compile-time-evaluable expression. An obligation is a goal with a
three-valued answer (Proved, Refuted, Unknown), and Unknown is an error. A solver can only turn Unknown into Proved, so
acceptance grows monotonically and the meaning of a predicate never changes. Decision procedures are specified in the language,
in-tree, with no heuristic search and no time limits; an external SMT backend is at most an opt-in tool outside the language
definition.

**Where each part lives.**

| Part | Layer | Note |
|---|---|---|
| `satisfying` predicates, sealed types, row predicates | L0 and L1 | RFC-0202 as written |
| A predicate slot on types | L2 | reserved, not filled |
| Verification-condition generation | a pass over L2 | wants every intermediate result named |
| Facts through mutation and references | L4 | needs ownership information |
| A discharged obligation used to drop a runtime check | L4 to L5 | proofs as an optimization |

**Staging.** Predicates on by-value, immutable data need no borrow checker (RFC-0202's sealed types, evaluation-only discharge).
Flow facts about local variables need only move and assignment tracking, which Core's dynamic semantics already has: a write to a
`var` kills the facts about it, and a fact about a sealed value lives in its type (RFC-0202 open question 1). Facts through
references wait for borrow checking. This is the same order as section 7.5: the refinement checker is a filter, and a compiled
profile does not wait on it.

**What is not borrowed from Liquid-style systems.** Inference of refinements by qualifiers makes acceptance depend on a heuristic
fixpoint, and general SMT makes it depend on a tool's version and timeouts. Named declarations already write every parameter
(RFC-0193), so signature refinements can be written and only body facts need path conditions. A language-specified fragment, for
example linear integer arithmetic or RFC-0202's label-set theory, can be formalized and verified in the Lean project of section
5; Lean 4's own `omega` is an example of that kind of procedure, not a proposed dependency.

**What Core has to leave room for.**

- A predicate slot on types, reserved the way section 7.3 reserves the region slot, and erased at L3.
- A shape that names intermediate results. Verification-condition generation wants that, which is an argument for A-normal form
  in Open question 28.
- A single facts environment, possibly shared between the move check (ownership state) and refinement (flow facts), over
  Core's explicit guards. That sharing is a hypothesis to test (Open question 33); the move check already does path-sensitive
  narrowing (RFC-0117).
- Polymorphic Core if a function is generic over a predicate, with predicates as type-level terms, which bears on Open question 25.

### 8. Incremental milestones

Indicative, not a committed roadmap:

1. **Minimal calculus.** A small functional language with explicit types and evaluation semantics; basic preservation and
   progress.
2. **Ownership.** Affine values, moves, destruction, partial moves; ownership invariants and their preservation.
3. **Borrowing.** Places, shared and exclusive access, structural disjointness, reborrowing; the access-safety invariants.
4. **Origins and brands.** Validity dependencies and generative resource identities; their relation to ownership and borrowing.
5. **Library-defined references.** Access witnesses and trusted access operations; soundness of abstractions built on them.
6. **Arena case study.** An arena with affine allocation handles; independently owned allocations borrowed exclusively without
   violating memory safety.
7. **Executable checking.** Reference algorithms and their soundness against the declarative model.
8. **Surface-language correspondence.** Elaboration from Surface Metel into Metel-Core and the preservation of typing and
   semantics.

Milestones 1 and 2 are the formal counterparts of steps 1 and 2 of section 7.6, and milestone 8 is where the lowering-preservation
statements of section 7.1 belong.

### 9. Proposed initial outcome

The first phase establishes a concrete design for Metel-Core, not a proof of the whole language. Initial deliverables:

1. A documented architecture separating Surface Metel, Metel-Core and the abstract machine.
2. A proposed minimal syntax and type system for Metel-Core.
3. A definition of the initial operational semantics.
4. A plan for representing ownership and borrowing.
5. A proposed Lean 4 project structure.
6. A small set of initial proof objectives.
7. A list of assumptions and unresolved language-design questions.

Implementation and proof development follow only after these are sufficiently clear. The immediate next step is to define the
smallest useful version of Metel-Core and the invariants it should preserve.

---

## Interaction with other work

This RFC does not change the language and does not decide any of the designs below. It is a vehicle for evaluating them.

- **RFC-0122** (under review, borrow checking), **RFC-0067** (under review, lifetime anchors) and **RFC-0159** (under review,
  abstract regions and a dedicated identity channel): the borrowing, origin and region designs the formal model would check.
  RFC-0159 already separates lifetimes, brands and storage identity as roles over one substrate and holds its own notation; the
  `@a` and `'b` spellings here are illustrative and follow whatever those RFCs settle.
- **RFC-0242** (draft, library-defined references and generalized place access): the language-design companion of this RFC. It
  proposes the access-witness model that Stages 3 and 4 and the arena case study formalize, and this RFC is the vehicle for
  validating it. **RFC-0143** (under review) already proposes a unique arena handle and a disjointness witness that the arena
  case study must be reconciled with.
- **RFC-0076** (under review, brand types) and **RFC-0143** (under review, allocator placement and storage identity): the brand
  and allocation-identity concepts of Stage 4 and the arena case study.
- **RFC-0077** (accepted, allocator generics): the allocator surface the arena case study exercises.
- **RFC-0071** (integrated, ownership and move semantics), **RFC-0089** (accepted, linear types) and **RFC-0091** (under review,
  linear records): the ownership semantics Stages 1 and 2 formalize. Linearity is deferred in the language; the core may begin
  with affine values only.
- **Roadmap themes touched by section 7** (named by theme, since none has a cut version; placement decided in section 7.8):
  Core representation (L2, this RFC's tracking theme); Ownership-explicit core (L4); Instance preparation (L3); Compiled kernel
  experiment (L5 for a subset; Compiled profile v0 stays behind the freeze); Runtime value semantics (metel-core#277, now part
  of Core representation, where copying and moving become explicit); Comptime (RFC-0132, whose execution model needs an evaluator over typed IR before any code
  generation); Abstract ownership solver (metel-core#1821, whose stored ownership interfaces and "witnesses carried to
  elaboration" are the dictionaries of option A in section 7.7); Effects design settlement (Core reserves `call` as the only
  entry point and decides nothing else).
- **RFC-0202** (under review, metel-core#2098, predicates and refinement types): the surface design whose solver and
  flow-sensitive extension points section 7.9 places on Core. Its goal interface is intended to be hosted by the abstract
  ownership solver (metel-core#1821, #1813). Its open question 1 (mutation of a sealed value) and Stage 2 of this RFC (borrowing)
  meet at facts through `&var`.
- **RFC-0206** (Copy and Clone, implemented): the class of a type decides whether a use copies or moves, so Core's use of a
  place has to resolve that, statically for concrete types and through a dictionary for a generic parameter.
- **ADR-0054** (stable identity) supplies the identities Core requires to be total. **metel-core#1704** and the defects
  tracked from it are the evidence for section 7.2's generic-body point; this RFC does not change how they are fixed in a patch.
- **RFC-0028** (refused) and **RFC-0052** (superseded) were earlier memory-model and lifetime proposals; nothing here revives them.

---

## Alternatives considered

1. **Formalizing Surface Metel directly.** Avoids a separate elaboration layer, but couples the formal semantics to syntax,
   inference and high-level features. A smaller core is expected to make the foundational proofs more manageable.
2. **Formalizing the production compiler implementation.** Implementing significant compiler components in Lean and proving them
   correct could give stronger guarantees about the actual algorithms. It would complicate the goal of a compiler written in
   Metel. This RFC favors an independent model and leaves room for verified executable algorithms.
3. **Informal specification with testing.** Prose specifications, compiler tests and implementation-driven validation are cheaper
   at first. They give weaker guarantees about subtle interactions between ownership, borrowing and unsafe abstractions. The
   formalization complements testing and does not replace it.
4. **Keeping Metel-Core a purely formal artifact, never a compiler IR.** Avoids committing the compiler to a calculus that is
   still moving. It leaves the compiler with no representation on which to run inference-independent checks, and it keeps the
   formal model and the implementation as two things that have to be kept in correspondence by testing alone.
5. **A separate compiler IR beside Metel-Core.** The compiler gets a representation shaped for its own needs, free of the
   calculus's constraints. Two cores then diverge, and the differential test of section 6 has to bridge a larger gap.

---

## Risks and tradeoffs

- **Formalization complexity.** Ownership and borrowing are hard to formalize, especially with partial moves, custom reference
  abstractions and resource-dependent validity. The project may need substantial research and iteration.
- **Design instability.** Metel is still evolving, and changes to fundamental concepts may require revising the model and its
  proofs. Incremental development and careful modularization reduce the cost.
- **Divergence from implementation.** A verified model does not guarantee that the compiler implements the same semantics.
  Keeping them in correspondence needs dedicated validation work.
- **Freezing a calculus too early.** Effects, row polymorphism and regions are unsettled. A Core used by the compiler has to be
  explicitly unstable until they are, with extension points reserved (section 7.3) and nothing decided about them.
- **Two evaluators during the transition.** The tree-walking interpreter and the Core evaluator coexist while the fixture
  corpus is run against both. The cost is bounded by the differential run, which is also the check that they agree.
- **Increased development effort.** Formalization adds work to language development. The expected benefit is more confidence in
  the design, clearer specifications, and the possibility of stronger correctness guarantees.

---

## Open questions

**Language representation**

1. How much of Metel's existing type system should appear directly in Metel-Core?
2. Should moves, destruction and loan termination be explicit operations?
3. How are polymorphism and structural types represented?
4. Are effects in the initial calculus or added later?

**Ownership and borrowing**

5. What is the formal representation of partial moves?
6. How is structural place disjointness established?
7. How is non-lexical loan liveness represented?
8. What information must be preserved across function boundaries?
9. How does reborrowing interact with ownership authority?

**Origins and brands**

10. Do origin parameters automatically imply validity dependencies?
11. Are storage dependencies declared explicitly?
12. What is the precise meaning of an origin union?
13. How are brands generated, and how are they prevented from escaping their valid scope?

**Access witnesses**

14. What is the minimal trusted primitive API?
15. How are witnesses represented in the operational semantics?
16. How are permissions and allocation identities tracked?
17. Which operations require unsafe authority?
18. What obligations must custom reference implementations satisfy?

**Verification architecture**

19. How is the Lean project modularized?
20. Which properties are proved first?
21. How can language extensions avoid invalidating large parts of existing proofs?
22. Which checking algorithms get executable Lean implementations?
23. Should Metel-Core become a production compiler IR? Section 7 and questions 25 to 33 develop the case; none is decided.
24. How can the formalization best support a self-hosted compiler?

**Compiler representation (section 7)**

25. Generics in Core: polymorphic with dictionary parameters, monomorphic per instance only, or polymorphic with specialization
    as a later pass (section 7.7)? Can the first datatype reserve the quantifier and dictionary nodes while the first lowering
    emits monomorphic instances only?
26. Rows: how much row polymorphism has to survive into compiled code? Is label-offset evidence needed, or can compiled code
    require closed rows after instance preparation?
27. Semantic model: is a store of locations with moved-from meaning uninitialized the right dynamic meaning, or should moves be
    explicit operations from the start (question 2)?
28. Shape: a structured Core with a control-flow graph only at L4, A-normal form throughout, or a control-flow graph from the
    start? Verification-condition generation (section 7.9) wants every intermediate result named, which favours A-normal form.
29. Effects: is reserving `call` as the sole entry point enough, or does handler control need a representation decision before
    Core is used by the compiler?
30. Placement: a module inside `metel-frontend` reusing its identity types, or a separate crate, and at what point does the Lean
    project need to import the datatype?
31. Proof ordering: type safety of Core first, preservation of each lowering first, or both in parallel?
32. Predicate slot: does Core's type language reserve a slot for a predicate on a type, in what form (an opaque term evaluated by
    comptime, or a term in a fixed logic), and is it erased at L3?
33. Facts: should flow facts (refinements) and ownership state share one facts-environment mechanism over Core, or stay
    separate analyses? Which decision-procedure fragment comes first is RFC-0202's question (its section 5), not this one.

---

## Decision

**Outcome:** *(pending)*
