---
id: rfc-0074
title: "Shared Ownership — SharedRegion, Rc, and Arc"
date: '2026-06-29'
---

> **Status — under review.** Depends on RFC-0063 (Region Handles), RFC-0065 (Region
> Ergonomics), RFC-0066 (Region Pointer Extraction), RFC-0071 (Ownership and Move
> Semantics), and RFC-0072 (Negative Bounds). Introduces `SharedRegion` as a general
> extension to the existing region system, and defines `Rc` and `Arc` as the two stdlib
> types that implement it.

## Summary

The four existing stdlib regions cover four distinct allocation strategies:

| Type | Lifetime | Move-out | Sendable |
|---|---|---|---|
| `Heap` | Indefinite | Always safe | Yes |
| `LocalHeap` | Indefinite, thread-local | Always safe | No |
| `BumpRegion` | Scoped, bump arena | `T: !Drop` only | No |
| `AutoRegion` | Scoped, compiler-managed | Always safe | No |

One ownership pattern is absent: **shared heap ownership** — multiple owning pointers to
the same allocation, with the allocation freed when the last owner drops. This is
reference-counted ownership: cloning a pointer increments a counter; dropping it
decrements the counter; the allocation is freed and the destructor is called when the
counter reaches zero.

This RFC introduces shared ownership without treating it as a special case. One general
extension to the existing system is required:

**`SharedRegion`** — a supertrait of `Region` for type-level region tags that carry
reference-counted lifetime semantics. Any tag implementing `SharedRegion` gets `Clone`
and `Drop` automatically, and enables use of the `unique` keyword on its pointers. The
mechanism is available to user-defined regions, not only to stdlib types.

`Rc` and `Arc` are two stdlib type tags that implement `SharedRegion`. No language rules
specific to `Rc` or `Arc` are introduced; everything they provide falls out of
`SharedRegion` and the `unique` keyword.

---

## Motivation

### The shared ownership gap

RFC-0063 establishes `@[Heap] T` as Metel's uniquely-owned heap pointer — the direct
equivalent of Rust's `Box<T>`. Unique ownership is the right default: the borrow checker
can prove exactly one owner exists at all times, mutation through `&mut T` is always
safe, and the allocation is freed deterministically when the owner is dropped.

Unique ownership does not cover every data structure. A doubly-linked list node needs
a reference to both neighbours; a tree node may need a reference to its parent; a
shared cache entry may be referenced by multiple consumers with unpredictable lifetimes.
In all of these cases, the allocation should live as long as at least one owner keeps it
alive — the defining property of reference counting.

### The mutation hazard

Naive shared mutable access is unsafe. Consider two owning pointers `a` and `b` to the
same `Engine` value. If `a` is used to match on the current variant and extract a
reference to its field, while `b` is used to replace the variant, the replacement
destroys the field while the reference derived from `a` is still live — a use-after-free.

In Rust, `Rc<RefCell<T>>` defends against this with a runtime borrow check that panics
on violation. The panic cannot be statically prevented. This RFC eliminates the hazard
at compile time using the `unique` keyword (§2), which performs a binding-level alias
analysis to prove statically that no other owning pointer to the same allocation is
accessible during the mutation.

### Why not introduce Rc/Arc as exceptions

Introducing `Rc` and `Arc` as region types with special language rules — a non-cloneable
region handle that suddenly becomes cloneable, ad-hoc alias analysis — would be treating
symptoms rather than extending the system. The `SharedRegion` supertrait is general: any
user-defined RC-style region (pool-managed RC, arena-backed RC with a shared control
block) gets `Clone`, `Drop`, and `unique` block support for free.

---

## 1. The `SharedRegion` aspect

```metel
aspect SharedRegion: Region {
    type AllocationError = !;
}
```

`SharedRegion` is a supertrait of `Region`. Types implementing it are **type-level region
tags** (like `Heap` and `LocalHeap`, as opposed to binding-level tags like the `r` in a
`BumpRegion::scoped` scope) whose pointers carry reference-counted lifetimes.

Implementing `SharedRegion` on a tag type `R` declares three things:

1. **`Clone`**: `@[R] T` implements `Clone`. Cloning a pointer increments the reference
   count of the underlying allocation and returns a second owning pointer to the same
   allocation. This is O(1) and does not copy `T`.

2. **`Drop`**: `@[R] T` implements `Drop`. Dropping a pointer decrements the reference
   count. If the count reaches zero, `T::drop` is called and the backing memory is freed.

