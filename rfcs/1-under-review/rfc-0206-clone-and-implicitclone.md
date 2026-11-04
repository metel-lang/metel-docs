---
id: rfc-0206
title: "Clone and ImplicitClone"
date: '2026-11-02'
status: under-review
updated: '2026-11-03'
tracking: 'https://github.com/metel-lang/metel-core/issues/1785'
---

> **Extracted from RFC-0080 on 2026-11-02**, the way RFC-0162 was extracted from RFC-0157, and
> **redesigned on 2026-11-03** after a prior-art survey (architecture/reports/copy-clone-prior-art-survey.md)
> and an adversarial review. It carries `Clone`, and the implicit-duplication marker that replaces
> `Copy`. Where a duplication marker is written is RFC-0207's; the model and its alternatives are
> RFC-0162's. Nothing here is decided.

> **Status — under review (2026-11-03).** Committed to v0.16.0 as the Clone half of the settlement.

## Summary

`Clone` is the aspect for explicit duplication: `fun clone(&self) -> Self`. `ImplicitClone` is a
marker the compiler knows that refines it: a type that is `ImplicitClone` is duplicated by the
compiler at a by-value use, by calling the type's own `clone`, instead of being moved. The marker
is granted only in the type's declaration, and it is the stronger bound: every `ImplicitClone`
type is `Clone`, and the converse does not hold.

```metel
struct Point derives ImplicitClone { x: i64, y: i64 }     // implicit; the compiler writes Clone
struct Cache: ImplicitClone { data: i64, hits: i64 }      // implicit; the author wrote Clone
struct Doc derives Clone { title: String }                // explicit only: d.clone()
```

`derives` means the compiler wrote the `Clone`, and the colon means the author did. `ImplicitClone`
is an ordinary aspect declared in std with general aspect properties (RFC-0212) over a super-aspect
relation (RFC-0213); the compiler reads those properties, never the aspect's name.

This replaces the pair `Copy`/`Clone`. The name `Copy` is kept for one minor release as a
deprecated alias for `ImplicitClone`. The explanation of the relationship is one sentence:
*`ImplicitClone` is `Clone` that the compiler calls for you.*

---

## Motivation

`Copy` does not currently give a type a `clone`. Measured against the implementation on
2026-11-02:

```metel
struct P { n: i64 }
extend P: Copy;
fun main() { let p := P { n = 1 }; let q := p.clone(); }   // no method `clone` on `P`
```

