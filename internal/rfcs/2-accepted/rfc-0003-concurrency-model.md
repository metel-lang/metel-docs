---
id: rfc-0003
title: "Concurrency Model"
date: '2026-05-20'
status: accepted
---

## Summary

Define Metel's concurrency model: fiber handles with linear ownership, typed channels as the primary communication primitive, a `select` expression for multiplexing, and a `Send` marker aspect to prevent data races. Concurrency syntax (`spawn`, `<-`, `->`, `select`) desugars to aspect implementations on standard library types, consistent with Metel's general philosophy that syntax sugar maps to aspect method calls. Fibers are first-class values with linear handles — fire-and-forget is possible but must be explicit via `.detach()`.

---

## Motivation

Metel's current spec has no concurrency primitives. Adding them now, before the pointer RFC (RFC-0001) is finalised, is important because the two designs are coupled: `*mut T` in a concurrent setting creates data races unless the type system or runtime prevents them. Resolving the concurrency model first lets RFC-0001 make the right choices about pointer transferability.

The three problems concurrency must address:

1. **Parallelism** — doing multiple things at once (CPU-bound work across cores)
2. **I/O multiplexing** — waiting on multiple sources without blocking an OS thread per source
3. **Coordination** — communicating results and signalling termination between concurrent tasks

---

## Design Philosophy

### Syntax desugars to aspect implementations

Metel's existing surface syntax desugars to aspect method calls: `?` desugars to `From`/`Into`, `+` to `Add::add`, `for x in iter` to `Iterator::next`. Concurrency operators follow the same pattern:

| Syntax | Desugars to |
|--------|-------------|
| `spawn { expr }` | `Spawnable::spawn(|| expr) -> Fiber<T>` |
| `ch <- value` | `Sendable::send(&ch, value)` |
| `<- ch` | `Receivable::recv(&ch) -> Perhaps<T>` |
| `select { ... }` | `Selectable::select(...)` |

Any type implementing the relevant aspect participates in the syntax. This means user-defined channels, mock channels in tests, and alternative spawning strategies are all first-class without special-casing in the compiler.

### No function colouring

Launching a fiber does not require functions to be declared differently. There is no `async fn` — a function that blocks inside a fiber does not need a different signature. The runtime schedules around blocking transparently.

### Communicate by transferring ownership

Values are *moved* into channels, not shared. Fibers own their data; ownership transfers when a value is sent. The `Send` marker aspect enforces this at compile time — only `Send` types can cross fiber boundaries.

---

## Proposed Design

### Aspects

Four aspects govern concurrency syntax:

```metel
aspect Spawnable {
    type Output;
    fun spawn(f: fun() -> Self::Output) -> Fiber<Self::Output>;
}

aspect Sendable<T> {
    fun send(self: &Self, value: T);
}

aspect Receivable<T> {
    fun recv(self: &Self) -> Perhaps<T>;       // blocking: waits until a value is available or channel closes
    fun try_recv(self: &Self) -> Perhaps<T>;   // non-blocking: returns nope immediately if no value is ready
}

aspect Selectable {
    fun register(self: &Self, selector: &Selector);
}
```

The standard library types `Fiber<T>`, `Chan<T>`, `SendChan<T>`, `RecvChan<T>` implement these aspects. User-defined types may also implement them to participate in concurrency syntax.

---

### Fiber handles and linearity

`spawn { expr }` returns a `Fiber<T>` handle. `Fiber<T>` is a **linear type** — it must be explicitly consumed. This makes accidental fire-and-forget of a meaningful fiber a compile error:

```metel
let f: Fiber<Int> = spawn { compute() };
let result = f.join();   // blocks until done, consumes handle
```

**Explicit fire-and-forget** is allowed via `.detach()`, which consumes the handle and releases the linearity constraint:

```metel
spawn { log_event(data) }.detach();   // explicit discard
```

A bare `spawn { }` statement (without binding) implicitly calls `.detach()`:

```metel
spawn { log_event(data) };   // sugar for .detach() — intentional, not accidental
```

The two uses are distinct at the type level. Holding a `Fiber<T>` and never joining or detaching it is a compile error, caught by the linearity checker (RFC-0028).

