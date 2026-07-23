---
id: algebraic-effects
title: "Algebraic Effects and the Metel Memory Model"
type: report
status: active
last_synced_against_model: '2026-07-23'
supersedes: null
revives: "reports/archive/algebraic-effects-and-memory-model.md"
---

# Algebraic Effects and the Metel Memory Model

*Living document — updated in place, not a point-in-time snapshot.*

*Exploration, not a decision. Revived from `../archive/algebraic-effects-and-memory-
model.md` (originally written 2026-06-29, against the pre-split "region" model where a
single tag was simultaneously allocator identity, lifetime bound, and disjointness
proof). This revision updates every example to the current split-model syntax
(`@a T` allocators in the value channel, `&r T` lifetime anchors in the type-parameter
channel — see `lifetimes-vs-regions-2026-07-02.md`), retracts everything that depended
on `SubRegion`/`Outlives` (both retracted — see that report's 2026-07-04 changelog
entry), and folds §12's linear-capability-token material into a pointer at
`linear-types.md` rather than re-deriving it a second time.*

> **Status of effect syntax, unchanged from the original report:** the `effect`,
> `^ EffectName`, `handle`, and `resume` constructs described here are **proposed** —
> not yet specified in any RFC and not implemented. Everything else follows the
> current, accepted allocator/lifetime split model.

---

## What this document covers

Algebraic effects are a mechanism for structured side-effect handling: a computation
declares what effects it may perform, and a surrounding `handle` block intercepts each
effect invocation, receives the suspended computation as a first-class value (the
*continuation*), and decides whether to resume it, abort it, or resume it multiple
times. This report analyzes how that mechanism interacts with Metel's memory model as
settled by the allocator/lifetime split. Most of the safety story falls out of rules
that already exist. A small number of genuine tensions require new constraints, and one
open question remains.

---

## 1. The memory model in three sentences

Allocators are ordinary values, passed explicitly, that own allocation identity;
`@a T` is "a `T` allocated by `a`," and `a`'s type (`Heap`, `LocalHeap`, `BumpAlloc`,
a custom `Alloc` implementor) determines disjointness and sendability. Lifetime anchors
are a separate, orthogonal concept: `&r T` and `&r mut T` are non-owning borrows whose
validity is bounded by the anchor `r` — never sendable, never escaping their anchor's
scope. The two concepts used to be fused into one "region" tag; RFC-0066 (move-out
from a region-allocated value while the region continues) is what forced them apart —
see `lifetimes-vs-regions-2026-07-02.md` §1 for the full argument.

The rules that matter most for this analysis:

- **Affine ownership (RFC-0071)**: non-`Copy` values move by default; exactly one live
  owner at any point. `Copy` and `Drop` are mutually exclusive. Dropping a value runs
  `Drop::drop` if implemented, then recursively drops fields.
- **Sendability (RFC-0063 §4/§5)**: `@Heap T` is sendable across fibers (iff `T: Send`);
  `@LocalHeap T` is thread-local; a scoped allocator's `@a T` (`BumpAlloc`, `AutoAlloc`)
  is never sendable. References `&r T` and `&r mut T` are never sendable, regardless of
  anchor.
- **Negative bounds (RFC-0072)**: `T: !Drop` is satisfied when no `Drop` impl exists for
  `T`. Move-out from a bulk-deallocating scoped arena requires `T: !Drop` (RFC-0066).

---

## 2. The continuation is an affine, allocator-owned value

When a computation performs an effect, it suspends. The "rest of the computation" —
everything that would have run after the effect site — is captured as a *continuation*
and handed to the handler. The type of this value in Metel's model is:

```
@Heap Continuation<ResumeValue, FinalResult>
```

**Why `@Heap`**: the continuation must outlive the effect-call stack frame that created
it, so it cannot be allocated by a scoped allocator. `Heap` is the only stdlib
allocator that supports indefinite lifetime. The continuation is individually freed
when the handler is done with it.

**Why affine**: `@Heap T` is non-`Copy` by construction (RFC-0063 §2, RFC-0071 §2).
Moving the continuation transfers exclusive ownership. There is no mechanism to
duplicate it — calling `resume` twice would require two owners of the same value, which
affine move semantics make a compile error. One-shot resumption is not a special rule
added for effects; it falls out of the general ownership model.

**Multi-shot continuations**: cannot be expressed with the current model, because
`@Heap Continuation<V, R>` is affine. Making a continuation multi-shot would require
`Continuation` to implement `Clone`. This is a legitimate constraint: any continuation
that captures non-`Clone` values (most structs, allocator-tagged pointers) cannot be
multi-shot. Continuations that capture only `Copy`/`Clone` values could support
cloning, and the programmer would write `k.clone().resume(v)` explicitly. Whether the
language should provide syntax for this is a separate design question.

