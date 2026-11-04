---
id: rfc-0212
title: "Aspect Declaration Properties"
date: '2026-11-04'
status: under-review
updated: '2026-11-04'
tracking: 'https://github.com/metel-lang/metel-core/issues/1795'
---

> **Written 2026-11-04** as part of the `Copy`/`Clone` settlement (RFC-0206). The compiler today
> treats `Copy`, `Send`, `Sync` and `Linear` as special cases by name; this RFC lets an aspect
> declaration state the properties those special cases encode, so that `ImplicitClone` is an
> ordinary std declaration. Nothing here is decided.

> **Status — under review (2026-11-04).** first draft opened for review

## Summary

An aspect declaration may state four properties. Each one replaces behaviour that is hardcoded for
a named aspect today.

| Property | Meaning | Replaces |
|---|---|---|
| `declared` | granted only through a type's declaration clauses (RFC-0207), never by `extend` | the `"Copy"` special case in coherence and `check_copy_impl_eligibility` |
| `auto` | granted structurally with no entry; a type opts out with a negative impl (`extend T: !A;`) | RFC-0096's closed list for `Send`, `Sync`, `Linear` (**deferred**: the Send/Sync/Linear revision is not part of the ImplicitClone settlement; `ImplicitClone` does not use `auto`) |
| `implicit via S::m` | **std only**: a by-value use of a type satisfying the aspect calls `m` instead of moving | the implicit-copy semantics of `Copy` |

```metel
// sketches; every keyword is a placeholder
aspect ImplicitClone: derived Clone, !Drop  // RFC-0213: Clone derived with it, Drop excluded
    declared
    implicit via Clone::clone;

aspect Send auto;                           // deferred with the Send/Sync/Linear revision (RFC-0096)
aspect Linear auto;                         // its existential rule is part of that revision
aspect Validated declared;                  // a user marker: a checked-by-nothing promise
```

`implicit` is the one property that is a language semantic and not a constraint. It is the single
exception that remains, stated as a declaration property read by identity and available to std
only. Everything else is a general feature other aspects can use.

---

## Motivation

The `Copy`/`Clone` settlement (RFC-0162, RFC-0206) first proposed a compiler-known marker for
implicit duplication, then a lang-item attribute for it. Both are exceptions keyed to one aspect.
The same pattern already exists elsewhere:

- **`Copy` is identified by the string `"Copy"` at about 38 sites** in the frontend
  (`aspect_name == "Copy"`, `infer_type_satisfies_aspect(…, "Copy", …)`).
- **RFC-0096 §1 proposes a closed compiler-intrinsic list** for `Send`, `Sync` and `Linear`, and
  notes that `AspectDecl` has no marker field for it.
- **`Copy`/`Drop` exclusion is hardcoded** in coherence (RFC-0071 §4).
- **Structural satisfaction** (tuples, records, arrays) is a hardcoded arm per aspect.

The language owner's position is to prefer a general feature over an exception even at the cost of
dependencies. This RFC collects the aspect-level properties; RFC-0213 supplies super-aspects and
RFC-0207 the declaration clauses.

---

## 1. `declared`

A `declared` aspect is satisfied by a named type only if the type's declaration says so, through the
colon list (`struct P: A`) or `derives A` (RFC-0207). An `extend T: A` is an error with a fix-it.

- **Targets with no declaration** (primitives, tuples, arrays, anonymous records, references)
  cannot carry a clause. Impls for them are allowed, and only in the aspect's defining module (the
  orphan rule keeps them with the aspect's author). A named type can never be granted this way.
- **The grant is in the type's own module,** so the orphan rule (`T0014`) holds trivially, and the
  aspect cannot be granted to a named type you do not own.
- **Refinement of the condition is not provided.** The condition is the aspect's structural rule
  (section 2), evaluated exactly, so there is nothing to refine.

## 2. The structural rule is a template, not a property

