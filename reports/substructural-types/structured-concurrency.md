---
id: structured-concurrency
title: "Structured Concurrency: Capture Separation and Allocator-Tag Disjointness"
type: report
status: active
last_synced_against_model: '2026-07-06'
supersedes: null
revives: "reports/substructural-types/archive/substructural-and-separation-types.md sections 7-8"
---

# Structured Concurrency: Capture Separation and Allocator-Tag Disjointness

*Living document — updated in place, not a point-in-time snapshot.*

*Exploration, not a decision. Revived from `archive/substructural-and-separation-types.md`
§7–8 (the Capture Separation Calculus and its integration with Metel's planned
concurrency model), which that archive note already identifies as "the working draft
behind" this document. Syntax updated throughout: `*T`/`*mut T` → `&T`/`&mut T`
(RFC-0067), `own T` → `@a T` for a concrete allocator `a` — most often `@Heap T`
(the archived report's `own T` reads today as exactly `@Heap T`; see that archive's
header note). The archived report's `iso T` (§5, not revived in full here) turns out to
be largely subsumed by the already-accepted exclusive-`&mut T` borrow model — a live
reference to a larger allocation that is "the only one, temporarily shareable" is
already what `&mut T` gives you; the fractional-uniqueness framing is not needed to get
the mechanism. Linear capability tokens (archived §6) and typestate (archived §4) have
their own homes now: `linear-types.md` and `structural-records.md`/`brand-types.md`
respectively.*

The one thing this document adds beyond a syntax port: **a direct reconciliation between
the Capture Separation Calculus (CSC) and RFC-0064's allocator-tag disjointness
argument**, which the archived report and RFC-0064 each worked out independently, in
different vocabularies, without citing each other.

---

## 1. Two levels of parallelism, still the right split

Metel's planned concurrency model: lightweight fibers via `spawn { }`, M:N scheduled (no
async/await, no function coloring), typed channels `Chan<T>` as the primary
communication primitive (`ch <- val` send, `<- ch` receive), and a `select` expression
for multiplexing (RFC-0003, draft). The ownership and separation mechanisms below map
onto two distinct levels of parallelism in this model:

**Fiber-level (coarse).** Fibers communicate through channels. Safety comes from
ownership transfer: sending an owned `@Heap T` (or any `T: Send`) into a channel strips
access from the sender and grants it to the receiver. No shared mutable state crosses
fiber boundaries. CSC machinery does not activate at this level — it's the ordinary
sendability rule (RFC-0063 §4/§5) doing the work, same as everywhere else in this
cluster.

**Intra-fiber (fine).** Once a fiber owns its data, it may split work across threads
using `||` (RFC-0064). The two sides share access to the same allocation but have
provably disjoint write domains. This is where capture-set disjointness is checked —
and, per §5 below, only sometimes needed at all.

```
Fiber boundary:   @Heap T → Chan<T> → @Heap T
                  ownership transferred; sender loses access

Intra-fiber:      @a [T] → split_at_mut → two disjoint sub-slices of the same @a [T]
                  each half's write-capture set is a distinct root; safe for ||
```

---

## 2. Capture sets

A capture set is the set of *root variables* a reference transitively reaches. It is
computed alongside the type during inference, stored as a side channel rather than
embedded in the type representation.

**Inference rules** (updated to `&`/`&mut` syntax):

| Expression | Capture set |
|---|---|
| Struct literal `T { .. }` | `{}` — a root value, not a reference |
| `let x = T { .. }` | binds root variable `x`; `cap(x) = {x}` |
| `&y`, `&mut y` | `{y}` |
| `&y.field` | `cap(y)` — propagate through field access |
| Closure capturing `x, y` | `cap(x) ∪ cap(y)` |
| `f(a, b)` returning a reference | `cap(a) ∪ cap(b)` (conservative) |
| `(e₁, e₂)` | `cap(e₁) ∪ cap(e₂)` |

