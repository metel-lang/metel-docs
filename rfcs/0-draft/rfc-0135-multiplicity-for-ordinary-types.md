---
id: rfc-0135
title: "Multiplicity for Ordinary Types"
date: '2026-08-13'
status: draft
target:
---

> **Companion to RFC-0134, not a dependency of it.** RFC-0134 (Closure Call Capability,
> `0-draft`, merged) proposes a `once`/`many` multiplicity axis for closures, inferred
> from the closure's own body, with an explicit qualifier syntax reserved for function
> parameters that need a stable, declared promise. That RFC named — deliberately, not
> designed — the idea this document takes up: that `Copy` for ordinary types and `many`
> for closures answer the same underlying question about different operations, and could
> share one vocabulary. Nothing here changes RFC-0134's own scope or mechanism; this is
> the "future RFC" its own §5 pointed at. Every design choice below that isn't already
> settled by existing, shipped behavior is marked as an Open Question, not asserted.

> **Update (2026-08-14) — the relationship tightened for RFC-0134 §1 specifically.**
> RFC-0134 §1 turned out to need somewhere to *store* a closure's `Copy`-ness: a
> closure's captures appear nowhere in its type, so `is_copy` — which receives only a
> `Type` — cannot compute the rule §1 states, and RFC-0134's own Motivation already rules
> out answering it in the move checker instead. RFC-0134 §4 now carries a second field
> (`use_multiplicity`) alongside its call-multiplicity field to hold it. That field *is*
> this document's core reframing — `Copy` is `many` answered for the by-value-use
> operation — arrived at independently from RFC-0134's own storage problem rather than
> imported from here. This does not make RFC-0134 depend on this document: §1 needs the
> field regardless, and if this document is refused, the field simply keeps the name
> `Copy` instead of gaining unified vocabulary. But the two documents now describe the
> same representation for closures, so a divergence between them would be a real
> inconsistency rather than a difference of framing.

## Summary

Reframe `Copy` as what `many` means when the operation in question is "by-value use"
rather than "call" — the same axis RFC-0134 proposes for closures, applied to the
operation every type (not just function types) already has. For named types (`struct`,
`enum`), this replaces the current explicit `extend TypeName: Copy;` aspect declaration
with a `once`/`many` qualifier on the type's own declaration — `many struct Example
{ ... }` — a syntactic simplification, not a new capability, since `Copy` for named types
is already always-explicit today, never structurally inferred. For structural types
(anonymous records, tuples, function types), this is **not** a uniform rename: the three
are in three different, unfinished states today (§3), and this proposal's vocabulary
change makes each state easier to describe precisely rather than treating them as one
mechanism to relabel.

---

## Motivation

RFC-0134 needed a `once`/`many` axis for closures because calling a closure is an
operation whose "does this consume or not" question `Copy` alone cannot answer — a
closure with a non-`Copy` capture that only *reads* it must still be callable
repeatedly, which is exactly why RFC-0134 §2 exists rather than reusing `Copy` directly.
Working through *why* that split was necessary surfaced a broader fact, worth stating
precisely rather than left as a passing analogy: **`Copy` is not a different concept
from `many` — it is `many`, answered for a specific, always-present operation** (using a
value by value: moving it, passing it, assigning it) rather than the call-specific
operation RFC-0134 is about. Non-`Copy`/affine is `once` for that same operation. This
isn't a coincidence discovered late — it is the same relationship RFC-0134 §2 already
draws between closure `many` and receiver-kind (`&self` methods are repeatable on
non-`Copy` receivers today, with no stated relationship to `Copy` anywhere, because
that's `many` answered for a *different* operation than the one `Copy` answers). Once
that's visible for one operation (call) and one other (receiver-kind, already shipped),
it's worth asking whether the *type* system's vocabulary should say so directly, instead
of treating `Copy` as a separate, unrelated-looking name for a special case of the same
thing.

This is squarely a vocabulary and mechanism-location proposal, not a soundness fix.
Nothing about `Copy`'s current behavior is broken the way `Type::Fun`'s blanket-`Copy`
bug was (`metel-core#596`-adjacent, the bug RFC-0134 §1 fixes for closures specifically).
The case for this RFC is legibility and consistency: one name for one concept, used
consistently across function types and ordinary types, rather than two names
(`once`/`many`, `Copy`/non-`Copy`) for what turns out to be the same axis.

---

## Background: how `Copy` actually works today

Checked directly against `metel-frontend/src/typeinference/mod.rs` and
`metel-frontend/src/coherence.rs` rather than assumed, since the RFC-0134 discussion
that led here got part of this wrong on a first pass:

- **Named types (`struct`, `enum`) are `Copy` only via an explicit `extend TypeName:
  Copy;` declaration** (or a conditional form, `extend<T: Copy> Foo<T>: Copy`),
  resolved through `type_satisfies_aspect`/`infer_type_satisfies_aspect` against
  registered `bare_impl_bounds`. There is **no structural auto-derivation** for named
  types — a struct with every field `Copy` is not `Copy` itself unless something wrote
  `extend`. This matters directly for this proposal: RFC-0134 §3 needed an *explicit*
  qualifier specifically to solve an inference-instability problem (a silently
  strengthening requirement with no annotation to point to). That problem does not exist
  for named-type `Copy` today, because it is already always-explicit. The case for
  `once`/`many` on a struct declaration is a syntax simplification, not a stability fix.
- **Structural types have no name to `extend` at all, but they don't share one uniform
  mechanism either — checked against RFC-0061 (`4-implemented`) and RFC-0071
  (`3-integrated`) rather than assumed, correcting this document's own first-draft claim
  that they were "necessarily derived from their own structure."** They're in three
  different, unfinished states:
  - **Records can never be `Copy` today, full stop.** RFC-0096's auto-impl set is closed
    to `{Send, Sync, Linear}` — `Copy` isn't in it — and RFC-0116 §3 bans a record from
    having any local `extend`. RFC-0071 (lines 45-69) states the consequence directly:
    "no anonymous record can ever be `Copy`... every record is affine and must be
    moved," naming it a known, accepted gap with RFC-0123 (field-wise constraints) as
    the eventual fix — not something already working structurally.
  - **Tuples have no impls of any kind yet**, `Copy` included — RFC-0061 §6: any aspect
    bound on a tuple fails Phase 1 diagnostics (`T0012`) today, pending a per-arity vs.
    variadic-generics decision that hasn't been made.
  - **Function pointers (`fun(A) -> B`, not closures) already have a real, working
    `Copy`** — RFC-0061 §7.2: a `std::core`-provided blanket impl, unconditional,
    because they carry no captured state. A genuine, already-specified mechanism, just
    not the same one records and tuples are missing.
  - **Closures get a fourth, new mechanism** once RFC-0134 §1 lands — capture-dependent,
    computed per closure literal, not structural recursion over a type's own shape the
    way the other three are (or would be).

  §3 below is rewritten against this; the earlier "unchanged mechanism, unified name"
  framing assumed a uniformity that doesn't exist yet.
