---
id: rfc-0228
title: "Aspects with type arguments: impl identity, bound satisfaction and method selection"
date: '2026-11-13'
status: draft
---

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
    let a: i64 := l.conv();       // chosen by the expected type
    let b: String := l.conv();
    let c := l.conv();            // error: ambiguous
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
4. An associated type an impl binds belongs to that impl's identity: `L: Source<A>` and `L: Source<B>` may bind
   different associated types, and a projection through a bound resolves in the impl the bound names (section 2).

## 2. Bound satisfaction

A bound `T: A<X1, .., Xn>` is satisfied by a concrete type exactly when it has an implementation whose identity is
`A<X1, .., Xn>`, the arguments compared after substituting the call's type arguments. A type whose only impls of `A`
have other arguments does not satisfy it: `T0012`, naming the arguments the type does implement
(`` `L` does not implement `Conv<i64>`; it implements Conv<String>``).

- The rule holds at a call, at a construction, for an inline bound and a `where` bound, for a bound inherited through a
  forwarded bound, and for a function imported from another module.
- A type whose `A` is provided by a conditional or blanket impl, or by the compiler, satisfies the bound by that impl's
  own conditions; this section adds nothing there.
- An argument that is still a free type parameter of the callee (`X: Conv<U>`, `U` bound by nothing else) is fixed by
  the impl when the type has exactly one impl of `A`; with several the call is ambiguous (`T0013`, below).

## 3. Method selection

A method call selects an implementation, never the last one registered.

1. **Through a bound.** For `x: T` with `T: A<X>`, `x.m()` calls the method of the impl `A<X>` of the type `T` is
   instantiated with. The choice is static and has no ambiguity: the bound names the arguments.
2. **Directly.** `l.m()` on a concrete receiver may have several candidates: impls of one aspect for different
   arguments, or of different aspects, that each provide `m` for the receiver. The call is resolved by its **expected
   type**: the candidate whose signature admits the types the call is used at (the annotated binding, the parameter it
   is passed to, the return position). Exactly one admissible candidate is chosen; none admissible is `T0012`, naming the
   candidates; several admissible is `T0013`, suggesting an annotation. An unannotated `let c := l.conv()` therefore
   stays an error while two candidates exist.
3. `T0013`, today the error for two different aspects defining the same method on one receiver, is the error for every
   case in which a call has no unique static target, including several impls of one aspect.

## 4. What this does not change

- `dyn Conv<i64>` and `dyn Conv<String>` are different object types; their vtables are not affected.
- An aspect without type arguments behaves as before: its identity is its name.
- A call syntax that names the impl explicitly is not introduced here (open question 3).

---

## Alternatives considered

- **Forbid a second impl of one aspect for a type** (the `Deref` model, where one type has one target). Simplest, and
  right for `Deref`, but it removes `From<A>` and `From<B>` on one type, which the associated-types section names as
  the reason to give an aspect a type parameter.
- **Select only by explicit qualification.** Always rejects an ambiguous call and needs surface syntax to select. It
  stays available as a later addition (section 4); it does not replace selection by expected type, which the owner
  decided for the common annotated call (2026-11-13).
- **Last impl wins** (today). Order-dependent and silently wrong; the coherence section rejects it elsewhere.

## Relationship to existing RFCs

RFC-0060 (coherence) states the rules this one applies per identity. RFC-0082 (associated types) states the prose this
makes normative and the equality-bound syntax (`A<Item = X>`) that composes with section 2. RFC-0040 (bound
enforcement) and RFC-0036 (conditional impls) own the call-site check and the conditional case that section 2 leaves
alone. RFC-0072 and RFC-0081 own negative bounds and negative impls (section 1.3).

## Open questions

1. **Staging of section 3.2.** Choosing among candidates by expected type needs the call's type, which inference only
   knows after unification, so it needs a deferred goal over an inference variable; the obligation solver of
   metel-core#1813 is for ownership goals and is not that mechanism. Until it exists a direct call with several
   candidates is `T0013` whether or not it is annotated, and section 3.2's resolution takes effect with the mechanism.
   Is that staging acceptable, or should the first release restrict section 1.1 to one impl per aspect and type?
2. **Locality of arguments (1.2).** Rust counts a trait's type arguments towards locality: `impl From<MyType> for i64` is
   legal in a crate that owns only `MyType`, which is how a crate converts its own types into foreign ones. Section 1.2
   says arguments do not count, the stricter choice, under which `extend i64: Conv<MyType>` needs `Conv` to be local.
   The cost is that a module cannot write a conversion from its own type into a foreign type for a foreign aspect; the
   benefit is that coherence stays decidable from the aspect and the target alone, and no other module's impls need to
   be consulted (the property the coherence section builds on). Should a local type argument make an impl local? If so
   the orphan rule needs a fundamental-type story (what `&MyType` or `List<MyType>` count as), which Rust spent several
   RFCs on. Revisit with the package system.
3. **A qualified call form.** Rust selects an impl explicitly with `<L as Conv<i64>>::conv(&l)`, always available, so an
   ambiguous call has an escape that needs no annotation (for example a call whose result is discarded, or a generic
   position the expected type cannot reach). Section 4 introduces no such form, so under section 3.2 the only way to
   resolve an ambiguous call is a type annotation. Should the RFC add a qualified form (`Conv<i64>::conv(&l)`,
   `l.conv::<Conv<i64>>()`, or a Rust-style `<L as Conv<i64>>::conv(&l)`), or leave it to a later RFC? It needs surface
   syntax, which interacts with RFC-0223's call rules and the path grammar, and the language has no aspect-qualified call today
   (`Show::show(&l)` is `T0003`, unresolved path; a type-qualified `L::show(..)` parses but names no aspect), so the form
   would be new, not an extension.
4. **Free argument in a bound (2).** Whether `X: Conv<U>` with several impls should infer `U` from other constraints
   rather than being ambiguous.

---

## Decision

**Outcome:** *(pending)*
