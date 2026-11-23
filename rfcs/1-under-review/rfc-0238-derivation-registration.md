---
id: rfc-0238
title: "Derivation Registration"
date: '2026-11-16'
status: under-review
updated: '2026-11-22'
tracking: 'https://github.com/metel-lang/metel-core/issues/2158'
---

> **Status — under review (2026-11-22).** Taken to review as part of the metel-core v0.17.0 plan (#2158)

## Summary

An aspect becomes derivable by implementing the std aspect `Derivable` for itself. `derives A(args)` then resolves through that
impl: the clause's arguments are the impl's `Args`, and its `derive` function emits the impl of `A` for the declaration:

```metel
aspect Serialize { fun serialize(&self) -> String; }

extend Serialize: Derivable {
    type Args = .{ .rename_all: String = "none" };
    comptime fun derive(Target: type, args: Self::Args) -> Decl {
        // reads typeinfo(Target), emits one `extend Target: Serialize { .. }`
    }
}

struct User derives Serialize(rename_all: "camel") { name: String, age: i64 }
```

`derivable` stops being a property that only std aspects can have. `derives A` is legal exactly when `A: Derivable`, and who may
provide the impl is decided by the orphan rule, so a library makes its own aspect derivable and nothing else can. Std's `Clone` and
`Copy` are written the same way, with a field-wise combinator the compiler provides until comptime can run it.

This is a design draft. Nothing here is accepted. It depends on RFC-0227 (derivation arguments), RFC-0237 (aspects as comptime
values) and on comptime (RFC-0092, RFC-0132). When accepted it supersedes the registration half of RFC-0093; the request half is the
`derives` clause (RFC-0207), already implemented.

---

## Motivation

1. **A user's aspect cannot be derived.** `derivable` is a marker the compiler reads by identity, and only std aspects may carry it
   (RFC-0212). The derivations of `Clone` and `Copy` are compiler code, so there is nowhere for a user aspect to say how it is
   derived.
2. **RFC-0093's registration is a function attribute.** `#derive(Aspect)` on a `comptime fun` lets any function claim to be an
   aspect's deriver. Its own questions 2 and 3 ask who may register and what happens when two do. An impl of an aspect for the
   aspect answers both with the rule the language already has.
3. **`via` was one argument to one derivation.** RFC-0227 turns the clause into a call with arguments. A derivation needs a
   signature for those arguments to be checked against, and the signature of a user's is its impl's `Args`.

---

## Proposal

### 1. The `Derivable` aspect

```metel
pub aspect Derivable for Aspect {
    type Args;
    comptime fun derive(Target: type, args: Self::Args) -> Decl;
}
```

`Self` is an aspect (RFC-0237 section 3). `Decl` is the comptime value of one declaration (RFC-0092 section 3), here an impl.
`Args` is the type of the clause's arguments, a row (RFC-0151, RFC-0223): positional arguments are numeric labels (`.0`, `.1`),
keyword arguments are named labels, and a field with a default makes its argument optional.

### 2. Resolution

For `struct T derives A(a, b: c)`:
1. Find the impl of `Derivable` for `A`. None: `A` has no derivation and the clause is an error ("`A` is not derivable").
2. Check the clause's arguments against `<A as Derivable>::Args`, as a call's arguments are checked against a parameter row.
3. Run `derive(T, args)` at comptime. The result must be one impl declaration; see section 4.
4. The declaration is added to the program as an ordinary impl.

The mark after the aspect name (RFC-0244) decides the `Flow` parameters:
- a bare entry gives every `Flow` parameter the **empty** flow, which holds for every argument and is an error if a field's
  aspect depends on a type parameter (the fix-it names `?`);
- `?` gives every `Flow` parameter the flow the compiler **computes** from the fields (RFC-0227), and is an error on a derivation
  with no `Flow` parameter;
- a parameter of another type takes its default under both forms (`rename_all: String = "none"`), and a field with no default makes
  the clause an error ("`A` requires arguments").

A derivation whose `Args` is the empty row accepts none. The deriver does not see impls (section 5): a conditional derivation emits
bounds on the parameters of its flow, and the ordinary checks decide. `?` does not make a derivation fallible, so no
failure-tolerant counterpart of `derive` is needed.

### 3. The field-wise combinator and std

Std provides, in comptime Metel, a combinator for field-wise derivations, and its `Derivable` impls use it:

```metel
extend Clone: Derivable {
    type Args = Flow;                                 // a flow of any width
    comptime fun derive(Target: type, args: Self::Args) -> Decl { field_wise(Clone, Target, args) }
}
```

`Flow` is the type of a row of positional type parameters of `Target` of any width (`(T, U)` is `.{ .0 = T, .1 = U }`; row
polymorphism is RFC-0125's). A parameter of type `Flow` is the one the `pub` rule of
RFC-0227 applies to: a `pub` generic type must state it, unless the computed flow is empty. Other parameters (`rename_all`) are
ordinary. Until comptime runs this code, the compiler provides the two impls natively with the same signature (the state of RFC-0227).

### 4. The emitted impl is an ordinary impl

A deriver is trusted with nothing. The declaration it returns:
- is an impl of `A` and of no other aspect, for `Target` and for no other type;
- is checked as a written impl is (coherence, the orphan rule, bounds, completeness);
- overlaps a written impl of `A` for `Target` as any two impls do (`T0015`).

A deriver that emits anything else is an error at the clause. So a deriver cannot add impls of other aspects, for other types, or
free items; RFC-0094 generalises `emit` and is not assumed.

### 5. What a deriver sees

A deriver receives `Target` and its arguments and may call `typeinfo(Target)` (RFC-0092 section 2). It does not see impls: it cannot
ask whether a field type implements `Clone`, because it emits the bounds and the ordinary checks decide. This keeps derivation
independent of the order of impls and rules out cycles (a deriver whose result depends on an impl it is itself deriving).

### 6. Who may provide a derivation

`extend A: Derivable` is an impl whose subject is the aspect `A`, so the orphan rule (RFC-0060, RFC-0237 section 3) allows it in `A`'s
crate and in `Derivable`'s (std). One impl per aspect value: two are `T0015`. A third party cannot make std's `Clone` derivable in a
different way, and cannot make its own aspect derivable for someone else's type in the sense of this RFC, since the derivation is a
property of the aspect.

### 7. The `derivable` property

The `derivable` property of an aspect declaration (RFC-0212) is replaced by the impl: `derives A` is legal exactly when `A: Derivable`.
The other properties (`declared`, `implicit`, `auto`) are unchanged and stay std-only. Std's `derivable` marks on `Clone` and `Copy`
become the impls of section 3.

---

## Interaction with other work

- **RFC-0227** (under review): defines the clause arguments and the built-in flow; this RFC makes the signature a user's to declare.
- **RFC-0244** (implemented): a bare entry is unconditional and `?` computes the flow; section 2 applies those marks to a derivation's
  `Flow` parameters.
- **RFC-0237** (draft): aspects as comptime values, and `Self` of kind `Aspect`. A prerequisite.
- **RFC-0234** (under review): the `derived` mark (RFC-0235) is an obligation to derive another aspect and is independent of registration. Opening
  it to user aspects (RFC-0213 question 9) is no longer a generation question; whether to open it is question 1 below.
- **RFC-0093** (under review): superseded in its registration half when this RFC is accepted. Its questions 1 to 5 are answered by
  sections 4 and 6 (orphan, coherence, who may register, the signature, the arguments); question 7 by section 7; question 8 by the
  `Flow` type; question 9 is question 2 below.
- **RFC-0212** (implemented): the `derivable` property is replaced (section 7).
- **RFC-0092, RFC-0132** (under review): the comptime execution model, `typeinfo` and `emit` this relies on.
- **RFC-0236** (draft): section 5 of that RFC lets the impl be written in the aspect's declaration.
- **RFC-0095** (attributes as comptime-visible metadata): per-field configuration (`#skip`, `#rename`) is read by the deriver through
  `typeinfo`, and type-level configuration travels as arguments. Both are kept.

---

## Alternatives considered

1. **Function-side registration (RFC-0093's `#derive(Aspect)`).** A function names the aspect it derives. Reopens who may register and
   what two registrations mean.
2. **Aspect-side name** (`derivable aspect Foo = derive_foo`). Sound and needs no aspect values, but it is a new binding form and the
   arguments' signature has no natural home; the impl gives both one.
3. **Keep `derivable` a std-only marker.** Leaves user aspects underivable and the compiler's derivations opaque.
4. **Let a deriver emit several declarations.** RFC-0094's generalisation; not assumed, and it widens what a derive may do.

---

## Costs

- A deriver is comptime code, so the feature waits on comptime. The clause arguments (RFC-0227) do not.
- `Derivable` makes `Self` of kind `Aspect` real, which is RFC-0237's cost.
- Two representations of std's derivations (native now, Metel later) must agree until the native one is retired.

---

## Open questions

1. **Open the `derived` mark to user aspects?** With generation gone (RFC-0234) the mark is an obligation to derive another aspect,
   which is safe for user aspects. Does this RFC enable it, or leave it std-only?
2. **Template derivations.** RFC-0222's `derives Builder` makes a struct's row visible to a row template and emits no impl. Is `Builder`
   a `Derivable` whose `derive` returns a non-impl declaration, or a separate derivation form?
3. **May a deriver ask about impls?** Section 5 says no. A derivation that depends on whether a field type has an aspect (for example
   to choose a strategy) cannot be written. Is the restriction acceptable?
4. **The `Decl` type.** Section 1 uses RFC-0092's single-declaration `emit`; whether a deriver returns a `Decl` or calls `emit` is a
   comptime detail this RFC does not fix.
5. **Several impls from one derive.** A derivation that needs a helper impl (an aspect and its super-aspect) cannot emit two. RFC-0234's
   obligation makes the user list both aspects, which covers `Copy` and `Clone`; is that enough?

---

## Decision

**Outcome:** *(pending)*
