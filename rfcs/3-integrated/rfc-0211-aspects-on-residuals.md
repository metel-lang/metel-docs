---
id: rfc-0211
title: "Aspects on Residuals"
date: '2026-11-02'
status: integrated
updated: '2026-11-13'
tracking: 'https://github.com/metel-lang/metel-core/issues/1792'
coverage:
  "1": { kind: blocked, reason: "Implementation of the aspects-on-a-residual rules is metel-core#1830; the rules are in reference/spec/ownership.md (aspects-on-a-residual legality 1 to 7, dynamics 1) and carry no fixtures until then.", ref: "metel-core#1830" }
  "2": { kind: untestable, reason: "The worked examples are fixtures citing the aspects-on-a-residual rules." }
  "3": { kind: untestable, reason: "Section 3 records rejected alternatives; it adds no rule." }
  "4": { kind: untestable, reason: "Section 4 states costs; it adds no rule." }
impl_tracking: 'https://github.com/metel-lang/metel-core/issues/1830'
impl_status: not-started
---

> **Status — accepted (2026-11-05).** Ratified in the Copy and Clone settlement sweep (metel-core#1824); spellings ratified by the language owner 2026-11-05.

> **Split (2026-11-06).** This RFC was accepted with a staged marker. It is split so that each RFC has one status:
> this RFC keeps the rules that apply in v0.16.0; the template half (a granted aspect's row template applying to
> every residual) is RFC-0217, under review. The title changed from "Aspect Templates on Residuals".

> **Status — integrated (2026-11-13).** Integrated into reference/spec/ownership.md (aspects-on-a-residual legality 1 to 7, dynamics 1); implementation tracked in metel-core#1830.

## Summary

A value narrowed by a partial move or a projection has a **residual** type, `Doc.{ .title }`: the same brand with
fewer fields (RFC-0137). The language did not say which aspects a residual satisfies, and the implementation answered
inconsistently. In v0.16.0 the rule is:

> A residual satisfies **structural `Copy`** (with the `Clone` that `Copy` provides) when its brand grants `Copy` and
> its present fields are `Copy`, and it keeps the existing **`Drop` dispatch** (RFC-0137 section 5). **Every other
> aspect that needs an impl is `T0012` on a residual**, whether the whole-type impl is written or derived.

```metel
copy struct Point { x: i64, y: i64 }
struct Doc derives Clone { title: String, n: i64 }

let p2 := p.{ .x };           // Point.{ .x }: Copy, because x is
let t := d.{ .title };        // the projection moves the field out
t.clone()                     // T0012: Clone has no impl for the projection (derived: template not yet available)
```

A hand-written `extend Doc: Clone { … }` does not apply to `Doc.{ .title }`; its body may read any field.

---

## Motivation

Measured against the build of 2026-11-02:

- **Methods do not apply to a residual.** After `let n := h.name;`, a method of `Handle` called on `h` gives
  `T0002: cannot infer receiver type`. The narrowed-`self` form of RFC-0109 (`&Self.{ .fd }`) does not parse yet.
- **Bounds look through the brand.** `Point.{ .x }` of a `Copy` struct satisfies `T: Copy` today and can be used twice
  under `--move-check`; `Doc.{ .title }` satisfies `T: Clone` when `Doc` has a user impl.
- **Dispatch does not follow the bound.** Through `fun dup<T: Clone>(t: &T) -> T { t.clone() }`, a full `Doc` runs
  the user's `clone`, and the residual `Doc.{ .title }` returns a value without running it (metel-core#1788). A user
  `Clone` that encodes an invariant is bypassed.

So bound satisfaction treats a residual as its brand, while dispatch does not. One of the two must change, and the
rule has to say which aspects survive narrowing. RFC-0137 section 4 says that passing a residual is ordinary type
matching and that a plain struct's residual never satisfies a row bound; it does not say what a residual satisfies for
aspects.

---

## 1. The rule (v0.16.0)

**Legality.**
1. A residual `T.{ .fields }` of a nominal type `T` is `Copy` exactly when `T`'s declaration grants `Copy` (RFC-0206,
   RFC-0207) and the residual's **present** fields are `Copy`. It then has the provided `Clone` that `Copy` brings. The
   rule is native compiler logic in v0.16.0 (metel-core#1823). It must be evaluated over the present fields: for
   `copy struct W<T> { n: i64, value: T }`, `W<String>.{ .n }` is `Copy`.
2. A residual does **not** satisfy `A` through a hand-written impl of `A` for `T` (an `extend T: A { … }`), because the
   body may read a field the residual no longer has. A bound `T: A` on a residual is `T0012` unless rule 1 or rule 5
   applies.
3. A residual does not satisfy `A` through a **derived** impl either in v0.16.0. The derivation is whole-type; the
   row template that would extend it to residuals is RFC-0217. The use-site diagnostic says "template not yet
   available" and does not name a written impl.
4. A residual of a type whose declaration grants nothing satisfies nothing for marker and derivable aspects, as the
   brand does.
5. A residual is a value of the same brand, so the brand's `Drop` rule is unchanged: a destructor is dispatched by the
   row-bounded rule of RFC-0137 section 5 and is outside this RFC. The total destructuring of a marked dismantling method (RFC-0089 section 2) suppresses the destructor and is separate from that dispatch.
6. **Compiler-computed ownership capabilities** (`Discard`, RFC-0089) are not impls: they follow the surviving fields of
   the residual. A partial move out of a nominal aggregate is legal only when the aggregate is known `Discard`
   (RFC-0089 section 2, "Consuming an aggregate that is not known `Discard`"), so a residual of a linear or possibly
   linear aggregate does not arise. A structural type (anonymous record, tuple) that holds a linear value narrows as
   usual and its leftover class is recomputed from the surviving components.

**Diagnostics.** The error is `T0012` at the use site. When a written whole-type impl exists, the note names it as the
cause; when the aspect is derived, the note says the template is not yet available. The language keeps no edit
history, so there is no warning at the edit.

**Marker aspects.** `Point.{ .x }` is `Copy` if `Point` grants `Copy` and `x` is `Copy`, whether or not `y` is. A
residual of a type that cannot grant `Copy` (a field is not) never is, even if the remaining fields are: the
declaration says so, not the shape. A type whose `Clone` is written is not `Copy` (RFC-0206 section 2), so its
projections move like the value itself.

**Dynamic semantics.** A copy of a `Copy` residual copies its present fields. No absent field is read.

---

## 2. Worked examples

1. **A written clone.** `extend Doc: Clone { fun clone(&self) -> Doc { … self.n … } }`: the residual does not satisfy
   `Clone`. The program of metel-core#1788 is `T0012` at the call.
2. **A derived clone.** `Doc derives Clone`, `t := d.{ .title }`, `t.clone()`: `T0012`, "template not yet available".
3. **A custom duplicate and `Copy` do not mix.** `struct Cache { data: i64, hits: i64 }` with a written `clone` that
   resets `hits` is not `Copy`, so `cache.{ .data }` moves; it is not `Clone` either (rule 2).
4. **Copy of a projection.** `copy struct Point { x: i64, y: i64 }`, `p.{ .x }` used twice: accepted, by rule 1.
5. **A non-grantable brand.** `struct H { fd: i64, name: String }` cannot grant `Copy`; `H.{ .fd }` is not `Copy`
   although `fd` is. A copyable projection of it needs a separate type.
6. **Widening.** A cloned residual is widened by restoring the missing fields (RFC-0137 section 6). That restores the
   width and does not validate the relation between the restored and the retained fields: RFC-0137 section 6
   documents an existing constructor-invariant bypass.

---

## 3. Alternatives considered

1. **Residuals satisfy nothing.** Declined: it breaks implicitly copied projections, which work today and are what
   `p.{ .x }` is for.
2. **Residuals satisfy whatever the brand does** (today's bounds) and dispatch calls the brand's impl. Declined:
   unsound for hand-written impls, which would read fields the residual lacks.
3. **Derive a required field set from each hand-written impl's body.** Declined by RFC-0137 section 5.
4. **Row templates in v0.16.0** (the earlier form of this RFC): split into RFC-0217, because they need the row
   machinery (RFC-0209, RFC-0210) that the settlement does not otherwise require.
5. **Declared narrowed receivers** (RFC-0109, RFC-0146, RFC-0147): the route for written impls (RFC-0214), outside
   this RFC.

---

## 4. Costs

- **Bound satisfaction changes for hand-written impls** on residuals: a program that passes a residual to `T: Clone`
  today (and silently skips the user's impl) becomes `T0012`. This is the behaviour the bug (#1788) reports.
- **A derived aspect is unavailable on projections** until RFC-0217 lands (`T0012`, "template not yet available").
- **Replacing a derivation by a written impl** does not change a projection's status in v0.16.0: both are `T0012`.

---

## Relationship to existing RFCs

- **RFC-0137** — residuals and the `Drop` dispatch rule; this RFC fills in aspects other than `Drop`.
- **RFC-0217** — the end state (row templates on residuals); **RFC-0209, RFC-0210** — the row machinery it needs.
- **RFC-0206, RFC-0207, RFC-0213** — `Copy`, `Clone`, the clauses, and the super-aspects.
- **RFC-0089** — `Discard` and `Linear`, which follow the surviving fields.
- **RFC-0109 / RFC-0146 / RFC-0147 / RFC-0148** — narrowed receivers, the route for written impls (RFC-0214).
- **metel-core#1788** — the dispatch bug this RFC's rule resolves.

## Open questions

1. **Empty residuals** (`Handle.{}`): whether `Copy` holds vacuously for a granted brand.
2. Open questions about templates moved to RFC-0217.

---

## Decision

**Outcome:** *(pending)*
