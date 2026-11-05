---
id: rfc-0089
title: "Linear Types"
date: '2026-07-09'
status: under-review
updated: '2026-09-03'
tracking: 'https://github.com/metel-lang/metel-core/issues/953'
---

> **New RFC, split out 2026-07-09** from `reports/substructural-types/linear-types.md`
> (a living design report) as part of decomposing an oversized RFC-0012 into smaller,
> independently reviewable pieces. Also resolves a lineage gap: RFC-0024 (Linear Types)
> was superseded by RFC-0028 (Memory and Reference Model), and RFC-0028 was refused —
> its own note says the foundation layer (linear types, owning pointers) "stands and
> may be implemented," but that content was never re-homed in an active RFC. This RFC
> is that re-homing, using the current, more developed design from `linear-types.md`
> rather than reviving RFC-0024's `linear`-keyword-only, `@T` read-reference form.
> Depends on RFC-0071 (Ownership and Move Semantics, integrated), RFC-0080 (Standard
> Library Aspects, for the auto-impl pattern), RFC-0081 (Negative Impls), and RFC-0072
> (Negative Bounds). No dependency on comptime derive (RFC-0092/0093).
>
> **Split 2026-11-05.** Sections 3 to 5 (partial consumption, the brand-carrying conversion, `NonLinear<T>`, the
> two-struct comparison) are RFC-0215; the notes below that mention them are the history of that text.

> **Revised 2026-07-09, later the same day.** §3 originally specified a bespoke
> "Option B" partial-consumption mechanism — ordinary field access directly off a
> nominal struct, with no record involved, requiring its own extension to RFC-0071
> §7's affine partial-move tracking for linear fields specifically. Decided against as
> a first implementation: `ToRecord` (RFC-0090) is the canonical mechanism instead —
> convert via `.to_record()`, move fields out of the resulting record value, where
> ordinary record field-narrowing (RFC-0090 §2-3) already determines the residual
> type. This removes a second, redundant partial-move mechanism that would have had to
> be built and maintained specifically for nominal structs, when records need
> equivalent field-narrowing semantics anyway. The real cost, stated plainly: a
> `Linear`-bearing struct now needs to additionally derive `ToRecord`/`FromRecord`
> before any of its fields can be partially consumed at all — plain structs with no
> such derive can only be consumed as a whole. §3 is rewritten accordingly, and this
> RFC now depends on RFC-0090 (specifically its `{ … }` type-former and tier 2, not
> tier 3 or RFC-0091's fuller automatic-downgrade extension) for the partial-
> consumption floor — the "no dependency on structural records" claim above no longer
> holds for that specific case, though the `Linear` aspect, lattice, and keyword sugar
> (§1-2, §4-5) remain fully independent of RFC-0090.
>
> **Revised 2026-07-10.** §3.1 added: fiat-linearity (§2.1) has a gap at the `ToRecord`
> boundary — a record's `Linear` status is always recomputed from its row alone (RFC-0090
> §5), so a struct forced `Linear` by fiat rather than by any field's own multiplicity
> silently loses that status on conversion. Resolved using a brand, not a synthetic field:
> the derived conversion for such a struct carries the source's brand, and the derive
> emits one ordinary explicit `impl Linear` against that specific branded shape.
> Corresponding amendment in RFC-0090 §8.
>
> **Revised 2026-07-24 — mechanical syntax sweep, no semantic change.** RFC-0090 dropped
> the `record` keyword from the anonymous type-former, so every `record { … }` here is now
> `{ … }`. This touches §3.1's branded-shape notation most visibly: the fiat-linear
> conversion's output is now written `{ id: i64 } @ 'receipt-origin` rather than
> `record { id: i64 } @ 'receipt-origin`, and the emitted impl targets
> `extend { id: i64 }: Linear @ 'receipt-origin`. **The brand is doing more visual work
> now that the keyword is gone** — `{ id: i64 }` and `{ id: i64 } @ 'receipt-origin` differ
> only by the tag, which is exactly §3.1's point (unrelated same-shaped records carry no
> such brand and so do not match the impl), but it is less obvious at a glance than it was.
> No change to the mechanism.

> **Status — under review (2026-07-21).** Reviewing the records/views substrate cluster together, per OBJECTIVES.md Priority 1 (reordered 2026-07-22). The cluster's first deliverable is the record/row semantics themselves -- RFC-0090 SS3 step 1's closed `{ … }` type-former plus `HasField` -- not the `ToRecord`/`FromRecord` conversions the blog names, which are tier 2 of RFC-0090 SS8 and convert into a type-former that must exist first. Thorough draft with a substantiated primary proposal; open questions remain, chiefly the RFC-0089/RFC-0090 dependency direction that Trigger 6 tracks.