---

## 3. Allocator tags determine continuation sendability precisely

A continuation captures the entire suspended stack frame: all bindings live at the
effect site. Each captured value's storage — its allocator tag, or its borrow anchor —
determines the continuation's sendability:

| Captured value type | Continuation sendable |
|---|---|
| `@Heap T` (where `T: Send`), `Copy` values, primitives | yes, if nothing else prevents it |
| `@LocalHeap T` | no — thread-local |
| `@a T` (scoped allocator — `BumpAlloc`/`AutoAlloc`) | no — the allocator may be torn down before the fiber terminates |
| `&r T`, `&r mut T` (any borrow, any anchor) | no — references are never sendable |

This is not an approximation. The allocator's type (or the fact of being a borrow at
all) encodes the exact relationship. There is no separate marker to reason about: the
type of each captured value already carries the answer.

**Practical implication for handlers**: a handler that receives a non-sendable
continuation can only use it within the current fiber — call `resume` synchronously,
pass the continuation to another function in the same fiber, or store it in a struct on
the same fiber. It may not send it through a `Chan<T>`, pass it to `spawn { }`, or
otherwise move it across a fiber boundary; any attempt is a compile error at the `Chan`
send or the `spawn` capture, caught by the ordinary sendability rules.

A handler for a computation that holds only `@Heap`-allocated or `Copy` values receives
a sendable continuation — storable in a channel, shippable to a worker fiber, resumable
from there. An async effect handler, with no special annotation or `unsafe` required.
The type system permits exactly the handlers that are safe.

---

## 4. The `&r mut T` constraint: the real design tension

This is the most important interaction in the model, and it comes entirely from
RFC-0067.

`&r mut T` is exclusive and non-sendable by construction. It is also non-escaping: the
borrow checker guarantees no `&r mut T` outlives its anchor `r`. If a computation holds
an active `&r mut T` borrow and performs an effect, the continuation captures that
borrow. Two properties follow immediately:

1. The continuation is non-sendable — async handlers are ruled out.
2. The original binding is inaccessible to the handler code: the `&r mut T` borrow is
   outstanding, so the handler cannot touch the same location the suspended computation
   is borrowing.

The second point is sound: while the computation is suspended, the handler cannot
concurrently mutate the value the computation has exclusively borrowed. The problem is
practical: if the handler does not resume synchronously, the borrow hangs open for as
long as the continuation is unresolved — the handler cannot re-borrow the location, the
original value cannot be moved, and no other code can access it mutably.

**The constraint in concrete terms**: performing an effect while holding an active
`&r mut T` borrow restricts the handler to synchronous resumption — receive the
continuation, call `resume`, and the borrow ends when the computation reaches the end
of `r`'s scope. An async handler that stores the continuation for later would leave the
borrow hanging indefinitely; the borrow checker prevents this by making the
continuation non-escaping in any way that would outlive `r`.

**The resolution**: well-designed effect handlers rarely need to suspend computations
that hold active `&mut` borrows. An `IO` effect for printing holds no borrows. A
`State` effect that reads and writes logical state holds logical state, not raw borrows
into physical memory. The fix is to release the borrow before performing the effect — a
natural refactoring the borrow checker guides you toward with a compile error that
names the type.

If the language wants to enforce this statically at the effect declaration site, an
effect could carry an annotation requiring that no active borrows exist at performance
sites:

```metel
effect IO ^ clean { ... }
```

Whether `^ clean` or a similar constraint is worth adding as explicit syntax is an open
question (§Open questions). The implicit enforcement through sendability is correct;
the question is whether it is discoverable enough.

---

## 5. Abort without resuming: `Drop` handles it

Not every handler calls `resume`. A handler may choose to abort — return a value
without ever resuming the suspended computation. In that case the continuation goes out
of scope unconsumed.

`@Heap Continuation<V, R>` is an affine value. If it goes out of scope without being
moved or consumed, its `Drop::drop` runs — the same way any heap-allocated struct with a
`Drop` impl is cleaned up. `Continuation::drop` recursively drops every value captured
in the suspended frame, following RFC-0071's drop ordering: fields in declaration
order, then any owned allocators.

If captured values themselves implement `Drop`, their destructors run as part of the
cascade. A suspended `FileHandle` that was open when the effect was performed — and
whose handler aborted without resuming — gets `FileHandle::drop` called on it
automatically. No special effect-specific machinery is needed; the standard `Drop`
protocol handles it.

---

## 6. Handler state via struct-owned allocators

