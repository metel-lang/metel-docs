---
id: rfc-0143
title: "Allocator Placement, Storage Identity, and Allocator-Selected Handles"
date: '2026-08-26'
status: draft
target:
---

> **Deliberate overlap, 2026-08-26.** This RFC was opened after checking the curated
> allocator cluster, the exact registry, and the RFC corpus directly. It is a proposed
> consolidation of accepted RFCs that are intentionally not implemented, not an
> undiscovered competing design. None of them changes status while this RFC is a draft.
>
> **Working syntax premise.** RFC-0093 and RFC-0095 currently spell metadata with `#`;
> they originally used `@` and changed because the accepted allocator cluster already
> claimed it. This RFC assumes that removing `@` from allocation permits those RFCs to
> restore it. It does not amend them by itself; their matching update must occur before
> this RFC can leave draft.

## Summary

Replaces the accepted-but-deliberately-unimplemented allocator cluster with one
coherent proposal written against the language that exists now. It preserves the
cluster's central result: a concrete allocator *instance*, not merely its type, has a
static identity that can appear in types and prove scope, disjointness, and
sendability properties. It no longer assumes that every allocator produces one
affine owning-pointer shape, and it no longer uses `@`, under the working premise that
the comptime/metadata proposal will restore that spelling.

The proposed explicit surface is:

```metel
fun build<T, A: Alloc>(alloc arena: A, value: T) -> at arena T {
    place arena value
}

fun preserve<storage s, T>(value: at s T) -> at s T {
    value
}
```

`alloc arena: A` binds an ordinary runtime allocator value and its static storage
identity together. `place arena expr` asks that allocator to place a value. `at arena
T` is the allocator-selected handle type produced by that operation; it is a type
projection, not a promise that the result is affine, uniquely owned, pointer-shaped,
or movable-out. `<storage s>` is the compile-time-only preservation form: it can name
an already-established placement but grants no capability to allocate.

For `Heap`, `LocalHeap`, `BumpAlloc`, and `AutoAlloc`, `at a T` has the accepted
cluster's unique affine semantics. A tracing allocator may instead select a copyable
`Gc` handle, and another allocator may select another family, without changing the
placement expression. Handle capabilities, rather than the fact of allocation alone,
determine borrowing, extraction, drop, copying, and sendability.

If this RFC is accepted, it supersedes RFC-0063, RFC-0065's allocator-specific
sections, RFC-0066, RFC-0068, RFC-0073, RFC-0077, and RFC-0141. Those RFCs remain
accepted and unchanged while this document is a draft. RFC-0065's lifetime-anchor
rules remain owned by RFC-0067 and are not superseded here.

---

## Motivation

The accepted allocator cluster is factually frozen. It was accepted as Phase 3 work,
has no grammar or allocator backend implementation, and was deliberately scheduled
after ownership, borrowing, brands, and the rest of the language substrate. That was
the right implementation order, but it means the design was written against a much
earlier Metel than the one that will eventually implement it.

The delay has surfaced four changes that cannot be handled as a mechanical sigil
rename.

First, RFC-0095 and RFC-0093 originally gave `@` a strong metadata/comptime role and
changed it to `#` specifically because the allocator cluster already occupied `@`.
The allocator cluster uses it in types, expressions, parameter declarations, generic
declarations, closure parameters, call arguments, and elided forms. The grammars can
be disambiguated, but two unrelated sublanguages would compete for the language's
most visually prominent marker. Removing it here dissolves the stated reason for that
change; a companion revision may restore metadata/comptime `@` without ambiguity over
which cluster moved first.

Second, RFC-0076's brand work and RFC-0137's branded-row model make static identity a
general language concern. An allocator instance still needs an identity, but it no
longer follows that allocator identity needs a wholly separate theory or that a
pointer sigil must introduce it.

Third, RFC-0139 exposes a semantic assumption in `@a T`: the accepted cluster makes
every allocation produce the same affine owned handle, while a tracing allocator
exists precisely to produce freely copyable, runtime-traced references. Treating GC
as an allocator is useful only if the allocator may select its result family.

Fourth, RFC-0133 checks the cluster against implementing `List<T>` in Metel and finds
that `Alloc` has no specified method contract and no runtime-sized buffer operation.
The cluster specifies single-value surface placement while leaving the substrate that
would implement it undefined. A consolidated replacement must name that gap rather
than accepting another surface above it.

The goal is therefore not to preserve `@a T` under a different glyph. It is to
preserve the old design's useful guarantees while separating four concepts it wrote
as one:

