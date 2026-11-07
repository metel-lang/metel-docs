---
id: rfc-0175
title: "Label Polymorphism"
date: '2026-10-06'
updated: '2026-11-07'
status: draft
---

## Summary

**A label is a compile-time value of a built-in type, `Label`.** A function or impl that is generic over a field
name takes a `comptime` parameter of type `Label` (RFC-0132 §3.6) and uses it in a row field, a row bound and a
selection. There is no label kind, and labels are not strings or types.

```metel
fun get<T, record R>(comptime l: Label, r: { .[l]: T, ..R }) -> T { r.[l] }

let id: i64 := get(.id, { .id = 7, .name = "ana" });
```

This RFC owns the semantics: the `Label` type, label equality, what a label parameter may do in a row, and what
the checker may and may not assume about it. Other RFCs own the pieces around it:

| piece | owner |
|---|---|
| the spelling `.name`, `.0`, `.[expr]` | RFC-0188 |
| a row field is a label, `.x` | RFC-0221 |
| the binder `comptime l: Label`, in the generic list or as a parameter | RFC-0132 §3, §3.6 |
| iterating a row's fields at compile time | RFC-0174 |
| draining a non-`Copy` field through `&var` | RFC-0122, RFC-0091 |

This is a design draft. It does not add label polymorphism to the language until accepted.

---

## Motivation

RFC-0121 makes the *remainder* of a record generic. The label in a row equation is fixed:

```metel
fun take_token<record R, record Rest>(s: Session<..R>) -> Session<..Rest>
where R = { .token: Token, ..Rest } { ... }
```

Code that should do the same thing for an arbitrary field has to be written once per field:

```metel
fun drain_token<record R>(s: &var { .token: Token, ..R }) -> ... { ... }
fun drain_alloc<record R>(s: &var { .alloc: Buffer, ..R }) -> ... { ... }
```

The unknown is not only the tail `R` but also the field name. That matters for generic record utilities, a
builder (RFC-0222), serialization, lenses, and the `drain_field` example that motivated RFC-0091.

The feature must stay compile-time. It must not turn a record into a runtime map, and it must not allow access
to a field whose existence or type the signature has not proved.

### Why a value, not a kind

A label kind (a type-level atom, parallel to `row`) would be enough for signatures such as `get`. It is not
enough for the rest of the label work:

- **RFC-0174 produces labels as values.** `comptime for field in fields(R)` binds `field.name`. With a kind, every
  use of `self.[field.name]` needs a conversion from a value to a kind-level atom.
- **A label argument.** `get(.id, record)` passes a label to a function. A kind can only be supplied as a type
  argument (`get::<.id, …>`).
- **Equality and branching.** `comptime if field.name == .password` needs a value that can be compared.
- **Spelling.** A label as a value of a type is one more instance of the comptime parameter RFC-0132 already
  specifies. A kind is a new parameter category with its own binder.

---

## Proposal

### 1. The `Label` type

`Label` is a built-in type with these properties:

- **Values.** `.name` for an identifier, `.0` for a decimal integer (RFC-0151), and `.[expr]` for any
  comptime-known `Label` expression (RFC-0188).
- **Equality.** Two labels are equal when they are the same kind (identifier or integer) and the same spelling.
  `==` and `!=` are available in comptime code, and unification at a row position uses the same relation.
- **A text form.** `l.to_string()` gives the label's spelling as a `String`, comptime only. `.name` gives `"name"`
  and `.0` gives `"0"`.
- **Nothing else.** No ordering, arithmetic, concatenation or construction from a string. A label is an atom.
- **Comptime only.** A `Label` has no run-time representation. It cannot be stored in a `let` or `var`, held in a
  field of a run-time value, passed as a run-time argument or returned from a run-time function. Any use that would
  need one is a compile error. Labels are erased after type checking; no metadata or dynamic field lookup remains.

The type of a label literal is `Label`. This RFC does not give a literal its own singleton type; nothing here
needs one, and RFC-0170's literal types need not extend to labels.

### 2. Label parameters

A label parameter is a `comptime` parameter of type `Label`, per RFC-0132 §3.6:

```metel
fun get<T, record R>(comptime l: Label, r: { .[l]: T, ..R }) -> T          // as a parameter
fun get<comptime l: Label, T, record R>(r: { .[l]: T, ..R }) -> T          // the same, in the generic list
extend<comptime l: Label, T> Wrapper<T> { … }                              // on an impl
```