- **RFC-0134's own findings, carried over rather than re-derived:** `Copy` implies
  `many` (a `Copy` closure has nothing non-`Copy` to consume, so it is necessarily
  reusable), but not the converse (a `many`, non-`Copy` closure — reads a capture without
  consuming it — is exactly RFC-0134 §2's reason for existing). The identical relationship
  applies to ordinary types under this proposal: `Copy` implies "by-value-use is `many`,"
  but a type could in principle be `many` for a *different* operation (a borrowing method)
  without being `Copy` — which is already true today, just not named consistently.
- **RFC-0071 §4 (referenced in `coherence.rs`) bans a type from implementing both `Copy`
  and `Drop`.** Coherence checking there verifies *that* exclusion (`impls_actually_overlap`
  between positive `Copy` and `Drop` impls).
- **Field-validation for `extend TypeName: Copy;` is real and enforced — the search that
  first turned up nothing was incomplete, not the codebase.** `coherence.rs` doesn't
  contain it, but `typechecker/inference.rs`'s `check_copy_impl_eligibility` does: called
  from the positive-impl-block inference path whenever `aspect_name == "Copy"`, it walks
  every struct field (or every enum variant's every payload field) and rejects the
  `extend` with `T0001` — `"cannot implement Copy for {target_name}: field {} has type {}
  which is not Copy"` — if any of them isn't `Copy` itself. Confirmed empirically, not
  just by reading: a struct with a `String` field and an explicit `extend Holder: Copy;`
  is rejected by the release binary with exactly that message; the enum-variant-payload
  form is rejected the same way; an all-`i64` struct with the same `extend` is accepted
  and behaves correctly (both post-assignment bindings independently usable). There is no
  soundness gap here for this proposal to inherit — see the former Open Question 2, now
  resolved rather than left open.

---

## Proposal

### 1. The core reframing

`Copy` for a type `T` becomes: *"the by-value-use operation on `T` is `many`."*
Non-`Copy`/affine becomes: *"the by-value-use operation on `T` is `once`"* — the current,
unchanged default. This is a renaming of what the concept *is called* and, for named
types, *how it's spelled* — not a change to which types end up `Copy`-equivalent today,
and not a claim that every operation on a type shares one multiplicity (a `&self` method
is `many` regardless, exactly as it already is, unrelated to this axis).

### 2. Named types: a declaration-site qualifier, replacing `extend TypeName: Copy;`

```metel
struct Example { field: i64 }        // unannotated: once (today's default, unchanged)
many struct Example { field: i64 }   // replaces `extend Example: Copy;`
```

`once` stays the implicit default for an unqualified declaration — this preserves
exactly what an unannotated `struct` means today (the overwhelming majority of structs,
which never write `extend: Copy`). `many` is the explicit, opt-in qualifier, written
once, on the declaration itself, in place of a separate `extend` statement — a strict
simplification (one declaration instead of two), not a new capability.

### 3. Structural types: four separate cases, not one mechanism to rename

Given the corrected Background above, this proposal's vocabulary change lands
differently on each structural case rather than uniformly:

- **Function pointers**: `Copy` → `many` is a real rename of a real, working mechanism.
  RFC-0061 §7.2's `std::core` blanket impl would need to actually change what it grants
  (`many` instead of `Copy`) — a small, concrete follow-up to that RFC, not just a change
  to this document's own vocabulary.
- **Records**: there is nothing to rename yet. A record stays permanently `once` under
  this proposal, exactly as it is permanently non-`Copy` today — this document doesn't
  change or fix the RFC-0071/RFC-0123 gap, only restates its outcome in `once`/`many`
  terms. "Records are `once`" under this proposal should not be read as a deliberate
  design choice the way it may be for closures (§4's per-expression reasoning) — it's an
  open, acknowledged limitation with its own fix path (RFC-0123) this document is not
  attempting.
- **Tuples**: same as records — nothing to rename, because there is no working `Copy`
  (or anything else) for tuples to relabel yet. `many`/`once` for tuples only becomes
  meaningful once RFC-0061 §6's per-arity-or-variadic-generics question is settled.
- **Closures**: covered by RFC-0134 §1/§2 directly, already named `once`/`many` there —
  this document adds nothing new for closures, only extends the same two words to the
  other three cases above, unevenly, as described.

### 4. Relationship to RFC-0134: shared vocabulary, distinct mechanism, distinct home

Restated precisely, since it's the crux of why this is a separate RFC rather than an
amendment to RFC-0134's own scope: closure multiplicity has to live *per expression* —
RFC-0134 §4's whole argument for a field on `Type::Fun` rather than an aspect query is
that two closures sharing a structural signature can have different multiplicities,
depending on their own bodies. Named-type `Copy`/`many` has no such per-expression
variance — every value of type `Example` has the same multiplicity, fixed at the
declaration. This proposal does not change that: it keeps the per-declaration,
nominal mechanism named types already use (registered `extend`-equivalent facts,
just spelled `once`/`many` on the declaration instead of appended as a separate
`extend: Copy` statement), and keeps the per-expression field mechanism for closures
exactly as RFC-0134 proposes it. Same word, same underlying axis, two different
*homes*, for the same structural reason RFC-0134 §4 already gives.

---

## What this deliberately does not include

- **No change to `Copy`'s actual semantics for any type that has one today.** This is a
  rename and a re-spelling, not a redesign — a struct that is `Copy` today under
  `extend: Copy` is `many` under this proposal and behaves identically.
- **No auto-derivation for named types.** `struct`/`enum` stay explicit-only, matching
  today's behavior; this proposal does not add structural Copy-inference for them (that
  would be a different, larger change, and isn't needed to answer the question RFC-0134's
  discussion raised).
- **No change to `&self`/receiver-kind mechanics.** Those already work, already don't
  depend on `Copy`, and stay exactly as they are — cited here only as the existing
  precedent this proposal's core reframing is checked against.
- **No opinion yet on whether `Copy` as a name is removed, deprecated, or kept as an
  alias.** See Open Question 4.

---

## Open Questions

1. **Generic named types.** `extend<T: Copy> Foo<T>: Copy` is a real, used pattern
   (`coherence.rs` cites it directly). What does its `once`/`many` translation look like
   on a declaration-site qualifier — `many<T: many> struct Foo<T> { ... }`, something
   closer to a `where`-style clause, or does the conditional case stay expressed as an
   `extend`-shaped form even after the unconditional case moves to a qualifier? Not
   resolved here; needs checking against every existing conditional-`Copy` pattern in
   the stdlib and test suite before proposing a specific syntax.
2. **Enums.** Not addressed above at all — does `many enum Example { ... }` require
   every variant's every field to be `many`, symmetric with the struct case? Presumed
   yes — and unlike the field-validation question below, this one is actually already
   answered for the *current* mechanism (`check_copy_impl_eligibility` walks enum
   variant payloads exactly the way it walks struct fields, confirmed both by reading it
   and by a real rejected test case), so the new qualifier form inherits a settled answer
   rather than an open one. Listed as its own item only because the *syntax* for `many`
   on an `enum` declaration specifically hasn't been written down anywhere yet.
3. **Migration: rename, alias, or coexistence?** Does `Copy` disappear entirely (a
   breaking rename — every `extend: Copy` in the stdlib and every user program needs
   rewriting), stay as a permanent alias for `many` (two names forever, undercutting the
   "one vocabulary" motivation), or something in between (deprecated but accepted for a
   transition period)? This is a real migration-cost question this document doesn't
   attempt to answer, and probably shouldn't until the rest of the design is settled.
4. **Diagnostic and teaching cost.** `Copy` is an immediately recognizable term for
   anyone coming from Rust or C++; `many` is not, outside of this RFC's and RFC-0134's
   own vocabulary. Existing diagnostics presumably say "not Copy" somewhere in their
   text — renaming what the type system calls this needs to weigh legibility-to-existing-
   Metel-programmers against unfamiliarity-to-newcomers-from-other-languages, a tradeoff
   with no clearly correct answer stated here.
5. **Should this document take a position on fixing the record/tuple gaps, or stay pure
   vocabulary?** As corrected, §3 inherits RFC-0071/RFC-0123's record gap and RFC-0061
   §6's tuple gap unchanged — this document only renames what each case currently
   resolves to, including "nothing yet" for two of the three. An alternative scope: use
   the `once`/`many` reframing as the occasion to also propose closing those gaps here.
   Not attempted above, since it would substantially widen this document's scope beyond
   "vocabulary and mechanism-location" (Motivation) into new soundness/design work
   RFC-0123 and RFC-0061 §6 already own.

**Resolved, formerly Open Question 2 — field-validation soundness.** Checked properly
this time: real, and enforced. See Background, above, for the mechanism
(`check_copy_impl_eligibility`) and the empirical confirmation. `many struct Example {
field: String }` inherits a working, already-verified check rather than needing to add
one from scratch — the qualifier form just needs to keep calling the equivalent of this
same validation, not invent a new one.

---

## References

- **RFC-0134 (Closure Call Capability), `1-under-review`** — the source of the `once`/`many`
  axis and the receiver-kind reconciliation this document generalizes from; §5 names
  this document's core idea and defers it here rather than designing it.
- `metel-frontend/src/typeinference/mod.rs` (`type_satisfies_aspect`,
  `infer_type_satisfies_aspect`) — confirms named-type `Copy` is explicit-only,
  resolved via registered `extend` bounds, never structurally auto-derived.
- `metel-frontend/src/coherence.rs` (RFC-0071 §4 checking, `impls_actually_overlap`) —
  confirms Copy/Drop mutual-exclusion coherence checking exists, for the conditional/
  generic-impl overlap case specifically.
- `metel-frontend/src/typechecker/inference.rs` (`check_copy_impl_eligibility`) — the
  per-field/per-variant-payload `Copy` validation this document's first draft searched
  for in the wrong file and reported as unconfirmed; confirmed present, wired into the
  positive-impl inference path, and empirically verified against three real test
  programs (rejects a non-`Copy` struct field, rejects a non-`Copy` enum variant
  payload, accepts and correctly runs an all-`Copy` struct).
- `metel-core#596` — the closure-`Copy` regression RFC-0134 §1 fixes; cited here only
  because this document's Background section leans on the same "structural vs.
  explicit" distinction that bug sits at the boundary of.
- **RFC-0061 (Structural Aspect Bounds), `4-implemented`** — §7.2 specifies the
  function-pointer `Copy` this document's §3 renames; §6 specifies tuples have no impls
  yet, the reason tuples have nothing to rename.
- **RFC-0071 (Ownership and Move Semantics), `3-integrated`** (lines 45-69) — states
  directly that no anonymous record can ever be `Copy` today, correcting this document's
  own first-draft Background claim; names RFC-0123 as the fix path this document does
  not attempt.
- **RFC-0096 (Auto-Impl Aspects), `0-draft`** — the closed `{Send, Sync, Linear}`
  auto-impl set `Copy` is deliberately not part of, one reason records have no
  structural path to `Copy`/`many` today.
- **RFC-0116** — §3's ban on local aspect impls for records, the other half (with
  RFC-0096) of why records can never reach `Copy`/`many` via `extend` either.
- **RFC-0123** — the field-wise-constraints fix path RFC-0071 names for records; not
  attempted by this document.

---

## Decision

**Outcome:** *(pending)*
**Target:** *(set when accepted)*
