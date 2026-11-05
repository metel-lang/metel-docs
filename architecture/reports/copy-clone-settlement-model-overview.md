---
title: "The Copy and Clone Settlement: Model Overview, Decisions and Implications"
date: '2026-11-05'
status: report
relates: rfc-0089, rfc-0206, rfc-0207, rfc-0211, rfc-0212, rfc-0213, rfc-0214, rfc-0216, rfc-0173
---

# The Copy and Clone Settlement: Model Overview, Decisions and Implications

A single-document account of the model the language owner settled on 2026-11-05 for `Copy`, `Clone`, the
ownership classes and generic code, with the decisions taken, the code each decision produces, and what each
implies for users, implementers and later work. The RFCs remain normative; this report is the map.

**Status.** Design settled in RFC-0206, RFC-0207, RFC-0212, RFC-0213 and RFC-0089 sections 1 to 2.2 (PR #555 on
`metel-docs`, tracked by metel-core#1808 and the ratification sweep #1824). RFC-0211 is staged (v0.16.0 part now,
template half later). RFC-0214 and RFC-0216 are drafts and not dependencies. Three adversarial reviews followed the prior-art
review: the first judged the cluster not ready, the second confirmed most repairs, and a whole-model review (review 7)
found a List classification defect, a nested derived-`Clone` contradiction and report inaccuracies, all applied here.
The RFC-0173 amendment note is in place. Open gates are tracked: the linear-release gate (#1828), the temporary List
rule (#1826), drop-site recording (#1827).

---

## 1. The model on one page

| Layer | What it is | Where it is decided |
|---|---|---|
| **Copy** | A sealed, implicit, representation copy. Runs no user code, so it is unobservable and elidable. Granted only in the declaration. | RFC-0206 section 2 |
| **Clone** | Explicit duplication, `x.clone()`. Provided by the compiler for every `Copy` type (and cannot be written there); ordinary and writable otherwise. | RFC-0206 sections 1, 2 |
| **Classes** | `copy` / `affine` / `linear` (contextual keywords, sugar). Affine by default. | RFC-0207 section 3, RFC-0089 section 2.1 |
| **Declarations** | `derives`, the colon list for user markers, and aspect properties `declared`, `auto`, `implicit` (std-only). | RFC-0207, RFC-0212 |
| **Super-aspects** | `aspect A: B`; a `derived` mark (std-only) makes a derivation generate the super; exclusions (`!Drop`) are grant-time checks. | RFC-0213 |
| **Generic code** | Exact per-instantiation predicate; a sound approximation in generic bodies (yes / no / undecided, and undecided is a diagnostic, not a move); stored ownership interfaces as the end state. | RFC-0206 sections 2 and 6 |
| **Discard** | A positive capability meaning "may be dropped". Bare `T` is possibly linear; `Discard` is inferred from bodies and stated on `pub` functions once `linear` ships. | RFC-0089 section 2.2 |
| **Projections** | A residual `T.{ fields }` gets structural `Copy` (with its provided `Clone`) and the `Drop` dispatch in v0.16.0; the rest is later. | RFC-0206 section 6, RFC-0211 |

The one-sentence design: **ownership class is a declaration-site fact, implicit duplication is sealed to a
representation copy, and everything else that looks like a special case is a property of an aspect declaration.**

---

## 2. Copy and Clone

### 2.1 The two aspects

```metel
copy struct Point { x: i64, y: i64 }
let a := Point { x = 1, y = 2 };
let b := a;                    // a copy; a is still valid
let c := a;                    // another copy: no `clone()` call, no user code

struct Cache { data: i64, hits: i64 }
extend Cache: Clone { fun clone(&self) -> Cache { Cache { data = self.data, hits = 0 } } }
// Cache is affine: `let b := c` moves; `c.clone()` runs the body (resets `hits`).
```

- `Copy` is **representation duplication**. A by-value use of a `Copy` value copies instead of moving. Nothing the
  program wrote runs, so a copy cannot be observed and the compiler may elide it.
- `Clone` is **explicit**. A type that needs a custom duplicate (reset a counter, `dup` a file descriptor) writes
  `Clone` and is simply not `Copy`.

### 2.2 `Copy` brings a provided `Clone`, and it cannot be written

```metel
copy struct Both { n: i64 }
extend Both: Clone { fun clone(&self) -> Both { Both { n = 0 } } }   // error T0015: overlaps the provided Clone

struct H { fd: i64 }
extend H: Drop  { fun drop(&var self) { } }
extend H: Clone { fun clone(&self) -> H { H { fd = dup(self.fd) } } } // fine: Clone on a Drop type
```

**Decision.** If a type is `Copy`, its `Clone` is the compiler-provided one. If it is not `Copy`, `Clone` is an
ordinary aspect: derive it or write it.

**Implication.** The two operations cannot diverge. Rust documents that `Clone` should agree with `Copy` and has Clippy
lints (`non_canonical_clone_impl` targets the divergence) but does not enforce it; here it is a compile error.

### 2.3 The implicit copy is the provided `Clone`, elided

RFC-0206 section 2 rule 4 defines the implicit copy as an **elidable invocation of the type's provided `Clone`**.
`Copy` has no methods of its own; the operation it grants *is* that `clone`, done implicitly. This is why
`Copy` entails `Clone`, and it keeps the intuition ("Copy uses Clone") true without a hook:

- The provided `clone` runs no user code, so the definition and the representation copy cannot differ.
- A `T: Copy` bound in generic code still guarantees no user code runs at a copy.
- Elision removes a call or the materialisation of a duplicate; it never discards a duplicate a use needs.

### 2.4 Granted only in the declaration

```metel
extend Point: Copy;             // error: granted only in the declaration (fix-it moves it)
struct P derives Copy { x: i64 }   // the same as `copy struct P`
```

**Decision.** `Copy` changes the meaning of every use of a type, so it is visible where the type is declared.
**Implication.** A reader never has to search the crate for an `extend T: Copy`. `extend T: Copy;` gets a fix-it that
moves it: a warning for one minor release, then an error.

### 2.5 Copy by default was rejected

A type whose fields are all copyable does **not** become `Copy` silently. Swift infers copyability; Metel does not,
because then a capability token or a handle written without a keyword would be freely copyable and droppable, the
failure linear types exist to prevent. Rust chose opt-in for the same reason.

---

## 3. Declarations: derives, the colon list, class keywords, properties

### 3.1 Clauses

```metel
struct Doc derives Clone { title: String, n: i64 }       // derived Clone: field-wise
struct Token: Validated { id: i64 }                      // colon list: a user `declared` marker
struct Dup derives Clone, Copy { n: i64 }
extend Dup: Clone { fun clone(&self) -> Dup { /* ... */ } }   // error T0015: overlaps the derived Clone
```

`derives` is an explicit request, distinct from a written impl; a derived impl and a written impl of the same
aspect overlap (`T0015`). The colon list holds user `declared` markers only; `: Copy` there is an error with a
fix-it to `derives Copy`.

### 3.2 Class keywords are sugar

```metel
copy   struct P { x: i64 }      // = struct P derives Copy
affine struct H { fd: i64 }     // = extend H: !Copy; extend H: !Linear;   (a locking pair of negative impls)
linear struct T { id: i64 }     // = extend T: Linear {}   (reserved; "Planned for" in v0.16.0)
```

**Implication.** `affine` is a real, checked commitment: a later `extend H: Copy` anywhere is a coherence error.
For a generic type a keyword states a capability, not a class: `copy struct Wrapper<T>` is `Copy` exactly when
`T` is.

### 3.3 Aspect properties replace lang items

```metel
// std declaration sketch (not legal user code: `implicit` and `derived` are std-only); spelling per RFC-0212, provisional
aspect Copy: derived Clone, !Drop declared implicit;
```

| Property | Meaning | Who may use it |
|---|---|---|
| `declared` | granted only in the type's declaration | any aspect |
| `auto` | structural rule, granted by field composition (`Send`, `Sync`; deferred) | std only |
| `implicit` | a by-value use copies the representation instead of moving | std only |

**Decision.** There is **no special case by name** for these three behaviours: the compiler reads these properties from the
aspect's declaration, never from the spelling "Copy". (Structural composition is a template, not a property; v0.16.0 uses
native logic for it, #1823.) The string-keyed sites (about 38 today) are replaced by identity
lookup. **Implication.** The compiler's privilege is organised, not removed: `implicit` is std-only because a user
aspect could otherwise change the ownership of every use of a type.

---

## 4. Super-aspects, exclusions and the `derived` mark

```metel
// std declarations (a user aspect may not carry `derived` in v0.16.0)
aspect PartialEq { fun eq(&self, other: &Self) -> boolean; }
aspect Eq: derived PartialEq;               // derives PartialEq with it
struct Id { n: i64 }
extend Id: PartialEq { /* ... */ }
extend Id: Eq;                              // ok: PartialEq exists
struct Bad { n: i64 }
extend Bad: Eq;                             // error: no PartialEq for Bad

aspect Error: Display;                      // unmarked entry = an obligation: Display must already exist
```

- A super-aspect entry is an **obligation** unless marked `derived`.
- `derived` means the sub-aspect's derivation also generates the super (`derives Copy` also derives `Clone`).
  **Decided 2026-11-05: only std aspects may carry the mark in v0.16.0** (open question 9 reopens it for user aspects
  when a real case appears). The mark is part of the aspect's contract: adding or removing it can change which impls
  are generated, so it is a breaking change to the aspect, which std controls.
- **Exclusions** (`!Drop`) are a **grant-time check only**. A grant of an excluded aspect is a coherence error naming
  both. There is no disjointness evidence, no contrapositive, no negative closure; absence is not negation.
  Disjointness evidence is a deferred extension: it would turn exclusions into a public coherence contract.

```metel
copy struct H2 { fd: i64 }
extend H2: Drop { fun drop(&var self) { } }     // error: Copy: !Drop (grant-time exclusion)
```

**Implication.** Rust and Haskell never generate a super-instance from the sub-aspect's derivation (Swift does in a
fixed case). The generic per-edge mark is the least established part of the design, which is why it is std-only.

---

## 5. Generic code

### 5.1 The predicate is exact; generic bodies approximate it

```metel
copy struct View<T> { r: &T }           // Copy for every T: a shared reference is always Copy
copy struct Wrapper<T> { v: T }         // Copy exactly when T: Copy

fun dup<T: Copy>(x: T) -> (T, T) { (x, x) }
fun twice<T: Clone>(x: &T) -> (T, T) { (x.clone(), x.clone()) }
```

- For an instantiation `T<A>`, `T<A>: Copy` holds when every field type is `Copy`, and the type is not `Drop` and not
  `Linear`. It is evaluated **per instantiation**, with no bound written on the type parameter.
- The analysis of a generic body is a **sound approximation**: yes, no, or **undecided**. Undecided never permits a
  copy. In v0.16.0 an undecided ownership in a generic body is a **diagnostic** (the named limitation, #1814), never
  a silent move and never a guess. Reusing a `View<T>` in a generic body is rejected until the solver (#1813); today
  it fails with an internal error (`I0011`).
- Because undecided is an error and not a move, the accepted set only grows as proof power grows, and the
  copy-or-move behaviour of an accepted program **never changes** with it. Adding proofs must also not change overload
  selection, conditional-implementation selection or coherence.

### 5.2 Stored ownership interfaces: the end state

```metel
copy struct Wrapper<T> { v: T }          // v0.16.x+: a stated condition (Copy when T: Copy) becomes the interface; clause spelling open, #1818
```

The route is incremental; nothing in v0.16.0 closes it:

1. v0.16.0: the design as written plus the undecided-ownership diagnostic (#1814).
2. A later minor: stored interfaces with explicit conditions (#1818).
3. The declaration-graph computation phase (#1819) and the solver as producer (#1813); epic #1821.
4. A `pub` generic type must state its condition (an error with a fix-it showing the computed one, #1820).

Rules fixed on 2026-11-05:

- **The stated condition is the interface.** A written `when` is checked sufficient and exported; the computed condition is
  the interface only when none is stated (a non-`pub` type). A representation change can therefore never silently
  change a public interface.
- **One rule for types and functions.** A `pub` item states its ownership interface (a type's conditions, a function's
  bounds including `Discard`); a non-`pub` item gets it computed; the diagnostic suggests the computed result as a fix-it.
- **Condition language.** A conjunction of `Param: Marker` atoms over the item's own parameters, with the constants
  `true` and `never`. No disjunction, negation or recursion. Only **permissive** capabilities are stored (`Copy`,
  `Discard`, later `Send`/`Sync`). Termination comes from solving order (recursive groups first, then dependency order).
- **Recursive declarations** follow one polarity rule:

| Marker | Resolution of a cycle | Why |
|---|---|---|
| `Discard`, `Send`, `Sync` | coinductive (assume it holds) | every field must qualify |
| `Linear` | inductive, computed per instantiation, never stored | one linear field suffices |
| `Copy` | inductive (a cycle is "no") | a recursive type needs an owning indirection, which is not `Copy` |
| derivation goals | coinductive on exactly repeating goals | `Tree derives Clone` with `Node(List<Tree>)` |
| function requirements | least fixed point | obligations only accumulate |

```metel
struct Node<T> { value: T, children: List<Node<T>> }   // Discard exactly when T is: the cycle adds nothing
```

---

## 6. Linear types, `Discard` and generic code

### 6.1 The lattice

Four points, not three: `erased` (0), `linear` (exactly once), `affine` (at most once, the default), `copy` (ω).
A struct's discipline is the **most restrictive** of its fields. `Drop` is compatible with affine only: not with `ω`
(a representation copy cannot do per-owner cleanup) and not with linear (a linear value is never implicitly
discarded).

### 6.2 The problem and the decision

A generic body can copy or drop a `T` without writing a call. A copy happens at a visible use site; a **drop** is
implicit (scope end, early `return`/`?`, overwrite, unused argument, discarded statement, the rest of a partial
move). If bare `T` were affine, linear types could never be used in generic code; if every dropping function had to
write a bound, 30 to 40 % of generic functions would carry it (measured over std and the integration programs on
2026-11-05; a floor).

**Decision.** Bare `T` is **possibly linear**. `Discard` is a positive, compiler-computed capability ("may be
dropped"); the compiler elaborates `T: Discard` from bodies, and a `pub` function states it once `linear` ships.

```metel
linear struct Tx { id: i64 }

fun identity<T>(x: T) -> T { x }                  // x is moved into the result: no Discard; identity(tx) is accepted
fun sink<T>(x: T) { }                             // drops x: elaborates T: Discard (silently, non-pub)
pub fun api<T>(x: T) { sink(x) }                  // inherits T: Discard from the callee; must state it once linear ships

// Option<T>::unwrap_or(self, fallback: T) -> T: the Some arm drops `fallback`,
// so the method needs T: Discard. Option<Tx> exists; Option<Tx>::unwrap_or does not.

aspect Finish { fun finish(self); }
extend Tx: Finish { fun finish(self) { commit(self) } }
fun run<T: Finish>(x: T) { x.finish() }           // x is moved into the call: run(tx) is accepted
```

- **Elaboration is transitive** (drops plus callee interfaces after substitution), a least fixed point for recursive
  helpers, and never selects an implementation on a bound the selection itself would infer.
- **Only `Discard` is elaborated**: a drop is the one implicit operation. Methods, operators, `Copy` and `Clone`
  stay declared. This is a single named exception to RFC-0173's "declared bounds", amended in RFC-0173's file.
- A compiler diagnostic on a `pub` function must **suggest the computed bound** (a fix-it), so the author confirms
  instead of working it out.
- `Discard` is **never user-writable**; a public stated condition may withhold it but never create it or suppress a
  structural linear obligation.
- **In v0.16.0 every type is `Discard`**, so no program changes. The generic-body analysis must record drop sites now
  so the elaboration can be computed when `linear` lands.

### 6.3 Ending a container of linear values

```metel
// Until the std List is redesigned, a named native rule says Discard(List<T>) = Discard(T) (#1826), because `inner: [T]`
// is a copyable view. fun abandon(xs: List<Tx>) { } is rejected.
// List<T> destructor becomes conditional: extend<T: Discard> List<T>: Drop  (a std change at `linear` time)
fun end_all(xs: List<Tx>) { xs.consume_each(|t| commit(t)); }
// consume_each(self, f: |T|) is a native that owns the list, moves each element into f, frees the storage.
// Emptying a list with `pop` does NOT consume it: the value is still a List<Tx> and must still be ended.
```

### 6.4 `Clone` is not contraction

A linear type may have a **written** `Clone` (the author asserts another instance is valid, for example opening
another handle). A derived `Clone` requires every field to satisfy `Clone`, including linear fields; a fiat-linear leaf
supplies a written one, and a wrapper of a field with a valid `Clone` derives normally.

---

## 7. Projections and residuals

A residual `T.{ fields }` (RFC-0137) is the same brand with some fields narrowed away.

```metel
struct Doc { title: String, n: i64 }
copy struct Point { x: i64, y: i64 }

let p := Point { x = 1, y = 2 };
let q := p.{ x };               // Point.{ x }: Copy (structural, sealed) with its provided Clone
let r := q; let s := q;         // accepted: copies

fun dup<T: Clone>(x: &T) -> (T, T) { (x.clone(), x.clone()) }
let d := Doc { title = "t", n = 1 };
let t := d.{ title };           // a projection moves the field out (a borrowed projection of a non-Copy field is rejected, RFC-0137)
dup(&t);                        // T0012 in v0.16.0: Clone has no impl for the projection (metel-core#1788)
```

**Decision (scope B, 2026-11-05).** In v0.16.0 a projection gets exactly structural `Copy` **with its provided
`Clone`** and the existing `Drop` dispatch (RFC-0137 section 5). Every other aspect is `T0012`. The diagnostic
distinguishes a written whole-type impl (named as the cause) from a derived aspect whose template is deferred
("template not yet available"). The language keeps no edit history, so there is no warning at the edit.

**Implication.** Once derived templates exist, replacing `derives Clone` with a hand-written `Clone` removes `Clone` from
projections, and the program fails at the use site, not at the edit (in v0.16.0 a non-`Copy` derived `Clone` already
provides none on a projection). The remedy is later: row templates for derived impls (RFC-0211) and
written residual impls (RFC-0214).

**Native for now.** The structural `Copy` rule for named types is compiler logic in v0.16.0, so the Row machinery is
not on the critical path. It is a named, time-boxed exception tracked by #1823, whose replacement must keep residuals such as
`W<String>.{ n }` of `copy struct W<T> { n: i64, value: T }` `Copy` (the stored interface must be row-sensitive). Scope B
means ordinary impl availability; compiler-computed ownership capabilities (`Discard`) follow the surviving fields.

### 7.1 Drafts (not dependencies)

```metel
// RFC-0214: a written impl that applies to a residual
view DocTitle for Doc { title }
extend DocTitle: Display { fun fmt(&self) -> String { return self.title.clone(); } }

// RFC-0214, row-generic form (spelling provisional): a written template over the whole row
extend Doc: Clone<record R> where ..R: Clone {
    fun clone(&self: Self.{ ..R }) -> Self.{ ..R } {
        return Self.{ ..R } { comptime for field in fields(R) {
            [field.name] = self.[field.name].clone(),
        } };                                    // construction: RFC-0216
    }
}
```

Open in the drafts: how a residual is built (RFC-0216, authority and constructor invariants), customising one field of
a symbolic row (a compile-time refinement or per-field customisation of a derive), enums (atomic, no residuals).

---

## 8. Decision log

| # | Decision | Date | Why | Implication |
|---|---|---|---|---|
| 1 | Sealed `Copy` (representation copy), explicit `Clone`; no writable implicit hook | 11-05 | The hook makes insertion and elision of a call observable and needs a full lowering and ordering contract | A type needing a custom duplicate is not `Copy` |
| 2 | `Copy` brings a provided `Clone` that cannot be written; implicit copy is its elided invocation | 11-05 | One operation, two spellings must not diverge; keeps "Copy uses Clone" true | `T0015` on a written `Clone` for a `Copy` type |
| 3 | `Copy` granted only in the declaration; affine by default; copy-by-default rejected | 11-05 | Visible at the type; fails safe for handles and tokens | `extend T: Copy;` deprecated |
| 4 | Class keywords `copy`/`affine`/`linear` as contextual sugar | 11-05 | One-word class at the declaration; leaves room for linear | `affine` is a locking pair of negative impls; `linear` reserved |
| 5 | Aspect properties (`declared`, `auto`, `implicit` std-only) instead of lang items | 11-05 | No special case by name | About 38 string-keyed sites become identity lookup |
| 6 | Super-aspects with a `derived` mark, std-only in v0.16.0 | 11-05 | Generalises "Copy brings Clone" without a per-aspect exception, confines the unproven combination | Opening to user aspects needs a real case |
| 7 | Exclusions are a grant-time check only | 11-05 | Disjointness evidence would make exclusions a public coherence contract | No negative closure; absence is not negation |
| 8 | Generic bodies: exact predicate, sound approximation, undecided is a diagnostic | 11-05 | Undecided-as-move would let a later solver change accepted programs | Accepted set only grows |
| 9 | Hybrid end state: stored interfaces, solver as producer; the stated condition is the interface; `pub` must state | 11-05 | Stable public interfaces; use sites consult stored data only | Steps #1814, #1818, #1819, #1820, #1813 |
| 10 | Stored conditions: permissive capabilities only, conjunctions with `true`/`never`; polarity for recursion | 11-05 | `Linear` is existential and cannot be a conjunction; termination by solving order | `Linear` is computed per instantiation |
| 11 | Bare `T` possibly linear; `Discard` inferred, transitive, stated on `pub` once `linear` ships | 11-05 | Linear types stay usable in generic code without a written bound on 30 to 40 % of functions | One named exception to RFC-0173 |
| 12 | `Discard` is compiler-computed, never user-writable | 11-05 | A user grant could make a linear value droppable | Only fiat removes it |
| 13 | RFC-0089 split; the lattice and keywords stay, partial consumption goes to RFC-0215 | 11-05 | The settlement needs the lattice, not the `ToRecord` coupling | Acceptance order 0089, 0206, 0207, 0213, 0212 |
| 14 | `Clone` is not contraction; panic in a derived clone ends the process | 11-05 | Resource duplication must stay possible; the spec already ends the process on panic | Linear fields need no partial-clone cleanup |
| 15 | Projections: scope B, native structural `Copy` for now | 11-05 | Keeps Row machinery off the critical path | `T0012` with a use-site diagnostic; #1823 removes the exception |
| 16 | Hook stays open with a named reopen trigger | 11-05 | Sealed-to-writable is monotone only as a separate, separately authorized mode | Four conditions in RFC-0206 section 8 |
| 17 | One ratification sweep, RFC-0211 staged | 11-05 | The cluster is interdependent (the RFC-0063 precedent) | Gates on #1824 |

---

## 9. Named exceptions and temporary workarounds (every one has a tracked exit)

| Workaround | Where | Exit | Tracked |
|---|---|---|---|
| Structural `Copy` for named types is native | v0.16.0 | std row template; residuals such as `W<String>.{ n }` stay `Copy` | #1823 |
| Arrays and the record `Clone` hook are compiler rules | v0.16.0 | std impls over a compile-time `N`, `comptime for` | #1811, #1390, #702 |
| Tuple structural arms are native | v0.16.0 | variadics (RFC-0125) | #794 |
| Native named-type `Clone` derivation | v0.16.0 | comptime derive (RFC-0092, RFC-0093) | #1829 |
| Undecided abstract ownership is a diagnostic | v0.16.0 | obligation solver and stored interfaces | #1813, #1818, #1819, #1820 |
| `Discard(List<T>) = Discard(T)` as a native rule | at `linear` | owning-storage kind distinct from the `[T]` view | #1826 |
| Drop-site and callee-interface recording only | v0.16.0 | `Discard` elaboration with `linear` | #1827, #1828 |

**Permanent restrictions** (design choices, not workarounds): `implicit`, `auto` and `derived` are std-only (open question 9 for
`derived`; the RFC-0096 revision for `auto`), and `Discard` is the single inferred bound.

---

## 10. What this means in practice

**For a language user.** Declare copyness where the type is declared (`copy struct`). Write `Clone` only when you
need a custom duplicate, and then the type is not `Copy`. Generic code that needs to copy says `T: Copy`; code that
duplicates says `T: Clone` and calls `.clone()`. v0.16.0 introduces no linear values; later stages require
public-interface annotations (see the next paragraph).

**For a library author.** A `pub` generic type will have to state its ownership condition at the final step of the stored-interface route (#1820). A `pub` generic function that drops a `T` will have to state `T: Discard` once `linear` ships; the compiler will
suggest it. A hand-written `Clone` on a type that is passed around as projections loses `Clone` for those
projections until residual impls exist.

**For the implementation.** Replace string-keyed `"Copy"` sites with identity lookup (#1799); add the clauses (#1800),
super-aspects (#1801), derivations (#1802) and properties (#1803); record drop sites of parameter-dependent values and the callee interfaces consulted in
the generic-body analysis (preparation for `Discard`, #1827); fix the derived-clone order (#1817). The evaluator keeps
`deep_clone_value` at bindings: a sealed copy is unobservable, so no per-site dispatch, witness or ordering rule is
needed.

**For later work.** RFC-0215 (partial consumption of mixed-multiplicity structs), RFC-0214 and RFC-0216 (residual
impls and construction), the solver and stored interfaces, `linear` itself, closure discard (RFC-0134, RFC-0153), and
the std audit (conditional `List` destructor, `consume_each`, and the dropping methods).

---

## 11. Risks and what is not settled

| Risk | State |
|---|---|
| The stored-condition language and `pub`-must-state | Moderate; high until implemented and tested |
| Derivation provenance deciding residual instances | Lower for v0.16.0 (scope B); the template half is later |
| Inferred `Discard` | Moderate; reviewed twice; open dependency on a conditional std destructor and closure discard |
| `derived` and `implicit` as properties | Low and moderate; std-only |
| A later observable hook | Reopened only on a named trigger and four conditions |

**Not settled:** closure and trait-object discard (RFC-0134, RFC-0153, gate #1828); the demonstration for `List<Tx>`
depends on the named List rule (#1826), the std change and the closure rule; spellings pending ratification
(`derives` and clause order, the property clause form, `!Drop`, `derived`, `Discard`); user-declared `derivable`
aspects; object safety for aspects with these properties.

---

## 12. Where this sits against prior art

| Question | Metel | Closest precedent |
|---|---|---|
| Sealed implicit copy, provided `Clone` | `Copy` runs no code; `Clone` cannot be written for a `Copy` type | Rust `Copy: Clone` (without the enforcement); Swift `BitwiseCopyable` |
| Class keywords | `copy`/`affine`/`linear` | Austral universes; Linear Haskell and Idris 2 quantities |
| Grant in the declaration | `copy struct`, `derives Copy` | Swift `~Copyable` on the declaration; Mojo trait list |
| Properties instead of lang items | `declared`, `auto`, `implicit` | Rust lang items and auto traits |
| Exact conditions, stored interfaces | stated condition is the interface | Haskell smallest derived context; Swift SE-0426 public contracts |
| Generic code and linear types | bare `T` possibly linear, `Discard` inferred | Austral `T: Type`; Swift SE-0427 `~Copyable` (written, not inferred) |

The review's judgement: the ownership choice is on well-trodden ground; the interface, exclusion and residual
machinery is a language-design experiment, and accepting the former is not external validation of the latter.

---

## 13. Map of artifacts

- RFCs: 0206 (Copy and Clone), 0207 (clauses), 0212 (properties), 0213 (super-aspects), 0089 (linear lattice and
  `Discard`), 0211 (residual templates, staged), 0214 and 0216 (drafts), 0215 (partial consumption), 0173 (amendment).
- Reports: `copy-clone-prior-art-survey.md`, `clone-implicitclone-declared-conditions-comparison.md`.
- Issues: epic #1808; implementation #1799 to #1807, #1814, #1817; stored interfaces epic #1821 (#1818, #1819, #1820,
  #1813); #1823 (native structural `Copy`), #1824 (ratification sweep), #1825 (large-copy lint).
