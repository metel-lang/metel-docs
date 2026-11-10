---
id: rfc-0224
title: "Stated flow for the ownership markers of generic types"
date: '2026-11-10'
status: under-review
updated: '2026-11-10'
tracking: 'https://github.com/metel-lang/metel-core/issues/1940'
---

> **Status — under review (2026-11-10).** Policy-narrowed Copy decided out by the language owner; design settlement tracked in metel-core#1940

> **Revised 2026-11-10 after an adversarial review (Codex, read-only).** The first draft claimed a type's whole ownership
> class (copy, affine, linear) flows from its parameters. That is wrong for linearity and `Drop` (a `Copy` flow
> cannot say whether a non-`Copy` type is affine or linear), and it overlooked that RFC-0206 section 6 already
> specifies the condition language. This version states the flow for one marker at a time, normatively for `Copy`, and
> is a surface and rules document for RFC-0206's stored interface, not a new mechanism. Scope decided by the language
> owner: a general mechanism for the "every field" markers, normative for `Copy` only in v0.16.0.

## Summary

RFC-0206 section 6 stores, for each permissive marker of a generic type, a **condition**: a conjunction of atoms
`Param: Marker` over the type's own parameters, with `true` and `never`, no disjunction, no negation, no recursion. It
leaves the declaration surface for stating it as a placeholder (`when`, metel-core#1815). This RFC fixes that surface
and the rules around it: a declaration states, per marker, the **flow set** of parameters the marker depends on.

```metel
struct Wrapper<T> derives Copy via T { value: T }          // Wrapper<X> is Copy exactly when X is
struct Pair<A, B> derives Copy via A + B { a: A, b: B }
copy struct View<T> { r: &T }                               // no flow: Copy for every T
```

`via` and the `+` separator are placeholder spellings (open question 1). The flow set is the same object as the
conjunction of RFC-0206, written as a parameter list, so there is no second condition language and no keyword that
competes with the struct-level `where`.

Scope, decided by the language owner on 2026-11-10: the mechanism is general for the markers defined as "every field
has it" (`Copy`, `Discard`, `Send`, `Sync`), and **normative for `Copy` and the `Clone` it provides in v0.16.0**. The
other markers adopt it in the RFCs that land their structural rules (section 3). `Linear` is not a stored marker and
the affine/linear class of a non-`Copy` type stays RFC-0089's computation.

This RFC also records two decisions: policy-narrowed `Copy` (a `Copy` that depends on something other than the markers of
the type's parameters) is not a requirement (section 5), and the rules for projections, conditional exclusions,
residuals and public types (section 2). It is a design draft. Nothing here is accepted.

---

## Motivation

RFC-0206 and RFC-0212 make `Copy` a declared property: it is granted in the declaration (`copy struct`,
`derives Copy`) and the predicate is exact (every field `Copy`, not `Drop`, not `Linear`). `extend X: Copy;` is an
error. That removed two things the old user-written `extend<T: Copy> Wrapper<T>: Copy where ...;` gave:

1. **A stored rule for generic bodies.** A generic body could ask "is `Wrapper<T>` `Copy`?" and get an answer from the
   `extend`. A derived `Copy` has no stored rule yet, so the abstract analysis answers *undecided*, a diagnostic
   (`I0011` today, RFC-0206 section 2 rule 3). `View<T>`, `Pair<Wrapper<T>, i64>` and other applications whose
   copy-ness depends on a parameter are affected.
2. **Conditions narrower than the structure** (section 5, decided out).

RFC-0206 plans stored interfaces (metel-core#1818) and a producer (#1819, #1813), and its condition language is
already a conjunction over the type's own parameters. What is missing is the declaration surface. The spike (#1815)
used `when`, a second conditional keyword beside the struct-level `where` (which constrains the type, not one property
of it), and the two read as near-duplicates. A flow list has no such overlap, because it names parameters and states
no condition.

---

## 1. Flow

**Definition.** For a marker `M` and a generic nominal type `N<P1..Pn>`, the *flow set* `F_M(N) ⊆ {P1..Pn}` is the set
of parameters on whose markers `N`'s holds:

```
N<A1..An>: M   exactly when   N has M by its own rule, and Ai: M for every Pi in F_M(N)
```

For `Copy`, "N has M by its own rule" is the declaration (`copy struct`, `derives Copy`) together with the exclusions
of RFC-0206 and RFC-0213 at the instantiation (not `Drop`, not `Linear`). The flow set is the stored conjunction
`P1: Copy, P2: Copy, ...` of RFC-0206 section 6, nothing more.

**Where it is stated.** On the `derives Copy` entry (RFC-0207). `copy struct P` is `struct P derives Copy`, so the
keyword form takes the same clause after the generics:

```metel
struct Wrapper<T> derives Copy via T { value: T }
copy struct Wrapper2<T> via T { value: T }              // the same declaration
enum Maybe<T> derives Copy via T { None, Some { value: T } }
struct Pair<A, B> derives Copy via A + B { a: A, b: B }
copy struct View<T> { r: &T }                            // empty flow
```

The clause lives on `derives`, not in the colon list: RFC-0207 rejects `Copy` in the colon list because `Copy`
generates `Clone`, and RFC-0213 says colon entries generate nothing. No change to either.

**The interface.** The stated set, or the computed one for a non-`pub` type that omits it, is stored as the type's
interface. Use sites read only the stored interface.

---

## 2. Rules

1. *Sufficient.* The stated set must contain every parameter the fields' markers depend on. A field of type `T`,
   `Option<T>`, `(T, i64)` or `Wrapper<T>` depends on `T`; `&T` does not (a reference is always `Copy`, RFC-0206);
   `i64` does not. A missing parameter is an error at the field, with the fix-it that adds it.
2. *May be larger.* The stated set may contain parameters the fields do not need. `struct Handle<T> derives Copy via T
   { id: i64 }` is `Copy` only when `T` is. This is the direction of a variance annotation that is more restrictive than
   the inferred one, and it lets a public type pin its interface against a later field edit.
3. *Omission always means "computed".* A non-`pub` type may omit `via`; the compiler computes the smallest sufficient
   set. A `pub` generic type may omit it only when the computed set is empty; otherwise omission is an error with a
   fix-it showing the computed set. No explicit-empty spelling is needed: a later field edit that makes the computed
   set non-empty fails at the declaration, so the interface cannot change silently.
4. *Same module.* The flow is part of the declaration; the orphan rule holds trivially (RFC-0206 section 2 rule 1).
5. *Whole nominal types only.* The flow set describes `N<A..>` as a whole. A **residual** type `N<A..>.{ .f }` is not
   covered: it is `Copy` by the structural rule of RFC-0206 over the visible field types, whatever `N`'s flow is
   (`W<T>.{ .n }` with `n: i64` is `Copy` for every `T`, RFC-0206 section 6).
6. *Projections are rejected.* A `Copy` declaration with a field whose copy-ness depends on an associated type
   (`value: T.Item`) is an error: whether `Payload<A>` is `Copy` depends on `A.Item`, which no set of parameters
   expresses, and an oversized set is not sufficient (`B: Copy` does not imply `B.Item: Copy`). A named limitation
   with a removal condition: associated-type conditions (RFC-0206's condition language rejects them today).
7. *No conditional exclusion on a Copy type.* A conditional negative grant of `Copy` (`extend<T: Marker> Token<T>:
   !Copy`) on a type that derives `Copy` is an error at the grant: a type is `Copy` exactly by its flow. The fixture
   `abstract_ownership_proves_conditional_negative_override` is reclassified at implementation.
8. *Arithmetic is not negative evidence.* In a generic body, "`Wrapper<T>` is not `Copy` under the bounds in scope"
   means the value moves. It is **not** evidence that `T: !Copy` and it does not select an implementation guarded by
   a negative bound; for selection and coherence an unavailable fact stays *undecided* (RFC-0206 section 2 rule 3,
   RFC-0213 section 3).

**Use in generic bodies.**

```metel
fun twice<T: Copy>(w: Wrapper<T>) -> (Wrapper<T>, Wrapper<T>) {
    (w, w)    // T: Copy and F(Wrapper) = {T}: accepted
}

fun bad<T>(w: Wrapper<T>) -> (Wrapper<T>, Wrapper<T>) {
    (w, w)    // T is not known Copy: the value moves; error: use after move
}

fun f<T: Copy>(p: Pair<Wrapper<T>, i64>) -> (Pair<Wrapper<T>, i64>, Pair<Wrapper<T>, i64>) {
    (p, p)    // F(Pair) = {A, B}, A = Wrapper<T>, F(Wrapper) = {T}: reduces to T: Copy. Accepted.
}

fun g<T>(v: View<T>) -> (View<T>, View<T>) {
    (v, v)    // F(View) = {}: always Copy
}
```

Consuming a stored interface is substitution of each declaration's stored conjunction; it needs no search for a proof.
**What still needs the solver.** *Producing* the computed set for an unstated type is the declaration-graph phase
(metel-core#1819), and the solver (#1813) remains for field-wise `Clone` derivation and the other markers' structural
rules. This RFC does not remove them; it removes the need for an obligation solver to *consume* a `Copy` fact for the
nominal forms, and it makes the stated case independent of one.

**Recursion.** A flow set is a set of parameters, so evaluation over stored interfaces terminates by construction.
Computing sets for a recursive declaration is the per-component fixed point of RFC-0206 section 6.

---

## 3. Other markers and `Clone`

- **`Clone`.** A `Copy` type has the provided `Clone` (RFC-0206 section 2 rule 2); `derives Copy via T` gives it the same
  flow, so `Wrapper<X>: Clone` when `X: Copy`. A type that is `Clone` and not `Copy` keeps `derives Clone`, whose
  condition is computed from `Clone` bounds (RFC-0207, RFC-0213); unchanged.
- **`Discard`, `Send`, `Sync` (direction, not normative).** They are "every field" markers, so a flow set describes
  them exactly, and RFC-0206 section 6 already stores their conditions in the same language. `Discard` is computed from
  the fields; a `pub` generic type's stated `Discard` condition (RFC-0206 D19) is a conjunction over its parameters, with a
  conservative default. Their declaration surface is settled in the RFC that lands each rule (`linear` for `Discard`,
  RFC-0158 and the structural rules for `Send`/`Sync`); this RFC only commits that it is the same form and that none
  of them needs a second condition language.
- **`Linear` and `Drop`.** Not stored markers; unchanged. Whether a non-`Copy` type is affine or linear is RFC-0089's
  computation (existential over owned fields), and `Drop`/`Linear`/`Copy` exclusions are RFC-0089 section 2.2 and
  RFC-0213. `Copy via T` says only when the type is `Copy`.

---

## 4. Worked examples

```metel
// 1. A container: copy exactly when the element is.
struct Slot<T> derives Copy via T { value: T }

// 2. A phantom parameter: no flow, always Copy.
copy struct Tagged<T> { id: i64 }

// 3. A pinned public interface.
pub struct Handle<T> derives Copy via T { id: i64 }

// 4. Insufficient flow.
struct Bad<A, B> derives Copy via A { a: A, b: B }
// error: field `b` has type `B`, whose Copy is not covered by `via A`. add B: `via A + B`

// 5. A public type that omits a non-empty flow.
pub struct W<T> derives Copy { value: T }
// error: a public generic type must state the flow when it is not empty: `derives Copy via T`

// 6. A residual is not governed by the flow.
struct R<T> derives Copy via T { value: T, n: i64 }
fun h<T>(x: R<T>.{ .n }) -> (R<T>.{ .n }, R<T>.{ .n }) { (x, x) }   // accepted: the residual holds only an i64

// 7. A projection.
copy struct Payload<T: Source> { value: T.Item }
// error: Copy cannot be declared with a field that depends on an associated type (named limitation)
```

---

## 5. What cannot be said

A `Copy` that depends on something other than the markers of the type's parameters cannot be stated:

```metel
// Not expressible: Copy only when T carries a user marker.
extend<T> Token<T>: Copy where T: Marker;         // error: Copy is granted only in the declaration (RFC-0206 rule 1)
```

RFC-0206's condition language (a conjunction of `Param: Marker` atoms) never admitted such a condition for `Copy`; this
RFC keeps it that way. The practical routes are a newtype that is itself `copy`, or the marker bound on the functions
that use the type. A bound on the type's own parameter (`struct Token<T: Marker>`) restricts which `Token`s exist, not
when one is `Copy`.

**Decided 2026-11-10 (language owner): policy-narrowed `Copy` is not a requirement.** The evidence follows.

---

## Alternatives considered

These are alternative spellings of the stored condition (RFC-0206's language is already a conjunction over the type's own
parameters), plus three larger shapes. The flow list is chosen because it names parameters and states no condition.

| Alternative | Spelling | Why not |
|---|---|---|
| `when` clause | `struct W<T>: Copy when T: Copy` | A second conditional word beside the struct-level `where`; the spike placeholder (#1815) |
| `if` after the entry | `: Copy if T: Copy` | Reads well, still two conditional words in one header |
| `copy?` with `given` | `copy? struct W<T> given T: Copy` | Clear, but adds `given`, tightens `copy` on every generic type, covers `Copy` only |
| Parenthesised | `: Copy(T: Copy)` | Looks like a call or a construction (RFC-0100, RFC-0114) |
| Flow in the colon list | `struct W<T>: Copy via T` | Conflicts with RFC-0207 (Copy not in the colon list) and RFC-0213 (colon entries generate nothing) |
| `extend` in the type's module | `extend<T: Copy> W<T>: Copy;` | Reverses RFC-0206 rule 1 and RFC-0212's `declared`; a second place to say `Copy` |
| Whole ownership class flows | `class(N<A>) = join(F)` | Wrong for linearity and `Drop`; the first draft of this RFC (section 3) |
| `Copy` as a property of the `Clone` impl | conditions only on `Clone` | Inverts "Copy implies the provided Clone"; least understood |
| Compile-time Boolean | `Copy where comptime(..)` | Waits on comptime; proving an arbitrary expression sufficient is hard |
| Computed interface only | no syntax | A public interface changes with a field edit |

### Evidence on policy-narrowed `Copy`

Prior-art evidence (searched 2026-11-10 from search snippets and one fetched thread, not full pages):
- *Rust* permits a narrower `Copy` (`impl<T: Copy + Marker> Copy for W<T>`), but no issue, post or thread found asks for
  it or shows real use of it; that is an absence in the searches, not proof. The documented pain runs the other way:
  `derive(Copy)` and `derive(Clone)` put a bound on every parameter whatever the fields hold, which over-constrains
  `PhantomData<T>` and references ([rust-lang/rust#26925](https://github.com/rust-lang/rust/issues/26925),
  [forum thread](https://users.rust-lang.org/t/how-to-copy-phantomdata-of-un-clone-able-types/82229)). The proposed
  fix, "perfect derive" ([Matsakis](https://smallcultfollowing.com/babysteps/blog/2022/04/12/implied-bounds-and-perfect-derive/)),
  computes the obligation from the field types, which is what a computed flow set does.
- *Rust* treats `Copy` as public API: removing it is breaking ([std docs](https://doc.rust-lang.org/std/marker/trait.Copy.html)),
  and tightening a generic bound is breaking ([Cargo SemVer](https://doc.rust-lang.org/cargo/reference/semver.html)).
  This supports section 2 rule 3 (a public type states its flow).
- *Swift* forbids it on purpose (SE-0427: conditional `Copyable` depends only on the type's own parameters being
  `Copyable`). In the [second review](https://forums.swift.org/t/second-review-se-0427-noncopyable-generics/72881) no
  visible post asked for broader conditions. Reviewers asked for explicit requirements, which supports stating the
  flow in the declaration. The main criticism (Slava Pestov) was that the `where` rule is another special case, so
  regularity of the rule matters more than its width.
- *Metel's own fixtures are not evidence.* The fixtures deleted in `f6d6aad9` that used `extend<T> X<T>: Copy where ...`
  tested the functionality that existed then; they were not written to show demand, so they are not counted
  (language owner, 2026-11-10). The prior art above is the evidence.

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
  more restrictive than the inferred one. The model for section 2 rule 2.

---

## Relationship to existing RFCs

- **RFC-0206** (integrated). Section 6's stored interface, condition language and recursion rules are used unchanged.
  Amended if this RFC is accepted: the `when` placeholder in the "End state" paragraph and step 2 becomes the flow
  list; section 2 gains rules 7 and 8 above; the unstated-condition error of step 4 becomes rule 3 here. Section 2
  rule 3 (exact predicate) and the undecided diagnostic stay.
- **RFC-0207.** The `derives` entry gains an optional `via` list (and `copy struct` the same clause). Open question 6
  ("whether `copy struct` on a generic type needs the condition in the header") is answered by rules 3 and 5.
- **RFC-0212, RFC-0213.** Unchanged: `declared`, `Copy: deriving Clone, !Drop` and the colon list are not touched.
- **RFC-0089.** Section 1's lattice and section 2.2's capabilities are unchanged; this RFC does not compute a class.
- **Spike metel-core#1815.** Its header grammar and desugaring work carry over with `via` for `when`. Its three
  fixtures that still hit `I0011` (`unbounded`, `nested`, `nested_unbounded`) are the first experiment (open question 3).

---

## Open questions

1. **Grammar.** `,` separates `derives` entries, so a multi-parameter flow needs another separator; `+` is proposed
   (`via A + B`), as in a bound list. Whether `copy struct W<T> via T` places the clause before or after the generics, and
   whether `via` should instead be a keyword of the class entry. Settleable now by choosing.
2. **`Discard`, `Send`, `Sync` surfaces.** Deferred to the RFCs that land them (section 3). Not blocking acceptance.
3. **Verification.** Run the three #1815 fixtures against a prototype that stores and consumes flow sets, and check
   that the fixtures deleted by the Copy migration still have an equivalent. Gate for acceptance: the first
   experiment, not a design question.

Resolved by this revision: the flow is stated on `derives` (not the colon list); mandatory on `pub` only when non-empty
(rule 3); enums have a whole-type flow and no per-variant flow; function and closure types follow RFC-0206's compiler
rules (they are not nominal types and have no flow); projections are rejected (rule 6); conditional negative grants on a
Copy type are rejected (rule 7); the amendment of RFC-0206 is the list in "Relationship".

---

## Decision

**Outcome:** *(pending)*
