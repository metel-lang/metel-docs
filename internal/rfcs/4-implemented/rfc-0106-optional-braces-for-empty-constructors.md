---
id: rfc-0106
title: "Optional Braces for Empty Constructors"
date: '2026-07-14'
status: implemented
target:
updated: '2026-07-14'
impl_status: implemented
---

> **Status — accepted (2026-07-14).** Narrow scope only: zero-field structs may omit
> braces, and zero-field enum variants declared with braces may also be constructed
> with braces. Non-empty constructors are unchanged.

> **Status — integrated (2026-07-14).** Integrated into the declarations spec's
> struct and enum instantiation sections.

> **Status — implemented (2026-07-14).** Parser and typechecker now accept `Empty`
> / `Empty {}` interchangeably for zero-field structs, and `Type::Variant {}` for
> zero-field enum variants alongside the already-supported bare-path form.

## Summary

Permit both bracketed and bracketless construction syntax when a constructor's field
set is empty:

- zero-field structs may be written as either `Empty` or `Empty {}`
- zero-field enum variants may be written as either `Type::Variant` or
  `Type::Variant {}`

---

## Motivation

The language currently handles these two empty-constructor cases inconsistently.

- Empty struct construction still requires braces. `struct Empty {}` may be
  constructed as `Empty {}`, but bare `Empty` is resolved as an ordinary name and
  fails.
- Empty enum variants declared with braces already construct through the bare path.
  For `enum Flag { On {} }`, `Flag::On` works today, but `Flag::On {}` is currently
  rejected by the parser.

That leaves "empty constructor" syntax split across two different rules for no clear
semantic reason. RFC-0100 already moved the surface syntax toward lighter-weight,
constructor-oriented forms; this is the same cleanup applied to the zero-field case.

---

## Decision

When a struct has zero fields, both `Empty` and `Empty {}` are valid and equivalent.

When an enum variant has zero fields, both `Type::Variant` and `Type::Variant {}`
are valid and equivalent.

This change is strictly limited to the zero-field case. Non-empty structs and
non-empty enum variants still require their ordinary field syntax; there is no
bracket elision for constructors that actually carry data.

## Examples

```metel
struct Empty {}

let a = Empty;
let b = Empty {};

enum Flag {
    On {},
    Off,
}

let x = Flag::On;
let y = Flag::On {};
```

## Implementation Notes

No new runtime behavior is intended here. This is surface-syntax normalization:

- the parser/typechecker should treat a bare zero-field struct name as construction
  of that struct
- the parser should also accept the braced spelling for zero-field enum variants,
  matching the bare-path form that already works today
