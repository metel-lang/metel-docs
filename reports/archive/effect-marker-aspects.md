---
id: effect-marker-aspects
title: "Effect Marker Aspects"
type: report
created_date: '2026-06-29'
rfcs: [0003, 0063, 0065, 0066, 0067, 0068, 0069, 0071, 0072]
reports: [substructural-and-separation-types, per-field-multiplicities, algebraic-effects-and-memory-model]
---

# Effect Marker Aspects

*Grounded in RFC-0063 (Region Handles), RFC-0065 (Ergonomics), RFC-0066 (Extraction),
RFC-0067 (Reference Types), RFC-0068 (Struct-Owned Regions), RFC-0069 (Sub-Region Typing),
RFC-0071 (Ownership and Move Semantics), RFC-0072 (Negative Bounds), RFC-0003 (Concurrency),
and the design explorations in `substructural-and-separation-types.md` and
`per-field-multiplicities.md`.*

> **Status of effect syntax**: The `^`, effect aspect declarations, and effect-polymorphic
> bounds described in this report are **proposed** — not yet specified in any RFC and not
> implemented. All other syntax follows the current language spec and the accepted RFC-006x
> cluster.

---

## What this document covers

Effect marker aspects are a lightweight effect-tracking mechanism that extends the existing
`Send`/`Sync` marker-aspect pattern to side effects. A function declares what effects it
may perform using a `^` annotation; the effect set propagates through the call graph; and
the type system enforces that callers have the required effect permission before calling
effectful code. No handlers, no continuations, no new runtime machinery — only
type-system bookkeeping over constructs the language already has.

This report analyses how that mechanism would interact with Metel's memory model and
ownership system as settled by the RFC-006x cluster and RFC-0071. Most of the integration
story is straightforward because marker aspects are already in the language; the main
design questions concern the effect lattice and the treatment of higher-order functions.

---

## 1. The existing marker-aspect pattern

Metel already uses zero-size marker aspects for capabilities the type system tracks without
runtime cost:

```metel
aspect Send {}   // value may cross fiber boundaries
aspect Sync {}   // value may be shared across threads
```

A type implements `Send` if and only if all its fields do. The type checker enforces this
transitively. No code beyond the declaration is needed; the aspect is a pure type-level
claim.

Effect marker aspects follow the same pattern exactly. The only new surface is the `^`
annotation position and the rule that `^` annotations propagate through calls.

---

## 2. Declaring effects

An effect is an aspect with no methods:

```metel
aspect IO  {}
aspect Net: IO {}    // Net implies IO — performing a network call is an IO action
aspect Alloc {}      // heap allocation (separate from region allocation)
aspect Panic {}      // may terminate the process abnormally
```

The superaspect relationship (`Net: IO`) encodes effect subsumption: any context that
permits `IO` also permits `Net`-implementing functions to perform their IO actions, but a
context that permits only `Net` does not automatically permit arbitrary `IO`. The lattice
is the aspect hierarchy.

A function that performs no effects is pure — it carries no `^` annotation. Purity is the
absence of effect claims, not a special marker.

---

## 3. Declaring effect requirements

The `^` annotation appears after the return type:

```metel
fun println(s: String) ^ IO { ... }
fun fetch(url: String) -> Bytes ^ Net { ... }
fun allocate<T>(size: USize) -> @[Heap] T ^ Alloc { ... }

// multiple effects
fun process(url: String) -> Bytes ^ IO, Net, Alloc { ... }

// pure — no annotation
fun add(a: I32, b: I32) -> I32 { a + b }
```

A function may only call effectful functions if it declares at least those effects itself.
Calling `println` from a function with no `^` annotation is a type error. This is the
entire enforcement rule; it is a simple inclusion check, not unification.

---

## 4. Effect propagation and polymorphism

The effect set propagates upward through the call graph. A function that calls `println`
must declare `^ IO`; a function that calls that function must also declare `^ IO`; and
so on to `main`.

`main` is the effect root. It may declare any effects — this is where the real world
enters. Functions that are reachable only from `main` with the appropriate effect
permissions form the effect boundary.

**Effect-polymorphic functions** accept a closure and propagate its effect set:

```metel
fun map<T, U, E>(xs: List<T>, f: fun(T) -> U ^ E) -> List<U> ^ E {
    // apply f to each element; whatever effects f has, map has
}

fun filter<T, E>(xs: List<T>, pred: fun(&T) -> Bool ^ E) -> List<T> ^ E { ... }
```

The type variable `E` ranges over effect sets. The effect set of `map` is exactly the
effect set of the closure it receives — no more, no less. A pure closure makes `map` pure;
an `IO` closure makes `map` carry `^ IO`.

This is the most important composability property: higher-order combinators do not need to
know what effects their callbacks perform. The effect variable abstracts over the effect
set the same way a type variable abstracts over the element type.

---

## 5. Interaction with the memory model

