---
id: rfc-0109
title: "Self-View Narrowing"
date: '2026-07-18'
status: under-review
target:
updated: '2026-08-27'
tracking: 'https://github.com/metel-lang/metel-core/issues/842'
---

> **Paper-only territory, more so than most drafts in this cluster.** This RFC's
> checker rules are meaningless without RFC-0071's affine move/borrow tracking, which
> is `3-integrated` — **corrected 2026-08-27: move-check is actually implemented**
> (`metel-frontend/src/move_check/`), just off by default behind `--move-check`; the
> original claim here ("confirmed 0% implemented") was stale even before this
> revision, the same correction RFC-0137 §8 needed for the same claim. Everything
> here describes intended behavior once `--move-check` is the default path, the same
> footing RFC-0091 (Linear Records) and RFC-0144 (Reference-Destructuring Patterns,
> split from this RFC) stand on.
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
> with independent `&`/`&var` modes per slot, checked pairwise-disjoint via §4.4 and
> unpacked in the body via ordinary `Pattern::Tuple` — no new grammar, no new
> mutability axis, just composing mechanisms already specified elsewhere in this RFC.
>
> **Revised 2026-07-24 — mechanical syntax sweep, plus one finding.** RFC-0090 dropped the
> `record` keyword from the anonymous type-former, so every `record { … }` here is now
> `{ … }`. The §4 revision note above is left quoting the original `self: &record { field:
> Type }` spelling, since it is describing what the first draft said.
>
> **Split 2026-08-27 — reference-destructuring patterns moved to RFC-0144.** The
> original draft's §2 (by-value struct patterns) and §3 (reference-destructuring
> patterns) shared motivation and representation history with this RFC's named-view
> mechanism, but are genuinely separable: §2's own premise — "Metel has no
> struct-destructuring pattern at all" — is now stale (`Pattern::Struct`/
> `Pattern::Record` both exist and are implemented, landed by RFC-0032/RFC-0034/
> RFC-0107 after this RFC was first drafted), so no prerequisite work was needed
> there at all. §3's mechanism is real, standalone grammar/pattern-matching work
> with its own soundness story (a new `Pattern::RefDestructure` AST kind), entirely
> gated on RFC-0071 regardless of what happens to this RFC — bundling the two risked
> the "mixed readiness" problem this corpus's process has flagged three times before
> (RFC-0012→RFC-0092/93/94/95, RFC-0092→RFC-0132, RFC-0124→RFC-0133). See RFC-0144
> for that mechanism and the precise relationship between the two.
>
> **Reconciled against RFC-0137, 2026-08-27 — the substantial revision.** RFC-0137
> (Nominal Types as Branded Rows) didn't exist when this RFC's `(row, brand)`
> representation was first drafted against the now-superseded RFC-0090 §9/RFC-0091
> §2.2. It generalizes almost exactly what §4 needs: every struct already has
> `(brand, row)`, narrowing (partial move or projection) already produces a
> same-brand residual, that residual's brand is already never visible to structural
> matching regardless of row width, and a parameter typed as a struct's own residual
> is already ordinary type-matching (RFC-0137 §2-§4). Checked point by point below —
> **a named view is now a name for an RFC-0137 residual type, not a separate
> mechanism that happens to reuse the same representation.** §4 is rewritten
> around this; several of the original draft's own Open Questions dissolve as a
> direct consequence rather than being separately resolved.

