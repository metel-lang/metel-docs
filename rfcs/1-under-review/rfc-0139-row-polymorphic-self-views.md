---
id: rfc-0139
title: "Row-Polymorphic Self-Views"
date: '2026-08-28'
status: under-review
target:
updated: '2026-08-28'
tracking: 'https://github.com/metel-lang/metel-core/issues/883'
---

> **New RFC, opened 2026-08-28 out of a design discussion on RFC-0137 §5 /
> `metel-core#858` (row-bounded `Drop` dispatch).** That discussion identified two
> distinct missing constructs — a *named row variable in receiver position* (`Self.R`),
> and a *destructor parameterized over which residual it runs against* (`drop<R>`) — and
> agreed they are separate RFCs with a dependency between them. This is the first;
> RFC-0140 (Generic-Projection Destructors) is the second and depends on this one.
>
> **Overlap check (`INDEX.md` records cluster + `REGISTRY.md`, done manually — this RFC
> was written by hand, not via `rfc.py new`):**
> - **RFC-0121 (Open Rows, under review)** owns the `row` kind, `..R`, row algebra
>   (extension/removal), row unification, and row-conditional typestate. This RFC is a
>   *consumer and a strict scoping* of that mechanism: receiver position only,
>   lower-bounded only, no algebra, no row-conditional impls. It is not a competing
>   proposal — see §6 and Open Question 1 for how the two reconcile (wait for RFC-0121,
>   or carve out the minimal lower-bounded-row-variable slice and hand the rest back).
> - **RFC-0109 (Self-View Narrowing, draft)** owns receiver-position sub-row annotations
>   in their *fixed* form (`self: &TicketView`, `self: &var { a, b }`). This RFC
>   generalizes the fixed view to a parametric one and depends on RFC-0109's
>   receiver-projection syntax existing at all.
> - **RFC-0137 (Nominal Types as Branded Rows, under review)** supplies the
>   `(brand, row)` representation `R` ranges over. Hard dependency.
> - **RFC-0117 (Row Narrowing, under review)** defines the closed 2^*N* subset lattice
>   the residuals `R` binds to are drawn from. This RFC reads that lattice; it does not
>   extend it.
> - **RFC-0118 (Row Bounds, implemented)** already establishes `{ fd, .. }` open-bound
>   syntax and that the trailing `..` is what makes a bound open. This RFC reuses that
>   spelling for the `where` clause verbatim.

> **Status — under review (2026-08-28).** Substantiated primary proposal with concrete syntax, static semantics, worked examples, and explicit blocking open questions; design engagement underway. Tracking: metel-core#883.

## Summary

A method may bind its receiver to a **row parameter** instead of a fixed type or a fixed
projection:

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
projection already costs.

This is RFC-0121's `<row R>` kind applied in exactly one position (the receiver), under
exactly one shape (a lower bound). It is the enabling mechanism behind RFC-0140's
`drop<R>`.

---

## Motivation

RFC-0137 makes every struct value carry a `(brand, row)`. RFC-0109 lets a method declare
a *fixed* sub-row it touches. Between them there is a gap.

Consider a method that genuinely does not care which extra fields are present — it reads
`self.fd` and nothing else, and should work identically on a freshly constructed
`Handle`, on a `Handle` that has had `name` moved out, and on an explicit projection
`h.{ fd }`. Today its author must pick one of two unsatisfactory options:

- **`fun close_fd(&var self)`** — receiver typed as the whole `Self`. Over-constrains
  every caller who has already narrowed: after `let n = h.name;`, `h: Handle.{ fd }` and
  the call no longer type-checks, even though the method never touches `name`.
- **`fun close_fd(&var self: Self.{ fd })`** (RFC-0109 + RFC-0137) — receiver typed as a
  fixed projection. RFC-0137 §4 forbids implicit truncation at the call boundary, so
  every caller must now narrow to *exactly* `.{ fd }` first, discarding width they may
  still want after the call.

Neither expresses the actual contract: *at least `{ fd }`, brand preserved, the rest is
none of this method's business.* A lower-bounded row parameter expresses precisely that,
and nothing more.

The same gap is what forces RFC-0137 §5's row-bounded `Drop` dispatch to *infer* a
destructor's required field set from its body (with an unsolved open question about
composing that set transitively through helper calls). A declared lower bound replaces
the inference — see RFC-0140.

