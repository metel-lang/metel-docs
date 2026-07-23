---
id: rfc-0114
title: "Constructor Aspect and Canonical Construction"
date: '2026-07-23'
status: draft
target:
---

> **New RFC, split out 2026-07-23** from `reports/substructural-types/nominal-types-as-branded-rows.md`
> §6/Open Question 1 — that document found a construction-invariant bypass reachable
> through ordinary code once row-narrowing and widening are both automatic, and this RFC
> is the proposed fix, formalized separately so it can be reviewed on its own terms.
> `rfc.py new`'s overlap check flagged RFC-0090, RFC-0096, RFC-0038, RFC-0103, RFC-0105 —
> checked each: RFC-0090 owns `ToRecord`/`FromRecord` and names the problem (§8, open
> question 10) without proposing this fix; RFC-0096 owns the *auto-impl* pattern
> (`Send`/`Sync`/`Linear`, a closed, compiler-intrinsic list) which this RFC's default
> derivation resembles in spirit but does not reuse directly (§7); none of the others
> touch construction at all. Depends on RFC-0100 (still `1-under-review`, reopened) for
> removing bare struct literals, and names RFC-0026 (`unsafe` blocks, `0-draft`,
> deferred) as the foundation for §6's escape hatch.
>
> **Revised 2026-07-23, later the same day.** §5's fallibility question — left with
> three unadopted candidates in the first draft — is resolved: `construct` returns
> `Result<Self, Self::Error>`, with `Self::Error` defaulting to `!`. Both halves of the
> resolution reuse already-*implemented* rules from RFC-0078 (uninhabited-variant
> exhaustiveness, inhabited-singleton coercion) rather than inventing new type-system
> machinery. The three original candidates are kept below, marked superseded, not
> deleted.

## Summary

A `Construct` aspect makes producing a value of a nominal type canonical: every `Self`
value, whether built fresh or reassembled after a partial move narrowed it away, comes
into existence through exactly one function, `Construct::construct(row) ->
Result<Self, Self::Error>`. This closes RFC-0090's open question 10 (`FromRecord`
bypassing constructor invariants) in its original scope and in the more general form
`reports/substructural-types/nominal-types-as-branded-rows.md` §6 found — automatic
widening after an ordinary partial move, not just an explicit conversion call. A
type author who has no invariant to enforce writes nothing; the compiler synthesizes a
trivial default, `Self::Error = !`, and RFC-0078's already-implemented coercion rules
make the resulting `Result<Self, !>` collapse to bare `Self` with no unwrap, no match,
and no runtime branch — provably, not by convention. A type whose invariant can
genuinely reject gets a real, typed error instead, and loses the automatic-firing sugar
in exchange — the same rule, applied uniformly, decides both. A separate, opt-in aspect,
`ConstructUnchecked`, gives performance-sensitive code an explicit, `unsafe`-gated way to
skip validation entirely when it already knows the invariant holds — mirroring Rust's
`new`/`new_unchecked` convention directly.

---

## Motivation

RFC-0090 §8 already names the risk, scoped narrowly: `SortedPair { small: i32, big: i32
}`'s invariant (`small <= big`), enforced only by `SortedPair::new`, can be silently
violated if `FromRecord` is auto-derived, because "auto-derived reconstruction can
silently skip validation a hand-written constructor enforces." Its own text limits the
concern to that one conversion function.

`nominal-types-as-branded-rows.md` §6 found the same bypass reachable through nothing
more than ordinary code, once narrowing and widening are both automatic and structural:

```metel
fun mess_with_it(p: &mut SortedPair) {
    let old_small = p.small;   // move small out; p narrows to .{ big }
    p.small = 999_999;         // assign an arbitrary value back in; p widens to full SortedPair
    // no call to SortedPair::new, anywhere. invariant possibly broken.
}
```

That document was explicit that plain mutable-field reassignment already has this
problem today, with zero row machinery involved — the finding is not a new hole, it is
that OQ10 was mis-scoped as `FromRecord`-specific when the underlying problem is general.

