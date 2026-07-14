---
id: rfc-0103
title: "Bodyless Aspect Declarations and Struct-Embedded Aspect Lists"
date: '2026-07-14'
status: accepted
target:
updated: '2026-07-14'
---

> **Status — accepted (2026-07-14).** Reviewed and resolved: the obligation check (§3) runs inside the same already-existing whole-graph coherence pass (coherence.rs, RFC-0060), and §4 resolves a real interaction with RFC-0096's auto-impl aspects (Send/Sync/Linear have no Decl::Impl to search for; the obligation is discharged by querying RFC-0096 §2's satisfies check directly instead). No open questions remain.

## Summary

One addition on top of RFC-0102, plus a small extension of that RFC's own bodyless theme to a new
position. **Bodyless aspect declarations** (`aspect Copy2;`) — pure sugar for `aspect Copy2 { }`, legal
whenever the braced form already would be (i.e. the aspect declares zero methods and zero associated
types), mirroring RFC-0102's own `extend`-block sugar one production earlier, at the aspect's own
declaration. And a **struct/enum-declaration-embedded aspect list** (`struct Token: Copy2, Serializable,
!Send { value: String }`), reusing RFC-0102's `extend_aspect_list`, where struct/enum bodies stay
fields-only: a negative item is always fully satisfied by the list itself, and a positive item always
declares a checked, module-wide *obligation* — discharged by an ordinary, separately-editable `extend`
block elsewhere, never satisfied by the list alone, regardless of how many methods the named aspect
currently happens to declare. Depends on RFC-0102. (An earlier draft of this RFC proposed a dedicated
`marker` keyword granting a *permanent* zero-methods guarantee, gating which struct/enum-embedded positive
items the list alone could satisfy. Dropped: since every positive item is now always an obligation, never
satisfied by the list alone, the permanence guarantee `marker` would have provided is never actually
load-bearing — see Alternatives Considered.)

---

## Motivation

RFC-0102 makes `extend Type: Aspect;` legal whenever an empty `extend`-block body already would be. Two
further ideas surfaced while drafting that RFC:

1. **The aspect *declaration* itself has the same "nothing to write" shape RFC-0102 already closed for
   `extend` blocks — one production earlier.** An aspect with no methods and no associated types at all
   (the `Send`/`Sync`-style case) still has to write `aspect Copy2 { }` today; the empty braces are pure
   noise, exactly the pattern `fun_decl`'s own `(block | ";")` alternative and RFC-0102's `extend_block`
   sugar both already exist to remove. This project's docs corpus already uses the term "marker aspect" for
   exactly this case — RFC-0080 §3 calls `Send`/`Sync` "marker aspect[s] with no methods" — so this section
   gives that existing, already-named concept a shorter spelling, not a new concept.
