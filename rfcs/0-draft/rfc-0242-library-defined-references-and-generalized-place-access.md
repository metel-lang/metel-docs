---
id: rfc-0242
title: "Library-Defined References and Generalized Place Access"
date: '2026-11-17'
updated: '2026-11-18'
status: draft
---

> **Replacement draft (2026-11-18).** This document replaces the earlier RFC-0242 draft under the **same RFC ID**. It proposes an integrated ownership, custody, validity, and access model, rather than treating access witnesses and origins in isolation. It is a design proposal, **not an accepted amendment** to the other RFCs cited here and not a claim about features available in Metel v0.16.0.
>
> **Syntax convention.** Ordinary declarations, receivers, references, bindings and assignments follow the Metel v0.16.0 `develop` grammar where possible. The generic forms `@s` (storage identity), `'b` (brand), and `&r` (explicit borrow region), the clauses `depends valid(@s)` and `revokes @s`, and the unsized interpretation of `[T]` are **proposed**. Examples involving `Gc`, `Rc`, allocation capabilities, compiler intrinsics, or `unsafe` are sketches of future APIs. In particular, `unsafe` examples are contracts, not assertions that v0.16.0 already parses an unsafe language feature.

## Summary

Metel should allow libraries to define reference and storage-management abstractions while preserving a common, compiler-enforced memory-safety model. The proposal separates four concerns that conventional reference or allocator types often combine:

1. **Value ownership:** who may move, destroy, or transfer an initialized object.
2. **Storage custody and validity:** which resource or protocol keeps the object's backing storage and initialized value alive.
3. **Location stability:** whether an object's current physical address is usable throughout a direct reference's lifetime.
4. **Access authority:** which shared or exclusive accesses may coexist over particular places.

These are orthogonal. An arena can own storage while independent handles own individual values. `Rc` can retain allocation validity without granting exclusive mutation. A moving garbage collector can maintain reachability and temporarily stabilize a target. A branded token can authorize access without owning or keeping alive the target.

The **unifying rule** is that creating a safe direct reference requires sound, target-bound evidence of (a) an initialized live target, (b) a usable and stable location, and (c) compatible access authority for the entire reference duration. The compiler tracks ownership, places, loans, capability transfer, and static validity dependencies. Libraries implement custody protocols; trusted operations establish guarantees that safe Metel alone cannot derive.

This RFC proposes:

- First-class, compiler-tracked **access witnesses** with structural projection, reborrowing, and checked splitting.
- First-class **custodian resources** with compiler-tracked relationships to validity domains and specific objects.
- Storage identities spelled `@s`, brands spelled `'b`, and borrowed access durations spelled `&r`, with distinct semantics.
- `depends valid(@s)` on value types and a checked `revokes @s` invalidation effect. These clauses do not grant access or revocation authority.
- Controlled, target-bound reference-establishment operations and an explicit unsafe/trusted boundary.
- A shared design for static arenas, arena-owned keys, reference counting, branded reference counting, tracing GC, custom containers, and externally managed memory.
- The collection distinction `[T; N]` (owned sized array), `[T]` (unsized sequence payload), `&[T]` (shared view), `&var [T]` (exclusive view), and `List<T>` (growable owner).

General composable dynamic-layout definitions are **deferred**. The initial design uses a compiler-known unsized `[T]` payload and generalized reference/access rules rather than a slice-specific borrow checker.

RFC-0241 (Metel-Core) is the intended formal-validation companion. This RFC does not claim a soundness proof or a complete implementation-ready calculus.

---

## Motivation

### A unified problem, not a collection of special pointers

The present RFC corpus contains interrelated designs for borrowing, lifetime anchors, brands, allocator-selected handles, garbage collection, and collection views. Each addresses a legitimate need, but several conflate storage location, allocation identity, lifetime, or access permission.

For example, a bump arena can allocate independently owned objects:

```text
// Proposed library API.
var arena := Arena::new();
var first := arena.alloc_box(10);
var second := arena.alloc_box(20);

let a := first.borrow_mut();
let b := second.borrow_mut(); // Should be legal: distinct targets.
```

The arena's continued existence is necessary for both handles. It should not follow that acquiring exclusive access to `first` exclusively borrows the arena's *allocator metadata*, preventing further allocations or access to `second`.

Conversely, a copyable arena key or GC handle is not proof of unique access. Two copies may identify the same object. Neither a shared arena identity nor a common type proves disjointness.

We want libraries to implement these patterns without a new compiler borrow rule for each container or collector.

### Why reference counting and GC matter to this foundation

A static arena dependency can keep an external storage owner alive. An `Rc` uses a runtime protocol instead: a retained strong owner makes the allocation live. A tracing collector maintains objects reachable from complete roots, and a relocating collector must additionally protect addresses of direct references. A branded token supplies access authority but not object liveness.

These differences concern **how guarantees are maintained**, not what a safe reference is allowed to do. The compiler should check the common guarantees and permit trusted libraries to supply the dynamic portions.

### Why collections are a useful stress test

The existing `[T]` is a sized, non-owning `Copy` view. The requested revised surface is `&[T]` / `&var [T]` over an unsized `[T]` payload. This exposes the need to distinguish reference representation, unsizing, element access, buffer ownership, and invalidation during `List<T>` growth. Treating them separately avoids hardcoding special list- or slice-specific borrowing rules.

---

## Design principles and scope

1. **Common safety invariants.** Safe code cannot forge access, read uninitialized objects, produce dangling direct references, or violate exclusive-access compatibility.
2. **First-class resources, checked relationships.** Custodians are ordinary moveable library-defined values where possible; the validity guarantees associated with them are tracked by the compiler or upheld through explicit trusted contracts.
3. **No authority from a name alone.** Matching types, brands, or storage identities never prove two dynamic handles disjoint, nor prove that a pointer identifies an initialized object.
4. **Static guarantees when available.** Ordinary borrowing, structural disjointness, and arena invalidation should be checked statically. Runtime checks are permitted for abstractions requiring them, but are not compulsory for ordinary references.
5. **No universal pointer representation.** Stable direct references, tagged handles, arena indices, reference-counted pointers, and relocating-GC handles need not share a physical representation.
6. **Ergonomic ordinary code.** Existing `&`, `&var`, `fun`, `extend`, `var`, `let`, and ordinary field access remain the routine surface. Most programmers do not manipulate proof objects directly.
7. **Small trusted base.** Operations that mint or bind access to memory cannot be implemented by arbitrary unchecked safe assertions.
8. **No requirement to preserve earlier RFC decisions.** Where needed, this proposal expressly requests changes to existing accepted or implemented design decisions; acceptance must reconcile those changes rather than silently overriding them.

