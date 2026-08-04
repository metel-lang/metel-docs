---
id: rfc-0028
title: "Memory and Reference Model"
date: '2026-05-24'
supersedes:
  - rfc-0001
  - rfc-0024
---

> **Note (2026-06-13) — partial hold.** The **foundation layer of this RFC stands and may be implemented**: linear types, the `@T` owning pointer, and `*T`/`*mut T` raw pointers are independently valuable and survive the memory-strategy reconsideration. The **region/lifetime extension layers** referenced below (RFC-0025, RFC-0051, RFC-0052) are **on hold** pending a survey of non-lifetime safety mechanisms — see `docs/reports/memory-model/memory-strategy-research-directions.md`. Treat anything in this RFC that depends on regions or lifetimes as provisional; the linear/pointer foundation does not.

## Summary

Define Metel's unified memory and reference model. The model has three interlocking parts:

- **Linear types** — opt-in, statically checked exactly-once ownership for resources that require deterministic release. Linearity is declared on the type; no use-site annotation is required.
- **Pointers** — raw `*T` for non-owning aliased access to non-linear values; `@T` as the owning heap pointer for any `T` with a linear handle.
- **Shared ownership** — `Arc<T>` (RFC-0003) for explicitly reference-counted shared ownership across fiber boundaries.

This RFC supersedes RFC-0001 (Pointer Syntax and Semantics) and RFC-0024 (Linear Types), incorporating all resolved decisions from both and carrying forward open questions in unified form.

---

## Staged Design Approach

This RFC defines the **foundation layer** of Metel's memory model — linear types, owning pointers, and raw pointers. It is intentionally conservative in some areas. These restrictions are not permanent language decisions; they are the safe, zero-annotation baseline from which later layers build.

The planned extension layers are:

- **This RFC**: linear types + `@T` owning pointer + `*T` raw pointer. The linear checker and basic pointer surface. Read-only access to linear values is through consume-and-return (no borrow mechanism without lifetimes).
- **Regions (RFC-0025)**: `region { }` introduces named region lifetimes (`'r`). `*T` inside a region is tagged `*'r T`. `RegionFree<'r>` enforces scope exit. This is the first step of lifetime inference.
- **Full lifetime system**: abstract lifetime variables on function signatures (`'a`). `*T` gains safe borrow semantics for linear values. Read-only access without consume-and-return becomes possible.

Each layer is additive. Nothing in this RFC forecloses the later layers.

---

## Motivation

Metel's default memory model uses `Arc<T>` for shared ownership and `region { }` blocks for bump-allocated short-lived state. This is ergonomic for most code but insufficient for systems-level use cases:

- Resources that must be explicitly released (file handles, sockets, buffers)
- Allocation and deallocation that must be deterministic and zero-overhead
- Use-after-free and resource leaks caught at compile time
- Single-owner heap allocation without reference-counting overhead
- Building self-referential or recursive data structures

Linear types address the first two groups. `@T` is the single-owner heap allocation mechanism for any `T` — including linear types. Raw `*T` pointers are non-owning aliases restricted to non-linear values until the lifetime system enables safe borrowing of linear values.

---

## Proposal

### Part 1 — Linear Types

#### 1.1 Declaring linear types

The `linear` keyword annotates a `struct` or `enum` declaration:

```metel
linear struct Buffer {
    ptr: Int,
    len: Int,
}

linear enum Connection {
    Open { socket: Int },
    Closed,
}
```

A struct or enum that contains a `linear` field must itself carry an explicit `linear` annotation. Omitting it when a field is linear is a compile error — implicit silent propagation is rejected to keep linearity visible at every declaration site:

```metel
linear struct Request {   // explicit annotation required
    body: Buffer,         // Buffer is linear
    url: String,
}
```

#### 1.2 Linearity at use sites

Linearity is tracked by the type declaration alone. No use-site annotation or sigil is required — `Buffer` in a binding or function signature is sufficient; the type system knows from the declaration that `Buffer` is linear and enforces exactly-once consumption accordingly.

```metel
let buf: Buffer = Buffer::alloc(1024);

fun write(buf: Buffer, data: Bytes) -> Buffer { ... }
```

#### 1.3 Consumption

A linear value is **consumed** by any of:

- Passing it as an argument to a function
- Returning it from a function or block
- Rebinding it to a new name via `let` (the original binding becomes dead)
- Destructuring it in `match` or a `let` destructure
- Boxing it with `@` (moves the value into heap allocation)

Consuming an already-consumed linear binding is a compile error. A linear binding that reaches the end of its scope without being consumed is a compile error (unless the type implements `Drop` — see §1.8).

```metel
let f = FileHandle::open("data.txt");
f.close();   // consumed — ok

let f2 = FileHandle::open("data.txt");
// scope ends — ERROR: f2 not consumed

let f3 = FileHandle::open("data.txt");
f3.close();
f3.close();  // ERROR: f3 already consumed
```

#### 1.4 Mutation via consume-and-return

There are no mutable references for linear types. Mutation is expressed by consuming the value and returning a new one. Methods on linear types take `self` and return `Self`:

```metel
fun write(buf: Buffer, data: Bytes) -> Buffer { ... }

let buf = write(buf, data);   // buf consumed; new buf bound
```

Method chaining is the idiomatic form for sequential operations:

```metel
buf.write(header).write(body).flush().free();
```

#### 1.5 Read-only access

Without a lifetime system, read-only access to a linear value that does not transfer ownership uses consume-and-return:

```metel
fun buf_len(buf: Buffer) -> (Buffer, Int) {
    let len = buf.len;
    (buf, len)   // buf returned — caller still owns it
}

let (buf, len) = buf_len(buf);
```

When the full lifetime system arrives, `*Buffer` (raw pointer to a linear value) will be the borrow mechanism, making this pattern unnecessary. Until then, consume-and-return is the safe zero-annotation option.

#### 1.6 Branching

Every branch of an `if` or `match` must leave all in-scope linear bindings in the same consumption state at the merge point:

```metel
// Correct:
if condition {
    buf.write(data);
    buf.free();
} else {
    buf.free();
}
```

#### 1.7 Loops

A linear value created outside a loop body may not be consumed inside it — the consumption count would be unpredictable. A linear value created inside a loop body is fine; it is created and consumed once per iteration.

This applies to all linear values including `linear fun` closures (RFC-0046). Calling a `linear fun` consumes it; calling it inside a loop where it was created outside is a compile error.

#### 1.8 `drop` — explicit discard

```metel
drop(buf);   // consumed; satisfies the linearity checker
```

`drop` has the signature `fun<linear T>(val: T)`. It does **not** call `Drop::drop` — it is a pure linearity-satisfying discard. If the type requires external cleanup, the programmer must invoke that cleanup explicitly before calling `drop`. `drop` and `Drop::drop` are distinct operations that happen to share the word "drop": the former is the discard function (always available, no side effects), the latter is the destructor method (opt-in, defined per type).

#### 1.9 `Drop` aspect — implicit destructor

A linear type may implement the `Drop` aspect:

```metel
aspect Drop {
    fun drop(self: Self);
}
```

If a linear value implements `Drop` and reaches the end of its scope unconsumed, the compiler inserts a call to `Drop::drop` automatically rather than emitting a compile error. Types that do not implement `Drop` still produce a compile error on unconsumed scope exit. Implementing `Drop` is the opt-in — there is no separate `#[auto_drop]` attribute.

The programmer is still responsible for calling any external cleanup inside `Drop::drop`. The auto-insert is the last line of defence, not a substitute for explicit consumption in the happy path.

#### 1.10 Destructuring

Destructuring a linear value consumes the outer binding and introduces each field as a new binding. Each extracted linear field must itself be consumed. Ignoring a linear field with `_` or `..` is a type error.

---

### Part 2 — Owning Pointers (`@T`)

#### 2.1 Overview

`@T` is the unique owning heap pointer. It has exactly one live handle; the handle is always linear — it cannot be cloned and must be consumed exactly once. When the handle is consumed, the allocation is released. `@T` is valid for any `T`, linear or non-linear.

The `@` prefix operator boxes a value — it moves the value into a heap allocation and returns the owning handle:

```metel
let x: Int = 42;
let p: @Int = @x;      // x moved into heap; p owns it — must be consumed

let buf: Buffer = Buffer::alloc(1024);
let owned: @Buffer = @buf;   // buf moved into heap; owned must be consumed
```

#### 2.2 Dereferencing

`*p` reads through the owning pointer. One pointer layer is auto-dereffed at field access and method calls:

