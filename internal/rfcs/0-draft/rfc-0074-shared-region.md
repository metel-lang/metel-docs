---
id: rfc-0074
title: "Rc and Arc — Reference-Counted Pointers"
date: '2026-06-29'
---

> **Status — draft.** Depends on RFC-0063 (Region Handles), RFC-0065 (Region
> Ergonomics), RFC-0066 (Region Pointer Extraction), RFC-0071 (Ownership and Move
> Semantics), and RFC-0072 (Negative Bounds). Introduces `Rc` as a fifth stdlib
> region with reference-counted lifetime semantics, and the `uniq` scope for
> compile-time-verified exclusive access to shared allocations. Names `Arc` as
> the sendable atomic-RC counterpart, deferred to a follow-up RFC.

## Summary

The four existing stdlib regions cover four distinct allocation strategies:

| Type | Lifetime | Move-out | Sendable |
|---|---|---|---|
| `Heap` | Indefinite | Always safe | Yes |
| `LocalHeap` | Indefinite, thread-local | Always safe | No |
| `BumpRegion` | Scoped, bump arena | `T: !Drop` only | No |
| `AutoRegion` | Scoped, bump + drop list | Always safe | No |

One ownership pattern is absent: **shared heap ownership** — multiple owning references to
the same heap allocation, with the allocation freed when the last owner is dropped. This is
the reference-counted pointer pattern (`Rc<T>` in Rust, `shared` in Ante, `shared_ptr` in
C++). Without it, graph-like structures and parent-child relationships where either party
may outlive the other require manual lifetime management or allocation into a long-lived
region.

`Rc` fills this slot. `@[Rc] T` is a reference-counted heap pointer. The
allocation is freed and `T::drop` is called when the last `@[Rc] T` owner is dropped.

The reference-counted ownership model introduces a new hazard: because multiple owning
references to the same allocation can coexist, mutating through one reference — in
particular replacing an enum variant — is only safe when no other owning reference is
reachable in the current scope. Enforcing this at runtime (the `RefCell` approach) adds
overhead and produces crashes that cannot be caught by the type system.

This RFC addresses the hazard at compile time using the **`uniq` scope**: a lexical block
in which the compiler statically verifies that no other owning reference to the same
allocation is accessible. Within that block, the shared pointer is usable as an exclusive
mutable borrow, permitting safe mutation of enum variants and other layout-changing
operations.

---

## Motivation

### The shared ownership gap

RFC-0063 establishes `@[Heap] T` as Metel's uniquely-owned heap pointer — the direct
equivalent of Rust's `Box<T>`. Unique ownership is the right default: the borrow checker
can prove exactly one owner exists at all times, mutation through `&mut T` is always safe,
and the allocation is freed deterministically when the owner is dropped.

Unique ownership does not cover every data structure. A doubly-linked list node needs a
reference to both its neighbours; a tree node may need a reference to its parent; a
shared cache entry may be referenced by multiple consumers that all outlive each other in
unpredictable order. In all of these cases, the correct ownership model is: the allocation
lives as long as at least one owner keeps it alive.

The existing workaround is `@[Heap] T` with interior sharing via `&T` borrows, but this
ties the allocation's lifetime to a single owning scope. When the owner's scope ends,
all borrows become invalid — even if other parties would have kept the allocation alive.
A reference-counted pointer solves this by making ownership additive: cloning an
`@[Rc] T` increments a reference count, dropping it decrements the count, and the
allocation is freed only when the count reaches zero. This is what `Rc` provides.

### The mutation hazard: why `Rc<RefCell<T>>` is unsatisfying

Naive shared mutable access is unsafe. Consider:

```metel
let a: @[Rc] Engine = @[Rc] Engine::StringTheory { core: @[Heap] Core::new() };
let b = a.clone();   // b is a second owner of the same Engine

// If a and b alias the same Engine, this is unsound:
match &a {
    Engine::StringTheory { core } => {
        b = @[Rc] Engine::Impulse { fuel: 100 };
                                // ^^^ drops the old StringTheory variant,
                                //     freeing core while &core is still live
        use(core);              // use-after-free
    }
}
```

