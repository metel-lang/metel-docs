---
id: rfc-0234
title: "Brought Super-Aspects in a derives Clause"
date: '2026-11-16'
status: under-review
updated: '2026-11-16'
tracking: 'https://github.com/metel-lang/metel-core/issues/2064'
---

> **Status — under review (2026-11-16).** Split from RFC-0227, which keeps the stated-flow rule and the `pub` statement. This RFC
> decides the two things about the `Clone` a `Copy` brings that RFC-0227's review raised: what condition it carries, and whether a
> clause may restate it.

## Summary

`derives Copy` also derives the `Clone` that `Copy` marks `deriving` (RFC-0213 section 4). This RFC states two rules for such a
*brought* entry:

1. **The brought `Clone` carries `Clone`'s own condition**, on the flow of the entry that brought it. `derives Copy via T` is the
   whole declaration of a type that is `Copy` when `T` is and `Clone` when `T` is.
2. **A clause may not restate a brought aspect.** A `derives` entry for an aspect that another entry of the same clause already
   derives as one of its `deriving` super-aspects is `T0015` (two derivations of one aspect), so `derives Clone, Copy` is an error.

```metel
struct Dup derives Clone, Copy { n: i64 }              // error (T0015): Clone is already derived by Copy; delete `Clone`
struct Dup derives Copy { n: i64 }                      // the whole declaration
struct Cell<T> derives Copy via T { value: T }          // Copy when T is Copy; Clone when T is Clone
```

This is a design draft under review. It amends no integrated RFC's text: RFC-0224 section 3's sentence on the brought `Clone`,
RFC-0213 section 5's `Dup` example and RFC-0206's account of the brought `Clone` are replaced by this RFC when it is integrated.
Tracked by metel-core#2064.

---

## Motivation

1. **Today a conditional `Copy` brings a `Clone` with `Copy`'s condition, so the declaration has to be written twice.** For
   `struct W<T> derives Copy { v: T }`, `W<String>` is not `Copy`, and with the condition `Copy` carries it has no `Clone` either:
   `w.clone()` is `T0012`, "`String` does not implement `Copy`". A type that is `Clone` for a non-`Copy` argument is declared
   `derives Clone, Copy via T`, which is accepted. Std's `Option` and `Result` are written that way.
2. **That spelling reads as a conflict.** `derives Clone, Copy` looks like two grants that could disagree, and the reader has to
   know that `Copy` brings `Clone` to see that they cannot. (RFC-0227's review: "`derives Clone, Copy` reads like it should
   actually conflict".)
3. **A restating entry has a flow of its own.** With a brought `Clone`, an explicit `Clone` entry beside `Copy` is a second
   derivation of one aspect whose flow can differ from the brought one. Making the entry an error removes that case.
4. **The language already rejects the same overlap one level down.** A *written* `Clone` on a type that derives `Copy` is `T0015`
   (RFC-0206 section 2 rule 2), because it overlaps the brought impl.

---

## Proposal

### 1. The brought `Clone` carries `Clone`'s condition

`derives Copy` brings `Clone` as the derivation of `Clone` itself, on the flow of the entry that brought it:

```
derives Copy via T      writes     extend<T: Copy>  W<T>: Copy
                        and        extend<T: Clone> W<T>: Clone      // the brought entry: Clone via T
```

The brought `Clone` is bounded by `Clone`, not by `Copy`, on the flow parameters. The two impls are the same at every
instantiation where the `Copy` holds: `X: Copy` proves `X: Clone` (RFC-0213), and for a `Copy` instantiation the body is the
representation copy, which equals the element-wise clone. They differ where `Copy` does not hold: `W<String>` is not `Copy`, and
with `Copy`'s condition it also had no `Clone`.

- **One entry declares both.** `Option<T>` and `Result<T, E>` in std become `derives Copy via T` and `derives Copy via T + E`.
- **A stated flow on the brought entry is the `Copy` entry's.** There is no second `via` to write. A type that needs a `Clone`
  flow different from its `Copy` flow is not a case this clause expresses; it writes `derives Clone via ..` and no `Copy`.
- **A written `Clone` on a type that derives `Copy` stays `T0015`** (RFC-0206 section 2 rule 2): it overlaps the brought impl.

### 2. A clause may not restate a brought aspect

For a `derives` clause, let *brought(E)* be the aspects that entry `E` derives as `deriving` super-aspects of its own aspect
(RFC-0213 section 4; for `Copy`, `Clone`). Another entry `F` of the same clause for an aspect in *brought(E)* is `T0015`, reported
at `F`, in whichever order the entries are written.

- **Whatever `F` states.** `F` with no `via`, with a `via` equal to the brought flow, or with a `via` that differs: all are the
  error. `derives Clone, Copy` with no `via` anywhere is the error too; there is no shorthand carve-out, since a second spelling is
  what the rule removes.
- **The fix-it depends on the flows.** When `F` states no flow or the brought flow, the fix-it deletes `F` ("`Clone` is derived by
  `Copy`; delete this entry"). When `F` states a different flow the entry is not a restatement, and deleting it changes the
  type's interface, so the error names both flows ("`Clone` is brought by `Copy` with flow `A + B`; this entry states `A`") and
  offers no automatic edit.
- **Every brought aspect.** The rule is stated for every `deriving` super-aspect, not for `Clone` alone. The spec accepts a
  `deriving` mark only on an aspect declared in std, so `Copy` with `Clone` is the only case until std declares another.
- A type that is `Clone` and not `Copy` at any instantiation writes `derives Clone` and no `Copy`.

### 3. Migration

Delete the restating entry. Std's `Option` and `Result` change as in section 1; RFC-0213 section 5's `Dup` example becomes
`derives Copy`. The language has no users to migrate, and no program in the corpus depends on the restating spelling except those
std declarations and that example.

---

## Interaction with other work

- **RFC-0227** (under review): it states the flow rule and the `pub` statement for every field-wise derivation and does not depend
  on this RFC. Its section 2 refers here for the brought entry's condition.
- **RFC-0224** (integrated): section 3's sentence "`Wrapper<X>: Clone` when `X: Copy`" is replaced by section 1:
  `Wrapper<X>: Clone` when `X: Clone`.
- **RFC-0213** (integrated): section 5's `Dup` example changes (section 3 here).
- **RFC-0206** (integrated): section 2 rule 2 is unchanged for a `Copy` instantiation; for a conditional `Copy` the brought
  `Clone` also covers the instantiations that are not `Copy`.

---

## Alternatives considered

1. **Keep `Copy`'s condition on the brought `Clone`.** Leaves `derives Clone, Copy via T` as the only way to say "`Clone` for every
   cloneable argument, `Copy` for copyable ones", with the redundant-looking entry that reads as a conflict.
2. **Accept the restating entry.** Costs the second spelling and the equal-flow question for a stated flow.
3. **A warning for the restating entry.** The language has no warning mechanism (RFC-0005 is a stub), so a warning would introduce
   the whole category for one case.
4. **Let `derives Clone, Copy` mean something different from `derives Copy`.** Section 1 already gives `derives Copy via T`
   that meaning, so the second spelling would carry no new information.

---

## Costs

The implementation of the brought entry changes (its bound is `Clone`, not `Copy`), std's two declarations change, and the
clause expansion gains the rejection of section 2.

---

## Open questions

None known.

---

## Decision

**Outcome:** *(pending)*
