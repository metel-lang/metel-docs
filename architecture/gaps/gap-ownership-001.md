---
id: GAP-OWNERSHIP-001
title: "No borrow checking: reference exclusivity and duration are not enforced"
summary: "Nothing prevents a shared and an exclusive reference to the same place from coexisting."
scope: "reference/spec/ownership.md#what-ownership-does-not-cover"
owner: language
discovered_by: "metel-core#1212 limitation analysis; `reference/spec/ownership.md` (References and Moves); `typed_ast` `RefTemp` note"
disposition: known
planned_for: v0.16.0
rfc: RFC-0122
review: null
---

## Gap

The ownership rules stop a reference from being consumed and prevent moving
out through one, but they grant no exclusivity guarantee: the reborrow's
duration is not tracked, and shared-XOR-exclusive is not enforced. The
Language Spec assigns that to a future borrow checker, which RFC-0122
proposes and which is still under review.

## Impact

A program can hold overlapping shared and exclusive references without a
compile-time error: `both(&x, &var x)` for `fun both(a: &i64, b: &var i64)`
typechecks and runs. Soundness arguments that rest on exclusivity, such as for
temporaries materialized behind a reference, hold only because nothing can
alias them, not because a checker proves it.

## Affects

- `spec.ownership.references-and-moves.legality-1`
- `RFC-0122`

## Resolution

None yet. RFC-0122 is at `1-under-review`; when it reaches `3-integrated` this
gap resolves and the record closes against that RFC.