A handler that accumulates state during effect handling is a natural candidate for a
struct-owned allocator (RFC-0068, primary-constructor syntax): the allocator's lifetime
equals the handler struct's lifetime, all accumulation goes through it, everything frees
in bulk when the handler drops.

```metel
struct TraceHandler(@a: BumpAlloc) {
    entries: @a List<String>,
    count:   i64,
}
```

The owned allocator `a` is implicitly in scope inside `impl TraceHandler` — never
re-declared on the impl header or on individual methods (05-struct-owned-allocators.mtl
§3). Allocating into it requires `&mut self`; a shared `&self` borrow can read from it
but cannot allocate into it — the same exclusivity RFC-0063 §1 already requires.

A returned borrow anchored to `self` — `&self List<String>` — is valid for the whole
struct's lifetime, not just the duration of the particular call that produced it,
exactly as in RFC-0067 §2's `&self` anchor rule.

---

## 7. Nested allocators need no special sub-region typing — the `SubRegion` retraction

The original version of this report relied on `SubRegion<R>`/`Outlives` to wire up the
lifetime relationship automatically when a handler struct's owned arena lived inside an
outer region. **Both are retracted** (`lifetimes-vs-regions-2026-07-02.md`, 2026-07-04
changelog) — there is no more region-as-lifetime concept for a sub-relationship to hold
between.

What replaces it is simpler, not more complex: an allocator's identity and a borrow
anchor's validity are now two independent things, so "a handler struct's own allocator,
itself allocated by an outer allocator" is just ordinary composition, not a special
case.

```metel
fun build_ast(src: &String) -> @Heap List<AstNode> {
    // AstBuilder's own allocator `a` is created fresh when the struct is
    // constructed — no relationship to Heap needs deriving, because there is
    // no lifetime-outlives fact being tracked between the two allocators at all.
    let mut builder = @Heap AstBuilder::new();

    handle parse_expr(src) {
        Parse::emit_node(node) => builder.handle_emit(node, k)
    }

    // AstBuilder's own arena cannot outlive `builder` itself — extract first.
    let result: @Heap List<AstNode> = builder.nodes.clone_into::<Heap>();
    result
    // builder drops here — AstBuilder's own arena freed in bulk
}
```

The one thing that still needs stating explicitly, and that the old `SubRegion`
machinery used to derive for you: any borrow taken from data inside `builder`'s own
arena is bounded by `builder`'s lifetime as an ordinary value, so it cannot be returned
past `build_ast`'s scope without first being cloned into an allocator that outlives the
function — `clone_into::<Heap>()` above, the same escape hatch RFC-0066/RFC-0067 already
provide, not new effects-specific machinery.

---

## 8. Desugaring to aspects

Metel's design principle is that syntax desugars to aspect method calls. Effects follow
the same pattern: an effect declaration desugars to an aspect; a `handle` block desugars
to an impl of that aspect wired into the call stack as an implicit bracket parameter.

```metel
// Effect declaration
effect Trace {
    fun log(msg: String) -> ()
}

// Desugars to:
aspect Trace {
    fun log(self: &self Self, msg: String, k: @Heap Continuation<(), Self::Output>) -> Self::Output;
}
```

Performing an effect inside a computation desugars to calling the aspect method on the
implicit handler value in the bracket channel, passing the current continuation as the
last argument. The bracket channel and aspect dispatch are already in the language. The
only genuinely new runtime piece is continuation capture — snapshotting a call frame —
which the current tree-walking evaluator does not support. The type system is ready;
the implementation work is in the runtime.

---

## 9. Interaction with structured concurrency

*Updated 2026-07-07: `||` (RFC-0064) is dropped; concurrency is `spawn` + `Chan<T>` with
a `Linear` `JoinHandle` (`structured-concurrency.md`). This section is rescoped from
"effects inside a `||` branch" to "effects inside a spawned fiber," which is the same
sendability argument on the surviving primitive.*

If an effect is performed inside a spawned fiber, the continuation captures that fiber's
stack. Whether the continuation may cross back out is governed by the ordinary
sendability rule (§3): if the fiber's frame holds any scoped-allocator data or borrow,
the continuation is non-sendable and cannot leave the fiber — so its handler must be
synchronous within that fiber. A continuation over only `@Heap`/`Copy` data is sendable
and may be shipped to a worker (§11.5). No effect-specific constraint is needed; the
tag-based sendability rule already does the right thing.

The fiber itself should not be silently abandonable mid-effect — the "must not escape the
structured boundary" guarantee. *Which* mechanism carries that guarantee (a `Linear`
`spawn` handle vs. a standalone `JoinToken<'b>`) is an open concurrency question, reopened
2026-07-07 — see `structured-concurrency.md` §3 and `brand-types.md` §2. The effects
analysis here is unaffected by that choice: it relies only on the guarantee existing, not
on its packaging.

