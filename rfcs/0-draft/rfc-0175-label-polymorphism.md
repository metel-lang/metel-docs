---
id: rfc-0175
title: "Label Polymorphism"
date: '2026-10-06'
status: draft
---

## Summary

Generic record operations parameterized by a compile-time field label. A label-polymorphic
function can be written once and instantiated for `token`, `alloc`, or any other field,
while preserving the field's type and the row left after the operation.

This RFC is a design draft. It does not add label polymorphism to the language or change
RFC-0121's current meaning of row variables.

---

## Motivation

RFC-0121 makes the *remainder* of a record generic:

```metel
fun take_token<row R, row Rest>(s: Session<..R>) -> Session<..Rest>
where R = { token: Token, ..Rest } { ... }
```

The label in that equation is fixed. Code that should do the same thing for an arbitrary
field must currently be duplicated:

```metel
fun drain_token(s: &var { token: Token, ..R }) -> ... { ... }
fun drain_alloc(s: &var { alloc: Buffer, ..R }) -> ... { ... }
```

The missing capability is different from ordinary row polymorphism: the unknown is not only
the tail `R`, but also the field name. This matters for generic record utilities,
serialization helpers, lenses, and the `drain_field` example that motivated RFC-0091.

The feature must remain compile-time. It must not turn a record into a runtime map or permit
access to a field whose existence or type has not been proved by the signature.

---

## Proposal

### 1. A label kind

Introduce a distinct `label` generic parameter kind, parallel to RFC-0121's `row` kind:

```metel
fun get_field<label L, row R, T>(value: { L: T, ..R }) -> T { ... }
```

`L` ranges over field labels, not types, values, or strings. A label parameter is therefore
not written as `L: Symbol`; that spelling would be an ordinary type parameter with a bound.

The exact keyword (`label`, `name`, or another spelling) is intentionally open in this draft.

### 2. Label literals and field selection

An instantiation needs a compile-time label literal:

```metel
let token = get_field::<"token", _, Token>(session);
```

The body needs a checked, compile-time field selection form. One candidate is the notation
used by RFC-0091's motivating example:

```metel
value.[L]
```

This is not the existing runtime index operator. `L` must be a label parameter or a label
literal, and the type checker resolves it against the statically known row. A missing label
or a field whose type does not unify with `T` is a type error.

### 3. Row decomposition with a variable label

The label variable participates in the same row equation machinery as a fixed label:

```metel
fun drain_field<label L, row R, T>(
    s: &var { L: T, ..R }
) -> (T, &var { ..R }) {
    let value = s.[L];
    (value, s)
}
```

The final surface and ownership rules require further design. In particular, the language
must specify whether the result row is represented directly as `R` or through a named
decomposition, and how a mutable borrow is split when `T` is not `Copy`.

The simpler read-only operation is a useful minimum example:

```metel
fun project<label L, row R, T>(value: { L: T, ..R }) -> T {
    value.[L]
}
```

### 4. Label equality and constraints

The type checker needs a notion of label equality when two label parameters meet. At a
minimum:

- two identical label literals unify;
- two different label literals do not unify;
- a label parameter may unify with a literal at an instantiation;
- a row cannot contain two fields with labels that unify.

This draft does not propose arithmetic, ordering, concatenation, or runtime reflection over
labels. A label is an identifier-like compile-time atom.

### 5. Diagnostics and erasure

Label parameters are erased after type checking. They must not introduce runtime metadata or
dynamic field lookup. Diagnostics should identify the requested label when it is known:

```text
field `token` is not present in this row
```

For an unresolved label parameter, the diagnostic should identify the missing entailment
(`L` is not known to be present) rather than claiming that a literal field is absent.

---

## Worked Examples

### Generic projection

```metel
fun get<label L, row R, T>(r: { L: T, ..R }) -> T {
    r.[L]
}

let id: i64 = get::<"id", _, i64>(record);
```

### Generic field draining

```metel
fun drain<label L, row R, T>(r: &var { L: T, ..R })
    -> (T, &var { ..R })
{
    let field = r.[L];
    (field, r)
}
```

This should work for both `"alloc"` and `"token"` without defining two functions. Whether
this exact example is legal for a non-`Copy` `T` depends on the borrow/move design selected
with RFC-0091 and RFC-0122.

### Fixed-label APIs remain useful

Label polymorphism does not replace ordinary row equations. A protocol transition whose
meaning is specifically “remove `token`” should remain explicit:

```metel
where R = { token: Token, ..Rest }
```

The generic-label feature is for utilities whose operation is independent of the label's
spelling.

---

## Alternatives Considered

### Specialize every field

Writing `drain_token`, `drain_alloc`, and so on requires no new type-system machinery, but
does not scale and prevents reusable libraries from abstracting over record schemas.

### Runtime string keys

Treating a label as `String` or a runtime symbol loses static field existence and type checks,
requires dynamic lookup, and turns a record into a map-like value. It is outside this RFC.

### Keep labels fixed and use `comptime for`

RFC-0174 can iterate over the known fields of a row, but it does not by itself let a caller
select one arbitrary label and preserve its field type in a function signature. The two
features may compose; neither subsumes the other.

### Encode labels as ordinary types

Using phantom types such as `TokenLabel` avoids a new kind, but makes labels part of the type
namespace, complicates record syntax, and still needs a checked mapping from the phantom type
to a field name. A dedicated label kind states the intended distinction directly.

---

## Open Questions

1. What is the final syntax for label binders and label literals? The draft uses
   `<label L>` and `"field"` only as notation.
2. Should label literals be strings, identifier tokens, or a separate `#field`/`'field'`
   literal form?
3. Is `value.[L]` the right selection syntax, and how is it distinguished from runtime
   indexing?
4. Can a label parameter appear in record construction and row equations, or only in a
   field-selection/decomposition position?
5. What is the precise ownership rule for draining a non-`Copy` field through `&var`?
   This likely requires coordination with RFC-0091 and RFC-0122.
6. Should labels support aliases, module qualification, or only identifier labels?
7. Does label unification need a first-class constraint form, or is unification at row
   positions sufficient?
8. Does this RFC own generic label iteration, or should that remain entirely with RFC-0174?

---

## Dependencies and Scope

- **RFC-0121 (Open Rows):** supplies row variables, row extension, and decomposition.
- **RFC-0116/0120:** supply anonymous and named record shapes.
- **RFC-0091 (Linear Records):** supplies the motivating `drain_field` operation and its
  ownership questions; this RFC does not settle RFC-0091's broader linear-record design.
- **RFC-0122 (Borrow Checking):** likely required for a sound mutable-field-draining story.
- **RFC-0174 (Compile-time iteration):** related but separate; computed access over an
  iteration variable must not be assumed to imply label-polymorphic function parameters.

Out of scope: runtime reflection, arbitrary string-keyed records, label arithmetic, label
ordering, and a decision on whether labels have a user-visible runtime representation.

---

## Decision

**Outcome:** *(pending)*
