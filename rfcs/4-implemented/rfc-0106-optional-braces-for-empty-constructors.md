---
id: rfc-0106
title: "Optional Braces for Empty Constructors"
date: '2026-07-14'
status: implemented
target:
updated: '2026-07-14'
impl_status: implemented
coverage:
  "1": { spec: "spec.declarations.structs.instantiation-and-field-access.dynamics-2" }
  "2": { spec: "spec.declarations.enums.dynamics-1" }
  "3": { spec: "spec.declarations.enums.instantiation.legality-1" }
  "4": { spec: "spec.declarations.structs.instantiation-and-field-access.legality-2" }
  "5": { spec: "spec.declarations.structs.instantiation-and-field-access.legality-3" }
  "6": { spec: "spec.declarations.enums.legality-1" }
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

let a := Empty;
let b := Empty {};

enum Flag {
    On {},
    Off,
}

let x := Flag::On;
let y := Flag::On {};
```

## Implementation Notes

No new runtime behavior is intended here. This is surface-syntax normalization:

- the parser/typechecker should treat a bare zero-field struct name as construction
  of that struct
- the parser should also accept the braced spelling for zero-field enum variants,
  matching the bare-path form that already works today

## Coverage Checklist (added 2026-08-19, not part of the original RFC)

Retroactive breakdown of this RFC's distinct, fixture-testable normative claims,
as headed sections for citation purposes only. The document above is
unchanged and remains the historical record. Deliberately excludes claims that
aren't independently observable from a program's behavior -- implementation
strategy, design rationale, or internal architecture discussion belongs in the
RFC's own prose, not here.

### 1. Zero-field struct constructor forms

For a zero-field struct, both the bare type name and the braced form construct
the value: `Empty` and `Empty {}` are equivalent expressions.

### 2. Zero-field enum-variant constructor forms

For a zero-field enum variant, both the bare qualified path and the braced form
construct the variant: `Type::Variant` and `Type::Variant {}` are equivalent
expressions.

### 3. Non-empty constructors retain field syntax

A struct or enum variant with fields cannot omit its constructor fields. A bare
non-empty struct name is resolved as a name rather than as construction.

### 4. Zero-field struct legality

For a zero-field struct, both the bare type name and the braced form are valid
constructor expressions -- distinct from claim 1's dynamics half (that the two forms
are *equivalent*), this is the legality half: that both forms are accepted at all.

### 5. Non-empty struct constructors retain field syntax

A struct with fields cannot omit its constructor fields; its bare type name is
resolved as an ordinary name, not a constructor expression. The struct-side half of
claim 3, which cites only the enum-variant side.

### 6. Zero-field enum-variant legality

For a zero-field enum variant, both the qualified path and the braced form are valid
constructor expressions -- the legality half of claim 2, mirroring claim 4 for enums.
