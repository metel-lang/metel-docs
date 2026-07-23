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

## Summary

A `Construct` aspect makes producing a value of a nominal type canonical: every `Self`
value, whether built fresh or reassembled after a partial move narrowed it away, comes
into existence through exactly one function, `Construct::construct(row) -> Self`. This
closes RFC-0090's open question 10 (`FromRecord` bypassing constructor invariants) in its
original scope and in the more general form
`reports/substructural-types/nominal-types-as-branded-rows.md` §6 found — automatic
widening after an ordinary partial move, not just an explicit conversion call. A
type author who has no invariant to enforce writes nothing; the compiler synthesizes a
trivial default. A separate, opt-in aspect, `ConstructUnchecked`, gives performance-
sensitive code an explicit, `unsafe`-gated way to skip validation when it already knows
the invariant holds — mirroring Rust's `new`/`new_unchecked` convention directly.

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
    fun construct(row: .{ /* all of Self's fields */ }) -> Self;
}

impl Construct for SortedPair {
    fun construct(row: .{ small: i32, big: i32 }) -> Self {
        if row.small <= row.big { SortedPair { small: row.small, big: row.big } }
        else { SortedPair { small: row.big, big: row.small } }
    }
}
```

`construct` takes the type's own complete row and produces `Self` — the same signature
shape RFC-0090 §8 already gives `from_record`, not a new calling convention.

**A struct with no invariant writes nothing.** The compiler synthesizes a trivial default
— `construct(row) { row }`, an identity — the same way `Send`/`Sync`/`Linear` compose a
default from field-level facts today. This default must compile away entirely for types
that never customize it; construction for the overwhelming majority of structs should
cost exactly what a bare field-literal costs now. That is a *commitment*, matching
`nominal-types-as-branded-rows.md` §9's own unvalidated zero-cost claim for the
representation generally — not a new promise, the same one recurring here.

---

## 2. Canonical construction: all construction is `Self::construct(row)`

Once RFC-0100 lands, `Type { field: value }` struct literals no longer exist as a
separate surface form — "`Type(args)` call-shaped syntax **replaces**
`Type { field: value }` struct literals at construction sites," in that RFC's own words.
Under this RFC, `SortedPair(3, 1)` desugars to `SortedPair::construct(.{ small: 3, big: 1
})` — fresh construction and post-narrowing reconstruction (§3) become the *same*
operation, not two mechanisms that happen to need the same validation.

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

## 5. Fallibility — the sharpest open problem in this RFC

`SortedPair::construct` above is **infallible and self-healing** — it never rejects, only
reorders. Not every invariant can be repaired that way. A `NonEmptyList<T>` cannot
manufacture an element out of nothing if its row completes empty; its invariant must be
able to *reject*, not just normalize.

If `construct()` needs a fallible signature (`-> Perhaps<Self>` or similar) to support
that, §3's automatic firing runs into a real problem: **an ordinary field assignment
looks syntactically infallible.** `p.small = 999_999` reads as plain mutation; under this
RFC it may need to reject the resulting value. What happens then is not settled here.
Three candidates, none adopted:

- **(a) Only infallible `Construct` impls participate in automatic row-completion.** A
  type whose invariant can genuinely reject opts out of implicit narrow/rewiden
  entirely — its values cannot be narrowed at all, or reconstruction requires new,
  explicit, fallible syntax rather than an ordinary assignment.
- **(b) `construct()` stays infallible by convention; genuine rejection lives only in
  explicit surface constructors** (`new`, returning `Perhaps<Self>`), called at
  construction time only, never automatically. This weakens what "canonical" can promise
  for genuinely-rejecting invariants — the type-level guarantee stops being universal.
- **(c) Let `construct()` panic on failure**, treating it as infallible at the type level
  even though the internal check can fail — the same shape as `unwrap()` or array
  indexing elsewhere in the language. Makes an ordinary-looking assignment able to panic,
  a real ergonomic surprise worth weighing against the alternative of silently allowing
  the bypass.

This is judged the single most consequential open question this RFC leaves — see Open
Questions §1.

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

1. **Fallibility (§5) — the most consequential open question here.** No candidate among
   (a)/(b)/(c) is adopted. The answer changes what "canonical construction" can actually
   guarantee for invariants that must reject rather than normalize.
2. **Does this RFC need its own literal-banning rule independent of RFC-0100** (§2), given
   RFC-0100's own status is currently uncertain?
3. **What derives `Construct`'s default implementation, mechanically?** Composition-based
   auto-derivation (RFC-0096's pattern) is structurally a closed, compiler-intrinsic list
   of exactly three aspects (RFC-0096 §1) and does not obviously extend to a
   user-declarable aspect with a synthesized default; RFC-0093's comptime-derive
   mechanism is a closer fit but is itself `0-draft`. Not resolved here.
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

---

## References

- `reports/substructural-types/nominal-types-as-branded-rows.md` — §6 and Open Question
  1, the problem this RFC is the proposed (partial) answer to
- `internal/rfcs/1-under-review/rfc-0090-structural-records.md` §5 (field-composition
  auto-derivation), §8 (`ToRecord`/`FromRecord`, the `SortedPair` example, open question
  10 in its original, narrower scope)
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
