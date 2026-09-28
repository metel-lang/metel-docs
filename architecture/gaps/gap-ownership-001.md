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

`T[]` inherits the same hole. RFC-0126 describes it as "produced only by
borrowing a `List<T>`, a `[T; N]`, or another slice"
([spec.types.arrays.legality-1](../../reference/spec/types.md#spec.types.arrays.legality-1)),
but nothing tracks how long that borrow may live — storing a `T[]` in a
struct field or returning one out of the function whose local it was
borrowed from typechecks and runs cleanly, for the same reason `&T`/`&var T`
do: duration tracking is borrow-checker scope, not the move checker's.

## Impact

A program can hold overlapping shared and exclusive references without a
compile-time error: `both(&x, &var x)` for `fun both(a: &i64, b: &var i64)`
typechecks and runs. Soundness arguments that rest on exclusivity, such as for
temporaries materialized behind a reference, hold only because nothing can
alias them, not because a checker proves it.

Reproduced against current `develop` (a borrow outliving its source, not just
overlapping references):

```metel
struct Holder { items: i64[] }

fun make() -> Holder {
    var owned: [i64; 3] := [1, 2, 3];
    return Holder { items = owned };
}
```

`make()` returns a `Holder` holding a slice borrowed from its own local
`owned`. This typechecks and runs (exit 0) with or without `--move-check` —
the move checker only tracks whether a binding has been consumed, not how
long a reference derived from it may live. It is memory-safe today only
because the interpreter backs every array with `Rc<RefCell<Vec<Value>>>`:
the GC keeps the storage alive regardless of what the type system claims
about borrowing. That safety net is an artifact of the current tree-walk
evaluator ([LIMIT-EVALUATION-004](../limitations/limit-evaluation-004.md)),
not a language guarantee, and will not hold once the Compiled Profile
(metel-core#1293) stops being GC-backed.

The one place exclusivity is enforced today is dynamic and narrow: a second
`mutating` call on the same closure value while the first is still running is a
runtime error (`R0015`), which `spec.functions.closures.dynamics-9` states as the
interim rule until the borrow checker lands. It follows one closure value's own
in-call flag, so it does not catch two different closure values that capture the
same place by `&var` (the aliased-capture case left open by RFC-0050).

## Affects

- `spec.ownership.references-and-moves.legality-1`
- `spec.functions.closures.dynamics-9`
- `spec.types.arrays.legality-1`
- `RFC-0122`

## Resolution

None yet. RFC-0122 is at `1-under-review`; when it reaches `3-integrated` this
gap resolves and the record closes against that RFC.
