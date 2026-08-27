---
id: rfc-0145
title: "Static Storage Duration"
date: '2026-08-27'
status: draft
---

> **Written 2026-08-27**, prompted by issue #840 ("static/constant/comptime values
> and generics") turning out to be fully covered by RFC-0092/RFC-0132's existing
> comptime work *except* for one real gap: everything in that cluster is `const` —
> compile-time-evaluated, no guaranteed address, never mutable. Nothing in Metel
> today answers `static` — a single, program-lifetime, addressable *place*, distinct
> from a compile-time-substituted *value*. This RFC is that gap, proposed on its own
> rather than folded into RFC-0132, since it's a genuinely separate capability RFC-
> 0132 was never scoped to cover.
>
> **Written against RFC-0143 (`1-under-review`), not the currently-accepted allocator
> cluster it proposes to replace.** RFC-0143 already has the exact primitive this
> RFC needs — `Heap` as a "static allocator... with a stable global identity" — more
> precisely than the accepted-but-unimplemented RFC-0063/RFC-0141 cluster does. This
> is a deliberate choice, not an oversight: it means this RFC depends on an
> unaccepted document that itself proposes superseding what's currently accepted,
> including RFC-0141. See §6 for the risk this creates and why it was chosen anyway.

## Summary

`static X: T = expr;` — a single binding with one real, stable address for the whole
process, distinct from `comptime let`'s value-substitution model in every load-
bearing way: it has an identity (`&X` is always the same pointer), it may have a
*runtime* initializer evaluated exactly once (unlike `comptime let`, which forbids
I/O entirely), and — through an interior-mutability wrapper, never a bare mutable
form — it may hold state that changes over the program's lifetime. Reuses `Heap`'s
already-designed process-scoped storage identity (RFC-0143 §2.1, §10) for the
immutable case; the mutable case needs the same interior-mutability answer this
corpus has already worked out for shared aliased mutation generally
(`RcToken<'b>`, contingent on RFC-0076).

---

## Motivation

### `const` vs `static`, precisely

Four independent properties, not one distinction — this RFC only needs the first two:

| | `const` (`comptime let`, RFC-0132 §1/§2) | `static` (this RFC) |
|---|---|---|
| Identity | No guaranteed address — a use site may get a substituted copy | Exactly one address for the whole process |
| Mutability | Never — nothing to mutate once every use is a copy | Can be, through interior mutability |
| Initializer | Must be comptime-evaluable, no exceptions | May be an ordinary runtime expression, evaluated once |
| Storage | May occupy no runtime memory at all | Always occupies a fixed location for the process's lifetime |

### Two capabilities `comptime let` cannot provide, structurally, not just by omission

1. **A runtime-computed one-time value.** `comptime fun` explicitly forbids I/O
   (RFC-0132 §4) — a value derived from `env::get()`, a syscall, or file contents
   cannot be a `comptime let` initializer under any circumstance, not just today's
   implementation. `static`'s initializer has no such restriction (§3).
2. **Persistent, safely shared state across the whole program.** No mechanism
   exists for this at all today — not even an unsafe one. A global counter, a
   registry, a cache: every one of these needs a single, addressable, potentially-
   mutating place, which `comptime let`'s substituted-value model cannot express by
   construction, independent of implementation effort.

---

## 1. Syntax and declaration positions

Mirrors `comptime let`'s own positions exactly (RFC-0132 §1/§2), for the same reason
`pub` already composes uniformly across declaration kinds — no new visibility rule:

```metel
static REQUEST_COUNT: i64 = 0;           // module-private, immutable, see §4 for
                                           // why this alone doesn't permit mutation
pub static VERSION: String = read_version_file();   // exported, runtime-initialized
```

`import`/`export` work exactly as for any other `pub` item. Ordinary (non-`static`,
non-`comptime`) module-level `let`/`var` is untouched, exactly as RFC-0132 §2 already
states for its own scope.

---

## 2. Storage identity: reusing `Heap`, not inventing a new region kind

RFC-0143 §2.1 already establishes what this RFC needs directly: *"Static allocators
such as `Heap` and `LocalHeap` have stable global identities named by those
bindings. They do not create fresh identities at each use."* §10's table gives
`Heap` **process** scope, unique affine handles, sendable when `T: Send`.

**`static X: T = expr;` desugars to placing `expr` in `Heap` once, under a single
implicit owner that is never moved, with `X` naming a `&T`/`&var T` borrow of it —
not a fresh `Heap` placement per use.** This needs no new storage-duration concept:
`Heap`'s existing process scope already means exactly "lives for the whole
program," and ordinary shared borrowing already means exactly "many call sites can
read the same place." A `static` is the degenerate case of RFC-0143's own model —
one placement, one implicit binding, never moved — not a fourth allocator family.

