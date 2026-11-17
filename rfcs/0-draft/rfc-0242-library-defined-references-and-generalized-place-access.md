---
id: rfc-0242
title: "Library-Defined References and Generalized Place Access"
date: '2026-11-17'
status: draft
---

## Summary

This RFC proposes a generalized model of borrowing and memory access for Metel, so that reference types can be defined in
libraries while static memory-safety guarantees are preserved.

The central idea is to separate three concepts that reference types traditionally intertwine:

1. **Access authority:** the permission to read or modify a particular memory location.
2. **Validity dependencies:** the resources that must remain valid for an access to stay safe.
3. **Resource identity:** the identity of a resource or allocation domain, represented by generative brands.

Under this model references are no longer necessarily fundamental compiler-defined types. The compiler provides a minimal set of
trusted primitives for acquiring, projecting and transferring access authority, and libraries use them to implement reference
abstractions such as `Ref<T, @a>` and `RefMut<T, @a>`. The existing surface syntax `&T@a` and `&var T@a` could remain as sugar
for those library-defined types.

The aim is to keep the convenience and safety of conventional borrowing while allowing richer abstractions: arena allocation,
custom pointer types, and possibly garbage-collected storage. A key goal is to support them **without runtime borrow checking**.

This RFC is exploratory. It describes the intended model and identifies the soundness requirements and unresolved questions. It
does not specify an implementation-ready design. Nothing here is accepted. Implementation: not started. It is the language-design
companion of RFC-0241 (Metel-Core), which is the proposed vehicle for validating it.

---

## Motivation

### 1. Limitations of conventional borrowing

Ownership-based borrowing systems associate references with compiler-defined rules for aliasing, mutation and lifetime validity.
That works well for references into ordinary owned values:

```text
let value = Point { x: 10, y: 20 };

let x = &var value.x;
let y = &var value.y;
```

The compiler can establish that `value.x` and `value.y` are disjoint places and allow both exclusive references. The same
reasoning is harder when memory is managed by a custom abstraction. Take an arena:

```text
let first = arena.alloc(10);
let second = arena.alloc(20);
```

Both allocations belong to one arena. A conventional borrow checker may conservatively tie mutable access to the arena itself and
forbid simultaneous mutable references even though the allocations are distinct. The accesses are not inherently unsafe. The
compiler lacks a representation of the relationship between:

- The arena that owns the storage.
- The individual allocations.
- The authority each allocation handle holds.
- The lifetime dependencies of references into those allocations.

### 2. Separating validity from access

A reference to an object stored in an arena depends on the arena staying alive. That does not mean it needs exclusive access to
the whole arena. The two properties are distinct:

- **Validity:** the arena must stay alive and must not invalidate the allocation.
- **Access:** the reference has permission to access one particular allocation.

Conflating them restricts safe programs unnecessarily. The proposed model makes the separation explicit.

### 3. Library-defined reference abstractions

Metel should ideally let libraries define their own reference-like types without building every memory-management strategy into
the compiler. Examples:

- Ordinary shared and exclusive references.
- References into arena allocations.
- References into custom containers.
- References managed by garbage collectors.
- References into externally managed memory.
- Specialized views over disjoint portions of an allocation.

These have different storage-management requirements and share common access-safety principles. The model expresses those
principles through a small set of compiler-tracked capabilities.

---

## Design principles

1. **Static safety by default.** Safe code cannot create conflicting access permissions or access invalid memory. A library may
   use runtime checks when it needs them; the fundamental borrowing model does not require them.
2. **Minimal trusted primitives.** The compiler exposes only the operations needed to establish and manipulate access authority.
   Higher-level reference abstractions are implemented in libraries wherever possible.
3. **Structural reasoning.** Access permissions apply to places and their projections, not only to complete values, so the
   compiler can reason about disjoint fields and nested structures.
4. **Explicit validity dependencies.** The validity of a reference may depend on resources other than the value its access
   permission was derived from. The type system can represent those dependencies.
5. **Compatibility with ownership.** The proposal extends Metel's ownership and partial-move model and does not replace it.
   Borrowing, moving and destruction stay consistent.
6. **Library abstraction.** Safe users of a reference abstraction need not understand its unsafe implementation. The library
   establishes the invariants the trusted primitives it uses require.

