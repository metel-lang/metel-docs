---
id: rfc-0252
title: "Opaque Types and Borrowable Projections"
date: '2026-11-25'
status: draft
---

## Summary

A public opaque type gives clients a stable abstract identity and explicitly stated
aspect bounds while hiding its representation. A separate borrowable projection relates
an owner place to an opaque type and specifies the origin and access footprint of the
result. Checked disjointness contracts let clients use independent projections together.
Existential packages can share abstract-type and bound-checking machinery without making
an opaque projection a per-value existential. Syntax throughout this RFC is illustrative.
Nothing here is accepted or implemented.

```metel
pub struct Store<T> { entries: List<T>, audit: Log, pub label: String }
pub opaque type Entries<T> for Store<T> := Store<T>.{ .entries };
pub opaque type Audit<T> for Store<T> := Store<T>.{ .audit };
pub disjoint Entries<T>, Audit<T>;
```

Transparent residual names may instead use type aliases once generic residual targets
are supported. This is a candidate alternative to a dedicated view declaration, not a
decision to remove RFC-0109 or replace RFC-0251.

## Motivation

A public method can expose a narrow borrowing contract without publishing private field
names. A client needs an identity for the hidden part and a checked relationship to the
particular owner's storage. Opaque type abstraction and existential packages both hide
representation and expose stated bounds, but neither an abstract type name nor a hidden
witness alone proves a projection, a loan origin or disjointness.

## 1. Opaque types

A defining module gives a public opaque type a hidden representation and states which
aspect bounds are available to clients. Outside that module the type has stable identity:
two occurrences of `Entries<String>` identify the same abstract type, while distinct
instantiations are equal only under the language's generic type equality rules. Clients
cannot infer the representation, its field labels, field types or unstated aspect impls
through alias expansion, structural bounds, row extraction, reflection, inference or
diagnostics. The compiler checks each published bound against its implementation.

Inside the defining module the representation is known. Whether the opaque type is
identical to its representation there or has distinct identity with explicit wrapping is
an open choice, especially for coherence and partial moves. It must not permit a private
representation to escape into a public type or inferable row. An opaque type's ownership,
size, destruction, lifetime and validity properties must be sufficient for its permitted
uses; opacity is not a promise of a uniform layout. The public interface must not erase
resource obligations or fabricate `Copy`, `Discard`, or `Drop` guarantees.

## 2. Borrowable projections

The `for Store<T>` part of the example proposes a checked public relationship: for each
valid owner place, a borrow of `Entries<T>` projects into that same owner instance. A
shared projection requires compatible shared access; an exclusive projection requires
exclusive access to its footprint. The projected borrow cannot outlive its owner borrow;
reborrows suspend or restrict parent access under the ordinary reference rules. A public
method taking a narrowed receiver may use the projection to borrow the owner at a call.

```metel
extend<T> Store<T> {
    pub fun count(&self: Entries<T>) -> i32 { self.entries.len() }
    pub fun add(&var self: Entries<T>, item: T) { self.entries.push(item); }
}
// Outside the module
store.add(item);                  // illustrative automatic projection
let part := &var store.Entries;   // illustrative explicit projection
```

The module must prove the hidden representation denotes a valid part of the owner and
that every exposed projection and method respects its declared footprint. The abstract
projection is a place/access contract, not an owned partial value, a raw pointer cast, or
a license to move out hidden fields. Layout and reference representation are left to
RFC-0241 and RFC-0242. Returned references must preserve the projected origin and all
validity dependencies through generic calls, aggregates and existential packaging.

## 3. Disjointness contracts

Externally, two distinct opaque projections of the same owner are conservatively treated
as overlapping unless a checked public contract proves otherwise. A declaration such as
`pub disjoint Entries<T>, Audit<T>;` is illustrative. The defining module checks it for
all permitted generic instantiations. A whole-owner borrow overlaps each projection. Loans
from different owners are handled by ordinary place and alias reasoning; type inequality
or distinct names alone do not prove different storage.

```metel
let entries := &var store.Entries;
let audit := &var store.Audit; // allowed while both live only if disjointness is proven
use_entries(entries);
use_audit(audit);
```

The contract is part of the public interface: a representation change that invalidates
it is rejected unless the contract is changed. A private-fields-only restriction could
make every opaque projection disjoint from public fields by construction; whether to
adopt that restriction is open. Nested projections, empty footprints, generic row
constraints and composition of disjointness facts need formal rules. `R # S` is a
possible notation for row disjointness, not an established operator in this RFC.

## 4. Existentials and shared abstraction

