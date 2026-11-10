---
id: rfc-0224
title: "Ownership class flow for generic types"
date: '2026-11-10'
status: draft
---

## Summary

A generic type states how its ownership class (copy, affine, linear; RFC-0089 section 1) **flows from its type
parameters**, instead of stating a boolean condition on them. The statement is checked against the fields and stored
as the type's interface; a generic body reads it with class arithmetic and never searches for a proof.

```metel
struct Wrapper<T>: Copy via T { value: T }            // Wrapper<X> is Copy exactly when X is
struct Pair<A, B>: Copy via A, B { a: A, b: B }
copy struct View<T> { r: &T }                          // flows from no parameter: Copy for every T
```

`Copy via T` is a placeholder spelling (open question 3). The rest of this RFC is about the behaviour.

This RFC revises one part of RFC-0206. RFC-0206 section 6 plans to answer "is `Wrapper<T>` `Copy` in this generic
body?" with a stored boolean condition (`when`, RFC-0206 end state) produced by an obligation solver (metel-core#1813).
Here the answer is the join of the classes of the parameters the type flows from, which needs no solver for `Copy`. The
price is that a condition which is not about the fields cannot be stated (section 5). It is a design draft. Nothing
here is accepted.

---

## Motivation

### What the new Copy model cannot say

RFC-0206 and RFC-0212 make `Copy` a declared property: it is granted in the declaration (`copy struct`, `derives Copy`),
and the predicate is exact (every field `Copy`, not `Drop`, not `Linear`). `extend X: Copy;` is an error. That removed
two things the old user-written `extend<T: Copy> Wrapper<T>: Copy where ...;` gave:

1. **A stored rule for generic bodies.** A generic body could ask "is `Wrapper<T>` `Copy`?" and get an answer from the
   `extend`. A derived `Copy` has no stored rule, so the abstract analysis answers *undecided*, which is a diagnostic
   (`I0011` today, RFC-0206 section 2 rule 3). `View<T>`, `Pair<Wrapper<T>, i64>` and every other nominal application
   whose copy-ness depends on a parameter are affected.
2. **Conditions narrower than the structure.** `extend<T> Token<T>: Copy where T: Marker, T: Other;` made `Token<T>`
   `Copy` only for chosen `T`, although the fields needed less.

RFC-0206's planned answer to (1) is stored interfaces with an optional `when` clause (RFC-0206 section 6, steps 2 and
3; metel-core#1818, #1813, spike #1815). That answer also covers (2), but it needs a condition language, and a second
conditional keyword beside the struct-level `where` (which constrains the type, not one property of it). Naming and
overlap with `where` were the reason to look for another shape.

### The observation

For ownership classes the condition is not arbitrary. A type's class is the most restrictive class among its fields
(RFC-0089 section 1), so for a generic type it is a **join over parameter classes**. What a use site needs is therefore
not a boolean formula but the set of parameters the class depends on. The rest of this RFC follows from stating that set.

---

## 1. Class flow

**Definition.** For a generic nominal type `N<P1..Pn>`, its *flow set* `F(N) ⊆ {P1..Pn}` is the set of parameters whose
class the type's class depends on. For an instantiation `N<A1..An>`:

```
class(N<A1..An>) = declared class of N, joined with class(Ai) for every Pi in F(N)
```

`join` is the lattice order of RFC-0089 section 1 (`ω` copy, then `affine`, then `1` linear). For `Copy` this reads:
`N<A..>` is `Copy` exactly when `N` is declared `Copy`, every `Ai` with `Pi` in `F(N)` is `Copy`, and the exclusions of
RFC-0206 (not `Drop`, not `Linear`) hold.

**Where the flow is stated.** In the declaration, on the class entry:

```metel
struct Wrapper<T>: Copy via T { value: T }
enum Maybe<T>: Copy via T { None, Some { value: T } }
struct Pair<A, B>: Copy via A, B { a: A, b: B }
copy struct View<T> { r: &T }                 // F = {}, Copy unconditionally
```

