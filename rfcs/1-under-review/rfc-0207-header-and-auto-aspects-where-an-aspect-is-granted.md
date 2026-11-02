---
id: rfc-0207
title: "Header and Auto Aspects — Where an Aspect Is Granted"
date: '2026-11-02'
status: under-review
updated: '2026-11-02'
tracking: 'https://github.com/metel-lang/metel-core/issues/1786'
---

> **Extracted from RFC-0162 on 2026-11-02**, at the language owner's request, the way RFC-0206
> was extracted from RFC-0080. RFC-0162 keeps the `Copy`/`Clone` model and its position that a
> named type states copyness in its declaration; this RFC owns the *mechanism* that position
> uses, which is not specific to `Copy`: a type's header listing marker facts, an `extend`
> that may only refine such a grant, and aspects that declare how they are granted. Nothing here
> is decided.

> **Status — under review (2026-11-02).**

## Summary

An aspect is today granted one way, by an `extend` block anywhere in the type's module. This RFC
proposes two further positions and a way to state which an aspect uses:

1. **Header aspects.** A type declaration lists marker aspects after its name
   (`struct Point: Copy { … }`, `struct Token: Copy, !Send { … }`). For an aspect with no
   required methods a positive item is the grant itself and a negative item (`!Send`) denies it.
   An `extend` of the same aspect is legal only to refine a header grant, for a target with no
   header, or as a negative impl.
2. **Auto aspects.** An aspect granted structurally with no grant at all (`Send`, `Sync`,
   `Linear`, RFC-0096), which a type opts out of in its header (`!Send`).
3. **Grant modes.** Each aspect declares which it is: `extend` (the default, as today), `header`
   or `auto`. The compiler enforces the mode, and a grant in the wrong position is an error with
   a fix-it.

RFC-0162 uses a `header` aspect for `Copy` (its position C4); RFC-0206 uses the same header
for a derived `Clone` (its §4, option (c)). Neither is decided, and both depend on this RFC
being accepted before the header spelling is implemented.

## Motivation

RFC-0162 (D6) argues that `Copy` is a grant whose effect, a change in what every use of the
type means, is out of proportion to where it is written: a bodyless `extend T: Copy;`
anywhere in the module. Its answer is to move the grant onto the declaration. Working that out
produced a mechanism that is not about `Copy`: it needs a rule for which aspects may be named
in a header, for what an `extend` of such an aspect may still do, and for how an aspect says
where it is granted, and it overlaps RFC-0096 (auto-impl aspects), RFC-0102 (bodyless
`extend`) and RFC-0105 (aspect lists in declarations). Settling those inside a `Copy`/`Clone`
model RFC buried them, and gave `Clone`, `!Send` and any future marker no home. They get one
here.

---

## Header aspects (from RFC-0162 C4)

> Added 2026-11-02 at the language owner's request, as a competitor to C2. It is the shape
> the draft RFC-0105 (`struct Token: Copy2, Serializable, !Send { … }`) proposed for aspect
> lists in general, restricted to the case `Copy` needs.

