---
id: rfc-0049
title: "`linear fun` Type System"
date: '2026-06-04'
---

## Summary

Address three underspecified aspects of the `linear fun` type introduced in RFC-0046: what happens when a `linear fun` is never called (unconsumed scope exit and `Drop` interaction), the general type for closures that transfer linear ownership out rather than consuming inside the body, and the subtyping relationship between `fun` and `linear fun` for use in generic code.

---

## Background

RFC-0046 establishes `linear fun() -> ()` as the type of a closure that move-captures a linear value. Calling the closure consumes it. Three questions were not resolved: what happens if the closure is never called, whether `linear fun() -> T` generalizes correctly to non-unit return types where the linear capture is transferred out, and whether `linear fun` is a subtype of `fun` or a completely separate type.

---

## Open Questions

### OQ-1 — Unconsumed `linear fun` and `Drop`

A `linear fun` is itself a linear value. If it reaches end of scope without being called, the linearity checker fires — same as any unconsumed linear binding.

The programmer has two options under RFC-0028's model:
1. Call `drop(f)` — explicit discard, does not call `Drop::drop`, does not clean up captured linear values.
2. Implement `Drop` for the closure type — compiler inserts `Drop::drop` call at unconsumed scope exit.

Neither option is straightforward for closures:

**Problem with `drop(f)`:** The captured linear values inside `f` are now unconsumed. `drop(f)` satisfies the linearity checker for `f` itself, but the captured `buf: Buffer` inside `f`'s environment is still live and must be consumed. Calling `drop(f)` does not consume `buf`. This is a nested linearity error — `drop(f)` appears to work but leaves the captured values dangling.

**Problem with `Drop` on closures:** Can a programmer implement `Drop` for a closure? Closures don't have a named type — the programmer cannot write `extend [move buf] () -> (): Drop`. The compiler would need to auto-generate a `Drop` implementation for each closure that captures linear values, which calls the appropriate cleanup on each captured linear binding.

**Options:**

**Option A — Captured linear values must be consumed inside the body (required):**

A closure that captures a linear value must consume it in the body. A closure that captures `buf` but never uses it inside the body is a compile error at closure definition time. This forces the programmer to be explicit: if you capture it, you must consume it.

Tradeoff: eliminates the unconsumed-inside problem entirely. Restrictive: a closure cannot capture a linear value just to return it (`[move buf] () -> Buffer { buf }`) without that counting as "consumed." Wait — returning `buf` from the closure does consume it. "Consuming inside the body" means any of the normal consumption paths, including return. So this option is: the closure body must have a code path that consumes every linear capture. This is already enforced by the linearity checker applied inside the closure body.

Under this option, `drop(f)` on an uncalled `linear fun` would still leave the inner linear values unconsumed — the problem remains.

**Option B — Compiler auto-generates `Drop` for `linear fun` closures:**

When a closure has `move` captures of linear values, the compiler auto-generates a `Drop` implementation that calls `drop(v)` on each captured linear value (satisfying their linearity without destructing). If those captured values themselves implement `Drop`, the compiler-inserted `drop` triggers their `Drop::drop`. This forms a recursive cleanup chain.

Tradeoff: ergonomic — `f` can be discarded without explicitly calling it, and cleanup propagates automatically. Requires the compiler to synthesize `Drop` for anonymous closure types, which is non-trivial but well-defined.

**Option C — `drop(f)` on a `linear fun` calls `Drop::drop` implicitly (special case):**

Calling `drop(f)` where `f` is a `linear fun` automatically runs `Drop::drop` on each captured linear value. This is a special case: normally `drop(x)` does not call `Drop::drop`, but for `linear fun` the captured values need cleanup.

Tradeoff: inconsistent with RFC-0028's rule that `drop` never calls a destructor. Introduces a special case the programmer must be aware of.

**Recommendation:** Option B — auto-generated `Drop` for `linear fun` closures. Consistent with the general principle that the compiler handles cleanup when `Drop` is not explicitly implemented (auto-generation), and avoids programmer-visible special cases.

---

### OQ-2 — `linear fun() -> T` generalization

RFC-0046 resolves that a closure with `move` captures has type `linear fun() -> ()`. The motivating examples show only unit return. The question is whether `linear fun() -> T` (non-unit return) is valid, and specifically what the typing rules are when the captured linear value is returned rather than consumed inside the body.

