---
id: rfc-0109
title: "Self-View Narrowing and Reference-Destructuring Patterns"
date: '2026-07-18'
status: under-review
target:
updated: '2026-07-21'
---

> **Paper-only territory, more so than most drafts in this cluster.** This RFC's
> checker rules are meaningless without RFC-0071's affine move/borrow tracking, which
> is accepted but confirmed **0% implemented** — a repo-wide search for
> borrow-checking infrastructure in the interpreter (`grep -rli "borrow.check\|borrowck"
> src/`) returns nothing. Everything here describes intended behavior once RFC-0071
> lands, the same footing RFC-0091 (Linear Records) already stands on. Amends RFC-0044
> (Explicit Receiver Semantics) — precedent for amending it already exists (RFC-0067a
> did so for reference types). Depends on RFC-0090 (Structural Records) for the
> `record { ... }` vocabulary and RFC-0091 (Linear Records) for the `(row,
> brand)` representation §4 reuses directly.
>
> **Revised 2026-07-18, later the same day.** §4 rewritten: the inline `self: &record
> { field: Type }` self-view spelling from the first draft is replaced by named `view`
> declarations — a view is a *branded* record, sharing RFC-0090 §9 / RFC-0091 §2.2's
> `(row, brand)` representation rather than an anonymous one. This is a strictly
> smaller-machinery, better-justified design: it resolves Open Question 1 (named,
> reusable views) directly instead of leaving it open, and turns the "why doesn't this
> reopen RFC-0090 §8" argument from an assertion about *where* the syntax appears into
> a mechanical consequence of brand equality. See §4.7 for how this reconciles with
> §8's existing "tier 2 is bare by default" rule rather than violating it.
>
> **Revised again 2026-07-18, later still.** §4.8's "declare two views instead" escape
> hatch is worked out concretely in new §4.9: `self` may be typed as a tuple of views
> with independent `&`/`&mut` modes per slot, checked pairwise-disjoint via §4.4 and
> unpacked in the body via ordinary `Pattern::Tuple` — no new grammar, no new
> mutability axis, just composing mechanisms already specified elsewhere in this RFC.

> **Status — under review (2026-07-21).** Reviewing the records/views substrate cluster together, per OBJECTIVES.md Priority 1 (reordered 2026-07-22). The cluster's first deliverable is the record/row semantics themselves -- RFC-0090 SS3 step 1's closed `record` type-former plus `HasField` -- not the `ToRecord`/`FromRecord` conversions the blog names, which are tier 2 of RFC-0090 SS8 and convert into a type-former that must exist first. Thorough draft with a substantiated primary proposal; open questions remain, chiefly the RFC-0089/RFC-0090 dependency direction that Trigger 6 tracks.

## Summary

Two additive mechanisms, closing the gap identified while comparing RFC-0090's records
against Rust's (still unshipped) [view types](https://smallcultfollowing.com/babysteps/blog/2021/11/05/view-types/)
proposal — records-as-drafted give reusable, generic, inter-procedural field-shape
abstraction (`drain_field<row R, ...>`), but nothing gives a *caller* the zero-syntax
benefit view types provide: calling a method that only touches some fields, while other
fields stay separately usable, without the caller writing any conversion:

- **Named views** (`view TicketView for Ticketing { golden_tickets }`) — a *branded*
  record: the same `(row, brand)` representation RFC-0090 §9 and RFC-0091 §2.2 already
  define for a struct's own internal shape, reused for a named, reusable sub-row tied
  to one specific struct. **Self-view narrowing** — an inherent method's `self`
  parameter declared as `&TicketView`/`&mut TicketView` — is the primary application:
  checked by the compiler with no call-site syntax and no `ToRecord`/`FromRecord` tier
  opt-in required. `self` may also be a **tuple of views** with independently-moded
  slots (§4.9) for mixed-mode access, Metel's answer to Rust's `&{bars, mut
  golden_tickets} self`.
- **Reference-destructuring patterns** — `let &mut { a, b } = h;` splits one `&mut`
  borrow into disjoint per-field sub-borrows within a function body, for the ad hoc
  cases a named view isn't worth declaring.

Neither mechanism weakens RFC-0090 §8's "no implicit coercion at call sites" rule — a
view's brand is exactly what prevents it from ever satisfying a *generic* structural
bound the way an anonymous record could; see §4.2.

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

