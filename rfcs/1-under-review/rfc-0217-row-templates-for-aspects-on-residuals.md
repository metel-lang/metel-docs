---
id: rfc-0217
title: "Row Templates for Aspects on Residuals"
date: '2026-11-06'
status: under-review
updated: '2026-11-06'
tracking: 'https://github.com/metel-lang/metel-core/issues/1834'
---

> **Status — draft (2026-11-06).** Split from RFC-0211 on 2026-11-06. RFC-0211 (accepted) keeps the rules that
> apply in v0.16.0; this RFC is the end state. Nothing here is decided.

> **Not a dependency.** The Copy/Clone settlement (RFC-0206, RFC-0207, RFC-0211, RFC-0212, RFC-0213) does not
> wait for this RFC. Until it is accepted and implemented, structural `Copy` on named types and their residuals is
> native compiler logic (metel-core#1823) and every other aspect on a residual is `T0012` (RFC-0211).

> **Status — under review (2026-11-06).** Split from RFC-0211: the template half

## Summary

A value narrowed by a partial move or a projection has a **residual** type, `Doc.{ title }`: the same brand with
fewer fields (RFC-0137). RFC-0211 says what a residual satisfies in v0.16.0. This RFC sets the end state:

> A **granted aspect's row template** (RFC-0209) applies to every residual of the granted brand, with the
> template's `where` bound evaluated over the residual's **present** fields. A **hand-written** impl applies to the
> full type only (RFC-0211 rule 2).

```metel
struct Doc derives Clone { title: String, n: i64 }   // the derives entry: the Clone template applies
copy struct Point { x: i64, y: i64 }

let q := d.{ title };        // q : Doc.{ title }
q.clone()                     // Doc.{ title }: the template clones the present field
let p2 := p.{ x };            // p2 : Point.{ x }, Copy because x is
```

---

## Motivation

- **A derived aspect should reach residuals.** After RFC-0211, `Doc derives Clone` has a whole-type `Clone` but
  `d.{ title }` is `T0012` ("template not yet available"). The derivation is field-wise, so the clone of a residual is
  well defined: clone the present fields.
- **The native `Copy` rule should become ordinary.** In v0.16.0 the rule that makes a named `Copy` type and its
  residuals `Copy` is compiler logic (metel-core#1823). The std row template of RFC-0209 replaces it with no change
  in accepted programs.
- **Dispatch and bounds must agree.** RFC-0211 resolves metel-core#1788 by rejecting; the template gives the
  derived case a defined meaning.

---

## 1. The rule

**Legality.**
1. A residual `T.{ fields }` of a nominal type `T` satisfies aspect `A` through a **row template** exactly when
   `T`'s header grants `A` (RFC-0207, RFC-0209), the template's `where` bound holds over the residual's present
   fields, and rule 4 holds.
2. `Self` in a template denotes the matched type, here the residual. A template method that returns `Self` returns
   the residual.
3. A residual of a type whose header grants nothing satisfies nothing for marker and derivable aspects, as the brand
   does (RFC-0211 rule 4).
4. **Super-aspects are rechecked on the residual.** A residual satisfies `A` only if every positive super-aspect of
   `A` (RFC-0213) also holds for the residual, through its own row template or through a written impl for that
   residual shape once the language can express one (RFC-0214). An entailment `T: A` implies `T: B` is never assumed
   across the residual boundary.

**Marker aspects.** `Copy` follows rules 1 and 4: `Point.{ x }` is `Copy` if `Point` grants `Copy` and `x` is `Copy`,
whether or not `y` is, and it has the `Clone` that `Copy` brings. **The stored interface must be row-sensitive**: for
`copy struct W<T> { n: i64, value: T }`, the projection `W<String>.{ n }` is `Copy` although `W<String>` is not, so
the condition of a residual is evaluated over the present fields and not as the whole-type condition. The template must
keep this when it replaces the native rule (metel-core#1823, #1818).

**Dynamic semantics.** The template runs over the present fields only. No absent field is read, so the result is
well defined at every width.

---

## 2. Worked examples

1. **A derived clone of a residual.** `Doc derives Clone`, `q := d.{ title }`: `q.clone()` is `Doc.{ title }`, built
   from the present field.
2. **Replacing a derivation by a written impl.** `derives Clone` to a hand-written `Clone` keeps whole-type behaviour
   and drops `Clone` from `Doc.{ title }` (RFC-0211 rule 2). A row-generic written impl (RFC-0214) is the remedy.
3. **A residual of a generic type.** `copy struct W<T> { n: i64, value: T }`, `w: W<String>`, `w.{ n }` is `Copy`.

---

## 3. Alternatives considered

1. **No templates; residuals satisfy only `Copy` and `Drop` (RFC-0211, the v0.16.0 rule).** Simple, and enough for the
   settlement. It leaves a derived `Clone` unusable on projections.
2. **Derive a required field set from each hand-written impl's body.** Declined by RFC-0137 section 5.
3. **Declared narrowed receivers** (RFC-0109, RFC-0146, RFC-0147): the route for written impls (RFC-0214), outside
   this RFC.

---

## 4. Costs

- **Replacing a derivation by a written impl removes the aspect from projections.** That is a capability change
  caused by implementation provenance, not by behaviour; the language keeps no edit history, so the use site carries
  the diagnostic.
- **Dependence on RFC-0209** for the template and on RFC-0207 for the header entry.

---

## Relationship to existing RFCs

- **RFC-0211** — the v0.16.0 rule this RFC extends.
- **RFC-0137** — residuals and the `Drop` dispatch.
- **RFC-0209, RFC-0210** — per-aspect row visibility and enum parameters; the template machinery.
- **RFC-0214, RFC-0216** — written residual impls and construction (drafts).
- **RFC-0206, RFC-0213** — `Copy`, `Clone` and the super-aspects rechecked by rule 4.

## Open questions

1. **Whether a user derivable aspect with a template** (RFC-0209 open question 5) gets the same residual behaviour;
   presumably yes.
2. **Residuals of generic types** and of types with row parameters: whether the template's condition is evaluated
   before or after narrowing.
3. **`Send`, `Sync`, `Linear`** (RFC-0096, auto aspects): they follow the present fields, but the rule has not been
   checked against RFC-0096's text.
4. **Empty residuals** (`Handle.{}`): whether every template is satisfied vacuously, and whether a derived `Clone` of
   an empty residual is useful or a hazard.
5. **Named views** (RFC-0109): whether a view declares its own header entries.
6. **A residual of a `Drop` type**: whether a derived `Clone` on it needs a warning about duplicating the resource
   whose destructor the residual keeps (RFC-0137 section 5).

---

## Decision

**Outcome:** *(pending)*