2. **A struct or enum declaration has exactly one body, and it's the field/variant list — not a
   per-aspect slot.** `struct Token: Copy2 { value: String }` (this RFC's other proposal) has nowhere to put
   a method implementation, unlike an `extend` block, which can always grow a body later. Embedding a
   negative aspect or a genuine positive obligation directly in the type's own declaration — `struct Token:
   Copy2, Serializable, !Send { ... }` — removes the boilerplate of a separate bodyless `extend` block for
   a fact that's really part of describing what the type *is*, the same motivation `class Foo : IBar` (C#),
   `class Foo implements Bar` (TypeScript), and `class Foo extends A with B` (Scala) share, adapted to this
   language's own `extend`/aspect vocabulary rather than borrowed wholesale.

---

## 1. Bodyless aspect declarations

```
aspect_decl = { pub_kw? ~ "aspect" ~ ident ~ generic_params?
                 ~ (("{" ~ (assoc_type_decl | aspect_method)* ~ "}") | ";") }
```

```metel
aspect Copy2;
```

Pure sugar, exactly like RFC-0102 §2: `aspect Copy2;` desugars to `aspect Copy2 { }` before anything else
runs. There is no separate "is this a marker aspect" check and no permanence guarantee attached to this
spelling — an aspect declared bodyless today can gain a method tomorrow by simply switching to the braced
form, exactly as freely as an aspect that happened to start out `aspect Foo { }`. The bodyless spelling is
legal if and only if the aspect declares zero methods and zero associated types, the same "currently empty"
condition RFC-0102 already uses for `extend` blocks, applied here to the aspect's own declaration instead.

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
implementation live inside a `struct`/`enum` declaration's own braces:

| Item | Eligible when | What it means |
|---|---|---|
| `!Aspect` (negative) | Always — any aspect, any shape, regardless of methods or associated types (RFC-0081's polarity guarantee, independent of the aspect's own declaration) | Fully satisfied by the list itself, same as an `extend Type: !Aspect;` block |
| `Aspect` (positive) | Always | **Declares an obligation, not an implementation** — see below |

**The obligation model for positive items.** Naming a real, positive aspect on a struct/enum's own
declaration doesn't try to satisfy it there (there's nowhere in a fields-only body to put its methods) — it
declares that the type *must* implement that aspect, checked module-wide against ordinary `extend` blocks
written elsewhere, the same ones you'd write without this RFC at all. `struct Token: Serializable { value:
String }` means: `Token`'s own declaration is unchanged, plus a checked obligation that *some* `extend
Token: Serializable { ... }` block exists (anywhere it would ordinarily be visible) and passes its own
already-existing completeness check. Forgetting to write that block is a compile error reported at the
struct's own declaration — earlier and more direct than today's alternative, where the gap is only ever
discovered wherever `Token: Serializable` happens to be required later.

This is uniform regardless of whether the named aspect happens to be bodyless-eligible under §1 — a
positive item is *always* an obligation, never satisfied by the list alone, so there's no separate
"currently empty enough to skip the `extend` block" fast path to reason about here. The real implementation
always lives in an ordinary, always-editable `extend` block, exactly like it would without this RFC — the
struct/enum-embedded list only ever adds a forward-declared, checked *promise* that the block exists, never
the implementation itself.

```metel
aspect Copy2;

aspect Serializable {
    fun serialize(&self) -> String;
}

struct Handle {
    id: i64,
}

// Copy2 is fully satisfied here (it's bodyless, i.e. requires nothing);
// Serializable is not -- it's an obligation, discharged by the separate
// extend block below. Composes with RFC-0080's real Send/Sync (auto-impl
// aspects): the compiler grants Send automatically based on field types,
// and the explicit negative override RFC-0080 §3 already specifies
// (`impl !Send for MyType {}`) is exactly the negative case this RFC's
// list embeds directly.
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

A positive item's obligation (above) is always discharged by an *ordinary* `extend` block — that block may
itself name more than one aspect and share a real body across them, under RFC-0104 (Multi-Aspect Extend
Blocks with Shared Bodies), split out of an earlier draft of this section into its own RFC since it's a
separate feature that doesn't need anything here to work.

## 3. Where and how the obligation check runs

The obligation check is inherently cross-declaration — a struct/enum's own embedded list names an aspect,
and the satisfying `extend` block may be written anywhere else the type is visible, possibly in a different
module. This is not a new kind of pass: it's the same shape of question RFC-0060's existing coherence
checking already answers (orphan rule, overlap detection), and it runs in the same place for the same
reason. Confirmed directly against the actual coherence implementation (`coherence.rs`, RFC-0060/issue
#238): `coherence::check` already takes the *entire* `NormalizedModuleGraph` — not one module at a time —
and does a single pass collecting every `Decl::Impl` block across every loaded module into one flat list
before checking orphan/overlap rules against it. The obligation check slots into that same already-existing
whole-graph pass: for each struct/enum declaration with a positive item in its embedded list, scan the same
already-collected cross-module impl list for a `Decl::Impl` matching that target and aspect name (any
polarity-appropriate match, same resolution rules `coherence.rs::resolve_id` already uses for names). No new
pipeline stage, no new whole-module traversal — this reuses the one that's already there, and the satisfying
block is found regardless of which loaded module declares it, exactly as already true for orphan-rule
locality checks today.

**Diagnostic wording.** Because the check already has the entire graph in view (not a partial or
incremental search), a missing obligation is reported once, definitively — "no `extend Token: Serializable {
... }` found in any loaded module" — rather than "not found in module X, still checking Y," since there is
no partial-search state to report; the whole graph has already been scanned by the time coherence checking
runs. The error points at the struct/enum's own declaration span, matching T0014/T0015's existing
span-reporting convention.

## 4. Interaction with auto-impl aspects (RFC-0096)

RFC-0096 settles a fact this RFC's obligation model (§2) must account for directly, not merely assume
doesn't collide: `Send`, `Sync`, and `Linear` are **auto-impl** — granted by the compiler's own
`satisfies(A, T)` structural-composition check (RFC-0096 §2), with **no `Decl::Impl` node ever written or
synthesized in the AST for them**. §3's obligation check, as stated, only ever looks for a real `Decl::Impl`
in the module graph — which means, unmodified, `struct Handle: Send { ... }` would always report a false
"unsatisfied obligation," even when `Handle`'s fields genuinely make it `Send` under RFC-0096 §2's rule,
because no `extend Handle: Send { ... }` block exists or ever will.

This is a real interaction, not a non-issue, and needs a real carve-out: **when a struct/enum-embedded
positive item names one of RFC-0096 §1's closed set of auto-impl aspects (`Send`, `Sync`, `Linear`), the
obligation is discharged by querying RFC-0096 §2's own `satisfies` check directly against the struct/enum's
field types — the same check any other consumer of an auto-impl aspect already goes through — instead of
searching for a `Decl::Impl`.** For every other aspect (the general case), §3's `Decl::Impl` graph scan
applies unchanged. `struct Handle: Send { id: i64 }` is therefore satisfied immediately (i64 is `Send`), with
no `extend` block required or possible; `struct Handle: Serializable { ... }` still requires a real,
separately-written `extend Handle: Serializable { ... }` exactly as §2 already states. The negative case
(`!Send`) needs no special handling beyond what §2 already gives it — RFC-0080 §3's explicit override
(`impl !Send for MyType {}`, spelled `struct MyType: !Send { ... }` under this RFC) is already how RFC-0096
itself expects an auto-impl aspect to be overridden, unrelated to whether the positive case is inline-listed
or an obligation.

---

## Alternatives Considered

- **A dedicated `marker` keyword granting a permanent, aspect-declaration-level guarantee that a positive
  aspect can never gain a method** (this RFC's own earlier draft) — gating which struct/enum-embedded
  positive items the list alone could satisfy (`marker`-declared: yes; ordinary: obligation-only). Dropped
  once §2 settled on treating *every* positive item as an obligation discharged elsewhere, never satisfied
  by the list alone: the permanence guarantee `marker` would have provided is never actually load-bearing
  under that design, so keeping the keyword would add surface area without removing any risk. Bodyless
  aspect declarations (§1) inherit exactly RFC-0102's own weaker "currently has zero methods" rule instead —
  symmetric with `extend`-block sugar, no stronger promise anywhere else in the language.
- **No dedicated syntax at all — reuse ordinary `aspect Foo { }` (currently empty) for struct/enum embedding
  too, with no bodyless declaration sugar.** This was RFC-0102's own original position for its own scope
  (impl sites, not the aspect declaration). §1 closes that remaining gap directly, on the same "nothing to
  write" grounds RFC-0102 already established one production earlier — writing `aspect Copy2 { }` for a
  permanently-empty aspect is exactly the noise `fun_decl`'s `(block | ";")` precedent argues against.
- **A `#[derive(Aspect)]`-style attribute annotation instead of extending the type declaration's own
  grammar.** Rejected: this project already has a working comma-separated aspect-list mechanism from
  RFC-0102 §5; reusing it directly is smaller than introducing an entirely new attribute/annotation syntax
  for the same purpose.
- **Allow RFC-0102 §4's looser "all-default-methods" aspects to be satisfied by the struct/enum-embedded
  list itself**, rather than always treating positive items as an obligation. Rejected — an all-default
  aspect can stop being all-default later (a default body removed), and unlike an `extend` block or the
  obligation model, there'd be no local fix available if the list itself were treated as the complete
  implementation. Every positive item is always an obligation discharged elsewhere (§2); nothing about an
  aspect's current shape (zero methods, all-default methods, or neither) changes that uniformly-applied
  rule.
- **Reject positive items in the struct/enum-embedded list entirely** (an even earlier draft of this RFC's
  own position). Reversed in §2 once it became clear the "no escape hatch" concern only applies to items the
  list itself is trying to *implement* — a positive item never does that under the obligation model, so
  there's nothing unsafe about allowing it as a forward-declared, separately-checked promise.

---

## Unresolved Questions

None remaining — §3 and §4 resolve the two design questions an earlier draft left open (where the
obligation check runs, and its interaction with RFC-0096's auto-impl aspects); the earlier draft's
diagnostic-quality question is answered as part of §3, once it was clear the check is whole-graph rather
than incremental.

---

## References

- RFC-0102 (Bodyless Extend Blocks for Marker Aspects and Negative Impls) — this RFC depends on it
  directly: `extend_aspect_list` (§5) is reused verbatim for §2's struct/enum-embedded lists, and the
  negative-polarity-always-eligible rule (§3) is the same reasoning applied to embedding; §1's bodyless
  aspect-declaration sugar mirrors that RFC's own `extend`-block sugar one production earlier, with no
  stronger guarantee attached.
- RFC-0080 (Standard Library Aspects — Clone, Deref, Send, Sync) — §3 already calls `Send`/`Sync` "marker
  aspect[s] with no methods" and already specifies the negative override (`impl !Send for MyType {}`) this
  RFC's §2 lets be written as `struct MyType: !Send { ... }` instead; not amended, only given a shorter
  spelling for its existing concept and override syntax.
- RFC-0096 (Auto-Impl Aspects, draft) — the compiler-automatic-derivation mechanism for `Send`/`Sync`/
  `Linear`; §4 depends on RFC-0096 §1/§2 directly (the closed auto-impl aspect list and the `satisfies`
  structural check), which this RFC's obligation model must query directly for those three aspects instead
  of searching for a `Decl::Impl`. Not amended, but this RFC is no longer independent of it.
- RFC-0098 (Surface Keyword Renames) — `extend Type: Aspect` grammar this RFC's struct/enum embedding
  parallels; not amended.
- RFC-0081 (Negative Impls) — the polarity mechanism §2's negative-always-eligible rule relies on,
  unchanged.
- RFC-0060 (Aspect Impl Coherence) — the existing duplicate/overlapping-impl detection that already governs
  what happens if a struct-embedded item is also given a redundant, separate `extend` block for the same
  aspect; not amended. §3 confirms the obligation check (a *different* question — does a satisfying impl
  exist at all, not whether two conflict) runs inside the same already-existing whole-graph coherence pass
  (`coherence.rs`) rather than as a separate stage, sitting alongside the orphan/overlap checks rather than
  replacing them.
- RFC-0104 (Multi-Aspect Extend Blocks with Shared Bodies) — split out of an earlier draft of this RFC's
  own §2; a positive item's obligation may be discharged by a multi-aspect `extend` block under that RFC's
  own rules, with no special interaction beyond what's already stated in either RFC.

---

## Decision

**Outcome:** *(pending)*
**Target:** *(set when accepted)*
