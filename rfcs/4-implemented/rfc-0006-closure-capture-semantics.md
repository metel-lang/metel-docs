---
id: rfc-0006
title: "Closure Capture Semantics and Cross-Closure Reference Sharing"
date: '2026-05-21'
status: implemented
spec_status: done
---

## Summary

Define how closures capture values from their enclosing scope and what mechanisms exist for two closures to share the same mutable value. The current PoC uses clone-at-definition capture everywhere; this RFC establishes the intended permanent semantics.

---

## Motivation

The PoC evaluator captures all free variables by cloning them at closure definition time. This is correct for independent closures but makes two important patterns impossible:

**Shared mutable state between closures:**
```metel
// Intended: inc and get both operate on the same counter.
// Under clone capture: each holds its own copy — inc's mutations are invisible to get.
var counter = 0;
let inc = () -> () { counter += 1; };
let get = () -> Int { counter };
```

**Mutation visible to the enclosing scope:**
```metel
// Intended: calling double() updates the original.
// Under clone capture: double works on a copy.
var x = 5;
let double = () -> () { x *= 2; };
double();
// x is still 5 here
```

These are genuine use cases; every production language with closures solves them somehow. Metel needs a principled answer before the PoC evaluator is rewritten.

The answer is constrained by one upstream RFC and one future compatibility boundary:

- **RFC-0043** introduces `*T` / `*mut T` — typed, explicit, non-owning regular pointers.
- **Concurrency and lifetime work** may later add additional rules for which closure captures are allowed to escape their defining scope or cross concurrency boundaries.

This RFC decides whether reference sharing between closures should be implicit (Go-style) or explicit (via pointer types from RFC-0043). It does not decide concurrency-specific transfer rules.

---

## Design Space

Two axes define the problem:

### Axis 1 — Capture semantics: by value vs by reference

**By value (current PoC):** at closure definition, each free variable is cloned. The closure owns a private copy. Mutations inside the closure do not affect the outer binding; mutations to the outer binding do not affect the closure.

**By reference (Go model):** the closure holds an implicit pointer to the enclosing scope's binding. Mutations are visible in both directions. This is the source of Go's classic closure-over-loop-variable bug (`for i := range xs { go func() { use(i) }() }` where all goroutines see the final value of `i`).

**Explicit pointer capture (RFC-0043 model):** value capture by default; reference capture requires the programmer to explicitly take a pointer before closing:
```metel
var counter = 0;
let p = &var counter;
let inc = () -> () { *p += 1; };
```
Aliasing is visible at the capture site. The loop variable problem cannot occur silently.

### Axis 2 — Shared ownership: can two closures alias the same value?

With by-value capture: impossible without a shared container type.
With by-reference capture: automatic — both closures close over the same binding.
With explicit pointer capture: possible if both closures capture the same pointer `p`.
With a reference-counted container (`Rc<RefCell<T>>`): possible — both closures clone the `Rc`, sharing the inner value.

## Proposal

### Default: value capture (clone)

Closures capture by value. At definition time, every free variable that appears in the closure body is cloned into the closure's environment. This is the current PoC behaviour and becomes the permanent default.

Rationale:
- Consistent with Metel's existing value semantics (struct assignment clones).
- No implicit aliasing — the programmer always sees a clone at the definition site.
- Eliminates the loop variable bug class entirely.

### Sharing state: via explicit pointer types (RFC-0043)

To share mutable state between two closures, the programmer takes an explicit pointer before closing over it:

```metel
var counter = 0;
let p: *mut Int = &var counter;
let inc = () -> () { *p += 1; };
let get = () -> Int { *p };
inc();
inc();
let n = get();  // n == 2; counter == 2
```

Both `inc` and `get` capture `p` by value (they hold a cloned `*mut Int`). Cloning a `*mut Int` produces a second pointer to the same `Rc<RefCell<Int>>` cell — this is how reference semantics are achieved under value-capture rules.

This means: **pointer types are their own aliasing mechanism**. Cloning a `*T` produces a second read-only alias; cloning a `*mut T` produces a second mutable alias. The programmer opts in explicitly by taking a pointer.

