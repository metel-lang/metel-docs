---
id: rfc-0234
title: "Super-Aspect Derivation Is an Obligation"
date: '2026-11-16'
status: integrated
updated: '2026-11-16'
tracking: 'https://github.com/metel-lang/metel-core/issues/2064'
coverage:
  "1": { kind: blocked, reason: "The obligation is not checked until metel-core#2066.", ref: "https://github.com/metel-lang/metel-core/issues/2066" }
  "2": { kind: blocked, reason: "The entailment is not checked until metel-core#2066.", ref: "https://github.com/metel-lang/metel-core/issues/2066" }
  "3": { spec: "spec.declarations.aspects.declaration-clauses.legality-6" }
  "4": { spec: "spec.ownership.copy.legality-4" }
  "5": { spec: "spec.ownership.aspects-on-a-residual.legality-1" }
  "6": { kind: untestable, reason: "The migration section lists corpus edits and states no rule." }
impl_tracking: 2066
impl_status: not-started
---

> **Status — under review (2026-11-16).** Split from RFC-0227 (derivation arguments, which replaces `via`). It settles
> what the mark on a super-aspect (today `deriving`, `derived` under RFC-0235) means, after RFC-0227's review raised the `Clone` a `Copy` brings.

> **Status — accepted (2026-11-16).** No open questions; design settled with the language owner 2026-11-16.

> **Status — integrated (2026-11-16).**

## Summary

A super-aspect entry marked `deriving` (`aspect Copy: deriving Clone`, RFC-0213 section 4; written `aspect Copy requires derived Clone` under RFC-0235) says that the sub-aspect's law is stated
over the super-aspect's method. Today the mark makes `derives Copy` also *generate* the `Clone`. This RFC changes the mark from
generation to an **obligation on the clause**:

> `derives E`, where `E` has a super-aspect entry marked `derived B`, requires that the same type derives `B` as well, in its own entry.
> A clause without it is an error that names the entry to add. A hand-written `extend P: B` beside `derives E` is an error too.

```metel
struct Dup derives Copy { n: i64 }                // error: `Copy` requires a derived `Clone`; add `Clone` to the derives clause
struct Dup derives Clone, Copy { n: i64 }         // the declaration
struct W<T> derives Clone, Copy via T { v: T }    // Clone when T is Clone (computed); Copy when T is Copy (stated)
copy struct P { n: i64 }                          // the class keyword declares both: derives Clone, Copy
```

Nothing is generated, so nothing is brought: each derivation carries its own condition and its own flow. The mark keeps its job,
which is to make the law hold **by construction**, as a check instead of a generation: the `Clone` of a `Copy` type is always the
compiler's, so it is the representation copy.

This is a design draft under review. It replaces RFC-0213 section 4 rule 2 (generation), RFC-0206's "provided `Clone`" and
RFC-0224 section 3's sentence on the brought `Clone` when it is integrated. Tracked by metel-core#2064.

---

## Motivation