```metel
fun main() {
    let mut a = Counter { value: 0 };   // cap(a) = {a}
    let mut b = Counter { value: 0 };   // cap(b) = {b}

    let pa: &a mut Counter = &mut a;    // cap(pa) = {a}
    let pb: &b mut Counter = &mut b;    // cap(pb) = {b}

    // cap(pa) ∩ cap(pb) = {a} ∩ {b} = ∅ — disjoint, safe for parallel use
}
```

**`||` — parallel composition (RFC-0064).** `e₁ || e₂` runs both expressions
concurrently; the checker verifies their write-accessible capture sets are disjoint:

```
write_cap(e₁) ∩ write_cap(e₂) = ∅   — no write–write race
write_cap(e₁) ∩ read_cap(e₂)  = ∅   — no write–read race
write_cap(e₂) ∩ read_cap(e₁)  = ∅   — no read–write race
```

Reader ∥ reader is unconditionally safe. The existing `&T` vs. `&mut T` distinction
directly encodes the reader/writer split — no new types needed:

```metel
fun main() {
    let mut a = Counter { value: 0 };
    let mut b = Counter { value: 0 };

    a.inc() || b.inc();          // cap {a} vs {b} — disjoint: OK
    let _ = a.get() || a.get();  // reader || reader — always OK

    // a.inc() || a.get();       // ERROR: write_cap({a}) ∩ read_cap({a}) ≠ ∅
    // a.inc() || a.inc();       // ERROR: write_cap({a}) ∩ write_cap({a}) ≠ ∅
}
```

**`sep{}` — proof propagation through call boundaries.** When `||` is *inside* a
function body, the checker cannot derive capture-set disjointness from call-site
arguments without inspecting the function's internals. `sep{}` is the mechanism by
which callers provide a proof at the call site and the function body trusts it:

```metel
fun parallel_inc(a: &a mut Counter, sep{a} b: &b mut Counter) {
    a.inc() || b.inc();   // safe inside: sep{a} is the axiom
}

fun main() {
    let mut x = Counter { value: 0 };
    let mut y = Counter { value: 0 };

    parallel_inc(&mut x, &mut y);    // cap = {x} vs {y} — disjoint: OK
    // parallel_inc(&mut x, &mut x); // ERROR: cap = {x} on both — sep{a} violated
}
```

---

## 3. Fibers and channels: ownership transfer

`spawn { }` captures variables from the enclosing scope. For the spawn to be safe,
captured variables must satisfy one of:

| Captured type | Semantics | Parent access after spawn |
|---|---|---|
| `@Heap T` (owned) | Moved into fiber | Lost — parent cannot use it |
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
exactly-once rule: the send is the single consumption. A `Linear` capability token can be
sent through a channel and the compiler confirms it was not used on the sending side
afterward — channels are the natural transport for linear values, not a special case
that needs its own rule.

---

## 4. `||` within a fiber: fine-grained parallelism, and where RFC-0064 already wins for free

After acquiring `@a [i64]` from a channel, a fiber may want to process independent
halves concurrently:

```metel
fun parallel_sum(data: &data [i64]) -> i64 {
    let mid = data.len() / 2;
    // Both sides read via &[i64] — reader || reader is always safe, RFC-0064 §2
    let (left_sum, right_sum) = sum_slice(data, 0, mid) || sum_slice(data, mid, data.len());
    left_sum + right_sum
}
```

For mutation, both sides must touch provably disjoint subsets. `split_at_mut` consumes
a `&mut [T]` and produces two `&mut [T]` halves with *distinct* root variables in the
capture environment:

```metel
fun parallel_transform(data: @a [i64]) -> @a [i64] {
    let mid = data.len() / 2;

    // split_at_mut divides one &mut [i64] into two, cap(left) = {left}, cap(right) = {right}
    let (left, right) = data.split_at_mut(mid);

    // write_cap(left side) = {left}, write_cap(right side) = {right} — disjoint: CSC passes
    transform_half(left) || transform_half(right);

    data
}
```

This is exactly the case RFC-0064 was **not** written to cover — and that distinction
is the whole point of §5.

---

## 5. Reconciling CSC with RFC-0064: two disjointness witnesses, not one

RFC-0064 and this document's CSC material were written independently and never cite
each other, but they solve overlapping-looking problems with a genuinely different
argument each. Naming the difference precisely:

**RFC-0064's argument works at the *allocator* granularity.** Two pointers `@r1 T` and
`@r2 T` tagged with distinct allocators cannot alias, because distinct scoped allocators
are distinct arenas by construction — "the tag *is* the proof" (RFC-0064 §2/§3). No
capture-set tracking is needed: the type of each branch already carries the answer, the
same way §1 above already relies on for fiber sendability. This is sufficient for the
common case in RFC-0064's own motivating example — `sum(&t.left) || sum(&t.right)`,
two *separately allocated* sub-trees.

**CSC's argument works at the *sub-allocation* granularity.** `split_at_mut` in §4 above
produces two halves that are **still tagged with the same allocator** `a` — RFC-0064's
witness says nothing here, because both `left` and `right` are `@a [i64]`, same tag.
What makes them safe to use in parallel is not that they come from different arenas; it's
that the *capture-set side-channel* tracks them as two distinct root variables with
non-overlapping index ranges, a fact the allocator tag alone cannot express. This is
precisely the gap RFC-0064 §5 item 3 leaves open ("`||` on non-region data... the general
case has no new safety obligations" — which is true only because that RFC never
attempts the same-allocator-split case at all).

**The two compose, they don't compete:** allocator tags settle disjointness whenever two
values happen to come from different allocators (the coarse, free case); capture sets are
needed only when two values share an allocator and disjointness instead has to be proven
about which *addresses within it* each side touches (the fine case, needed for any
splitting operation — arrays, but potentially also arena sub-regions, tree rebalancing,
etc.).

**The value-over-novelty question this raises, unresolved:** is a *general* CSC
worth building — full capture-set inference plus `sep{}` annotations, usable on
arbitrary references — or does Metel only actually need a narrow, closed-world version of
this fact wired into a small number of stdlib primitives (`split_at_mut` and similar),
the way Rust gets the equivalent guarantee from `split_at_mut`'s implementation being
`unsafe`-and-trusted rather than from a general prover? A full CSC is more expressive (it
would let *user code*, not just stdlib primitives, split and recombine disjoint views);
a narrow stdlib-primitive version is far cheaper to build and verify, and covers what
RFC-0064's own examples actually need. This document takes no position — it is exactly
the kind of "novelty vs. value" question the wider design effort has flagged as needing
deliberate judgment before being pursued (see `../strategy/strategic-overview-2026-07-06.md`).

---

## 6. `spawn` with CSC disjointness — a more liberal alternative

A more liberal alternative to the ownership-only capture rule (§3): `spawn` may capture
`&mut T` references, provided the spawned fiber's write-capture set is provably disjoint
from the parent's write-capture set at the spawn point.

```metel
fun update_partitions(part_a: &pa mut [i64], part_b: &pb mut [i64]) {
    // Fiber's write-capture: {part_b}; parent's write-capture after spawn: {part_a}
    // {part_a} ∩ {part_b} = ∅ — safe
    let fiber = spawn {
        for (let x in part_b) { *x *= 2; }
    };

    for (let x in part_a) { *x *= 2; }

    fiber.join();   // synchronization point; both capture sets merge
}
```

This is a strictly stronger claim than RFC-0064 §4 currently makes: RFC-0064 says
`spawn` requires sendability, which rules out capturing any reference at all (references
are never sendable, §1). A CSC-liberalized `spawn` would let a spawned fiber capture a
`&mut T` when disjointness is provable — a real capability increase, not free, and not
addressed by RFC-0064 as currently drafted. Whether this liberalization is worth pursuing
is bound up with the same value-over-novelty question as §5: it requires exactly the
general capture-set machinery whose cost/benefit is undecided there.

---

## 7. `select`

`select` is sequentially exclusive — at most one arm fires — so arms do not race with
each other and require no CSC checking between them:

```metel
select {
    msg = <- ch_work => { process(msg); },   // msg: @Heap WorkItem
    _   = <- ch_done => { break; },
}
```

Any concern about what a fired arm does relative to concurrently running fibers is
handled by the fiber-level ownership rule (§3) or the spawn-point disjointness check
(§6), not by `select` itself.

