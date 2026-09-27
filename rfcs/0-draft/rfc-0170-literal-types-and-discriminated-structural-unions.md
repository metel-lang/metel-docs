---
id: rfc-0170
title: "Literal Types and Discriminated Structural Unions"
date: '2026-09-27'
status: draft
---

## Summary

Introduce finite singleton literal types — `"ok"`, `404`, and `true` are types with
exactly one inhabitant — and discriminator-based narrowing. Together with RFC-0165
structural unions, they express value-discriminated sums without a nominal enum or a
compiler-invented runtime tag:

```metel
type Reply<T, E> :=
    { kind: "ok", value: T }
  | { kind: "error", error: E };
```

`reply.kind == "ok"` narrows `reply` to the first member; matching both literal values
is exhaustive. Literal types widen to their primitive base types, so `"ok"` is usable
where `String` is expected.

This RFC owns the literal and narrowing half of TypeScript-style discriminated unions.
It proposes that RFC-0165 resolve its tagged-vs-untagged question in favour of untagged
unions; that joint decision is the sole gate on acceptance.

---

## Motivation

RFC-0165's tagged-coproduct lean cannot express the common protocol shape in which a
field's **value** identifies the case:

```metel
type Message :=
    { op: "ping", id: i64 }
  | { op: "publish", topic: String, body: String };
```

Without singleton types, both `op` fields are `String`. The checker cannot infer that
`message.op` permits `.id` but not `.topic`; a hidden tag does not make the source value
itself the discriminator. This matters for JSON, wire protocols, and configuration where
the producer already emits the literal field.

Nominal enums remain for declaration-owned names, methods, recursion, or a deliberately
closed API. This feature is for structurally described data whose existing fields define
its protocol.

## Goals

- Let a finite literal denote the type inhabited by exactly that value.
- Retain ordinary primitive-literal inference unless a literal type is expected.
- Narrow structural unions from a distinct literal-valued record field.
- Support literal record patterns and direct equality-based narrowing.
- Require neither RTTI nor a synthetic runtime tag.

## Non-goals

- General dependent types, arbitrary value expressions in types, or value parameters.
- Floating-point singleton types, ranges, or interval analysis.
- Record width subtyping or changes to nominal enum representation.
- General runtime type tests; RFC-0165 owns broader union elimination.

## 1. Literal types

In type position, existing non-interpolated string, character, boolean, and integer
literals denote singleton types:

```metel
"ok"       // subtype of String
'x'        // subtype of Char
true       // subtype of boolean
404        // subtype of i64
404u16     // subtype of u16
```

The grammar adds `literal_type` as a type atom. `()` already has one inhabitant. Floats
are excluded: NaN is non-reflexive and signed zero has identity/representation edge cases,
so they belong with RFC-0168's equality design. An unsuffixed integer type literal uses
`i64`, matching RFC-0007's unconstrained-literal default; a suffix is part of identity,
so `1i8` and `1i64` differ. Interpolated strings are expressions, never literal types.

The compiler conceptually represents a literal type as `Literal<Base, value>`. Equality
uses both base and normalized value. Each literal type is a subtype of its base:

```text
"ok" <: String       404u16 <: u16       true <: boolean
```

The reverse conversion is not implicit. Expression literals retain current inference:
`"ok"` normally infers `String` and unconstrained `404` infers `i64`. Precision is
retained only when expected:

```metel
let label: "ok" := "ok";             // accepted
let label: "ok" := "error";          // rejected
let r: { kind: "ok", value: i64 } := { kind = "ok", value = 7 };
```

This deliberately omits a TypeScript `const`/`as const` inference mode. Ascription and
RFC-0160 aliases request precision visibly, leaving ordinary locals freely assignable.

## 2. Discriminated structural unions

A union is discriminated when each record member contains a common label with a distinct
literal type:

```metel
type Reply<T, E> :=
    { kind: "ok", value: T }
  | { kind: "error", error: E };
```

After RFC-0165 normalization, `kind` maps each literal to exactly one final member. The
compiler may choose any qualifying label; that choice is unobservable. A union with no
such label remains an RFC-0165 union but gains none of this RFC's field-equality narrowing
or discriminator-pattern exhaustiveness.

When checking a record literal against an expected union, literal fields are checked
before widening. Exactly one member must accept it: zero is a type error and more than
one is ambiguity. A record literal never acquires a hidden case identity.

## 3. Elimination and narrowing

Record-pattern fields accept a subpattern; a bare field remains a binding:

```metel
match reply {
    { kind: "ok", value } => use(value),
    { kind: "error", error } => recover(error),
}
```

The grammar is `field_pattern = ident ~ (":" ~ pattern)?`. `:` labels a field pattern,
not a binding/initializer separator, so RFC-0136's `:=` rule does not apply. A literal
discriminator selects its member; covering every discriminator literal is exhaustive,
while `_` covers the remaining members.

Direct equality narrows a base path:

```metel
if (reply.kind == "ok") {
    use(reply.value);       // reply: { kind: "ok", value: T }
} else {
    recover(reply.error);   // reply: { kind: "error", error: E }
}
```

`!=` narrows by exclusion in its true branch. The first version recognizes only a direct
field projection compared with a literal, not aliases, calls, arbitrary boolean algebra,
or mutable references. Reassigning the base ends its refinement; a different discriminator
assignment is independently rejected by the singleton field type.

## 4. Representation and RFC-0165

This RFC proposes resolving RFC-0165 Open Question 1: structural unions are **untagged**.
A member is represented as itself; the literal record field is its runtime discriminator.
No wrapper or compiler-generated tag is allocated or observable.

A tagged union can preserve identity for overlapping members, but foreign/wire values do
not carry that identity. Untagged representation accepts the member directly and needs no
RTTI for the discriminated subset. RFC-0165 remains the owner of spelling, normalization,
coercions, and non-discriminated elimination; its tagged-construction language must be
amended with this RFC if accepted.

## 5. Interactions

- **RFC-0165:** direct dependency and joint representation decision; literal members
  compare by full singleton identity.
- **RFC-0116:** records remain exact; `{ kind: "ok" }` and `{ kind: String }` differ.
- **RFC-0160:** transparent aliases name public discriminated-union contracts.
- **RFC-0109:** this is flow narrowing of an anonymous union, not branded self-view
  narrowing.
- **RFC-0168:** the float exclusion avoids deciding NaN equality here.
- **RFC-0007:** supplies integer contextual typing and the `i64` default.
- **Ownership:** narrowing changes only static view; it never moves, copies, or borrows.

## Alternatives considered

### Nominal enum variants

Enums remain better when a declaration owns behaviour or encapsulation. They require a
conversion for externally specified record protocols and use a variant name, not a value
field, as their tag.

### Literal types with hidden union tags

This distinguishes shapes but leaves two competing case identities: a hidden compiler tag
and a visible wire value. It is rejected for the TypeScript-style use case.

### General value-dependent types

Arbitrary expressions require const evaluation, normalization, and equality machinery.
RFC-0132 owns the comptime/const-generic foundation; this RFC admits only finite literals.

## Open questions

1. **Joint RFC-0165 resolution:** Does RFC-0165 accept §4's untagged representation,
   including overlapping non-discriminated members? This is the sole acceptance blocker.
   If rejected, literal types should split into their own RFC.


---

## Decision

**Outcome:** *(pending — `0-draft`. The literal-type proposal is concrete, but its
TypeScript-style union semantics depend on RFC-0165's unresolved representation choice.)*
