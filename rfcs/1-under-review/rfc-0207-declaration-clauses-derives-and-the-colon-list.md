---
id: rfc-0207
title: "Declaration Clauses: derives and the Colon List"
date: '2026-11-02'
status: under-review
updated: '2026-11-03'
tracking: 'https://github.com/metel-lang/metel-core/issues/1786'
---

> **Extracted from RFC-0162 on 2026-11-02** (its Axis C), and **cut down on 2026-11-03** when the
> `Copy`/`Clone` settlement was redesigned around a compiler-known `ImplicitClone` marker
> (RFC-0206). The earlier draft proposed `header` and `derivable` declaration modifiers, a
> `provides` clause and a selection rule over overlapping impls; the adversarial review found
> those unnecessary for the settlement and they are not carried. Nothing here is decided.

> **Status — under review (2026-11-03).** Tracking metel-core#1786, v0.16.0.

## Summary

A type declaration may carry two clauses after its name:

```metel
struct Point: ImplicitClone { x: i64, y: i64 }               // colon list: what the type is
struct Doc derives Clone, Debug { title: String }            // derives: what the compiler writes
struct Token: !Send derives Debug { id: i64 }                // both; the colon list comes first
```

- **The colon list** names facts about the type that the compiler checks and that change what its
  uses mean: a compiler-known declaration-granted marker (`ImplicitClone`, RFC-0206), and opt-outs
  of an `auto` aspect (`!Send`, `!Sync`, RFC-0096).
- **The `derives` clause** requests that the compiler generate an implementation of an aspect
  that has a derivation (`Clone`, `Debug`).

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

Entries are aspects with no methods that the compiler checks.

1. A positive entry must name a compiler-known marker that is granted in the declaration. Today
   that is `ImplicitClone`. Naming any other aspect is an error with a fix-it: a method-bearing
   aspect goes in `derives` or `extend`.
2. A negative entry (`!X`) must name an `auto` aspect (RFC-0096): `Send`, `Sync`, `Linear`. It is the
   opt-out of the structural rule. For any other aspect it says nothing and is an error.
3. The colon list does not generate an impl. The compiler may derive `Clone` as a consequence of
   `ImplicitClone` (RFC-0206 section 2); that is a rule of that marker, not of the clause.
4. The grant is in the type's own module, so the orphan rule (`T0014`) holds trivially, and a marker
   cannot be granted to a type you do not own.

## 2. The `derives` clause

1. `derives X` is legal exactly when `X` has a derivation. In the first implementation the
   derivations are native and belong to std (`Clone`; `Debug` and `Display` as they gain one). An
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

## 3. What this does not do

- It does not add `header`, `derivable` (on user aspects) or `provides` machinery for markers, a
  refinement of a marker's condition, or a selection rule over overlapping impls.
- It does not let a user declare a marker whose entry is an unchecked promise. A checked promise is
  better expressed as a refinement type (RFC-0202), and method-bearing aspects in the colon list
  are the later stage of RFC-0105.
- It does not specify the grammar of named records and enums beyond the two clauses; RFC-0209 to
  RFC-0211 are the derivation templates, which stay drafts.

## 4. Worked examples

```metel
struct Point: ImplicitClone { x: i64, y: i64 }               // ok
struct Bad: Clone { x: i64 }                                 // error: Clone has methods; write `derives Clone`
struct B2 derives ImplicitClone { x: i64 }                   // error: ImplicitClone is granted in the colon list
struct Token: !Send { id: i64 }                              // ok: opt-out of an auto aspect
struct C: !Clone { x: i64 }                                  // error: Clone is not an auto aspect
struct D derives Clone { n: i64 }
extend D: Clone { fun clone(&self) -> D { D { n = 0 } } }    // error T0015: overlaps the derived impl
struct E derives Clone { s: NoClone }                        // error at the field: NoClone is not Clone
```

## Relationship to existing RFCs

- **RFC-0206** — `Clone` and `ImplicitClone`, the first user of the colon list and of `derives`.
- **RFC-0162** — the model and the Axis C analysis this was extracted from.
- **RFC-0093 / RFC-0092** — derive registration and comptime; `derives` is the request half.
- **RFC-0096** — auto aspects, whose opt-out is written in the colon list.
- **RFC-0105** — aspect lists in declarations; its later stage (method-bearing aspects after the
  colon, qualified methods in the body) is untouched.
- **RFC-0123 / RFC-0209** — the field-wise condition and the row templates a derivation can use.
- **RFC-0202** — refinement types, the checked alternative to an unchecked marker.

## Open questions

1. **Spelling:** `derives` against `derive`, and the clause order (colon list first).
2. **User-declared `derivable` aspects** wait for comptime; until then only std declares them.
3. **Whether user markers** (checked or promised) are ever added to the colon list, or are left to
   RFC-0202's refinement types.
4. **`Debug` and `Display`:** which std aspects gain a derivation in the first implementation.

---

## Decision

**Outcome:** *(pending)*