---

## 10. Summary table

| Concern | Mechanism | RFC |
|---|---|---|
| One-shot resumption | `@Heap Continuation` is affine — not `Copy`, cannot duplicate | RFC-0071 |
| Abort without resuming | `Continuation::drop` cascades to all captured values | RFC-0071 §3 |
| Scoped-allocator data in frame | Continuation inherits the scoped tag → not sendable | RFC-0063 §4/§5 |
| Cross-fiber async handlers | Legal only when all captured values are `@Heap`/`Copy` | RFC-0063 §4/§5 |
| Active `&r mut T` borrow in frame | Non-sendable; original location inaccessible; synchronous only | RFC-0067 |
| Handler-local state allocation | `struct Handler(@a: BumpAlloc)` — arena freed with handler | RFC-0068 |
| Nested handler allocators | Ordinary allocator composition — no `SubRegion`/`Outlives` needed (retracted) | — |
| Move-out on resume | Type-directed move-out / ascription — standard extraction form | RFC-0066 |
| `T: !Drop` in continuation internals | Scoped-allocator data in continuation requires `T: !Drop` for safe bulk-free | RFC-0072 |

**What falls out for free**: one-shot enforcement, abort cleanup, sendability
constraints, handler state lifetime. These are all consequences of existing rules
applied to `@Heap Continuation<V, R>` as an ordinary value.

**What is genuinely new**: the `handle` block syntax, the runtime mechanism for
capturing continuations (snapshotting a call frame), and the implicit-parameter wiring
that threads the handler through the call graph to the effect site. These are
implementation work, not type-system work.

**The one open question carried from the original report**: whether performing an
effect while holding an active `&r mut T` borrow should be a compile error at the effect
declaration site (a `^ clean` annotation), or whether the current implicit constraint —
handlers receive non-sendable continuations and are restricted to synchronous
resumption — is sufficient ergonomically. Both are sound; the question is
discoverability.

---

## 11. Usage examples

Illustrative only. Assumes allocator-elision (RFC-0065) is active where only one
allocator is in scope, so a bare `@` elides to the named one.

### 11.1 Testable console IO

The canonical motivation. `greet` declares it performs `Console` effects; the handler
decides what those effects mean.

```metel
effect Console {
    fun print(s: String) -> ()
    fun read_line() -> String
}

fun greet() ^ Console {
    Console::print("What is your name? ");
    let name = Console::read_line();
    Console::print("Hello, ${name}!");
}

// Production: wire to real stdin/stdout
fun main() {
    handle greet() {
        Console::print(msg) => { println(msg); resume(()) }
        Console::read_line() => { resume(stdin_read_line()) }
    }
}

// Test: fixed inputs, captured outputs — no real IO
fun test_greet() {
    let mut output: String = "";

    handle greet() {
        Console::print(msg) => { output = output + msg; resume(()) }
        Console::read_line() => { resume("Alice") }
    }

    assert(output == "What is your name? Hello, Alice!");
}
```

The function signature tells you everything: `greet() ^ Console` means it may print and
read, nothing else. Swapping handlers is the entire test strategy — no mocking
framework, no dependency injection wiring.

### 11.2 Tracing with an allocator-backed handler

```metel
struct TraceHandler(@a: BumpAlloc) {
    entries: @a List<String>,
    count:   i64,
}

impl TraceHandler {
    fun new() -> TraceHandler {
        TraceHandler { entries: @List::Nil {}, count: 0 }
    }

    fun handle_log(&mut self, msg: String, k: @Heap Continuation<(), T>) -> T {
        self.entries = @List::Cons { head: @msg, tail: self.entries };
        self.count  += 1;
        k.resume(())
    }

    fun summary(&self) -> String {
        "${self.count} events logged"
    }
}

fun handle_request(order_id: i64) {
    let mut tracer = TraceHandler::new();

    let result = handle process_order(order_id) {
        Trace::log(msg) => tracer.handle_log(msg, k)
    };

    println(tracer.summary());
    // tracer drops here — arena freed in O(1), all log strings gone
}
```

### 11.3 Short-circuit / abort

A handler arm that does not call `resume` short-circuits the entire computation. The
continuation is dropped, and `Drop` cascades to everything the suspended computation was
holding.

```metel
effect Lookup {
    fun find(key: String) -> Perhaps<String>
}

fun build_config() ^ Lookup -> Config {
    let host = match Lookup::find("host") {
        Perhaps::Some { value: h } => h,
        nope                       => "localhost",
    };
    Config { host }
}

// Abort entirely when a required key is missing
fun config_strict(map: &HashMap<String, String>) -> Result<Config, String> {
    handle build_config() {
        Lookup::find(key) => {
            match map.get(key) {
                Perhaps::Some { value: v } => resume(Perhaps::Some { value: v }),
                nope => {
                    // No resume — k is dropped here; Drop cascades automatically.
                    Result::Err { error: "missing required key: ${key}" }
                }
            }
        }
    }
}
```

