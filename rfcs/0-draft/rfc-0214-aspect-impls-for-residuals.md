---
id: rfc-0214
title: "Aspect Impls for Residuals"
date: '2026-11-04'
status: draft
---

> **Status — draft (2026-11-04).** First draft. Nothing here is decided.

> **Not a dependency.** The `Copy`/`Clone` settlement (RFC-0206, RFC-0207, RFC-0211, RFC-0212,
> RFC-0213) does not wait for this RFC. Until it is accepted and implemented a residual satisfies an
> aspect only through a row template (RFC-0217 rule 1), a hand-written impl for the whole type never
> applies to a residual (RFC-0211 rule 2), and there is no way to write an impl for a residual. This RFC
> only adds that written route; every rule of the settlement stays true without it.

## Summary

A residual type `T.{ .fields }` (RFC-0137) is the same brand as `T` with some fields narrowed away. Today
a written aspect impl for `T` never applies to a residual, because its body may read a field the
residual no longer has, and the language has no way to write an impl whose receiver is a residual.
Only `Drop` has such a route: RFC-0137 section 5 dispatches a destructor against any residual whose row
contains the fields the `drop` receiver declares (RFC-0147, RFC-0148).

This RFC generalises that route to any aspect. An impl declares the residual it needs on its method
receivers, in the forms RFC-0147 and RFC-0146 already define, and applies to every residual that has
those fields. An impl for one exact shape is also allowed, and may build its own result.

```metel
struct Doc { title: String, n: i64, }

view DocTitle for Doc { title }                 // RFC-0109: a name for Doc.{ .title }

extend Doc: Display {                           // the whole type
    fun fmt(&self) -> String { return self.title.clone() + ": " + self.n.to_string(); }
}

extend DocTitle: Display {                      // the residual: needs only `title`
    fun fmt(&self) -> String { return self.title.clone(); }
}
```

## Motivation

1. **A residual cannot carry a written impl.** `d.{ .title }` is a value of a type with the same brand
   as `Doc`, yet an author who wrote `Doc: Clone` by hand has no way to say what cloning a projection
   means. RFC-0211 and RFC-0217 give the author two options only: derive the impl (a template then covers every
   residual) or accept that the projection has no impl. For a non-`Copy` type with a written `Clone` the
   projection simply has no `Clone` (RFC-0211 rule 2); a `Copy` type needs none, since its `Clone` is provided.
2. **A bound call on a residual silently skips the written impl today.** `dup(&d.{ .title })` with
   `T: Clone` is accepted and runs a structural copy instead of the user's `clone` (metel-core#1788).
   RFC-0211 turns that into `T0012`. A written residual impl would give it a defined meaning.
3. **`Drop` already works this way** and is the only aspect that does. The mechanism is not specific to
   destructors, and a second special case per aspect is the kind of exception the settlement avoids.
4. **Some impls are naturally partial.** A `Display` for a view, or an equality that compares only the
   key fields, reads a few fields and should apply to every wider residual.

## 1. Three forms of residual impl

**Row-bounded impl.** The impl's required field set is the union of the residual rows its method
receivers declare (RFC-0147 fixed projection, RFC-0146 `Self.R where R: { f, .. }`). A receiver that
is a bare `&self` requires the whole row. The impl applies to every residual of the brand whose present
fields include the required set, and each method body is checked against its own receiver row, exactly
as RFC-0137 section 5 checks a destructor. `R` is erased (RFC-0146 section 3): no cost beyond a fixed
residual receiver.

```metel
extend Doc: Display {
    fun fmt(&self: Self.{ .title }) -> String { return self.title.clone(); }
}
// applies to Doc, Doc.{ .title }, Doc.{ .title, .n }; not to Doc.{ .n }
```

**Exact-shape impl.** The impl target is one residual type or one named view (RFC-0109):
`extend DocTitle: A .{ .. }` or `extend Doc.{ .title }: A .{ .. }`. It applies to exactly that shape and
`Self` is that shape. It is the form for a method that returns `Self`, because a row-bounded impl cannot
build a value of an unknown width.

```metel
extend DocTitle: Clone {
    fun clone(&self) -> Self { return /* a DocTitle built from self.title.clone() */; }
}
```

**Row-generic impl.** The impl is generic over the whole row of the brand through a row binder
(RFC-0208), with a field-wise bound (RFC-0123) and a body that walks the row (RFC-0174). It applies to
the whole type and to every residual whose present fields all satisfy the bound. It is the written
counterpart of a derivation: the compiler's row template (RFC-0209, RFC-0217) is this impl, generated.

