---
id: rfc-0207
title: "Declaration Clauses: derives and the Colon List"
date: '2026-11-02'
status: implemented
updated: '2026-11-13'
tracking: 'https://github.com/metel-lang/metel-core/issues/1786'
coverage:
  "1": { spec: "spec.declarations.aspects.declaration-clauses.legality-1" }
  "2": { spec: "spec.declarations.aspects.declaration-clauses.legality-3" }
  "3": { spec: "spec.declarations.aspects.declaration-clauses.legality-6" }
  "4": { kind: untestable, reason: "Section 4 states what the RFC does not do; it adds no rule." }
  "5": { kind: untestable, reason: "The worked examples are fixtures citing the declaration-clause rules." }
impl_tracking: 'https://github.com/metel-lang/metel-core/issues/1800'
impl_status: implemented
---

> **Extracted from RFC-0162 on 2026-11-02** (its Axis C), and **cut down on 2026-11-03** when the
> `Copy`/`Clone` settlement was redesigned (RFC-0206; since 2026-11-05 around a sealed `Copy` and the class
> keywords of RFC-0089). The earlier draft proposed `header` and `derivable` declaration modifiers, a
> `provides` clause and a selection rule over overlapping impls; the adversarial review found
> those unnecessary for the settlement and they are not carried. Nothing here is decided.

> **Status — under review (2026-11-03).** Tracking metel-core#1786, v0.16.0.