- **Named views / self-view narrowing** answer "can I call this *specific* method
  while other fields of the receiver are in use *elsewhere*" — the check spans a call
  boundary, so it has to live in the callee's own signature, checked once, reused by
  every caller.
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
§3's reference form to have something to destructure into. It explicitly does not
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

**Once §4 exists, a named view is usually the better choice for anything reused across
more than one call site** — `let v: &mut TicketView = h;` (§4.1's coercion) says the
same thing as `let &mut { golden_tickets } = h;` but gives the shape a name, checked
once at the `view` declaration instead of re-derived at every destructure site. This
pattern form stays the right tool for genuinely ad hoc, one-off splits that don't merit
declaring a type for.

---

## 4. Named views: branded records tied to one struct

### 4.1 Declaration and semantics

```metel
struct Ticketing { golden_tickets: Token, bars: Vec<Bar> }

view TicketView for Ticketing { golden_tickets }
```

The field list is bare — no re-declared types. `golden_tickets`'s type is looked up
from `Ticketing`'s own declaration and checked against it, not restated; re-typing it
here would create exactly the divergence risk RFC-0091 §1's `uses(fd)` mechanism is
careful to avoid by being checked rather than merely declared.

Semantically, this declares:

```
(row: { golden_tickets: Token }, brand: brand_of(Ticketing))
```

reusing RFC-0090 §9 / RFC-0091 §2.2's `(row, brand)` representation directly, rather
than inventing a new type-former. RFC-0091 §2.2 already describes the general operation
this specializes: "if a struct is already internally `(row, brand)`, the residual after
consuming one field is just `(row - field, brand)`." A named view is a *named point* in
that same lattice, reached non-consumingly (borrowed) rather than by move.

The coercion this buys is symmetric and free, because it's ordinary row-shrink/grow on
one fixed brand, not a bespoke conversion:

```metel
fun example(h: &mut Ticketing) {
    let v: &mut TicketView = h;   // row-shrink, same brand — no .to_record_mut() needed
    v.golden_tickets.redeem();
}
```

**A view's `for` target must name a concrete struct in scope**, and (§4.3) a method may
only declare `self` as a view whose `for` target is that method's own enclosing `impl`
type — a view can't be used to make one function generic across two unrelated structs
that happen to share a field name. That would reopen exactly the structural-matching
question §4.2 exists to close off; it's a deliberately declined generalization, the
same discipline §4.8 applies to per-field mutability.

### 4.2 Brand equality is the ambient-typing guard

RFC-0090 §8's core concern is a value silently satisfying a *generic* structural bound
it was never declared against — the TypeScript failure mode. A named view can't do
that: `TicketView` cannot apply to any struct other than `Ticketing`, because its
brand *is* `Ticketing`'s brand, not a lookalike shape that happens to match. This
replaces what an earlier draft of this RFC described as "a declared, closed, nominal
pairing, checked once" with something more mechanical — the guard isn't a separate
rule bolted onto `view`, it's the same brand-equality check every other nominal
operation in this cluster already relies on.

### 4.3 Self-view narrowing

```metel
impl Ticketing {
    fun should_insert_ticket(self: &TicketView, idx: usize) -> bool {
        self.golden_tickets.matches(idx)
    }
}

fun example(t: &mut Ticketing) {
    let bars = &mut t.bars;
    if t.should_insert_ticket(0) {      // legal: TicketView's row is disjoint from
                                          // `bars`, same brand as t — no ceremony here
        bars.push(Bar::default());
    }
}
```

The caller writes nothing beyond an ordinary method call — `t.should_insert_ticket(0)`.
No `.to_record()` appears anywhere; the promise lives entirely in
`should_insert_ticket`'s own signature, checked once at its declaration, consulted by
the checker at every call site the same way an ordinary `&self`/`&mut self` signature
already is. The call-site check itself is now: does `TicketView`'s row fit inside `t`'s
currently-live row, same brand — see §4.5 for what "currently-live row" means when part
of `t` has already been partially consumed.

Because this never touches `ToRecord`/`FromRecord`/row-conditional-impl machinery
(§4.6), self-view narrowing needs **no tier opt-in at all** — it applies to plain
tier-1 structs exactly as freely as to tier-2/3 ones.

### 4.4 View-to-view composition and disjointness

Two views of the same struct are two named points in the same `(row, brand)` lattice,
so both of the operations that matter fall out of the representation rather than
needing their own rule:

- **Narrowing/widening between views composes.** Given a broader `view FullView for
  Ticketing { golden_tickets, bars }` and the narrower `TicketView`, moving between
  them is ordinary row-shrink/grow on one fixed brand — nothing view-specific to
  define beyond §4.1.
- **Disjointness is a two-line check.** `TicketView` (`{golden_tickets}`) and `view
  BarsView for Ticketing { bars }` are safe to hold simultaneously — as two separately
  narrowed method calls, or as two bindings produced by §3's destructuring pattern —
  exactly when their brands match and their field-name sets don't intersect. This
  lets simultaneity be checked once, structurally, rather than re-derived per call
  site the way an anonymous `record {...}` self-view would require.

### 4.5 Interaction with RFC-0091 Option C

This inherits part of RFC-0091 §2.1's still-unproven aliasing question, but only the
part that's actually the same question:

- **A view borrowed from an intact struct — no prior partial move involved — is an
  ordinary disjoint borrow, not a move.** It never touches Option C's downgrade
  machinery at all, so it doesn't inherit §2.1's open soundness question. This is also
  Rust's own motivating scenario for view types (`should_insert_ticket` above never
  moves anything), so it's the common case, not the edge case.
