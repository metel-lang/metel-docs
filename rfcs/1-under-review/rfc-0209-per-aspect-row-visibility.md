---
id: rfc-0209
title: "Per-Aspect Row Visibility"
date: '2026-11-02'
status: under-review
updated: '2026-11-04'
tracking: 'https://github.com/metel-lang/metel-core/issues/1790'
---

> **Note, 2026-11-05.** The `Copy`/`Clone` settlement was redesigned (RFC-0206): `Copy` is a sealed implicit
> copy granted by `derives Copy` or the `copy` keyword, and the `Clone` it brings is provided and cannot be
> written. The `header` and `derivable` modifiers and `provides` that this draft cited are not part of that
> design. What remains relevant here is the derivation of `Clone` and the structural `Copy` rule by a row template;
> examples below that use `Copy` read as `copy struct`. The operative text below
> was updated on 2026-11-04 to the settled rules: exact per-instantiation conditions (RFC-0206 rule 3), a
> written impl that overlaps a template is `T0015` (RFC-0207 rule 4), and no refining `extend`.

> **Status — under review (2026-11-04).** Tracker milestoned; reviewed as part of the Copy/Clone settlement (RFC-0206, RFC-0212)

## Summary

Today a nominal type's row is invisible to row-conditional impls: a plain `struct` never
matches an impl over `{ ..R }`, and a `record` declaration matches every such impl (RFC-0137,
RFC-0120's tiers). This RFC adds a middle position, **row visibility per aspect**: a header
entry in a type's declaration (RFC-0207) makes that type's row visible to the row-conditional
impls of that one aspect.

```metel
// std, in the aspect's module: the aspect's row template (exists today for records)
extend<record R> { ..R }: Clone where ..R: Clone { … }

struct Doc derives Clone { title: String, tags: List<String> }   // Doc's row is visible to Clone's template
struct Handle { fd: i64 }                                 // not visible to any row template
```

The derivation behind a `derives` or marker entry is then not a separate mechanism. `struct Doc derives Clone` is
`extend Doc: Clone` supplied by the aspect's existing template, applied to `Doc`'s row, and
checked field by field through the template's `where ..R: Clone`. No new parameter kind and no
derive attribute are added.

---

## Motivation

RFC-0162 and RFC-0207 give a named type an entry for `Copy` (`: Copy`) and `Clone` (`derives Clone`), and the entry
behaves like a derive: it checks the fields, supplies the body, and fixes the generic
condition. RFC-0207 asks that this fall out of the language's rules instead of being a
special case. The rule needed is how a nominal type's row reaches an aspect's template.

Measured against the current build (2026-11-02):

- An impl `extend<record R> { ..R }: Describe where ..R: Describe` applies to an anonymous
  record and to a named `record Pt`, and a plain `struct S` gets `no method describe on S`.
- An impl over the parameter itself, `extend<record R> R: Describe where ..R: Describe`, is
  rejected with `T0012`: a field-wise bound on an `extend` must name the row tail of its
  record target.

So the field-wise impls std has for records are the templates a derivation needs, and the one
missing piece is how a struct opts in to one. RFC-0137 states that a struct "never satisfies a
row bound or a row-conditional `extend`", and that is the decision to preserve: it keeps a
struct's narrowed residual and an opted-in `record` from being confusable.

---

## 1. The rule

**Legality.**
1. **Row visibility is a property of a (type, aspect) pair.** A nominal type's row is visible
   to the row-conditional impls of aspect `A` exactly when its declaration header lists `A`, after the colon for a marker aspect or after
   `derives` for a derivable one (RFC-0207), or, for a `record` declaration, as section 2 provides. Otherwise it is
   invisible, as today.
2. **A row template.** An `extend` of `A` whose target is `{ ..R }` (with `R` a row, RFC-0208, or
   a `record R` today) is a row template. A template applies to a nominal type `T` that has
   granted visibility to `A` when every field type of `T` satisfies the template's `where`
   clause on `..R`.
3. **`Self` in a template** denotes the type the template matched: the anonymous record `{ ..R }`
   for an anonymous record, and `T` for a nominal type. A template method that returns `Self`
   returns a `T`. Field access by label (`self.[label]`) needs no relabelling, so a template
   that only reads works unchanged.
4. **The nominal type stays nominal.** Visibility does not make `T` a record: it does not
   satisfy any row bound, and it matches no template of an aspect it has not granted.
5. **An entry that no template covers is an error.** `struct P: Pod` for a `declared`
   aspect with no row template and no methods is an unchecked promise (RFC-0207 rule 1); for an aspect that has a
   row template, the template must apply, and a field that fails the `where` clause is reported
   at the declaration, next to the field.

**Dynamic semantics.** The relabelling between `T` and its row is zero-cost, as in RFC-0119
(same bits, new static type).

**Generic types.** A generic nominal type is checked per instantiation: the template's `where`
clause is evaluated on the instantiated field types, so `copy struct View<T> { r: &T }`
is `Copy` for every `T` (because `&T` is) and `copy struct Wrapper<T> { v: T }`
only when `T` is. This is the exact per-instantiation condition (RFC-0162's R2), decided in RFC-0206
rule 3; the analysis of a generic body is a sound approximation of it (RFC-0206 section 2).

---

## 2. Records

A `record` declaration is visible to every row template today (RFC-0120 tier 3). Under this
RFC it is gated like a struct **for marker and derivable aspects** (RFC-0207): `record P`
satisfies Clone's template only when `record P derives Clone` is written. For plain aspects
(granted by `extend` only) nothing changes. This is the consequence of RFC-0162's decision that a named `record` takes a
header entry; it is breaking for any `record` that is `Copy` or `Clone` today and is a
mechanical migration (add the entry).

Anonymous records keep matching every template; they have no declaration to carry an entry.

---

## 3. Enums

An enum has variants, not one row. This RFC does not cover them: a header entry on an enum is
the compiler's native derivation until a variant-wise form exists (a separate RFC on enum rows).

---

## 4. Relationship to the tiers of RFC-0120 / RFC-0137

| Position | Visible to row templates | Today |
|---|---|---|
| plain `struct` / `enum`, no entry | none | none |
| `struct T: A` / `derives A` | the templates of `A` | new |
| `record` declaration, no entry | none, for marker and derivable aspects | all (changes) |
| `record T: A` | the templates of `A` | all (narrowed) |
| anonymous record | all | all |
| `to_record()` (RFC-0119) | the result is an anonymous record | unchanged |

---

## 5. Alternatives considered

1. **A brand parameter kind**, `extend<struct S, ..R> S.{ ..R }: A where ..R: A`. Declined: it
   adds a parameter kind, and RFC-0137's rule that a struct never matches a row-conditional impl
   still needs an opt-in, so the gate returns under another name.
2. **Reuse `ToRecord`/`FromRecord`** (RFC-0119): `clone = from_record(self.to_record().clone())`.
   Declined: both directions are by-value, and `clone` takes `&self`.
3. **Compiler-native derivation only.** Declined as the end state: it is the stage-1 plan, but
   user derivable aspects could never have a derivation, and each aspect would be its own special
   case.
4. **Make every struct row-visible.** Declined by RFC-0137: it would make a struct's narrowed
   residual and an opted-in record confusable.

---

## 6. Costs

- **`Self` in template bodies** needs a rule for constructing a `T` from a row (section 1,
  Legality 3). Until it is specified, std's field-wise bodies are native hooks (RFC-0206 §4).
- **Breaking for named records** that are `Copy`/`Clone` today (section 2), mechanically.
- **A second visibility axis** in the type system: per (type, aspect), not per type.

---

## Relationship to existing RFCs

- **RFC-0137 / RFC-0120** — the tiers; this RFC refines tier 1 and narrows tier 3 for marker and derivable aspects.
- **RFC-0207** — the declaration kinds (marker, derivable, auto), the colon list and the `derives` clause; this RFC gives an entry its derivation.
- **RFC-0162 / RFC-0206** — `Copy` and `Clone`; R2 falls out here.
- **RFC-0123 / RFC-0186 / RFC-0208** — the field-wise bound `..R: A` and row parameters.
- **RFC-0119** — the explicit conversions, unchanged.
- **RFC-0174** — `comptime for`, which would write the template bodies.
- **RFC-0092 / RFC-0093** — comptime and derive registration: a derivation that is not a single
  template (an aspect with methods, a condition a template cannot state) is a comptime derive run
  by the header entry. RFC-0207 records the `derives` clause; RFC-0093 the derive-registration question.

## Open questions

1. **Constructing `Self` in a template body**: a spread, a native intrinsic, or `comptime for`
   over the row (RFC-0174).
2. **Records gated or automatic** (section 2).
3. **Residuals**: whether a template applies to a narrowed residual `Doc.{ .title }`, and the
   `Drop` and move interactions (a follow-up RFC).
4. **Field privacy**: a template in the aspect's module reads fields the type's module may
   keep private (RFC-0116's rule for record fields); whether visibility overrides privacy for
   the granted aspect.
5. **Which aspects have templates.** Whether a user derivable aspect may provide one, and what
   makes a template's `where` bound the check of the entry.
6. **R1 or R2**: resolved. R2, the exact per-instantiation condition, is the rule (RFC-0206 rule 3).
7. **Coherence**: resolved. A header-visible template that overlaps a written `extend` of the same
   aspect is `T0015` (RFC-0207 rule 4, RFC-0213 section 4); there is no refining `extend` and no order
   of resolution.

---

## Decision

**Outcome:** *(pending)*
