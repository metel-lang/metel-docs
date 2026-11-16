---
id: rfc-0239
title: "Arguments on the copy Class Keyword"
date: '2026-11-16'
status: draft
---

## Summary

The `copy` class keyword may carry an argument list, the flow of the declaration it stands for:

```metel
pub copy(T) struct Wrapper<T> { value: T }          // = struct Wrapper<T> derives Clone(T), Copy(T)
pub copy(A, B) enum Either<A, B> { Left { a: A }, Right { b: B } }
pub copy() struct Id<T> { n: i64 }                  // = derives Clone(), Copy(): Copy and Clone whatever T is
copy struct Point { x: i64, y: i64 }                // unchanged: no list, the flow is computed
```

`copy(T) struct Foo<T>` is `struct Foo<T> derives Clone(T), Copy(T)`: the class keyword declares both entries
(RFC-0234), and the list is the flow of both. Nothing else about the keyword changes, and no existing program changes
meaning.

This reads the title as "`copy(T) struct Foo` is the class keyword with the flow RFC-0227 gave `derives`". If something
else was meant, the proposal below is not it. This is a design draft. Nothing here is accepted.

---

## Motivation

1. **The keyword cannot be used where the rule needs it most.** RFC-0227 section 3 (the `pub` rule) requires a `pub`
   generic type to state its flow, because the flow is its published interface. `copy struct` takes no argument list
   (RFC-0227 section 1), so a `pub` generic `copy struct` with a non-empty flow is an error whose fix-it is to give up the
   keyword and write `derives Clone(T), Copy(T)`. The one-word form is available for exactly the types that do not need it
   (non-generic, non-`pub`, or an empty flow).
2. **The keyword is the common spelling.** `copy struct` is how the language writes a copyable type (RFC-0207 section 2,
   RFC-0234 section 3). A public generic container should be able to use it too, without a longer form that says the
   same thing twice (`Clone(T), Copy(T)`).
3. **An explicit entry beside the keyword is silently ignored today.** `copy struct H<T> derives Copy(T)` keeps the
   keyword's computed flow and drops the stated one, so `H<String>` is copied (metel-core#2070). The keyword and the
   entries need one rule for who states the flow.
4. **Both entries share one flow in nearly every case.** The class keyword already stands for the pair, and RFC-0234
   section 2 requires the `Clone` flow to be inside the `Copy` flow. A flow written once on the keyword is the case where
   they coincide.

---

## Proposal

### 1. The form

```
class_decl = { pub_kw? ~ class_kw ~ ("struct" | "enum" | "record") ~ .. }
class_kw   = { copy_kw ~ derive_args? | linear_kw }
```

An argument list follows `copy` directly, in parentheses, with the grammar of RFC-0227 section 1: type parameters of the
declaration separated by commas, possibly none. It is accepted only on `copy`. `linear` takes no list: linear types are
reserved (RFC-0207), and whether they take a flow is that RFC's decision.

`copy(P1, .., Pk) struct T<..>` is `struct T<..> derives Clone(P1, .., Pk), Copy(P1, .., Pk)`, and likewise for `enum` and
`record`. `copy() struct T` is `derives Clone(), Copy()`. `copy struct T` (no list) is unchanged: both flows are computed
(RFC-0234 section 3).

### 2. Legality

The rules of RFC-0227 section 2 apply to the list as they apply to the entries it stands for: every argument is a type
parameter of the declaration, a row- or record-kinded parameter is not accepted, and the list must contain every
parameter a field's `Copy` and a field's `Clone` depend on (it may contain more). The stated flow satisfies the `pub`
rule (RFC-0227 section 3): `pub copy(T) struct W<T>` is accepted, `pub copy struct W<T>` is not.

### 3. An explicit entry beside the keyword

A `derives` entry for `Clone` or `Copy` in the same declaration restates an entry the keyword already stands for.

- If the keyword has **no list**, the explicit entry replaces the entry the keyword stands for, with its list:
  `copy struct P<T> derives Clone(T)` states the `Clone` flow and leaves the `Copy` flow computed, and
  `pub copy struct W<T> derives Clone(T), Copy(T)` states both. (Today the explicit entry's list is dropped,
  metel-core#2070; this section is the rule that fixes it.)
- If the keyword **has a list**, an explicit entry for `Clone` or `Copy` is an error, with the fix-it "write `copy(..)` or
  the `derives` entries, not both": the flow would be stated twice, and a silent winner would hide it.

### 4. A different flow for each aspect

The keyword states one flow for both aspects. A type whose `Clone` and `Copy` flows differ (RFC-0234 section 2: the
`Clone` flow inside the `Copy` flow) writes the `derives` entries.

---

## Interaction with other work

- **RFC-0227** (implemented): section 1's "`copy struct` and `copy enum` take no argument list" becomes "take the list of
  this RFC"; its `pub` fix-it for a `copy` declaration names `copy(T)` and no longer the `derives` form.
- **RFC-0234** (implemented): the keyword stays the one-word form of `derives Clone, Copy`; the entailment of the two
  flows holds trivially when they are the same list.
- **RFC-0207** (implemented): the grammar of class keywords gains the optional list; `linear` is untouched.
- **RFC-0219** (implemented): `copy` before a closure literal and `copy` in a written function type are different
  positions and unaffected; the argument list occurs only before a type declaration.
- **Std**: `Option` and `Result` could be written `copy(T) enum Option<T>` and `copy(T, E) enum Result<T, E>`; this RFC
  does not require it.

---

## Alternatives considered

1. **Status quo.** A `pub` generic copyable type writes `derives Clone(T), Copy(T)`. Costs the one-word form for the
   types that most want it.
2. **Allow `pub copy struct` with a computed flow.** Removes the point of the `pub` rule (RFC-0227 section 3).
3. **`copy struct Foo<T>(T)` or a trailing list.** Puts the flow after the name, among the generic parameters, where it
   reads as a tuple or a second parameter list.
4. **`copy<T> struct`.** Angle brackets are the aspect's own type arguments (RFC-0228), not derivation arguments.
5. **Two lists on the keyword, `copy(T) clone(T, U)`.** A second spelling for the case the `derives` entries already
   handle (section 4).

---

## Costs

The class keyword gains a grammar production and the clause expansion states one list for two entries. The
fix-it text of the `pub` rule changes for the keyword. No existing program changes meaning.

---

## Open questions

None known.

---

## Decision

**Outcome:** *(pending)*