**Included:** logical object/place identities; ownership and initialized-state interaction; first-class witnesses; storage-domain dependencies; revocation; custody protocols; arenas, keys, `Rc`, GC and brands as stress cases; sequence views; soundness obligations; interoperability with Metel-Core.

**Excluded:** arbitrary user-defined dynamic layouts; full GC tracing algorithms and stack-map ABI; a final grammar for every unsafe intrinsic; a full general-purpose proof language; automatic verification of arbitrary unsafe libraries; a full re-specification of allocator-placement expressions; generalized concurrency/atomics; and an implementation schedule for v0.16.0.

---

## Proposal

### 1. Vocabulary and identities

The model distinguishes the following entities:

| Entity | Meaning | Candidate spelling |
|---|---|---|
| Logical object | One initialized value instance, distinguished from reused storage | internal identity `o` |
| Place | Object or field/index projection, used for moves and access | `value.field`, `value[index]` |
| Storage domain | Resource whose invalidation may invalidate dependent objects | `@s` |
| Brand | Generative rigid identity of an authority domain | `'b` |
| Borrow duration | Interval/region for an access relationship | `&r` |
| Access mode | Permission to read or exclusively mutate | `Shared`, `Exclusive` (conceptual) |

A **brand is not an allocation identity**: many cells may share `'b`, and multiple handles with the same brand may alias. A **storage identity is not a borrow**: two allocations may depend on `@s` while being borrowed independently. A **borrow duration is not an allocator placement**.

Storage parameters use `@s` consistently:

```text
struct ArenaBox<T, @s>
    depends valid(@s)
{
    allocation: OwnedAllocation<T, @s>,
}

struct BrandedRc<T, 'b> {
    owner: Rc<BrandedCell<T, 'b>>,
}

// Explicit reference-region syntax is proposed; ordinary &T remains elided.
fun identity<&r, T>(value: &r T) -> &r T {
    value
}
```

In RFC-0143, `T@a` means allocator placement/allocator-selected handle. This RFC does not reuse that postfix form to mean a borrowed reference's origin. The use of `@s` **as a generic identity** is a distinct role; its interaction with RFC-0143's placement syntax must be reconciled explicitly.

### 2. Abstract machine invariants

Let `W` be a machine state, `o` a logical object, `p` a concrete location, `q` an access interval, and `m` an access mode.

- `Alive(W, o, q)` means the object exists and remains initialized, including the particular subplaces needed by the access, throughout `q`.
- `Located(W, o, p, q)` means the location and representation of `o` are usable through the direct reference throughout `q`, including stability against relocation.
- `Permit(W, o, m, q)` means the access is supported by an authority whose live loans are compatible with all other accesses to overlapping places.

The reference-establishment obligation is:

```text
Alive(o, q)   Located(o, p, q)   Permit(o, mode, q)
--------------------------------------------------
             DirectRef(o, p, mode, q)
```

The target identity must match across all three premises. Merely passing a `RawPtr<T>` and three type-correct but unrelated witnesses must not create a safe `&T`.

The machine tracks initialized places and partial moves; allocating a new object into a freed slot creates a **new logical object identity** even if the physical address is reused. A fresh type-level identity for each ordinary runtime allocation is not required.

The global safety invariant is that every active safe direct reference remains live, correctly located, initialized for its permitted operations, and free of incompatible overlapping access. All safe machine transitions must preserve that invariant.

### 3. Ownership and access authority

Ownership over a value and permission to access it are related but not identical.

A unique owner can ordinarily move or destroy an initialized value, subject to outstanding loans and any destruction constraints. Shared and exclusive accesses are temporary authority derived from owners, guards, or a properly trusted interior-access protocol.

The conceptual compiler capability is:

```text
AccessWitness(target, mode, duration, parent-loan, dependencies)
```

It is target-bound and may be represented statically, dynamically, or in a mixed representation. A value of type `AccessWitness<T>` without a verified link to its specific target is insufficient.

The minimal operations to formalize are:

- **Acquire:** derive read or exclusive access from an owned place or authorized provider, checking conflicts.
- **Project:** derive an access to a known subplace (field, tuple component, checked element/range).
- **Reborrow:** derive a child loan and suspend/restrict the relevant parent authority until the child ends.
- **Split:** divide exclusive access into verified disjoint places, preserving the total authority and common validity dependencies.
- **End/transfer:** terminate a loan or move an affine witness without duplicating its authority.
- **Establish:** a controlled trusted operation binding an actual target/location to liveness, stability, and permission evidence.

Structural disjointness is expressed over logical places rather than addresses alone. Two different array indices can have the same physical address for zero-sized elements; access identities and index projections must still behave coherently.

Ordinary Metel references should elaborate to the same witness semantics as library-defined reference abstractions. The compiler may reserve a fundamental reference/capability representation and calling convention: *library-defined* means libraries can derive and expose the same safe access semantics, **not** that safe libraries can synthesize arbitrary bare references from raw bytes.

### 4. Validity dependencies and first-class custodians

A **custodian** is a first-class resource whose presence, borrow, or runtime protocol maintains a validity guarantee. The custodian need not own the value it protects and need not grant access to it.

Examples:

- `Arena` owns backing storage and the authority to reclaim it.
- `ArenaBox<T, @s>` owns an initialized value in storage maintained by `Arena<@s>`.
- `Rc<T>` retains a strong owner via reference counting.
- `GcRoot<T>` retains a GC reachability guarantee.
- `GcPin<T>` retains or borrows a rooting/stability guarantee.
- `Token<'b>` supplies access authority, **not** storage custody.