> **Status — accepted (2026-11-05).** Ratified in the Copy and Clone settlement sweep (metel-core#1824); spellings ratified by the language owner 2026-11-05

> **Status — integrated (2026-11-10).**

> **Implementation note (2026-11-10).** Implemented before this integration step (see RFC-0206's note). The implementation follows the text except: the generic derive bounds exactly the type parameters a field's aspect depends on, computed through the flow of each type a field names (RFC-0224; metel-core#1819 for `Copy`, #1938 for `Clone`, #1964 for declarations in function bodies). Details the text left open: the clauses are accepted on a named `record` as on a struct (RFC-0206 section 3), `linear` is a parse error until `Linear` exists, a negative colon-list entry is a parse error, and the clause impls are written after name resolution (`pipeline/clause_expansion.rs`). The error codes are T0046 (invalid entry) and T0003 (unknown aspect).

> **Status — implemented (2026-11-13).** Implemented in the compiler in the v0.16.0 stage Declarations and derivation.

## Summary

A type declaration may carry two clauses after its name:

```metel
copy struct Point { x: i64, y: i64 }                         // class keyword: one-word form of `derives Copy`
struct Pixel derives Copy, Debug { x: i64, y: i64 }          // derives: the compiler writes the marker, its Clone and Debug
struct Doc derives Clone, Debug { title: String }            // derives: what the compiler writes
struct Ticket: Validated derives Debug { id: i64 }           // colon list: a user marker (an unchecked promise); both clauses
linear struct Receipt { id: i64 }                            // class keyword: exactly once (reserved until Linear is implemented)
```

- **The colon list** names facts about the type that the compiler checks and that change what its
  uses mean: a `declared` method-less user marker (an unchecked promise, section 1). It has no
  negative entries: an opt-out of an `auto` aspect stays the existing bodyless negative impl
  (`extend Token: !Send;`, RFC-0102). A colon-list opt-out is recorded as an alternative in
  RFC-0096.
- **The `derives` clause** requests that the compiler generate an implementation of an aspect
  that has a derivation (`Copy`, `Clone`, `Debug`). The **class keywords** `copy` and `linear` before
  `struct` and `enum` are sugar for these clauses (section 3).

Derivation is always explicit: a type with neither a `derives` entry nor an `extend` of an aspect
does not have it. A written `extend` and a `derives` entry for the same aspect and type overlap and
are an error.

## Motivation

RFC-0162 (D6) argues that `Copy` is a grant whose effect, a change in what every use of the type
means, is out of proportion to where it is written. RFC-0206 moves that grant to the declaration. A
place in the declaration is needed for it, and for derive requests (RFC-0093's `#derive` is both a
request on a type and a registration on a function), and for `!Send`-style opt-outs (RFC-0105's
aspect lists, RFC-0096's auto aspects). This RFC names those places, once.

---

## 1. The colon list

Entries are `declared` aspects (RFC-0212) with no methods. The colon **authorizes**: the type claims the
capability in its declaration, and the supporting impls must exist (written by hand or requested in
`derives`). `derives` **generates**: the compiler writes the impls it names.

1. A positive entry must name an aspect that is `declared` and has no methods; a `declared` aspect is
   granted only through a declaration clause (RFC-0212). A user marker (`declared aspect Validated;`) is an
   unchecked promise, visible in the declaration, until refinement types (RFC-0202) can check it. An aspect
   with a `deriving` super-aspect, such as `Copy`, is granted through `derives` (or its class keyword), not the
   colon list, because the super-aspect it brings is generated (RFC-0213 section 4). Naming any other aspect is an error
   with a fix-it: a method-bearing aspect goes in `derives` or `extend`. No rule keys on a name or on
   std provenance.
2. There are no negative entries. An opt-out of an `auto` aspect (`Send`, `Sync`, RFC-0096)
   is the existing bodyless negative impl, `extend T: !Send;` (RFC-0102, RFC-0081), which is legal
   anywhere in the type's module. Whether the opt-out should instead be a colon-list entry, so that
   it is visible at the declaration, is an open question of RFC-0096 (item 8), deferred with the
   Send/Sync revision (language owner, 2026-11-04). `Linear` is declared, not `auto`, and has no opt-out.
3. The colon list never generates an impl. Every positive super-aspect of an entry must already exist for the
   type, written or derived, or it is an error naming the missing one (RFC-0213 section 4, rule 5).
4. The grant is in the type's own module, so the orphan rule (`T0014`) holds trivially, and a marker
   cannot be granted to a type you do not own.

## 2. The `derives` clause

1. `derives X` is legal exactly when `X` has a derivation. In the first implementation the
   derivations are native and belong to std (`Clone`; `Debug` and `Display` as they gain one). The
   super-aspects marked `deriving` are derived with their sub-aspect (RFC-0213 section 4), so
   `derives Copy` derives the marker and the `Clone` it brings (RFC-0206). An
   aspect declares it has one with the `derivable` modifier (`derivable aspect Clone { … }`), which
   only std uses until comptime (RFC-0092, RFC-0093) lets a user supply a derivation.
2. The derived impl is generated under the exact condition that every field type satisfies the
   aspect at the instantiation. For a generic type this is evaluated per instantiation, not as a
   bound on the type parameters (RFC-0123's `where ..R: A` is the same condition for records).
3. A field type that cannot satisfy the aspect makes the entry an error at the declaration, next to
   the field.
4. A derived impl and a written `extend` of the same aspect for one type overlap (`T0015`). A type
   customises by writing the impl instead of deriving it.
5. `derives X` is a request, not a registration. It replaces the request half of RFC-0093's
   `#derive(Aspect)`; the registration half becomes the `derivable` declaration, and RFC-0093 is
   narrowed to what a comptime derivation needs when it is integrated.

## 3. Class keywords

`copy` and `linear` before `struct` and `enum` (RFC-0089 section 2.1) state a type's class in one word. Affine is the default and has no keyword (decided 2026-11-06).
They are contextual (not reserved globally), apply to structs and enums and not to the anonymous record type, and
are sugar for the clauses above:
- `copy struct P { … }` is `struct P derives Copy { … }`: the marker and the `Clone` it brings are generated, and
  every field must be `Copy` (RFC-0206 section 2).
- `linear struct T { … }` grants the declared aspect `Linear` in the declaration (RFC-0089 section 2): the type may hold
  linear fields or none (a capability token), and is reserved and marked "Planned for" in v0.16.0, until `Linear` is
  implemented. `extend T: Linear {}` is not legal.
A type with no keyword is affine; the class is never inferred. A type with a linear field and no `linear` keyword is an
error whose fix-it adds it (RFC-0089 section 2). For a generic type a keyword states a capability, not a class:
`copy struct Wrapper<T>` is `Copy` exactly when `T` is, and `linear struct Pair<T>` is linear exactly when a field is. A `pub` generic
type states its condition once computed defaults exist (RFC-0206 section 6, "End state").

## 4. What this does not do

- It does not add `header`, `derivable` (on user aspects) or `provides` machinery for markers, a
  refinement of a marker's condition, or a selection rule over overlapping impls.
- A user marker's entry is an unchecked promise, accepted because the aspect is `declared`. A checked
  promise is better expressed as a refinement type (RFC-0202), and method-bearing aspects in the colon
  list are the later stage of RFC-0105.
- It does not specify the grammar of named records and enums beyond the two clauses; RFC-0209 to
  RFC-0217 (under review) are the derivation templates.

## 5. Worked examples

```metel
copy struct Point { x: i64, y: i64 }                         // ok: Copy, with the Clone it brings
struct Bad: Clone { x: i64 }                                 // error: Clone has methods; write `derives Clone`
struct B2: Copy { x: i64 }                                   // error: Copy brings a derived Clone; write `derives Copy` or `copy struct`
struct B3 derives Copy { x: i64 }                            // ok: derives the marker and its Clone
struct Ticket: Validated { id: i64 }                         // ok: a user marker, an unchecked promise
struct Token { id: i64 }
extend Token: !Send;                                         // ok: the existing opt-out of an auto aspect
struct C: !Clone { x: i64 }                                  // error: the colon list has no negative entries
struct D derives Clone { n: i64 }
extend D: Clone { fun clone(&self) -> D { D { n = 0 } } }    // error T0015: overlaps the derived impl
copy struct F { n: i64 }
extend F: Clone { fun clone(&self) -> F { F { n = 0 } } }    // error T0015: overlaps the Clone that `Copy` brings
struct E derives Clone { s: NoClone }                        // error at the field: NoClone is not Clone
```

## Relationship to existing RFCs

- **RFC-0206** — `Copy` and `Clone`, the first user of `derives` and of the class keywords.
- **RFC-0089** — the lattice and the keywords (`copy`, `linear`) of section 3.
- **RFC-0162** — the model and the Axis C analysis this was extracted from.
- **RFC-0093 / RFC-0092** — derive registration and comptime; `derives` is the request half.
- **RFC-0096** — auto aspects, whose opt-out stays the negative `extend`; the colon-list form is
  an open question there, deferred.
- **RFC-0105** — aspect lists in declarations; its later stage (method-bearing aspects after the
  colon, qualified methods in the body) is untouched.
- **RFC-0123 / RFC-0209** — the field-wise condition and the row templates a derivation can use.
- **RFC-0202** — refinement types, the checked alternative to an unchecked marker.

## Open questions

1. **Spelling:** `derives` against `derive`, and the clause order (colon list first).
2. **User-declared `derivable` aspects** wait for comptime; until then only std declares them.
3. **User markers:** resolved. A `declared` method-less aspect is admitted by property (rule 1), as an
   unchecked promise until RFC-0202 can check it.
4. **`Debug` and `Display`:** which std aspects gain a derivation in the first implementation.
5. **Two spellings for a method-less aspect.** `struct T: Validated` and `extend T: Eq;` both state a
   marker. They differ in kind, not in taste: the colon list is limited to markers that are `declared`
   (RFC-0212), which cannot be granted by `extend`, so the declaration is the only place to say it. `Eq`,
   `Send` and the like are grantable by `extend`, and `extend T: Eq;` is the existing form (RFC-0168). Whether a
   grantable marker may also appear in the colon list is not proposed.
6. **The class keywords:** their contextual spelling, their use on enums, and whether `copy struct` on a generic
   type needs the condition in the header (RFC-0206 section 6).
   *Resolved 2026-11-10 by RFC-0224:* a `derives Copy` entry takes an optional `via A + B` flow list; `copy struct` takes
   none, and a `pub` generic type states a non-empty flow.

---

## Decision

**Outcome:** *(pending)*
