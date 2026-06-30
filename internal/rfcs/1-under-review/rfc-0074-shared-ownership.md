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

One ownership pattern is absent: **shared heap ownership** — multiple owning pointers to
the same allocation, with the allocation freed when the last owner drops. This is
reference-counted ownership: cloning a pointer increments a counter; dropping it
decrements the counter; the allocation is freed and the destructor is called when the
counter reaches zero.

This RFC introduces shared ownership without treating it as a special case. One general
extension to the existing system is required:

**`SharedRegion`** — a supertrait of `Region` for type-level region tags that carry
reference-counted lifetime semantics. Any tag implementing `SharedRegion` gets `Clone`
and `Drop` automatically. The mechanism is available to user-defined regions, not only
to stdlib types.

`Rc` and `Arc` are two stdlib type tags that implement `SharedRegion`. They differ in
one critical dimension: sendability.

- **`Rc`** is non-atomic and non-sendable. All clones are confined to the same fiber.
  This enables the `unique` keyword (§2), which performs compile-time binding-level
  alias analysis to provide static exclusive mutable access.
- **`Arc`** is atomic and sendable. Clones may exist in other fibers beyond the
  compiler's view. Compile-time `unique` is therefore unsound for `Arc`; instead,
  `Arc` exposes `get_mut` (§4.1), a runtime-checked API that returns `Option<&mut T>`.

---

## Motivation

### The shared ownership gap

RFC-0063 establishes `@[Heap] T` as Metel's uniquely-owned heap pointer. Unique
ownership does not cover every data structure. A doubly-linked list node needs a
reference to both neighbours; a tree node may need a reference to its parent; a shared
cache entry may be referenced by multiple consumers with unpredictable lifetimes. In
all of these cases, the allocation should live as long as at least one owner keeps it
alive — the defining property of reference counting.

### The mutation hazard and its two solutions

Naive shared mutable access is unsafe. Consider two owning pointers `a` and `b` to the
same `Engine` value. If `a` is used to match on the current variant and extract a
reference to its field, while `b` is used to replace the variant, the replacement
destroys the field while the reference derived from `a` is still live — a use-after-free.

The two stdlib shared-ownership types solve this differently, matching their aliasing
models:

- **`Rc`**: All clones are local to one fiber and visible to the compiler. The `unique`
  keyword performs a static alias analysis and rejects programs where a known clone
  would be accessible during mutation. No runtime cost; no possible panic.
- **`Arc`**: Clones may exist in other fibers. The compiler cannot enumerate all live
  aliases. The `get_mut` method checks `strong_count() == 1` at runtime and returns
  `None` if other aliases exist. The caller handles the failure.

### Why not introduce Rc/Arc as exceptions

Introducing `Rc` and `Arc` as region types with special language rules would treat
symptoms rather than extending the system. The `SharedRegion` supertrait is general:
any user-defined RC-style region (pool-managed RC, arena-backed RC with a shared
control block) gets `Clone` and `Drop` for free. If the region is non-sendable, it also
gets the `unique` keyword.

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
   count of the underlying allocation and returns a second owning pointer to the same
   allocation. This is O(1) and does not copy `T`.

2. **`Drop`**: `@[R] T` implements `Drop`. Dropping a pointer decrements the reference
   count. If the count reaches zero, `T::drop` is called and the backing memory is freed.

`Clone` and `Drop` are derived automatically by the compiler for any `R: SharedRegion`;
no `impl Clone for @[R] T` or `impl Drop for @[R] T` is written by hand.

The `unique` keyword is **not** a property of `SharedRegion` alone. It additionally
requires `R: !Send` — see §2.

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
RFC-0063 §4: `@[R] T` is sendable iff `R: Send`. `SharedRegion` introduces no new
sendability rules.

---

## 2. The `unique` keyword

`unique` is a compiler keyword that provides exclusive mutable access to a
shared-region pointer. It requires `R: SharedRegion + !Send`.

The `!Send` requirement is not incidental — it is the soundness condition. When
`R: !Send`, no clone of `@[R] T` can cross a fiber boundary. Every live alias is in
the current fiber's scope and is visible to the compiler's alias analysis. If `R: Send`,
clones may exist in other fibers beyond the compiler's view, and compile-time alias
exclusion cannot be guaranteed. `Arc` therefore does not support `unique`; see §4.1.

### Alias analysis

The safety guarantee of `unique` rests on a **binding-level alias analysis** performed
by the compiler:

- The pointer operand `a` is **consumed** by the `unique` expression and is not
  accessible inside the block as `@[R] T`.
- The compiler tracks which other in-scope bindings are **known clones** of `a` —
  bindings derived from `a` through `.clone()` calls, transitively. These are excluded
  from the block.
- Bindings of the same type `@[R] T` that were **independently allocated** (not derived
  from `a`) are unrelated and may be freely used inside the block.

`unique` does not assert or check that the reference count equals one at runtime — the
alias analysis is a static, compile-time guarantee. No runtime overhead; no possible
crash.

### 2.1 Form A — explicit block with explicit binding

```metel
unique a as s {
    s.engine = Engine::Impulse { fuel: 100 };
}
```