This avoids a special capture mode — the language has one capture rule (clone) and one aliasing mechanism (pointers). The interaction between the two produces shared-reference closures without adding a new language concept.

### Concurrency and escape analysis are deferred

This RFC does not decide which closures may cross concurrency boundaries, which captures may outlive their defining scope, or whether such rules are expressed through `Send`, limited lifetimes, or another mechanism.

The only requirement imposed here is compatibility:

- the closure capture model chosen here must admit a future rule that restricts escaping or concurrent use of captured aliasing state
- explicit pointer capture must remain visible in the closure surface so later concurrency rules can reason about it

### Escaping closures extend the lifetime of reachable non-linear storage

If a closure leaves the lexical scope of a non-linear local that it captured by value, the closure simply owns its captured copy and no further rule is needed.

If a closure leaves the lexical scope of a non-linear local that it can still reach through an explicit regular pointer capture, the storage reachable through that pointer must remain alive for as long as the closure can still reach it.

Example:

```metel
fun make_counter() -> () -> Int {
    var n = 0;
    let p = &var n;
    return () -> Int {
        *p += 1;
        return *p;
    };
}
```

This is valid only if the runtime representation promotes or otherwise preserves the storage for `n` when the closure escapes. The user-visible rule is simple: an escaping closure may extend the lifetime of captured non-linear storage it can still reach. The end of the original lexical scope does not invalidate that capture.

This is a language guarantee. The implementation strategy is deliberately left open.

## Implementation Strategies

The language semantics above do **not** require the evaluator or future runtime to represent every variable as `Rc<RefCell<T>>`. Only bindings that are captured, aliased, or allowed to outlive their defining frame need indirection.

Ordinary locals may remain plain frame slots. The runtime only needs a distinct representation for captured storage.

### Option A — Eager heap boxing for captured bindings

As soon as the implementation determines that a local binding is captured by a closure, it places that binding in a heap-allocated capture cell. Uncaptured locals remain ordinary frame slots.

Conceptually:

```text
ordinary local      -> plain frame slot
captured local      -> heap cell
closure free var    -> handle to heap cell
```

Under this model:

- clone-by-value closure capture copies ordinary values directly into the closure environment
- explicit pointer capture stores a handle to the same capture cell
- if the closure escapes, no further promotion step is needed because the captured storage is already heap-backed

Advantages:

- simple implementation model
- easy to reason about escaping closures
- no special closing step when a frame exits

Costs:

- every captured binding pays heap allocation cost immediately
- non-escaping captures are boxed even when they never need promotion

This is the simplest replacement for the current PoC-wide `Rc<RefCell<T>>` approach. It narrows indirection to captured bindings only.

### Option B — Open/closed upvalues

This model keeps a captured binding tied to its live frame slot while the defining frame is still active, then promotes it only when the frame exits and an escaping closure still needs it.

Conceptually:

```text
open upvalue   -> points at live frame slot
closed upvalue -> owns promoted heap value
closure free var -> handle to upvalue
```

While the defining frame is active, closures read and write through the open upvalue into the frame slot. When the frame is about to exit, any still-live open upvalues are "closed": their current value is copied into heap-owned storage, and the upvalue handle is rewritten to point there instead of into the dead frame.

Advantages:

- avoids heap allocation for many short-lived captures
- matches established VM practice (Lua-style upvalues)
- keeps ordinary locals and non-escaping captures cheap

Costs:

- more complex runtime bookkeeping
- requires a precise frame-exit closing step
- implementation is harder to validate than eager boxing

This model is a strong long-term candidate if the evaluator is replaced by a lower-level runtime or VM.

### Common requirement for both options

Both implementation strategies must preserve the same language contract:

- uncaptured locals do not require reference counting or heap allocation
- captured-by-value locals behave like ordinary cloned values
- explicit pointer captures may alias shared storage
- escaping closures keep reachable non-linear captured storage alive

The RFC therefore chooses the **language semantics** now while leaving the runtime free to adopt either eager capture boxing or open/closed upvalues later.

## Fit with Linear Types and the Compiler

