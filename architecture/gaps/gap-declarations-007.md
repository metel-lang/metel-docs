---
id: GAP-DECLARATIONS-007
title: "A direct call among several impls of one aspect is not resolved by its expected type"
summary: "A call that two impls of one aspect for different type arguments could answer is a `T0013` error even where the expected type decides it (`let a: i64 := l.conv()`); so is a call through a parameter bound twice by the aspect."
scope: "reference/spec/declarations.md#spec.declarations.aspects.aspect-bounds-on-function-type-parameters.legality-18"
owner: language
discovered_by: "metel-core#1987, stage 2; language owner decision 2026-11-13 (resolve by the expected type; an unannotated call stays an ambiguity error)"
disposition: planned
tracked_by: metel-core#2018
rfc: null
review: null
---

## Gap

`aspect-bounds-on-function-type-parameters.legality-18` rejects every call that two or more impls of one aspect, for different type
arguments, could answer. The language owner decided such a call resolves by its expected type, as `let a: i64 := l.conv();` and
`f(l.conv())` with `f(x: i64)`, and stays an error when nothing fixes the type. Inference is constraint-based: the expected type is
known only after unification, so the selection is a deferred goal over an inference variable (`L: Conv<?T>`), and no
deferred-obligation mechanism exists in inference yet. A correct implementation of the current spec rejects the annotated forms.

## Impact

A type that implements one aspect at several type arguments cannot have its method called directly or through a parameter bound at
each of them, whatever annotation is written. The workaround is a function with a single bound of the aspect
(`fun use_conv<X: Conv<i64>>(x: &X) -> i64 { x.conv() }`), whose bound names the type arguments.

## Affects

- `spec.declarations.aspects.aspect-bounds-on-function-type-parameters.legality-18`
- `spec.declarations.aspects.static-dispatch-only.legality-1`

## Resolution

Planned: metel-core#2018 adds the deferred obligation (a pending `type: aspect<args>` goal that picks one candidate once the expected type
is fixed, and reports `T0012` or `T0013` otherwise). The gap closes when legality-18 states the resolution and the annotated forms are
accepted.
