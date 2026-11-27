---
id: rfc-0229
title: "Single-Field Projection Shorthand"
date: '2026-11-14'
status: draft
---

## Summary

Write the projection of one field, `Type.{ .field }`, as `Type.field`, in type position and where a type is named in an
expression.

```metel
fun describe(h: Handle.fd) -> i64 { h.fd }        // Handle.{ .fd }, RFC-0137
let r: Handle.fd := handle.{ .fd };               // the value projection keeps its brace form (section 2)
Handle.fd::describe(handle.{ .fd })               // Handle.{ .fd }::describe(..)
```

The shorthand has exactly one field. A projection of several fields keeps its braces: `Handle.{ .fd, .name }`. The shorthand
adds no meaning of its own: `Type.field` is read as `Type.{ .field }` and everything RFC-0137, RFC-0116 and RFC-0211 say about
the residual applies unchanged.

Section 2 records a collision that limits the expression-position half of the request: on a **value**, `v.field` already
means field access and cannot become a projection. This draft states the part of expression position that is free, and asks
whether the rest is wanted.

This is a design draft. Nothing here is accepted.

---

## Motivation

A residual with one field is the common case of the projection cluster. A function that needs only a handle's descriptor, a
`Drop` receiver that names the one field its destructor reads (RFC-0147, `fun drop(&var self: Self.{ .fd })`), a parameter that
takes a token without its payload:

```metel
fun describe(h: Self.{ .fd }) -> i64 { h.fd }
fun peek(t: Ticket) -> Ticket.{ .secret }
```

Each writes a brace, a dot and a space around a single name. The braces exist so the form can list several fields; for one
field they carry no information. Dotted labels (RFC-0221) already made the label form `.name`; `Type.name` is the same name
with the brace and the second dot dropped.

The brace form stays the general one. The shorthand is for the case where it is noise.

---

## Proposal

### 1. Type position

In a type, `Type.name` where `Type` resolves to a nominal type or to `Self` and `name` is a label of its row is the type
`Type.{ .name }`:

| Written | Means |
|---|---|
| `Handle.fd` | `Handle.{ .fd }` |
| `Self.fd` | `Self.{ .fd }` |
| `Outer.inner` | `Outer.{ .inner }` |
| `Handle.fd: i64` as a parameter's type | `Handle.{ .fd }` with `fd: i64` known from the declaration |

The result is the residual type of the same brand (RFC-0137), with the same subtyping, `Copy`/`Clone` rules (RFC-0211) and
`Drop` dispatch (RFC-0147). It is not a new type and has no new name in diagnostics: a diagnostic that prints the type prints
the brace form, as it does today, or the shorthand if the source used it; the choice is stated in section 5.

`Type.name` is not ambiguous with the other dotted forms in type position, because none exists: associated types and modules
use `::` (`T::Item`, `lib::Type`), and a dotted type reaches the brace form only. A name that is not a label of the row is an
error that names the labels, as `Type.{ .name }` is today.

### 2. Expression position

A dotted name in an expression has a **receiver**, and the receiver is either a value or a type.

**A value receiver.** `v.field` is field access and yields the field's value:

```metel
let h := Handle { fd = 1, name = ".." };
take(h.fd)                  // h.fd is i64; today: cannot unify i64 with Handle.{ fd: i64 }
take(h.{ .fd })             // the projection: Handle.{ .fd }
```

The two differ in kind (a field value versus a one-field residual), and the first is how every program reads a field. **This
RFC does not change `v.field`**, so `v.{ .field }` has no shorthand. Any form that made `v.field` a projection would redefine
the most common expression in the language.

**A type receiver.** Where the receiver names a type and no value of that name is in scope, a dotted name is today an error
(`undefined name \`Handle\``). The shorthand gives it a meaning: `Type.name` is `Type.{ .name }`, used as a path prefix and as a
type argument:

```metel
Handle.fd::describe(h.{ .fd })              // Handle.{ .fd }::describe(..)
let parts: Vec<Handle.fd> := Vec::new();    // a turbofish or ascription is type position (section 1)
```

So expression position gains the shorthand only where a *type* is being named. The way a value is projected stays the brace
form.

**Resolution.** `A.b` is field access when `A` resolves to a value in scope, and the projection shorthand when `A` resolves to
a type and to no value. A name that is both is field access (the value wins), which keeps every program that compiles today
meaning what it means. The reverse hazard, a local `Handle` that shadows the type and silently turns a shorthand into field
access, is open question 1.

### 3. What does not change