The implementation strategies above are intended for **non-linear captured storage**. They are not, by themselves, a complete model for linear closure capture.

### Boundary with linear types

Linear values impose a stronger constraint than ordinary closure lifetime management:

- a linear binding cannot be silently duplicated
- a linear binding cannot be turned into shared aliasing state by ordinary capture machinery
- an escaping closure over linear state requires an ownership-transfer rule, not merely a storage-promotion rule

Therefore this RFC should be read as establishing the permanent closure model for **non-linear values**:

- non-linear values may be clone-captured by default
- non-linear values may be shared explicitly through regular pointer capture
- escaping closures may extend the lifetime of reachable non-linear captured storage

Linear values remain future work. A later RFC may permit some form of explicit move capture or ownership capture for linear bindings, but that must be expressed as a distinct rule. The non-linear capture machinery described here must not be treated as automatically applicable to linear values.

### Why this matters for the compiler

A production compiler will want to distinguish at least three cases:

1. uncaptured locals
2. captured locals that do not escape
3. captured locals that escape their defining frame

That classification is useful for both performance and ownership reasoning.

For non-linear values, either implementation strategy from this RFC can support that pipeline:

- **eager heap boxing** is simpler and can be used as a transitional implementation
- **open/closed upvalues** are a better long-term fit for a compiler or VM because they separate frame-local storage from promoted escaping storage

### Eager heap boxing as a transitional implementation

Eager heap boxing works well as a first compiler implementation because it is easy to make correct:

- captured locals are identified during capture analysis
- captured locals are placed in heap cells immediately
- closures store handles to those cells
- escaping closures need no additional promotion step

This is a reasonable early compiler strategy because it keeps the closure conversion story simple and avoids tying correctness to a more complex frame-exit algorithm.

Its main limitation is that it over-allocates. Captured locals that never truly need heap promotion still pay the cost. That is acceptable in an early compiler, but it is unlikely to be the final performance model.

### Open/closed upvalues as the long-term compiler direction

Open/closed upvalues fit the longer-term compiler story more naturally:

- uncaptured locals remain ordinary frame slots
- captured non-escaping locals can remain frame-backed while the frame is alive
- only escaping captured locals are promoted into owned storage when needed

This aligns well with:

- closure conversion
- escape analysis
- stack allocation of ordinary locals
- later optimization passes that reduce heap pressure

It also provides a cleaner separation between:

- lifetime extension for non-linear captures
- future ownership-transfer rules for linear captures

That separation matters. The compiler should not encode non-linear aliasing and lifetime extension in a way that later forces linear captures into the same machinery.

This RFC chooses **open/closed upvalues as the preferred long-term implementation strategy** for the compiler and runtime rewrite. Eager heap boxing remains a valid transitional implementation, but it is not the intended end state.

### Long-term direction

The intended long-term picture is:

- RFC-0006 defines closure semantics for non-linear values
- a later linear-types RFC defines whether linear values may be closure-captured at all, and if so, under what explicit ownership rule
- the compiler lowers closures into explicit environment objects or upvalue handles rather than treating the whole frame as universally reference-counted state

In that model, eager boxing is an acceptable step on the path to a compiler, but open/closed upvalues — or an equivalent closure-environment representation with selective promotion — are the better fit for the final implementation architecture.

---

## Alternatives Considered

### A — Implicit reference capture (Go model)

All closures close over references to the enclosing scope. Mutations are always shared.

**Rejected.** Implicit aliasing violates Metel's design principle of "no implicit conversions." The loop variable bug is a well-documented footgun. Explicit pointer capture makes aliasing visible at the definition site.

### B — `move` / non-`move` closure distinction (Rust model)

Two syntactic forms:
- `fun(...) -> R { ... }` — reference capture (borrows from enclosing scope)
- `move fun(...) -> R { ... }` — value capture (moves/clones from enclosing scope)

**Rejected.** Metel does not have borrow checking today. A reference-capture closure whose enclosing scope has ended would dangle unless the language later adds a lifetime or escape discipline. The explicit-pointer approach (Proposal) gives the same expressive power for shared state while keeping aliasing explicit.

### C — `Rc<RefCell<T>>` as primary sharing primitive (no pointer syntax)

