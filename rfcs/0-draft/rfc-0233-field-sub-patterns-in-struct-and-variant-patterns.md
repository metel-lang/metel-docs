---
id: rfc-0233
title: "Field Sub-Patterns in Struct and Variant Patterns"
date: '2026-11-16'
status: draft
---

## Summary

A struct or variant pattern entry may take a pattern after the field name, as a record pattern's entry does:
`Tag { n: 0 }`, `Tag { n: k }`, `Shape::Circle { r: 0 }`, `Some { value: Some { value: v } }`. Today an entry is a bare
name (`Tag { n }`), so a field can be bound or skipped but never renamed, and a literal or nested pattern cannot be matched in
it. The bare form stays, and means `n: n`. Field names stay bare (not dotted).

This extends RFC-0107's pattern forms and RFC-0032 section 5's visibility rule; it changes no rule of either. Tracked by
metel-core#2055. This is a design draft. Nothing here is accepted.

---

## Motivation

RFC-0107 section 1.2 specifies `Some { value }` and RFC-0032 section 5 specifies the struct form with bare field bindings. RFC-0032's
original example wrote `Token { kind: TokenKind::Ident, .. }`; the 2026-08-24 correction (metel-core#753/#755) records that struct
patterns shipped with bare bindings only, and that the nested form is not required by that section's normative claims.

The result is an asymmetry. A record pattern takes `.label: p` (RFC-0151), and a named struct, which cannot be written as a record
pattern, has no way to match a literal in a field or to bind it under another name. The workaround is a guard
(`Tag { n } if n == 0`), which hides the field's value from exhaustiveness, so such an arm never counts toward covering the type.

---

## Proposal

### 1. Entries

| Entry | Meaning |
|---|---|
| `f` | bind the field `f` to a name `f` (unchanged; the bare form of RFC-0107 section 1.2) |
| `f: p` | match the field `f` against the pattern `p` |
| `..` | skip every field not named (unchanged) |

`p` is any pattern: a name (the rename), a literal, a wildcard, an enum or struct pattern, a record or tuple pattern,
an array pattern. A bare entry `f` is exactly `f: f`. Entries of both kinds may be mixed in one pattern, and the
form applies to a struct, a qualified variant (`Shape::Circle { r: 0 }`) and a bare variant (RFC-0107 section 1.2) alike.
RFC-0107's resolution is unchanged: a bare variant name is resolved from the scrutinee's type, and the field
sub-patterns are then checked against that variant's field types.

The field name is written **bare**, not dotted. RFC-0221's rule is that a name is dotted when it is a label of a row and
bare when it is a member a nominal type declares for itself; a struct's fields are the second kind, and `n` in
`Tag { n: x }` is the same name as in `Tag { n: 1, label: "" }`.

### 2. Typing and exhaustiveness

1. A sub-pattern is checked against the type of its field, with the type's arguments substituted for a generic struct
   or variant. A field named twice is an error, as in a struct literal.
2. A sub-pattern that can fail makes the pattern refutable at the position where it is written, and the pattern is
   rejected in a `let` declaration for that reason (RFC-0151's rule for record patterns).
3. A struct has one shape, so an unguarded arm is exhaustive for its struct type when every sub-pattern in it is
   irrefutable. With a refutable sub-pattern the arm covers only the values it matches, and exhaustiveness is checked
   **field by field** over the arms, as for record patterns: a `match` is exhaustive when every combination of the
   fields' values is covered. A variant's arms combine with RFC-0107 section 2's variant-coverage rule, field by field inside
   each variant.
4. **Visibility is unchanged** (RFC-0032 section 5). A pattern outside the declaring module that names a private field,
   with a sub-pattern or without one, is `T0009`; the field must be omitted, which requires `..`.

### 3. Not changed

- The bare form, the single-segment variant form and the `Pattern::EnumVariant` rewrite of RFC-0107 sections 1.1 and 1.2.
- The record pattern's `.label: p`, which stays dotted: a record's labels are row labels.
- Anonymous-record and nominal patterns remain different forms; this RFC gives the nominal one what the record one
  already has, and does not let a record pattern match a struct.

---

## Alternatives considered

1. **Names only; use a guard for a literal (`Tag { n } if n == 0`).** The status quo. A guard hides the field's value from
   exhaustiveness, so such an arm never counts toward covering a type, and a rename is impossible.
2. **Dotted names (`Tag { .n: x }`).** Rejected under section 1: the dot marks a row label, and `n` is not one.
3. **A separate rename syntax (`Tag { n as x }`).** One more form for what `n: x` already says in a record pattern.

---

## Implementation notes

The grammar's `field_pat_list` takes an optional `: pattern` after each name. The AST entries of `Pattern::Struct` and
`Pattern::EnumVariant` gain a nested pattern, as `Pattern::Record` has (`nested`); inference, construction, move
checking, the evaluator and generic-body retention resolve a nested pattern against the field's type with the
machinery record sub-patterns already use (metel-core#2035), and the field-wise exhaustiveness check is the one record
patterns use. Spec changes: the struct-patterns section of `expressions.md` (its sentence that sub-patterns are always
plain bindings) and the unqualified-variant section. The spec's Struct patterns rules stay as they are for the bare form.

---

## Interaction with other work

- **RFC-0107** (implemented): the bare form and the single-segment variant rewrite are unchanged; this RFC adds to the entries
  of the patterns it specifies.
- **RFC-0032** (implemented): section 5's visibility rule applies unchanged to every named field, with or without a sub-pattern.
- **RFC-0151** (implemented): the record pattern's nested sub-patterns and its field-wise exhaustiveness are the model, and share
  their implementation (metel-core#2035).
- **RFC-0221** (implemented): the rule that a name is dotted when it is a row label and bare when it is a member a nominal type
  declares settles the spelling.

---

## Open questions

None known. The design follows the record pattern's, whose behaviour is implemented and specified.

---

## Decision

**Outcome:** *(pending)*