- `v.{ .field }`, `v.{ .a, .b }`, `Type.{ .a, .b }` (RFC-0116, RFC-0137, RFC-0221): unchanged and still the general forms.
- Field access `v.field`, and `v.a.b` as two field accesses.
- A chained projection `Type.a.b` is **not** `Type.{ .a }.{ .b }`: chained projection is rejected today (RFC-0116 open
  question 2), and a dotted chain after a type is an error rather than a nested residual. The nested form is RFC-0150's
  `Outer.{ inner: Inner.{ .b } }`.
- Struct-literal and record-literal syntax. `Handle { fd = 1 }` and `.{ .fd = 1 }` are untouched.

### 4. Grammar

One production in the type grammar and one in the path grammar:

```
projected_type   = type_path "." label                // new: the shorthand
                 | type_path "." "{" label_list "}"   // existing
```

with `label` an identifier. A type path followed by `.` and an identifier parses as a projection; the existing production
requires `{` after the dot, so the two never compete. In expression position the parser cannot decide between field access and
shorthand, since both are `ident "." ident`; the choice is made after name resolution (section 2), as the choice between a
path and a field access already is for `A.b` where `A` is a module alias.

### 5. Printing

A diagnostic that shows a one-field residual shows the brace form: it is the general form, it is what a multi-field residual
prints, and one rendering per type keeps messages searchable. The shorthand is a spelling in the source, not a second name
for the type.

---

## Interaction with other work

- **RFC-0137** (branded rows): defines the residual `Handle.{ .fd }` this form names. No change to it.
- **RFC-0116 / RFC-0221 / RFC-0225**: the brace form, dotted labels and the `.{` introducer. The shorthand drops the brace and
  the second dot, so a reader must know `Handle.fd` is the type's projection, not a path into `Handle`. RFC-0225's rule that a
  whole-row form keeps its own contiguous introducer is not affected.
- **RFC-0147** (projection-receiver destructors) and **RFC-0211** (aspects on residuals): `fun drop(&var self: Self.fd)` would
  be the shorthand of the form RFC-0147 writes.
- **RFC-0150** (nested row narrowing): `Outer.inner.b` is the natural spelling of a nested residual and is excluded here
  (section 3) so this RFC does not decide it.
- **metel-core#2021** (negative label entry `!label`): if row-bound entries stop carrying the dot, whether projections follow is
  one decision, not two. The shorthand is written to survive either answer, since it names a label after the dot and `.fd` is
  the label's dotted spelling today.

---

## Alternatives considered

1. **Shorthand on values too (`v.field` as `v.{ .field }`).** Rejected: it redefines field access. The probe in section 2 shows
   `take(h.fd)` is a type error for a `Handle.{ .fd }` parameter precisely because `h.fd` is the field's value.
2. **A different token for the shorthand (`Type::field`, `Type#field`).** `::` is the namespace separator (modules, associated
   types, static members) and would collide with `Handle::describe`; a new sigil costs more than it saves.
3. **Shorthand only in type position.** The smallest version, and the one with no resolution rule. It leaves a type named in an
   expression (`Handle.fd::describe`) to spell the brace form. Section 2's type-receiver case is the question of whether that
   is worth the resolution rule.
4. **Do nothing.** The brace form works everywhere; the cost is three characters of noise per one-field projection.

---

## Open questions

1. **Shadowing.** `A.b` is field access when a value `A` is in scope, so a local that shadows a type turns a shorthand into
   field access without an error. The same hazard exists for `A.b` with a module alias today. Is "the value wins, and the
   shorthand is written with the type in scope" enough, or should the shorthand require that no value shadows the type, as
   an error at the use?
2. **Is the type-receiver half of expression position wanted?** If not, the RFC shrinks to section 1, and `Handle.fd::describe`
   stays `Handle.{ .fd }::describe`.
3. **Printing.** Section 5 prints the brace form. Should a diagnostic echo the shorthand when the source used it?
4. **Declaration of a field-qualified type argument.** `Vec<Handle.fd>` reads as a path into `Handle`; does that confuse a
   reader who expects a nested type? The brace form never could be read that way.
5. **Chained shorthand.** Section 3 excludes `Type.a.b`. If RFC-0150 lands, does it take this spelling?
6. **Spelling of a typed entry.** The brace form can state a field's type (`Handle.{ .fd: i64 }`); a shorthand has nowhere to
   write it. The proposal leaves the typed form to the braces.

---

## Implementation notes

- Grammar and parser: the type production above and the expression-position resolution (`grammar.pest`, the type-expression
  parser, name resolution for a dotted path whose head is a type).
- Spec: the record-types projection rule in the types chapter gains the shorthand and the type-receiver rule; the ownership
  chapter's residual examples can use it.
- Fixtures: each position, the multi-field case staying braced, an unknown label, a shadowing local, and `v.field` unchanged.
- No runtime change: the shorthand is expanded in parsing and name resolution to the existing residual type.

---

## Decision

**Outcome:** *(pending)*