The hazard arises specifically when mutating through one alias while holding a borrow
derived from another alias into the old value. In Rust, `Rc<RefCell<T>>` defends against
this by checking exclusive access at runtime and panicking on violation. The panic cannot
be predicted by the type system.

Metel can eliminate both the runtime check and the crash potential using the
`uniq` scope, which proves at compile time that no other owning reference is accessible
during the mutation.

---

## 1. The `Rc` region kind

`Rc` is a stdlib type that implements the region allocator interface (RFC-0063 §1.1):

```metel
impl Region for Rc {
    type AllocationError = !;
}
```

`AllocationError = !` means allocation is infallible — OOM panics rather than returning
an error. This matches `Heap`, `LocalHeap`, and `AutoRegion`.

`Rc` is not a scoped region. There is no `Rc::scoped` form — the allocation's
lifetime is determined by reference counting, not lexical scope. Creation uses a single
form:

```metel
let x: @[Rc] T = @[Rc] expr;
```

---

## 2. Semantics of `@[Rc] T` and `@[Arc] T`

### 2.1 Clone — acquiring a second owner

`@[Rc] T` is non-`Copy` (RFC-0071 §4). Moving an `@[Rc] T` value transfers
ownership without changing the reference count:

```metel
let a: @[Rc] Node = @[Rc] Node { val: 1 };
let b = a;   // ownership transferred; a is gone; reference count unchanged
```

Acquiring a *second* owning reference requires an explicit clone, which increments the
reference count:

```metel
let a: @[Rc] Node = @[Rc] Node { val: 1 };
let b = a.clone();   // reference count: 2; both a and b are valid owners
```

`clone()` on `@[Rc] T` is always O(1) and does not copy the `T` value — it copies
only the pointer and increments the count.

### 2.2 Drop — releasing ownership

When an `@[Rc] T` is dropped — either by going out of scope or by an explicit
`drop` — the reference count is decremented. If the count reaches zero, `T::drop` is
called and the backing memory is freed. If the count remains above zero, no visible action
occurs. This is the standard reference-counting destructor protocol.

### 2.3 Immutable borrow

Borrowing `@[Rc] T` as `&T` is always safe and does not affect the reference count.
Multiple simultaneous `&T` borrows to the same allocation are permitted:

```metel
let a: @[Rc] Node = @[Rc] Node { val: 1 };
let b = a.clone();
let r1: &Node = &a;
let r2: &Node = &b;   // both borrows valid simultaneously
```

### 2.4 Mutable borrow — the `uniq` scope

Borrowing `@[Rc] T` as `&mut T` (exclusive mutable borrow) is only valid within a
`uniq` scope (§3). Outside a `uniq` scope, `&mut @[Rc] T` is not permitted — the
compiler cannot prove at that point that no other owning reference exists.

---

## 3. The `uniq` scope

### 3.1 Syntax

`uniq` is a method on `@[Rc] T` that accepts a closure through the bracket channel:

```metel
a.uniq([ship]() -> {
    // ship: &mut T — exclusive mutable borrow of a's allocation
    ship.engine = Engine::Impulse { fuel: 100 };
});
```

The bracket parameter `ship` receives `&mut T`. Within the closure body, `a` is
temporarily consumed as a uniqueness witness; it is returned when the closure exits.
After the `uniq` call, `a` is again a valid `@[Rc] T`.

`uniq` does not change the reference count. It does not require the reference count to
equal one — it requires only that no other owning reference is *accessible in the current
scope*. Other `@[Rc] T` owners may exist in unreachable code or in functions that
were not called with an aliasing reference.

### 3.2 Alias analysis: what the compiler checks

When the compiler encounters `a.uniq([ship]() -> { body })`, it performs alias analysis
over the variables in scope at the call site. The analysis asks: **could any variable
accessible to `body` be an owning alias of the same `@[Rc] T` allocation as `a`?**

A variable `v` is considered a potential alias if:

1. **Direct alias**: `v` has type `@[Rc] T` — it is a direct owning reference of
   the same type.
2. **Transitive alias**: `v` has a type that contains `@[Rc] T` as a field,
   transitively — accessing `v` could yield an owning reference of the same type.
