---
id: rfc-0143
title: "Allocator Storage Resources and Custody-Aware Typed Allocation"
date: '2026-08-26'
updated: '2026-11-18'
status: under-review
tracking: 'https://github.com/metel-lang/metel-core/issues/850'
---

> **Proposed replacement, 2026-11-18.** This text replaces the previous design of RFC-0143 under the **same RFC number**. The replacement is a proposal for review, not a claim that the existing accepted allocator RFCs have already been superseded or that any new syntax has been implemented. In particular, the change from allocator-selected `T@a` handles to storage-resource allocation is deliberate, not a mechanical rewrite.
>
> **Compatibility with RFC-0242.** This RFC assumes the *proposed revised* RFC-0242 ownership/custody/access model: target-bound access witnesses, storage validity domains, first-class custodians, and checked revocation. The GitHub version of RFC-0242 may still contain its older exploratory text; the two replacements must be reviewed together. RFC-0241 is the proposed formal validation vehicle.
>
> **Syntax convention.** Ordinary examples follow Metel 0.16.0 `develop` conventions where possible: `fun`, `struct`, `extend`, `&T`, `&var T`, `let`/`var ... :=`, and assignment with `=`. Storage parameters `@s`, brands `'b`, explicit borrow regions `&r`, `depends valid(@s)`, `revokes @s`, `unsafe aspect`, and the library APIs here are **proposed extensions**. Comments labeled *schematic* describe semantic contracts, not compiler-accepted declarations. The planned `[T]` unsized payload and `&[T]` / `&var [T]` views are likewise proposed changes to current collection semantics.

## Summary

An **allocator** provides *storage*, not an initialized value and not a universal kind of owning or shared pointer. This RFC replaces the allocator-selected-handle foundation with three composable layers:

1. **`Alloc<@s>`:** a trusted storage-acquisition interface tied to an instance-level storage identity `@s`.
2. **`RawStorage<@s>`:** an affine, provenance-preserving resource representing a particular allocation of uninitialized storage, including the authority and protocol needed to retire or release it.
3. **Typed ownership layers:** library-defined `Unique`, `Box`, `ArenaBox`, `OwnedBuffer`, `Rc`, and other abstractions that initialize and own or retain particular objects using the raw storage substrate where appropriate.

Storage validity, object liveness, location stability, and access permission remain **distinct** as defined by RFC-0242. A storage identity `@s` names a rigid domain and can appear in validity dependencies; it is not a borrow, a pointer, an allocator value, or exclusive access authority. Borrow regions `&r` govern access duration; brands `'b` identify generative authority domains.

The baseline `Alloc` contract promises **non-invalidating allocation**: acquiring another block cannot invalidate an already live block or relocate a live object. An allocator that cannot uphold this contract may expose a different, specialized interface, but must not implement `Alloc` dishonestly. An optional reallocation facility can be defined separately; it requires exclusive ownership of the affected block and preserves object/initialization obligations.

This RFC defines the *semantic interface*, an initial proposed surface, and soundness requirements. It does **not** settle the low-level unsafe syntax, owning-existential capsules, a general dynamic-layout language, or moving-GC implementation details. It does specify enough raw runtime-sized allocation capability to address the missing buffer primitive identified by RFC-0133.

The key rule is:

> **Allocation grants control of storage, not ownership of an initialized `T`.** Creating `T` in that storage, moving it, destroying it, sharing it, and accessing it are separately checked operations.

---

## Motivation

### 1. The old allocator interface conflates responsibilities

RFC-0063 introduced allocation-tagged `@a T` and `@a expr`. RFC-0143 revised this to `T@a` and `place a expr`, where the allocator selects the resulting handle family. This accounts for the fact that GC and ordinary unique ownership have different pointer semantics, but still makes a single allocation operation responsible for allocator choice, storage identity, object construction, and ownership policy.

In the revised RFC-0242 model, these responsibilities can be separated. The same heap storage facility can support a unique `Box<T>` or a reference-counted `Rc<T>`. An arena can return an affine per-allocation owner even though the arena—not the owner—eventually reclaims its backing chunks. A GC heap can provide traced handles without pretending they are ordinary affine storage blocks.

### 2. A raw pointer is too weak an allocation result

A traditional `allocate(layout) -> RawPtr` API leaves independently important facts outside the type system: which allocator created the block, who may free it, whether it is already initialized, whether two returned blocks overlap, and whether a later allocation could relocate it.

RFC-0242 already provides machinery for representing such authority. The allocation result should be a **resource**, not an unrestricted integer address or freely forged pointer. Unsafe implementations establish its invariants; safe code may transfer the resource into higher-level ownership types.

### 3. An allocator may outlive individual objects

An arena can own backing memory while an `ArenaBox<T, @s>` owns one initialized object inside that memory. Destruction of the object need not return bytes to the arena immediately. Conversely, reclamation of arena memory must not run before live dependent objects and direct references are safely discharged.

A single shared storage dependency must not act like an exclusive loan of the whole arena: new allocations and simultaneous exclusive borrows of distinct objects must remain possible.

### 4. Runtime-sized buffers are a foundational need

RFC-0133 documents that neither `[T; N]` (compile-time fixed size) nor the existing borrowed `[T]` view can provide the storage for a Metel-authored growable `List<T>`. An allocator must support allocating a checked runtime size and alignment. The higher-level buffer tracks how many elements are actually initialized.

---

## 1. Scope, decisions, and non-goals

This RFC proposes the following decisions:

- An allocation interface operates on **raw blocks** identified by storage domain `@s`.
- Its result is an **affine, provenance-preserving `RawStorage` resource**, never an ordinary `T` and never a freely copyable raw pointer.
- New allocations are non-invalidating for all live blocks and objects reachable from them.
- A block carries a usable **reclamation/retirement capability**, even when physical release is deferred.
- Safe typed construction and initialization are built above the raw interface.
- Object destruction and storage release are distinct obligations.
- Resizing is an optional capability, not an obligation of `Alloc`.
- An allocator does not select a universal owning-pointer family; high-level allocating APIs may select handles independently.
- `@s` denotes storage identity in generics and validity contracts; **`T@a` is not the foundational allocation type**.

