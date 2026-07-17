---
id: rfc-0052
title: "Lifetime System"
date: '2026-06-05'
status: superseded
updated: '2026-07-17'
superseded_by: rfc-0067
---

> **⏸ On hold (2026-06-13) — memory-strategy reconsideration.** A full lifetime system is the most expensive, most Rust-derivative layer of the region model, and the reconsideration is specifically evaluating whether to avoid lifetimes entirely (mutable value semantics, generational references, Perceus). Do **not** implement pending that decision. See `docs/reports/memory-model/memory-strategy-research-directions.md`.

> **Status — superseded (2026-07-17).** Predates the 2026-07-02 allocator/lifetime-anchor split and depends entirely on refused prerequisites (RFC-0028, RFC-0025, RFC-0051). Its on-hold memory-strategy reconsideration concluded with that split; the live lifetime-anchor design is RFC-0067 (&T/&mut T anchors named after real bindings), not this RFC's abstract 'a/*'a T syntax.

## Summary

Introduce lifetime annotations to Metel's type system. Lifetimes name the live range during which a borrowed pointer (`*'a T`) is guaranteed to remain valid. This is the third and final layer of the memory safety stack:

- **RFC-0028** — linear types, `@T` owning pointer, `*T` raw pointer (foundation)
- **RFC-0025 + RFC-0051** — region lifetimes (`'r`), `*'r T` region-internal pointer, `RegionFree<'r>` exit constraint
- **This RFC** — abstract lifetime variables on function signatures and struct definitions; borrow state for linear values; full static enforcement that no pointer outlives its referent

Once this RFC lands, `*T` gains safe borrow semantics for linear values, and the consume-and-return workaround becomes optional for read-only access.

---

## Motivation

The current model has three gaps that lifetimes close:

**1. Zero-copy borrowed views cannot cross function boundaries.**

A function that takes `*T` and returns `*T` is already valid syntax, but the return pointer has no statically enforced relationship to the input. The compiler cannot prove the returned pointer is valid — it may outlive the storage it was taken from. Lifetime annotations establish that relationship.

```metel
// Today: must allocate a new String to return a substring
fun first_word(s: String) -> String { ... }

// With lifetimes: return a pointer into the original — no allocation
fun first_word<'a>(s: *'a String) -> *'a String { ... }
```

**2. Structs cannot hold borrowed references.**

A struct field of type `*T` has no tracked lifetime — it can outlive the value it points to. A struct parameterised by a lifetime carries the constraint explicitly: the struct cannot outlive `'a`.

```metel
struct Parser<'a> {
    source: *'a String,
    pos:    Int,
}
// A Parser<'a> cannot outlive the String it borrows from
```

**3. Linear values cannot be borrowed without consume-and-return.**

RFC-0028 §1.5 acknowledges that read-only access to linear values without ownership transfer requires consume-and-return until the lifetime system arrives. A `*'a T` borrow of a linear value provides read access for `'a` without consuming it.

```metel
// Today:
fun buf_len(buf: Buffer) -> (Buffer, Int) { (buf, buf.len) }

// With lifetimes:
fun buf_len<'a>(buf: *'a Buffer) -> Int { buf.len }
```

---

## Design

### Lifetime syntax

```
lifetime        = '\'' identifier          -- named: 'a, 'r, 'scope
                | '\'' '_'                 -- anonymous (inferred)
                | '\'' 'static'            -- valid for the entire program

lifetime-ptr    = '*' lifetime type        -- *'a T: pointer valid for 'a
fun-sig         = 'fun' '<' lifetime* '>' '(' params ')' '->' type
struct-def      = 'struct' name '<' lifetime* type-params* '>'
```

`*T` without a lifetime annotation is shorthand for `*'_ T` — an anonymous lifetime that the compiler fills in via elision rules. `*'r T` for region-internal pointers (RFC-0025) is an instance of this general syntax with `'r` bound by the enclosing `region { }` block.

`'static` is the only predefined lifetime. A value satisfying `'static` is valid for the entire program (global constants, intentionally leaked values).

### Elision rules

Most functions do not need explicit lifetime annotations. The compiler applies three elision rules in order:

1. **Single-input rule** — if a function has exactly one `*T` parameter (or `*'_ T` parameter) and the return type is also `*T`, the return lifetime equals the input lifetime.
2. **Self-like receiver rule** — if one parameter is in receiver position (first argument, same type as the enclosing struct), the output lifetime equals that parameter's lifetime.
3. **Explicit otherwise** — when two or more `*T` inputs are present and the return type borrows from one of them, the lifetime must be written explicitly.

```metel
// Rule 1: inferred — return borrows from s
fun first_word(s: *String) -> *String { ... }

// Rule 3: explicit — which input is returned depends on runtime value
fun longest<'a>(x: *'a String, y: *'a String) -> *'a String {
    if string_len(x) >= string_len(y) { x } else { y }
}
```

### Lifetime bounds

`'a: 'b` means lifetime `'a` outlives lifetime `'b`. Most bounds are inferred. They surface in signatures only when the validity of a return value depends on an ordering relationship between two input lifetimes.

```metel
fun lookup<'a, 'b, K, V>(map: *'a Map<K, V>, key: *'b K) -> Perhaps<*'a V> where 'a: 'b { ... }
```

### Lifetime-parameterised structs

A struct that holds a `*'a T` field is parameterised by `'a`. An instance cannot outlive `'a`.

```metel
struct Iter<'a, T> {
    data:  *'a [T],
    index: Int,
}

fun array_iter<'a, T>(arr: *'a [T]) -> Iter<'a, T> {
    Iter { data: arr, index: 0 }
}
```

`Iter<'a, T>` is not `Send` (it contains `*'a T` which borrows from somewhere). It cannot cross fiber boundaries or escape the scope of `'a`.

### Borrow state for linear values

RFC-0028's `LinearEnv` tracks bindings as `Unconsumed` or `Consumed`. This RFC extends it with a third state:

| State | Meaning |
|---|---|
| `Unconsumed` | Live, no active borrows |
| `Borrowed('a)` | Live, one or more `*'a T` borrows active |
| `Consumed(loc)` | Consumed, cannot be used |

Transition rules:

- `&x` where `x` is linear and `Unconsumed` → transitions `x` to `Borrowed('a)`; produces `*'a T`
- Attempting to consume `x` while `Borrowed('a)` → compile error
- When lifetime `'a` ends → bindings in `Borrowed('a)` transition back to `Unconsumed`
- `drop(x)` while `Borrowed('a)` → compile error (same as any consumption)

```metel
let conn: Connection = Connection::new(fd);   // linear

let port = connection_port(&conn);    // conn → Borrowed('expr)
// conn.close();  ← compile error: conn is borrowed

// borrows expire at end of their expression scope
conn.close();   // OK — conn is Unconsumed again
```

Storable borrows: a `*'a Connection` borrow can be stored in a struct parameterised by `'a`, as long as the struct does not outlive the linear binding.

```metel
struct ConnView<'a> { conn: *'a Connection }

fun view<'a>(c: *'a Connection) -> ConnView<'a> { ConnView { conn: c } }

let conn: Connection = Connection::new(fd);
let view = view(&conn);         // conn → Borrowed('scope)
let port = connection_port(view.conn);
// view drops here → 'scope ends → conn → Unconsumed
conn.close();   // OK
```

### Lifetime interaction with regions

RFC-0025 already introduces `'r` as the region scope lifetime and `*'r T` as region-internal pointers. This RFC makes `'r` a full participant in the general constraint system:

- `*'r T` is an instance of `*'a T` with `'a = 'r`
- `RegionFree<'r>` (RFC-0051) is an instance of the general `RegionFree<'a>` constraint
- Nested regions: `'outer: 'inner` (outer outlives inner); a `*'outer T` is valid inside the inner block and satisfies `RegionFree<'inner>` because it is not tagged `'inner`

The `region 'r { }` label (currently a no-op, RFC-0025) becomes a concrete binding: `'r` is the lifetime introduced by the enclosing `region` block.

### Pointer borrow rules

**From `*T` (immutable pointer):**

`&(*p)` where `p: *T` produces `*'a T` valid for `'a = scope_of(p)`. As long as `p` is live, the referent is reachable. This is sound under the current `Rc`-backed evaluator and under a compiled backend where `p` keeps storage live.

**From `*mut T` (mutable pointer):**

`&(*p)` where `p: *mut T` is a type error without first downgrading: `let rp: *T = p`. This prevents forming a read borrow from a write alias, but does not prevent aliased mutation during the borrow (see OQ-3). Safe borrowing from `*mut T` is deferred.

**From `@T` (owning pointer):**

`&(*p)` where `p: @T` produces `*'a T` valid for `'a = scope_of(p)`. The owning pointer is the lifetime anchor; the borrow cannot outlive it.

**From `Arc<T>`:**

`&(*arc)` produces `*'a T` valid for `'a = scope_of(arc)`. The reference count guarantees the inner value is live for as long as the `Arc<T>` handle exists.

---

## What This Does Not Include

**`*mut T` borrow safety.** Forming a read borrow `*'a T` from `*mut T` via downgrade is syntactically allowed but not semantically enforced — a write through a `*mut T` alias can invalidate the borrow. Safe mutable borrowing requires an exclusivity checker and is deferred (see OQ-1).

**Mutable references (`*mut 'a T`)** — a mutable borrow type with exclusivity guarantee. Not introduced here. See OQ-1.

**Higher-ranked lifetimes.** `for<'a> fun(*'a T) -> boolean` — universally quantified lifetimes for callbacks and higher-order functions. Deferred (see OQ-5).

**Variance rules.** Covariance / contravariance / invariance for lifetime-parameterised types. Required for soundness of lifetime subtyping; the rules are mechanical but need explicit specification.

---

## Open Questions

### OQ-1 — `*mut 'a T` and mutable borrowing

The biggest gap a lifetime system without mutable borrowing leaves: in-place mutation through a reference without consume-and-return. Adding `*mut 'a T` requires an exclusivity invariant — at most one mutable borrow, no read borrows during it. This is a borrow-checker-level guarantee.

Options:
- **Defer indefinitely** — consume-and-return is the permanent model; `*mut 'a T` is not added.
- **`unsafe` only** — `*mut 'a T` available inside `unsafe { }` (RFC-0026); the programmer asserts exclusivity manually.
- **Full exclusivity checker** — adds significant compiler complexity; closes the last gap vs. Rust's `&mut T`.

### OQ-2 — Borrowed linear state and the loop constraint

RFC-0028 §1.7 forbids consuming a linear value created outside a loop body. The `Borrowed('a)` state adds a new variant: a borrow created from a binding outside the loop. Can a borrow be created and expire within each loop iteration?

If the borrow's lifetime spans multiple iterations (i.e. a `*'a T` is stored in a struct that persists across iterations), this conflicts with the loop constraint in a novel way. Explicit rules are needed for when a linear binding may transition `Borrowed → Unconsumed` inside a loop body.

### OQ-3 — Aliased mutation during a pointer borrow

Downgrading `*mut T` to `*T` before borrowing is a type-level safety measure, but does not prevent a write through a surviving `*mut T` alias during the borrow's lifetime. Options:

- **Document and accept** — pointer borrows are programmer-asserted safety; the same caveats as other aliasing patterns apply.
- **Suspend `*mut T` aliases** — downgrading to `*T` for borrowing invalidates (consumes) the `*mut T` alias for the duration of the borrow, similar to `RefCell::borrow()`. The `*mut T` is restored when the borrow expires.
- **Require `unsafe`** for any `*T` borrow derived from a `*mut T` alias.

### OQ-4 — Annotation burden and elision completeness

The elision rules cover the most common patterns. Whether they are sufficient for idiomatic Metel code — or whether additional heuristics are needed — is only answerable by writing real programs with the system. This question is deferred to the implementation phase.

Open sub-question: should struct definitions with lifetime parameters require explicit bounds at every use site (Rust-style), or should the compiler infer them from the struct definition?

### OQ-5 — Higher-ranked lifetimes

Passing a callback `fun(*T) -> boolean` to a higher-order function that operates on a borrowed collection requires the callback to work for *any* lifetime — `for<'a> fun(*'a T) -> boolean`. Without this, many iterator and predicate patterns are not expressible in the general case. Defer until the base lifetime system is in use and concrete demand is observed.

---

## Staged Delivery

This RFC is the capstone of the memory safety stack. Suggested order within it:

1. **Lifetime syntax and elision** — parse `*'a T`, lifetime parameters on functions and structs; elision rules; `'static`
2. **Pointer borrow enforcement** — verify `*'a T` does not outlive the binding it was produced from; enforce in the typechecker
3. **Borrow state for linear values** — extend `LinearEnv` with `Borrowed('a)`; block consumption during active borrows
4. **Region lifetime unification** — `region 'r { }` produces a real `'r` variable; `*'r T` participates in the general constraint system; `RegionFree<'r>` (RFC-0051) replaces `Send`
5. **Variance** — covariance / contravariance / invariance rules for lifetime-parameterised types

---

## References

- Lifetime system proposal: `docs/reports/memory-model/lifetime-system-proposal.md` — exploratory design; §4.1–4.3 for region, linear, and pointer interactions
- RFC-0028: `docs/internal/rfcs/6-refused/rfc-0028-memory-and-reference-model.md` — linear types, `@T`, `*T`; §1.5 explicitly defers to this RFC for linear borrows
- RFC-0025: `docs/internal/rfcs/6-refused/rfc-0025-region-allocation.md` — region lifetimes; `*'r T`; `Send` interim constraint
- RFC-0051: `docs/internal/rfcs/6-refused/rfc-0051-regionfree-exit-constraint.md` — `RegionFree<'r>`; lands as part of step 4 above
- RFC-0047: `docs/internal/rfcs/6-refused/rfc-0047-owning-pointer-completeness.md` — `*T` from `@T`; OQ-2 there resolves under this RFC
- RFC-0026: unsafe blocks (deferred) — OQ-1 option B depends on unsafe
- Prior art: Rust lifetime system and borrow checker; Cyclone region-based memory management