- **Checking a self-view against an already-partially-consumed residual** — some field
  was previously moved out via RFC-0091 Option C, and a later call's declared view
  needs to fit inside what remains — genuinely is the same question RFC-0091 §2.1
  leaves open ("what type does a pre-downgrade borrow have afterward"), and this RFC
  does not resolve it independently. If Option C never gets a soundness argument, this
  RFC's §4.3 still stands on its own for the intact-struct case; only this
  already-partially-moved interaction would need to fall back to something more
  conservative (e.g. rejecting the call outright once any field has been consumed).

### 4.6 Deliberately not tier 3 — views never enter coherence

A view's brand is consumed only by §4.2's ambient-typing guard, §4.3's row-containment
check, and §4.4's disjointness check — **never handed to the coherence/impl-resolution
pass.** This is what keeps `view` from silently becoming "tier 3 for free": RFC-0090
§8's tier-3 named record is distinguished specifically by row-conditional impls
resolving against a type's own intrinsic row *at impl-resolution time*. A view is
deliberately never inserted into that resolution path, regardless of the fact that it
now carries the same `(row, brand)` shape tier 3 uses internally. Reusing a
representation is not the same as reusing a capability, and this boundary is what keeps
that distinction real rather than nominal.

### 4.7 A third exception to "tier 2 is bare by default," not a violation of it

RFC-0090 §8 states tier 2's `to_record()`/`to_record_mut()` output is bare/anonymous
"except for a fiat-linear source struct" (RFC-0089 §3.1) — one narrow, explicitly
justified case where the derived record carries a brand because the bare row can't
reconstruct some fact (there: `Linear`-by-fiat status). A named `view` is a second,
differently-motivated instance of the same exception pattern: the fact the bare row
can't reconstruct here is provenance/reversibility — an anonymous `record {
golden_tickets: Token }` has no way to widen back to `Ticketing` specifically, but a
brand-carrying view does, for free (§4.1). Framed this way, `view` doesn't weaken §8's
bare-by-default rule; it's the second of what the rule already anticipated could need
narrow, justified carve-outs — and §4.6 is what keeps this exception from creeping
further than RFC-0089 §3.1's already did.

### 4.8 Deliberately no mixed per-field mutability

Rust's `&{bars, mut golden_tickets} self` mixes shared and exclusive access to
different fields in one view. This RFC does not — a view is uniformly `&View` or `&mut
View`, matching RFC-0044's existing all-or-nothing `&self` / `&mut self` split (Metel
has no per-field mutability anywhere else in the language either). **Considered and
declined for v1:** per-field mutability inside a view would need new grammar (`mut
golden_tickets` inside a field list, meaning something different from the field's own
declared mutability) and a second mutability axis nothing else in the language has.
Narrower scope: a view is exclusive-or-shared as a whole, over whichever field subset
it names. This does give up some of Rust's expressiveness (a single narrowed method can
no longer simultaneously read one field and write another) but keeps the mechanism
consistent with RFC-0044 rather than introducing a novel mutability model to serve one
feature. §4.4's disjointness check is the intended escape hatch for the mixed-mode
case: declare two views instead of one field list with mixed modes — worked out
concretely in §4.9.

### 4.9 Mixed-mode methods: a tuple-of-views `self`

Worked out, §4.8's escape hatch is: `self` may be declared as a **tuple of views**,
each with its own independent `&`/`&mut` mode, checked pairwise-disjoint via §4.4.

```metel
view BarsView for Ticketing { bars }
view TicketView for Ticketing { golden_tickets }

