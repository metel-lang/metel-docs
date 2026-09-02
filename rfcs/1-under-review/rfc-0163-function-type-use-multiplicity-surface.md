---
id: rfc-0163
title: "Function-Type Use-Multiplicity Surface"
date: '2026-09-02'
status: under-review
target: v0.13.0
updated: '2026-09-02'
tracking: 'https://github.com/metel-lang/metel-core/issues/936'
---

> **Status — under review (2026-09-02).**

## Summary

RFC-0134 gives every function value a use-multiplicity axis: it is `Copy` exactly
when its captures are `Copy`, otherwise it is move-only. RFC-0152 permits
capability widening only at first-order sites and requires exact capability
matching below the first nested function level.

Written function types can spell `once` and `var`, but cannot spell the
use-multiplicity axis. Consequently `|T| -> U` is ambiguous: it may be a
requirement for a `Copy` callable, a requirement for a move-only callable, or
an axis-agnostic callable type. The ambiguity becomes observable in generic
higher-order APIs such as `map(f: |T| -> U)`: a concrete `Copy` named function
and a function-type annotation must be reconciled without silently turning the
RFC-0152 first-order limit into a general nested widening rule.

This RFC proposes a surface representation and corresponding matching rule. It
does not reopen the v0.13.0 capture default, `once`/`many`, `var`, or the
higher-order variance question deferred to RFC-0155.

---

## Motivation

The three fields carried by `Type::Fun` are not equally visible in source:

| Axis | Source spelling | Default |
| --- | --- | --- |
| call multiplicity | `once` | `many` |
| call mutation | `var` | reading |
| by-value use multiplicity | *none* | unspecified |

The missing third spelling was exposed while implementing the closure cluster.
The frontend must currently reconcile a written generic callback type with a
concrete callable whose `Copy`-ness is known from its captures. Treating a
written type as move-only rejects ordinary named callbacks in generic APIs;
treating the mismatch as general widening contradicts RFC-0152's exact-nested
rule. Neither behavior is a satisfactory implicit language decision.

The issue is also user-facing. A signature communicates the call and mutation
requirements it places on a callback, but currently cannot communicate whether
the callback is retained, copied, or consumed by value. That makes an API's
ownership contract incomplete precisely where higher-order functions need it.

## Scope and constraints

- Preserve RFC-0152's first-order-only rule for actual capability widening.
- Preserve RFC-0134's fact that a closure's concrete `Copy`-ness is derived
  from its captures, not inferred from call sites.
- Keep a generic callback signature usable with ordinary named functions and
  capture-free closures.
- Decide whether the chosen spelling is an assertion, an upper/lower bound, or
  an axis-agnostic abstraction; construction and diagnostics must agree.
- Reconcile the result with RFC-0155, which owns variance and subtyping for
  genuinely nested function types.

## Proposal

### Surface syntax

A bare function type erases its use multiplicity:

```metel
fun map<T, U>(xs: List<T>, f: |T| -> U) -> List<U> { /* ... */ }
```

It accepts either a `Copy` or a move-only function value. It does **not** give
the holder permission to copy the value: an erased value is usable as a
move-only value unless the type says otherwise.

This RFC adds `copy` as a function-type qualifier for an API that requires a
copyable callable:

```metel
fun duplicate_callback(f: copy |i64| -> i64) -> () { /* may copy `f` */ }
```

`copy` composes with the existing qualifiers in the same prefix position:

```metel
copy once |T| -> U
copy var |T| -> U
copy once var |T| -> U
```

As with `once` and `var`, the type spelling's qualifier order is
order-insensitive. A closure literal still has its independently specified
`[captures] once? var? |params|` prefix; `copy` is never written on a literal,
because its concrete capability is derived from its captures.

`copy` joins `once` and `var` as a reserved keyword in v0.13.0. The qualifier
family therefore cannot be used as ordinary identifiers, including in a
binding, path segment, or field name. A future RFC may consider making the
whole family contextual, but it must do so as a compatibility and lexer/parser
change for all three words together; this RFC does not make that change.

There is intentionally no source `move` qualifier in this proposal. A caller
that merely accepts, stores, returns, or consumes a callable needs no stronger
promise than a bare erased type gives it. `copy` is needed because copying is
the capability that must be statically established. A future use case for an
exact move-only assertion may extend this RFC, but must not redefine bare
types in the meantime.

### Type model and matching

