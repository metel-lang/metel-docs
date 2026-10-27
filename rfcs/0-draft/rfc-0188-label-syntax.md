---
id: rfc-0188
title: "Label syntax"
date: '2026-10-26'
status: draft
---

> **Scope (2026-10-27).** This RFC was split out of RFC-0187 as "Label syntax and rows as record
> types". The rows part is dropped: rows are RFC-0186's (`record R` and the `..R` operator), which
> stays the single change to row declarations. This RFC is the label spelling only.

## Summary

**A label as a compile-time value is written `.name`**, and a label variable `.[L]`. Ordinary
fields keep their plain identifier. This is the spelling that label polymorphism (RFC-0175),
tuples as numeric-label rows (RFC-0151) and compile-time field iteration (RFC-0174) are missing.

The semantics of label polymorphism (RFC-0175) and of rows (RFC-0121, RFC-0186) are not changed
here. This RFC is the syntax layer, and it answers RFC-0175's open questions 1 to 4 on spelling.

Examples write records as `{| … |}` (RFC-0187) and row parameters as `record R` with `..R`
(RFC-0186). The label spelling does not depend on either: with the current `{ … }` and `row R`
every example reads the same apart from those tokens.

This is a design draft. Nothing here is accepted, and the grammar is unchanged until it is.

---

## Motivation

### Labels have no spelling of their own of their own

A field name in a record is a bare identifier. That is unambiguous while labels are always fixed in
the source. Three proposals need a label to be a value or a variable:

- **RFC-0175 (Label Polymorphism, `0-draft`)** wants `fun get<label L, row R, T>(r: { L: T, ..R })`.
  Written like that, `L` in field position looks exactly like a field called `L`. The draft leaves
  the binder keyword, the literal form (strings, identifier tokens, `#field`) and the selection
  syntax (`value.[L]`) open (its questions 1 to 4).
- **RFC-0151 (Tuples as numeric-label rows, `0-draft`)** would write `(a, b)` as `{ 0 = a, 1 = b }`,
  which today is not a record at all, since `0 = a` is not an identifier field.
