---
id: rfc-0117
title: "Row Narrowing"
date: '2026-07-24'
status: implemented
tracking: 'https://github.com/metel-lang/metel-core/issues/789'
target: v0.13.0
updated: '2026-09-03'
coverage:
  "1": { spec: "spec.ownership.narrowing.legality-1" }
  "2": { spec: "spec.ownership.narrowing.legality-2" }
  "3": { kind: untestable, reason: "Scope-boundary section: enumerates capabilities owned by other RFCs (widening -> RFC-0114, nested narrowing -> RFC-0150, borrowed narrowing -> RFC-0119/0109, per-field multiplicity -> RFC-0089/0091). No rule of its own to test." }
impl_tracking: 'https://github.com/metel-lang/metel-core/issues/789'
impl_status: implemented
---

> **Extracted from RFC-0090 on 2026-07-24** (superseded; see RFC-0116's header for why the
> split happened and what the six pieces are).
>
> **Depends on RFC-0116 (Anonymous Record Types) and on RFC-0071 (Ownership and Move
> Semantics).** RFC-0071 was `2-accepted` but **0% implemented** at the time this note
> was written — confirmed by direct grep of the interpreter for borrow/move-tracking
> infrastructure. That was a sequencing dependency on already-accepted work, not a
> ratification blocker on a draft, but it was the reason this is a separate RFC from
> RFC-0116 rather than bundled with it: the type-former was buildable and this was not.
> **Corrected 2026-08-27: RFC-0071 is now `3-integrated`, and partial-move tracking is
> real, tested code (`--move-check`, gated off by default) — verified directly, not
> "0% implemented" any longer.**

> **Status — under review (2026-08-23).** Committed to v0.13.0, tracking issue #789 filed 2026-08-22 -- real dependency-chain engagement, not a calendar promotion
>
> **Updated 2026-08-29 (pre-acceptance review).** Open Question 3 resolved: **this RFC
> covers flat narrowing only** — moving a whole field out, at any depth the field is
> reached, removes that one label. A record-typed field is moved as a **unit**. Narrowing
> a field *of* a record-typed field in place (`o.inner.a`, leaving `o : Outer.{ inner:
> Inner.{ b }, tag }`) needs a recursive residual type system — new type grammar for a
> branded row whose field type differs from the declaration, tuple residuals, and
> recursive `Drop` receiver shapes — none of which exist yet. That is **RFC-0150 (Nested
> Row Narrowing)**, targeted with RFC-0147/0148. RFC-0137 references corrected to
> `3-integrated`. All three open questions now resolved.

> **Status — accepted (2026-08-29).** Flat row narrowing: moving a field out narrows the value's type to the 2^N subset lattice, no row variables; path-sensitive via RFC-0071's existing move tracking. All three open questions resolved (OQ1/OQ2 via RFC-0137 §5, OQ3 by scoping to flat -- nested narrowing is RFC-0150). Pre-acceptance Codex review clean for the flat case.

> **Status — integrated (2026-08-29).** Flat row narrowing integrated into reference/spec/ownership.md#narrowing (legality-1/legality-2, co-origin with RFC-0137), blocked-exempt on metel-core#858 pending move-triggered narrowing. Nested narrowing is RFC-0150.

> **Status — implemented (2026-09-03), metel-core#789.** Anonymous-record row narrowing lands in v0.13.0, in both the inference and construction passes, reusing the `crate::flow_state::FlowState` machinery RFC-0137 slice 2 (#858) threaded through both for the struct case. A partial move of a non-`Copy` record field narrows the binding to the record type with that label gone; a whole-value use afterward is a plain `T0001` at type-check time (the ordinary record-shape mismatch — an anonymous record has no distinct residual-type marker the way a struct's brand gives one). A `Copy` field read by value does not narrow; an unresolved field type is held in the row until known (the field's `Copy`-ness is re-tested at each read, since a record literal's field types are inference variables until solved). `spec.ownership.narrowing.legality-1` / `legality-4`, `spec.ownership.partial-moves.which-constructs-support-partial-moves.legality-2` (rewritten — records now narrow). Nested narrowing is still RFC-0150; the residual-type ⇄ `--move-check` gap (a whole-value use of a narrowed binding) was shared with #858 and is closed by metel-core#950 — `--move-check` now accepts such a use.

