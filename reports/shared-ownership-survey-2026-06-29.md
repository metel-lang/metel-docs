---
id: shared-ownership-survey-2026-06-29
title: "Shared Ownership Survey: Ante, Rust RC APIs, Pony Capabilities, and GhostCell"
type: report
created_date: '2026-06-29'
---

# Shared Ownership Survey: Ante, Rust RC APIs, Pony Capabilities, and GhostCell

*This report documents a research round undertaken to evaluate how other languages
handle static exclusive access to reference-counted values, and to determine whether
Metel's RFC-0074 §6 future work direction is sound. The key finding is that no existing
language solves this problem for aliased RC values — but the GhostCell pattern provides
a sound, practical alternative that maps directly onto Metel's brand types (RFC-0076).*

---

## 1. The Problem Statement

RFC-0074 defers static exclusive mutable access to RC-wrapped values as future work.
The core difficulty: a `.clone()` of an `Rc<T>` can be moved into an arbitrary data
structure, after which no binding-level analysis can prove the original binding is the
sole owner. The question driving this research was: have other languages solved this,
and if so, how?

---

## 2. Ante

### 2.1 Ante does not solve the problem — it sidesteps it

Ante's ownership system is based on directly-owned values. Ante's `uniq` is syntactic
sugar for `&mut T` in Rust terms: an exclusive mutable reference to a value the current
scope uniquely owns. The keyword `uniq` annotates bindings, not types:

```ante
foo: uniq I32 = 3
bar bar2 : I32 = 3
```

This is not relevant to RC-wrapped values. Ante's `shared type` (non-atomic RC, immutable)
and `shared mut type` (non-atomic RC, arbitrarily mutable) are distinct categories.
Crucially, a `shared mut` value is **never** `uniq` — Ante provides no mechanism for
exclusive access to a `shared mut` value, because the type system makes no such promise.

The distinction:

| Ante concept | Metel analogue | Notes |
|---|---|---|
| `uniq Foo` | `&mut T` (uniquely owned) | Directly-owned mutable reference |
| `shared Foo` | `Rc<T>` (immutable) | Non-sendable, non-atomic RC |
| `shared mut Foo` | Not yet in Metel | Freely-mutable non-atomic RC |

Ante does not have a `get_mut` analogue — it does not attempt to prove RC uniqueness
at runtime or compile time. The `shared mut` type accepts aliased mutation as its
fundamental mode.

### 2.2 Ante borrow sets

References in Ante carry `'variable` annotations that name the value they borrow from:

```ante
ref 'foo I32    // a reference that borrows from the binding `foo`
```

The compiler infers these through reference operations. Two rules guide the inference:

1. A reference derived from `foo` borrows `'foo`.
2. A reference derived from another reference `r` inherits `r`'s borrow set.

These annotations do not apply to `shared`/`shared mut` values — the borrow set
mechanism tracks *reference* provenance, not *ownership* provenance. It is relevant to
Metel's borrow checker design but not to the RC mutation problem.

**Conclusion:** Ante's `uniq` is Rust's `&mut T`. Ante's `shared mut` is freely-mutable
aliased RC without static exclusivity guarantees. Ante does not solve the RC exclusive
access problem and does not provide a path to solving it.

---

## 3. Rust RC mutation APIs

Rust provides three mechanisms for mutating RC-wrapped values. Each addresses a
different use case:

| API | Signature | Condition checked | Behaviour on failure | Allocates |
|---|---|---|---|---|
| `Rc::get_mut` | `fn get_mut(this: &mut Rc<T>) -> Option<&mut T>` | `strong == 1 && weak == 0` | Returns `None` | Never |
| `Rc::make_mut` | `fn make_mut(this: &mut Rc<T>) -> &mut T` | Always succeeds | Clones `T` (clone-on-write) | On alias |
| `Rc::try_unwrap` | `fn try_unwrap(this: Rc<T>) -> Result<T, Rc<T>>` | `strong == 1` | Returns original `Rc` | Never |

Details:

