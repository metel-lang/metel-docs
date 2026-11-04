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
| `structural` | satisfied for an instantiation when its parts are (`all`, or `any`) | the per-aspect composition code |
| `excludes B` | no type satisfies both | the hardcoded `Copy`/`Drop` check (RFC-0071 §4) |
| `implicit via S::m` | **std only**: a by-value use of a type satisfying the aspect calls `m` instead of moving | the implicit-copy semantics of `Copy` |

```metel
// sketches; every keyword is a placeholder
aspect ImplicitClone: derived Clone         // RFC-0213: a super-aspect, derived with it
    declared
    structural all
    excludes Drop
    implicit via Clone::clone;

aspect Send auto structural all;
aspect Linear auto structural any;          // RFC-0089, RFC-0096 section 2
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

## 2. `structural`

`structural all` makes the aspect satisfied for `T<args>` when it holds for every field type of
`T<args>`: every field of a struct or record, every field of every variant of an enum, every element
of a tuple or array. `structural any` is satisfied when it holds for some field (RFC-0089's
`Linear`). RFC-0096 section 2 states which quantifier each existing aspect uses; this RFC only needs
the declaration to name it.

- **Exact, per instantiation.** The rule is evaluated on the instantiated field types, not as a
  bound on the type parameters. `struct View<T> { r: &T }` is covered for every `T` when `&T` is.
- **Reaching the fields of a nominal type** needs the row machinery: RFC-0209 (a type's row is
  visible to the templates of an aspect it has granted), RFC-0210 (enums) and RFC-0211 (residuals,
  so the rule is defined on a narrowed value), with RFC-0208 for the row binder.
- **Kinds with no fields to walk** (references, views, closures, function types) are covered by std
  impls on those targets, in the aspect's defining module (`extend<T> &T: ImplicitClone`, a negative
  impl for `&var T`), and by the closure rule of RFC-0134 §1 once function types can satisfy aspects
  (metel-core#739). Tuples need variadic generics (RFC-0125) and arrays a compile-time `N`
  (RFC-0132 §3), or a hardcoded arm until then.
- **With `auto`,** the rule is the grant. With `declared` it is a check on the entry: a concrete
  field type that fails is an error at the declaration, next to the field; one that depends on a type
  parameter is decided per instantiation.

## 3. `excludes`

`aspect A excludes B` means no type satisfies both. The coherence pass (RFC-0060) reports a grant of
the second as an error at that grant, naming both. It generalises RFC-0071 §4. `T: A` entails
`T: !B` for negative reasoning. The exclusion is symmetric: it need only be declared on one side.

## 4. `implicit via S::m` (std only)

`aspect A: S … implicit via S::m` states that a by-value use of a value whose type satisfies `A` is
the call `m(&x)` with the call inserted, and not a move. It requires:
1. `A` refines the aspect `S` that owns `m` (RFC-0213);
2. `m` has the shape `fun m(&self) -> Self`;
3. the declaration is in std. The compiler identifies std by module provenance and rejects
   `implicit` elsewhere. User-declared implicit aspects would let a user hook run silently at every
   use, which RFC-0162's D1 contains, so this is not offered.

A type that satisfies two implicit aspects with different methods is a coherence error. Today there is
one such aspect, `ImplicitClone`.

---

## 5. Existing aspects, expressed

| Aspect | Declaration |
|---|---|
| `ImplicitClone` | `: derived Clone`, `declared`, `structural all`, `excludes Drop`, `implicit via Clone::clone` |
| `Send`, `Sync` | `auto`, `structural all` |
| `Linear` | `auto`, `structural any` |
| `Drop` | plain (no properties) |
| `Clone`, `Debug` | plain, with a derivation (RFC-0207) |

## 6. Worked examples

```metel
struct Point derives ImplicitClone { x: i64, y: i64 }     // declared: the entry is the grant
extend Point: ImplicitClone;                              // error: ImplicitClone is declared; use the declaration
struct H { fd: i64 }
extend H: Drop { fun drop(&var self) { } }
struct H2 derives ImplicitClone { fd: i64 }
extend H2: Drop { fun drop(&var self) { } }              // error: ImplicitClone excludes Drop
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
- **Make `implicit` user-available.** Rejected (section 4).

## Relationship to existing RFCs

- **RFC-0206** — `ImplicitClone` is declared with these properties.
- **RFC-0213** — super-aspects, which `implicit via` and the derived relation need.
- **RFC-0207** — the clauses that grant a `declared` aspect.
- **RFC-0096** — revised so that `auto` is the `auto structural` declaration.
- **RFC-0209 / RFC-0210 / RFC-0211 / RFC-0208** — the row machinery for `structural` on named types.
- **RFC-0060 / RFC-0081 / RFC-0071 §4** — coherence, negative impls and the `Copy`/`Drop` exclusion.
- **RFC-0125 / RFC-0132 / metel-core#739** — tuples, arrays and function types.
- **RFC-0123 / RFC-0186** — the field-wise bound `where ..R: A`, the form of the rule.

## Open questions

1. **Spelling and form.** Clauses on the declaration, a property list, or attributes (RFC-0095).
2. **Which properties users may use.** `implicit` is std only; whether `declared`, `structural` and
   `excludes` are open to user aspects.
3. **`structural any` and the existential rule of `Linear`,** and whether other quantifiers are needed.
4. **Interaction of `declared` and a field of type-parameter type** when the failing instantiation is
   only discovered at a use.
5. **Object safety** of aspects with these properties (`dyn ImplicitClone`).
6. **Provenance of std** for the `implicit` check.
7. **Identity-based aspect resolution** is a prerequisite refactor with no RFC of its own; the
   properties are read from the aspect's declaration, never from its spelling.

---

## Decision

**Outcome:** *(pending)*
