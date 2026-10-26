---
id: rfc-0188
title: "Label syntax and rows as record types"
date: '2026-10-26'
status: draft
---

## Summary

Two surface changes to how labels and rows are written, split out of RFC-0187 (which keeps only the
record delimiters):

1. **A label as a compile-time value is written `.name`**, and a label variable `.[L]`. Ordinary
   fields keep their plain identifier. This is the spelling that label polymorphism (RFC-0175),
   tuples as numeric-label rows (RFC-0151) and compile-time field iteration (RFC-0174) are missing.
2. **Rows are record types, and `..` is the operator that takes a record type's row.** There is no
   `row` kind and no `row` keyword: `<row R>` becomes `<R>`, a row argument is just a record type
   (`Session<R>`, not `Session<..R>`), and the remainder bound by a rest pattern is an ordinary
   record value. A label binder needs no keyword either: `.[L]` marks a label at its uses.

The semantics of rows (RFC-0121), of records (RFC-0116, RFC-0120) and of label polymorphism
(RFC-0175) are not changed here. This RFC is the syntax layer, and it answers RFC-0175's open
questions 1 to 4 on spelling.

**Dependency.** The examples below write records as `{| … |}`, which RFC-0187 proposes. The two
changes are independent in meaning: if RFC-0187 is declined, every `{| … |}` here reads `{ … }` and
nothing else in this RFC changes.

This is a design draft. Nothing here is accepted, and the grammar is unchanged until it is.

---

## Motivation

### 2. Labels have no spelling of their own

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

### 3. A `row` kind duplicates the record type

Metel already has the pieces to say that a row is the row component of a record type. RFC-0120 and
RFC-0137 represent a record or struct type as a (brand, row) pair, and `..` already means "the fields of" in three places: a
value spread `{ ..r, x = 1 }`, a rest pattern `{ token, ..rest }`, and an open tail `{ x: f64, ..R }`.
Yet a row parameter is declared with its own kind keyword, `<row R>`, is passed with its own argument
form, `Session<..R>` and `Session<..{ host: String }>` (RFC-0180), and a value of a row has to be
wrapped back into a record type, `{ ..R }`, before it can be stored.

The binder keyword is also the only place a row parameter must say what it is: every use already
carries `..R`, and RFC-0121 §1 fixes that a bare identifier in type position is always a type. RFC-0121
kept the keyword because a declaration naming its own kind is ordinary, and because `<..R>` would
read as splicing into a parameter list. Feedback on the published syntax asked for the keyword to go,
and suggested the stronger form: drop the kind and treat `..` as an operator on a record type that
returns its row. Adding a `label` kind keyword (RFC-0175) would repeat the redundancy.

---

## Proposal

### 1. Labels: `.name` and `.[L]`

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
everything twice. Whether `.x` should also be accepted in field position is open question 2.

**This RFC does not define the label kind.** What `.[L]` ranges over, label equality, ownership of
a drained field and the meaning of `r.[L]` for a non-`Copy` field are RFC-0175's, and its open
questions 5 to 8 stay open. This RFC settles only how a label is written.

### 2. Rows are record types; `..` takes a record type's row

There is no `row` kind. A generic parameter that stands for a record shape is an ordinary type
parameter that happens to be a record type, and `..X` denotes the **row of the record type `X`**:

- in a record type, `{| x: f64, ..R |}` is the field `x` plus the row of `R`;
- in a literal, `{| ..r, x = 1 |}` is the fields of the value `r` plus `x` (the existing spread);
- in a pattern, `{| token, ..rest |}` binds `rest` to the remainder.

One operator, one meaning: *the fields of*. At the type level it takes a record type and returns its
row; at the value level it takes a record value and spreads its fields.

```metel
// today
record Request<row R> { data: { ..R } }
extend<row R: { host: String, .. }> Request<..R> where R: !{ token } {
    fun authenticate(self, t: String) -> Request<..{ token: String, ..R }> { … }
}

// proposed
record Request<R> { data: R }
extend<R: {| host: String, .. |}> Request<R> where R: !{| token |} {
    fun authenticate(self, t: String) -> Request<{| token: String, ..R |}> { … }
}
```

`R` is the whole record type here (it has `host`), a bound on a record type, and `data: R` stores it
directly. Where `R` is the *remainder* (`{| x: f64, ..R |}`), it is the record type of the leftover
fields. Both roles are the same kind of thing: a record type.

**Rules**

1. **`..X` needs a record type.** `X` is an anonymous record type (open or closed), a `record`-declared
   type, or a parameter that is one. A parameter that is the operand of `..`, has a row bound
   (`R: {| x: f64, .. |}`), or appears in a row equation is thereby a record type. No keyword says so.
   Instantiating it with a non-record type, such as `i64`, is an error naming the `..` that required
   one.
2. **Brands.** A record type is a (brand, row) pair (RFC-0120, RFC-0137), and `..` returns the row, so it drops
   the brand. A parameter may be instantiated with a branded `record` type; its brand is simply not
   part of what `..R` embeds. This is explicit at the one place it happens, the `..`.
