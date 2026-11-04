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
> examples below that use `Copy` read as `ImplicitClone` in the colon list.

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
struct Point: Copy { x: i64, y: i64 }

let q := d.{ title };        // q : Doc.{ title }
q.clone()                     // Doc.{ title }: the template clones the present field
let p2 := p.{ x };            // p2 : Point.{ x }, Copy because x is
```

A hand-written `extend Doc: Clone { … }` does not apply to `Doc.{ title }`; its body may read any
field.

---

## Motivation

Measured against the current build (2026-11-02):

- **Methods do not apply to a residual.** After `let n := h.name;`, a method of `Handle` called on
  `h` gives `T0002: cannot infer receiver type`. The narrowed-`self` form of RFC-0109
  (`&Self.{ fd }`) does not parse yet.
- **Bounds look through the brand.** `Point.{ x }` of a `Copy` struct satisfies `T: Copy` and can
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
   exactly when `T`'s header grants `A` (RFC-0207, RFC-0209) and the template's `where` bound holds
   over the residual's present fields.
2. A residual does **not** satisfy `A` through a hand-written impl of `A` for `T` (an
   `extend T: A { … }`), because the body may read a field the residual no longer has. A bound
   `T: A` on a residual is satisfied only through rule 1; otherwise it is `T0012`.
3. `Self` in a template denotes the matched type, here the residual. A template method that returns
   `Self` returns the residual.
4. A residual of a type whose header grants nothing satisfies nothing for marker and derivable aspects, as the
   brand does.
5. A residual is a value of the same brand, so the brand's `Drop` rule is unchanged: a destructor
   is dispatched by the row-bounded rule of RFC-0137 §5 and is outside this RFC.

**Marker aspects.** `Copy` follows rule 1: `Point.{ x }` is `Copy` if `Point` grants `Copy` and `x`
is `Copy`; it is `Copy` whether or not `y` is. A residual of a type that cannot grant `Copy`
(a field is not `Copy`) never is, even if the remaining fields are `Copy`: the header says so, not
the shape.

**Dynamic semantics.** The template runs over the present fields only. No field that is absent is
read, so the result is well defined at every width.

---

## 2. Worked examples

1. **A derived clone of a residual.** `Doc derives Clone`, `q := d.{ title }`: `q.clone()` is
   `Doc.{ title }`, built from the present field.
2. **A written clone.** `extend Doc: Clone { fun clone(&self) -> Doc { … self.n … } }`: the
   residual does not satisfy `Clone`. The program of metel-core#1788 is `T0012` at the call.
3. **Copy of a projection.** `Point: Copy` (a marker entry), `p.{ x }` used twice: accepted, as today, now by
   rule 1 and not by looking through the brand.
4. **A non-grantable brand.** `struct H { fd: i64, name: String }` cannot grant `Copy`;
   `H.{ fd }` is not `Copy` although `fd` is. A `Copy` projection of it needs a separate type.
5. **Widening.** A cloned residual is widened by restoring the missing fields (RFC-0137 §6), so
   a derived clone does not provide a way around a constructor invariant.

---

## 3. Alternatives considered

1. **Residuals satisfy nothing.** Declined: it breaks `Copy` projections, which work today and are
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
- **Two ways to satisfy an aspect** depending on whether it is derived or written, which the
  header entry already makes visible.
- **Dependence on RFC-0209** for the template and on RFC-0207 for the header entry.

---

## Relationship to existing RFCs

- **RFC-0137** — residuals and the `Drop` dispatch rule; this RFC fills in aspects other than `Drop`.
- **RFC-0209 / RFC-0207** — per-aspect row visibility and header entries; the template applied here.
- **RFC-0162 / RFC-0206** — `Copy` and `Clone`.
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