Non-goals for this replacement include: a mandatory `place` keyword; complete generic associated-type machinery for arbitrary typed placement; a composable dynamic-layout definition language; general user-defined unsized types; a particular GC tracing/root-discovery algorithm; full ABI or calling-convention guarantees; and automatic support for self-referential owning structs without an appropriate custody-capsule mechanism.

The proposed base interface is intentionally about **stable allocated storage**. A moving collector or another manager with different guarantees need not implement it for its movable objects.

---

## 2. Storage identities, lifetimes, and brands

### 2.1 Three different roles

| Notation | Meaning | Primary rule |
| --- | --- | --- |
| `@s` | Rigid storage/resource identity | Storage-dependent values require `valid(@s)` |
| `&r` | Borrow duration / access relationship | Loans may be shortened and must not conflict |
| `'b` | Rigid generative authority brand | Brand equality does not itself establish access or liveness |

A storage identity names the *resource domain*, not an individual object within it. Two blocks allocated in `@s` may be disjoint, but the fact that they share `@s` alone does not prove disjointness; the allocation contract does.

This proposal uses `@s` in generic positions (e.g. `BumpArena<@s>`, `ArenaBox<T, @s>`), without the older `<storage s>` spelling. Brand parameters are consistently `<'b>` / `Token<'b>`, never `<brand 'b>`.

### 2.2 Introduction and generativity

A new independent arena may introduce a fresh storage identity. An inferred identity is not just the allocator's *type*: two instances of `BumpArena` can have distinct `@s` values despite identical runtime types.

```text
// Proposed generative API; storage binders are inferred.
BumpArena::scoped(|arena| {
    var arena := arena;
    let a := arena.alloc_box(10)?;
    use_value(&a);
});
```

The scoped constructor introduces a fresh identity whose dependent values cannot escape unless a sound owning existential/custody package transfers the underlying storage resource with them. A storage identity is erased at runtime when its representation is not otherwise required.

### 2.3 Storage validity is not an access loan

```text
struct ArenaBox<T, @s>
    depends valid(@s)
{
    allocation: OwnedAllocation<T, @s>,
}
```

`depends valid(@s)` means that a live `ArenaBox<T, @s>` requires the backing storage domain to remain valid. It does not establish that the allocation contains an initialized `T`, does not assert that the address is stable by itself, and does not borrow the arena exclusively. Those other facts follow from the `OwnedAllocation` contract and the access operations.

The compiler may infer propagated dependencies from fields; explicit declarations on public/opaque types must be verified, not treated as declarations that fabricate the validity of `@s`.

---

## 3. `Alloc`: the base storage interface

### 3.1 Proposed declaration

```text
// Proposed language surface; not valid in v0.16.0.
unsafe aspect Alloc<@s> {
    type Error;
    type Block: RawStorage<@s>;

    fun allocate(
        &var self,
        layout: Layout
    ) -> Result<Self::Block, Self::Error>;
}
```

An `unsafe aspect` is a proposed way to mark a contract whose implementations must uphold invariants the compiler cannot infer solely from ordinary method bodies. **Calls to a sound implementation can be safe**, even if the implementation requires trusted or unsafe operations. The precise `unsafe` syntax remains a dependency on RFC-0026; this proposal does not claim it is implemented.

The `@s` parameter is the storage identity bound to a real allocator/custodian instance, not permission to allocate by naming a region. The compiler must reject an implementation or call that purports to manufacture a block in an unrelated `@s` without the required establishment authority.

`Layout` represents a **checked** byte size and alignment for a block. It is distinct from the deferred *composable dynamic-layout definition* facility: runtime-sized contiguous buffers need only checked `Layout::array<T>(count)`-like computations, not a general user-defined unsized layout calculus.

### 3.2 Normative allocation contract

For any successful `allocate(layout)` call:

1. **Fresh logical allocation:** the result denotes a new allocation identity. For nonzero usable extents, it does not overlap any independently live allocation returned under incompatible exclusive authority. Zero-sized allocations still have distinct logical identities; raw address equality alone is never an aliasing proof.
2. **Sufficient storage:** the usable extent has the requested size and alignment, or a stronger compatible extent, with integer overflow and unsupported layouts reported as errors.
3. **Uninitialized state:** the block does not assert that any `T` object is initialized. Safe typed reads require a separate initialization proof.
4. **Stable extent:** while the block is valid, unrelated calls to `allocate` cannot relocate it, overwrite its live contents, revoke its validity, or silently change its usable layout.
5. **Provenance:** the block carries allocation origin and the authority to establish access to its actual extent. It cannot be arbitrarily created, duplicated, or rebound to another block by safe code.
6. **Custody:** the block's validity dependencies remain satisfied for as long as safe operations can use it. If it depends on `@s`, reclamation of `@s` is forbidden until those dependencies are discharged.
7. **Reclamation:** the block carries or securely delegates a usable release/retirement protocol. Releasing the block once must never double-free; releasing it must not require reconstructing an exclusive borrow of an allocator currently inaccessible through ordinary borrowing.
8. **Failure atomicity:** on allocation error, no ownership or destruction obligation is silently lost and no invalid block is returned. The allocator state may have changed (e.g. reserved capacity) only if its public contract permits it without invalidating other blocks.

For standard heaps, the release protocol may return storage to the heap immediately. For bump arenas, release may mark a logical slot retired while physical memory is reclaimed only on epoch reset or arena destruction. Per-block retirement **need not** mean per-block reclamation.

The `&var self` receiver allows allocator bookkeeping to change. It does not confer authority to invalidate other live blocks, which have independent resource guarantees. An implementation that uses movable backing buffers must use indirection or chunking sufficient to honor the non-invalidating rule.

### 3.3 Why stable allocation is mandatory

```text
var a := arena.alloc_box(10)?;
var b := arena.alloc_box(20)?;

let x := a.borrow_mut();
let y := b.borrow_mut(); // Allowed: independently owned targets.
```

If allocating `b` could move or destroy `a`, the returned handles could not be independent without additional borrowing or relocation protocols. The contract therefore rules out a `Vec`-like moving backing buffer behind a naive implementation of `Alloc`. Such a manager must either stabilize allocations or expose a different, narrower capability.