**The idea.** A type declaration may list marker aspects after its name. For an aspect that
declares no required methods, `Copy` among them, a positive item is a grant, the same fact a
bodyless `extend T: Copy;` states today. A negative item (`!Send`) denies, exactly as a
bodyless negative `extend` does (RFC-0102, RFC-0081). Aspects with methods (`Drop`,
`Display`, a user's own) are still implemented in `extend`; naming one in the header would
be RFC-0105's obligation model, which this proposal does not take.

**What it changes against C2.**

- **The stop rule (D6.3) has a principled answer.** C2 moves `Copy` to a keyword and leaves
  `Drop`, `Send` and `Sync` as aspects, and has to say why. C4's boundary is a class: *marker
  facts about a type are declared on the type; behaviour is implemented in `extend`*. `Copy`
  is a marker; `Drop` is not (it has a method); `Send`/`Sync`/`Linear` are markers, and RFC-0096
  already treats them as structural, with `!Send` the opt-out. No aspect is special-cased.
- **`Copy` stays an aspect and a bound.** Nothing about `T: Copy`, `Copy ⇒ Clone`, the
  conditional rules or coherence changes. The grant's location moves, as in C2.
- **The derive hazard is not closed by the mechanism.** C2 has no impl to emit; C4 has a
  header entry a deriver could add. In practice `#derive(Copy)` would be no shorter than
  `: Copy`, so it would add nothing, and RFC-0162's question 5, the written rule ("`Copy` has no deriver")
  covers it. This is closed by policy and not by construction, which is a real difference.
- **Visibility.** `copy struct P` puts a modifier before the keyword; `struct P: Copy` puts
  the fact after the name, before any generics' `where`. Both are in the header. A modifier is
  harder to miss; a list scales to several facts (`: Copy, !Send`) where a keyword does not.
- **Conditional grants.** The derived condition (RFC-0162's R1) is a rule of `Copy`'s eligibility
  check (every field must be `Copy`), not of marker aspects in general: for a plain user
  marker `struct W<T>: Marker`, there is no field-wise rule to derive from. So under C4 the
  derived-condition rule would belong to a named class, the aspects with a structural
  eligibility rule (`Copy`, and RFC-0096's `Send`/`Sync`/`Linear`), and any other marker
  grant is unconditional or keeps `extend<T: X> W<T>: Marker;`.
- **Vocabulary.** Axis S spells copyness on structural types as a qualifier (`copy`,
  `once`); C4 spells it on named types as an aspect (`: Copy`). Two forms of one fact. C2
  has one word throughout.
- **Cost and dependency.** It adds a clause to type-declaration grammar, and depends on
  RFC-0105 (a `0-draft` that was deferred as "a materially larger surface-language
  commitment") being narrowed to markers and moved forward, or on this RFC absorbing the
  marker-only subset. The obligation check and the registry-injection question RFC-0105 raises do
  not arise for markers, because there is no `extend` to find.

**Spelling and direction (language owner, 2026-11-02).** `: Copy` is the header's
spelling because it mirrors the `extend T: Copy` block it replaces. The expected direction is
that header aspects later accept aspects with methods too, which would make a header behave
nearly identically to an `extend` block; this RFC proposes only the marker case, which needs
no obligation check. That direction is why the single-place rule for `Copy` should rest on the
aspect's grant mode (C5) and not on markers being the only aspects a header can name.

**Refinable header grants (added 2026-11-02).** A pure header list cannot express a
condition the compiler cannot derive, and gives std's own grants (primitives, the record
rule) no place to live. The restriction can be relaxed without losing its invariant, which
is: **a type is `Copy`-capable only if its header says so.** An `extend` of the aspect is
legal in exactly three situations and an error otherwise (with a fix-it):

1. *It refines a header grant.* The header already names the aspect (`struct W<T>: Copy`),
   and the `extend` supplies the condition: `extend<T: Marker> W<T>: Copy;`. Without an
   `extend`, the condition is derived from the fields (R1, decided 2026-11-02: every type parameter that occurs
   in a field must be `Copy`; R2, the weakest sufficient condition, needs a solver and is not
   taken; where R1 is too strict, as for `struct W<T> { r: &T }`, this `extend` widens it). With one, the `extend` wins, and must still satisfy the aspect's
   eligibility check, exactly as `check_copy_impl_eligibility` does today.
2. *The target has no header.* std's `extend i64: Copy;` and
   `extend<record R> { ..R }: Copy where ..R: Copy;` have structural or builtin targets;
   no exemption needs inventing.
3. *It is a negative impl.* `extend<T> W<T>: !Copy where T: Marker;` denies and grants
   nothing.

An `extend T: Copy;` for a type whose header does not name `Copy` is rejected, so neither a
deriver nor a distant `extend` can make a type `Copy` silently. This is RFC-0105's obligation
model, header as promise and `extend` as detail, applied to markers only. The check is
module-local, not whole-graph: `Copy` is a std aspect, so the orphan rule (`T0014`) already
puts the grant in the type's own module, which is where the header is. The cost is that a
conditional type can have two places, the header and an optional refining `extend`, and that
a deriver may emit the refining `extend`, though only for a type whose header already names
`Copy`. In C5's terms this is a `header` aspect that is *refinable*.

**Structural types under C4.** A header list has no site on a tuple or an anonymous record.
Axis S proposes S6 for them, a marker on the written type, which uses the same items as the
header.

**Worked examples** (reasoned; C1 is today's `extend`, C2 is the `copy` keyword alternative kept in RFC-0162):

1. *Adding a field* (`name: String` to a `Copy` struct): C1 errors at the `extend` line, C2
   and C4 at the declaration, next to the field.
2. *Reading the declaration:* C2 `copy struct P`, C4 `struct P: Copy`; both visible. C4 also
   shows `struct P: Copy, !Send` in one place.
3. *Conditional grant, `Holder<T>`, phantom `Witness<T>`:* both derive the condition from the
   fields, C2 by the keyword and C4 by `Copy`'s eligibility rule.
4. *A user marker* (`aspect Marker {}`; `struct Token: Marker`): C2 does not apply; C4 grants
   it, unconditionally, with no `extend`.
5. *`Drop`:* `struct H: Copy` with `extend H: Drop { … }` is rejected at the declaration under
   both, with the same message as C2's.
6. *A derive:* closed by construction under C2, by the written rule under C4, and by the
   header requirement for the refining `extend` (above).
7. *A condition on another aspect* (`extend<T: Marker> Witness<T>: Copy`, used by a
   coherence fixture): inexpressible under C2 and under a pure header list; under refinable
   header grants it is `struct Witness<T>: Copy { … }` plus that `extend`.
8. *std's own grants:* `extend i64: Copy;` and the record rule stay as `extend`, by case 2,
   with no exemption to invent.

**What would decide it.** If the only grant ever moved is `Copy`, C2 is smaller and closes
the derive hazard by construction. If the language wants one place for all marker facts
(including `!Send`, and any future marker), C4 generalises and answers D6.3 without an
exception, at the price of a larger grammar change, an RFC-0105 dependency and two forms of
copyness across named and structural types.

---

## Grant modes (from RFC-0162 C5)

> Added 2026-11-02 at the language owner's request, as the question "could the language
> enforce the position in which an aspect is granted?". It is a way to decide C2 against C4
> once and for the other aspects too, and it would be a design of its own (see below).

**The idea.** An aspect declares a *grant mode*, and the coherence pass (RFC-0060) enforces
it; a grant in the wrong position is an error with a fix-it.

| Mode | The aspect is granted | Examples |
|---|---|---|
| `extend` (the default) | by `extend T: A { … }`, as today | `Drop`, `Display`, any aspect with methods |
| `header` | only in the type's declaration; an `extend` of it is an error | `Copy` |
| `auto` | structurally, with no grant; a type opts out in its header (`!A`) | `Send`, `Sync`, `Linear` (RFC-0096) |

A `header` aspect has no methods (it is a marker) and may declare a structural eligibility
rule, "every field must implement it", which is today's `check_copy_impl_eligibility` for
`Copy`. The derived condition of a generic grant (R1) is then a property of the aspect, not
a special case of `Copy`: it is derived for exactly the aspects that declare the field-wise
rule. The sketch is `header aspect Copy;` and `auto aspect Send;`; the spelling is open.

**What it settles**

- **The stop rule (D6.3).** There is nothing to argue about why only `Copy` moved: the
  aspect states how it is granted, and `Drop` says `extend` because it has a method.
- **C2 against C4.** The mandatory location is the mode; the modifier (`copy struct`) or the
  list (`struct P: Copy`) is only how a `header` grant is written, and can be chosen on
  readability.
- **The derive hazard.** If a `header` aspect has no `extend` form, a deriver has no impl to
  emit, which is C2's closure by construction with C4's uniformity.
- **Where a grant may live.** A header grant is in the type's own module, so the orphan rule
  (`T0014`) holds trivially; the foreign-type case stays rejected.

**Worked examples**

1. *`extend Point: Copy;`* under C5: error, "`Copy` is granted in the type's declaration";
   the fix-it moves it into the header, in whichever spelling C2/C4 settled on.
2. *`struct H: Drop`* (a method aspect named in a header): error, "`Drop` has methods and
   is granted with `extend`". The same mechanism says why, in both directions.
3. *`struct Token: !Send`* on an `auto` aspect: the opt-out, as RFC-0105 first proposed,
   with `Send` otherwise holding because every field is `Send`.
4. *A user marker* (`aspect Marker {}`): `extend` by default, so unchanged; declaring it
   `header` is a choice open to std only at first.
5. *Std's primitives and the record rule:* granted where std declares them; the mode of
   `Copy` applies to declarations, and a builtin or structural type has none, so std's own
   `extend i64: Copy;` and `extend<record R> { ..R }: Copy where ..R: Copy;` stay as
   std-internal grants (RFC-0162's question 7).

**Costs and risks**

- A new concept in the aspect system, and a property of each aspect that readers have to
  learn. Keeping `header` and `auto` std-only at first leaves user aspects exactly as today.
- RFC-0096's compiler-recognized auto-impl set would become declared properties, which
  changes an under-review RFC; RFC-0105 would be narrowed to the marker case or absorbed.
- A user-declared `auto` aspect would let users make a property hold implicitly, which is
  the invisible behaviour D1 and the language owner's first concern object to. Hence
  std-only.
- It is a design of its own, large enough for its own RFC (aspect grant modes), which this
  RFC would depend on. This section records the idea and what it would decide.

**What would decide it.** C5 is worth its weight if more than `Copy` benefits from an
enforced grant position (`Send`/`Sync`/`Linear`, any future marker) or if the stop rule
cannot otherwise be stated. If `Copy` is the only aspect that ever needs it, C2 is the
smaller change.

---

## Relationship to existing RFCs

- **RFC-0162** — the `Copy`/`Clone` model; its position C4 is a `header` aspect in this RFC's
  terms, and its alternative C2 (`copy struct`) is a spelling of the same grant mode.
- **RFC-0206** — `Clone`; its §4(c) derives a `Clone` body from a header entry.
- **RFC-0105** — the draft this narrows: aspect lists in declarations, taken here for markers
  only, with no obligation check.
- **RFC-0096** — the auto-impl set (`Send`, `Sync`, `Linear`) that `auto` mode would turn into
  a declared property.
- **RFC-0102 / RFC-0081** — bodyless and negative `extend`, which remain the form of a
  refinement and of std's own grants.
- **RFC-0060** — the coherence pass that would enforce modes; **RFC-0097** — the orphan rule
  the header grant satisfies trivially.

## Open questions

1. **Spelling of a mode**: `header aspect Copy;` and `auto aspect Send;` are sketches.
2. **Std only or user aspects too.** The proposal keeps `header` and `auto` std-only at first,
   so user aspects stay exactly as today. When a user marker may be declared `header` is open.
3. **Methods in a header.** The expected direction is that header aspects later accept
   aspects with methods, so a header behaves almost like an `extend` block. This RFC proposes
   the marker case only; what the obligation model would add is RFC-0105's question.
4. **Whether `auto` is wanted at all** for anything beyond RFC-0096's existing set, given the
   invisible-behaviour objection above.
5. **Process.** RFC-0105 is narrowed or absorbed, and RFC-0096's recognized-set text is
   updated; decided when this RFC is reviewed.

---

## Decision

**Outcome:** *(pending)*
