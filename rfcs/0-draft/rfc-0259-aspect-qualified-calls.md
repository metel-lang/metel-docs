---
id: rfc-0259
title: "Aspect-qualified calls"
date: '2026-11-27'
status: draft
---

## Summary

A caller can explicitly select the instantiated aspect that supplies a receiver
method. This proposal owns the call syntax deferred by RFC-0228. It can be
specified independently of expected-type method selection.

## Motivation

A type can implement both `Conv<i64>` and `Conv<String>`. RFC-0228 allows a
call through a bound to select the exact implementation, but a direct call
through a receiver with both implementations is ambiguous:

```metel
fun as_int<T: Conv<i64>>(value: &T) -> i64 {
    value.conv()
}
```

An explicit call form would let a caller name the same aspect identity without
introducing a helper for each method.

## Proposed semantics

A qualified call supplies the aspect declaration, its type arguments, the
method name, and a receiver. Under the candidate spelling below, the first
written argument supplies the receiver:

```metel
let n := Conv<i64>::conv(&item);
let s := Conv<String>::conv(&item);
```

The spelling is illustrative. For a concrete receiver, the checker selects the
applicable implementation of the named instantiated aspect under the ordinary
coherence and visibility rules. For a generic receiver, the current bounds must
entail that aspect instance. A receiver with both bounds can therefore select
one explicitly. The qualifier selects only the named aspect and its method,
including any default implementation supplied by that aspect.

The method retains its declared receiver access and ordinary ownership,
argument-binding, and effect rules. For a method with a defaulted parameter,
its aspect declaration supplies the default under RFC-0248. An explicit call
cannot supply an implementation excluded by ordinary accessibility, an unmet
bound, or an invalid receiver. The expected result type checks the selected
call as usual, while the qualifier determines the aspect identity.

## Scope and alternatives

- `Conv<i64>::conv(&item)` names the aspect instance and gives the receiver as
  an argument. It needs a path lookup rule for a receiver method.
- `<Item as Conv<i64>>::conv(&item)` also names the target type, which can help
  in contexts where the receiver alone cannot determine it. This would add a
  new qualifier to Metel. RFC-0082 considered it for associated types and
  did not adopt it.
- A receiver-side qualifier such as `item.conv::<Conv<i64>>()` keeps the
  receiver spelling but overlaps existing explicit generic method arguments.
- Calling through a bound remains available under RFC-0228.

RFC-0127 owns receiverless associated functions. RFC-0250 owns selecting a
named provider at an implementation grant. This RFC covers selection at a call
site. Associated-type projection syntax and general explicit-receiver calls to
inherent methods are separate topics.

## Open questions

1. Choose a spelling and disambiguate it from associated functions, type and
   module paths, and ordinary explicit generic arguments.
2. Decide how the receiver is passed for shared, exclusive, and owned methods,
   including whether implicit receiver borrowing applies to the chosen spelling.
3. Decide whether the first slice includes calls through aspect objects and
   how qualification uses their retained aspect evidence.

## Decision

**Outcome:** *(pending)*
