---
id: rfc-0109
title: "Self-View Narrowing and Reference-Destructuring Patterns"
date: '2026-07-18'
status: draft
target:
---

> **Paper-only territory, more so than most drafts in this cluster.** This RFC's
> checker rules are meaningless without RFC-0071's affine move/borrow tracking, which
> is accepted but confirmed **0% implemented** — a repo-wide search for
> borrow-checking infrastructure in the interpreter (`grep -rli "borrow.check\|borrowck"
> src/`) returns nothing. Everything here describes intended behavior once RFC-0071
> lands, the same footing RFC-0091 (Linear Records) already stands on. Amends RFC-0044
> (Explicit Receiver Semantics) — precedent for amending it already exists (RFC-0067a
> did so for reference types). Depends on RFC-0090 (Structural Records, draft) for the
> `record { ... }` vocabulary and RFC-0091 (Linear Records, draft) for the row-shrink
> tracking this RFC's self-view checking rule directly reuses.

## Summary

Two additive mechanisms, closing the gap identified while comparing RFC-0090's records
against Rust's (still unshipped) [view types](https://smallcultfollowing.com/babysteps/blog/2021/11/05/view-types/)
proposal — records-as-drafted give reusable, generic, inter-procedural field-shape
abstraction (`drain_field<row R, ...>`), but nothing gives a *caller* the zero-syntax
benefit view types provide: calling a method that only touches some fields, while other
fields stay separately usable, without the caller writing any conversion:

- **Self-view narrowing** — an inherent method's `self` parameter may declare which
  sub-row of the receiver it touches (`self: &record { golden_tickets: Token }`),
  checked by the compiler against the receiver's own row, with no call-site syntax and
  no `ToRecord`/`FromRecord` tier opt-in required.
- **Reference-destructuring patterns** — `let &mut { a, b } = h;` splits one `&mut`
  borrow into disjoint per-field sub-borrows within a function body, without a
  dedicated `split_record_mut::<R1, R2>()` primitive.

Neither mechanism weakens RFC-0090 §8's "no implicit coercion at call sites" rule —
both are scoped so they never let a value escape into generic, reusable structural-bound
territory; they only ever narrow what a *specific* struct's *own* declared access looks
like, which is a materially smaller claim.

---

## Motivation

RFC-0090/RFC-0091's records, as drafted, solve the *reusable* half of Rust's view-types
motivation — a generic `drain_field<row R, name, T>` function works across any
`ToRecord`-deriving struct, which Rust's per-signature `&{a, b} self` annotation cannot
do (it names concrete paths on one concrete type, at one call site, non-reusably).

But they do not solve the *original* motivating case at all. Rust's own example:

```rust
fn should_insert_ticket(&self, ...) -> bool  // only touches self.golden_tickets

// caller:
let bars = self.bars;                  // move a field out
self.should_insert_ticket(&other);     // ERROR without view types: needs &self,
                                        // but part of self is already moved
```

Translated to Metel with RFC-0090/0091's mechanisms as currently drafted, the caller's
only path is `h.to_record_mut()` plus manual narrowing — RFC-0090 §8 states explicitly
that a struct "must never be silently accepted wherever a row-generic bound is
expected... `.to_record()` has to appear in the source," which is a deliberate,
load-bearing rule (it's what keeps records from becoming TypeScript's "silent nominal
collapse"). That rule is exactly right for the *reusable, generic-function* case. It is
also exactly what stands between Metel and view types' actual headline benefit: calling
an ordinary method while another field is separately in use, with **zero new syntax at
the call site**.

Two more gaps, found by checking the actual source rather than assuming:

- **Metel has no struct-destructuring pattern at all.** `Pattern` (`src/ast/mod.rs`)
  has exactly seven variants — `Wildcard`, `None`, `Literal`, `Binding`, `EnumVariant`,
  `Tuple`, `Array` — and no `Struct` case. `let Point { x, y } = p;` does not parse
  today. A *reference*-destructuring pattern (`let &mut { x, y } = &mut p;`) would be
  an odd, syntactically orphaned addition if the plain by-value form it mirrors doesn't
  exist — every other pattern kind in the enum supports both a bare and (per RFC-0108,
  once accepted) reference-transparent form. §2 below defines the minimal by-value
  struct pattern this RFC needs as a foundation, explicitly deferring the fuller
  semantics (partial-move interaction, field visibility across module boundaries) to
  whichever RFC ends up as struct patterns' primary owner — RFC-0071 or a follow-up,
  not re-litigated here.
- **RFC-0091's `drain_field` already gestures at this but only for one field at a
  time**, and asymmetrically — `(T, &mut record { R })` returns an *owned value* plus
  *one* remainder reference, not two symmetric live references over a genuine row
  partition. Rust's motivating case (read `bars` while mutating `golden_tickets`,
  neither owned/moved out, both alive) needs a real N-way split, not a single-field
  drain.

