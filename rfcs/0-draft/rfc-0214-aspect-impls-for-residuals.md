---
id: rfc-0214
title: "Aspect Impls for Residuals"
date: '2026-11-04'
status: draft
---

> **Status — draft (2026-11-04).** First draft. Nothing here is decided.

> **Not a dependency.** The `Clone`/`ImplicitClone` settlement (RFC-0206, RFC-0207, RFC-0211, RFC-0212,
> RFC-0213) does not wait for this RFC. Until it is accepted and implemented a residual satisfies an
> aspect only through a row template (RFC-0211 rule 1), a hand-written impl for the whole type never
> applies to a residual (RFC-0211 rule 2), and there is no way to write an impl for a residual. This RFC
> only adds that written route; every rule of the settlement stays true without it.

## Summary

A residual type `T.{ fields }` (RFC-0137) is the same brand as `T` with some fields narrowed away. Today
a written aspect impl for `T` never applies to a residual, because its body may read a field the
residual no longer has, and the language has no way to write an impl whose receiver is a residual.
Only `Drop` has such a route: RFC-0137 section 5 dispatches a destructor against any residual whose row
contains the fields the `drop` receiver declares (RFC-0147, RFC-0148).

This RFC generalises that route to any aspect. An impl declares the residual it needs on its method
receivers, in the forms RFC-0147 and RFC-0146 already define, and applies to every residual that has
those fields. An impl for one exact shape is also allowed, and may build its own result.

```metel
struct Doc { title: String, n: i64, }

view DocTitle for Doc { title }                 // RFC-0109: a name for Doc.{ title }

extend Doc: Display {                           // the whole type
    fun fmt(&self) -> String { return self.title.clone() + ": " + self.n.to_string(); }
}

extend DocTitle: Display {                      // the residual: needs only `title`
    fun fmt(&self) -> String { return self.title.clone(); }
}
```

## Motivation

1. **A residual cannot carry a written impl.** `d.{ title }` is a value of a type with the same brand
   as `Doc`, yet an author who wrote `Doc: Clone` by hand has no way to say what cloning a projection
   means. RFC-0211 gives the author two options only: derive the impl (a template then covers every
   residual) or accept that the projection has no impl. With `ImplicitClone` that decides whether a
   projection is copied or moved (RFC-0206, RFC-0211 rule 1).
2. **A bound call on a residual silently skips the written impl today.** `dup(&d.{ title })` with
   `T: Clone` is accepted and runs a structural copy instead of the user's `clone` (metel-core#1788).
   RFC-0211 turns that into `T0012`. A written residual impl would give it a defined meaning.
3. **`Drop` already works this way** and is the only aspect that does. The mechanism is not specific to
   destructors, and a second special case per aspect is the kind of exception the settlement avoids.
4. **Some impls are naturally partial.** A `Display` for a view, or an equality that compares only the
   key fields, reads a few fields and should apply to every wider residual.

## 1. Two forms of residual impl

**Row-bounded impl.** The impl's required field set is the union of the residual rows its method
receivers declare (RFC-0147 fixed projection, RFC-0146 `Self.R where R: { f, .. }`). A receiver that
is a bare `&self` requires the whole row. The impl applies to every residual of the brand whose present
fields include the required set, and each method body is checked against its own receiver row, exactly
as RFC-0137 section 5 checks a destructor. `R` is erased (RFC-0146 section 3): no cost beyond a fixed
residual receiver.

```metel
extend Doc: Display {
    fun fmt(&self: Self.{ title }) -> String { return self.title.clone(); }
}
// applies to Doc, Doc.{ title }, Doc.{ title, n }; not to Doc.{ n }
```

**Exact-shape impl.** The impl target is one residual type or one named view (RFC-0109):
`extend DocTitle: A { .. }` or `extend Doc.{ title }: A { .. }`. It applies to exactly that shape and
`Self` is that shape. It is the form for a method that returns `Self`, because a row-bounded impl cannot
build a value of an unknown width.

```metel
extend DocTitle: Clone {
    fun clone(&self) -> Self { return /* a DocTitle built from self.title.clone() */; }
}
```

**Self-returning methods.** In a row-bounded impl `Self` is the matched residual, of unknown width. A
method that returns `Self` or takes it by value cannot construct the missing fields, so it is an error
in a row-bounded impl unless the missing fields are handled by a template (`where ..R: A`, RFC-0123,
RFC-0209). `Clone` therefore needs the exact-shape form, or the template. Methods that only read
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
4. **Templates.** If the type's header grants the aspect, the row template (RFC-0209, RFC-0211)
   already covers every residual, and a residual impl of the same aspect overlaps it (`T0015`), as a
   written impl overlaps a derived one (RFC-0207 rule 4). A type that wants a written residual impl does
   not derive that aspect.