```metel
extend Doc: Display<record R> where ..R: Display {      // spelling provisional (RFC-0208: `extend<..R>`)
    fun fmt(&self: Self.{ ..R }) -> String {
        var out := "";
        comptime for field in fields(R) {
            out = out + field.name + " = " + self.[field.name].fmt() + ", ";
        }
        return out;
    }
}

extend Doc: Clone<record R> where ..R: Clone {          // a Self-returning method, written once
    fun clone(&self: Self.{ ..R }) -> Self.{ ..R } {
        return Self.{ ..R } { comptime for field in fields(R) {
            [field.name] = self.[field.name].clone(),
        } };                                            // construction: RFC-0216
    }
}
```

It subsumes the other two forms for aspects that read or rebuild every field. Customising one field (reset `hits`
on clone) is not expressible in the loop above: a symbolic field with only `Clone` has no known type, so a branch
on `field.name` cannot return an integer. It needs either a compile-time refinement rule (a `comptime if` on
`field.name` that refines `field.type` in that branch, open question 9) or per-field customisation of a derive
(RFC-0213 open question 8). It is checked once against a symbolic field
(RFC-0174 D3). Its cost is the heaviest: it needs RFC-0174, RFC-0208, RFC-0123 and, for a `Self`-returning
method, RFC-0216. `derives` stays the normal path; this is the power-user form.

**Self-returning methods.** In a row-bounded impl `Self` is the matched residual, of unknown width. A
method that returns `Self` or takes it by value cannot construct the missing fields, so it is an error
in a row-bounded impl unless the missing fields are handled by a template (`where ..R: A`, RFC-0123,
RFC-0209). `Clone` therefore needs the exact-shape form, the template, or the row-generic form with
residual construction (RFC-0216). Methods that only read
(`fmt`, `eq(&self, other: &Self)` over the required fields) are fine.

## 2. Rules

**Legality.**
1. A residual impl may be written only in the module that defines the brand. The residual is the
   brand's own, so the orphan rule (`T0014`) holds trivially and a foreign type's residual cannot be
   given an impl.
2. A residual impl applies to a residual by its static type: an exact-shape impl to exactly that
   shape, a row-bounded impl to every residual whose present fields include its required set. A
   whole-type impl never applies to a residual (RFC-0211 rule 2).
3. **Overlap is an error.** Two residual impls of the same aspect for one residual (two exact shapes
   that are equal, a row-bounded impl whose required set the shape contains and an exact-shape impl for
   it, two row-bounded impls whose required sets are both contained) overlap and are `T0015`. There is
   no most-specific rule.
4. **Templates.** If the type's header grants the aspect, the row template (RFC-0209, RFC-0217)
   already covers every residual, and a residual impl of the same aspect, including a row-generic one
   (which covers the whole type too, so a separate whole-type impl overlaps it), overlaps it (`T0015`), as a
   written impl overlaps a derived one (RFC-0207 rule 4). A type that wants a written residual impl does
   not derive that aspect.
5. **Full width.** A residual whose row is the whole type normalises to the plain type (RFC-0137). An exact-shape impl for the full row is the whole-type impl, and writing both is `T0015`.
6. **Super-aspects.** An impl of `A` for a residual requires every positive super-aspect of `A` to hold
   for that residual, through a template or a residual impl (RFC-0213 section 2).
7. **`declared` aspects** are never granted by a residual impl: `extend DocTitle: Copy;` is the
   error of RFC-0212 section 1. A residual is `Copy` only through the declaration's grant.
8. **Dispatch** is static. A bound `T: A` instantiated with a residual selects the residual's impl, or
   fails with `T0012` if there is none. The silent skip of metel-core#1788 cannot occur.

**Dynamic semantics.** A row-bounded method sees only its declared fields. An exact-shape impl sees the
fields of its shape. Neither can read an absent field, so no field is read that does not exist.

## 3. Worked examples

```metel
struct Cache { data: i64, hits: i64, }
extend Cache: Clone { fun clone(&self) -> Cache { return Cache { data = self.data, hits = 0 }; } }

view CacheData for Cache { data }
extend CacheData: Clone {
    fun clone(&self) -> Self { /* a CacheData from self.data */ }
}
// cache.{ .data } is Clone through the residual impl (Cache is affine, so it is never Copy).

struct Id derives Clone { n: i64, }
extend Id.{ .n }: Clone { /* .. */ }             // error T0015: overlaps the template of `derives Clone`

struct Row { key: i64, payload: String, }
extend Row: PartialEq {
    fun eq(&self: Self.{ .key }, other: &Self.{ .key }) -> boolean { return self.key == other.key; }
}
// Row, Row.{ .key }, Row.{ .key, .payload } all compare by key
```

