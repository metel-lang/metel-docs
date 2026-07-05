---
id: capability-objects
title: "Capability Objects"
type: report
created_date: '2026-06-29'
rfcs: [0003, 0063, 0065, 0066, 0067, 0068, 0069, 0071, 0072]
reports: [substructural-and-separation-types, per-field-multiplicities, algebraic-effects-and-memory-model, effect-marker-aspects]
---

# Capability Objects

*Grounded in RFC-0063 (Region Handles), RFC-0065 (Ergonomics), RFC-0066 (Extraction),
RFC-0067 (Reference Types), RFC-0068 (Struct-Owned Regions), RFC-0069 (Sub-Region Typing),
RFC-0071 (Ownership and Move Semantics), RFC-0072 (Negative Bounds), RFC-0003 (Concurrency),
and the design explorations in `substructural-and-separation-types.md` and
`per-field-multiplicities.md`.*

> **Status of capability syntax**: The `using`/`given` implicit-passing constructs
> described in this report are **proposed** — not yet specified in any RFC and not
> implemented. The `linear struct` and `phantom linear ()` patterns draw on the
> `per-field-multiplicities.md` design exploration. All other syntax follows the current
> language spec and the accepted RFC-006x cluster.

---

## What this document covers

Capability objects are a mechanism for controlling access to effects by making access a
*value* — a first-class object the caller must possess and pass to functions that perform
that effect. The mechanism requires no handlers, no continuations, and no new type-system
primitives beyond what Metel already has for linear and affine ownership. What it does
require is a convenient way to thread capabilities through the call stack without making
every function signature explicitly list them.

This report analyses how the capability-object pattern would interact with Metel's memory
model and ownership system as settled by the RFC-006x cluster and RFC-0071. The integration
story is mostly natural — capabilities are values, and Metel already has a rich ownership
system for values. The main design surface is the implicit-parameter mechanism and the
interaction with linear capabilities.

---

## 1. The capability pattern

A capability is a struct value that grants access to an effect. Possessing the value
(holding a borrow of it, or owning it) is the permission; not possessing it is the
denial. The type checker enforces that the permission is held before the effectful
operation is invoked — not by an annotation, but by the normal parameter-passing rules:
if `println` requires `&IOCap` as an argument, and you don't have an `IOCap`, the call
does not type-check.

```metel
struct IOCap {}     // zero-size; grants permission to perform I/O
struct NetCap {}    // grants permission to open network connections

fun println(s: String, io: &IOCap) { ... }
fun fetch(url: String, net: &NetCap) -> Bytes { ... }
```

Capability values are zero-size by default. They exist solely at the type level — the
compiler erases them entirely. Holding `&IOCap` costs nothing at runtime; the only cost
is that the permission must appear in the call stack.

---

## 2. Implicit parameter threading with `using`/`given`

Explicit capability passing is safe but verbose. Every function in a call chain must name
the capability explicitly, even if it only passes it through to a callee. This is the
capability analogue of the "function colouring" problem — though more localised, since
capabilities are values rather than a viral type qualifier.

The `using`/`given` mechanism solves this by letting the compiler thread capabilities
through calls automatically:

```metel
given io: IOCap {
    println("hello");   // io passed implicitly to println
    println("world");   // and here
    inner_function();   // and transitively to any callee that needs &IOCap
}

fun inner_function() using io: &IOCap {
    println("from inner", io);   // io available without being passed explicitly
}
```

A `given` block introduces a capability into the implicit-parameter scope. A function
declared `using cap: &T` receives `cap` implicitly from the innermost enclosing `given`
block that provides `T`. The capability's type is the dispatch key — if two `given` blocks
in scope provide distinct types, the compiler routes each `using` parameter to the right
one.

This is a scoped implicit-parameter mechanism, not a global registry. No `given` block
affects code outside its lexical scope; capability access is always bounded by a block.

---

## 3. Capability types and the ownership model

### 3.1 Shared capability — `&CapType`

Most capabilities are non-exclusive: many call sites may use I/O simultaneously, and
there is no meaningful sense in which one "owns" the permission to print a line. The
standard form is a shared borrow:

```metel
fun println(s: String, io: &IOCap) { ... }
```