> **Status — implemented (2026-09-03).**

## Summary

Moving a field out of a record narrows the record's type to exactly the fields that
remain. `{ fd: i64, path: String }` with `path` moved out becomes `{ fd: i64 }` — not a
partially-valid value, not an opaque "moved-from" marker, but an ordinary value of a
narrower record type.

No row variables and no unification are involved. For a closed record over *N* fields the
space of possible residuals is the subset lattice, bounded by 2^*N* and trivial at
realistic struct sizes.

**The same rule applies to a nominal struct's own row, not only an anonymous record's**
(RFC-0137, `3-integrated`) — see §1's own worked example.

---

## Motivation

Without narrowing, a record is a product type you can build and read but never partially
consume, and the natural pattern of "take one field out, keep using the rest" has no
expression. Rust's answer is to track partial moves as compiler-internal state that the
type does not reflect; the value's type stays `Foo` while the compiler separately
remembers which fields are gone.

Making the residual a **real type** rather than hidden state is what lets it be passed to
a function, returned, and named in a signature — which is the whole point of the
downstream features (RFC-0119's `to_record`/`from_record` round trip, and eventually
per-field multiplicity, which is deferred until records are implemented).

---

## 1. The rule

```metel
let r := { fd = 3, path = "/tmp/x" };   // { fd: i64, path: String }
let p := r.path;                         // r : { fd: i64 } -- moving a non-Copy field
                                         // out is implicit, no separate `move` syntax
```

Narrowing is a **type-level consequence of an ordinary partial move**, not a separate
operation with its own syntax. Nothing is written at the narrowing site beyond the move
that causes it.

**The residual is an ordinary value.** It can be bound, passed, returned, dropped, and
narrowed again. It is not a special "partially moved" state that must be repaired before
use.

**Narrowing is path-sensitive, following RFC-0071's move tracking.** The residual type at
a program point is determined by the set of fields moved on *every* path reaching it: a
field moved on one arm of an `if` (and not the other) is conservatively treated as moved
after the join, and a move carried around a loop participates in the same fixpoint the
move checker already computes. Narrowing adds no new control-flow analysis — it is the
type-level reading of the move state RFC-0071 already tracks per binding.

**The same rule applies uniformly to a nominal type's own row, not only to an anonymous
record's (dependency discharged, see §3 below).**

```metel
struct Handle { fd: i64, name: String }

fun main() {
    let h := Handle { fd = 3, name = "x" };
    let n := h.name;   // h : Handle.{ fd } from this point on, same brand as Handle
}
```

`Handle.{ fd }` is a real, ordinary value of the *same brand* as `Handle` — not a
coincidentally-shaped anonymous record. RFC-0137 (Nominal Types as Branded Rows,
`3-integrated`) supplies the `(brand, row)` representation this depends on; the rule
itself, the subset-lattice bound, and "the residual is an ordinary value" all apply
exactly as stated above, for either kind.

**A record-typed field is moved as a unit.** `let i = o.inner` removes the whole `inner`
label, giving `o : Outer.{ tag }` — the residual's row never carries a *narrower* type
for a field it still holds. Narrowing a field *of* `inner` in place is nested narrowing,
deferred to RFC-0150 (§3).

## 2. Why this needs no row machinery

A closed record over *N* fields has at most 2^*N* residual shapes, all of them concrete
record types that RFC-0116 can already express. Narrowing computes one concrete type from
another concrete type by removing a label. A field is either present at its declared type
or gone — a record-typed field is one label, not a sub-lattice — so there is no
unification variable, no row kind, and no inference problem. (Recursing into a
record-typed field, which *would* make the residual space a product of sub-lattices and
needs residual field types the type grammar does not yet express, is RFC-0150.)

This is the load-bearing reason narrowing is specified here rather than in RFC-0121: it
looks like row polymorphism and is not. Abstracting over *which* residual a function
accepts is a genuinely different capability and belongs to RFC-0121.

## 3. What this RFC does not cover

- **Widening.** Assigning a moved-out field back is the inverse operation, and it raises a
  question narrowing does not: whether the reassembled value satisfies whatever invariant
  its type was built with. That is RFC-0114's (`Construct`), which specifies that row
  completion fires a constructor rather than being a bare write.