1. an allocator is a runtime capability;
2. a particular allocator binding has a static storage identity;
3. placement asks that capability to store a value;
4. the allocator chooses the handle family returned by placement.

---

## 1. Scope and supersession

This RFC is deliberately overlapping. The overlap check performed when it was opened
found RFC-0068, RFC-0077, RFC-0073, RFC-0141, and RFC-0076; the curated allocator
cluster additionally identifies RFC-0063, RFC-0065, RFC-0066, RFC-0133, and RFC-0139.
They are the inputs to this document, not accidental duplicates.

### 1.1 Normative disposition of the accepted cluster

| Existing rule | Disposition here |
|---|---|
| Allocators are ordinary runtime values implementing `Alloc` | Preserved (§3) |
| Each allocator instance has a distinct static identity | Preserved (§2) |
| `@a T` is one universal affine owning-pointer type | Replaced by allocator-selected `at a T` (§4) |
| `@a expr` selects explicit placement | Replaced by `place a expr` (§5) |
| `(@a: A)` binds capability and tag together | Replaced by `alloc a: A` (§2.2) |
| `<@a>` relays a tag without a runtime handle | Replaced by `<storage a>` (§2.3) |
| Allocator names may be elided only when resolution is unique | Preserved (§8) |
| Allocator arguments may be omitted at uniquely resolved calls | Delegated to general context parameters (§8.4) |
| Borrowing through an allocated handle is transparent | Preserved for handles providing borrow access (§6) |
| Heap move-out works for every `T` | Preserved for `Heap`'s unique handle (§7.2) |
| Bulk arenas restrict move-out of `T: Drop` | Preserved (§7.3) |
| Plain-parameter calls never trigger hidden extraction | Preserved (§7.5) |
| Type-directed placement/extraction occurs at bindings only | Preserved (§5.3, §7.4) |
| Structs may own an allocator | Preserved with new spelling (§9) |
| A struct initially owns at most one allocator | Reopened; model permits more, initial grammar remains OQ4 (§9.3, §15.2) |
| `AutoAlloc` may choose an unobservable strategy | Preserved and narrowed to compatible handle semantics (§10) |
| Generic well-formedness is checked from storage scopes | Preserved (§11) |
| Allocated unique handles are covariant in storage scope and `T` | Preserved; no longer generalized to every handle family (§11.3) |
| Owned `dyn Aspect` values may select an allocator explicitly | Preserved (§12) |

### 1.2 Dependencies retained rather than absorbed

- RFC-0067a owns `&T`/`&var T`, address-of, and base auto-deref.
- RFC-0067 owns named lifetime anchors and their elision.
- RFC-0071 owns affine moves and drop order.
- RFC-0072 owns negative bounds such as `T: !Drop`.
- RFC-0076 owns general generative brands. This RFC requires allocator storage
  identities to obey the same rigidity and non-forgeability rules, but does not settle
  the surface syntax of unrelated brands.
- RFC-0080 owns `Clone`, `Deref`, `Send`, and `Sync` as general aspects.
- RFC-0082 owns ordinary associated types. Generic associated handle families are an
  extension identified here, not retroactively attributed to RFC-0082.
- RFC-0113 owns general context-parameter declaration, provision, and resolution.
- RFC-0122 owns the borrow checker that enforces exclusivity and outlives constraints.

### 1.3 Adjacent drafts

RFC-0139 remains the GC-specific design: collection timing, root discovery,
finalization, and cyclic structures. This RFC absorbs only its finding that allocators
must select handle families. RFC-0133 remains the question of whether `List<T>` should
be implementable in Metel; §3.3 supplies the missing buffer-capable allocator contract
that RFC-0133 identified, but does not decide the rest of `List`'s prerequisites.

---

## 2. Storage identities

### 2.1 Identity belongs to the binding, not only the allocator type

Every binding established as an allocator capability has a rigid static storage
identity. Two different `BumpAlloc` instances therefore remain distinct:

```metel
let a = BumpAlloc::new();
let b = BumpAlloc::new();

let x: at a Node = place a Node { value = 1 };
let y: at b Node = place b Node { value = 2 };
```

`at a Node` and `at b Node` are not equal merely because both allocators have type
`BumpAlloc`. The identities are generative, cannot be forged from text, and cannot be
compared or converted at runtime. They are erased when no selected handle
representation needs them at runtime.

Static allocators such as `Heap` and `LocalHeap` have stable global identities named
by those bindings. They do not create fresh identities at each use.

### 2.2 Capability binders: `alloc a: A`

In a parameter list, the contextual modifier `alloc` states that the binding is both
an ordinary value and the source of a storage identity:

```metel
fun build<T, A: Alloc>(alloc a: A, value: T) -> at a T {
    place a value
}
```

Within the body, `a` may be used as an ordinary value and through `Alloc` methods. In
`at a T`, the same spelling denotes its static identity. The caller passes an ordinary
allocator value; the callee's identity is substituted with the identity of that
argument, rather than freshly generated on every call.

Local construction infers the modifier when the initializer's static type implements
`Alloc`, though writing it remains legal:

```metel
let arena = BumpAlloc::new();
let explicit = place arena Node { value = 1 };
```

An ordinary parameter `a: A` where `A: Alloc` does not implicitly become usable in
type position. Public signatures must write `alloc a: A`; this keeps the dependent
part of the signature visible and prevents adding an `Alloc` impl from silently
changing an existing function's type.

### 2.3 Identity without capability: `<storage s>`

Code that only preserves a placement does not need the runtime allocator:

```metel
fun identity<storage s, T>(value: at s T) -> at s T {
    value
}
```

`storage s` is a compile-time-only identity parameter. It occupies no runtime
argument slot, has no `Alloc` bound, and permits `s` only in type relationships. The
body may not evaluate `place s expr`, call allocation methods through `s`, collect an
arena, or otherwise exercise an allocator capability.

This is categorically different from `alloc a: A`: the latter carries both capability
and identity; the former carries identity only. It preserves RFC-0063's tag-only
parameter without tying it to punctuation or pretending a runtime value exists.

---

## 3. The allocator interfaces

### 3.1 Safe placement interface

The surface contract is conceptually:

```metel
aspect Alloc {
    type AllocationError;
    type Handle<T>;
}
```

`Handle<T>` is a generic associated type. It describes the ownership and runtime
representation family selected by an allocator kind. The compiler additionally
indexes each produced handle by the identity of the allocator binding used at the
placement site; `at a T` is the surface projection of that complete type.

`AllocationError = !` declares placement infallible. The compiler collapses
`Result<at a T, !>` to `at a T`, preserving RFC-0063's rule.

`place a expr` is a language operation governed by `Alloc`, not specified as a simple
method desugaring. A method-only desugaring cannot express the binding identity in the
result without adding general value-dependent associated-type projection. An
implementation may lower it to a compiler-known `Alloc` entry point, but that is not
observable source semantics.

### 3.2 Handle capabilities

An `Alloc` implementation must define, for each `T`, which operations its handle
family supports. The language does not infer the following merely from `A: Alloc`:

- shared access to `T`;
- exclusive access to `T`;
- affine ownership;
- copying or cloning the handle;
- moving `T` out of the placement;
- individually releasing the placement;
- tracing or collecting it;
- `Send` and `Sync`.

The standard unique families support shared and exclusive borrowing, transparent
field/method access, affine move tracking, and allocator-dependent extraction. `Gc`
handles support shared access and copying but do not become affine merely because they
came from `place`. Generic code requiring an operation must state the corresponding
handle/aspect bound or operate only parametrically on `at s T`.

For the standard unique families, `at a T: Send` exactly when the selected handle is
sendable, the allocator identity may cross the boundary, and `T: Send`. `Heap` meets
the allocator condition; `LocalHeap`, `BumpAlloc`, and `AutoAlloc` do not. A custom
family's `Send`/`Sync` rules are structural aspect rules, not a second annotation on
the placement expression.

### 3.3 Raw storage and runtime-sized buffers

The accepted cluster leaves `Alloc.alloc` unspecified and consequently cannot support
a from-Metel growable buffer. This RFC requires the allocator substrate to provide
four semantic operations, whether their eventual unsafe surface is an aspect or a
compiler intrinsic:

1. allocate an uninitialized block for a checked size and alignment;
2. grow or relocate an existing block while preserving a stated initialized prefix;
3. shrink a block while preserving a stated initialized prefix;
4. release a block previously produced by that allocator.

The operations return `AllocationError`, never manufacture initialized `T` values,
and require proof that layout, provenance, initialized ranges, and destruction
obligations are respected. `place a expr` is the safe, initialized single-value layer
built above them.

The exact user-authorable spelling of these raw operations depends on RFC-0026's
unsafe primitive layer. That dependency blocks custom allocator implementation, not
the static meaning of `at`/`place` or use of compiler-provided standard allocators.
Unlike RFC-0063, this document nevertheless specifies the required capability now, so
RFC-0133 has a concrete allocator contract to depend on rather than an unnamed gap.

---

## 4. Placement types: `at a T`

`at a T` is the type produced by placing a `T` in allocator `a`. It combines:

- `a`'s rigid storage identity;
- the allocator kind's `Handle<T>` family;
- any static scope, sendability, and extraction properties that family declares.

It is not a universal runtime wrapper. The compiler normalizes it after the allocator
kind is known:

```text
at Heap T       -> unique heap handle carrying Heap identity
at arena T      -> unique arena handle carrying arena identity
at global_gc T  -> copyable traced handle carrying GlobalGc identity
```

The source projection remains useful in generic signatures because it says exactly
what callers need: preserve the placement selected by this identity, without exposing
or hard-coding its representation.

### 4.1 Same type, different instances

`at a T` and `at b T` are distinct when `a` and `b` are distinct storage identities.
For storage families that prohibit cross-arena references, this is a static
disjointness witness. A manual `a.collect()` may therefore collect only `a`'s traced
arena without scanning `b`, subject to RFC-0139's root and inter-arena-edge rules.

### 4.2 Identity permanence

The storage identity remains part of the static type for as long as the handle is
live. It is not silently erased on field storage, argument passing, or return. Explicit
extraction or an allocator-family-specific erasure operation is required to remove it.

### 4.3 Syntax category

`at` is contextual in this proposal. It starts a placement type only where a type may
begin and when followed by a storage identity and another type. It does not reserve
ordinary identifiers containing `at`, conflict with metadata `@name`, or consume the
array, generic, or lifetime-anchor channels.

---

## 5. Placement expressions: `place a expr`

`place a expr` evaluates `expr` first, then asks `a` to place the resulting initialized
value. For `expr: T`, its type is:

```text
Result<at a T, A::AllocationError>
```

with the `!` collapse from §3.1. If evaluation of `expr` fails or transfers control,
no placement occurs. If allocation fails after `expr` has been evaluated, the value is
dropped normally before the error is returned.

```metel
let node = place arena Node { value = 1, next = None };
let fallible = place pool Node { value = 2 }?;
```

### 5.1 Explicit allocator choice

`Heap` and `LocalHeap` are always nameable:

```metel
let durable: at Heap Node = place Heap Node { value = 1 };
```

They enter an elision candidate set only when explicitly provided as a capability in
the current context. Merely being globally nameable does not cause a scoped `place`
to choose the heap silently.

### 5.2 Multiple allocators

Multiple allocator parameters remain ordinary ordered parameters:

```metel
fun transfer<T, A: Alloc, B: Alloc>(
    alloc src: A,
    alloc dst: B,
    value: at src T,
) -> at dst T {
    place dst (value: T)
}
```

The destination must be explicit when more than one compatible allocator is in scope.

### 5.3 Type-directed placement

At a `let` binding only, an expected placement type may supply the operation:

```metel
let node: at arena Node = Node { value = 1 };
```

This is equivalent to `let node = place arena Node { value = 1 };`. Nested expressions
and ordinary function arguments never allocate merely because an expected type is
`at a T`; they require `place` or an explicit binding. This preserves the old
cluster's storage-transparency boundary.

---

## 6. Borrowing and transparent access

For a handle family providing shared access, `&handle` borrows its `T`. For one
providing exclusive access, `&var handle` obtains an exclusive borrow subject to
RFC-0122. Neither consumes the handle:

```metel
let ptr = place arena Node { value = 1 };
let read: &Node = &ptr;
let write: &var Node = &var ptr;
```

Auto-deref for field access and method dispatch follows RFC-0067a and applies only
when the selected handle family exposes the corresponding dereference operation. This
is unconditional for the standard unique families, but not a promise made by the bare
bound `A: Alloc`.

A borrow may never outlive either the handle value or the storage identity on which
that handle depends. Named cross-function cases use RFC-0067 lifetime anchors; this
RFC does not create a second lifetime notation.

---

## 7. Extraction and destruction

Extraction applies to the standard unique handle family. Other families define their
own operations; in particular, copying a `Gc` handle is not extraction of its pointee.

### 7.1 Copy extraction

When `T: Copy`, ascription copies the pointee and leaves the handle and placement live:

```metel
let point = ptr: Point;
```

### 7.2 Individually released placement

`Heap` and any allocator whose unique family tracks individual live allocations permit
move-out for every `T`. Moving consumes the handle, transfers `T` to ordinary
storage-independent ownership, and releases the slot without invoking `T::drop` there.
The moved value is dropped normally at its new owner.

### 7.3 Bulk-deallocated placement

A bulk allocator that cannot mark an individual slot vacant permits move-out only
when `T: !Drop`. Raw memory may remain unused until the arena is reclaimed, but no
destructor is skipped or invoked twice. For `T: Drop`, move-out is a compile error.

