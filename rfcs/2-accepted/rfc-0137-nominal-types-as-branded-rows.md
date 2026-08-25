---
id: rfc-0137
title: "Nominal Types as Branded Rows"
date: '2026-08-24'
status: accepted
target:
updated: '2026-08-25'
tracking: 'https://github.com/metel-lang/metel-core/issues/827'
---

> **New RFC, formalizing the central thesis of
> `reports/substructural-types/nominal-types-as-branded-rows.md`** — an exploration
> document that spent 2026-07-22 through 2026-07-24 pressure-testing this exact idea
> against nine separate hazards (`Drop` dispatch, constructor-invariant bypass, ambient
> structural matching, generic structs, cross-call passing, cost) and resolved all but
> one of them. That document deliberately did **not** propose itself as this cluster's
> foundation — its own Open Question 7 concluded the central thesis should "stay a live,
> separate exploration" rather than gate the nearer, more concrete records cluster
> (RFC-0116–0121) already under review. This RFC is that deferred step, taken now on an
> explicit decision that the thesis is worth pursuing as a real proposal rather than
> staying an open exploration indefinitely. Sections below are organized as normative
> design, not as the exploration document's own back-and-forth; each traces back to the
> section that resolved it, and the still-open questions are kept open here too, not
> quietly closed by being restated as prose.
>
> `rfc.py new`'s overlap check flagged RFC-0120, RFC-0116, RFC-0089, RFC-0117, RFC-0090 —
> checked each: RFC-0116 (Anonymous Record Types, implemented) owns the record
> *type-former* this RFC narrows nominal values into, and is a dependency, not an
> overlap. RFC-0117 (Row Narrowing, under review) specifies narrowing for records and
> explicitly defers narrowing a *nominal* type as out of its own scope (§3: "depends on
> nominal types carrying rows at all") — this RFC is that missing dependency, not a
> restatement. RFC-0120 (Named Records, under review) proposes an **opt-in** third declaration
> kind, `record X { … }`, that carries `(row, brand)`; this RFC's central claim is that
> *every* struct already does, unconditionally — narrower in one sense (structs only,
> no new declaration keyword) and broader in another (no opt-in). §"Relationship to
> RFC-0120" below states the reconciliation precisely rather than leaving the two RFCs
> to silently disagree. RFC-0089 (Linear Types, draft, deferred) depends on per-field
> multiplicity, which this RFC does not add — flagged only because both touch structs'
> internal representation. RFC-0090 (Structural Records, superseded 2026-07-24) is the
> six-way split's source document; §9 there sketched representation-sharing without the
> narrowing-on-move consequence this RFC adds, already noted as this document's own
> starting point.

> **Status — under review (2026-08-24).** Committed to v0.13.0 (issue #827, milestoned 2026-08-24); discharges RFC-0117 §3's own dependency and answers RFC-0120's Open Question 5
>
> **Updated 2026-08-25.** Added a worked example to §3 (a `struct` fully projected next
> to a same-shaped `record`) after a review question asked whether projecting every
> field of an ordinary struct earns it a named record's structural-matching eligibility.
> It doesn't, by design — the example makes the divergence concrete rather than leaving
> §3's prose claim untested against a reader's own attempt to break it.

> **Status — accepted (2026-08-25).** All four Open Questions closed or determined not to block acceptance; design settled.

## Summary

Every `struct` — not only an opt-in declaration kind — is represented internally as
`(brand, row)`: a fixed nominal identity plus the set of fields currently present. As
long as a value has all its original fields, nothing observable changes; `Handle` reads,
writes, and prints exactly as it does today. Moving a field out narrows the value's
*type* to a smaller row of the *same brand* — `Handle` becomes `Handle.{ fd }` — rather
than leaving the value's type unchanged while a separate, compiler-internal bookkeeping
mechanism remembers what was consumed. Because the residual's brand is exactly `Handle`,
a parameter typed `Handle.{ fd }` (or, inside `Handle`'s own `extend` block, `Self.{ fd
}`) is understood as "still recognizably a `Handle`, narrowed" — not as a plain
structural record indistinguishable from an unrelated anonymous record of the same
shape.

## Motivation

Two gaps in the currently-shipped design motivate this:

**1. A struct's own projection type accepts values that never came from that struct.**
`extend Handle { fun f(h: Self.{ fd }) -> … }` currently typechecks a call passing a
bare anonymous record literal (`{ fd = 3 }`) exactly as readily as a value actually
projected from a real `Handle` (`h.{ fd }`) — confirmed directly against the shipped
v0.13.0 interpreter. RFC-0116 §4 states plainly that this is the intended behavior as
specified: "projection yields a record type" — a genuinely plain, unbranded one, with no
tracking of where it came from. That is a real design choice, not an oversight, but it
means a struct's own projected-field parameter type currently states no more than "has
these fields, whatever their origin" — the same thing `{ fd: i64 }` written directly
would say, with no benefit from naming the struct at all beyond avoiding repetition of
field types.

**2. Partial moves have no type to be moved into.** RFC-0071 (Ownership and Move
Semantics, `3-integrated`) tracks a partial move as compiler-internal bookkeeping
invisible to the type itself — the value's type stays `Handle` even after a field is
gone. That state cannot be named, passed to a function, or returned; the natural pattern
of "take one field out, keep using the rest of the struct" has no expression beyond the
function that did the moving.

Both gaps have the same fix: give the *residual* of a partial move a real type, and make
that type provably still the same struct, narrowed — not a coincidentally-shaped
unrelated value.

---

## 1. The representation

Every `struct` declaration mints a fixed, compile-time-only identity tag (its **brand**)
the moment it is declared. A value of that struct is represented, for type-checking
purposes, as that brand paired with its current **row** — the set of fields still
present, with their types. Construction and whole-value use sites are unaffected: a
freshly-constructed `Handle { fd = 3, name = "x" }` has the row `{ fd: i64, name: String
}`, and every existing program that never triggers narrowing typechecks exactly as
before.

The brand is **not** a new, fourth identity mechanism. `reports/substructural-types/brand-kind-unification.md`
§8 already proposes that allocator tags (`@a`), lifetime anchors (`&r`), and RFC-0076's
brands are one underlying identity kind under three sigils; a struct's own declaration
identity is a fourth surface use of that same kind, not a new concept.

## 2. Narrowing

Moving a field out of a struct value narrows that value's type to a row with the moved
field removed, at the same brand:

```metel
struct Handle { fd: i64, name: String }

fun main() {
    let h = Handle { fd = 3, name = "x" };
    let n = move h.name;   // h : Handle.{ fd } from this point on
}
```

Narrowing is a type-level *consequence* of an ordinary partial move (RFC-0071), not a
separate operation with its own syntax — nothing is written at the narrowing site beyond
the move itself. The residual is an ordinary value: it can be bound, passed, returned,
dropped, and narrowed again. For a struct over *N* fields the space of residual shapes is
the subset lattice, bounded by 2^*N* and trivial at realistic struct sizes; there is no
row variable and no unification involved in computing it.

**A struct's own field projection expression (RFC-0116 §4) produces exactly the same
residual type as a partial move does.** `h.{ fd }` and `move h.name` (leaving only `fd`)
both yield `Handle.{ fd }` — projection is narrowing performed explicitly on a copy of
the reference, rather than as a side effect of consuming the original.

## 3. Eligibility: the brand is universal, visibility to structural matching is not

Giving every struct a row risks reopening exactly what RFC-0116 §5 and RFC-0090 §8 both
argued against: structural matching becoming ambient, so that every struct in the corpus
becomes eligible for every row-conditional blanket `extend` whether its author asked for
that exposure or not.

**Resolution: separate "has a row" from "row is visible to structural matching."**
*Having* a row (for narrowing purposes) is universal — every struct needs it for
narrowing to work uniformly. *Visibility* of that row to `HasField`-style checks and
row-conditional impl resolution stays exactly as opt-in as it is under RFC-0120's
three-tier model:

- A plain `struct` has a row, but that row is never visible to structural matching.
  `Handle.{ fd }` remains a distinct type from `{ fd: i64 }` for every purpose that
  matters to a caller — it is still, unambiguously, `Handle`'s own row — but neither
  `Handle` nor any residual or view produced from it ever satisfies a row bound or a
  row-conditional `extend`.
- Visibility is scoped to the **brand**, fixed once at declaration, and inherited
  unchanged by every narrowing and every view produced from that brand. A residual's
  *row content* is irrelevant to whether it is structurally matchable — only the
  brand's own, once-declared eligibility is. This is what keeps a genuinely opted-in
  named record (RFC-0120) and an ordinary struct's narrowed residual from ever being
  confusable, even when their rows happen to look identical.
- RFC-0119's `#derive(ToRecord, FromRecord)` conversion continues to work exactly as
  specified: `.to_record()` produces a bare, brandless anonymous record — the brand is
  deliberately stripped, which is precisely what makes the converted value trivially
  eligible for structural matching. Nothing about this RFC changes that tier.

This is a restatement of RFC-0120's existing three-tier table, not a fourth tier: what
changes is that tier 1 is described as "brand not visible to matching" rather than "no
row at all." A plain struct's *mechanism* for representing its row becomes uniform with
every other tier; its *eligibility* does not move.

### Worked example: full-width projection does not earn what `record` earns

The property above is easy to state and easy to doubt — "a residual's row content is
irrelevant to eligibility" sounds like it should have an exception at the point where
the residual's row is *complete*. It doesn't. Same fields, same row, one nominal type
declared `struct` and one declared `record` (RFC-0120):

```metel
struct Handle { fd: i64, name: String }
record NamedHandle { fd: i64, name: String }   // RFC-0120 — different declaration, different brand

fun wants_a_record<record T: { fd: i64, name: String, .. }>(t: T) -> i64 { t.fd }

fun main() {
    let h = Handle { fd = 3, name = "x" };
    let r = NamedHandle { fd = 3, name = "x" };

    wants_a_record(r);            // OK — NamedHandle opted in at declaration
    wants_a_record(h.{ fd, name }); // REJECTED — every field named, still not a record
}
```

`h.{ fd, name }` names every field `Handle` has. Its row, at that point, is *identical*
in content to `r`'s. It is still rejected, for exactly the reason §"Resolution" states:
eligibility was fixed the moment `struct Handle` was declared, not `record NamedHandle`,
and projection — at any width, including full width — narrows or restates a row without
ever touching that flag. The two values are structurally indistinguishable and nominally
worlds apart; that gap is the entire point of RFC-0120's `record` keyword being an
explicit, one-way opt-in — RFC-0120 itself states plainly that "the upgrade is a
one-way door," `struct`-to-`record` only, precisely because declaring `record`
publishes the type's fields as public interface in a way a `struct` never does —
rather than something reachable by manipulating an ordinary struct's projection
syntax. If `h.{ fd, name }` satisfied the bound, declaring `record` would buy nothing
a `struct` didn't already have for free.

## 4. Passing a residual to a function

A parameter naming a struct's own projected type is available to **every** struct,
regardless of tier, and needs nothing from §3's eligibility gate:

```metel
struct Handle { fd: i64, name: String }

extend Handle {
    fun describe(h: Self.{ fd }) -> i64 { h.fd }
}

fun main() {
    let handle = Handle { fd = 3, name = "x" };
    Handle::describe(handle.{ fd });   // ordinary type-matching: the parameter names
                                        // exactly this shape, at this brand
}
```

This is ordinary type-matching — the same kind that already governs passing an `i64`
where `i64` is expected — not a structural query. It requires nothing from `HasField` or
impl-resolution coherence, and is unaffected by whether the struct in question ever
opts into RFC-0120's `record` kind.

**A caller must match the parameter's row exactly; there is no implicit truncation at
the call boundary.** Passing `Handle.{ fd, name }` where `Handle.{ fd }` is expected
requires the caller to narrow itself first (`let n = move handle.name;`, or the
equivalent projection `handle.{ fd }`) — the call never silently discards `name` on the
caller's behalf. This matches RFC-0119 §3's existing "no implicit coercion at call
sites" stance, applied one level down: narrowing only ever happens through the caller's
own explicit move or projection, never as a side effect of argument-passing. A future
`.narrow()` utility synthesizing this mechanically, for every field not in a target row,
is plausible but out of scope here — see Open Questions.

A function generic over *which* residual it accepts (`fun f<row R: { fd: i64, .. }>(h:
Handle.{ ..R })`) is a different capability, gated behind RFC-0121's open-row machinery
and RFC-0120's brand-visibility opt-in exactly as it is today; this RFC does not change
that gate.

## 5. `Drop` dispatch against a narrowed residual

A struct implementing `Drop` whose destructor reads a field that has since been narrowed
away must not silently skip the destructor's work. Dispatch is **row-bounded**: for a
given `Drop` impl, the compiler computes — once, from the impl body, at compile time — a
fixed, concrete set of fields the destructor actually reads (conservatively, the union
across every branch of a conditional body). The destructor fires against *any* residual
of the correct brand whose current row is a superset of that fixed set, regardless of
what else has already been moved out.

This needs nothing beyond an ordinary subset check against a value already known,
concretely, at compile time — not a row *variable*, and not RFC-0121's deferred `<row
R>` machinery. It is unrelated to §3's eligibility gate: `Drop` dispatch is the compiler
checking one type's own impl against its own residual, internal bookkeeping rather than
user-facing structural matching, and applies to every struct implementing `Drop`
regardless of tier.

**RFC-0071 §7's blanket rule — "a struct implementing `Drop` may not be partially
moved" — is superseded by this section, not narrowed by an exception.** §7 was written
under the assumption that no representation exists for "which fields remain" on a
`Drop`-implementing struct; under this RFC one always does, so the rule as stated needs
rewriting at the source when this RFC is accepted, not carve-out language layered on top
of it.

**If a destructor calls a helper method, the required field set composes transitively
(resolved 2026-08-25 — see Open Questions #2 for the full reasoning):** the required
set for a `Drop` impl is the union of the fields the destructor body reads directly and,
recursively, the required sets of every `self`-method it calls. This is a fixed point
over one type's own finite method set — the recursion follows only calls to `self`'s own
methods (a call passing some other struct's value reasons against *that* struct's own,
independently-computed set, not this one's), and ordinary visited-set tracking during
the union handles mutual recursion between two of the type's own helpers the same way
any fixed-point computation over a finite graph does. Real call-graph-level work, closer
to effect inference than ordinary type-checking, and harder to *compute* than the
direct-read case — but no longer a different, undesigned kind of mechanism, and it still
bottoms out in exactly one fixed, concrete set per `Drop` impl, checked the same way §5's
opening paragraph already describes. Dynamic dispatch through `dyn Aspect` is out of
scope for this composition, same as it is for the rest of this RFC (§8).

## 6. Widening, and the constructor-invariant risk

Assigning a moved-out field back onto a residual widens its type — `Handle.{ fd }`
becomes `Handle` again once `name` is reassigned. If narrowing and widening are both
fully automatic, an invariant a struct's constructor enforces can be bypassed through
nothing more than ordinary field mutation:

```metel
struct SortedPair { small: i32, big: i32 }   // invariant: small <= big, enforced by SortedPair::new

fun mess_with_it(p: &var SortedPair) {
    let old_small = p.small;   // p narrows to .{ big }
    p.small = 999_999;         // p widens back to full SortedPair -- no call to `new`,
                                // invariant possibly broken
}
```

This is not a new hole this RFC introduces — plain mutable-field reassignment already
bypasses a struct's own constructor today, with zero row machinery involved. What
narrowing/widening does is make the general shape of the problem impossible to keep
scoping narrowly to one conversion function, since move-then-reassign becomes
structurally identical to what a hand-written `from_record`-style conversion already
does. **This RFC does not solve it** — RFC-0114 (Constructor Aspect and Canonical
Construction) is the proposed fix, routing every value of a nominal type through one
`construct`/`construct_unchecked` path, fresh or reassembled. This RFC depends on
RFC-0114 landing before automatic widening can be considered safe to enable; until then,
narrowing (the read side) is presented on its own, and widening a residual back is left
exactly as constrained as ordinary field mutation is today — this RFC neither loosens
nor tightens that.

## 7. Generic structs

Which fields a struct declares is fixed at declaration and does not vary with a generic
parameter — only the field's *type* does. Narrowing a generic struct's value therefore
needs nothing beyond what generic field access already provides: `Pair<T> { a: T, b: T
}` narrows to `Pair<T>.{ b }` (with `b: T` still symbolic) the same way `pair.a`'s type
is already tracked symbolically pre-monomorphization. `Drop`'s row-bounded dispatch
(§5) composes the same way — which field a destructor body touches never depends on
`T`, so the required set stays fixed across every instantiation.

**A generic struct's brand is tied to its declaration, not to any one instantiation.**
`Pair<i64>` and `Pair<String>` share one brand; what differs between them is captured
entirely by their rows (different concrete field types). This is forced by how a single
generic impl (`extend<T> Pair<T>: Drop { … }`) already has to cover every
instantiation with one match, matches every mainstream generic-nominal type system, and
is grounded in `brand-kind-unification.md` §8's freshness property: a generic type's
introduction event is its one declaration, never one per instantiation.

## 8. Cost

**On solid ground independently of this RFC's own status:** a *view* — borrowed access
to a narrower row — costs exactly what taking a reference already costs (RFC-0067a,
implemented); it is a small value holding references to specific fields, no different in
kind from any struct already containing reference fields. The eligibility gate (§3) is a
single declaration-time flag, O(1) per declaration, unrelated to move-tracking.

**Contingent on RFC-0071 actually being built:** whether narrowing itself, and `Drop`'s
compile-time-only dispatch, cost nothing at runtime depends on move-tracking being
implemented as **static** bookkeeping — the row a type-checker fiction, a struct's
memory layout never changing at runtime, a moved-out field's memory sitting inert until
the whole value is eventually torn down by ordinary per-field drop. That is RFC-0071's
own stated design. It is not, today, its *status*: RFC-0071 is `3-integrated` but its
partial-move tracking is not implemented (confirmed directly — no such mechanism exists
in the interpreter). This RFC's zero-runtime-cost claim for narrowing and `Drop`
dispatch is therefore a design argument resting on RFC-0071's stated design, not a
demonstrated property, and cannot be validated by inspection until RFC-0071 is actually
built.

One case is flagged rather than resolved: dynamic dispatch through `dyn Aspect`
(RFC-0008, deferred, no consumer yet) could need an actual runtime row representation if
a call site cannot statically know the concrete residual shape behind a trait object.
Not a live concern while RFC-0008 stays deferred, but worth a note rather than silence.

---

## Relationship to existing RFCs

This RFC changes the foundation two under-review RFCs are currently written against, and both
need a corresponding revision if this RFC is accepted:

- **RFC-0117 (Row Narrowing).** §3 there currently states "narrowing a nominal type…
  depends on nominal types carrying rows at all, which is RFC-0120's question" — under
  this RFC, every struct carries a row unconditionally, so that dependency is
  discharged here rather than by RFC-0120, and RFC-0117's own scope should be extended
  from records-narrowing-to-records to cover nominal narrowing directly, with this RFC
  named as the supplying dependency.
- **RFC-0120 (Named Records).** Its own Open Question 5 — "does a narrowed named record
  keep its brand… the rule is unstated" — is answered here for the general case: yes,
  universally, for every struct, not only tier-3 `record` declarations. RFC-0120's
  three-tier table (§1 there) needs restating in the terms §3 above uses: what a
  `record` declaration adds is not "having a row" (every struct already has one under
  this RFC) but "that row being visible to structural matching" — RFC-0120 remains the
  RFC that governs the *opt-in*, this RFC supplies the *representation* it opts into
  being visible.
- **RFC-0071 (Ownership and Move Semantics), §7.** Superseded, not narrowed by an
  exception — see §5 above.
- **RFC-0119 (Record Conversions), added 2026-08-25 (Open Questions #3).** `.to_record()`
  is currently described against "the record" for a struct, written before residual
  types existed to make that ambiguous between the type's full declared row and self's
  *current* row — under RFC-0071 alone those were always the same value. Under this RFC
  they diverge; the answer is self's current row, consistent with §1 there's own framing
  of `to_record()` as "reading fields out." RFC-0119 needs a short clarifying addition
  stating this — not a new capability, a distinction its text never had to draw before.

This RFC depends on RFC-0116 (the record type-former narrowing produces values of) and,
for widening to be considered safe, on RFC-0114 (Constructor Aspect) landing first —
see §6.

---

## Out of Scope

- **Enums.** This is a structs-only move, consistent with RFC-0116/RFC-0090's existing
  scoping — enums are sums, not products, and a records-only foundation for them is
  already declined (RFC-0116 §5).
- **`.narrow()`, a compiler-synthesized utility** for mechanically discarding every
  field not in a target row at a call site. Plausible future ergonomics (§4), but
  depends on RFC-0121's deferred `<row R>` machinery actually being built, and is not
  proposed here.
- **Per-field multiplicity** (`uses (fd)`-style declared consumption). Deliberately
  deferred until this representation exists — RFC-0089/RFC-0091's territory, not
  reopened here.

---

## Open Questions

*Resolved 2026-08-25, working toward acceptance. `PROCESS.md`'s bar for `2-accepted` is
"no more open questions block it" — each item below is closed, or its reason for not
blocking acceptance is stated, rather than left open by default. Original text kept,
resolution appended, per this corpus's append-only convention for exactly this
situation.*

1. ~~Does the zero-runtime-cost property actually hold once RFC-0071 is built, not just
   as stated design? §8's claim for narrowing and `Drop` dispatch rests on RFC-0071's
   own stated design (static bookkeeping) rather than on anything currently
   implemented. Cannot be validated further until RFC-0071 exists to check against.~~
   **Does not block acceptance, 2026-08-25.** This is a verification question, not a
   design one — the design itself (assume RFC-0071's own stated static-bookkeeping
   property) is fully specified and not in doubt; what's pending is empirical
   confirmation once RFC-0071 actually exists to check against. That's squarely
   `4-implemented` territory ("Built against the integrated spec... spec and
   interpreter agree"), the same gate every other RFC resting on an unimplemented
   dependency's stated design already goes through — not a special case unique to this
   RFC's own acceptance.
2. ~~Transitivity of `Drop`'s required-field-set through helper-method calls. §5's
   fixed-set analysis is exact for a destructor body that reads fields directly; a
   destructor calling a helper method needs the required set to compose across that
   call, which is real, call-graph-level work not designed here.~~
   **Resolved 2026-08-25.** The required set for a `Drop` impl is the union of (a)
   fields the destructor body reads directly, and (b), recursively, the required sets
   of every `self`-method it calls. This terminates: it is a fixed point over one
   type's own finite method set (a struct has finitely many methods, and the recursion
   only ever follows calls to `self`'s own methods, not into other types' — a call
   receiving some other struct's value is a call against *that* struct's own,
   separately-computed required set, not part of this one's fixed point). Ordinary
   mutual recursion between two of the type's own helper methods still terminates the
   same way any fixed-point computation over a finite graph does — visited-set
   tracking during the union, not a new kind of analysis. Dynamic dispatch through
   `dyn Aspect` remains outside this (already flagged separately in §8, deferred with
   RFC-0008 itself). This is harder to *compute* than the direct-read case — real
   call-graph work, still not ordinary type-checking — but it is no longer undesigned;
   §5 is updated to state it.
3. ~~Does `.to_record()` (RFC-0119) behave correctly on an already-narrowed residual?
   `handle_narrowed.to_record()`, after some field was already moved out, would produce
   an even-smaller anonymous record than the type's full declared row. Plausible, not
   examined against RFC-0119's own text anywhere.~~
   **Resolved 2026-08-25, checked directly against RFC-0119.** RFC-0119 §§1–4 describe
   `to_record()` as producing *the* record for a `#derive(ToRecord)` struct, written
   before residual types existed to make "the record" ambiguous between "the type's
   full declared row" and "self's current row" — under RFC-0071 alone those were
   always the same value, so the text never had to distinguish them. Under this RFC
   they diverge, and the consistent answer is **self's current row**: `.to_record()`
   is defined per §1 there as "reading fields out," and reading out exactly the fields
   a residual currently has is what that operation already means for a whole value —
   narrowing doesn't add a new capability to `to_record()`, it just means "current
   row" and "full declared row" are no longer synonyms it could get away with
   conflating silently. `handle_narrowed.to_record()` therefore produces the smaller
   record matching `handle_narrowed`'s own row, consistent with §3's "no implicit
   coercion" stance (nothing is silently widened or narrowed further by the call
   itself — it reflects exactly the row already there). RFC-0119 needs a small
   clarifying addition stating this explicitly, since its current text has no
   vocabulary for "current row" distinct from "declared row" at all; tracked as part
   of this RFC's sibling-RFC updates (see "Relationship to existing RFCs").
4. ~~Coherence priority when a value could match both a brand-keyed impl and a
   row-keyed blanket impl. Under brand-scoped visibility (§3), this can only arise for
   a struct that has opted into RFC-0120's `record` kind — a plain struct's row is
   never visible to a row-conditional impl at all — but the priority rule itself
   (more-specific-wins is the obvious default) is not specified anywhere. Same
   question RFC-0090 §9 and RFC-0118's own Open Question 4 already carry, seen from a
   third angle.~~
   **Does not block acceptance, 2026-08-25.** This RFC does not introduce a new
   instance of the question or make an existing one worse — it is the same
   corpus-wide open item RFC-0090 §9 and RFC-0118's own Open Question 4 already carry,
   and RFC-0118 is `4-implemented` today with this exact question still open,
   establishing direct precedent that it doesn't gate acceptance or implementation
   elsewhere in the corpus. No reason for this RFC to be held to a stricter bar than
   RFC-0118 already was for the identical question. Stays open, tracked where it
   already was tracked, not duplicated into a fifth place.

---

## References

- `reports/substructural-types/nominal-types-as-branded-rows.md` — the exploration this
  RFC formalizes; every section above traces back to a numbered section there
- `reports/substructural-types/access-and-presence-rows.md` — the earlier audit that
  found `HasField` bolted onto nominal types rather than derived from them, which this
  document responds to
- `reports/substructural-types/brand-kind-unification.md` §8 — the single
  identity-kind proposal §1 and §7 reuse rather than inventing a fourth mechanism
- RFC-0116 (Anonymous Record Types, implemented) — the record type-former narrowing
  produces values of; §4 there is the projection expression this RFC's narrowing
  matches exactly
- RFC-0117 (Row Narrowing, under review) — specifies narrowing for records; this RFC supplies
  the nominal-type dependency §3 there currently defers
- RFC-0118 (Row Bounds, implemented) — `<record T: { … }>`; already establishes that a
  nominal struct does not satisfy a row bound, the same principle §3 here extends to a
  struct's own projected type
- RFC-0119 (Record Conversions, under review) — tier 2, `#derive(ToRecord, FromRecord)`; §3
  above confirms this RFC leaves that tier's brand-stripping behavior unchanged; needs a
  small clarifying addition per Open Questions #3 / "Relationship to existing RFCs"
- RFC-0120 (Named Records, under review) — tier 3, the opt-in `record` kind this RFC's §3
  reconciles with rather than replaces
- RFC-0071 (Ownership and Move Semantics, `3-integrated`, partial-move tracking not yet
  implemented) — §7's blanket partial-move-with-`Drop` ban this RFC's §5 supersedes;
  also the move-tracking foundation §2 and §8 depend on
- RFC-0114 (Constructor Aspect and Canonical Construction, draft) — the fix for §6's
  constructor-invariant bypass risk, a dependency for widening specifically
- RFC-0089 / RFC-0091 (Linear Types / Linear Records, draft, deferred) — per-field
  multiplicity, deliberately out of scope here (see Out of Scope)

---

## Decision

**Outcome:** Accepted (2026-08-25). Every `struct` is `(brand, row)`; narrowing is a
type-level consequence of partial move (RFC-0071) and of explicit projection
(RFC-0116 §4); brand eligibility for structural matching stays exactly as opt-in as
RFC-0120's three-tier model already has it, unaffected by row content at any width.
All four Open Questions closed or determined not to block acceptance (see that
section). RFC-0117, RFC-0119, RFC-0120, and RFC-0071 §7 each need the corresponding
revision named in "Relationship to existing RFCs."
**Target:** v0.13.0 (tracked by metel-core#827)