3. **Structs are not record types.** `..S` for a struct `S` is an error, as "a plain struct never
   satisfies a row bound" is today. A struct's residual projection `Handle.{ fd, ..R }` is unchanged:
   `R` is the record type of the remaining fields.
4. **Arguments are types.** A generic argument for a record-type parameter is a record type:
   `Session<R>`, `Session<{| host: String, ..R |}>`. `Session<..R>` is an error with a hint to write
   `Session<R>`. RFC-0180's literal-row arguments (`..{ … }`) are therefore no longer a separate form.
5. **Bounds and equations are bounds on record types.** `R: {| host: String, .. |}` says `R` is a record
   type with at least `host`. `!{| token |}` says it has no `token`. `where R = {| token: T, ..Rest |}`
   says `R` is the record type with `token` plus the record type `Rest`.
6. **The remainder is a value type.** A rest pattern `{| token, ..rest |}` binds `rest` at the record
   type `Rest`, so a record can store it as `data: Rest` instead of `data: { ..Rest }`.
7. **Label parameters.** A parameter used as `.[L]` is a label. Its binder needs no keyword.

```metel
fun get_x<R>(p: {| x: f64, ..R |}) -> f64 { p.x }                 // was <row R>
fun twice<R>(p: {| x: f64, ..R |}) -> f64 where all R: Copy { … }  // unchanged by this RFC
```

**Kind inference.** With no row kind, a binder needs a kind only for record-type constraints and for
labels, and both follow from the uses (rule 1, rule 7). A bare use and a `..` use of the same
parameter are both legal, because both are uses of a record type; the previous draft's "conflicting
uses" error does not exist. The binder keywords `row` and `record T: …` are both dropped, since a
bound or a `..` already says what they said. Whether a bare `T` in a bound-less position that is
later used under `..` is accepted is open question 8.

**What this does not change.** Row polymorphism, row equations, narrowing, residual types and brands
keep their semantics; the front end's internal row machinery can stay as it is. `where all R: Copy`
is unchanged by this RFC. With `R` a record type, `R: Copy` could say the same thing for the record
as a whole, given the row-conditional impls of RFC-0123, but that simplification is a follow-up.

### 3. A worked example: a record map

With both parts together, a map keyed at compile time looks like this. The label-typed
parameter `l: .[L]` (a label literal is also its own singleton type) is not defined by this RFC and is
open question 9; the turbofish form `m.put::<.host>("a.com")` needs nothing beyond §2.

```metel
record Rec<R> { data: R }

extend<R> Rec<R> {
    fun empty() -> Rec<{| |}> { Rec { data = {| |} } }

    fun put<L, V>(self, l: .[L], v: V) -> Rec<{| .[L]: V, ..R |}>
    where R: !{| .[L] |}
    {
        Rec { data = {| .[L] = v, ..self.data |} }
    }

    fun get<L, V>(&self, l: .[L]) -> &V where R = {| .[L]: V, ..Rest |} { &self.data.[L] }
}

let m := Rec::empty().put(.host, "a.com").put(.port, 8080);   // Rec<{| host: String, port: i64 |}>
```

Every `put` changes the type, so this is a persistent, statically keyed map, not a runtime dictionary.

---

## Alternatives Considered

### Labels