At a call, the argument must be comptime-known (RFC-0132 §1.1): a label literal, a `comptime let`, a label
parameter in scope, or the name of a field in a `comptime for`. A label parameter is a unification variable, like
a type parameter, and is resolved per call.

### 3. Labels in rows

A label parameter or literal may stand in any row-field position:

| position | form |
|---|---|
| record type | `{ .[l]: T, ..R }` |
| record literal | `{ .[l] = v, ..r }` |

| row bound entry | `R: { .[l]: T, .. }` |
| negative bound entry (RFC-0189) | `R: !{.[l]}`, `{ !.[l]: T, .. }` |
| row equation | `R = { .[l]: T, ..Rest }` |
| selection | `r.[l]` |

The row rules are RFC-0121's, RFC-0123's and RFC-0189's, with a label variable in place of a literal. In
particular:

1. **Presence and absence are entailments** of the declared bounds and equations. `r.[l]` is accepted when the
   signature entails that the row has a field `l`, and has the type that field is bound to. It is rejected
   otherwise, with the diagnostic in §6.
2. **Duplicate labels.** A row cannot contain two fields whose labels are equal. A bound `R: !{.[l]}` is how a
   signature states that `l` is absent from a row. How a signature states that two label parameters differ is
   §10.
3. **Unification.** Two label parameters unify when they are the same label. Two different literals do not unify.
   A parameter unifies with a literal at an instantiation.

### 4. Selection and ownership

`r.[l]` means exactly what `r.x` means after `l` is replaced by `x`. It adds no ownership rule:

- on a `Copy` field it copies;
- on a non-`Copy` field of an owned value it is a partial move, leaving the residual that RFC-0117 describes;
- through `&` it reads, and through `&var` it follows the field type's rules.

Moving a field out through `&var` and handing back the rest (`drain_field`) is not settled by this RFC. It
depends on RFC-0091 and RFC-0122 and is expressed here only as `r.[l]` for whatever those RFCs allow.

### 5. Checking a body once

A function body with a label parameter is checked once, against a symbolic label (RFC-0132 §3.3, RFC-0174 D3),
not once per instantiation. The checker assumes nothing about the label's spelling. It can use only the bounds in
the signature: `r.[l]` needs a bound that entails the field. A comptime condition on a label, such as
`l == .password`, has no known value at the definition. Both of its arms are checked at the definition under
the declared bounds, with no assumption that the condition holds or fails inside an arm, and each instantiation
keeps the arm the condition selects (RFC-0132 §5, as amended). An arm therefore cannot rely on a fact the
condition would imply: in the `password` arm, `l` is still an unknown label.

### 6. Diagnostics

For a literal label that is absent, the diagnostic names it:

```text
field `token` is not present in this row
```

For a label parameter the diagnostic names the missing entailment and not a missing field:

```text
`l` is not known to be a field of this row; add the bound `R: { .[l]: T, .. }`
```

A `Label` used where a run-time value is needed reports that a label is compile-time only, and where it was
used.

### 7. Iteration

RFC-0174's `field.name` is a `Label`, not a string. `self.[field.name]` is selection by a label, the form in §3.
Where text is needed it is `field.name.to_string()`:

```metel
comptime for field in fields(R) {
    out := out + field.name.to_string() + " = " + self.[field.name].to_string() + ", ";
}
```

RFC-0174 and RFC-0216, which currently call the name a "compile-time string", are amended separately.

### 8. Tuples

A numeric label `.0` is a `Label`. `t.0` is selection by `.0`, and a tuple is a numeric-label row (RFC-0151).
`fun nth<T, record R>(comptime n: Label, t: { .[n]: T, ..R }) -> T { t.[n] }` is generic over the position.

### 9. Visibility

A generic body reaches a field only through a bound in its signature (RFC-0173 D2, D6). Field privacy is
therefore enforced where such a bound is discharged, which is at a call:

1. **Discharge checks visibility.** When a call discharges a row bound that names a field, whether by a
   literal label or by a label parameter instantiated to one, that field must be visible from the module
   containing the call. Every field of an anonymous record or a `record` is public (RFC-0120). A field of a
   nominal type has the visibility it was declared with (RFC-0032).
