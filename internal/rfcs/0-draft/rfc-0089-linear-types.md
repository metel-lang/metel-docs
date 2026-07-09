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
> (Negative Bounds). No dependency on structural records (RFC-0090) or comptime derive
> (RFC-0092/0093) — the record-based extension of partial consumption is split out to
> RFC-0091 (Linear Records) specifically so this RFC stands on its own.

## Summary

Adds an opt-in `Linear` aspect: a value whose type is `Linear` must be consumed exactly
once — not silently dropped, not used twice. This sits on top of RFC-0071's existing
affine-by-default model rather than replacing it: affine already means "at most once, no
duplication"; `Linear` narrows that to "at least once too," ruling out silent drop.
Linearity is checked statically, no runtime overhead. Partial consumption of a struct
with mixed multiplicities (some `Linear` fields, some not) is resolved with an explicit,
non-record floor (Option B, below) sufficient to meet RFC-0063 §9 item 5's deadline
without any row/record machinery.

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

## 3. Partial consumption: the floor, without records

When a struct with mixed multiplicities has its `1` fields consumed, what happens to
the rest? Two options that need no row/record machinery at all:

**Option A — drop everything.** The struct is consumed atomically; `affine`/`ω` fields
are discarded alongside the `1` ones. Simplest, but the caller can never recover an
otherwise-unrestricted field after the terminal action. Not adopted as the floor — too
coarse for the common case of "release one resource, keep using the rest."

**Option B — explicit residual extraction, the adopted floor.** The consuming function
returns the non-linear fields as ordinary values; the compiler injects nothing
automatically:

```metel
fun close(f: File) -> i64 {
    sys_close(f.fd);
    f.fd   // fd survives; the linear field's obligation is satisfied by having been
           // reached at all
}
```

Unambiguous, no per-binding state tracking beyond ordinary move semantics, no row kind,
no row-unification algorithm. **This is what satisfies RFC-0063 §9 item 5's deadline on
its own** — sufficient for Phase 3 to proceed, with no dependency on RFC-0090 or
RFC-0091.

A third option — automatic downgrade, where the binding's type changes at the point of
consumption to reflect exactly which fields remain — is real and more expressive, but
it needs the row/record machinery from RFC-0090, and an aliasing question (what type
does a borrow taken before the downgrade have afterward) that took real design work to
answer. That option, and the aliasing question's answer, are specified in RFC-0091
(Linear Records) as an additive extension, not a prerequisite for this RFC's floor.

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
5. Does `Linear` interact with RFC-0071 §7's affine partial-move side-table directly, or
   stay a separate check layered on top — unresolved.

---

## Relationship to the tracked deadline

RFC-0063 §9 item 5 requires partial consumption to be resolved before RFC-0071/RFC-0067
implementation begins (Phase 3 steps 1–2). §3's Option B is what satisfies that
deadline, entirely within this RFC, with no dependency on RFC-0090 or RFC-0091.

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
  satisfies
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
