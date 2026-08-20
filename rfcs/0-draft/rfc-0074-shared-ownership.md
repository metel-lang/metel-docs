---
id: rfc-0074
title: "Shared Pointers — Rc and Arc"
date: '2026-06-30'
---

> **Status — under review.** Moved back from accepted: the struct definitions use
> `brand 'b` as a type parameter kind (`struct Rc<T, brand 'b>`, `PhantomBrand<'b>`),
> which is syntax from RFC-0076 (Brand Types). RFC-0076 Q1 (brand introduction
> mechanism) remains unresolved. Until RFC-0076 is accepted, the type signatures in
> this RFC are formally incomplete. Blocking: RFC-0076. Also depends on RFC-0071
> (Ownership and Move Semantics) and RFC-0072 (Negative Bounds).

## Summary

The existing region types (`Heap`, `LocalHeap`, `BumpRegion`, `AutoRegion`) all provide
**unique ownership**: each allocation has exactly one owner; moving transfers it; the
type system enforces this statically. One ownership pattern is absent: **shared
ownership** — multiple owning pointers to the same allocation, with the allocation freed
when the last owner drops.

This RFC introduces shared ownership through two stdlib **smart pointer structs**:

- **`Rc<T>`** — reference-counted, non-sendable. The reference count is a plain
  integer. All owners are confined to the same fiber.
- **`Arc<T>`** — atomically reference-counted, sendable when `T: Send + Sync`. Owners
  may be distributed across fibers.

`Rc<T>` and `Arc<T>` are structs, not region tags. They wrap a heap allocation and
manage its lifetime through the reference count. They implement `Clone` (increment
count), `Drop` (decrement; free when zero), and `Deref` (borrow the inner `T`). They
do not implement `Region`.

A standalone **`SharedPointer`** aspect captures the common interface — `clone`,
`get_mut`, `try_unwrap` — for generic code over shared pointers. `SharedPointer` is
not a subtype of `Region`.

---

## Motivation

### The shared ownership gap

RFC-0063 establishes uniquely-owned heap allocation via `@[Heap] T`. Unique ownership
does not cover every data structure. A doubly-linked list node needs a reference to
both neighbours; a tree node may need a reference to its parent; a shared cache entry
may be referenced by multiple consumers with unpredictable lifetimes. In all of these
cases the allocation should live as long as at least one owner keeps it alive — the
defining property of reference counting.

### The mutation hazard

Naive shared mutable access is unsafe. Consider two owning pointers `a` and `b` to the
same `Engine` value. If `a` is used to match on the current variant and extract a
reference to its field, while `b` is used to replace the variant, the replacement
destroys the field while the reference derived from `a` is still live — a use-after-free.

The safe approach is to verify, at the moment mutation is attempted, that no other
owner exists. This RFC provides `get_mut` — a runtime check returning `Perhaps<&var T>`.
If the reference count is exactly one, no other owner exists and exclusive mutable
access is safe. Otherwise `None` is returned and the caller handles the failure.

### Why Rc and Arc are not regions

An earlier design of this RFC classified `Rc` and `Arc` as implementors of a
`SharedRegion: Region` supertrait. That classification was rejected after analysis
(see report: `allocatable-region-split-analysis`). The exceptions required to fit
shared pointers into the region model are not edge cases — they describe a
fundamentally different kind of thing:

- **No runtime handle.** Region allocation passes an allocator handle through the
  bracket channel (`@[r] T`). There is no "Rc handle" — the allocation always goes to
  the global heap. The bracket channel would pass nothing.
- **Clone on the pointer.** No region pointer `@[R] T` implements `Clone`. Moving is
  the norm. Rc and Arc require clone-as-refcount-increment as a core operation.
- **Drop with side effects on the pointer.** For region types, drop is managed by the
  region scope or the owning binding. For Rc/Arc, the pointer itself carries significant
  drop logic (decrement; conditionally free).
- **Brand parameter required for identity.** No other allocation type needs a brand
  parameter. Rc and Arc need one because aliasing is fundamental to their purpose and
  there is no handle to serve as an identity token.
- **`get_mut` — a runtime aliasing query.** Nothing else in the region system asks
  "am I the only reference to this?" The question does not arise for unique ownership.

Beyond the structural exceptions, the claimed ergonomic benefit of the region
classification — that changing `@[Heap] T` to `@[Rc] T` leaves downstream code
unchanged — does not hold in practice. Mutation requires `get_mut`; clone produces a
second pointer to the *same* allocation rather than an independent copy; extraction
requires `try_unwrap` rather than a direct move. Code that does anything beyond
borrowing must be updated when switching to shared ownership. The transparent
strategy-change property holds within the unique-ownership region family but not across
the unique/shared ownership boundary.

