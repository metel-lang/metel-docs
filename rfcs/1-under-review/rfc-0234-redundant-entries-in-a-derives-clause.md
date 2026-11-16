---
id: rfc-0234
title: "Redundant Entries in a derives Clause"
date: '2026-11-16'
status: under-review
updated: '2026-11-16'
tracking: 2064
---

> **Status — under review (2026-11-16).**

## Summary

`derives Copy` also derives the `Clone` that `Copy` marks `deriving` (RFC-0213 section 4). A `derives` clause that also lists
`Clone` restates what `Copy` already brings: `derives Clone, Copy`. Today it is accepted. This RFC asks that it be an error with a
fix-it that deletes the restating entry, and states the rule for every aspect a sibling entry brings, not only `Clone`:

> A `derives` entry for an aspect that another entry of the same clause already derives, as one of that entry's `deriving`
> super-aspects, is `T0015` (two derivations of one aspect), with a fix-it that deletes it.

```metel
struct Dup derives Clone, Copy { n: i64 }     // error: Clone is already derived by Copy; delete `Clone`
struct Dup derives Copy { n: i64 }            // the whole declaration
struct Cell<T> derives Copy via T { value: T }    // Copy and Clone when T is (RFC-0227 section 2)
```

This is a design draft. Nothing here is accepted. It is split from RFC-0227, which decides what the brought `Clone` is bounded by
and does not decide whether a clause may restate it.

---

## Motivation

1. **The spelling reads as a conflict.** `derives Clone, Copy` looks like two grants that could disagree, and the reader has to
   know that `Copy` brings `Clone` to see that they cannot. RFC-0227's review raised it ("`derives Clone, Copy` reads like it
   should actually conflict").
2. **There is a second way to write one thing.** The language rejects the same overlap one level down: a *written* `Clone` on a type
   that derives `Copy` is `T0015` (RFC-0206 section 2 rule 2), because it overlaps the brought impl. A derived entry that overlaps it
   is accepted only because the entry is coalesced with the brought one.
3. **It is a hazard for a stated flow.** Under RFC-0227 an explicit `Clone` entry beside a `Copy` entry has a flow of its own, and
   RFC-0227 has to say what happens when it differs from the brought flow. Making the entry an error removes that case.

No program in the corpus depends on the redundancy except the std declarations RFC-0227 section 2 rewrites (`Option`, `Result`),
and RFC-0213 section 5's `Dup` example. The language has no users to migrate.

---

## Proposal

### 1. The rule

For a `derives` clause, let *brought(E)* be the aspects that entry `E` derives as `deriving` super-aspects of its own aspect
(RFC-0213 section 4; for `Copy`, `Clone`). Another entry `F` of the same clause for an aspect in *brought(E)* is an error, `T0015`,
reported at `F`, with the fix-it "`Clone` is derived by `Copy`; delete this entry".

- It applies whatever flow `F` states, and whether or not `E` states one: the entries are the same derivation, so a stated flow on
  `F` is either equal to the brought one (redundant) or different (a conflict). Both are the same error.
- It applies to every aspect with `deriving` super-aspects, as the aspects that have them are declared (RFC-0212). Today that is
  `Copy` with `Clone`.
- It does not apply to a type that is `Clone` and not `Copy` at any instantiation: `derives Clone` alone is the declaration.

### 2. What does not change

- The brought `Clone` itself: its condition and its flow are RFC-0227 section 2's, and `derives Copy via T` is one complete entry.
- A written `Clone` on a type that derives `Copy` stays `T0015` (RFC-0206 section 2 rule 2).
- RFC-0213's rule that `Copy` brings `Clone`; only the restating entry is affected.

### 3. Migration

Delete the restating entry. std's `Option` and `Result` become `derives Copy via T` and `derives Copy via T + E` under
RFC-0227; RFC-0213 section 5's `Dup` example becomes `derives Copy`. The diagnostic's fix-it gives the exact edit.

---

## Interaction with other work

- **RFC-0227** (under review): its section 2 makes the brought `Clone` carry `Clone`'s condition, which is what makes the
  restating entry unnecessary. This RFC does not depend on its other parts; if RFC-0227's section 2 is not adopted, the
  restating entry may be the only way to say "`Clone` for every cloneable argument, `Copy` for copyable ones", and this RFC does
  not apply.
- **RFC-0213** (integrated): section 5's `Dup` example changes.
- **RFC-0206** (integrated): the `T0015` of a written `Clone` is the sibling rule.
- **RFC-0224** (integrated): its `via` clause applies to the `Copy` entry; no second `via` is written for the brought `Clone`.

---

## Alternatives considered

1. **Accept the redundancy (today).** Costs the second spelling and the equal-flow question RFC-0227 would otherwise have to answer.
2. **A warning.** The language has no warning mechanism (RFC-0005 is a stub), so a warning would introduce the whole category for one
   case.
3. **Make the entry meaningful.** Let `derives Clone, Copy` mean something different from `derives Copy`, for example `Clone` for
   every cloneable argument and `Copy` for copyable ones. RFC-0227 section 2 gives `derives Copy via T` that meaning already, so
   the second spelling would carry no new information.

---

## Open questions

1. **Every brought aspect, or `Clone` only?** The rule is stated for every `deriving` super-aspect. Only `Copy` has one today, so
   the two readings agree until another aspect declares one.
2. **Does the error reach a restating entry on a type that states no flow anywhere?** The rule says yes: `derives Clone, Copy` with
   no `via` on either is `T0015`. The alternative accepts the flow-free form as shorthand and errors only when a flow is stated.

---

## Decision

**Outcome:** *(pending)*
