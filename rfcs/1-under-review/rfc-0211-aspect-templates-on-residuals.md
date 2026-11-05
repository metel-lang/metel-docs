---
id: rfc-0211
title: "Aspect Templates on Residuals"
date: '2026-11-02'
status: under-review
updated: '2026-11-03'
tracking: 'https://github.com/metel-lang/metel-core/issues/1792'
---

> **Note, 2026-11-03.** The `Copy`/`Clone` settlement was redesigned: RFC-0206 is now "Clone and
> ImplicitClone", and RFC-0207 is reduced to the `derives` clause and the colon list. The `header` and
> `derivable` modifiers, `provides` and the `derives Copy` spelling that this draft cites are not part
> of that design. What remains relevant here is the derivation of `Clone` by a row template;
> examples that used `Copy` were rewritten on 2026-11-04 to `derives ImplicitClone`.

> **Status — under review (2026-11-03).** review of residual templates

## Summary

A value narrowed by a partial move or a projection has a **residual** type, `Doc.{ title }`: the
same brand with fewer fields (RFC-0137). The language does not say which aspects a residual
satisfies, and the implementation answers inconsistently. This RFC sets the rule:

> A **granted aspect's row template** (RFC-0209) applies to every residual of the granted brand,
> with the template's `where` bound evaluated over the residual's **present** fields. A
> **hand-written** impl applies to the full type only.

```metel
struct Doc derives Clone { title: String, n: i64 }   // derives entry: the Clone template applies
struct Point derives ImplicitClone { x: i64, y: i64 }

let q := d.{ title };        // q : Doc.{ title }
q.clone()                     // Doc.{ title }: the template clones the present field
let p2 := p.{ x };            // p2 : Point.{ x }, ImplicitClone because x is (rules 1 and 6)
```

A hand-written `extend Doc: Clone { … }` does not apply to `Doc.{ title }`; its body may read any
field.

---

## Motivation

Measured against the current build (2026-11-02):

- **Methods do not apply to a residual.** After `let n := h.name;`, a method of `Handle` called on
  `h` gives `T0002: cannot infer receiver type`. The narrowed-`self` form of RFC-0109
  (`&Self.{ fd }`) does not parse yet.
- **Bounds look through the brand.** `Point.{ x }` of a `Copy` struct satisfies `T: Copy` today and can
  be used twice under `--move-check`; `Doc.{ title }` satisfies `T: Clone` when `Doc` has a user
  impl.