### 11.4 The `&r mut T` constraint in practice

```metel
effect IO {
    fun print(s: String) -> ()
}

// Problem: &mut buf is active at the effect site — continuation captures the borrow.
fun annotate_buffer_wrong(buf: &mut Buffer) ^ IO {
    IO::print("writing to buffer");   // &mut buf active here
    buf.write("hello");
}

// Fix: release the borrow before the effect, re-borrow after.
fun annotate_buffer(buf: &mut Buffer) ^ IO {
    let msg = "writing ${buf.len()} bytes";   // read through &mut, then release
    IO::print(msg);                            // no active borrow here
    buf.write("hello");                        // &mut taken again after the effect site
}
```

If `annotate_buffer_wrong` is used with an async handler, the compiler rejects it — not
because effects are involved, but because the continuation contains a non-sendable
`&mut Buffer`. The error names the type.

### 11.5 Sendability — heap data enables async handlers

```metel
struct Task   { id: i64, payload: @Heap String }
struct Output { id: i64, result:  @Heap String }

effect Compute {
    fun run(task: @Heap Task) -> @Heap Output
}

fun run_parallel(tasks: @Heap List<Task>) -> @Heap List<Output> {
    let work_ch: Chan<WorkItem> = Chan::new();
    spawn { worker_loop(&work_ch) }.detach();

    handle pipeline(tasks) {
        Compute::run(task) => {
            // k is sendable — every captured value is @Heap; ship it to the pool
            work_ch <- WorkItem { task, k };
            // handler arm ends without resume — a worker calls k.resume(output) later
        }
    }
}

fun worker_loop(ch: &Chan<WorkItem>) {
    while let Perhaps::Some { value: item } = <- ch {
        let output = expensive_compute(&item.task);
        item.k.resume(output);   // resume from worker fiber — sound because k is sendable
    }
}
```

Try the same with `@a Task` for a scoped `a` instead of `@Heap Task` — `work_ch <-
WorkItem { task, k }` becomes a compile error naming the scoped allocator tag as the
reason the continuation isn't `Send`.

### 11.6 Nested handler allocators (§7)

```metel
struct AstBuilder(@a: BumpAlloc) {
    nodes: @a List<AstNode>,
}

impl AstBuilder {
    fun new() -> AstBuilder { AstBuilder { nodes: @List::Nil {} } }

    fun handle_emit(&mut self, node: AstNode, k: @Heap Continuation<(), ()>) {
        self.nodes = @List::Cons { head: @node, tail: self.nodes };
        k.resume(())
    }
}
```

See §7 for `build_ast`, the full function this handler is used from.

### Example summary

| Example | Primary point |
|---|---|
| Testable IO | Effect as a seam — swap handlers to test without mocking frameworks |
| Allocator-backed tracer | Struct-owned allocator for handler state; bulk-free on drop |
| Short-circuit / abort | Not calling `resume` is valid; `Drop` cascades automatically |
| `&r mut T` constraint | Release borrows before effect sites; compiler guides you |
| Sendable continuations | `@Heap`-only computations enable async/worker-pool handlers |
| Nested handler allocators | Ordinary composition — no special sub-region machinery needed |

---

## 12. Linear capability tokens and typestate at effect boundaries

This section used to re-derive the multiplicity/linearity model inline; that model now
has a proper home in `linear-types.md`, which should be read first. What's kept here is
only the part that is genuinely specific to effects and not covered there: **the
tension between linear values and captured continuations.**

### 12.1 Linear tokens as effect arguments: handlers must clean up even on abort

When an effect operation takes a `Linear` value as an argument (`linear-types.md` §2),
the handler receives that value and becomes its owner:

```metel
effect FS {
    fun close(h: FileHandle, cap: FileCap) -> ()   // FileCap: Linear (linear-types.md §5)
}

handle computation() {
    FS::close(h, cap) => {
        sys_close(h.fd);
        consume(cap);       // handler owns cap — must consume it even when aborting
        // resume is not called — computation aborts here
    }
}
```

If the handler tries to abort without consuming `cap`, the linearity checker fires:
`cap` exits scope unconsumed. A handler that aborts cannot silently leak a resource the
computation passed to it — the handler author is forced to be explicit about cleanup
regardless of whether they resume. This is stricter than the affine case (§5): an
affine `@Heap FileCap` would just run `Drop::drop` automatically on abort, which is
right for values where a silent drop is fine, and wrong for values — uncommitted
transactions, unsent acknowledgements, unclosed protocol states — where it isn't.

