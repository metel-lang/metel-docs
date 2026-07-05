---
id: algebraic-effects-and-memory-model
title: "Algebraic Effects and the Metel Memory Model"
type: report
created_date: '2026-06-29'
rfcs: [0003, 0063, 0064, 0065, 0066, 0067, 0068, 0069, 0071, 0072]
reports: [substructural-and-separation-types, per-field-multiplicities]
---

# Algebraic Effects and the Metel Memory Model

*Grounded in RFC-0063 (Region Handles), RFC-0065 (Ergonomics), RFC-0066 (Extraction),
RFC-0067 (Reference Types), RFC-0068 (Struct-Owned Regions), RFC-0069 (Sub-Region Typing),
RFC-0071 (Ownership and Move Semantics), RFC-0072 (Negative Bounds), RFC-0003 (Concurrency),
and the design explorations in `substructural-and-separation-types.md` and
`per-field-multiplicities.md`.*

> **Status of effect syntax**: The `effect`, `^ EffectName`, `handle`, and `resume`
> constructs described in this report are **proposed** — not yet specified in any RFC and
> not implemented. All other syntax follows the current language spec and the accepted
> RFC-006x cluster.

---

## What this document covers

Algebraic effects are a mechanism for structured side-effect handling: a computation
declares what effects it may perform, and a surrounding `handle` block intercepts each
effect invocation, receives the suspended computation as a first-class value (the
*continuation*), and decides whether to resume it, abort it, or resume it multiple times.
This report analyses how that mechanism would interact with Metel's memory model as settled
by the RFC-006x cluster and RFC-0071. Most of the safety story falls out of rules that
already exist. A small number of genuine tensions require new constraints, and one open
question remains.

---

## 1. The memory model in three sentences

All heap allocation goes through a named region. Every pointer `@[r] T` carries the name
of its allocator as a type-level tag, and that tag is the lifetime bound and the
disjointness proof simultaneously. References `&T` and `&mut T` are non-owning borrows —
non-sendable, non-escaping, orthogonal to allocation.

The rules that matter most for this analysis:

- **Affine ownership (RFC-0071)**: non-`Copy` values move by default; exactly one live
  owner at any point. `Copy` and `Drop` are mutually exclusive. Dropping a value runs
  `Drop::drop` if implemented, then recursively drops fields.
- **Sendability (RFC-0063 §4)**: `@[Heap] T` is sendable across fibers; `@[LocalHeap] T`
  is thread-local; scoped `@[r] T` is never sendable. References `&T` and `&mut T` are
  never sendable.
- **Negative bounds (RFC-0072)**: `T: !Drop` is satisfied when no `Drop` impl exists for
  `T`. Move-out from a bulk-deallocating scoped arena requires `T: !Drop`.

---

## 2. The continuation is an affine heap-allocated value

When a computation performs an effect, it suspends. The "rest of the computation" —
everything that would have run after the effect site — is captured as a *continuation* and
handed to the handler. The type of this value in Metel's model is:

```
@[Heap] Continuation<ResumeValue, FinalResult>
```

**Why `@[Heap]`**: the continuation must outlive the effect-call stack frame that created
it, so it cannot be allocated into a scoped arena. `Heap` is the only region kind that
supports indefinite lifetime. The continuation is heap-allocated, individually freed when
the handle is consumed.

**Why affine**: `@[Heap] T` is non-`Copy` by construction (RFC-0063 §2, RFC-0071 §2).
Moving the continuation transfers exclusive ownership. There is no mechanism to duplicate
it — calling `resume` twice would require two owners of the same value, which affine move
semantics make a compile error. One-shot resumption is not a special rule added for
effects; it falls out of the general ownership model.

**Multi-shot continuations**: multi-shot continuations — where `resume` may be called more
than once — cannot be expressed with the current model, because `@[Heap] Continuation<V,
R>` is affine. Making a continuation multi-shot would require `Continuation` to implement
`Clone`. This is a legitimate constraint: any continuation that captures non-`Clone` values
(most structs, region pointers) cannot be multi-shot. Continuations that capture only
`Copy` or `Clone` values could support cloning, and the programmer would write
`k.clone().resume(v)` explicitly. Whether the language should provide syntax for this is a
separate design question.

---

## 3. Region tags determine continuation sendability precisely

A continuation captures the entire suspended stack frame: all bindings live at the effect
site. Each of those bindings carries a region tag. The continuation's sendability follows
from the most restrictive tag among its captured values:

| Captured value type | Continuation sendable |
|---|---|
| `@[Heap] T`, `Copy` values, primitives | yes, if nothing else prevents it |
| `@[LocalHeap] T` | no — thread-local |
| `@[r] T` (scoped region) | no — region may be freed before the fiber terminates |
| `&T`, `&mut T` (any reference) | no — references are never sendable |

This is not an approximation. The tag encodes the exact lifetime relationship. There is no
separate `RegionFree` marker to reason about: the type of each captured value already
carries the answer.

**Practical implication for handlers**: a handler that receives a non-sendable continuation
can only use it within the current fiber. It may call `resume` synchronously, pass the
continuation to another function in the same fiber, or store it in a struct on the same
fiber. It may not send it through a `Chan<T>`, pass it to `spawn { }`, or otherwise move
it across a fiber boundary. Any attempt to do so produces a compile error at the `Chan`
send or the `spawn` capture — the ordinary sendability rules catch it.

A handler for a computation that holds only heap-allocated or `Copy` values receives a
sendable continuation. That continuation may be stored in a channel, shipped to a worker
fiber, and resumed from there — an async effect handler — with no special annotation or
unsafe required. The type system permits exactly the handlers that are safe.

---

## 4. The `&mut T` constraint: the real design tension

This is the most important interaction in the model, and it comes entirely from RFC-0067.

`&mut T` is exclusive and non-sendable by construction. It is also non-escaping: the
borrow checker guarantees no `&mut T` outlives its source. If a computation holds an
active `&mut T` borrow and performs an effect, the continuation captures that borrow. Two
properties follow immediately:

1. The continuation is non-sendable — async handlers are ruled out.
2. The original binding is inaccessible to the handler code: the `&mut` borrow is
   outstanding, so the handler cannot touch the same location the suspended computation is
   borrowing.

The second point is sound. It means that while the computation is suspended, the handler
cannot concurrently mutate the value the computation has exclusively borrowed. The problem
is a practical one: if the handler does not resume synchronously, the `&mut` borrow hangs
open for as long as the continuation is unresolved. The handler cannot re-borrow the
location, the original value cannot be moved, and no other code can access it mutably.

**The constraint in concrete terms**: performing an effect while holding an active `&mut T`
borrow restricts the handler to synchronous resumption. The handler receives the
continuation, calls `resume`, and the borrow ends when the computation reaches the end of
the original scope. An async handler that stores the continuation for later would leave
the `&mut` borrow hanging indefinitely — the borrow checker prevents this by making the
continuation non-escaping in any way that would outlive the borrow's scope.

**The resolution**: well-designed effect handlers rarely need to suspend computations that
hold active `&mut` borrows. An `IO` effect for printing holds no borrows. A `State` effect
that reads and writes logical state holds logical state, not raw borrows into physical
memory. The fix is to release the borrow before performing the effect — a natural
refactoring the borrow checker guides you toward with a compile error that names the type.

If the language wants to enforce this statically at the effect declaration site, an effect
could carry an annotation requiring that no active borrows exist at performance sites:

```metel
effect IO ^ clean { ... }
```

Whether `^ clean` or a similar constraint is worth adding as explicit syntax is an open
question. The implicit enforcement through sendability is correct; the question is whether
it is discoverable enough.

---

## 5. Abort without resuming: `Drop` handles it

Not every handler calls `resume`. A handler may choose to abort — return a value without
ever resuming the suspended computation. In that case the continuation goes out of scope
unconsumed.

`@[Heap] Continuation<V, R>` is an affine value. If it goes out of scope without being
moved or consumed, its `Drop::drop` runs — the same way any heap-allocated struct with a
`Drop` impl is cleaned up. `Continuation::drop` recursively drops every value captured in
the suspended frame, following RFC-0071's drop ordering: fields in declaration order, then
any owned regions.

If captured values themselves implement `Drop`, their destructors run as part of the
cascade. A suspended `FileHandle` that was open when the effect was performed — and whose
handler aborted without resuming — gets `FileHandle::drop` called on it automatically. No
special effect-specific machinery is needed. The standard `Drop` protocol handles it.

---

## 6. Handler state via struct-owned regions

A handler that accumulates state during effect handling is a natural candidate for `[own
r]` (RFC-0068). The arena's lifetime equals the handler struct's lifetime; all
accumulation is arena-allocated; everything is freed when the handler drops.

Handler methods have access to two distinct lifetimes: `r` (the struct's own arena, always
implicitly in scope inside `impl` blocks) and a per-call borrow duration `s` (the
duration of the specific `&mut self` borrow). A return type of `&[r] T` means the returned
reference is valid for the *struct's* lifetime, not just the duration of the call.