An entry with no `via` has an empty flow set. The clause lists parameters only; there is no condition language.

**Legality.**
1. *Sufficient.* The stated flow set must contain every parameter the fields' classes depend on. A field of type `T`,
   `Option<T>`, `(T, i64)` or `Wrapper<T>` depends on `T`; a field of type `&T` does not (a reference is always `Copy`,
   RFC-0206); a field of type `i64` does not. A missing parameter is an error at the field, with the fix-it that adds it.
2. *Never smaller than needed, may be larger.* The stated set may contain parameters the fields do not need. This is the
   same direction as a variance annotation that is more restrictive than the inferred one. `struct Handle<T>: Copy via T
   { id: i64 }` is `Copy` only when `T` is, although no field mentions `T`. It is how a public type pins its interface
   against a later field edit.
3. *Every generic type states it where it is visible.* A `pub` generic type whose class depends on a parameter must state
   the flow (an error with a fix-it otherwise). A non-`pub` type may leave it to the compiler, which computes the
   smallest sufficient set. Open question 2.
4. *Same module.* The flow is part of the declaration, so the orphan rule holds trivially (RFC-0206 section 2 rule 1
   is unchanged).

**The interface.** The stated set (or the computed one for a non-`pub` type) is stored as the type's interface. Use sites
read only the stored interface, never the fields.

---

## 2. Use in generic bodies

A generic body evaluates a copy question by class arithmetic over the stored interface:

```metel
fun twice<T: Copy>(w: Wrapper<T>) -> (Wrapper<T>, Wrapper<T>) {
    (w, w)         // class(Wrapper<T>) = join(class(T)) = copy, because T: Copy. Accepted.
}

fun bad<T>(w: Wrapper<T>) -> (Wrapper<T>, Wrapper<T>) {
    (w, w)         // class(T) is affine, so Wrapper<T> moves. Error: use after move (a definite no, not undecided).
}

fun f<T: Copy>(p: Pair<Wrapper<T>, i64>) -> (Pair<Wrapper<T>, i64>, Pair<Wrapper<T>, i64>) {
    (p, p)         // join(class(Wrapper<T>), copy) = class(T) = copy. Accepted: nested, no solver.
}

fun g<T>(v: View<T>) -> (View<T>, View<T>) {
    (v, v)         // F(View) = {}; always Copy. Accepted, with no bound on T.
}
```

The question is answered for every nominal application whose type arguments are parameters, other nominals, tuples,
references and the other structural kinds, because each has a class function. A question the interface cannot answer
(for example, a field whose class depends on a projection `T.Item`, open question 5) is reported as undecided exactly as
RFC-0206 section 2 rule 3 says; this RFC does not weaken that rule.

**Recursion.** A flow set is a set of parameters, so evaluation over a stored interface terminates by construction.
Computing the set for a recursive declaration is a fixed point over the strongly connected component, as RFC-0206
section 6 ("Recursive declarations") already requires for stored interfaces.

---

## 3. Relationship to `Clone`, `Linear` and the other markers

- **`Clone`.** A `Copy` type has the provided `Clone` (RFC-0206 section 2 rule 2). `Copy via T` gives that `Clone` the
  same flow: `Wrapper<X>: Clone` when `X: Copy`. A type that is `Clone` but not `Copy` keeps `derives Clone`, whose
  condition is computed from `Clone` bounds on parameters (RFC-0207, RFC-0213); this RFC does not change it.
- **`Linear`.** `linear` is the join's top element, so a linear parameter in the flow set makes the type linear without
  `Linear` being a stored fact. RFC-0206 says `Linear` is existential and never stored; class arithmetic computes it per
  instantiation, which is the same statement.
- **`Share`, `Send`, `Sync`, `Discard` and user markers.** Out of scope. They are not classes in the lattice, and they keep
  RFC-0206/RFC-0207/RFC-0212 as written. Whether a flow form should later cover the "every field" markers is open
  question 6.
