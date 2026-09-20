---
id: GAP-FUNCTIONS-001
title: "Free-function overloading is implemented but the Language Spec does not describe it"
summary: "A module can declare several free functions with one name and the compiler resolves calls by exact argument types, but the spec states no rules for it, including whether an overloaded name can be used as a value."
scope: "reference/spec/functions.md#first-class-functions"
owner: language
discovered_by: "answering whether same-named functions share a SymbolId; checked against reference/spec/functions.md"
disposition: known
review: null
---

## Gap

The compiler supports free-function overloading (METEL-180): a module may declare
several `fun`s with one name if they are non-generic, fully annotated and differ
in their parameter types (identical signatures are `T0011`); a call selects a
definition by **exact** argument types, with no implicit numeric coercion. None
of this is in the Language Spec. The only mention of overloading in
`reference/spec/` is the built-in `assert` (`runtime.md`). The spec has no rule
for declaring overloads, for how a call picks one, for what makes two
definitions distinct, or for the restrictions (non-generic, module-local: an
overload set is not exported across modules, `LIMIT-TYPE-CONSTRUCTION-002`).

One consequence is visibly undefined. An overloaded name cannot be used as a
value: `let g := f;` and `apply(f)` both fail with `T0003 undefined name `f``
(`metel-core#1230`). Whether that is intended, or whether `f` should resolve
against an expected function type, is a language decision the spec does not
make.

## Impact

Programmers can use a feature the spec never promises, and cannot tell from it
what is guaranteed, what is an accident of the current implementation, or how
overloads interact with function values, generics and imports. Method overloading
is also unspecified; the implementation does not support it (`metel-core#1229`).

## Affects

- `spec.functions.first-class-functions.legality-2`
- `RFC-0128`

## Resolution

None yet. RFC-0128 (draft) covers exportable overload sets; specifying the
rules above, including overloaded function values, needs its own accepted design.