```metel
let p: @Buffer = @Buffer::alloc(1024);
let len = p.len;       // auto-deref: equivalent to (*p).len
p.write(data);         // method dispatch auto-derefs
```

Reading through `@T` does not consume the handle. Consuming the handle (passing `p` to a function, returning it, or dropping it) releases the allocation.

#### 2.3 Freeing

To explicitly free an owning pointer, pass it to `free` or any consuming function. If the inner type is linear, its `Drop::drop` is called before the allocation is released (if implemented).

#### 2.4 Recursive structures

`@T` enables recursive data structures for both linear and non-linear types:

```metel
linear struct Node {
    value: Int,
    next: Perhaps<@Node>,
}

struct Tree {
    value: Int,
    left: Perhaps<@Tree>,
    right: Perhaps<@Tree>,
}
```

#### 2.5 Relationship to `*T` and `Arc<T>`

| Type | Ownership | Handle linear | T may be linear | Validity |
|---|---|---|---|---|
| `*T` | non-owning alias | no | no — lifetime system needed | region / lifetime |
| `@T` | owning | yes — always | yes | linear handle is the lifetime |
| `Arc<T>` | shared RC | no | no | reference count |

`&x` → `*T` (address-of, non-owning). `@x` → `@T` (box, owning, consuming).

---

### Part 3 — Raw Pointers (`*T`, `*mut T`)

#### 3.1 Overview

`*T` is a raw non-owning pointer. It is an alias — it does not own the value it points to and carries no runtime reference count. Validity is enforced by the region lifetime system (RFC-0025) and, eventually, the full lifetime system.

```metel
mut x: Int = 42;
let p: *Int = &x;
let q: *mut Int = &mut x;
```

`*T` and `*mut T` are currently restricted to non-linear values. `&x` where `x` is a linear type is a type error — taking a raw alias to a linear binding would produce a second path to the value, violating the exactly-once guarantee without lifetime enforcement. This restriction will be lifted when the full lifetime system enables safe borrowing of linear values via `*T`.

**Address-of operators:**

| Expression | Result type | Condition |
|---|---|---|
| `&x` | `*T` | `x` must be non-linear |
| `&mut x` | `*mut T` | `x` must be non-linear and a `mut` binding |

**Dereference:** `*p` reads the value. `*p = v` writes through (only valid for `*mut T`).

**Mutability subtyping:** `*mut T` coerces to `*T` implicitly (downgrade safe; upgrade never allowed).

**Auto-deref:** one pointer layer is auto-dereffed at field access, method calls, and function pointer calls (RFC-0043).

**No pointer arithmetic.** `*Int + 1` is a type error.

**Null safety:** absent pointers use `Perhaps<*T>`. There is no implicit null.

#### 3.2 Pointer validity — staged safety model

| Layer | Mechanism | Scope |
|---|---|---|
| Region scope (RFC-0025) | `*T` inside `region { }` gets lifetime `'r`; `RegionFree<'r>` enforces no `*'r T` escapes the block | Region-allocated pointers |
| Full lifetime system | Abstract lifetime variables on function signatures; borrow checker enforces no pointer outlives its referent | All pointers, including linear value borrows |

`@T` manages its own validity: the allocation lives exactly as long as the handle. No lifetime annotation needed — the linear handle is the lifetime.

`Arc<T>` (RFC-0003) uses reference counting for validity. It is the explicitly RC type.

---

### Part 4 — Typechecker Changes

#### 4.1 Linearity pass

A **linearity environment** (`LinearEnv`) runs as a pass after type inference, once all types are concrete. It maps each in-scope binding to `Unconsumed` or `Consumed(location)`.

| Event | Action |
|---|---|
| `let x = <linear expr>` | Add `x → Unconsumed` |
| Use of linear `x` | If `Unconsumed`: mark `Consumed`. If `Consumed`: error |
| `@x` (box linear `x`) | Mark `x` as `Consumed`; result is owning `@T` (itself linear) |
| Scope exit | Error if any linear binding is still `Unconsumed` (unless `Drop` implemented) |
| `if`/`match` merge | Verify `LinearEnv` state is identical across all branches |
| Loop body entry | Snapshot outer linear bindings; forbid consuming any inside body |

#### 4.2 Pointer type additions

