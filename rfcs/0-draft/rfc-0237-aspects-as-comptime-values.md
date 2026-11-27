---
id: rfc-0237
title: "Aspects as Comptime Values"
date: '2026-11-16'
status: draft
---

## Summary

An aspect, with or without its arguments, is a comptime value of a new kind, `Aspect`, as a type is a comptime value of kind `type`
(RFC-0092 section 1). Three things follow, and this RFC is only these three:

1. **A value.** `Clone`, `Display` and `Conv<i64>` are values of kind `Aspect`. They can be bound by `comptime let`, passed to a
   `comptime fun`, returned from one, and compared.
2. **A parameter.** A comptime parameter may have kind `Aspect`, and a bound may name it: `comptime fun derive_all<A: Aspect, T>(..)
   where T: A`.
3. **A Self.** An aspect may declare that its `Self` is an aspect and not a type, so that an aspect can be the subject of an impl:

```metel
aspect Derivable for Aspect {                       // Self is an aspect (strawman spelling, open question 1)
    type Args;
    comptime fun derive(Target: type, args: Self::Args) -> Decl;
}
extend Serialize: Derivable { .. }                  // the impl's subject is the aspect Serialize
```

The third is the one RFC-0238 (derivation registration) needs; the first two are what make it usable. Aspects remain compile-time
entities: there is no runtime value of kind `Aspect`, no `dyn Aspect` of an aspect, and no general higher-kinded type system.

This is a design draft. Nothing here is accepted, and it waits on comptime (RFC-0092, RFC-0132), which is itself under review.

---

## Motivation

1. **Registration is an impl of an aspect for an aspect.** RFC-0238 puts a type's derivation in `extend Foo: Derivable { .. }`.
   That needs `Foo` to be able to stand where a type stands in an impl. Without it, registration needs a new property or a function
   attribute, which brings back the orphan and ownership questions RFC-0093 listed (questions 2 and 3).
2. **Comptime code needs to talk about aspects.** RFC-0055 sketched `comptime has_aspect(T, Aspect)` and RFC-0093 answered its
   question with a registration instead, so the query is still unspecified. A derivation combinator that is generic over the aspect
   it derives (`field_wise(Clone, T, ..)`) needs an aspect it can pass.
3. **`type` is already a value.** RFC-0092 section 1 makes a type an ordinary comptime value. An aspect is the next thing a
   comptime function wants to name, and treating it differently from a type would be an exception to a rule the rest of the
   comptime design states once.

---

## Proposal

### 1. The kind `Aspect`

`Aspect` is a kind, written as a type of a comptime value (`A: Aspect`). Its values are aspect expressions:

- a bare aspect name (`Clone`), resolved by name resolution as a type name is;
- an aspect applied to type arguments (`Conv<i64>`, RFC-0228), a different value from `Conv<String>`;
- nothing else: negative entries (`!Send`) are not aspect values, since they are clauses of a bound and not aspects.

Two aspect values are equal when they name the same aspect declaration with equal arguments, as types are.

### 2. Aspect parameters and bounds

A `comptime` parameter may have kind `Aspect`. An aspect value may stand where an aspect name stands in a bound:

```metel
comptime fun implements(T: type, A: Aspect) -> boolean;                 // does T satisfy A? (std)
comptime fun field_wise(A: Aspect, Target: type, flow: Flow) -> Decl;   // a derivation generic over its aspect (RFC-0238)
fun need<T, comptime A: Aspect>(x: T) where T: A { .. }
```

The bound is checked at the point the aspect value is known, which is at the call of the comptime function that supplies it. A
bound on an aspect parameter is treated as an ordinary bound at every instantiation, and RFC-0092's rule that bounds are checked
at the definition (not deferred to the instantiation) holds for every bound whose aspect is not a parameter.

### 3. Aspects as the `Self` of an impl

An aspect declaration states the kind of its `Self`. The default is `type`, which is every aspect today. A *meta-aspect* has
`Self` of kind `Aspect`. An impl of a meta-aspect names an aspect as its subject:

```metel
extend Clone: Derivable { .. }          // the subject is the aspect Clone
```

The rules of impls apply unchanged with one observation: the subject is an aspect declaration, so it is *local* when that aspect
is declared in the current crate. RFC-0060's orphan rule then says an impl of a meta-aspect is allowed where the meta-aspect is
declared or where the subject aspect is declared, which is what registration needs.

- **Coherence.** Two impls of one meta-aspect for the same aspect value overlap (`T0015`). Impls for different arguments are
  different subjects.
- **Blanket impls over `Aspect`** (`extend<A: Aspect> A: M`) are not allowed in v1 (open question 3).
- **The `Self` kind is part of the aspect's declaration.** An aspect of `Self` kind `type` cannot be implemented for an aspect and
  the reverse.

### 4. What aspect values are not

- Not runtime values: a `comptime` binding, parameter or return type only.
- Not types: an aspect value cannot appear where a type is expected, and a type cannot appear where an aspect is.
- Not a way to abstract over the aspect of a *dyn* object: `dyn A` with `A` a comptime variable is not introduced.
- Not general kind polymorphism. `Aspect` is the one new kind, beside the existing ones (`type`, `row`, `record`, RFC-0121).

### 5. Staging

Aspect values exist at comptime only. Name resolution turns an aspect name into a value before comptime evaluation of anything
that uses it; the impls of a meta-aspect are collected with the ordinary impls, before any comptime function that looks them up
runs. This is the ordering RFC-0132 gives `typeinfo` and impl lookup.

---

## Interaction with other work

- **RFC-0092, RFC-0132** (under review): `Aspect` is a second comptime kind beside `type`. This RFC does not change their execution
  model.
- **RFC-0238** (draft): the only consumer in this release; its `Derivable` is a meta-aspect.
- **RFC-0236** (draft): its stage 2 puts a meta-aspect impl in an aspect's own declaration. It needs section 3.
- **RFC-0228** (under review): aspects with type arguments give `Conv<i64>` its identity, which section 1 uses for equality.
- **RFC-0060** (coherence): section 3's orphan rule is an application of it.
- **RFC-0055** (superseded): its `has_aspect` sketch is `implements` above.
- **RFC-0125, RFC-0121**: variadic generics and row kinds are separate; an `Args` row of unknown width in RFC-0238 uses them.

---

## Alternatives considered

1. **A property or attribute on the aspect instead of an impl.** `derivable aspect Foo = derive_foo` (the aspect names its derivation)
   or `#derive(Foo)` on a function (RFC-0093). Both need no aspect values, but each is a new mechanism for a binding an impl already
   expresses, and the function-side form reopens the orphan question.
2. **Aspects as types** (`Aspect` a type whose values are aspects, with `extend` over it). Gives a runtime story the design does not
   want, and puts aspect values where types may appear.
3. **General higher-kinded types.** A much larger commitment; one kind is enough for registration.

---

## Open questions

1. **How an aspect states the kind of its `Self`.** The draft writes `aspect Derivable for Aspect`. Other options: a bound on
   `Self` (`where Self: Aspect`) or a kind annotation on a generic-like parameter. It should read like the language's existing kinds
   (`row R`, RFC-0121).
2. **Are negative bounds values?** `!Send` is excluded here. Whether code that builds a bound at comptime needs it is open.
3. **Blanket impls over `Aspect`.** `extend<A: Aspect> A: M` would give every aspect a default. Not in v1: it makes registration
   coherence depend on overlap between a blanket impl and a specific one.
4. **Aspects with associated types as values.** `Iterator` has an associated type; is `Iterator` a value, or only `Iterator<Item = i64>`?
   RFC-0228 and RFC-0082 decide.
5. **Does `implements(T, A)` see impls added later?** The comptime evaluation order (section 5) fixes the answer for one crate; across
   crates, RFC-0132's rule applies.

---

## Decision

**Outcome:** *(pending)*