3. **Reference to alias**: `v` has type `&@[Rc] T` or `&mut @[Rc] T` — dereferencing
   it yields a potential alias.

The closure `body` must not access any such variable. If it does, the compiler emits a
type error at the point of access.

The closure *may* access:
- Variables of types that do not contain `@[Rc] T` (directly or transitively)
- `a` itself, through the exclusive `ship` parameter
- Owned `@[Heap] T` or region-allocated values of `T` — these have distinct tags and
  cannot alias `a`'s `Rc` allocation

```metel
let a: @[Rc] Spaceship = @[Rc] Spaceship { engine: Engine::StringTheory { ... } };
let b = a.clone();          // b: @[Rc] Spaceship — potential alias
let fuel: I32 = 100;        // I32 — no @[Rc] Spaceship, safe to access

a.uniq([ship]() -> {
    let _ = b;              // ERROR: b is @[Rc] Spaceship — potential alias of a
    ship.engine = Engine::Impulse { fuel };   // OK: fuel is I32; ship is the exclusive borrow
});
```

### 3.3 Function calls within `uniq`

A function called inside a `uniq` body is permitted if its signature does not accept a
`@[Rc] T` parameter or a parameter of a type containing `@[Rc] T`. The alias
analysis extends to call sites: if calling `f(x)` would pass a potential alias into `f`,
it is rejected.

```metel
a.uniq([ship]() -> {
    update_engine(ship);   // OK: update_engine takes &mut Engine, not @[Rc] Spaceship
    log_fuel(fuel);        // OK: log_fuel takes I32
    process(b);            // ERROR: process takes @[Rc] Spaceship — potential alias
});
```

### 3.4 The `uniq` scope and `Drop`

The `uniq` closure is a standard closure subject to the normal drop rules (RFC-0071 §5).
Any values dropped within the closure are dropped before the closure exits and `a` is
returned. The reference count is not affected by drops within the `uniq` scope — `a`
still holds one owning reference throughout.

---

## 4. Sendability — `Rc` vs `Arc`

`@[Rc] T` uses **non-atomic reference counting**. Incrementing or decrementing the
count is not thread-safe. Therefore:

```metel
// @[Rc] T: !Send — cannot cross fiber boundaries
// @[Rc] T: !Sync — cannot be shared across threads
```

The sendable complement is `Arc` — Atomic Reference Counted — which uses atomic
operations on the reference count and is sendable when `T: Send + Sync`:

```metel
impl Region for Arc {
    type AllocationError = !;
}

// @[Arc] T: Send when T: Send + Sync
// @[Arc] T: Sync when T: Send + Sync
```

`Arc` is deferred to a follow-up RFC. The two types are identical in interface and
differ only in the atomicity of the reference count operations and their `Send`/`Sync`
impls. Naming both here establishes the pair: `Rc` for single-fiber use, `Arc` for
cross-fiber shared ownership.

---

## 5. Interaction with existing regions

### 5.1 `@[Heap] T` — the unique-ownership counterpart

`@[Heap] T` and `@[Rc] T` are distinct region tags and cannot alias. An `@[Heap] T`
allocation is always uniquely owned; moving it does not create a second owner. A `uniq`
scope is never required for `@[Heap] T` because the type system already guarantees
exclusive access — there is always exactly one owner. `@[Arc] T` is similarly distinct
from both.

### 5.2 Region-allocated containers of shared values

`@[Rc] T` pointers may be stored in arena-allocated structures:

```metel
AutoRegion::scoped([r]() -> {
    let node = @[r] ListNode {
        value: @[Rc] HeavyData::load("data.bin"),
        next: null,
    };
    // node's arena slot is freed when r drops; the HeavyData's RC is decremented at that point
    // if this was the last owner, HeavyData::drop runs and the Rc allocation is freed
});
```

The arena slot holds an `@[Rc] HeavyData` value. When the region drops, the arena
slot is freed, decrementing the reference count. This composes correctly with `AutoRegion`
(which calls `Drop::drop` on tracked slots before bulk-freeing): the arena's drop of the
slot decrements the RC, and if the count hits zero, `HeavyData::drop` runs in the normal
way.

### 5.3 Struct-owned regions and shared values (RFC-0068)

