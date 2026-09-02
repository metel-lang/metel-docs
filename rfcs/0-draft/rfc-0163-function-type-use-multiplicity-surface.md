---
id: rfc-0163
title: "Function-Type Use-Multiplicity Surface"
date: '2026-09-02'
status: draft
target:
---

## Summary

RFC-0134 gives every function value a use-multiplicity axis: it is `Copy` exactly
when its captures are `Copy`, otherwise it is move-only. RFC-0152 permits
capability widening only at first-order sites and requires exact capability
matching below the first nested function level.

Written function types can spell `once` and `var`, but cannot spell the
use-multiplicity axis. Consequently `(T) -> U` is ambiguous: it may be a
requirement for a `Copy` callable, a requirement for a move-only callable, or
an axis-agnostic callable type. The ambiguity becomes observable in generic
higher-order APIs such as `map(f: (T) -> U)`: a concrete `Copy` named function
and a function-type annotation must be reconciled without silently turning the
RFC-0152 first-order limit into a general nested widening rule.

This RFC settles that surface representation and the corresponding matching
rule. It does not reopen the v0.13.0 capture default, `once`/`many`, `var`, or
the higher-order variance question deferred to RFC-0155.

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

## Design space

### A. Add a use-multiplicity qualifier to function types

Introduce an explicit type-level qualifier, with a spelling chosen by this
RFC. A bare type would receive one documented default; APIs that need the
other capability would write it. This makes exact nested matching literal, but
adds syntax and a migration question for existing function-type annotations.

### B. Make written function types axis-agnostic

`(T) -> U` would quantify over use multiplicity rather than denote either
concrete capability. A value supplies its actual `Copy`-ness; the written type
does not constrain it. This keeps existing syntax compact, but requires a
precise account of which operations are permitted through such an abstraction
and how it composes with fields, returns, and type aliases.

### C. Default written function types to `Copy`

A bare type would require a `Copy` callable; a separate spelling would be
needed for move-only values. This keeps the common named-function case simple
and lets nested matching remain literal, but risks making APIs unintentionally
exclude closures that capture owned non-`Copy` state.

### D. Default written function types to move-only

A bare type would require a move-only callable, with a separate spelling for
`Copy`. This is conservative for ownership but makes ordinary named functions
need a special reconciliation rule or annotation, which is the current gap.

## Questions to resolve

1. Does use multiplicity need a source-level qualifier, and if so what is its
   spelling and default?
2. If bare types are axis-agnostic, are they existential, universally bounded,
   or a distinct capability state in `Type::Fun`?
3. Can a generic callback position erase this axis while a concrete nested
   function type remains exact? If yes, define the boundary mechanically.
4. Which type positions may write or infer the chosen form: parameters,
   returns, fields, aliases, `dyn Callable` (RFC-0161), and generic bounds?
5. Does the decision amend RFC-0152's "exact below nesting" wording, or merely
   state that an omitted axis is not a concrete nested capability?

## Required integration examples

The accepted proposal must work through, at minimum:

```metel
fun map<T, U>(xs: List<T>, f: (T) -> U) -> List<U> { /* ... */ }
fun add_one(x: i64) -> i64 { x + 1 }

let mapped := map([1, 2], add_one);
```

and a move-only capturing closure passed through the same API, a function type
nested under a parameter with mismatched `once`/`var`, a field storing the
callback, and a type alias. The examples must distinguish surface-axis
abstraction from RFC-0152 widening.


---

## Decision

**Outcome:** *(pending; no implementation decision is authorized by this draft)*
**Target:** *(set when accepted)*
