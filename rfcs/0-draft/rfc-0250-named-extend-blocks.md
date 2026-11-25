---
id: rfc-0250
title: "Named Extend Blocks"
date: '2026-11-25'
status: draft
---

## Summary

A reusable row-conditional aspect implementation may have a name. A nominal type's author
can explicitly select it, so the behavior is identifiable at the grant and does not arise
merely because the type has matching public fields. For discussion, this RFC uses
`named extend` and `using`; both spellings are illustrative.

```metel
// Library
pub named extend IdentifiedById<..R> .{ .id: i32, R }: Identified {
    fun describe(&self) -> String { … }
}

// Type's module
struct Invoice { pub id: i32, pub total: i32 }
extend Invoice: Identified using IdentifiedById;
```

The selected block supplies an ordinary coherent implementation for `Invoice`. The
provider's row requirements must hold and its body is checked. This is a design draft;
no spelling, status transition, or interaction with derived `Clone` is decided.

## Motivation

RFC-0243's emerging direction lets public fields satisfy structural bounds while a
nominal type opts in to a row-based aspect implementation. A bodyless grant such as
`extend Invoice: Identified;` leaves the implementation to be selected implicitly. Naming
the provider makes the chosen behavior reviewable and permits useful diagnostics when its
requirements are not met. It can also support migration of named records that currently
receive a plain aspect through a blanket implementation.

## 1. Proposed model

1. A named extend declares one reusable implementation of a specified aspect identity,
   a row target and its bounds, together with the implementation items. Its name has
   ordinary module visibility and must be visible at a selection. The declaration is
   checked against its symbolic fields and stated bounds; using it does not waive method
   completeness, well-formedness or access checks.
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
   identity or a method-selection priority.
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
// Illustrative bounds and provider
pub named extend ShowValue<T, ..R> .{ .value: T, R }: Display where T: Display { … }
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
and ambiguity. Listing fields in a grant identifies the row, but not a unique provider.
A handwritten impl forwarding to library functions is explicit and works without
selectable impls, at the cost of repeating aspect methods. Label arguments or mappings
could make a provider reusable for differently named fields, but require their own
label-polymorphism and checking rules and are not assumed here.

## Open questions

1. Is a named block an active blanket impl, an inactive provider, or can it be either?
2. What syntax names the provider, selects it and supplies explicit generic arguments?
   Are names public API and can they be imported or re-exported?
3. Which orphan rules govern declaring the provider and selecting it? Can an aspect owner
   publish one for a structural target without claiming all matching nominal types?
4. How do overlap checks handle conditional generic selections, negative impls, auto
   impls and existing anonymous-record blankets?
5. How are `Self`, associated types and construction checked when the nominal target is
   not known at provider definition? May a provider return `Self` at all?
6. Which fields can the selected provider read, including private fields? Does explicit
   selection confer any authority beyond the public row, and how is it scoped?
7. Can the grant provide label arguments or a mapping? How are label collisions and
   bounds checked without confusing mapping with implicit renaming?
8. How do multiple super-aspect obligations, generic aspect arguments and provider
   parameters compose? Are associated items fixed by the provider or selectable?
9. Can residuals select a provider, and what overlapping residual domains are legal?
10. How do inline implementations in RFC-0236 and named providers compose?
11. Can provider names become comptime values, and can a derivation select one? This is
    deferred with the derived `Clone` / field-wise `Clone` interaction.
12. What migration preserves named-record blanket behavior without guessing a provider
    when several candidates exist?

## Decision

**Outcome:** *(pending)*