A named opaque type is a stable interface identity whose representation is chosen by its
defining module. An existential package may contain a different hidden witness in each
value. Opening a package introduces a fresh rigid witness and the explicitly retained
bounds; independent openings do not establish witness equality. Repeated uses of an
opaque alias at the same arguments instead refer to its stable identity. Both can use
common checking of abstract types and evidence, but their equality and scope differ.

```text
Dynamic<Display> = exists T: Display. { value: Owned<T> }
```

This is semantic pseudocode, not a proposed grammar. A borrowed existential package
containing a borrow of an `Entries` projection must retain that loan's owner origin,
access mode, duration and validity dependencies. Packaging cannot extend a loan, mint
exclusive access, or erase a resource obligation. Existentials need their own storage,
witness, evidence, dispatch and opening rules; this RFC does not settle those rules.
The existential-binder research report is an input, not a normative RFC or evidence of
an implemented syntax.

## 5. Worked boundaries

```metel
// External caller
let label := &store.label;
let entries := &var store.Entries; // permitted only if public contract proves disjoint
// entries.entries  // error: hidden field
```

A field-wise row loop or a public structural bound on the opaque `Entries` cannot reveal
its hidden row. If a public API promises `Entries<T>: Countable`, generic code may use
that bound, but cannot infer additional aspects from the representation. A partial move
producing `Store<T>.{ .entries }` must not accidentally acquire an opaque abstraction's
behavior merely by naming the same hidden fields. The choice between hidden equality and
distinct identities, including its consequences for RFC-0214, remains unresolved.

## 6. Alternatives

1. **RFC-0251 opaque views.** A dedicated view declaration directly combines the hidden
   residual and access contract. It offers a focused syntax, but may duplicate general
   abstract-type machinery.
2. **Only existential packages.** Packages hide per-value witnesses but need additional
   origin and projection facts to represent a borrow of a known owner part.
3. **Opaque types plus ordinary functions.** A function returning a reference can hide
   details, but callers need a public footprint and disjointness contract to hold another
   borrow of the owner at the same time.
4. **Transparent aliases only.** Existing aliases expand to their representations and
   cannot publish a private field list in a public signature.

## 7. Interactions and staging

- **RFC-0109 and RFC-0160:** transparent named residuals could use aliases rather than a
  dedicated view syntax. Generic residual targets need grammar and typechecking work;
  narrowed receivers are a separate feature. This RFC does not decide RFC-0109's surface.
- **RFC-0251 and RFC-0243:** RFC-0251 explores opaque views and explicit disjointness;
  reconcile the two designs before acceptance. Public structural bounds see only public
  fields; opacity and projection do not publish a hidden row.
- **RFC-0214 and RFC-0217:** aspect implementations on residuals and template behavior
  after narrowing are unresolved. Opaque identity must not silently settle them.
- **RFC-0122, RFC-0241, RFC-0242, RFC-0067 and RFC-0159:** borrow checking, Core places,
  general access, origins and validity dependencies need a common soundness argument.
- **RFC-0237, RFC-0238 and existential research:** aspects as comptime values and
  derivation providers are distinct from opaque type identity. Existential opening,
  evidence, layout and borrowed packages must be designed separately.
- **RFC-0089 and RFC-0071:** linearity, destruction and partial moves must be preserved,
  including across hidden representations and abnormal exits.

This work is deferred from the current row-visibility settlement. It cannot claim safe
simultaneous borrowing until the required loan and origin rules are available and tested.

## Open questions

1. Is an opaque declaration equal to its representation internally, or a distinct type?
   How do coherence, residual impls and explicit wrapping work under each choice?
2. What exactly is public: owner relation, projection name, aspect bounds, size, ownership
   and validity facts? How are representation leaks prevented through inference and tools?
3. Are projections private-field-only? How do public fields, nested parts, empty parts and
   generic owners affect overlap and evolution?
4. How are disjointness facts stated, checked, composed and exported without leaking rows?
5. How do references, returned origins, lifetimes and dependencies survive projection,
   generic calls, aggregates and existential packaging?
6. How are unsized or dynamically represented opaque types passed, and which operations
   require a known layout? What ABI and separate-compilation contracts are needed?
7. How are `Drop`, linearity, partial moves, destruction, panic and invalidation handled?
8. Can users implement aspects on an opaque type or its hidden representation, and where?
   How are super-aspects, conditional bounds and ownership capabilities checked?
9. How should a projection be spelled and named, and should it be declared separately
   from the opaque type? How do automatic method receiver narrowing and direct borrows work?
10. How does this design compose with the alternative in RFC-0251, and can transparent
    view declarations in RFC-0109 be replaced by extended aliases?

## Decision

**Outcome:** *(pending)*
