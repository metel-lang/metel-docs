---
id: rfc-0140
title: "Algebraic Effects"
date: '2026-08-25'
status: under-review
target: v0.18.0
updated: '2026-08-25'
tracking: 'https://github.com/metel-lang/metel-core/issues/834'
---

> **Formalizes `reports/substructural-types/algebraic-effects.md`** (metel-docs-internal,
> `status: active`, last synced against the model 2026-07-23) — a living exploration
> report, not a point-in-time snapshot. That report's own header has carried, since
> 2026-08-13, a **pre-registered acceptance blocker**: whenever it is drafted into an RFC,
> Open Questions 4 and 7 below block `2-accepted`, stated explicitly rather than left at
> positions four and seven of a list, per `PROCESS.md`'s rule (adopted after RFC-0122's
> third `2-accepted` → `1-under-review` reversion) that an accepting review which checks
> only the list a document itself provides, and treats that list as complete, is exactly
> the mechanism behind those reversions. Carried forward into this RFC's own Open
> Questions section unchanged.

> **Status — under review (2026-08-25).** Design settlement scheduled: metel-core#834 opened, milestoned v0.18.0 (new milestone, created for this RFC). Formalizes an already-substantive, actively-maintained exploration report (algebraic-effects.md) with 15 sections and worked examples -- real engagement, not an option list.

## Summary

Algebraic effects: a computation declares what effects it may perform (`fun greet() ^
Console`); a surrounding `handle` block intercepts each effect operation, receives the
suspended computation as a first-class value (a *continuation*), and decides whether to
resume it, abort it, or resume it multiple times. Following Metel's existing "syntax
desugars to aspect calls" principle, an `effect` declaration desugars to an `aspect`, and
`handle` desugars to an impl of that aspect wired through the call stack as an implicit
bracket parameter — no new dispatch mechanism, reusing the one aspects already have.

The central finding: **most of the safety story for algebraic effects falls out of rules
this language already has**, applied to one new value type,
`@Heap Continuation<ResumeValue, FinalResult>`. One-shot resumption, abort-cleanup, and
sendability-gated async handlers are not special-cased effect features — they are ordinary
consequences of affine ownership (RFC-0071), `Drop` (RFC-0071), and allocator-tag-based
sendability (RFC-0063) applied to a continuation the way they would apply to any other
heap-allocated affine value. A small number of genuine tensions require attention (§4, §9,
§12.3), and several real open questions remain (below) — this is why the RFC is entering
review, not requesting acceptance.

---

## Motivation

Metel has no structured mechanism for effects today. `IO`, mutable state, and similar
capabilities are either ambient (ordinary function calls with no declared surface) or
threaded manually as explicit parameters. Neither gives a caller a way to see, from a
signature alone, what a function might do — and neither gives a test author a way to swap
what "printing" or "reading" means without a mocking framework or dependency-injection
wiring.

Algebraic effects solve this directly: `fun greet() ^ Console` declares the entire
effectful surface in the signature. Swapping the handler is the entire test strategy —
```metel
fun test_greet() {
    var output: String = "";
    handle greet() {
        Console::print(msg) => { output = output + msg; resume(()) }
        Console::read_line() => { resume("Alice") }
    }
    assert(output == "What is your name? Hello, Alice!");
}
```
No mock objects, no injected trait objects — the handler *is* the ordinary language
mechanism (an aspect impl) that would exist anyway.

This is prior art with a mature reference point (Koka; also OCaml 5, Unison) rather than a
novel proposal, and §10 below draws directly on Koka's design where Metel's situation
matches it, and explicitly declines to borrow where it does not (§10.6).

---

## Design

### 1. Effects desugar to aspects; `handle` desugars to an impl

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

Performing an effect desugars to calling the aspect method on the implicit handler value
in the bracket channel, passing the current continuation as the last argument. The bracket
channel and aspect dispatch already exist in the language; the only genuinely new runtime
piece is continuation capture (snapshotting a call frame), which the current tree-walking
evaluator does not support. **The type system is ready for this design; the implementation
work is entirely in the runtime.**

### 2. The continuation is an affine, `@Heap`-owned value

The "rest of the computation" after an effect-performance site is captured as
`@Heap Continuation<ResumeValue, FinalResult>`.