### 12.2 Typestate through effect boundaries: flows via the resume type

Phantom typestate parameters (or, per `structural-records.md` §5, row-conditional
typestate) compose with effects without friction: the effect operation's return type is
what `resume` must provide, directly controlling what protocol state the computation
continues in.

```metel
effect Net {
    fun accept(sock: Socket<Listening>) -> (Socket<Accepting>, Socket<Listening>)
    fun recv(sock: Socket<Accepting>)   -> ([u8], Socket<Accepting>)
    fun close(sock: Socket<Accepting>)  -> Socket<Closed>
}
```

If a handler arm passes the wrong state to `resume` — `Socket<Closed>` where
`Socket<Accepting>` is expected — it is a type error at the `resume` call site. The
computation's protocol invariant is statically preserved across the effect boundary. A
handler cannot resume `Net::recv` with `Socket<Closed>` to fake a dropped connection,
because `recv`'s resume type doesn't allow it — to signal an error, the handler simply
does not call `resume`. "Error" is an abort, not a lie about state.

### 12.3 The real tension: linear values captured in continuations

This is the one interaction that requires genuinely new machinery — a static check
neither the linearity system nor the effect system currently has on its own.

```metel
fun process() ^ IO {
    let (handle, cap) = open("/tmp/log.txt");   // cap: Linear

    IO::print("about to read");   // cap is in scope but NOT passed to IO::print
                                  // — continuation captures cap

    let (line, cap) = FS::read(handle, cap);
    FS::close(handle, cap);
}
```

When `IO::print` performs its effect, the continuation captures `cap`. If the handler
aborts without calling `resume`, the continuation is dropped. `Continuation::drop`
would need to drop `cap` — but `cap` is `Linear` and, by `linear-types.md` §2's own
mutual-exclusion rule, `Linear` types have no `Drop` impl to fall back on. This is
unsound as stated.

**The required check**: at every effect-performance site, the checker must verify that
no unconsumed `Linear` value remains in scope unless it is explicitly passed to the
effect as an argument. Performing an effect while holding a "dangling" linear capability
is a compile error:

```
error: linear value `cap` is in scope at effect site but not consumed or passed as an argument
  --> ...
   | IO::print("about to read");
   | cap must be consumed before this effect, or passed through it
```

Two valid resolutions — restructure so the linear value is acquired after the
non-linear effect site, or thread it through the effect explicitly as an argument so the
handler receives it and must resume with it (or consume it on abort, per §12.1). The
second is the general solution for cases where the linear value genuinely spans the
effect site.

**This check does not yet exist in `linear-types.md`.** It belongs there as much as
here — flagged as a cross-reference to add once that document's implementation section
is written, not duplicated in full a second time.

### 12.4 Summary

| Interaction | Behavior |
|---|---|
| `Linear` token as effect argument | Handler must consume it even on abort — enforced by the linearity checker |
| Typestate via phantom parameter or row (`structural-records.md` §5) | Flows through the effect boundary via the resume type; wrong-state resume is a compile error |
| `Linear` value in scope at effect site, not passed | Unsound on abort — requires the new static check in §12.3 |
| Threading a `Linear` value through an effect | Pass as an effect argument; handler receives it and must consume or resume with it |

---

## 13. Lessons from Koka

Koka is the most mature algebraic-effect language and the closest design point to what
this report proposes. Several of its decisions are directly applicable to Metel; others
solve problems Metel does not have. (Unchanged from the original report — this section
concerns effect-declaration syntax, not memory-model syntax, so nothing here needed
updating for the allocator/lifetime split.)

### 13.1 `fun` vs `ctl`: most operations don't need a continuation

Koka splits effect operations into two kinds at the declaration site: **`fun`** — the
operation always resumes exactly once with a value, like a function call, no
continuation captured — and **`ctl`** — the handler decides whether to resume, how many
times, and with what; full continuation machinery required.

Metel's current proposal treats all effect operations uniformly — every performance
allocates a `@Heap Continuation`. That is unnecessarily expensive for the common case
(state reads, configuration queries, logging are all `fun`-style):

```metel
effect State<S> {
    fun get() -> S       // always resumes once — no continuation allocated
    fun set(x: S) -> () // same
}

effect Yield<T> {
    ctl yield(x: T) -> Bool   // handler decides whether to resume — continuation required
}
```

This is a declaration-level change with no effect on programmer-visible semantics.
State and reader effects become zero-overhead; generators and async retain full power.

### 13.2 `final ctl`: non-resuming operations need no continuation at all