- **`Drop`.** `Copy` excludes `Drop` as today. A `Drop` type's class is `affine` whatever its parameters are.

---

## 4. Worked examples

```metel
// 1. A container: copy exactly when the element is.
struct Slot<T>: Copy via T { value: T }

// 2. A phantom parameter: no flow, always Copy.
copy struct Tagged<T> { id: i64 }

// 3. A pinned interface: a public type that is Copy only when T is, whatever its fields become.
pub struct Handle<T>: Copy via T { id: i64 }

// 4. Insufficient flow.
struct Bad<A, B>: Copy via A { a: A, b: B }
// error: field `b` has type `B`, whose class is not covered by `Copy via A`.
//        add B: `Copy via A, B`

// 5. A public type that declares Copy and does not say how it flows.
pub struct Wrapper<T>: Copy { value: T }
// error: a public generic type that declares `Copy` and whose copy-ness depends on `T` must state the flow:
//        `: Copy via T`
```

Example 5 is the only case of legality rule 3. A type that declares no `Copy` is affine and has no flow to state
(RFC-0206); `copy struct View<T> { r: &T }` has an empty flow set and needs no clause.

---

## 5. What cannot be said

A `Copy` that depends on something other than the classes of the type's parameters cannot be stated:

```metel
// Not expressible: Copy only when T carries a user marker.
extend<T> Token<T>: Copy where T: Marker;          // error: Copy is granted only in the declaration (RFC-0206 rule 1)
```

The practical routes are a newtype wrapper that is itself `copy`, or putting the marker bound on the functions that use
the type. A bound on the type's own parameter (`struct Token<T: Marker>`) is a different statement: it restricts which
`Token`s exist, not when one is `Copy`.

This is a deliberate narrowing. Whether it is acceptable is the central open question (open question 1).

---

## Alternatives considered

Each of these states the condition as a boolean formula. All of them recover section 5's case; all of them need a
condition language and the sufficiency check that goes with it.