`a` is consumed; inside the block, `s` is bound as `&mut T`. The alias analysis checks
that no known clone of `a` is referenced inside the block.

### 2.2 Form B — explicit block with implicit rebinding

```metel
unique a {
    a.engine = Engine::Impulse { fuel: 100 };
}
```

Equivalent to form A with the binding name equal to `a`. Inside the block, `a` is
rebound as `&mut T` for the duration of the block.

### 2.3 Form C — binding without explicit block *(deferred)*

```metel
let s = unique a;
s.engine = Engine::Impulse { fuel: 100 };
```

`unique a` produces a `&mut T` whose scope is determined by the borrow checker. This
form requires continuation capture and is deferred to a follow-up RFC. Forms A and B
cover the common cases without it.

---

## 3. `Rc` — non-atomic shared ownership

`Rc` implements `SharedRegion` with **non-atomic** reference counting:

```metel
impl Region for Rc {
    type AllocationError = !;
}

impl SharedRegion for Rc {}
```

The reference count is a plain integer; incrementing and decrementing it is not
thread-safe. `Rc` therefore does not implement `Send` or `Sync`:

```metel
// Rc: !Send — @[Rc] T cannot cross fiber boundaries
// Rc: !Sync — @[Rc] T cannot be shared across threads simultaneously
```

`Rc: !Send` is what makes the `unique` keyword applicable to `@[Rc] T`. Because no
clone can leave the current fiber, the compiler's scope-level alias analysis is
exhaustive.

---

## 4. `Arc` — atomic shared ownership

`Arc` implements `SharedRegion` with **atomic** reference counting:

```metel
impl Region for Arc {
    type AllocationError = !;
}

impl SharedRegion for Arc {}
impl Send for Arc {}
impl Sync for Arc {}
```

Sendability of `@[Arc] T` follows the standard rule: `@[Arc] T: Send` iff `Arc: Send`
and `T: Send + Sync`.

`Arc: Send` means clones may exist in other fibers. The compiler cannot enumerate all
live aliases at any given point, so compile-time `unique` is unsound for `@[Arc] T`.
`Arc` does not satisfy the `R: !Send` precondition of the `unique` keyword; attempting
`unique` on `@[Arc] T` is a type error.

### 4.1 `get_mut` — runtime-checked exclusive access

`Arc` exposes exclusive mutable access through a runtime check:

```metel
fun get_mut[s](self: &mut [s] @[Arc] T) -> Option<&mut [s] T>
```

`get_mut` checks `strong_count() == 1` atomically. If the count is one, no other owner
exists and a mutable reference is returned. If the count is greater than one, `None` is
returned and the caller handles the failure.

```metel
let counter: @[Arc] Counter = @[Arc] Counter::new(0);

match counter.get_mut() {
    Some(c) => c.increment(),
    None    => { /* other owners exist; handle accordingly */ }
}
```

The caller must hold a `&mut @[Arc] T` to call `get_mut` — the standard borrow rule
prevents concurrent borrows of the outer pointer, ensuring the count check and the
resulting `&mut T` are used safely within a single fiber.

### 4.2 `Arc` vs. `Rc` comparison

| | `Rc` | `Arc` |
|---|---|---|
| RC operations | Non-atomic | Atomic |
| `Send` | No | Yes (when `T: Send + Sync`) |
| Per-clone cost | One integer increment | One atomic increment |
| Exclusive access | `unique` — static, no cost | `get_mut` — runtime, returns `Option` |
| Use case | Single-fiber shared ownership | Cross-fiber shared ownership |

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
let b: @[Rc] Node = @[Rc] Node { val: 2 };   // independent allocation

unique a as node {
    node.val = b.val;   // OK: b was not derived from a
}
```

### 6.4 `unique` with a called function

```metel
fun upgrade_engine(ship: &mut Spaceship, fuel: I32) {
    ship.engine = Engine::Impulse { fuel };
}

let ship: @[Rc] Spaceship = @[Rc] Spaceship { ... };

unique ship as s {
    upgrade_engine(s, 100);
}
```

`upgrade_engine` receives `&mut Spaceship`, not `@[Rc] Spaceship`. The `unique` block
converts the shared pointer to an exclusive borrow before calling out.

### 6.5 `Arc` with `get_mut`

```metel
let config: @[Arc] Config = @[Arc] Config::default();

// ... config cloned and shared across fibers ...
// ... all clones dropped ...