---

## 1. Why two mechanisms, not one

The two problems look similar but are not the same claim:

- **Self-view narrowing** answers "can I call this *specific* method while other
  fields of the receiver are in use *elsewhere*" — the check spans a call boundary, so
  it has to live in the callee's own signature, checked once, reused by every caller.
- **Reference-destructuring patterns** answer "can I get two independently-usable
  sub-borrows of one value *within this function body* right now" — purely local, no
  signature involved, closer to an ordinary `let` pattern than to a method contract.

Collapsing these into one mechanism was considered — e.g., requiring every self-view
narrowed method to be called through an explicit destructure first — and rejected,
because that reintroduces exactly the call-site ceremony this RFC exists to remove for
the method-call case, without buying back anything the split case doesn't already need
on its own.

---

## 2. Prerequisite: minimal by-value struct-destructuring patterns

```metel
struct Point { x: i64, y: i64, z: i64 }

let Point { x, y, .. } = p;   // binds x, y by move; z (and its move) is untouched here
```

Grammar sketch, following the existing `Pattern::Array`'s `elems`/`rest` shape:

```rust
Struct {
    path: Vec<String>,
    fields: Vec<(String, Pattern)>,   // "x" -> Pattern::Binding("x", ..) for shorthand `x`
    has_rest: bool,                   // `..` present
    span: Span,
}
```

Shorthand `x` desugars to `x: x` (a binding pattern reusing the field name), matching
`EnumVariant`'s existing `fields: Vec<String>` shorthand convention rather than
inventing a new one.

**Scoped deliberately narrow.** This RFC only needs enough struct-pattern grammar for
§4's reference form to have something to destructure into. It explicitly does not
re-derive:

- How a partial struct destructure interacts with RFC-0071's affine move rules beyond
  "each named field is moved independently, `..` leaves the rest where it is, and the
  original binding becomes partially-moved exactly as `let x = p.x;` already would."
- Whether unmatched fields under `..` in a `Drop`-implementing struct's destructure are
  restricted the way RFC-0091 §1 restricts partial moves out of `Drop` types generally
  — this RFC reuses whatever RFC-0091 §1 decides, not a second rule.

---

## 3. Reference-destructuring patterns

```metel
fun rebalance(h: &mut Handle) {
    let &mut { golden_tickets, bars } = h;
    // golden_tickets: &mut Token, bars: &mut Vec<Bar> — both live, disjoint borrows
    golden_tickets.redeem();
    bars.push(Bar::default());
}
```

`&mut { fields }` (and its shared counterpart `& { fields }`) is a pattern, not an
expression — it never produces an intermediate `record` value at all, it directly
splits the incoming `&mut Handle`/`&Handle` into one reborrow per named field, each
typed `&mut FieldType` / `&FieldType`. This is deliberately **not** built on RFC-0090's
`to_record_mut()` — going through an intermediate `record {...}` value would force a
tier-2 `ToRecord`/`FromRecord` derive requirement onto every struct that wants to use
this pattern, which is disproportionate to what the pattern actually needs (structural
field access, already legal on any struct via ordinary `.field` syntax; this just does
several disjoint borrows of it in one statement instead of one at a time).

