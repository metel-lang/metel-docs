---
id: rfc-0102
title: "Bodyless Extend Blocks for Marker Aspects and Negative Impls"
date: '2026-07-14'
status: accepted
target:
updated: '2026-07-14'
---

> **Status — accepted (2026-07-14).** Reviewed and revised: extended to a comma-separated multi-aspect list (S5), and the negative-impl braces spelling retired outright (bodyless is now mandatory, not just sugar), matching this project's own precedent (RFC-0100, RFC-0042) for retiring a strictly-superseded old spelling. No open questions block it.

## Summary

`extend Type: Aspect;` and `extend Type: !Aspect;` (no braces) as sugar for an empty-bodied `extend` block, valid in exactly the situations an empty body is already accepted today (negative impls, always; positive impls when every method has a default or the aspect declares none). Mirrors `fun_decl`'s existing `(block | ";")` alternative — no new semantic category. Also covers a comma-separated multi-aspect form for the same bodyless case (`extend Type: A, B, !C;`), itself pure desugaring into N independent single-aspect blocks, scoped strictly to bodyless/empty-bodied extends since a shared, non-empty body across multiple aspects has no principled disambiguation and isn't attempted here.

---

## Motivation

Two shapes of `extend` block (RFC-0098) never have anything to write inside `{ }`, yet the grammar
requires the braces anyway:

- **Negative impls** (`extend Type: !Aspect { }`, RFC-0081) — the parser already enforces
  `ib.methods.is_empty()` for these; a negative impl is a declaration of non-implementation, and there is
  nothing it could legally put in a body even if it wanted to.
- **Marker aspects** — an aspect with no methods at all (the `Send`/`Sync`-style case, e.g. a hypothetical
  `aspect Copy2 { }`), or an aspect whose every method already has a default body (RFC-0060's
  default-aspect-method mechanism, already real and tested — `stage12_01_default_methods.mtl`,
  `63_default_methods.mtl`) — for both, `extend Type: Aspect { }` is already legal today with a literally
  empty body; there's simply nothing new to say at that impl site.