---

## 4. `RawStorage`: an affine block with a release protocol

### 4.1 Contract, not merely a pointer

A block is a first-class affine resource with an unforgeable target identity. A conceptual interface is:

```text
// Explanatory contract, not a final aspect signature.
unsafe aspect RawStorage<@s> {
    // Properties supplied to trusted typed-construction operations:
    // - allocation identity, extent, alignment, provenance
    // - domain validity dependency (where applicable)
    // - exclusive authority over uninitialized bytes
    // - release/retirement capability

    fun layout(&self) -> Layout;
    fun release(self);
}
```

An ordinary safe `RawStorage` implementation cannot create these guarantees by returning a pointer. Establishing the initial block or a verified sub-block partition is a trusted operation whose preconditions are explicit in RFC-0242 and the future unsafe primitives layer.

`RawStorage` may be a **sealed/proof-carrying** capability rather than an unrestricted user-implementable aspect in the first implementation. The RFC requires its semantics, not that arbitrary library code can immediately implement it safely.

### 4.2 Drop and release

The resource must have exactly one *logical owner* of the release authority at a time. It is affine under RFC-0071: copying or using it after a move is forbidden; it can be consumed by `release` or transferred into a typed owner. An uninitialized block can be safely retired on ordinary destruction according to its implementation's release protocol.

Affine abandonment may leak physical storage if the language permits suppressing cleanup, but it may not create a dangling safe reference or cause a double release. A stronger linear obligation is appropriate only if a particular allocator needs mandatory discharge; this RFC does not impose linearity on every raw block. RFC-0089 remains the owner of the general linear-type mechanism.

The **release ticket** can be represented by the block itself, a stable allocator control object, a retained allocator reference with its own valid custody protocol, or another implementation-specific resource. The public type need not expose which. What is required is that safe `Unique`/`OwnedBuffer` destruction can finish without acquiring an invalid or conflicting `&var` borrow of a separately held allocator.

### 4.3 Partition and merging

A trusted operation may split a raw block into nonoverlapping sub-block capabilities; it must conserve allocation extent, exclusivity, and reclamation authority. A partition must not let each child independently free the entire parent allocation. A shared parent release ticket, join requirement, or equivalent accounting is necessary.

Ordinary safe code may not manufacture a sub-block by constructing a new address and length. Range checks alone do not prove provenance or independent release authority.

---

## 5. Typed initialization and ownership

### 5.1 Separate storage from initialized objects

The transition from raw storage to `T` ownership has distinct proof obligations:

```text
RawStorage block
    -- checked layout + move-in + initialization -->
Initialized T at target o
    -- ownership transfer + cleanup protocol -->
Unique<T, Block, @s>
```

The trusted initialization primitive must prove that the block fits `T`, that alignment is valid, that the destination is available and not already initialized, and that the constructed object has unique logical ownership. It must transfer the block's release authority to the resulting owner. Safe code cannot reinterpret uninitialized bytes as a `T`.

A schematic library result is:

```text
struct Unique<T, B, @s>
    depends valid(@s)
{
    // Opaque: initialized T, exclusive ownership witness,
    // backing resource B, and its release protocol.
}
```

The type is illustrative. In particular, `Unique` cannot expose a movable `B` field while an initialized `T` still occupies it, and it must preserve any extra liveness/relocation constraints of `T`. Where the domain is self-owned or globally valid, `@s` can be hidden behind an opaque public owner rather than being exposed on every `Box<T>`.

### 5.2 A generic safe allocation helper

```text
// Schematic API; generic associated type and error details are proposed.
fun allocate_unique<T, A: Alloc<@s>, @s>(
    allocator: &var A,
    value: T
) -> Result<Unique<T, A::Block, @s>, (A::Error, T)>;
```

The error returns `value` if no initialized owner could be established. This makes the failure contract explicit even for types whose value cannot simply be discarded. An implementation may expose a convenience overload that drops `value` on failure only when such destruction/discard is permitted.

Typical implementation sequence:

1. Compute a checked `Layout::of<T>()` and allocate a raw block.
2. If allocation fails, return `(error, value)` without consuming its value ownership.
3. Move `value` into the block through the restricted initialization primitive.
4. Transfer the initialized object's ownership and block's release ticket to `Unique`.
5. On any intermediate failure or exceptional exit, recover or correctly destroy the value and retire the block exactly once; never expose a partially constructed `T` as fully initialized.

The initial API supports sized `T`. Unsized payloads such as `[T]` require a separately specified initialization builder with runtime element count, not a general dynamic-layout language.

### 5.3 Borrowing and extraction

```text
extend<T, B, @s> Unique<T, B, @s> {
    fun borrow(&self) -> &T;
    fun borrow_mut(&var self) -> &var T;
}
```

Borrowing derives access to the specific initialized target, not to the entire allocator. It must be prohibited when the target has been moved or destroyed and must carry the validity dependencies of its backing block.

Consuming a unique owner may move out the object only if the handle can finish the backing storage's retirement and preserve `T`'s destruction/movement obligations. Extraction is explicit (consistent with RFC-0066 as amended by RFC-0185), and **not** inferred from argument or expected return types. The exact integration of dereference syntax with the generalized access API is owned jointly by RFC-0242 and a later extraction-specific revision.

```text
// Conceptual, where the unique owner supports extraction.
let value: Node := *owner;
```

A bulk allocator without per-object tracking can still support move-out where no destructor or initialization obligation would be lost. If it cannot safely support a particular `T`, the handle simply does not provide extraction for that `T`. The **handle protocol**, not the allocator's name, determines availability.

### 5.4 Destruction order and panic/failure safety

For a fully initialized owner, destruction must end all incompatible live access, run the object's destructor **once if required**, mark the storage no longer containing a live `T`, and then retire/release the block. These responsibilities may be implemented via trusted capsule machinery; ordinary field drop order alone is insufficient when parts of the representation can move out independently.

A destructor that fails must not lead to a second destructor invocation or to a safe reference to reclaimed memory. The precise unwind/abort policy is a language-wide decision. This RFC requires the storage/initialization state machine to be safe under whichever policy Metel adopts.