`&IOCap` is the borrow of a value held in the enclosing `given` block. The reference
is non-escaping (RFC-0067 §2): it cannot outlive the `given` block that introduced the
capability, which is exactly the right lifetime — the permission is scoped to the block.
No lifetime annotation is needed; the existing borrow rules enforce it for free.

### 3.2 Exclusive capability — `&mut CapType`

Some effects are inherently exclusive: writing to a file, consuming a token from a
limited-use pool, or modifying a shared data structure. The exclusive borrow form grants
write-exclusive access:

```metel
struct TransactionCap {}   // exclusive — at most one writer at a time

fun write_record(record: &Record, tx: &mut TransactionCap) { ... }
```

While `&mut TransactionCap` is held by one caller, no other caller can use `&mut
TransactionCap`. This is not a new rule — it is the existing `&mut` exclusivity rule
(RFC-0067 §3). The capability object is merely a zero-size witness that is subject to the
same rules as any other value.

### 3.3 Linear capability — exactly-once consumption

The most restrictive form uses the `linear struct` / `phantom linear ()` pattern from the
`per-field-multiplicities.md` exploration:

```metel
struct AuthToken {
    phantom linear (),   // one-time-use: must be consumed exactly once
    token: Bytes,
}

fun authenticate(server: &Server, token: AuthToken) -> Session {
    // consumes token — it cannot be used again
    ...
}
```

A `linear struct` must be consumed exactly once — it cannot be dropped (no `Drop` impl),
cannot be copied (no `Copy` impl), and cannot be forgotten. If `authenticate` is never
called with `AuthToken`, the program does not type-check. This enforces that the token is
always used, never silently discarded.

Linear capabilities integrate with RFC-0071's ownership and move semantics without
modification: `AuthToken` moves into `authenticate`, and after the move the binding is
gone. The "use exactly once" guarantee is the standard affine rule with the added
non-droppability constraint from the `phantom linear ()` field.

### 3.4 Typestate capability

Capabilities may carry a phantom state parameter to track whether they have been used or
are in a valid state:

```metel
struct FileHandle<State> {
    fd: I32,
    phantom State,
}

struct Open {}
struct Closed {}

fun read(f: &FileHandle<Open>) -> Bytes { ... }
fun close(f: FileHandle<Open>) -> FileHandle<Closed> { ... }
// FileHandle<Closed> has no useful methods; the type system prevents use-after-close
```

This is the typestate pattern from `substructural-and-separation-types.md`. The capability
object (`FileHandle`) encodes resource state in its type parameter; the consuming method
`close` takes ownership and returns a different type. The borrow checker prevents the
caller from using `f` after `close` returns.

---

## 4. Capability scoping and region interaction

### 4.1 The `given` block as a region analogue

A `given` block is structurally similar to a `BumpRegion::scoped` or `AutoRegion::scoped`
block: it introduces a value into scope, makes it available within the block, and removes
it when the block exits. The analogy is close enough that the two compose naturally:

```metel
AutoRegion::scoped([r]() -> {
    given io: IOCap {
        let buf = @[r] read_into_region(io);   // capability threading + region allocation
        process(&buf);
    }   // io leaves scope; r still valid
});    // r freed; buf unreachable
```

The `IOCap` is scoped to the inner `given` block. The region pointer `@[r] Bytes` is
scoped to the outer `AutoRegion::scoped` block. The two lifetimes are independent and
compose without friction because both are enforced by the borrow checker using the same
underlying rules.

### 4.2 Sendability of capabilities

A capability held as `&IOCap` is a reference and is therefore never sendable (RFC-0067).
A capability held by ownership (`IOCap`) is sendable if `IOCap` implements `Send`
(RFC-0063 §4). Most capabilities should implement `Send` — the permission to do I/O is
not inherently tied to a particular fiber.

Linear capabilities require care: moving a `linear struct` capability into a spawned
closure transfers the obligation to consume it to that fiber. If the fiber may panic, the
obligation is unmet — this is a soundness concern similar to the linear continuation issue
in algebraic effects. The resolution is the same: linear capabilities require the spawned
context to guarantee consumption (e.g., through a structured join combinator from
RFC-0003/RFC-0064 rather than fire-and-forget `spawn`).

### 4.3 Capability stored in a struct-owned region

A capability may be stored in a struct that owns its region (`[own r]`), making the
capability's lifetime the struct's lifetime:

```metel
struct Session[own r] {
    conn: @[r] Connection,
    cap:  NetworkCap,
}

impl Session {
    fun request(self: &mut Session, path: &String) -> @[r] Response {
        fetch(self.conn, path, &self.cap)
    }
}
```

The `NetworkCap` is owned by the `Session` struct. Any code that has a `&mut Session`
implicitly has access to `self.cap` without additional `given` blocks. The capability's
scope is the struct's lifetime — when the session is dropped, the capability is gone.

---

## 5. Effect isolation via capability absence

The most powerful property of capability objects is that absence of a capability is a
**compile-time guarantee of isolation**. A function that neither receives a capability
nor contains a `given` block introducing one cannot perform the guarded effect — no
matter what code it calls, because any callee that needs the capability must receive it
through the type system.

```metel
// No IOCap in scope — provably cannot perform I/O
// This is verifiable without reading the function body
fun parse_expression(tokens: &[Token]) -> Expr { ... }

// Can only be called from within a `given io: IOCap` scope
fun log_expression(expr: &Expr) using io: &IOCap { ... }
```

This is a stronger isolation guarantee than `^` effect annotations in one respect: the
isolation is enforced by the *absence* of a value in scope, which the borrow checker
verifies precisely. An `^` annotation is an upper-bound claim about what *may* happen; a
missing capability is an exact claim about what *cannot* happen.

The tradeoff is expressiveness: `using` is less flexible than `^` for higher-order
functions. A capability-polymorphic higher-order function must somehow express "I thread
whatever capabilities the closure needs" — which requires either a `given`-forwarding
mechanism, explicit capability parameters, or both.

---

## 6. Capability polymorphism and higher-order functions

The main design challenge for capability objects is higher-order functions. A function
`map` that applies a closure to each list element must forward whatever capabilities the
closure needs:

```metel
// Explicit capability threading — verbose
fun map<T, U, C>(
    xs: &List<T>,
    cap: &C,
    f: fun(&T, &C) -> U
) -> List<U> { ... }

// Using `given` forwarding — the `given` block in the caller propagates to the closure
fun map<T, U>(xs: &List<T>, f: fun(&T) -> U) -> List<U> {
    xs.map(f)   // f is called inside; if it has `using` parameters, they are forwarded
                // from the `given` scope at the call site
}
```

The `given` forwarding model is cleaner: the compiler sees that `f` has `using io: &IOCap`
and verifies that an `IOCap` is in the `given` scope at the site where `map` is called.
The `map` function itself need not mention `IOCap` — it is transparent to capabilities it
does not use directly.

This is analogous to how effect-polymorphic functions work with the `^` annotation system:
the outer function does not enumerate the inner closure's effects; it simply propagates
whatever effects appear. The difference is the mechanism: `^` uses a type variable; `given`
uses lexical scope.

---

## 7. Usage examples

### 7.1 Testing via capability substitution

The practical value of capability objects for testing: substitute a mock capability in
tests without changing the code under test.

```metel
// Production code
struct FilesystemCap { root: String }

fun read_config(path: &String, fs: &FilesystemCap) -> Config {
    let raw = fs.read_file(path);
    parse_config(&raw)
}

// Test — supply an in-memory capability
struct FakeFsCap { files: Map<String, Bytes> }

// FakeFsCap implements the same interface as FilesystemCap
fun test_read_config() {
    let fake_fs = FakeFsCap { files: Map::from([("/config.toml", b"debug = true")]) };
    let config = read_config("/config.toml", &fake_fs);
    assert(config.debug == true);
}
```

This works because `read_config` accepts any value that satisfies the filesystem interface.
If `FilesystemCap` and `FakeFsCap` both implement a `Filesystem` aspect, the function is
fully substitutable. Note that this requires an *aspect* (`Filesystem`) over the capability
type — it is not as automatic as an algebraic effect handler, which intercepts at the
call site without modifying the function signature.

### 7.2 Scoped permission grant

```metel
fun restricted_parse(input: &String, grant: &mut ParseBudget) -> Result<Ast, ParseError> {
    // grant.decrement() fails if budget is exhausted
    grant.decrement(input.len())?;
    parse_inner(input)
}

given budget: ParseBudget { budget_remaining: 1024 } {
    let ast1 = restricted_parse(&query1, &mut budget)?;
    let ast2 = restricted_parse(&query2, &mut budget)?;
    // budget shared across both calls; both charge against the same limit
}
```