Allocation into the owned region requires `&mut self`; shared `&[s] self` can read and
borrow from the arena but cannot allocate into it — the same exclusivity constraint as
RFC-0063 §1.

---

## 7. SubRegion and handle blocks inside regions

When a `handle` block lives inside a scoped region, RFC-0069 wires the lifetime
relationships automatically. If a handler struct is allocated into an outer region `R`, its
owned arena is typed as `SubRegion<R>` at the allocation site. The compiler derives `R:
Outlives<r>` without any annotation.

The continuation `k: @[Heap] Continuation<V, R>` is heap-allocated — independent of both
the outer region and the handler's arena. If the computation used scoped-region values
internally, those are captured in `k` with scoped tags, making `k` non-sendable. The
handler receives a non-sendable continuation, which it can only resume synchronously. For
the common single-fiber, synchronous handler case, none of this is a problem.

SubRegion transitivity (RFC-0069 §3) applies naturally to nested handles. If a
computation's arena `r: SubRegion<outer>` contains structs with their own owned arenas
`s: SubRegion<r>`, the full chain `outer: Outlives<r>`, `r: Outlives<s>`, and therefore
`outer: Outlives<s>` is derived without annotation.

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
    fun log[s](self: &[s] Self, msg: String, k: @[Heap] Continuation<(), Self::Output>) -> Self::Output;
}
```

Performing an effect inside a computation desugars to calling the aspect method on the
implicit handler value in the bracket channel, passing the current continuation as the
last argument. The bracket channel and aspect dispatch are already in the language. The
only genuinely new runtime piece is continuation capture — snapshotting a call frame — which
the current tree-walking evaluator does not support. The type system is ready; the
implementation work is in the runtime.

---

## 9. Interaction with structured parallelism (RFC-0064, deferred)

RFC-0064's `||` combinator requires both branches to complete before returning. If an
effect is performed inside a `||` branch, the continuation captures that branch's stack.
The continuation cannot escape the combinator's synchronisation boundary — it must be
resumed or dropped before the `||` expression returns. This is automatically enforced: the
continuation's captured region tags include the branch's scoped region (if any), making it
non-sendable and therefore non-escapable past the `||` join point.

This means effect handlers inside `||` branches must be synchronous — consistent with
`||`'s structured semantics. No additional constraint is needed; the tag-based sendability
rule already does the right thing.

---

## 10. Summary table

| Concern | Mechanism | RFC |
|---|---|---|
| One-shot resumption | `@[Heap] Continuation` is affine — not `Copy`, cannot duplicate | RFC-0071 |
| Abort without resuming | `Continuation::drop` cascades to all captured values | RFC-0071 §3 |
| Scoped region data in frame | Continuation inherits scoped tag → not sendable | RFC-0063 §4 |
| Cross-fiber async handlers | Legal only when all captured values are `@[Heap]`/`Copy` | RFC-0063 §4 |
| Active `&mut T` borrow in frame | Non-sendable; original location inaccessible; synchronous only | RFC-0067 |
| Handler-local state allocation | `struct Handler[own r]` — arena freed with handler | RFC-0068 |
| Handler inside scoped region | `SubRegion<R>` at allocation site — `Outlives` derived automatically | RFC-0069 |
| Move-out on resume | Type-directed move-out / ascription — standard extraction form | RFC-0066 |
| `T: !Drop` in continuation internals | Scoped-arena data in continuation requires `T: !Drop` for safe bulk-free | RFC-0072 |

**What falls out for free**: one-shot enforcement, abort cleanup, sendability constraints,
handler state lifetime, nested region relationships. These are all consequences of existing
rules applied to `@[Heap] Continuation<V, R>` as an ordinary value.

**What is genuinely new**: the `handle` block syntax, the runtime mechanism for capturing
continuations (snapshotting a call frame), and the implicit-parameter wiring that threads
the handler through the call graph to the effect site. These are implementation work, not
type-system work.

**The one open question**: whether performing an effect while holding an active `&mut T`
borrow should be a compile error at the effect declaration site (a `^ clean` annotation),
or whether the current implicit constraint — handlers receive non-sendable continuations and
are restricted to synchronous resumption — is sufficient ergonomically. Both are sound; the
question is discoverability.

---

## 11. Usage examples

The examples below illustrate the system in practice. They assume single-region elision
(RFC-0065) is active, so bare `@` in type and expression position elides to the unique
in-scope region.

---

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
read, nothing else. Swapping handlers is the entire test strategy — no mocking framework,
no dependency injection wiring, no interface extraction.

---

### 11.2 Tracing with an arena-backed handler

Handler state that accumulates during the computation lives in a struct-owned arena
(RFC-0068). The whole trace is freed in one shot when the handler drops.

```metel
effect Trace {
    fun log(msg: String) -> ()
}