Rc and Arc are smart pointer structs. The region system is for allocation strategies
with unique ownership.

---

## 1. The `SharedPointer` aspect

```metel
aspect SharedPointer<T> {
    fun clone(self: &Self) -> Self
    fun get_mut<'s>(self: &'s var Self) -> Perhaps<&'s var T>
    fun try_unwrap(self: Self) -> Result<T, Self>
    fun strong_count(self: &Self) -> USize
}
```

`SharedPointer<T>` is a standalone aspect — not a subtype of `Region`. Types
implementing it are owning smart pointers to `T` with reference-counted lifetime
semantics.

`SharedPointer` is the extension point for user-defined shared pointer types: a
pool-managed RC, an arena-backed RC with a shared control block, or an intrusive
reference count. Any type implementing `SharedPointer<T>` gets the full generic
interface without special-casing.

---

## 2. `Rc<T>` — non-atomic shared ownership

`Rc<T>` is a smart pointer struct with non-atomic reference counting:

```metel
struct Rc<T, brand 'b> {
    inner: @[Heap] RcInner<T>,
    _brand: PhantomBrand<'b>,
}

struct RcInner<T> {
    strong: USize,
    value: T,
}
```

The brand parameter `'b` provides per-allocation identity (RFC-0076). Two `Rc<T, 'b>`
values with the same brand are aliases of the same cell; two with different brands are
independent. In normal code the brand is inferred and invisible; it appears in error
messages when aliasing is relevant.

### 2.1 Allocation

```metel
let a: Rc<Node> = Rc::new(Node { val = 1 });
```

`Rc::new` allocates `Node` on the global heap, prepends a reference count initialised
to one, and returns the owning pointer. There is no scope form — the lifetime is
governed by the reference count, not a lexical scope.

### 2.2 Clone — acquiring a second owner

```metel
let a: Rc<Node> = Rc::new(Node { val = 1 });
let b = a.clone();   // reference count: 2; a and b are both owners of the same Node
```

Clone increments the reference count and returns a second pointer to the *same*
allocation. It does not copy `Node`. Moving `a` transfers one owner without touching
the count:

```metel
let b = a;   // b is the only owner; a is consumed; count unchanged
```

### 2.3 Borrow — read access

`Rc<T>` implements `Deref<Target = T>`. Any borrow of an `Rc<T>` yields `&T`:

```metel
let a: Rc<Node> = Rc::new(Node { val = 1 });
let r: &Node = &*a;   // borrow; lifetime tied to binding `a`
```

The borrow expires when `a` goes out of scope or is moved. Borrows derived from
different `Rc` aliases (e.g., from `b = a.clone()`) are independent borrows that each
track their source binding, not the shared allocation.

### 2.4 `get_mut` — runtime-checked exclusive access

```metel
fun get_mut<'s>(self: &'s var Rc<T, 'b>) -> Perhaps<&'s var T>
```

`get_mut` checks `strong_count == 1`. If the count is one, no other owner exists and a
mutable reference is returned. Otherwise `None` is returned.

The receiver is `&var Rc<T>`, which prevents concurrent borrows of the outer pointer
within the same fiber, making the check sound.

```metel
var node: Rc<Node> = Rc::new(Node { val = 1 });

match node.get_mut() {
    Some(n) => n.val = 42,
    None    => { /* other owners exist */ }
}
```

### 2.5 `try_unwrap` — consuming extraction

```metel
fun try_unwrap(self: Rc<T, 'b>) -> Result<T, Rc<T, 'b>>
```

`try_unwrap` consumes the `Rc<T>` and checks `strong_count == 1`. If the count is one,
the inner `T` is returned. Otherwise the original `Rc<T>` is returned in `Err`. Useful
for teardown patterns where the caller holds the last known owner.

### 2.6 Sendability

`Rc<T>` is not sendable. The reference count is a non-atomic integer; cloning an
`Rc` from one fiber while another fiber drops it produces a data race.

```metel
extend<T, brand 'b> Rc<T, 'b>: !Send;
extend<T, brand 'b> Rc<T, 'b>: !Sync;
```

Negative impls are required here rather than relying on absence of a positive impl.
The `Send` auto-impl rule (RFC-0080 §3.2) grants `Send` to any struct whose fields
are all `Send`. `Rc<T, 'b>`'s reference count field is an integer, which is `Send`
by value — so the auto-impl would incorrectly grant `Rc<T>: Send` without an
explicit override. The negative impls (RFC-0081) prevent this regardless of any
blanket that might otherwise apply.

`T`'s sendability is irrelevant — the counter is the unsound part.

---

## 3. `Arc<T>` — atomic shared ownership

`Arc<T>` is a smart pointer struct with atomic reference counting:

```metel
struct Arc<T, brand 'b> {
    inner: @[Heap] ArcInner<T>,
    _brand: PhantomBrand<'b>,
}

struct ArcInner<T> {
    strong: AtomicUSize,
    value: T,
}
```

The interface is identical to `Rc<T>`: `new`, `clone`, `Deref`, `get_mut`,
`try_unwrap`. The difference is the counter type and sendability.

### 3.1 Sendability

`Arc<T>` is sendable when `T: Send + Sync`:

```metel
extend<T: Send + Sync, brand 'b> Arc<T, 'b>: Send {}
extend<T: Send + Sync, brand 'b> Arc<T, 'b>: Sync {}
```

Both `Send` and `Sync` require `T: Send + Sync` because the allocation is reachable
from any fiber that holds an `Arc` clone; any fiber may read `T` through its `Arc`
(requiring `Sync`), and any fiber may be the last to drop (requiring `Send` for the
destructor).

### 3.2 `get_mut` race safety

`get_mut` on `Arc<T>` checks the atomic count. The check is inherently racy in the
presence of concurrent clones from other fibers; requiring `&var Arc<T>` as the
receiver prevents concurrent access to the *outer pointer* within the same fiber and
makes the check sound. A concurrent clone on another fiber that arrives after the check
would have to produce a new `Arc` that is not the one being checked.

---

## 4. Comparison

| | `Rc<T>` | `Arc<T>` |
|---|---|---|
| RC operations | Non-atomic | Atomic |
| `Send` | No | Yes (when `T: Send + Sync`) |
| Per-clone cost | One integer increment | One atomic increment |
| Exclusive access | `get_mut` — runtime `Option` | `get_mut` — runtime `Option` |
| Extraction | `try_unwrap` — runtime `Result` | `try_unwrap` — runtime `Result` |
| Use case | Single-fiber shared ownership | Cross-fiber shared ownership |

---

## 5. Usage examples

### 5.1 Parent–child graph

```metel
struct Node {
    value: I32,
    children: @[Heap] List<Rc<Node>>,
}

fun make_tree() -> Rc<Node> {
    let leaf1 = Rc::new(Node { value = 1, children = @[Heap] List::Nil {} });
    let leaf2 = Rc::new(Node { value = 2, children = @[Heap] List::Nil {} });
    Rc::new(Node { value = 0, children = @[Heap] List::from([leaf1, leaf2]) })
}
```

### 5.2 Safe mutation via `get_mut`

```metel
enum Engine { StringTheory { core: @[Heap] Core }, Impulse { fuel: I32 } }

var ship: Rc<Spaceship> = Rc::new(Spaceship { engine = Engine::StringTheory { ... } });

match ship.get_mut() {
    Some(s) => s.engine = Engine::Impulse { fuel = 100 },
    None    => panic("unexpected alias"),
}
```

### 5.3 Shared state with `Arc`

```metel
let config: Arc<Config> = Arc::new(Config::default());
let config2 = config.clone();   // send to another fiber

// after all other owners are dropped:
var config = config;
match config.get_mut() {
    Some(cfg) => cfg.update(new_settings),
    None      => { /* still shared */ }
}
```

### 5.4 Generic over shared pointers

```metel
fun log_count<T, P: SharedPointer<T>>(ptr: &P) {
    println("owners: {}", ptr.strong_count());
}

log_count(&rc_node);
log_count(&arc_config);
```

---

## 6. Future work — static exclusive access

The `get_mut` approach is always sound but imposes a runtime check and forces the
caller to handle the `None` case even when the program structure guarantees uniqueness.
A purely static mechanism is desirable when it can be made formally sound.

### 6.1 Token-gated access via `RcToken<'b>` (GhostCell pattern)

A sound alternative to proving the RC count is one: introduce a **linear token** whose
exclusive borrow grants mutable access to all same-brand cells regardless of how many
aliases exist. Soundness comes from `&var token` exclusivity — the borrow checker
enforces that only one `&var token` exists at a time:

```metel
brand 'b {
    let token: RcToken<'b> = RcToken::new();
    let a: Rc<Node, 'b> = Rc::new_branded(Node { val = 1 });
    let alias = a.clone();   // multiple owners — fine

    a.borrow_mut(&var token).val = 42;
    // alias is still live; soundness from &var token, not from count
}
```

No `strong_count` check required. The coarse-grained tradeoff: `&var token` covers all
`'b`-branded cells simultaneously. This is acceptable for most graph manipulation
patterns.

Prerequisites: RFC-0076 (Brand Types) must be accepted. `Rc::new_branded` and
`RcToken` are follow-on stdlib additions contingent on RFC-0076.

### 6.2 Static exclusive access for `Arc` via structured concurrency

