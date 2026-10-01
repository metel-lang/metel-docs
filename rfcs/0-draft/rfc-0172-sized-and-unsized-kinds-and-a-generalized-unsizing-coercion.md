---
id: rfc-0172
title: "Sized and Unsized Kinds, and a Generalized Unsizing Coercion"
date: '2026-10-01'
status: draft
---

## Summary

A Sized/?Sized-equivalent kind distinction and a generalized unsizing coercion, scoped to what an unsized [T] payload needs -- split out of RFC-0124 OQ7's @a [T] prerequisites, also required by RFC-0124 OQ2 option (a).

---

## Motivation

**No `Sized`/`?Sized`-equivalent kind distinction exists anywhere in `metel-frontend`'s type
checker today** (checked directly, 2026-09-28, while drafting RFC-0124 OQ7). Every type is
implicitly "however big it needs to be" — there is no way to say "`[T]` may appear as a
pointer-shaped wrapper's payload, but never as a bare field, local, or return type on its
own." This RFC proposes that distinction, scoped to exactly what `[T]`-as-unsized-payload
needs — not a general-purpose unsized-types system.

This was first identified as a prerequisite for RFC-0124 Open Question 7: what `@a [T]`
(Metel's `Box<[T]>` analogue, via RFC-0063's `@a T` allocator-tagged pointer type) would
need beyond RFC-0067's anchor dependency. OQ7 lists it as "the foundational piece, prior to
anything else in this list," but files the whole question as "deliberately not a near-term
priority" — because `List<T>` already fills "owned, heap, growable" without a separate
unsized-payload type underneath it, so `@a [T]` composability has no urgent consumer.

**That framing undersells it.** The same kind distinction is *also* a hard prerequisite for
RFC-0124's own Open Question 2, option (a) — the "sigil requirement, Rust-exact" path for
making `[T]` itself lifetime-anchor-checked once RFC-0067 lands: *"Introduce an unsized
`[T]` payload type — cannot be a bare field, local, or return type on its own — and require
every use site to spell the borrow explicitly, `&[T]` / `&var [T]`, through the existing
`Reference`/`MutReference` machinery."* Option (b) (implicit lifetime on bare `[T]`, no
spelling change) needs no unsized kind at all — but if OQ2 settles on (a), this stops being
a deprioritized side question and becomes the thing blocking `[T]`'s own soundness story.
This RFC exists so that branch is designed and waiting, not discovered mid-implementation.

