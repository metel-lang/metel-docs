---
id: GAP-FUNCTIONS-004
title: "`?` is defined for the core `Result` and `Option` only; there is no `Try` aspect"
summary: "`?` works on the core `Result` and `Option` and on no other type; a user-defined type cannot be propagated with `?`. A future `Try` aspect would generalise the rule."
scope: "reference/spec/functions.md#spec.functions.the-operator.legality-1"
owner: language
discovered_by: "RFC-0182 review (metel-core#1593); alternative 2 and Open Question 1"
disposition: known
rfc: RFC-0182
review: null
---

## Gap

`?` is a compiler special form over exactly two types. The operand and the enclosing function's
return type must both be the core `Result` or both the core `Option` (RFC-0182), and the checker
recognises them by declaration identity, not through any aspect. A user-defined type, however
Result-like, cannot be used with `?` as an operand or as a return type.

RFC-0182 accepted this closed rule on purpose, as the first two impls of a future `Try` aspect:
`?` would be defined over any type implementing the aspect, with `Result` and `Option` as its
first two implementations. That generalisation is additive, so programs written against the closed
rule keep compiling. It needs a residual/branch design (the associated types, and how the error
conversion composes with `From`), and it interacts with object safety (RFC-0008) and the `Callable`
question for closures (RFC-0161). None of that is designed or scheduled.

## Impact

Only `Result` and `Option` can carry an early exit through `?`. A library type that models its own
fallible or absent value must be bridged to one of the two (`.ok()`, `.ok_or(...)`, or a
conversion method) before `?` applies. The closed rule also fixes one semantic: `None` carries no
payload, so the `Option` row has no conversion step.

## Affects

- `spec.functions.the-operator.legality-1`
- `RFC-0182`

## Resolution

Not scheduled. The open design question is metel-core#1637, which has no milestone. If it is taken up, RFC-0182's
closed rule becomes the first two impls of the aspect rather than being replaced.