`Type::Fun` gains an internal third use-multiplicity state, here called
`Erased`, beside its concrete `Copy` and `Move` states. `Erased` is produced by
lowering a source function type whose `copy` qualifier is absent. It is not
inferred for a function value: named functions, capture-free closures, and
closures whose captures are all `Copy` have concrete `Copy`; a closure with a
non-`Copy` capture has concrete `Move`.

The use-axis matching relation is directional:

| Actual value | Expected type | Allowed | Resulting static capability |
| --- | --- | --- | --- |
| `Copy` | bare / `Erased` | yes | erased |
| `Move` | bare / `Erased` | yes | erased |
| `Copy` | `copy` | yes | `Copy` |
| `Move` or `Erased` | `copy` | no | — |

Erasure may occur at a parameter, ascription, field initialization, return,
or alias expansion, including under a nested function type. This is not
RFC-0152 widening: it affects only an omitted use axis. The written
`once`/`many` and `var`/reading axes remain exact below the first function-type
level, exactly as RFC-0152 requires. `Erased` must therefore not become a
general exception for nested `once` or `var` mismatches.

The existing implementation's normalization of a parsed move placeholder to a
concrete `Copy` callable is replaced by this relation. It must not retain a
Copy-to-Move special case after `Erased` exists.

### Ownership through an erased type

An erased value may be called subject to its written `once` and `var`
qualifiers, and it may be moved into another binding, field, or return value.
It may not be copied merely because the runtime value happened to be `Copy`.
For example:

```metel
fun consume(f: |i64| -> i64) -> () {
    let saved := f;       // move: permitted
    saved(1);
}

fun duplicate(f: copy |i64| -> i64) -> () {
    let a := f;           // copy: permitted
    let b := f;
    a(1);
    b(2);
}
```

A return type, field, or alias containing a bare function type similarly
forgets a concrete callable's copyability. This conservative loss is
observable and intentional; an API that promises or needs copyability writes
`copy`.

### Generic callbacks

The ordinary higher-order signature remains useful for both categories of
callable:

```metel
fun map<T, U>(xs: List<T>, f: |T| -> U) -> List<U> { /* call `f` for each item */ }
fun add_one(x: i64) -> i64 { x + 1 }

let mapped := map([1, 2], add_one);
let offset := 10;
let shifted := map([1, 2], [offset] |x: i64| -> i64 { x + offset });
```

If an implementation copies a callback rather than merely calling or moving
it, its signature must require `copy`. This makes the ownership contract
visible without introducing `Callable` bounds before RFC-0161.

## Alternatives considered

### A. Concrete default with qualifiers for both capabilities

Giving bare types either a `Copy` or move-only concrete default makes nested
matching literal, but cannot express the common "accept either" callback API
without a second abstraction. It either rejects stateful closures or ordinary
named callbacks. The proposal instead makes that abstraction explicit in the
meaning of omission.

### B. Axis-agnostic bare types without a `copy` spelling

This solves `map`, but leaves an API unable to say it will duplicate a callback
or return one that callers may duplicate. The proposal retains axis erasure for
bare types and adds only the positive `copy` requirement.

### C. Default written function types to `Copy`

A bare type would require a `Copy` callable; a separate spelling would be
needed for move-only values. This keeps the common named-function case simple
and lets nested matching remain literal, but risks making APIs unintentionally
exclude closures that capture owned non-`Copy` state.

### D. Default written function types to move-only

A bare type would require a move-only callable, with a separate spelling for
`Copy`. This is conservative for ownership but makes ordinary named functions
need a special reconciliation rule or annotation, which is the current gap.

## Required integration examples

The accepted proposal must work through, at minimum:

```metel
fun map<T, U>(xs: List<T>, f: |T| -> U) -> List<U> { /* ... */ }
fun add_one(x: i64) -> i64 { x + 1 }

let mapped := map([1, 2], add_one);
```

and a move-only capturing closure passed through the same API, a rejected
attempt to copy a bare callback, an accepted `copy` callback duplication, a
function type nested under a parameter with mismatched `once`/`var`, a field
storing the callback, and a type alias. The examples must distinguish
surface-axis erasure from RFC-0152 widening.


---

## Decision

**Outcome:** *(proposed — bare function types erase use multiplicity; `copy`
requires it concretely. Pending review.)*
**Target:** *(set when accepted; no implementation is authorized while this RFC
remains draft)*
