---
id: rfc-0003
title: "Concurrency Model"
date: '2026-05-20'
updated: '2026-08-24'
status: draft
---

> **Status — corrected 2026-08-24.** This RFC's own "Decision" section previously said
> "Outcome: Accepted" despite the file sitting in `0-draft/`, with no `status:`
> frontmatter field to catch the mismatch. It also hadn't been touched since it was
> written (2026-05-20) while nearly everything it depends on moved underneath it:
> RFC-0001 (pointer syntax), RFC-0002 (aspect bound syntax), and RFC-0025 (region
> allocation) are now superseded/refused; RFC-0028 (memory and linear types), which
> this RFC leaned on for "the linearity checker enforces `Fiber<T>` must be joined or
> detached," is **refused** with no replacement RFC — linearity exists today only as
> exploration (`linear-types.md`, metel-docs-internal), not a numbered proposal; RFC-0043
> (regular pointers, `*T`/`*mut T`) is **superseded** by RFC-0067a's `&T`/`&var T`. This
> pass: rewrites the pointer/reference syntax throughout, reworks the `Send`/`Sync`
> tables around the current reference *and* allocator-tag model (RFC-0063 §7's `@a T`
> sendability rule didn't exist when this was written), shrinks the `Arc<T>` section to
> point at RFC-0074 as the actual source of record instead of re-deriving it
> independently (avoiding the exact kind of two-document drift this correction pass is
> fixing), marks the join-guarantee mechanism as the leading sketch rather than a
> settled fact (matching `structured-concurrency.md` §3's later, more careful framing,
> which found this genuinely unresolved), and sets an honest `status: draft`. Found
> while checking whether an RFC already existed for a runtime-configurability proposal
> before drafting a new one — it did, in a form simpler than what was being proposed,
> which is folded in below (§ Runtime and primitive layers) rather than duplicated.

## Summary

Define Metel's concurrency model: fiber handles with linear ownership, typed channels as the primary communication primitive, a `select` expression for multiplexing, and a `Send` marker aspect to prevent data races. Concurrency syntax (`spawn`, `<-`, `->`, `select`) desugars to aspect implementations on standard library types, consistent with Metel's general philosophy that syntax sugar maps to aspect method calls. Fibers are first-class values, intended to be linearly held — fire-and-forget is possible but must be explicit via `.detach()` (see "Fiber handles and linearity" for what's actually settled about this versus sketched).

The stdlib ships a default M:N green-thread runtime. Third-party runtimes can replace it by providing their own types that implement the same four concurrency aspects. No syntax changes are required in user code — `spawn { }`, `ch <- v`, `<- ch`, and `select { }` all continue to work unchanged regardless of which runtime is active.

---

## Motivation

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

### Runtime is pluggable; syntax is not

The aspect-based desugaring cleanly separates concurrency *syntax* from concurrency *implementation*. The four aspects — `Spawnable`, `Sendable`, `Receivable`, `Selectable` — form a stable interface between the language and any backing scheduler. The stdlib ships a default implementation (`Fiber<T>`, `Chan<T>`) backed by an M:N green-thread scheduler, but nothing about `spawn { }`, `ch <- v`, `<- ch`, or `select { }` is tied to that specific runtime.

A third-party runtime can ship its own fiber and channel types that implement the same aspects. User code then uses identical syntax — the only thing that changes is which concrete type fills in the fiber or channel slot, which is typically handled by a single type alias at the crate root:

```metel
// crate root — switch the whole codebase to a different runtime
use myruntime::Fiber;
use myruntime::Chan;
```

All spawn sites and channel operations throughout the code resolve to the third-party runtime through normal type inference, without touching body-level syntax. Projects that never switch runtimes see no API seam at all.

**This is a whole-crate, compile-time choice, not a scoped one** — worth being explicit about, since it's easy to read "pluggable" as finer-grained than it is. Two different runtimes coexisting within one compiled program (e.g. a deterministic single-threaded runtime for a test module alongside the real M:N scheduler everywhere else) isn't directly expressible by this mechanism alone; the closest available answer today is splitting into separate crates/modules that each pick their own alias and compose at a boundary. Whether finer-grained, scoped swapping is ever wanted is an open question — see "Open Questions."

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

`spawn { expr }` returns a `Fiber<T>` handle, intended to require explicit consumption — accidental fire-and-forget of a meaningful fiber should be a compile error:

```metel
let f: Fiber<Int> = spawn { compute() };
let result = f.join();   // blocks until done, consumes handle
```

**Explicit fire-and-forget** is allowed via `.detach()`, which consumes the handle:

```metel
spawn { log_event(data) }.detach();   // explicit discard
```

A bare `spawn { }` statement (without binding) implicitly calls `.detach()`:

```metel
spawn { log_event(data) };   // sugar for .detach() — intentional, not accidental
```

**What this RFC does not settle: which mechanism actually enforces "must consume."**
The original version of this section asserted `Fiber<T>` "is a **linear type**" and cited
"the linearity checker (RFC-0028)" as what makes forgetting to join or detach a compile
error. RFC-0028 is refused, and no replacement RFC for linearity exists — `linear-types.md`
(metel-docs-internal) is exploration, not a numbered proposal, and its own open questions
include exactly this: `structured-concurrency.md` §3 treats "which mechanism carries the
must-join guarantee" as the central open concurrency question, reopened 2026-07-07 as
premature to decide, listing three real candidates (a `Linear` `spawn` handle — the
leading one, once `linear-types.md`'s `Linear` aspect exists; a standalone
`fork`/`JoinToken<'b>`; or an affine handle with no static guarantee at all, i.e.
abandonment silently allowed). Read the code above as the intended *shape* of the API
(`.join()`/`.detach()` as the two discharge methods), not as a settled claim about what
enforces using one of them. See `structured-concurrency.md` §3 for the live version of
this question.

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
    v <- data_ch             => Perhaps::Some { value = v },
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
| `&T`, `&var T` | **no** | references are never sendable, regardless of anchor (RFC-0067) |
| `@a T` | iff `a: Send` and `T: Send` | allocator-tag rule (RFC-0063 §7) — `@Heap T` is `Send` when `T: Send`; `@LocalHeap T`/`@a T` for any scoped or custom allocator is not |
| `Mutex<T>` where `T: Send` | yes | mutex is the synchronisation mechanism |

Deriving `Send` is automatic for most types — the programmer does not annotate it. A type is non-`Send` if it contains a reference (`&T`/`&var T`) or a non-`Heap`-tagged allocator pointer.

---

### The `Sync` marker aspect

`Sync` is a marker aspect — no methods. A type that is `Sync` can be accessed concurrently from multiple fibers via a shared reference without a data race.

```metel
aspect Sync {}
```

The precise relationship: `T: Sync` means that holding multiple `&T` references to the same value simultaneously across fibers is race-free. This is a stronger property than `Send` (which governs ownership transfer) — `Sync` governs concurrent access.

| Type | `Sync`? | Reason |
|------|---------|--------|
| `Int`, `Float`, `boolean`, `String` | yes | immutable value semantics — concurrent reads are safe |
| Structs with all-`Sync` fields | yes | automatic |
| Enums with all-`Sync` variants | yes | automatic |
| `&T`, `&var T` | **no** | a borrow's own validity is scope-bound; concurrent access through it is a separate question this RFC does not settle beyond marking it unsafe by default |
| `Mutex<T>` where `T: Send` | yes | access is serialized by the lock |
| `RwLock<T>` where `T: Send` | yes | multiple readers serialized by the lock |
| `Atomic<Int>`, `Atomic<boolean>` | yes | atomics are safe for concurrent access by design |
| `Chan<T>` where `T: Send` | yes | channels have internal synchronisation |
| `Arc<T>` where `T: Send + Sync` | yes | see RFC-0074 — reference-counted, no interior mutability without an explicit cell |

`Sync` is not usually written explicitly. It is derived automatically when all fields are `Sync`.

---

### Shared ownership across fibers — see RFC-0074

The original version of this section independently re-derived `Arc<T>`'s design (properties, a `Send`/`Sync` bound table, a "prohibition on linear types" rule, lifetime/drop behavior). That's now specified in its own RFC (RFC-0074, `Rc<T, brand 'b>`/`Arc<T, brand 'b>`, contingent on RFC-0076 brands) — duplicating it here risks exactly the drift this correction pass exists to fix, so this section is intentionally shrunk to a pointer rather than kept as an independent copy.

What's still specific to *this* RFC, not RFC-0074's concern: `Arc<T>` is the standard mechanism for sharing a value across fiber boundaries (as opposed to across aliases generally); `Arc<T>: Send` requires `T: Send + Sync` for the same reason any cross-fiber transfer does.

```metel
let config = Arc::new(load_config());
let c1 = Arc::clone(&config);
spawn { use_config(c1) };
```

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

### Default runtime (stdlib)

The stdlib provides `Fiber<T>`, `Chan<T>`, `SendChan<T>`, `RecvChan<T>`, and `Mutex<T>` backed by an M:N green-thread scheduler. This is the runtime a project gets without any explicit configuration — `Fiber<T>` resolves to the stdlib type unless overridden. The scheduler itself is not exposed to user code and is never part of the public API.

### Custom runtime implementations

A third-party crate can supply a complete alternative runtime by implementing the four concurrency aspects on its own types. The minimum contract is:

| Aspect | Needed for |
|--------|-----------|
| `Spawnable` | `spawn { }` syntax |
| `Sendable<T>` | `ch <- value` syntax |
| `Receivable<T>` | `<- ch` syntax |
| `Selectable` | `select { }` syntax |

A runtime does not need to implement all four — a crate that only replaces the scheduler but keeps stdlib channels only needs to implement `Spawnable` on its own fiber type.

**Switching at the crate level.** Because `spawn { }` resolves via type inference, pointing a crate at a different runtime is a one-line change per type at the crate root:

```metel
use myruntime::Fiber;    // replaces stdlib Fiber<T>
use myruntime::Chan;     // replaces stdlib Chan<T>
```

All `spawn { }` expressions whose inferred return type flows to `Fiber<T>` now resolve to `myruntime::Fiber<T>`. No call-site changes are needed. This is a **compile-time, whole-crate** choice — see the Design Philosophy section's note above, and "Open Questions" for whether finer granularity is ever wanted.

**What a runtime is free to decide.** The aspects define the *interface*, not the implementation. A custom runtime can use:
- A different scheduling strategy (work-stealing, cooperative-only, single-threaded event loop)
- Different internal channel representations (lock-free, io_uring-backed, virtual)
- Platform-specific I/O integration (io_uring, kqueue, IOCP, WASI)

None of these choices affect the syntax a user writes.

**What a runtime cannot change.** The aspects fix the observable semantics: `recv` blocks until a value is available or the channel closes; `send` moves the value; `Fiber<T>.join()` returns `Result<T, Panic>`; `Fiber<T>.detach()` consumes the handle. A runtime that violates these contracts is non-conformant.

### M:N scheduler (default runtime detail)

Fibers in the stdlib runtime are lightweight (green threads), M:N scheduled by the language runtime. The programmer launches fibers and forgets about OS threads, cores, and scheduling. The scheduler is an implementation detail — it is never exposed to user code.

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
| `Fiber<T>` | Lightweight M:N-scheduled fiber handle |
| `Thread<T>` | 1:1 OS thread handle |
| `Chan<T>` | Typed bidirectional channel |
| `SendChan<T>` | Write-only channel view |
| `RecvChan<T>` | Read-only channel view |
| `Mutex<T>` | Exclusive mutable access. `.lock()` returns a guard; released on drop |
| `RwLock<T>` | Shared read / exclusive write |
| `Atomic<Int>`, `Atomic<boolean>` | Lock-free integer and boolean operations |
| `Arc<T>` | Reference-counted shared ownership — see RFC-0074 |

`Mutex<T>` and `RwLock<T>` are `Send` because they wrap the synchronisation mechanism around the value. Internally they use `&var T` inside `unsafe`, but the public API is safe.

---

## Interaction with reference types (RFC-0067a) and allocators (RFC-0063)

The original version of this section resolved `*T`/`*mut T`'s `Send` status against RFC-0043, which is now superseded by RFC-0067a's `&T`/`&var T`. Restated against the current model:

1. **`&T` and `&var T` are not `Send`** — references are never sendable, regardless of anchor (RFC-0067 §1, once accepted; the rule is unconditional today regardless). A reference is a local-fiber tool; allowing it to cross fiber boundaries would create data races or dangle past its anchor's scope.
2. **`Perhaps<&T>` is not `Send`** — wrapping a non-`Send` type in `Perhaps` does not make it `Send`.
3. **`@a T`'s sendability is the allocator-tag rule** (RFC-0063 §7), not a blanket reference rule: `@Heap T` is `Send` when `T: Send`; every scoped or custom allocator's `@a T` is not.
4. **Auto-deref** (RFC-0067a §3) applies to field access, method dispatch, and function calls through `@a T` — unaffected by `Send`.

The `Send`/non-`Send` boundary for references and allocator pointers is fully settled by the current RFC-0063/RFC-0067a model; this RFC does not need to independently resolve it, unlike its original version, which predated both and tried to.

### Known future tension: scoped concurrency

The `&T: !Send` rule is unconditional. This forecloses one specific future pattern: **scoped fibers** — fibers whose lifetime is bounded by a lexical scope, making it provably safe to send references into the enclosing stack frame without copying. Rust achieves this via `std::thread::scope`, where `&'a T` borrows are tied to the scope's lifetime and become sendable within it.

If Metel later wants scoped fibers that borrow from the enclosing scope, the unconditional `&T: !Send` rule would block naively sending `&T` into them. The clean resolution — consistent with Metel's existing separation of allocator identity (`@a`) from borrow validity (`&r`, RFC-0067) — is a dedicated `ScopedFiber<'scope, T>` handle type whose lifetime the borrow checker can reason about, rather than making `&T` conditionally `Send`. This keeps `&T` semantics simple and stable. Not a current concern.

---

## Interaction with linearity — genuinely unresolved, see the note in "Fiber handles and linearity"

The original version of this section cited RFC-0028 as the linearity checker enforcing `Fiber<T>`/`Thread<T>` must be joined or detached. RFC-0028 is refused. This is not restated as settled fact — see the note above and `structured-concurrency.md` §3 for the actual, live state of this question. What survives independent of which mechanism wins: `Mutex<LinearT>` and `Arc<LinearT>` should remain forbidden once `Linear` exists as a real aspect (a linear value cannot be soundly shared), and channel send remains a natural consumption point for a linear value regardless of how the fiber-handle question resolves.

---

## Alternatives Considered

### `async`/`await`

Functions are coloured: async functions must be called with `await`. Solves structured concurrency naturally but introduces the "what colour is my function?" problem. Rejected — function colouring conflicts with Metel's goal of concurrency that is transparent syntactically. (This choice is also what lets Metel's later algebraic-effects work, `algebraic-effects.md` §2, express suspension as an ordinary affine continuation value rather than a syntactic mode — not a consideration available when this RFC was first written, but consistent with it in hindsight.)

### Actor model

Isolated processes communicating only via message passing. Eliminates data races entirely but requires supervision trees and is heavier than fibers. The channel model captures the message-passing philosophy in a lighter-weight, more composable form.

### Fire-and-forget only (original Go model)

No fiber handles. Simple but makes accidental resource leaks undetectable at compile time. The intent (not yet a settled mechanism — see above) is linear-or-similar handles, which make intentional fire-and-forget explicit (`.detach()`) and accidental omission a compile error.

---

## Open Questions

*Rewritten 2026-08-24. Several items in the original "Resolved Questions" table asserted more than this RFC's current dependencies actually support; restated honestly below rather than left as claimed resolutions.*

1. **Which mechanism enforces "a `Fiber<T>` must be joined or detached"?** (See "Fiber handles and linearity.") Not resolved — this RFC's original dependency (RFC-0028) is refused. `structured-concurrency.md` §3 tracks the live version of this question; not duplicated here.
2. **Is the crate-wide-only granularity of runtime switching (§ Design Philosophy, § Custom runtime implementations) sufficient, or is a finer-grained, scoped mechanism wanted** — e.g. two different runtimes coexisting in one compiled program? The type-alias mechanism specified here needs nothing beyond ordinary type inference and works today; a scoped alternative would most plausibly be expressed via context parameters (RFC-0113, `1-under-review`) threading a runtime value implicitly through a call tree the way an allocator already is — genuinely new machinery with a real prerequisite, not a refinement of what's here. No concrete use case has been named that the crate-wide mechanism can't already serve by splitting into separate crates/modules; this stays open rather than assumed necessary.
3. **Whether the scheduler should ever be expressible as an effect handler** (the OCaml 5 model: `spawn`/channel operations as effect operations with a default handler, swappable by installing a different one) rather than a value or a type alias. This RFC predates the algebraic-effects exploration entirely (`algebraic-effects.md`, metel-docs-internal) and takes no position on it. `algebraic-effects.md` §9 already found that performing an effect inside a spawned fiber composes correctly through the ordinary sendability rules with no special-casing — effects and fibers are already independently sound — so this question is about a possible *additional*, deeper unification, not a prerequisite for anything specified here.
4. Fiber names and observability — deferred to a tooling RFC. No syntax change proposed here.
5. `Sync`'s relationship to `&T`/`&var T` concurrent access beyond "references are unsafe by default" is not fully worked out — RFC-0067's own liveness/NLL interaction (still under review) likely bears on this and hasn't been checked against it.

---

## References

- Language spec: `docs/public/spec.md`
- RFC-0063 (Allocator Handles) — `@a T` sendability rule (§7), replacing this RFC's
  original independent pointer-`Send` derivation.
- RFC-0067 (Lifetime Anchors, under review) / RFC-0067a (Reference Types, implemented) —
  `&T`/`&var T`, replacing the `*T`/`*mut T` syntax this RFC originally specified
  against (RFC-0043, now superseded).
- RFC-0074 (Shared Ownership, draft) — `Arc<T>`'s actual specification; this RFC no
  longer independently re-derives it.
- `reports/substructural-types/structured-concurrency.md` (metel-docs-internal) — the
  actively-maintained continuation of this RFC's fiber/channel model: the `||`
  combinator this RFC never mentions (added and later retracted after this RFC was
  written), the live join-guarantee question, and the runtime-configurability
  discussion Open Question 2 above summarizes.
- `reports/substructural-types/linear-types.md` (metel-docs-internal) — where
  linearity now lives, since RFC-0028 (this RFC's original dependency) is refused.
- RFC-0044 (Explicit Receiver Semantics, implemented).
- RFC-0026 (Unsafe Blocks, draft, unimplemented) — `unsafe`-only OS-primitive access.
- Go specification: goroutines and select statements.
- Go memory model.

---

## Decision

**Outcome:** *(pending — draft, not settled; see Open Questions)*

The fiber/channel model, aspect-based desugaring, `select { }`, and the crate-wide
pluggable-runtime mechanism remain the leading design and need no further syntax work
to stay consistent with the rest of the corpus as of this correction. What's actually
unresolved is narrower than the shape of the API: which mechanism enforces the
must-join guarantee (Open Question 1), and whether finer-grained runtime configurability
is ever wanted (Open Question 2). Implementation was deferred pending core-language
stability when this was written and that recommendation still holds.