- **String literals**, `get::<"id", …>` (RFC-0175's notation): a label would look like a runtime
  string. The spelling would also not match field access `r.id`.
- **`#field`**: see `#{ … }` above; also a new sigil for the same idea.
- **Phantom types as labels** (RFC-0175's own alternative): puts labels in the type namespace.

### Rows and binder kinds

- **Rows are record types, `..` takes the row (proposed).** One concept fewer, no keyword, row
  arguments become ordinary type arguments, and `..` has one meaning at every level.
- **Keep `row R` and add `label L`:** two more keywords, both repeating what the use sites say.
- **Infer a separate row kind from use (an earlier draft of this RFC):** removes the keyword but keeps
  the row kind, the `Name<..R>` argument form and RFC-0180's literal rows, and needs a rule for a
  parameter used both bare and under `..`.
- **Sigil at the binder, `<..R>`:** declined by RFC-0121 §1 because it reads as splicing.
- **Kind annotations as bounds, `<R: row>`:** a new syntax for the same redundancy.

---

## Interactions

- **RFC-0187 (Anonymous record delimiters):** supplies the `{| … |}` spelling used in the examples.
- **RFC-0121 (Open Rows):** the row kind and `<row R>` are replaced by §2 here. Row bounds,
  equations and `..R` tails are read as bounds on record types. §1's reasoning on the binder is
  superseded; the semantics of rows are unchanged.
- **RFC-0180 (Literal rows in row arguments):** its `..{ … }` argument form is no longer needed, since
  a row argument is a record type; the rest of that RFC's rules (kind check, tail recognition) apply
  to record-type arguments.
- **RFC-0178 (Row Remainder Construction):** the rest value now has the record type `Rest` directly.
- **RFC-0120 and RFC-0137 (Named records, branded rows):** a record type being a (brand, row) pair is
  what makes `..` well defined; `..` is the projection to the row.
- **RFC-0123 (Field-wise constraints):** `where all R: A` is unchanged here.
- **RFC-0175 (Label Polymorphism):** this RFC supplies spellings for its questions 1 to 4 (binder,
  literal form, selection, use in construction). RFC-0175 keeps the semantics and is amended, not
  superseded.
- **RFC-0151 (Tuples as numeric-label rows):** `.0`, `.1` give its rows a legible spelling.
- **RFC-0174 (compile-time iteration over a row's fields):** a label value can be written `.name`.
- **RFC-0099 (dot-separated paths) and RFC-0100 (keyword-argument construction):** a leading `.name`
  or `.[L]` never starts a path or a call argument, so neither is affected.

---

## Migration

This is a breaking, language-visible change and so at least a minor version when it ships, never a
patch. It is mechanical:

- Every `<row R>` binder loses its keyword, every `Name<..R>` argument becomes `Name<R>`, every
  `..{ … }` row-literal argument becomes a record type, and a `{ ..R }` field type becomes `R`.
- Labels are new syntax; no existing program uses `.name` or `.[L]` in these positions.
- A parse-based rewriter produces the new forms, so the migration is not a hand edit.
- Transition policy is open question 1.

---

## Changes on Acceptance

- `grammar.pest` and the generated `grammar.md`: `generic_param` without `row_kw` or `record_kw`;
  `row_arg` and `row_literal` removed; label literals and `.[ ]`; the `..` type operator.
- Spec: generics (rows as record types, the `..` operator and its rules), expressions (selection by
  label), and types (label literals).
- A new diagnostic for `..` on a non-record type or a struct, and one for `Name<..R>`;
  `reference/error-codes.md`.
- RFC-0121, RFC-0178 and RFC-0180 examples updated, RFC-0175 amended.
- Fixtures: the corpus migrated by the rewriter; new fixtures for `..` on each kind of type, brand
  erasure, and `.[L]` once RFC-0175 is integrated.

---

## Open Questions

1. **Transition:** one release where the old row forms still parse with a deprecation diagnostic, or
   a hard break with the rewriter? The project has no warning channel today, so a deprecation would
   be an error with a suggested rewrite.
2. **Dot in field position:** should a field entry also accept `.x` as an equivalent spelling of
   `x`? Recommended no: one way to write a field.
3. **Label lists:** projections `Handle.{ fd }` and negative bounds `!{| token |}` list label names
   without values. Should they use `.fd`, or stay plain? Recommended plain, since `.{` and `!`
   already mark them.
4. **`.[expr]`:** is a computed label beyond a variable needed now, or only when RFC-0174 asks for it?
5. **`..S` on a struct:** an error as proposed, or should a struct's row be extractable? Residual
   projections `Handle.{ fd }` are the nearest case.
6. **Record-ness inferred from `..`:** a parameter first used bare and later under `..` is a record
   type from that use; should a parameter with no such use but a record-shaped intent need a way to
   say so, or is the instantiation-time error enough?
7. **A label-typed parameter** (`l: .[L]`, a label literal being its own singleton type) so a call
   can write `m.put(.host, v)`. Alternatives are the turbofish only, or a parameter pattern
   `fun put<L, V>(self, .[L], v: V)`. This interacts with RFC-0170's literal types.
8. **Explicit instantiation:** `f::<{| y: i64 |}>(…)` now passes a record type for a remainder.
   Allowed, or only inferred?
9. **`R: Copy` for `where all R: Copy`:** fold the field-wise bound into an ordinary aspect bound on a
   record type, here or in a follow-up? Recommended follow-up.

---

## Acceptance Criteria for the Prototype

Before this leaves draft:

- Every existing row-kind signature typechecks under the record-type reading with the same results,
  including branded instantiations of a remainder parameter.
- `..` on a struct and on a non-record type is rejected with a targeted error.
- `.[L]` parses and resolves once RFC-0175 is integrated, and a label never starts a path or a call
  argument.

---

## References

- RFC-0187 — Anonymous record delimiters (`{| … |}`).
- RFC-0120 — Named Records; RFC-0117 — Row Narrowing.
- RFC-0121 — Open Rows (§1 binder kinds and the projection-brace rule); RFC-0137 — Branded rows;
  RFC-0123 — Field-wise constraints; RFC-0170 — Literal types and discriminated structural unions.
- RFC-0178 — Row Remainder Construction; RFC-0180 — Literal rows in row arguments.
- RFC-0175 — Label Polymorphism (questions 1 to 4); RFC-0151 — Tuples as Numeric-Label Rows;
  RFC-0174 — Compile-time iteration over a row's fields; RFC-0091 — Linear Records.
- RFC-0099 — Dot-separated module paths; RFC-0100 — Constructor-call construction.

---

## Decision

**Outcome:** *(pending)*