An allocator may opt into per-allocation destructor tracking and thereby support
move-out for `T: Drop`, at the cost of bookkeeping. Caller-driven manual destruction
does not make move-out safe and is not part of the safe surface.

### 7.4 Explicit and binding-directed extraction

The two forms are:

```metel
let node = ptr: Node;
let node: Node = ptr;
```

Both obey the selected handle family's extraction capability and the rules above.

### 7.5 No hidden extraction across calls

Given `consume(value: Node)`, `consume(ptr)` is a type error when `ptr: at a Node`.
The caller must write `consume(ptr: Node)` or bind an extracted `Node` first. A
function that only relays placement instead writes:

```metel
fun consume<storage s>(value: at s Node) -> at s Node { value }
```

This keeps callability from depending invisibly on the caller's allocator and drop
strategy.

### 7.6 Clone into another allocator

When `T: Clone`, code may clone through a borrowed pointee and place the result in a
chosen destination:

```metel
let copy: at Heap Config = place Heap src.clone();
```

The source remains live. A future convenience such as `clone_into` is a standard
library API question and is not required by this RFC.

---

## 8. Elision and context resolution

All elision obeys one invariant: it is legal only when type-directed filtering leaves
one correct answer. Ambiguity is a compile error; lexical depth never silently chooses
an allocator.

### 8.1 Placement-name elision

When exactly one compatible allocator capability is in scope:

```metel
fun build(alloc arena: BumpAlloc, value: Node) -> at Node {
    place value
}
```

The return type means `at arena Node`; the body means `place arena value`.
Type-directed filtering first uses any concrete required allocator type. If the
position is generic over `A: Alloc`, every compatible allocator remains a candidate.

### 8.2 Ambiguity and nesting

An outer `Heap` capability and an inner `BumpAlloc` are both candidates for a bare
placement expression with no concrete expected allocator kind. The compiler does not
choose the inner binding by depth:

```metel
fun process(alloc heap: Heap) {
    BumpAlloc::scoped((alloc arena) -> {
        let x = place arena Node { value = 1 }; // name required
    });
}
```

Introducing a nested allocator therefore cannot silently retarget existing placement.

### 8.3 Storage-only elision

When no runtime allocator capability is in scope, `at T` introduces or propagates an
elided `<storage s>` identity:

```metel
fun identity(value: at Node) -> at Node { value }
```

A single input identity propagates to the output. Separate input positions receive
separate identities unless an explicit `<storage s>` relates them:

```metel
fun same<storage s>(x: at s Node, y: at s Node) -> at s Node { x }
```

Elision never produces plain `T` and never performs extraction.

### 8.4 Call-site capability elision

RFC-0065 invented allocator-specific omission of a single allocator argument. RFC-0113
now proposes the general mechanism for values threaded implicitly through call trees.
This RFC does not retain a second allocator-only call rule. An allocator parameter is
explicit by default:

```metel
wrap(arena, value)
```

If declared as a context parameter under RFC-0113, it may be omitted and is resolved
by that RFC's type-directed, ambiguity-is-an-error rules. Multi-allocator positional
relationships remain explicit unless their distinct required types make each context
resolution independently unique.

---

## 9. Scoped, external, and struct-owned allocators

### 9.1 Scoped construction

Closure-scoped allocators expose an `alloc` parameter:

```metel
BumpAlloc::scoped((alloc arena) -> {
    let node = place arena Node { value = 1 };
    process(&node);
});
```

The allocator cannot be destroyed while any `at arena T` handle or derived borrow is
live. Variable-scoped construction obeys the same rule at explicit `drop(arena)` and
at scope exit.

### 9.2 External storage parameters

A type that preserves caller-owned storage declares a storage identity explicitly:

```metel
struct Parser<storage arena> {
    input: at arena String,
    pos: u64,
}

extend<storage arena> Parser<arena> {
    fun new<A: Alloc>(alloc a: A, src: String) -> Parser<a> {
        Parser { input = place a src, pos = 0 }
    }
}
```

The storage parameter records identity and selected family, not merely allocator kind.
Methods that allocate again must additionally receive the corresponding runtime
capability; preservation alone cannot recreate it.

### 9.3 Struct-owned allocators

In a struct primary constructor, `alloc` means the value owns the allocator:

```metel
struct Cache(alloc arena: BumpAlloc) {
    entries: at arena HashMap<Key, Value>,
}
```

Construction creates `arena` as part of `Cache`; destruction drops allocation-backed
fields before the allocator. `arena` is implicitly in scope in `extend Cache` bodies
but is not an externally nameable parameter of `Cache`'s public type.

