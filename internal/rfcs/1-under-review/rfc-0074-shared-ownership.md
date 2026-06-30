---
id: rfc-0074
title: "Shared Ownership — SharedRegion, Rc, and Arc"
date: '2026-06-30'
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

One ownership pattern is absent: **shared heap ownership** — multiple owning pointers
to the same allocation, with the allocation freed when the last owner drops.

This RFC introduces shared ownership without treating it as a special case. One general
extension is required:

**`SharedRegion`** — a supertrait of `Region` for type-level region tags that carry
reference-counted lifetime semantics. Any tag implementing `SharedRegion` gets `Clone`
and `Drop` automatically, and exposes `get_mut` for runtime-checked exclusive mutable
access. The mechanism is available to user-defined regions, not only to stdlib types.

`Rc` and `Arc` are the two stdlib type tags that implement `SharedRegion`. They differ
in one dimension: `Rc` uses non-atomic reference counting and is non-sendable; `Arc`
uses atomic reference counting and is sendable when `T: Send + Sync`.

---

## Motivation

### The shared ownership gap

RFC-0063 establishes `@[Heap] T` as Metel's uniquely-owned heap pointer. Unique
ownership does not cover every data structure. A doubly-linked list node needs a
reference to both neighbours; a tree node may need a reference to its parent; a shared
cache entry may be referenced by multiple consumers with unpredictable lifetimes. In
all of these cases the allocation should live as long as at least one owner keeps it
alive — the defining property of reference counting.

### The mutation hazard

Naive shared mutable access is unsafe. Consider two owning pointers `a` and `b` to the
same `Engine` value. If `a` is used to match on the current variant and extract a
reference to its field, while `b` is used to replace the variant, the replacement
destroys the field while the reference derived from `a` is still live — a use-after-free.

The safe approach is to verify, at the moment mutation is attempted, that no other
owner exists. This RFC provides `get_mut` — a runtime check that returns
`Option<&mut T>`. If the reference count is exactly one, no other owner exists and
exclusive mutable access is safe. Otherwise `None` is returned and the caller handles
the failure.

Purely static exclusive access — establishing at compile time that no live alias exists
— is a goal for future work and is discussed in §Future work.

### Why not introduce Rc/Arc as exceptions

Introducing `Rc` and `Arc` as region types with special language rules would treat
symptoms rather than extending the system. The `SharedRegion` supertrait is general:
any user-defined RC-style region (pool-managed RC, arena-backed RC with a shared
control block) gets `Clone`, `Drop`, and `get_mut` for free.

---

## 1. The `SharedRegion` aspect

```metel
aspect SharedRegion: Region {
    type AllocationError = !;
}
```

`SharedRegion` is a supertrait of `Region`. Types implementing it are **type-level
region tags** whose pointers carry reference-counted lifetimes.

Implementing `SharedRegion` on a tag type `R` declares two things:

1. **`Clone`**: `@[R] T` implements `Clone`. Cloning a pointer increments the reference
   count and returns a second owning pointer to the same allocation. This is O(1) and
   does not copy `T`.

2. **`Drop`**: `@[R] T` implements `Drop`. Dropping a pointer decrements the reference
   count. If the count reaches zero, `T::drop` is called and the backing memory is freed.

`Clone` and `Drop` are derived automatically by the compiler for any `R: SharedRegion`.

### 1.1 Allocation

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

### 1.3 `get_mut` — runtime-checked exclusive access

`SharedRegion` pointers expose exclusive mutable access through a runtime check:

```metel
fun get_mut[s](self: &mut [s] @[R] T) -> Option<&mut [s] T>
```

`get_mut` checks `strong_count() == 1`. If the count is one, no other owner exists and
a mutable reference is returned. Otherwise `None` is returned.

The caller must hold `&mut @[R] T` to call `get_mut`. This prevents concurrent borrows
of the outer pointer within the same fiber.

```metel
let node: @[Rc] Node = @[Rc] Node { val: 1 };

match node.get_mut() {
    Some(n) => n.val = 42,
    None    => { /* other owners exist */ }
}
```

### 1.4 Sendability

The sendability of `@[R] T` follows the existing rule from RFC-0063 §4: `@[R] T` is
sendable iff `R: Send`. `SharedRegion` introduces no new sendability rules.

---

## 2. `Rc` — non-atomic shared ownership

`Rc` implements `SharedRegion` with non-atomic reference counting:

```metel
impl Region for Rc {
    type AllocationError = !;
}

impl SharedRegion for Rc {}
```

The reference count is a plain integer; incrementing and decrementing it is not
thread-safe. `Rc` does not implement `Send` or `Sync`:

```metel
// Rc: !Send — @[Rc] T cannot cross fiber boundaries
// Rc: !Sync — @[Rc] T cannot be shared across threads simultaneously
```

`get_mut` on `@[Rc] T` checks the non-atomic integer count.

---

## 3. `Arc` — atomic shared ownership

`Arc` implements `SharedRegion` with atomic reference counting:

```metel
impl Region for Arc {
    type AllocationError = !;
}

impl SharedRegion for Arc {}
impl Send for Arc {}
impl Sync for Arc {}
```

Sendability of `@[Arc] T`: `@[Arc] T: Send` iff `T: Send + Sync`.

`get_mut` on `@[Arc] T` checks the atomic count. The check is inherently racy in the
presence of concurrent clones; `get_mut` requires `&mut @[Arc] T`, which prevents
concurrent access to the outer pointer within the same fiber, making the check sound.

| | `Rc` | `Arc` |
|---|---|---|
| RC operations | Non-atomic | Atomic |
| `Send` | No | Yes (when `T: Send + Sync`) |
| Per-clone cost | One integer increment | One atomic increment |
| Exclusive access | `get_mut` — runtime `Option` | `get_mut` — runtime `Option` |
| Use case | Single-fiber shared ownership | Cross-fiber shared ownership |

---

## 4. The six stdlib regions

| Type | Lifetime | Drop behaviour | Move-out | Sendable |
|---|---|---|---|---|
| `Heap` | Indefinite | `Drop::drop` when owner dropped | Always safe | Yes |
| `Arc` | Indefinite, atomic RC | `Drop::drop` when RC hits zero | Always safe | Yes (when `T: Send + Sync`) |
| `LocalHeap` | Indefinite, thread-local | `Drop::drop` when owner dropped | Always safe | No |
| `Rc` | Indefinite, non-atomic RC | `Drop::drop` when RC hits zero | Always safe | No |
| `BumpRegion` | Scoped, bump arena | Bulk free; no `Drop::drop` per slot | `T: !Drop` only | No |
| `AutoRegion` | Scoped, compiler-managed | Compiler-managed drop | Always safe | No |

---

## 5. Usage examples

### 5.1 Parent–child graph

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

### 5.2 Safe mutation via `get_mut`

```metel
enum Engine { StringTheory { core: @[Heap] Core }, Impulse { fuel: I32 } }

let ship: @[Rc] Spaceship = @[Rc] Spaceship { engine: Engine::StringTheory { ... } };

match ship.get_mut() {
    Some(s) => s.engine = Engine::Impulse { fuel: 100 },
    None    => panic("unexpected alias"),
}
```

### 5.3 Shared state with `Arc`

```metel
let config: @[Arc] Config = @[Arc] Config::default();
let config2 = config.clone();

// config2 sent to another fiber ...

// after all other owners are dropped:
match config.get_mut() {
    Some(cfg) => cfg.update(new_settings),
    None      => { /* still shared */ }
}
```

---

## 6. Future work — static exclusive access

The `get_mut` approach is always sound but imposes a runtime check and forces the
caller to handle the `None` case even when the program structure guarantees uniqueness.
A purely static mechanism — establishing at compile time that no live alias exists —
is desirable when it can be made formally sound.

Two open design threads:

### 6.1 `unique` keyword for `Rc`

Because `Rc: !Send`, all clones of `@[Rc] T` are confined to the same fiber. A
compiler-level alias analysis operating on binding provenance — tracking which
in-scope bindings were derived from a specific `@[Rc] T` via `.clone()` — could
establish statically that no accessible alias exists, and admit a `unique` block that
provides `&mut T` without a runtime check.

This analysis is sound for the cases it can track: clones that are direct bindings in
scope, and clones captured by closures with explicit capture-list types (RFC-0050).
It is not sound in the general case. A clone moved into a data structure accessible
from inside the block represents an alias the binding-level analysis cannot see; the
standard borrow checker does not catch this because it does not know the two paths
alias the same allocation. The full solution requires type-level allocation identity —
brand types (RFC-0076) — to make same-allocation relationships visible to the type
checker.

