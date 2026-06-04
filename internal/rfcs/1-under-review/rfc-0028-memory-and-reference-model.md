---
id: rfc-0028
title: "Memory and Reference Model"
date: '2026-05-24'
status: under-review
supersedes:
  - rfc-0001
  - rfc-0024
---

## Summary

Define Metel's unified memory and reference model. The model has three interlocking parts:

- **Linear types** — opt-in, statically checked exactly-once ownership for resources that require deterministic release
- **Read references** (`@T`) — expression-scoped, non-storable views of a linear value that do not consume it
- **Pointers** — raw `*T` for non-owning aliased access; unique `unique *T` as the owning heap indirection for any `T`; `Arc<T>` (RFC-0003) for explicitly reference-counted shared ownership

The three parts are inseparable: linear types require read references to be usable, unique pointers are the bridge that allows linear values to be heap-allocated and passed indirectly, and regular pointers are restricted to non-linear types to preserve the aliasing model. They must be designed and implemented together.

This RFC supersedes RFC-0001 (Pointer Syntax and Semantics) and RFC-0024 (Linear Types), incorporating all resolved decisions from both and carrying forward their open questions in unified form.

---

## Staged Design Approach

This RFC defines the **foundation layer** of Metel's memory model — linear types, expression-scoped read references, and unique pointers. It is intentionally conservative in some areas, particularly the placement rules for `@T`. These restrictions are not permanent language decisions; they are the safe, zero-annotation baseline from which later layers build.

The planned extension layers are:

- **This RFC**: linear types + expression-scoped `@T` + unique pointers. The linear checker and basic pointer surface.
- **Regions (RFC-0025)**: `Region::scope` introduces named region lifetimes (`'r`). Allocations inside become lifetime-tagged (`*'r T`). `@T` gains a region lifetime form (`@'r T`) that can be stored and returned within the scope. `RegionFree<'r>` replaces the `Send` scope-exit constraint. This is the first step of lifetime inference — the programmer writes a scope boundary; the compiler infers lifetimes from it.
- **Full lifetime system**: abstract lifetime variables on function signatures (`'a`) for cross-region and cross-function borrow tracking. Explicit annotations required only where inference from region boundaries is insufficient.

Each layer is additive. Nothing in this RFC forecloses the later layers; the `@T` restrictions here are the subset that requires zero annotations and can be checked without a lifetime or region system.

---

## Motivation

Metel's default memory model uses `Arc<T>` for shared ownership and `region { }` blocks for bump-allocated short-lived state. This is ergonomic for most code but insufficient for systems-level use cases:

- Resources that must be explicitly released (file handles, sockets, buffers)
- Allocation and deallocation that must be deterministic and zero-overhead
- Use-after-free and resource leaks caught at compile time
- Single-owner heap allocation without reference-counting overhead
- Building self-referential or recursive data structures

Linear types address the first two groups. `unique *T` is the single-owner heap allocation mechanism for any `T` — including linear types. Raw `*T` pointers are non-owning aliases whose validity is enforced by the region and lifetime systems.

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

A struct or enum that contains a `linear` field is itself treated as linear automatically, but the outer type **must** carry an explicit `linear` annotation. Omitting it when a field is linear is a compile warning that becomes an error — implicit silent propagation is rejected to keep linearity visible at every declaration site:

```metel
linear struct Request {   // explicit annotation required
    body: Buffer,         // Buffer is linear
    url: String,
}
```

#### 1.2 Linearity sigil at use sites

Linearity must be visible at every use site — in variable declarations, function parameters, and return types. The form `Buffer` alone is a type error if `Buffer` is declared linear; the marked form `!Buffer` is required everywhere.

`!` is the linearity sigil. It is unambiguous in type position (`!` is logical NOT only in expression position). It is concise and visually distinct from `&` (address-of) and `@` (read reference):

```metel
let buf: !Buffer = Buffer::alloc(1024);

fun write(buf: !Buffer, data: Bytes) -> !Buffer { ... }
```

#### 1.3 Consumption

A linear value is **consumed** by any of:

- Passing it as an argument to a function
- Returning it from a function or block
- Rebinding it to a new name via `let` (the original binding becomes dead)
- Destructuring it in `match` or a `let` destructure

