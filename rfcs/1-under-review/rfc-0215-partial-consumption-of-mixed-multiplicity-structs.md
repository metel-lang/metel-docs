---
id: rfc-0215
title: "Partial Consumption of Mixed-Multiplicity Structs"
date: '2026-11-05'
status: under-review
updated: '2026-11-05'
tracking: 'https://github.com/metel-lang/metel-core/issues/1822'
---

> **Split from RFC-0089 on 2026-11-05.** RFC-0089 (Linear Types) carried two things: the multiplicity lattice,
> the `Linear` aspect and the class keywords (its sections 1 to 2.1), and the mechanism for partially
> consuming a struct that mixes linear and non-linear fields (its sections 3 to 5). The first half became a
> design-level dependency of the Copy and Clone settlement (RFC-0206); the second half is coupled to
> RFC-0090/0091 and to the deadline of RFC-0063 section 9 item 5, so it moves here and the first half can be
> accepted on its own. **The sections keep their RFC-0089 numbers (3, 3.1, 4, 5)** so that citations such as
> "RFC-0089 section 3.1" stay valid. Nothing here is decided.

> **Status — draft (2026-11-05).** Moved text; not yet re-reviewed as its own RFC.

> **Status — under review (2026-11-05).** Split from RFC-0089; carries the partial-consumption text that was already under review

## Summary

Partial consumption of a struct with mixed multiplicities (some `Linear` fields, some not) is not supported
directly on plain structs; `ToRecord` (RFC-0090) is the canonical mechanism instead: convert explicitly, then move
fields out of the resulting record, whose type already narrows to reflect what remains. A struct forced `Linear`
by fiat needs the conversion to carry its brand (section 3.1), and `NonLinear<T>` names the projection that drops
the linear fields (section 4). This is the floor RFC-0063 section 9 item 5 requires before the RFC-0071/RFC-0067
implementation begins. It depends on the lattice and the `Linear` aspect of RFC-0089 sections 1 to 2.1.

---

> **§3 is deferred, 2026-07-24, and this is the substance of the deferral rather than a
> filing change.** The section below routes partial consumption through RFC-0090's
> `ToRecord`. That coupling was introduced by this RFC's own same-day revision on
> 2026-07-09 — §3 originally specified "Option B", ordinary field access on a nominal
> struct — and it was a mistake: per-field multiplicity was meant to wait until records
> were implemented, not to be built on top of a records design that was itself still
> under review.
>
> That is also the answer to `OBJECTIVES.md` Trigger 6, which asked whether the
> RFC-0089↔RFC-0090 dependency was genuine and observed that *"neither RFC states the
> conflict."* Neither states it because neither chose it.
>
> **What this means concretely:** §3 below is **not** the specified floor. It is the
> record-based mechanism as drafted, kept intact so nothing is lost, to be revisited once
> RFC-0116–0121 are implemented and there is a real records substrate to build against.
> Whether the floor then routes through conversions (as below), through Option B after
> all, or through something the implemented records suggest, is genuinely open again.
>
> **§1–2 (the `Linear` aspect and the multiplicity lattice) and §4–5 (keyword sugar) are
> unaffected and remain fully independent of the records cluster** — this RFC's own
> 2026-07-09 note already said so. They are the half that could have been accepted all
> along, and were blocked only by being in the same document as §3.

## 3. Partial consumption: no bespoke mechanism on plain structs — `ToRecord` is canonical

When a struct with mixed multiplicities has its `1` fields consumed, what happens to
the rest? Two mechanisms were considered:

**Ordinary field access directly off a nominal struct** (`f.fd`, moving one field out
while the rest of `f` stays live) is **not supported as a first implementation.**
Building this would mean extending RFC-0071 §7's affine partial-move tracking to
reason specifically about linear fields, on plain nominal structs, as its own bespoke
mechanism — real design and implementation work that a second, later mechanism (below)
would duplicate anyway.

**The canonical mechanism: convert to a record, move fields out of that.** A struct
that wants any of its fields partially consumed derives `ToRecord`/`FromRecord`
(RFC-0090), converts explicitly via `.to_record()`, and moves fields out of the
resulting record value — whose type narrows to reflect exactly which fields remain,
because that narrowing is already part of what makes RFC-0090's `{ … }` type-former a
type-former at all (§2-3 there), not a new mechanism invented for this case:

```metel
#derive(ToRecord, FromRecord)
struct File { fd: i64, path: String }

fun close(f: File) -> String {
    let r = f.to_record();       // { fd: i64, path: String }
    sys_close(r.fd);
    let path = r.path;           // moving a non-Copy field out is implicit, no `move`
                                  // keyword exists (verified directly against
                                  // grammar.pest); r narrows to { fd: i64 } — but
                                  // `fd`'s obligation was already satisfied by
                                  // sys_close above; nothing further needs to happen
                                  // to it
    path
}
```

Explicit, no per-binding state tracking beyond what RFC-0090's records already need for
their own sake, no new row-unification algorithm invented for Linear specifically.
**This is what satisfies RFC-0063 §9 item 5's deadline** — via this RFC's `Linear`
aspect and lattice (§1-2) plus RFC-0090's `{ … }` type-former and tier 2
(`ToRecord`/`FromRecord`), not RFC-0091's fuller automatic-downgrade extension or its
still-open aliasing question, neither of which is required for the deadline.

**The real cost, stated plainly:** a `Linear`-bearing struct that does not derive
`ToRecord`/`FromRecord` cannot have its fields partially consumed at all — it can only
be consumed as a whole (equivalent to what an "Option A, drop/consume everything
atomically" choice would have given, had this RFC specified one). This is a real
behavior change from an earlier draft of this RFC, which allowed partial field access
with no extra derive required. It is also consistent with this whole design cluster's
tier philosophy (RFC-0090 §8): no capability is ambient; partial consumption is an
explicit opt-in, not something every struct gets for free.

A more expressive mechanism — automatic downgrade, where the binding's type changes at
the point of consumption with no explicit `.to_record()` call needed — is specified in
RFC-0091 (Linear Records) as an additive extension on top of this floor, not a
prerequisite for it.

### 3.1 Fiat-linear structs: `ToRecord` must preserve the origin brand, not produce a bare row

§2.1's fiat-linearity (`extend Receipt: Linear {}`, forcing a struct `Linear` with no
field of its own requiring exactly-once handling) creates a gap the rest of §3 doesn't
cover. `.to_record()`'s output is `Linear` only via RFC-0090 §5's structural join over
the row — recomputed from field types alone. For a struct whose `Linear` status is *not*
explained by any field (the entire point of fiat), the produced record's row contains
nothing that would make the join rule return `Linear`, and the fiat assertion is silently
lost: `receipt.to_record()` followed by letting the result fall out of scope would
typecheck today, discharging a "must consume exactly once" obligation with no
consumption having occurred.

**Why a synthetic marker field is the wrong fix.** The natural first idea — add a hidden,
zero-sized field whose own type is genuinely `Linear`, so the ordinary join rule produces
the right answer with no new mechanism — treats a nominal fact (this bundle, not any
particular field, must be handled once) as if it were structural content. It works
mechanically, but requires the row/`HasField` machinery to support fields invisible even
to the declaring module's own field access, and misattributes *why* the record is linear
to a field that was never really there.