```metel
// Captured buf is returned, not consumed inside:
let get_buf: linear fun() -> Buffer = [move buf] () -> Buffer { buf };
let buf2: Buffer = get_buf();   // get_buf consumed; buf2 is the extracted Buffer
```

After `get_buf()`, `buf2` owns the buffer. `get_buf` is consumed. The linear value has been transferred out of the closure rather than consumed inside it. This is valid: the closure still satisfies exactly-once semantics — `buf` is consumed (by returning), and `get_buf` is consumed (by calling).

**Decision needed:** is this valid, or must linear captures be consumed inside the body (not returned)?

**Option A — Any consumption path inside the body is valid (return counts):**

The linearity checker runs inside the closure body and enforces exactly-once consumption. Returning a linear value from the closure body is a valid consumption path. `linear fun() -> T` where `T` contains linear values is valid.

Implication: `linear fun() -> Buffer` is a valid type. The caller receives the linear value via the return type.

**Option B — Linear captures must be consumed (destructed/freed) inside the body:**

The closure is a "do this once and clean up" primitive. Returning a linear value from a `linear fun` is not permitted — it would mean the caller receives ownership of a value that conceptually lived inside the closure.

Tradeoff: more restrictive; simpler invariant; but eliminates a useful pattern (factory closures, deferred initialization).

**Recommendation:** Option A — any consumption path is valid. The linearity checker inside the closure body enforces correctness regardless of whether `buf` is freed, passed to another function, or returned.

---

### OQ-3 — `linear fun` subtyping

Is `linear fun() -> T` a subtype of `fun() -> T`? The two options:

**Option A — No subtyping; they are distinct types:**

`linear fun` and `fun` are unrelated. A function that accepts `fun() -> ()` cannot be passed a `linear fun() -> ()`. Generic code that wants to accept both must be parameterized explicitly.

```metel
fun run<F: fun() -> ()>(f: F) { f(); }           // only non-linear
fun run_once<F: linear fun() -> ()>(f: F) { f(); } // only linear
```

Tradeoff: explicit and consistent; no covariance surprises. Verbose for generic code.

**Option B — `linear fun` is a subtype of `fun` (a `linear fun` can go where `fun` is expected):**

If you have a `linear fun`, you can pass it to a function that expects `fun`. The callee can call it at most once (it doesn't know it's linear), and in practice it will be called exactly once. The linearity guarantee on the caller side is preserved — the `linear fun` value is consumed by passing it.

Problem: `fun run_many(f: fun() -> ()) { f(); f(); }` — if called with a `linear fun`, the second call `f()` would be on an already-consumed value. This is a soundness violation.

So `linear fun` is NOT safely a subtype of `fun`. Option B is unsound.

**Option C — `fun` is a subtype of `linear fun` (a plain `fun` can go where `linear fun` is expected):**

A plain `fun` (non-linear) can be passed to a function expecting `linear fun` — the callee will call it once and consume it. The `fun` is capable of being called multiple times but happens to be called once here. This is safe: no linearity violation.

This is the useful direction: a generic `run_once` that accepts `linear fun` can also accept a plain `fun`. The plain `fun` is consumed by the call just as a `linear fun` would be.

**Recommendation:** Option C — `fun` is a subtype of `linear fun`. A plain function can always be used where a once-callable function is required. The converse is unsound.

---

## Constraints

- OQ-1 (auto-generated `Drop`) interacts with RFC-0028 §1.9: the auto-generated `Drop` for a `linear fun` must call `Drop::drop` or `drop` on each captured linear value, consistent with the Drop chain.
- OQ-2 (return of linear values) interacts with RFC-0028's consume-and-return pattern — this RFC should be consistent with how linear values are passed through function boundaries generally.
- OQ-3 (subtyping) determines what `fun<F: fun() -> ()>(f: F)` bounds mean and whether they are usable with `linear fun` values.

---

## Resolved Questions

*(None yet — all three are open.)*

---

## References

- RFC-0046: `docs/internal/rfcs/6-refused/rfc-0046-linear-closure-capture.md` — `linear fun` type, `[move x]` captures
- RFC-0028: `docs/internal/rfcs/6-refused/rfc-0028-memory-and-reference-model.md` — `Drop` aspect, linearity checker, `drop` function
- RFC-0006: `docs/internal/rfcs/4-implemented/rfc-0006-closure-capture-semantics.md` — non-linear closure model
