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

**A label as a compile-time value is written `.name`**, and a label variable `.[L]`. A field of a row
is a label, so it is written `.name` too (RFC-0221). This is the spelling that label polymorphism (RFC-0175),
tuples as numeric-label rows (RFC-0151) and compile-time field iteration (RFC-0174) are missing.

The semantics of label polymorphism (RFC-0175) and of rows (RFC-0121, RFC-0186) are not changed
here. This RFC is the syntax layer: it gives the spelling that RFC-0175's earlier draft left open, and RFC-0175 now
defines the `Label` type that the spelling denotes.

Examples write anonymous records as `{ … }` with dotted fields (RFC-0221) and row parameters as `record R` with `..R` (RFC-0186). The label spelling does not depend on either.

This is a design draft. Nothing here is accepted, and the grammar is unchanged until it is.

---

## Motivation

### Labels have no spelling of their own

A field name in a record is a bare identifier. That is unambiguous while labels are always fixed in
the source. Three proposals need a label to be a value or a variable:

- **RFC-0175 (Label Polymorphism, `0-draft`)** wants `fun get<label L, row R, T>(r: { L: T, ..R })`.
  Written like that, `L` in field position looks exactly like a field called `L`. That draft left
  the binder keyword, the literal form (strings, identifier tokens, `#field`) and the selection
  syntax (`value.[L]`) open. RFC-0175 now takes the binder from RFC-0132 (`comptime l: Label`) and the spelling
  from this RFC.
- **RFC-0151 (Tuples as numeric-label rows, `0-draft`)** would write `(a, b)` as `{ 0 = a, 1 = b }`,
  which today is not a record at all, since `0 = a` is not an identifier field.
- **RFC-0174 (compile-time iteration over a row's fields, `1-under-review`)** needs a way to name a
  label as a value.

Once a label has a spelling of its own, a row field written as a bare identifier is a second spelling of the
same thing. RFC-0221 removes it, so there is one way to write a label wherever it appears.

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
- **`.[L]`** is a label variable `L` (a `comptime` parameter of type `Label`, RFC-0175), and `.[expr]` is reserved for a
  compile-time label expression, to be defined by RFC-0174 if it needs one.

They are used wherever a label appears as a value, an argument or a variable, and (as `.name`) as the label of a row field, which is RFC-0221's:

```metel
// a label as an argument
let id := get(.id, record);

// a label variable in a type, a literal and a selection
fun get<T, record R>(comptime l: Label, r: { .[l]: T, ..R }) -> T { r.[l] }
fun single<V>(comptime l: Label, v: V) -> { .[l]: V } { { .[l] = v } }
let one := single(.id, 5);
```

The existing selection `r.x` is unchanged, and `r.[L]` is the computed form, the notation RFC-0175
and RFC-0091 already use. Selection is a value followed by a label: `r.x` is `r` and the label `.x`, and
`r.[L]` is `r` and the label variable `.[L]`. The dot marks "a label" and the brackets mark "computed at
compile time".

**Numeric labels** (RFC-0151) are `.0`, `.1`, matching the existing `t.0` access:

```metel
// (a, b) is notation for the row below
{ .0 = a, .1 = b }
```

**A field of a row is a label.** In an anonymous record literal, pattern, type, row bound, negative bound,
row equation and projection list the field is written `.x`: `{ .x = 1 }`, `Handle.{ .fd, ..R }`.
RFC-0221 owns that rule and its sites. Struct and enum construction, declarations and patterns keep bare
names (RFC-0100).

**This RFC does not define the `Label` type.** What `.[L]` ranges over (a comptime value of the built-in
`Label` type), label equality, and the meaning of `r.[L]` for a non-`Copy` field are RFC-0175's. The binder is
a `comptime` parameter (RFC-0132 §3.6), so there is no label kind. This RFC settles only how a label is written.

### A worked example: a record map

A map keyed at compile time. The label is passed as a `comptime l: Label` parameter (RFC-0132 §3.6, RFC-0175),
so `m.put(.host, "a.com")` infers it from the argument. This example depends on RFC-0175 being integrated, and is
illustrative.

```metel
record Rec<record R> { data: { ..R } }

extend<record R> Rec<..R> {
    fun empty() -> Rec<..{}> { Rec(data = {}) }

    fun put<V>(self, comptime l: Label, v: V) -> Rec<..{ .[l]: V, ..R }>
    where R: !{ .[l] }
    {
        Rec(data = { .[l] = v, ..self.data })
    }

    fun get<V, record Rest>(&self, comptime l: Label) -> &V where R = { .[l]: V, ..Rest } { &self.data.[l] }
}

let m := Rec::empty().put(.host, "a.com").put(.port, 8080);   // Rec<..{ .host: String, .port: i64 }>
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

- **RFC-0175 (Label Polymorphism):** defines the `Label` type, label equality and what a label parameter may do in
  a row. This RFC supplies the spelling it uses.
- **RFC-0132 (§3.6):** supplies the binder, `comptime l: Label`, in the generic list or as a function parameter.
- **RFC-0151 (Tuples as numeric-label rows):** `.0`, `.1` give its rows a legible spelling.
- **RFC-0174 (compile-time iteration over a row's fields):** a label value can be written `.name`.
- **RFC-0186 (Rows as an operator on record parameters):** supplies the row spelling in the examples
  (`record R`, `..R`). A label binder needs no keyword: `.[L]` marks a label at its uses.

- **RFC-0221 (Dotted Row Labels):** makes a row field a label, `.x`, and answers this RFC's former open
  questions 1 and 2 (a dotted field is required, and label lists in projections and negative bounds are dotted).
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

- `grammar.pest` and the generated `grammar.md`: label literals and `.[ ]`. Row-field positions take a label
  under RFC-0221.
- Spec: expressions (selection by label) and types (label literals).
- RFC-0175 amended.
- Fixtures for each label position, and `.[L]` once RFC-0175 is integrated.

---

## Open Questions

1. **`.[expr]`:** is a computed label beyond a variable needed now, or only when RFC-0174 asks for it?

---

## Acceptance Criteria for the Prototype

Before this leaves draft:

- `.name` and `.[L]` parse in every position listed above, and a label never starts a path or a
  call argument.
- `.[L]` resolves once RFC-0175 is integrated.

---

## References

- RFC-0175 — Label Polymorphism; RFC-0132 §3.6 — label parameters; RFC-0151 — Tuples as Numeric-Label Rows;
  RFC-0174 — Compile-time iteration over a row's fields; RFC-0091 — Linear Records.
- RFC-0186 — Rows as an operator on record parameters.
- RFC-0121 — Open Rows (the projection-brace rule); RFC-0170 — Literal types and discriminated
  structural unions.
- RFC-0099 — Dot-separated module paths; RFC-0100 — Constructor-call construction.

---

## Decision

**Outcome:** *(pending)*