---

## 1. Syntax

```
method      ::= "fun" ident row-generics? "(" receiver rest-params? ")" ret? where-clause? block
row-generics ::= "<" "row" ident ("," ...)? ">"          // reuses RFC-0121 §1's `row R` spelling
receiver    ::= ("&" | "&var")? "self" ":" "Self" "." ident
where-clause ::= "where" ident ":" "{" field-list "," ".." "}"
```

- `<row R>` introduces a row-kinded generic parameter, distinct from an ordinary type
  parameter `<T>`. A method may mix them: `fun m<T, row R>(...)`.
- `Self.R` in receiver-type position is the residual type. `&Self.R` / `&var Self.R`
  follow the ordinary receiver-mode rules (RFC-0067a).
- The `where R: { … , .. }` clause is a **lower bound**: the row `R` unifies with must
  contain at least the listed fields. The trailing `..` is mandatory and carries the
  same meaning as in RFC-0118 — it is what marks the bound *open* (a lower bound rather
  than an exact row).
- Omitting the `where` clause means `R` has the empty lower bound: the body may name no
  `self.<field>` at all. Legal but near-useless; a lint should flag it and suggest
  either naming the fields or dropping the row parameter. (Open Question 3.)

Row parameters are permitted **only** on the receiver in this RFC. `R` may not appear on
another parameter, in the return type, or in the body as a standalone type. Those are
RFC-0121 territory (see Out of Scope).

---

## 2. Static semantics

**Body check (once, against the lower bound).** The method body is type-checked a single
time with `self: Self.<lower-bound-row>`. Two rules:

1. Every `self.<field>` access (read or write) must name a field in the `where` lower
   bound. A field outside it is a compile error at the access site — *"`close_fd`
   declares it needs `Self.{ fd, .. }`; `self.name` is not in that row"*.
2. Every call `self.other_method(...)` must have `other_method`'s own receiver lower
   bound ⊆ this method's `where` lower bound. Composition is **local**: each callee
   states its own bound in its own signature; there is no whole-call-graph fixed point
   and no effect inference. A callee typed on the whole `Self` has lower bound = the full
   row, so calling it from a row-polymorphic method forces this method's `where` clause
   to name the full row too (and the row parameter then buys nothing — correctly).

**Use-site check (unify `R`).** At a call site, `R` is unified with the receiver
expression's statically known residual row (from RFC-0117's lattice). The call is
well-typed iff that row ⊇ the `where` lower bound. No implicit narrowing occurs — a
wider receiver is fine (that is the point); the parameter is not a truncation request.

**Brand.** `Self.R` carries `Self`'s brand. `R` unifies only with residuals of that same
brand. A same-shaped anonymous record, or a same-shaped residual of a different struct's
brand, does not unify — the RFC-0137 §4 motivating-bug fix extends unchanged to the
parametric receiver.

---

## 3. Erasure and cost

`R` is a type-checker fiction. There is no monomorphization: the body is compiled once,
against the lower bound, and the residual's additional fields are simply not nameable
inside it. A call on a wide receiver and a call on a narrow one dispatch to the same
compiled body.

Runtime cost is therefore identical to the fixed-projection form (RFC-0109 §4): a
receiver reference is a small value holding field references; a struct's memory layout
never changes with narrowing (RFC-0137 §8, contingent on RFC-0071's static-bookkeeping
design being what gets built). This RFC adds no new runtime representation and no new
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
RFC-0137 §7, the `where` lower bound is a fixed set of field *names* and must not depend
on `T` — a field's *type* may be symbolic, its *presence* may not.

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
    let x = h.raw_fd();       // OK: { fd, name } ⊇ { fd }, h still Handle afterward
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

    // rejected: calls `whole(self)` whose receiver lower bound is the full row
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
- **Row-conditional impl resolution / typestate** — `extend Handle.R where R: { open, .. }: Foo`.
- **Naming `R` in return position** to hand back a value of the caller's original width,
  or to reconstruct a wider value. Widening a residual is RFC-0114's `construct` path.
- **Row parameters on free functions or non-receiver parameters.** Plausible and
  probably wanted eventually; deferred so this RFC stays scoped to the one position
  RFC-0140 needs.

