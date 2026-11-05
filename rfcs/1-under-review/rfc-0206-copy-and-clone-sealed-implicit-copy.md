---
id: rfc-0206
title: "Copy and Clone: A Sealed Implicit Copy and an Explicit Clone"
date: '2026-11-02'
status: under-review
updated: '2026-11-05'
tracking: 'https://github.com/metel-lang/metel-core/issues/1785'
---

> **Extracted from RFC-0080 on 2026-11-02**, the way RFC-0162 was extracted from RFC-0157, **redesigned on
> 2026-11-03** after a prior-art survey (architecture/reports/copy-clone-prior-art-survey.md) and an adversarial
> review, and **revised on 2026-11-05** after three adversarial reviews and two spikes: the implicit copy is
> **sealed** (a representation copy that runs no user code) and the marker is `Copy` again, settled against the
> multiplicity lattice of RFC-0089. The earlier design, an `ImplicitClone` marker whose hook was the type's own
> `clone`, is recorded in section 8 as the extension this RFC leaves open. Where a duplication marker is written is
> RFC-0207's; the model and its alternatives are RFC-0162's. Nothing here is decided.

> **Status — under review (2026-11-05).** Committed to v0.16.0 as the Copy and Clone half of the settlement.

## Summary

`Clone` is the aspect for explicit duplication: `fun clone(&self) -> Self`. It may do anything a function can.
`Copy` is the implicit duplication: a by-value use of a `Copy` value duplicates it instead of moving it, and the
duplicate is the **representation copy**. It is sealed: it runs no user code, so it cannot be observed, and the
compiler may turn a copy into a move at the last use. `Copy` is granted only in the type's declaration, excludes
`Drop` and `Linear`, and implies `Clone`, which the compiler provides (it is the same copy) and which cannot be
written for a `Copy` type.

```metel
copy struct Point { x: i64, y: i64 }              // Copy; Clone is provided; the declaration says so
struct Doc derives Clone { title: String }        // affine (the default): moves; d.clone() is explicit
affine struct Handle { fd: i64 }                  // locked: nothing can later make it Copy or Linear
struct Cache { data: i64, hits: i64 }
extend Cache: Clone { fun clone(&self) -> Cache { Cache { data = self.data, hits = 0 } } }
// explicit-only: a custom duplicate means the type is not Copy
```

The classes are the lattice of RFC-0089: unrestricted (`Copy`), affine (the default: at most once, no duplication)
and linear (exactly once). The one-sentence explanation is: *`Copy` is the duplication the compiler does for you, a
bit copy; `Clone` is the one you ask for, and it may be anything.* `copy struct P` is the one-word form of
`struct P derives Copy`; `affine` and `linear` are the other two keywords (section 5).

---

## Motivation

`Copy` does not currently give a type a `clone`. Measured against the implementation on 2026-11-02:

```metel
struct P { n: i64 }
extend P: Copy;
fun main() { let p := P { n = 1 }; let q := p.clone(); }   // no method `clone` on `P`
```