**Resolution: a brand-carrying `ToRecord`, for this case only.** Fiat linearity is a
nominal-identity fact, and brands (RFC-0074/RFC-0076, `brand-kind-unification.md`) are
this design's existing mechanism for nominal facts that must survive a structural
conversion — a brand cannot itself carry the "consume exactly once" obligation (it sits
at multiplicity `0`, outside the lattice entirely, per §1; something erased was never a
runtime value to consume), but it can preserve *which specific origin* a converted value
came from, which is the actual missing ingredient. For a struct whose `Linear` status is
not fully explained by its own row, `ToRecord`'s derive produces a record that carries
the source's brand rather than RFC-0090 §8's ordinarily-bare row: `{ id: i64 } @
'receipt-origin` instead of a plain `{ id: i64 }`. The derive (RFC-0093's `emit`)
then generates one ordinary, explicit `impl Linear for { id: i64 } @
'receipt-origin {}` against that exact branded shape — no new coherence primitive, no
dynamic brand-to-aspect lookup: an explicit impl targeting one specific nominal/branded
type is completely ordinary machinery, and the brand is what makes the target specific
enough that unrelated same-shaped records (which carry no such brand, or a different one)
are correctly unaffected.

This composes with RFC-0090 §9 / RFC-0091 §2.2's existing `(row, brand)` residual idea
rather than introducing a fourth mechanism alongside it — see RFC-0090 §8 for the
corresponding amendment to the tier-2 conversion itself.

**Scope, stated precisely: this only applies when `Linear` isn't row-derivable.** A
struct that is `Linear` purely because a field is (the ordinary case throughout the rest
of this RFC) converts to a fully bare, brand-less record exactly as RFC-0090 §8 already
specifies — the join rule alone already gets the right answer, and attaching a brand
there would be spending machinery nothing asked for, the exact thing RFC-0090's tier
discipline (§8) is built to avoid.

---

## 4. `NonLinear<T>`: a standalone, nameable projection

A type-level operator — `NonLinear<T>`, computed by filtering `T`'s own closed, known
field list to exclude anything at multiplicity `1`:

```metel
struct Session { token: LinearToken, name: String, retries: i64 }

fun archive(entry: NonLinear<Session>) { ... }   // = { name: String, retries: i64 }
```

Needs only a closed, already-known field list — no row-kind, no unification
algorithm — so it needs nothing from RFC-0090 either, and is usable independent of
whether RFC-0090's `<row R>` open generics are ever pursued. Once RFC-0090's
`HasField`/`Lacks` predicates exist, `NonLinear<T>` is their natural companion in the
same family: `HasField` is a predicate ("does this row have field X"), `NonLinear<T>`
is a function on rows ("this row, minus whichever fields are multiplicity-`1`").

---

## 5. Two-struct vs. mixed-multiplicity: the same design, different explicitness

Is the "address + capability" pattern —

```metel
struct FileHandle { fd: i64 }          // multiplicity ω (or affine) — freely copyable
linear struct FileCap { fd: i64 }      // multiplicity 1 — must be consumed
```

— a different design from a single mixed-multiplicity struct, or the same design at
different explicitness? **The same design.** Under Option B (§3), consuming a mixed
struct and extracting its non-linear fields produces exactly what the two-struct
version would have given you by holding `FileHandle` independently while consuming
`FileCap`. They differ only in whether the split is manifest in the type definitions or
deferred to the point of consumption:

| | Two-struct | Mixed-multiplicity struct |
|---|---|---|
| Freely alias the handle | Yes — its own type | Yes — via `&Struct` borrows |
| Recover the handle after consuming the cap | Yes — lives on independently | Yes — via residual extraction |
| Typestate | Separate type param per struct | One type param, one struct |
| Syntax weight | Two definitions, two threaded values | One definition, one value |

Two-struct is preferable when the address and the capability genuinely have independent
lifetimes and travel to different parts of a program separately. Mixed-multiplicity is
preferable when they always travel together until the terminal action. Both should
remain available — this is a style choice given the same underlying model, not a
decision between two different models.


---

## Open Questions

1. Ship the four-point lattice (§1) as the documented model, or keep presenting
   `Linear` as a flat per-struct property with the lattice as internal justification
   only — affects how this gets written up if formalized, not the mechanics. Leaning
   toward presenting the lattice explicitly, since it's what actually explains the
   composition and reversion rules rather than asserting them.
2. Struct-only `linear`/`affine` keyword sugar (§2.1) — leaning yes, not ratified.
3. `NonLinear<T>`'s exact surface syntax (a type-level function, a special form,
   something else) — unresolved; only the shape of what it computes is settled.