The core tracks a relation `Depends(x, @s)`: while resource `x` is live, storage domain `@s` must remain valid. `depends valid(@s)` declares this obligation on a type:

```text
struct ArenaBox<T, @s>
    depends valid(@s)
{
    allocation: OwnedAllocation<T, @s>,
}
```

The clause **does not prove that any particular `T` is initialized** and does not create a storage owner. It restricts when a custodian's storage may be revoked. A resource may depend on several domains; dependency composition is conjunctive (each is required), not an invitation to treat different domains as interchangeable.

Dependencies contained in fields, tuples, closures, and collections propagate. An abstract/opaque type may expose an explicit dependency as part of its public interface. Removing such a dependency from a returned value is rejected unless an operation actually acquires independent custody or moves the value into independently owned storage.

#### 4.1 A dependency must be linked to a real storage owner

A phantom `@s` alone cannot keep memory alive. The creation of `@s` must be associated with a generative storage-domain owner or a verified storage protocol, and operations that could invalidate that domain must be checked against all dependents.

A constructor may return an arena bound to a fresh, non-forgeable identity; the exact fresh-identity introduction syntax is outside this RFC. Safe code may not write an arbitrary `ArenaBox<T, @s>` and thereby gain access to storage it does not own.

An arena handle with `depends valid(@s)` carries a persistent obligation even if a particular derived reference is no longer used. If its value must still be destroyed, liveness is not merely the last syntactic read of the handle. Drop/elimination and any linearity restrictions must be accounted for.

#### 4.2 Custody may be borrowed or retained

Two common strategies have different mechanics:

- **Borrowed custody:** `&Rc<T>` protects an allocation because an ordinary borrow prevents the final owner handle from being destroyed while the derived reference is live.
- **Retained custody:** a `Rc<T>` copied by `.share()` or moved into an owning wrapper protects the allocation itself; the resource's internal refcount protocol is runtime-backed.

A single custodian may support more than one target. For example, independent arena handles may share `valid(@s)` while retaining separate exclusive access authority. This does not automatically cause an exclusive borrow of the arena's allocator metadata.

### 5. Invalidation and revocation effects

The declaration:

```text
// Proposed syntax; body omitted.
fun dispose<@s>(owner: StorageOwner<@s>) revokes @s;
```

means that the operation may invalidate the resource domain `@s`. It is a **checked effect**, not permission to invalidate arbitrary domains. The operation must possess appropriate revocation authority, and its call is invalid while any incompatible dependencies remain live.

An operation's revocation effect is inferred or checked from its body and called operations. A safe library cannot omit `revokes @s` to hide deallocation. Implicit destruction of a custodian may carry the same effect and must be checked.

Conceptually:

```text
OwnRevoke(@s)    NoOutstandingDependents(@s)
---------------------------------------------
                 Revoke(@s)
```

The rule must cover values and references that retain their dependency through function calls, aggregates, and destructor obligations. It must account for dependencies consumed in the same transition and for nested domains; the simple presentation above is not the final operational rule.

A method that merely mutates allocator metadata or allocates from free storage need not revoke existing domains. Conversely, **being passed `&var Arena<@s>` must not grant an escape hatch for resetting or deallocating live backing storage**. The compiler checks the revocation effect (or equivalent exclusive revocation-capability consumption) of the called operation, including internally.

#### 5.1 Epochs and per-object invalidation

Invalidation of a whole backing allocation is not always the correct granularity. An arena `reset` may preserve its physical buffer while destroying or reusing contained objects. A resettable arena can have an allocation **epoch** distinct from its backing-storage domain. Reset revokes the old epoch and establishes a fresh one. The API must prevent retained handles from depending on the old epoch; the exact syntax for existential fresh-epoch results is deferred.

A container can also invalidate only specific elements or ranges. The witness model tracks loans over those places. A copyable key that does not itself confer access can remain inert after removal, but every lookup must validate that the key still denotes a live object (for example, using a slot generation). Such a key is not equivalent to a borrowed reference.

### 6. Trusted proof establishment

The compiler need not understand refcount arithmetic or tracing collection to accept an ordinary `&T`, but it **must not accept arbitrary claims of liveness or location stability from safe code**.

The design distinguishes:

1. **Checked derivation.** References, owned allocations, field projections, and safe splitting produce new witnesses from existing verified authority.
2. **Trusted establishment.** An implementation maintains required guarantees through a mechanism whose correctness is not derivable solely from the type checker: raw-pointer provenance, reference counting, GC roots/pins, OS-managed memory, etc.

At the trusted boundary, a target-bound operation conceptually combines:

```text
InitializedObject(o) + AliveFor(o, q)
                    + StableAt(o, p, q)
                    + Permit(o, mode, q)
       --> DirectReference(o, p, mode, q)
```

These are **semantic judgments**, not necessarily first-class public `AliveProof` and `StableProof` objects. They may be embodied by opaque library types plus checked lifetime relationships. In particular, a contract cannot simply be an unchecked `ValidityProvider<T>` trait that fabricates proofs in safe code.

A trusted implementation must establish and preserve:

- pointer/target provenance, alignment, bounds, layout, and correct initialization;
- no illegal duplication of unique ownership or exclusive access;
- complete target-bound evidence for the entire derived borrow duration;
- correct cleanup and invalidation on drops, panic/unwinding, cancellation, and any concurrency or GC safepoints it permits;
- safety of all safe operations subsequently exposed by the abstraction.

The RFC does not require the entire GC or RC implementation to be compiler-verified. It requires its invariant to be an explicit unsafe/trusted obligation, suitable for later verification in Metel-Core.

### 7. Access leases, transfer, and owning references

An **access lease** packages an access witness with the custody/stability relationships required for a safe direct reference. The lease may borrow its custodian or itself retain one.

Conceptually:

```text
AccessLease(target, mode, custody, duration)
```

