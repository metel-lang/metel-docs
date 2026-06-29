---
id: rfc-0074
title: "Shared Ownership — SharedRegion, NotCapturing, Rc, and Arc"
date: '2026-06-29'
---

> **Status — under review.** Depends on RFC-0063 (Region Handles), RFC-0050 (Closure
> Capture Lists), RFC-0065 (Region Ergonomics), RFC-0066 (Region Pointer Extraction),
> RFC-0071 (Ownership and Move Semantics), and RFC-0072 (Negative Bounds). Introduces
> two general extensions to the existing system — the `SharedRegion` aspect and the
> `NotCapturing<T>` closure bound — and defines `Rc` and `Arc` as the two stdlib types
> that implement them.

## Summary

The four existing stdlib regions cover four distinct allocation strategies:

| Type | Lifetime | Move-out | Sendable |
|---|---|---|---|
| `Heap` | Indefinite | Always safe | Yes |
| `LocalHeap` | Indefinite, thread-local | Always safe | No |
| `BumpRegion` | Scoped, bump arena | `T: !Drop` only | No |
| `AutoRegion` | Scoped, bump + drop list | Always safe | No |

One ownership pattern is absent: **shared heap ownership** — multiple owning pointers to
the same allocation, with the allocation freed when the last owner drops. This is
reference-counted ownership: cloning a pointer increments a counter; dropping it
decrements the counter; the allocation is freed and the destructor is called when the
counter reaches zero.

This RFC introduces shared ownership without treating it as a special case. Two general
extensions to the existing system are required:

1. **`SharedRegion`** — a supertrait of `Region` for type-level region tags that carry
   reference-counted lifetime semantics. Any tag implementing `SharedRegion` gets
   `Clone`, `Drop`, and the `unique` method automatically. The mechanism is available to
   user-defined regions, not only to stdlib types.

2. **`NotCapturing<T>`** — a general closure-type bound that asserts a closure does not
   close over any variable of type `T`, or any type that transitively contains `T`. It is
   a marker aspect implemented by closure types; the compiler infers it from the capture
   set. Like `Send` and `Sync`, it is a property the type system tracks rather than a
   piece of syntax the programmer writes.

`Rc` and `Arc` are then two stdlib type tags that implement `SharedRegion`. No language
rules specific to `Rc` or `Arc` are introduced; everything they provide falls out of the
two general extensions above.

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
at compile time using the `unique` method, which uses the `NotCapturing<T>` bound to prove
statically that no other owning pointer is accessible during the mutation.

### Why not introduce Rc/Arc as exceptions

Introducing `Rc` and `Arc` as region types with special language rules — a non-cloneable
region handle that suddenly becomes cloneable, a new `unique` syntax, a new alias-analysis
pass — would be treating symptoms rather than extending the system. The two mechanisms
introduced here (`SharedRegion` and `NotCapturing<T>`) are general: any user-defined
region can implement `SharedRegion` and receive `unique` for free; any higher-order
function can express "this closure must not close over type T" using `NotCapturing<T>`
independently of regions altogether.

---

## 1. The `SharedRegion` aspect

```metel
aspect SharedRegion: Region {
    type AllocationError = !;

    fun unique<T, U, F>(self: @[Self] T, f: F) -> U
        where F: fun(&mut T) -> U,
              F: NotCapturing<@[Self] T>;
}
```

`SharedRegion` is a supertrait of `Region`. Types implementing it are **type-level region
tags** (like `Heap` and `LocalHeap`, as opposed to binding-level tags like the `r` in a
`BumpRegion::scoped` scope) whose pointers carry reference-counted lifetimes.

The aspect uses `@[Self] T` as the receiver type of `unique`, where `Self` is the
implementing tag (e.g., `Rc` or `Arc`). This requires the aspect system to support
arbitrary self types — receivers that are not `Self` directly but are a type parameterised
by `Self`. Metel's region pointer `@[R] T` is the natural vehicle for this: the method
belongs on the pointer type, not on the bare tag.

Implementing `SharedRegion` on a tag type `R` declares three things:

1. **`Clone`**: `@[R] T` implements `Clone`. Cloning a pointer increments the reference
   count of the underlying allocation and returns a second owning pointer to the same
   allocation. This is O(1) and does not copy `T`.

2. **`Drop`**: `@[R] T` implements `Drop`. Dropping a pointer decrements the reference
   count. If the count reaches zero, `T::drop` is called and the backing memory is freed.

3. **`unique`**: `@[R] T` gains the `unique` method (§2), declared in the aspect and
   provided by the implementing tag. The method gives exclusive mutable access under a
   `NotCapturing` bound.

`Clone` and `Drop` are derived automatically by the compiler for any `R: SharedRegion`;
no `impl Clone for @[R] T` or `impl Drop for @[R] T` is written by hand. `unique` is
declared in the aspect body; the compiler provides the canonical implementation for all
`R: SharedRegion` since the behaviour is determined entirely by the RC semantics and the
`NotCapturing` bound. An implementor may provide their own `unique` if the RC strategy
differs (e.g., a pool-managed region with a distinct control block).

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

## 2. The `unique` method

`unique` is declared in the `SharedRegion` aspect and available on all `@[R] T` where
`R: SharedRegion`:

```metel
fun unique<T, U, F>(self: @[Self] T, f: F) -> U
    where F: fun(&mut T) -> U,
          F: NotCapturing<@[Self] T>
```

`unique` takes a closure that receives an exclusive mutable borrow of the allocation and
returns a result. Within the closure, `self` is accessible as `&mut T`. The
`NotCapturing<@[Self] T>` bound (§3) ensures that no other pointer of type `@[R] T` is
closed over by the closure — the proof that no other owning reference is accessible in
the current scope.

```metel
let a: @[Rc] Spaceship = @[Rc] Spaceship {
    engine: Engine::StringTheory { core: Core::new() },
};

a.unique(fun(ship: &mut Spaceship) -> () {
    ship.engine = Engine::Impulse { fuel: 100 };
});
```

`unique` does not assert or check that the reference count equals one at runtime. It does
not need to: the `NotCapturing` bound guarantees that no other `@[Rc] Spaceship` pointer
is reachable from the closure, which is the property that makes the mutation safe. Other
`@[Rc] Spaceship` owners may exist in memory that is unreachable from the closure's
capture set; they cannot be accessed and therefore pose no hazard.

---

## 3. The `NotCapturing<T>` aspect

```metel
aspect NotCapturing<T> {}
```

`NotCapturing<T>` is a marker aspect implemented by closure types. A closure type
implements `NotCapturing<T>` if and only if its capture set contains no variable of type
`T`, and no variable of a type that contains `T` as a field transitively.

The compiler infers `NotCapturing<T>` for a closure automatically from its capture set.
The programmer never writes `impl NotCapturing<T>` — it is a derived property, exactly
as `Send` and `Sync` are derived from the types of a value's fields.

### 3.1 What the compiler checks

A closure `f` implements `NotCapturing<X>` if none of the following hold:

1. **Direct capture**: a captured variable has type `X`.
2. **Transitive capture**: a captured variable has a type that contains `X` as a field,
   directly or through any chain of field accesses.
3. **Reference to captured**: a captured variable has type `&X`, `&mut X`, or any
   reference type that could yield an `X`.

Variables of types unrelated to `X` — including `@[Heap] T`, `@[BumpRegion] T`, or any
`@[R2] T` where `R2 ≠ R` — do not affect `NotCapturing<@[R] T>`.

### 3.2 Function call sites within the closure

If the closure body calls a function `f(x)` where `x` has type `X` or a type containing
`X`, the call site is itself an implicit capture of `x` — the closure captures `x` to
pass it. The `NotCapturing<X>` check therefore applies transitively to arguments at call
sites inside the closure body, not only to names in the explicit capture list.

### 3.3 Interaction with RFC-0050 capture lists

RFC-0050 introduces explicit capture lists on closures. The `NotCapturing<T>` bound is
a property of the closure's CAPTURE SET — whatever it actually closes over — not of the
capture list syntax. The two are orthogonal:

- A closure with an empty capture list `[]() -> { ... }` trivially implements
  `NotCapturing<T>` for all `T` (nothing captured).
