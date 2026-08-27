---
id: rfc-0144
title: "Reference-Destructuring Patterns"
date: '2026-08-27'
status: under-review
tracking: 'https://github.com/metel-lang/metel-core/issues/843'
---

> **Split from RFC-0109 (Self-View Narrowing and Reference-Destructuring Patterns),
> 2026-08-27.** RFC-0109's own §3 proposed this mechanism alongside named views
> (self-view narrowing), sharing motivation and a representation history with it, but
> the two are genuinely separable: named views are a small, mostly-inherited addition
> now that RFC-0137 (Nominal Types as Branded Rows) exists, while this mechanism is
> real, standalone grammar and pattern-matching work with its own soundness story,
> entirely gated on RFC-0071 regardless of what happens to RFC-0109. Bundling them
> risked exactly what this corpus's own process has flagged before (RFC-0012 →
> RFC-0092/93/94/95, RFC-0092 → RFC-0132, RFC-0124 → RFC-0133): a mix of readiness
> levels under one document delays the more-settled piece for no reason. See RFC-0109
> for the sibling mechanism and the cross-reference between them.
>
> **Corrected from RFC-0109's own draft, 2026-08-27**: the original text wrote this
> as `let &var { fields } = h;`. `let` in Metel's grammar (`let_decl`) binds a single
> bare identifier only — it has no pattern-destructuring form at all today, and this
> was never valid syntax to begin with, just an unexamined assumption carried over
> from languages where `let` and pattern-destructuring are the same construct. The
> correct forms, confirmed directly: `&var { fields } = h;` for the mutable case (no
> `let`, matched against an already-`&var`-typed scrutinee), and `{ fields } = &expr;`
> for the shared case (bare pattern, the reference taken on the right-hand side against
> a plain value) — asymmetric on purpose, not two spellings of one rule; see §2.
>
> **Also checked against the current AST, 2026-08-27**: RFC-0109's original §2 assumed
> Metel had no struct-destructuring pattern at all ("`Pattern` has exactly seven
> variants... no `Struct` case"). That's stale — `Pattern::Struct` and `Pattern::Record`
> both exist and are implemented today (`metel-frontend/src/ast/mod.rs`), landed by
> RFC-0032/RFC-0034/RFC-0107 sometime after RFC-0109 was drafted. This RFC needs no
> prerequisite by-value pattern work at all as a result — it builds directly on what's
> already shipped, plus one new pattern kind (§3).

> **Status — under review (2026-08-27).** Committed to v0.14.0 (issue #843, milestoned 2026-08-27), same milestone as sibling RFC-0109 (metel-core#842).

## Summary

Two forms, one mechanism: `&var { fields } = h;` and `{ fields } = &expr;` split an
existing or fresh reference to a struct into **disjoint per-field sub-references** in
one statement, narrowing the original's residual row the same way a partial move or
projection already does (RFC-0137 §2) — without going through an intermediate
`Type::Record` value, and without requiring the struct to opt into any conversion
tier. The ad hoc, one-off counterpart to RFC-0109's named views: reach for this when
a split is used once, reach for a named view when the same split is reused across
multiple call sites.

---

## Motivation

RFC-0116/RFC-0137's records-and-narrowing cluster solves the *reusable, named* half
of splitting a struct's fields for independent use (a `.{ field }` projection, or a
named `view` declaration per RFC-0109). Neither gives a caller a way to split a
reference into several disjoint live sub-references **in one statement, without
naming a type for it** — the case that's used once and doesn't merit declaring
anything:

```metel
fun rebalance(h: &var Handle) {
    &var { golden_tickets, bars } = h;
    // golden_tickets: &var Token, bars: &var Vec<Bar> — both live, disjoint borrows
    golden_tickets.redeem();
    bars.push(Bar::default());
}
```

Doing this today needs either two sequential field borrows (`let a = &var
h.golden_tickets; let b = &var h.bars;` — legal already, just repeats `h.` per field
and doesn't read as one operation) or RFC-0109's named-view machinery, disproportionate
ceremony for a split used exactly once.

**Deliberately not built on `to_record_mut()`.** Going through an intermediate
`{ ... }` value would force a tier-2 `ToRecord`/`FromRecord` derive requirement onto
every struct that wants to use this pattern — disproportionate to what the pattern
actually needs (structural field access, already legal on any struct via ordinary
`.field` syntax; this just does several disjoint borrows of it in one statement
instead of one at a time).

---

## 1. Syntax and semantics

Two forms, asymmetric on purpose — they answer different questions, not the same
question twice:

**Mutable form** — the pattern carries the `&var` sigil, matched against a scrutinee
that is *already* `&var`-typed:

```metel
fun rebalance(h: &var Handle) {
    &var { golden_tickets, bars } = h;
    golden_tickets.redeem();          // &var Token
    bars.push(Bar::default());        // &var Vec<Bar>
}
```

`h` is already `&var Handle`; the pattern peels that off and splits the row it
points at. There is nothing to take a reference *of* here — `h` already is one.

**Shared form** — the pattern is bare (no sigil), and the reference is taken on the
right-hand side of a plain, non-reference value:

```metel
fun peek(point: Point) {
    { x, y } = &point;
    // x: &i32, y: &i32 — point itself still usable afterward
}
```

`point` is an ordinary local, not a reference. `&point` takes a fresh shared
reference to it; the bare pattern on the left is what makes every produced binding a
reference rather than a move — reusing the reading `Pattern::Record` already has
elsewhere ("bare `{ x, y }` is always structural"), just resolved against a struct
scrutinee via the same type-directed mechanism `resolve_struct_pattern` already uses
for a bare one-segment `EnumVariant` (§3).

Both forms narrow the original binding's residual type the same way a partial move
or an explicit projection already does (RFC-0137 §2): after either statement above,
`h`/`point` is narrowed to the row with the named fields removed, same brand,
usable exactly as any other RFC-0137 residual is.

**`..` omits the rest, the same convention `Pattern::Record`'s `record_rest` already
uses**: `&var { golden_tickets, .. } = h;` borrows only `golden_tickets`, leaving
every other field reachable through `h` directly afterward (RFC-0137 narrowing, not
a second binding).

**Composes with RFC-0109's named views**: `{ fields } = &h;` and `let v: &View = h;`
(RFC-0109 §4.1's coercion, once that RFC exists) describe the same underlying split;
the difference is where it happens (inline, once, vs. named and reusable) and how
much has to be spelled out. Reach for a named view when the same split recurs across
call sites; reach for this when it doesn't.

---

## 2. A new pattern kind

Neither existing struct-shaped pattern fits. `Pattern::Struct` (named, `Point { x, y
}`) exists for ordinary by-value/by-mode struct matching — nothing about it commits
every binding it produces to being a reference, or narrows the scrutinee's own type
afterward instead of consuming/rebinding it. `Pattern::Record` is explicitly
documented as "always structural, matching `Type::Record`, never a named struct" —
the opposite of what this needs, which is a bare field list matched against a
*struct*. Reusing either would mean overloading a meaning that's already precisely
scoped elsewhere. A new variant instead:

```rust
/// A reference-destructuring pattern (`&var { fields }` / `{ fields } = &expr`) —
/// splits a struct-typed reference into N disjoint per-field sub-references,
/// narrowing the scrutinee's own residual type per RFC-0137 §2. Distinct from
/// `Pattern::Struct` (whose bindings follow whatever mode the match context
/// dictates generally): every binding this produces is a reference,
/// unconditionally, and the scrutinee stays live afterward at a narrowed row
/// rather than being consumed or rebound.
Struct {
    ...
},
Record {
    ...
},
RefDestructure {
    mutable: bool,   // &var vs &
    fields: Vec<String>,
    rest: bool,
    span: Span,
},
```

## 3. Type-directed resolution, reusing the existing mechanism

The parser never produces `RefDestructure` directly — the same deferred-resolution
shape `Pattern::Struct` itself already uses (its own doc comment: "never produced
directly by the parser… rewritten from a one-segment `EnumVariant`… once the
scrutinee's type identifies which struct is meant"). A bare `{ fields }` (optionally
preceded by `&var`/`&`) is ambiguous at parse time between three things the grammar
alone can't distinguish:

- an ordinary `Pattern::Record` match against a genuine `Type::Record` scrutinee,
- an ordinary `Pattern::Struct` match (once resolved) against a struct scrutinee in
  by-value match position,
- this RFC's `Pattern::RefDestructure`, when the leading sigil (or the right-hand
  side's `&`) marks it as a reference split rather than an ordinary match.

Resolution follows the scrutinee's type, the same pass that already disambiguates
`Pattern::Struct` from a bare `EnumVariant`: a `Type::Record` scrutinee keeps
`Pattern::Record`'s existing meaning unchanged; a struct-typed scrutinee under a
reference-destructuring statement (§1's two forms specifically, not ordinary
`match`) resolves to `Pattern::RefDestructure`. No grammar ambiguity is introduced —
this is exactly the same class of one-token-lookahead-insufficient, type-driven
resolution the corpus already has a working mechanism for, applied a second time.

---

## 4. Checking rule

Legal wherever ordinary sequential field borrows of the same disjoint fields would
already be legal one at a time (`let a = &var h.golden_tickets; let b = &var
h.bars;` — assumed sound once RFC-0071's field-sensitive move/borrow tracking
exists, same baseline field-sensitivity Rust itself relies on). The pattern form
grants no new aliasing power; it grants doing several such borrows in one statement
without repeating `h.`/`&var h.` per field. **Because RFC-0071 is `3-integrated` but
its move-check is off by default** (`metel-frontend/src/move_check/`, gated behind
`--move-check`), nothing here can be more than a specification of intended behavior
against a checker that exists but isn't yet the default path — the same footing
RFC-0109 stands on for its own mechanism.

---

## 5. Interaction with adjacent RFCs

- **RFC-0137 (Nominal Types as Branded Rows, `1-under-review`)** — both forms narrow
  the scrutinee's residual type exactly as §2 there already specifies for a partial
  move or projection; this RFC adds no new narrowing rule, only a new *statement
  shape* that triggers the existing one for several fields simultaneously instead of
  one at a time.
- **RFC-0109 (Self-View Narrowing, `1-under-review`, sibling — split from the same original draft)** —
  the named, reusable counterpart to this ad hoc, one-off mechanism; §1 above states
  the relationship precisely.
- **RFC-0032 (Field-Level Visibility, implemented)** — a `RefDestructure` pattern's
  field list is checked against the scrutinee's struct exactly like an ordinary
  struct pattern's ("explicitly naming a private field in a pattern is a compile
  error") — reused, not reinvented; no new visibility rule needed.
- **RFC-0108 (Reference-Transparent Match Scrutinees)** — no direct dependency, but
  this RFC's forms and RFC-0108's own scrutinee-peeling rule should stay consistent,
  for the same reason RFC-0107/0108 already cross-reference each other.
- **RFC-0071 (Ownership and Move Semantics, `3-integrated`, move-check implemented
  behind `--move-check`)** — the field-sensitive borrow tracking both statement
  forms assume exists; the hard blocker, same as for RFC-0109.

---

## Alternatives considered

- **`let &var { fields } = h;`** — RFC-0109's original spelling. Rejected: `let` in
  Metel's grammar binds a single bare identifier only (`let_decl`), never a pattern.
  Never valid syntax; corrected here, not merely restyled.
- **Reuse `Pattern::Record` directly**, treating a struct scrutinee as coercing to
  `Type::Record` first. Rejected: `Pattern::Record`'s own documentation reserves it
  for genuine anonymous records specifically — reusing it here would blur a
  distinction the AST already draws on purpose, and would force exactly the
  `to_record_mut()` ceremony the Motivation explains this mechanism exists to avoid.
- **A dedicated `split_mut<F1, F2>()` primitive instead of a pattern.** Rejected as
  the primary mechanism, matching RFC-0109's own reasoning for the same
  alternative: row-generic parameters spelled out at every call site is
  disproportionate for what is, in the common case, an ordinary local split of a
  handful of named fields. Might be worth adding later as a genuinely generic,
  reusable helper — additive, not a replacement.

---

## Open Questions

1. **Soundness of the checking rule against genuinely overlapping (not just
   sequential) later use** — carried from RFC-0109's own Open Question 2, the same
   shape here: asserted to fall out from RFC-0071's field-sensitive reasoning, not
   independently verified in this document.
2. **Whether `Pattern::RefDestructure` should be restricted to top-level statement
   position, or may nest** (e.g. as one arm's sub-pattern inside a `match`, or
   inside `Pattern::Tuple`) — not addressed; §1's examples only show it as a
   standalone statement.
3. **Interaction with a scrutinee that's already partially narrowed** (some field
   already moved out or view-narrowed before this statement runs) — the same
   partially-consumed-residual question RFC-0109 §4.5 raises for self-views, likely
   the identical underlying question asked from the pattern side instead of the
   parameter-type side; not resolved independently here.

---

## References

- RFC-0109 (Self-View Narrowing, `1-under-review`) —
  the sibling this RFC was split from; the named/reusable counterpart to this ad hoc
  mechanism.
- RFC-0137 (Nominal Types as Branded Rows, `1-under-review`) — the narrowing
  semantics both statement forms trigger; this RFC adds no narrowing rule of its
  own, only the statement shape that invokes it for several fields at once.
- RFC-0071 (Ownership and Move Semantics, `3-integrated`, move-check implemented
  behind `--move-check`) — the field-sensitive borrow tracking this RFC's checking
  rule assumes exists; the hard blocker.
- RFC-0032 (Field-Level Visibility, implemented) — the private-field-in-a-pattern
  check this RFC reuses unchanged.
- RFC-0108 (Reference-Transparent Match Scrutinees) — adjacent pattern-position
  work, no direct dependency, noted for consistency.
- `metel-frontend/src/ast/mod.rs` — `Pattern::Struct`/`Pattern::Record`, confirmed
  already implemented (contradicting RFC-0109's original, stale claim that no
  struct-destructuring pattern exists at all); `resolve_struct_pattern`, the
  type-directed resolution mechanism §3 reuses.

---

## Decision

**Outcome:** *(pending)*
**Target:** *(set when accepted — not required for any current milestone; paper-only
territory pending RFC-0071, same footing as RFC-0109)*
