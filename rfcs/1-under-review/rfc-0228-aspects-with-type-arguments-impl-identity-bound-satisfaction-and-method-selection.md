---
id: rfc-0228
title: "Aspects with type arguments: impl identity, bound satisfaction and method selection"
date: '2026-11-13'
status: under-review
updated: '2026-11-13'
tracking: 'https://github.com/metel-lang/metel-core/issues/2001'
---

> **Status — under review.** Design settlement is in Function types (metel-core#2001).
> Instantiated aspect identities are part of the callable contract, and aspect-object dispatch is tracked by metel-core#2062.

> **Brought in line with the compiler (2026-11-16).** Most of this RFC is implemented (impl identity and its coherence,
> bound satisfaction by argument list, selection through a bound, `T0013` for every call with no unique target; spec text in
> metel-docs#625). Remaining work includes deferred expected-type selection (section 3.2, metel-core#2018),
> a negative impl removing one identity (section 1.3, #2061), a `dyn` object choosing the impl of its own
> identity (section 4, #2062), and a projection resolving in the impl a bound names (section 1.4, #2063).

## Summary

An aspect may take type arguments (`Conv<T>`, `From<T>`), and a type may implement it for several argument lists at once.
The spec says so in prose (the associated-types section: "use a type parameter on the aspect itself when a type may
implement it for multiple type arguments simultaneously") but leaves four things unstated, and the compiler answers
each of them wrongly or by accident:

1. **What an impl is, for coherence.** The coherence section says "every `(aspect, type)` pair has at most one
   implementation", which contradicts the prose above unless "aspect" includes its arguments.
2. **When a bound that names arguments is satisfied.** `X: Conv<i64>` is satisfied by an impl of `Conv<String>`
   (metel-core#1984, fixed in the compiler ahead of this RFC because it returned a `String` typed as `i64`).
3. **How a method call chooses among several impls.** The registry keeps one method per `(type, method name)`, so a
   second impl of the same aspect for the same type silently replaces the first, and a call through a bound can run the
   wrong impl (metel-core#1987).
4. **Which error says so.**

```metel
aspect Conv<T> { fun conv(&self) -> T; }
struct L { n: i64 }
extend L: Conv<i64> { fun conv(&self) -> i64 { self.n } }
extend L: Conv<String> { fun conv(&self) -> String { "s" } }     // legal: a different aspect identity

fun as_int<X: Conv<i64>>(x: &X) -> i64 { x.conv() }              // calls the Conv<i64> impl
fun as_text<X: Conv<String>>(x: &X) -> String { x.conv() }       // calls the Conv<String> impl

fun main() {
    let l := L { n = 4 };
    let a := as_int(&l);          // picks Conv<i64> through the bound
    let b := as_text(&l);         // picks Conv<String> through the bound
    let c: i64 := l.conv();       // T0013: multiple impls match the direct call
}
```

---

## Motivation

The compiler already records an aspect's type arguments per impl (`impl_aspect_env`) and the spec's own text allows
several impls per type, so the feature exists; its rules do not. Three defects came out of one afternoon of work on
block-local impls (metel-core#1979) and each is the same missing sentence:

- `L: Conv<String>` satisfied `X: Conv<i64>` (#1984): the bound check compared the aspect's name only.
- `extend L: Conv<i64>` followed by `extend L: Conv<String>` made `l.conv()` a type error for the first impl
  (`cannot unify String with i64`): the method table is keyed by `(type, name)` (#1987).
- Two functions bounded `Conv<i64>` and `Conv<String>` both ran the same impl (#1987).

---

## 1. Impl identity

The identity of an implementation is the aspect **together with its type arguments**: `Conv<i64>` and `Conv<String>`
are two aspects as far as coherence is concerned. The coherence rules apply per identity.

1. Two impls of the same aspect with arguments that can be equal for some instantiation, for the same target, overlap
   and are `T0015`, as two impls of one argument-less aspect do. `extend L: Conv<i64>` twice is `T0015`;
   `extend L: Conv<i64>` and `extend L: Conv<String>` are not.
2. The orphan rule looks at the aspect's declaring module and the target's outermost constructor, as before. The type
   arguments do not count towards locality: `extend i64: Conv<MyType>` is not allowed in a module that declares only
   `MyType` unless it also declares `Conv`.
3. An explicit negative impl `extend L: !Conv<i64>` removes the identity `Conv<i64>` for `L`, not `Conv<String>`.
   *Not yet:* the compiler keys a negative impl by the aspect's name, so `extend L: !Conv<String>` removes `Conv<i64>`
   as well and `L: Conv<i64>` then fails with `T0012` (metel-core#2061).
4. An associated type an impl binds belongs to that impl's identity: `L: Source<A>` and `L: Source<B>` may bind
   different associated types, and a projection through a bound resolves in the impl the bound names (section 2).
   *Not yet:* two impls of one aspect may bind different associated types, but a projection `X::Item` through
   `X: Source<i64>` is left unresolved when the type has both (`T0001`, metel-core#2063).

## 2. Bound satisfaction

A bound `T: A<X1, .., Xn>` is satisfied by a concrete type exactly when it has an implementation whose identity is
`A<X1, .., Xn>`, the arguments compared after substituting the call's type arguments. A type whose only impls of `A`
have other arguments does not satisfy it: `T0012`, naming the arguments the type does implement
(`` `L` does not implement `Conv<i64>`; it implements Conv<String>``).

- The rule holds at a call, at a construction, for an inline bound and a `where` bound, for a bound inherited through a
  forwarded bound, and for a function imported from another module.
- A type whose `A` is provided by a conditional or blanket impl, or by the compiler, satisfies the bound by that impl's
  own conditions; this section adds nothing there.
- Determine an aspect argument such as `U` in `X: Conv<U>` through ordinary type inference or an
  explicit type argument. Then check whether `X` satisfies `Conv<U>`. If `U` is still unresolved,
  the call reports `T0002`, even when `X` has exactly one `Conv` implementation. Adding another
  implementation cannot change the inference for `U`.

## 3. Method selection

A method call selects an implementation, never the last one registered.

1. **Through a bound.** For `x: T` with `T: A<X>`, `x.m()` calls the method of the impl `A<X>` of the type `T` is
   instantiated with. The choice is static and has no ambiguity: the bound names the arguments. A type parameter with
   *two* bounds of the aspect (`X: Conv<i64> + Conv<String>`) is the exception: `x.conv()` names no arguments, so it is
   `T0013` ("this type parameter has more than one bound of `Conv`, and each provides `conv`; the call names no type
   arguments to choose between them").
2. **Directly.** A direct call on a concrete receiver reports `T0013` when multiple implementations provide
   a matching method. An expected result type does not resolve the ambiguity in v0.17.0. The diagnostic
   identifies the competing identities and can suggest a call through a bound that names the type arguments.
   Multiple implementations for distinct aspect identities remain legal. Expected-type selection needs
   deferred method resolution and is follow-up work tracked by metel-core#2018.
3. `T0013` is the error for every case in which a call has no unique static target: two different aspects defining the
   same method on one receiver, several impls of one aspect called directly, and a parameter with several bounds of one
   aspect (section 3.1).

**Free-function overloads.** Existing overload sets remain available in v0.17.0. A free-function call
selects a candidate through the ordinary argument-binding and overload rules. Expected result type
does not select a free-function overload. The separate audit in metel-core#2112 owns future changes
to that mechanism.

## 4. What this does not change

- `dyn Conv<i64>` and `dyn Conv<String>` are different object types; their vtables are not affected. *Not yet for a type
  that implements both:* the coercion to either object picks the last registered impl, so a call through
  `dyn Conv<i64>` can run the `Conv<String>` impl (metel-core#2062).
- An aspect without type arguments behaves as before: its identity is its name.
- RFC-0259 owns the syntax for explicit aspect-qualified calls. A bound naming the instantiated
  aspect already supplies an explicit identity for selection through a generic function.

---

## Alternatives considered

- **Forbid a second impl of one aspect for a type** (the `Deref` model, where one type has one target). Simplest, and
  right for `Deref`, but it removes `From<A>` and `From<B>` on one type, which the associated-types section names as
  the reason to give an aspect a type parameter.
- **Select among multiple direct candidates by expected type.** This would allow an annotated call to
  choose an implementation by its result type. It needs a deferred goal over an inference variable,
  tracked separately in metel-core#2018.
- **Select by explicit qualification.** RFC-0259 covers naming an impl identity directly at the call.
- **Last impl wins** (today). Order-dependent and silently wrong; the coherence section rejects it elsewhere.

## Relationship to existing RFCs

RFC-0060 (coherence) states the rules this one applies per identity. RFC-0082 (associated types) states the prose this
makes normative and the equality-bound syntax (`A<Item = X>`) that composes with section 2. RFC-0040 (bound
enforcement) and RFC-0036 (conditional impls) own the call-site check and the conditional case that section 2 leaves
alone. RFC-0072 and RFC-0081 own negative bounds and negative impls (section 1.3). RFC-0128 (exportable overload sets) and
`spec.functions.keyword-arguments.legality-5` continue to govern free-function overloading.

## Design resolutions

1. **Staging of section 3.2.** Resolved for v0.17.0. Keep multiple identities and bound-directed dispatch.
   Ambiguous direct calls report `T0013` even with an annotation. Expected-type selection is deferred to
   metel-core#2018.
2. **Locality of arguments (1.2).** Resolved for v0.17.0. The aspect or the target's outermost type
   constructor must be declared in the implementing module. An aspect argument contributes to impl
   identity only. Any extension to the orphan rule can be considered with the package system.
3. **A qualified call form.** Deferred to RFC-0259, which owns the syntax and its interaction
   with receiver passing and path lookup. For this release, a helper with the desired aspect
   bound selects the implementation.
4. **Free argument in a bound (2).** Resolved for v0.17.0. Ordinary inference or explicit arguments
   determine the aspect argument before impl lookup. An unresolved argument reports `T0002`.

5. **Free-function overloading.** Resolved for v0.17.0. Existing overload sets remain available.
   Any change to this language mechanism goes through the separate overload audit (metel-core#2112).

---

## Decision

**Outcome:** *(pending)*