---

## 8. `JoinToken<'b>` and `||`: two different structured-concurrency stories

`brand-types.md` §Applications describes `JoinToken<'b, T>` — a `Linear`, brand-tagged
token returned by `fork`, consumed by `join`, whose linearity makes fiber abandonment a
compile error. RFC-0064's `||` gets the same "cannot be abandoned" guarantee a different
way: `||` has no separate fork step at all — both branches are lexically inside the
combinator, so there is nothing to abandon; the join is not a value the programmer
consumes, it's syntactically the only way `||` returns.

These are not the same mechanism wearing different syntax — they cover different
shapes of problem:

- **`||` (RFC-0064)** — both branches known statically, both always joined at one
  lexical point, no possibility of a detached fiber outliving the expression. No token
  needed because there is no state in which one could forget to join.
- **`fork`/`JoinToken<'b>` (`brand-types.md`)** — the fork and its join may be
  lexically separated (do other work between them, store the token, pass it to another
  function), which is exactly what makes a token necessary: the type system has nothing
  else to check "was this ever joined" against once the fork isn't immediately followed
  by its join.

**Open question, not resolved by either source document:** does Metel need both, or
does one subsume the other for the language's actual needs? `||` is simpler and
sufficient for the "process this data in two halves" shape that motivates RFC-0064's own
examples and §4 above. `fork`/`JoinToken` is needed only if genuinely detached-but-
tracked fibers (fire off work now, collect it after unrelated work later) turn out to be
a pattern worth supporting as a first-class primitive rather than being expressed via
`spawn` + `Chan<T>` (§3), which already covers "detached, ownership transferred through a
channel" without needing a brand or a token at all. Nothing here argues for adding
`fork`/`join` — it's flagged as a real design fork, not a settled direction.

---

## Summary table

| Mechanism | Disjointness witness | Granularity | Status |
|---|---|---|---|
| Fiber + `Chan<T>` (§3) | Ownership transfer / sendability | Coarse — whole values crossing fiber boundaries | RFC-0003 draft |
| `\|\|` on separately-allocated data (§4, RFC-0064) | Allocator tag — distinct tags ⇒ distinct arenas | Coarse — different allocations | RFC-0064 deferred |
| `\|\|` on split same-allocation data (§4–5) | Capture-set disjointness (CSC) | Fine — sub-ranges of one allocation | Not in any RFC; open per §5 |
| `sep{}` (§2, §6) | Caller-provided proof, trusted in the callee body | Fine, across call boundaries | Not in any RFC |
| Liberalized `spawn` (§6) | Capture-set disjointness at the spawn point | Coarse-looking, fine-grained proof | Not in any RFC; strictly beyond RFC-0064 §4 |
| `select` (§7) | N/A — mutual exclusion, not parallelism | — | RFC-0003 draft |
| `fork`/`JoinToken<'b>` (§8, `brand-types.md`) | Linearity + brand identity | Coarse — detached, individually tracked fibers | Contingent on RFC-0064 per that RFC's own text |

---

## Open questions

1. **General CSC vs. narrow stdlib-primitive disjointness (§5)** — the central open
   question this document exists to state. Not resolved either direction.
2. **Liberalized `spawn` capturing `&mut T` under CSC (§6)** — a real capability increase
   over RFC-0064 §4's current sendability-only rule; contingent on §1's resolution.
3. **`\|\|` vs. `fork`/`JoinToken<'b>` (§8)** — whether both belong, or whether `fork`
   should be dropped in favor of `spawn` + `Chan<T>` for anything `\|\|` itself doesn't
   cover. Not resolved by either source document.
4. **RFC-0064's own unresolved questions** — nesting (`\|\|` inside `\|\|`, runtime
   scheduling left to the implementation), cross-branch error/panic handling, and `\|\|`
   on non-allocator data (§5's own general case) — all still open in that RFC, unrelated
   to CSC specifically.
5. **`sep{}` surface syntax and inference cost** — sketched here in the same shape as
   the archived report; whether it's the right surface form, or whether disjointness
   should instead be inferred structurally more often (reducing annotation burden), is
   untouched since the original exploration.
