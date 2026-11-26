---
id: rfc-0254
title: "Universal Row Extraction and Retiring Record Parameters"
date: '2026-11-25'
status: under-review
updated: '2026-11-26'
tracking: 'https://github.com/metel-lang/metel-core/issues/2195'
---

> **Status — under review (2026-11-25).** Scheduled for row visibility and named records design review

## Summary

Every type has an extractable structural row. `..T` extracts that row from an ordinary
type parameter, without requiring a `record` parameter kind or an empty structural bound.
The `record` generic parameter kind is retired. A structural bound states a shape
requirement, and RFC-0208's `<..R>` binds a row rather than a type.

```metel
fun inspect<T>(value: &T) where ..T: Display { … } // proposed field-wise bound
fun read_id<T: .{ .id: i32, .. }>(value: &T) -> i32 { value.id }
fun use_row<..R>(value: &.{ R }) where R: Display { … }
```

The language owner agreed to the direction on 2026-11-25; the type classification (section 1) and its interaction
with overload resolution, inference, coherence, orphan rules and vacuous bounds (section 2a) are now resolved,
2026-11-26. This RFC remains under review: migration mechanics and the remaining grammar question still need
work, and no implementation is authorized until integration.

## Motivation

RFC-0243 retires the named `record` declaration kind and makes public fields available
for structural matching. RFC-0208 separates a row binder from a type parameter. The
remaining `<record T>` kind combines an ordinary type identity with permission to use
its row. If extraction is defined for every type, ordinary `<T>` can carry the identity
and `..T` can extract its row. Structural bounds are needed when code requires fields,
not simply to establish that an extractable row exists.

## 1. Extracted row

For ordinary structural matching and extraction, the row is module-independent:

| Type | Extracted row |
|---|---|
| Struct | Its public fields, after generic substitution |
| Branded residual | Its present public fields |
| Anonymous record or tuple | Its present fields; tuples use numeric labels |
| Primitive | Empty |
| Enum | Empty; variant rows are separate work (RFC-0210) |
| Reference | Empty; extraction does not implicitly dereference the target |
| Array `[T; N]` or slice `[T]` | Empty; elements are indexed, not labeled fields |
| Function type (`\|A, B\| -> R`, `dyn Callable<..>`) | Empty; never the parameter row (see below) |
| `Never` | Empty, vacuously: no value exists to have fields |
| Aspect object (`dyn A`) | Empty; the underlying type is erased, nothing to read statically |
| Unconstrained type parameter or associated type | Empty unless narrowed by a structural bound, in which case exactly the bound's stated fields and no more |

**The classification is total, by one governing principle (language owner, 2026-11-26), not a list of unrelated
special cases:** a type's extracted row is the maximal set of (label, type) pairs *statically* known, at the point
of extraction, to be present in every value of that type — never inferred through indirection (a reference),
erasure (a `dyn` object), homogeneous indexing (an array or slice), a call signature (a function type), or an
as-yet-undetermined instantiation (an unconstrained type parameter or associated type) beyond what an explicit
structural bound states. Every row above, including the categories already agreed, is this one rule applied. No
category is excluded from universal extraction — every type has *an* answer, even where that answer is uniformly
Empty.

**A named risk, not an omission: function types and RFC-0232.** RFC-0232 (same release, "Function types" stage)
represents a function's call signature as `dyn Callable<ROW, R>` — a row already sits inside a function type's own
representation. If `..F` extracted *that* row, it would conflate "this function's call signature" with "this
type's own data fields" under one operation, exactly the accidental-conformance risk the row-visibility cluster
(RFC-0243 E4) has been working to keep out. Extraction stays out of it on purpose: a function's parameter row is
reached, if at all, through whatever RFC-0232's own `Callable` aspect exposes, never through `..F`.

**What a generic body knows about an abstract type's row** is the bound's row and nothing more — the same
parametricity discipline RFC-0146's lower-bounded row receiver already establishes for a residual (a method
checked against `Self.R` where `R: { fd, .. }` may use only `.fd`, never assuming a specific caller's residual
happens to have more). An unconstrained type parameter and an associated type with no stated bound are the same
case under this rule, not two different ones: both are "a type not yet concretely known at this point," so both
default to Empty until a bound says otherwise.

These categories, now exhaustive, replace the earlier "initial categories are agreed direction; other current and
future types need classification" framing — this is that classification. Empty means the row contains no fields,
not that the type is the empty record. `..T` forgets the nominal brand, while `T` retains its identity. Extraction
at a privileged derivation boundary may require a different full-field operation; that deferred design is not
specified here.

`T: .{}` is an exact empty **public** row bound. It can hold for a primitive or a struct
with no public fields, including a struct with private fields. It makes no claim about
private state or interchangeability with `.{}`. `T: .{ .. }` imposes no field requirement
and is redundant if extraction is universal. `T: .{ .id: i32, .. }` requires an accessible
public `id` and permits other public fields; the exact form without `..` permits no
other public fields. Matching a bound preserves `T` and does not convert its value.

