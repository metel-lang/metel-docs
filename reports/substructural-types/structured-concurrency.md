---
id: structured-concurrency
title: "Structured Concurrency: Fibers, Channels, and the Linear Join Handle"
type: report
status: active
last_synced_against_model: '2026-07-07'
supersedes: null
revives: "reports/substructural-types/archive/substructural-and-separation-types.md sections 7-8"
---

# Structured Concurrency: Fibers, Channels, and the Linear Join Handle

*Living document — updated in place, not a point-in-time snapshot.*

*Exploration, not a decision. Revived from `archive/substructural-and-separation-types.md`
§7–8. Syntax updated throughout: `*T`/`*mut T` → `&T`/`&var T` (RFC-0067), `own T` → `@Heap T`.*

> **Updated 2026-07-07 — `||` dropped from the design.** The `||` fork-join combinator
> (RFC-0064) has been **retracted**: it barely interacted with the rest of the language
> and did not add enough value to justify a *second* concurrency mechanism alongside
> `spawn` + `Chan<T>`. Three consequences, all reflected below:
> 1. The structured guarantee `||` provided — *a fiber cannot be silently abandoned* —
>    needs a new home, but **which mechanism carries it is left open** (reopened
>    2026-07-07 as premature to settle). The leading candidate (§3) is a `Linear` `spawn`
>    handle — `spawn` returns a `JoinHandle<T>` discharged by `.join()` or an explicit
>    `.detach()`, forgetting either a compile error — which would absorb `brand-types.md`'s
>    `JoinToken<'b>` into the primitive that already exists. Alternatives (a standalone
>    `fork`/`JoinToken`, or an affine handle with no static guarantee) are not ruled out.
> 2. The **Capture Separation Calculus (CSC)** — capture-set disjointness, `sep{}`,
>    same-allocation splits via `split_at_mut` — existed primarily to give `||` a
>    sub-allocation-granularity disjointness witness. With `||` gone it has no consumer;
>    it is demoted to a deferred possibility, kept for the record in §5, motivated only by
>    a hypothetical future liberalized `spawn`.
> 3. The one capability genuinely given up is **ergonomic shared-memory data parallelism**
>    (parallel map/reduce over one arena or array *without* transferring ownership of the
>    parts). This is deferred, not refused — it can return later as a library or a
>    liberalized-`spawn`+CSC feature if real demand materializes.

---

## 1. One model: fibers over channels

Metel's concurrency model is a single level, not two: lightweight fibers via `spawn`,
M:N scheduled (no async/await, no function coloring), communicating through typed
channels `Chan<T>` (`ch <- val` send, `<- ch` receive), multiplexed with `select`
(RFC-0003, draft).

Safety comes entirely from **ownership transfer**: sending an owned `@Heap T` (or any
`T: Send`) into a channel strips access from the sender and grants it to the receiver. No
shared mutable state crosses fiber boundaries. This is the ordinary sendability rule
(RFC-0063 §4/§5) doing the work — the same rule that governs every other boundary in the
language, not a bespoke concurrency mechanism.

```
Fiber boundary:   @Heap T → Chan<T> → @Heap T
                  ownership transferred; sender loses access
```

**What there is no longer a second level for.** Prior drafts had an *intra-fiber* level
where `||` split work across threads over provably-disjoint parts of the *same*
allocation. That level is removed with `||`. A fiber is sequential; parallelism is across
fibers, via `spawn`, paid for with ownership transfer (and therefore `Send`, and
therefore — for scoped-allocator data — a copy into `@Heap` first). The cost of this is
honest and worth stating: **arena-allocated data has no in-place parallel story** now that
`||` is gone; parallelizing over it means moving it to the heap. See §5 for the deferred
mechanism that would restore the in-place case if it is ever wanted.

---

## 2. Fibers and channels: ownership transfer

`spawn { }` captures variables from the enclosing scope. For the spawn to be safe,
captured variables must satisfy one of:

| Captured type | Semantics | Parent access after spawn |
|---|---|---|
| `@Heap T` (owned, `T: Send`) | Moved into fiber | Lost — parent cannot use it |
| `T: Copy` | Copied into fiber | Retained (immutable copy in fiber) |
| `Chan<T>` endpoint | Endpoint moved into fiber | Lost — each end owned by one fiber |

