---
id: allocatable-region-split-analysis
title: "Allocatable vs Region: Analysis of the SharedPointer Split"
type: report
created_date: '2026-06-30'
rfcs: [0063, 0065, 0066, 0067, 0068, 0069, 0071, 0072, 0074]
---

# Allocatable vs Region: Analysis of the SharedPointer Split

*This report analyses whether introducing an `Allocatable` supertrait above `Region`
is a sound way to preserve the `@[_] T` syntax and coercion ergonomics for `Rc` and
`Arc` while removing them from the `Region` hierarchy. Five questions are worked
through in sequence; the report ends with a recommendation.*

**Background.** RFC-0074 currently classifies `Rc` and `Arc` as `SharedRegion`
implementors — subtypes of `Region`. This has been questioned: Rc and Arc require too
many exceptions to the region model to be genuine regions. A proposed alternative is to
introduce a broader `Allocatable` concept that covers both regions and shared pointers,
with `Region` and `SharedPointer` as siblings underneath it. The `@[_] T` syntax would
be tied to `Allocatable` rather than `Region`, preserving the ergonomic benefits while
making the conceptual distinction explicit.

---

## Question 1: What does `Allocatable` actually require?

For the supertrait to be meaningful — not just a grouping — there must be a minimal set
of operations that both `Region` and `SharedPointer` genuinely share.

**Construction** — `@[R] expr` produces `@[R] T` for any `R: Allocatable`. For
handle regions this passes the allocator handle at runtime; for strategy types it
selects an allocation strategy. The *syntax* and the *produced type form* are uniform.
The underlying mechanism differs but is hidden behind the bracket channel. This unifies.

**Borrow** — `&@[R] T` produces `&T` with a lifetime tied to the owning pointer. This
is already uniform across all strategy types. `&@[Heap] T` lives as long as the owning
`@[Heap] T` binding. `&@[Rc] T` lives as long as the specific owning `@[Rc] T`
binding — not as long as any clone, just the one being borrowed. Both follow the same
rule: the borrow cannot outlive its source binding. This unifies.

The contrast is with *handle regions*, where the borrow lifetime is tied to the region
scope `r`, not any specific allocation binding. The handle vs strategy distinction is
more fundamental than the unique vs shared distinction for borrow lifetime. But since
`Allocatable` would cover all four cases, the borrow rule is: *borrow lifetime ≤
source binding lifetime*, which holds uniformly.

**Sendability** — `@[R] T: Send` follows a rule determined by `R`. For `Heap`:
`T: Send` suffices. For `Rc`: `@[Rc] T: !Send` always. For `Arc`: `T: Send + Sync`
required. The structure of the rule (R determines the condition on T) is uniform; the
specific condition varies. `SharedPointer` could specify its own sendability rule as
part of the supertrait contract. This unifies in structure.

**Drop** — `@[R] T` is eventually dropped. For unique-ownership types the owner's drop
triggers `T::drop` and deallocation. For shared-ownership types the last owner's drop
does the same. The *contract* (no double-drop, no leak, `T::drop` called exactly once)
is uniform. The mechanism differs. This unifies at the contract level.

**Conclusion.** A meaningful `Allocatable` interface exists: construction, borrow,
sendability, and drop contract. All four are genuinely shared.

---

## Question 2: Does move-out unify?

RFC-0066 defines move-out as extracting a `T` from `@[R] T`, consuming the pointer.

For regions: move-out is always possible (with the `T: !Drop` restriction for
`BumpRegion`). The owning pointer is consumed; the allocation slot is reclaimed by the
region. This is safe because unique ownership guarantees no other pointer exists.

For shared pointers: the equivalent operation is `try_unwrap`, which succeeds only if
the reference count is exactly one — `Result<T, @[Rc] T>`. If other owners exist, the
operation fails at runtime and returns the pointer unchanged.

These are not the same operation. Unique-ownership move-out is unconditional; shared
move-out is a runtime-checked fallible operation. The asymmetry is fundamental: unique
ownership guarantees the precondition statically; shared ownership cannot.

**Move-out must not be part of `Allocatable`.** It stays as a `Region`-specific
operation (or more precisely, a unique-ownership-specific operation). Generic code over
`Allocatable` cannot move out of `@[R] T` — it can only borrow and drop. `try_unwrap`
remains a method on `@[Rc] T` and `@[Arc] T` specifically.

This is the sharpest incompatibility between regions and shared pointers. It is also
well-contained: move-out is already a specific RFC-0066 operation, not a core
`Region` trait method.

---

## Question 3: What is the lifetime of `&@[Rc] T`?

A potential concern: for handle regions there is a region scope `r`; for `@[Rc] T`
there is no scope. Does this create a borrow-rule divergence?

It does not. The borrow rule is uniform across all allocation kinds: **the borrow
lifetime is tied to the source binding**, with any enclosing region scope acting as an
additive upper bound.

For handle regions, individual bindings can be dropped before the region scope expires,
and the borrow expires with them — the region scope does not extend the borrow:

```metel
AutoRegion::scoped([r]() -> {
    let x: @[r] Node = Node { val: 1 };
    let ref_x: &Node = &*x;
    drop(x);      // ERROR: x is borrowed by ref_x
                  // r is still live, but x — the binding — is gone
    let y: @[r] Node = Node { val: 2 };  // independent binding, independent lifetime
});
```

The region scope `r` is an additional upper bound — a borrow into a region allocation
cannot outlive `r` even if the binding were kept alive past it — but the binding is the
primary anchor. This is the same structure as:

```metel
let h: @[Heap] Node = Node { val: 1 };
let r_h: &Node = &*h;
drop(h);   // ERROR: h is borrowed by r_h

let a: @[Rc] Node = Node { val: 1 };
let b = a.clone();
let r_a: &Node = &*a;
drop(a);   // ERROR: a is borrowed by r_a
// b is still live, but r_a borrows from `a` specifically, not from `b`
```

In all three cases — handle region, unique strategy, shared strategy — the borrow
checker ties the borrow to the specific owning binding. The region scope adds an upper
bound for handle regions but does not change the primary rule.

**Borrow lifetime semantics are uniform across all allocation kinds and unify cleanly
under `Allocatable`.** This is a stronger result than the handle vs strategy framing
suggested.

---

## Question 4: Do RFC-0068 and RFC-0069 apply to `SharedPointer`?

**RFC-0068 (`[own r]` struct-owned regions):** A `[own r]` field in a struct means
the struct owns the region handle; when the struct drops, it drops `r`, which drops all
allocations in that region. This is coherent only for handle regions: the owned value
is the allocator handle.

`[own Rc]` has no meaning — there is no "Rc handle" to own. Individual `@[Rc] T`
pointers are the owning units; the Rc "system" has no handle. RFC-0068 does not apply
to SharedPointer.

**RFC-0069 (SubRegion / Outlives):** `r: SubRegion<s>` asserts that all allocations
in `r` outlive all allocations in `s`. This is a structural containment relationship
between lifetime scopes. `Rc: SubRegion<Heap>` would assert that all Rc allocations
outlive all Heap allocations, which is neither true nor useful — both are indefinite,
independent lifetimes. RFC-0069 does not apply to SharedPointer.

**These are non-issues for the split.** Both RFC-0068 and RFC-0069 reference `Region`
by name in their specifications. Changing `@[_]` to be tied to `Allocatable` rather
than `Region` leaves these RFCs unchanged: `[own r: Region]` and `SubRegion<R: Region>`
naturally continue to exclude shared pointers. No amendments needed.

---

## Question 5: Is the ergonomic benefit large enough to justify `Allocatable`?

The claimed benefit is two-fold: uniform allocation syntax, and transparent strategy
changes — changing `@[Heap]` to `@[Rc]` without touching downstream code.

### 5.1 What downstream code can actually ignore

Downstream code that only *borrows* is genuinely strategy-agnostic. A function taking
`&Node` works identically whether the caller holds `@[Heap] Node` or `@[Rc] Node`:

```metel
fun read(n: &Node) -> I32 { n.val }

let h: @[Heap] Node = Node { val: 1 };
let r: @[Rc]   Node = Node { val: 1 };

read(&*h);   // fine
read(&*r);   // fine — same call site
```

This is a real benefit. Read-only access to allocated values is common, and the borrow
being uniform means functions that only read do not need to know the allocation strategy.

### 5.2 What downstream code cannot ignore

**Mutation.** For `@[Heap] Node`, direct mutation through the owning pointer is
unconditional — unique ownership guarantees no alias exists:

```metel
let mut h: @[Heap] Node = Node { val: 1 };
h.val = 42;   // fine
```

For `@[Rc] Node`, the same mutation requires a runtime check:

```metel
let mut r: @[Rc] Node = Node { val: 1 };
r.val = 42;   // ERROR: cannot mutate through a shared pointer directly
r.get_mut().unwrap().val = 42;   // get_mut() returns None if other owners exist
```

Every mutation site must change when moving from unique to shared ownership. This is
not a transparent strategy change.

**Clone semantics.** For `@[Heap] Node`, `.clone()` deep-copies `Node` — the result
is an independent value. For `@[Rc] Node`, `.clone()` increments the reference count
and returns a second pointer to the *same* `Node`. Code that clones and mutates the
clone — expecting an independent copy — silently aliases instead:

```metel
let a: @[Heap] Node = Node { val: 1 };
let mut b = a.clone();
b.val = 99;   // a.val is still 1 — independent copy

let a: @[Rc] Node = Node { val: 1 };
let b = a.clone();
// b.val = 99 requires get_mut, and would also affect a if it succeeded
// a and b point to the same Node — completely different semantics
```

**Extraction and pattern matching.** `@[Heap] Node` can be consumed and its inner
value extracted unconditionally. `@[Rc] Node` requires `try_unwrap` — a fallible,
runtime-checked operation that returns `Result<Node, @[Rc] Node>`.