`T: Clone` rejects such a `P`, and a bodyless `extend P: Clone;` is rejected because the method is required. A
`Copy` struct that needs a `Clone` must hand-write one, and there is no derive. Five integration fixtures carry a
hand-written `clone` callback as scaffolding for exactly this (metel-core#270).

Three further facts shaped this design:

- **Coverage holes.** `&T` and `[T]` are `Copy` but not `Clone` (`&i64` fails `T: Clone` with `T0012`), and array
  `clone` does not call the element's `clone` while record `clone` does. A rule of the form "every `Copy` type is
  `Clone`" cannot be left to std.
- **Rust's pair has a documented friction.** `Copy: Clone` requires both impls and a type must write or derive
  both; Rust documents that `Clone` should agree with the copy for a `Copy` type (RFC 1521) but the compiler does
  not enforce it; and derive over-approximates generic bounds (the `Copy` documentation says so).
- **A user-writable implicit hook was explored and set aside.** Three adversarial reviews found that running user
  code at an implicit copy makes insertion and elision observable, and that its lowering, ordering and generic
  semantics cost more than they return in the first release (section 8). A sealed copy removes the problem, fits
  the lattice of RFC-0089 (contraction is a structural rule, not a computation) and can be relaxed later without
  breaking any program.

The survey found the precedents: Rust's non-overloadable `Copy` and Swift's compiler-managed copy (neither can
run user code at an implicit copy), Swift's `BitwiseCopyable` (SE-0426), which separates types copyable by
direct memory operations from ordinary copyable types and makes the property a permanent promise (the closest
precedent for a sealed `Copy` with a declaration-level authorization), Mojo's single copy hook with an
`ImplicitlyCopyable` marker, and Swift's rule that copyability is fixed on the declaration.

---

## 1. `Clone`

```metel
aspect Clone {
    fun clone(self: &Self) -> Self;
}
```

`clone` returns a new owned value of the same type and the caller keeps the original; no move occurs. The
contract is Rust's signature and ownership shape: *another value of this type*. Rust also expects `clone` to
preserve equality where `PartialEq` exists, and collections rely on it; Metel states no equality law, so Rust's
collection assumptions cannot be inherited without a further contract: a future collection API must not assume an
equality- or hash-preserving `clone` silently, and either states which operations cannot rely on it or asks for a
stronger law-bearing capability. A reference or a view is cloned by cloning
the reference or view, not the referent. A handle that aliases shared state is `Share` (RFC-0158), a separate
aspect, and is not `Clone` unless its type says so.

A type gets a `Clone` by writing one (`extend T: Clone { … }`), by a `derives Clone` request (RFC-0207), or, for a
`Copy` type, because the compiler provides it (section 2). Calling `clone` is always explicit.

---

## 2. `Copy`

`Copy` is declared in std as an ordinary aspect, using the aspect properties of RFC-0212 and the super-aspect
relation of RFC-0213 (the spelling is a sketch):

```metel
aspect Copy: derived Clone, !Drop           // RFC-0213: Clone derived with it, Drop excluded (and Linear, once it exists)
    declared                                // RFC-0212: granted only in a declaration
    implicit;                               // RFC-0212: std only; a by-value use copies instead of moving
```

It is the stronger bound: `T: Copy` accepts fewer types than `T: Clone`.

**No special case by name.** Every behaviour below follows from one of those properties. The compiler reads them
from the aspect's declaration by identity and never tests the spelling "Copy". The one property that is a language
semantic and not a constraint is `implicit` (RFC-0212 section 3): it is std only. Today the compiler identifies
`Copy` by the string `"Copy"` at about 38 sites in the frontend (`aspect_name == "Copy"`,
`infer_type_satisfies_aspect(…, "Copy", …)`); replacing them is the prerequisite refactor of section 6.

**Legality.**
1. *Granted only in the declaration.* A named type is `Copy` only through its declaration:
   `copy struct P { … }` or, equivalently, `struct P derives Copy { … }` (RFC-0207, section 5). An
   `extend T: Copy;` is an error with a fix-it that moves it (a deprecation for one minor release, section 5).
2. *`Clone` is provided and cannot be written.* `derives Copy` derives the marker and the `Clone` (RFC-0213
   section 4); the provided `clone` is the representation copy. A written `extend P: Clone` for a `Copy` type
   overlaps the provided impl and is an error (`T0015`). A type that needs a custom duplicate is not `Copy`.
3. *The predicate is exact and conjunctive.* For an instantiation `T<A>`, `T<A>: Copy` holds when every field's
   type is `Copy`, and the type is not `Drop` and not `Linear`. It is evaluated per instantiation, so
   `copy struct View<T> { r: &T }` is `Copy` for every `T`. This is the declarative meaning: the least solution of
   those conditions over concrete instantiations. The analysis of a generic body (ADR-0063) is a **sound
   approximation** of it: it answers yes, no or unknown, and unknown never permits a copy, so the checker may
   reject a program the rule accepts and never accept a copy the rule forbids. The v0.16.0 implementation decides
   only what the abstract analysis decides today (conditions on parameters, and the compiler rules for
   references, tuples, arrays, closures and function types) and reports every other abstract ownership as
   **undecided**: a read of such a value in a generic body is a diagnostic (a named limitation), never a guess in
   either direction. Reusing a `View<T>` in a generic body is therefore rejected until the obligation solver,
   which is deferred to a later minor (metel-core#1813; section 6, step 2); today it is rejected with an internal
   error (`I0011`). Because undecided is an error and not a move, the accepted set only grows when proof power
   improves, and the copy-or-move behaviour of an accepted program never changes with it. Adding proofs must also not change overload
   selection, conditional-implementation selection or coherence conclusions: every consumer of an ownership fact other
   than the copy-or-move decision sees an undecided fact as undecided, never as no (RFC-0213 section 3). Concrete uses
   are unaffected.
4. *The implicit copy is the representation copy.* A copy site (below) of a `Copy` value duplicates its
   representation. No user code runs, so a copy is unobservable; a type that is not `Copy` is moved.
   **Definition.** The implicit copy *is* an invocation of the type's provided `Clone` (rule 2), which the compiler
   is free to elide because it is the representation copy. This is why `Copy` entails `Clone`: `Copy` has no
   methods of its own, and the operation it grants is the provided `clone`, done implicitly. Because that `clone`
   cannot be written (rule 2) and runs no user code, the definition and the representation copy cannot differ,
   and a `T: Copy` bound in generic code still guarantees no user code runs at a copy. The leaf native
   `copy_value` (section 2, leaf clones) belongs to the explicit `Clone` of non-`Copy` leaves such as `String`; those
   are moved, never implicitly copied, so the definition does not involve it.
5. *`Drop` and `Linear` exclude it.* A type that implements `Drop` cannot be `Copy`, and neither can a `Linear`
   type. The justification is operational, and RFC-0089 section 1 states it with the lattice: a representation copy
   cannot perform the per-owner cleanup bookkeeping that a destructor needs, and a linear value is never implicitly
   discarded (RFC-0071 section 4's `Copy`/`Drop` exclusion is the first fact). `Clone` on a `Drop` type is allowed.
6. *Residuals.* A residual `T.{ fields }` of a `Copy` type is `Copy` when the present fields are `Copy`
   (RFC-0211 rule 1) and has the provided `Clone`; there is no dependence on how `Clone` was written, because it
   cannot be.
7. *Entailment.* `T: Copy` entails `T: Clone` in the checker and in the abstract analysis of generic bodies, by
   the super-aspect relation of the declaration (RFC-0213).

**Where an implicit copy happens (copy sites).**
1. A **place read in value position** is a copy site when the place's type is `Copy`, and a move otherwise. Value
   position means a use that would otherwise take the value out of the place: `let b := a`, `f(a)`,
   `return a`, `S { f = a }`, `[a, a]`, a by-value `self` argument, a by-copy capture, and the same for a field
   `a.x`, an index `a[i]` and a dereference `*r`. A borrow (`&a`, a `&self` receiver) reads nothing. A temporary
   (a call, a literal, a constructor, a block result) is transferred.
2. Every other by-value form (patterns and `match` bindings, `for` iteration, record spread, closure creation,
   `?`, operators) classifies a read the same way and follows the move checker's existing rules for what it
   consumes; because the copy is unobservable, nothing further is specified about their order or count.
3. **The copy may be elided.** A copy at the last use of a place may be a move; the compiler may copy lazily.
   Neither is observable.
4. **A generic body decides at its definition.** Whether a read is a copy or a move is decided by the bounds
   visible there: `fun relay<T>(x: T) -> T { x }` moves, even when instantiated with a `Copy` type, and the same
   read under `T: Copy` is a copy. This is the parametricity Rust has. The decision matters to the move checker,
   which runs on the definition's abstract body; at run time a copy and a move have the same effect, so the
   interpreter needs no per-site record.
5. **Repeated arrays.** `[e; N]` with `N > 1` requires the element type to be `Copy`.

**Recursion and termination.** A recursive type goes through `List`, `Option`, `Result` or a reference (there is
no `Box`).
1. **Predicate queries are inductive.** A cycle in a `Copy` (or any marker) query is "no". This is the least
   solution of rule 3, and it costs nothing: `List`, `Option` and `Result` are not `Copy`, a reference is always
   `Copy` without being inspected, and a cycle by value would be an infinite value.
2. **Derivation conditions are coinductive on goals that repeat exactly.** `enum Tree derives Clone {
   Leaf, Node(List<Tree>) }` needs `Tree: Clone`, which needs `List<Tree>: Clone`, which needs `Tree: Clone`
   again. The solver assumes the impl being derived while it checks the fields, as Rust and Haskell do. The
   derived `clone` is a recursive function over finite values, so termination comes from the data and not from the
   proof. This covers regular recursion such as `Node<T> { next: Option<Node<T>>, v: T }`.
3. **Coinduction never applies to a negative goal** (`!Drop`, `T: !B`) **or to a marker aspect.** A cycle through
   one is unknown, never a proof.
4. **Expanding recursion is rejected.** `struct Grow<T> derives Clone { rest: Option<Grow<List<T>>> }` grows its
   argument at every step. A size and depth limit gives an error at the declaration with the fix-it "write the
   impl", and unknown in the abstract analysis.
5. **The derived body** is a per-field call, so a recursive `clone` recurses through the impl and needs no
   unrolling. A written impl whose where clause mentions its own type is the ordinary case: the impl exists and
   is not unrolled.

**Built-in kinds: std impls where the target can be named, compiler rules where it cannot.**

| Kind | `Copy` | `Clone` |
|---|---|---|
| Integers, floats, `boolean`, `Char`, unit | yes, a std impl (`extend i64: Copy;`, as today) | provided: the copy |
| Shared references `&T`, views `[T]` | yes, for every `T`: `extend<T> &T: Copy;` in std | provided: the reference or view copied |
| `&var T` | never | none |
| Tuples, `[T; N]`, records | when every part is (a compiler rule: tuples until variadics, #794; arrays and the record hook until a compile-time `N` and RFC-0174, after this release) | provided whenever `Copy`; otherwise field-wise |
| Closures | when every capture is (RFC-0134 §1) | provided when `Copy`; otherwise by captures |
| Written function types | move-only (RFC-0166) | none |
| `String`, `List`, `Option`, `Result` | no | the std impls of section 3 |

Unit becomes a std impl like the scalars, which fixes the disagreement between the bound and the move checker
(metel-core#1784) without a special case. Because the compiler provides `Clone` for every `Copy` kind, the coverage
holes of the Motivation cannot recur.

**Leaf clones.** The `Clone` of a non-`Copy` leaf such as `String` is a std native
(`native(@std.core.copy_value) fun clone(&self) -> Self;`); it cannot panic or reenter. A *derived* `clone` of a
non-`Copy` type is a per-field call to each field's `clone`, in declaration order for structs, named records and
enum payload fields, in increasing index order for sequences, left to right for tuples, in lexicographic label
order for anonymous records and in capture-list order for closures. If a field's `clone` panics, the derived clone
stops: fields already cloned are dropped in reverse order by whatever the runtime's panic semantics do (panics are
not catchable, RFC-0153), and no partial value is observable. The order is observable only when an inner
`clone` is written, and it is defined so that it is stable (the interpreter's record clone iterates a `HashMap`
today and gives no defined order; metel-core#1817).

**What `Copy` promises.** It is side-effect-free duplication, not necessarily cheap duplication: a large inline
array is copied at its size (Zig's reference makes the same point), and a large-copy diagnostic is a possible
later tool once layout exists.

**Bounds in generic code.** Generic code that must copy bounds on `Copy`; code that may duplicate bounds on
`Clone` and calls `.clone()`. An unbounded type parameter is affine: it can be moved and dropped but not copied
or duplicated, and it cannot yet hold a `Linear` value (section 5).

**Third-party types.** A type from another module cannot be made `Copy` by its user, because the grant is
`declared`. This is intended: whether a type may be duplicated implicitly is its author's statement. A wrapper in
the user's module can be `copy` over the foreign type when that type is.

---

## 3. Standard `Clone` impls

Measured on 2026-11-02:

| Type | `Clone` today | Plan |
|---|---|---|
| Primitives | yes | `Copy` types: the `Clone` is provided; the explicit bodies go |
| `String` | yes | the body becomes the leaf native `copy_value` |
| `[T; N]` | yes, but it does not call the element's `clone` | `Copy` when the element is (provided); otherwise field-wise through the element's `clone`; the discrepancy with records is a defect to fix |
| Anonymous records | yes, field-wise: `extend<record R> { ..R }: Clone where ..R: Clone` (RFC-0123) | unchanged |
| Named `record` | yes today, the same field-wise impl | takes `derives Clone` or `derives Copy` like a `struct`; a plain `record P` is not cloneable |
| Tuples | **no** | a structural arm, hardcoded like tuple `Copy` (metel-core#263), until variadic generics (metel-core#794) |
| `Option`, `Result`, `List` | **no** | `extend<T: Clone> Option<T>: Clone`, and the same for the others (metel-core#270) |
| A named `struct` or `enum` | only if the user writes one | section 4 |
| `&T` | no `Clone` in the reference satisfaction arm | provided: `Clone` for every `T` |
| `[T]` | `Clone` only under `T: Clone` (`extend<T: Clone> [T]: Clone`) | provided: `Clone` for every `T`, the view copied, not its elements. This is a different operation from the owning array's element-wise `Clone` (`[T; N]` above), and the two stay separate |
| Closures | no `Clone` | provided when `Copy` (by captures, RFC-0134 §1); otherwise by captures with an environment-cloning witness |

---

## 4. `Clone` for a user type

- **Written:** `extend P: Clone { fun clone(&self) -> P { … } }`, always available for a non-`Copy` type and the way
  to customise (skip a cache field, reset a counter). Such a type is explicit-only: its uses move, and `p.clone()`
  runs the written body.
- **Derived:** `struct P derives Clone { … }`. The derived `clone` clones each field, so it is deep for owning
  fields, and a field type without `Clone` makes the entry an error at the declaration. The derived impl applies
  at an instantiation when every field's type is `Clone` there (the exact condition of RFC-0207 section 2).
  For an enum it matches the active variant. Written and derived impls of the same aspect for one type overlap
  and are an error.
- **Provided:** `copy struct P { … }` gives `Clone` and `Copy` together.
- **Not automatic.** A type with none of these has no `Clone`: whether a named type may be duplicated is a
  statement about what it means, not a consequence of its fields, so an accidental `Clone` (for example on a
  handle type whose fields happen to be `Clone`) is not provided.

The derivation itself is native in the first implementation, as it already is for records; a comptime derivation
replaces the native one when RFC-0092 and RFC-0093 allow.

---

## 5. Names, keywords and migration

- **`Clone`** keeps its name, its Rust signature and its ownership shape (section 1).
- **`Copy`** keeps its name and its place in bounds (`T: Copy`); what changes is where it is granted (the
  declaration) and that `Clone` comes with it. `extend X: Copy;` is accepted for one minor release with a
  deprecation warning and a fix-it that rewrites it to `copy struct X`, then becomes an error. An `extend X: Clone`
  next to a `Copy` type must be removed (or the type made affine). The name `ImplicitClone` of earlier drafts is
  not used.
- **Class keywords** before `struct` and `enum` (RFC-0089 section 2.1), contextual and not reserved globally, sugar
  for the declaration clauses (RFC-0207): `copy struct P` is `struct P derives Copy`; `affine struct H` is the
  locking pair of negative impls `extend H: !Copy; extend H: !Linear;`, a declaration-site opt-out that needs no
  negative colon entry; `linear struct T` is `extend T: Linear {}` and is **reserved and marked "Planned for"** in
  v0.16.0. They apply to structs and enums, not to the anonymous record type. For a generic type a keyword states
  a capability, not a class: `copy struct Wrapper<T>` is `Copy` exactly when `T` is (the conditions of section 6,
  "End state").
- **The function-type qualifier** `copy` and the keyword `once` (RFC-0163, RFC-0134) keep their planned spelling;
  the type keyword `copy` and the qualifier name the same property.
- **Defaults.** A type is affine unless it says otherwise (RFC-0071): forgetting a keyword on a handle or a token
  fails safe. A `Copy` grant is a statement; it is never inferred from the fields (copy-by-default, section 8).
- **Generic code with respect to `Linear`.** In v0.16.0 every type is discardable, so an unbounded type parameter
  behaves as affine: movable and droppable, not copyable. The long-term rule is RFC-0089 section 2.2 (decided 2026-11-05): a bare `T` is
  possibly linear, the capability `Discard` is elaborated for the one implicit operation (drop), and a `pub` generic
  function states it once `linear` ships. The generic-body analysis must record drop sites of parameter-dependent
  values now, so that nothing in v0.16.0 forecloses it. RFC-0089 must show the demonstration of section 2.2 before
  its sections 1 to 2.1 are accepted.
- **`Share`** (RFC-0158) is unaffected, since the name `Clone` stays.

---

## 6. Implementation staging and dependencies

**Scope of projections in v0.16.0 (decided 2026-11-05).** A residual `T.{ fields }` gets exactly two things:
`Copy`, structurally and sealed (section 2 rule 6), and the existing `Drop` dispatch (RFC-0137 section 5). Every
other aspect on a projection is `T0012`, with a use-site diagnostic that names the written impl as the cause
(the language keeps no edit history, so it cannot warn at the edit). The end state is row templates for derived
impls (RFC-0211) plus written residual impls (RFC-0214, including its row-generic form, with construction in
RFC-0216) for hand-written ones. Neither draft is a dependency.

**Native structural `Copy` for now (decided 2026-11-05).** The structural rule that makes a named `Copy` type and
its residuals `Copy` is compiler logic in v0.16.0, not the std row template, so the Row machinery stage is not on
this settlement's critical path. It is a named, time-boxed exception; metel-core#1823 (milestone "Structural kinds
after comptime") tracks replacing it by the template with no change in accepted programs.

There is no first stage that carries the semantics with a special case. The settlement waits for the general
features, in this order:

1. **Identity-based aspect resolution.** Replace the string-keyed `"Copy"` sites by an aspect identity lookup (the
   ADR-0054/0066/0067 line). A prerequisite refactor, no RFC.
2. **The abstract-ownership limitation** (metel-core#1814), not a solver. A spike (#1810, 2026-11-04) prototyped
   an obligation solver and estimated 15 to 30 engineer-days for a production one, so v0.16.0 ships a limitation:
   an abstract ownership the analysis cannot decide is a diagnostic in the generic body (not an internal error,
   and not a silent move, which would make a later solver change what accepted programs do). The established
   proofs are preserved. **The obligation solver** (goals `type: aspect` over abstract types, answered yes with a
   witness, no or unknown; nested applications, field-wise templates) is a later minor
   (metel-core#1813). Super-aspect entailment in this release covers declared bounds and their super-aspect
   closure; an exclusion (a negative super entry) is a grant-time check only (RFC-0213 section 3), so coherence needs no
   closure beyond the positive one and no solver.
3. **The declaration clauses** (RFC-0207): `derives`, the colon list for user markers, and the class keywords.
4. **Super-aspects** (RFC-0213), including entailment over declared bounds and their super-aspect closure, and the
   syntactic negative closure (there is no solver in this release).
5. **Derivations** (RFC-0207): native `Clone` first; the marked super-aspect derivation of RFC-0213 section 4,
   which derives the provided `Clone` with `Copy`.
6. **Aspect properties** (RFC-0212): `declared` and `implicit`, and the std-written structural rule (a row
   template, RFC-0123), with the row machinery it needs for named types (RFC-0209, RFC-0210, RFC-0211). RFC-0208's
   `<..R>` binder is not a prerequisite: the templates use `record R` until it lands (the spikes did not exercise
   templates; to be checked in the Row machinery stage).
7. **Built-in kinds as impls:** references and views, then tuples (RFC-0125, #794), then closures and function
   types (metel-core#739, RFC-0134). **Arrays and the native record `Clone` hook stay named compiler rules in this
   release.** Their std impls need a compile-time `N` (RFC-0132 §3) and the comptime-for implementation
   (RFC-0174), which the roadmap schedules after Move check default-on and so after v0.16.0. They move to a later
   theme, "Structural kinds after comptime" (#1811, #1390, #702), and the compiler rules are deleted there. These
   are the structural-kind exceptions of the release; the abstract-ownership limitation of step 2 is the other.
   Each is named, listed here and in the table of section 2, and has a removal condition.
8. **Then `Copy` itself** as a declared aspect in std, with `extend X: Copy;` deprecated.

**Dependency on RFC-0089 (decided 2026-11-05, design level only).** The classes of ownership are the lattice of
RFC-0089 section 1. Settling against it gives: the `Copy`/`Drop` and `Copy`/`Linear` exclusions as one rule; the
class keywords as one-word spellings (above); and the closure rule shared with RFC-0194. RFC-0089 is split so that
its sections 1 to 2.1 can be accepted without section 3 (partial consumption through `ToRecord`, coupled to
RFC-0090), which moves to its own RFC. v0.16.0 implements `copy` and `affine`; `linear` is reserved; `Linear`
itself, its structural `auto` rule and partial consumption stay with the split-off RFC and the RFC-0096 revision.

**End state: stored interfaces with the solver as producer (decided 2026-11-05).** v0.16.0 ships the design of
this RFC as written, with the limitation of step 2. The direction after it is the hybrid recorded in the
comparison report (`architecture/reports/clone-implicitclone-declared-conditions-comparison.md`, section 13): the
general solver computes, once per declaration, the weakest condition on the type's parameters under which the
exact predicate holds; that condition is stored as the type's interface (an impl set, whose heads may be
instantiation patterns); every use, including generic bodies, consults only stored interfaces. The invariant is
that a stored interface implies the exact predicate of rule 3 and equals it whenever the condition language can
express it, so rule 3 stays the meaning and the generic-body analysis becomes complete for markers on nominal
types. **The stated condition is the interface.** An optional `when` clause, checked as sufficient against the
computed one, is what other code sees; the computed condition is the interface only when none is stated (a
non-`pub` type). A stronger stated condition therefore keeps the published interface stable when a
representation change would weaken the computed one. Use sites evaluate only stored interfaces, and the stored
condition language is finite and acyclic: its evaluation terminates by construction (recursive conditional
heads are rejected or normalised at the declaration). An ownership diagnostic names its proof path: no
declaration permission, a field that fails, an absent bound, or a checker limitation. Haskell's report is the precedent for the computation: the smallest derived context, with a fixed point over
mutually recursive declarations, and GHC restricts the inferred shapes and offers a written context for the rest.
The route is incremental and nothing in v0.16.0 closes it:
1. v0.16.0: this RFC, with the undecided-ownership diagnostic (#1814).
2. A later minor: stored interfaces with explicit conditions, with copy classification separated from obligation
   entailment (metel-core#1818).
3. Then: the declaration-graph computation phase (#1819) and the solver as producer of the interfaces (#1813).
4. Finally: an unstated condition on a `pub` generic type is an error, with a fix-it showing the computed
   condition (#1820); a non-`pub` type may rely on the computed condition. A field change to a public type then
   either keeps its stated condition sufficient or fails validation, so it cannot change the interface silently.
Epic: metel-core#1821.

Work specific to this RFC and independent of that order:
- The std repairs: array and tuple `Clone`, the reference and view cases, the unit fix, and #270's `Option`,
  `Result` and `List`.
- The interpreter's derived-clone order (section 2, leaf clones) and the removal of the `HashMap` iteration in
  `record_clone.rs` (metel-core#1817).
- The evaluator may keep `deep_clone_value` at bindings: a sealed copy is unobservable, so no per-site dispatch,
  witness or ordering rule is required (this closes the copy-site retention and lowering work of the earlier
  design, metel-core#1816).

---

## 7. Worked examples

```metel
copy struct Point { x: i64, y: i64 }
let a := Point { x = 1, y = 2 };
let b := a;                    // a copy; a is still valid
let c := a;

copy struct Wrapper<T> { v: T }
// Wrapper<i64>: Copy and Clone (provided); Wrapper<String>: neither (String is not Copy) -- but it may
// `derives Clone` separately if it is written affine:
struct Boxed<T> derives Clone { v: T }     // Boxed<String>: Clone, moves

struct Cache { data: i64, hits: i64 }
extend Cache: Clone { fun clone(&self) -> Cache { Cache { data = self.data, hits = 0 } } }
// explicit-only: `let b := c` moves, `c.clone()` runs the body

struct H { fd: i64 }
extend H: Drop { fun drop(&var self) { } }
extend H: Clone { fun clone(&self) -> H { H { fd = dup(self.fd) } } }     // Clone on a Drop type: fine
// copy struct H2 { fd: i64 } with extend H2: Drop { … }                  // error: Copy: !Drop

copy struct Both { n: i64 }
extend Both: Clone { fun clone(&self) -> Both { Both { n = 0 } } }        // error T0015: overlaps the provided Clone
extend Point: Copy;                                                       // error: granted only in the declaration
affine struct Token { id: i64 }                                           // locked: extend Token: Copy; is a coherence error
```

---

## 8. Alternatives considered

- **A user-writable implicit hook** (`ImplicitClone`, the design of the drafts before 2026-11-05): the implicit
  copy calls the type's own `clone`, so a `Cache` can reset a field on copy. It is not taken for v0.16.0.
  Three adversarial reviews found that it makes insertion and elision of the call observable; that it needs a
  complete lowering and ordering contract for patterns, iteration, spread, `?`, captures and aggregates; that
  generic reads need a per-site decision and dispatch evidence through reconstruction; and that a value-changing
  clone makes "unknown" a semantic choice. A sealed copy removes all of that, matches Rust and Swift, and fits the
  lattice of RFC-0089. **It stays open as a later extension, on conditions.** Sealed to writable preserves every
  accepted program only if the hook is a **separate, separately authorized mode** and nothing weakens what `Copy`
  already guarantees: `Copy` (and so `T: Copy` in generic code) keeps meaning a representation copy that runs no
  user code, the existing elision permissions stay valid, existing exclusions keep their meaning (removing
  `!Drop` would let a type be granted both, RFC-0213 section 3), and a hook cannot replace an already provided `Clone`.
  Allowing callbacks under the existing `Copy` guarantee would weaken a contract that generic libraries may rely
  on. No surveyed mature language replaced a sealed-copy guarantee by observable hooks while keeping its old
  guarantees (D added and replaced hook mechanisms and accumulated precedence rules; C++ needs explicit
  elision rules). Writable to sealed would be a break. The cost of the extension is the work listed above,
  which is why it is deferred and not designed here.
  **The definition of the implicit copy does not open the hook.** Section 2 rule 4 defines the implicit copy as an
  elidable invocation of the *provided* `Clone`. That is a statement about the compiler-provided, unwritable
  `clone` of a `Copy` type, whose body is the representation copy. It must not be read as "an implicit copy calls
  whatever `clone` the type has": a written `Clone` on a `Copy` type is `T0015`, so there is no written `clone` for
  an implicit copy to reach. A later hook is a separate, separately authorized mode with its own dispatch and
  elision rules, not a relaxation of rule 2.
  **Decision (2026-11-05): the extension stays open, with a named trigger.** It is reopened only if a std or
  ecosystem type needs observable behaviour on an implicit copy and an explicit `.clone()` cannot express it. Until
  then `Copy` is sealed and nothing is built. Any proposal must meet the four conditions above and carry its own
  compatibility argument; this RFC does not promise that the extension is monotone, only that it is not ruled out.
- **Copy by default** (Swift's inference): rejected. A type whose fields are all copyable becomes `Copy` silently,
  so a capability token or a handle written without a keyword is freely copyable and droppable, the failure
  linear types exist to prevent. Rust chose opt-in for the same reason; the affine default fails safe, and the
  `copy` keyword makes the opt-in one word.
- **`Copy` and `Clone` linked by `provides` with overlapping impls** (the first draft of this RFC and RFC-0207).
  Rejected after the first adversarial review: it needs a selection rule over overlapping impls, an uncheckable
  equality invariant between two bodies, and an R1-to-R2 migration that negative bounds break. Super-aspects are
  used here, but as a plain refinement relation (RFC-0213) with a single provided impl.
- **An explicit duplication operator and no implicit marker** (`copy x`). Set aside: it moves the question to
  which types may be implicit anyway, since generic numeric code needs a bound.
- **A lang-item attribute for one aspect, or a compiler-known marker.** Rejected by the language owner: each is
  an exception keyed to a name. The aspect properties of RFC-0212 and the relation of RFC-0213 replace them, at the
  cost of the dependency chain of section 6.
- **The string-keyed special case that exists today.** Rejected: about 38 sites test the spelling "Copy", which
  cuts against the identity-based resolution of ADR-0054, ADR-0066 and ADR-0067.

---

## Relationship to existing RFCs

- **RFC-0162** — the model, the design space and the survey; this RFC is its accepted-direction specification of
  the two aspects.
- **RFC-0207** — the `derives` clause and the colon list (user markers) that carry the grant and the derivation,
  and the class keywords as sugar.
- **RFC-0212** — the aspect properties (`declared`, `implicit`) that `Copy` is declared with.
- **RFC-0213** — super-aspects, which give `Copy: derived Clone, !Drop`.
- **RFC-0089** — the multiplicity lattice, the `Linear` aspect and its exclusions, and the class keywords. A
  **design-level dependency** of this settlement (decided 2026-11-05); RFC-0089 is split so its sections 1 to 2.1
  can be accepted without section 3. See section 6.
- **RFC-0096** — auto aspects, whose revision (including how `Linear` is inferred) is deferred.
- **RFC-0071 §2** — states the one predicate; its `Copy` stays `Copy`, with the grant moved to the declaration.
- **RFC-0134 / RFC-0163 / RFC-0166 / RFC-0194** — closures and function types: copyable by captures; the `copy`
  qualifier; written function types move-only; linear closures.
- **RFC-0158** — `Share`, unchanged.
- **RFC-0080** — the source of `Clone`; it keeps `Deref`, `Send` and `Sync`.
- **RFC-0093 / RFC-0092** — the derive mechanism and comptime that replace the native derivation.
- **RFC-0097** — the orphan rule for bare-parameter blanket impls; no longer needed for this.

## Novel parts and acceptance

The fourth review (prior art, 2026-11-05) judged that the ownership choice is on well-trodden ground (a sealed copy,
a declaration-local grant, a provided `Clone`, definition-time generic decisions) and that the surrounding machinery
is a language-design experiment. Accepting this RFC should not be presented as external validation of the latter. The
novel parts and their risk:

| Part | Risk |
|---|---|
| Exclusion-based disjointness evidence (RFC-0213 section 3, deferred) | High if built: exclusions would become a public coherence contract; v0.16.0 keeps them a grant-time check only |
| The stated condition as the public interface and its terminating language (section 6) | High until implemented and tested |
| Derivation provenance deciding residual instances (RFC-0211) | High teaching and migration cost, smaller for `Copy` types |
| The `derived` mark on super-aspect edges (RFC-0213 section 4) | Moderate: API evolution; less established than Rust's or Haskell's require-only rule |
| `implicit` as a std-only property (RFC-0212) | Moderate: organises the compiler's privilege, does not remove it |
| The undecided-ownership limitation (section 2 rule 3) | Moderate usability risk, acceptable if the diagnostics name the proof path |
| A later observable hook under the same capability | High unless `Copy`'s sealed guarantee stays intact (section 8) |

Acceptance order: RFC-0089 sections 1 to 2.1 (the lattice and keywords), then this RFC's ownership model (sections 1 to
5), then RFC-0207, RFC-0213 and RFC-0212, with the row RFCs (0209 to 0211) later; each remains a separate decision.

## Open questions

1. **A custom implicit hook** as a later extension (section 8): whether to build it, and its spelling.
2. **The class keywords:** contextual spelling, their use on enums, and whether `copy struct` for a generic type
   needs the condition of section 6 in the header.
3. **The default for an unbounded type parameter with respect to `Linear`**: decided in RFC-0089 section 2.2
   (bare `T` possibly linear, `Discard` elaborated, `pub` states it once `linear` ships); this RFC ships the affine
   behaviour, which is equivalent while no linear type exists.
4. **Allocator-placed values and `Clone`.** Out of scope; the allocator RFCs (RFC-0063, RFC-0139) own them.
5. **The spelling and home of the aspect properties** (RFC-0212) and of negative super-aspect entries (RFC-0213).
6. **The `copy_value` native.** A native method inside an aspect impl is already accepted (the record `Clone` in
   `core.mtl` is one). What is missing is the key: `@std.core.copy_value` is not in the closed `NativeKey` set and
   needs a key and a host function whose contract distinguishes a string and an owning array.
7. **Written `Clone` for a residual of a non-`Copy` type.** RFC-0214 (draft) would let the author write one; it is
   not a dependency of this RFC.

---

## Decision

**Outcome:** *(pending)*