This is why the **immutable** case needs nothing beyond RFC-0143 itself: unique-
affine ownership doesn't prevent many simultaneous shared (`&`) borrows, only
simultaneous owners or exclusive (`&var`) borrows. A `static` never having a second
owner (nobody can move it — there is no binding to move it *from*, since the
`static` declaration itself is the one and only owner, implicitly, forever) is
exactly the shape unique-affine placement already handles correctly with zero new
rules.

---

## 3. Initializer timing — genuinely open, not decided

Two coherent choices, and this RFC does not pick one:

- **Eager** — every `static` initializer runs once, before `main`, in some order
  (declaration order within a module is the obvious default; cross-module order is
  the harder question — C++'s "static initialization order fiasco" is the standard
  cautionary tale for getting this wrong).
- **Lazy** — an initializer runs on first access, guarded so concurrent first-access
  from multiple fibers doesn't run it twice. Costs a per-access check (or relies on
  the placement being provably single-threaded before first use, which needs its
  own argument). Avoids the ordering question entirely, at the cost of the first
  access to any `static` being observably different from every later one.

Flagged as Open Question 1 rather than guessed at — this is exactly the kind of
comptime-adjacent design decision this project has already declined to rush once
(RFC-0132 §3's own "I don't want to rush the design of comptime" correction, §7
below).

---

## 4. Mutability: no bare `static var`, ever

A bare mutable static (`static var COUNTER: i64 = 0;`, Rust's old `static mut`
shape) is a data race the instant more than one part of the program touches it —
there is no lexical scope to hang an ownership or borrow discipline off of the way
there is for an ordinary local, and RFC-0071/RFC-0122's borrow checker has nothing
to check it against (every call site can reach the same place, by definition).
Rust's own answer was gating this behind `unsafe`. **Metel has no `unsafe` to gate
it behind** — RFC-0026 (Unsafe Blocks) is deferred, blocked on the refused
RFC-0028 — so that path isn't available even if wanted.

**Proposed instead: mutation only through an interior-mutability wrapper, reusing
`RcToken<'b>` rather than inventing a second mechanism.**
`reports/substructural-types/shared-ownership-survey-2026-06-29.md` already worked
out the general problem this is a special case of — *exclusive mutation of an
aliased value* — and landed on `RcToken<'b>`: a zero-size, affine (non-`Copy`) token
value where holding `&var RcToken<'b>` grants exclusive access to every cell
sharing that brand, "composable with RFC-0076 — brands already exist; `RcToken` is
a thin stdlib addition." A mutable `static` is exactly that problem at process
scope instead of local scope:

```metel
static COUNTER: RcCell<i64, 'counter> = RcCell::new(0);   // illustrative spelling,
                                                            // not proposed here

fun increment(token: &var RcToken<'counter>) {
    COUNTER.get_mut(token) += 1;   // exclusivity proven by holding the token,
                                     // not by any property of `static` itself
}
```

This RFC does **not** work out `RcCell`'s exact API, the token's exact acquisition
story, or whether `'counter`-shaped brands compose with `Heap`'s own storage
identity or need their own. That's real design work belonging to RFC-0076 and
whatever RFC formalizes `RcToken` as a real language feature (currently exploration-
report-only) — this section states the shape the answer takes, not the answer
itself. See Open Question 2.

**Why require the wrapper rather than also offering a raw/unsafe escape hatch
later:** Metel already has a working answer to safe shared mutation on the table
(`RcToken`) and does not have a working `unsafe` story. Offering both would mean
maintaining two ways to do the same thing where only one is actually buildable
today.

---

## 5. Relationship to RFC-0132 (`comptime let`)

Siblings, not overlapping, not one subsuming the other:

- `comptime let` is compile-time-evaluated, has no address, and never has a
  mutable form — a *value* substituted at each use.
- `static` is a real *place* — one address, may be runtime-initialized, may be
  mutable through §4's wrapper.
- Neither can express the other: `comptime let` cannot hold a runtime-computed
  value (§4 of RFC-0132 forbids I/O in `comptime fun`, the only path to a non-
  literal `comptime let` initializer); `static` gains nothing from compile-time
  evaluation specifically and does not need it — an eagerly-runtime-initialized
  `static` costs the same either way, since `Heap` placement itself is already a
  runtime operation.
