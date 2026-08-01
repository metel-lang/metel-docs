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

RFC-0076's token-gated-access pattern (`Token<'b>` + branded cells + `&var Token<'b>`
as the access key) is described in the RFC as "a non-`Copy`, non-`Clone` struct." That's
correct but under-specified relative to `linear-types.md`'s multiplicity lattice —
non-`Copy`-and-non-`Clone` is exactly the *affine* point on that lattice, not
necessarily the *linear* one, and the three worked instantiations in RFC-0076 actually
want different points:

- **`JoinToken<'b, T>` must be `Linear`, not merely affine.** RFC-0076 says as much
  directly: "the token is linear — it cannot be dropped without joining." Silently
  dropping a `JoinToken` abandons the fiber; there is a real teardown obligation, which
  is exactly `linear-types.md` §2's criterion for requiring the `Linear` aspect rather
  than accepting the affine default. (Whether this guarantee is carried by a standalone
  `JoinToken` or absorbed into a `Linear` `spawn` handle is an open concurrency question —
  `structured-concurrency.md` §3; the lattice point is the same either way.)
- **`RcToken<'b>` and `HandlerToken<'b, E>` only need to be affine.** Dropping either
  one has no cleanup obligation attached — it just means no future `&var token` can be
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

**Division of labor with `structural-records.md` §2 (added 2026-07-08):** `RcToken`
answers *who may share and mutate* — handle identity and multiplicity, the subject of
this document. It says nothing about how the shared allocation's own internal struct
(refcounts plus value) tears itself down, which is a separate, narrower question:
`value` outlives the box by *less* than the counters do (a weak handle keeps the
allocation alive without keeping the value alive), and mainstream implementations handle
that teardown ordering with `unsafe`/`ManuallyDrop` for lack of a safe alternative.
`structural-records.md` §2's declared-Drop-field-usage mechanism is a candidate for
expressing that ordering safely instead — a narrow point of contact with this document's
subject, not an overlap with it.

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
typestate is pursued seriously. Left open in §6 below rather than resolved here — it is
too early to pick a canonical typestate encoding.

**Considerations for whenever this is eventually decided** (recorded as inputs, not a
verdict): brand typestate reuses *only already-accepted machinery* (generics + RFC-0072
negative bounds, the table above), whereas row-conditional typestate requires the open
`<row R>` generics (`structural-records.md` §4 step 2 — row unification, a coherence
extension, the unprecedented width-subtyping rule of §8) that the build order defers; and
row-conditional cannot express state-plus-identity at all. Both push toward brands, but
neither is being treated as decisive yet.

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

This section's observation — allocator identity and brand identity are one mechanism
wearing two names — is generalized in `brand-kind-unification.md` into a claim about all
three identity kinds (`@a`, `&r`, `'c`) and a proposed answer to RFC-0076 Q2. This
document establishes the two-way case (regions/brands); that one takes it to three.

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
   from `'r`. Deferred in the RFC. **`brand-kind-unification.md` now takes a position on
   this specific question:** `@a`, `&r`, and `'c` are one kind under three sigil-selected
   roles — same kind, distinguished by sigil rather than being separate kinds. Read that
   document for the argument; this item is no longer open in a vacuum, though the RFC
   itself hasn't been amended.
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
   other? §3's comparison records the considerations (brand form is cheaper and covers
   state-plus-identity; row form is more novel and ties into the structural-records
   vision) but **it is too early to pick a canonical encoding — left open, not decided.**

## Example program

Illustrative only — a brand-indexed state machine (one of the two typestate encodings,
§3) plus a `spawn` handle standing in for whatever mechanism ends up carrying the
structured-concurrency guarantee (`structured-concurrency.md` §3, open).

```metel
struct File<brand 'b, State> { fd: i64 }
struct Open {}
struct Closed {}

fun open<brand 'b>(path: String) -> File<'b, Open> { ... }
fun read<brand 'b>(f: &File<'b, Open>) -> String { ... }
fun close<brand 'b>(f: File<'b, Open>) -> File<'b, Closed> { ... }

fun main() -> i64 {
    let f = open("/tmp/log.txt");        // File<'f, Open>
    let text = read(&f);                 // read into an owned String (borrow ends here)
    let closed = close(f);               // File<'f, Closed> — provably the same file, new state

    // Independent background work; the handle is Linear, so it can't be silently abandoned.
    let h = spawn { summarize(text) };   // owned `text` (Send) MOVED into the fiber
    let summary = h.join();              // must join (or detach) — the handle's linearity enforces it
    println(summary);
    0
}
```

Two separate mechanisms in one sketch: the brand `'b` does its **identity** job on `File`
(proving `File<'f, Open>` and `File<'f, Closed>` are the *same* file across the
transition), while the concurrency guarantee — here shown via a linear `spawn` handle — is
carried by *some* must-join mechanism whose exact form is an open question (linear handle
vs. a standalone `JoinToken`, `structured-concurrency.md` §3). Note also *why* the read is
done before the spawn: a fiber can only capture sendable data, so an owned `String` moves
in cleanly where a borrow `&f` could not have crossed the boundary at all.