match config.get_mut() {
    Some(cfg) => cfg.update(new_settings),
    None      => panic("unexpected Arc alias during reconfiguration"),
}
```

`get_mut` is the correct tool for `Arc` when exclusive access is needed and the
program's logic guarantees uniqueness at a certain point — but cannot prove it
statically. The `Option` return forces the caller to handle the aliased case.

---

## Alternatives considered

### Compile-time `unique` for `Arc`

The compile-time binding-level alias analysis that makes `unique` sound for `Rc` does
not extend to `Arc`. When a clone of `@[Arc] T` is sent to another fiber, it leaves
the compiler's scope — the clone is no longer a live binding in the current fiber, so
the alias analysis sees no known aliases and would permit `unique`. But the clone is
still alive in the other fiber, pointing to the same allocation. Two simultaneous
`&mut T` borrows would result: a data race.

The `!Send` precondition on `unique` is exactly the condition that closes this gap. It
cannot be relaxed without replacing scope-level analysis with something that can reason
across fiber boundaries.

Static `unique` for `Arc` would require structured fork-join concurrency (RFC-0064)
with an additional branch non-escape condition: every `Arc` clone moved into a fork
branch must be provably consumed within that branch and must not escape through
channels, return values, or shared heap state that outlives the join. After the join,
the compiler can prove all forked clones are dropped. This is a meaningful future
direction but depends on RFC-0064 being finalised and introduces significant additional
machinery. It is not part of this RFC.

### Runtime alias check for `unique` on `Rc`

`unique` on `Rc` could check `RC == 1` at runtime and panic if not. This is Rust's
`Rc::get_mut` approach. It works but cannot be statically prevented from panicking.
The binding-level alias analysis makes the check static: the compiler rejects programs
where a known alias would be accessible during mutation. No runtime overhead; no
possible crash. `Rc`'s `!Send` property makes this static approach sound.

### `get_mut` for `Rc`

`Rc` could expose only `get_mut` (like `Arc`) rather than the `unique` keyword. This
unifies the API surface but discards the static guarantee that `Rc`'s non-sendability
enables. A runtime check that could never actually fail (because `Rc: !Send` means the
program structure is what controls all aliases, and the programmer already knows the
count) is pure overhead. The `unique` keyword exists precisely to exploit the static
guarantee.

### Closure-based `unique` with a type-level alias bound

An earlier design expressed `unique` as a static method accepting a closure, with a
type-level bound to exclude aliases. This design has two problems: the bound cannot be
expressed precisely at the type level because it requires distinguishing aliases of a
specific binding from unrelated pointers of the same type; and even an approximation
may not be well-formed if region tags are not type constructors. The binding-level
analysis in the keyword form correctly excludes only known clones of the specific
pointer being mutated, without any type-level machinery.

### `Rc<T>` as a library struct (not a region tag)

`Rc<T>` could be a plain struct containing `@[Heap] T` plus a reference count. This
fits the existing system but requires a runtime borrow check for mutation — the same
situation as `Rc<RefCell<T>>` in Rust. The region tag approach enables the static
`unique` keyword analysis; the struct approach cannot.

---

## Unresolved questions

1. **Cycle handling.** Reference counting cannot free cyclic structures. Options: weak
   pointers (a non-owning `@[WeakRc] T` that yields `Perhaps<@[Rc] T>`, implementing
   a `WeakSharedRegion` aspect); a cycle collector; a type-system prohibition on cycles.
   Deferred — the right answer depends on observed usage patterns.

2. **Precision of the alias analysis.** The current analysis excludes only bindings
   derived from `a` via `.clone()` calls. A more sophisticated analysis based on
   data-flow or escape analysis could handle aliases introduced through function calls
   or field projections. The conservative clone-tracking approach is sound; the extent
   to which it can be made more precise is an implementation question. Deferred.

3. **`unique` nesting.** Whether a `unique` block may open a second `unique` block on
   a different `@[R] U` (for `U ≠ T`) is unspecified. The naive rule — each `unique`
   block independently performs its own alias analysis — appears sound; formal
   verification deferred.

4. **Form C (deferred).** The continuation-capture mechanism required for
   `let s = unique a;` is unspecified. Deferred to a follow-up RFC.

5. **Static `unique` for `Arc` via structured concurrency.** If RFC-0064 introduces
   strict fork-join with branch non-escape conditions for `Arc` clones, static `unique`
   on `Arc` after a join point becomes statically sound. The design and the required
   interaction between RFC-0064 and this RFC are deferred to RFC-0064.

---

## References

- RFC-0063 (Region Handles) — region allocator interface; the `Region` aspect that
  `SharedRegion` extends; sendability rule (`@[R] T: Send iff R: Send`) that determines
  `Rc` and `Arc` sendability.
- RFC-0065 (Region Ergonomics) — `@`-position elision and call-site inference apply to
  `@[Rc] T` and `@[Arc] T` identically to any other region tag.
- RFC-0066 (Region Pointer Extraction) — move-out semantics; `@[Rc] T` and `@[Arc] T`
  move-out is always safe (RC decrement handles cleanup).
- RFC-0071 (Ownership and Move Semantics) — `Clone` and `Drop` aspects; `Copy`/`Drop`
  mutual exclusion means neither `@[Rc] T` nor `@[Arc] T` is `Copy`.
- RFC-0072 (Negative Bounds) — `T: !Send`; the precondition that makes `unique`
  statically sound, applied here as `R: !Send` on the region tag.
- RFC-0064 (Fork-Join Parallelism) — future work; structured concurrency with branch
  non-escape conditions may eventually enable static `unique` for `Arc`.
- Ante programming language — the compile-time alias exclusion concept for non-sendable
  shared pointers, adapted here as the `unique` keyword. Ante's shared pointer (`Ref`)
  is non-sendable; the extension to sendable `Arc` via `get_mut` is Metel-specific.
