---
id: rfc-0089
title: "Linear Types"
date: '2026-07-09'
status: draft
target:
---

> **New RFC, split out 2026-07-09** from `reports/substructural-types/linear-types.md`
> (a living design report) as part of decomposing an oversized RFC-0012 into smaller,
> independently reviewable pieces. Also resolves a lineage gap: RFC-0024 (Linear Types)
> was superseded by RFC-0028 (Memory and Reference Model), and RFC-0028 was refused —
> its own note says the foundation layer (linear types, owning pointers) "stands and
> may be implemented," but that content was never re-homed in an active RFC. This RFC
> is that re-homing, using the current, more developed design from `linear-types.md`
> rather than reviving RFC-0024's `linear`-keyword-only, `@T` read-reference form.
> Depends on RFC-0071 (Ownership and Move Semantics, accepted), RFC-0080 (Standard
> Library Aspects, for the auto-impl pattern), RFC-0081 (Negative Impls), and RFC-0072
> (Negative Bounds). No dependency on comptime derive (RFC-0092/0093).
>
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
> RFC now depends on RFC-0090 (specifically its `record` type-former and tier 2, not
> tier 3 or RFC-0091's fuller automatic-downgrade extension) for the partial-
> consumption floor — the "no dependency on structural records" claim above no longer
> holds for that specific case, though the `Linear` aspect, lattice, and keyword sugar
> (§1-2, §4-5) remain fully independent of RFC-0090.

## Summary

Adds an opt-in `Linear` aspect: a value whose type is `Linear` must be consumed exactly
once — not silently dropped, not used twice. This sits on top of RFC-0071's existing
affine-by-default model rather than replacing it: affine already means "at most once, no
duplication"; `Linear` narrows that to "at least once too," ruling out silent drop.
Linearity is checked statically, no runtime overhead. Partial consumption of a struct
with mixed multiplicities (some `Linear` fields, some not) is not supported directly on
plain structs; `ToRecord` (RFC-0090) is the canonical mechanism instead — convert
explicitly, then move fields out of the resulting record, whose type already narrows to
reflect what remains. This is sufficient to meet RFC-0063 §9 item 5's deadline, using
RFC-0090's `record` type-former and tier 2 rather than a bespoke mechanism invented for
Linear specifically.

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
directly rather than being a bespoke case. **No `@derive(Linear)` annotation is needed
or meaningful** — this is category 1 (auto-trait structural composition), not category 2
(derive-as-codegen); it should never appear in a derivable-aspects list alongside
`Clone`/`Eq`/`Display` (RFC-0093 §"Derivable Aspects" corrects an earlier draft's error
on exactly this point). `impl !Linear for X {}` (RFC-0081) is the escape hatch for a
type that would otherwise structurally qualify but shouldn't.

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
impl Linear for Receipt {}          // explicit, forces it
linear struct Receipt { id: i64 }   // proposed sugar for exactly the line above
```

The keyword should stay struct-only, never extended to the `record` type-former
(RFC-0090) — records have no declaration site to attach it to, and forcing a
structurally-plain row to be linear "by fiat" undermines the premise that a record is
*just* its row.

**`Affine` needs no aspect of its own.** It's definitionally "not `Copy` and not
`Linear`" — `T: !Copy + !Linear` (RFC-0072's already-accepted mixed positive/negative
bound form) already says it. RFC-0039 (`aspect` Alias Syntax, draft) is the vehicle to
name it without writing the compound bound at every call site:

```metel
aspect Affine = !Copy + !Linear
```

Symmetrically to `linear struct`, a struct-only `affine struct` keyword would desugar
to a *locking pair of negative impls* — `impl !Copy for X {} impl !Linear for X {}` —
not a positive capability grant, since affine is an absence, not an addition. That pair
is more than documentation: RFC-0081's negative impls override any later conflicting
impl via ordinary coherence, so `affine struct Handle { fd: i64 }` is a real, checked
commitment that nothing elsewhere in the codebase can later add `impl Copy for Handle`
and silently change what moving a `Handle` means.

---

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
because that narrowing is already part of what makes RFC-0090's `record` type-former a
type-former at all (§2-3 there), not a new mechanism invented for this case:

```metel
@derive(ToRecord, FromRecord)
struct File { fd: i64, path: String }

fun close(f: File) -> String {
    let r = f.to_record();       // record { fd: i64, path: String }
    sys_close(r.fd);
    let path = move r.path;      // r narrows to record { fd: i64 } — but `fd`'s
                                  // obligation was already satisfied by sys_close
                                  // above; nothing further needs to happen to it
    path
}
```

Explicit, no per-binding state tracking beyond what RFC-0090's records already need for
their own sake, no new row-unification algorithm invented for Linear specifically.
**This is what satisfies RFC-0063 §9 item 5's deadline** — via this RFC's `Linear`
aspect and lattice (§1-2) plus RFC-0090's `record` type-former and tier 2
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

---

## Relationship to the tracked deadline

RFC-0063 §9 item 5 requires partial consumption to be resolved before RFC-0071/RFC-0067
implementation begins (Phase 3 steps 1–2). §3 is what satisfies that deadline — this
RFC's `Linear` aspect and lattice (§1-2) together with RFC-0090's `record` type-former
and tier 2 (`ToRecord`/`FromRecord`). This is a real dependency on RFC-0090 that an
earlier draft of this RFC did not have; RFC-0091's fuller automatic-downgrade extension
and its open aliasing question remain explicitly not required for the deadline.

---

## References

- RFC-0071 (Ownership and Move Semantics, accepted) — affine-by-default foundation this
  RFC builds on
- RFC-0080 (Standard Library Aspects) — the auto-impl pattern `Linear` reuses (§2),
  substituting `Linear` for `Send`
- RFC-0081 (Negative Impls) — `impl !Linear for X {}` opt-out
- RFC-0072 (Negative Bounds) — `T: !Copy + !Linear` compound bound form (§2.1)
- RFC-0039 (`aspect` Alias Syntax, draft) — vehicle for the `Affine` alias (§2.1)
- RFC-0049 (Linear Function Type System, draft) — documents the generic-`drop`-discharges-
  linearity hazard this RFC's `drop<T: !Linear>` avoids
- RFC-0063 (Allocator Handles, under review) — §9 item 5's deadline this RFC's §3
  satisfies, together with RFC-0090
- RFC-0090 (Structural Records — Rows and Tiers) — the `record` type-former and tier 2
  (`ToRecord`/`FromRecord`) §3 depends on as the canonical partial-consumption
  mechanism
- RFC-0024 (Linear Types, superseded) — prior exploration; superseded by RFC-0028
- RFC-0028 (Memory and Reference Model, refused) — its foundation-layer content is what
  this RFC re-homes, using the more developed design from `linear-types.md` rather than
  RFC-0024's original form
- `reports/substructural-types/linear-types.md` — the living design report this RFC is
  extracted from
- RFC-0091 (Linear Records, draft) — the record-based fuller extension of §3's partial
  consumption, depends on this RFC
- Prior art: `archive/per-field-multiplicities.md` — the multiplicity lattice's
  theoretical foundation (Atkey 2018, Idris 2, Linear Haskell)

---

## Decision

**Outcome:** *(pending)*
**Target:** unspecified; §3's floor is required before RFC-0071/RFC-0067 Phase 3 begins
per RFC-0063 §9 item 5.

*(Decision rationale goes here when the RFC is evaluated.)*