1. **The brought `Clone` has no good condition.** Generated from the `Copy` entry, it carried `Copy`'s condition: for
   `struct W<T> derives Copy { v: T }`, `W<String>` has no `Clone` (`w.clone()` is `T0012`, "`String` does not implement
   `Copy`"). A type that is `Clone` for a non-`Copy` argument had to write `derives Clone, Copy via T`. Giving the brought
   entry `Clone`'s own condition (the earlier form of this RFC) needs a second set of rules: its flow is the `Copy` entry's, a
   restating entry is an error, a differing flow is a different error.
2. **Generation is the novel part.** Haskell and Rust require the super-instance to exist and never generate it from the
   sub-aspect's derivation; Swift generates a missing one. A declared per-edge mark that does it is the unproven combination
   RFC-0213 rates a moderate risk, and adding or removing the mark changes downstream impl sets. An obligation is the
   established model.
3. **The law needs only a check.** "`clone` of a `Copy` type is its copy" holds when no `Clone` for a `Copy` type is
   hand-written: primitives are built in, every field of a `Copy` type is `Copy`, so by induction every `Copy` type's `clone` is
   its copy. The check is the rule that the `Clone` is derived. Generation is not needed to establish it.
4. **The clause shows what the type has.** `derives Clone, Copy` lists both impls the type gets. It no longer hides one behind
   the other.

---

## Proposal

### 1. The obligation

For an aspect `E` with a super-aspect entry marked `derived B`:

1. `derives E` requires `derives B` in the same clause (`copy struct P` and the other class keywords count as their entries,
   section 3). Otherwise it is an error naming the entry: "`Copy` requires a derived `Clone`; add `Clone` to the derives clause".
   The requirement is transitive through `derived` entries of `B`.
2. A written `extend P: B` for a type whose clause derives `E` is an error ("`Copy` requires a derived `Clone`; this type writes
   one"). This is today's `T0015` outcome with a message that names the obligation. The fix-it depends on `E`: delete the impl
   in every case; or, when `E` can be written by hand (`Eq`: `extend P: Eq;`, RFC-0213), write `E` by hand too so that it is no
   longer derived. `Copy` is sealed and granted only in the declaration (RFC-0206), so for `Copy` the choices are to delete the
   written `Clone` or to drop `Copy`.
3. If `B` has no derivation (RFC-0207), `derives E` is an error: both are written by hand. The entry is an obligation in the
   sense of an unmarked entry, with the stronger requirement that `B` be derived when `E` is.
4. Derivation stays idempotent per type and aspect: listing an aspect twice derives it once (RFC-0213 section 4 rule 4).
5. The colon list (`struct P: A`) generates nothing and is unchanged for an aspect it can grant: every super-aspect must already
   exist for `P`. It cannot grant an aspect that has a derivation, and an aspect with a marked super-aspect has one by
   definition (its recipe includes the super), so the obligation concerns `derives` and the class keywords only. Today
   `struct P: Copy` is already `T0046`, "`Copy` is granted by derivation, so the colon list cannot grant it".

An unmarked super-aspect entry (`aspect Error: Display`) stays an ordinary obligation that the super-aspect *exist*, written or
derived.

### 2. Conditions and flows

Each derivation has its own condition: `derives Clone, Copy via T` is `extend<T: Clone> W<T>: Clone` and
`extend<T: Copy> W<T>: Copy`. The obligation requires that `Copy` entail `Clone`: `Clone` must hold at every instantiation where
`Copy` does. RFC-0224's sufficiency rule (the stated `Copy` flow contains every parameter a field depends on) together with the
computed `Clone` flow already guarantees it. A stated `Clone` flow (RFC-0227) that is larger than the `Copy` flow, so that
`Clone` can fail where `Copy` holds, is an error at the `Copy` impl, from the super-aspect obligation, naming the parameter.

### 3. Class keywords

`copy struct P` is `struct P derives Clone, Copy` (it was `derives Copy`, RFC-0207). The keyword declares the class, and the class
needs both impls. `copy enum` is the same. A clause that lists `Clone` or `Copy` as well is idempotent.

### 4. The body of a derived `Clone` on a `Copy` type

A derived `Clone` at an instantiation where the type is `Copy` is the representation copy, the same operation as the implicit copy
of a use by value, not a field-by-field clone that happens to agree with it. Because no `Clone` for a `Copy` type can be written
(section 1 rule 2), nothing observes the difference except the cost. This is RFC-0206's "elided provided `Clone`" restated: the
`Clone` of a `Copy` type is derived and is the copy.

### 5. Residuals

A residual has no clause (RFC-0137, RFC-0211). A residual that is `Copy` is `Clone` by the entailment `Copy` implies `Clone`
(RFC-0168's super-aspect relation, RFC-0213), and its `clone` is the copy, as section 4 says for any `Copy` instantiation.
Where RFC-0217 gives a residual a derived `Clone` by a row template, section 4 applies to it too. The words "the provided
`Clone` that `Copy` brings" in RFC-0211, RFC-0217 and the spec's ownership chapter describe this entailment and are replaced
by it when this RFC is integrated.

### 6. Migration

Std's `Option` and `Result` stay `derives Clone, Copy via T` and `derives Clone, Copy via T + E`: `Clone` has its computed flow
and `Copy` its stated one. RFC-0213 section 5's `Dup` example becomes `derives Clone, Copy`. A type that derives `Copy` alone adds
`Clone`; the diagnostic's fix-it gives the edit. The language has no users to migrate, but the corpus does: at the time of
writing 57 uses of `derives Copy` without `Clone` in 41 fixture files and about 20 mentions in the spec change. `copy struct`
and `copy enum` are unaffected, since they expand to both entries.

---

## Interaction with other work

- **RFC-0227** (under review): replaces `via` with derivation arguments (`derives Clone(T), Copy(T)`) and widens the `pub` statement. It does not depend on this
  RFC, and this RFC does not depend on it: with today's `via` on `Copy` only, section 2 holds with the computed `Clone` flow. If
  RFC-0227 is adopted, a stated `Clone` flow is subject to section 2's entailment.
- **RFC-0213** (integrated): section 4 rules 2 and 3 are replaced by section 1; the mark's name and its std-only restriction are
  unchanged. Opening the mark to user aspects (RFC-0213 open question 9) is no longer a generation question, since nothing is
  generated.
- **RFC-0206** (integrated): the provided, unwritable `Clone` of a `Copy` type becomes the derived `Clone` of section 4, with the
  written case rejected by section 1 rule 2.
- **RFC-0207** (implemented): `copy struct` is `derives Clone, Copy` (section 3).
- **RFC-0211** (integrated) and **RFC-0217** (under review): a `Copy` residual's `Clone` is the entailment of section 5; their
  "brings" wording is replaced at integration.
- **RFC-0224** (integrated): section 3's sentence on the brought `Clone` is replaced by section 2.
- **RFC-0168** (draft): `Eq: deriving PartialEq` (`Eq requires derived PartialEq`) becomes `derives PartialEq, Eq`, the same obligation.

---

## Alternatives considered

1. **Keep generation, give the brought `Clone` `Clone`'s condition** (this RFC's earlier form). It needs a flow rule for the
   brought entry, an error for a restating entry and a second error for a differing flow, to express what an explicit list
   already says.
2. **Remove the mark; supers are plain obligations.** Loses the guarantee that the `Clone` of a `Copy` type is the copy, unless a
   separate rule re-adds it, which is this RFC's section 1 rule 2.
3. **A blanket `extend<T: Copy> T: Clone` in std.** Overlaps every derived `Clone` at the `Copy` instantiations, and cannot be split
   by `T: !Copy` because `Copy` is conditional (`W<T>` is `Copy` only when `T` is).
4. **A sub-aspect method binding (`Copy` provides `Clone::clone`).** The same overlap, or `Clone` available only where `Copy`
   holds. The copy-or-clone choice can only be made per instantiation, in the body (section 4).
5. **Dispatch priority for super-aspect methods.** A new language feature with an instantiation-dependent rule, and the written
   `Clone` still has to be rejected or it is silently shadowed.

---

## Costs

- **Verbosity.** `derives Clone, Copy` is longer than `derives Copy`, and `copy struct` is the short form. A `pub` generic `Copy`
  type that states a flow for `Clone` as well (RFC-0227) states it twice (`derives Clone(T), Copy(T)` under RFC-0227); the repetition is short and RFC-0227 adds no group syntax for it.
- **Implementation.** The clause expansion stops generating the marked super and checks for it instead; `copy struct` expands to
  both entries; the derived `Clone` body uses the copy at `Copy` instantiations; the error messages change. Section 4 needs one
  derived `Clone` body of a conditional type to choose per instantiation, so whether `T` is `Copy` must be known where the body
  runs, in a generic body of the interpreter as in a monomorphised one. If that proves costly, the rule holds as "observably the
  copy" (nothing can tell the difference once a written `Clone` is rejected), at the price of the literal identity.

---

## Open questions

None known.

---

## Decision

**Outcome:** *(pending)*
