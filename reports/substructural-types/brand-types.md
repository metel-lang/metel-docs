---
id: brand-types
title: "Brand Types"
type: report
status: active
last_synced_against_model: '2026-07-06'
supersedes: null
---

# Brand Types

*Living document — updated in place, not a point-in-time snapshot.*

*Exploration, not a decision. This document is design-notes commentary on
`internal/rfcs/0-draft/rfc-0076-rc-brands.md`, which remains the source of record for
the mechanism itself — read that RFC first. What follows is synthesis: how brands
connect to `linear-types.md` and `structural-records.md`, and where this cluster still
has an open fork rather than a settled answer.*

---

## 1. What brands add beyond typestate

Plain phantom-parameter typestate (`File<State>`, `Open`/`Closed`) answers "what state
is this object in." It does not answer "which object is this" — two open files are both
`File<Open>`, interchangeable as far as the type system is concerned. RFC-0076's brand
parameter (`File<brand 'b, State>`) answers the second question by giving each
introduction site a type-level identity that survives state transitions: `File<'b,
Open>` → `File<'b, Closed>` is provably the *same* file, and `File<'f1, Open>` vs.
`File<'f2, Open>` are provably *different* files even in the same state. Identity and
state are orthogonal axes, and RFC-0076 §Applications' summary table is the right
mental model: typestate tracks *what*, brands track *which*, token-gated access adds
*exclusive*.

## 2. Token-gated access is where this cluster actually meets `linear-types.md`

RFC-0076's token-gated-access pattern (`Token<'b>` + branded cells + `&mut Token<'b>`
as the access key) is described in the RFC as "a non-`Copy`, non-`Clone` struct." That's
correct but under-specified relative to `linear-types.md`'s multiplicity lattice —
non-`Copy`-and-non-`Clone` is exactly the *affine* point on that lattice, not
necessarily the *linear* one, and the three worked instantiations in RFC-0076 actually
want different points:

- **`JoinToken<'b, T>` must be `Linear`, not merely affine.** RFC-0076 says as much
  directly: "the token is linear — it cannot be dropped without joining." Silently
  dropping a `JoinToken` abandons the fiber; there is a real teardown obligation, which
  is exactly `linear-types.md` §2's criterion for requiring the `Linear` aspect rather
  than accepting the affine default.
- **`RcToken<'b>` and `HandlerToken<'b, E>` only need to be affine.** Dropping either
  one has no cleanup obligation attached — it just means no future `&mut token` can be
  produced, so the branded cells become permanently read-only (via `Rc` sharing) or the
  handler becomes permanently non-reentrant-lockable. Nothing leaks. Affine (droppable,
  non-duplicable) is the correct — and cheaper — commitment; reaching for `Linear` here
  would be over-constraining the design for no safety benefit.

This is a real, previously-unstated distinction: **not every token in the token-gated-
access family belongs at the same point on the lattice**, and RFC-0076's uniform "non-
Copy, non-Clone" phrasing should be read as "affine at minimum, linear where an actual
teardown obligation exists" rather than as one undifferentiated rule. If `linear-types.md`
§2's `Linear` aspect is adopted as designed, the natural update to RFC-0076 is to state
`JoinToken<'b, T>: Linear` and `RcToken<'b>`/`HandlerToken<'b, E>: !Linear` (affine)
explicitly, rather than leaving both under the same "non-Copy, non-Clone" description.

## 3. Two typestate encodings, not one — the fork this document exists to name

`structural-records.md` §5 works out typestate via **row-conditional impls**: the state
*is* the record's row, and methods are gated by `HasField`/`Lacks` conditions on that
row. RFC-0076 works out typestate via a **phantom brand/state type parameter**:
`File<brand 'b, State>`. Both solve the same problem — make illegal state transitions a
missing-method compile error — and neither document was written with the other in mind
as an alternative to reconcile against, only to connect to.

Comparing them directly, rather than leaving that undone:

| | Brand + phantom state param | Row-conditional impl |
|---|---|---|
| What tracks *state* | A type parameter (`Open`, `Closed`) | The row's field membership |
| What tracks *identity* | The brand parameter, separately | Not addressed — records have no identity story at all (`structural-records.md` §6: records can't be allocators, precisely because they lack per-instance identity) |
| Precedent | Conventional; the standard Rust-community typestate idiom | Novel; no mainstream language ships this for typestate specifically |
| Mechanism reused | Generics + RFC-0072 negative bounds | RFC-0036 conditional impls, generalized to row shape |
| Composes with token-gated access | Directly — same brand on `Mutex<'b, T>` and `MutexGuard<'b, T>` | Not naturally — rows have no brand-like identity primitive of their own |

**The asymmetry that matters:** brands can express identity *and* state together
(`File<'b, Open>`); row-conditional impls can only express state. A protocol session
that needs "this specific connection, currently in the authenticated state" — not just
"a connection, in the authenticated state" — needs a brand regardless of whether the
state tracking itself uses a row or a phantom parameter. That suggests these are not
actually competing solutions to the same problem, but a partial overlap: **for state
tracking alone, either works; for state-plus-identity, brands are not optional.** A
brand-parameterized record — `record { ..R }` with an added `brand 'b` — is not
discussed in either source document and is the natural next question if row-conditional
typestate is pursued seriously. Left open in §6 below rather than resolved here.

## 4. Why regions don't need this, and allocators barely do

RFC-0076 §Motivation already makes the relevant argument precisely: a `BumpRegion`
handle is simultaneously the runtime allocator, the lifetime tag, and the identity
token, because its freshness per scope *is* the brand. Nothing here changes that
argument or reopens it — it's additional confirmation, from the brand-types side, of
the same conclusion `../memory-model/lifetimes-vs-regions-2026-07-02.md` reaches from
the allocator side: allocator identity (RFC-0063's disjointness story) and brand
identity are the same underlying mechanism wearing two names, and region handles
already get it for free. `Rc`/`Arc` need brands explicitly only because, unlike
regions, they have no runtime handle to press into double duty.

## 5. Effects — pointer forward, not a claim

RFC-0076 §Applications/Algebraic effects sketches `HandlerToken<'b, E>` for handler-
state exclusivity and brand-tagged `handle<Fail<'h>>` blocks for O(1) type-directed
dispatch, both cited against the (pre-split-syntax) `algebraic-effects-and-memory-
model.md` report. That report has not yet been revived into this directory
(`algebraic-effects.md`, pending) — anything said here about how brands and effect
handlers actually compose would be restating RFC-0076's own sketch rather than adding
to it. Deferred to `algebraic-effects.md` once written, at which point this section
should be revisited and connected properly rather than left as a pointer.

## 6. Open questions

Carried forward from RFC-0076 §Unresolved questions (restated, not re-litigated — the
RFC is the source of record for these):

1. Brand introduction mechanism — `brand` block / `forall<brand 'b>` rank-2
   polymorphism vs. a simpler per-binding-fresh rule. Deferred in the RFC.
2. Brand kind vs. lifetime kind — shared syntactic kind, or `brand 'b` distinguished
   from `'r`. Deferred in the RFC.
3. Brand inference at function boundaries (existential vs. propagating), especially
   for recursive functions and trait objects. Deferred in the RFC.
4. `RcToken`/`Arc` across fiber boundaries — needs a `SharedToken<'b>` with lock-like
   semantics, or `Arc` stays runtime-only (`get_mut`) and opts out of token-gated
   access entirely. Deferred to RFC-0064's cluster.
5. Brand equality across module boundaries when a brand's origin is opaque to the
   caller. Deferred in the RFC.

New, raised by this document specifically:

6. Should RFC-0076 be amended to state token multiplicities explicitly (§2) — `Linear`
   for `JoinToken`, affine for `RcToken`/`HandlerToken` — once `linear-types.md`'s
   `Linear` aspect design is itself further along? Not urgent (no deadline forces it —
   contrast RFC-0063 §9 item 5), but worth tracking so the two documents don't drift.
7. Is a brand-parameterized record (`record { ..R }` plus `brand 'b`) worth designing,
   to give row-conditional typestate (`structural-records.md` §5) the identity
   dimension it currently lacks (§3 above)? No proposal exists yet either way.
8. Do brands and row-conditional impls end up as two permanent, independently-useful
   mechanisms for typestate, or should the language eventually recommend one over the
   other? §3's comparison suggests "both, for different needs" rather than "pick one,"
   but that has not been stated anywhere as a decision, only as an observation.

## Example program

Illustrative only — brand-indexed state machine plus a `Linear`-per-§2 join token,
composed in one sketch.

```metel
struct File<brand 'b, State> { fd: i64 }
struct Open {}
struct Closed {}

fun open<brand 'b>(path: String) -> File<'b, Open> { ... }
fun read<brand 'b>(f: &File<'b, Open>) -> String { ... }
fun close<brand 'b>(f: File<'b, Open>) -> File<'b, Closed> { ... }

// Structured concurrency: JoinToken is Linear (§2) — dropping it without
// joining is a compile error, not just a lint.
linear struct JoinToken<brand 'b, T> { }

fun fork<brand 'b, T>(f: fun() -> T) -> JoinToken<'b, T> { ... }
fun join<brand 'b, T>(token: JoinToken<'b, T>) -> T { ... }

fun main() -> i64 {
    let f = open("/tmp/log.txt");        // File<'f, Open>
    let token = fork(|| read(&f));       // JoinToken<'t, String>
    let closed = close(f);               // File<'f, Closed> — same file, new state
    let contents = join(token);          // must join; token is Linear, can't be dropped
    println(contents);
    0
}
```