A struct with `[own r]` may hold `@[Rc] T` fields. The struct's destructor drops the
owned region, which decrements the reference count of any `@[Rc] T` stored in the
arena — exactly as in §5.2.

---

## 6. Shape stability — a note on future relaxation

Ante's design distinguishes *shape-stable* types — structs with no enum fields — for
which multiple simultaneous mutable borrows are safe, because mutations to fields cannot
invalidate references held through sibling borrows. For shape-stable types, Ante relaxes
the single-`&mut` rule.

Metel does not currently adopt this relaxation. The `uniq` scope is the only path to
mutable access through `@[Rc] T`. This is conservative: even for shape-stable types,
the programmer must enter a `uniq` scope to mutate through a shared pointer.

A future RFC may introduce a `ShapeStable` marker aspect and relax the `uniq` requirement
for types implementing it, allowing multiple simultaneous `&mut T` borrows through
distinct `@[Rc] T` or `@[Arc] T` owners. This is deferred until the `uniq` scope
semantics are validated in practice.

---

## 7. The stdlib regions

| Type | Lifetime | Drop behaviour | Move-out | Sendable |
|---|---|---|---|---|
| `Heap` | Indefinite | `Drop::drop` when owner dropped | Always safe | Yes |
| `Arc` | Indefinite, atomic RC | `Drop::drop` when RC hits zero | Always safe | Yes (when `T: Send + Sync`) |
| `LocalHeap` | Indefinite, thread-local | `Drop::drop` when owner dropped | Always safe | No |
| `Rc` | Indefinite, non-atomic RC | `Drop::drop` when RC hits zero | Always safe | No |
| `BumpRegion` | Scoped, bump arena | Bulk free; no `Drop::drop` per slot | `T: !Drop` only | No |
| `AutoRegion` | Scoped, bump + drop list | Drop list then bulk free | Always safe | No |

---

## 8. Usage examples

### 8.1 Parent–child graph

```metel
struct Node {
    value: I32,
    children: @[Heap] List<@[Rc] Node>,
}

fun make_tree() -> @[Rc] Node {
    let leaf1 = @[Rc] Node { value: 1, children: @[Heap] List::Nil {} };
    let leaf2 = @[Rc] Node { value: 2, children: @[Heap] List::Nil {} };
    @[Rc] Node {
        value: 0,
        children: @[Heap] List::from([leaf1, leaf2]),
    }
}
```

Multiple `@[Rc] Node` owners may exist simultaneously. Each node is freed when its
last owner is dropped.

### 8.2 Safe variant replacement via `uniq`

```metel
effect Engine = StringTheory { core: @[Heap] Core } | Impulse { fuel: I32 }

let ship: @[Rc] Spaceship = @[Rc] Spaceship {
    engine: Engine::StringTheory { core: Core::new() },
};

ship.uniq([s]() -> {
    // Safe: within uniq, no other @[Rc] Spaceship is accessible
    // The old StringTheory variant (and its core) is dropped before the new variant is set
    s.engine = Engine::Impulse { fuel: 100 };
});
```

### 8.3 Shared cache entry

```metel
struct Cache {
    entries: @[Heap] Map<String, @[Rc] CacheEntry>,
}

impl Cache {
    fun get(self: &Cache, key: &String) -> Perhaps<@[Rc] CacheEntry> {
        self.entries.get(key).map(|e| e.clone())
        // caller receives a second owner; entry lives until both Cache and caller drop it
    }
}
```

### 8.4 `uniq` with function call

```metel
fun upgrade_engine(ship: &mut Spaceship, fuel: I32) {
    ship.engine = Engine::Impulse { fuel };
}

let ship: @[Rc] Spaceship = @[Rc] Spaceship { ... };

ship.uniq([s]() -> {
    upgrade_engine(s, 100);   // OK: upgrade_engine takes &mut Spaceship, not @[Rc] Spaceship
});
```

---

## Alternatives considered

### `Rc<RefCell<T>>` as a library type

The standard alternative in languages without native shared mutability. `RefCell<T>` (or
equivalent) provides runtime borrow checking — `borrow_mut()` succeeds if no other borrow
is active, and panics otherwise. This requires neither new syntax nor new type-system
rules.