For `Arc`, token-gated access across fiber boundaries requires coordination. Whether
this takes the form of a `SharedToken<'b>` with lock-like semantics or is simply out
of scope for static analysis is an open question deferred to the concurrency RFC cluster
(RFC-0064).

---

## Alternatives considered

### `Rc` and `Arc` as `SharedRegion: Region` implementors

The previous version of this RFC classified `Rc` and `Arc` as implementors of a
`SharedRegion` supertrait of `Region`, using region tag syntax (`@[Rc] T`,
`@[Arc] T`). This was rejected after analysis (report: `allocatable-region-split-analysis`).

The classification required seven exceptions to the region model: no runtime handle,
clone on the pointer, per-pointer drop with side effects, brand parameter for identity,
a new `SharedRegion` supertrait, `get_mut`, and the aliasing semantics themselves. The
claimed benefit — transparent allocation strategy change (`@[Heap] T` → `@[Rc] T`
without touching downstream code) — does not hold: mutation, clone semantics, and
extraction all change when crossing the unique/shared ownership boundary. Downstream
code that does anything beyond borrowing must change.

Forcing shared pointers into the region model is the worst of both worlds: the region
concept accumulates exceptions without delivering the transparency that would justify them.

### `Allocatable` supertrait with `@[Rc] T` allocation syntax

An intermediate design introduces an `Allocatable` supertrait above both `Region` and
`SharedPointer`, with the `@[_]` bracket syntax tied to `Allocatable` rather than
`Region`. `Rc` and `Arc` would implement `SharedPointer: Allocatable`, preserving the
`@[Rc] T` allocation expression syntax while being explicitly non-region types.

The analysis shows that `Allocatable` would unify construction, borrow, sendability,
and drop contract — but not move-out, which remains a `Region`-only operation. The
remaining benefit of `Allocatable` is syntactic uniformity at allocation expressions
and borrow sites. Syntactic uniformity is achievable more cheaply: `@[Rc] expr` can be
allocation sugar that desugars to `Rc::new(expr)` without `Rc` implementing any trait.

This RFC does not adopt the `Allocatable` design. The `@[Rc] T` allocation syntax
remains an open question (§Unresolved questions).

---

## Unresolved questions

1. **Allocation syntax.** Whether `@[Rc] expr` and `@[Arc] expr` are supported as
   syntactic sugar for `Rc::new(expr)` and `Arc::new(expr)` is unresolved. The sugar
   would preserve allocation-site uniformity without requiring `Rc` to implement any
   trait. Whether the benefit justifies the special syntax rule is a language design
   decision deferred to a follow-on RFC.

2. **Cycle handling.** Reference counting cannot free cyclic structures. Options: weak
   pointers (`Weak<T>`, a non-owning pointer that does not extend the lifetime); a
   cycle collector; a type-system prohibition on cycles. Deferred.

3. **Token-gated static exclusive access.** Contingent on RFC-0076 (brand types). The
   `RcToken<'b>` direction is the target; formal specification deferred to a follow-on
   RFC once RFC-0076 is accepted.

4. **Static exclusive access for `Arc`.** Contingent on the Rc case being resolved and
   RFC-0064 (structured fork-join parallelism) being accepted. Deferred.

---

## References

- RFC-0071 (Ownership and Move Semantics) — `Clone`, `Drop`, `Deref`; `Copy`/`Drop`
  mutual exclusion means neither `Rc<T>` nor `Arc<T>` is `Copy`.
- RFC-0072 (Negative Bounds) — `T: !Aspect` bounds used at call sites.
- RFC-0081 (Negative Impls) — `extend Rc<T>: !Send;` and `extend Rc<T>: !Sync;`;
  required because the `Send` auto-impl would otherwise grant sendability via the
  integer reference-count field.
- RFC-0080 (Stdlib Aspects) — `Send`/`Sync` auto-impl rules; `Clone` and `Deref`
  impls for `Rc` and `Arc`.
- RFC-0063 (Region Handles) — region system that Rc and Arc are explicitly *not* part
  of; `@[Heap] T` as the unique-ownership heap pointer.
- RFC-0076 (Brand Types) — brand parameter `'b` on `Rc<T, 'b>` and `Arc<T, 'b>`;
  prerequisite for `RcToken<'b>` static exclusive access (§6.1).
- RFC-0064 (Fork-Join Parallelism) — prerequisite for static exclusive access on
  `Arc` (§6.2).
- Report: `allocatable-region-split-analysis` — analysis of whether Rc/Arc should be
  regions, `Allocatable` implementors, or library structs; motivates the current design.
- Report: `shared-ownership-survey-2026-06-29` — survey of Ante, Rust RC APIs, Pony
  reference capabilities, and GhostCell/qcell; motivates `get_mut` as the baseline and
  `RcToken<'b>` as the future static access path.