It is not required that a public `Lease` type exist. Its key constraints are that access authority is not duplicated improperly and that custody is not released before dependent access ends.

A borrowed reference can cross function boundaries if its signature preserves the relevant relationship:

```text
fun first<&r, T>(xs: &r [T]) -> &r T {
    // Checked projection; assumes a nonempty slice or handles failure.
    &xs[0]
}
```

A reference into a locally owned array cannot escape if the owner is destroyed during return:

```text
// Must be rejected under proposed borrowed-view rules.
fun bad() -> &[i64] {
    let values := [1, 2, 3];
    &values
}
```

An owning wrapper can retain a `Rc<T>` and **derive** a reference when borrowed, avoiding self-reference:

```text
struct OwningView<T> {
    owner: Rc<T>,
}

extend<T> OwningView<T> {
    fun borrow(&self) -> &T {
        self.owner.borrow()
    }
}
```

More general owning references with an internal borrowed field and an internal owner/guard may require **opaque dependent custody capsules** or a trusted constructor/destructor protocol. Ordinary structs containing an owner plus a reference borrowed from that owner do not automatically become safe merely because the underlying allocation has a stable address. The first version favors deriving short references from owned custodians on demand; general self-dependent capsules remain an explicitly tracked open design issue.

A lease can combine a borrowed brand token for permission with an owned `Rc` or GC pin for validity. All contributors must agree on the target, and the active duration is limited by the shortest required supporting guarantee.

### 8. Arena allocation as a case study

The arena design deliberately separates **storage ownership** from **value ownership**. Two variants can coexist.

#### 8.1 Externally owned values: `ArenaBox`

```text
// Proposed types and API; constructor internals are trusted or built on
// checked allocation, partition, and initialization primitives.
struct Arena<@s> {
    // Maintains storage domain @s, free-space authority, and reclamation authority.
}

struct ArenaBox<T, @s>
    depends valid(@s)
{
    allocation: OwnedAllocation<T, @s>,
}

extend<@s> Arena<@s> {
    fun alloc_box<T>(&var self, value: T) -> ArenaBox<T, @s> {
        // Allocate nonoverlapping storage and transfer value ownership.
    }
}
```

The arena maintains backing storage; each `ArenaBox` owns its initialized `T` and corresponding unique allocation authority. Independently allocated boxes can be exclusively borrowed at the same time. Further allocation can proceed while boxes remain live if the arena guarantees existing allocation addresses and values remain valid.

```text
var arena := Arena::new();
var a := arena.alloc_box(10);
var b := arena.alloc_box(20);

let ra := a.borrow_mut();
let rb := b.borrow_mut(); // Permitted: independent allocation targets.
*ra = 11;
*rb = 21;
```

`drop(arena)` or a revoking `reset` must be rejected while live `ArenaBox` values depend on its domain. Dropping an `ArenaBox` destroys its `T` when appropriate and releases the allocation authority; the arena may reclaim/reuse the slot under a sound reuse protocol. The arena itself must not destruct independently owned `T` values behind live handles.

An implementation based on one `Vec`-like buffer that physically relocates elements upon growth cannot offer unrestricted further allocation while direct handles into the old buffer remain live. A chunked/nonmoving allocator, stable indirection, or restrictive growth protocol is required.

#### 8.2 Arena-owned values: `ArenaKey`

An arena may instead own the values as well as the storage. Clients receive **keys** identifying slots, not independent reference or value ownership. Access goes through the live arena under an appropriate borrow or checked lookup.

```text
var arena := Arena::new();
let key := arena.insert(42);

arena.with_mut(key, |value| {
    *value = 43;
});
```

Keys may be copyable because they do not themselves authorize dereference. The arena can destroy arena-owned values during `clear`, subject to outstanding accesses; subsequently used keys must be rejected by its lookup protocol. A key may survive the arena only if its representation and API make it inert without the arena; a key with a static arena dependency may instead be forbidden to escape.

A single arena may support both `alloc_box` and `insert`, maintaining the different value-ownership policies in its bookkeeping. A `clear_owned` operation can destroy arena-owned values without invalidating externally owned boxes; a full `reset` must account for both.

#### 8.3 Backing-storage ownership policies

The same access rules admit arenas backed by a statically maintained root, shared refcounted storage, or partitioned linear storage regions. The choice affects deallocation protocols, not the meaning of `&T` or `&var T`. Partitioning one physical allocation does **not** allow one partition to free the common allocation while others are live.

### 9. Reference counting and branded access

An ordinary `Rc<T>` is a **runtime-backed custodian**. A strong owner retains allocation validity. A shared reference may borrow from a live strong owner:

```text
let a := Rc::new(42);
let b := a.share();
let r := a.borrow();
// b may be released independently; a must remain borrowed while r is live.
```

`Share` creates another strong owner of the *same allocation*, not a second exclusive access capability. Exclusive mutation through plain shared `Rc` requires an established uniqueness protocol, checked interior mutability, or separately supplied authority.

Branded cells illustrate independently supplied access permission:

```text
// Proposed generative-brand block and types.
brand 'b {
    var token := Token::new();
    let a := BrandedRc::new(10);
    let b := a.share();

    let r := b.borrow_mut(&var token);
    *r = 42;
}
```

`BrandedRc<T, 'b>` retains the object through reference counting. `&var Token<'b>` supplies exclusive access within the protected domain. The returned mutable reference borrows **both** the owner (for validity) and the token (for authority). All access to the protected contents must participate in the token protocol; no unrestricted `&T` through the shared owner may bypass it.

A single exclusive `Token<'b>` generally serializes mutable borrows even to distinct branded objects. Splitting it into two identical exclusive tokens is unsound. Libraries may expose a verified disjoint-target API or authority-domain partition to enable concurrent exclusive access.

A brand may govern many allocations. Brand rigidity must not be mistaken for proof of distinct per-object addresses, including repeated runtime allocations at one source site.

### 10. Tracing garbage collection

GC fits the model through runtime custody and temporary location stability:

- A `Gc<T>` handle may be copyable and need not be an exclusive value owner.
- The GC protocol must discover **all** roots and trace **all** relevant edges. Borrow liveness alone is not a complete root-finding algorithm.
- A root or retained heap owner maintains reachability/liveness; it does not automatically freeze the object's physical address.
- A moving collector must pin, suspend relocation, or use an address-resolving access scope before exposing a direct `&T` or `&var T`.
- Destroying the entire GC heap has a distinct invalidation obligation from collecting unreachable objects.

```text
let gc := GcRegion::new();
let node := gc.alloc(Node { value = 10 });

gc.with_ref(node, |value| {
    println(value.value);
});
```

The callback interface is only safe if the temporary direct reference cannot escape and remains stable during all allowed operations, including nested collection/safepoints. A scoped root/pin or equivalent guard is required. A pinned handle can be moved as a **custodian value** if doing so preserves its root/pin registration; an already borrowed direct reference cannot outlive the pin guard.

A hypothetical GC-backed branded cell combines three independent mechanisms: reachability, stability, and exclusive token authority. No GC-specific borrow checker is required, but the collector's runtime contract may require compiler support for stack maps, safepoints, write barriers, and other runtime integration. Root discovery, cross-heap edges, affine contents/finalizers, and concurrency are not settled here.

### 11. Collections and unsized sequence views

The proposed public collection split is:

| Form | Meaning | Status relative to 0.16.0 |
|---|---|---|
| `[T; N]` | Owned, statically sized sequence | Preserved |
| `[T]` | **Unsized sequence payload**, not a value-sized borrowed view | Changed semantics |
| `&[T]` | Shared, non-owning slice reference | Proposed use of existing `&` on unsized payload |
| `&var [T]` | Exclusive, mutable slice reference | Proposed use of existing `&var` on unsized payload |
| `List<T>` | Resizable owner of initialized elements and buffer capacity | Preserved role |

Array literals continue to produce `[T; N]`. Safe coercion `&[T; N]` -> `&[T]`, and its exclusive counterpart, needs compiler-known metadata for length and a checked unsizing operation. The coercion produces a **borrow**, not a new owner. The reverse is not valid. The common access checker handles shared/exclusive compatibility; no slice-specific borrow rules are needed.

```text
var fixed := [10, 20, 30];
let view: &[i64] := &fixed;
// An overlapping mutation of fixed is rejected while view remains live.
```

A shared reference `&[T]` can be `Copy` without requiring `T: Copy`; copied references inherit their validity/loan relationships. An exclusive `&var [T]` cannot be freely copied.

`List<T>::as_slice(&self) -> &[T]` obtains a shared borrow of the currently initialized prefix. `as_mut_slice(&var self) -> &var [T]` obtains exclusive access to that prefix. `push`, `pop`, `clear`, and potential reallocation are conservatively incompatible with outstanding views through ordinary whole-list borrowing. More precise operations may preserve subrange validity if their access/effect contracts prove it.

A safe `split_at_mut` can consume an exclusive slice access and yield two nonoverlapping exclusive subviews after bounds checking. It transfers/partitions the witness, not duplicates it.

**The unsized payload `[T]` is initially compiler-recognized**: its runtime layout is a repeated sequence of `T` with pointer metadata containing a length. An initial `Sized`/unsized kind distinction and wrapper-aware unsizing are necessary. General user-defined unsized payloads and composable dynamic layouts are **future work**.

A Metel-defined `List<T>` further needs a runtime-sized `OwnedBuffer<T>` allocation primitive with capacity, initialized-prefix tracking, fallible allocation, destruction of only initialized elements, and correct deallocation. This is a separate gap from reference validity. The design must support `Box<[T]>`/`Rc<[T]>`-like owned unsized handles where their owners and unsizing protocols can maintain correct allocation and destruction metadata.

### 12. Function boundaries, abstraction and separate checking

Access dependencies are not local implementation hints. Signatures and generic instantiation must preserve the relationships on returned references and custom views.

A function accepting a borrowed `&T` cannot return a reference with an unrelated longer lifetime; a function moving an `ArenaBox<T, @s>` retains `depends valid(@s)` on the returned value. A generic function can discard an input's dependency by **destroying or consuming** the relevant value, but cannot silently erase it from a still-live returned alias.

The checker must model returned origins, including branches where a reference may originate from several different places, and partial loans through aggregates across function boundaries. This RFC specifies the requirement but does not fix final origin-set syntax or a complete interprocedural effect calculus; that work overlaps RFC-0067, RFC-0122 and RFC-0159.

Whole-domain revocation effects must be visible in separately compiled public interfaces. The compiler may infer effects for private functions, but a public `revokes @s` contract cannot be suppressed by implementation opacity. Type/ABI erasure must preserve the actual validity obligations even when the concrete custodian type is abstracted.

---

## Formal safety obligations and acceptance criteria

A future Metel-Core formalization must at minimum model:

1. **Ownership conservation:** initialization, move, partial move, destruction, and capability transfer cannot create duplicate unique value ownership.
2. **Loan compatibility:** overlapping active places obey shared/exclusive access constraints; splitting proves disjointness, and parent authority is restricted during reborrow.
3. **Dependency preservation:** any live resource with `depends valid(@s)` blocks incompatible revocation of `@s`, including across generic functions, aggregates and opaque types.
4. **Invalidation authority:** an effect annotation does not mint revocation permission; only an authorized operation can invalidate a domain, and no safe implementation can hide the effect.
5. **Target binding:** liveness, location, and access evidence always concern the same logical object and the correct subplace; arbitrary `RawPtr<T>` combinations cannot forge references.
6. **Initialization discipline:** references to dynamically allocated or partially initialized regions expose only initialized places; destruction handles the initialized prefix/fields correctly.
7. **Dynamic custody preservation:** `Rc` strong owners, GC roots/pins and similar trusted resources maintain their promised invariants for the lifetime of any supporting borrows or owned leases.
8. **Relocation safety:** live direct references remain stable or are restricted from crossing relevant GC safepoints; a mere reachability root is insufficient.
9. **Unwinding/destruction:** scope exits, panics, cancellation, `Drop`, and partial drops respect access, dependency, and cleanup order.
10. **Representation independence:** pointer arithmetic, tagged handles, indices and alternative GC representations cannot circumvent the abstract target/authority relation.