### 5.3 The transparent-change boundary

The transparent strategy-change property holds within the **unique-ownership** family:
`@[Heap] T`, `@[LocalHeap] T`, `@[AutoRegion] T`, `@[BumpRegion] T` (modulo the
`!Drop` restriction). These share the same ownership model — one owner, direct
mutation, deep-copy clone — so switching between them really does leave downstream
code unchanged.

Changing from any unique-ownership type to `@[Rc] T` or `@[Arc] T` is **not**
transparent. It changes the ownership model, which changes mutation patterns, clone
semantics, and extraction. Downstream code that does anything beyond borrowing must
change.

### 5.4 What remains of the benefit

The `@[_]` syntax uniformity is still worth something, but narrower than presented:

- **Borrow sites** — `&@[R] T` code is genuinely unchanged. This is common.
- **Allocation expressions** — `@[Rc] Node { ... }` is more ergonomic than
  `Rc::new(Node { ... })`, regardless of what else changes.
- **Type annotation consistency** — `@[Rc] Node` reads like `@[Heap] Node` rather
  than like a structurally different type.

These are surface ergonomics. They are real but they do not justify the "transparent
strategy change" framing. The accurate claim is: *allocation syntax and borrow syntax
are uniform; ownership semantics are not*.

### 5.5 Does this undermine `Allocatable`?

Partially. The strongest argument for `Allocatable` — transparent strategy change —
does not hold across the unique/shared boundary. The remaining benefit is syntactic
uniformity for allocation expressions and borrow sites.

Whether syntactic uniformity alone justifies introducing `Allocatable` as a language
concept depends on how heavily the language wants to emphasize "allocation strategy is
a local decision." If that principle is load-bearing, `Allocatable` is worth the cost.
If it applies only within the unique-ownership family (which is where it is actually
sound), then `Allocatable` may be over-engineering: the unique-ownership types already
unify under `Region`, and `Rc`/`Arc` can be library structs with allocation sugar
(`@[Rc] expr` desugaring to `Rc::new(expr)`) without being `Allocatable` implementors.

---

## Recommendation

The analysis produces a more conditional recommendation than initially expected.

### The case for `Allocatable`

The four core properties (construction, borrow, sendability, drop contract) unify
genuinely. Move-out is the only hard incompatibility, and it is well-contained.
Borrow semantics are uniform across all allocation kinds. RFC-0068 and RFC-0069 need
no changes. The `Allocatable` interface is coherent.

If the language treats "allocation syntax is uniform" as a first-class design value —
even knowing that ownership semantics differ — then `Allocatable` is justified:

```
Allocatable                          — @[_] T syntax; borrow; sendability; drop contract
├── Region                           — unique ownership; move-out; SubRegion; [own r]
│   ├── BumpRegion  (handle region)
│   ├── AutoRegion  (handle region)
│   ├── Heap        (global unique)
│   └── LocalHeap   (global unique)
└── SharedPointer                    — shared ownership; Clone on pointer; get_mut
    ├── Rc
    └── Arc
```

### The case against `Allocatable`

The "transparent strategy change" claim does not hold across the unique/shared
boundary. Mutation, clone semantics, and extraction all change when moving to shared
ownership. Downstream code that does anything beyond borrowing must be updated. The
principal benefit reduces to: allocation expressions and borrow sites use the same
syntax.

Syntactic uniformity at those two sites can be achieved more cheaply: `@[Rc] expr`
could be allocation sugar that desugars to `Rc::new(expr)` without `Rc` implementing
any `Allocatable` trait. The programmer writes `@[Rc] Node { val: 1 }` and gets
`Rc<Node>`; the borrow `&*ptr` is covered by `Deref`. No new trait, no hierarchy.

### The open design question

The decision hinges on whether the following two positions are held:

1. **"Allocation syntax should be uniform for all kinds."** → `Allocatable` is worth
   introducing as a trait, with the ownership-model differences visible in the subtype.
   Programmers who only borrow get full transparency; those who mutate see the
   difference in the type.

2. **"Syntax uniformity for its own sake is not sufficient."** → `Rc`/`Arc` are
   library structs; `@[Rc] expr` is allocation sugar (not a trait bound); the `Region`
   concept stays clean and exception-free.

Both positions are internally consistent. This report does not resolve the choice —
that is a language philosophy decision. What the analysis rules out is the middle
ground: treating `Rc` and `Arc` as full `Region` implementors (the current RFC-0074
design) is the worst of both worlds — it forces exceptions into the region model
without delivering the transparent-strategy-change property that would justify them.

---

## Open question not resolved here

The handle-region vs strategy-region split (BumpRegion/AutoRegion vs Heap/LocalHeap)
is currently both under `Region`. Whether `Region` should be further subdivided into
`HandleRegion` and `GlobalRegion` is a separate question not required for the
`Allocatable` split. It can be deferred.