- **Dispatch does not follow the bound.** Through `fun dup<T: Clone>(t: &T) -> T { t.clone() }`,
  a full `Doc` runs the user's `clone`, and the residual `Doc.{ title }` returns a value without
  running it (metel-core#1788). A user `Clone` that encodes an invariant is bypassed.

So bound satisfaction treats a residual as its brand, while dispatch does not. One of the two must
change, and the rule has to say which aspects survive narrowing. RFC-0137 §4 states that passing a
residual is ordinary type matching and that a plain struct's residual never satisfies a row bound;
it does not say what a residual satisfies for aspects.

The question matters for the Copy/Clone settlement (RFC-0162, RFC-0206, RFC-0207, RFC-0209): a
header entry derives behaviour from the type's row, and a residual is that row narrowed.

---

## 1. The rule

**Legality.**
1. A residual `T.{ fields }` of a nominal type `T` satisfies aspect `A` through a **row template**
   exactly when `T`'s header grants `A` (RFC-0207, RFC-0209), the template's `where` bound holds
   over the residual's present fields, and rule 6 holds.
2. A residual does **not** satisfy `A` through a hand-written impl of `A` for `T` (an
   `extend T: A { … }`), because the body may read a field the residual no longer has. A bound
   `T: A` on a residual is satisfied only through rule 1; otherwise it is `T0012`.
3. `Self` in a template denotes the matched type, here the residual. A template method that returns
   `Self` returns the residual.
4. A residual of a type whose header grants nothing satisfies nothing for marker and derivable aspects, as the
   brand does.
5. A residual is a value of the same brand, so the brand's `Drop` rule is unchanged: a destructor
   is dispatched by the row-bounded rule of RFC-0137 §5 and is outside this RFC.
6. **Super-aspects are rechecked on the residual.** A residual satisfies `A` only if every positive
   super-aspect of `A` (RFC-0213) also holds for the residual, by these same rules: through its own
   row template, or through a written impl for that residual shape once the language can express one
   (RFC-0214, not a dependency of this RFC). An entailment `T: A` implies `T: B` is never assumed
   across the residual boundary. A residual whose `A` template holds but whose super-aspect does not
   does not satisfy `A`.

**Marker aspects.** `ImplicitClone` follows rules 1 and 6: `Point.{ x }` is `ImplicitClone` if
`Point` grants `ImplicitClone`, `x` is `ImplicitClone`, and the residual is `Clone` (its super-aspect).
It is `ImplicitClone` whether or not `y` is. A residual of a type that cannot grant `ImplicitClone`
(a field is not) never is, even if the remaining fields are: the header says so, not the shape. A
residual of a type whose `Clone` is written has no `Clone` template, so it is neither `Clone` nor
`ImplicitClone`, and is moved, even though the type's header grants `ImplicitClone`.

**Dynamic semantics.** The template runs over the present fields only. No field that is absent is
read, so the result is well defined at every width.

---

## 2. Worked examples

1. **A derived clone of a residual.** `Doc derives Clone`, `q := d.{ title }`: `q.clone()` is
   `Doc.{ title }`, built from the present field.
2. **A written clone.** `extend Doc: Clone { fun clone(&self) -> Doc { … self.n … } }`: the
   residual does not satisfy `Clone`. The program of metel-core#1788 is `T0012` at the call.
3. **A written clone and the marker.** `struct Cache: ImplicitClone { data: i64, hits: i64 }` with a
   written `clone` that resets `hits`: `cache.{ data }` is not `Clone` (rule 2) and therefore not
   `ImplicitClone` (rule 6), so `let a := p; let b := p;` on the projection is a use after move. The
   same type declared `derives ImplicitClone` has both templates, and the projection copies.
4. **Copy of a projection.** `struct Point derives ImplicitClone { x: i64, y: i64, }`, `p.{ x }` used
   twice: accepted, by rules 1 and 6 through the two templates, and not by looking through the brand.
5. **A non-grantable brand.** `struct H { fd: i64, name: String }` cannot grant `ImplicitClone`;
   `H.{ fd }` is not `ImplicitClone` although `fd` is. A copyable projection of it needs a separate type.
6. **Widening.** A cloned residual is widened by restoring the missing fields (RFC-0137 §6). That restores
   the width and does not validate the relation between the restored and the retained fields: RFC-0137
   §6 documents an existing constructor-invariant bypass, which a derived clone neither adds nor repairs.

---

## 3. Alternatives considered

1. **Residuals satisfy nothing.** Declined: it breaks implicitly copied projections, which work today and are
   what `p.{ x }` is for, and it needs a separate story for generic code that passes residuals.
2. **Residuals satisfy whatever the brand does** (today's bounds) and dispatch calls the brand's
   impl. Declined: unsound for hand-written impls, which would read fields the residual lacks.
3. **Derive a required field set from each hand-written impl's body**, so impls apply to every
   residual that covers what the body reads. Declined by RFC-0137 §5, which removed body-derived
   sets in favour of declared ones.
4. **Declared narrowed receivers** (RFC-0109, RFC-0146, RFC-0147): a hand-written impl that states
   the residual it works on. Not an alternative but the route for written impls (drafted as RFC-0214, not a dependency of this RFC), and is outside
   this RFC.

---

## 4. Costs

- **Bound satisfaction changes for hand-written impls** on residuals: a program that passes a
  residual to `T: Clone` today (and silently skips the user's impl) becomes `T0012`. This is the
  behaviour the bug (#1788) reports, and the fix is the rule.
- **A written `Clone` removes implicit copying from projections** (rule 6): replacing a derived
  `clone` with an equivalent written one changes `cache.{ data }` from copied to moved. A type that
  wants copyable projections derives its `Clone`, or gets a residual impl from RFC-0214. A program
  that copies a projection of a `Copy` type whose `Clone` will be written needs the same change when
  it migrates to `ImplicitClone` (RFC-0206 section 5).
- **Two ways to satisfy an aspect** depending on whether it is derived or written, which the
  header entry already makes visible.
- **Dependence on RFC-0209** for the template and on RFC-0207 for the header entry.

---

## Relationship to existing RFCs

- **RFC-0137** — residuals and the `Drop` dispatch rule; this RFC fills in aspects other than `Drop`.
- **RFC-0209 / RFC-0207** — per-aspect row visibility and header entries; the template applied here.
- **RFC-0162 / RFC-0206** — `Copy` and `Clone`; RFC-0213 for the super-aspects rechecked by rule 6.
- **RFC-0109 / RFC-0146 / RFC-0147 / RFC-0148** — narrowed receivers, the route for written impls.
- **RFC-0210** — enums, which are atomic for narrowing (RFC-0150) and have no residuals.
- **metel-core#1788** — the dispatch bug this RFC's rule resolves.

## Open questions

1. **Whether a user derivable aspect with a template** (RFC-0209 Open Question 5) gets the same
   residual behaviour; presumably yes.
2. **Residuals of generic types** and of types with row parameters: whether the template's
   condition is evaluated before or after narrowing.
3. **`Send`, `Sync`, `Linear`** (RFC-0096, auto aspects): they follow the present fields, but the
   rule has not been checked against RFC-0096's text.
4. **Empty residuals** (`Handle.{}`): whether every template is satisfied vacuously, and whether a
   derived `Clone` of an empty residual is useful or a hazard.
5. **Named views** (RFC-0109): whether a view declares its own header entries.
6. **A residual of a `Drop` type**: whether a derived `Clone` on it needs a warning about
   duplicating the resource whose destructor the residual keeps (RFC-0137 §5).

---

## Decision

**Outcome:** *(pending)*