- **`@Heap`, not a scoped allocator**: the continuation must outlive the stack frame that
  created it; `Heap` is the only stdlib allocator with indefinite lifetime. It is freed
  individually when the handler is done with it.
- **Affine, not `Copy`**: `@Heap T` is non-`Copy` by construction (RFC-0063 §2, RFC-0071
  §2). Calling `resume` twice would require two owners of the same value, which affine
  move semantics reject at compile time. **One-shot resumption is not a rule added for
  effects — it falls out of the general ownership model applied to this one value type.**
- **Multi-shot continuations are not expressible** under this design, because
  `Continuation` would need `Clone`, and most captured state (structs, allocator-tagged
  pointers) is not `Clone`. A continuation over only `Copy`/`Clone` data could support
  `k.clone().resume(v)` explicitly; whether the language should add syntax for this is
  deliberately out of scope here (see Out of Scope).

### 3. Sendability is exact, not approximated, from existing allocator tags

A continuation captures every binding live at the effect site. Each captured value's
storage — allocator tag, or borrow anchor — determines whether the whole continuation may
cross a fiber boundary:

| Captured value type | Continuation sendable |
|---|---|
| `@Heap T` (`T: Send`), `Copy` values, primitives | yes, if nothing else prevents it |
| `@LocalHeap T` | no — thread-local |
| `@a T` (scoped allocator — `BumpAlloc`/`AutoAlloc`) | no — the allocator may be torn down before the fiber terminates |
| `&r T`, `&r var T` (any borrow, any anchor) | no — references are never sendable |

No separate marker is needed; the type of each captured value already carries the answer.
A handler receiving a non-sendable continuation is restricted to the current fiber
(synchronous `resume`, or storage in a same-fiber struct); attempting to send it through a
`Chan<T>` or into `spawn { }` is an ordinary compile error at the send/capture site, caught
by sendability rules that already exist and need no effect-specific extension. A handler
for a computation touching only `@Heap`/`Copy` data receives a sendable continuation —
storable in a channel, shippable to a worker fiber — **with no special annotation or
`unsafe` required.**

### 4. The `&r var T` tension — the one genuine new constraint

This is the most significant interaction, and it comes entirely from RFC-0067 (Lifetime
Anchors, `1-under-review`).

`&r var T` is exclusive, non-sendable, and non-escaping by construction (the borrow
checker guarantees no `&r var T` outlives its anchor `r`). If a computation holds an
active `&r var T` and performs an effect, the continuation captures it, and two things
follow immediately: (1) the continuation is non-sendable, ruling out async handlers, and
(2) the handler cannot touch the same location — the borrow is outstanding.

The second point is sound (no concurrent mutation of an exclusively-borrowed value while
suspended); the first is a real ergonomic cost: an async handler that stores the
continuation for later would leave the borrow hanging open indefinitely — the original
value cannot be moved, and nothing else can access it mutably until the continuation
resolves. **The concrete constraint**: performing an effect while holding an active
`&r var T` restricts the handler to synchronous resumption, and the borrow checker
enforces this by construction — a continuation cannot outlive `r` in any way that would
require async storage.

**The resolution proposed here is a refactoring discipline, not new syntax**: well-designed
handlers rarely need to suspend across an active `&var` borrow (an `IO` effect holds no
borrows; a `State` effect holds logical state, not raw memory borrows). The fix is
releasing the borrow before the effect site — a natural direction the borrow checker's own
compile error already points toward. Whether the language should additionally let an
effect declaration require "no active borrows at performance sites" explicitly —

```metel
effect IO ^ clean { ... }
```

— is Open Question 1: both the implicit (sendability-forces-synchronous) and the explicit
(`^ clean`) versions are equally sound; the question is purely discoverability.

### 5. Abort without resuming: `Drop` already handles it

A handler need not call `resume` — it may abort, returning a value without ever resuming
the suspended computation. The continuation then goes out of scope unconsumed. Since
`@Heap Continuation<V, R>` is an ordinary affine value, `Drop::drop` runs on it exactly as
it would on any other heap-allocated struct with a `Drop` impl, recursively dropping every
captured value in the suspended frame per RFC-0071's drop order (fields in declaration
order, then owned allocators). A suspended `FileHandle` open at the effect site, whose
handler aborted, gets `FileHandle::drop` called automatically — **no effect-specific
cleanup machinery is needed.**

