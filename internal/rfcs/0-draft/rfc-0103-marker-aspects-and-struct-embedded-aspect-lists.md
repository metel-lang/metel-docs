---
id: rfc-0103
title: "Marker Aspects and Struct-Embedded Aspect Lists"
date: '2026-07-14'
status: draft
target:
---

## Summary

A `marker` keyword for aspects permanently declared to have zero methods and zero associated types
(`marker aspect Copy2;`, itself bodyless per the same nothing-to-write theme as RFC-0102), plus a
struct/enum-declaration-embedded aspect list (`struct Token: Copy2, !Send { value: String }`) reusing
RFC-0102's `extend_aspect_list`. Positive items require the `marker` keyword — a *permanent* guarantee, not
just "currently has zero methods" — since a struct's body has no per-aspect slot to patch into if the
aspect later gains a real method; negative items are always allowed regardless of the aspect's own shape,
the same asymmetry RFC-0102 §3 already establishes for `extend` blocks. Depends on RFC-0102.

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

**Eligibility — deliberately narrower than RFC-0102 §5's extend-block list:**

| Item | Eligible when |
|---|---|
| `!Aspect` (negative) | Always — any aspect, any shape, regardless of methods or associated types (RFC-0081's polarity guarantee, independent of the aspect's own declaration) |
| `Aspect` (positive) | Only if `Aspect` is `marker`-declared |

Positive items do **not** get RFC-0102 §4's looser "currently zero methods, or all methods have a default"
rule here — an aspect that's all-default *today* could stop being all-default tomorrow (a default body
removed), and unlike an `extend` block, a struct declaration has nowhere to grow a method implementation
if that happens. Restricting positive struct/enum embedding to `marker`-declared aspects only is what makes
this position safe to have no escape hatch at all.

```metel
marker aspect Copy2;

struct Handle {
    id: i64,
}

// Composes with RFC-0080's real Send/Sync (auto-impl aspects): the compiler
// grants Send automatically based on field types, and the explicit negative
// override RFC-0080 §3 already specifies (`impl !Send for MyType {}`) is
// exactly the negative case this RFC's list embeds directly.
struct Token: Copy2, !Send {
    value: String,
}

// Rejected — Display is not marker-declared (it has a real required
// method), so it cannot appear positively in a struct-embedded list, even
// though `extend Token: Display { ... }` naming a real body is fine.
struct BadToken: Display {   // error: `Display` is not a marker aspect
    value: String,
}
```

Out of scope: conditional/generic aspect satisfaction (`struct Box<T>: SomeAspect` requiring a bound on
`T`) is not addressed here — the aspect list this RFC adds is unconditional, exactly like RFC-0102's own
`extend`-block lists. A generic struct that needs a *conditional* impl still writes an ordinary, separate
`extend<T: Bound> Box<T>: Aspect { ... }` block, unaffected by this RFC.

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
  matching `extend`-block eligibility exactly. Rejected (§2) — an all-default aspect can stop being
  all-default later (a default body removed), and unlike `extend` blocks, a struct declaration has no
  local fix available if that happens; restricting positive embedding to `marker`-declared aspects only is
  what makes the no-escape-hatch position safe.

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

---

## Decision

**Outcome:** *(pending)*
**Target:** *(set when accepted)*