Shared mutable state is always wrapped in `Rc<RefCell<T>>` directly. No pointer types in the language — RFC-0043 is deferred or dropped.

**Partially rejected.** `Rc<RefCell<T>>` is the right tool for heap-allocated shared ownership. However, it requires a standard library type to express what pointers express at the language level. RFC-0043's explicit `&` / `&var` syntax is more ergonomic for the common case of sharing a stack-local value between closures in the same scope. Both mechanisms should coexist: `*T` for short-lived intra-scope sharing, `Rc<RefCell<T>>` for heap-allocated long-lived sharing.

## Interaction with Upstream RFCs

| RFC | Dependency |
|---|---|
| RFC-0043 (Regular Pointers) | This RFC depends on `*T`/`*mut T` for the explicit-sharing proposal and treats RFC-0043 as the source of truth for regular-pointer semantics. |
| Future concurrency / lifetime RFCs | Those RFCs must define how closure captures interact with escaping scope and concurrent use. This RFC intentionally leaves that undecided. |

---

## Resolved Decisions

1. **A single closure capture model is sufficient**

   Metel uses clone-by-value capture by default. Shared mutable closure state is expressed through explicit pointer capture rather than through separate implicit capture modes.

2. **Pointer captures intentionally keep the captured cell alive**

   If a closure captures a regular pointer to a non-linear local binding, the captured storage remains alive for as long as the closure can still reach it. That behavior is intentional and must be reflected in the eventual spec text. The user-visible model is that closures can extend the lifetime of captured non-linear storage; programmers should not reason about the original lexical binding going away as invalidating the capture.

3. **This RFC does not decide concurrency transfer rules for closures**

   Whether escaping or concurrently used closures are constrained by `Send`, limited lifetimes, or another model remains future work. This RFC only fixes capture and aliasing semantics within the ordinary closure model.

4. **Language-facing closure sharing uses pointer syntax, not evaluator internals**

   `Rc<RefCell<T>>` is an implementation detail of the current evaluator, not a surface-language construct. This RFC, RFC-0043, and future spec text should describe shared mutable closure state in terms of `*T` and `*mut T`. Internal runtime storage strategy can evolve without changing the language contract.

---

## Timing Recommendation

This RFC should be resolved **before the PoC evaluator is rewritten**. The rewrite is the right moment to change capture semantics, since the `Value` and `Environment` types need changes anyway. The PoC's clone-capture model is correct for the test suite as-is and does not need changing before the rewrite.

The blocking dependency is RFC-0043 (regular pointers). Resolve RFC-0043 before implementing the capture changes in the rewrite.

---

## References

- Language spec: [`spec/functions.md#closures`](../../public/spec/functions.md#closures), [`spec/runtime.md#panics`](../../public/spec/runtime.md#panics)
- RFC-0043: `docs/public/rfcs/5-superseded/rfc-0043-regular-pointers.md` (superseded by RFC-0067a) — `*T`/`*mut T`, regular pointer semantics, and closure-sharing support
- RFC-0044: `docs/public/rfcs/4-implemented/rfc-0044-explicit-receiver-semantics.md` — explicit receiver forms, including `&var self` for iterator-style mutation
- RFC-0024: `docs/public/rfcs/rfc-0024-linear-types.md` — linear values cannot be clone-captured; move capture (`move fun`) is required; linear values can be passed as explicit closure parameters
- RFC-0025: `docs/public/rfcs/rfc-0025-region-allocation.md` — `Region` handles are linear; move capture or explicit parameter passing required
- RFC-0026: `docs/public/rfcs/rfc-0026-unsafe-blocks.md` — inside an `unsafe fun` closure, the linear capture restriction is relaxed
- Cluster report: `docs/internal/rfc-cluster-memory-model.md`

---

## Decision

**Outcome:** Accepted  
**Target:** *(pending milestone assignment)*

Metel adopts clone-by-value closure capture as the default model. Shared mutable closure state is explicit and pointer-based, escaping closures extend the lifetime of reachable non-linear captured storage, and open/closed upvalues are the preferred long-term implementation strategy.