---

## 6. Runtime-sized buffers and optional reallocation

### 6.1 `OwnedBuffer<T>` is not `[T]`

A growable buffer owns a raw allocation with capacity `c` and an initialized prefix of length `n`, where `0 <= n <= c`. It must track ownership of the `n` initialized elements and of the raw capacity separately:

```text
struct OwnedBuffer<T, @s>
    depends valid(@s)
{
    // Opaque: raw block, length, capacity,
    // initialization state, and reclamation ticket.
}
```

`OwnedBuffer` may expose an `&[T]` view over the **initialized prefix only**, or an `&var [T]` view under exclusive borrow. It must not expose uninitialized capacity as a safe `[T]`.

The first implementation need only support checked runtime byte layouts such as `Layout::array<T>(capacity)`. General user-defined unsized type layouts are deferred.

### 6.2 Growth works without reallocating the old block

A generic `List<T>` can grow by acquiring a larger block, moving each initialized element when allowed, transferring each element's destruction obligation, retiring the old block, and replacing the buffer. It may not do this while existing references or pinning contracts forbid relocation.

```text
// Illustrative surface, with no allocator-specific compiler rule.
var list := ArenaList::new(&var arena)?;
list.push(10)?;
list.push(20)?;
let view: &[i64] := list.as_slice();
```

The borrow checker prohibits a conflicting mutating `push` while `view` remains live. A specialized stable-buffer abstraction may offer a more permissive API only if it can establish the required per-target stability contract.

### 6.3 `Reallocate` is optional

Not every allocator can or should resize an allocation. A distinct optional capability may offer `grow`/`shrink` without becoming part of the base `Alloc` requirement.

The raw form must be restricted to an **uninitialized** block or to a verified state in which no initialized value/borrow is invalidated. A higher-level typed `OwnedBuffer` must separately preserve or move initialized elements and respect pinning; `memcpy` of arbitrary initialized `T` is not automatically valid.

A fallible consuming resize must either return the original usable block on failure or specify another equally safe ownership-preserving failure result. It may not silently lose the only reclamation ticket or leave a caller holding an invalidated block.

---

## 7. Custody, reclamation, and revocation

### 7.1 Domain validity and block custody

A block backed by an externally owned arena may depend on its storage identity:

```text
struct ArenaBlock<@s>
    depends valid(@s)
{
    // Opaque affine raw storage and release ticket.
}
```

`valid(@s)` is a domain-level guarantee, not evidence that any particular slot is initialized. Allocation establishes a fresh block target and distinct exclusive authority to that block; typed initialization establishes the object target's liveness.

The associated custodian must ensure that `@s` is valid for as long as any safe dependent handle or reference can be used. This can be statically enforced through RFC-0242's dependencies and checked revocation, or through a trusted runtime custody protocol with equivalent strength.

### 7.2 Revocation is a checked operation

```text
// Schematic effect signature.
fun dispose<@s>(arena: BumpArena<@s>) revokes @s;
```

The `revokes @s` clause is an effect declaration, **not** revocation authority. The compiler must verify the operation's authorization and detect outstanding dependencies across function calls, moves, generic interfaces, and implicit destructor execution.

A move of the allocator custodian into a function that might destroy it is subject to the same obligations as an explicit `dispose`. Merely hiding teardown in another function must not bypass the rule.

### 7.3 Resettable arenas use epochs

A reset need not invalidate the arena's backing *capacity* forever; it invalidates the objects allocated during the current epoch. Model the two identities separately:

```text
// Conceptual identities, not a finalized public API.
struct BumpArena<@s, @e> {
    // @s: backing storage domain
    // @e: current allocation epoch
}

struct ArenaBox<T, @s, @e>
    depends valid(@s), valid(@e)
{
    // ...
}
```

`reset` is allowed only when objects and references depending on the old epoch have been safely discharged, and creates a fresh epoch identity `@e2`. A reset that retains the same physical addresses **must not** allow stale handles to become valid again (the ABA problem). The epoch transition and generativity syntax remain to be defined; a plain `&var self` receiver is not enough to justify invalidating unrelated live handles.

### 7.4 Dropping the allocator is not necessarily dropping all its objects

For an externally owned arena, a live `ArenaBox` prevents destruction of the domain until the box and any dependent references are no longer usable. Destroying an `ArenaBox` normally destroys or transfers its `T` and retires its slot; it need not free the arena chunk immediately.

If an arena internally owns all its objects, it may use a different library type with an `ArenaKey<T>`-like non-owning lookup handle. Such keys must not yield unchecked long-lived references that outlive a reset; access may instead require an epoch check and a scoped guard. This is a separate ownership protocol, not a different implementation of the same `ArenaBox` contract.

---

## 8. Concrete allocator families

### 8.1 Heap allocation

A global or local heap can implement `Alloc` by returning blocks with individually usable release tickets. Its `Box<T>` and `Rc<T>` facilities are higher-level abstractions over these blocks:

```text
let a := Box::new(Node { value = 10 });
let b := Rc::new(Node { value = 20 });
let c := b.share();
```

The `Box<T>` and `Rc<T>` examples need not expose `@s` publicly when ownership of their allocation is internally self-sustaining. For `Rc`, each strong handle retains the underlying object; arbitrary copying of an affine release ticket is not permitted. Shared ownership is implemented by a trusted accounting protocol, not by duplicating the raw block.

### 8.2 Bump arena

```text
// Proposed API; error handling elided in the scoped closure for clarity.
BumpArena::scoped(|arena| {
    var arena := arena;
    var a := arena.alloc_box(10)?;
    var b := arena.alloc_box(20)?;

    let x := a.borrow_mut();
    let y := b.borrow_mut();

    // x and y are compatible because the object targets differ.
});
```

Each handle depends on the arena's storage domain, but allocation need not borrow the whole arena for the lifetime of each handle. The arena must maintain stable addresses of its live blocks.

### 8.3 Pool and slab allocators

A pool can implement `Alloc` if it grants an exclusive, stable block resource for each live slot and does not reuse a slot until its prior logical ownership and references have ended. Slot indices alone are not sufficient to establish provenance; generation counters, affine slot ownership, or equivalent invariants are required.

