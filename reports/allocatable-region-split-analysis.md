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

A potential concern: for handle regions the borrow lifetime is tied to the region
scope; for `@[Rc] T` there is no scope. Does this create a rule divergence?

It does not, because `@[Rc] T` behaves like `@[Heap] T` in this respect, not like
`@[AutoRegion] T`. Consider:

```metel
let h: @[Heap] Node = @[Heap] Node { val: 1 };
let r_h: &Node = &*h;
drop(h);   // ERROR: h is borrowed by r_h

let a: @[Rc] Node = @[Rc] Node { val: 1 };
let b = a.clone();
let r_a: &Node = &*a;
drop(a);   // ERROR: a is borrowed by r_a
// b is still live, but r_a borrows from `a` specifically, not from `b`
```

In both cases the borrow checker ties `r` to the specific owning binding, not to any
scope or any other alias. The borrow lifetime rule is uniform for all strategy types
(Heap, LocalHeap, Rc, Arc): the borrow cannot outlive the binding it was derived from.

The handle-region case is the unusual one: there, the borrow is tied to the region tag
`r` rather than a specific allocation binding, because every allocation in the region
shares the same scope. This is a genuine divergence between handle regions and strategy
types, but it does not create a divergence between unique and shared strategy types.

**Borrow lifetime semantics are uniform across all strategy types and unify cleanly
under `Allocatable`.**

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

The concrete benefit: allocation expressions use the same syntax regardless of strategy.

```metel
// Change allocation strategy by changing one word:
let a: @[Heap] Node = @[Heap] Node { val: 1 };
let a: @[Rc]   Node = @[Rc]   Node { val: 1 };
let a: @[Arc]  Node = @[Arc]  Node { val: 1 };
```

Downstream code that borrows `&Node` from `a` is unchanged in all three cases. This
fits Metel's design identity ("allocators as lifetimes") — the allocation strategy is a
local decision that should not ripple through the rest of the codebase.

The alternative (`Rc<T>` as a library struct) partially recovers this via `Deref`
coercion, but the allocation expression changes form:

```metel
let a: @[Heap] Node = @[Heap] Node { val: 1 };
let a: Rc<Node>     = Rc::new(Node { val: 1 });  // different syntax, different type annotation
```

This is a genuine loss. The strategy-change use case is the strongest argument for
keeping shared pointers in the bracket position.

The cost of `Allocatable` is one new concept. Its benefit is that the concept does real
work: it names the property that justifies `@[_] T` syntax — "this type can appear in
the bracket channel" — separately from the property that justifies region-specific
operations like move-out, `SubRegion`, and `[own r]`. Without `Allocatable`, `Region`
is doing both jobs and doing neither cleanly.

---

## Recommendation

The analysis supports introducing `Allocatable` with the following structure:

```
Allocatable                          — can appear in @[_] T; borrow and drop
├── Region                           — unique ownership; move-out; SubRegion; [own r]
│   ├── BumpRegion  (handle region)
│   ├── AutoRegion  (handle region)
│   ├── Heap        (global unique)
│   └── LocalHeap   (global unique)
└── SharedPointer                    — shared ownership; Clone on pointer; get_mut
    ├── Rc
    └── Arc
```

**`Allocatable` provides:**
- Construction syntax — `@[R] expr`
- Borrow — `&@[R] T` with lifetime = source binding
- Sendability rule — R specifies the condition on T
- Drop contract — T::drop called exactly once, no leaks

**`Allocatable` does not provide:**
- Move-out — stays in `Region` (unique ownership required)
- SubRegion ordering — stays in `Region`
- `[own r]` struct fields — stays in `Region`
- Clone on the pointer — stays in `SharedPointer`
- `get_mut` — stays in `SharedPointer`

**What changes in the RFCs:**
- RFC-0063: introduce `Allocatable` as the bracket-channel interface; demote `Region`
  to a subtrait covering unique-ownership allocation strategies.
- RFC-0074: rename to "Shared Pointers"; replace `SharedRegion: Region` with
  `SharedPointer: Allocatable`; remove the three-category region table (it was a
  symptom of the forced classification); Rc and Arc are no longer regions.
- RFC-0065, RFC-0066, RFC-0067: audit each for `Region` bounds — some will stay
  `Region` (move-out, SubRegion interaction); others will widen to `Allocatable`
  (borrow syntax, ergonomic elision).
- RFC-0068, RFC-0069: no changes — already anchored to `Region` specifically.

**What does not change:** syntax, coercion, and borrow semantics as seen by the
programmer. The `@[Rc] T` form, `@[Heap] T` form, and downstream borrow code are
identical before and after.

---

## Open question not resolved here

The handle-region vs strategy-region split (BumpRegion/AutoRegion vs Heap/LocalHeap)
is currently both under `Region`. Whether `Region` should be further subdivided into
`HandleRegion` and `GlobalRegion` is a separate question not required for the
`Allocatable` split. It can be deferred.
