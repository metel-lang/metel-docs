---
id: rfc-0251
title: "Opaque Views for Private State"
date: '2026-11-25'
status: draft
---

## Summary

A module can publish a name for a borrowable part of a nominal value while keeping the
fields making up that part private. A public method can declare that it accesses that
part instead of borrowing the entire value. This draft explores explicit disjointness
promises between such parts. All syntax below is illustrative and nothing is decided.

```metel
pub struct Store { entries: List<Entry>, audit: Log, pub label: String }
pub opaque view Entries for Store { entries }
pub opaque view Audit for Store { audit }
pub disjoint Entries, Audit; // checked and exported, illustrative

extend Store {
    pub fun add(&var self: Entries, e: Entry) { self.entries.push(e); }
    pub fun record(&var self: Audit) { … }
}

// Caller, using illustrative view-borrow syntax
let entries := &var store.Entries;
let audit := &var store.Audit; // allowed by the published disjointness promise
```

RFC-0109 proposes named transparent views of residuals. RFC-0243 identifies opacity as
an additional design and offers disjointness options. This RFC separates that work so it
can follow the view and borrow-checking foundations without blocking their settlement.

## Motivation

A method that needs a private field cannot currently publish a receiver that names the
field without disclosing private representation. Taking the whole `&var self` hides the
representation but prevents a caller from simultaneously borrowing an unrelated field.
An opaque view makes the access footprint part of the public interface while hiding its
field names and types.

## Candidate model

1. The type's defining module declares the opaque view and its private field set. The
   name and owner brand are public when the view is exported; its representation is
   visible only where the field declarations are accessible. At external use sites it is
   an abstract place and a receiver contract, not a structural row with readable labels.
2. A reference to a view is obtained by narrowing a reference to the owner, carries the
   original origin and lifetime, and cannot outlive it. Shared and exclusive access,
   reborrowing and suspension follow the same rules as the owner's references. A method
   receiving a view can use its fields only in a scope authorized to see them.
3. For the initial candidate a view contains only private fields. It is then disjoint
   from each public field by construction. A whole-owner borrow overlaps every view.
   Whether a view may include public fields is open.
4. Outside the defining module, distinct opaque views may overlap unless the module
   exports a checked `disjoint` promise. A promise applies to the same owner instance,
   is checked against the actual field sets, and is part of the public API. Inside the
   module the checker may use the actual field sets. It is an error to claim disjointness
   for overlapping sets. The exact declaration syntax and whether promises compose are
   open.
5. Callers can hold and pass view references. They cannot name, project, enumerate,
   destructure, or reconstruct hidden fields from a view. A public structural bound
   reveals no hidden row through it. Passing a view does not create an owned partial
   value or allow a private field to be moved out.
6. A defining module may revise a view's representation only if all its published
   access and disjointness contracts remain valid. Removing a field from or adding a
   field to the hidden set can break those contracts even if field names remain private.

The abstract view's relation to RFC-0109's transparent residual type needs a formal
account. In particular, it must not expose a private field through type equality,
reflection, diagnostics, row remainders, or generic inference. A proposed Core account
is an owner place plus an abstract projection and exported overlap facts; no ABI,
pointer cast, runtime representation, or compiler implementation is prescribed.

## Worked examples

```metel
let part := &var store.Entries;
let label := &store.label; // accepted under the private-only candidate
store.add(e);              // rejected while part is still live if the loans overlap
```

The rejection depends on the actual last use of `part`, not lexical scope alone. If the
module declares a second view over `entries`, two mutable loans through the two names
are rejected, even if their field lists are hidden. If `Audit` contains only `audit`,
the module may promise that it is disjoint from `Entries`; without that promise an
external caller must assume they overlap. References to `Entries` from different `Store`
instances are independent when the ordinary place and alias rules prove that fact.

A generic function with a public row bound cannot obtain `entries` by extracting a
remainder from the opaque view. A whole `Store` matches structural bounds only against
its public row under the current RFC-0243 direction; an opaque view does not publish
additional fields.

## Alternatives

RFC-0252 explores opaque types with separately checked borrowable projections as a
related alternative. The two drafts need reconciliation before either is accepted.

- Export automatically all disjoint pairs computed from the private implementation.
  This is convenient but makes a hidden representation change silently remove a public
  borrowing capability.
- Treat all distinct views as overlapping, even when an author wants to promise
  disjointness. This avoids new public facts but limits simultaneous borrowing.
- Declare fixed partitions of the owner. Disjointness follows from the partition, but
  overlapping useful views require additional composition rules.
- Keep RFC-0109's current visibility restriction and use whole-owner receivers for
  methods touching private state. This is simpler and leaves the borrowing gap.

## Interactions and scope

RFC-0109 owns transparent named views and narrowed receivers. RFC-0144 covers splitting
references; RFC-0146 covers row-polymorphic receivers, whose interaction with opaque
names remains open. RFC-0122 and RFC-0241 own sound loan and place reasoning. RFC-0242's
library-defined access abstractions may overlap this design and must be reconciled.
RFC-0243 owns public structural matching. RFC-0214 addresses aspect impls on residuals;
this draft does not grant aspects or derive behavior to opaque views. Stored references
and returned origins depend on RFCs 0067 and 0159. `Drop`, partial moves, and generic
owner types need separate worked soundness checks. Opaque views are deferred from the
current row-visibility settlement and do not block acceptance of transparent views.

## Open questions

1. Are opaque views abstract residual types, abstract places, or both? What equality and
   coercion rules prevent recovering private representation?
2. Are view field sets restricted to private fields, or can they include public fields?
3. Are distinct views conservatively overlapping unless the author explicitly promises
   disjointness, or should relationships be inferred or declared as partitions?
4. How are disjointness promises written, exported, versioned and composed, including
   nested views, empty views, and views of generic owners?
5. What exact borrow, reborrow, origin and method-receiver rules apply across calls?
   How does a caller refer to a view without creating overlapping loans for method calls?
6. May a view be split, combined or narrowed by a caller without exposing its fields?
7. What can aspect bounds, impls, row binders, comptime reflection and diagnostics observe?
8. How do opaque views interact with Drop receivers, partial moves, linear fields, stored
   references, and concurrent or effectful access?
9. How are public API and compatibility checked when hidden field sets change?
10. What are the surface spellings and the required borrow-checker / Core staging?

## Decision

**Outcome:** *(pending)*