### 5.1 Allocation as an effect

Region allocation in Metel (`@[r] expr`) is already infallible for `AllocationError = !`
regions (RFC-0063 §1.1). The physical allocation is not tracked as an effect — it is
backed by an already-held region handle, and the type-level record of that allocation is
the pointer tag `@[r] T`, not a side effect in the `^` sense.

What `^ Alloc` would track is **global heap allocation** — calls that ultimately reach
`malloc` or the system allocator without a region backing them. This is a narrower claim
than "any allocation happens here." Region-backed allocation is controlled entirely through
the region handle in the bracket channel; no `^ Alloc` annotation is needed or meaningful
for it.

This distinction is useful: a function that only allocates into a caller-supplied region
`[r]` is `^ !Alloc` (pure with respect to global allocation), even if it does a lot of
work on region-backed data. This is a stronger guarantee than most languages can express.

```metel
// no Alloc effect — all allocation goes through the supplied region r
fun build_graph[r](nodes: List<NodeSpec>) -> @[r] Graph ^ IO {
    // reads node specs (IO), allocates into r (region, not Alloc)
    ...
}

// Alloc effect — returns a Heap-backed value
fun build_graph_heap(nodes: List<NodeSpec>) -> @[Heap] Graph ^ IO, Alloc {
    ...
}
```

### 5.2 Sendability and effects across fibers

RFC-0003 introduces fiber-level parallelism. A closure spawned into a fiber must implement
`Send` (RFC-0063 §4). The effect system interacts with this in a natural way: a closure
carries its effect annotations as part of its type, and those annotations don't change
when the closure crosses a fiber boundary.

However, effects that are inherently thread-local — such as `LocalHeap` access or
thread-local storage — can be expressed as non-`Send` capabilities rather than `^`
effects. The two systems are complementary:

```metel
aspect ThreadLocalIO {}   // can only be performed on the current thread
```

A closure `^ ThreadLocalIO` that also requires `Send` would be a type error if
`ThreadLocalIO` is declared as `!Send`. This links the effect system to the existing
sendability rules without new machinery.

### 5.3 Effects and borrowed references

References `&T` and `&mut T` are always non-sendable (RFC-0067). A closure that captures
an `&mut T` is not `Send` regardless of its effect annotation. The two constraints are
independent and compose correctly: a closure may be `^ IO` and also non-`Send` due to
a captured `&mut T` borrow.

The effect annotation does not encode whether the function borrows or mutates its
arguments — that is expressed in the argument types themselves via `&` vs `&mut`. The
`^` annotation encodes only external interactions (I/O, network, global allocation, panic).

### 5.4 Drop and effects

`Drop::drop` can in principle perform effects: a `FileHandle::drop` closes a file
descriptor, which is `^ IO`. This creates a tension: code that holds a `FileHandle` and
then goes out of scope implicitly performs `^ IO` at drop time, but the enclosing function
may not have declared `^ IO`.

There are two coherent positions:

**Position A — drops are exempt.** `Drop::drop` is called by the runtime's cleanup path
and not counted as an effect of the enclosing function. This is pragmatically necessary:
requiring every function that might hold a drop-implementing value to declare all effects
of that value's destructor is unworkable. The effect system tracks *deliberate* effects,
not cleanup.

**Position B — effect-annotated drop impls.** `Drop` implementations may carry `^`
annotations, and the borrow checker ensures a function can only hold a `T: Drop ^ E` value
if the function declares `^ E`. This is stricter but consistent with the principle that
effects must be declared.

Position A is the practical starting point. Position B is correct in principle but likely
too burdensome — the compiler would need to track effect sets through the type of every
binding. The tradeoff is deferred.

---

## 6. The effect lattice

Effect aspects form a partial order via the superaspect hierarchy. This is a lattice with:

- **Top**: the set of all effects (no restriction)
- **Bottom**: the empty effect set (pure)
- **Meet** (most specific common upper bound): union of two effect sets
- **Join** (most general common lower bound): intersection

The subtyping rule is: a function with effect set `E₁` may be used where `E₂` is expected
if `E₁ ⊆ E₂` — fewer effects is a subtype of more effects, because a pure function can be
called anywhere an effectful function could be called. This matches the intuition: a pure
computation is always safe to use in an effectful context; an effectful computation cannot
substitute for a pure one.

```metel
// f expects a possibly-IO closure
fun run(f: fun() -> () ^ IO) { f() }

// passing a pure closure — legal, since {} ⊆ {IO}
run(fun() -> () { 42 })

// passing an IO closure — legal
run(fun() -> () ^ IO { println("hi") })

// passing a Net closure — legal if Net: IO (Net ⊆ {IO} via superaspect)
run(fun() -> () ^ Net { fetch("...") })
```

---

## 7. Usage examples

### 7.1 Separating pure computation from I/O