2. **A grant entitles the template, not its callers.** `derives A` makes a type's row visible to `A`'s row
   template (RFC-0209), so the template may read and build every field of the row it was granted, and calls
   made inside the template are entitled to it. Code that calls the template's methods with a label, such as
   `set(.secret, v)` on a builder (RFC-0222), is a caller: rule 1 applies to that call, and naming a private
   field is an error.
3. **No provenance.** A `Label` is a plain atom and carries no module. A wrapper that forwards a label to
   another generic function states the bound in its own signature (RFC-0173), so the check happens at the
   wrapper's call.

This adds no rule to RFC-0032. It states where that rule is applied when a field is named by a label.

### 10. Distinct labels

A row cannot contain two fields with equal labels (§3). When a signature puts two labels into one row as
sibling fields and they are not both literals, that is two label parameters or a parameter and a literal, the
signature must state that they differ:

```metel
fun both<A, B, record R>(comptime a: Label, comptime b: Label, r: { .[a]: A, .[b]: B, ..R }) -> (A, B)
where a != b {
    (r.[a], r.[b])
}
```

1. **A new fact in the bounds.** `where a != b` is a label inequality between two label parameters, or between
   a parameter and a literal (`where l != .id`). Two different literals are known to differ, and two equal
   ones are an error.
2. **Required.** A signature that puts two such labels in one row without the clause is a definition error:
   "labels `a` and `b` may be equal; add `where a != b`".
3. **Decided at the call.** Both labels are comptime-known there (RFC-0132 §1.1), so the clause is checked
   at each call, and equal labels are an error that names both.
4. **Entailment.** The clause is a member of the bounds. The well-formedness of the row uses it, and it is
   forwarded to a callee's `where x != y` for the same pair. There is no transitivity and no search
   (RFC-0173 D6); RFC-0173 D6 gains this entry on acceptance.
5. **Not needed for a row tail.** `R: !{.[l]}` already states that `l` is absent from `R`.

---

## Worked Examples

### Projection and insertion

```metel
fun get<T, record R>(comptime l: Label, r: { .[l]: T, ..R }) -> T { r.[l] }

fun insert<V, record R>(comptime l: Label, r: { ..R }, v: V) -> { .[l]: V, ..R }
where R: !{.[l]} {
    { .[l] = v, ..r }
}

fun main() {
    let cfg := insert(.port, insert(.host, {}, "a.com"), 8080);   // { .host: String, .port: i64 }
    assert(get(.port, cfg) == 8080);
}
```

`insert` has the shape of the `tagged` function in the row-parameter fixtures, with the fixed `tag` replaced by `l`.

### Branching on a label

```metel
extend<record R> { ..R }: Json where ..R: Json {
    fun to_json(&self) -> String {
        var parts: [String] := [];
        comptime for field in fields(R) {
            comptime if field.name == .password {
                // no code is emitted for this field
            } else {
                parts.push(field.name.to_string() + ":" + self.[field.name].to_json());
            }
        }
        "{" + parts.join(",") + "}"
    }
}
```

### What is rejected

```metel
get(.missing, user);                   // field `missing` is not present in this row
get(.name, user) + 1;                  // `name` is String, not i64
insert(.host, cfg, "b.com");           // R already has `host`, violating `R: !{.host}`
fun bad(comptime l: Label) { let x := l; }   // a Label is compile-time only
fun f<T, record R>(comptime l: Label, r: { ..R }) -> T { r.[l] }   // `l` is not known to be a field of R
both(.id, .id, rec);                   // `a` and `b` must differ; both are `.id`
```

---

## Alternatives Considered

### A label kind

A type-level atom with its own binder, parallel to `row`. Enough for signatures, but it needs a conversion from
RFC-0174's `field.name`, cannot be passed as an argument, cannot be compared in comptime code, and adds a parameter
category (see Motivation). Rejected.

### Labels as compile-time strings

The wording RFC-0174 and RFC-0216 use today. A string has operations a label must not have: concatenation and
slicing would make type identity depend on string computation, and nothing would stop a field named `"a b"` or an
empty name, or a numeric label `"0"` being confused with an identifier. A distinct `Label` type keeps unification to
atom equality. Rejected; `to_string()` gives the text where it is wanted.

### Specialise every field

`drain_token`, `drain_alloc`, and so on. No new machinery, but it does not scale and prevents reusable libraries
from abstracting over record schemas.

### Runtime string keys

Loses static field existence and type checks, requires dynamic lookup, and turns a record into a map-like value.
Outside this RFC.