`T: Clone` rejects such a `P`, and a bodyless `extend P: Clone;` is rejected because the method is
required. A `Copy` struct that needs a `Clone` must hand-write one, and there is no derive. Five
integration fixtures carry a hand-written `clone` callback as scaffolding for exactly this
(metel-core#270).

Three further facts shaped this design:

- **Coverage holes.** `&T` and `[T]` are `Copy` but not `Clone` (`&i64` fails `T: Clone` with
  `T0012`), and array `clone` does not call the element's `clone` while record `clone` does. A
  rule of the form "every `Copy` type is `Clone`" cannot be left to std.
- **The interpreter ignores written clones.** It deep-clones every by-value use, so a hand-written
  `clone` never runs on an implicit copy today.
- **Rust's pair has a documented friction.** `Copy: Clone` requires both impls, `Clone` may diverge
  from the copy, and derive over-approximates generic bounds (the `Copy` documentation says so).

The survey found one precedent that fits: Mojo's `Copyable` (explicit, one hook) with an
`ImplicitlyCopyable` marker that refines it, "ensuring only one definition for the logic of how a
type is copied", and Swift's rule that copyability is fixed on the declaration.

---

## 1. `Clone`

```metel
aspect Clone {
    fun clone(self: &Self) -> Self;
}
```

`clone` returns a new owned value of the same type and the caller keeps the original; no move
occurs. The contract is Rust's: *another value of this type*. A reference or a view is cloned by
cloning the reference or view, not the referent. A handle that aliases shared state is `Share`
(RFC-0158), a separate aspect, and is not `Clone` unless its type says so.

A type gets a `Clone` by writing one (`extend T: Clone { … }`), by a `derives Clone` request
(RFC-0207), or through `derives ImplicitClone`, which derives it along with the marker (section 2).

---

## 2. `ImplicitClone`

`ImplicitClone` is declared in std as an ordinary aspect that refines `Clone`, using the aspect
properties of RFC-0212 and the super-aspect relation of RFC-0213 (the spelling is a sketch):

```metel
aspect ImplicitClone: Clone, !Drop          // RFC-0213: requires Clone, excludes Drop
    declared                                // RFC-0212: granted only in a declaration
    implicit via Clone::clone;              // RFC-0212: std only; names the hook
```

It is the stronger bound: `T: ImplicitClone` accepts fewer types than `T: Clone`.

**No special case by name.** Every behaviour below follows from one of those properties. The compiler
reads them from the aspect's declaration by identity and never tests the spelling "ImplicitClone" or
"Copy". The one property that is a language semantic and not a constraint is `implicit via`
(RFC-0212 section 3): it is the exception that remains, stated as a declaration property, and it is
std only. Today the compiler identifies `Copy` by the string `"Copy"` at about 38 sites in the
frontend (`aspect_name == "Copy"`, `infer_type_satisfies_aspect(…, "Copy", …)`); replacing them is the
prerequisite refactor of section 6.

**Legality.**
1. *Granted only in the declaration.* A named type is `ImplicitClone` only through its declaration:
   `struct P: ImplicitClone { … }` or `struct P derives ImplicitClone { … }` (RFC-0207). An
   `extend T: ImplicitClone;` is an error with a fix-it that moves it.
2. *It requires `Clone`, and the clause says where it comes from.*
   - `struct P: ImplicitClone` (the colon) promises that the type's own `Clone` may be called
     implicitly. A `Clone` must already exist for the type, written (`extend P: Clone { … }`) or
     requested (`derives Clone`). If none exists it is an error with two fix-its: write one, or use
     `derives ImplicitClone`.
   - `struct P derives ImplicitClone` always derives the `Clone` too (RFC-0213 section 4):
     it is `: ImplicitClone derives Clone`. With a written `extend P: Clone` it overlaps the
     derived impl and is an error (`T0015`); the author's own `Clone` is the colon form.
   The colon never generates an impl; `derives` always does.
3. *The predicate is exact and conjunctive.* For an instantiation `T<A>`, `T<A>: ImplicitClone`
   holds when every field's type is `ImplicitClone`, and `T<A>: Clone` holds, and the type is not
   `Drop`. It is evaluated per instantiation, so `struct View<T>: ImplicitClone { r: &T }` is
   `ImplicitClone` for every `T`. A written `Clone` covering narrower instantiations makes
   `ImplicitClone` hold only there; the error appears where an implicit copy is needed. This is the
   declarative meaning: the least solution of those conditions over concrete instantiations. The
   analysis of a generic body (ADR-0063) is a **sound approximation** of it: it answers yes, no or
   unknown, and unknown never permits a copy, so the checker may reject a program the rule accepts
   and never accept a copy the rule forbids. The first implementation decides a stated fragment
   (conditions on parameters, on nested applications of provable types, and on shared references to
   abstract types) and answers unknown outside it (section 6, step 2).
4. *The implicit copy is the call.* A copy site (below) of an `ImplicitClone` value calls the type's
   `clone`. A type that is not `ImplicitClone` is moved. A written `clone` is therefore
   run at an implicit copy (Mojo's choice), and nothing is sealed to a bitwise body.
5. *`Drop` excludes it, and only it.* A type that implements `Drop` cannot be `ImplicitClone`.
   `Clone` on a `Drop` type is allowed.
6. *Residuals.* A residual of an `ImplicitClone` type is `ImplicitClone` only if it is also `Clone` by
   the rules of RFC-0211 (a template, or a residual impl once RFC-0214 exists); a type with a written
   `Clone` therefore has projections that move. The residual's hook is its own `Clone`.
7. *Entailment.* `T: ImplicitClone` entails `T: Clone` in the checker and in the abstract analysis
   of generic bodies, by the super-aspect relation of the declaration (RFC-0213).

**Where an implicit copy happens (copy sites).** These rules are normative; the slogan "a by-value use
is `x.clone()`" is not.
1. A **place read in value position** is a copy site when the place's type is `ImplicitClone`, and a
   move otherwise. Value position means a use that would otherwise take the value out of the place:
   `let b := a`, `f(a)`, `return a`, `S { f = a }`, `[a, a]`, a by-value `self` argument, a by-copy
   capture, and the same for a field `a.x`, an index `a[i]` and a dereference `*r`. A borrow (`&a`, a
   `&self` receiver) reads nothing.
2. A **temporary is transferred, never cloned.** Calls, literals, constructors, block results and the
   result of an explicit `.clone()` are temporaries, so `let d := a.clone();` runs the hook once. A field
   read from an owned temporary (`make().x`) transfers that field.
3. **No elision of the last use.** `return x`, or the last use of `x`, is still a copy site, because a
   written `clone` can change the value. An optimiser may skip a clone only for an intrinsically
   cloneable type (leaf clones, below), where the skip is unobservable.
4. **A generic body decides at its definition.** Whether a read is a copy or a move is decided by the
   bounds visible there. `fun relay<T>(x: T) -> T { x }` moves, even when instantiated with an
   `ImplicitClone` type; the same read under `T: ImplicitClone` is a copy site. Reconstructing the body
   per instantiation reuses the definition's decisions and never revisits them, so generic and
   non-generic code behave alike.
5. **The hook runs with shared access and in a fixed order.** The base and index of a place expression
   are evaluated once, left to right, then `clone` is called with `&self`, so the source place is
   untouched whatever the hook does. A panic in the hook propagates like any panic and leaves no
   partial result. A hook may call arbitrary code, including another copy site, so the interpreter
   holds no borrow of its environment while it runs.

The evaluator therefore does not clone at binding and assignment. Elaboration marks each copy site in the
typed AST and the evaluator calls the clone method only there (today `deep_clone_value` runs at every
`let`, assignment, pattern binding and `for` iterable, for moves as well as copies, which is harmless
only while a clone is unobservable).

**Recursion and termination.** A recursive type goes through `List`, `Option`, `Result` or a reference
(there is no `Box`).
1. **Predicate queries are inductive.** A cycle in an `ImplicitClone` (or any marker) query is "no". This
   is the least solution of rule 3, and it costs nothing: `List`, `Option` and `Result` are not
   `ImplicitClone`, a reference is always `ImplicitClone` without being inspected, and a cycle by value
   would be an infinite value.
2. **Derivation conditions are coinductive on goals that repeat exactly.** `enum Tree derives Clone {
   Leaf, Node(List<Tree>) }` needs `Tree: Clone`, which needs `List<Tree>: Clone`, which needs
   `Tree: Clone` again. The solver assumes the impl being derived while it checks the fields, as Rust
   and Haskell do. The derived `clone` is a recursive function over finite values, so termination comes
   from the data and not from the proof. This covers regular recursion such as `Node<T> { next:
   Option<Node<T>>, v: T }`.
3. **Coinduction never applies to a negative goal** (`!Drop`, `T: !B`) **or to a marker aspect.** A cycle
   through one is unknown, never a proof.
4. **Expanding recursion is rejected.** `struct Grow<T> derives Clone { rest: Option<Grow<List<T>>> }`
   grows its argument at every step. A size and depth limit gives an error at the declaration with the
   fix-it "write the impl", and unknown in the abstract analysis.
5. **The derived body** is a per-field call, so a recursive `clone` recurses through the impl and needs
   no unrolling. A written impl whose where clause mentions its own type is the ordinary case: the impl
   exists and is not unrolled.

**Built-in kinds: std impls where the target can be named, compiler rules where it cannot.**

| Kind | `ImplicitClone` | `Clone` |
|---|---|---|
| Integers, floats, `boolean`, `Char`, unit | yes, a std impl (`extend i64: ImplicitClone;`, as `extend i64: Copy;` is today) | the value: a leaf native (below) |
| Shared references `&T`, views `[T]` | yes, for every `T`: `extend<T> &T: ImplicitClone;` in std | the reference or view copied: a leaf native |
| `&var T` | never | none |
| Tuples, `[T; N]`, records | when every part is (compiler rule until variadics and const `N`) | field-wise, guaranteed whenever `ImplicitClone` |
| Closures | when every capture is (RFC-0134 §1) | by captures, guaranteed |
| Written function types | move-only (RFC-0166) | none |
| `String`, `List`, `Option`, `Result` | no | the std impls of §3 |

Unit becomes a std impl like the scalars, which fixes the disagreement between the bound and the move
checker (metel-core#1784) without a special case. Because std provides `Clone` with every
`ImplicitClone` impl of a leaf and the compiler guarantees it for every `ImplicitClone` compiler-rule
kind, the coverage holes of the Motivation cannot recur.

**Leaf clones and the representation copy.** A leaf `Clone` is a std native, not Metel code:
`extend i64: Clone { native(@std.core.copy_value) fun clone(&self) -> Self; }`, one host function for
every scalar, `String`, `&T` and `[T]`. A native body cannot panic, reenter or allocate observably, and
producing its result does not call `clone` again, so "an implicit copy is a call to `clone`" has a base
case. A *derived* `clone` is defined as a per-field call to each field's `clone` (the semantics of
today's record `Clone`, extended to structs, enums and arrays). A type is **intrinsically cloneable**
when its `Clone` is a leaf native or derived and every field type is intrinsically cloneable, decided
per instantiation (recursive types coinductively: a derived clone over finite values is well defined).
The interpreter may perform the representation copy (`deep_clone_value`) for an intrinsically cloneable
type, and must dispatch through the `clone` method otherwise. That is not a second semantics: a derived
clone over leaf natives is by definition the representation copy, so the choice is unobservable. Any
written `clone` among the reachable field types makes the type not intrinsically cloneable.

**The cost convention and what the language relies on.** An implicit copy runs user code, so a `clone`
on an `ImplicitClone` type is expected to be cheap, total and free of external side effects. That is a
convention against surprise in cost and value at every by-value use, not a law the compiler may assume.
1. The language relies on nothing about a hook's result except that it is a value of the type. `Clone`
   keeps its contract of RFC-0206 section 1, "another value of this type", with no equality law: a
   `clone` may reset a field (the `Cache` example) or even change a counter.
2. Insertion and elision of the call are therefore observable. Beyond the copy-site rules, an
   implementation, interpreter or compiled backend, must preserve the number and order of hook calls
   for any type that is not intrinsically cloneable.
3. The first implementation neither checks nor lints the convention; detecting an allocating or
   panicking body without effect information would be guesswork.
4. **A future effect bound is a new restriction with a migration, not the completion of this
   contract.** It would restrict a hook's effects (panic, I/O, allocation) and stop a type whose
   `clone` has them from being `ImplicitClone`. It would not make a clone value-preserving. It is a
   language change needing its own RFC and a migration note.

**Bounds in generic code.** Generic code that may copy should bound on `Clone` and call `.clone()`
where the copy is intended, and bound on `ImplicitClone` only where an implicit copy is the point
(for example numeric code over cheap scalars). A bound on `ImplicitClone` promises callers that every
by-value use may run the type's `clone`; Mojo's documentation gives the same advice for
`ImplicitlyCopyable` (prior-art report, section 11.9).

**`!Drop` is a policy.** Rule 5 does not follow from soundness, as Rust's `Copy`/`Drop` rule does,
because the hook can duplicate a resource. It keeps resource-owning types from being copied silently,
and it is one entry in the super list (`!Drop`). Deleting that entry is a one-line edit but not a
one-line change: it removes the evidence that makes impls such as `extend<T: ImplicitClone> W<T>: A` and
`extend<T: Drop> W<T>: A` disjoint, so it can turn valid programs into `T0015`, and it lets a type be both
(RFC-0213 section 3). A negative super entry is part of the aspect's contract. Mojo allows
a destructor on a type with a user copy initializer; that point is not confirmed (report, 11.13).

**Third-party types.** A type from another module cannot be made `ImplicitClone` by its user, because
the grant is `declared`. This is intended: whether a type is cheap to copy is its author's statement.
A wrapper type in the user's module can be `ImplicitClone` over the foreign type when that type is.

---

## 3. Standard `Clone` impls

Measured on 2026-11-02:

| Type | `Clone` today | Plan |
|---|---|---|
| Primitives, `String` | yes | the body becomes the leaf native `copy_value`; scalars also get `ImplicitClone` impls (`String` does not) |
| `[T; N]` | yes, but it does not call the element's `clone` | field-wise through the element's `clone`; the discrepancy with records is a defect to fix |
| Anonymous records | yes, field-wise: `extend<record R> { ..R }: Clone where ..R: Clone` (RFC-0123) | unchanged |
| Named `record` | yes today, the same field-wise impl | takes a `derives Clone` or `: ImplicitClone` entry like a `struct`; a plain `record P` is not cloneable |
| Tuples | **no** | a structural arm, hardcoded like tuple `Copy` (metel-core#263), until variadic generics (metel-core#794) |
| `Option`, `Result`, `List` | **no** | `extend<T: Clone> Option<T>: Clone`, and the same for the others (metel-core#270) |
| A named `struct` or `enum` | only if the user writes one | section 4 |
| `&T`, `[T]`, closures | not `Clone` today | by the built-in rules of section 2 |

---

## 4. `Clone` for a user type

- **Written:** `extend P: Clone { fun clone(&self) -> P { … } }`, always available and the way to
  customise (skip a cache field, reset a counter).
- **Derived:** `struct P derives Clone { … }`. The derived `clone` clones each field, so it is deep
  for owning fields, and a field type without `Clone` makes the entry an error at the declaration.
  The derived impl applies at an instantiation when every field's type is `Clone` there (the exact
  condition of RFC-0207 section 2), which is what lets `View<T> { r: &T }` be `ImplicitClone` for
  every `T`.
  For an enum it matches the active variant. Written and derived impls of the same aspect for one
  type overlap and are an error.
- **Derived with the marker:** `derives ImplicitClone`, section 2 rule 2. The colon form needs one of
  the other three.
- **Not automatic.** A type with none of these has no `Clone`, and `: ImplicitClone` alone is an error: whether a named type may be
  duplicated is a statement about what it means, not a consequence of its fields, so an
  accidental `Clone` (for example on a handle type whose fields happen to be `Clone`) is not
  provided.

The derivation itself is native in the first implementation, as it already is for records; a
comptime derivation replaces the native one when RFC-0092 and RFC-0093 allow.

---

## 5. Names and migration

- **`Clone`** keeps its name and its Rust contract.
- **`ImplicitClone`** replaces `Copy`. `Copy` remains for one minor release as a deprecated alias
  that is accepted wherever `ImplicitClone` is, with a warning and a fix-it that rewrites
  `extend X: Copy;` to the colon-list entry and `T: Copy` to `T: ImplicitClone`.
- **The function-type qualifier** `copy` and the keyword `once` (RFC-0163, RFC-0134) keep their
  spelling. The qualifier now names the property whose aspect is `ImplicitClone`; the mismatch is
  recorded, and a shipped qualifier is not renamed here.
- **Generic code** should bound on `Clone` and call `.clone()`; `T: ImplicitClone` is for code
  that needs by-value reuse of a type. This is Mojo's guidance for `ImplicitlyCopyable`.
- **`Share`** (RFC-0158) is unaffected, since the name `Clone` stays.

---

## 6. Implementation staging and dependencies

There is no first stage that carries the semantics with a special case. The settlement waits for the
general features, in this order:

1. **Identity-based aspect resolution.** Replace the string-keyed `"Copy"` sites by an aspect
   identity lookup (the ADR-0054/0066/0067 line). A prerequisite refactor, no RFC.
2. **An obligation solver for abstract types** (metel-core#1810, a spike first). Goals
   `type: aspect` over abstract types, answered yes, no or unknown with a witness (the selected impl
   or derivation), from assumptions and their super-aspect closure, impls and templates with their
   where clauses, and the compiler rules. Super-aspect entailment and the structural template are
   instances of it, and elaboration carries the witness so a copy site records the `clone` it calls.
   Recursion and cycles are a separate decision (RFC-0210, #1809 M2). If the spike shows it too large
   for the release, the fallback is the stopgap (a nominal application that mentions an abstract
   parameter is a move unless proven) with the solver completed in a later minor.
3. **The declaration clauses** (RFC-0207): the colon list and `derives`.
4. **Super-aspects** (RFC-0213), including entailment through the solver and negative closure.
5. **Derivations** (RFC-0207): native `Clone` first; the uniform super-aspect derivation of RFC-0213 section 4.
6. **Aspect properties** (RFC-0212): `declared`, `implicit via`, and the std-written structural rule (a row template, RFC-0123), with the row
   machinery it needs for named types (RFC-0209, RFC-0210, RFC-0211, RFC-0208).
7. **Built-in kinds as impls:** references and views, then tuples (RFC-0125) and arrays (RFC-0132 §3),
   then closures and function types (metel-core#739, RFC-0134).
8. **Then `ImplicitClone` itself,** declared in std, with `Copy` as a deprecated alias.

Work specific to this RFC and independent of that order:
- The representation copy is used only for intrinsically cloneable types (section 2, leaf clones); a type
  with a written `clone` among its reachable fields is cloned by dispatching to the method, as the record
  `Clone` does today. `deep_clone_value` does not dispatch and must not be used for such types.
- An implicit copy of a type with a hand-written `Clone` calls it; the evaluator must dispatch to the
  written `clone` at by-value uses of such types.
- The move check and the abstract analysis treat an implicit copy as a call to `T::clone` under
  the entailment of section 2, rule 7.
- The std repairs: array and tuple `Clone`, the reference and view cases, the unit fix, and #270's
  `Option`, `Result` and `List`.

---

## 7. Worked examples

```metel
struct Point derives ImplicitClone { x: i64, y: i64 }
let a := Point { x = 1, y = 2 };
let b := a;                    // a.clone() inserted; a is still valid
let c := a;

struct Wrapper<T> derives ImplicitClone { v: T }
// Wrapper<i64>: ImplicitClone and Clone; Wrapper<String>: Clone only (String is Clone, not ImplicitClone);
// Wrapper<NoClone>: neither (NoClone has no Clone)

struct Id: ImplicitClone derives Clone { n: i64 }          // accepted: the long form of `derives ImplicitClone`

struct Cache: ImplicitClone { data: i64, hits: i64 }
extend Cache: Clone { fun clone(&self) -> Cache { Cache { data = self.data, hits = 0 } } }
// accepted: the written clone runs at every implicit copy of a Cache

struct H { fd: i64 }
extend H: Drop { fun drop(&var self) { } }
extend H: Clone { fun clone(&self) -> H { H { fd = dup(self.fd) } } }     // Clone on a Drop type: fine
// struct H2: ImplicitClone { fd: i64 } with extend H2: Drop { … }       // error: ImplicitClone: !Drop

struct NoClone2: ImplicitClone { n: i64 }                   // error: no Clone; write one or use `derives ImplicitClone`
struct Both derives ImplicitClone { n: i64 }
extend Both: Clone { fun clone(&self) -> Both { Both { n = 0 } } }   // error T0015: overlaps the derived Clone; write `: ImplicitClone`
extend Point: ImplicitClone;                                // error: granted only in the declaration
```

---

## 8. Alternatives considered

- **`Copy` and `Clone` linked by `provides` with overlapping impls** (the earlier draft of this RFC
  and RFC-0207). Rejected after the adversarial review: it needs a selection rule over overlapping
  impls, an uncheckable equality invariant between two bodies, and an R1-to-R2 migration that negative
  bounds break. Super-aspects are used here, but as a plain refinement relation (RFC-0213) with no
  second impl.
- **A sealed bitwise body.** Rejected: a user-writable hook is what makes the refinement meaningful,
  and an effect bound can restrict it later.
- **An explicit duplication operator and no implicit marker** (`copy x`). Set aside: it moves the
  question to which types may be implicit anyway, since generic numeric code needs a bound.
- **A bound `T: ImplicitClone` that accepts any `Clone` type.** Rejected: it would make the same name
  mean two things and let the author of a generic function consent for a type that never opted in.
- **A lang-item attribute for one aspect, or a compiler-known marker** (earlier drafts of this RFC).
  Rejected by the language owner: each is an exception keyed to a name. The aspect properties of
  RFC-0212 and the relation of RFC-0213 replace them, at the cost of the dependency chain of
  section 6; the review had judged that chain heavy for one customer, and the owner prefers it to an
  exception.
- **The string-keyed special case that exists today.** Rejected: about 38 sites test the spelling
  "Copy", which cuts against the identity-based resolution of ADR-0054, ADR-0066 and ADR-0067.
- **Inference of implicitness from fields** (Swift's default for structs). Rejected: it brings back
  the hazard that adding a field flips every use from copy to move.

---

## Relationship to existing RFCs

- **RFC-0162** — the model, the design space and the survey; this RFC is its accepted-direction
  specification of the two aspects.
- **RFC-0207** — the colon list and the `derives` clause that carry the grant and the derivation.
- **RFC-0212** — the aspect properties (`declared`, `implicit via`) that
  `ImplicitClone` is declared with.
- **RFC-0213** — super-aspects, which give `ImplicitClone: Clone, !Drop`.
- **RFC-0096** — auto aspects, revised so that `auto` is a declaration of RFC-0212.
- **RFC-0071 §2** — states the one predicate; its `Copy` becomes `ImplicitClone`.
- **RFC-0134 / RFC-0163 / RFC-0166** — closures and function types: copyable by captures; the `copy`
  qualifier; written function types move-only.
- **RFC-0158** — `Share`, unchanged.
- **RFC-0080** — the source of `Clone`; it keeps `Deref`, `Send` and `Sync`.
- **RFC-0093 / RFC-0092** — the derive mechanism and comptime that replace the native derivation.
- **RFC-0097** — the orphan rule for bare-parameter blanket impls; no longer needed for this.
- **Effects design** — the future bound on an implicit `clone`.

## Open questions

1. **The exact effect bound** and when `ImplicitClone` starts to enforce it (with the effect system).
2. **How long the `Copy` alias lasts** (one minor release is proposed).
3. **Allocator-placed values and `Clone`.** Out of scope; the allocator RFCs (RFC-0063, RFC-0139) own
   them.
4. **A scoped implicit mode** for generic code over `Clone` types, if `.clone()` proves too noisy;
   deferred with the effects work.
5. **The spelling and home of the aspect properties** (RFC-0212) and of negative super-aspect entries (RFC-0213).
6. **A native method in an aspect impl block.** Existing std natives are inherent methods (`String`,
   `List`). Whether `native(..) fun clone(&self) -> Self;` is accepted inside `extend T: Clone { }`
   must be confirmed; if not, the body calls an inherent native helper, or the checker accepts it in std.
7. **Written `Clone` for a residual.** A projection of a type with a written `Clone` is neither `Clone` nor
   `ImplicitClone` today (RFC-0211 rule 2). RFC-0214 (draft) would let the author write the impl for a
   residual shape, and RFC-0211's super-aspect recheck then gives the projection `ImplicitClone`. Not a
   dependency of this RFC.

---

## Decision

**Outcome:** *(pending)*