---

## Proposal

### 1. Conceptual model

Three complementary mechanisms, with different purposes that are not interchangeable:

| Mechanism | Proposed notation | Responsibility |
|---|---|---|
| Origins | `@a` | Express validity dependencies |
| Brands | `'b` | Distinguish generative resource identities |
| Access witnesses | `AccessWitness` | Represent authority to access a target |

All notation in this RFC is illustrative. It follows whatever RFC-0159, RFC-0076 and RFC-0143 settle (see "Interaction with other
work").

#### 1.1 Origins

An origin is a dependency on the continued validity of some resource or storage. A reference may depend on one or more origins.
`&T@a` is a shared reference whose validity depends on origin `@a`. Origins may be combined: `&T@(a | b)` depends on both `@a`
and `@b`. The exact semantics and syntax of composition are not specified. The formal model has to determine how origin
dependencies are introduced, propagated and discharged.

#### 1.2 Brands

A brand is a generatively distinct identity. `ArenaPtr<T, 'b>` may be a pointer associated with the arena identified by brand
`'b`. Brands prevent accidental mixing of resources from different domains. A brand is not a memory-access permission. Two
pointers sharing a brand may refer to the same allocation or to different ones, so brand equality alone establishes neither
aliasing nor disjointness.

#### 1.3 Access witnesses

An access witness represents authority to access a particular target:

```text
AccessWitness<T, @a, Shared>
AccessWitness<T, @a, Exclusive>
```

The witness is compiler-tracked and cannot be freely constructed by safe code. It preserves enough information to establish:

- Which allocation or place is accessed.
- Whether the access is shared or exclusive.
- Which other accesses are compatible.
- Which validity dependencies must remain satisfied.
- Whether the access was derived from another access.

An exclusive witness must not be duplicable in a way that permits conflicting exclusive accesses. A shared witness may support
multiple compatible readers, subject to the access model.

### 2. Library-defined references

#### 2.1 Reference representation

The language could provide reference abstractions through library types:

```text
struct Ref<T, @a> {
    witness: AccessWitness<T, @a, Shared>
}

struct RefMut<T, @a> {
    witness: AccessWitness<T, @a, Exclusive>
}
```

These definitions are conceptual. The witness representation may be opaque, and the reference types may need additional compiler
support or restrictions. The important property is that the safety of reference operations derives from the witness and not from
a hardcoded reference type.

#### 2.2 Surface syntax

Ordinary borrowing stays convenient. `let shared = &value;` and `let exclusive = &var value;` could elaborate into operations
that construct the appropriate library-defined reference types, and `&T@a` and `&var T@a` could be aliases or sugar for
`Ref<T, @a>` and `RefMut<T, @a>`. The familiar user-facing model is preserved while the underlying reference abstractions are
defined outside the compiler.

#### 2.3 Compiler responsibilities

Even if references are library-defined, the compiler keeps enforcing the fundamental safety properties:

- Ownership and move tracking.
- Place identity and projections.
- Partial moves.
- Shared and exclusive access compatibility.
- Reborrowing.
- Suspension of parent access.
- Validity dependencies.
- Prevention of invalid destruction or mutation.

The compiler does not become unaware of borrowing. It operates on generalized access capabilities and not on a fixed set of
reference types.

### 3. Access witness operations

The compiler would expose a small set of trusted operations. The exact API is open.

**Acquiring access.** An owned place may be used to acquire a witness: `let witness = acquire_exclusive(value);`. The operation
establishes that exclusive access is currently permitted, which may require suspending or restricting other accesses to
overlapping places.

**Projecting access.** A witness may be projected onto a subplace: `let field = project(witness, .field);`. The compiler tracks
the relationship between the original target and the projected target. For disjoint projections it may derive independent
witnesses.

**Reborrowing.** A reference may temporarily yield a new reference to the same target: `let child = &var parent;`. While an
exclusive child borrow is active, conflicting use of the parent is suspended. The formal model defines how the suspension is
established and when parent access becomes available again.

**Unsafe access establishment.** Some abstractions cannot derive their authority from an existing reference. An arena may store
raw pointers internally while exposing safe allocation handles. Such libraries may need a primitive like
`unsafe establish_access(...)`, which creates a witness from externally established invariants. It is unsafe because the compiler
cannot prove those invariants from the raw pointer alone, and it has explicit soundness obligations. In particular it must not
permit arbitrary fabrication of exclusive access to an aliased allocation.

### 4. Structural borrowing

The model preserves and generalizes structural borrowing. For

```text
struct Pair {
    left: Int,
    right: Int
}

let pair = Pair { left: 1, right: 2 };

let left = &var pair.left;
let right = &var pair.right;
```

the two exclusive references coexist because their target places are structurally disjoint. The compiler reasons about places as
paths through values:

```text
pair
 |-- left
 `-- right
```

Two projections are disjoint when their paths diverge through independently stored fields. The formal rules account for cases
where structural separation does not imply independent storage, such as overlapping representations or unsafe aliasing.

**Partial moves.** The same place model supports partial moves. After `let left = move pair.left;`, `pair.left` is no longer
initialized and `pair.right` may remain usable. The ownership model and the borrowing model share one understanding of places and
their state.

**Function boundaries.** A major objective is preserving useful access information across function boundaries: a function may
borrow one field of a structure and leave the others available. The type system should be able to express the resulting partial
access state where necessary. How such effects appear in caller-visible access permissions is unresolved.

### 5. Arena allocation

Arena allocation is the motivating example.

#### 5.1 The problem with copyable pointers

```text
struct ArenaPtr<T, 'b> {
    ptr: RawPtr<T>
}
```

An `ArenaPtr` may be copyable, and two copies may refer to the same allocation (`let first = ptr; let second = ptr;`). If both
could independently establish exclusive access, safe code could create conflicting mutable references. A shared arena brand
therefore does not justify exclusive borrowing.

#### 5.2 Affine allocation handles

A possible solution is an affine handle that owns the access authority over one allocation:

```text
struct ArenaBox<T, 'b, @a> {
    ptr: RawPtr<T>
}
```

- The arena owns the physical storage.
- The `ArenaBox` owns unique authority over a particular allocation.
- The handle cannot be freely duplicated.
- Borrowing the handle may produce references to its allocation.
- The allocation stays valid while the handle or derived references depend on it.

This resembles an owning pointer and its pointee, except that an external arena manages the storage.

#### 5.3 Independent exclusive borrowing

```text
let first = arena.alloc_owned(10);
let second = arena.alloc_owned(20);