Koka's `final ctl` marks operations that never resume; the compiler allocates no
continuation at all — the handler is a straight abort.

```metel
effect Fail {
    final ctl fail(msg: String) -> !   // ! = Never; never resumes
}

fun run_safe<T>(f: fun() -> @[Fail] T) -> Perhaps<T> {
    handle f() {
        Fail::fail(msg) => Perhaps::None    // no resume call — final handler
    }
}
```

This covers exceptions, panics, and early return — the most common "effectful"
operations in practice — at zero continuation cost.

### 13.3 Evidence passing: O(1) resumption without heap allocation

Koka dispatches effect operations via *evidence passing*: each effectful function
receives hidden parameters pointing to the nearest handler in the call stack. Resuming a
`ctl` continuation is then a return from a function — the stack frame is already in
place. The current Metel proposal boxes continuations into `@Heap Continuation<V, R>`,
sound but potentially expensive since every performance allocates.

The two approaches are not in conflict. A practical implementation could use evidence
passing for `fun` and `final ctl` operations and only box into `@Heap Continuation` for
multi-shot or cross-fiber handlers — those where the continuation genuinely needs to
outlive the handler's stack frame. This is an implementation strategy, not a language
design change, but it is the reason Koka's effects are competitive with hand-written
state machines in benchmarks.

### 13.4 Open effect rows for higher-order composability

Koka's effect rows distinguish closed (`<io>` — exactly `io`) and open (`<io|e>` — at
least `io`, plus whatever is in `e`) effect sets. The open tail is what makes
effect-polymorphic standard library functions work:

```metel
fun map<T, U, E>(xs: List<T>, f: fun(T) -> U ^ {E}) -> List<U> ^ {E} { ... }
fun run_logged(f: fun() -> () ^ {IO}) -> () { ... }
```

Metel's current `^` annotation uses a type variable `E` for effect polymorphism, which
achieves the same result. The Koka insight is that making the closed/open distinction
*syntactically explicit* — `{IO}` vs `{IO | E}` — prevents a class of inference
ambiguities at higher-order call sites and makes the constraint visible in
documentation.

### 13.5 What not to borrow

**Perceus / functional-but-in-place.** Koka needs Perceus because it has no
programmer-visible allocators — it must infer when memory can be reused. Metel's
explicit allocator system (`BumpAlloc`, `AutoAlloc`, `@a T`) gives the programmer direct
control over allocation patterns; Perceus solves a problem Metel does not have.

**`st<h>` effect elimination.** Koka tracks all mutation through `ref<h,a>` and erases
the heap variable `h` when it does not escape the function. Metel handles the same case
with scoped allocators: allocation via `BumpAlloc::scoped(...)` produces a tag that does
not escape the block. The mechanism is different but the outcome is the same — local
mutation does not appear in the external type.

### 13.6 Priority order

| Borrow | Cost | Value |
|---|---|---|
| `fun` vs `ctl` in effect declarations | Low — declaration syntax only | High — eliminates continuation allocation for the common case |
| `final ctl` for non-resuming operations | Low — declaration syntax + one compiler rule | High — zero-cost exceptions and early return |
| Evidence passing | Medium — implementation work | High — O(1) resumption; no heap box for synchronous handlers |
| Explicit open/closed effect row syntax | Low — syntax clarification | Medium — better inference and documentation |

---

## 14. The effect row is the type-level projection of the handler context — and it is a row of borrows

**Added 2026-07-23**, connecting three things that had not previously been put in the
same sentence: RFC-0113 (Context Parameters), the row/view machinery worked out in
`access-and-presence-rows.md` and `nominal-types-as-branded-rows.md`, and §8's own
aspect-desugaring. None of the source documents states this; it falls out of reading
them together.

### 14.1 A handler is an ordinary value; several handlers in scope form a row

§8 already establishes that a handler is an ordinary struct (or any type) implementing
the desugared effect aspect — the same principle as `Heap`/`BumpAlloc` implementing
`Alloc`, nothing effect-specific about the value itself. If several handlers can be
active simultaneously (a `Trace` handler and a `State<S>` handler both in scope), then
"what is currently in the bracket channel" is a set of `(role, handler value)`
bindings — structurally a row, whether or not anything in this cluster has called it
one before.

RFC-0113 supplies the labeling discipline for that row directly: context parameters are
"resolved by type… ambiguity is always a compile error," meaning at most one handler per
aspect may be in scope at once. That constraint is exactly what makes "the label is the
type" well-defined — an ordinary structural row's labels are arbitrary field names
chosen by the programmer; a context row's labels are implicitly the aspect being
resolved, a narrower discipline within the same general row mechanism, not a different
mechanism.

### 14.2 The effect row and the handler context are the same row, at two levels