Allocation through a struct-owned allocator requires exclusive access to the owner,
because allocation mutates allocator state:

```metel
extend Cache {
    fun insert(&var self, value: Value) {
        let stored = place arena value;
        self.entries.insert(stored);
    }
}
```

A shared `&self` method may inspect existing placements but may not allocate unless the
allocator explicitly provides synchronized/interior-mutability semantics through a
different handle API.

Multiple owned allocators and allocator-type-polymorphic owned structs are permitted
by the model; a concrete use should settle whether the initial grammar admits both.

The initial conservative rule remains at most one owned allocator until §15.2 OQ4 is
resolved. This records RFC-0068's accepted restriction rather than silently widening
it while the replacement is still a draft.

### 9.4 The owner's lifetime and a method borrow are distinct

A method sees both the lifetime of the containing value/storage and the duration of
the particular borrow used to call the method. A reference anchored to `self` in a
return type denotes the containing binding's lifetime under RFC-0067, not permission
to retain the exclusive call borrow indefinitely:

```metel
extend Cache {
    fun root(&self) -> &self Value {
        &self.entries.first
    }
}
```

The call's shared borrow may end while the returned reference remains valid, but the
reference cannot outlive the `Cache` binding or its owned allocator. RFC-0067 and
RFC-0122 own the precise anchor and NLL rules; this RFC preserves the two-lifetime
requirement that their rules must express.

### 9.5 Generic `extend` blocks and aspect methods

External storage identities are repeated in generic `extend` headers; struct-owned
identities are implicit:

```metel
extend<storage s, T> ArenaSet<s, T> {
    fun first(&self) -> &T { &self.data.first }
}

extend Cache {
    // the owned `arena` binding is in scope here
}
```

Multiple external identities are declared independently. Ordinary allocator type
parameters retain ordinary aspect bounds:

```metel
fun copy_into<T: Clone, A: Alloc>(alloc dst: A, value: &T) -> at dst T {
    place dst value.clone()
}
```

Aspects themselves do not acquire allocator parameters merely because one method
allocates. The method declares them:

```metel
aspect Serialize {
    fun serialize<A: Alloc>(alloc dst: A, self: &Self) -> at dst Bytes;
}

extend Record: Serialize {
    fun serialize<A: Alloc>(alloc dst: A, self: &Self) -> at dst Bytes {
        place dst Bytes::encode(self)
    }
}
```

---

## 10. Standard allocators and `AutoAlloc`

| Allocator | Selected handle | Scope | Sendability | Individual move-out |
|---|---|---|---|---|
| `Heap` | unique affine | process | when `T: Send` | all `T` |
| `LocalHeap` | unique affine | thread | not `Send` | all `T` |
| `BumpAlloc` | unique affine | binding | not `Send` by default | `T: Copy` or `T: !Drop` |
| `AutoAlloc` | unique affine | binding | not `Send` by default | all `T` |
| `GlobalGc` | traced copyable | process | subject to RFC-0139 | no pointee move-out |
| `LocalGc` | traced copyable | thread | not `Send` | no pointee move-out |
| `GcRegion` | traced copyable | binding | not `Send` by default | no pointee move-out |

GC rows are interface commitments only; their collection semantics remain RFC-0139.

`AutoAlloc` guarantees validity for its declared scope, complete destruction of live
`Drop` values, reverse-declaration drop order where observable, safe move-out for its
unique handles, and observational equivalence to using `Heap` except for performance,
addresses, and allocation failure behavior already made visible by the type.

The compiler may choose stack, bump, or heap backing per placement and may combine
allocations. It may inline a placement into containing storage or elide it entirely
when doing so preserves observable behavior. It may not choose a tracing or shared
handle family for `AutoAlloc`, because that would change copyability, destruction, and
aliasing rather than only strategy. A correct implementation that initially uses heap
backing everywhere still satisfies the language semantics; minimum optimization,
debug/release strategy stability, and unsafe address observability are implementation
policy rather than type-system guarantees.

---

## 11. Well-formedness, scope, and variance

### 11.1 Nested placements

`at a T` is well-formed only if every storage identity contained by `T` lives at least
as long as the placement in `a`. Equivalently, for each `b` occurring in `T`, `b`'s
scope must enclose the live range of the `a` placement.

```metel
BumpAlloc::scoped((alloc outer) -> {
    BumpAlloc::scoped((alloc inner) -> {
        let x: at inner Node = place inner Node { value = 1 };
        let bad: at outer (at inner Node) = place outer x;
        // error: inner may end before the outer placement
    });
});
```