### 8.4 Automatic allocation policy

`AutoAlloc` may remain a useful high-level library/compiler policy, but it must not erase observable guarantees: it cannot move allocations while direct references remain valid, weaken the storage dependency model, or violate `Send`/`Sync` constraints. It need not be a magical subtype of every allocator. Whether it implements `Alloc` as an ordinary allocator or is expressed as a separate compiler strategy is deferred.

### 8.5 Tracing garbage collection

A moving GC need not implement `Alloc<@s>` for ordinary movable objects, because `RawStorage` promises stable live block locations. It can implement `Alloc` for **pinned/immovable** allocations if it actually provides those guarantees, or it can use raw allocation internally and expose a higher-level `GcHeap::alloc<T>` operation returning GC-managed handles.

```text
// Proposed high-level managed API, not an Alloc method.
let node := gc.alloc(Node { value = 42 });

gc.with_ref(node, |value| {
    println(value.value);
});
```

GC roots maintain reachability, pin/guard protocols establish location stability for direct references, and access witnesses govern shared or exclusive access. `valid(@s)` alone does not keep an individual GC object alive. RFC-0139 retains responsibility for complete root discovery, cross-arena edges, affine contents and finalization, and concurrency guarantees.

---

## 9. Allocator parameters and generic APIs

### 9.1 Storage polymorphism is not allocator-type polymorphism

An allocator value `A: Alloc<@s>` grants an operation capability, while `@s` names the storage whose validity a handle depends upon. A function that only forwards a storage-dependent value needs `@s` but does not need to receive an allocator value:

```text
fun forward<T, @s>(value: ArenaBox<T, @s>) -> ArenaBox<T, @s> {
    value
}
```

A function that allocates needs an actual allocator capability:

```text
fun build<T, A: Alloc<@s>, @s>(
    allocator: &var A,
    value: T
) -> Result<Unique<T, A::Block, @s>, (A::Error, T)> {
    allocate_unique(allocator, value)
}
```

The syntax linking `A` to `@s` needs an elaboration rule, but the **semantic distinction is normative**: an identity cannot be used as a replacement for the runtime allocator resource.

### 9.2 No universal `T@a` placement projection

The common result of an allocation request is `A::Block`, not a compiler-selected `T@a` smart pointer. Typed owners are explicitly named by the library API:

```text
let node := arena.alloc_box(Node { value = 42 });
let shared := Rc::new(Node { value = 42 });
```

Generic allocation-constructor aspects (such as `Allocate<T>`) and an optional `place` syntax may be layered on top. They are not required to define `Alloc`, and they cannot fabricate valid ownership by choosing a convenient return type. Any associated handle must implement the RFC-0242 custody and access-establishment obligations.

### 9.3 Elision and context parameters

Ordinary borrow elision remains the responsibility of RFC-0067 and RFC-0122 as revised for RFC-0242. Allocator-value omission, implicit placement, or type-directed context selection is a separate ergonomics question, potentially related to RFC-0113. In the initial foundation, allocator selection is explicit and never silently switches between multiple candidates.

---

## 10. Struct-owned allocators and owning custody capsules

The useful motivation from RFC-0068 survives: a parser can own an arena and nodes allocated within it. The following *naive* declaration is not automatically sound merely because fields have a favorable drop order:

```text
// NOT sufficient under ordinary freely movable/partially movable structs.
struct Parser<@s> {
    arena: BumpArena<@s>,
    nodes: List<ArenaBox<AstNode, @s>>,
}
```

The implementation must control generativity and escape of `@s`, prevent premature movement or destruction of the custodian, and disallow partial moves that would expose dependent handles after arena teardown.

The intended abstraction is an **opaque owned custody package**, conceptually:

```text
Parser = exists @s . {
    arena: BumpArena<@s>,
    nodes: List<ArenaBox<AstNode, @s>>
}
```

The package transfers storage and dependent values together, enforces correct teardown, and exposes safe methods without leaking the hidden identity. Ordinary callers still write `Parser::new(source)`.

An implementation-ready mechanism for dependent owning packages is a **blocking prerequisite** for claiming that arbitrary struct-owned allocators are safe. This RFC does not pretend that synthesized field drop order alone solves self-dependency, partial moves, or pinning.

---

## 11. Well-formedness, variance, and concurrency

### 11.1 Dependency preservation

If a value's type contains handles depending on `@s`, transferring, storing, or returning that value must preserve the dependency. A wrapper cannot erase it merely by omitting an explicit `depends valid(@s)` clause. A generic function must be checked against a signature that exposes the necessary dependency/effect information; it cannot rely on checking particular later instantiations to repair an unsound abstract body.

A value containing a dependent handle cannot be placed in storage whose custodian might be revoked first, unless the owning package proves that destruction/movement order and escape rules preserve validity. Storage identity equality is rigid; a handle in `@a` is not interchangeable with one in unrelated `@b` without an authorized transfer that creates a new valid allocation or custody arrangement.

### 11.2 Variance

Rigid storage identities should not be treated as ordinary borrow lifetimes merely because both are represented by region indices internally. Storage identity is not generally covariant by time shortening. Variance of a container in `T`, `@s`, or an authority parameter depends on the representation and operations it supports and must be justified independently.

### 11.3 `Send` and `Sync`

Neither `Alloc<@s>` nor `RawStorage<@s>` automatically implies `Send` or `Sync`. Crossing a thread or fiber boundary depends on the block's ownership protocol, the custodian's thread-safety, `T`'s own requirements once initialized, and the synchronization of release and shared-access operations. A local arena's storage identity cannot be smuggled across threads merely by hiding it behind an opaque block.

---

## 12. Metel-Core model and soundness obligations

RFC-0241 should model at least:

- A set of storage domains `S`, a set of allocation identities `B`, and a set of initialized object identities `O`.
- A backing relation `backedBy(b, s)` and an optional object-occupancy relation `occupies(o, b, range)`.
- Per-allocation extent, alignment, provenance, initialization state, and exclusive release authority.
- `valid(s)` and (where needed) epoch validity; checked revocation effects.
- Ownership of initialized objects separately from ownership of raw allocations.
- Live access witnesses, loan compatibility, and location-stability obligations.