impl Ticketing {
    fun redeem_and_log(self: (&mut BarsView, &TicketView)) {
        let (bars, tickets) = self;    // ordinary Pattern::Tuple destructure — §2
                                        // doesn't even need to introduce this, it's
                                        // already in the AST
        if tickets.golden_tickets.matches(0) {
            bars.bars.push(Bar::default());
        }
    }
}

fun example(t: &mut Ticketing) {
    t.redeem_and_log();   // ordinary call — no new syntax, same as any &mut self method
}
```

This reuses three things that already exist rather than adding a fourth mutability
axis: ordinary tuple types, §4.4's disjointness check (generalized from a pair to
however many views a tuple names — every pairwise combination among the N elements must
be disjoint, a mechanical extension of the same rule, not a new one), and
`Pattern::Tuple`, already in the AST, for unpacking `self` in the body. No new grammar
for mixed modes: each tuple slot stays uniformly `&View` or `&mut View`, exactly what
§4.8 requires of any single view — the mixing happens *across* slots, never within one.

**Addressability follows the tightest slot — the same rule Rust's own reborrowing
already uses, not a new one.** A tuple self-declaration containing at least one `&mut
ViewX` element can only be satisfied by a caller holding (or able to produce) `&mut
Ticketing` for the whole receiver: you cannot manufacture new exclusive access out of a
shared borrow, only subdivide an already-exclusive borrow into a mix of exclusive and
shared sub-borrows. A tuple where every slot is `&ViewX` only ever needs `&Ticketing`.
This extends RFC-0044 §9's addressability table by one row rather than replacing it.

**Worked example, in RFC-0044 §9's own allowed/disallowed style** (that section's
worked examples are exactly this shape — `counter.increment()` vs.
`make_counter().increment()` — extended here to a tuple self):

```metel
impl Ticketing {
    // all-shared tuple: only ever needs &Ticketing, same row as an ordinary &self method
    fun summarize(self: (&TicketView, &BarsView)) -> String { ... }

    // mixed tuple, from above: at least one &mut slot, needs &mut Ticketing
    fun reconcile(self: (&mut BarsView, &TicketView, &mut MetaView)) { ... }
}
```

Allowed:

```metel
let mut t = Ticketing { golden_tickets: Token::new(), bars: vec![], metadata: Meta::new() };
t.summarize();     // &Ticketing suffices — t is addressable, mut not required
t.reconcile();     // t is mutably addressable, so the &mut-containing tuple is satisfied

let shared: &Ticketing = &t;
shared.summarize();   // all-shared tuple — an ordinary shared reference is enough
```

Disallowed:

```metel
let shared: &Ticketing = &t;
// shared.reconcile();
// ERROR: reconcile's self contains &mut BarsView and &mut MetaView slots, which need
// &mut Ticketing for the whole receiver — `shared` is only a shared reference, the
// same failure as calling an ordinary &mut self method through a &T (RFC-0044 §9's
// own `(&counter).increment()` case), just now triggered by one slot out of several
// rather than the receiver's only mode.

fun make_ticketing() -> Ticketing { ... }
// make_ticketing().reconcile();
// ERROR: an rvalue has no stable address to borrow &mut from — RFC-0044 §9's
// `make_counter().increment()` case, unchanged by this RFC, and triggered here for
// the same reason it's triggered for an ordinary &mut self call.
```

Whether `make_ticketing().summarize()` (all-shared tuple, no `&mut` slot) is allowed
depends entirely on whether an ordinary `&self` method may already be called on an
rvalue — a question RFC-0044 §9 doesn't settle either (its own worked examples only
cover `&mut self` on an rvalue). This RFC adds nothing to that question; the
all-shared-tuple case inherits whatever RFC-0044 §9 already says, or eventually says,
about `&self` there, unchanged.

**Worked example: three views, to exercise "pairwise" for real instead of just for a
pair.** Extend `Ticketing` with a third field:

```metel
struct Ticketing { golden_tickets: Token, bars: Vec<Bar>, metadata: Meta }