- **RFC-0174 (compile-time iteration over a row's fields, `1-under-review`)** needs a way to name a
  label as a value.

RFC-0116 and RFC-0121 hit the same wall once already. RFC-0121 §1 and RFC-0116's projection section record that a
bare identifier in projection braces had to be "always a field label, never a row variable", because
the two were told apart only by case convention. A label variable needs a marker at its use for the
same reason a row variable needs `..`.

---

## Proposal

### Labels: `.name` and `.[L]`

A **label** is a compile-time atom, written with a leading dot where it appears as a value or a
variable:

- **`.name`** is a label literal.
- **`.[L]`** is a label variable `L` (RFC-0175's kind), and `.[expr]` is reserved for a
  compile-time label expression, to be defined by RFC-0174 if it needs one.

They are used in exactly the positions where a label is not simply the field's own name:

```metel
// a label as an argument
let id := get::<.id, _, i64>(record);

// a label variable in a type, a literal and a selection
fun get<L, R, T>(r: {| .[L]: T, ..R |}) -> T { r.[L] }
fun single<L, T>(v: T) -> {| .[L]: T |} {| .[L] = v |}
let one := single::<.id, i64>(5);
```

The existing selection `r.x` is unchanged, and `r.[L]` is the computed form, the notation RFC-0175
and RFC-0091 already use. Reading is `r.x` and `r.[L]`, and declaring a literal label is `.x`, so
the dot marks "a field" and the brackets mark "computed at compile time".

**Numeric labels** (RFC-0151) are `.0`, `.1`, matching the existing `t.0` access:

```metel
// (a, b) is notation for the row below
{| .0 = a, .1 = b |}
```

Ordinary field entries keep the plain identifier: `{| x = 1 |}` is not written `{| .x = 1 |}`.
Under `{| … |}` a field is already distinguished from a block, so a mandatory prefix would mark
everything twice. Whether `.x` should also be accepted in field position is open question 1.

**This RFC does not define the label kind.** What `.[L]` ranges over, label equality, ownership of
a drained field and the meaning of `r.[L]` for a non-`Copy` field are RFC-0175's, and its open
questions 5 to 8 stay open. This RFC settles only how a label is written.

### A worked example: a record map

A map keyed at compile time. The label-typed parameter `l: .[L]` (a label literal is also its own
singleton type) is not defined by this RFC and is open question 4; the turbofish form
`m.put::<.host>("a.com")` needs nothing beyond the spelling above. This example depends on RFC-0175
being integrated, and is illustrative.

```metel
record Rec<record R> { data: {| ..R |} }

extend<record R> Rec<..R> {
    fun empty() -> Rec<..{| |}> { Rec { data = {| |} } }

    fun put<L, V>(self, l: .[L], v: V) -> Rec<..{| .[L]: V, ..R |}>
    where R: !{| .[L] |}
    {
        Rec { data = {| .[L] = v, ..self.data |} }
    }

    fun get<L, V, record Rest>(&self, l: .[L]) -> &V where R = {| .[L]: V, ..Rest |} { &self.data.[L] }
}

let m := Rec::empty().put(.host, "a.com").put(.port, 8080);   // Rec<..{| host: String, port: i64 |}>
```

Every `put` changes the type, so this is a persistent, statically keyed map, not a runtime dictionary.

---

## Alternatives Considered

### Labels

- **String literals**, `get::<"id", …>` (RFC-0175's notation): a label would look like a runtime
  string. The spelling would also not match field access `r.id`.
- **`#field`**: see `#{ … }` above; also a new sigil for the same idea.
- **Phantom types as labels** (RFC-0175's own alternative): puts labels in the type namespace.

---

## Interactions

- **RFC-0175 (Label Polymorphism):** this RFC supplies spellings for its questions 1 to 4 (binder,
  literal form, selection, use in construction). RFC-0175 keeps the semantics and is amended, not
  superseded.
- **RFC-0151 (Tuples as numeric-label rows):** `.0`, `.1` give its rows a legible spelling.
- **RFC-0174 (compile-time iteration over a row's fields):** a label value can be written `.name`.
- **RFC-0186 (Rows as an operator on record parameters):** supplies the row spelling in the examples
  (`record R`, `..R`). A label binder needs no keyword: `.[L]` marks a label at its uses.
- **RFC-0187 (Anonymous record delimiters):** supplies the `{| … |}` spelling in the examples.
- **RFC-0121 (Open Rows):** a bare identifier in projection braces is "always a field label, never a
  row variable"; a label variable `.[L]` carries its own marker for the same reason a row variable
  carries `..`.
- **RFC-0099 (dot-separated paths) and RFC-0100 (keyword-argument construction):** a leading `.name`
  or `.[L]` never starts a path or a call argument, so neither is affected.

---

## Migration

Labels are new syntax. No existing program uses `.name` or `.[L]` in these positions, so there is
nothing to migrate. It is a language-visible addition and so a minor version when it ships.

---

## Changes on Acceptance

- `grammar.pest` and the generated `grammar.md`: label literals and `.[ ]`.
- Spec: expressions (selection by label) and types (label literals).
- RFC-0175 amended.
- Fixtures for each label position, and `.[L]` once RFC-0175 is integrated.

---

## Open Questions

1. **Dot in field position:** should a field entry also accept `.x` as an equivalent spelling of
   `x`? Recommended no: one way to write a field.
2. **Label lists:** projections `Handle.{ fd }` and negative bounds `!{| token |}` list label names
   without values. Should they use `.fd`, or stay plain? Recommended plain, since `.{` and `!`
   already mark them.
3. **`.[expr]`:** is a computed label beyond a variable needed now, or only when RFC-0174 asks for it?
4. **A label-typed parameter** (`l: .[L]`, a label literal being its own singleton type) so a call
   can write `m.put(.host, v)`. Alternatives are the turbofish only, or a parameter pattern
   `fun put<L, V>(self, .[L], v: V)`. This interacts with RFC-0170's literal types.

---

## Acceptance Criteria for the Prototype

Before this leaves draft:

- `.name` and `.[L]` parse in every position listed above, and a label never starts a path or a
  call argument.
- `.[L]` resolves once RFC-0175 is integrated.

---

## References

- RFC-0175 — Label Polymorphism (questions 1 to 4); RFC-0151 — Tuples as Numeric-Label Rows;
  RFC-0174 — Compile-time iteration over a row's fields; RFC-0091 — Linear Records.
- RFC-0186 — Rows as an operator on record parameters; RFC-0187 — Anonymous record delimiters.
- RFC-0121 — Open Rows (the projection-brace rule); RFC-0170 — Literal types and discriminated
  structural unions.
- RFC-0099 — Dot-separated module paths; RFC-0100 — Constructor-call construction.

---

## Decision

**Outcome:** *(pending)*