- **`get_mut`** — the conservative check. Requires no weak references (since a weak
  pointer could be upgraded after the check). Requires `&mut Rc<T>` as the receiver
  to prevent concurrent access to the pointer within the same thread (same role as
  Metel's `&mut Rc<T>`). Returns `Perhaps<&mut T>` that borrows from the `Rc`.
  This is the model for Metel's `SharedPointer::get_mut`.

- **`make_mut`** — the "I always need to mutate" API. If the RC is uniquely held,
  returns the inner `&mut T` directly. If aliases exist, deep-clones `T` into a new
  allocation, replaces `this` with the new `Rc`, then returns a mutable reference to
  the new value. Caller pays for cloning only when needed. Useful for copy-on-write
  patterns. `T: Clone` required.

- **`try_unwrap`** — the "I want to consume the value" API. Consumes the `Rc` itself.
  Does not require zero weak references. On success returns `T` (not a reference);
  on failure returns the original `Rc` wrapped in `Err`. Useful for extracting from
  the last known owner after all other handles are confirmed dropped.

**Design note for Metel.** `make_mut` could be added to `SharedPointer` once `Clone` is
properly tracked in the type system — it requires `T: Clone`, which interacts with
allocation and copy semantics. `try_unwrap` is a consuming operation that returns an
owned `T`; this is already in RFC-0074 and useful for teardown patterns. Neither is
required for the current RFC-0074 design.

---

## 4. Pony Reference Capabilities

Pony solves shared-memory concurrency at the type level with six reference capabilities
(refcaps). Each refcap names a different aliasing and mutability contract:

| Refcap | Mutable | Readable | Aliases allowed | Sendable |
|---|---|---|---|---|
| `iso` | Yes | Yes | None | Yes — transfer only |
| `trn` | Yes | Yes | Read aliases only | No |
| `val` | No | Yes | Any number | Yes |
| `ref` | Yes | Yes | Any number | No |
| `box` | No | Yes | Any number | No |
| `tag` | No | No | Any number | Yes |

The safe concurrency rule: actors can share `val` (immutable, sendable) and transfer
`iso` (exclusive, sendable). All mutation of `ref` and `iso` happens in isolation —
no live alias exists when a `ref`/`iso` is mutated.

`iso` is Pony's answer to static exclusive ownership of heap-allocated values. It is
tracked at the type level: an `iso` value has no live aliases, so the compiler can
prove mutation is safe. When an `iso` is moved to another actor it is consumed; the
receiving actor holds the only reference.

**Why Pony's approach does not translate directly to Metel's Rc situation:**

Pony's `iso` works because the type system tracks aliasing from *creation*. A value is
either `iso` (no aliases, ever) or it has given up that property by creating an alias.
The downgrade is one-way. Once a second alias exists, the value becomes `ref` or `box`
and the `iso` property is permanently lost for that allocation.

Metel's `Rc<T>` is analogous to a Pony `ref` object shared among actors — aliases
are fundamental to its purpose. There is no Pony path from "I have a `ref`-refcapped
value with multiple aliases" to "I hold `iso`-refcapped access to it." The same is
true in Metel: once a clone exists, binding-level analysis cannot recover exclusive
access.

The Pony analogy is useful for a different framing: rather than trying to prove the
`Rc<T>` is unique, give the unique proof to a *capability token* and let the token
grant access to the data.

---

## 5. GhostCell and the `qcell` Crate

### 5.1 The inversion

GhostCell (Yanovski et al., ICFP 2021) inverts the exclusivity problem. Instead of
trying to prove that an RC-wrapped value has no aliases, GhostCell separates:

- **Permission** — held by a branded token (`GhostToken<'brand>`), which has no data.
- **Data** — held by cells (`GhostCell<'brand, T>`) that can be freely aliased via RC.

To access a cell's data mutably, you need `&mut token`. Since the token is a single
value, the standard borrow checker ensures only one `&mut token` exists at a time —
which means only one mutable view of all same-brand cells at a time. Soundness comes
from ordinary `&mut` exclusivity on the token, not from proving RC uniqueness.

```rust
GhostToken::new(|token| {
    let cell1 = GhostCell::new(42);
    let rc1 = Rc::new(&cell1);
    let rc2 = rc1.clone();          // two Rc pointers to the same GhostCell
    // ...
    *rc1.borrow_mut(&mut token) = 99;   // exclusive write via &mut token
    // rc2 is still live — but the write is sound
});
```

The `'brand` lifetime is a `PhantomData` invariant lifetime introduced by
`GhostToken::new`'s callback signature:

```rust
pub fn new<R, F>(f: F) -> R
where F: for<'brand> FnOnce(GhostToken<'brand>) -> R
```

The `for<'brand>` quantifier creates a unique lifetime per call to `new`, making it
impossible to mix tokens from different calls.

### 5.2 The `qcell` crate variants

The `qcell` crate provides four variants addressing different tradeoffs:

| Type | Token | Token uniqueness | Cell access overhead |
|---|---|---|---|
| `QCell` | `QCellOwner` (runtime ID) | Runtime check (panic on dup) | None after type check |
| `TCell` | `TCellOwner<Q>` (marker type) | Compiler-enforced (one per type `Q`) | Zero |
| `TLCell` | `TLCellOwner<Q>` (thread-local) | One per `Q` per thread | Zero |
| `LCell` | Token is the callback scope | `for<'id>` invariant lifetime | Zero |

`LCell`'s model is closest to GhostCell: the token is the owner of a closure scope, and
the `'id` invariant lifetime is the brand. No runtime overhead whatsoever.

### 5.3 The coarse-grained caveat

GhostCell's exclusive access is coarse-grained: `&mut token` grants access to **all**
cells sharing the same brand simultaneously. This is both a feature (one token = one
lock) and a constraint (you cannot hold mutable access to cell A while immutably
reading cell B of the same brand through a normal reference, because the type system
cannot express partial brands within one token).

For fine-grained access — where different cells in the same graph need concurrent
partial access — multiple brand parameters are needed, or the cells must be re-wrapped
with inner mutability. This is an accepted limitation.

---

## 6. Mapping to Metel

### 6.1 RFC-0076 brands as GhostCell brands

Metel's brand types (RFC-0076) are invariant phantom types introduced by a
brand-parameterized callback:

```metel
brand::new[b](() -> {
    // 'b is the brand; unique per call site
});
```

This is the same structure as `GhostToken::new`. The connection is direct:

| GhostCell concept | Metel analogue |
|---|---|
| `'brand` invariant lifetime | Brand parameter `b` (RFC-0076) |
| `GhostToken<'brand>` | `RcToken<'b>` (linear token value) |
| `GhostCell<'brand, T>` | `Rc<T, 'b>` — Rc struct carrying the brand |
| `&mut token` grants exclusive access | `&mut RcToken<'b>` grants exclusive access to all `Rc<T, 'b>` cells |

An `RcToken<'b>` would be a zero-size linear value (one live binding, no `Copy`). Holding
`&mut RcToken<'b>` means holding the exclusive access right to all `Rc<T, 'b>`
allocations. The borrow checker enforces this exactly as it does for any other `&mut`.

### 6.2 Reframing RFC-0074 §6 future work

RFC-0074 §6.1 describes the future work direction as "binding-level alias analysis." The
GhostCell insight reframes this:

**Old framing:** Prove at compile time that the `Rc<T>` binding has no live aliases.

**New framing:** Do not attempt to prove RC uniqueness. Instead, introduce an `RcToken<'b>`
whose exclusive borrow grants mutable access to all `Rc<T, 'b>` cells, regardless of
how many RC aliases exist.

The new framing is:
- **Formally sound** — soundness comes from `&mut RcToken<'b>` exclusivity, not from a
  fragile alias count proof.
- **Zero runtime cost** — no `strong_count()` check.
- **Composable with RFC-0076** — brands already exist; `RcToken` is a thin stdlib addition.
- **More powerful** — it works when many RC aliases exist, not only when the count is one.

The only cost relative to the original `unique` idea is that access is coarse-grained:
`&mut token` covers all cells of the brand at once, not a single pointer in isolation.
For most graph/tree manipulation patterns this is acceptable.

### 6.3 Required prerequisites

Implementing the `RcToken` pattern as a formal language feature requires:

1. **RFC-0076 (Brand Types)** — the invariant brand parameter `'b`.
2. **Linearity constraint on `RcToken<'b>`** — the token must be affine (non-`Copy`,
   non-`Clone`) to maintain the one-token-per-brand invariant. This follows from
   RFC-0071 (Ownership and Move Semantics) — any non-`Copy` type is already affine.
3. **Branded RC interaction** — `Rc<T, 'b>` as the struct carrying the brand
   parameter. Borrow rules for `Rc<T, 'b>` cells when the token's borrow is active.

RFC-0050 (Closure Capture Lists) is no longer a required prerequisite — the GhostCell
approach does not depend on tracking closure captures.

---

## 7. Summary of Findings

| Approach | Static exclusivity | Aliases survive | Runtime check | Notes |
|---|---|---|---|---|
| Ante `uniq` | Yes | No | No | Only for directly-owned values; not applicable to RC |
| Ante `shared mut` | No | Yes | No | Freely-mutable aliased RC; no exclusive mechanism |
| Rust `get_mut` | No | No (requires 0) | Yes | Sound, practical, the RFC-0074 baseline |
| Rust `make_mut` | No | Yes (clone-on-write) | Yes (then clone) | Useful for COW; `T: Clone` required |
| Pony `iso` | Yes | No | No | Aliasing tracked from creation; lost on first alias |
| GhostCell / `RcToken<'b>` | Yes | Yes | No | Sound via `&mut token`; coarse-grained |

GhostCell is the only approach that achieves static exclusive mutable access to a
value that has multiple RC aliases. It does so by transferring the exclusivity question
from the data to a separate linear token. This is the right future direction for
RFC-0074 §6.

The immediate design (RFC-0074 as accepted) is unaffected: `get_mut` is sound, practical,
and requires none of the above prerequisites. The GhostCell direction is noted in §6
as the target for static access, contingent on RFC-0076.

---

## References

- Yanovski, J. et al. *GhostCell: Separating Permissions from Data in Rust* (ICFP 2021).
  The original paper establishing the GhostCell pattern and its soundness argument.
- `qcell` crate documentation — four variants of GhostCell/LCell for different
  uniqueness-guarantee mechanisms.
- Ante language documentation — `uniq`, `shared`, `shared mut`; borrow set annotations.
- Pony tutorial — six reference capabilities; the "share only val, transfer only iso"
  philosophy.
- RFC-0074 (Shared Ownership) — current `get_mut` approach; §6 future work.
- RFC-0076 (Brand Types) — invariant phantom brands; the prerequisite for `RcToken<'b>`.
- RFC-0050 (Closure Capture Lists) — **no longer a required prerequisite** for the
  GhostCell-based static access path.
