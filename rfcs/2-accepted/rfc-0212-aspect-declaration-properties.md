---
id: rfc-0212
title: "Aspect Declaration Properties"
date: '2026-11-04'
status: accepted
updated: '2026-11-05'
tracking: 'https://github.com/metel-lang/metel-core/issues/1795'
---

> **Written 2026-11-04** as part of the `Copy`/`Clone` settlement (RFC-0206). The compiler today
> treats `Copy`, `Send`, `Sync` and `Linear` as special cases by name; this RFC lets an aspect
> declaration state the properties those special cases encode, so that `Copy` is an ordinary std
> declaration (revised 2026-11-05: the implicit copy is sealed, so `implicit` has no hook). Nothing here is decided.

> **Status — under review (2026-11-04).** first draft opened for review

> **Status — accepted (2026-11-05).** Ratified in the Copy and Clone settlement sweep (metel-core#1824); spellings ratified by the language owner 2026-11-05

## Summary

An aspect declaration may state three properties (`declared`, `auto`, `implicit`; `auto` is deferred). Each one replaces behaviour that is hardcoded for
a named aspect today.

| Property | Meaning | Replaces |
|---|---|---|
| `declared` | granted only through a type's declaration clauses (RFC-0207), never by `extend` | the `"Copy"` special case in coherence and `check_copy_impl_eligibility` |
| `auto` | granted structurally with no entry; a type opts out with a negative impl (`extend T: !A;`) | RFC-0096's closed list for `Send`, `Sync`, `Linear` (**deferred**: the Send/Sync/Linear revision is not part of the Copy settlement; `Copy` does not use `auto`, it is opt-in) |
| `implicit` | **std only**: a by-value use of a type satisfying the aspect copies its representation instead of moving | the implicit-copy semantics of `Copy` |

```metel
// sketches; every keyword is a placeholder
aspect Copy: derived Clone, !Drop           // RFC-0213: Clone derived with it, Drop excluded (and Linear once it exists)
    declared
    implicit;

aspect Send auto;                           // deferred with the Send/Sync/Linear revision (RFC-0096)
aspect Linear auto;                         // its existential rule is part of that revision
aspect Validated declared;                  // a user marker: a checked-by-nothing promise
```

`implicit` is the one property that is a language semantic and not a constraint. It is the single
exception that remains, stated as a declaration property read by identity and available to std
only. It means one thing: a by-value use copies the representation (RFC-0206 section 2), with no user code.
Encoding it as declaration data organises and exposes the compiler's privileged operation (it is inspectable and
keyed by identity); it does not make it ordinary library semantics. Unsupported property combinations are
rejected. Everything else is a general feature other aspects can use.

---

## Motivation

The `Copy`/`Clone` settlement (RFC-0162, RFC-0206) first proposed a compiler-known marker for
implicit duplication, then a lang-item attribute for it, then a hook. Both are exceptions keyed to one aspect.
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

