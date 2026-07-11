---
id: rfc-0093
title: "Derive Registration — @derive(Aspect) as Request and Registration"
date: '2026-07-09'
status: draft
target:
---

> **New RFC, split out 2026-07-09** from RFC-0012 (Attributes, Metadata, Macros, and
> Derived Aspects), as part of decomposing that RFC into smaller, independently
> reviewable pieces. Depends on RFC-0092 (Comptime Core) for `type`-as-value, `typeinfo`,
> and single-declaration `emit`. RFC-0080 (Standard Library Aspects) depends on this RFC
> for `Clone`'s derive mechanism; RFC-0090 (Structural Records) depends on this RFC only
> for `ToRecord`/`FromRecord`'s auto-derive *convenience*, not their existence as
> ordinary aspects.
>
> **Answers RFC-0055's Open Question 4** ("can comptime code inspect whether a type
> implements an aspect... could replace some uses of conditional `impl` blocks"),
> discovered 2026-07-09 via `INDEX.md` after this RFC was already drafted — §1's
> `@derive(Aspect)` registration is a more precise answer than RFC-0055's own
> `comptime has_aspect(T, Aspect)` sketch, since it resolves to a specific registered
> comptime function rather than a boolean query. RFC-0055 is superseded by RFC-0092
> primarily, with this RFC covering its OQ-4 specifically.

## Summary

Specifies the mechanism `derives`/`@derive(Aspect)` resolves through: nothing in prior
exploration ever specified how a derive request at a struct or enum's declaration finds
the *specific* comptime function that implements it. `@derive(Aspect)`, attached to the
comptime function that implements the derive, registers it as that aspect's deriver.
The same spelling is used for both request (attached to a struct/enum) and registration
(attached to a comptime function), disambiguated purely by attachment target — mirroring
Rust's `#[derive]`/`#[proc_macro_derive]` split, but with one shared spelling instead of
two.

Also settles the call-site surface syntax as `@derive(Aspect, ...)` — an attribute on
the struct/enum itself — over a `derives` keyword-clause, since nothing about the
registration mechanism requires a new keyword, and the attribute form keeps a struct's
own declaration line uncrowded and is closer to what Rust users already expect.

---

## Motivation

Writing `impl Eq for Point { fun eq(self, other: Point) -> boolean { self.x == other.x && self.y == other.y } }`
by hand for every struct is tedious and error-prone. A derive mechanism generates these
implementations structurally — field-by-field for structs, variant-by-variant for
enums. The question this RFC exists to answer is not *whether* derive is useful — that
much is uncontested and already assumed by RFC-0080 — but *what kind of mechanism*
generates the impl, and specifically *how a derive request finds its implementation*,
which no prior document specifies.

---

## 1. Resolving a derive request to a comptime function

`@derive(Aspect)`, attached to the comptime function that implements the derive,
registers it as that aspect's deriver:

```metel
@derive(Clone)
comptime fun derive_clone(comptime T: type) {
    let fields = typeinfo(T).row;
    emit impl Clone for T { ... }
}
```

`@derive(Clone) struct Point { x: f64, y: f64 }` then resolves by looking up whichever
comptime function is registered for `Clone` — exactly how Rust's own `#[derive(Clone)]`
isn't magic either: it resolves via `#[proc_macro_derive(Clone)]` on the macro's own
implementing function, in a compiler-visible table keyed by name.

The same `@derive(Aspect)` spelling is used in both places above, disambiguated purely
by what kind of declaration it is attached to — a struct/enum means "derive this for
me," a `comptime fun` means "I implement this" — the same way `@inline` only makes
sense attached to a function. This is a real design choice, not an assumed one: Rust
deliberately uses two different attribute names (`derive` vs. `proc_macro_derive`) to
keep the two roles unambiguous at the syntax level; reusing one spelling for both here
trades a small amount of that separation for one fewer concept to learn.

This gives an "open/extensible" derive mechanism an actual implementation: a
third-party library makes its own aspect derivable by writing
`@derive(MyAspect) comptime fun derive_my_aspect(comptime T: type) { ... }` in its own
module, with no special compiler support beyond the registration lookup itself.