The `ParseBudget` capability enforces a resource limit without a global counter or runtime
injection. The `given` block scopes the limit to the two parses; when the block exits, the
budget object is dropped and any remaining budget is released.

### 7.3 Linear capability for one-shot initialisation

```metel
struct InitToken {
    phantom linear (),
}

fun initialise_subsystem(token: InitToken) {
    // token consumed here — cannot call initialise_subsystem twice
    ...
}

// Only one InitToken is ever created
let token = unsafe { InitToken::new_once() };   // runtime panic if called twice
initialise_subsystem(token);
// token is gone; initialise_subsystem cannot be called again
```

The `linear struct` / `phantom linear ()` pattern enforces single-use at compile time where
possible and detects misuse at the creation site otherwise. The combination of a linear
capability and a single-creation guard gives a strong single-initialisation guarantee.

### 7.4 Capability with struct-owned region and SubRegion

```metel
struct RequestContext[own r] {
    io_cap:   IOCap,
    net_cap:  NetCap,
    scratch:  @[r] BumpRegion,   // sub-arena for request-scoped scratch data
}

impl RequestContext {
    fun handle(self: &mut RequestContext, path: &String) -> @[r] Response {
        let url = fetch(path, &self.net_cap);       // uses net capability
        let body = @[r] parse_response(&url);       // allocates into owned region
        log_request(path, &self.io_cap);            // uses io capability
        body
    }
}
```

All capabilities (`io_cap`, `net_cap`) are owned by the `RequestContext`. The owned region
`r` provides scratch allocation with the same lifetime as the request context. When the
request context is dropped, the region is freed and the capabilities are dropped. No
`given` block is needed inside the `impl` block because the capabilities are struct fields
— implicit field access already provides them.

---

## 8. Summary table

| Property | Capability objects |
|---|---|
| Effect declaration | Hold a value; borrow implies permission |
| Effect propagation | Explicit via `using`/`given`; transparent for closures |
| Handlers | None — cannot intercept effects |
| Runtime cost | Zero — capability structs are zero-size |
| New syntax | `using`/`given` implicit parameter blocks |
| New runtime | None |
| Fits metel's philosophy | Good — capabilities are first-class values |
| Linear / one-shot resources | Natural via `linear struct` / `phantom linear ()` |
| Typestate | Natural via phantom type parameters |

---

## 9. What capability objects do not provide

- **Interception.** Like marker aspects, capability objects cannot redirect or mock an
  effect at the call site without changing the function signature. Testing requires passing
  a mock capability that implements the same interface — a structural change, not a
  transparent swap. Compare with algebraic effects, where the handler intercepts with no
  change to the function under test.

- **Effect-set visibility.** There is no type-level summary of "this function may perform
  IO and Net." The effects are visible only by reading the function's `using` parameters.
  The `^` annotation system (`effect-marker-aspects.md`) provides this visibility
  explicitly; capability objects leave it implicit in the parameter list.

- **Handlers.** Neither the marker-aspect system nor the capability-object system supports
  delimited continuations or `resume`. For coroutine-like or async-like patterns, algebraic
  effects (`algebraic-effects-and-memory-model.md`) are necessary.

---

## 10. Relationship to the other effect proposals

| | Marker aspects | Capability objects | Algebraic effects |
|---|---|---|---|
| Tracks effect presence | Yes | Yes (implicitly, via `using`) | Yes |
| Effect summary in type | Yes (`^` annotation) | No (read `using` params) | Yes (`^` annotation) |
| Handlers / interception | No | No | Yes |
| Linear / one-shot resources | No (use `Drop`) | Yes (linear capability) | Partial |
| Typestate | No | Yes (phantom type params) | No |
| Runtime overhead | Zero | Zero | Continuation allocation |
| Implementation complexity | Low | Medium | High |
| Testing improvement | Documentation only | Mock via interface | Full interception |

Capability objects and marker aspects address partially overlapping concerns and are
composable: a function can declare `^ IO` (marker aspect, for static documentation) and
also require `using io: &IOCap` (capability, for enforcement). The `^` annotation
documents the effect class; the capability object enforces that access is explicitly
granted. Used together, they provide both the bird's-eye view (what effects exist) and
the enforcement layer (who is allowed to perform them).