## 2. Parameters and bounds

An ordinary `T` can occur as a type and `..T` denotes its extracted row. A row-only
parameter `R` declared by `<..R>` denotes fields directly and is used as `R` in row
positions, as proposed by RFC-0208. Field-wise bounds over an empty row hold vacuously;
therefore `where ..T: A` alone does not assert `T: A`. A function using only such a bound
must not invoke an `A` method on `T` itself without a separate `T: A` bound. A negative
field-wise bound (`where ..T: !A`) is vacuously true over an empty row by the same logic.

**Resolved (language owner, 2026-11-26): this vacuous-truth rule is uniform across every aspect, including
ownership and auto aspects — with one named implementation risk, not a language-level special case.** The rule
above already rules out the general danger (a field-wise bound can never assert the whole-type bound) for Send,
Sync, Copy and Linear alike; none of them can be satisfied merely because `where ..T: A` holds vacuously. The real
risk is narrower and belongs to whoever eventually specifies `auto`'s deferred structural rule (RFC-0096, RFC-0212
section 2): an **auto** aspect's grant must be computed from a type's *full* field set, public and private alike,
inspected at the type's own definition — the same way `Copy`'s and `Linear`'s structural checks already work
(RFC-0206 rule 3, RFC-0212 sections 1-2) — never by reusing `..T`'s public-only extracted row. Reusing it would
make the auto-grant itself unsound: a type with a non-`Send` private field could vacuously satisfy a
`Send`-shaped check restricted to its (possibly empty) public row, and be silently granted `Send` it does not
actually have. `Copy`, `Clone` and `Linear` do not share this risk, because their structural checks already
happen at the type's own declaration with full field access by construction; the risk is specific to `auto`'s
no-entry, module-independent grant mechanism, exactly where a public/private mismatch could silently creep in if
implemented by reusing universal extraction instead of a dedicated full-field check. This is a constraint for
`auto`'s still-deferred structural rule to honor, not a bug in anything currently specified.

A bound and a row literal use the syntax of RFC-0208. The `record T` binder is removed
as a distinct generic kind; the declaration kind's retirement is RFC-0243. A plain type
parameter's ordinary well-formedness and kind rules still apply. No implicit dereference,
owned conversion, field move, reference creation, or automatic nominal aspect grant is
introduced by type-level extraction.

## 2a. Overload resolution, inference, coherence and orphan rules

**Resolved (language owner, 2026-11-26).** Most of this collapses to one fact: `..T` is a *derived, one-way
projection* of an already-determined `T`, computed after the fact from the classification table (section 1) — it
never participates in type inference, impl matching or coherence as a *source*, only as a *consumer* of existing,
unchanged machinery.

- **Type inference is unaffected.** `T` is always inferred by the usual means (arguments, return-type context,
  explicit turbofish); `..T` is computed from `T` only once `T` is already known. There is nothing new to infer:
  many different types can share the same extracted row (most share Empty), so inference could never run
  backward from a row to a type, and this RFC does not attempt to.
- **Coherence and the orphan rule are untouched.** Row-conditional impl matching (RFC-0121) and who may write
  such an impl (RFC-0060) are governed entirely by those RFCs and by RFC-0243's decided opt-in rule, neither of
  which this RFC changes. Extraction supplies a row *value* for a bound to check against an aspect
  (`where ..T: A`); it is never itself the thing an impl is matched against. A primitive's or `Never`'s empty
  extracted row does not make it eligible for row-conditional impl matching — that eligibility was never keyed
  on the extracted row to begin with; only a record, or a nominal type that has explicitly opted in (RFC-0202
  section 6, RFC-0250 section 0), is ever a candidate.
- **Negative bounds** (`T: !A`) are about `T` itself, unaffected by extraction directly; the field-wise case is
  covered above.
- **Field-wise aspect constraints** (`where ..R: A`, RFC-0123) keep their existing, already-implemented rule;
  this RFC only widens which types may supply `R` via `..T` — from `record T` only to every `T`.
