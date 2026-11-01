---
id: rfc-0199
title: "Lazy<T> — Deferred, Once-Evaluated Values"
date: '2026-11-01'
status: draft
---

## Summary

Add `Lazy<T>` to the standard library: a value whose computation is deferred until first
demanded and then cached. A `Lazy<T>` owns a **call-once closure** (`once || -> T`, RFC-0134)
and a result slot. Because the thunk is `once`, "evaluated at most once" is enforced by the
ownership checker rather than by a runtime flag, and the thunk's captures are dropped at a
deterministic point (when it is forced, or when the unforced `Lazy` is dropped).

This RFC adds **no syntax**. It is a library type plus two requirements on the language
(see "Language requirements").

---

## Motivation

Metel is strict. Three recurring needs have no good answer today:

1. **Expensive values that may never be used** (a parsed config section, a loaded asset).
   The workaround is `Option<T>` plus hand-written "if none, compute" code at every use site.
2. **Infinite or very large sequences** consumed by prefix (`naturals().take(5)`).
3. **Deferred validation** or deferred I/O whose result is wrapped once and consumed later.

The usual lazy-language answer (implicit thunks everywhere) would conflict with deterministic
`Drop` order (RFC-0071) and with the explicit capture model (RFC-0134). An *explicit* `Lazy<T>`
whose thunk is a `once` closure fits both: captures are moved in, visible in the capture list,
and dropped exactly when the thunk runs or the `Lazy` dies.

---

## Design

### Representation

```metel
enum LazyState<T> {
    Pending { thunk: once || -> T },
    Done    { value: T },
    Poisoned,                       // the thunk panicked mid-evaluation
}

pub struct Lazy<T> { state: LazyState<T> }
```

`LazyState` is private. Only `Lazy` is exported.

### API

```metel
extend<T> Lazy<T> {
    pub fun new(thunk: once || -> T) -> Lazy<T>;      // defer
    pub fun ready(value: T) -> Lazy<T>;               // already evaluated
    pub fun force(&var self) -> &T;                   // evaluate if needed, borrow result
    pub fun into_value(self) -> T;                    // consume, evaluate if needed, move out
    pub fun is_forced(&self) -> boolean;
    pub fun map<U>(self, f: once |T| -> U) -> Lazy<U>;   // builds a new thunk; forces nothing
}
```

### Semantics

1. `Lazy::new(t)` runs nothing. `t`'s captures are moved into the `Lazy` at construction.
2. `force` runs the thunk the first time and stores the result; later calls return the stored
   reference. `into_value` moves the result out, running the thunk if necessary.
3. The thunk is consumed by the call. Calling it twice is a compile error in the
   implementation, never a runtime check.
4. If the thunk panics, the `Lazy` is `Poisoned`; a later `force` panics with a clear message
   (see Open Question 3).
5. Dropping an unforced `Lazy` drops the thunk's captures at that point, in `Drop` order.
6. `map` composes thunks: the new thunk, when forced, forces the old one. The result is
   `once` for the same reason the input is.

### Example

```metel
fun main() {
    let rows := load_rows();
    var report := Lazy::new([rows] once || -> Report { expensive_report(rows) });

    if (user_wants_report()) {
        println(report.force().summary());   // computed here
        println(report.force().total());     // cached
    }
    // not forced: `rows` is dropped with `report`
}
```

Lazy streams (an enum whose tail is a `Lazy`) are expressible without further support and are
the main use of `into_value`:

```metel
enum Stream<T> { Nil, Cons { head: T, tail: Lazy<Stream<T>> } }
```

### Language requirements

- **R1. Moving out of a `&var` place.** `force` must take the state out of `&var self` while it
  runs the thunk. This needs either a `mem::replace`/`mem::take`-style primitive or the
  partial-move machinery from the *Drop and partial moves* roadmap theme. This RFC does not
  invent one; it depends on whichever lands.
- **R2. Interior mutability for shared forcing** is **out of scope** (Open Question 1).

---

## Interactions

- **RFC-0134 / RFC-0153 (closure qualifiers):** `once` is the load-bearing feature.
- **RFC-0071 (Drop):** capture drop order is the main behavioural difference from a GC thunk.
- **RFC-0198 (recursive closures):** self-referential lazies (`let xs := Lazy::new(|| ... xs ...)`)
  need that RFC.
- **RFC-0003 (concurrency):** `Send`/thread-safe forcing is a separate decision.
- **RFC-0124 / RFC-0133 (sequence types, List):** `Stream` is an alternative to `List` for
  unbounded data; no overlap in API.
- **RFC-0140 (effects):** a thunk with a latent effect forces that effect at the force site; the
  effect row of `force` is the thunk's.
- **RFC-0203 (list comprehensions):** comprehensions over a `Stream` only terminate if they
  desugar to lazy iterator adapters.

---

## Alternatives considered

1. **Implicit laziness** (Haskell). Rejected: incompatible with deterministic drop and explicit
   captures.
2. **`Option<T>` + helper function.** Works for one type but cannot express `map` and gives no
   at-most-once guarantee.
3. **`FnOnce`-only (no caching).** That is just a closure; the point of `Lazy` is the cache.
4. **Language-level `lazy let`.** Possible later sugar over this type.

---

## Open Questions

1. **Shared forcing.** `force(&var self)` cannot be called through a shared `&Lazy<T>`. A cache
   behind `&T` needs a `OnceCell`-style type with interior mutability, which has no RFC. Is
   that a prerequisite or a follow-up?
2. **Thread safety.** Is `Lazy<T>` `Send`? Does a synchronised variant need a separate type?
3. **Poisoning vs. abort.** If panics abort the program (RFC-0014 remains draft), `Poisoned` is
   dead code and can be removed.
4. **Allocation.** Recursive uses (`Stream`) need the thunk on the heap; how this is spelled
   depends on RFC-0063/0143 (allocator placement).
5. **Should `map` require `once`?** A `Lazy::map` over a multi-use `|T| -> U` could be `Copy`/
   `Clone`-friendly, but would complicate the signature.

---

## Decision

**Outcome:** *(pending)*
