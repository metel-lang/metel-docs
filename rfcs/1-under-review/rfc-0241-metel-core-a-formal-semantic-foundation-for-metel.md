---
id: rfc-0241
title: "Metel-Core: A Formal Semantic Foundation for Metel"
date: '2026-11-17'
status: under-review
updated: '2026-11-20'
tracking: metel-core#2095
---

> **Status — under review (2026-11-20).** Open milestoned tracking issue; PROCESS.md requires review

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

Metel-Core is proposed as a formal language, not necessarily as a production compiler intermediate representation; reusing it
as a typed IR is a possible later direction (section 8.3).

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
self-hosted toolchain needs further architectural decisions. This stays exploratory.

### 7. Incremental milestones

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

### 8. Proposed initial outcome

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

---

## Risks and tradeoffs

- **Formalization complexity.** Ownership and borrowing are hard to formalize, especially with partial moves, custom reference
  abstractions and resource-dependent validity. The project may need substantial research and iteration.
- **Design instability.** Metel is still evolving, and changes to fundamental concepts may require revising the model and its
  proofs. Incremental development and careful modularization reduce the cost.
- **Divergence from implementation.** A verified model does not guarantee that the compiler implements the same semantics.
  Keeping them in correspondence needs dedicated validation work.
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
23. Should Metel-Core become a production compiler IR?
24. How can the formalization best support a self-hosted compiler?

---

## Decision

**Outcome:** *(pending)*