4. Multiplicity polymorphism (`Guarded<T, Cap>` generic over a field's multiplicity) —
   noted as a real, later extension; not attempted here.
5. ~~Does `Linear` interact with RFC-0071 §7's affine partial-move side-table
   directly, or stay a separate check layered on top~~ — **Resolved 2026-07-09, §3:**
   no. `Linear`-bearing structs do not support direct partial moves at all; the
   canonical path is conversion to a record (RFC-0090) first, an entirely separate
   mechanism from RFC-0071's affine side-table. No extension of that side-table for
   linear fields is needed.
6. **New, 2026-07-10.** The brand-carrying `ToRecord` for fiat-linear structs (§3.1) is a
   candidate, not a proven mechanism — no soundness argument is written down, only the
   shape of one, matching the standard this cluster already holds RFC-0091's Option C to.
   Needs: (a) confirmation that a derive-emitted impl against one specific branded record
   shape is genuinely unreachable by any other code (i.e., the brand is unforgeable from
   outside the derive — plausible given brand rigidity/freshness, RFC-0076, but not
   proven here); and (b) a decision on whether `FromRecord` for such a struct needs to
   check the brand matches before reconstructing, or whether the row alone suffices once
   the value is back in nominal form.


---

## Relationship to the tracked deadline

RFC-0063 §9 item 5 requires partial consumption to be resolved before RFC-0071/RFC-0067
implementation begins (Phase 3 steps 1–2). §3 is what satisfies that deadline — this
RFC's `Linear` aspect and lattice (§1-2) together with RFC-0090's `{ … }` type-former
and tier 2 (`ToRecord`/`FromRecord`). This is a real dependency on RFC-0090 that an
earlier draft of this RFC did not have; RFC-0091's fuller automatic-downgrade extension
and its open aliasing question remain explicitly not required for the deadline.


---

## References

- RFC-0071 (Ownership and Move Semantics, integrated 2026-07-24, target v0.12.0) —
  affine-by-default foundation this RFC builds on
- RFC-0080 (Standard Library Aspects) — the auto-impl pattern `Linear` reuses (§2),
  substituting `Linear` for `Send`
- RFC-0096 (Auto-Impl Aspects, under review) — formalizes that pattern once, generically,
  rather than each auto-impl aspect (`Send`/`Sync`/`Linear`) restating it
- RFC-0081 (Negative Impls) — `extend X: !Linear;` opt-out
- RFC-0072 (Negative Bounds) — `T: !Copy + !Linear` compound bound form (§2.1)
- RFC-0039 (`aspect` Alias Syntax, `1-under-review`) — vehicle for the `Affine` alias (§2.1)
- RFC-0049 (Linear Function Type System, superseded by RFC-0194) — documents the generic-`drop`-discharges-
  linearity hazard this RFC's `drop<T: !Linear>` avoids
- RFC-0063 (Allocator Handles, accepted) — §9 item 5's deadline this RFC's §3
  satisfies, together with RFC-0090
- RFC-0090 (Structural Records — Rows and Tiers) — the `{ … }` type-former and tier 2
  (`ToRecord`/`FromRecord`) §3 depends on as the canonical partial-consumption
  mechanism; §8 there carries the corresponding amendment for §3.1's brand-carrying
  conversion
- RFC-0074 (Shared Ownership), RFC-0076 (Rc Brands) — brand rigidity/freshness
  properties §3.1's derive-emitted impl depends on being unforgeable from outside
- `brand-kind-unification.md` — the erased/value-channel distinction (§4 there) that
  separates "a brand carries the obligation" (no) from "a brand preserves identity so
  the obligation can still be checked" (yes), the distinction §3.1 turns on
- RFC-0024 (Linear Types, superseded) — prior exploration; superseded by RFC-0028
- RFC-0028 (Memory and Reference Model, refused) — its foundation-layer content is what
  this RFC re-homes, using the more developed design from `linear-types.md` rather than
  RFC-0024's original form
- `reports/substructural-types/linear-types.md` — the living design report this RFC is
  extracted from
- RFC-0091 (Linear Records) — the record-based fuller extension of §3's partial
  consumption, depends on this RFC
- Prior art: `archive/per-field-multiplicities.md` — the multiplicity lattice's
  theoretical foundation (Atkey 2018, Idris 2, Linear Haskell)


---

## Decision

**Outcome:** *(pending)*
**Target:** unspecified; section 3's floor is required before RFC-0071/RFC-0067 Phase 3 begins per RFC-0063
section 9 item 5.