Suggested initial adversarial tests:

| Test | Expected behavior |
|---|---|
| Mutable borrows of two independent arena boxes | Accept |
| Allocate into stable arena while those boxes exist | Accept |
| Revoke/reset arena storage with live boxes | Reject |
| Call revoking method inside `alloc` despite outstanding dependencies | Reject or make the method unavailable under its authority contract |
| Two mutable borrows through two copies of one key | Reject unless mediated by a checked disjointness/access protocol |
| `Rc.share()` followed by unchecked unique mutable reference | Reject |
| Branded mutable borrow while its token is already exclusively borrowed | Reject |
| Return borrowed `Rc` reference after local owner dies | Reject |
| Return owned `Rc` wrapper that can derive its own borrow | Accept |
| Move a guard while a reference borrows from it | Reject conflicting move |
| GC collect while target pinned and rooted | Allow only if collector preserves both guarantees |
| GC relocate target behind live direct unpinned pointer | Reject or runtime contract violation |
| Return `&[T]` borrowed from a function-local `[T; N]` | Reject |
| `List.push` while an overlapping shared slice remains live | Reject under base API |
| Split an exclusive slice into checked disjoint ranges | Accept |
| Reuse an allocation address with a stale key | Reject access via key-generation check or type-level invalidation |

The safety theorem aimed at by RFC-0241 is preservation of a well-formed machine state's object-validity and access invariants across all safe evaluation steps, conditional on explicitly stated trusted-library invariants.

---

## Interaction with existing RFCs

The following table is **normative as a compatibility intention of this draft, not as an amendment to those RFCs**. Existing accepted/implemented behavior remains in force until separate review, integration and migration change it.

| RFC | Current relationship | Required reconciliation if this proposal is accepted |
|---|---|---|
| **RFC-0241 — Metel-Core** (draft) | Formal foundation | Extend its calculus with value ownership, custody, target-bound access witnesses, stable-location guarantees, static domain dependency/revocation, and trusted runtime transitions. RFC-0241 owns the formalization; this RFC owns proposed surface semantics. |
| **RFC-0242 — prior draft** | Direct replacement | Retain its goals of library-defined references and structural access, replacing the `&T@a`-as-origin suggestion with the four-part ownership/custody/stability/access model. Keep the RFC ID. |
| **RFC-0071 — Ownership and Move Semantics** (integrated) | Extends | Preserve affine moves, partial moves, and `Copy`/`Drop` discipline. Add logical object/capability ownership and the rules tying destruction to outstanding accesses and storage dependencies. |
| **RFC-0089 — Linear Types** (accepted) | Complements | Some reclamation/rejoin protocols may require mandatory consumption. Do not assume affine drop/discard implies exactly-once release; explicitly account for linear resources and the possibility of leaks without unsafe dangling access. |
| **RFC-0067A — Reference Types** (implemented) | Preserves core syntax | Retain `&T`, `&var T`, expression borrowing, and existing receiver conventions; reinterpret their semantics as producing compiler-checked access witnesses, with unsized pointees supported. |
| **RFC-0044 — Explicit Receiver Semantics** (implemented) | Compatible | Continue using `self`, `&self`, `&var self` rather than Rust-style `self: &Self`. Custom reference abstractions may require additional trusted dereference/access establishment without changing ordinary method receiver syntax. |
| **RFC-0122 — Borrow Checking** (under review) | Generalizes | Keep shared-XOR-exclusive, place-based borrowing, reborrowing, partial loans and NLL. Extend the checker to treat library-defined witnesses and custody dependencies as first-class and to check revocation effects. |
| **RFC-0067 — Lifetime Anchors** (under review) | Revises/clarifies | Keep explicit `&r T` / `&r var T` as candidate lifetime notation, with abstract borrow regions and origins. Distinguish a borrow duration from `@s` storage validity and from a runtime custodian. Signature/origin inference must be reconciled with library-defined access. |
| **RFC-0159 — Abstract Regions and a Dedicated Identity Channel** (under review) | Aligns semantically; syntax change | Share region-index machinery but preserve distinct roles for borrowed durations, brands and storage. This RFC uses `<@s>` and `<'b>` in generic positions rather than RFC-0159's deferred separate identity channel; final grammar must reconcile them. |
| **RFC-0076 — Brand Types** (under review) | Narrows identity claims | Keep `'b`, rigid generativity and token-gated access. Clarify that a brand may name one access domain containing multiple allocations and **does not by itself prove per-allocation disjointness**. Require sound, unforgeable token creation and token-protected interior access. |
| **RFC-0063 — Allocator Handles** (accepted) and **RFC-0077 — Allocator Generics** (accepted) | Revises foundation | Preserve allocator parametrization where useful. Require a specified raw/dynamic buffer and initialized-allocation substrate, rather than treating single-value placement as sufficient for a Metel-defined `List<T>`. Do not force all allocator handles to be unique pointer-shaped values. |
| **RFC-0143 — Allocator Placement, Storage Identity, and Allocator-Selected Handles** (under review) | Significant overlap; explicit distinction | Preserve `T@a` as *allocator placement/selected handle*, not as `&T` validity-origin syntax. Use `@s` for storage identity and `depends valid(@s)` for the validity obligation. Reconcile the `@` grammar and define how allocator-selected handles carry suitable custody and access guarantees. |
| **RFC-0139 — Garbage-Collected Allocators and Allocator-Determined Pointer Types** (under review) | Supplies common correctness model | Retain the possibility of copyable GC handles and allocator-selected pointer families. Add explicit requirements for complete root discovery, stable direct access/pinning, cross-heap edges, affine contents, finalization and concurrency. This RFC does not resolve those RFC-0139 blockers. |
| **RFC-0158 — Share and Clone** (under review) | Compatible | `Share` retains shared ownership/aliasing, never duplicates exclusive authority. Use `.share()` for `Rc` examples; keep independent-value `Clone` distinct. |
| **RFC-0053 — Fixed-Size Arrays** (implemented) | Preserves owned arrays | Retain `[T; N]` and array-literal inference. Replace bare `[T; N]` -> `[T]` view coercion with a borrow-aware unsizing from `&[T; N]` to `&[T]` (and exclusive counterpart). |
| **RFC-0054 — Standard `List<T>`** (implemented) | Preserves container role; revises view API | Keep `List<T>` as the growable owner and explicit `.as_slice()`. Change the result from bare `[T]` to `&[T]`; add optional `as_mut_slice()` -> `&var [T]`. Its owned-buffer implementation remains library-oriented. |
| **RFC-0126 — `T[]` as a Copy Borrowed View** (implemented) | **Directly revises an implemented decision** | Replace the **sized bare `Copy` view** with an **unsized `[T]` payload**. The shared borrowed view becomes `&[T]` and remains `Copy`; `&var [T]` is exclusive and non-`Copy`. This requires a deliberate compatibility migration, not a silent elaboration. |
| **RFC-0171 — Prefix Array Type Syntax** (implemented) | Preserves spelling; changes meaning | Preserve `[T]` and `[T; N]` lexical forms. Change the kind/legality of bare `[T]`: it is no longer a standalone field, local, parameter, or returned view value. |
| **RFC-0124 — Sequence Types** (under review) | Resolves two open directions | Choose the Rust-style `&[T]` / `&var [T]` surface, rather than an implicit bare `[T]` lifetime; make lifetime checking part of the common borrowing mechanism. The remaining sequencing/representation questions stay separately tracked. |
| **RFC-0172 — Sized and Unsized Kinds / generalized unsizing** (draft) | Adopts a narrow initial slice | Initially recognize `[T]` as a compiler-known unsized payload and implement wrapper-aware, direction-sensitive unsizing. General user-defined dynamic layouts and arbitrary unsized payload constructors remain deferred; adjust any conflicting assumptions about bare coercion. |
| **RFC-0133 — From-Metel `List` / runtime buffer gap** (draft) | Exposes an outstanding prerequisite | Introduce or commission a runtime-sized allocation/initialization substrate for `OwnedBuffer<T>`; `&[T]` and `[T; N]` alone do not provide an owning growable buffer. |
| **RFC-0132 — Comptime Execution Model** (under review) | Orthogonal | Its `comptime N: u64` generic length mechanism remains useful for `[T; N]`; runtime-sized `[T]` does not turn fixed arrays into runtime-variable inline arrays. |