Consuming an already-consumed linear binding is a compile error. A linear binding that reaches the end of its scope without being consumed is a compile error.

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
fun write(buf: !Buffer, data: Bytes) -> !Buffer { ... }

let buf = write(buf, data);   // buf consumed; new buf bound
```

Method chaining is the idiomatic form for sequential operations:

```metel
buf.write(header).write(body).flush().free();
```

#### 1.5 Branching

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

#### 1.6 Loops

A linear value created outside a loop body may not be consumed inside it — the consumption count would be unpredictable. A linear value created inside a loop body is fine; it is created and consumed once per iteration.

#### 1.7 `drop` — explicit discard

```metel
drop(buf);   // consumed; satisfies the linearity checker
```

`drop` has the signature `fun<T: Linear>(val: T)`. It does not call a destructor method — the programmer must call the destructor explicitly before dropping if needed.

#### 1.8 `Drop` aspect — implicit destructor

A linear type may implement the `Drop` aspect:

```metel
aspect Drop {
    fun drop(self: Self);
}
```

If a linear value implements `Drop` and reaches the end of its scope unconsumed, the compiler calls `drop` automatically rather than emitting a compile error. Types that do not implement `Drop` still produce a compile error on unconsumed scope exit. Implementing `Drop` is the opt-in — there is no separate `#[auto_drop]` attribute.

The programmer is still responsible for calling any external cleanup (closing file handles, etc.) inside `drop`. `Drop::drop` is the last line of defence, not a substitute for explicit consumption in the happy path.

#### 1.9 Destructuring

Destructuring a linear value consumes the outer binding and introduces each field as a new binding. Each extracted linear field must itself be consumed. Ignoring a linear field with `_` or `..` is a type error.

---

### Part 2 — Read References (`@T`)

#### 2.1 Overview

`@T` is a non-owning, expression-scoped view of a linear value. It allows inspection without consumption, making it possible to call read-only functions without transferring ownership.

`@T` is formed with the `@` prefix operator:

```metel
linear struct Buffer { ptr: Int, len: Int }

fun buf_len(b: @Buffer) -> Int { b.len }

let buf = Buffer::alloc(1024);
let len = buf_len(@buf);   // buf is not consumed
buf.free();
```

#### 2.2 Placement rules

- `@T` may only appear in **expression position** — it cannot be bound to a `let`, stored in a struct field, or appear in a function return type
- `@T` is not itself linear — it may be used any number of times within its expression scope
- A function accepting `@T` may read from the value but cannot consume it

Because `@T` cannot be stored, it cannot outlive the expression it appears in. No lifetime annotations are needed.

**Note — intentionally conservative:** these restrictions define the zero-annotation baseline. They will be relaxed when region lifetimes are introduced: `@'r T` will be storable in structs and returnable from functions, provided the struct or return type is parameterized by `'r` and the value does not outlive the region scope. The expression-scoped form here is the subset that requires no annotations and no region or lifetime system.

#### 2.3 No mutable read references

`@mut T` is not introduced by this RFC. Mutation is handled by consume-and-return (§1.4). This is a deliberate stage-gate: `@mut T` requires an exclusivity checker (at most one `@mut T` at a time, no `@T` concurrent with it) — effectively a borrow checker. That machinery belongs to the full lifetime system layer, not this foundation. If in-place mutation through a reference becomes a demonstrated need, it will be designed as an extension of the lifetime system.

#### 2.4 Relationship to `&`

`@x` and `&x` are distinct operators with no overlap:

| Operator | Result type | Storable | Runtime cost | Valid on |
|---|---|---|---|---|
| `&x` | `*T` | yes | none (raw pointer) | non-linear `x` only |
| `@x` | `@T` | no | none | linear `x` only |

`&x` where `x` is linear is a type error. `@x` where `x` is non-linear is a type error.

**Note — potential convergence with the lifetime system.** The distinction between `@T` and `*T` is narrower than it appears: both are non-owning, non-allocating references. The key difference today is that `@T` is expression-scoped and therefore safe without lifetime annotations — it cannot outlive the linear value it borrows. `*T` lacks that scope guarantee and requires the lifetime system to be safe.

When `@'r T` (storable read reference tagged with a region lifetime) is introduced, it and `*'r T` (raw pointer with a region lifetime) become structurally very similar. At that point they may converge into a single unified reference type, with expression-scoped `@T` as the `'_`-lifetime special case. Whether `@` and `*` unify or remain distinct operators is an open question for the full lifetime system RFC.

