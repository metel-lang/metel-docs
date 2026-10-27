---
id: GAP-FUNCTIONS-005
title: "Explicit type arguments are not supported on a function with a row parameter"
summary: "`name::<…>(…)` on a function that takes an open-record (row) parameter is rejected with a targeted error; the row is inferred from the arguments."
scope: "reference/spec/functions.md#spec.functions.turbofish.legality-1"
owner: language
discovered_by: "metel-core#1646; found while checking explicit instantiation for RFC-0186's open question 5"
disposition: known
rfc: RFC-0186
review: null
---

## Gap

A function whose signature has an open-record parameter, `fun get_x<record R>(p: { x: i64, ..R })`, quantifies a synthetic type variable for `p`'s own type in addition to the declared `R`. The scheme's quantified variables are ordered by `TypeVar`, not by declaration, so written type arguments cannot be matched to the declared generics. Pinning `R` alone also leaves the synthetic variable unbound when the call's function type is instantiated.

Until a design exists, a call with explicit type arguments on such a function is `T0004`: "explicit type arguments are not supported on `get_x`: it takes an open-record parameter (a row). Remove the `::<…>`; the row is inferred from the arguments". The parser separately rejects a `..R` splice in an explicit argument list on purpose.

## Impact

The row of an open-record parameter is always inferred from the arguments; it cannot be pinned. A function that mixes a row parameter with ordinary type parameters (`fun f<T, record R>(…)`) cannot be called with `::<…>` at all, so an ordinary parameter that is not determined by the arguments cannot be pinned there either. Functions without a row parameter are unaffected and pin their generics in declaration order.

## Affects

- `spec.functions.turbofish.legality-1`
- `RFC-0186`

## Resolution

Not scheduled. The design questions are in metel-core#1647: what a type argument for a row parameter denotes (the remainder record), carrying the declared generic order on the scheme, binding the synthetic variable from the row bound, and whether `_` may stand for an inferred argument.