**Migration note.** RFC-0126 and RFC-0171 are implemented. Their proposed semantic revision is intentionally breaking: code with a bare `[T]` local/parameter/field/return type must be reviewed for `&[T]`, `&var [T]`, or an owned collection type. The current evaluator's reference-counted representation cannot substitute indefinitely for the new compile-time borrowing and escape checks. The RFC does not claim these migrations are already implemented.

---

## Alternatives considered

**Only compiler-defined references.** Lower trusted implementation complexity but fails the generalized library-access goal, especially for arenas, branded cells, and custom views.

**Single universal `Custodian<T>` or `ValidityProvider<T>` aspect.** Not every custodian grants the same ownership or duplication rights, and a Boolean `is_valid()` cannot guarantee validity *throughout* a borrow. Allowing safe libraries to assert proof facts would be unsound.

**Storage validity as ordinary shared borrowing of the arena.** Simpler, but often unnecessarily prohibits allocating new objects or independently mutating disjoint allocations while handles remain live.

**Brands as exact dynamic allocation identities.** Cannot safely infer nonaliasing for two runtime handles solely because they share or differ in a coarse domain brand; dynamic allocations require actual minting and conservation of per-target authority or checked runtime disjointness.

**Owning lease for every reference.** Overly heavy: borrowed references should normally derive access from an external custodian. Retaining an owning guard is useful when explicitly requested, but not the default.

**Only runtime borrow checking.** Useful for some APIs, but forces runtime overhead/failure cases where static access authority can prove exclusivity.

**Keep bare `[T]` as an implicitly borrowed sized view.** Avoids a migration, but prevents a clean separation of unsized payload and different owner/reference wrappers. The proposed `&[T]` / `&var [T]` split is clearer and matches general access semantics.

**Entirely library-defined `[T]` through a layout DSL or `LayoutOf<T>` aspect.** Attractive longer-term but expands this RFC beyond ownership and access. The initial compiler-known dynamic slice layout is the deliberate boundary.

---

## Risks and implementation dependencies

- **Type-checker breadth:** access witnesses, origin sets, validity-domain ownership, effect checking, partial borrows, and opaque types touch inference, construction, move checking, borrowing, and destruction.
- **Unsound trusted APIs:** a poorly designed target-binding intrinsic could bypass the entire memory-safety model. Keep intrinsics sealed and state preconditions precisely.
- **GC runtime integration:** a collector cannot be safely implemented solely by declaring a `GcRoot` type if roots, barriers, relocation and safepoints are not guaranteed by the runtime/compiler integration.
- **Destructor and affine/linear semantics:** a live handle with a necessary destructor may continue to require storage after its final ordinary read. Interactions with arbitrary `forget`, unwinding, and linear resources need explicit operational rules.
- **Static arena expressiveness:** `depends valid(@s)` must protect actual allocations without pessimistically borrowing all allocator metadata; its root/epoch/revoker protocol requires proof, not merely syntax.
- **Public API effects:** propagation through generic functions, opaque modules and separate compilation must avoid loss of dependency or hidden revocation.
- **Breaking collection migration:** changing `[T]` from a sized `Copy` view to an unsized payload is a deliberate revision of implemented semantics and needs diagnostics and a migration strategy.
- **ABI and zero-cost erasure:** witness and custodian information may be compile-time-only, runtime-backed, or both. The language must not promise zero overhead where a chosen runtime protocol needs refcounts, roots or pins.

---

## Open questions