```metel
fun producer_consumer() {
    let (tx, rx): (SendChan<@Heap [i64]>, RecvChan<@Heap [i64]>) = Chan::new();

    let producer = spawn {
        let data: @Heap [i64] = @Heap [1, 2, 3, 4, 5, 6, 7, 8];
        tx <- data;         // data MOVED into channel — producer loses it
        // data[0]          // ERROR: data was sent
    };

    let consumer = spawn {
        let received: @Heap [i64] = <- rx;   // consumer acquires ownership
        let sum = received.iter().fold(0i64, |a, x| a + x);
        assert(sum == 36);
    };

    producer.join();
    consumer.join();
}
```

Channel endpoints are directional: `SendChan<T>` and `RecvChan<T>` are distinct types. A
`Chan<T>` where `T: Linear` (`linear-types.md` §2) directly satisfies the linear type's
exactly-once rule: the send is the single consumption, and the compiler confirms the value
was not used on the sending side afterward. Channels are the natural transport for linear
values, not a special case.

---

## 3. Carrying the structured guarantee — leading candidate: a `Linear` spawn handle

**Open question, not a decision (reopened 2026-07-07 as premature).** With `||` gone, the
"cannot silently abandon a fiber" guarantee needs a home. The candidates: (a) a `Linear`
`spawn` handle, sketched below; (b) a standalone `fork`/`JoinToken<'b>` as in RFC-0076;
(c) an affine `spawn` handle with no static guarantee at all (abandonment allowed). This
section develops (a) because it is the leading candidate — it reuses machinery that already
exists and needs no brand — but the choice is not settled.

Under candidate (a), `spawn` returns a **`JoinHandle<T>` that is `Linear`**
(`linear-types.md` §2). A linear handle can be discharged in exactly two ways, and reaching
scope end without discharging it is a compile error:

```metel
// Structured: wait for the fiber and collect its result.
let h = spawn { heavy_computation() };   // h: JoinHandle<i64>, Linear
do_other_work();
let result: i64 = h.join();              // consumes h; blocks until the fiber finishes

// Deliberate abandonment: the fiber runs free, detached from any join point.
let bg = spawn { background_loop() };
bg.detach();                             // explicit consumption; nothing left to join

// Forgetting both:
fun leak() {
    let h = spawn { work() };
    // <no join, no detach>
}   // ERROR: linear handle `h` is not consumed — join it or detach it explicitly
```

If adopted, candidate (a) would recover the whole of what `||` and `brand-types.md`'s
`JoinToken<'b>` gave, from a mechanism that already exists:

- **You cannot *silently* abandon a fiber.** The only way to end up with an
  un-joined fiber is to write `.detach()` — visible, deliberate, greppable. Accidental
  fiber leaks are a compile error, exactly as `JoinToken`'s linearity made them.