view TicketView for Ticketing { golden_tickets }
view BarsView for Ticketing { bars }
view MetaView for Ticketing { metadata }

impl Ticketing {
    fun reconcile(self: (&mut BarsView, &TicketView, &mut MetaView)) {
        let (bars, tickets, meta) = self;
        if tickets.golden_tickets.matches(0) {
            bars.bars.push(Bar::default());
            meta.metadata.record_redemption();
        }
    }
}

fun example(t: &mut Ticketing) {
    t.reconcile();   // ordinary call
}
```

`self`'s three slots require checking all `C(3,2) = 3` pairs — `(BarsView, TicketView)`,
`(BarsView, MetaView)`, `(TicketView, MetaView)` — each pairwise disjoint since `{bars}`,
`{golden_tickets}`, `{metadata}` share no field. Two slots are `&mut` and one is `&`; by
the addressability rule above, the *tightest* slot governs, so `t.reconcile()` still
only needs `&mut Ticketing` overall — the same single requirement as the two-view case,
not one requirement per `&mut` slot.

**What the pairwise check rejects.** A fourth view whose row overlaps an existing one
in the tuple is caught by the same check, not a special case of it:

```metel
view GoldenNameView for Ticketing { golden_tickets, metadata }   // overlaps both
                                                                   // TicketView and MetaView

impl Ticketing {
    fun broken(self: (&TicketView, &GoldenNameView)) { ... }
    // ERROR: TicketView ({golden_tickets}) and GoldenNameView ({golden_tickets,
    // metadata}) are not disjoint — `golden_tickets` appears in both rows, so this
    // pair fails §4.4's check even though every individual view is well-formed on
    // its own.
}
```

Nothing about this needs a new diagnostic path: it's the exact same "two views, same
brand, intersecting field sets" case §4.4 already defines, just found while checking
one pair out of a larger tuple instead of a lone two-element case.

**This is §3's reference-destructuring pattern, applied at the receiver boundary
instead of a local `let`** — worked out concretely, not just asserted, using §3's own
bare-field-list syntax rather than a named-view tuple type:

```metel
fun reconcile_inline(t: &mut Ticketing) {
    let &mut { bars, metadata } = t;   // §3's pattern — two disjoint mutable sub-borrows
    if t.golden_tickets.matches(0) {   // `golden_tickets` was never named in the pattern,
                                        // so `t` itself stays usable to reach it directly —
                                        // ordinary field-sensitive borrowing (RFC-0071),
                                        // no new syntax needed for the read-only slot
        bars.push(Bar::default());
        metadata.record_redemption();
    }
}
```

This reproduces §4.9's `reconcile` example's exact access pattern (exclusive on `bars`
and `metadata`, shared on `golden_tickets`) with no mixed-mode pattern syntax at all —
the trick is that §3's pattern only ever needs to *name* the fields being reborrowed
exclusively; a field left out of the pattern is simply still reachable through the
original binding, at whatever mode the checker can still justify. This is why §3 never
needed its own per-field mutability annotation (§4.8's concern for named views): the
"mixed mode" case falls out for free at the local level, because the un-destructured
field always has a live whole-value binding (`t`) to fall back on.

**That fallback doesn't exist inside a self-view-narrowed method.** Once `self` is
declared `(&mut BarsView, &TicketView, &mut MetaView)`, the method body never sees an
un-narrowed `Ticketing` at all — only the three declared slots (§4.10 enforces this by
construction) — so there is no binding equivalent to `t` above to reach an
un-destructured field through. This is the real reason §4.9's tuple form has to name
every field it touches, including the read-only ones, while §3's local pattern doesn't:
one is checked against a value the function still holds in full; the other replaces
that value's visibility entirely once inside the method.

`self: (&mut BarsView, &TicketView)` and `let &mut { bars, metadata } = t;` (plus
ordinary continued access to whatever's left over) describe the same underlying split;
the difference is *where* it happens (implicitly at call entry, reusable by every
caller vs. explicitly at one `let`, local to one function) and *how much has to be
named* (every slot vs. only the exclusively-borrowed ones). Naming the split once, in
the receiver position, is what buys zero-call-site-syntax reuse; the local `let` form
(§3) stays the right tool when a specific caller wants to split a receiver it already
holds, without declaring a whole method for it.

### 4.10 Accuracy checking, not a declared-and-trusted annotation

A self-view is a soundness-relevant claim, not documentation — unlike RFC-0091 §1's
`uses(fd)` (which that RFC already requires to be "checked (not just asserted) against
the method body," the same standard this RFC follows): if `should_insert_ticket`'s body
read `self.bars` while declaring only `TicketView`, a caller relying on the narrowed
view to keep `bars` usable elsewhere would be unsound. The construction pass must
reject any field access inside the method body that isn't covered by the declared
view's row — the same check RFC-0091 §1 already specifies for `uses(...)`, applied here
to a receiver's declared view instead of a `Drop` impl's declared field usage. Not a new
checking philosophy, the same one applied a second place.

For §4.9's tuple form, the same rule applies to the *union* of the tuple's rows, with
one addition: an access through one slot's binding that only the *other* slot's row
covers must also be rejected — `bars.golden_tickets` inside `redeem_and_log` above is
an error even though `golden_tickets` is somewhere in scope (via `tickets`), because
`bars`'s own declared type (`&mut BarsView`) doesn't include it. Each binding is
checked against its own slot's row, not the union — the union only matters for deciding
whether the *method as a whole* may exist against a given receiver.

### 4.11 Interaction with RFC-0032 field visibility

Two cases, worth separating because only one of them is actually novel.

**Self-view narrowing never crosses the boundary at all.** Every self-view/tuple-of-views
declaration in this RFC lives inside an inherent `impl` block (§4.3, §4.9), and
inherent impls are restricted to a type's own declaring module — the same "no owning
module" reasoning RFC-0090 §5 already relies on to explain why *records* can't have
inherent impls at all; ordinary structs have one, and it's fixed. So a method declaring
`self: &TicketView` is always written where every field of `Ticketing` — private or
`pub` — is already visible:

```metel
// ticketing.mln
struct Ticketing {
    pub golden_tickets: Token,
        bars: Vec<Bar>,          // private — no `pub`
}