- ~~**Narrowing a *nominal* type.** Whether `Handle` narrows to `Handle.{ fd }` on partial
  move — as opposed to a record narrowing to a record — depends on nominal types carrying
  rows at all, which is RFC-0120's question and, in its strong form, an open exploration
  (`reports/substructural-types/nominal-types-as-branded-rows.md`).~~ **Dependency
  discharged, 2026-08-25 — RFC-0137 (Nominal Types as Branded Rows)
  answers this directly:** every `struct` carries `(brand, row)` unconditionally, and
  narrows to `Handle.{ fd }` on partial move by exactly this RFC's own mechanism, at the
  same brand. This RFC's own scope should now be understood as extending to nominal
  narrowing via RFC-0137 as the supplying dependency, not excluding it — full
  nominal-type worked examples in this RFC's own "Proposed Design" are a real follow-up
  this correction does not itself perform, left for this RFC's own review to take up.
  **Caveat, 2026-08-25 same day: RFC-0137 was reverted to `1-under-review` the same
  day it was accepted** (its own Open Questions 5-6, opened on reversion). The design
  reasoning above is unchanged. **RFC-0137 was re-accepted 2026-08-27**, all four Open
  Questions closed. **Follow-up performed, 2026-08-27: §1 above now carries the
  nominal-type worked example this note called for.** This item no longer belongs
  under "what this RFC does not cover" — kept here, not moved, per this corpus's
  append-only convention, but nominal narrowing is now within this RFC's own stated
  scope, not excluded from it.
- **Nested narrowing.** Narrowing a field *of* a record-typed field in place
  (`o.inner.a`, so `o : Outer.{ inner: Inner.{ b }, tag }`) — as opposed to moving the
  whole `inner` field as a unit — is **RFC-0150 (Nested Row Narrowing)**. It needs a
  recursive residual type system this RFC deliberately avoids: a type grammar for a
  branded row whose field type differs from the declaration, residual types for tuple
  fields (RFC-0071 §9a tracks tuple elements like struct fields), recursive `Drop`
  receiver shapes rather than a flat required-field set, and control-flow-join rules for
  path-dependent nested residuals. RFC-0150 is targeted alongside RFC-0147/0148, whose
  narrowed `drop` receiver forms it depends on.
- **Borrowed narrowing.** Narrowing a `&var` view rather than an owned value is
  RFC-0119's by-reference mode and RFC-0109's views.
- **Per-field multiplicity.** Deliberately out of scope for the whole records cluster
  until records are implemented — see this RFC's References.

---

## Open Questions

