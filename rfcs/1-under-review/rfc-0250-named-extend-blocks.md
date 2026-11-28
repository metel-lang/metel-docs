---
id: rfc-0250
title: "Named Extend Blocks"
date: '2026-11-25'
status: under-review
updated: '2026-11-28'
tracking: 'https://github.com/metel-lang/metel-core/issues/2196'
---

> **Status — under review (2026-11-26).** Section 0's migration-naming slice is decided. It was committed to closing RFC-0243's migration gap in v0.17.0, then deferred (language owner, 2026-11-28): v0.17.0 retires the `record` kind without it, and the slice moves to the Surface settlement theme with no release commitment

## Summary

A reusable row-conditional aspect implementation may have a name. A nominal type's author
can explicitly select it, so the behavior is identifiable at the grant and does not arise
merely because the type has matching public fields. Two declaration spellings are live and
neither is ruled out: `named extend Name<..R> .{ R }: Aspect { body }`, and
`extend Name<..R> .{ R } for Aspect { body }`, reusing RFC-0109's `Name for Target` idiom
from named views. Selection is `using`. All three spellings are illustrative.

```metel
// Library -- two live candidates for the same declaration:
pub named extend IdentifiedById<..R> .{ .id: i32, R }: Identified {
    fun describe(&self) -> String { … }
}
// or, reusing the named-view idiom:
pub extend IdentifiedById<..R> .{ .id: i32, R } for Identified {
    fun describe(&self) -> String { … }
}

// Type's module (unaffected by which declaration spelling is chosen)
struct Invoice { pub id: i32, pub total: i32 }
extend Invoice: Identified using IdentifiedById;
```

The selected block supplies an ordinary coherent implementation for `Invoice`. The
provider's row requirements must hold and its body is checked.

**A minimal slice of this is decided (language owner, 2026-11-26): section 0.** It closes RFC-0243's migration gap — a
struct migrated from a `record` regaining a plain aspect's lost blanket match — without settling this RFC's general
provider-selection design. It is deferred from v0.17.0 (language owner, 2026-11-28): the decision stands, but v0.17.0
retires the `record` kind and accepts the gap, and the slice is implemented later. Everything else here (multiple providers, label mapping, comptime provider values, residual
selection, interaction with derived `Clone`, the active-vs-inactive-blanket question) remains undecided, a design draft.

## 0. The decided slice: migration naming

**A row-conditional impl may carry a name, and `extend T: A using Name;` is accepted when `Name`'s own `where` clause is
satisfied by `T`'s public row (RFC-0243) and every method of `A` is by-reference-only — never returning or consuming
`Self` by value (language owner, 2026-11-26).** Acceptance installs `Name`'s methods for `T` as an ordinary, coherent
impl of `A`.

- **The name is always required, with no bare/unnamed shortcut**, even in a case where only one candidate could ever
  legally match. This is a deliberate choice, not an oversight: a bare `extend T: A;` would be ambiguous to a *reader*
  (which behavior did this adopt?) even where RFC-0121's coherence rule makes it unambiguous to the *compiler* — the two
  are different properties, and this slice optimizes for the reader. Naming also means this slice needs no uniqueness
  proof over existing row-conditional impls of `A`, unlike an earlier draft of this idea: the name picks the impl
  directly, so a second, differently-named provider existing elsewhere is simply not this grant's concern.
- **The by-reference-only restriction is what keeps this slice narrow.** It avoids RFC-0209's open question of
  constructing `Self` from a row — a method that only reads through `&self`/`&var self` needs no such construction
  (RFC-0209 section 1 already says a template that only reads "works unchanged"). An aspect with a `Self`-by-value
  method (Clone-shaped) has no grant here at all, named or not; it needs a handwritten impl, or whatever this RFC
  eventually settles for that case.
- **Naming an existing impl changes nothing about it for anonymous records.** An unnamed blanket impl stays exactly as
  active and ambient as it always was; adding a name is purely an additional way to *refer* to it from a `using` clause,
  never a change to its own activation. This sidesteps section 2's "active vs. inactive" question entirely for this
  slice — a named provider here is active by inheriting whatever activation it already had.