struct TraceHandler[own r] {
    entries: @[r] List<String>,
    count:   i64,
}

impl TraceHandler {
    fun new() -> TraceHandler {
        TraceHandler { entries: @List::Nil {}, count: 0 }
    }

    fun handle_log[s](self: &mut [s] TraceHandler, msg: String, k: @[Heap] Continuation<(), T>) -> T {
        self.entries = @List::Cons { head: @msg, tail: self.entries };
        self.count  += 1;
        k.resume(())
    }

    fun summary[s](self: &[s] TraceHandler) -> String {
        "${self.count} events logged"
    }
}

fun process_order(order_id: i64) ^ Trace -> Result<Invoice, OrderError> {
    Trace::log("begin order ${order_id}");
    let items = fetch_items(order_id)?;
    Trace::log("fetched ${array_len(items)} items");
    let invoice = compute_invoice(items)?;
    Trace::log("invoice total: ${invoice.total}");
    Result::Ok { value: invoice }
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

Every `@msg` inside `handle_log` goes into `TraceHandler`'s owned arena `r`. The arena's
lifetime equals the `tracer` variable's lifetime; the borrow checker enforces that any
`&[r] String` borrow is valid only while `tracer` is alive. When `tracer` drops, the arena
bulk-frees all entries with a single deallocation — no per-entry destructor calls when
`String: !Drop`.

---

### 11.3 Short-circuit / abort

A handler arm that does not call `resume` short-circuits the entire computation. The
continuation is dropped, and `Drop` cascades to everything the suspended computation was
holding.

```metel
effect Lookup {
    fun find(key: String) -> Perhaps<String>
}

// Builds config by looking up keys — pure logic, no I/O knowledge
fun build_config() ^ Lookup -> Config {
    let host = match Lookup::find("host") {
        Perhaps::Some { value: h } => h,
        nope                       => "localhost",
    };
    let port_str = match Lookup::find("port") {
        Perhaps::Some { value: p } => p,
        nope                       => "8080",
    };
    Config { host, port: port_str.parse_i64() }
}

// Handler: look up in a HashMap
fun config_from_map(map: &HashMap<String, String>) -> Config {
    handle build_config() {
        Lookup::find(key) => resume(map.get(key))
    }
}

// Handler: env vars first, file second — composed from the same computation
fun config_layered(file_map: &HashMap<String, String>) -> Config {
    handle build_config() {
        Lookup::find(key) => {
            let val = match env_get(key) {
                Perhaps::Some { value: v } => Perhaps::Some { value: v },
                nope                       => file_map.get(key),
            };
            resume(val)
        }
    }
}

// Handler: abort entirely when a required key is missing
fun config_strict(map: &HashMap<String, String>) -> Result<Config, String> {
    handle build_config() {
        Lookup::find(key) => {
            match map.get(key) {
                Perhaps::Some { value: v } => resume(Perhaps::Some { value: v }),
                nope => {
                    // No resume — k is dropped here.
                    // Drop cascades: anything build_config held at this effect site
                    // gets its Drop::drop called automatically.
                    Result::Err { error: "missing required key: ${key}" }
                }
            }
        }
    }
}
```

`build_config` has no idea which handler it runs under. Every handler composes cleanly
because the effect declaration is the complete interface — no config source is baked into
the logic.

---

### 11.4 The `&mut T` constraint in practice

References are never sendable. A continuation that captures an active `&mut T` is
non-sendable and forces synchronous resumption. The fix is to release the borrow before
performing an effect.

```metel
effect IO {
    fun print(s: String) -> ()
}

// Problem: &mut Buffer is active at the effect site.
// The continuation captures the borrow — handler must resume synchronously.
fun annotate_buffer_wrong(buf: &mut Buffer) ^ IO {
    IO::print("writing to buffer");   // &mut buf active here — borrow in continuation
    buf.write("hello");
}

// Fix: release the borrow before the effect.
// &mut buf is NOT active when IO::print is called — handler can be anything.
fun annotate_buffer(buf: &mut Buffer) ^ IO {
    let msg = "writing ${buf.len()} bytes";   // read through &mut, then release
    IO::print(msg);                            // no active borrow here
    buf.write("hello");                        // &mut taken again after effect site
}

// The pattern scales — release, effect, re-borrow.
fun process_batch(items: &mut List<Item>) ^ IO {
    let count = items.len();              // read, release
    IO::print("processing ${count}");    // no borrow active
    for (let item in items) {            // borrow taken again inside loop
        transform(item);
    }
}
```

If `annotate_buffer_wrong` is used with an async handler, the compiler rejects it — not
because effects are involved, but because the continuation contains a non-sendable `&mut
Buffer`. The error names the type; you know exactly what to fix.

---

### 11.5 Sendability — heap data enables async handlers

When the computation works only with `@[Heap]` values and `Copy` types, the continuation
is sendable. This enables a worker-pool handler with no unsafe, no special annotations.

```metel
use Heap;

struct Task  { id: i64, payload: @[Heap] String }
struct Output { id: i64, result: @[Heap] String }

effect Compute {
    fun run(task: @[Heap] Task) -> @[Heap] Output
}

// All data is @[Heap], no scoped regions, no &mut borrows at effect sites.
// Continuation will be sendable.
fun pipeline(tasks: @[Heap] List<Task>) ^ Compute -> @[Heap] List<Output> {
    let mut results = @[Heap] List::Nil {};
    for (let task in tasks) {
        let output = Compute::run(task);      // effect site — no &mut, no scoped tags
        results = @[Heap] List::Cons { head: output, tail: results };
    }
    results
}

struct WorkItem {
    task: @[Heap] Task,
    k:    @[Heap] Continuation<@[Heap] Output, @[Heap] List<Output>>,
}

// Async handler: send work to a fiber pool, resume from there.
// Legal because @[Heap] Continuation<...> is sendable — all captured values are @[Heap].
fun run_parallel(tasks: @[Heap] List<Task>) -> @[Heap] List<Output> {
    let work_ch: Chan<WorkItem> = Chan::new();

    spawn { worker_loop(&work_ch) }.detach();

    handle pipeline(tasks) {
        Compute::run(task) => {
            // k is sendable — ship it to the worker pool
            work_ch <- WorkItem { task, k };
            // handler arm ends without resume — worker calls k.resume(output) later
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

Try the same with `@[r] Task` instead of `@[Heap] Task` — `work_ch <- WorkItem { task, k
}` becomes a compile error. The tag `[r]` makes the continuation non-sendable; the channel
send requires `Send`; the error names the scoped region. The fix is to move the data to
`@[Heap]` for anything that crosses fiber boundaries, or to use a synchronous handler.

---

### 11.6 SubRegion and handle blocks inside regions

When both the computation and the handler live inside the same scoped region, `SubRegion<R>`
wires the lifetimes automatically.

```metel
effect Parse {
    fun emit_node(node: AstNode) -> ()
}

fun parse_expr(src: &String) ^ Parse {
    // ... parse logic ...
    Parse::emit_node(AstNode::Literal { val: 42 });
    Parse::emit_node(AstNode::Add {});
}

struct AstBuilder[own r] {
    nodes: @[r] List<AstNode>,
}

impl AstBuilder {
    fun new() -> AstBuilder {
        AstBuilder { nodes: @List::Nil {} }
    }

    fun handle_emit[s](self: &mut [s] AstBuilder, node: AstNode, k: @[Heap] Continuation<(), ()>) {
        self.nodes = @List::Cons { head: @node, tail: self.nodes };
        k.resume(())
    }
}

fun build_ast(src: &String) -> @[Heap] List<AstNode> {
    use Heap;
    // AstBuilder allocated into Heap — its owned arena r : SubRegion<Heap> automatically
    let mut builder = @[Heap] AstBuilder::new();

    handle parse_expr(src) {
        Parse::emit_node(node) => builder.handle_emit(node, k)
    }

    // Clone node list to Heap before builder drops — scoped arena cannot outlive builder
    let result: @[Heap] List<AstNode> = builder.nodes.clone_into[Heap]();
    result
    // builder drops here — AstBuilder's arena freed in bulk
}
```

`SubRegion<Heap>` is assigned at `@[Heap] AstBuilder::new()`: the compiler derives
`Heap: Outlives<r>` automatically. The borrow checker knows that `&[r] AstNode` borrows
are bounded by `builder`'s lifetime, so returning them past `build_ast`'s scope is a type
error — which is why `clone_into[Heap]()` is needed to extract the list first.

---

### Example summary

| Example | Primary point |
|---|---|
| Testable IO | Effect as a seam — swap handlers to test without mocking frameworks |
| Arena-backed tracer | `[own r]` for handler state; bulk-free on drop; zero per-entry overhead |
| Short-circuit / abort | Not calling `resume` is valid; `Drop` cascades automatically |
| `&mut T` constraint | Release borrows before effect sites; compiler guides you |
| Sendable continuations | `@[Heap]`-only computations enable async/worker-pool handlers |
| SubRegion in handle block | Nested lifetimes resolved without annotation; clone before drop |

---

## 12. Linear capability tokens, typestate, and per-field multiplicities

*Based on the design explorations in `substructural-and-separation-types.md` and
`per-field-multiplicities.md`. Neither `linear struct`, `phantom`, nor per-field
multiplicities are yet in any RFC; this section treats them as design options.*

The region-based memory model handles allocation lifetime and sendability. Linear
capability tokens and typestate address a different concern: *protocol correctness* —
ensuring resources are used in the right order and always explicitly terminated. The
two systems are orthogonal but interact deeply at effect boundaries.

---

### 12.1 Linear tokens as effect arguments: handlers must clean up even on abort

The substructural report proposes separating a resource's address from the permission
to use it:

```metel
struct FileHandle { fd: i64 }          // freely copyable — the address
linear struct FileCap { fd: i64 }      // must be consumed exactly once — the permission
```

When an effect operation takes a linear value as an argument, the handler receives that
value and becomes its owner:

```metel
effect FS {
    fun read(h: FileHandle, cap: linear FileCap) -> (String, linear FileCap)
    fun close(h: FileHandle, cap: linear FileCap) -> ()
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
`cap` exits scope unconsumed. This is the correct behavior — a handler that aborts cannot
silently leak a resource the computation passed to it. The handler author is forced to
be explicit about cleanup regardless of whether they resume.

Compare with the affine case (`@[Heap] FileCap`): `Drop::drop` would run automatically
on abort. Linear is stricter — it says "this must be explicitly terminated, not just
freed," which is right for values where a silent drop is a bug: uncommitted transactions,
unsent acknowledgements, unclosed protocol states.

---

### 12.2 Typestate through effect boundaries: flows via the resume type

Phantom typestate parameters compose with effects without friction. The effect
operation's return type is what `resume` must provide, directly controlling what
protocol state the computation continues in:

```metel
struct Socket<State> {
    fd:     i64,
    _state: phantom State,   // zero-size; erased at runtime
}

struct Listening {}
struct Accepting {}
struct Closed    {}

effect Net {
    fun accept(sock: Socket<Listening>) -> (Socket<Accepting>, Socket<Listening>)
    fun recv(sock: Socket<Accepting>)   -> ([u8], Socket<Accepting>)
    fun close(sock: Socket<Accepting>)  -> Socket<Closed>
}
```

A test handler controls what state the computation resumes with:

```metel
handle server_loop(listening_sock) {
    Net::accept(sock) => {
        resume((
            Socket { fd: mock_fd(), _state: phantom },
            sock
        ))
    }
    Net::recv(sock) => {
        resume(([b"GET / HTTP/1.1"], sock))
    }
    Net::close(sock) => {
        resume(Socket { fd: -1, _state: phantom })
    }
}
```

If a handler arm passes the wrong state to `resume` — say `Socket<Closed>` where
`Socket<Accepting>` is expected — it is a type error at the `resume` call site. The
computation's protocol invariant is statically preserved across the effect boundary.

Typestate also constrains how a handler simulates errors. A handler cannot resume
`Net::recv` with `Socket<Closed>` to signal a dropped connection, because `recv`'s
resume type is `([u8], Socket<Accepting>)`. To abort on error, the handler simply does
not call `resume`. This is the correct design: "error" is an abort, not a lie about
state.

---

### 12.3 The real tension: linear values captured in continuations

The interaction between linear values and effect performance sites requires a new static
constraint that neither system currently has.

Consider a computation that holds a linear capability at an effect site but does not
pass it to the effect operation:

```metel
fun process() ^ IO {
    let (handle, cap) = open("/tmp/log.txt");   // cap: linear FileCap

    IO::print("about to read");   // cap is in scope but NOT passed to IO::print
                                  // continuation captures cap

    let (line, cap) = FS::read(handle, cap);
    FS::close(handle, cap);
}
```

When `IO::print` performs its effect, the continuation captures `cap`. If the handler
aborts without calling `resume`, the continuation is dropped. `Continuation::drop`
attempts to drop `cap` — but `cap` is linear and has no `Drop` impl. This is unsound.

**The required check**: at every effect-performance site, the checker verifies that no
unconsumed linear values without `Drop` remain in scope unless they are explicitly
passed to the effect as arguments. Performing an effect while holding a "dangling" linear
capability is a compile error:

```
error: linear value `cap` is in scope at effect site but not consumed or passed as an argument
  --> ...
   | IO::print("about to read");
   | cap must be consumed before this effect, or passed through it
```

The two valid resolutions:

**Restructure to avoid overlap** — acquire linear values after effect sites that don't
need them:

```metel
fun process() ^ IO {
    IO::print("about to read");                    // no linear values in scope — fine
    let (handle, cap) = open("/tmp/log.txt");      // acquire after the effect site
    let (line, cap)   = FS::read(handle, cap);
    FS::close(handle, cap);
}
```

**Thread the linear value through the effect** — include it as an argument so the
handler receives it and must resume with it:

```metel
effect IO {
    fun print<linear T>(through: T, s: String) -> T   // T is threaded in and out
}

let cap = IO::print(cap, "about to read");   // handler receives cap, must resume(cap)
```

The second form is the general solution for cases where the linear value genuinely spans
the effect site. The handler can inspect or transform the value but must always return
it to the computation via `resume`, or explicitly consume it when aborting.

---

### 12.4 Per-field multiplicities resolve the hybrid case

The per-field multiplicities report proposes `phantom linear` fields — zero-size fields
with exactly-once consumption obligations embedded inside an otherwise-ordinary struct.
This gives a single type that simultaneously enforces both protocol ordering (via the
phantom state parameter) and leak prevention (via the linear capability field):

```metel
struct Socket<State> {
    fd:   i64,
    _cap: phantom linear (),   // multiplicity 1: must consume exactly once
    _st:  phantom State,       // multiplicity 0 at runtime: protocol tag only
}
```

This composes cleanly with effects. When `Net::close(sock)` is performed, `sock` —
which carries the linear `_cap` — is moved out of the computation and into the handler
as an effect argument. The handler must consume it:

```metel
Net::close(sock) => {
    let closed = sys_close(sock);   // sys_close takes Socket<Accepting>, returns Socket<Closed>
                                    // sock consumed, _cap obligation satisfied
    resume(closed)
}
```

The continuation holds nothing linear from the closed-over socket (it was moved to the
handler). The per-field multiplicity model makes this clean: the `fd: i64` field
(multiplicity ω) is freely readable through borrows without touching the linear
obligation, while `_cap` (multiplicity 1) enforces the terminal action. Only the
consuming `self` operation triggers the linearity check.

The practical consequence: a single `Socket<Open>` value enforces protocol ordering via
`phantom State` *and* prevents leaks via `phantom linear ()`, and effects thread both
constraints through the handler boundary simultaneously via the same move.

---

### 12.5 Summary

| Interaction | Behavior |
|---|---|
| Linear token as effect argument | Handler must consume it even on abort — enforced by linearity checker |
| Typestate via phantom parameter | Flows through effect boundary via the resume type; wrong-state resume is a compile error |
| Linear value in scope at effect site, not passed | Unsound on abort — requires a new static check at effect-performance sites |
| Threading linear values through effects | Pass as effect argument; handler receives it and must consume or resume with it |
| Per-field multiplicities (`phantom linear`) | Collapses address + capability into one type; threads both constraints through effect boundaries via the same move |

The third row is the only interaction that requires new machinery beyond what either
system currently specifies. Everything else composes from the linearity checker, the
typestate type parameter, and the existing effect resume-type discipline.

---

## 13. Lessons from Koka

Koka is the most mature algebraic-effect language and the closest design point to what
this report proposes. Several of its decisions are directly applicable to Metel; others
solve problems Metel does not have.

### 13.1 `fun` vs `ctl`: most operations don't need a continuation

Koka splits effect operations into two kinds at the declaration site:

- **`fun`** — the operation always resumes exactly once with a value, like a function
  call. No continuation needs to be captured; the handler computes a value and returns.
- **`ctl`** — the handler decides whether to resume, how many times, and with what. Full
  continuation machinery is required.

Metel's current proposal treats all effect operations uniformly — every performance
allocates a `@[Heap] Continuation`. That is unnecessarily expensive. The vast majority of
practical effects (state reads, configuration queries, logging) are `fun`-style: resume
exactly once immediately. Distinguishing them at the declaration site lets the compiler
skip continuation allocation for the common case:

```metel
effect State<S> {
    fun get() -> S       // always resumes once — no continuation allocated
    fun set(x: S) -> () // same
}

effect Yield<T> {
    ctl yield(x: T) -> Bool   // handler decides whether to resume — continuation required
}
```

This is a declaration-level change with no effect on the semantics visible to the
programmer. State and reader effects become zero-overhead; generators and async retain
full power.

### 13.2 `final ctl`: non-resuming operations need no continuation at all

Koka's `final ctl` marks operations that never resume. The compiler allocates no
continuation — the handler is a straight abort.

```metel
effect Fail {
    final ctl fail(msg: String) -> !   // ! = Never; never resumes
}

fun safe_div(x: I32, y: I32) -> @[Fail] I32 {
    if y == 0 { Fail::fail("division by zero") } else { x / y }
}

fun run_safe<T>(f: fun() -> @[Fail] T) -> Perhaps<T> {
    handle f() {
        Fail::fail(msg) => Perhaps::None    // no resume call — final handler
    }
}
```

This covers exceptions, panics, and early return — the most common "effectful" operations
in practice — at zero continuation cost. Without the distinction every `fail()` call would
allocate and immediately discard a continuation.

### 13.3 Evidence passing: O(1) resumption without heap allocation

Koka dispatches effect operations via *evidence passing*: each effectful function receives
hidden parameters pointing to the nearest handler in the call stack. Resuming a `ctl`
continuation is then a return from a function — the stack frame is already in place.

The current Metel proposal boxes continuations into `@[Heap] Continuation<V, R>`. That is
sound but potentially expensive: every effect performance allocates. Evidence passing
avoids this for single-shot synchronous handlers, which are the overwhelmingly common case.

The two approaches are not in conflict. A practical implementation could use evidence
passing for `fun` and `final ctl` operations and only box into `@[Heap] Continuation` for
multi-shot or cross-fiber handlers — those where the continuation genuinely needs to
outlive the handler's stack frame. The programmer's code is unchanged; only the generated
code differs. This is an implementation strategy, not a language design change, but it is
the reason Koka's effects are competitive with hand-written state machines in benchmarks.

### 13.4 Open effect rows for higher-order composability

Koka's effect rows distinguish closed and open effect sets:

- `<io>` — exactly `io`, nothing more
- `<io|e>` — at least `io`, plus whatever is in `e`

The open tail `|e` is what makes effect-polymorphic standard library functions work.
Without it, a `map` that accepts a closure must either enumerate every effect the closure
might perform or discard the effect information entirely. With it:

```metel
// open — map carries whatever effects f carries, plus nothing extra
fun map<T, U, E>(xs: List<T>, f: fun(T) -> U ^ {E}) -> List<U> ^ {E} { ... }

// closed — run_logged accepts only IO closures; anything more is a type error
fun run_logged(f: fun() -> () ^ {IO}) -> () { ... }
```

Metel's current `^` annotation uses a type variable `E` for effect polymorphism, which
achieves the same result. The Koka insight is that making the closed/open distinction
*syntactically explicit* — `{IO}` vs `{IO | E}` — prevents a class of inference
ambiguities at higher-order call sites and makes the constraint visible in documentation.

### 13.5 What not to borrow

**Perceus / functional-but-in-place.** Koka needs Perceus because it has no
programmer-visible regions — it must infer when memory can be reused. Metel's explicit
region system (`BumpRegion`, `AutoRegion`, `@[r]`) gives the programmer direct control
over allocation patterns. Perceus solves a problem Metel does not have.

**`st<h>` effect elimination.** Koka tracks all mutation through `ref<h,a>` and erases
the heap variable `h` when it does not escape the function. Metel handles the same case
with scoped regions: allocation into a `BumpRegion::scoped` or `AutoRegion::scoped` block
produces a tag that does not escape the block. The mechanism is different but the outcome
is the same — local mutation does not appear in the external type. No new machinery is
needed.

### 13.6 Priority order

| Borrow | Cost | Value |
|---|---|---|
| `fun` vs `ctl` in effect declarations | Low — declaration syntax only | High — eliminates continuation allocation for the common case |
| `final ctl` for non-resuming operations | Low — declaration syntax + one compiler rule | High — zero-cost exceptions and early return |
| Evidence passing | Medium — implementation work | High — O(1) resumption; no heap box for synchronous handlers |
| Explicit open/closed effect row syntax | Low — syntax clarification | Medium — better inference and documentation |
