---
id: rfc-0146
title: "Row-Polymorphic Self-Views"
date: '2026-08-28'
status: under-review
target:
updated: '2026-08-28'
tracking: 'https://github.com/metel-lang/metel-core/issues/886'
---

> **New RFC, opened 2026-08-28 out of a design discussion on the integrated spec's
> "Drop dispatch against a narrowed residual" section (`reference/spec/ownership.md`,
> from RFC-0137) and `metel-core#858` (row-bounded `Drop` dispatch, RFC-0137 slice 2).**
> That discussion identified two distinct missing constructs — a *named row variable in
> receiver position* (`Self.R`), and a *destructor parameterized over which residual it
> runs against* (`drop<row R>`). This is the first; RFC-0148 (Row-Parametric Destructors)
> is the second and depends on this one. (RFC-0147, Projection-Receiver Destructors,
> covers the *fixed* projected `drop` receiver and depends on RFC-0109, not on this RFC.)
>
> **Overlap check (`rfc.py new` similarity + `INDEX.md` records cluster + `REGISTRY.md`):**
> - **RFC-0121 (Open Rows, `1-under-review`, `metel-core#792`)** owns the `row` kind,
>   `..R`, row algebra (extension/removal), row unification, and row-conditional
>   typestate. This RFC is a *consumer and a strict scoping* of that mechanism: receiver
>   position only, lower-bounded only, no algebra, no row-conditional impls. Not a
>   competing proposal — see §6 and Open Question 1 (wait for RFC-0121, or carve out the
>   minimal lower-bounded-row-variable slice and hand the rest back).
> - **RFC-0123 (Field-Wise Row Constraints, `1-under-review`, `metel-core#793`)** also
>   quantifies over `<row R>` but applies an *aspect* bound to every field of a row
>   (`where all R: Display`). Different constraint kind — presence of fields vs. a
>   capability of each field's type — and independent of this RFC; both are consumers of
>   RFC-0121's `<row R>`.
> - **RFC-0109 (Self-View Narrowing, `1-under-review`, `metel-core#842`)** lets a method
>   name a *fixed* residual and take it as its receiver — `view V for S { a }` then
>   `self: &V`, which it defines as exactly `self: &S.{ a }`. This RFC generalizes that
>   fixed residual to a parametric one; it builds directly on RFC-0109's
>   residual-typed-receiver form.
> - **RFC-0144 (Reference-Destructuring Patterns, `1-under-review`, `metel-core#843`)**
>   is RFC-0109's split-off sibling — `&var { a, b } = h;` pattern work, unrelated to
>   receiver typing. Named only to disambiguate.
> - **RFC-0044 (Explicit Receiver Semantics, implemented)** — the receiver forms
>   (`&self` / `&var self`) this RFC's row-parametric receiver slots into.
> - **RFC-0118 (Row Bounds, implemented)** — `{ a, .. }` open-bound spelling, reused
>   verbatim for the `where` clause here.
> - **RFC-0137 (Nominal Types as Branded Rows, `3-integrated`)** — the `(brand, row)`
>   representation and the narrowing lattice, now in `reference/spec/ownership.md`
>   ("Partial moves", "Narrowing", "Passing a residual to a function", "Drop dispatch
>   against a narrowed residual"). Cited as normative spec, with RFC-0137 as design
>   history.

> **Status — under review (2026-08-28).** Substantiated primary proposal (concrete syntax, static semantics, worked examples) with explicit blocking open questions; design engagement underway, on a concrete downstream path (RFC-0148, Row-Parametric Destructors). Committed to **v0.15.0** (issue #886) — deliberately a release behind the row/view frontier (RFC-0121, RFC-0123, RFC-0109 at v0.14.0), so it can depend on *full* RFC-0121 rather than needing the Open Question 1 carve-out. Downstream RFC-0148 then lands v0.16.0+. Tracking: metel-core#886.

## Summary

A method may bind its receiver to a **row parameter** instead of a fixed type or a fixed
named view:

```metel
extend Handle {
    fun close_fd<row R>(&var self: Self.R) where R: { fd, .. } {
        sys_close(self.fd)
    }
}
```

`Self.R` is "some residual of `Self`, same brand, whose row contains *at least* the
fields named in the `where` clause." One method body type-checks once, against that
lower bound, and becomes callable on the full struct, on `Self.{ fd, name }`, on
`Self.{ fd }` — any residual wide enough. `R` is a compile-time-only row variable: it is
**erased, never monomorphized**, and carries zero runtime cost beyond what a fixed
residual receiver (RFC-0109) already costs.

This is RFC-0121's `<row R>` kind applied in exactly one position (the receiver), under
exactly one shape (a lower bound). It is the enabling mechanism behind RFC-0148's
`drop<row R>`.

---

## Motivation

RFC-0137 (integrated) makes every struct value carry a `(brand, row)`, and a partial
move or a field projection narrows a value's static type to a residual of the same brand
(`Handle` → `Handle.{ fd }`). RFC-0109 lets a method name a *fixed* residual —
`view FdView for Handle { fd }` — and take it as `self: &FdView`, defined there as
exactly `self: &Handle.{ fd }`.

Between them there is a gap. Consider a method that genuinely does not care which extra
fields are present — it reads `self.fd` and nothing else, and should work identically on
a freshly constructed `Handle`, on a `Handle` that has had `name` moved out, and on an
explicit projection `h.{ fd }`. Today its author must pick one of three unsatisfactory
options:

- **`fun close_fd(&var self)`** — receiver typed as the whole `Self`. Over-constrains
  every caller who has already narrowed: after `let n = h.name;`, `h: Handle.{ fd }` and
  the call no longer type-checks, even though the method never touches `name`.
- **`fun close_fd(&var self: Self.{ fd })`** or the RFC-0109 named-view equivalent —
  receiver typed as a *fixed* residual. The integrated spec's "Passing a residual to a
  function" rule permits no implicit truncation at the call boundary, so every caller
  must narrow to *exactly* `.{ fd }` first, discarding width they may still want after
  the call.
- Write **one overload per residual width** the method should accept — combinatorial,
  and most of the widths are not nameable in advance.

None of these expresses the actual contract: *at least `{ fd }`, brand preserved, the
rest is none of this method's business.* A lower-bounded row parameter expresses
precisely that, and nothing more.

Closing the same gap for `Drop` is exactly what RFC-0137 §5's row-bounded dispatch was
amended to do on 2026-08-28: a `Drop` impl's required field set is now *declared on the
`drop` receiver* (`spec.ownership.drop-dispatch-against-a-narrowed-residual.legality-1`),
not inferred from the body. This RFC's `Self.R` is the parametric form of that declared
receiver (RFC-0148); the fixed form is RFC-0109's named views (RFC-0147).

---

## 1. Syntax

```
method       ::= "fun" ident row-generics? "(" receiver rest-params? ")" ret? where-clause? block
row-generics ::= "<" ("row" ident) ("," (ident | "row" ident))* ">"   // reuses RFC-0121 §1's `row R`
receiver     ::= ("&" | "&var")? "self" ":" "Self" "." ident
where-clause ::= "where" ident ":" "{" field-list "," ".." "}"
```

- `<row R>` introduces a row-kinded generic parameter, distinct from an ordinary type
  parameter `<T>`. A method may mix them: `fun m<T, row R>(...)`.
- `Self.R` in receiver-type position is the residual type. `&Self.R` / `&var Self.R`
  follow the ordinary receiver-mode rules (RFC-0044).
- The `where R: { … , .. }` clause is a **lower bound**: the row `R` unifies with must
  contain at least the listed fields. The trailing `..` is mandatory and carries the
  same meaning as in RFC-0118 — it is what marks the bound *open* (a lower bound rather
  than an exact row).
- Omitting the `where` clause gives `R` the empty lower bound: the body may name no
  `self.<field>` at all. Legal but near-useless; a lint should flag it (Open Question 3).

Row parameters are permitted **only** on the receiver in this RFC. `R` may not appear on
another parameter, in the return type, or in the body as a standalone type — those are
RFC-0121 territory (see Out of Scope).

An RFC-0109 named view remains the way to give a *fixed* residual a reusable name;
`Self.R` is for the case where no single fixed residual is the contract.

---

## 2. Static semantics

**Body check (once, against the lower bound).** The method body is type-checked a single
time with `self: Self.<lower-bound-row>`. Two rules:

1. Every `self.<field>` access (read or write) must name a field in the `where` lower
   bound. A field outside it is a compile error at the access site — *"`close_fd`
   declares it needs `Self.{ fd, .. }`; `self.name` is not in that row"*.
2. Every call `self.other_method(...)` must have `other_method`'s own receiver lower
   bound ⊆ this method's `where` lower bound. Composition is **local**: each callee
   states its own bound in its own signature; there is no whole-call-graph fixed point.
   A callee typed on the whole `Self` has lower bound = the full row, so calling it from
   a row-polymorphic method forces this method's `where` clause to name the full row too
   (and the row parameter then buys nothing — correctly).

**Use-site check (unify `R`).** At a call site, `R` is unified with the receiver
expression's statically known residual row (from RFC-0137's narrowing lattice, spec
"Narrowing"). The call is well-typed iff that row ⊇ the `where` lower bound. No implicit
narrowing occurs — a wider receiver is fine; the parameter is not a truncation request.

**Brand.** `Self.R` carries `Self`'s brand. `R` unifies only with residuals of that same
brand. A same-shaped anonymous record, or a same-shaped residual of a different struct's
brand, does not unify — the spec's "Narrowing" legality-2 (a residual's row is never
visible to structural matching; only its brand) extends unchanged to the parametric
receiver.