- **Predicate-only aspects (`satisfying`, RFC-0202) never use this form.** They have no body to adopt and are granted
  through the colon list instead (RFC-0202 section 6), never `extend`. This slice is exclusively for aspects with real,
  by-reference-only methods.
- **Migration mechanics.** For each existing `record` with a plain aspect's blanket match that would otherwise be lost
  on retirement (RFC-0243), a migration tool can compute the match today and emit one `extend T: A using Name;` per
  (type, aspect) pair — mechanically, since the match itself is unaffected by naming. A match whose aspect fails the
  by-reference restriction has no bridge here and is flagged for manual follow-up rather than silently dropped. While
  this slice is deferred (2026-11-28), v0.17.0 ships no migration tool at all: records are rewritten by hand and a lost
  match is restored, if wanted, by a handwritten impl (RFC-0243, Migration).

## Motivation

RFC-0243's decided direction lets public fields satisfy structural bounds while a
nominal type opts in to a row-based aspect implementation. A bare grant with no provider
named would leave the implementation selected implicitly — readable to the compiler
(RFC-0121's coherence rule admits at most one match per aspect) but not to a human at the
grant site, who cannot tell whose behavior was just adopted without searching the
dependency graph. Naming the provider, always, makes the chosen behavior reviewable and
permits useful diagnostics when its requirements are not met — section 0 settles exactly
this much, for migrating a named record's lost plain-aspect blanket match. The rest of
this document is about the general case: several candidate providers for one aspect,
which does need disambiguation beyond naming alone.

## 1. Proposed model

1. A named declaration — `named extend Name<..R> .{ R }: Aspect { body }`, or equivalently
   `extend Name<..R> .{ R } for Aspect { body }` (reusing RFC-0109's `Name for Target`
   idiom; neither spelling is ruled out) — declares one reusable implementation of a
   specified aspect identity, a row target and its bounds, together with the
   implementation items. Both read as the same shape an ordinary anonymous
   `extend<..R> .{ R }: Aspect { body }` already has, with a name inserted and either a
   leading `named` modifier or a trailing `for Aspect` in place of `: Aspect`.
   Its name has ordinary module visibility and must be visible at a selection. The
   declaration is checked against its symbolic fields and stated bounds; using it does not
   waive method completeness, well-formedness or access checks.
2. A selection names the provider and a nominal target. The aspect identity in the grant
   must equal the provider's instantiated identity, including aspect type arguments
   (RFC-0228). The target's eligible row must satisfy its required shape and bounds.
   An inaccessible provider, missing field, wrong field type, unsatisfied bound, or
   incompatible aspect is an error at the grant. Generic target parameters and provider
   parameters are instantiated without assuming bounds absent from the grant.
3. The selection creates an implementation for the nominal target subject to ordinary
   orphan, overlap and super-aspect requirements. A second selection, handwritten impl,
   derived impl or applicable auto impl for the same aspect identity and target is an
   overlap, subject to that aspect's existing rules. Names do not create a second aspect
   identity or a method-selection priority. Current Metel separately gives a brand-specific
   impl priority over a matching row-conditional impl; whether and how a selection changes
   that relationship is open and must be reconciled with this candidate.
4. The type's author must explicitly select the provider. Selection uses public fields
   in this initial candidate. Whether an explicit grant can authorize a provider to use
   private fields, and how it names that authority, is open. It does not grant access to
   fields beyond the selected provider's checked requirements.
5. A selection for a whole type does not by itself establish an impl for its residuals.
   Residual-specific impls and template application are addressed by RFCs 0214 and 0217.

These rules describe the selection, not an implementation strategy. `Self` in an
instantiated provider must denote the nominal target, but how a body that constructs or
returns `Self` does so is an open question. No implicit record conversion, layout cast or
copy is implied by selection.

## 2. Anonymous records and blanket implementations

Two alternatives need review. **A:** the named block is also an active blanket impl for
anonymous records. Existing blanket coherence applies, while nominal types select it
explicitly. **B:** a named block is an inactive provider, and a separate declaration
installs it as a blanket impl for anonymous records. B permits several providers for a
shape without automatically introducing overlapping blanket impls; it adds a declaration
and requires a precise installation rule. Neither alternative is selected here.

A provider name selects behavior; it must not cause the same anonymous record to satisfy
an aspect through multiple overlapping active impls. Selection order, import order and
provider declaration order do not resolve overlaps.

The current specification rejects same-aspect row-conditional impls unless their row
conditions are provably disjoint (`spec.types.generics.row-conditional-impls.legality-3`).
The frontend implements this check and a fixture rejects overlapping `{ a, .. }` and
`{ b, .. }` conditions with `T0015`. For a brand-specific impl alongside a matching row
impl, current dispatch instead checks the brand first and does not report that pair as
overlapping (`legality-2`). An active named blanket must account for both rules; an
inactive provider has no active blanket effect until installed. These are existing rules,
not a decision to preserve them unchanged for the new selection mechanism.

## 3. Examples

```metel
struct Order { pub id: i32 }
extend Order: Identified using IdentifiedById; // accepted if requirements hold

struct Receipt { pub number: i32 }
extend Receipt: Identified using IdentifiedById; // error: required .id absent

struct PrivateId { id: i32 }
extend PrivateId: Identified using IdentifiedById; // error under public-row candidate
```

For a generic provider, the selection must establish its condition:

```metel
// Illustrative bounds and provider -- either declaration spelling:
pub named extend ShowValue<T, ..R> .{ .value: T, R }: Display where T: Display { … }
// or:
pub extend ShowValue<T, ..R> .{ .value: T, R } for Display where T: Display { … }

struct Box<T> { pub value: T }
extend<T: Display> Box<T>: Display using ShowValue;
```

The exact binder and argument inference are open. The condition applies to the resulting
impl, and coherence must account for its domain.

## 4. Interactions

- **RFC-0208 and RFC-0243.** The example uses the proposed row binder and explicit
  nominal grant. Public structural bounds alone do not install an aspect impl. The
  named-record migration must account for previously automatic plain-aspect impls.
- **RFC-0209, RFC-0217 and RFC-0238.** Provider selection may eventually interact with
  derivations and residual templates. The entire derived `Clone` / field-wise `Clone`
  interaction, including extraction and construction, is deferred. This RFC does not
  specify a comptime selection API or change current compiler-provided derives.
- **RFC-0237 and comptime.** An aspect value identifies an aspect, not an impl. A
  source-level provider name need not be a first-class comptime value. If impl values
  or emitted selections are later added, RFC-0238's coherence and orphan checks still
  apply to the emitted impl.
- **RFC-0228, RFC-0060 and RFC-0096.** Full aspect identity, orphan and overlap rules,
  and auto-impl coherence apply. Conditional and generic selections must be checked
  against blanket, negative, and automatic impls without introducing priority.
- **RFC-0236.** Inline blocks named after an aspect locate a type's own implementation;
  a named provider identifies reusable behavior. Their syntax and duplicate-impl rules
  need reconciliation if both designs advance.
- **RFC-0109, RFC-0146 and RFC-0214.** A named view is a branded residual, not a new
  nominal owner. Selecting a provider for one residual shape needs the separate residual
  impl rules, including overlap with wider or narrower shapes.

## 5. Alternatives

A bodyless grant inferred from shape requires no provider names, but must define selection
and ambiguity. **Declined for section 0's slice** (language owner, 2026-11-26): even where
RFC-0121's coherence makes the match unambiguous to the compiler, it stays unnamed and
unreviewable to a reader, which is exactly what naming is for. Listing fields in a grant
identifies the row, but not a unique provider.
A handwritten impl forwarding to library functions is explicit and works without
selectable impls, at the cost of repeating aspect methods. Label arguments or mappings
could make a provider reusable for differently named fields, but require their own
label-polymorphism and checking rules and are not assumed here.

## 6. Declaration spelling: two live candidates, checked against existing keywords

Neither `named extend Name<..R> .{ R }: Aspect { body }` nor `extend Name<..R> .{ R } for Aspect { body }` is
ruled out (2026-11-26). The second reuses RFC-0109's `Name for Target` idiom, already established for named
views (`view Value<T> for Box<T> { value }`), so the two naming constructs would share one preposition and one
mental model instead of each inventing its own. The first keeps the name immediately after `extend`, with no new
connector at all, at the cost of a leading modifier a reader has to notice.

Other candidates for the connector were checked against the existing keyword set and set aside, not because the
idea is wrong but because the word is already spoken for:

- **`via`** is already a real, implemented keyword with an unrelated meaning — a flow-parameter list on a
  `derives` clause (RFC-0224: `derives Copy via A + B`). Reusing it here for provider selection would give one
  word two unrelated jobs depending on where it appears, which is exactly the kind of ambiguity this cluster has
  spent effort removing elsewhere (the colon list's `satisfying` split, `extend`'s predicate-vs-behavior split).
- **`as`** already carries two jobs (import renaming, explicit runtime conversion). Metel does have precedent for
  one contextual keyword serving unrelated jobs by position (`copy`, RFC-0219), so this is not disqualifying on
  principle, but a third job on an already-double-loaded word is a real cost, not a free one.
- **`using`**, for the *selection* half, checks out clean. RFC-0160 once considered it for type aliases
  (`### A distinct keyword (using / typedef / alias)`) and dropped it — but only because `type … := …` already
  existed for that job; the reason is specific to aliases and does not apply here.

This section records the comparison so it is not re-derived from scratch later; it does not pick a winner.

## Open questions

1. Is a named block an active blanket impl, an inactive provider, or can it be either? **Orthogonal to section 0's
   slice**: naming an *existing* blanket impl there changes nothing about its own activation, whichever this is decided
   to be; it only matters for a provider declared named from the start.
2. **Two live declaration candidates (2026-11-26), neither ruled out:** `named extend Name<..R> .{ R }: Aspect
   { body }`, and `extend Name<..R> .{ R } for Aspect { body }` (reusing RFC-0109's `Name for Target` idiom rather
   than a second naming preposition — see section 6 for the comparison). Selection is `using Name` either way. All
   still illustrative, not decided, since the rest of this RFC's selection semantics (several providers, generic
   arguments) is what the spelling would actually need to carry. Are names public API and can they be imported
   or re-exported?