- **No separate `fork`/`JoinToken` primitive would be needed.** `JoinToken<'b>` is a linear,
  brand-tagged token whose only jobs are "prove this was joined" and "prove you joined
  the *right* fiber." The first would be the handle's linearity. The second is free: each
  `spawn` yields a distinct handle binding, so there is no way to confuse two — `h.join()`
  joins `h`'s fiber and no other. The brand `'b` that `JoinToken` needs for identity would be
  redundant once the handle is the value you hold. (This is the argument *for* candidate (a)
  over candidate (b) — the decision itself is still open.)
- **It would be a clean worked example of a two-discharge linear type.** `JoinHandle<T>`
  has a real teardown obligation with two named ways to satisfy it (`join` / `detach`) —
  structurally the same shape as a linear allocator with `.free()`, or a linear `FileCap`
  with `close()` (`linear-types.md` §5). The concurrency instance of the same lattice
  point, not a new concept.

Under candidate (a), detach is the deliberate escape hatch from structured concurrency;
its *explicitness* is the guarantee — you leave a fiber running, but never by accident.

**One small open point:** whether `JoinHandle<T>` should still carry a brand for any
reason (e.g. tying a handle to a scope so it cannot outlive it) is minor and unresolved —
see Open questions. The linearity, not a brand, is what carries the must-join property.

---

## 4. `select`

`select` is sequentially exclusive — at most one arm fires — so arms do not race with each
other and need no disjointness checking between them:

```metel
select {
    msg = <- ch_work => { process(msg); },   // msg: @Heap WorkItem
    _   = <- ch_done => { break; },
}
```

Any concern about what a fired arm does relative to concurrently running fibers is handled
by the ownership-transfer rule (§2), not by `select` itself.

---

## 5. Capture Separation Calculus — deferred, kept for the record

CSC (capture-set disjointness, `sep{}` annotations, `split_at_mut`) was the fine-grained
complement to `||`: it proved that two references into the *same* allocation touch
disjoint sub-ranges, so they could be used in parallel even though a shared allocator tag
could not witness their disjointness. **With `||` retracted, CSC has no consumer** —
nothing in the surviving model uses shared, in-place, disjoint parallel access. It is
recorded here, condensed, as the mechanism that would be revived if the deferred
capability in §1 (in-place data parallelism) is ever wanted.

The essential idea, for the record:

- A **capture set** is the set of root variables a reference transitively reaches,
  computed as a side-channel during inference (`&y → {y}`, `&y.field → cap(y)`, closures
  union their captures).
- **`split_at_mut`** consumes one `&var [T]` and produces two `&var [T]` halves with
  *distinct* root variables, so their write-capture sets are disjoint by construction.
- **`sep{}`** would let a caller pass a disjointness proof across a call boundary that the
  callee's body then trusts.

The only place this could return is a **liberalized `spawn`** (§6) that captures `&var T`
under a proven-disjoint capture set instead of requiring `Send`. That is the sole future
consumer; absent it, CSC is unmotivated, and building a general capture-set prover for a
feature nothing uses would be exactly the kind of speculative machinery the wider design
effort has flagged as needing to wait for real demand
(`../strategy/strategic-overview-2026-07-06.md`).

---

## 6. Liberalized `spawn` (also deferred) — the only future home for CSC

A more permissive `spawn` could capture `&var T` when the spawned fiber's write-capture
set is provably disjoint from the parent's at the spawn point:

```metel
fun update_partitions(part_a: &pa var [i64], part_b: &pb var [i64]) {
    let h = spawn { for (let x in part_b) { *x *= 2; } };  // captures &var part_b
    for (let x in part_a) { *x *= 2; }                     // parent uses &var part_a
    h.join();   // {part_a} ∩ {part_b} = ∅ throughout — safe
}
```

This is strictly beyond RFC-0003's current sendability-only capture rule (references are
never `Send`, §2), and it is the one feature that would justify building CSC (§5). It is
deferred together with CSC; neither is on any near-term path. Note that whatever mechanism
§3 settles on for the join guarantee, it is orthogonal to whether the capture is by-move or
by-disjoint-borrow.

---

## Summary table

| Mechanism | Disjointness / safety witness | Status |
|---|---|---|
| Fiber + `Chan<T>` (§2) | Ownership transfer / sendability | RFC-0003 draft — the model |
| Join guarantee (§3) | Linearity (leading candidate: `Linear` `JoinHandle`) vs. `fork`/`JoinToken` vs. affine handle | **Open — mechanism not decided** |
| `select` (§4) | N/A — mutual exclusion, not parallelism | RFC-0003 draft |
| CSC / `sep{}` (§5) | Capture-set disjointness | **Deferred — lost its consumer when `\|\|` was dropped** |
| Liberalized `spawn` (§6) | Capture-set disjointness at the spawn point | Deferred — the only future consumer of CSC |
| ~~`\|\|` (RFC-0064)~~ | ~~Allocator-tag disjointness~~ | **Retracted 2026-07-07** |

---

## Open questions

1. **Which mechanism carries the structured join guarantee (§3)?** The central open
   question now that `||` is gone: a `Linear` `spawn` handle (leading candidate), a
   standalone `fork`/`JoinToken<'b>`, or an affine handle with no static guarantee.
   Reopened 2026-07-07 as too early to decide. Sub-question if candidate (a) wins: should
   the handle carry a brand at all, or is linearity alone sufficient (probably sufficient).
2. **Is in-place data parallelism (§1's deferred capability) worth restoring later?** It is
   the one thing dropping `||` gave up. If real workloads want parallel map/reduce over
   arena data without heap round-trips, that is the signal to revive CSC (§5) + liberalized
   `spawn` (§6) — not before.
3. **Liberalized `spawn` capturing `&var T` under CSC (§6)** — a real capability increase
   over RFC-0003's sendability-only rule; deferred with CSC.
4. **`sep{}` surface syntax and inference cost** — untouched since the original
   exploration; only relevant if §5/§6 are ever revived.
5. **RFC-0003's own open questions** (channel buffering, `select` fairness, fiber
   scheduling) — independent of everything above.