Until the interaction between binding-level alias analysis, explicit closure capture
lists (RFC-0050), and brand types (RFC-0076) is fully worked out, a statically sound
`unique` construct cannot be specified. This is deferred.

### 6.2 Static `unique` for `Arc` via structured concurrency

For `Arc`, the binding-level analysis is additionally unsound because `Arc: Send` —
clones can cross fiber boundaries and exist outside the compiler's view. Static
`unique` for `Arc` would require structured fork-join concurrency (RFC-0064) with a
branch non-escape condition: every `Arc` clone moved into a fork branch must be
provably consumed within that branch and must not escape through channels or shared
state that outlives the join. After the join point, the compiler could prove all
forked clones are dropped. This is a further future direction, contingent on both
RFC-0064 and the `Rc` static analysis being resolved first.

---

## Alternatives considered

### Static `unique` keyword now

Introducing a `unique` keyword with binding-level alias analysis in this RFC was
considered and rejected. The analysis is not formally sound in the general case: a
clone moved into a data structure accessible from inside the `unique` block creates an
alias that the binding-level analysis cannot see and the standard borrow checker cannot
detect. Presenting an unsound construct as a safety guarantee is worse than the
runtime check. The path to a sound static mechanism is clear (§6), but it depends on
RFC-0050 and RFC-0076, neither of which is accepted.

### `get_mut` only for `Arc`, `unique` only for `Rc`

An earlier version of this RFC proposed `unique` for `Rc` and `get_mut` only for
`Arc`, based on the observation that `Rc: !Send` confines all clones to one fiber.
This was rejected for the reason above: confinement to one fiber is necessary but not
sufficient for a sound static analysis. Clones stored in data structures accessible
from inside the block still escape the analysis. Soundness requires either RFC-0050
and RFC-0076, or restricting `unique` so severely that it becomes impractical.

### `Rc<T>` as a library struct (not a region tag)

`Rc<T>` could be a plain struct containing `@[Heap] T` plus a reference count, with
`Deref` for read access and a `borrow_mut`-style method for guarded write access. This
fits the existing system completely but requires a runtime borrow check for mutation —
the same situation as `Rc<RefCell<T>>` in Rust, with all the accompanying panic risk.
The region tag approach keeps the interface uniform and leaves room for the static
analysis in §6 to be added later without changing the type.

---

## Unresolved questions

1. **Cycle handling.** Reference counting cannot free cyclic structures. Options: weak
   pointers (a non-owning pointer yielding `Perhaps<@[Rc] T>`, via a `WeakSharedRegion`
   aspect); a cycle collector; a type-system prohibition on cycles. Deferred.

2. **Static `unique` for `Rc`.** Contingent on RFC-0050 (explicit closure capture
   lists) and RFC-0076 (brand types). The design sketch is in §6.1; formal
   specification is deferred to a follow-up RFC once those dependencies are accepted.

3. **Static `unique` for `Arc`.** Contingent on §6.1 being resolved and RFC-0064
   (structured fork-join parallelism) being accepted. Deferred.

---

## References

- RFC-0063 (Region Handles) — region allocator interface; the `Region` aspect that
  `SharedRegion` extends; sendability rule that determines `Rc` and `Arc` sendability.
- RFC-0065 (Region Ergonomics) — elision and inference apply to `@[Rc] T` and
  `@[Arc] T` identically to any other region tag.
- RFC-0066 (Region Pointer Extraction) — move-out semantics; always safe for `Rc`
  and `Arc` (RC decrement handles cleanup).
- RFC-0071 (Ownership and Move Semantics) — `Clone` and `Drop`; `Copy`/`Drop` mutual
  exclusion means neither `@[Rc] T` nor `@[Arc] T` is `Copy`.
- RFC-0072 (Negative Bounds) — `Rc: !Send`; used in §6.1 as the necessary condition
  for the future static analysis.
- RFC-0050 (Closure Capture Lists) — prerequisite for static `unique` (§6.1); explicit
  capture types make closure-captured clones visible to alias analysis.
- RFC-0076 (Brand Types) — prerequisite for static `unique` (§6.1); allocation
  identity at the type level is required for the analysis to be formally sound.
- RFC-0064 (Fork-Join Parallelism) — prerequisite for static `unique` on `Arc` (§6.2).
- Ante programming language — the compile-time alias exclusion concept for shared
  pointers that inspired the `unique` direction in §6.