---

## 3. Erasure and cost

`R` is a type-checker fiction. There is no monomorphization: the body is compiled once,
against the lower bound, and the residual's additional fields are simply not nameable
inside it. A call on a wide receiver and a call on a narrow one dispatch to the same
compiled body.

Runtime cost is therefore identical to an RFC-0109 named-view receiver: a receiver
reference is a small value holding field references; a struct's memory layout never
changes with narrowing (the spec's "Narrowing" and RFC-0137 §8 rest on RFC-0071's
static-bookkeeping design). This RFC adds no new runtime representation and no new
dispatch path.

---

## 4. Interaction with generics

A generic struct has type parameters `<T>` and, under this RFC, its methods may also have
row parameters `<row R>`. They are independent kinds:

```metel
extend<T> Pair<T> {
    fun first<row R>(&self: Self.R) -> &T where R: { a, .. } { &self.a }
}
```

`T` ranges over types, `R` over rows; neither constrains the other. Consistent with
RFC-0137 §7 (a struct's declared fields never vary with `T`), the `where` lower bound is
a fixed set of field *names* and must not depend on `T` — a field's *type* may be
symbolic, its *presence* may not.

---

## 5. Worked examples

```metel
struct Handle { fd: i32, name: str }

extend Handle {
    fun raw_fd<row R>(&self: Self.R) -> i32 where R: { fd, .. } { self.fd }
}

fun demo(h: Handle) {
    let n = h.name;          // h: Handle.{ fd }
    let x = h.raw_fd();       // OK: { fd } ⊇ { fd }
}

fun demo_wide(h: Handle) {
    let x = h.raw_fd();       // OK: { fd, name } ⊇ { fd }; h still Handle afterward
    use_full(h);              // still typechecks — no truncation happened
}
```

```metel
extend Handle {
    // rejected: body names `self.name`, not in the declared lower bound
    fun bad<row R>(&self: Self.R) -> str where R: { fd, .. } { self.name }
    //                                                          ^^^^^^^^^ E: `name` ∉ Self.{ fd, .. }
}
```

```metel
extend Handle {
    fun helper<row R>(&self: Self.R) where R: { fd, .. } { /* ... */ }

    fun caller<row R>(&self: Self.R) where R: { fd, .. } {
        self.helper();   // OK: { fd } ⊆ { fd }
        self.whole();    // E: `whole` needs Self.{ fd, name, .. }, not covered by { fd, .. }
    }
    fun whole(&self) { let _ = self.name; }
}
```

---

## 6. What this RFC does not add

Deliberately excluded, all RFC-0121 (or RFC-0114) territory:

- **Row extension** — `R + { x }`, building a wider row from `R`.
- **Row removal where-clauses** — `where S: R \ { x }`.
- **Row-conditional impl resolution / typestate** — `extend Self.R where R: { open, .. }: Foo`.
- **Naming `R` in return position** to hand back a value of the caller's original width,
  or to reconstruct a wider value. Widening a residual is the spec's "Widening" /
  RFC-0114's `construct` path.
- **Row parameters on free functions or non-receiver parameters.** Plausible and
  probably wanted eventually; deferred so this RFC stays scoped to the one position
  RFC-0148 needs.

If RFC-0121 is accepted first, this RFC becomes a short "`row R` in receiver position,
lower-bounded, erased" application of it. If this RFC is wanted sooner, it carves out
only that minimal slice — a lower-bounded row variable unified structurally at the use
site — and RFC-0121 keeps the algebra. Either way the split is recorded here and in
RFC-0121's own status blockquote when it happens.

---

## Out of Scope

- Everything in §6.
- Enums (structs-only, consistent with the whole records cluster).
- Turning `--move-check` on by default (a separate migration; this RFC's residuals
  arise under move checking / projection, but it does not change the flag's default).
- `dyn Aspect` receivers — a `dyn` value erases the residual shape. Whether a
  row-polymorphic method is even callable through a trait object is left to RFC-0008's
  own build-out; the `Drop`-specific coercion checkpoint is RFC-0147's concern, not
  this RFC's.

---

## Open Questions

1. **Carve-out vs. wait for RFC-0121.** *(Blocked on a dated dependency.)* This RFC needs
   the `row` kind and lower-bounded row unification. RFC-0121 owns both but also carries
   the expensive algebra and is not accepted. Decide whether RFC-0146 extracts the
   minimal slice (and RFC-0121 is revised to depend on it) or is scheduled strictly
   after RFC-0121's acceptance. **The v0.15.0 milestone (issue #886) puts this a release
   after RFC-0121 (v0.14.0)**, so the default is "wait for full RFC-0121" and the
   carve-out becomes an optimisation to pull RFC-0146 forward, not a requirement.
2. **Parse boundary.** RFC-0121 §1 chose `row R`; this RFC follows it (`<row R>`).
   Confirm no ambiguity in a method carrying both `<T>` and `<row R>`, and that
   `Self.R` in receiver position never collides with a `T.field` associated-type-style
   path. Needs an integration example at that boundary.
3. **Is an unbounded `R` worth allowing?** A `where`-less row parameter permits no field
   access and is almost always a mistake. Reject it outright, or accept with a lint.
   (Leaning: require the `where` clause.)
4. **Bound inference as a convenience.** Could `R`'s lower bound be *inferred* from the
   body's field accesses rather than written? That is exactly the body-analysis approach
   RFC-0147 argues against for `Drop` (action-at-a-distance, no stable contract). State
   explicitly whether inference is offered as sugar for the non-`Drop` case or refused
   for consistency.
5. **Relationship to RFC-0109's named views.** A named view is a fixed residual with a
   reusable name; `Self.R` is a parametric residual with a bound. Confirm they compose
   (a `where R: V`-style bound naming a view as the lower bound?) or stay deliberately
   separate spellings, and which of RFC-0147 / RFC-0148 builds on which.

---

## References

- `reference/spec/ownership.md` — "Partial moves", "Narrowing", "Passing a residual to
  a function", "Drop dispatch against a narrowed residual" (RFC-0137, integrated); the
  normative rules this RFC's receiver types and use-site checks build on
- RFC-0137 (Nominal Types as Branded Rows, `3-integrated`) — design history for the
  above; §7 (generic structs), §8 (cost)
- RFC-0121 (Open Rows, `1-under-review`, `metel-core#792`) — owns `<row R>`, `..R`, row
  algebra and unification; this RFC is a scoped consumer (see §6, Open Question 1)
- RFC-0123 (Field-Wise Row Constraints, `1-under-review`, `metel-core#793`) — the other
  `<row R>` consumer; per-field aspect bounds, orthogonal to this RFC
- RFC-0109 (Self-View Narrowing, `1-under-review`, `metel-core#842`) — fixed named
  residual receivers (`view V for S { a }`, `self: &V` = `self: &S.{ a }`); this RFC
  generalizes the residual to a parameter
- RFC-0144 (Reference-Destructuring Patterns, `1-under-review`, `metel-core#843`) —
  RFC-0109's split-off sibling; pattern work, unrelated to receiver typing
- RFC-0118 (Row Bounds, implemented) — `{ a, .. }` open-bound spelling reused for the
  `where` clause
- RFC-0044 (Explicit Receiver Semantics, implemented) — receiver forms `&self` / `&var self`
- RFC-0071 (Ownership and Move Semantics, `3-integrated`, partial-move tracking not yet
  implemented, `metel-core#858`) — the move-tracking foundation residuals depend on
- RFC-0148 (Row-Parametric Destructors, `1-under-review`) — the `Drop`-specific
  application this RFC exists to enable (the parametric `fun drop<row R>(...)` form)
- RFC-0147 (Projection-Receiver Destructors, `1-under-review`) — the sibling *fixed*
  `drop` receiver form; depends on RFC-0109, not on this RFC
- `metel-core#858` — RFC-0137 slice 2 (move-triggered narrowing/widening, row-bounded
  `Drop` dispatch); the implementation context that prompted this RFC
- `metel-core#261` — RFC-0071 (3/4): drop order and explicit drop; destructor invocation,
  which must land before any `Drop` body actually runs

---

## Decision

**Outcome:** *(pending)*
**Target:** *(set when accepted)*