Under that reading, `^{Trace, State<S>}` is not merely *analogous* to a row — it is the
**type-level projection** of the row whose **value-level instantiation** is "the actual
`Trace` and `State<S>` handler instances currently in scope." This is the same
type/value relationship this whole cluster has built out for ordinary structs (a
declared type and its concrete values), applied here to context instead of to fields.

### 14.3 Propagating context to a callee is ordinary row-narrowing, not new machinery

If a function `f`'s context row satisfies `{Trace, State<S>}` and it calls `g`, whose
own signature only needs `^{Trace}`, passing `f`'s context to `g` is the same
row-narrowing-and-passing operation `nominal-types-as-branded-rows.md` §8 already
specifies for ordinary structs — project down to the subset `g` needs, pass that. The
strict rule from that section's §8.2 (exact match, or an explicit narrowing step)
applies unchanged; nothing new needs designing for effect-context propagation
specifically.

### 14.4 Why this does not reopen the `Drop` transitivity problem

`nominal-types-as-branded-rows.md` §4.3 (and, before it, RFC-0091 §1's own "not
resolved" note) flagged transitivity through helper calls as the one place field-usage
tracking stays genuinely hard — because `Drop::drop` has **no written signature**
stating what it touches, so the required set has to be *inferred* from the body.
Effect-performing functions do not share that problem: `^{IO}` is *declared*, on every
function, by construction — that is the entire point of an effect system. Checking
whether a caller's context row covers a callee's declared effect row is therefore
ordinary row-subset type-checking, the same as any other bound check, not inference
over a call graph. This sharpens rather than contradicts the earlier finding: `Drop`'s
difficulty is specific to lacking what effect-performing code already has by
declaration.

### 14.5 This is an access row, not a presence row — worth keeping distinct

A handler is invoked by reference: §8's own desugared signature takes
`self: &self Self` (RFC-0065's lifetime-anchored `&self`). The "context row" being
passed from caller to callee is therefore a row of **borrows**, not owned values — an
*access* row in `access-and-presence-rows.md`'s vocabulary, which is the case that
already desugars for free (that document's §3), not the owned-narrowing case with its
stricter no-implicit-truncation rule (`nominal-types-as-branded-rows.md` §8.2). Handler
*state* (the fields the handler struct itself owns, e.g. a log buffer) stays an
ordinary owned value inside the handler; only the *reference to the handler* travels
through the context row.

### 14.6 What this does and does not settle

This reframes how the effect row's propagation could be checked — as reuse of
already-specified row machinery — rather than proposing new syntax, new runtime
behavior, or a new checking algorithm. It does not address evidence-passing,
continuation capture, or any of §2/§12's linearity concerns, which stay exactly as
open as they were. See Open Question 6 below for what remains unchecked.

---

## Open questions

1. `^ clean` (or similar) as an explicit declaration-site annotation forbidding active
   borrows at performance sites, vs. relying on the current implicit
   sendability-forces-synchronous constraint (§4, §10) — both sound, discoverability
   unresolved.
2. The linear-value-in-continuation static check (§12.3) — needed for effects to be
   sound once `Linear` exists, not yet specified precisely (what exactly counts as "in
   scope," how it interacts with partial consumption from `linear-types.md` §3) and not
   yet cross-referenced from `linear-types.md` itself.
3. `HandlerToken<'b, E>` (`brand-types.md` §5) for handler-state exclusivity and
   O(1) brand-directed dispatch — RFC-0076 sketches this against this report's
   evidence-passing model; not yet reconciled in either direction now that both
   documents live in this directory together.
4. Koka's `fun`/`ctl`/`final ctl` split and evidence-passing (§13) — not adopted, not
   rejected; flagged as the highest-value borrow from prior art whenever effect syntax
   moves from proposed to an actual RFC.
5. Whether `effect`/`handle`/`resume` syntax should become its own RFC, and if so how
   it's sequenced against the rest of the substructural-types cluster — not addressed
   here; a project-planning question, not a design one.
6. **(§14) Does the context-row-as-effect-row reading actually hold once more than one
   handler of the same aspect could plausibly want to be in scope** — e.g. nested
   `handle` blocks for the same effect, shadowing rather than erroring? RFC-0113's
   "ambiguity is always a compile error" rule is what makes the labeling-by-type
   discipline well-defined; whether real handler-nesting patterns ever need to violate
   that uniqueness constraint is unchecked. Also unchecked: whether `.narrow()`
   (`nominal-types-as-branded-rows.md` §8.3) is the actual mechanism context-row
   propagation should use, or whether context resolution already has its own,
   independently-specified propagation rule in RFC-0113 that this section's reading
   needs to reconcile with rather than assume matches.