---

### Part 3 — Pointers

#### 3.1 Regular pointers (`*T`, `*mut T`)

`*T` is a raw non-owning pointer to a value of type `T`. It is an alias — it does not own the value it points to and carries no runtime reference count. Validity is not tracked at runtime; it is enforced by the region lifetime system (RFC-0025) and, eventually, the full lifetime system.

```metel
mut x: Int = 42;
let p: *Int = &x;
let q: *mut Int = &mut x;
```

`*T` and `*mut T` cannot point to linear values. `&x` where `x` is linear is a type error — taking a raw alias to a linear binding would produce a second path to the value, violating the exactly-once guarantee.

**Address-of operators:**

| Expression | Result type | Condition |
|---|---|---|
| `&x` | `*T` | always — `x` may be `let` or `mut` |
| `&mut x` | `*mut T` | type error if `x` is a `let` binding |

**Dereference:** `*p` reads the value. `*p = v` writes through (only valid for `*mut T`).

**Mutability subtyping:** `*mut T` coerces to `*T` implicitly (downgrade safe; upgrade never allowed).

**Auto-deref:** one pointer layer is auto-dereffed at field access, method calls, and function pointer calls — `p.field` and `(*p).field` are equivalent for a single indirection (RFC-0043).

**No pointer arithmetic.** `*Int + 1` is a type error.

**Null safety:** absent pointers use `Perhaps<*T>`. There is no implicit null.

#### 3.2 Unique pointers

A unique pointer `unique *T` is the owning heap allocation mechanism. It has exactly one live handle; the handle is linear — it cannot be cloned and must be consumed exactly once. When the handle is consumed (freed or transferred), the allocation is released.

`unique *T` is valid for any `T` — linear or non-linear:

| Type | Ownership | T linear | Handle linear |
|---|---|---|---|
| `*T` | non-owning alias | no — type error | no |
| `unique *T` | owning | yes or no | yes — always |
| `Arc<T>` | shared RC | no — type error | no |

Recursive linear data structures become possible:

```metel
linear struct Node {
    value: Int,
    next: Perhaps<unique *!Node>,
}
```

**Open questions:** unique pointer allocation syntax and reading through a unique pointer. See OQ-2 and OQ-3.

#### 3.3 Pointer validity — staged safety model

`*T` is a raw non-owning pointer with no runtime validity tracking. Validity is guaranteed progressively by compile-time mechanisms:

| Layer | Mechanism | Scope |
|---|---|---|
| Region scope (RFC-0025) | `*T` inside `region { }` gets lifetime `'r`; `RegionFree<'r>` enforces no `*'r T` escapes the block | Region-allocated pointers |
| Full lifetime system | Abstract lifetime variables on function signatures; borrow checker enforces no pointer outlives its referent | All pointers |

`unique *T` manages its own validity: the allocation lives exactly as long as the handle. No lifetime annotation needed for unique pointers — the linear handle is the lifetime.

`Arc<T>` (RFC-0003) uses reference counting for validity. It is the explicitly RC type; `*T` is not.

---

### Part 4 — Typechecker Changes

#### 4.1 Linearity pass

A **linearity environment** (`LinearEnv`) runs as a pass after type inference, once all types are concrete. It maps each in-scope binding to `Unconsumed` or `Consumed(location)`.

| Event | Action |
|---|---|
| `let x = <linear expr>` | Add `x → Unconsumed` |
| Use of linear `x` | If `Unconsumed`: mark `Consumed`. If `Consumed`: error |
| `@x` | Do not mark consumed; verify `x` is `Unconsumed` |
| Scope exit | Error if any linear binding is still `Unconsumed` |
| `if`/`match` merge | Verify `LinearEnv` state is identical across all branches |
| Loop body entry | Snapshot outer linear bindings; forbid consuming any inside body |

#### 4.2 Pointer type additions

- `InferType::Pointer(Box<InferType>, /*mutable*/ bool)` — new variant; `unify` gains pointer cases
- `Type::Pointer(Box<Type>, bool)` — new resolved type variant
- `UnaryOp::AddressOf`, `UnaryOp::AddressOfMut`, `UnaryOp::Deref` — new AST variants
- All `match` on `TypeExpr`, `InferType`, `Type`, and `UnaryOp` gain new arms (exhaustiveness-checked by the compiler)