**Panic isolation:** Because fibers have handles, a fiber's panic does not terminate the program. The panic is captured as an error value in the handle's result. `f.join()` returns `Result<T, Panic>` rather than `T`. A detached fiber that panics has no handle — its panic terminates the program (Go model), since there is no owner to report to. This gives a clean semantic distinction: owned fibers are isolated; detached fibers are program-terminating on panic.

---

### Channel types

`Chan<T>` is a typed, bidirectional, first-class channel. Both unbuffered and buffered variants exist:

```metel
let ch: Chan<Int> = Chan::new();          // unbuffered
let ch: Chan<Int> = Chan::buffered(16);   // buffered
```

**Directional subtypes** fall out naturally from the aspect model: `SendChan<T>` implements `Sendable<T>` only; `RecvChan<T>` implements `Receivable<T>` only; `Chan<T>` implements both. The typechecker enforces directionality through aspect resolution — no special language syntax required.

```metel
Chan<T>       // Sendable<T> + Receivable<T>
SendChan<T>   // Sendable<T> only
RecvChan<T>   // Receivable<T> only
```

`Chan<T>` coerces to `SendChan<T>` or `RecvChan<T>` where the narrower type is expected.

---

### Send and receive operators

**Send** — `ch <- value`:

```metel
ch <- 42;   // desugars to Sendable::send(&ch, 42)
            // blocks if unbuffered and no receiver is ready
```

Send moves `value` into the channel. `value` is no longer accessible in the sending fiber after this point.

**Receive** — `<- ch`:

```metel
let x = <- ch;   // desugars to Receivable::recv(&ch) -> Perhaps<Int>
                 // blocks until a value is available or channel closes
```

`<- ch` returns `Perhaps<T>`:
- `Perhaps::Some { value }` — a value was received
- `nope` — the channel is closed and drained

```metel
while let Perhaps::Some { value: x } = <- ch {
    process(x);
}
```

**Non-blocking receive** — `ch.try_recv()`:

```metel
let x = ch.try_recv();   // desugars to Receivable::try_recv(&ch) -> Perhaps<Int>
                         // returns nope immediately if no value is ready
```

Use `try_recv()` inside `select` arms or polling loops where blocking is not acceptable. `<- ch` is always blocking; `try_recv()` is always non-blocking.

**Close** — `ch.close()`: marks the channel closed. Further sends panic. Receivers drain buffered values, then receive `nope`.

---

### The `select` expression

`select` waits on multiple channel operations simultaneously, executing the first ready arm. It is an expression — every arm produces a value of the same type. Under the hood it desugars to `Selectable::register` calls on each arm's operand, with the runtime resolving which arm fires.

```metel
let result = select {
    v <- ch1       => process(v),
    ch2 <- payload => "sent",
    else           => "would block",   // optional: non-blocking
}
```

`else` is optional. Without it, `select` blocks until one arm is ready. With `else`, it returns immediately if no arm is ready.

**Timeout** — a timer type implements `Selectable`, making timeout a natural `select` arm rather than a special language construct:

```metel
let result = select {
    v <- data_ch             => Perhaps::Some { value: v },
    _ <- Chan::timeout(5_s)  => nope,
}
```

`Chan::timeout(duration) -> RecvChan<Unit>` returns a channel that receives a single `Unit` value after the duration elapses. No special timeout syntax is needed.

If multiple arms are ready simultaneously, one is chosen at random. This prevents starvation but means `select` with multiple ready arms is non-deterministic.

---

### Joining fibers

`Fiber<T>` provides:

```metel
fun join(self: Fiber<T>) -> Result<T, Panic>   // blocks, consumes handle
fun detach(self: Fiber<T>)                      // fire-and-forget, consumes handle
```

Joining a collection of fibers:

```metel
let results = [f1, f2, f3].map(Fiber::join);
```

`WaitGroup` is not a language primitive — it is a library pattern built on top of fiber handles and channels for cases where the number of fibers is dynamic.

---

### The `Send` marker aspect

`Send` is a marker aspect — no methods. A type that is `Send` can be moved across fiber boundaries.

```metel
aspect Send {}
```