3. Which orphan rules govern declaring the provider and selecting it? Can an aspect owner
   publish one for a structural target without claiming all matching nominal types?
4. How do overlap checks handle conditional generic selections, negative impls, auto
   impls and existing anonymous-record blankets?
5. How are `Self`, associated types and construction checked when the nominal target is
   not known at provider definition? May a provider return `Self` at all? **Resolved for
   section 0's slice** by exclusion: a by-reference-only provider never constructs `Self`,
   so the question doesn't arise there. Open for any provider that returns or consumes
   `Self` by value.
6. Which fields can the selected provider read, including private fields? Does explicit
   selection confer any authority beyond the public row, and how is it scoped? **Resolved
   for section 0's slice**: no authority beyond the public row is granted, full stop.
   Private-field authority is open for a future, broader selection form.
7. Can the grant provide label arguments or a mapping? How are label collisions and
   bounds checked without confusing mapping with implicit renaming?
8. How do multiple super-aspect obligations, generic aspect arguments and provider
   parameters compose? Are associated items fixed by the provider or selectable?
9. Can residuals select a provider, and what overlapping residual domains are legal?
10. How do inline implementations in RFC-0236 and named providers compose?
11. Can provider names become comptime values, and can a derivation select one? This is
    deferred with the derived `Clone` / field-wise `Clone` interaction.
12. What migration preserves named-record blanket behavior without guessing a provider
    when several candidates exist? **Resolved for the single-candidate case** (section
    0): RFC-0121's coherence already forbids two overlapping row-conditional impls of the
    same aspect, so there is nothing to guess there. Still open if "several candidates"
    means something coherence doesn't already rule out (e.g. across differently-scoped
    imports) — needs a concrete example before it's known whether this is a real case.
13. Does a selected nominal implementation behave as a brand-specific impl under the
    current brand-priority rule, and how does it interact with the provider's own active
    blanket impl and with other matching row impls? **Resolved for section 0's slice**:
    the grant materializes an ordinary impl, so existing dispatch (brand-specific before
    row-conditional) already covers it with no new rule. Open for the general case's
    "provider's own active blanket" interaction.

## Decision

**Outcome:** *(pending, except section 0's slice — decided, language owner, 2026-11-26)*