> **Status — under review (2026-08-27).** Committed to v0.14.0 (issue #842, milestoned 2026-08-27) — one release after RFC-0137's own (v0.13.0, metel-core#827), since this RFC's foundation is now RFC-0137's specifics directly, not just its theme.
> **New downstream dependent, 2026-08-28 — milestone unchanged (v0.14.0).** RFC-0137 §5 was amended so that a `Drop` impl's required field set is *declared on the `drop` receiver type* rather than inferred from the body. The fixed form of that receiver — `fun drop(&var self: Self.{ fd })`, specified by **RFC-0147 (Projection-Receiver Destructors, metel-core#887)** — is precisely this RFC's residual-typed-receiver mechanism (§2). RFC-0147 therefore depends on this RFC and follows it into **v0.14.0** — the "view frontier" milestone the roadmap already places self-view narrowing in, alongside RFC-0121 and RFC-0144. (An intermediate move of #842 to v0.13.0 was reverted: v0.13.0 is records-core and does not include the view work.) RFC-0137's own branded-rows representation stays v0.13.0; only §5's narrowed `Drop` receiver forms wait for this RFC. The row-parametric form is **RFC-0148**, later still, via RFC-0146 → RFC-0121.

## Summary

`view TicketView for Ticketing { golden_tickets }` declares a name for a **residual
type** RFC-0137 already produces — `Ticketing.{ golden_tickets }` — nothing more.
**Self-view narrowing** — an inherent method's `self` parameter declared as
`&TicketView`/`&var TicketView` — is the primary application: a `self` parameter
typed as the struct's own residual, checked by the compiler with no call-site syntax
and no `ToRecord`/`FromRecord` tier opt-in required, exactly as RFC-0137 §4 already
specifies for any residual-typed parameter. `self` may also be a **tuple of views**
with independently-moded slots for mixed-mode access, Metel's answer to Rust's
`&{bars, mut golden_tickets} self` — the one piece of this RFC that's genuinely new
machinery rather than inherited.

The ad hoc, one-off counterpart — splitting a reference into several disjoint
sub-references without naming anything — is RFC-0144 (split from this RFC's
original draft), not this document.

---

## Motivation

RFC-0117/RFC-0119/RFC-0137, as currently scoped, solve the *reusable, generic* half
of Rust's view-types motivation — `.{ field }` projection and RFC-0137's own residual
types work across any struct — but give a *caller* no way to name and reuse a
specific sub-shape across multiple call sites without repeating the field list (an
inline `Self.{ fd }` parameter type) or losing the brand entirely (RFC-0119's
`to_record()`, which strips it on purpose, RFC-0119 §3). Rust's own example:

```rust
fn should_insert_ticket(&self, ...) -> bool  // only touches self.golden_tickets

// caller:
let bars = self.bars;                  // move a field out
self.should_insert_ticket(&other);     // works with view types: self's other fields
                                        // stay usable even though bars was moved out
```

Metel's residual types (RFC-0137) already make the *callee* side of this work — a
method can already declare `self: Self.{ golden_tickets }` and get exactly the
narrowing this needs. What's missing is a **name** for that shape, reusable across
every method that wants the same narrowing, instead of repeating the field list at
every declaration and hoping they stay in sync by eye. That's the entire remaining
gap this RFC closes.

---

## 1. Declaration: a name for a residual type

```metel
struct Ticketing { golden_tickets: Token, bars: Vec<Bar> }

view TicketView for Ticketing { golden_tickets }
```

The field list is bare — no re-declared types; `golden_tickets`'s type is looked up
from `Ticketing`'s own declaration, not restated, avoiding the divergence risk a
re-typed field list would create. This declares `TicketView` as a name for
`Ticketing.{ golden_tickets }` (RFC-0137 §2's residual type of `Ticketing`, narrowed
to that one field) — nothing about the representation is new; only the name is.

```metel
fun example(h: &var Ticketing) {
    let v: &var TicketView = h;   // RFC-0137 §2's narrowing, spelled through the alias
    v.golden_tickets.redeem();
}
```

**A view's `for` target must name a concrete struct in scope**, and (§2 below) a
method may only declare `self` as a view whose `for` target is that method's own
enclosing `impl` type — a view can't be used to make one function generic across two
unrelated structs that happen to share a field name. Nothing new here either: RFC-
0137 §3's eligibility gate already ties a residual's brand to exactly one struct;
this restriction is that gate, not a separate rule invented for `view`.

**Everything §4.2 of the original draft argued from scratch — that a view can't
satisfy a *generic* structural bound the way an anonymous record could, because its
brand is exactly the struct's own brand — is now simply RFC-0137 §3's eligibility
gate, inherited, not re-derived.** A named view's row is never visible to structural
matching, at any width, for the same reason a plain struct's own residual isn't
(RFC-0137 §3's worked example covers exactly this shape already).

## 2. Self-view narrowing

```metel
extend Ticketing {
    fun should_insert_ticket(self: &TicketView, idx: usize) -> bool {
        self.golden_tickets.matches(idx)
    }
}

fun example(t: &var Ticketing) {
    let bars = &var t.bars;
    if t.should_insert_ticket(0) {      // legal: TicketView's row is disjoint from
                                          // `bars`, same brand as t — no ceremony here
        bars.push(Bar::default());
    }
}
```

The caller writes nothing beyond an ordinary method call. No `.to_record()` appears
anywhere; the promise lives entirely in `should_insert_ticket`'s own signature. This
is RFC-0137 §4 ("Passing a residual to a function") applied to `self` specifically —
`self: &TicketView` is exactly `self: &Ticketing.{ golden_tickets }`, spelled through
the alias, checked the same way any residual-typed parameter already is. Because this
never touches `ToRecord`/`FromRecord`/coherence at all (RFC-0137 §3 again — a plain
struct's row is never visible to impl resolution), self-view narrowing needs **no
tier opt-in**, applying to plain structs exactly as freely as to RFC-0120's
opt-in-tier ones.

**Field-access accuracy is ordinary type-checking, not a bespoke pass.** If
`should_insert_ticket`'s body read `self.bars`, that's a plain type error — `self`'s
declared type (`Ticketing.{ golden_tickets }`, via the alias) doesn't have `bars` in
its row. The original draft framed this as a soundness-relevant checking pass this
RFC needed to specify (mirroring RFC-0091 §1's `uses(fd)` checking discipline); under
the RFC-0137 reading it's not a new checking philosophy at all, just the field-access
rule every residual type already has.

## 3. Composition and disjointness

Two views of the same struct are two named points in RFC-0137 §2's subset lattice,
so both properties that matter are inherited, not separately defined:

- **Narrowing/widening between views composes** — ordinary row-shrink/grow on one
  fixed brand (RFC-0137 §2), nothing view-specific to add.
- **Disjointness is inherited, not re-derived**: `TicketView` (`{golden_tickets}`) and
  `view BarsView for Ticketing { bars }` are safe to hold simultaneously exactly when
  their rows don't intersect — the same subset-lattice reasoning RFC-0137 §2 already
  specifies, checked once, structurally.

---

## 4. Not a tier-2 exception — a view was never a conversion output

The original draft framed a view's brand-carrying-ness as a *third exception* to
RFC-0090 §8's "tier 2 output is bare by default" rule, alongside RFC-0089 §3.1's
fiat-`Linear` carve-out. **That framing doesn't survive the RFC-0137 reading, and
should be dropped rather than patched.** A view was never a `to_record()`/
`to_record_mut()` output at all — it's a name for a struct's own RFC-0137 residual,
which was never unbranded to begin with (narrowing preserves the brand
unconditionally, RFC-0137 §2). There's no bare-by-default rule to except `view`
from, because `view` never enters tier 2's conversion path in the first place. RFC-
0089 §3.1's fiat-`Linear` exception remains exactly what it was; this RFC no longer
claims to be a second instance of it.

---

## 5. Deliberately no mixed per-field mutability

Rust's `&{bars, mut golden_tickets} self` mixes shared and exclusive access to
different fields in one view. This RFC does not — a view is uniformly `&View` or `&mut
View`, matching RFC-0044's existing all-or-nothing `&self` / `&var self` split (Metel
has no per-field mutability anywhere else in the language either). **Considered and
declined for v1:** per-field mutability inside a view would need new grammar (`mut
golden_tickets` inside a field list, meaning something different from the field's own
declared mutability) and a second mutability axis nothing else in the language has.
Narrower scope: a view is exclusive-or-shared as a whole, over whichever field subset
it names. §6's tuple-of-views is the intended escape hatch for the mixed-mode case.

## 6. Mixed-mode methods: a tuple-of-views `self`

`self` may be declared as a **tuple of views**, each with its own independent
`&`/`&var` mode, checked pairwise-disjoint via §3:

```metel
view BarsView for Ticketing { bars }
view TicketView for Ticketing { golden_tickets }

extend Ticketing {
    fun redeem_and_log(self: (&var BarsView, &TicketView)) {
        let (bars, tickets) = self;    // ordinary Pattern::Tuple destructure —
                                        // already in the AST, nothing new needed
        if tickets.golden_tickets.matches(0) {
            bars.bars.push(Bar::default());
        }
    }
}

fun example(t: &var Ticketing) {
    t.redeem_and_log();   // ordinary call — no new syntax, same as any &var self method
}
```

This reuses three things that already exist rather than adding a fourth mutability
axis: ordinary tuple types, §3's disjointness check (generalized from a pair to
however many views a tuple names — every pairwise combination among the N elements
must be disjoint, a mechanical extension, not a new rule), and `Pattern::Tuple` for
unpacking `self` in the body. No new grammar for mixed modes: each tuple slot stays
uniformly `&View` or `&var View` — the mixing happens *across* slots, never within
one.

**Addressability follows the tightest slot — Rust's own reborrowing rule, not a new
one.** A tuple self-declaration containing at least one `&var ViewX` element can only
be satisfied by a caller holding (or able to produce) `&var Ticketing` for the whole
receiver: you cannot manufacture new exclusive access out of a shared borrow, only
subdivide an already-exclusive borrow into a mix of exclusive and shared
sub-borrows. A tuple where every slot is `&ViewX` only ever needs `&Ticketing`. This
extends RFC-0044 §9's addressability table by one row rather than replacing it.

**Worked example, in RFC-0044 §9's own allowed/disallowed style:**

```metel
extend Ticketing {
    // all-shared tuple: only ever needs &Ticketing, same as an ordinary &self method
    fun summarize(self: (&TicketView, &BarsView)) -> String { ... }

    // mixed tuple: at least one &var slot, needs &var Ticketing
    fun reconcile(self: (&var BarsView, &TicketView)) { ... }
}

var t = Ticketing { golden_tickets = Token::new(), bars = vec![] };
t.summarize();     // &Ticketing suffices — t is addressable, var not required
t.reconcile();     // t is mutably addressable, so the &var-containing tuple is satisfied

let shared: &Ticketing = &t;
shared.summarize();   // all-shared tuple — an ordinary shared reference is enough
// shared.reconcile();
// ERROR: reconcile's self contains a &var slot, which needs &var Ticketing for the
// whole receiver — the same failure as calling an ordinary &var self method through
// a &T (RFC-0044 §9's own `(&counter).increment()` case), just triggered by one slot
// out of several rather than the receiver's only mode.
```

**Accuracy checking for the tuple case is where the original draft's bespoke pass
still earns its place** — unlike §2's single-view case (ordinary type-checking
already rejects an out-of-row access), a tuple's slots are separate types, so an
access through one slot's binding that only *another* slot's row covers must be
rejected specifically: `bars.golden_tickets` inside `redeem_and_log` above is an
error even though `golden_tickets` is reachable via `tickets` in the same scope,
because `bars`'s own declared type (`&var BarsView`) doesn't include it. Each binding
is checked against its own slot's row, not the tuple's union — the union only
matters for deciding whether the method may exist against a given receiver at all.

---

## 7. Interaction with RFC-0091 Option C (partially-consumed residuals)

This inherits part of RFC-0091 §2.1's still-unproven aliasing question, but only the
part that's actually the same question:

- **A view borrowed from an intact struct — no prior partial move involved — is an
  ordinary RFC-0137 residual read, not a move.** It never touches RFC-0091 Option
  C's downgrade machinery at all. This is also Rust's own motivating scenario for
  view types, so it's the common case, not the edge case.
- **Checking a self-view against an already-partially-consumed residual** — some
  field was previously moved out via RFC-0091 Option C, and a later call's declared
  view needs to fit inside what remains — genuinely is the same question RFC-0091
  §2.1 leaves open, and this RFC does not resolve it independently. Mechanically
  it's an ordinary RFC-0137 §2 subset check (does `TicketView`'s row fit inside `t`'s
  currently-live row, same brand) once RFC-0091 Option C settles what "currently-live
  row" means after a downgrade — not a separate soundness argument to construct. If
  Option C never gets one, this RFC's §2 still stands on its own for the intact-struct
  case; only this already-partially-moved interaction falls back to something more
  conservative (e.g. rejecting the call once any field has been consumed).

## 8. Interaction with RFC-0032 field visibility

Two cases, worth separating because only one is actually novel.

**Self-view narrowing never crosses the module boundary at all.** Every self-view/
tuple-of-views declaration lives inside an inherent `impl` block, and inherent impls
are restricted to a type's own declaring module. So a method declaring `self:
&TicketView` is always written where every field of `Ticketing` — private or `pub` —
is already visible; RFC-0032 has nothing to check here.

**Declaring a view from outside the module is checked exactly like a struct
pattern** — a `view`'s field list is a list of field names checked against `Struct`,
the same shape RFC-0032's own pattern-matching rule already covers ("explicitly
naming a private field in a pattern is a compile error").

**The genuinely open case — worth flagging as likely RFC-0137's own gap, not
specific to `view`:** a view declared inside the module, naming a private field,
then exposed outside it through an ordinary `pub` function:

```metel
// ticketing.mln
view BarsView for Ticketing { bars }   // legal here — bars is private, this is
                                         // Ticketing's own module

pub fun peek_bars(t: &var Ticketing) -> &var BarsView { t }   // ordinary RFC-0137
                                                                 // narrowing coercion

// caller.mln
let v = peek_bars(&var t);
v.bars.push(Bar::default());
// must still be an error — bars is private to ticketing.mln
```

If field access through a residual only checked visibility at the *declaration*
site, this would silently defeat RFC-0032 — any `pub` function returning a residual
over a private field becomes an unintended backdoor. **This isn't actually a
`view`-specific problem**: `pub fun peek(t: &var Ticketing) -> &var Ticketing.{ bars
}` has the identical shape with no `view` involved at all, since RFC-0137 residuals
are ordinary types a function can return. The check has to be re-applied at the
point of *access*, against the field's own visibility on `Ticketing`, regardless of
how the residual type reached the caller — but that's a gap in RFC-0137's own
field-visibility story, not something this RFC introduces or should solve
independently. **Recorded here because this is where it was found; the fix, if one
is needed, belongs in RFC-0137.**

---

## 9. Interaction with other RFCs

- **RFC-0044 (Explicit Receiver Semantics, implemented)** — amended. The three
  receiver forms (`self`, `&self`, `&var self`) are unchanged; self-view narrowing
  adds an optional named-view refinement *to* `&self`/`&var self`, not a fourth
  receiver kind. §6's tuple-of-views `self` extends §9's addressability table by one
  row rather than replacing it. Precedent for amending RFC-0044 already exists
  (RFC-0067a).
- **RFC-0137 (Nominal Types as Branded Rows, `3-integrated`)** — supplies
  everything §1-§3 above used to derive independently: the `(brand, row)`
  representation, the eligibility gate, residual-typed parameters, and the subset
  lattice. This RFC now depends on RFC-0137 directly rather than on the superseded
  RFC-0090/RFC-0091 vocabulary it originally cited for the same ideas.
- **RFC-0120 (Named Records, `2-accepted`)** — a named view stays outside
  RFC-0120's tier system entirely (§1, §4) — it's a name for a plain struct's own
  residual, not an opt-in named-record declaration; the two mechanisms don't
  overlap despite superficially similar syntax (`view X for T { … }` vs. `record X {
  … }`).
- **RFC-0091 (Linear Records, `0-draft`)** — §7 above specializes part of its §2.1
  open aliasing question, inheriting only the part that's actually the same
  question.
- **RFC-0032 (Field-Level Visibility, implemented)** — §8's private-field checks,
  reused directly; §8 also identifies a gap that belongs to RFC-0137, not to this
  RFC.
- **RFC-0071 (Ownership and Move Semantics, `3-integrated`, move-check implemented
  behind `--move-check`)** — both mechanisms in this RFC are inert without
  RFC-0071's field-sensitive borrow tracking being the default path; see the status
  note at the top.
- **RFC-0144 (Reference-Destructuring Patterns, `1-under-review`, split from this RFC)** —
  the ad hoc, one-off counterpart; §1 above states the relationship precisely.
- **RFC-0108 (Reference-Transparent Match Scrutinees)** — no direct dependency,
  noted for consistency with RFC-0144's own note.

---

## Alternatives considered

- **Anonymous, brandless self-views** (`self: &{ golden_tickets: Token }`, this
  RFC's own original spelling before its first revision). Superseded, not merely
  rejected: it worked, but required re-deriving the ambient-typing safety argument
  from "declared inside an inherent impl" each time, gave no free reversibility or
  view-to-view composition, and left named-view reuse unanswered. The branded design
  — now understood as "a name for an RFC-0137 residual" rather than new machinery —
  is strictly less new surface for strictly more capability.
- **Adopt Rust's `&{a, b}` sigil syntax directly**, instead of a `view` declaration.
  Rejected: it would be a second, unrelated way to spell "a set of field names"
  alongside the one this cluster already has, for no expressiveness gain, and has no
  natural resting place for a name or a brand the way a declaration does.
- **Require self-view narrowing to go through tier 2** (a struct must derive
  `ToRecord`/`FromRecord` before its methods can declare narrowed self-views).
  Rejected — §2 shows this isn't needed for soundness (it's ordinary RFC-0137
  residual-parameter typing), and requiring it would be pure, unjustified ceremony.

---

## Open Questions

1. ~~Named, reusable views~~ — **resolved**: `view X for Struct { fields }`, now
   understood as a name for an RFC-0137 residual type rather than separate
   machinery.
2. **Multiple, separately-declared narrowed method calls with overlapping
   lifetimes** — distinct from §6's resolved case (one method, mixed modes, split at
   call entry). Here two *different* methods, each narrowed to disjoint views,
   called with genuinely overlapping (not just sequential) lifetimes. §3's
   disjointness check covers the shape in principle; whether the checker's
   call-lifetime reasoning composes correctly for overlapping calls needs the same
   reasoning §2 already assumes from RFC-0071 — asserted to fall out for free, not
   independently verified here.
3. ~~Where a `view X for Struct` declaration is allowed to live, and its interaction
   with cross-module field visibility~~ — **substantially addressed by §8.** What
   §8 leaves genuinely open — and now attributed to RFC-0137, not this RFC — is
   exactly which pass re-checks field visibility at a residual's *access* site when
   it reached the caller through a `pub` function, regardless of whether a named
   `view` was involved at all.
4. ~~§4.6's coherence-avoidance needs verification once implemented, not just
   assertion.~~ — **dissolved, 2026-08-27.** Under the RFC-0137 reading there's no
   new code path to verify: a view's brand not reaching coherence is RFC-0137 §3's
   existing exclusion, already established there, not a property this RFC's own
   implementation needs to separately maintain.
5. ~~§2's by-value struct pattern is scoped to this RFC's own needs, not a full
   proposal — split into its own RFC, or fold into RFC-0071?~~ — **moot,
   2026-08-27.** §2 no longer exists in this RFC at all: `Pattern::Struct`/
   `Pattern::Record` were already implemented by the time this reconciliation
   happened (RFC-0032/RFC-0034/RFC-0107), and the reference-destructuring mechanism
   that motivated §2 moved to RFC-0144, which needed no by-value prerequisite either.
6. **Whether a view's `for` target may itself be generic** (`view X for Container<T>
   { field }`) — not addressed; out of scope for this draft.
7. **Whether tuple-of-views self-declarations (§6) should be allowed to nest, or mix
   a named view with a raw field reference** (e.g. `self: (&var BarsView, &Token)`
   naming a field directly instead of via a one-field view) — not addressed; §6's
   worked examples only show named views in every slot.

---

## References

- Niko Matsakis, [View types for Rust](https://smallcultfollowing.com/babysteps/blog/2021/11/05/view-types/)
  — the motivating comparison this RFC closes the gap against.
- RFC-0044 (Explicit Receiver Semantics, implemented) — the three receiver forms this
  RFC amends.
- RFC-0067a (Reference Types, implemented) — precedent for amending RFC-0044; the
  `&T`/`&var T` vocabulary self-views build on.
- RFC-0137 (Nominal Types as Branded Rows, `3-integrated`) — supplies the
  representation, eligibility gate, residual-parameter typing, and subset lattice
  §1-§3 above build directly on, superseding this RFC's original citations of
  RFC-0090 §9 / RFC-0091 §2.2 for the same ideas.
- RFC-0120 (Named Records, `2-accepted`) — the tier system a named view stays
  deliberately outside of (§1, §4).
- RFC-0091 (Linear Records, `0-draft`) — §2.1's open aliasing question, partially
  inherited by §7.
- RFC-0089 (Linear Types, `0-draft`) §3.1 — the fiat-`Linear` brand-carrying
  exception; §4 explains why this RFC no longer claims to be a second instance of
  it.
- RFC-0032 (Field-Level Visibility, implemented) — the private-field-access check §8
  reuses; the rule a view exposed through a `pub` function must not be allowed to
  bypass.
- RFC-0071 (Ownership and Move Semantics, `3-integrated`, move-check implemented
  behind `--move-check`) — the field-sensitive move/borrow tracking both mechanisms
  in this RFC assume exists.
- RFC-0144 (Reference-Destructuring Patterns, `1-under-review`, split from this RFC) — the
  ad hoc, one-off counterpart to named views.
- RFC-0108 (Reference-Transparent Match Scrutinees) — adjacent pattern-position
  work, noted for consistency.

---

## Decision

**Outcome:** *(pending)*
**Target:** *(set when accepted — not required for any current milestone; paper-only
territory pending RFC-0071's move-check becoming the default path)*

*(Decision rationale goes here when the RFC is evaluated.)*
