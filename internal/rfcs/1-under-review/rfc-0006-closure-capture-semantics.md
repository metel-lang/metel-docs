---
id: rfc-0006
title: "Closure Capture Semantics and Cross-Closure Reference Sharing"
date: '2026-05-21'
status: draft
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
mut counter = 0;
let inc = fun() -> () { counter += 1; };
let get = fun() -> Int { counter };
```

**Mutation visible to the enclosing scope:**
```metel
// Intended: calling double() updates the original.
// Under clone capture: double works on a copy.
mut x = 5;
let double = fun() -> () { x *= 2; };
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
mut counter = 0;
let p = &mut counter;
let inc = fun() -> () { *p += 1; };
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
mut counter = 0;
let p: *mut Int = &mut counter;
let inc = fun() -> () { *p += 1; };
let get = fun() -> Int { *p };
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

**Partially rejected.** `Rc<RefCell<T>>` is the right tool for heap-allocated shared ownership. However, it requires a standard library type to express what pointers express at the language level. RFC-0043's explicit `&` / `&mut` syntax is more ergonomic for the common case of sharing a stack-local value between closures in the same scope. Both mechanisms should coexist: `*T` for short-lived intra-scope sharing, `Rc<RefCell<T>>` for heap-allocated long-lived sharing.

## Interaction with Upstream RFCs

| RFC | Dependency |
|---|---|
| RFC-0043 (Regular Pointers) | This RFC depends on `*T`/`*mut T` for the explicit-sharing proposal. RFC-0043 must be accepted before this RFC can be closed. |
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
- RFC-0043: `docs/internal/rfcs/1-under-review/rfc-0043-regular-pointers.md` — `*T`/`*mut T`, regular pointer semantics, and closure-sharing support
- RFC-0044: `docs/internal/rfcs/1-under-review/rfc-0044-explicit-receiver-semantics.md` — explicit receiver forms, including `&mut self` for iterator-style mutation
- RFC-0024: `docs/internal/rfcs/rfc-0024-linear-types.md` — linear values cannot be clone-captured; move capture (`move fun`) is required; linear values can be passed as explicit closure parameters
- RFC-0025: `docs/internal/rfcs/rfc-0025-region-allocation.md` — `Region` handles are linear; move capture or explicit parameter passing required
- RFC-0026: `docs/internal/rfcs/rfc-0026-unsafe-blocks.md` — inside an `unsafe fun` closure, the linear capture restriction is relaxed
- Cluster report: `docs/internal/rfc-cluster-memory-model.md`

---

## Decision

**Outcome:** Under review  
**Target:** *(blank until accepted)*

*(Decision rationale goes here when the RFC is evaluated.)*