### Keep labels fixed and use `comptime for`

RFC-0174 can iterate over the known fields of a row but cannot let a caller select one arbitrary label and keep
its field type in a signature. The two compose; neither subsumes the other.

### Encode labels as ordinary types

A phantom `TokenLabel` type avoids a new type but puts labels in the type namespace, complicates record syntax, and
still needs a checked mapping from the type to a field name.

---

## Interactions

- **RFC-0132 §3, §3.6:** supplies the binder, the function-parameter position, the admissible arguments, and
  definition-site checking. A label parameter is the same kind of generic parameter as `comptime N: u64`.
- **RFC-0188 (Label syntax):** the spelling of `.name`, `.0` and `.[expr]`. This RFC defines the `Label` type it
  refers to.
- **RFC-0221 (Dotted Row Labels):** a row field is a label, so a fixed label and a label variable share one slot.
- **RFC-0174 (Compile-time iteration):** `field.name` is a `Label` (§7). Its row syntax (`row R`, `where all R`)
  is also stale against RFC-0186 and is amended with it.
- **RFC-0216 (Constructing rows and residuals):** its computed-label literal `{ [field.name] = expr }` is
  `{ .[field.name] = expr }`.
- **RFC-0189 (Per-label negative bounds):** `!.x` generalises to `!.[l]`. The entailment table is the same.
- **RFC-0151 (Tuples as numeric-label rows):** numeric labels are `Label` values (§8).
- **RFC-0091 / RFC-0122:** own the ownership of draining a field (§4).
- **RFC-0222 (Builder aspect):** the first consumer. Its `set` takes `comptime l: Label`.
- **RFC-0121, RFC-0090 (superseded):** both said "no label kind is required". That stays true: this RFC adds a
  value type and no kind.

---

## What this does not include

- Runtime reflection, string-keyed records, label arithmetic or ordering.
- Aliases or module-qualified labels. A label is an atom spelled by its name.
- Labels that name enum variants (RFC-0210).
- A label's own singleton type, and any change to RFC-0170.
- The ownership rule for draining a non-`Copy` field through `&var` (§4).

---

## Changes on Acceptance

- Spec: types (`Label`), expressions (selection by label), generics (label parameters), row bounds.
- RFC-0132 §3.6 reaches `2-accepted` first or together with this RFC.
- RFC-0188, RFC-0174 and RFC-0216 amended as listed under Interactions.
- RFC-0132 §5 gains the rule for a condition that depends on a parameter (§5 here).
- RFC-0173 D6 gains the label-inequality entry (§10).
- Error codes for an unentailed `r.[l]`, a duplicate label, equal labels at a `where a != b`, a private field
  named through a grant, and a run-time use of a `Label`; a fixture each.

---

## Open Questions

None blocking.

---

## Acceptance Criteria for the Prototype

Before this leaves draft:

- `get`, `insert` and a numeric `nth` type-check as written, and each rejected case above gives its stated
  diagnostic.
- A body with a label parameter is checked once with `l` symbolic, and instantiation substitutes a literal.
- The `comptime if` on `l == .password` in the `Json` example is accepted, and a type error in the `password`
  arm is reported at the definition, not at the first instantiation that selects it (§5).
- A call that names a private field through a granted aspect's method is rejected at that call, and the
  granted template itself may read and build every field (§9).
- `both` is rejected without `where a != b`, and a call with equal labels is rejected naming both (§10).
- A `Label` used in a run-time position is rejected.
- A duplicate label is rejected both for two literals and for two parameters instantiated to the same label.

---

## References

- RFC-0132 — Comptime execution model (§1.1, §3, §3.6); RFC-0092 — Comptime core (§1).
- RFC-0188 — Label syntax; RFC-0221 — Dotted row labels; RFC-0151 — Tuples as numeric-label rows.
- RFC-0121 — Open rows; RFC-0123 — Field-wise row constraints; RFC-0189 — Per-label negative row bounds;
  RFC-0117 — Row narrowing.
- RFC-0174 — Compile-time iteration over a row's fields; RFC-0216 — Constructing rows and residuals.
- RFC-0091 — Linear records; RFC-0122 — Borrow checking; RFC-0032 — Field-level visibility.
- RFC-0170 — Literal types (not extended here); RFC-0222 — Builder aspect.

---

## Decision

**Outcome:** *(pending)*
