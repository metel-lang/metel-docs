---
id: rfc-0180
title: "Literal rows in row arguments"
date: '2026-10-16'
status: under-review
updated: '2026-10-16'
tracking: 'https://github.com/metel-lang/metel-core/issues/1473'
---

> **Status — under review (2026-10-16).** Opened for review; drafted from the v0.14.0 record work.

## Summary

A row argument in generic-argument position may be a literal row, `Req<..{ host: String, ..R }>`,
in addition to the variable form `Req<..R>`. A function or method that returns a nominal
type whose row gained fields can then write its return type, which today it cannot.

---

## Motivation

The compiler already computes the type of a row-extending function. This runs today, with the
return type left off:

```metel
record Req<row R> { data: { ..R } }

fun add_host<row R: !{ host }>(r: Req<..R>, h: String) {
    Req { data = { host = h, ..r.data } }
}

extend<row R: { host: String, .. }> Req<..R> {
    fun build(self) -> String { "GET " + self.data.host }
}
```

The inferred return type is `Req` over a row that gained `host`. That type has no spelling,
because RFC-0121 §5 makes a row argument a variable: `RowArg → ".." IDENTIFIER?`. Three
consequences follow:

- **`Req<..{ host: String, ..R }>` does not parse.** The parser expects an identifier after `..`.
- **A `where` equation does not help in the building direction.** `-> Req<..S> where
  S = { host: String, ..R }` fails with "found type parameter `S`: a declared type parameter is
  opaque inside its own definition", because the body builds a concrete row and `S` is rigid.
- **A method cannot be a setter.** A method with no written return type defaults to `()`,
  so `req.host("x").port(80)` cannot be written. A typestate builder, the main use of
  row-conditional impls (RFC-0121 §3), cannot be completed as methods.

---

## 1. Design

### 1.1 Grammar

`RowArg` gains a literal alternative:

```
RowArg → ".." ( IDENTIFIER | RowLiteral )?
RowLiteral → RecordType        // an open or closed record type, as already parsed
```

`..R` and the anonymous `..` are unchanged. `..{ host: String, ..R }` is an open record type
used as a row, and `..{ host: String }` is the closed row with exactly that field. The prefix
`..` already marks "this is a row" (RFC-0121 §1), so no new marker is needed, and the existing
checks that `..` cannot collide with range syntax apply unchanged (it is type position only).

### 1.2 Meaning

`Req<..{ f₁: T₁, …, ..R }>` denotes `Req` instantiated at the row with those fields extended
by `R`. It is the same type the checker already builds for a record literal with a spread
(`{ f₁ = e₁, …, ..d }`), so an inferred return type and its written form agree and unify.

### 1.3 Disjointness

The labels written in the literal must be provably absent from the tail, exactly as for a
record literal with a spread: `R` needs the bound `R: !{ host }`, or the labels must be
absent from a concrete `R`. Otherwise the type is rejected with the same negative-bound error
(`T0012`) a spread with a possibly-present label produces today.

### 1.4 Kind checking

A `RowArg` may appear only where the corresponding generic parameter is declared `row`. A
literal row where a type parameter is expected is a kind error with a message that names the
parameter.

### 1.5 Where it applies

Everywhere a `RowArg` already can: function and method signatures, annotations, struct and
record fields, and type aliases (RFC-0160). Anonymous tails in a literal (`..{ host: String, .. }`)
are freshened per signature as the anonymous `..` already is.

---

## 2. Costs

- **A grammar addition.** It is additive and does not change the shape of any existing production.
- **A conversion.** The literal converts to the row-extension form the checker already has, so no
  new type-engine variant is needed.
- **A longer type.** `Req<..{ host: String, ..R }>` is longer than `Req<..S>`, and setters that
  add several fields get long return types. A named alias (RFC-0160) can shorten it.

## 3. Alternatives considered

- **A bare record type in the row position, `Req<{ host: String, ..R }>`.** Shorter, but the
  parameter's kind would decide whether a record type is a type or a row, which hides the
  distinction that `..` makes visible everywhere else.
- **Make an equation-defined row transparent in its body**, so `where S = { host: String, ..R }`
  lets `S` and its right-hand side be used interchangeably. More general, and it also helps
  equations used inside bodies, but it changes how rigid parameters are solved in both
  directions. It is not needed to write the return type, and it can follow later without
  conflicting with this RFC.
- **Allow methods to infer their return type.** A larger change to the inference rules for
  methods, and it would not give a written type for annotations or fields.

## 4. Changes to existing documents on acceptance

- RFC-0121 §5 and `reference/spec/grammar.md` (generated from `grammar.pest`): the `RowArg` production.
- `reference/spec/types.md`, `spec.types.generics.open-rows.legality-1`: row arguments may be
  literal rows.
- Fixtures: a written-return-type setter and `build`, a method setter chain, a possibly-present
  label rejected, a literal row where a type is expected rejected.

---

## Open Questions

1. **Is the closed form `..{ host: String }` wanted?** It names a row with exactly one field.
   It may only confuse next to the open form; the alternative is to accept only open literals.
2. **Should a type alias be able to abbreviate a literal row** by naming it, such as
   `type WithHost<row R> := Req<..{ host: String, ..R }>`? RFC-0160 already allows aliases of
   types with row parameters, so this probably works unchanged and needs a fixture, not a rule.

## References

- RFC-0121 §1, §3 and §5 — row parameters, typestate, and the `RowArg` grammar.
- RFC-0178 — row remainder construction (the spread literal this type mirrors).
- RFC-0160 — type aliases.
- metel-core#1473 (the issue) and #1472 (the nested-row bug found alongside it).

---

## Decision

**Outcome:** *(pending)*