let a = first.borrow_mut();
let b = second.borrow_mut();
```

Both borrows are permitted. The safety argument rests on the unique allocation authority each handle represents, not on both
allocations belonging to one arena. For soundness the allocator guarantees that independently live owned handles represent
distinct allocations, or enforces an equivalent non-aliasing invariant.

#### 5.4 Borrowing an allocation

```text
impl<T, 'b, @a> ArenaBox<T, 'b, @a> {
    fun borrow_mut<@self>(
        self: &var Self@self
    ) -> &var T@(self | a)
}
```

The returned reference depends on `@self`, the borrow of the affine handle, and on `@a`, the validity of the arena-managed
storage. It does not require exclusive access to the whole arena. The arena dependency prevents storage invalidation, and the
handle borrow provides exclusive access authority over the particular allocation.

#### 5.5 Arena lifetime and invalidation

The arena must not be destroyed, reset or otherwise invalidate allocations while live handles or references depend on them. This
may need explicit storage-validity constraints, for example:

```text
struct ArenaBox<T, 'b, @a>
where valid: @a
{
    ptr: RawPtr<T>
}
```

Alternatively, validity dependencies could be intrinsic to the meaning of origin parameters. This RFC does not choose. The formal
model should clarify the difference between a type that carries an origin parameter and a value whose validity actually depends on
that origin.

#### 5.6 Allocation destruction

The design also specifies what happens when an `ArenaBox` is destroyed. Possible responsibilities: destroying the stored value,
releasing exclusive allocation authority, leaving the storage allocated until the arena is destroyed, preventing double
destruction, and preventing references from outliving the handle. The exact semantics depend on the arena abstraction and are
defined by its ownership contract.

### 6. Other memory-management abstractions

- **Garbage-collected storage.** A collector may guarantee validity through reachability or rooting instead of lexical
  ownership. A reference into collected storage may depend on the lifetime of a root or another validity guarantee. Access
  permissions still have to prevent conflicting mutation, and the design must account for collectors that relocate objects.
- **Custom containers.** Containers could expose references to disjoint elements when they can establish non-overlapping access
  authority: split views, mutable access to separate regions, tree and graph traversal, custom layouts. Not every container can
  establish disjointness statically; some operations need runtime checks or unsafe implementation invariants.
- **External memory.** The witness model may apply to memory managed by external systems. Such abstractions need explicit
  validity and access guarantees supplied by trusted code.

### 7. Soundness requirements

1. **Access compatibility.** For any live location, active access permissions are mutually compatible; an exclusive access does
   not coexist with another conflicting access to the same location.
2. **Storage validity.** A valid access witness does not refer to invalidated storage, and its validity dependencies stay
   satisfied.
3. **Ownership consistency.** Moving or destroying a value does not invalidate outstanding accesses. Partial moves preserve the
   initialization and ownership state of unaffected subplaces.
4. **Witness provenance.** Safe code cannot manufacture arbitrary witnesses. Every safe witness originates from an authorized
   acquisition, projection or reborrowing operation.
5. **Authority conservation.** Access authority is not duplicated in ways that violate exclusivity. Projection and reborrowing
   preserve the constraints of the parent access authority.
6. **Unsafe abstraction boundaries.** Unsafe code may establish access authority using invariants the compiler cannot see; a
   safe abstraction ensures those invariants hold for every permitted safe use. The formalization identifies the assumptions the
   trusted witness-establishment operations require.

### 8. Relationship to Metel-Core

This proposal is a candidate for formalization in Metel-Core (RFC-0241), which could represent explicitly: places and
projections, ownership state, access witnesses, loan relationships, validity dependencies, generative brands, allocation
identity, and the trusted access-establishment operations. The arena model could serve as the case study showing that the
generalized borrowing system supports independently mutable allocations without runtime borrow checking.

The design need not wait for the formalization to be finished. Major safety-sensitive decisions should ideally be validated
against the formal model before implementation.

### 9. Proposed next steps

Refine the model; do not implement the whole system yet.

1. Define the semantic distinction between origins, brands and access authority.
2. Specify a minimal access-witness API.
3. Define how witness acquisition, projection and reborrowing interact with ownership.
4. Develop examples for ordinary borrowing, partial borrowing and function boundaries.
5. Specify the `ArenaBox` ownership and validity model.
6. Identify the trusted assumptions required by unsafe witness establishment.
7. Express the essential invariants in Metel-Core.
8. Evaluate the design by formalization before committing to implementation details.

---

## Interaction with other work

This RFC overlaps existing designs and decides none of them. Reconciling the overlaps is part of its review.

- **RFC-0143** (under review, allocator placement, storage identity and allocator-selected handles): the closest neighbour.
  It already proposes a unique arena handle `T@arena` carrying arena identity, a static disjointness witness for storage families
  that forbid cross-arena references, and `place` expressions. Section 5 here (`ArenaBox`, affine allocation authority) and the
  `@` notation overlap it. In RFC-0143 `@arena` names the allocator that owns a value; here `@a` is an origin, a validity
  dependency. Whether these are one mechanism or two is the first question to settle.
- **RFC-0159** (under review, abstract regions and a dedicated identity channel): separates lifetimes, brands and storage
  identity as roles over one `RegionIndex` substrate in a channel that is not `<>`. The origin/brand/witness split here is the
  same separation approached from the library side, and the notation follows RFC-0159.
- **RFC-0122** (under review, borrow checking) and **RFC-0067** (under review, lifetime anchors): the borrow-checking and
  lifetime designs that witness operations would generalize or replace.
- **RFC-0076** (under review, brand types): the brand concept.
- **RFC-0139** (under review, garbage-collected allocators and allocator-determined pointer types): the garbage-collection case
  of section 6.
- **RFC-0077** (accepted, allocator generics): the allocator surface the arena case study exercises.
- **RFC-0067a** (implemented, reference types), **RFC-0044** (implemented, explicit receiver semantics) and **RFC-0126**
  (implemented, `T` as a copy-borrowed view): the compiler-defined references that library-defined `Ref`/`RefMut` would have to
  stay compatible with.
- **RFC-0241** (draft, Metel-Core): the formal model this RFC proposes to validate against.
- **RFC-0028** (refused) and **RFC-0043** are earlier memory and pointer models; nothing here revives them.

---

## Alternatives considered

1. **Compiler-defined references only.** Keep conventional compiler-defined shared and exclusive references. Simpler to implement
   and fewer trusted abstractions, but it restricts the ability of libraries to define custom memory-access mechanisms.
2. **Runtime borrow checking.** Custom abstractions could rely on runtime borrow checks. Viable for some containers and
   allocators, but it adds runtime overhead and runtime failures for access patterns that could be established statically. The
   proposed model makes runtime checks optional and not fundamental.
3. **Brand-based disjointness.** Use generative brands to identify arena allocations. A single arena brand identifies a domain,
   not individual allocations. A unique brand for every allocation would need a different allocation interface and complicate
   dynamic allocation patterns. Affine allocation authority bases disjointness on ownership instead of per-allocation type
   identities.
4. **Special compiler support for arenas.** Recognize specific allocator abstractions and apply dedicated borrowing rules.
   Simpler for particular cases, but it adds special cases and limits extensibility. A general access-witness model gives
   reusable foundations for several allocation strategies.

---

## Risks and tradeoffs

- **Increased type-system complexity.** Separating origins, brands and access authority adds concepts. It may improve
  expressiveness and soundness and it also makes the type system more complex.
- **Unsafe primitive design.** A poorly designed witness API could let safe libraries violate memory safety. The trusted
  operations need carefully specified semantics and preconditions.
- **Compiler complexity.** The compiler tracks access relationships, place projections, ownership and validity dependencies. The
  proposal may need significant changes to the existing borrow-checking architecture.
- **Ergonomics.** A more expressive internal model must not make ordinary borrowing verbose. Most users should be able to use
  familiar borrowing syntax without manipulating witnesses or complex origin expressions.
- **Formal verification effort.** This RFC does not establish soundness. A rigorous formalization may reveal further
  restrictions or require revising the proposed abstractions.

---

## Open questions

**Reference representation**

1. Should `Ref` and `RefMut` be entirely library-defined?
2. What compiler support do their representation and use need?
3. Should references have special calling-convention or layout guarantees?
4. How does implicit borrowing elaborate into witness operations?

**Witness API**

5. What is the minimal set of witness primitives?
6. How do field projection and splitting work?
7. Can witness permissions be represented as types?
8. How are reborrowing and parent suspension modeled?
9. How can safe libraries expose custom borrowing operations without exposing the unsafe primitives?

**Origins**

10. What exactly does an origin represent?
11. Do origin parameters imply validity dependencies automatically?
12. Are validity constraints declared explicitly?
13. How are multiple origins composed?
14. How are origin dependencies tracked across function boundaries?

**Brands**

15. How are generative brands introduced?
16. What stops brands from escaping their valid scope?
17. How do brands interact with generic types and higher-ranked polymorphism?
18. Which guarantees can safely be derived from brand identity?

**Allocation authority**

19. How is unique allocation authority represented?
20. Can ownership of an allocation be transferred between handles?
21. How are independently owned allocations proven disjoint?
22. How are allocation handles invalidated or destroyed?
23. Can allocation authority be split or combined safely?

**Partial borrowing**

24. How are partially borrowed structures represented in the type system?
25. What access information survives function calls?
26. Can the compiler track partial borrowing without explicit user annotations in common cases?
27. How do partial moves interact with outstanding field borrows?

**Unsafe operations**

28. What are the precise preconditions for establishing access from raw pointers?
29. Which invariants must library authors verify?
30. How are unsafe access-establishment operations represented in the formal semantics?
31. Can the trusted primitive set be reduced further?

**Relationship to existing RFCs**

32. Is `T@arena` (RFC-0143) and the origin `@a` here one mechanism or two, and which RFC owns the `@` spelling?
33. Does an `ArenaBox` replace RFC-0143's arena handle, wrap it, or sit beside it?

---

## Decision

**Outcome:** *(pending)*