3. **`unique` blocks**: The `unique` keyword (§2) may be used on any `@[R] T` where
   `R: SharedRegion`. The compiler's binding-level alias analysis applies to the block.

`Clone` and `Drop` are derived automatically by the compiler for any `R: SharedRegion`;
no `impl Clone for @[R] T` or `impl Drop for @[R] T` is written by hand.

### 1.1 Allocation

Creation of a shared-owned value uses the standard allocation expression:

```metel
let a: @[Rc] Node = @[Rc] Node { val: 1 };
```

There is no `Rc::scoped` form — the allocation's lifetime is governed by the reference
count, not by lexical scope.

### 1.2 Clone — acquiring a second owner

```metel
let a: @[Rc] Node = @[Rc] Node { val: 1 };
let b = a.clone();   // reference count: 2; a and b are both valid owners
```

Moving `a` transfers the single owner without touching the reference count:

```metel
let b = a;   // b is now the only owner; a is consumed; count unchanged
```

### 1.3 Sendability

The sendability of `@[R] T` for any `R: SharedRegion` follows the existing rule from
RFC-0063 §4: `@[R] T` is sendable iff `R: Send`. The tag type's `Send` implementation
is the sole determinant. `SharedRegion` introduces no new sendability rules.

---

## 2. The `unique` keyword

`unique` is a compiler keyword that provides exclusive mutable access to a
shared-region pointer. It is only applicable to `@[R] T` where `R: SharedRegion`.

### Alias analysis

The safety guarantee of `unique` rests on a **binding-level alias analysis** performed
by the compiler on the block:

- The pointer operand `a` is **consumed** by the `unique` expression and is not
  accessible inside the block as `@[R] T`.
- The compiler tracks which other in-scope bindings are **known clones** of `a` —
  bindings derived from `a` through `.clone()` calls, transitively. These are excluded
  from the block.
- Bindings of the same type `@[R] T` that were **independently allocated** (not derived
  from `a`) are unrelated and may be freely used inside the block.

`unique` does not assert or check that the reference count equals one at runtime — the
alias analysis is a static, compile-time guarantee. Other `@[R] T` owners that are not
reachable from known clones of `a` may exist in memory; they cannot be accessed through
the block and therefore pose no hazard.

### 2.1 Form A — explicit block with explicit binding

```metel
unique a as s {
    s.engine = Engine::Impulse { fuel: 100 };
}
```

`a` is consumed; inside the block, `s` is bound as `&mut T`. The alias analysis checks
that no known clone of `a` is referenced inside the block. The result of the block is
the value of the last expression, as with any block expression.

### 2.2 Form B — explicit block with implicit rebinding

```metel
unique a {
    a.engine = Engine::Impulse { fuel: 100 };
}
```

Equivalent to form A with the binding name equal to `a`. Inside the block, `a` is
rebound as `&mut T` — its type changes from `@[R] T` to `&mut T` for the duration of
the block.

### 2.3 Form C — binding without explicit block *(deferred)*

```metel
let s = unique a;
s.engine = Engine::Impulse { fuel: 100 };
```

`unique a` produces a `&mut T` whose scope is determined by the borrow checker. The
exclusive-access region extends to the end of `s`'s live range; the compiler synthesises
the block boundary at that point.

This form requires the compiler to capture the continuation of the `let` binding as the
block body — the same mechanism as `async`/`await` lowering. The design and
implementation of continuation capture in this context are deferred to a follow-up RFC.
Forms A and B cover the common cases without it.

---

## 3. `Rc` — non-atomic shared ownership

`Rc` is a stdlib type tag that implements `SharedRegion`:

```metel
impl Region for Rc {
    type AllocationError = !;
}

impl SharedRegion for Rc {}
```

`Rc` uses **non-atomic** reference counting. The reference count is a plain integer;
incrementing and decrementing it is not thread-safe. Therefore `Rc` does not implement
`Send` or `Sync`:

```metel
// @[Rc] T: !Send — cannot cross fiber boundaries
// @[Rc] T: !Sync — cannot be shared across threads simultaneously
```

This falls out of the existing sendability rule (RFC-0063 §4): `@[Rc] T` is sendable iff
`Rc: Send`. Since `Rc: !Send`, no `@[Rc] T` is sendable, regardless of `T`.

---