5. **Full width.** A residual whose row is the whole type normalises to the plain type (RFC-0137). An exact-shape impl for the full row is the whole-type impl, and writing both is `T0015`.
6. **Super-aspects.** An impl of `A` for a residual requires every positive super-aspect of `A` to hold
   for that residual, through a template or a residual impl (RFC-0213 section 2). This is how a
   projection of a type with a written `Clone` becomes `ImplicitClone`: its header grants
   `ImplicitClone`, and a residual `Clone` is written for that shape. The hook of the residual's
   `ImplicitClone` is that residual's own `Clone` (RFC-0206 section 2).
7. **`declared` aspects** are never granted by a residual impl: `extend DocTitle: ImplicitClone;` is the
   error of RFC-0212 section 1. A residual is `ImplicitClone` only through the declaration's grant.
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
// cache.{ data } is Clone through the residual impl; with `: ImplicitClone` on Cache it is also
// ImplicitClone, and an implicit copy of it calls CacheData::clone.

struct Id derives Clone { n: i64, }
extend Id.{ n }: Clone { /* .. */ }             // error T0015: overlaps the template of `derives Clone`

struct Row { key: i64, payload: String, }
extend Row: PartialEq {
    fun eq(&self: Self.{ key }, other: &Self) -> boolean { return self.key == other.key; }
}
// Row, Row.{ key }, Row.{ key, payload } all compare by key
```

## 4. Relationship to existing RFCs

- **RFC-0137** (section 5 and section 6) — `Drop` dispatch is the one existing instance; widening
  restores the missing fields and is unaffected.
- **RFC-0109, RFC-0146, RFC-0147, RFC-0148, RFC-0150** — the receiver forms and the named view this RFC
  uses. This RFC depends on them being accepted; they are under review. RFC-0146 section 6 excludes
  "row-conditional impl resolution" (`extend Self.R where R: { f, .. }: Foo`); this RFC does not add it.
  The required set comes from method receivers, as for `Drop`, so the impl is selected by a subset
  check against a concrete row and needs no row variable in impl resolution.
- **RFC-0209, RFC-0211** — templates for granted aspects; written impls cover the cases templates do not.
- **RFC-0206, RFC-0212, RFC-0213** — `ImplicitClone` on a residual (rule 6), `declared` (rule 7),
  super-aspects (rule 6). Not a dependency of any of them.
- **RFC-0207 / RFC-0093** — derived against written impls (rule 4).
- **RFC-0081 / RFC-0060** — coherence; `T0015` for overlap.

## Alternatives considered

- **Templates only; no written residual impl.** The status quo of RFC-0211. Simple, and enough for the
  settlement. It leaves a type with a written `Clone` unable to define what its projections copy to,
  and leaves `Drop` as the only aspect with a written residual route.
- **A row-conditional impl** (`extend Self.R where R: { f, .. }: A`). Excluded by RFC-0146 section 6 as
  RFC-0121 territory; it needs a row variable in impl resolution. The receiver-declared set avoids that.
- **Apply the whole-type impl to every residual that has the fields it reads.** A check of the body
  against the residual row is the `Drop` rule for one aspect. It needs a fixed point over helper calls
  that RFC-0137 section 5 removed in favour of a declared set.
- **Generate a structural impl for the residual when the whole type's is written.** This is the
  template, and deriving it for a type whose author wrote the impl by hand discards the author's
  intent. Rejected by RFC-0211.

## Out of Scope

- Residual impls for foreign types; negative residual impls (`extend DocTitle: !Send;`).
- `dyn Aspect` over a residual: a `dyn` value erases the shape (RFC-0146).

## Unresolved Questions

1. **How is a residual value built?** An exact-shape `clone` returns `Self`, a residual, and a residual
   is produced today only by projection or partial move. A construction form (a residual literal),
   restricted to the defining module, is needed. Its spelling and the constructor-invariant risk of
   RFC-0137 section 6 are open.
2. **Methods with different receiver rows in one impl.** The union is the required set; whether a
   method with a narrower receiver may be called on a residual that has only its own fields is open.
3. **Enums.** Enums are atomic for narrowing and have no residuals (RFC-0150, RFC-0211), so this RFC
   does not apply to them unless that changes (variant rows, RFC-0210).
4. **Default methods** of the aspect and their receiver rows.
5. **Spelling:** `extend DocTitle: A` through a view, `extend Doc.{ f }: A` inline, or both.
6. **Whether row-bounded impls are needed at all** if exact-shape impls and templates suffice; the
   `Display`/`PartialEq` examples are the case for them.

---

## Decision

**Outcome:** *(pending)*