view TicketView for Ticketing { golden_tickets }
view BarsView for Ticketing { bars }    // names a private field — fine here, this file
                                          // IS Ticketing's own declaring module

impl Ticketing {
    fun should_insert_ticket(self: &TicketView, idx: usize) -> bool { ... }   // untouched
                                                                                 // by RFC-0032
}
```

**Declaring a view from outside the module is checked exactly like a struct pattern —
reused, not reinvented.** A `view`'s field list is a list of field names checked against
`Struct`, the same syntactic shape RFC-0032's own pattern-matching rule already covers
("Explicitly naming a private field in a pattern is a compile error"):

```metel
// caller.mln — a different module
// view LeakyView for Ticketing { bars }
// ERROR: field `bars` is private — same error family as constructing or
// pattern-matching Ticketing { bars } from outside ticketing.mln (RFC-0032 D1)
```

**The genuinely open case: a view declared inside the module, naming a private field,
then exposed outside it through an ordinary `pub` function.** Nothing in §4.1's
coercion rule stops this:

```metel
// ticketing.mln
view BarsView for Ticketing { bars }   // legal here — bars is private, but this is
                                         // Ticketing's own module

pub fun peek_bars(t: &mut Ticketing) -> &mut BarsView {
    t   // ordinary row-shrink coercion (§4.1) — legal cross-module because peek_bars
        // itself is pub, independent of bars's own visibility
}
```

```metel
// caller.mln
let v = peek_bars(&mut t);
v.bars.push(Bar::default());
// must still be an error — `bars` is private to ticketing.mln, and returning a view
// over it through a pub function must not become a way to launder that
```

If field access through a view only checked the view's own *declaration* site (inside
`ticketing.mln`, where `bars` is visible), this would silently defeat RFC-0032 — any
`pub` function returning a view over a private field becomes an unintended backdoor. The
check has to be re-applied at the point of *access* (`v.bars`), against the field's own
visibility on `Ticketing`, regardless of where or by whom the view type itself was
declared — the same discipline `struct_value.field` already uses today, just reapplied
through one more layer of indirection. **Not settled here which pass performs this
check or how field-visibility metadata threads through a view's own type
representation** — this is the concrete design gap Open Question 3 refers to; this
section gives it a specific failure case to check an implementation against, rather
than leaving it a vague cross-module concern.

---

## 5. Interaction with existing/adjacent RFCs

- **RFC-0044 (Explicit Receiver Semantics, implemented)** — amended. The three
  receiver forms (`self`, `&self`, `&mut self`) are unchanged; self-view narrowing adds
  an optional named-view refinement *to* `&self`/`&mut self`, it does not introduce a
  fourth receiver kind. §4.9's tuple-of-views `self` extends §9's addressability table
  by one row (a `&mut`-containing tuple requires `&mut` addressability of the whole
  receiver) rather than replacing it. Precedent for amending RFC-0044 already exists
  (RFC-0067a).
- **RFC-0090 (Structural Records)** — §4 reuses §9's `(row, brand)`
  representation directly, and §4.7 frames the view-carries-a-brand exception as a
  second instance of §8's existing fiat-`Linear` carve-out rather than a new one. §4.6
  keeps views out of tier 3's coherence-facing capability regardless of representation
  overlap.
- **RFC-0091 (Linear Records)** — §4.1 specializes §2.2's `(row, brand)`
  residual-reuse operation; §4.5 inherits part, but only part, of §2.1's open aliasing
  question. If RFC-0091's Option C is adopted, self-view checking against a partially
  consumed residual and Option C's own downgrade tracking become literally the same
  code path checking the same row; if only RFC-0091's floor (explicit
  `to_record_mut`) is adopted, self-view narrowing over *intact* structs (§4.5's first
  case) still works standalone.
- **RFC-0032 (Field-Level Visibility, implemented)** — §4.11 reuses its existing
  pattern-matching private-field check directly for a cross-module `view` declaration's
  field list, and identifies one genuinely open gap: a view declared inside a module
  over a private field, then exposed outside it through an ordinary `pub` function,
  must still reject field access at the *use* site, not just check visibility at the
  view's *declaration* site — otherwise a `pub` function returning a view becomes an
  unintended way to launder a private field. Self-view narrowing itself (§4.3, §4.9)
  never interacts with this RFC at all, since inherent impls are always written inside
  the declaring module already.
- **`brand-kind-unification.md`** — already proposes `@a`/`&r`/`'c` as one underlying
  identity kind with a struct's own identity tag as a plausible fourth surface use
  (RFC-0090 §9). A view's brand is that same tag, reused a second time for a narrower
  purpose (§4.6) — not a fifth kind alongside it.