| Alternative | Spelling | Why not (or not first) |
|---|---|---|
| `when` clause | `struct W<T>: Copy when T: Copy` | A second conditional keyword beside the struct-level `where`; confusing next to it. The original RFC-0206 end-state spelling (spike #1815) |
| `if` after the entry | `: Copy if T: Copy` | Reads well, still two conditional words in one header |
| `copy?` with `given` | `copy? struct W<T> given T: Copy` | Clear, but adds `given`, tightens the meaning of `copy` on every generic type, and covers `Copy` only |
| Parenthesised | `: Copy(T: Copy)` | Looks like a call or a construction (RFC-0100, RFC-0114) |
| `extend` in the type's module | `extend<T: Copy> W<T>: Copy;` | Reverses RFC-0206 rule 1 and RFC-0212's `declared`; a second place to say `Copy` |
| `Copy` as a property of the `Clone` impl | conditions only on `Clone` | Inverts RFC-0206's "Copy implies the provided Clone"; least understood |
| Compile-time Boolean | `Copy where comptime(..)` | Waits on comptime, which follows v0.16.0; proving an arbitrary expression sufficient is hard |
| Computed interface only | no syntax | A public interface changes with a field edit; policy narrowing gone as well; solver stays on the critical path |

### Prior art

From a survey (Codex, 2026-11-10); its citations have not been checked individually, and the Mojo and Hylo details it
marks as unverified are marked so here.

- **Swift (SE-0427).** Conditional `Copyable` is restricted to "these of the type's own parameters are `Copyable`";
  arbitrary marker bounds are forbidden, the declaration must be in the same file, and a `deinit` forbids it. Swift
  removed inferred conditional copyability after early users found it confusing. This is the closest precedent for
  stating a flow and not a formula.
- **Rust.** `derive(Clone, Copy)` adds the bound to every type parameter, which over-constrains `PhantomData<T>` and
  references; "perfect derive" proposals use field obligations and struggle with recursion and with private-field
  edits changing a public impl. A manual `impl<T: Copy> Copy for W<T> {}` may be narrower than the fields. Rust checks
  sufficiency, not minimality. Rust allows what section 5 forbids, and it is rarely used for `Copy`.
- **Haskell.** Inferred derived contexts, or standalone deriving with an explicit context that may be narrower; the
  inferred rules are restricted, and exotic explicit contexts need `UndecidableInstances`.
- **Mojo.** Declaration-local `Copyable where conforms_to(T, Copyable)` with an arbitrary compile-time Boolean. How the
  abstract checker establishes an arbitrary implication is unverified.
- **Austral.** A generic type's category (free or linear) follows its arguments, and an explicit declaration may be
  more restrictive than the structure. This is the shape of section 1.
- **Variance annotations (OCaml, Scala).** A checked per-parameter annotation, exported across abstraction, that may be
  more restrictive than the inferred one. The model for legality rule 2.

---

## Relationship to existing RFCs

- **RFC-0206** (accepted, integrated). Section 2 rule 3 (exact predicate), section 6 steps 2 and 3 and the "End state:
  stored interfaces" paragraph are the parts this RFC would replace for `Copy`. Rules 1 and 2, the `Clone` provision and
  the undecided-ownership diagnostic stay. This RFC needs RFC-0206 amended if accepted (OQ4).
- **RFC-0207.** Open question 6 ("whether `copy struct` on a generic type needs the condition in the header") is answered
  by section 1 rule 3. The colon list gains an optional `via` list on a class entry.
- **RFC-0212.** `declared` is unchanged. The flow list is part of the declaring entry.
- **RFC-0213.** Super-aspects: `Copy: deriving Clone, !Drop` is unchanged; the flow of `Clone` follows `Copy`'s.
- **RFC-0089.** Section 1's lattice is the substrate. Its amendment of 2026-11-06 says a type's declared class is
  checked against its fields and that a generic instance computes its class; this RFC states that computation for
  `Copy`.
- **Spike metel-core#1815.** Its outcome (header grammar and desugaring work, three of ten fixtures still `I0011`) is the
  evidence that the boolean form needs the solver. This RFC's claim is that the class form does not, for `Copy`.

---

## Open questions

1. **Is policy narrowing (section 5) a requirement?** If yes, this RFC is the wrong shape and a boolean form is needed,
   with the overlap with `where` resolved. Evidence to gather: how many removed fixtures (the `extend<T> X<T>: Copy
   where ...` family in `f6d6aad9`) and std types used it.
2. **Is the flow mandatory on `pub` generic types?** Recommended yes, computed otherwise.
3. **Spelling.** `Copy via T` is a placeholder. Alternatives: `Copy of T`, `Copy(T)`, a modifier on the parameter
   (`struct W<copy T>`), a class keyword taking parameters (`copy<T> struct W`). Choose after question 1.
4. **Amendment of RFC-0206.** Whether this is a separate accepted design that amends RFC-0206 section 6, or replaces its
   end state; and the migration of metel-core#1813, #1815 and #1818.
5. **Projections.** A field of type `T.Item` has a class that depends on an associated type, not on a parameter's class.
   The flow form cannot say it. Likely answer: undecided, as today, until associated-type conditions are designed.
6. **Other markers.** Whether `Discard`, `Send`, `Sync` and `Share` should take the same flow form. They are structural
   "every field" markers (RFC-0206 section 2), which a flow set describes exactly, but they are not lattice classes.
7. **Function and closure types.** A field of type `fn(T) -> U` or a closure type: whether the copy-ness of function
   types flows from anything (RFC-0166, RFC-0219).
8. **Enums.** Narrowing treats an enum as atomic (RFC-0137); whether a per-variant flow is ever wanted. Assumed no.
9. **Verification.** The claim that the three failing fixtures of #1815 (`I0011`) pass under class arithmetic has not
   been run. It is the first experiment to do before this RFC moves to review.

---

## Decision

**Outcome:** *(pending)*