## 4. Relationship to existing RFCs

- **RFC-0137** (section 5 and section 6) — `Drop` dispatch is the one existing instance; widening
  restores the missing fields and is unaffected.
- **RFC-0109, RFC-0146, RFC-0147, RFC-0148, RFC-0150** — the receiver forms and the named view this RFC
  uses. This RFC depends on them being accepted; they are under review. RFC-0146 section 6 excludes
  "row-conditional impl resolution" (`extend Self.R where R: { f, .. }: Foo`); this RFC does not add it.
  The required set comes from method receivers, as for `Drop`, so the impl is selected by a subset
  check against a concrete row and needs no row variable in impl resolution.
- **RFC-0174, RFC-0208, RFC-0123, RFC-0216** — the row-generic form: the field loop, the row binder,
  the field-wise bound, and construction of the `Self`-returning result. Only this form depends on them.
- **RFC-0209, RFC-0217** — templates for granted aspects; written impls cover the cases templates do not.
- **RFC-0206, RFC-0212, RFC-0213** — `Copy` on a residual (rule 6), `declared` (rule 7),
  super-aspects (rule 6). Not a dependency of any of them.
- **RFC-0207 / RFC-0093** — derived against written impls (rule 4).
- **RFC-0081 / RFC-0060** — coherence; `T0015` for overlap.

## Alternatives considered

- **Templates only; no written residual impl.** The status quo of RFC-0211 and RFC-0217. Simple, and enough for the
  settlement. It leaves a type with a written `Clone` unable to define what its projections copy to,
  and leaves `Drop` as the only aspect with a written residual route.
- **A row-conditional impl** (`extend Self.R where R: { f, .. }: A`). Excluded by RFC-0146 section 6 as
  RFC-0121 territory; it needs a row variable in impl resolution. The receiver-declared set avoids that.
- **Apply the whole-type impl to every residual that has the fields it reads.** A check of the body
  against the residual row is the `Drop` rule for one aspect. It needs a fixed point over helper calls
  that RFC-0137 section 5 removed in favour of a declared set.
- **Generate a structural impl for the residual when the whole type's is written.** This is the
  template, and deriving it for a type whose author wrote the impl by hand discards the author's
  intent. Rejected by RFC-0211 and RFC-0217.

## Out of Scope

- Residual impls for foreign types; negative residual impls (`extend DocTitle: !Send;`).
- `dyn Aspect` over a residual: a `dyn` value erases the shape (RFC-0146).

## Unresolved Questions

1. **How is a residual value built?** An exact-shape or row-generic `clone` returns `Self`, a residual,
   and a residual is produced today only by projection or partial move. RFC-0216 (draft) proposes a
   construction form restricted to the defining module; its spelling and the constructor-invariant risk
   of RFC-0137 section 6 are open there.
2. **Methods with different receiver rows in one impl.** The union is the required set; whether a
   method with a narrower receiver may be called on a residual that has only its own fields is open.
3. **Enums.** Enums are atomic for narrowing and have no residuals (RFC-0150, RFC-0217), so this RFC
   does not apply to them unless that changes (variant rows, RFC-0210).
4. **Default methods** of the aspect and their receiver rows.
5. **Spelling:** `extend DocTitle: A` through a view, `extend Doc.{ .f }: A` inline, or both.
6. **Whether row-bounded impls are needed at all** if exact-shape impls and templates suffice; the
   `Display`/`PartialEq` examples are the case for them.
7. **Per-field customisation of a derive** (`derives Clone` with one field's behaviour overridden) as
   a lighter alternative to the row-generic form for the common "reset one field" case (RFC-0213
   open question 8).
8. **Receiver narrowing as tooling.** Inferring a required field set from a body is rejected as a
   language rule (RFC-0137 section 5); an editor suggestion that proposes `Self.{ .title }` for a body
   that reads only `title` is not.
9. **Compile-time refinement of a symbolic field.** Whether `comptime if (field.name == "hits")` refines
   `field.type` inside the branch, so a loop body can treat one named field specially while keeping the others
   generic.

---

## Decision

**Outcome:** *(pending)*