The following are required invariants, not claims of proved theorems:

**A. Nonoverlap and authority conservation.** Independently live allocations with nonzero usable bytes cannot confer exclusive authority to overlapping bytes. Partition and transfer operations conserve the ability to release the parent exactly once.

**B. No fabrication.** Safe code cannot manufacture `RawStorage` from arbitrary bytes, forge an allocation identity, claim an initialized `T` from uninitialized storage, or grant an exclusive access witness without authorization.

**C. Custody preservation.** For every live safe block or object whose usability depends on `@s`, `valid(@s)` holds. A transition revoking `@s` is rejected unless the necessary dependents have been safely discharged or transferred to an independent valid custodian.

**D. Stable direct references.** If `&r T` or `&r var T` is live, the target remains initialized, its location remains stable during `r`, and access conflicts are prevented. A live borrow is not invalidated by an unrelated allocation, resize, teardown, or GC operation.

**E. Destruction accounting.** A `T` destructor runs at most once for one initialized object, and every required destructor obligation is discharged or transferred before the corresponding storage is reused or released. Skipping cleanup is not permission to reaccess invalid storage.

**F. Failure safety.** Any allocation, initialization, or resizing failure leaves the program in a valid state with no duplicated authority and no fabricated initialized object.

**G. Generic and destructor effects.** Revocation performed through an implicit destructor, a generic wrapper, or a called function is subject to the same checks as an explicit `revokes @s` operation. Dependency and effect abstraction must be sound under separate compilation.

The raw implementation of an allocator is an explicit trust boundary. The compiler can check safe derivations from legitimate block and object capabilities, but it cannot deduce the nonoverlap or allocator-implementation invariants from arbitrary unsafe machine code. The unsafe contract and its verification obligations must therefore remain visible.

---

## 13. Worked acceptance and rejection tests

These programs describe the **intended future type-system behavior**, not behavior currently implemented in 0.16.0. For brevity, error handling is omitted where it does not affect the property under test.

### 13.1 Independent arena allocations: accept

```text
var a := arena.alloc_box(10)?;
var b := arena.alloc_box(20)?;
let x := a.borrow_mut();
let y := b.borrow_mut();
*x = 11;
*y = 21;
```

Two distinct affine allocation owners yield disjoint exclusive target permissions, even though both depend on `@s`.

### 13.2 Allocate while a different object is borrowed: accept

```text
var a := arena.alloc_box(10)?;
let x := a.borrow();
let b := arena.alloc_box(20)?;
println(*x);
```

The arena can allocate without invalidating `a`; the shared borrow does not borrow the arena object itself for its entire duration.

### 13.3 Revoke storage with a live dependent: reject

```text
let a := arena.alloc_box(10)?;
arena.dispose(); // Error: a depends on valid(@s).
println(a.borrow());
```

The rejection must also occur if `dispose()` is hidden in a helper, a generic function, or a destructor.

### 13.4 Two owners for one raw block: reject

```text
let raw := arena.allocate(Layout::of<i64>())?;
let first := core::init_owned(raw, 10);
let second := core::init_owned(raw, 20); // Error: raw moved/consumed.
```

### 13.5 Read raw storage as initialized `T`: reject

```text
let raw := arena.allocate(Layout::of<i64>())?;
let x: &i64 := raw.borrow(); // Error: no initialized i64 exists.
```

### 13.6 Relocate while a view is live: reject

```text
var values := List::new();
values.push(10);
let view: &[i64] := values.as_slice();
values.push(20); // Error while view remains live, even if spare capacity exists.
println(view[0]);
```

### 13.7 Attempt to reset an occupied arena epoch: reject

```text
let a := arena.alloc_box(10)?;
arena.reset(); // Error: current epoch has a live dependent.
```

### 13.8 Reallocate uninitialized block, preserving failure ownership: accept

```text
// Schematic optional operation; error returns the original block.
let raw := arena.allocate(Layout::array<u8>(64)?)?;
let resized := try_resize(raw, Layout::array<u8>(128)?)?;
```

An implementation must document how the original block is returned or retained if `try_resize` fails.

### 13.9 Rooted GC access: accept only under guard

```text
let root := gc.root(gc.alloc(Node { value = 1 }));
gc.with_ref(root, |node| {
    println(node.value);
});
// Returning node by direct reference outside the guard is rejected.
```

These cases should become small Metel-Core preservation and rejection obligations before implementation decisions are treated as settled.

---

## 14. Interaction with existing RFCs and supersession

The *proposed* disposition below becomes normative only if this replacement is accepted and the dependent RFCs are reconciled. It must not be read as having silently changed already accepted or implemented RFCs.