- **The one real consequence is overload resolution at existing call sites, already named in section 3's
  migration text below, not a new rule to invent.** Because `..T` now type-checks for every `T` rather than being
  a kind error for a non-`record` type, a call site that used to have exactly one eligible overload can gain a
  second one after migration (one candidate's `..T`-involving bound now also type-checks for an argument it
  previously didn't). This needs no new disambiguation rule: existing overload resolution already picks the most
  specific match or reports ambiguity, and a newly-ambiguous call site surfaces as a loud compile error, not a
  silent behavior change — consistent with migration being "not necessarily behavior-preserving," below, rather
  than silently unsound.

## 3. Migration

A candidate migration changes `<record T>` to `<T>` when `T` denotes a type, and its
existing row uses to `..T`. A parameter used only as a row may instead become `<..R>`
with bare `R` uses under RFC-0208. Existing code that depended on the old eligibility
restriction can accept more instantiations; migration is not necessarily behavior-preserving.
Audit constraints, overloads, explicit arguments, method resolution and public generic
interfaces before choosing a mechanical rewrite. Row-based implementations for nominal
types remain deferred, so a new row bound alone does not grant them an aspect.

```metel
// Before (current syntax)
fun count<record T>(value: &T) -> i64 { … }
// Candidate after
fun count<T>(value: &T) -> i64 { … }
```

An exact compatibility predicate, transition period, diagnostics and tooling remain
open. Migration must also cover existing standard-library and documentation uses and
RFC-0192's explicit record-parameter arguments. No deprecated spelling is specified yet.

## 4. Interactions

- **RFC-0208 / RFC-0186:** one row kind and bare row use; this RFC replaces the record
  type-parameter eligibility gate, rather than changing the difference between a type
  and its extracted row. Explicit arguments and row equations need joint review.
- **RFC-0243 / RFC-0137:** public and present field selection, residual brands and named
  record retirement. Visibility must not depend on the use-site module or reveal private
  fields through remainders, reflection, diagnostics or inferred public interfaces.
- **RFC-0151 / RFC-0125 / RFC-0247:** tuples are numeric rows; positional operations and
  variadic calls retain their own rules. Universal extraction adds no pack kind.
- **RFC-0210:** enums initially extract the empty row; variant-wise access remains separate.
- **RFC-0121 / RFC-0060 / RFC-0228:** broader structural eligibility affects generic and
  row-conditional impl domains, coherence, orphan rules and dispatch. Existing active
  anonymous-row blankets must not silently grant aspects to nominal types under the
  deferred nominal-implementation design. Check primitive, reference and enum domains.
- **RFC-0214 / RFC-0217:** nominal row implementations and residual aspect behavior stay open (RFC-0209, their
  own basis, is superseded with no successor yet); extraction and a vacuous field-wise bound do not settle them
  either way.
- **RFC-0232** (same release, "Function types" stage): represents a callable's parameter row as part of `dyn
  Callable<ROW, R>`. Extraction deliberately never reaches it (section 1) — the two row concepts, a type's own
  fields and a callable's call signature, stay disjoint through this operation.
- **RFC-0253:** generic nominal residual projections retain their instantiated brand and
  may include row-kind arguments; privacy and substitution need cross-module checks — RFC-0253's own adversarial
  pass (declaring a `pub` alias that retains a private field is legal; accessing that field through it is what's
  rejected) is a directly reusable precedent for stating this RFC's own privacy rule precisely.
- **References and ownership:** `..&T` is empty, not `..T`; this does not alter borrowing,
  `Drop`, linearity, or the destruction of private fields. A type-level row is not an
  owned or borrowed record value.

## Open questions

1. **Resolved (language owner, 2026-11-26), section 1.** Every type now has a classification, by one governing
   principle rather than a list of special cases; none is excluded from universal extraction (every category
   gets an answer, some uniformly Empty). A generic body knows exactly its type parameter's or associated
   type's stated bound, nothing more — the same parametricity discipline RFC-0146's lower-bounded row receiver
   already uses. The function-type case surfaced a real, same-release collision risk with RFC-0232, now named
   explicitly (section 1, section 4) rather than left to be discovered later.
2. What exact constraint and diagnostic preserves old `<record T>` eligibility where an
   API requires it, and should the old binder have a staged migration?
3. **Resolved (language owner, 2026-11-26), section 2a.** `..T` is a derived, one-way projection and never a
   source for inference, impl matching or coherence; those stay governed entirely by their own existing rules
   (RFC-0121, RFC-0060, RFC-0123, RFC-0243). The one real consequence is overload resolution at existing call
   sites gaining newly-eligible candidates after migration — already named in section 3, caught loudly by
   existing ambiguity detection, not a silent risk needing a new rule.
4. How do public-row opacity and exactness interact with generic aliases, separate
   compilation, private representation changes and row remainder inference?
5. **Partially resolved.** The explicit-argument half is settled: a `<..R>` parameter's turbofish argument
   composes with RFC-0192 exactly as `record R`'s already does (RFC-0208 open question 1) — no change to
   RFC-0192's own rule was needed. Still open: the grammar that distinguishes a row extraction (`..T`), a row
   literal (`..{ ... }`), a row binder (`<..R>`), and variadic spread syntax from each other at a glance.
6. **Resolved (language owner, 2026-11-26), section 2.** Yes, uniformly, at the language level — no special
   case for ownership or auto aspects. The real risk is implementation-level and narrower: `auto`'s own
   (still-deferred, RFC-0096) structural grant must use a type's full field set, never `..T`'s public-only row,
   or the grant itself becomes unsound. `Copy`/`Clone`/`Linear` don't share this risk, since their checks already
   happen at the declaration with full field access.
7. What migration fixtures demonstrate both the old restriction's removal and the
   deliberate loss of automatic nominal row implementations after record retirement?

## Decision

**Outcome:** *(pending)*