Rejected because: the panic is not statically preventable. A function that calls
`borrow_mut()` and could panic cannot be distinguished in its type from one that cannot.
The `uniq` scope makes the panic statically impossible: the compiler rejects programs that
would panic at the equivalent runtime check.

### Require `RC == 1` at runtime before entering `uniq`

A weaker alternative: `uniq` checks the reference count at runtime and panics if it is
not 1. Syntactically identical to the static version but with a runtime cost and a
possible crash.

Rejected for the same reason as `RefCell`: the crash is not statically preventable.
The static alias analysis is strictly better and has zero runtime cost.

### A single unified `Heap` region with optional sharing

Rather than separate `Rc` and `Arc` region kinds, `@[Heap] T` could carry a flag
indicating whether it is uniquely or reference-counted owned. Unique heap pointers and
shared heap pointers would have the same type, differentiated by a runtime flag.

Rejected because: the ownership mode is a compile-time property and encodes different
static guarantees. Collapsing them into one type erases the distinction the type system
uses to reason about aliasing. The `uniq` scope, which relies on the alias analysis over
`@[Rc] T` tags, would not be expressible.

---

## Unresolved questions

1. **Cycle handling.** Reference counting cannot free cyclic structures — two `@[Rc] T`
   values that reference each other will never reach a count of zero and will leak. The
   same applies to `@[Arc] T`. Options: weak references (`@[Weak] T` and `@[WeakArc] T`,
   non-owning references that yield `Perhaps<@[Rc] T>` / `Perhaps<@[Arc] T>`), a cycle
   collector run alongside RC, or a language-level prohibition on `@[Rc] T` / `@[Arc] T`
   cycles enforced by the type system. Deferred — cycle detection is a substantial
   addition and the right answer depends on observed usage patterns.

2. **`Arc` — atomic RC for cross-fiber sharing.** `@[Rc] T` is non-atomic and
   non-sendable. `Arc` uses atomic reference counting and is sendable when `T: Send +
   Sync`. Named in this RFC; full design (including interaction with `uniq` across fiber
   boundaries) deferred to a follow-up RFC.

3. **Shape-stability relaxation.** As noted in §6, shape-stable types could be exempted
   from the `uniq` requirement for mutation. Deferred until `uniq` scopes are validated in
   practice and the shape-stability boundary is well understood.

4. **Alias analysis across module boundaries.** The `uniq` alias analysis must reason
   about types defined in other modules. If a foreign type's fields are not visible
   (private fields), the compiler must conservatively assume it may contain `@[Rc] T`.
   Whether this conservatism is acceptable in practice, or whether a visibility-aware
   analysis is needed, is deferred to the implementation RFC.

5. **`uniq` and `uniq` nesting.** Whether a `uniq` scope may be nested inside another
   `uniq` scope for a different type — or the same type accessed through a field — is
   unspecified. The naive rule (each `uniq` scope independently applies its alias analysis)
   appears sound; formal verification is deferred.

---

## References

- RFC-0063 (Region Handles) — region allocator interface; `@[r] expr`; sendability rules;
  the `Region` aspect that `Rc` and `Arc` implement.
- RFC-0065 (Region Ergonomics) — `@`-position elision; call-site inference; both apply to
  `@[Rc] T` and `@[Arc] T` identically.
- RFC-0066 (Region Pointer Extraction) — move-out semantics; `@[Rc] T` and `@[Arc] T`
  move-out is always safe (no `T: !Drop` restriction; RC decrement handles cleanup).
- RFC-0071 (Ownership and Move Semantics) — non-`Copy` move semantics; `Drop` protocol;
  drop ordering; `@[Rc] T` and `@[Arc] T` are non-`Copy` by construction.
- RFC-0072 (Negative Bounds) — `T: !Drop`; not required for `@[Rc] T` or `@[Arc] T`
  move-out.
- Ante programming language — Léo Stefanesco and Evan Ovadia, "Blending Borrowing and
  Reference Counting" — the `uniq` scope and compile-time alias analysis for safe mutation
  of shared values, which this RFC adapts to Metel's region tag model.