---

## Open Questions

### OQ-2 — Unique pointer syntax and allocation

The working syntax is `unique *T`. Alternatives:
- A sigil form that composes with the linearity sigil from OQ-1
- A keyword other than `unique`

Allocation syntax is also open. Candidate: `Box::alloc(value) -> unique *T` as a standard-library constructor.

### OQ-10 — Linear type parameters

Can a generic parameter be constrained to linear: `fun<T: Linear>(val: T)`? Required for `drop`. The interaction with v0.2 generics needs design.

---

## Resolved Questions

### OQ-1 — Linearity sigil at use sites ✓ Resolved

**Decision:** `!T` — the `!` prefix is the linearity sigil at every use site. Unambiguous in type position (`!` is logical NOT only in expression position); concise; visually distinct from `&` (address-of) and `@` (read reference). Every occurrence of a linear type in a variable declaration, function parameter, or return type must carry the `!` prefix. The bare type name without `!` is a type error if the type is declared linear.

### OQ-4 — Transitivity warnings ✓ Resolved

**Decision:** When a struct becomes implicitly linear because a field is linear, the compiler emits a warning and requires an explicit `linear` annotation on the outer type. Silent propagation is rejected. This keeps linearity visible and intentional at every declaration site.

### OQ-5 — Destructor protocol ✓ Resolved

**Decision:** The language defines a `Drop` aspect with a `drop(self)` method. If a linear value implements `Drop`, the compiler calls `drop` automatically when the value would otherwise go out of scope unconsumed — converting what would be a compile error into an implicit destructor call. Types that do not implement `Drop` still produce a compile error on unconsumed scope exit. `#[auto_drop]` is not needed as a separate annotation; implementing `Drop` is the opt-in.

### OQ-6 — Auto-deref for field access ✓ Resolved (RFC-0043)

**Decision:** One pointer layer is auto-dereffed at field access, method calls, and function pointer calls. `(*p).field` and `p.field` are equivalent for a single pointer indirection. `->` is not introduced.

### OQ-7 — Addressability rules ✓ Resolved (RFC-0043)

**Decision:** Only named bindings and field/element chains are addressable. `&(x + 1)` is a type error.

### OQ-8 — Pointer equality ✓ Resolved (RFC-0043)

**Decision:** `p == q` compares addresses (identity). Value equality requires explicit `*p == *q`.

### OQ-3 — Reading through a unique pointer ✓ Resolved

**Decision:** `@p` where `p: unique *!T` auto-dereferences through the pointer, producing `@T`. Consistent with the one-layer auto-deref rule (RFC-0043). The handle `p` is not consumed; the `@T` view is expression-scoped as usual.

### OQ-9 — Linear vs affine types ✓ Resolved

**Decision:** Linear types only (exactly once). Affine types (at most once — silent drop permitted) are not introduced. Every linear value must be explicitly consumed; silent discard is always a compile error. This gives the strongest guarantee and makes resource management always visible. Affine may be revisited as a future extension if a clear use case emerges.

---

## References

- Language spec: `docs/public/spec.md`, `docs/public/spec/types.md`
- Typechecker notes: `metel-interpreter/docs/typechecker.md`
- Superseded: RFC-0001 (`rfc-0001-pointer-syntax.md`), RFC-0024 (`rfc-0024-linear-types.md`)
- RFC-0043: regular pointers (incorporated) — `*T`/`*mut T` syntax, addressability, auto-deref, pointer equality settled
- Cluster report: `docs/reports/memory-model/rfc-cluster-memory-model.md`
- Lifetime system design: `docs/reports/memory-model/lifetime-system-proposal.md`
- RFC-0006: closure capture — `move fun` syntax depends on this RFC (linear capture semantics)
- RFC-0025: region allocation — `Region` is a linear type; RFC-0025 is also the first step of the lifetime system (region scope introduces named lifetime `'r`, enabling `@'r T` and `RegionFree<'r>`)
- RFC-0026: unsafe blocks — linearity checker relaxed inside `unsafe`; depends on this RFC
- Prior art: Linear Haskell (Bernardy et al. 2018), Rust `Box<T>` and ownership model, Cyclone regions and lifetime system