The same-identity case is trivially well-formed. A `Heap` placement stored inside a
shorter arena is well-formed because `Heap` outlives it. The reverse is rejected.

### 11.2 Generic checking

When `T` is generic, nested-storage well-formedness is checked at instantiation, where
the identities contained by the concrete `T` are known. An explicit `WellFormed<s>`
bound is not required initially; it may be added later if instantiation diagnostics
prove insufficient.

### 11.3 Variance

The standard unique `at a T` family is covariant in a storage scope and in `T`: a
longer-lived identity may satisfy a shorter guarantee, and structurally longer-lived
identities inside `T` strengthen the guarantee. `&r var T` remains invariant in `T`
under RFC-0067.

Allocator-selected families must declare and justify their own variance. This RFC does
not incorrectly transfer unique-pointer covariance to a mutable shared or traced
family. User-defined generic types derive variance from fields once the general
variance rules are specified.

---

## 12. Aspect objects and heterogeneous collections

An explicitly placed owned aspect object uses the same projection and operation:

```metel
let shape: at arena (dyn Shape) =
    place arena Circle { radius = 5.0 };
```

The expected `dyn Shape` type causes object coercion and allocation of the concrete
value in `arena`. The result has RFC-0008's data pointer and vtable pointer; only the
data placement and selected ownership family differ. Borrowed `&dyn Shape` and `&var
dyn Shape` are unchanged.

```metel
let shapes: List<at arena (dyn Shape)> = List::new();
shapes.push(place arena Circle { radius = 5.0 });
shapes.push(place arena Rectangle { width = 3.0, height = 4.0 });
```

For a unique family, drop invokes the concrete destructor through the vtable and then
releases or records the placement according to the allocator. A tracing family follows
its own finalization rules. Object safety and dispatch remain RFC-0008's concern.

---

## 13. Diagnostics

Diagnostics name source bindings and capabilities rather than exposing compiler-only
brand identifiers:

```text
error: value of type `at arena Node` outlives allocator `arena`
  | `arena` is dropped here while `node` is still live
```

Ambiguous elision lists every candidate and suggests the explicit form:

```text
error: `place Node { ... }` has two compatible allocator contexts: `heap`, `arena`
  | write `place heap ...` or `place arena ...`
```

Unsupported extraction identifies the selected handle policy:

```text
error: cannot move `Config: Drop` out of bulk allocator `arena`
  | borrow it, clone into another allocator, or use an individually tracked allocator
```

---

## 14. Alternatives considered

### 14.1 Replace `@` with another sigil

`^a T`, `~a T`, or `$a T` could preserve the accepted grammar mechanically. This is
the smallest textual change, but it preserves the larger semantic problem: the syntax
still presents every allocation as one owning-pointer family. It also spends another
scarce punctuation mark on a subsystem whose concepts now have ordinary names.

### 14.2 `alloc a T` for both type and expression

Using one keyword in both positions most closely mirrors `@a T`/`@a expr`. It becomes
difficult to distinguish the allocator capability declaration, placement operation,
and resulting type in dense generic code. `alloc` for the capability binder, `place`
for the operation, and `at` for the relationship assign each word one role.

### 14.3 Explicit pointer families only

The language could expose `ArenaBox<T, 'a>`, `HeapBox<T>`, and `Gc<T, 'g>` directly and
use ordinary `.alloc` calls. This cleanly separates ownership families but loses the
accepted design's representation-independent statement "preserve exactly the caller's
storage." Generic code would need higher-kinded type parameters or repeated bounds for
every family. `at s T` retains that abstraction as a projection while allowing the
normalized family to differ.

### 14.4 Path-dependent types

`a::Pointer<T>` is a compact alternative to `at a T` and naturally suggests instance
identity. It requires general path-dependent associated types, makes an allocator value
look like a namespace, and leaves the identity-only `<storage s>` case without a
runtime path. This RFC chooses a narrow placement projection instead of committing the
whole language to path-dependent members.

### 14.5 Brands written explicitly everywhere

An explicit form such as `A::Pointer<T, 'a>` is semantically adequate. It forces users
to thread allocator type `A`, value `a`, and brand `'a` as three names for one ordinary
case. `alloc a: A` deliberately binds capability and identity together; the identity
may lower to the general brand mechanism without exposing that duplication.

### 14.6 Ordinary method calls only

`a.alloc(value)` cannot on its own express expected-type-directed aspect-object
coercion, type-directed placement at bindings, or the identity-indexed result without
a more general dependent method type. It may remain an implementation entry point,
but `place` is the language-visible operation.