| Type | `Send`? | Reason |
|------|---------|--------|
| `Int`, `Float`, `boolean`, `String` | yes | primitives — copied |
| Structs with all-`Send` fields | yes | automatic |
| Enums with all-`Send` variants | yes | automatic |
| `Perhaps<T>` where `T: Send` | yes | automatic |
| `Chan<T>` where `T: Send` | yes | channels cross fiber boundaries by design |
| `Fiber<T>` where `T: Send` | yes | handles are `Send` |
| `*T` | **no** | aliased read could race with concurrent write |
| `*mut T` | **no** | shared mutable access — data race |
| `Mutex<T>` where `T: Send` | yes | mutex is the synchronisation mechanism |
| Linear types where all fields are `Send` | yes | linear values move, never alias |

Deriving `Send` is automatic for most types — the programmer does not annotate it. Only types containing `*T` or `*mut T` are not `Send` by default.

---

### The `Sync` marker aspect

`Sync` is a marker aspect — no methods. A type that is `Sync` can be accessed concurrently from multiple fibers via a shared reference without a data race.

```metel
aspect Sync {}
```

The precise relationship: `T: Sync` means that holding multiple read pointers (`*T`) to the same value simultaneously across fibers is race-free. This is a stronger property than `Send` (which governs ownership transfer) — `Sync` governs concurrent access.

| Type | `Sync`? | Reason |
|------|---------|--------|
| `Int`, `Float`, `boolean`, `String` | yes | immutable value semantics — concurrent reads are safe |
| Structs with all-`Sync` fields | yes | automatic |
| Enums with all-`Sync` variants | yes | automatic |
| `*T` | **no** | no lifetime guarantee — pointee may be dropped or mutated through another alias |
| `*mut T` | **no** | concurrent writes through different aliases = data race |
| `Mutex<T>` where `T: Send` | yes | access is serialized by the lock |
| `RwLock<T>` where `T: Send + Sync` | yes | multiple readers serialized by the lock |
| `Atomic<Int>`, `Atomic<boolean>` | yes | atomics are safe for concurrent access by design |
| `Chan<T>` where `T: Send` | yes | channels have internal synchronisation |
| `Arc<T>` where `T: Send + Sync` | yes | reference-counted; no interior mutability |
| Linear types where all fields are `Sync` | yes | linear values move and never alias |

`Sync` is not usually written explicitly. It is derived automatically when all fields are `Sync`, and violated only when a type contains `*T`, `*mut T`, or interior-mutability primitives without synchronisation.

---

### `Arc<T>` — shared ownership across fibers

`Arc<T>` is a reference-counted shared pointer. It is the standard mechanism for sharing a large immutable value (lookup table, config object, compiled structure) across multiple fibers without cloning it into each one.

```metel
let config = Arc::new(load_config());
let c1 = Arc::clone(&config);
let c2 = Arc::clone(&config);

spawn { use_config(c1) };
spawn { use_config(c2) };
```

**Properties:**

- `Arc<T>` is not linear — it can be cloned freely to produce additional handles to the same allocation.
- `Arc<T>: Send` when `T: Send + Sync`. The `Send` bound ensures the value was safe to move into the `Arc`; the `Sync` bound ensures concurrent reads through multiple `Arc` handles are race-free.
- `Arc<T>: Sync` when `T: Send + Sync`.
- `Arc<T>` provides read-only access to the inner value. There is no `Arc::get_mut` in the general case — interior mutability requires `Arc<Mutex<T>>` or `Arc<RwLock<T>>`.

**Shared mutation pattern:**

```metel
let shared = Arc::new(Mutex::new(Counter::new()));
let s1 = Arc::clone(&shared);
let s2 = Arc::clone(&shared);

spawn { s1.lock().increment() };
spawn { s2.lock().increment() };
```

**Prohibition on linear types:**

`Arc<LinearT>` is a type error. A linear value must be owned by exactly one party — reference-counting it would allow multiple owners and defeat the linearity guarantee.

**Lifetime:** when the last `Arc<T>` handle is dropped, the inner value is freed. Reference counting is atomic — `Arc<T>` handles may be dropped from different fibers.

---

## Runtime and primitive layers

The concurrency model rests on a layered implementation stack. Only the top two layers are visible to user code:

```
spawn { } / <- / -> / select      ← syntax, desugars to aspect calls
───────────────────────────────────
Fiber<T>, Chan<T>, Mutex<T>        ← safe stdlib types (implement aspects)
───────────────────────────────────
Thread<T>, Atomic<T>               ← low-level stdlib primitives
───────────────────────────────────
OS primitives (futex, pthread_t)   ← inside unsafe only, stdlib-internal
───────────────────────────────────
M:N runtime scheduler              ← invisible to user code
```

### M:N scheduler

Fibers are lightweight (green threads), M:N scheduled by the language runtime. The programmer launches fibers and forgets about OS threads, cores, and scheduling. The scheduler is an implementation detail of the runtime — it is never exposed to user code.

### `Atomic<T>`

Lock-free atomic operations. Required internally by `Chan<T>`, `Mutex<T>`, and the scheduler itself. Exposed publicly in the stdlib as a safe API for `Atomic<Int>` and `Atomic<boolean>`, since the operations are well-defined and carry no memory unsafety beyond the ordering contract. Memory ordering annotations (acquire, release, sequentially consistent) are explicit parameters.

### `Thread<T>`

A 1:1 OS thread that implements `Spawnable`. Heavier than `Fiber<T>` but has no runtime scheduler dependency — useful for CPU-bound work that must bypass the M:N scheduler, for FFI with thread-local storage requirements, or for embedding Metel in environments without a runtime.

Because `Thread<T>` implements `Spawnable`, `spawn { }` syntax works with it when the declared type is `Thread<T>`. The aspect model makes the two spawning strategies syntactically uniform:

```metel
let f: Fiber<Int>  = spawn { compute() };   // M:N fiber
let t: Thread<Int> = spawn { compute() };   // OS thread
let result = f.join();
let result = t.join();
```

`Thread<T>` is a low-level type. It is available without `unsafe` but is clearly documented as a systems-level escape hatch.

### OS primitives

Futexes, semaphores, `pthread_t`, and similar OS-level constructs are used inside the stdlib to implement `Thread<T>`, `Mutex<T>`, and `Atomic<T>`. They are not exposed outside `unsafe` blocks and are not part of the public API surface.

---

### Standard library concurrency types

| Type | Purpose |
|------|---------|
| `Fiber<T>` | Lightweight M:N-scheduled fiber handle (linear) |
| `Thread<T>` | 1:1 OS thread handle (linear) |
| `Chan<T>` | Typed bidirectional channel |
| `SendChan<T>` | Write-only channel view |
| `RecvChan<T>` | Read-only channel view |
| `Mutex<T>` | Exclusive mutable access. `.lock()` returns a guard; released on drop |
| `RwLock<T>` | Shared read / exclusive write |
| `Atomic<Int>`, `Atomic<boolean>` | Lock-free integer and boolean operations |
| `Arc<T>` | Reference-counted shared ownership. `Send + Sync` when `T: Send + Sync` |

`Mutex<T>` and `RwLock<T>` are `Send` because they wrap the synchronisation mechanism around the value. Internally they use `*mut T` inside `unsafe`, but the public API is safe.

---

## Interaction with RFC-0043 (Regular Pointers)

RFC-0043 is implemented. The pointer surface (`*T`, `*mut T`, `&x`, `&mut x`, `*p`) is settled. RFC-0043 explicitly deferred the question of whether pointers are `Send` to the concurrency RFC. This RFC now resolves that:

1. **`*T` and `*mut T` are not `Send`** — pointers are local-fiber tools. `*T` introduces aliasing to non-linear storage; allowing it to cross fiber boundaries without synchronisation would create data races. `*mut T` additionally allows writes — sharing it is the canonical data race.
2. **`Perhaps<*T>` is not `Send`** — wrapping a non-`Send` type in `Perhaps` does not make it `Send`.
3. **`*mut T` coerces to `*T`** (RFC-0043 §4) — this coercion is unaffected by concurrency rules. Neither end of the coercion is `Send`.
4. **Auto-deref** (RFC-0043 §6) applies to field access, method dispatch, and function pointer calls — unaffected by `Send`.
5. **Pointer equality** (RFC-0043, equality section) is identity equality — unaffected by `Send`.

The `Send`-non-`Send` boundary for pointer types is now fully settled by this RFC. RFC-0043's compatibility constraint ("future concurrency or lifetime model must account for that aliasing explicitly") is satisfied by the `Send` marker aspect defined here.

### Known future tension: scoped concurrency