- A closure with `[&mut count]() -> { ... }` implements `NotCapturing<@[Rc] Spaceship>`
  as long as `count` is not of type `@[Rc] Spaceship` or a type containing it.

The capture list does not need a new specifier for `NotCapturing`; the bound is checked
against the capture set at call sites that require it.

### 3.4 `NotCapturing<T>` beyond shared ownership

`NotCapturing<T>` is a general mechanism. It can be used by any higher-order function
that needs to assert a closure will not interact with a particular type:

```metel
// A sandboxed evaluator: the callback may not capture any IO capability
fun eval_sandboxed<R, F>(expr: Expr, f: F) -> R
    where F: fun(Value) -> R,
          F: NotCapturing<IOCap>
{ ... }
```

This is independent of the region system and of `SharedRegion`. It is a bound on closure
types, applicable wherever a type-level exclusion on captures is useful.

---

## 4. `Rc` — non-atomic shared ownership

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

## 5. `Arc` — atomic shared ownership

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

`unique` is available on both `@[Rc] T` and `@[Arc] T`. Its `NotCapturing` bound is
`NotCapturing<@[Rc] T>` and `NotCapturing<@[Arc] T>` respectively — the two tags are
distinct and do not interfere with each other's alias analysis.

---

## 6. The six stdlib regions

| Type | Lifetime | Drop behaviour | Move-out | Sendable |
|---|---|---|---|---|
| `Heap` | Indefinite | `Drop::drop` when owner dropped | Always safe | Yes |
| `Arc` | Indefinite, atomic RC | `Drop::drop` when RC hits zero | Always safe | Yes (when `T: Send + Sync`) |
| `LocalHeap` | Indefinite, thread-local | `Drop::drop` when owner dropped | Always safe | No |
| `Rc` | Indefinite, non-atomic RC | `Drop::drop` when RC hits zero | Always safe | No |
| `BumpRegion` | Scoped, bump arena | Bulk free; no `Drop::drop` per slot | `T: !Drop` only | No |
| `AutoRegion` | Scoped, bump + drop list | Drop list then bulk free | Always safe | No |

---

## 7. Usage examples

### 7.1 Parent–child graph

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

### 7.2 Safe variant replacement via `unique`

```metel
enum Engine { StringTheory { core: @[Heap] Core }, Impulse { fuel: I32 } }

let ship: @[Rc] Spaceship = @[Rc] Spaceship { engine: Engine::StringTheory { ... } };

ship.unique(fun(s: &mut Spaceship) -> () {
    // Safe: the NotCapturing<@[Rc] Spaceship> bound on this closure has been verified.
    // The old StringTheory variant (and its core) drops before the new variant is set.
    s.engine = Engine::Impulse { fuel: 100 };
});
```

### 7.3 Cross-fiber shared state with `Arc`

```metel
let counter: @[Arc] Counter = @[Arc] Counter::new(0);
let c2 = counter.clone();   // atomic RC increment

spawn(fun() -> () {
    c2.unique(fun(c: &mut Counter) -> () { c.increment() });
});

counter.unique(fun(c: &mut Counter) -> () { c.increment() });
```

`@[Arc] Counter: Send` because `Arc: Send` and `Counter: Send + Sync`. The two `unique`
calls may not overlap — the `NotCapturing` bound prevents each closure from capturing
the other's handle, and the borrow checker prevents simultaneous `&mut` borrows of the
same allocation through separate `unique` calls (each `unique` call takes exclusive mutable
access for its duration).

### 7.4 `unique` with a called function

```metel
fun upgrade_engine(ship: &mut Spaceship, fuel: I32) {
    ship.engine = Engine::Impulse { fuel };
}

let ship: @[Rc] Spaceship = @[Rc] Spaceship { ... };

ship.unique(fun(s: &mut Spaceship) -> () {
    upgrade_engine(s, 100);
    // OK: upgrade_engine takes &mut Spaceship, not @[Rc] Spaceship.
    // The closure captures nothing of type @[Rc] Spaceship.
});
```

### 7.5 `NotCapturing<T>` outside shared ownership