## 4. `Arc` — atomic shared ownership

`Arc` implements `SharedRegion` with **atomic** reference counting, making it safe to
clone and drop across fiber boundaries:

```metel
impl Region for Arc {
    type AllocationError = !;
}

impl SharedRegion for Arc {}

impl Send for Arc {}
impl Sync for Arc {}
```

Sendability of `@[Arc] T` follows the standard rule: `@[Arc] T: Send` iff `Arc: Send`
and `T: Send + Sync`. Since `Arc: Send`, `@[Arc] T` is sendable when `T: Send + Sync`.

`Arc` and `Rc` are otherwise identical in interface. The distinction is:

| | `Rc` | `Arc` |
|---|---|---|
| RC operations | Non-atomic | Atomic |
| `Send` | No | Yes (when `T: Send + Sync`) |
| Per-clone cost | One integer increment | One atomic increment |
| Use case | Single-fiber shared ownership | Cross-fiber shared ownership |

The `unique` keyword is available on both `@[Rc] T` and `@[Arc] T`; the alias analysis
is identical for both since it operates on binding provenance, not on the tag type.

---

## 5. The six stdlib regions

| Type | Lifetime | Drop behaviour | Move-out | Sendable |
|---|---|---|---|---|
| `Heap` | Indefinite | `Drop::drop` when owner dropped | Always safe | Yes |
| `Arc` | Indefinite, atomic RC | `Drop::drop` when RC hits zero | Always safe | Yes (when `T: Send + Sync`) |
| `LocalHeap` | Indefinite, thread-local | `Drop::drop` when owner dropped | Always safe | No |
| `Rc` | Indefinite, non-atomic RC | `Drop::drop` when RC hits zero | Always safe | No |
| `BumpRegion` | Scoped, bump arena | Bulk free; no `Drop::drop` per slot | `T: !Drop` only | No |
| `AutoRegion` | Scoped, compiler-managed | Compiler-managed drop | Always safe | No |

---

## 6. Usage examples

### 6.1 Parent–child graph

```metel
struct Node {
    value: I32,
    children: @[Heap] List<@[Rc] Node>,
}

fun make_tree() -> @[Rc] Node {
    let leaf1 = @[Rc] Node { value: 1, children: @[Heap] List::Nil {} };
    let leaf2 = @[Rc] Node { value: 2, children: @[Heap] List::Nil {} };
    @[Rc] Node { value: 0, children: @[Heap] List::from([leaf1, leaf2]) }
}
```

Each node is freed when its last `@[Rc] Node` owner drops.

### 6.2 Safe variant replacement via `unique`

```metel
enum Engine { StringTheory { core: @[Heap] Core }, Impulse { fuel: I32 } }

let ship: @[Rc] Spaceship = @[Rc] Spaceship { engine: Engine::StringTheory { ... } };

// Form A — explicit block, renamed binding
unique ship as s {
    // The old StringTheory variant (and its core) drops before the new variant is set.
    s.engine = Engine::Impulse { fuel: 100 };
}

// Equivalent form B — explicit block, implicit rebinding
unique ship {
    ship.engine = Engine::Impulse { fuel: 100 };
}
```

### 6.3 Unrelated shared pointers are not excluded

```metel
let a: @[Rc] Node = @[Rc] Node { val: 1 };
let b: @[Rc] Node = @[Rc] Node { val: 2 };   // independent allocation — not a clone of a

unique a as node {
    node.val = b.val;   // OK: b was not derived from a
}
```

### 6.4 Cross-fiber shared state with `Arc`

```metel
let counter: @[Arc] Counter = @[Arc] Counter::new(0);
let c2 = counter.clone();   // atomic RC increment; c2 is a known clone of counter

spawn(fun() -> () {
    unique c2 { c2.increment() }
});

unique counter { counter.increment() }
```

`@[Arc] Counter: Send` because `Arc: Send` and `Counter: Send + Sync`. Inside each
`unique` block, the other handle (`counter` / `c2`) is a known clone and is excluded.
The two blocks cannot overlap because each consumes its handle for the duration.

### 6.5 `unique` with a called function

```metel
fun upgrade_engine(ship: &mut Spaceship, fuel: I32) {
    ship.engine = Engine::Impulse { fuel };
}

let ship: @[Rc] Spaceship = @[Rc] Spaceship { ... };

unique ship as s {
    upgrade_engine(s, 100);
    // OK: upgrade_engine receives &mut Spaceship, not @[Rc] Spaceship.
}
```