**The coercion story has the same shape of gap, and it is narrower than it looks.**
`[T; N]` coerces to `[T]` today (RFC-0053 §4), but verified directly against source
(2026-10-01): the *accepted* direction is not implemented by any coercion rule at all — it
falls out of `unify()`'s general, deliberately-kept-*symmetric* `Array`/`SizedArray`
structural matching, shared by every unification call site in the type checker. Symmetry
means `unify()` alone would also wrongly accept the unsound reverse direction (`T[]` where
`[T; N]` is expected — a dynamic length can't satisfy a fixed one). That reverse direction
is re-rejected by one narrow, direction-aware guard,
`reject_dynamic_array_where_sized_expected`
(`metel-frontend/src/pipeline/type_checking/construction/mod.rs:683-697`), called
explicitly at each argument-construction site that needs it
(`construction/calls.rs:114,665`; `construction/mod.rs:723`) — not a general mechanism,
by its own doc comment's admission (`mod.rs:659-682`): changing `unify()` itself to be
asymmetric was tried and reverted, since it broke five existing fixtures and two cases
found by hand elsewhere in the corpus that depend on the symmetric match. **Nothing here
composes through a wrapper type.** `@a [T; N]` does not coerce to `@a [T]` — there is no
mechanism that unifies two wrapper types by recursively unsizing their payloads and
synthesizing the fat pointer's length under the pointer at the coercion site. Any wrapper
kind (`@a T` today; `&T`/`&var T` if option (a) is chosen for `[T]` itself) hits the same
wall.

---

## 1. The `Sized` / `?Sized` kind distinction

Every type is `Sized` by default, exactly as today, with no surface syntax change for the
overwhelming majority of types. `[T]` becomes Metel's first — and, in this RFC's scope,
*only* — built-in `?Sized` type: a type whose size is not known until a length accompanies
it.

An unsized type may appear only as the immediate payload of a **pointer-shaped wrapper
kind** — a closed list, not an open trait-bound-driven system: `&T`, `&var T` (if RFC-0124
OQ2 chooses option (a) for `[T]`), and `@a T` (RFC-0063). Everywhere else a type is expected
— a bare `let`/`var`/field/parameter/return type, a generic type argument instantiating an
ordinary (implicitly-`Sized`) type parameter — an unsized type is rejected at that position,
the same way `[T]` as a bare field is accepted today but would stop being accepted under
option (a) without a sigil.

**Deliberately out of scope:** a `?Sized` opt-out spelling on user-authored generic type
parameters (Rust's `fn foo<T: ?Sized>`), a mechanism for *user-defined* unsized structs
(Rust's custom DSTs), and any interaction with `dyn Aspect` existentials — RFC-0008 already
implements `dyn Aspect` through its own, separately-built erasure mechanism, not a kind
system, and nothing here requires touching it. Widening this RFC to a general unsized-types
facility was considered and rejected; see Alternatives Considered.

---

## 2. A generalized unsizing coercion

One coercion rule, applied wherever a wrapper-kind type is checked against an
expected wrapper-kind type of the same wrapper, replacing both existing mechanisms above:

- If the expected type is `W<[T]>` (for wrapper kind `W` — today `@a`, plain `&`/`&var` once
  relevant) and the actual type is `W<[T; N]>` for the same `W` and same `a`/reference kind,
  the coercion is accepted and the fat pointer's length is synthesized as `N` under the
  wrapper at the coercion site.
- The reverse (`W<[T]>` where `W<[T; N]>` is expected) is rejected, for the same reason
  `reject_dynamic_array_where_sized_expected` rejects it today: a dynamic length cannot
  satisfy a static one.
- The bare (unwrapped) `[T; N]` → `[T]` case is this rule's `W = identity` instance — the
  existing RFC-0053 behavior falls out of the general rule rather than needing its own
  hand-written guard, and the bolted-on function this RFC replaces is deleted.

This is deliberately **not** a change to `unify()`. `unify()` stays symmetric and
structural, used for the many call sites that have nothing to do with actual-vs-expected
coercion (per `mod.rs:671-682`'s own finding that making it asymmetric broke unrelated
fixtures). The generalized coercion is its own explicit, direction-aware pass — the same
shape as today's guard, just written once, recursively, against any wrapper kind, instead
of once per wrapper kind as each is added.

---

## Alternatives Considered

**Do nothing; keep the bolted-on guard.** Rejected as the status quo this RFC exists to fix:
it already does not compose (confirmed by RFC-0124 OQ7's finding), and each future wrapper
kind that wants `[T]` as a payload (a second allocator-pointer type, a future `&`/`&var`
sigil requirement) would need its own hand-written guard repeating the same reasoning.

**A full general-purpose unsized-types system** (Rust's `str`, trait-object-as-unsized,
user-defined DSTs via a custom `?Sized` struct tail field). Rejected as over-scoped: Metel
has no `str`/`[u8]`-distinct string representation to motivate it, `dyn Aspect` already
solves the trait-object case through its own mechanism, and no user-defined unsized type
has ever been proposed in this corpus. Scoping to exactly `[T]` keeps this RFC reviewable
and keeps the kind list closed rather than opening a new axis of generic-bound surface area.

**Fold this into RFC-0124 itself**, rather than a separate RFC. Rejected on the same
precedent that produced RFC-0126 and RFC-0133 as splits from RFC-0124: a tractable,
independently-designable piece trapped inside a document gated on a different question
(here, OQ2's (a)-vs-(b) choice, which itself waits on RFC-0067) does not get worked on. This
RFC can be designed, reviewed, and sit ready regardless of when OQ2 resolves.

---

## Open Questions

1. **Does this proceed at all?** If RFC-0124 OQ2 settles on option (b) (implicit lifetime on
   bare `[T]`, no spelling change), `[T]`'s own need for an unsized kind evaporates, and
   only OQ7's `@a [T]` composability motivation remains — explicitly not a near-term
   priority on its own. This is the central open question, and it is why this RFC carries
   no target (see Decision).
2. **Surface syntax for a `?Sized` bound, if ever exposed to user-authored generics.** Out
   of scope here since only the built-in `[T]` is unsized under this proposal, but a future
   RFC extending the kind list (a second built-in unsized type, or user-defined ones) would
   need to answer it. Not blocking.
3. **Should `dyn Aspect` (RFC-0008) be retrofitted onto this kind system later**, now that
   one would exist, rather than kept as its own separately-built erasure mechanism? Not
   blocking; raised only so it isn't rediscovered as a surprise if this RFC proceeds.

---

## References

- **RFC-0124 (Sequence Types), `1-under-review`** — Open Question 2 (option (a)) and Open
  Question 7, this RFC's two motivating consumers; OQ7 is where this gap was first
  confirmed absent from the type checker (2026-09-28).
- **RFC-0067 (Lifetime Anchors), `1-under-review`** — the `Reference`/`MutReference`
  machinery OQ2 option (a) would reuse; this RFC's `[T]`-specific motivation is only live
  once RFC-0067 exists and OQ2 resolves in its favor.
- **RFC-0122 (Borrow Checking), `1-under-review`** — blocks RFC-0067 settling first.
- **RFC-0063 (Allocator Handles), `2-accepted`** — defines `@a T`, the one pointer-shaped
  wrapper kind this RFC's coercion needs to compose through today for `@a [T]`.
- **RFC-0171 (prefix array syntax `[T]`/`[T; N]`), `3-integrated`, impl not started
  (`metel-core#1291`)** — option (a) would reopen this freshly-accepted bare spelling by
  requiring `&[T]`/`&var [T]` at every use site instead.
- **RFC-0053 (Fixed-Size Array Type), `4-implemented`** — source of the `[T; N]` → `T[]`
  one-directional coercion rule this RFC generalizes.
- **RFC-0126 (`T[]` as a Copy Borrowed View), `4-implemented`** — makes `[T]` the unsized
  payload candidate in the first place.
- **RFC-0133 (From-Metel List), `0-draft`, no target** — the precedent this RFC follows for
  staying deliberately untargeted pending a gating question's resolution.
- `metel-frontend/src/pipeline/type_checking/construction/mod.rs:659-697`
  (`reject_dynamic_array_where_sized_expected`, plus its own doc comment explaining why it
  is not a `unify()` change) and `construction/calls.rs:114,665` — the current narrow,
  bolted-on guard this RFC's generalized coercion replaces; verified directly 2026-10-01
  that the *accepted* `[T; N]` → `T[]` direction is handled by `unify()`'s general symmetric
  matching, not by this function, which exists only to re-reject the unsound reverse
  direction symmetry alone would wrongly admit.
- `metel-core#1291` — RFC-0171's own tracking issue, relevant if option (a) is chosen since
  implementing it would reopen that work.

---

## Decision

**Outcome:** *(pending)*
**Target:** *(none, deliberately — see Open Question 1. This RFC should not receive a
target until RFC-0124 OQ2 resolves (a) vs (b), per `PROCESS.md`'s convention; same posture
as RFC-0133.)*