### 6. Handler state via struct-owned allocators

A handler accumulating state during effect handling is a natural fit for a struct-owned
allocator (RFC-0068, `2-accepted`):

```metel
struct TraceHandler(@a: BumpAlloc) {
    entries: @a List<String>,
    count:   i64,
}
```

The owned allocator is implicitly in scope inside `impl TraceHandler`; allocating into it
requires `&var self` (the same exclusivity RFC-0063 §1 already requires); a returned
borrow anchored to `self` is valid for the struct's whole lifetime, per RFC-0067 §2's
`&self` anchor rule. Nothing here is new — it is RFC-0068's mechanism applied to a handler
struct like any other.

### 7. Nested handler allocators need no special sub-region typing

A handler struct's own allocator, itself allocated by an outer allocator, is ordinary
allocator composition — allocator identity and borrow-anchor validity are independent
concepts under the current split model, so no lifetime-outlives relationship needs
deriving between the two allocators. Any borrow taken from data inside the handler's own
arena is bounded by the handler's own lifetime as an ordinary value; escaping it past the
handler's scope requires `clone_into::<Heap>()`, the same escape hatch RFC-0066/RFC-0067
already provide elsewhere — not new, effects-specific machinery. (An earlier version of
this design depended on a `SubRegion`/`Outlives` mechanism to wire this automatically; both
were retracted before the allocator/lifetime split settled, and nothing effects-specific
was lost by their retraction — see the report's §7 for the full history.)

### 8. Interaction with structured concurrency

If an effect is performed inside a spawned fiber (`spawn` + `Chan<T>`, per
`structured-concurrency.md`), the continuation captures that fiber's stack, and whether it
may cross back out is governed by the same sendability rule as §3: scoped-allocator data
or a borrow in the frame makes the continuation non-sendable and confines its handler to
that fiber; a continuation over only `@Heap`/`Copy` data is sendable and may ship to a
worker. No effect-specific constraint is needed. The fiber itself should not be silently
abandonable mid-effect (the "must not escape the structured boundary" guarantee); *which*
mechanism carries that guarantee (a `Linear` `spawn` handle vs. a standalone
`JoinToken<'b>`) is an open concurrency question this RFC takes no position on — the
effects analysis here relies only on the guarantee existing, not on its packaging.

### 9. Linear capability tokens at effect boundaries

*(Depends on `linear-types.md`, itself not yet an RFC — see Out of Scope. This section is
the part of that interaction genuinely specific to effects.)*

- **A `Linear` value passed as an effect argument makes the handler its owner** — the
  handler must consume it even when aborting (not calling `resume`), enforced by the
  linearity checker exactly as any other unconsumed-linear-value error would be. This is
  *stricter* than the affine case (§5): an affine `@Heap` value just runs `Drop::drop`
  automatically on abort, which is correct for values where silent drop is fine and wrong
  for ones — uncommitted transactions, unsent acknowledgements — where it is not.
- **Typestate composes with effects with no friction.** An effect operation's return type
  is exactly what `resume` must supply, so a phantom-typestate or row-conditional protocol
  state flows through the effect boundary automatically — a handler arm that tries to
  `resume` with the wrong protocol state is an ordinary type error at the `resume` call
  site, not new machinery.
- **The one genuinely new requirement**: a `Linear` value left in scope at an effect site
  *without* being passed through the effect is unsound — if the handler aborts, the
  continuation's `Drop` would need to drop it, and `Linear` types have no `Drop` impl to
  fall back on by construction. This needs a new static check: at every effect-performance
  site, no unconsumed `Linear` value may remain in scope unless explicitly passed to the
  effect as an argument. Two resolutions: restructure so acquisition happens after the
  effect site, or thread the value through the effect explicitly so the handler receives
  and must dispose of it. **This check does not exist in `linear-types.md` either** — it
  is real, cross-cutting work belonging to both documents, not yet specified in full in
  either (Open Question 2).

### 10. Lessons from Koka, prioritized

Koka is the closest existing design point. Not everything transfers — Perceus and `st<h>`
effect elimination solve problems Metel's explicit allocator system does not have — but
several decisions are directly applicable, in priority order:

| Borrow | Cost | Value |
|---|---|---|
| `fun` vs `ctl` split in effect declarations | Low — declaration syntax only | High — eliminates continuation allocation for operations that always resume exactly once (state reads, config queries, logging) |
| `final ctl` for non-resuming operations | Low — declaration syntax + one compiler rule | High — zero-cost exceptions/early-return, the most common "effectful" operations in practice |
| Evidence passing (hidden per-call handler-pointer parameters, O(1) resumption) | Medium — implementation work | High — makes synchronous handlers competitive with hand-written state machines; **not in conflict with** boxing into `@Heap Continuation` — a practical implementation could use evidence passing for `fun`/`final ctl` and box only for genuinely cross-fiber or multi-shot cases |
| Explicit open/closed effect-row syntax (`{IO}` vs `{IO \| E}`) | Low — syntax clarification | Medium — clearer higher-order inference and documentation; Metel's `^` with a type variable already achieves the same result implicitly |

This RFC's current design treats every effect operation uniformly (every performance
allocates a `@Heap Continuation`) — sound, but needlessly expensive for the common case.
**Adopting the `fun`/`ctl`/`final ctl` split and evidence passing is flagged as the
highest-value revision before this RFC can reach `2-accepted`** (Open Question 4, a
pre-registered blocker — see this RFC's header).

### 11. The effect row is the type-level projection of the handler context

*(Connects RFC-0113 — Context Parameters, `1-under-review` — with the row/view machinery
from `access-and-presence-rows.md` and `nominal-types-as-branded-rows.md`, and §1's own
aspect desugaring. None of the source documents states this on its own; it follows from
reading them together.)*

§1 already establishes a handler as an ordinary value implementing the desugared effect
aspect. If several handlers are active simultaneously, "what's currently in the bracket
channel" is structurally a row of `(role, handler value)` bindings. RFC-0113 supplies the
labeling discipline directly — context parameters resolve by type, "ambiguity is always a
compile error," meaning at most one handler per aspect is in scope at once, which is
exactly what makes "the label is the type" well-defined for this row (a narrower
discipline than an ordinary structural row's arbitrary field names, not a different
mechanism).

Under that reading, `^{Trace, State<S>}` is the type-level projection of the row whose
value-level instantiation is the actual handler instances in scope. Propagating context to
a callee needing a subset (`f`'s `^{Trace, State<S>}` calling `g`'s `^{Trace}`) is ordinary
row-narrowing-and-passing, the same operation already specified for structs — project down
to the subset needed, pass that, with the same "exact match or an explicit narrowing step"
rule. It is specifically an access row (handlers are invoked by reference,
`self: &self Self`), not an owned/presence row — the reference to the handler travels
through the context row; handler state itself stays an ordinary owned value inside the
handler struct.

**Does not reopen the `Drop`-transitivity problem.** `Drop::drop` has no written signature,
so its required field set must be *inferred* from the body (a genuinely hard,
call-graph-level problem elsewhere in this cluster). Effect-performing functions do not
share this: `^{IO}` is *declared* on every function by construction, so checking a caller's
context row against a callee's declared effect row is ordinary row-subset type-checking,
not inference over a call graph.

This reframes how effect-row propagation *could* be checked (reuse of already-specified row
machinery) rather than proposing new syntax or a new checking algorithm. It does not touch
evidence-passing, continuation capture, or §9's linearity concerns. Whether it survives
contact with handler-nesting (two handlers of the same aspect wanting to both be in scope)
is Open Question 6.

### 12. String interpolation is an undeclared effect-performance site

RFC-0010 (String Interpolation, `4-implemented`, qualified 2026-08-12) rules `${...}`'s
grammar full-expression on purpose — including arbitrary calls. Combined with this design,
that means an interpolated expression may perform an effect:

```metel
fun greet_inline() ^ Console -> String {
    "Hello, ${Console::read_line()}!"
}
```

**Mechanically sound, not a soundness gap** — RFC-0010 lowers interpolation to an ordinary
expression tree before typechecking, so effect-row inference sees
`"Hello, " + Console::read_line().to_string() + "!"` as an ordinary nested call, no
special-casing needed. **The tension is discoverability, not correctness**: every other
effect-performance site in this design reads as a call; a `${...}` site reads as data, and
nothing marks it as a place a computation can suspend and hand control to a handler that
may resume it once, zero times, or from a different fiber. Whether this should stay legal
as-is, or require extracting an effectful sub-expression to a named binding first
(`let msg = Console::read_line(); "Hello, ${msg}!"`, making the suspension point an
ordinary statement again), is Open Question 7 — also a pre-registered `2-accepted` blocker.

`lexical.md`'s own current text (updated 2026-08-25, metel-core#704) already anticipates
this RFC directly: measured against the corpus, two narrower restrictions (comptime-only,
place-expressions-only) are already ruled out (0/80 and 13/80 interpolation sites would
break, respectively); an effect-axis restriction — `${...}` may not perform an effect — is
the only candidate that survives, and it is only expressible once this RFC's effect system
actually exists. Until Open Question 7 is settled, the full-expression status quo holds.

---

## What falls out for free vs. what is genuinely new

| Concern | Mechanism | Existing RFC |
|---|---|---|
| One-shot resumption | `@Heap Continuation` is affine — not `Copy`, cannot duplicate | RFC-0071 |
| Abort without resuming | `Continuation::drop` cascades to all captured values | RFC-0071 §3 |
| Scoped-allocator data in frame | Continuation inherits the scoped tag → not sendable | RFC-0063 §4/§5 |
| Cross-fiber async handlers | Legal only when all captured values are `@Heap`/`Copy` | RFC-0063 §4/§5 |
| Active `&r var T` borrow in frame | Non-sendable; original location inaccessible; synchronous only | RFC-0067 |
| Handler-local state allocation | `struct Handler(@a: BumpAlloc)` — arena freed with handler | RFC-0068 |
| Nested handler allocators | Ordinary allocator composition — no `SubRegion`/`Outlives` needed | — |
| Move-out on resume | Type-directed move-out / ascription — standard extraction form | RFC-0066 |
| `T: !Drop` in continuation internals | Scoped-allocator data in a continuation requires `T: !Drop` for safe bulk-free | RFC-0072 |

**Genuinely new**: the `effect`/`handle`/`resume` surface syntax; the runtime mechanism for
capturing a continuation (snapshotting a call frame — the current tree-walking evaluator
has nothing like this); the implicit-parameter wiring threading a handler through the call
graph to its effect site; and §9's linear-value-at-effect-site static check. Everything
else in this design is an existing rule applied to one new value type, not a new rule.

---

## Relationship to existing RFCs

- **RFC-0071 (Ownership and Move Semantics, `3-integrated`)** — supplies affine ownership,
  `Copy`/`Drop` exclusion, and drop ordering, which §2/§5 depend on directly. No changes
  requested to RFC-0071 itself.
- **RFC-0063 (Allocator Handles, `2-accepted`)** and **RFC-0065 (Allocator Ergonomics,
  `2-accepted`)** — supply the allocator-tag sendability rules §3/§8 apply unchanged, and
  the elision this RFC's examples assume.
- **RFC-0066 (Allocated-Value Extraction, `2-accepted`)** and **RFC-0067 (Lifetime
  Anchors, `1-under-review`)** — supply the move-out form §7 reuses and the `&r var T`
  borrow-checker guarantee §4 depends on entirely. §4 is a real ergonomic tension in
  RFC-0067's own design surfacing here, not a defect in either RFC.
- **RFC-0068 (Struct-Owned Allocators, `2-accepted`)** — the mechanism §6 applies to
  handler structs with no modification.
- **RFC-0072 (Negative Bounds, `4-implemented`)** — supplies `T: !Drop`, referenced in the
  summary table for scoped-allocator continuation internals.
- **RFC-0010 (String Interpolation, `4-implemented`)** — §12's entire finding depends on
  RFC-0010's own qualified-status ruling (2026-08-12) that `${...}` is full-expression by
  design. This RFC does not ask RFC-0010 to change; it names the consequence and defers
  the resolution to Open Question 7.
- **RFC-0113 (Context Parameters, `1-under-review`)** — §11's reading of the effect row as
  a row of borrowed handler references depends directly on RFC-0113's "ambiguity is always
  a compile error" resolution rule. Not a dependency in the blocking sense — this RFC does
  not require RFC-0113 to reach any particular stage first — but the two should stay
  reconciled; see Open Question 6.
- **RFC-0076 (RC Brands, `1-under-review`)** — sketches `HandlerToken<'b, E>` for handler-state
  exclusivity and O(1) brand-directed dispatch against an earlier form of this design; not
  yet reconciled with this RFC's own evidence-passing discussion (§10) in either direction
  — Open Question 3.
- **RFC-0091 (Linear Records, `0-draft`)** and `linear-types.md` (report, not yet an RFC)
  — §9 depends on the `Linear` multiplicity model these define; the linear-value-at-
  effect-site check (§9, Open Question 2) is real work belonging to both documents and is
  specified in neither yet.
- **RFC-0003 (Concurrency Model, `1-under-review`)** and `structured-concurrency.md` (report) —
  §8's fiber-boundary interaction depends on `spawn`/`Chan<T>` as specified there; this RFC
  takes no position on the open `JoinHandle`-vs-`JoinToken` question RFC-0003 itself
  carries.
- **RFC-0064 (Fork-Join Parallelism, `6-refused`)** — superseded by the `spawn`/`Chan<T>`
  model above; §8 (originally scoped against `||`) has been rescoped accordingly and cites
  nothing from RFC-0064.
- **RFC-0122 (Borrow Checking, `1-under-review`)** — supplies the borrow-checker machinery
  §4's `&r var T` non-escaping guarantee depends on being actually enforced.

---

## Out of Scope

- **Multi-shot continuation syntax** (§2) — `k.clone().resume(v)` is expressible today for
  `Clone`-eligible continuations with no new construct; dedicated sugar, if wanted, is a
  separate, smaller follow-on proposal.
- **The `Linear` type system itself** — `linear-types.md` is not yet an RFC; this RFC
  depends on it for §9 without attempting to specify it.
- **The `JoinHandle`/`JoinToken` structured-concurrency boundary mechanism** (§8) — an open
  question RFC-0003/`structured-concurrency.md` already carries; this RFC takes no
  position.
- **`HandlerToken<'b, E>`-style brand-directed dispatch** (Open Question 3) — sketched in
  RFC-0076 against an earlier form of this design, not reconciled here.
- **Evidence-passing as a committed implementation strategy** — flagged (§10) as the
  highest-value revision this design needs before `2-accepted`, but the actual
  continuation-capture runtime mechanism (call-frame snapshotting) is unbuilt regardless
  of which strategy is chosen, and is implementation work rather than a design question
  this RFC resolves.

---

## Open Questions

*Carried from `reports/substructural-types/algebraic-effects.md`'s own Open Questions
section, unchanged in substance. Items 4 and 7 are pre-registered `2-accepted` blockers
per that report's header (added 2026-08-13) — not ordinary open items that a future
review might reasonably decide don't block acceptance.*

1. **`^ clean` (or similar) as an explicit declaration-site annotation** forbidding active
   borrows at effect-performance sites, versus relying on the current implicit
   sendability-forces-synchronous constraint (§4). Both sound; discoverability unresolved.
2. **The linear-value-in-continuation static check (§9)** — needed for soundness once
   `Linear` exists, not yet specified precisely (what exactly counts as "in scope," how it
   interacts with partial consumption), and not yet cross-referenced from `linear-types.md`
   itself.
3. **`HandlerToken<'b, E>` (RFC-0076 §"Effect handlers")** for handler-state exclusivity
   and O(1) brand-directed dispatch — sketched against this design's evidence-passing
   discussion; not yet reconciled in either direction.
4. **[Pre-registered `2-accepted` blocker.] Koka's `fun`/`ctl`/`final ctl` split and
   evidence passing (§10)** — not adopted, not rejected. Flagged as the highest-value
   revision from prior art; this design currently treats every effect operation uniformly
   (every performance allocates a `@Heap Continuation`), which §10 argues is needlessly
   expensive for the common case.
5. **Sequencing against the rest of the substructural-types cluster** — a project-planning
   question, not a design one. This RFC's own transition to `1-under-review` and its
   tracking issue are the concrete answer for *this* RFC's own scheduling; how it relates
   to `linear-types.md`, RFC-0076, and RFC-0113's own remaining review is not addressed
   further here.
6. **Does §11's context-row-as-effect-row reading hold once more than one handler of the
   same aspect could plausibly want to be in scope** — nested `handle` blocks for the same
   effect, shadowing rather than erroring? RFC-0113's uniqueness rule is what makes the
   labeling discipline well-defined; whether real handler-nesting patterns need to violate
   it is unchecked. Also unchecked: whether row-narrowing (`nominal-types-as-branded-
   rows.md` §8.3's `.narrow()`) is the actual mechanism context-row propagation should use,
   or whether RFC-0113 already has its own independently-specified propagation rule this
   needs to reconcile with rather than assume matches.
7. **[Pre-registered `2-accepted` blocker.] Should an effect-performing call be allowed
   inside a string interpolation (§12)?** Not a soundness question — effect-row inference
   sees the lowered form regardless — but a discoverability one in the same family as Open
   Question 1. Two candidate restrictions (comptime-only, place-expressions-only) are
   already measured and ruled out against the current corpus (`lexical.md`, updated
   2026-08-25); an effect-axis restriction (`${...}` may not perform an effect) is the only
   one that survives, and is only expressible once this RFC's own effect system exists —
   so today's full-expression status quo holds by default regardless of which is
   ultimately preferred.

---

## References

- `reports/substructural-types/algebraic-effects.md` (metel-docs-internal, `status:
  active`) — the exploration this RFC formalizes; every section above traces to a numbered
  section there (§1–§15) or to its Open Questions
- `reports/substructural-types/lifetimes-vs-regions-2026-07-02.md` — the allocator/
  lifetime split this whole design is built against; §7's history (`SubRegion`/`Outlives`
  retraction) traces here
- `reports/substructural-types/structured-concurrency.md` — §8's `spawn`/`Chan<T>`
  interaction
- `reports/substructural-types/linear-types.md` — §9's `Linear` multiplicity model
- `reports/substructural-types/brand-types.md` §5 — the `HandlerToken<'b, E>` sketch
  Open Question 3 and RFC-0076 both carry
- `reports/substructural-types/access-and-presence-rows.md`,
  `reports/substructural-types/nominal-types-as-branded-rows.md` — §11's row machinery
- RFC-0071 (Ownership and Move Semantics, `3-integrated`) — affine ownership, `Drop`,
  drop ordering
- RFC-0063 (Allocator Handles, `2-accepted`), RFC-0065 (Allocator Ergonomics,
  `2-accepted`) — allocator-tag sendability
- RFC-0066 (Allocated-Value Extraction, `2-accepted`) — move-out form reused in §7
- RFC-0067 (Lifetime Anchors, `1-under-review`) — the `&r var T` guarantee §4 depends on
- RFC-0068 (Struct-Owned Allocators, `2-accepted`) — §6's handler-state mechanism
- RFC-0072 (Negative Bounds, `4-implemented`) — `T: !Drop`
- RFC-0010 (String Interpolation, `4-implemented`) — §12's undeclared-effect-site finding
- RFC-0113 (Context Parameters, `1-under-review`) — §11's labeling discipline
- RFC-0076 (RC Brands, `1-under-review`) — Open Question 3's `HandlerToken<'b, E>` sketch
- RFC-0091 (Linear Records, `0-draft`) — §9's dependency, alongside `linear-types.md`
- RFC-0003 (Concurrency Model, `1-under-review`) — §8's `spawn`/`Chan<T>` boundary
- RFC-0064 (Fork-Join Parallelism, `6-refused`) — superseded by the model RFC-0003 and
  `structured-concurrency.md` now specify; §8 no longer depends on it
- RFC-0122 (Borrow Checking, `1-under-review`) — enforces the `&r var T` non-escaping
  guarantee §4 relies on
- `rfcs/PROCESS.md` — the `2-accepted` pre-registered-blocker rule this RFC's header
  applies

---

## Decision

**Outcome:** *(pending)*
**Target:** *(set when accepted)*