A second, independent motivation: without a single canonical path, a type with several
surface constructors (`new`, `from_str`, …) has no structural guarantee they stay in
sync with the same invariant — each is free-standing code that happens to duplicate
validation logic, or forgets to.

---

## 1. The `Construct` aspect

```metel
aspect Construct {
    type Error;
    fun construct(row: .{ /* all of Self's fields */ }) -> Result<Self, Self::Error>;
}

impl Construct for SortedPair {
    type Error = !;
    fun construct(row: .{ small: i32, big: i32 }) -> Result<Self, !> {
        if row.small <= row.big { Ok(SortedPair { small: row.small, big: row.big }) }
        else { Ok(SortedPair { small: row.big, big: row.small }) }
    }
}
```

`construct` takes the type's own complete row and produces a `Result`, not a bare `Self`
— the signature that makes §5's fallibility resolution possible. `ToRecord`/`FromRecord`
(RFC-0090 §8) use bare `Self`; `construct` deliberately does not, for the reason §5
works through.

**A struct with no invariant writes nothing.** The compiler synthesizes a trivial default
— `type Error = !; construct(row) { Ok(row) }` — the same way `Send`/`Sync`/`Linear`
compose a default from field-level facts today. Whether this specific default (a *whole*
synthesized impl, not a partial one) is expressible with mechanisms this corpus already
has is Open Question 3 — RFC-0082 (associated types) explicitly declined a *general*
default-associated-type mechanism, for reasons that don't obviously transfer to this
narrower case; see that question for why. This default must compile away entirely for
types that never customize it; construction for the overwhelming majority of structs
should cost exactly what a bare field-literal costs now. That is a *commitment*, matching
`nominal-types-as-branded-rows.md` §9's own unvalidated zero-cost claim for the
representation generally — not a new promise, the same one recurring here.

---

## 2. Canonical construction: all construction is `Self::construct(row)`

Once RFC-0100 lands, `Type { field: value }` struct literals no longer exist as a
separate surface form — "`Type(args)` call-shaped syntax **replaces**
`Type { field: value }` struct literals at construction sites," in that RFC's own words.
Under this RFC, `SortedPair(3, 1)` desugars to `SortedPair::construct(.{ small: 3, big: 1
})` — fresh construction and post-narrowing reconstruction (§3) become the *same*
operation, not two mechanisms that happen to need the same validation. Both get the
*same* result-handling treatment from §5, uniformly: `let p = SortedPair(3, 1);` binds a
bare `SortedPair` when `Self::Error = !` (RFC-0078's inhabited-singleton coercion applies
automatically), and binds a `Result<SortedPair, E>` the caller must handle otherwise —
ordinary, unsurprising behavior for a function call either way.

**This RFC depends on RFC-0100 removing the bare literal, and that dependency is not
solid yet.** RFC-0100 is `1-under-review`, reverted there during integration and
currently "reconsidering whether general keyword arguments belong in the spec at all"
(`OBJECTIVES.md` Trigger 14). If RFC-0100 is refused or narrowed, this RFC needs its own,
narrower restriction — the compiler simply refuses a bare `Type { field: value }` literal
specifically for any type implementing a non-default `Construct` — rather than leaning
entirely on RFC-0100 having landed. That fallback is not worked out here.

---

## 3. Row-completion firing `construct()` automatically

The mechanism `nominal-types-as-branded-rows.md` §6 needed: any assignment that completes
a narrowed row — every label present again — is sugar for calling `construct()` on the
completed row and replacing the narrowed value with the result, rather than a bare
in-place write.