**Checking rule:** legal wherever ordinary sequential field borrows of the same
disjoint fields would already be legal one at a time (`let a = &mut h.golden_tickets;
let b = &mut h.bars;` — assumed sound once RFC-0071's field-sensitive move/borrow
tracking exists, same as Rust's own baseline field-sensitivity). The pattern form
doesn't grant new aliasing power; it grants doing several such borrows in one place
without repeating `&mut h.` for each field, and — because RFC-0071 isn't implemented
yet — nothing here can be more than a specification of intended behavior against that
not-yet-real checker.

Composes with §2 by dropping the leading `&`/`&mut`: `let { x, y } = &point;` for a
shared multi-field borrow is the same mechanism, immutable.

---

## 4. Self-view narrowing

An inherent method's `self` parameter may be typed as a reference to a **sub-row** of
the receiver's own fields, using `record {...}` purely as field-list notation:

```metel
struct Ticketing { golden_tickets: Token, bars: Vec<Bar> }

impl Ticketing {
    fun should_insert_ticket(self: &record { golden_tickets: Token }, idx: usize) -> bool {
        self.golden_tickets.matches(idx)
    }
}

fun example(t: &mut Ticketing) {
    let bars = &mut t.bars;             // field-level mutable borrow
    if t.should_insert_ticket(0) {      // legal: only needs `golden_tickets`, disjoint from `bars`
        bars.push(Bar::default());
    }
}
```

The caller writes nothing beyond an ordinary method call — `t.should_insert_ticket(0)`.
No `.to_record()` appears anywhere. This is the entire point: the promise lives in
`should_insert_ticket`'s own signature, checked once at its declaration, consulted by
the checker at every call site the same way an ordinary `&self`/`&mut self` signature
already is.

### 4.1 Why this doesn't reopen RFC-0090 §8

§8's rule targets a specific failure mode: a value silently satisfying a *generic,
reusable* structural bound it was never declared against, so two unrelated pieces of
code can accidentally treat unrelated structs as interchangeable. Self-view narrowing
never produces a value that can do that:

- It only ever appears on `self`, inside an `impl` block inherent to one specific
  struct. It cannot be written as a free function's parameter type, and cannot be
  called on any type other than the one declaring it — there is no cross-struct
  unification to accidentally trigger.
- `record {...}` here is never a first-class value flowing anywhere; it names a
  *subset of an already-known type's own fields*, checked once against that type's own
  declaration. Nothing downstream ever needs to ask "does this satisfy `HasField`" —
  the compiler already knows the exact struct and the exact row.

Because of this, self-view narrowing needs **no tier opt-in at all** — it applies to
plain tier-1 structs exactly as freely as to tier-2/3 ones, since it never touches
`ToRecord`/`FromRecord`/row-conditional-impl machinery. This is a real simplification
found while drafting, not an assumption carried in from RFC-0090: self-view narrowing
and the tier system are orthogonal, not layered.

### 4.2 Checking rule, reusing RFC-0091's row-shrink tracking directly

Rather than inventing a second "which fields are currently borrowed" tracker alongside
RFC-0091's row-shrink-on-partial-move tracking, self-view narrowing is checked against
the *same* row state: a call to a method declaring `self: &record { R_needed }` is
legal exactly when `R_needed` is a subset of whatever row the receiver currently has
present — whether that's the type's full declared row (the ordinary case) or an
already-narrowed residual row left over from an earlier partial move
(RFC-0091 §2's `record { b: B }` left behind after moving field `a` out). This reuses
RFC-0091's residual-row representation rather than adding new machinery: "can I call
this method" and "has this field already been moved out" become the same question —
row containment — asked against the same row.

### 4.3 Deliberately no mixed per-field mutability

Rust's `&{bars, mut golden_tickets} self` mixes shared and exclusive access to
different fields in one view. This RFC does not — a self-view is uniformly `&record
{...}` or `&mut record {...}`, matching RFC-0044's existing all-or-nothing `&self` /
`&mut self` split (Metel has no per-field mutability anywhere else in the language
either). **Considered and declined for v1:** per-field mutability inside a view would
need new grammar (`mut golden_tickets` inside a field list, meaning something different
from the field's own declared mutability) and a second mutability axis nothing else in
the language has. Narrower scope: a view is exclusive-or-shared as a whole, over
whichever field subset it names. This does give up some of Rust's expressiveness (a
single narrowed method can no longer simultaneously read one field and write another)
but keeps the mechanism consistent with RFC-0044 rather than introducing a novel
mutability model to serve one feature.

### 4.4 Accuracy checking, not a declared-and-trusted annotation

A self-view is a soundness-relevant claim, not documentation — unlike RFC-0091 §1's
`uses(fd)` (which that RFC already requires to be "checked (not just asserted) against
the method body," the same standard this RFC follows): if `should_insert_ticket`'s body
read `self.bars` while declaring only `golden_tickets`, a caller relying on the
narrowed view to keep `bars` usable elsewhere would be unsound. The construction pass
must reject any field access inside the method body that isn't covered by the declared
view — the same check RFC-0091 §1 already specifies for `uses(...)`, applied here to a
receiver's declared sub-row instead of a `Drop` impl's declared field usage. Not a new
checking philosophy, the same one applied a second place.

---

## 5. Interaction with existing/adjacent RFCs

- **RFC-0044 (Explicit Receiver Semantics, implemented)** — amended. The three
  receiver forms (`self`, `&self`, `&mut self`) are unchanged; self-view narrowing adds
  an optional row annotation *to* `&self`/`&mut self`, it does not introduce a fourth
  receiver kind. Precedent for amending RFC-0044 already exists (RFC-0067a).
- **RFC-0090 (Structural Records, draft)** — self-view narrowing reuses `record {...}`
  purely as notation (§4.1); it does not depend on tier 2/3 existing, and does not
  touch `HasField`/`Lacks`/row-conditional impls at all.
- **RFC-0091 (Linear Records, draft)** — §4.2 reuses its row-shrink-on-partial-move
  representation directly rather than adding a parallel tracker. If RFC-0091's Option C
  (automatic downgrade) is adopted, self-view checking and partial-move checking become
  literally the same code path checking the same row; if only RFC-0091's floor
  (explicit `to_record_mut`) is adopted, self-view narrowing still works standalone —
  it does not depend on Option C, only on the *representation* of "which fields remain"
  existing in some form.
- **RFC-0071 (Ownership and Move Semantics, accepted, unimplemented)** — both
  mechanisms in this RFC are inert without RFC-0071's field-sensitive borrow tracking;
  see the status note at the top.
- **RFC-0108 (Reference-Transparent Match Scrutinees, draft)** — no direct dependency,
  but §2's struct patterns should stay consistent with whatever scrutinee-peeling rule
  RFC-0108 settles on, for the same reason RFC-0107/0108 already cross-reference each
  other.

---

## Alternatives considered

- **Adopt Rust's `&{a, b}` sigil syntax directly**, instead of reusing `record {...}`
  notation. Rejected: it would be a second, unrelated way to spell "a set of field
  names" alongside the one this cluster already has, for no expressiveness gain — this
  RFC's `record {...}` spelling is inert notation in self-view position (§4.1), so
  there is no real machinery cost to reusing it instead of inventing new syntax.
- **A dedicated `split_record_mut<R1, R2>()` primitive**, instead of a pattern. Rejected
  as the primary mechanism for §3: it would require row-generic parameters spelled out
  at every call site for what is, in the common case, an ordinary local `let` splitting
  a handful of named fields — more ceremony than the problem needs. Might still be
  worth adding later as a *generic, reusable* helper (in the spirit of `drain_field`)
  for code that wants to split a row without knowing the field names statically, but
  that is additive, not a replacement for the pattern form.
- **Require self-view narrowing to go through tier 2** (a struct must derive
  `ToRecord`/`FromRecord` before its methods can declare narrowed self-views).
  Rejected — §4.1 shows this isn't needed for soundness, and requiring it would be
  pure, unjustified ceremony.

---

## Open Questions

1. **Named, reusable views.** Matsakis's own writeup flags the same gap: repeating an
   identical field list across several methods on the same struct has no abstraction
   mechanism yet (a `type` alias for a self-view shape, analogous to his `type
   GoldenTicket = {serial_number, mut owner} GoldenTicketData` sketch). Not designed
   here.
2. **Two simultaneously narrowed method calls, not just one call plus a raw field
   borrow.** The worked example above splits one field-borrow and one narrowed call.
   Whether the checker also permits `t.method_a()` (declares `{bars}`) and
   `t.method_b()` (declares `{golden_tickets}`) with *overlapping* call lifetimes (not
   just sequential) needs the same disjoint-path reasoning §3 already assumes from
   RFC-0071 — asserted to fall out for free, not independently verified here.
3. **Cross-module field visibility (RFC-0032).** A self-view can only ever be declared
   inside the struct's own inherent `impl` (§4.1), so it never exposes private fields
   to outside code — but this hasn't been checked against RFC-0032's actual visibility
   rules line by line.
4. **§2's by-value struct pattern is scoped to this RFC's own needs, not a full
   proposal.** Whether it should be split into its own RFC (matching this project's
   general preference for decomposing shared/foundational grammar work — see issue
   #233's AST-generalization scoping) or folded permanently into RFC-0071's move
   semantics is not decided.

---

## References

- Niko Matsakis, [View types for Rust](https://smallcultfollowing.com/babysteps/blog/2021/11/05/view-types/)
  — the motivating comparison this RFC closes the gap against.
- RFC-0044 (Explicit Receiver Semantics, implemented) — the three receiver forms this
  RFC amends.
- RFC-0067a (Reference Types, implemented) — precedent for amending RFC-0044; the
  `&T`/`&mut T` vocabulary self-views and reference-destructuring patterns build on.
- RFC-0090 (Structural Records — Rows and Tiers, draft) — `record {...}` notation and
  the tier system this RFC deliberately stays orthogonal to (§4.1).
- RFC-0091 (Linear Records, draft) — the row-shrink-on-partial-move representation
  §4.2 reuses; `drain_field`'s single-field asymmetric split, the gap §3 closes.
- RFC-0071 (Ownership and Move Semantics, accepted, unimplemented) — the field-
  sensitive move/borrow tracking both mechanisms in this RFC assume exists.
- RFC-0108 (Reference-Transparent Match Scrutinees, draft) — adjacent pattern-position
  work; no direct dependency, noted for consistency.
- `src/ast/mod.rs` — `Pattern` enum, confirmed to have no struct-destructuring variant
  today, motivating §2.

---

## Decision

**Outcome:** *(pending)*
**Target:** *(set when accepted — not required for any current milestone; paper-only
territory pending RFC-0071)*

*(Decision rationale goes here when the RFC is evaluated.)*