There is no `structural` or `excludes` property. The field-wise rule of `ImplicitClone` is written in
std as a conditional template over the type's row, in the form RFC-0123 and RFC-0186 give (`where ..R:
A`), and an exclusion is a negative super-aspect entry (RFC-0213 section 3, `aspect ImplicitClone:
Clone, !Drop`).

- **Exact, per instantiation.** The condition is evaluated on the instantiated field types, not as a
  bound on the type parameters. `struct View<T> { r: &T }` is covered for every `T` when `&T` is.
- **Reaching the fields of a nominal type** needs the row machinery: RFC-0209 (a type's row is
  visible to the templates of an aspect it has granted), RFC-0210 (enums) and RFC-0211 (residuals,
  so the rule is defined on a narrowed value), with RFC-0208 for the row binder.
- **Kinds with no fields to walk** (references, views, closures, function types) are covered by std
  impls on those targets, in the aspect's defining module (`extend<T> &T: ImplicitClone`, a negative
  impl for `&var T`), and by the closure rule of RFC-0134 §1 once function types can satisfy aspects
  (metel-core#739). Tuples need variadic generics (RFC-0125) and arrays a compile-time `N`
  (RFC-0132 §3), or a hardcoded arm until then.
- **Errors name their cause.** A failed structural check names the aspect, the instantiation and the
  field whose type fails (`Wrapper<String>: ImplicitClone: field v: String is not ImplicitClone`), at the
  declaration when the field type is concrete and at the use that needs the instance otherwise, with the
  instantiation in the message. C++'s late, distant template errors are the cautionary precedent.
- **With `declared`** the template is a check on the entry: a concrete field type that fails is an
  error at the declaration, next to the field; one that depends on a type parameter is decided per
  instantiation.
- **`auto` with a structural rule** (`Send`, `Sync`, `Linear`, including the existential rule of
  `Linear`) is deferred with the Send/Sync/Linear revision of RFC-0096. This RFC does not specify it.

## 3. `implicit via S::m` (std only)

`aspect A: S, … implicit via S::m` states that a by-value use of a value whose type satisfies `A` is
the call `m(&x)` with the call inserted, and not a move. It requires:
1. `A` refines (transitively) the aspect `S` that owns `m` (RFC-0213);
2. `m` has the shape `fun m(&self) -> Self`;
3. the declaration is in std. The compiler identifies std by module provenance and rejects
   `implicit` elsewhere. User-declared implicit aspects would let a user hook run silently at every
   use, which RFC-0162's D1 contains, so this is not offered.

The hook is named, not inferred from method shapes. Inference would make the meaning of `implicit`
depend on every other method of the super-aspects: a second `fun (&self) -> Self` added to `Clone`
would silently change or break the hook. Naming it makes the declaration say what an implicit copy
calls, and a rename or a second candidate cannot change it unnoticed. The compiler reads the named
method by identity, not by spelling.

A type that satisfies two implicit aspects with different hooks is a coherence error. Today there is
one such aspect, `ImplicitClone`. The reserved effect bound (RFC-0206) belongs to the hook's
signature.

---

## 5. Existing aspects, expressed

| Aspect | Declaration |
|---|---|
| `ImplicitClone` | `: Clone, !Drop`, `declared`, `implicit via Clone::clone`; the structural rule is a std row template |
| `Send`, `Sync`, `Linear` | `auto` (their structural rules deferred, section 2) |
| `Drop` | plain (no properties) |
| `Clone`, `Debug` | plain, with a derivation (RFC-0207) |

## 6. Worked examples

```metel
struct Point derives ImplicitClone { x: i64, y: i64 }     // declared: the entry is the grant
extend Point: ImplicitClone;                              // error: ImplicitClone is declared; use the declaration
struct H { fd: i64 }
extend H: Drop { fun drop(&var self) { } }
struct H2 derives ImplicitClone { fd: i64 }
extend H2: Drop { fun drop(&var self) { } }              // error: ImplicitClone: !Drop
struct Token { id: i64 }
extend Token: !Send;                                      // opt-out of an auto aspect: the existing negative impl
```

---

## 7. Alternatives considered

- **A lang-item attribute for one aspect** (the previous draft of RFC-0206). Rejected: it is still an
  exception keyed to a name, and the other special aspects would each need their own.
- **Keep RFC-0096's closed list.** Rejected: the same exception for three more aspects.
- **Properties as attributes** (`#declared`). Possible; RFC-0095 is the home, and the properties
  change what the compiler accepts, which attributes are meant not to do. Open question 1.
- **Make `implicit` user-available.** Rejected (section 3).
- **Infer the hook from the shape `fun (&self) -> Self` and drop `via`.** Tried and reversed on
  2026-11-04: it is fragile against a second method of that shape in a super-aspect.

## Relationship to existing RFCs

- **RFC-0206** — `ImplicitClone` is declared with these properties.
- **RFC-0213** — super-aspects, which `implicit` and the exclusion need.
- **RFC-0207** — the clauses that grant a `declared` aspect.
- **RFC-0096** — its `auto` revision is deferred; see section 2.
- **RFC-0209 / RFC-0210 / RFC-0211 / RFC-0208** — the row machinery for the structural template on named types.
- **RFC-0060 / RFC-0081 / RFC-0071 §4** — coherence, negative impls and the `Copy`/`Drop` exclusion.
- **RFC-0125 / RFC-0132 / metel-core#739** — tuples, arrays and function types.
- **RFC-0123 / RFC-0186** — the field-wise bound `where ..R: A`, the form of the rule.

## Open questions

1. **Spelling and form.** Clauses on the declaration, a property list, or attributes (RFC-0095).
2. **Which properties users may use.** `implicit` and `auto` are std only. `declared` is open to user
   aspects (RFC-0207 rule 1): a user `declared` marker is admitted by the colon list as an unchecked
   promise, and `extend T: A;` for it is an error.
3. **`auto` and the structural rules of `Send`, `Sync`, `Linear`** (including `Linear`'s existential rule): deferred with the RFC-0096 revision.
4. **Interaction of `declared` and a field of type-parameter type** when the failing instantiation is
   only discovered at a use.
5. **Object safety** of aspects with these properties (`dyn ImplicitClone`).
6. **Provenance of std** for the `implicit` check.
7. **Identity-based aspect resolution** is a prerequisite refactor with no RFC of its own; the
   properties are read from the aspect's declaration, never from its spelling.

---

## Decision

**Outcome:** *(pending)*
