---
sidebar_position: 6
---

# Call multiplicity and the mutation axis

A closure's function type carries two written qualifiers besides its parameter and return
types:

- **`once`** — invoking the closure consumes one of its captures. Written when the body
  moves a capture out (returns it, or passes it by value to something that takes
  ownership). [Omitting it when the body consumes a capture is an error](capture-semantics.md#spec.functions.closures.legality-8);
  the default is *many* (reusable).
- **`var`** — invoking the closure mutates a capture. Written when the body assigns to a
  by-value capture, takes `&var` of one, or calls a `&var self` method on one, and
  [always when the closure captures `[&var x]`](capture-semantics.md#spec.functions.closures.legality-25),
  regardless of what the body does through it. The default is *reading*.

The two qualifiers are [order-insensitive as a *type* spelling](capture-semantics.md#spec.functions.closures.legality-24);
in a closure *literal* the [fixed order is `[captures] once? var? (params)`](capture-semantics.md#spec.functions.closures.legality-23).
An unqualified literal in a typed position takes [its `once` / `var` from the expected
type](capture-semantics.md#spec.functions.closures.legality-18) rather than defaulting and then failing.
Verification runs in a [fixed stage order — capture classification, then `use_multiplicity`,
then `once`, then `var`](capture-semantics.md#spec.functions.closures.legality-19); the two axes are checked
independently.

[A function value may be used where a *less permissive* multiplicity is
expected](capture-semantics.md#spec.functions.closures.legality-9) — a *many* value satisfies a `once` slot, a
*reading* value satisfies a `var` slot, a `Copy` value satisfies a non-`Copy` slot — at
first-order argument, ascription, field-init, and return positions. The reverse is
rejected. A conditional's type is the least-permissive of its arms, each arm widening to
it. [Widening changes only the static type](capture-semantics.md#spec.functions.closures.dynamics-12): a
widened `reading` value keeps its plain call behaviour, and a `var`-typed field that holds
one is [thereafter observed `var`, with no re-narrowing](capture-semantics.md#spec.functions.closures.dynamics-14).

Whether a closure value is [`Copy` is exactly whether every capture is
`Copy`](capture-semantics.md#spec.functions.closures.legality-20); a `Copy` closure is necessarily *many*.

[A `mutating` call needs exclusive access to the closure value for the call's
duration](capture-semantics.md#spec.functions.closures.legality-10): the callee must be an owned binding, an
owned temporary, an exclusive projection off one, or a `&var` parameter — not a
shared-`&` callee. [Overlapping and reentrant `mutating` calls on the same closure value
are rejected](capture-semantics.md#spec.functions.closures.dynamics-9). If a `var` call exits early via `?` or
`return`, [its partial mutations persist and the closure stays
callable](capture-semantics.md#spec.functions.closures.dynamics-13); a `panic` is uncatchable and ends the
process, so no post-exit state is observable.