The draft settles the architectural **direction** but not the following implementation-sensitive choices:

1. **Canonical primitive API:** which acquisition, project, split, establish and revoke operations are compiler intrinsics, which can be safe library code over lower primitives, and which require a declared unsafe implementation boundary?
2. **Domain introduction:** what exact source syntax introduces a fresh storage identity `@s`, and how are its owner and revocation rights tied to that identity without forging or accidental escape?
3. **Effect calculation:** should `revokes @s` be a declared effect, a requirement to consume an exclusive revocation capability, or both? What is the minimum complete function-boundary effect system?
4. **Fine-grained invalidation:** how are epoch transitions, slot reuse, key generations, and partial-range reclamation represented alongside whole-domain `revokes @s`?
5. **Origins across functions:** what signature language expresses a result derived from one of several input places and partial loans when a higher-level API needs more than elided `&r` parameters?
6. **Owned reference capsules:** do we need a general compiler primitive for internally self-dependent custody, or should safe on-demand reference derivation remain the baseline?
7. **Brand generativity:** what exact brand-introduction form is adopted, and how do inferred/new brands interact with existential packaging and domain-wide tokens? No `brand` keyword appears in generic positions.
8. **Unsized kind/metadata:** what minimal `Sized`/unsized kind and `Unsize` machinery is needed for `[T]` and pointer-wrapper coercions, without importing a general composable dynamic-layout facility?
9. **Allocator interface:** what checked raw buffer/initialized-prefix API allows `List<T>` and arenas to be implemented in Metel, and how does `T@a` choose a custodian/handle family?
10. **GC contracts:** which compiler/runtime interfaces must tracing, rooting, moving collection and finalizers use, and which are separate blockers of RFC-0139?
11. **Concurrency:** how do `Send`/`Sync`, atomic refcounts, GC pinning, and token authority interact with data-race freedom? This RFC is initially single-threaded in its core examples.
12. **Migration:** how should bare `[T]` uses be rewritten or diagnosed, particularly in structurally generic code, arrays of views and public APIs?

These are explicit **review gates**, not permission for safe implementations to choose unsound defaults. Acceptance should require at least a small Metel-Core model validating ordinary borrows, arena invalidation, trusted reference construction, and one runtime-backed custodian protocol.

---

## Proposed next steps

1. Develop a minimal formal core of ownership, initialized places, access witnesses, storage domains, and revocation under RFC-0241.
2. Prove or model-check the two central counterexamples: contradictory exclusive access through aliasing handles, and arena destruction/reset while an external owned allocation survives.
3. Specify the safe and trusted operation boundary with at least one realistic arena implementation sketch and one reference-counted implementation sketch.
4. Reconcile the storage/brand/borrow index grammar with RFC-0159 and allocator placement with RFC-0143, keeping `@s` and `'b` as this draft's working spelling.
5. Specify the `[T]` migration and narrow `Unsize` rules as a coordinated revision of RFC-0124, RFC-0126, RFC-0171 and RFC-0172.
6. Keep dynamic-layout composability, a fully specified GC backend, and broad self-dependent custody abstractions as subsequent design work.

---

## References

- [RFC-0241 — Metel-Core](rfc-0241-metel-core-a-formal-semantic-foundation-for-metel.md)
- [RFC-0071 — Ownership and Move Semantics](../3-integrated/rfc-0071-ownership-and-move-semantics.md)
- [RFC-0089 — Linear Types](../2-accepted/rfc-0089-linear-types.md)
- [RFC-0067A — Reference Types](../4-implemented/rfc-0067a-reference-types.md)
- [RFC-0044 — Explicit Receiver Semantics](../4-implemented/rfc-0044-explicit-receiver-semantics.md)
- [RFC-0122 — Borrow Checking](../1-under-review/rfc-0122-borrow-checking.md)
- [RFC-0067 — Lifetime Anchors](../1-under-review/rfc-0067-lifetime-anchors.md)
- [RFC-0159 — Abstract Regions](../1-under-review/rfc-0159-abstract-regions-and-a-dedicated-identity-channel.md)
- [RFC-0076 — Brand Types](../1-under-review/rfc-0076-rc-brands.md)
- [RFC-0063 — Allocator Handles](../2-accepted/rfc-0063-allocator-handles.md)
- [RFC-0077 — Allocator Generics](../2-accepted/rfc-0077-allocator-generics.md)
- [RFC-0143 — Allocator Placement and Storage Identity](../1-under-review/rfc-0143-allocator-placement-storage-identity-and-allocator-selected-handles.md)
- [RFC-0139 — GC Allocators](../1-under-review/rfc-0139-garbage-collected-allocators-and-allocator-determined-pointer-types.md)
- [RFC-0158 — Share and Clone](../1-under-review/rfc-0158-share-and-clone-separating-aliasing-from-duplication.md)
- [RFC-0053 — Fixed-Size Arrays](../4-implemented/rfc-0053-fixed-size-arrays.md)
- [RFC-0054 — List](../4-implemented/rfc-0054-list-type.md)
- [RFC-0126 — Borrowed Array Views](../4-implemented/rfc-0126-t-as-a-copy-borrowed-view.md)
- [RFC-0171 — Prefix Array Types](../4-implemented/rfc-0171-prefix-array-type-syntax-t-and-t-n.md)
- [RFC-0124 — Sequence Types](../1-under-review/rfc-0124-sequence-types-fixed-arrays-slices-and-the-growable-list.md)
- [RFC-0172 — Sized/Unsized Kinds](rfc-0172-sized-and-unsized-kinds-and-a-generalized-unsizing-coercion.md)
- [RFC-0133 — From-Metel `List` Buffer Gap](rfc-0133-from-metel-list-the-runtime-sized-buffer-gap.md)
- [RFC-0132 — Comptime Execution](../1-under-review/rfc-0132-comptime-execution-model-comptime-let-comptime-fun-comptime-if.md)

## Decision

**Outcome:** *(pending)*

**Implementation:** *Not started. No acceptance, integration or supersession of other RFCs is implied by this draft.*