| RFC | Relationship to this replacement |
| --- | --- |
| **RFC-0063 — Allocator Handles** (`2-accepted`) | **Proposed supersession.** Retains first-class allocators and instance-level identity; replaces `@a T` / `@a expr` as a universal pointer/placement foundation with `Alloc<@s>` returning affine raw blocks. |
| **RFC-0065 — Allocator and Lifetime Ergonomics** (`2-accepted`) | **Partial proposed supersession.** Drops automatic `@`-allocation/tag elision; retains ordinary borrow/lifetime-elision questions for RFC-0067/0122 and defers optional allocator-context inference. |
| **RFC-0066 — Allocated Value Extraction** (`2-accepted`) | **Revised and narrowed.** Preserves explicit extraction and double-drop constraints but makes move-out conditional on a handle's ownership/reclamation protocol, not on a universal allocator pointer category. Aligns with RFC-0185. |
| **RFC-0068 — Struct-Owned Allocators** (`2-accepted`) | **Proposed supersession of special `struct Foo(@a: ...)` surface.** Retains the use case, but makes safe owning-custody packages an explicit prerequisite; ordinary drop order alone is not a sufficient proof. |
| **RFC-0073 — AutoAlloc** (`2-accepted`) | **Recast as an optional allocation policy.** Compiler selection must not weaken stability, validity, extraction, or concurrency guarantees. |
| **RFC-0077 — Allocator Generics** (`2-accepted`) | **Proposed supersession of tag/form-specific rules.** Separates `A: Alloc<@s>` (runtime capability and policy) from bare `@s` (storage identity), and requires independently justified variance/dependency well-formedness. |
| **RFC-0141 — Aspect Objects: Explicit Allocator Placement** (`2-accepted`) | **Proposed supersession of `@[r] dyn Aspect` placement syntax.** Explicit allocation is preserved through an owning library handle and existing object metadata/vtable requirements from RFC-0008. |
| **RFC-0143 — previous text** (`1-under-review`) | **Direct replacement.** Removes `T@a`, `place a expr`, allocator-selected `Handle<T>` as foundational features; retains and strengthens the raw runtime-buffer substrate identified there. |
| **RFC-0242 — Library-Defined References and Generalized Place Access** (`0-draft`) | **Foundational prerequisite.** Supplies storage validity dependencies, checked revocation, target-bound ownership/access witnesses, and custodian contracts. The *revised* RFC-0242 is intended; reconcile if its repository version differs. |
| **RFC-0241 — Metel-Core** (`0-draft`) | **Validation companion.** Formalizes preservation, access, custody, and release invariants before implementation. |
| **RFC-0159 — Abstract Regions and a Dedicated Identity Channel** (`1-under-review`) | **Compatible intended substrate, new syntax decision.** Storage identities use `@s`, borrow regions use `&r`, brands use `'b`; they may share an internal region-index representation, but not semantics. |
| **RFC-0076 — Brand Types** (`1-under-review`) | **Orthogonal.** Keeps generative brands `'b` for authority/gating; brands do not prove storage liveness or allocation disjointness by themselves. |
| **RFC-0067 — Lifetime Anchors** and **RFC-0122 — Borrow Checking** (`1-under-review`) | **Generalized by RFC-0242.** Preserve sound reference lifetime/exclusivity goals; dependent storage validity is not an exclusive borrow of an allocator, and returned access keeps the relevant loan/custody requirements. |
| **RFC-0071 — Ownership and Move Semantics** (`3-integrated`) and **RFC-0089 — Linear Types** (`2-accepted`) | **Foundational.** Raw blocks are affine by default; mandatory release/discharge is an optional stronger obligation governed by linearity. Initialization and partial moves must preserve object/drop state. |
| **RFC-0026 — Unsafe Blocks** (`0-draft`) | **Implementation prerequisite.** Defines or coordinates the trusted `unsafe` vocabulary and how allocators may establish raw block resources. |
| **RFC-0133 — From-Metel List: Runtime-Sized Buffer Gap** (`0-draft`) | **Directly addressed at the design level.** Adds checked runtime-sized raw allocation and initialization-state requirements; does not claim that the evaluator implements them yet. |
| **RFC-0053 — Fixed-Size Arrays**, **RFC-0054 — List**, **RFC-0124 — Sequence Types**, **RFC-0126 — Borrowed View**, **RFC-0171 — Prefix Array Syntax**, and **RFC-0172 — Sized/Unsized Kinds** | **Collection integration.** Fixed-size `[T; N]` remains owned. The revised RFC-0242 proposes `[T]` as an unsized payload and explicit `&[T]` / `&var [T]` borrowing, a substantive revision to the currently implemented bare `[T]` view semantics. `OwnedBuffer` supplies raw dynamic backing for `List`. |
| **RFC-0139 — Garbage-Collected Allocators** (`1-under-review`) | **Reframed, not resolved.** GC can use raw allocation internally but is not forced to expose `Alloc` for movable objects. Root completeness, finalization of affine contents, cross-arena edges, and concurrency remain independent blockers. |
| **RFC-0008 — Aspect Objects** and **RFC-0185 — Remove Type-Directed Dereference** | **Preserved behavior.** Vtable/object-safety semantics remain separate from storage policy; implicit extraction is not reintroduced. |
| **RFC-0113 — Context Parameters**, **RFC-0082 — Associated Types**, **RFC-0093/0095 — Metadata/Comptime Syntax** | **Adjacent design dependencies.** This RFC does not commit to context-driven allocator omission, unrestricted generic associated handle families, or restoring prefix `@` metadata at the expense of `@s` storage identities. |

Existing RFCs **retain their actual statuses** while this replacement is reviewed. After acceptance, affected documents, reference spec, registry/indices, and tracking issues must be updated through the RFC process; this file alone is not a silent status transition.

---

## 15. Alternatives considered

1. **`Alloc` returns `RawPtr`.** Small interface, but raw pointers erase provenance, unique release authority, and typed initialization guarantees that higher-level safe abstractions would otherwise have to rebuild manually. Rejected as the safe foundation; raw pointers may still exist within unsafe implementations.
2. **`Alloc` selects `Handle<T>`.** Closest to the previous RFC-0143 and RFC-0139. Convenient for `place`, but makes ownership and GC policies part of the low-level allocator contract. Rejected as the foundation; a typed high-level layer can still expose associated handle types where useful.
3. **Make `allocate<T>` mandatory.** Couples storage acquisition to object initialization and excludes raw runtime-sized buffers; a poor fit for `List` and custom containers. Rejected.
4. **Make `Reallocate` mandatory.** Forces a capability some arenas/pools cannot provide and complicates stabilization and pinning. Rejected; resizing is optional.
5. **Treat every allocation as a long-lived mutable borrow of its allocator.** Prevents bulk teardown but also blocks independent allocations and can conflate distinct object targets. Rejected in favor of validity dependencies plus allocation-local access authority.
6. **Let GC weaken `RawStorage` stability.** Would make arbitrary direct references unsound unless every client understood collector relocation. Rejected; moving GC uses a different managed-object protocol or pinned blocks.
7. **Require an arbitrary user-defined layout language now.** Not necessary for checked contiguous buffers. Rejected for this RFC; composable dynamic layouts remain a future extension.

---

## 16. Risks and open questions

The architectural boundary is proposed as settled **within this replacement**, but these questions require answers before implementation or acceptance that claims a complete safe library protocol:

1. **Trusted block-establishment vocabulary.** Exactly which unsafe/compiler primitives establish a `RawStorage` implementation, provenance, disjointness, and release authority? Should `RawStorage` be sealed initially?
2. **Release-ticket representation.** How is an independent block's reclamation capability encoded, especially when the allocator requires internal synchronized mutation? Is ordinary `Drop` sufficient or is an explicit linear retirement token necessary for certain allocators?
3. **Generativity and owning packages.** How do allocator constructors create a fresh `@s` and how do opaque owners package their own arena with values depending on that identity? Which moves and field projections must be forbidden?
4. **Generic checking and effects.** How are `revokes @s`, implicit destructors, field-wise dependencies, and abstract generic functions represented so that separate compilation cannot hide invalidation?
5. **Initialization under failure and partial construction.** What is the minimal typed builder protocol, including cleanup for linear or non-discardable elements and behavior under panics/effects?
6. **API surface and ergonomics.** Is `unsafe aspect` the right surface for `Alloc`? Should `RawStorage` be a sealed marker plus intrinsics? Is optional `place` justified by real generic APIs once typed constructors are usable?
7. **Zero-sized and over-aligned allocations.** Define address/provenance equality, allocation identity, and rejected/unsupported layouts precisely.
8. **Reallocation and pinning.** Which optional resize contracts preserve or return the old block on failure, and what generic movability constraints are needed for typed buffer growth?
9. **Concurrency and GC.** Precisely which block and custodian protocols permit `Send`/`Sync`, and how do collectors establish root/guard stability independently of the raw allocator foundation?

These are not an excuse to reopen the architectural split. They are the concrete obligations needed to make that split safe and implementable.

---

## 17. Suggested implementation and verification sequence

1. **Formal model:** add storage blocks, allocation identities, initialization state, release authority, validity domains, and revocation to RFC-0241's Metel-Core stages.
2. **Minimal trusted primitives:** specify and validate block acquisition/retirement and one-element initialization, first with a built-in heap implementation.
3. **Safe unique ownership:** build and test `Unique<T, B, @s>` (or an equivalent opaque owner) with independent borrowing and correct destruction/extraction.
4. **Arena instance identity:** introduce generative `@s`, `depends valid(@s)`, and checked revocation; verify that independent arena blocks can be allocated and borrowed simultaneously.
5. **Runtime-sized buffer:** add checked array layout arithmetic, initialized-prefix tracking, and `OwnedBuffer<T>` with basic allocate-and-move growth.
6. **Optional capabilities:** prototype `Reallocate`, pool allocation, and higher-level typed-allocating aspects without changing the base `Alloc` contract.
7. **Owning capsules and GC integration:** address externally dependent structures and moving collectors only after their respective safety protocols are explicit.
8. **Reconcile the RFC corpus:** update affected accepted RFCs, reference specifications, and examples only after substantive review and proof/prototype gates pass.

Each stage should include rejecting tests from section 13, not just success-path examples. A successful tree-walking evaluator run does not substitute for static ownership and lifetime enforcement.

---

## References

- [RFC-0242 — Library-Defined References and Generalized Place Access](../0-draft/rfc-0242-library-defined-references-and-generalized-place-access.md) — proposed revised custody/validity/access model.
- [RFC-0241 — Metel-Core](../0-draft/rfc-0241-metel-core-a-formal-semantic-foundation-for-metel.md) — formal semantic foundation.
- [RFC-0063 — Allocator Handles](../2-accepted/rfc-0063-allocator-handles.md).
- [RFC-0065 — Allocator and Lifetime Ergonomics](../2-accepted/rfc-0065-allocator-ergonomics.md).
- [RFC-0066 — Allocated Value Extraction](../2-accepted/rfc-0066-allocated-value-extraction.md).
- [RFC-0068 — Struct-Owned Allocators](../2-accepted/rfc-0068-struct-owned-allocators.md).
- [RFC-0073 — AutoAlloc](../2-accepted/rfc-0073-auto-alloc.md).
- [RFC-0077 — Allocator Generics](../2-accepted/rfc-0077-allocator-generics.md).
- [RFC-0141 — Aspect Objects: Explicit Allocator Placement](../2-accepted/rfc-0141-aspect-objects-explicit-allocator-placement.md).
- [RFC-0139 — Garbage-Collected Allocators](../1-under-review/rfc-0139-garbage-collected-allocators-and-allocator-determined-pointer-types.md).
- [RFC-0159 — Abstract Regions and a Dedicated Identity Channel](../1-under-review/rfc-0159-abstract-regions-and-a-dedicated-identity-channel.md).
- [RFC-0133 — From-Metel List: the Runtime-Sized Buffer Gap](../0-draft/rfc-0133-from-metel-list-the-runtime-sized-buffer-gap.md).
- [RFC-0172 — Sized and Unsized Kinds](../0-draft/rfc-0172-sized-and-unsized-kinds-and-a-generalized-unsizing-coercion.md).
- [RFC-0124 — Sequence Types](../1-under-review/rfc-0124-sequence-types-fixed-arrays-slices-and-the-growable-list.md).
- [RFC-0122 — Borrow Checking](../1-under-review/rfc-0122-borrow-checking.md).
- [RFC-0067 — Lifetime Anchors](../1-under-review/rfc-0067-lifetime-anchors.md).
- [RFC-0076 — Brand Types](../1-under-review/rfc-0076-rc-brands.md).
- [RFC-0026 — Unsafe Blocks](../0-draft/rfc-0026-unsafe-blocks.md).
- [RFC-0071 — Ownership and Move Semantics](../3-integrated/rfc-0071-ownership-and-move-semantics.md).
- [RFC-0089 — Linear Types](../2-accepted/rfc-0089-linear-types.md).
- [RFC-0185 — Remove Type-Directed Dereference](../4-implemented/rfc-0185-remove-type-directed-dereference.md).

---

## Decision

**Outcome:** *(pending)*

**Target:** *(to be set through the RFC process)*

**Acceptance preconditions:** Explicit agreement with the revised RFC-0242 semantics; a sound trusted `RawStorage` establishment/release contract; a checked story for `@s` generativity and revocation (including generic destructors); proof/prototype results for independent arena allocations and runtime-sized initialization; and a reviewed migration/supersession plan for the accepted allocator cluster.