```metel
// Sandbox: the scoring function must not perform any IO
fun run_scored<F>(board: &Board, score: F) -> I32
    where F: fun(&Board) -> I32,
          F: NotCapturing<IOCap>
{
    score(board)
}

// Pure scorer — no IOCap in scope, trivially satisfies NotCapturing<IOCap>
run_scored(&board, fun(b: &Board) -> I32 { b.white_score() - b.black_score() });

// Logging scorer — captures io_cap, fails NotCapturing<IOCap> at compile time
run_scored(&board, fun(b: &Board) -> I32 {
    log_move(&io_cap, b);   // ERROR: closure captures IOCap
    b.white_score() - b.black_score()
});
```

---

## Alternatives considered

### Rc/Arc as exceptions to the region system

Introducing `clone()` on region handles as a one-off feature of `Rc` and `Arc`, and
`unique` as new dedicated syntax, would work but would not generalise. The approach taken
here — `SharedRegion` as a supertrait, `NotCapturing<T>` as a general bound — means any
user-defined RC-style region (pool-managed RC, arena-backed RC with a shared control
block) gets the full protocol for free.

### Runtime alias check for `unique`

`unique` could check `RC == 1` at runtime and panic if not. This is Rust's `Rc::get_mut`
approach. It works but cannot be statically prevented from panicking. The
`NotCapturing<T>` approach makes the check static: the compiler rejects the program at
the point where a potential alias would be captured. No runtime overhead; no possible
crash.

### `Rc<T>` as a library struct (not a region tag)

`Rc<T>` could be a plain struct containing `@[Heap] T` plus a reference count, with
`Deref` for read access and a `borrow_mut`-style method for guarded write access. This
fits the existing system completely but requires a runtime borrow check for mutation —
the same situation as `Rc<RefCell<T>>` in Rust. `NotCapturing<T>` cannot be applied
because there is no region tag for the alias analysis to anchor on. The type tag
approach is strictly more powerful.

---

## Unresolved questions

1. **Cycle handling.** Reference counting cannot free cyclic structures — two `@[Rc] T`
   values referencing each other will never reach a count of zero and will leak. Options:
   weak pointers (a non-owning `@[WeakRc] T` that yields `Perhaps<@[Rc] T>`, also
   implementing a `WeakSharedRegion` aspect); a cycle collector; a type-system
   prohibition on cycles. Deferred — the right answer depends on observed usage patterns.

2. **Precision of `NotCapturing<@[R] T>`.** The current analysis treats all `@[Rc] T`
   pointers as potential aliases regardless of which RC allocation they point to. This is
   sound but conservative: two independent `@[Rc] Spaceship` pointers provably allocated
   at different sites are treated as potential aliases. A more precise analysis based on
   allocation-site identity would reduce false rejections at the cost of implementation
   complexity. Deferred.

3. **`unique` across fiber boundaries for `Arc`.** The example in §7.3 shows two `unique`
   calls on distinct clones in distinct fibers. The soundness argument relies on the
   borrow checker preventing simultaneous `&mut` borrows through separate handles; the
   details of how the borrow checker reasons across fiber spawn points (RFC-0003/RFC-0064)
   are unresolved.

4. **Alias analysis across module boundaries.** A foreign type with private fields cannot
   be inspected to determine whether it contains `@[Rc] T`. The compiler must
   conservatively assume it might. Whether this conservatism is acceptable in practice, or
   whether a visibility-aware analysis is needed, is deferred to the implementation RFC.

5. **`unique` nesting.** Whether a `unique` closure may call `unique` on a different
   `@[Rc] U` (for `U ≠ T`) is unspecified. The naive rule — each `unique` closure
   independently satisfies its own `NotCapturing` bound — appears sound; formal
   verification deferred.

---

## References

- RFC-0050 (Closure Capture Lists) — the capture list syntax; `NotCapturing<T>` is a
  bound on the closure's capture set and interacts with the capture list without requiring
  new syntax.
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
- Ante programming language — the `uniq` compile-time alias exclusion concept, adapted
  here as `NotCapturing<T>` applied to the `unique` method declared in `SharedRegion`.