The empty `{ }` in both cases is pure noise, and this grammar already has a precedent for dropping it:
`fun_decl = { ... ~ (block | ";") }` — a function declaration ends in either a real body or a bare
semicolon, used throughout aspect method signatures and native declarations for exactly this reason
(nothing to write, so don't make anyone write nothing). `impl_block`'s own grammar has no such
alternative — `"{" ~ (fun_decl | assoc_type_def)* ~ "}"` is unconditional — and this RFC proposes closing
that gap the same way `fun_decl` already closed it for itself.

---

## 1. Grammar

Today: `impl_block = { "impl" ~ bang? ~ generic_params? ~ (named_type ~ "for")? ~ type_expr ~
where_clause? ~ "{" ~ (fun_decl | assoc_type_def)* ~ "}" }` (pre-RFC-0098 spelling; RFC-0098 reorders the
target/aspect clauses but the braced body is untouched by that RFC). Proposed: add a bodyless alternative,
mirroring `fun_decl`'s own `(block | ";")` exactly —

```
extend_block = { "extend" ~ generic_params? ~ type_expr ~ (":" ~ bound)? ~ where_clause?
                  ~ (("{" ~ (fun_decl | assoc_type_def)* ~ "}") | ";") }
```

```metel
extend SomeType: Copy2;              // marker aspect, no methods at all
extend Type: !Sendable;              // negative impl
```

(§5 below widens this same aspect clause from a single `bound` to a comma-separated list — the grammar
shown here is the single-aspect base case, not the final shape.)

No new AST field is needed — `ast::ImplBlock`'s `methods`/`assoc_type_defs` are simply empty `Vec`s either
way; the bodyless spelling and an explicit `{ }` produce identical `ImplBlock` values. This is purely a
parser-level convenience, not a new shape at any later stage of the pipeline.

## 2. Semantics: sugar, not a new rule

`extend Type: Aspect;` desugars to `extend Type: Aspect { }` before any validation runs — there is no
separate "is this a marker aspect" check anywhere, and no new semantic category. Whatever already validates
an empty-bodied impl today (the required-method-vs-default-body check in `infer_decl`'s `Decl::Impl`
handling, RFC-0082's associated-type completeness check) runs completely unchanged against the desugared
form. The consequence is important and deliberate: **the bodyless spelling's legality is never checked
syntactically** — it is exactly as legal as writing `{ }` explicitly, no more and no less. `extend Type:
Display;` (bodyless) fails with the same missing-required-method error `extend Type: Display { }` already
produces today, since `Display::to_string` has no default body — not a new, bodyless-specific diagnostic
category, just the existing one, reached one token sooner.

## 3. Negative impls: the bodyless form is mandatory, not optional

Since a negative impl's method list is already grammar-and-parser-enforced to be empty regardless of
spelling, the bodyless form is always available for `extend Type: !Aspect;` with no further condition to
check — polarity alone decides it. **The explicit-braces spelling (`extend Type: !Aspect { }`) is retired,
not kept as a second valid way to write a negative impl.** This is the same call this project already made
twice for an analogous choice — RFC-0100 retiring `Type { field: value }` once `Type(field: value)` existed
rather than keeping both, and RFC-0042 retiring standalone `mut` rather than keeping every spelling that
ever worked — and it applies more cleanly here than the "leave both valid" framing an earlier draft of this
RFC proposed: unlike `fun_decl`'s own `(block | ";")` (a real choice, since a function can meaningfully have
either), a negative impl's body is *never* meaningfully non-empty — there is no case where writing `{ }`
communicates anything `;` doesn't, so keeping both is pure duplication, not two spellings serving different
needs. `extend Type: !Aspect { }` is a compile error once this RFC lands: **use `extend Type: !Aspect;`.**

## 4. Marker aspects and default methods (positive impls)

The bodyless form is legal for a *positive* impl exactly when an empty body already would be — precisely:
every method the aspect declares has a default body (vacuously true when the aspect declares zero methods
at all — the true "marker aspect" case), **and** the aspect declares no associated types requiring a
concrete binding (RFC-0082 has no default-associated-type mechanism, so an aspect with any associated type
always requires a real, non-empty impl body regardless of this RFC — the existing completeness check
already enforces this, and the bodyless sugar inherits that rejection automatically, with nothing new to
implement for that interaction).

```metel
// True marker aspect — zero methods, zero associated types.
aspect Copy2 { }

struct Handle { id: i64 }
extend Handle: Copy2;

// All-defaults aspect — every method has a default body, so an empty impl
// (and therefore the bodyless spelling) is legal exactly as it is today.
aspect Greeter {
    fun greet(&self) -> String { "hello" }
}

extend Handle: Greeter;

// Rejected — Display::to_string has no default body, so neither the
// bodyless spelling nor an explicit empty `{ }` is legal here.
extend Handle: Display;   // error: missing required method `to_string`
```

## 5. Multiple aspects in one bodyless extend block

A type often has several independent, nothing-to-say-about-any-of-them facts to declare at once — several
marker/all-defaults aspects, or one to explicitly negate alongside them, the way the motivating example for
this section reads: `extend Handle: Copy2, Sendable, !Displayable;`. Writing N separate bodyless `extend`
blocks for N independent facts is exactly the repetition §2's own sugar already exists to cut down on, one
level up — so this section extends the aspect clause to a comma-separated list, reusing the existing
`bound` production (`{ "!" ~ bound_head | bound_head }`, already used for polarity-aware generic bounds)
directly, so per-item `!` polarity — and anything else `bound` already supports, such as associated-type
bindings on the aspect itself (`From<i64>`) — comes for free, with nothing new to parse:

```
extend_aspect_list = { bound ~ ("," ~ bound)* }
extend_block        = { "extend" ~ generic_params? ~ type_expr
                          ~ (":" ~ extend_aspect_list)? ~ where_clause?
                          ~ (("{" ~ (fun_decl | assoc_type_def)* ~ "}") | ";") }
```

**Semantics: pure desugaring, exactly like §2.** `extend Type: A, B, !C;` means precisely `extend Type: A;
extend Type: B; extend Type: !C;` — three fully independent extend blocks, each checked exactly as if the
others weren't there. There is no cross-item interaction: `A`'s requirements, `B`'s requirements, and `C`'s
negative-impl rule are each validated completely independently.

**Restriction: a multi-aspect list may only appear on a bodyless (or, for an all-positive list, an
explicitly-empty-braced) extend block.** `extend Type: A, B { fun foo() { ... } }` is rejected outright —
there is no principled way to say which aspect `foo` belongs to (Rust sidesteps this question entirely by
requiring exactly one trait per `impl` block in the first place). This RFC doesn't invent a disambiguation
mechanism for a shared, non-empty body (e.g. a qualified `A::foo` method-declaration syntax) — multi-aspect
lists are scoped exactly to the situation this RFC already covers: nothing to write in the body, no matter
how many aspects are named. **Per §3, if the list contains any negative item, the block must be bodyless —
never explicit braces, empty or otherwise:** `extend Type: A, !B { }` is rejected the same way a lone
`extend Type: !B { }` is; the choice between bodyless and empty-braced (§4) exists only for lists that are
entirely positive.

**Each aspect name may appear at most once per list, regardless of polarity** — `extend Type: A, !A;` is
rejected as self-contradictory (declaring both "implements `A`" and "does not implement `A`" in the same
breath), a cheap, local, parse-adjacent check, independent of full cross-module coherence.

Composes with RFC-0097's bare-parameter blankets with no special-casing at all, since "how many aspects
does this block name" and "what is the block's target" are orthogonal concerns:

```metel
extend<T: Copy> T: Clone, Debug;
```

Full example, mixing polarities as in this section's own motivating case:

```metel
aspect Copy2 { }
aspect Sendable { }
aspect Displayable {
    fun display(&self) -> String;
}

struct Handle { id: i64 }

// Three independent, bodyless facts about Handle in one block.
extend Handle: Copy2, Sendable, !Displayable;

// Exactly equivalent to:
extend Handle: Copy2;
extend Handle: Sendable;
extend Handle: !Displayable;
```

---

## Alternatives Considered

- **Status quo — always require braces.** Simplest, zero grammar change, but leaves exactly the noise this
  RFC exists to remove for both motivating cases.
- **Mark the aspect declaration itself as a "marker aspect"** (e.g. a `marker aspect Copy2 { }` keyword),
  rather than changing the impl-site grammar. Rejected *for this RFC's own scope*: the pain point this RFC
  targets is at each *impl site*, not at the aspect declaration (which is written once); marking the aspect
  doesn't remove the need to write `{ }` at every `extend` site, so it doesn't solve the problem this RFC
  is scoped to. A sibling RFC (RFC-0103) considered this same idea for a different reason — a permanent,
  declared guarantee that a struct/enum-embedded aspect list (which has no per-aspect body to fall back on)
  might need — but ultimately dropped it too, once it settled on treating every positive struct/enum-
  embedded item as a checked obligation rather than something the list itself could satisfy; a bodyless
  *aspect declaration* (`aspect Copy2;`) still exists there, but as plain sugar inheriting this RFC's own
  weaker "currently has zero methods" rule, not a `marker` keyword's permanent one.
- **A dedicated bodyless-specific diagnostic** distinguishing "you wrote `;` but this aspect needs a method"
  from the ordinary missing-method error. Considered in Unresolved Questions rather than assumed — the
  minimal version of this RFC reuses the existing error verbatim.
- **Allowing a multi-aspect list with a shared, non-empty body**, disambiguating which method belongs to
  which aspect via a qualified declaration syntax (e.g. `A::foo`). Rejected as significantly larger in scope
  than this RFC — effectively its own feature (closer to Rust's exploratory `impl Trait1 + Trait2`
  discussions), and not needed for either of §5's two motivating cases (marker aspects, negative impls),
  both of which never have a body regardless of how many are named.
- **Keep the explicit-braces spelling valid alongside the bodyless one for negative impls** (an earlier
  draft of this RFC's own recommendation). Reversed in §3: unlike `fun_decl`'s real body-vs-signature
  choice, a negative impl's body is never meaningfully non-empty, so keeping both spellings would be pure
  duplication rather than two forms serving different needs — this project's own precedent (RFC-0100,
  RFC-0042) is to retire the old spelling outright once a strictly-better one exists, not to carry it
  forward as a permanent alternative.

---

## Unresolved Questions

1. **A tailored diagnostic hint for the bodyless-but-not-actually-empty-eligible case** — e.g. "hint:
   `extend Type: Aspect;` requires every method to have a default body; `to_string` does not" — versus
   reusing today's generic missing-required-method message verbatim. Not blocking; a documentation/UX
   refinement that can be decided at implementation time.
2. **Confirm the RFC-0082 associated-type interaction (§4) against the actual completeness-check code**
   before implementation — this RFC asserts it needs no changes there, but that should be verified directly
   against `infer_decl`'s associated-type handling rather than assumed from this RFC's own reasoning alone.
3. **Does §5's per-list duplicate-aspect-name check need to look outside the list at all** — e.g. `extend
   Handle: Sendable;` written once as its own block *and* `Sendable` also named again inside a separate
   `extend Handle: Copy2, Sendable;` list elsewhere in the same module? This RFC's position is that this is
   the same question ordinary duplicate-impl coherence checking already answers for any two separate impls
   of the same aspect on the same type, regardless of whether either was written via a list — §5's own
   check is narrower and purely local (within one list, not across the module) — but worth confirming this
   framing holds once implemented, rather than assumed.

---

## References

- RFC-0098 (Surface Keyword Renames) — this RFC extends `extend Type: Aspect`'s grammar with the bodyless
  alternative; depends on RFC-0098's grammar shape (or, if RFC-0098 doesn't land, could be respelled
  against today's `impl Aspect for Type` instead — the mechanism itself doesn't depend on which keyword
  spelling is current).
- RFC-0081 (Negative Impls) — the polarity/`!` mechanism §3's case builds on; the parser's existing
  `ib.methods.is_empty()` enforcement for negative impls is what makes the bodyless form unconditionally
  legal there, not something this RFC needs to add.
- RFC-0060 (Aspect Impl Coherence) — the default-aspect-method mechanism (`inherited_defaults`) §4's
  positive-impl case relies on, completely unchanged by this RFC.
- RFC-0082 (Associated Types) — the completeness check that already rejects an empty body for an aspect
  with associated types, unchanged; see Unresolved Question 3.
- RFC-0036 (Conditional Impl Blocks) — the `bound`/`bound_head` grammar (`"!" ~ bound_head | bound_head`)
  §5's comma-separated list reuses directly for per-item polarity and associated-type-bound syntax; not
  amended, only reused in a new position.
- RFC-0097 (Orphan Rule for Bare-Parameter Blanket Impls) — §5's example composing a multi-aspect list with
  a bare-parameter blanket target; not amended, the two features are orthogonal.
- RFC-0103 (Bodyless Aspect Declarations) — depends on this RFC as the direct precedent for
  bodyless declaration sugar one production earlier; also dropped the same `marker`-keyword
  alternative rejected above.
- RFC-0105 (Struct-Embedded Aspect Lists, draft) — the larger struct/enum-embedding proposal
  split out of RFC-0103; reuses `extend_aspect_list` and the negative-always-eligible reasoning
  directly.

---

## Decision

**Outcome:** *(pending)*
**Target:** *(set when accepted)*