- **RFC-0071 (Ownership and Move Semantics, accepted, unimplemented)** — both
  mechanisms in this RFC are inert without RFC-0071's field-sensitive borrow tracking;
  see the status note at the top.
- **RFC-0108 (Reference-Transparent Match Scrutinees)** — no direct dependency,
  but §2's struct patterns should stay consistent with whatever scrutinee-peeling rule
  RFC-0108 settles on, for the same reason RFC-0107/0108 already cross-reference each
  other.

---

## Alternatives considered

- **Anonymous, brandless self-views** (`self: &record { golden_tickets: Token }`,
  this RFC's own original spelling before this revision). Superseded, not merely
  rejected: it worked, but required re-deriving §4.2's ambient-typing safety argument
  from "declared inside an inherent impl" each time, gave no free reversibility or
  view-to-view composition (§4.1, §4.4), and left named-view reuse (Open Question 1 in
  the prior draft) unanswered. The branded design is strictly less new machinery (no
  new type-former, reuses RFC-0091 §2.2's representation) for strictly more capability.
- **Adopt Rust's `&{a, b}` sigil syntax directly**, instead of a `view` declaration.
  Rejected: it would be a second, unrelated way to spell "a set of field names"
  alongside the one this cluster already has (`record {...}`), for no expressiveness
  gain, and it has no natural resting place for a brand the way a named declaration
  does.
- **A dedicated `split_record_mut<R1, R2>()` primitive**, instead of a pattern, for §3.
  Rejected as the primary mechanism there: it would require row-generic parameters
  spelled out at every call site for what is, in the common case, an ordinary local
  `let` splitting a handful of named fields. Might still be worth adding later as a
  *generic, reusable* helper (in the spirit of `drain_field`) for code that wants to
  split a row without knowing the field names statically, but that is additive, not a
  replacement for the pattern form.
- **Require self-view narrowing to go through tier 2** (a struct must derive
  `ToRecord`/`FromRecord` before its methods can declare narrowed self-views).
  Rejected — §4.3 shows this isn't needed for soundness, and requiring it would be
  pure, unjustified ceremony.

---

## Open Questions

1. ~~Named, reusable views~~ — **resolved by §4**: `view X for Struct { fields }`.
2. **Multiple, separately-declared narrowed method calls with overlapping lifetimes** —
   distinct from §4.9's resolved case (one method, mixed modes, split at call entry).
   Here two *different* methods (`t.method_a()` returning something still held while
   `t.method_b()` is also called) each narrowed to disjoint views. §4.4's disjointness
   check covers the shape of this in principle (same brand, disjoint rows), but whether
   the checker's call-lifetime reasoning composes correctly for genuinely *overlapping*,
   not just sequential, calls needs the same disjoint-path reasoning §3 already assumes
   from RFC-0071 — asserted to fall out for free, not independently verified here.
3. ~~Where a `view X for Struct` declaration is allowed to live, and its interaction
   with cross-module field visibility~~ — **substantially addressed by §4.11.**
   Declaring a view from outside the module reuses RFC-0032's existing pattern-matching
   private-field check unchanged; self-view narrowing never crosses the boundary at
   all. What §4.11 leaves genuinely open: exactly which pass enforces the private-field
   check at a view's *access* site (`v.private_field`) when the view itself was
   declared inside the module and later exposed outside it through a `pub` function —
   the mechanism isn't designed, only the failure case it must prevent.
4. **§4.6's coherence-avoidance needs verification once implemented, not just
   assertion.** The design intent is that a view's brand never reaches the
   coherence/impl-resolution pass; confirming no code path accidentally lets it leak in
   (the same class of gap RFC-0089 §3.1's Open Question 11 flags for its own
   brand-carrying exception) is future work, not settled here.
5. **§2's by-value struct pattern is scoped to this RFC's own needs, not a full
   proposal.** Whether it should be split into its own RFC (matching this project's
   general preference for decomposing shared/foundational grammar work — see issue
   #233's AST-generalization scoping) or folded permanently into RFC-0071's move
   semantics is not decided.
6. **Whether a view's `for` target may itself be generic** (`view X for Container<T> {
   field }`) — not addressed; out of scope for this draft.
7. **Whether tuple-of-views self-declarations (§4.9) should be allowed to nest, or mix
   a named view with a raw field reference** (e.g. `self: (&mut BarsView, &Token)`
   naming a field directly instead of via a one-field view) — not addressed; §4.9's
   worked example only shows named views in every slot.

---

## References

- Niko Matsakis, [View types for Rust](https://smallcultfollowing.com/babysteps/blog/2021/11/05/view-types/)
  — the motivating comparison this RFC closes the gap against.
- RFC-0044 (Explicit Receiver Semantics, implemented) — the three receiver forms this
  RFC amends.
- RFC-0067a (Reference Types, implemented) — precedent for amending RFC-0044; the
  `&T`/`&mut T` vocabulary self-views and reference-destructuring patterns build on.
- RFC-0090 (Structural Records — Rows and Tiers) — §9's `(row, brand)`
  representation §4.1 reuses; §8's tier system and its existing fiat-`Linear` bare-vs-
  branded exception §4.7 mirrors; §8's tier-3 coherence-eligibility boundary §4.6
  deliberately stays clear of.
- RFC-0091 (Linear Records) — §2.2's `(row, brand)` residual-reuse operation §4.1
  specializes; §2.1's open aliasing question §4.5 partially, not wholly, inherits;
  `drain_field`'s single-field asymmetric split, the gap §3 closes.
- RFC-0089 (Linear Types) §3.1 — the fiat-`Linear` brand-carrying exception to
  tier 2's bare-by-default rule, the precedent §4.7 extends.
- RFC-0032 (Field-Level Visibility, implemented) — the private-field-access check §4.11
  reuses for cross-module `view` declarations, and the rule a view exposed through a
  `pub` function must not be allowed to bypass.
- `brand-kind-unification.md` — the `(row, brand)`/`'c`-kind tag-reuse claim §4.1 and
  §5 depend on.
- RFC-0071 (Ownership and Move Semantics, accepted, unimplemented) — the field-
  sensitive move/borrow tracking both mechanisms in this RFC assume exists.
- RFC-0108 (Reference-Transparent Match Scrutinees) — adjacent pattern-position
  work; no direct dependency, noted for consistency.
- `src/ast/mod.rs` — `Pattern` enum, confirmed to have no struct-destructuring variant
  today, motivating §2.

---

## Decision

**Outcome:** *(pending)*
**Target:** *(set when accepted — not required for any current milestone; paper-only
territory pending RFC-0071)*

*(Decision rationale goes here when the RFC is evaluated.)*