- `InferType::Pointer(Box<InferType>, /*mutable*/ bool)` — raw pointer variant
- `InferType::Owned(Box<InferType>)` — owning pointer variant (`@T`)
- `Type::Pointer(Box<Type>, bool)` and `Type::Owned(Box<Type>)` — resolved type variants
- `UnaryOp::AddressOf`, `UnaryOp::AddressOfMut`, `UnaryOp::Deref`, `UnaryOp::Box` — AST variants
- All `match` on `TypeExpr`, `InferType`, `Type`, and `UnaryOp` gain new arms

---

## Resolved Questions

### OQ-1 — Linearity sigil at use sites ✓ Resolved

**Decision:** No use-site sigil. Linearity is tracked by the type declaration alone — `linear struct Buffer` is sufficient; the type system infers linearity at every binding and parameter site from the declaration. A use-site annotation was considered (`!T`) but dropped: it complicates pointer type composition (e.g. `*Buffer` for a future linear borrow) and adds annotation burden without proportionate readability gain since the type name itself carries the information.

### OQ-2 — Owning pointer syntax and allocation ✓ Resolved

**Decision:** `@T` is the owning heap pointer type. `@x` is the boxing operator — it moves `x` into a heap allocation and returns the owning handle. This replaces `unique *T` from earlier drafts. The `@` sigil is unambiguous (distinct from `&` address-of and `*` raw pointer), composes cleanly in type position, and reads consistently: `@T` always means "I own a T on the heap."

### OQ-3 — Reading through an owning pointer ✓ Resolved

**Decision:** `*p` dereferences an owning pointer. One layer of auto-deref applies at field access and method calls, consistent with RFC-0043. The handle `p` is not consumed by a read — only by a consuming operation (passing to a function, returning, or explicit `free`).

### OQ-4 — Transitivity warnings ✓ Resolved

**Decision:** When a struct contains a linear field, the outer type must carry an explicit `linear` annotation. Omitting it is a compile error. Silent propagation is rejected.

### OQ-5 — Destructor protocol ✓ Resolved

**Decision:** The `Drop` aspect provides an implicit destructor. If a linear value implements `Drop`, the compiler calls `drop` automatically on unconsumed scope exit. Types without `Drop` still error on unconsumed exit.

### OQ-6 — Auto-deref for field access ✓ Resolved (RFC-0043)

**Decision:** One pointer layer auto-dereffed at field access, method calls, and function pointer calls. `->` not introduced.

### OQ-7 — Addressability rules ✓ Resolved (RFC-0043)

**Decision:** Only named bindings and field/element chains are addressable. `&(x + 1)` is a type error.

### OQ-8 — Pointer equality ✓ Resolved (RFC-0043)

**Decision:** `p == q` compares addresses (identity). Value equality requires explicit `*p == *q`.

### OQ-9 — Linear vs affine types ✓ Resolved

**Decision:** Linear types only (exactly once). Affine types are not introduced.

### OQ-10 — Linear type parameters ✓ Resolved

**Decision:** The `linear` keyword is used as a type parameter constraint: `fun<linear T>(val: T)`. This is consistent with `linear struct` at the declaration site — `linear` means "this type must satisfy exactly-once consumption" wherever it appears. The `drop` function signature is `fun<linear T>(val: T)`. The linearity checker applies to `T` within the function body: the parameter must be consumed exactly once.

---

## References

- Language spec: `docs/public/spec.md`, `docs/public/spec/types.md`
- Typechecker notes: `metel-interpreter/docs/typechecker.md`
- Superseded: RFC-0001 (`rfc-0001-pointer-syntax.md`), RFC-0024 (`rfc-0024-linear-types.md`)
- RFC-0043: regular pointers (incorporated) — `*T`/`*mut T` syntax, addressability, auto-deref, pointer equality settled
- Cluster report: `docs/reports/memory-model/rfc-cluster-memory-model.md`
- Lifetime system design: `docs/reports/memory-model/lifetime-system-proposal.md`
- RFC-0006: closure capture — move capture depends on this RFC (linear capture semantics)
- RFC-0025: region allocation — `Region` is a linear type; first step of the lifetime system
- RFC-0026: unsafe blocks — linearity checker relaxed inside `unsafe`; depends on this RFC
- Prior art: Linear Haskell (Bernardy et al. 2018), Rust `Box<T>` and ownership model, Cyclone regions and lifetime system
