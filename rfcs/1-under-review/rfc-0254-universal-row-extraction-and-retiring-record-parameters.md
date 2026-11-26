---
id: rfc-0254
title: "Universal Row Extraction and Retiring Record Parameters"
date: '2026-11-25'
status: under-review
updated: '2026-11-25'
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

The language owner agreed to the direction and the initial categories below on
2026-11-25. This RFC remains under review: interactions, migration, soundness and
syntax need review and no implementation is authorized until integration.

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

These initial categories are agreed direction; other current and future types need an
exhaustive classification before integration. Empty means the row contains no fields,
not that the type is the empty record. `..T` forgets the nominal brand, while `T` retains
its identity. Extraction at a privileged derivation boundary may require a different
full-field operation; that deferred design is not specified here.

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
must not invoke an `A` method on `T` itself without a separate `T: A` bound.

A bound and a row literal use the syntax of RFC-0208. The `record T` binder is removed
as a distinct generic kind; the declaration kind's retirement is RFC-0243. A plain type
parameter's ordinary well-formedness and kind rules still apply. No implicit dereference,
owned conversion, field move, reference creation, or automatic nominal aspect grant is
introduced by type-level extraction.

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
- **RFC-0209 / RFC-0214 / RFC-0217:** nominal row implementations and residual aspect
  behavior are deferred; extraction and a vacuous field-wise bound do not settle them.
- **RFC-0253:** generic nominal residual projections retain their instantiated brand and
  may include row-kind arguments; privacy and substitution need cross-module checks.
- **References and ownership:** `..&T` is empty, not `..T`; this does not alter borrowing,
  `Drop`, linearity, or the destruction of private fields. A type-level row is not an
  owned or borrowed record value.

## Open questions

1. Classify every current type, including arrays, slices, function types, `Never`, aspect
   objects and abstract or associated types. Are any intentionally excluded from universal
   extraction, and what does a generic body know about an abstract type's row?
2. What exact constraint and diagnostic preserves old `<record T>` eligibility where an
   API requires it, and should the old binder have a staged migration?
3. How do universal extraction and empty exact rows affect overload selection, type
   inference, coherence, orphan rules, negative bounds and field-wise aspect constraints?
4. How do public-row opacity and exactness interact with generic aliases, separate
   compilation, private representation changes and row remainder inference?
5. Which grammar distinguishes a row extraction, row literal, row binder, and variadic
   syntax, and how do explicit type/row arguments and equations compose with RFC-0192?
6. Are empty-row field-wise bounds vacuous for all aspects, including ownership and
   auto aspects, without accidentally granting an aspect to the enclosing type?
7. What migration fixtures demonstrate both the old restriction's removal and the
   deliberate loss of automatic nominal row implementations after record retirement?

## Decision

**Outcome:** *(pending)*