```metel
// Pure — no I/O, no allocation, no effects
fun compress(data: &[U8]) -> Vec<U8> { ... }

// Reads from disk (IO), compresses (pure), writes back (IO)
fun compress_file(path: &String) ^ IO {
    let data = read_file(path);   // ^ IO
    let compressed = compress(&data);   // pure
    write_file(path, &compressed);   // ^ IO
}
```

The type of `compress` documents that it can be called from any context — test harnesses,
pure functions, sandboxed environments — without any effect permissions. The caller of
`compress_file` knows at a glance that disk access happens.

### 7.2 Effect-polymorphic iterators

```metel
fun for_each<T, E>(xs: &List<T>, f: fun(&T) -> () ^ E) ^ E {
    match xs {
        List::Nil {}       => {}
        List::Cons { head, tail } => {
            f(head);
            for_each(tail, f);
        }
    }
}

// With a pure closure — for_each is pure
for_each(&items, fun(x) { sum += x.value });

// With an IO closure — for_each carries ^ IO
for_each(&items, fun(x) ^ IO { println(x.name) });
```

### 7.3 Sandboxed computation

A function that explicitly takes no effect parameters and declares no `^` annotation is
provably sandboxed — it cannot perform I/O, network calls, or panics regardless of what
closures it is given (because those closures must also be pure to satisfy the type check):

```metel
// Provably cannot perform I/O or panic — accepts only pure closures
fun evaluate_expression(expr: Expr, env: &Env) -> Value {
    ...   // any closure called inside must also be pure
}
```

This is a stronger isolation guarantee than capabilities or effect systems that rely on
runtime checks. It is a compile-time guarantee: no code path reachable from this function
can perform an effect.

### 7.4 Interaction with struct-owned regions (RFC-0068)

```metel
struct Parser[own r] {
    source: String,
    nodes:  @[r] List<AstNode>,
}

impl Parser {
    // Reads source (pure — already in memory), allocates into r (region, not Alloc)
    // No IO, no Alloc effect — allocation is through the owned region
    fun parse(self: &mut Parser) -> @[r] AstNode { ... }
}
```

The `Parser::parse` method carries no `^` annotation because all its side effects
(building the AST) are captured in the region `r`'s type-level tag. The effect-annotation
system and the region system are genuinely complementary here: the region tracks *what was
allocated*, while the effect annotation tracks *what external interactions occurred*.

---

## 8. Summary table

| Property | Effect marker aspects |
|---|---|
| Effect declaration | Marker aspects with `^` annotation |
| Effect propagation | Upward through call graph; polymorphic via `E` variable |
| Handlers | None — cannot intercept or mock effects |
| Runtime cost | Zero — pure type erasure |
| New syntax | `^` annotation; aspect declarations |
| New runtime | None |
| Fits metel's philosophy | Excellent — extends existing `Send`/`Sync` pattern |
| Algebraic effects upgrade | Compatible — `^` annotations can survive if handlers are added |

---

## 9. What effect marker aspects do not provide

This system tracks *what* effects a computation may perform. It does not provide:

- **Interception.** There is no way to observe or redirect an effect; you cannot test code
  by swapping its I/O implementation for a mock. That requires algebraic effects
  (`algebraic-effects-and-memory-model.md`).
- **Effect count or ordering.** Whether `^ IO` fires once or a hundred times is invisible
  to the type system. A function with `^ IO` might perform no I/O in some branches;
  the annotation is an upper bound, not an exact description.
- **Effect-conditional control flow.** There is no way to express "this function performs
  I/O if and only if the condition is true." The annotation is per-function, not
  per-branch.
- **Resource acquisition guarantees.** Whether the I/O succeeds, and what happens if it
  doesn't, is expressed through the return type (`Perhaps<T>`, `Result<T, E>`) — not the
  effect system.

These limitations are not bugs — they are the design point. Effect marker aspects are the
lightest possible effect-tracking system: they add documentation enforced by the compiler
without any runtime overhead or language redesign. The gap between what they track and what
algebraic effects track is the gap between "I know it may happen" and "I can intercept
when it happens."

---

## 10. Relationship to the other effect proposals

| | Marker aspects | Capability objects | Algebraic effects |
|---|---|---|---|
| Tracks effect presence | Yes | Yes (by capability holding) | Yes |
| Handlers / interception | No | No | Yes |
| Linear / one-shot resources | No (use `Drop`) | Yes (linear capability) | Partial |
| Runtime overhead | Zero | Zero (zero-size) | Continuation allocation |
| Implementation complexity | Low | Medium | High |
| Testability improvement | Documentation only | Documentation only | Full mock/intercept |

The three proposals are not mutually exclusive. Marker aspects could serve as the base
layer (static documentation of what effects exist), capability objects as the enforcement
layer for resource acquisition, and algebraic effects as an opt-in layer for the subset of
effects where interception is valuable (testing, dependency injection, async I/O).