---

## Alternatives considered

### Rc/Arc as exceptions to the region system

Introducing `clone()` on region handles as a one-off feature of `Rc` and `Arc`, and
`unique` as dedicated syntax with ad-hoc alias rules, would work but would not
generalise. The `SharedRegion` supertrait means any user-defined RC-style region gets
`Clone`, `Drop`, and `unique` block support for free.

### Runtime alias check for `unique`

`unique` could check `RC == 1` at runtime and panic if not. This is Rust's `Rc::get_mut`
approach. It works but cannot be statically prevented from panicking. The binding-level
alias analysis makes the check static: the compiler rejects programs where a known alias
would be accessible during mutation. No runtime overhead; no possible crash.

### Closure-based `unique` with a type-level alias bound

An earlier design expressed `unique` as a static method on `SharedRegion` accepting a
closure, with a type-level bound to exclude aliases. This design has two problems: first,
the bound cannot be expressed precisely at the type level because it requires
distinguishing aliases of a specific binding from unrelated pointers of the same type;
second, even an approximation (`NotCapturing<@[R] T>`) may not be well-formed if region
tags are not type constructors. The binding-level analysis in the keyword form correctly
excludes only known clones of the specific pointer being mutated, without any type-level
machinery.

### `Rc<T>` as a library struct (not a region tag)

`Rc<T>` could be a plain struct containing `@[Heap] T` plus a reference count, with
`Deref` for read access and a `borrow_mut`-style method for guarded write access. This
fits the existing system completely but requires a runtime borrow check for mutation —
the same situation as `Rc<RefCell<T>>` in Rust. The region tag approach enables the
static `unique` keyword analysis; the struct approach cannot.

---

## Unresolved questions

1. **Cycle handling.** Reference counting cannot free cyclic structures — two `@[Rc] T`
   values referencing each other will never reach a count of zero and will leak. Options:
   weak pointers (a non-owning `@[WeakRc] T` that yields `Perhaps<@[Rc] T>`, also
   implementing a `WeakSharedRegion` aspect); a cycle collector; a type-system
   prohibition on cycles. Deferred — the right answer depends on observed usage patterns.

2. **Precision of the alias analysis.** The current analysis excludes only bindings
   derived from `a` via `.clone()` calls. A more sophisticated analysis based on
   data-flow or escape analysis could handle aliases introduced through function calls
   or field projections. The conservative clone-tracking approach is sound; the extent
   to which it can be made more precise is an implementation question. Deferred.

3. **`unique` across fiber boundaries for `Arc`.** The example in §6.4 shows two
   `unique` blocks on distinct clones in distinct fibers. The soundness argument relies
   on each block consuming its handle for its duration; the details of how the borrow
   checker reasons across fiber spawn points (RFC-0003/RFC-0064) are unresolved.

4. **`unique` nesting.** Whether a `unique` block may open a second `unique` block on
   a different `@[R] U` (for `U ≠ T`) is unspecified. The naive rule — each `unique`
   block independently performs its own alias analysis — appears sound; formal
   verification deferred.

5. **Form C (deferred).** The continuation-capture mechanism required for
   `let s = unique a;` is unspecified. Deferred to a follow-up RFC.

---

## References

- RFC-0063 (Region Handles) — region allocator interface; the `Region` aspect that
  `SharedRegion` extends; sendability rule (`@[R] T: Send iff R: Send`) that determines
  `Rc` and `Arc` sendability without new rules.
- RFC-0065 (Region Ergonomics) — `@`-position elision and call-site inference apply to
  `@[Rc] T` and `@[Arc] T` identically to any other region tag.
- RFC-0066 (Region Pointer Extraction) — move-out semantics; `@[Rc] T` and `@[Arc] T`
  move-out is always safe (no `T: !Drop` restriction; RC decrement handles cleanup).
- RFC-0071 (Ownership and Move Semantics) — `Clone` and `Drop` aspects; `@[Rc] T` and
  `@[Arc] T` implement both; `Copy`/`Drop` mutual exclusion means neither is `Copy`.
- RFC-0072 (Negative Bounds) — `T: !Drop`; not required for `@[Rc] T` or `@[Arc] T`.
- Ante programming language — the compile-time alias exclusion concept for shared
  pointers, adapted here as the `unique` keyword with binding-level alias analysis.