---

## 15. Acceptance dependencies and open questions

This RFC is intentionally a draft. Its primary proposal is concrete; the following
items must be closed before review can claim the replacement is complete.

### 15.1 Acceptance dependencies

1. RFC-0026 must provide enough unsafe vocabulary to spell or deliberately seal the
   raw block operations in §3.3. Standard allocators can be implemented first, but an
   accepted claim that `Alloc` is user-implementable cannot remain aspirational.
2. RFC-0076 must settle the rigidity and generativity rules reused by storage
   identities. This RFC does not require its chosen surface sigil.
3. RFC-0113 must decide context-parameter syntax before allocator call-site omission
   can be specified by reference rather than by analogy.
4. RFC-0122 must provide the borrow/outlives enforcement on which scoped allocator
   safety depends.
5. Generic associated handle families must either extend RFC-0082 or be specified in
   a focused prerequisite RFC.

These dependencies are named rather than restated as heterogeneous open questions;
they close when the corresponding RFCs settle.

### 15.2 Settleable design questions

1. **Surface spelling.** Confirm `alloc a: A`, `at a T`, `place a expr`, and
   `<storage a>`, or select one of §14's spellings before promotion to under-review.
2. **Projection normalization.** Decide whether compiler diagnostics normally retain
   `at a T` or display the allocator's normalized handle family when known.
3. **Local binding inference.** §2.2 permits a local `let arena = BumpAlloc::new()` to
   introduce identity without `alloc`; confirm that this convenience does not make an
   impl added later alter source meaning.
4. **Multiple struct-owned allocators.** The model permits them; decide whether the
   first grammar does too or deliberately restricts the feature pending a use case.
5. **Allocator-polymorphic owned structs.** Decide whether
   `struct Cache<A: Alloc>(alloc arena: A)` belongs in the initial surface.
6. **Standard GC rows.** Decide whether §10 should list the GC allocators now or merely
   state the interface they would satisfy after RFC-0139 settles.

---

## 16. Worked acceptance tests

Before this RFC may reach `2-accepted`, worked examples must cover at least:

- two instances of the same allocator type, proving identities do not unify;
- a nested handle whose inner storage dies too early;
- `T: Drop` moved from `Heap`, an individually tracked arena, and a bulk arena;
- a generic preserving function with no allocator capability;
- a generic allocating function with a capability and fallible result;
- ambiguity between outer and inner allocators, with no depth-based shadowing;
- a struct owning its allocator and rejecting allocation through shared `&self`;
- `AutoAlloc` selecting two different backing strategies without changing behavior;
- a `Gc` handle proving `at a T` does not imply affine ownership;
- a runtime-sized buffer growing across relocation while initialized elements remain
  owned and dropped exactly once;
- a heterogeneous `List<at a (dyn Aspect)>`;
- interaction with context-parameter omission after RFC-0113 settles.

This list is part of the proposal because the previous cluster was internally
consistent yet still accumulated contradictions between sibling RFCs. Acceptance must
exercise the combined model rather than ratify each section independently.

---

## References

- RFC-0008 — Aspect Objects.
- RFC-0026 — Unsafe Blocks.
- RFC-0063 — Allocator Handles; proposed superseded core.
- RFC-0065 — Allocator and Lifetime Ergonomics; allocator portions proposed
  superseded, lifetime-anchor portions retained under RFC-0067.
- RFC-0066 — Allocated Value Extraction; proposed superseded.
- RFC-0067 / RFC-0067a — Lifetime Anchors and Reference Types.
- RFC-0068 — Struct-Owned Allocators; proposed superseded.
- RFC-0071 — Ownership and Move Semantics.
- RFC-0072 — Negative Bounds.
- RFC-0073 — AutoAlloc; proposed superseded.
- RFC-0076 — Brand Types.
- RFC-0077 — Allocator Generics; proposed superseded.
- RFC-0080 — Standard Library Aspects.
- RFC-0082 — Associated Types.
- RFC-0093 / RFC-0095 — Derive Registration and Attributes/Metadata; the proposed
  restoration of their original `@` spelling motivates the syntax reopening.
- RFC-0113 — Context Parameters.
- RFC-0122 — Borrow Checking.
- RFC-0133 — From-Metel List: the Runtime-Sized Buffer Gap.
- RFC-0139 — Garbage-Collected Allocators and Allocator-Determined Pointer Types.
- RFC-0141 — Aspect Objects: Explicit Allocator Placement; proposed superseded.

---

## Decision

**Outcome:** *(pending)*
**Target:** *(set when accepted)*
