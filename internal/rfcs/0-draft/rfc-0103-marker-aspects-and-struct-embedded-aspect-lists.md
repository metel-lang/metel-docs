---
id: rfc-0103
title: "Marker Aspects and Struct-Embedded Aspect Lists"
date: '2026-07-14'
status: draft
target:
---

## Summary

Two related additions on top of RFC-0102. A `marker` keyword for aspects permanently declared to have
zero methods and zero associated types (`marker aspect Copy2;`, itself bodyless per the same
nothing-to-write theme as RFC-0102). And a struct/enum-declaration-embedded aspect list (`struct Token:
Copy2, Serializable, !Send { value: String }`) reusing RFC-0102's `extend_aspect_list`, where struct/enum
bodies stay fields-only — `marker`-declared and negative items are fully satisfied by the list itself,
while a non-`marker` positive item declares a checked, module-wide *obligation* discharged by an ordinary,
separately-editable `extend` block, not embedded inline. Depends on RFC-0102. (A third, related idea —
lifting RFC-0102 §5's bodyless-only restriction so an `extend` block can share a real, non-empty body
across multiple aspects — was split out to RFC-0104, since it's a separate feature that doesn't need
anything in this RFC to work.)

---

## Motivation

RFC-0102 makes `extend Type: Aspect;` and `extend Type: !Aspect;` legal whenever an empty body already
would be — for a positive aspect, that means "currently has zero methods, or every method has a default."
That's the right rule for `extend` blocks specifically, because there's always an escape hatch if the
aspect stops qualifying later: switch the same block to `extend Type: Aspect { fun the_new_method() {...}
}`. Two further ideas surfaced while drafting that RFC don't have that same escape hatch, and need their
own treatment:

1. **A struct or enum declaration has exactly one body, and it's the field/variant list — not a
   per-aspect slot.** `struct Token: Copy2 { value: String }` (this RFC's proposal) has nowhere to put a
   method implementation if `Copy2` later gains one; every struct embedding it would break with no local
   fix available, unlike an `extend` block, which can just grow a body. This needs a *permanent* guarantee
   that a positive aspect will never require an implementation — RFC-0102's "currently bodyless-eligible"
   rule isn't strong enough for this position.
2. **This project's docs corpus already uses the term "marker aspect" for exactly this permanent-zero-
   method case** — RFC-0080 §3 defines `Send`/`Sync` as "marker aspect[s] with no methods" (`aspect Send {
   }`), with `impl !Send for MyType {}` as the real, already-specified way to opt a type out of the
   compiler's automatic `Send` derivation. There's no dedicated syntax marking `Send`'s declaration as
   permanently bodyless today — this RFC gives that existing, already-named concept a real keyword, rather
   than inventing a new one.

Once a `marker`-declared aspect exists, embedding it (and any negative aspect) directly in the type's own
declaration — `struct Token: Copy2, !Send { ... }` — removes the boilerplate of a separate bodyless
`extend` block for a fact that's really part of describing what the type *is*, the same motivation
`class Foo : IBar` (C#), `class Foo implements Bar` (TypeScript), and `class Foo extends A with B` (Scala)
share, adapted to this language's own `extend`/aspect vocabulary rather than borrowed wholesale.

---

## 1. The `marker` keyword

```
aspect_decl = { pub_kw? ~ marker_kw? ~ "aspect" ~ ident ~ generic_params?
                 ~ (("{" ~ (assoc_type_decl | aspect_method)* ~ "}") | ";") }
```

The bodyless form (`;`) is legal if and only if `marker_kw` is present — mirroring RFC-0102's own theme
one production earlier, at the aspect's *declaration* rather than its implementation:

```metel
marker aspect Copy2;
```

`marker` is a **permanent commitment, enforced by the parser at the aspect's own declaration**: a
`marker`-qualified `aspect` may never declare a method or an associated type, in this declaration or any
future edit to it — attempting to add one is a compile error at the aspect declaration itself, not a
silent behavior change discovered later at some unrelated call site. Removing `marker` to turn a marker
aspect into an ordinary one is possible, but only by editing the aspect's own declaration to drop the
keyword — a deliberate, visible source change, after which every place that relied on the permanent
guarantee (§2's struct-embedded positive lists) gets an ordinary, clear compile error pointing at exactly
what broke, not a silent one.

An aspect *without* `marker` may still have an empty body today (`aspect Foo { }`) — that remains legal,
unchanged, and such an aspect still qualifies for RFC-0102's own `extend`-block bodyless sugar (which only
ever needs the weaker "currently has zero methods" guarantee). What a non-`marker` aspect does **not**
qualify for is §2's struct-embedded *positive* list — that position needs the permanent guarantee `marker`
provides, for the reason given in the Motivation: no fallback body position exists there.

## 2. Struct- and enum-embedded aspect lists

```
struct_decl = { pub_kw? ~ "struct" ~ ident ~ generic_params? ~ (":" ~ extend_aspect_list)?
                 ~ where_clause? ~ "{" ~ struct_fields ~ "}" }
enum_decl   = { pub_kw? ~ "enum" ~ ident ~ generic_params? ~ (":" ~ extend_aspect_list)?
                 ~ where_clause? ~ "{" ~ enum_variants ~ "}" }
```

`extend_aspect_list` is reused directly from RFC-0102 §5 (`bound ~ ("," ~ bound)*`) — the same
comma-separated, per-item-polarity list, in a new position. Both `struct` and `enum` get it, deliberately
symmetric: both have exactly one body reserved for their own shape (fields, variants), with the identical
no-fallback-position problem this RFC exists to solve for either one.

**Semantics: pure desugaring, same as RFC-0102 §5, just bundling the type declaration itself into the same
statement.** `struct Token: A, !B { value: String }` means precisely:

```metel
struct Token { value: String }
extend Token: A;
extend Token: !B;
```

**Eligibility.** Struct and enum bodies stay fields/variants-only — this RFC does not let a method
implementation live inside a `struct`/`enum` declaration's own braces. That constrains what a *positive*,
non-`marker` item in the list can mean, but doesn't rule it out the way an earlier draft of this RFC
assumed:

| Item | Eligible when | What it means |
|---|---|---|
| `!Aspect` (negative) | Always — any aspect, any shape, regardless of methods or associated types (RFC-0081's polarity guarantee, independent of the aspect's own declaration) | Fully satisfied by the list itself, same as an `extend Type: !Aspect;` block |
| `Aspect`, `marker`-declared | Always | Fully satisfied by the list itself, same as an `extend Type: Aspect;` block (RFC-0102 §4) |
| `Aspect`, not `marker`-declared | Always | **Declares an obligation, not an implementation** — see below |

**The obligation model for non-`marker` positive items.** Naming a real, non-`marker` aspect on a
struct/enum's own declaration doesn't try to satisfy it there (there's nowhere in a fields-only body to put
its methods) — it declares that the type *must* implement that aspect, checked module-wide against ordinary
`extend` blocks written elsewhere, the same ones you'd write without this RFC at all. `struct Token:
Serializable { value: String }` means: `Token`'s own declaration is unchanged, plus a checked obligation
that *some* `extend Token: Serializable { ... }` block exists (anywhere it would ordinarily be visible) and
passes its own already-existing completeness check. Forgetting to write that block is a compile error
reported at the struct's own declaration — earlier and more direct than today's alternative, where the gap
is only ever discovered wherever `Token: Serializable` happens to be required later.

This is why the earlier concern about "no escape hatch" (§1's motivation for requiring `marker` at all)
doesn't apply here: a non-`marker` positive item's real implementation lives in an ordinary, always-editable
`extend` block, exactly like it would without this RFC — the struct/enum-embedded list only ever adds a
forward-declared, checked *promise* that the block exists, never the implementation itself. `marker` still
matters for exactly one thing: whether the list *alone* is enough, or whether a separate `extend` block is
still required.

```metel
marker aspect Copy2;

aspect Serializable {
    fun serialize(&self) -> String;
}

struct Handle {
    id: i64,
}

// Copy2 (marker) is fully satisfied here; Serializable is not -- it's an
// obligation, discharged by the separate extend block below. Composes with
// RFC-0080's real Send/Sync (auto-impl aspects): the compiler grants Send
// automatically based on field types, and the explicit negative override
// RFC-0080 §3 already specifies (`impl !Send for MyType {}`) is exactly the
// negative case this RFC's list embeds directly.
struct Token: Copy2, Serializable, !Send {
    value: String,
}

extend Token: Serializable {
    fun serialize(&self) -> String { self.value }
}

// Rejected -- Token names Serializable but no extend block anywhere
// provides it. Error is reported at Token's own declaration line, not
// wherever Token: Serializable is later required.
struct BadToken: Serializable {   // error: no `extend BadToken: Serializable { ... }` found
    value: String,
}
```

Out of scope: conditional/generic aspect satisfaction (`struct Box<T>: SomeAspect` requiring a bound on
`T`) is not addressed here — the aspect list this RFC adds is unconditional, exactly like RFC-0102's own
`extend`-block lists. A generic struct that needs a *conditional* impl still writes an ordinary, separate
`extend<T: Bound> Box<T>: Aspect { ... }` block, unaffected by this RFC.

A non-`marker` positive item's obligation (above) is always discharged by an *ordinary* `extend` block —
that block may itself name more than one aspect and share a real body across them, under RFC-0104
(Multi-Aspect Extend Blocks with Shared Bodies), split out of an earlier draft of this section into its
own RFC since it's a separate feature that doesn't need anything here to work.

---

## Alternatives Considered

- **No dedicated `marker` keyword — reuse ordinary `aspect Foo { }` (currently empty) for struct/enum
  embedding too.** This was RFC-0102's own original position (an earlier draft of that RFC rejected a
  `marker` keyword, reasoning that the pain point was at impl sites, not the aspect declaration). Revisited
  and reversed here specifically because struct/enum embedding has no fallback body position — "currently
  empty" isn't a strong enough guarantee for a position with no escape hatch, where `extend`'s own weaker
  rule already has one.
- **A `#[derive(Aspect)]`-style attribute annotation instead of extending the type declaration's own
  grammar.** Rejected: this project already has a working comma-separated aspect-list mechanism from
  RFC-0102 §5; reusing it directly is smaller than introducing an entirely new attribute/annotation syntax
  for the same purpose.
- **Allow RFC-0102 §4's looser "all-default-methods" aspects into positive struct-embedded lists too**,
  matching `extend`-block eligibility exactly, treating them as fully satisfied by the list itself the same
  way `marker`-declared aspects are. Rejected — an all-default aspect can stop being all-default later (a
  default body removed), and unlike an `extend` block or the obligation model (§2), there'd be no local fix
  available if the list itself were treated as the complete implementation. `marker` remains the only way a
  positive item is satisfied *by the list alone*; a non-`marker` positive item is still allowed (§2), just
  as an obligation discharged elsewhere, never as an inline implementation.
- **Reject non-`marker` positive items entirely** (an earlier draft of this RFC's own position). Reversed
  in §2 once it became clear the "no escape hatch" concern only applies to items the list itself is trying
  to *implement* — a non-`marker` positive item never does that under the obligation model, so there's
  nothing unsafe about allowing it as a forward-declared, separately-checked promise.

---

## Unresolved Questions

1. **Tooling for `marker` removal.** This RFC states that removing `marker` from an aspect produces
   ordinary compile errors at every struct/enum-embedded positive use — sufficient, or does this need a
   dedicated migration diagnostic (e.g. listing every affected struct/enum in one message rather than one
   error per site)? Not blocking; a UX refinement for implementation time.
2. **A lint encouraging `marker` on aspects that are already permanently empty** (e.g. flagging `aspect Foo
   { }` with no methods and no plausible future ones, suggesting the author add `marker`) — out of scope
   for this RFC, which only specifies what `marker` *means*, not tooling that suggests using it.
3. **Confirm no interaction with RFC-0096 (Auto-Impl Aspects, draft)** — `Send`/`Sync`/`Linear` are granted
   automatically by the compiler based on field types, never via an explicit positive `extend` or embedded
   list; this RFC's positive-embedding case is for aspects a type *chooses* to implement, and its negative
   case (`!Send`) is exactly RFC-0080 §3's existing override, unchanged. This RFC asserts these don't
   collide, but it's worth confirming directly against RFC-0096's own mechanism once that RFC is further
   along, rather than assumed here.
4. **Where and when does §2's obligation check run?** It's inherently cross-declaration (a struct/enum's
   own list vs. one or more `extend` blocks that could appear anywhere the type is visible), unlike every
   other check in this RFC and RFC-0102, which are local to one declaration. This RFC doesn't pin down the
   exact pipeline stage — plausibly alongside existing coherence checking, which already runs as its own
   whole-module (or whole-graph) pass — nor whether the satisfying `extend` block may live in a different
   module than the struct/enum declaration itself. Needs real design work against the actual module-loading
   pipeline before implementation, not assumed here.
5. **Diagnostic quality for an unsatisfied obligation spanning multiple modules** — if `struct Token:
   Serializable { ... }` is declared in one module and the satisfying `extend Token: Serializable { ... }`
   is expected in another, a missing-obligation error should probably say where it looked, not just that it
   didn't find one. A UX concern for implementation time, not a blocking design question.

---

## References

- RFC-0102 (Bodyless Extend Blocks for Marker Aspects and Negative Impls) — this RFC depends on it
  directly: `extend_aspect_list` (§5) is reused verbatim for §2's struct/enum-embedded lists, and the
  negative-polarity-always-eligible rule (§3) is the same reasoning applied to embedding.
- RFC-0080 (Standard Library Aspects — Clone, Deref, Send, Sync) — §3 already calls `Send`/`Sync` "marker
  aspect[s] with no methods" and already specifies the negative override (`impl !Send for MyType {}`) this
  RFC's §2 lets be written as `struct MyType: !Send { ... }` instead; not amended, only given a name for its
  existing concept and a shorter spelling for its existing override syntax.
- RFC-0096 (Auto-Impl Aspects, draft) — the compiler-automatic-derivation mechanism for `Send`/`Sync`/
  `Linear`, distinct from and not amended by this RFC; see Unresolved Question 3.
- RFC-0098 (Surface Keyword Renames) — `extend Type: Aspect` grammar this RFC's struct/enum embedding
  parallels; not amended.
- RFC-0081 (Negative Impls) — the polarity mechanism §2's negative-always-eligible rule relies on,
  unchanged.
- RFC-0060 (Aspect Impl Coherence) — the existing duplicate/overlapping-impl detection that already governs
  what happens if a `marker`-declared struct-embedded item is also given a redundant, separate `extend`
  block for the same aspect; not amended, and §2's obligation check (a *different* question — does a
  satisfying impl exist at all, not whether two conflict) is meant to sit alongside it, not replace it.
- RFC-0104 (Multi-Aspect Extend Blocks with Shared Bodies) — split out of an earlier draft of this RFC's
  own §2; a non-`marker` positive item's obligation may be discharged by a multi-aspect `extend` block
  under that RFC's own rules, with no special interaction beyond what's already stated in either RFC.

---

## Decision

**Outcome:** *(pending)*
**Target:** *(set when accepted)*