- **Nothing about RFC-0132's own scope changes.** This RFC does not touch `comptime
  let`, `comptime fun`, `comptime if`, or §3's const-generics proposal.

---

## 6. Relationship to RFC-0143 — the dependency risk, named plainly

RFC-0143 is `0-draft`, proposes superseding RFC-0063/RFC-0065/RFC-0066/RFC-0068/
RFC-0073/RFC-0077/**RFC-0141**, and none of those RFCs change status while it stays
a draft. Writing this RFC against RFC-0143's model rather than the currently-
accepted cluster means:

- If RFC-0143 is accepted roughly as drafted, this RFC's §2 is already correctly
  grounded — no rework needed.
- If RFC-0143 is rejected or changes substantially, §2 needs rewriting against
  whatever model actually ships (either the original RFC-0063/RFC-0141 cluster, or
  a different consolidation).
- If RFC-0143 stalls indefinitely, this RFC's immutable case (§2) is blocked on it
  specifically, not on the broader allocator cluster generally — `Heap`'s process-
  scoped identity is the one piece this RFC needs, and every candidate consolidation
  discussed so far (the accepted cluster, RFC-0143) agrees `Heap` has that property
  under some spelling.

Chosen anyway because RFC-0143's vocabulary is precise enough to write §2 without
hand-waving, which the accepted-but-frozen cluster's own `@[r]` spelling doesn't
give as directly for a *stable, named, global* identity specifically (most of that
cluster's own worked examples are scoped/local allocators, not `Heap`'s global
case).

---

## Alternatives considered

- **Bare `static var`, Rust's original model.** Rejected — needs `unsafe`, which
  doesn't exist in Metel and isn't close to existing (RFC-0026 deferred, blocked on
  refused RFC-0028).
- **A `GlobalGc`-backed handle (RFC-0143 §10) instead of `Heap` for the immutable
  case.** Considered and rejected as unnecessary: `GlobalGc`'s traced-copyable
  handles solve *sharing without a single owner*, but an immutable `static` already
  has a single owner (the declaration itself) that's never moved — ordinary shared
  borrowing already covers every read access without needing tracing at all. Worth
  revisiting only if the mutable case (§4) turns out to need process-scoped tracing
  specifically, which `RcToken`'s own design (reference-counted, not traced) doesn't
  currently suggest.
- **No `static`, keep working around the gap.** Rejected as papering over a real,
  named capability gap rather than closing it — see Motivation.
- **Thread-local storage instead of a true process-global.** Different semantics
  (one instance per fiber/thread, not one instance total), genuinely useful for some
  cases this RFC's `static` doesn't cover, but a separate feature — not addressed
  here, flagged as Open Question 4.

---

## Open Questions

1. **Eager vs. lazy initializer timing (§3)** — not decided. Affects whether
   cross-module initialization order needs its own rule.
2. **The interior-mutability wrapper's exact shape (§4)** — this RFC states that
   mutation must go through something `RcToken`-shaped, not what that something's
   full API is. Real design work, contingent on RFC-0076 (Brand Types, `1-under-review`)
   and on `RcToken` graduating from exploration report to an actual RFC.
3. **Whether `static`'s storage identity needs its own named concept, or `Heap`'s
   is sufficient as stated in §2** — this RFC's working answer is "sufficient,"
   but that's this document's own first-draft position, not something anyone else
   has reviewed it against.
4. **Thread-local / per-fiber static storage** — genuinely useful, genuinely
   different semantics, not addressed by this RFC at all. A separate RFC's
   territory if wanted.
5. **Does a `static` ever run a destructor at process exit, or does its value
   simply persist until the OS reclaims the process** — Rust deliberately does not
   run `'static` destructors; C++ does, with the well-known static-destruction-
   order hazard as the cost. Not decided here.

---

## References

- RFC-0132 (Comptime Execution Model, `1-under-review`) — the sibling `const`
  mechanism this RFC is deliberately not overlapping with; §5 states the
  distinction precisely.
- RFC-0143 (Allocator Placement, Storage Identity, and Allocator-Selected Handles,
  `1-under-review`) — supplies `Heap`'s process-scoped storage identity §2 builds on
  directly; §6 states the dependency risk this creates.
- RFC-0063 / RFC-0141 (currently accepted, proposed for supersession by RFC-0143)
  — the allocator cluster this RFC deliberately did not write against; see §6.
- RFC-0076 (Brand Types, `1-under-review`) — `RcToken`'s own dependency, inherited by §4.
- `reports/substructural-types/shared-ownership-survey-2026-06-29.md` —
  `RcToken<'b>`, the interior-mutability precedent §4 reuses rather than inventing
  a second mechanism.
- RFC-0139 (Garbage-Collected Allocators, `1-under-review`) — considered and set aside for
  the immutable case (Alternatives Considered); may become relevant if the mutable
  case's design changes.
- RFC-0026 (Unsafe Blocks, deferred) — the alternative path for a raw mutable
  static, unavailable today.
- RFC-0071 (Ownership and Move Semantics, `3-integrated`) / RFC-0122 (Borrow
  Checking, `1-under-review`) — why a bare mutable static has nothing to check it
  against; the reasoning behind §4's restriction.

---

## Decision

**Outcome:** *(pending)*
**Target:** *(set when accepted — depends on RFC-0143 for §2 and RFC-0076 for §4;
not schedulable ahead of either)*