**Piecewise building composes the same way.** A value built up field by field —
`structural-records.md`'s `MaybeUninit`-avoidance example, `let partial = record { a:
compute_a() }; let partial = record { ..partial, b: compute_b() }; …` — only calls
`construct()` once, at the point the row becomes complete, exactly as a single literal
would. Intermediate partial states are ordinary, fully-valid values of a narrower type;
nothing fires until nothing is missing.

---

## 4. Collapsing `FromRecord` into `Construct`

`ToRecord`/`FromRecord` (RFC-0090 §8) are the same shape as `construct`'s signature under
a different calling convention. `ToRecord` needs nothing from this RFC — RFC-0090 already
states reading fields out of an already-valid value "is always safe." `FromRecord`'s
half, though, is the *exact* danger OQ10 names, under a different name for the same
operation. Under this RFC, `from_record(row)` is sugar for `Self::construct(row)`; there
is no second validation story to maintain. **This RFC does not itself amend RFC-0090's
text** — that reconciliation is left as a note for whichever review pass reconciles the
two, not decided unilaterally here.

---

## 5. Fallibility — resolved, reusing already-implemented rules

`SortedPair::construct` above is **infallible and self-healing** — it never rejects, only
reorders. Not every invariant can be repaired that way. A `NonEmptyList<T>` cannot
manufacture an element out of nothing if its row completes empty; its invariant must be
able to *reject*, not just normalize. `construct` therefore returns
`Result<Self, Self::Error>` (§1) rather than bare `Self` — but that alone would leave the
same problem §2 already names: **an ordinary field assignment looks syntactically
infallible.** `p.small = 999_999` reads as plain mutation; if `construct` can genuinely
fail, what does the automatic firing (§3) do with an `Err`?

**The resolution reuses two already-*implemented* rules from RFC-0078 (Bottom Type,
`4-implemented`, integrated 2026-07-10), rather than inventing a new one:**

- **§3.2, uninhabited variants:** "an enum variant whose payload type is `!` is
  uninhabited. No value of that variant can ever be constructed." `Result<Self, !>`'s
  `Err(!)` branch is therefore not reachable — not by convention, by construction.
- **§3.3, inhabited-singleton coercion:** "If an enum type has exactly one inhabited
  variant... and that inhabited variant has exactly one field, a value of that enum type
  implicitly coerces to that field's type. The compiler inserts the destructuring; no
  explicit match is required." `Result<Self, !>` matches this exactly — `Ok` is the sole
  inhabited variant, holding exactly `Self`.

**For the default case (`Self::Error = !`), these two rules together mean the compiler
already, today, implicitly coerces `Result<Self, !>` to bare `Self` — no unwrap, no
match, no runtime branch, and *provably* safe rather than trusted.** The automatic firing
in §3 needs no special casing: it calls `construct`, the result coerces silently, the
assignment stays exactly as ordinary as it looks.

**For a genuinely fallible type** (`type Error = NonEmptyListError;`),
`Result<Self, Error>` has two inhabited variants, so §3.3's coercion simply does not
trigger — there is no silent path to bare `Self`. Concretely, this means **the
automatic-firing sugar in §3 is not available for such a type**: completing its row
cannot happen through a bare assignment at all: the compiler has no implicit coercion to
insert, so the assignment is rejected, and reconstruction must go through an explicit
call to `construct`, handled with the same already-existing machinery ordinary fallible
calls already use (`?`, `match`, `.unwrap_or`) — the `?` operator with `From`-based error
coercion has been live since v0.4.0 (noted in RFC-0079's own refusal record, which
otherwise only confirms `Result<T, E>` and `Perhaps<T>` are already implemented and
spec'd, not that anything about them needs inventing here).

**One rule decides both halves, and it is not a new rule.** Whether a type gets the
automatic-firing convenience or requires explicit result-handling falls entirely out of
whether `Self::Error` is uninhabited — the same declaration that expresses "can this
fail" also decides "does this get silent re-widening," with no separate flag to keep in
sync. This applies uniformly to fresh construction and post-narrowing reconstruction
alike (§2) — the same rule, not two rules that happen to agree.

**`ConstructUnchecked` (§6) is a genuinely different flavor of trust, not made redundant
by this.** `Construct`'s infallibility, when claimed, is *proven* by the type system
(`Err` uninhabited, checked exhaustively). `ConstructUnchecked`'s is *asserted* by the
programmer, via `unsafe`, unchecked — the escape hatch remains necessary for types whose
invariant is real but whose author, in a specific call site, already knows it holds and
wants to skip re-proving it.

**Superseded, kept for the record — the first draft's three candidates, before this
resolution:** *(a)* only infallible impls participate in automatic firing, others opt
out of implicit narrow/widen entirely; *(b)* `construct` stays infallible by convention,
genuine rejection lives only in separate explicit constructors; *(c)* `construct` panics
on failure, treated as infallible at the type level. Reading them back, (a) is what the
resolution above actually *is*, made precise and automatic via RFC-0078 rather than left
as a design choice to enforce by hand; (b) and (c) are no longer needed.

---

## 6. The unsafe escape hatch: `ConstructUnchecked`

A systems language needs a way to skip redundant validation when a caller already knows
the invariant holds — Rust's `NonZeroU32::new` (checked) alongside `new_unchecked`
(unsafe, no check) is the direct precedent.

```metel
aspect ConstructUnchecked {
    unsafe fun construct_unchecked(row: .{ /* all of Self's fields */ }) -> Self;
}
```

**Separate from `Construct`, deliberately.** Not auto-derived, not implied by
implementing `Construct` — a type author writes it explicitly, taking on the
responsibility the `unsafe` block already signals elsewhere in the language. Ordinary
row-completion (§3) never calls it; only code that explicitly reaches for
`construct_unchecked` inside an `unsafe` block does.

**This depends on RFC-0026 (`unsafe` blocks), which is not a solid foundation yet.**
RFC-0026 is `0-draft`, and its own header still describes itself as deferred pending
RFC-0028 (Memory and Reference Model) and RFC-0046 (Linear Closure Capture) — **both of
which are actually `6-refused`**, not open or unresolved as RFC-0026's text currently
claims. That drift is RFC-0026's own to fix, not addressed here, but it means the
foundation this section leans on is staler than a first read of RFC-0026 suggests, and
may in fact be closer to revisitable than its own header currently states.

---

## 7. Generics and monomorphization

A generic struct's row depends on its type parameter — `Pair<T> { a: T, b: T }`'s row
isn't fully known until `T` is concrete. Whether `construct()` resolution needs to defer
to monomorphization time, the way Metel's generic function bodies already do
(`FunBody::Generic`/`TypedExpr::GenericClosure`, constructed from runtime values), is the
same question `nominal-types-as-branded-rows.md` open question 4 already asks, recurring
here rather than being separate. Not worked through in either document.

---

## 8. Scope

**Enums are out of scope**, consistent with RFC-0090 §6/§9 and
`nominal-types-as-branded-rows.md` — this is a structs-only mechanism. Stated explicitly
rather than left to be assumed.

This RFC does not propose changes to `Drop` dispatch (`nominal-types-as-branded-rows.md`
§4) beyond noting the parallel: `Construct`/`ConstructUnchecked` govern how a value is
*born*, the same way `Drop` governs how it is *torn down* — two ends of the same
lifecycle, addressed by two separate, independently-motivated RFCs rather than one.

---

## Open Questions

1. ~~Fallibility.~~ **Resolved 2026-07-23, §5:** `construct` returns
   `Result<Self, Self::Error>`; RFC-0078's already-implemented uninhabited-variant and
   inhabited-singleton-coercion rules make the default (`Error = !`) collapse to bare
   `Self` provably, and a real `Error` type loses the automatic-firing sugar in exchange,
   both by the same mechanism. Kept as a struck-through entry rather than removed, per
   this corpus's convention of leaving resolved questions visible.
2. **Does this RFC need its own literal-banning rule independent of RFC-0100** (§2), given
   RFC-0100's own status is currently uncertain?
3. **What derives `Construct`'s default implementation, mechanically?** §5's resolution
   sharpens this rather than settling it: RFC-0082 (associated types, `4-implemented`)
   explicitly declined a *general* default-associated-type mechanism — "a default would
   create a compiler-generated impl that could conflict with user impls under the
   overlap rules" — but that objection is about a *partial* default merging into a
   user-written impl. `Construct`'s need is a *whole* synthesized impl
   (`type Error = !` and the trivial body together), existing only when the user writes
   no impl at all, which is structurally closer to RFC-0096's auto-impl pattern
   (`Send`/`Sync`/`Linear`) than to what RFC-0082 declined — but RFC-0096's own pattern is
   a closed, compiler-intrinsic list of exactly three aspects (RFC-0096 §1), not a
   general mechanism either. Whether RFC-0082's stated objection actually applies to this
   narrower, whole-impl case is unexamined. RFC-0093's comptime-derive mechanism is a
   third candidate, itself `0-draft`. Not resolved here.
4. **Monomorphization timing for generic structs** (§7) — open in both this RFC and
   `nominal-types-as-branded-rows.md`.
5. **Does the compiler need to separately enforce that hand-written surface constructors
   (`new`, `from_str`) route through `construct()`**, or does removing the bare literal
   (§2) make this automatic — since, once no other way to produce a `Self` exists
   structurally, every constructor must bottom out in `construct()` or another function
   that does? Plausible, not checked against a concrete typechecking design.
6. **Is RFC-0026 a solid enough foundation for §6?** Its own cited blockers are both
   already refused, not open — which may mean it is closer to revisitable than its
   current text suggests, but that is RFC-0026's maintenance question, not settled here.
7. **Does a fallible type's narrowed-but-incomplete row ever get stuck**, the same
   liveness-not-safety gap RFC-0090 §8 already accepts for `restore` ("nothing stops code
   from never calling `restore`")? Presumably yes, and presumably fine for the same
   reason — not checked against a concrete example here.

---

## References

- `reports/substructural-types/nominal-types-as-branded-rows.md` — §6 and Open Question
  1, the problem this RFC is the proposed answer to
- `internal/rfcs/1-under-review/rfc-0090-structural-records.md` §5 (field-composition
  auto-derivation), §8 (`ToRecord`/`FromRecord`, the `SortedPair` example, open question
  10 in its original, narrower scope)
- `internal/rfcs/4-implemented/rfc-0078-bottom-type.md` §3.2 (uninhabited variants), §3.3
  (inhabited-singleton coercion) — the two already-implemented rules §5's fallibility
  resolution reuses rather than inventing new machinery
- `internal/rfcs/6-refused/rfc-0079-perhaps-and-result.md` — refused as redundant with
  reality, not with the type itself: confirms `Result<T, E>`/`Perhaps<T>` and the
  `?`-operator with `From`-based error coercion are already implemented, live since
  v0.4.0, which §5 depends on for the fallible-type path
- `internal/rfcs/4-implemented/rfc-0082-associated-types.md` §9 — the declined general
  default-associated-type mechanism, cited precisely in Open Question 3 rather than
  assumed to transfer to `Construct`'s narrower case
- `internal/rfcs/0-draft/rfc-0096-auto-impl-aspects-compiler-recognized-structural-aspects.md`
  — the auto-impl pattern `Construct`'s default derivation resembles but does not reuse
  directly (§1, §3)
- `internal/rfcs/1-under-review/rfc-0100-constructor-call-construction.md` — the
  literal-removal this RFC's canonical-construction claim depends on; its own status is
  uncertain (`OBJECTIVES.md` Trigger 14)
- `internal/rfcs/0-draft/rfc-0026-unsafe-blocks.md` — the foundation for
  `ConstructUnchecked`; `0-draft`, deferred, with a stale dependency note (§6)
- `internal/rfcs/0-draft/rfc-0093-derive-registration.md` — the comptime-derive
  mechanism possibly relevant to `Construct`'s default (open question 3)
- `reports/substructural-types/structural-records.md` — the piecewise-`MaybeUninit`
  worked example §3 generalizes

---

## Decision

**Outcome:** *(pending)*
**Target:** *(set when accepted)*
