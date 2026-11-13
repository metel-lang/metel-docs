---
id: GAP-OWNERSHIP-004
title: "Structural `Copy` for named types and their residuals is a compiler rule, not something the language can express"
summary: "A residual of a `Copy` brand is `Copy` over its present fields by a rule the compiler hardcodes; the language has no way to state an aspect over the fields of a brand's residual, so the rule cannot be written in std or by a user."
scope: "reference/spec/ownership.md#spec.ownership.aspects-on-a-residual.legality-1"
owner: language
discovered_by: "language owner review of the v0.16.0 Declarations and derivation milestone, 2026-11-13; metel-core#1823"
disposition: planned
tracked_by: metel-core#1823
rfc: RFC-0217
review: null
---

## Gap

`Aspects on a residual` (RFC-0211) says a residual `T.{ .fields }` is `Copy` exactly when `T`'s declaration grants `Copy` and the
present fields are `Copy`, with the provided `Clone`, and that every other aspect that needs an impl is `T0012` on a residual. The `Copy`
rule is native compiler logic. A correct implementation of the current spec still has this property, because the language has no way
to write an aspect's impl over the *fields of a residual*: a written impl never applies to a residual (RFC-0211 rule 2), a derived impl
does not either (rule 3), and impls for a residual are not expressible (RFC-0214 is a draft). The same holds for structural `Copy` of
named types, which RFC-0206 lists as a "named, time-boxed exception".

## Impact

No accepted program is affected: the rule gives residuals the `Copy` the declaration grants. The gap is expressiveness. The `Copy`
rule for residuals cannot be moved to std, and an author cannot give an aspect of their own a structural meaning on a residual, so
for every aspect other than `Copy` and `Drop` a projection satisfies nothing (`T0012`, "template not yet available").

## Affects

- `spec.ownership.aspects-on-a-residual.legality-1`
- `spec.ownership.aspects-on-a-residual.legality-3`
- `RFC-0211`
- `RFC-0217`
- `RFC-0214`

## Resolution

Planned, with an explicit exit condition. The native rule is a named exception tracked as metel-core#1823 (RFC-0206 section 2, "Temporary
workarounds and their exits"): it is replaced by the std-written row template of RFC-0217 (tracked by metel-core#1834) once the row
templates of RFC-0209 and RFC-0210 and `comptime for` (RFC-0174, on the comptime core of RFC-0132) land, **with no change in accepted
programs**. The exit is complete when the native structural `Copy` path for named types and residuals is deleted, the fixtures for
`copy struct` projections pass unchanged (a residual such as `W<String>.{ .n }` stays `Copy`), and RFC-0206 section 6 and RFC-0211's
v0.16.0 notes no longer list the exception. The exit has no date of its own: it waits on comptime and RFC-0217.
