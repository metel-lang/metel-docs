---
id: rfc-0210
title: "Enum Parameters and Variant Rows"
date: '2026-11-02'
status: under-review
updated: '2026-11-04'
tracking: 'https://github.com/metel-lang/metel-core/issues/1791'
---

> **Note, 2026-11-03.** The `Copy`/`Clone` settlement was redesigned: RFC-0206 is now "Clone and
> ImplicitClone", and RFC-0207 is reduced to the `derives` clause and the colon list. The `header` and
> `derivable` modifiers, `provides` and the `derives Copy` spelling that this draft cites are not part
> of that design. What remains relevant here is the derivation of `Clone` by a row template;
> examples below that use `Copy` read as `ImplicitClone` in the colon list.

> **Status — under review (2026-11-04).** Tracker milestoned; reviewed as part of the Copy/Clone settlement (RFC-0206, RFC-0212)

## Summary

RFC-0209 lets a nominal type's row be visible to an aspect's row template, but a template is
written over `{ ..R }`, and an enum has no anonymous counterpart: it is a sum of variants, each
a row of named fields. This RFC adds the missing pieces for enums:

1. **An enum parameter kind**, `<enum E>`: `E` stands for a nominal enum type that has granted
   visibility to the aspect (RFC-0209), usable as a type and as `..E`.
2. **A variant row**, `..E`: the labelled set of `E`'s variants, each member a variant's row of
   fields.
3. **The existing bound, reused**: `where ..E: A` holds when `A` holds for every field of every
   variant of `E`.

```metel
extend<enum E> E: Clone where ..E: Clone {
    fun clone(&self) -> Self {
        // one arm per variant, unrolled at compile time (RFC-0174)
        comptime for variant in ..E { … }
    }
}

enum Shape derives Clone { Circle { r: f64 }, Rect { w: f64, h: f64 } }   // derives entry, RFC-0207
enum Option<T> derives Clone { None, Some { value: T } }
```

`Copy` needs no body. Its sealed `clone` is a bitwise copy (RFC-0206 §2), so a `Copy` enum needs
only the eligibility check `..E: Copy`.

---

## Motivation

RFC-0207 gives named types a header entry and RFC-0209 explains it as the aspect's own template
applied to the type's row. For structs and records the template is the existing `{ ..R }` impl.
For enums nothing equivalent exists:

- **Enums are the exception in the Copy/Clone settlement.** std's `Option`, `Result` and `List`
  have no `Clone` today (metel-core#270), and the `Copy` eligibility check
  (`check_copy_impl_eligibility`) is a hand-written walk over variant payloads. The header entry
  for an enum would be the compiler's own rule, the special case RFC-0207 asks to avoid.
- **A variant is a row.** The spec gives variants as unit (an empty row) or struct-like (named
  fields). RFC-0092's reflection models an enum as `variants = (name, fields: Row)[]`. So the
  structure a template needs exists; it has no name in the type system.
- **RFC-0150 stops at enums.** Nested narrowing treats enums, arrays and function types as
  atomic "unless a future RFC supplies a residual form". This RFC supplies a form for
  *aspect templates*, not for narrowing, which stays out of scope.

The difficulty is that products have an anonymous structural counterpart (a record) that a
template can target, and sums do not. The options, evaluated below, are to leave enums native, to
introduce anonymous sum types, or to give enums a parameter kind. This RFC proposes the kind.

---

## 1. The enum parameter

`<enum E>` declares `E` as a generic parameter that stands for a nominal enum type.

**Legality.**
1. `E` may be instantiated only by an `enum` declaration, and only by one that has granted
   visibility to the aspect of the enclosing `extend` (RFC-0209 section 1). An enum whose header
   does not list the aspect does not match, as a struct does not match a record template today.
2. `E` may be used as a type (`E`, `&E`, `Self`) and as the row operand `..E`.
3. A template whose target is `E` may carry the bound `..E: A`. This is the form RFC-0186
   rejects for `record R` (`T0012`: the bound must name the row tail of a record target); it is
   permitted here because the target is an enum parameter and there is no `{ ..R }` form to
   write instead.
4. `Self` in the template body denotes the matched enum.

**Dynamic semantics.** None; the parameter is erased as other generic parameters are, and the
unrolled body (section 3) is generated per instantiation.

---

## 2. The variant row

`..E` is the **variant row** of `E`: a labelled set whose labels are `E`'s variant names and
whose members are those variants' rows (unit variants contribute the empty row). It reuses the
operator of RFC-0186, "the members of": `..R` for a record, `..Ts` for a pack, `..E` for an enum.

`where ..E: A` holds iff `A` holds for every field of every variant. It is the field-wise bound
one level down: the members of `..E` are rows, and a row satisfies the bound when `..V: A` holds
for it. A unit variant satisfies it vacuously.

```metel
enum Shape: Copy { Circle { r: f64 }, Rect { w: f64, h: f64 } }   // marker entry; holds: f64 is Copy
enum Bad: Copy { A { s: String } }                                // rejected at the declaration, next to `s`
```

For a generic enum the bound is evaluated per instantiation (RFC-0209, R2): `Option<&String>`
is `Clone` and `Option<String>` is `Clone` only because `String` is.

---

## 3. Bodies

`Clone` for an enum matches the active variant, clones its fields and rebuilds the same variant.
That needs three things at compile time:

1. iterating the variants, `comptime for variant in ..E` (RFC-0174, extended from fields to
   variants), and a variant's fields, `comptime for field in ..variant`;
2. matching an arm by a compile-time variant name;
3. constructing a variant by a compile-time name, the way `self.[field.name]` reads a field by one.

The spelling of 2 and 3 is open (Open Question 1). Until RFC-0174 and these two forms exist, std's
field-wise bodies for enums are native hooks, as they are for records (RFC-0206 §4), and a header
entry on an enum is checked by the same `..E: A` bound with a native body. The user-visible
behaviour is the same; only the source of the body differs.

---

## 4. Alternatives considered

1. **Native only.** The compiler keeps its enum rules and no template exists. Declined as the end
   state: it is the stage-1 plan, but a user derivable aspect could never derive for an enum, and
   enums would be the one exception in an otherwise uniform mechanism.
2. **Anonymous sum types** (`enum { A { x: i64 }, B }`), the mirror of anonymous records, so
   RFC-0209's approach carries over unchanged. Declined: it is the largest option and opens open
   unions and structural variants, a far wider decision than this settlement needs. It does not
   exclude this RFC; if anonymous sums arrive, the kind here becomes a convenience.
3. **Encode an enum as a record of optionals** or a tagged record. Declined: it changes the
   representation and the match semantics for the sake of the derivation.
4. **A new bound operator for the nested case**, in place of reusing `..`. Declined: the member
   of `..E` is a row, and a bound on a row member already means "its fields", so the existing
   operator reads correctly and adds no token.

---

## 5. Costs

- **A fourth parameter kind** beside type, `record R` and the row binder of RFC-0208, and a rule
  that the bound `..E: A` is legal on a target that is not `{ ..R }`.
- **Dependence on RFC-0174** for the source-level bodies (iteration over variants and fields) and
  on two forms that do not exist (match and construct by compile-time name).
- **Enum reflection leaks the variant structure** of an enum to the aspect's module, as a struct's
  row does under RFC-0209; field privacy is open in both.

---

## Relationship to existing RFCs

- **RFC-0209** — per-aspect row visibility; this RFC extends it to enums.
- **RFC-0207 / RFC-0206 / RFC-0162** — header entries, `Clone`, and the Copy/Clone model.
- **RFC-0186 / RFC-0208** — the `..` operator and the row-only binder.
- **RFC-0174 / RFC-0092** — compile-time iteration and reflection (`variants`).
- **RFC-0150** — nested narrowing, which treats enums as atomic; unchanged.
- **RFC-0078** — the bottom type; an enum with no inhabited variant satisfies every `..E: A`
  vacuously.
- **metel-core#270** — std `Clone` impls, which this RFC would express as `enum Option<T> derives Clone`.

## Open questions

1. **Spelling of match and construct by compile-time variant name** (for example
   `Self::[variant.name] { … }`), and whether they belong here or in RFC-0174.
2. **The binder**: `<enum E>` is a sketch. Whether it should be a modifier of `record R`'s family,
   or inferred from use, is open.
3. **A variant row without the enum**: whether `<..V>` (RFC-0208) should also be allowed to stand
   for a variant row, which would matter only if anonymous sums arrive.
4. **Field privacy** across the aspect's module and the enum's module (as in RFC-0209).
5. **Recursive enums.** A recursive enum satisfies `..E: A` coinductively, or the bound is
   rejected; `List`'s `Clone` shows the need.
6. **Narrowing and match refinement**: whether a template can see a narrowed variant after a
   match, which belongs to the residual RFC.
7. **Which std enums** (`Option`, `Result`, user enums) take header entries first, and how that
   interacts with the hand-written impls of metel-core#270.

---

## Decision

**Outcome:** *(pending)*