If RFC-0121 is accepted first, this RFC becomes a short "here is `row R` in receiver
position, lower-bounded, erased" application of it. If this RFC is wanted sooner, it
carves out only that minimal slice — a lower-bounded row variable unified structurally at
the use site — and RFC-0121 keeps the algebra. Either way the split is recorded here and
in RFC-0121's own status blockquote when it happens.

---

## Out of Scope

- Everything in §6.
- Enums (structs-only, consistent with the whole records cluster).
- Turning `--move-check` on by default (a separate migration; this RFC's residuals only
  arise under move checking, but it does not change the flag's default).
- `dyn Aspect` receivers — a `dyn` value erases the residual shape; whether a
  row-polymorphic method is even callable through a trait object, and whether that needs
  the runtime row representation RFC-0137 §8 flags, is left to RFC-0008's own revival.

---

## Open Questions

1. **Carve-out vs. wait for RFC-0121.** *(Blocked on a dated dependency.)* This RFC needs
   the `row` kind and lower-bounded row unification. RFC-0121 owns both but also carries
   the expensive algebra and is not accepted. Decide whether RFC-0139 extracts the
   minimal slice (and RFC-0121 is revised to depend on it) or is scheduled strictly
   after RFC-0121's acceptance.
2. **Syntax for the row-generics list.** RFC-0121 §1 chose `row R`. This RFC follows it
   (`<row R>`). Confirm there is no parse ambiguity with an ordinary `<R>` where the
   receiver position `Self.R` would otherwise be the only rowness signal — leaning on the
   explicit `row` keyword avoids it, but the collision boundary (a method with both `<T>`
   and `<row R>`, `Self.R` vs `T.field`) should get an integration example.
3. **Is an unbounded `R` worth allowing?** A `where`-less row parameter permits no field
   access and is almost always a mistake. Options: reject it outright, or accept it with
   a lint. (Leaning: require the `where` clause.)
4. **Bound inference as a convenience.** Could `R`'s lower bound be *inferred* from the
   body's field accesses rather than written? That is exactly the body-analysis approach
   RFC-0140 argues against for `Drop` (action-at-a-distance, no stable contract). State
   explicitly whether inference is offered as sugar for the non-`Drop` case or refused
   for consistency.
5. **Does this subsume RFC-0109's fixed `self: &View`?** A fixed projection is
   `Self.R where R: { exact-fields, .. }` with `R` never otherwise mentioned. Keeping the
   fixed form as its own spelling has value: it needs no `row` kind and can ship with
   RFC-0137/RFC-0109 while the parametric form waits on RFC-0121. Decide whether both
   spellings coexist or the fixed one is sugar.

---

## References

- RFC-0121 (Open Rows, under review) — owns `<row R>`, `..R`, row algebra and
  unification; this RFC is a scoped consumer, see §6 and Open Question 1
- RFC-0109 (Self-View Narrowing, draft) — receiver-position sub-row annotations in fixed
  form; this RFC generalizes them to parametric and depends on their syntax
- RFC-0137 (Nominal Types as Branded Rows, under review) — the `(brand, row)`
  representation `R` ranges over; §4's no-implicit-truncation rule this RFC works within;
  §5's `Drop` dispatch this RFC's sibling RFC-0140 rewrites
- RFC-0117 (Row Narrowing, under review) — the closed 2^*N* subset lattice residuals are
  drawn from
- RFC-0118 (Row Bounds, implemented) — `{ fd, .. }` open-bound spelling reused verbatim
  for the `where` clause
- RFC-0067a (Reference Forms, implemented) — receiver modes `&self` / `&var self`
- RFC-0071 (Ownership and Move Semantics, `3-integrated`, partial-move tracking not yet
  implemented) — the move-tracking foundation residuals depend on
- RFC-0140 (Generic-Projection Destructors, under review) — the `Drop`-specific application this
  RFC exists to enable
- `metel-core#858` — RFC-0137 slice 2 implementation issue (row-bounded `Drop` dispatch),
  the discussion that prompted this RFC
- `metel-core#261` — RFC-0071 (3/4): drop order and explicit drop; destructor invocation,
  which must land before any `Drop` body (row-polymorphic or not) actually runs

---

## Decision

**Outcome:** *(pending)*
**Target:** *(set when accepted)*