> **Status — draft (2026-07-24).** Deferred 2026-07-24: per-field multiplicity waits until records are implemented. The RFC-0090 coupling was introduced by accident (RFC-0089's 2026-07-09 same-day revision rewrote its floor from Option B to ToRecord), which is why Trigger 6 could observe that neither RFC states the conflict. Returned to draft so the records cluster is not gated on it and the review backlog reflects what is actually reviewable.

> **Status — under review (2026-09-03).** Re-promoted 2026-09-03: the 2026-07-24 deferral condition (wait until records ship) is substantially met -- RFC-0116/0117/0118 implemented/integrated, RFC-0120 accepted; RFC-0119 (the ToRecord floor sec3 depends on) still under review but milestoned v0.13.1, ahead of this RFC's own v0.21.1 target. Milestoned v0.21.1 as a third design-settlement lane alongside RFC-0140/RFC-0003, not folded into v0.20.0's in-flight substrate milestone. metel-core#953.

## Summary

Adds an opt-in `Linear` aspect: a value whose type is `Linear` must be consumed exactly
once — not silently dropped, not used twice. This sits on top of RFC-0071's existing
affine-by-default model rather than replacing it: affine already means "at most once, no
duplication"; `Linear` narrows that to "at least once too," ruling out silent drop.
Linearity is checked statically, no runtime overhead. Partial consumption of a struct
with mixed multiplicities (some `Linear` fields, some not) moved to RFC-0215 on 2026-11-05; this RFC is the
lattice, the aspect and the class keywords (`copy`, `affine`, `linear`) that the Copy and Clone settlement
(RFC-0206) depends on.

---

## Motivation

RFC-0071 makes affine ownership — move-by-default, at most once, no implicit copy — the
default for every field. That default has no way to express "this value's consumption
is mandatory," the property closing/freeing/releasing patterns actually need: a file
handle, a lock guard, a one-shot capability token. Today, that has to be enforced by
convention or a runtime check (a "was this closed?" flag, checked at drop time). `Linear`
makes it a compile-time-checked property instead — the type itself refuses to compile if
a value goes unused.

---

## 1. The multiplicity lattice

Quantitative type theory (Atkey 2018, Idris 2, Linear Haskell) typically uses a
three-point lattice — 0 (erased) / 1 (linear) / ω (unrestricted) — assuming an
ω-default background where ordinary bindings are already freely copyable. Metel inverts
this: RFC-0071 makes affine the default for every field, and ω-like unrestricted
behavior is something opted into via `Copy`. A three-point lattice has no point for
Metel's actual default. The lattice needs four:

```
0      — erased: a compile-time-only marker (a brand, a phantom state tag);
         not present as a runtime value at all
1      — linear: exactly once; no weakening (can't silently drop), no contraction
         (can't duplicate); must be explicitly consumed
affine — at most once: weakening allowed (may drop; Drop::drop runs), no
         contraction (can't duplicate); THE DEFAULT for ordinary fields (RFC-0071)
ω      — unrestricted: weakening and contraction both allowed; Copy fields
```

Ordered by how much the discipline permits: `1` is strictly more restrictive than
`affine` (affine additionally allows silent dropping); `affine` is strictly more
restrictive than `ω` (ω additionally allows duplication). `0` sits outside this
ordering — it's not "fewer uses," it's "not a runtime value," and behaves the way
`PhantomBrand` (RFC-0074) and phantom type-state parameters already do.

**A struct's overall discipline is the join (least upper bound, toward more permissive)
of its fields' multiplicities.** A struct with any `1` field is linear overall; a
struct with only `affine`/`ω` fields (no `1`) is affine overall; a struct with only `ω`
fields may (if it opts in) be `Copy`. `Drop` is compatible with `affine` and `1` but not
`ω` (RFC-0071 §4's existing `Copy`/`Drop` exclusion is a special case of this general
rule, not a separate one).

---

## 2. `Linear` as an aspect

```metel
aspect Linear { }
```

A marker aspect, structurally identical in form to `Send` (RFC-0080). Auto-derived, not
opt-in: a struct containing a multiplicity-`1` field is `Linear` automatically, per
RFC-0080 §3.2's auto-impl rule (the same structural-composition mechanism that grants
`Send`/`Sync`, substituting `Linear` for `Send`), matching the lattice's join rule
directly rather than being a bespoke case — RFC-0096 (2026-07-11) is where that
mechanism is now formalized once, generically, since this citation and RFC-0080 §3.2's
own text were the two places it was previously only informally assumed. **No
`#derive(Linear)` annotation is needed or meaningful** — this is category 1 (auto-trait
structural composition), not category 2 (derive-as-codegen); it should never appear in
a derivable-aspects list alongside `Clone`/`Eq`/`Display` (RFC-0093 §"Derivable Aspects"
corrects an earlier draft's error on exactly this point). `extend X: !Linear;`
(RFC-0081) is the escape hatch for a type that would otherwise structurally qualify but
shouldn't.

**Mutually exclusive with `Copy`** (`ω` and `1` can't coexist in the same field) **and
with `Drop`.** `Drop`'s triggers — implicit scope-end, the generic `drop(x)` free
function — have no legitimate firing point for a value that can never legally reach
scope-end unconsumed, and `drop`'s signature should exclude `Linear` via `T: !Linear`
(mirroring RFC-0072's negative-bound mechanism), specifically to avoid a documented
hazard (RFC-0049): a generic `drop` that discharges a linearity obligation without
running real cleanup ("`drop(f)` appears to work but leaves captured values dangling").
A linear type's teardown logic lives in an ordinary, author-named consuming method
instead, called directly.

### 2.1 Surface syntax: aspect, keyword, or a mix

Every mechanism that needs `Linear` in a bound position (`drop<T: !Linear>`,
`HasField`/`Lacks` conditions in RFC-0090, residual recomposition in RFC-0091) needs
`Linear` to be usable as an aspect, not just a keyword. A bare keyword with no backing
aspect either collapses into aspect sugar or is a strictly weaker mechanism that can't
participate in the rest of this design. Aspect-plus-sugar wins on one real capability:
declaring a type linear *by fiat* when nothing about its fields structurally requires
it (a capability token wrapping a plain `i64`, say):

```metel
extend Receipt: Linear {}          // explicit, forces it
linear struct Receipt { id: i64 }   // proposed sugar for exactly the line above
```

The keyword should stay struct-only, never extended to the `{ … }` type-former
(RFC-0090) — records have no declaration site to attach it to, and forcing a
structurally-plain row to be linear "by fiat" undermines the premise that a record is
*just* its row.

**`Affine` needs no aspect of its own.** It's definitionally "not `Copy` and not
`Linear`" — `T: !Copy + !Linear` (RFC-0072's already-accepted mixed positive/negative
bound form) already says it. RFC-0039 (`aspect` Alias Syntax, `1-under-review`) is the vehicle to
name it without writing the compound bound at every call site:

```metel
aspect Affine = !Copy + !Linear
```

Symmetrically to `linear struct`, a struct-only `affine struct` keyword would desugar
to a *locking pair of negative impls* — `extend X: !Copy; extend X: !Linear;` —
not a positive capability grant, since affine is an absence, not an addition. That pair
is more than documentation: RFC-0081's negative impls override any later conflicting
impl via ordinary coherence, so `affine struct Handle { fd: i64 }` is a real, checked
commitment that nothing elsewhere in the codebase can later add `extend Handle: Copy`
and silently change what moving a `Handle` means.


> **Sections 3 to 5 moved to RFC-0215 on 2026-11-05.** Partial consumption through `ToRecord`, the brand-carrying
> conversion for fiat-linear structs (old section 3.1), `NonLinear<T>` and the two-struct comparison are in
> RFC-0215 (Partial Consumption of Mixed-Multiplicity Structs), which keeps their section numbers. This RFC is
> now the lattice (section 1), the `Linear` aspect and its exclusions (section 2) and the class keywords
> (section 2.1), which the Copy and Clone settlement (RFC-0206) depends on at the design level.

---

## Open Questions

1. Ship the four-point lattice (§1) as the documented model: **resolved 2026-11-05**, yes; the settlement of
   RFC-0206 is written against it.
2. Struct-and-enum `copy`/`affine`/`linear` keyword sugar (§2.1): **resolved 2026-11-05** in favour, for
   structs and enums, not the anonymous record type; the sugar is `copy struct P` = `struct P derives Copy`,
   `affine struct H` = the locking pair of negative impls, `linear struct T` = `extend T: Linear {}`. In v0.16.0
   `copy` and `affine` are implemented and `linear` is reserved ("Planned for").
3. *(Moved to RFC-0215.)* `NonLinear<T>`'s surface syntax.
4. Multiplicity polymorphism (`Guarded<T, Cap>` generic over a field's multiplicity) — noted as a real, later
   extension; not attempted here.
5. **The default for an unbounded type parameter with respect to `Linear`** (new 2026-11-05). This RFC did not
   decide it; `drop<T: !Linear>` suggested a bare `T` might be linear. The settlement of RFC-0206 takes: an
   unbounded `T` is affine (movable, droppable, not copyable), so existing generic code stays valid, and linear
   types cannot instantiate it until a suppression spelling exists, which arrives with the implementation of
   `linear`. To be ratified here.
6. *(Moved to RFC-0215.)* The brand-carrying `ToRecord` for fiat-linear structs.

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
**Target:** unspecified; the partial-consumption floor (now RFC-0215 §3) is required before RFC-0071/RFC-0067 Phase 3 begins
per RFC-0063 §9 item 5.

*(Decision rationale goes here when the RFC is evaluated.)*