There is no `structural` or `excludes` property. The field-wise rule of `Copy` is written in
std as a conditional template over the type's row, in the form RFC-0123 and RFC-0186 give (`where ..R:
A`), and an exclusion is a negative super-aspect entry (RFC-0213 section 3, `aspect Copy:
derived Clone, !Drop`).

- **Exact, per instantiation.** The condition is evaluated on the instantiated field types, not as a
  bound on the type parameters. `struct View<T> { r: &T }` is covered for every `T` when `&T` is.
- **Reaching the fields of a nominal type** needs the row machinery: RFC-0209 (a type's row is
  visible to the templates of an aspect it has granted), RFC-0210 (enums) and RFC-0217 (residuals,
  so the rule is defined on a narrowed value), with RFC-0208 for the row binder.
- **Kinds with no fields to walk** (references, views, closures, function types) are covered by std
  impls on those targets, in the aspect's defining module (`extend<T> &T: Copy`, a negative
  impl for `&var T`), and by the closure rule of RFC-0134 §1 once function types can satisfy aspects
  (metel-core#739). Tuples need variadic generics (RFC-0125) and arrays a compile-time `N`
  (RFC-0132 §3), or a hardcoded arm until then.
- **Errors name their cause.** A failed structural check names the aspect, the instantiation and the
  field whose type fails (`Wrapper<String>: Copy: field v: String is not Copy`), at the
  declaration when the field type is concrete and at the use that needs the instance otherwise, with the
  instantiation in the message. C++'s late, distant template errors are the cautionary precedent.
- **With `declared`** the template is a check on the entry: a concrete field type that fails is an
  error at the declaration, next to the field; one that depends on a type parameter is decided per
  instantiation.
- **`auto` with a structural rule** (`Send`, `Sync`, `Linear`, including the existential rule of
  `Linear`) is deferred with the Send/Sync/Linear revision of RFC-0096. This RFC does not specify it.

## 3. `implicit` (std only)

`aspect A … implicit` states that a by-value use of a value whose type satisfies `A` copies its
representation instead of moving it. There is no hook: the copy runs no user code (RFC-0206 section 2), so it
is unobservable and needs no method, no signature check and no ordering rule. It requires:
1. `A` has the shape of a duplication marker: it refines `Clone` through a `derived` super-aspect (RFC-0213), so
   the compiler can provide the `Clone` that is the same copy;
2. the declaration is in std (below).

**What is restricted.** `implicit` is the one language-semantic property: it changes what a by-value use
means. It is std only because a user aspect could otherwise change the ownership of every use of a type, which
RFC-0162's D1 contains, so it is not offered.

**Provenance is a property of the declaration.** A declaration is in std when its module comes from the
embedded standard library, and the loader records that on the declaration. The flag belongs to the aspect,
not to a path written at a use site, so it survives imports, aliases and re-exports. `std` is a reserved
path root, so a user module cannot take the name. Under separate compilation the origin must be carried
and verified in compiled artifacts (open question 6).

**At most one implicit aspect per program** in the first implementation: `Copy`. A later std
aspect with `implicit` must carry a negative entry excluding every other implicit aspect (RFC-0213
section 3), so that no type can satisfy two. Applicability is decided at the declaration, not at an
instantiation, and a conflict is an error at the second declaration.

**Refining an implicit aspect does not bypass `declared`.** `aspect Cheap: Copy` is allowed, but
`extend T: Cheap;` still needs `T: Copy` as a super-aspect obligation, which only a declaration
clause grants. A sub-aspect cannot carry `implicit` itself, since that is std only. The `derived` mark on a super-aspect entry (RFC-0213 section 4) is std only for the same reason.

**A custom hook is a later extension, not a property of this RFC.** The earlier design let `implicit` name a
method (`implicit via Clone::clone`) so that a written `clone` ran at an implicit copy. It is deferred (RFC-0206
section 8): a later minor can add a **separate, separately authorized** custom mode without changing any accepted
program, provided `Copy` keeps its sealed guarantee for generic `T: Copy` code, the elision permissions and the
exclusion facts keep their meaning, and a hook cannot replace a provided `Clone`. It is reopened only on the trigger in RFC-0206 section 8 (a type
that needs observable behaviour on an implicit copy which an explicit `.clone()` cannot express).

---

## 5. Existing aspects, expressed

| Aspect | Declaration |
|---|---|
| `Copy` | `: derived Clone, !Drop`, `declared`, `implicit`; the structural rule is native in v0.16.0, a std row template later (metel-core#1823) |
| `Send`, `Sync`, `Linear` | `auto` (their structural rules deferred, section 2) |
| `Drop` | plain (no properties) |
| `Clone`, `Debug` | plain, with a derivation (RFC-0207) |

## 6. Worked examples

```metel
copy struct Point { x: i64, y: i64 }                      // declared: the declaration is the grant
extend Point: Copy;                                       // error: Copy is declared; use the declaration
struct H { fd: i64 }
extend H: Drop { fun drop(&var self) { } }
copy struct H2 { fd: i64 }
extend H2: Drop { fun drop(&var self) { } }              // error: Copy: !Drop
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
- **`implicit via S::m`, a named hook** (the design of 2026-11-04). Deferred with the custom hook of RFC-0206
  section 8. While it was the design, inferring the hook from the shape `fun (&self) -> Self` was tried and
  reversed as fragile against a second method of that shape in a super-aspect.

## Relationship to existing RFCs

- **RFC-0206** — `Copy` is declared with these properties.
- **RFC-0089** — the lattice whose `Copy`/`Drop`/`Linear` exclusions the negative super entries express.
- **RFC-0213** — super-aspects, which `implicit` and the exclusion need.
- **RFC-0207** — the clauses that grant a `declared` aspect.
- **RFC-0096** — its `auto` revision is deferred; see section 2.
- **RFC-0209 / RFC-0210 / RFC-0217 / RFC-0208** — the row machinery for the structural template on named types.
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
5. **Object safety** of aspects with these properties (`dyn Copy`).
6. **Provenance of std** under separate compilation: how the origin of a declaration is carried and
   verified in compiled artifacts. Within one program the loader's record suffices.
7. **Identity-based aspect resolution** is a prerequisite refactor with no RFC of its own; the
   properties are read from the aspect's declaration, never from its spelling.

---

## Decision

**Outcome:** *(pending)*