1. ~~What is the interaction with `Drop`? If a record type could carry custom teardown
   this would be the hard case — a narrowed residual reaching end of scope with the
   destructor's required fields already gone. RFC-0116 §3 forbids custom `Drop` on
   records outright, so for records this question does not arise. It arises the moment
   narrowing is extended to nominal types (RFC-0120), and a concrete leak example is
   worked through in `reports/substructural-types/nominal-types-as-branded-rows.md` §4.
   Recorded here so the extension does not inherit the exemption silently.~~ **Resolved,
   2026-08-25 — RFC-0137 §5.** Dispatch is row-bounded: the compiler computes, once per
   `Drop` impl, a fixed concrete set of fields the destructor reads (including
   transitively through helper-method calls, per RFC-0137 §5's 2026-08-25 update), and
   the destructor fires against any residual whose row is a superset of that set. No
   leak — the destructor is never skipped for lacking a field it never reads.
   **Updated 2026-08-28.** RFC-0137 §5 was amended: the required set is no longer
   computed from the body but *declared on the `drop` receiver type* (RFC-0109 named
   view, or RFC-0146/RFC-0147's `Self.R`). The row-bounded dispatch rule (residual ⊇
   required set) and the no-leak property are unchanged; only where the set comes from
   changed.
2. ~~Does narrowing interact correctly with RFC-0071 §7's blanket ban on partial moves out
   of `Drop`-implementing types? RFC-0071 bans them wholesale; a narrowing-aware design
   might narrow the ban to the fields a destructor actually reads. That refinement was
   drafted in RFC-0091 §1 (`uses (fd)`), which is now deferred. Whether the ban simply
   applies as written, or needs revisiting for records, is unresolved.~~ **Resolved in
   design, 2026-08-25 — not yet in the implementation.** RFC-0071 §7's blanket ban is
   superseded *in design*, not narrowed by an exception, by RFC-0137 §5's row-bounded
   dispatch — the exact refinement this question anticipated (narrow the ban to the
   fields a destructor actually reads), specified concretely rather than left to
   RFC-0091's now-deferred `uses (fd)` mechanism. **Corrected the same day**: RFC-0071
   §7's ban is not an unimplemented gap RFC-0137 fills — it is real, tested,
   `--move-check`-enforced behavior today (off by default; a separate default-on
   migration is tracked). Until RFC-0137's own row-bounded mechanism is actually built,
   `--move-check` continues to reject every partial move of a `Drop` type
   unconditionally, exactly as RFC-0071 §7 states.
3. ~~**Is the 2^*N* claim actually the right bound in the presence of nesting?** A record
   whose field is itself a record has residuals in both dimensions. Believed fine —
   narrowing is per-value, not recursive — but not checked.~~ **Resolved 2026-08-29 —
   this RFC is flat; nesting does not arise.** A record-typed field is moved as a **unit**
   (`let i = o.inner` → `o : Outer.{ tag }`); a residual's row never carries a narrower
   type for a field it still holds. So the bound is exactly `2^N` over the value's own
   fields, and `R` never recurses. The moved-out `inner` is then its own value with its
   own independent `2^M` lattice — no interaction, no product. **Recursive (nested)
   narrowing** — `o.inner.a` narrowing `o.inner`'s type in place — is a real capability
   but a separate one: it needs residual field types the type grammar does not express, a
   residual form for tuple-typed fields, recursive `Drop` receiver shapes, and join rules
   for path-dependent nested residuals. It is **RFC-0150 (Nested Row Narrowing)**, §3,
   targeted with RFC-0147/0148.

---

## References

- `public/rfcs/5-superseded/rfc-0090-structural-records.md` §3 step 1 — the source, which
  bundled narrowing with the type-former
- RFC-0116 (Anonymous Record Types) — the type-former this narrows
- RFC-0071 (Ownership and Move Semantics, `3-integrated`) — supplies the move
  tracking this rule is a type-level consequence of; partial-move tracking itself is
  gated behind `--move-check`, off by default
- RFC-0114 (Constructor Aspect and Canonical Construction) — the inverse operation:
  completing a row fires `construct` rather than a bare write
- `reports/substructural-types/nominal-types-as-branded-rows.md` §4 — the `Drop`-dispatch
  leak that arises when narrowing is extended to nominal types
- RFC-0137 (Nominal Types as Branded Rows, `3-integrated`) — supplies nominal-type
  narrowing directly and the branded `(brand, row)` representation; §3's own stated
  dependency folded in 2026-08-27 (§1's nominal-type worked example); its §5 row-bounded
  `Drop` dispatch resolves Open Questions 1 and 2
- RFC-0150 (Nested Row Narrowing) — the recursive extension: narrowing a field of a
  record-typed field in place. Depends on this RFC and on RFC-0147/0148's narrowed
  `drop` receiver forms; carries the residual-type-grammar, tuple-residual, and
  control-flow-join questions this RFC leaves out (Open Question 3, §3)
- `public/rfcs/1-under-review/rfc-0089-linear-types.md`,
  `public/rfcs/1-under-review/rfc-0091-linear-records.md` — per-field multiplicity, deliberately
  deferred until records are implemented

---

## Decision

**Outcome:** **Accepted and integrated 2026-08-29.** Flat row narrowing: moving a field
out narrows the value's type to the closed 2^*N* subset lattice, at the same brand for a
struct; path-sensitive via RFC-0071's existing move tracking. All three open questions
resolved — OQ1/OQ2 via RFC-0137 §5's row-bounded `Drop` dispatch, OQ3 by scoping this RFC
to flat narrowing (nested/recursive narrowing is RFC-0150). Integrated into
`reference/spec/ownership.md#narrowing` (`spec.ownership.narrowing.legality-1`/`legality-2`,
co-origin with RFC-0137), blocked-exempt on metel-core#858 pending move-triggered
narrowing.
**Target:** v0.13.0, via metel-core#789.