### Worked example

```metel
@derive(Clone)
comptime fun derive_clone(comptime T: type) {
    let fields = typeinfo(T).row;   // T's row, reified as a comptime value
    emit impl Clone for T {
        fun clone(self: &T) -> T {
            // built field-by-field from `fields` by ordinary comptime code —
            // a loop generating a constructor expression, not a macro template
        }
    }
}
```

Surface syntax at the call site is `@derive(Clone) struct Point { x: f64, y: f64 }`,
resolving via the registration `@derive(Clone)` attaches to `derive_clone`'s own
declaration above. Closed-list ergonomics today — the standard library provides and
registers the initial derivable set (§2) — with an open path to user-defined derivable
aspects later: a third party registers its own aspect the same way, with no syntax
change required when that lands.

---

## 2. Derivable Aspects (initial standard-library set)

| Aspect | Behaviour |
|---|---|
| `Eq` | Field-by-field equality |
| `Ord` / `Comparable` | Lexicographic field ordering |
| `Display` | Structural `to_string` (see Open Question 4) |
| `Clone` | Deep field-by-field clone (RFC-0080 §1.3) |
| `Hash` | Structural hash combining all fields |

**`Linear` does not belong on this list.** An earlier revision of this thread's design
(and this RFC's own predecessor, RFC-0012) incorrectly treated `Linear` as
derive-as-codegen alongside `Clone`/`Eq`/`Display`. Per RFC-0089 §2, `Linear` is an
**auto-impl aspect**, structurally identical in category to `Send`/`Sync` (RFC-0080
§3.2's rule) — no `@derive(Linear)` annotation is needed or meaningful; the compiler
grants it automatically to any type with a multiplicity-`1` field. This RFC corrects
that error by omitting `Linear` from the table above.

---

## 3. Alternatives Considered

### Compiler-built-in derive (no comptime, no macro system)

Derive is a closed set of structurally derivable aspects known to the compiler, with no
user extensibility. Its own original call-site syntax, `@derive(Aspect, ...)`, is in
fact the syntax adopted here — just resolving through the comptime registration
mechanism above rather than a hardcoded compiler list.

### Attribute macros (procedural macros)

`@derive(Aspect)` expands to an `impl` block generated by a macro associated with
`Aspect` — Rust's model. Fully extensible, but procedural macros are notoriously
complex to write and maintain, and require a full macro system (token streams, hygiene)
as a prerequisite. This RFC reaches the same extensibility by running ordinary staged
code over reflected values instead of syntax — while keeping this alternative's own
`@derive(Aspect)` call-site spelling, since nothing about its con (macro complexity) was
actually about that syntax.

### Derive as a language keyword (`derives`), closed

Derive expressed with a `derives` keyword rather than the `@` attribute system:

```metel
struct Point derives Eq, Ord, Display { x: Float, y: Float }
```

Ergonomic and self-contained, but does not scale to user-defined derivable aspects.
**Not adopted, at the mechanism level or the syntax level.** `derives`'s only stated
con (no extensibility) is exactly what §1's comptime registration mechanism solves, so
its syntax could in principle ride along on top of that mechanism — but `derives` as a
trailing clause crowds a struct's declaration line (competing for space with generic
parameters and row-conditional bounds before the opening brace) in a way
`@derive(Aspect, ...)` as a leading attribute does not, and `@derive(...)` is closer to
what Rust users already expect. `derives` is therefore dropped, not merely superseded
by something that happens to look the same.

### `#[...]` Rust-style attributes

Familiar to Rust programmers but visually ambiguous with comments (`#`). Rejected in
favour of `@` (RFC-0095). The final adopted form, `@derive(Clone)`, ends up
structurally close to `#[derive(Clone)]`, differing only in the sigil, not the overall
shape — the objection was always to `#` specifically, not to attaching derive
information via an attribute-like form.

---

## Open Questions

1. **`emit` soundness.** Does ordinary orphan-rule/coherence checking (RFC-0060) apply
   unchanged to an impl emitted by comptime code? Can a comptime function emit an impl
   for a type it does not own (e.g. a third-party library deriving an aspect for a
   stdlib type)? This is the crux of this RFC's soundness and needs its own worked
   examples before the mechanism can be specified precisely. (Inherited from RFC-0092's
   Open Question 2, specific to derive's use of `emit`.)

2. **Registration coherence for `@derive(Aspect)`.** Can two different comptime
   functions both carry `@derive(Clone)`? An orphan-rule-shaped question, sibling to
   Open Question 1's `emit`-soundness question. Most likely resolution is a hard
   compile error on conflicting registration, matching RFC-0060's coherence discipline
   for impls, but this is asserted, not specified.

3. **Who may register for a given aspect.** Can any library register `@derive(Clone)`
   for the stdlib's own `Clone`, or only `Clone`'s defining module — the same
   orphan-rule question RFC-0060 already answers for impls, now needed for derive
   *registration* specifically.

4. **Required signature shape.** A function tagged `@derive(Aspect)` presumably must
   match a fixed signature (`comptime fun(comptime T: type)`, or a variant accepting
   configuration per Open Question 5) — checked by the compiler, the way Rust's
   `#[proc_macro_derive]` functions must match a fixed `TokenStream -> TokenStream`
   shape. Not yet specified.

5. **`@derive(Aspect(...))` arguments vs. separate `@` attributes for derive
   configuration.** Should a derive function's own configuration (e.g. a rename
   convention for every field at once) travel as arguments nested inside `@derive(...)`
   itself (`@derive(Serialize(rename_all = "camelCase"))`), or always as separate
   per-field/per-type `@` attributes read via `typeinfo` (RFC-0095 §"Attributes as
   comptime-visible metadata")? Rust uses the latter pattern exclusively; both are
   coherent, and this RFC does not yet pick one. Connects directly to Open Question 4
   (the registered function's signature would need to accept whichever form is
   chosen).

6. **`Display` vs `From` for string conversion.** `print` currently only accepts
   `String`. When aspects land, `print` should accept any type with a string
   representation. The question is which aspect owns that conversion:
   - A `Display` aspect (`fun to_string(self) -> String`) implemented by the source
     type — the natural direction for user-defined types.
   - `String` implementing `From<T>` for each printable type — consistent with the
     `from` pattern but puts the responsibility on `String`, which cannot know about
     user-defined types without open dispatch.
   These serve different purposes and should likely remain separate aspects. Resolve
   before finalising the `print` signature.

---

## Timing Recommendation

Deferred to **v0.5+**, alongside RFC-0092. `@derive(Clone)`'s registration function
(RFC-0080's `derive_clone`) cannot be written until RFC-0092's `type`-as-value and
`typeinfo` exist.

---

## References

- RFC-0092 (Comptime Core) — `type`-as-value, `typeinfo`, single-declaration `emit`
  this RFC's registration mechanism is built from
- RFC-0080 (Standard Library Aspects) — `Clone`'s derive is the concrete first test
  case; its `@derive(Clone)` example depends on this RFC
- RFC-0089 (Linear Types) — §2's correction (`Linear` is auto-impl, not derive-as-
  codegen)
- RFC-0096 (Auto-Impl Aspects, draft) — owns the auto-impl category (§2) this RFC
  deliberately excludes `Linear`/`Send`/`Sync` from
- RFC-0090 (Structural Records) — `ToRecord`/`FromRecord`'s auto-derive convenience
  depends on this RFC, though the aspects themselves do not
- RFC-0060 (Aspect Impl Coherence) — coherence/orphan rules Open Questions 1-3 depend
  on
- RFC-0095 (Attributes and Metadata) — Open Question 5's alternative configuration
  mechanism
- RFC-0011 (Operator Overloading) — `Eq`/`Ord` derive depends on operator aspects
- Prior art: Rust `#[derive(...)]` and `#[proc_macro_derive(...)]`

---

## Decision

**Outcome:** *(pending)*
**Target:** v0.5+

*(Decision rationale goes here when the RFC is evaluated.)*