The `*T: !Send` rule is unconditional. This forecloses one specific future pattern: **scoped fibers** — fibers whose lifetime is bounded by a lexical scope, making it provably safe to send references into the enclosing stack frame without copying. Rust achieves this via `std::thread::scope`, where `&'a T` borrows are tied to the scope's lifetime and become sendable within it.

If Metel later wants scoped fibers that borrow from the enclosing scope, the unconditional `*T: !Send` rule would block naively sending `*T` into them. The clean resolution — consistent with Metel's direction of separate reference types (`@T` for linear read references, future `&'a T` for lifetime-tracked references) — is a dedicated `ScopedFiber<'scope, T>` handle type whose lifetime the borrow checker can reason about, rather than making `*T` conditionally `Send`. This keeps `*T` semantics simple and stable.

This is not a current concern but should be considered when designing the lifetime system (RFC-0028) and when `Fiber<T>` is formalised.

---

## Interaction with RFC-0028 (Memory and Linear Types)

- `Fiber<T>` and `Thread<T>` are linear types. The linearity checker (RFC-0028) enforces that handles must be joined or detached.
- Linear types are `Send` if all their fields are `Send` — channel send is a natural consumption point for linear values.
- `Mutex<LinearT>` and `Arc<LinearT>` are forbidden — a linear value cannot be shared.

---

## Alternatives Considered

### `async`/`await`

Functions are coloured: async functions must be called with `await`. Solves structured concurrency naturally but introduces the "what colour is my function?" problem. Rejected — function colouring conflicts with Metel's goal of concurrency that is transparent syntactically.

### Actor model

Isolated processes communicating only via message passing. Eliminates data races entirely but requires supervision trees and is heavier than fibers. The channel model captures the message-passing philosophy in a lighter-weight, more composable form.

### Fire-and-forget only (original Go model)

No fiber handles. Simple but makes accidental resource leaks undetectable at compile time. Rejected in favour of linear handles, which make intentional fire-and-forget explicit (`.detach()`) and accidental omission a compile error.

---

## Resolved Questions

| # | Question | Decision |
|---|----------|----------|
| Q1 | Blocking vs. try-receive | `Receivable` defines both: `recv` (blocking) and `try_recv` (non-blocking). `<- ch` desugars to `recv`; `try_recv` is called explicitly. |
| Q2 | Fiber names and observability | Deferred to a tooling RFC. No syntax change. |
| Q3 | `Arc<T>` and `Sync` | Both defined. `Sync` is a marker aspect for concurrent-read safety. `Arc<T>: Send + Sync` when `T: Send + Sync`. `Arc<LinearT>` is forbidden. |
| Q4 | Detached fiber panic policy | Detached fibers terminate the program on panic (no handle to report to). Owned fibers capture panics in `Result<T, Panic>` from `.join()`. |

---

## Timing Recommendation

Do not implement concurrency primitives in the current PoC evaluator. The evaluator uses `Rc<RefCell<Value>>` — single-threaded. Fibers require `Arc<Mutex<Value>>` or a redesigned runtime. The PoC's purpose is to validate the core language.

**Minimum action from this RFC:** update the spec overview to name concurrency as a first-class design principle, note that language-native fibers and channels are planned, and record the aspect-desugaring model so that implementation choices in the PoC do not conflict with it.

**Implementation target:** Scoped after core language is stable. `Arc<T>` and `Sync` are defined in this RFC.

---

## References

- Language spec: `docs/public/spec.md`
- RFC-0043: regular pointers (implemented) — `*T`/`*mut T` syntax settled; `Send` status resolved by this RFC
- RFC-0044: explicit receiver semantics (implemented)
- RFC-0002: aspect bound syntax — `Send` as marker aspect; fiber capture bounds
- RFC-0028: memory and linear types — `Fiber<T>` linearity; linear types and `Send`
- RFC-0025: region allocation — `Region` is not `Send`
- RFC-0026: unsafe blocks — `unsafe_send` bypasses `Send` for lock-free stdlib internals
- Go specification: goroutines and select statements
- Go memory model

---

## Decision

**Outcome:** Accepted

Fiber/channel model, `Send`/`Sync` marker aspects, `Arc<T>`, `Mutex<T>`, and `select { }` are all settled. Implementation deferred until after the core language is stable.
