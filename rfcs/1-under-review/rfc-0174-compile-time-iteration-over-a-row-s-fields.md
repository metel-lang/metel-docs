---
id: rfc-0174
title: "Compile-time iteration over a row's fields"
date: '2026-10-03'
status: under-review
updated: '2026-10-03'
tracking: 'https://github.com/metel-lang/metel-core/issues/1340'
---

> **Status — under review (2026-10-03).** Design settlement tracked in metel-core#1340 (unmilestoned); not committed to a release

## Summary

A compile-time `for` loop over the fields of a row, so that a blanket impl over every
record can walk its fields:

```metel
extend<row R> { ..R }: Display where all R: Display {
    fun to_string(&self) -> String {
        var out := "{ ";
        comptime for field in fields(R) {
            out := out + field.name + " = " + self.[field.name].to_string() + ", ";
        }
        out + "}"
    }
}
```

The loop is **unrolled per instantiation**, `field.name` and `field.type` are compile-time
values, `self.[field.name]` is a field access by a compile-time name, and the body is
**checked once against a symbolic field** that has only the aspects `where all R: A` grants.
That last rule is what lets a loop over an unknown row be checked at the definition, in line
with RFC-0173.

The same construct is what RFC-0125's stage 2 needs to expand a type-parameter pack
(`static for` in the Rust draft it cites), and, if RFC-0151 makes a tuple a numeric-label
row, the same loop walks a tuple. One loop, three uses.

---

## Motivation

### The condition exists; the body does not

RFC-0123 added `where all R: Aspect`, now implemented (metel-core#1302): an impl or function
requires an aspect of every field of a row. It deliberately stopped there. RFC-0123 §4 chose
a primitive quantifier over PureScript-style induction because "every actual use needed is
*apply one fixed aspect to every field*, never user-programmable" — a statement about the
**condition**.

The **body** of such an impl is a different problem. A `Display` for a record has to render
each field, and nothing in the language can iterate a row: there is no reflection, no row
induction, and no macro system. So `extend<row R> { ..R }: Display where all R: Display` is
accepted today but cannot be given a body that does anything (metel-core#1338). `Eq`, `Hash`
and `Clone` for records have the same shape. `Copy` does not: it has no body (metel-core#1337).

### The near-term answer and why this is still needed

The short path for `Display`, `Eq` and `Hash` is compiler-derived field-wise impls, an
extension of RFC-0096's closed auto-impl set, which already derives `Send`/`Sync` for records
field by field. That needs no new syntax and is the right first step. It is also a **closed
list**: a user aspect (a serializer, a `Describe`, a schema generator) cannot join it. RFC-0093
points at the open version (`#derive` plus `emit`) and RFC-0092 §2 says a derive function
builds its output "by ordinary comptime code — a loop generating a constructor expression",
but neither says what that loop looks like, and both are larger RFCs still under review.

### Three consumers of the same construct

- **Records.** The case above.
- **Parameter packs.** RFC-0125 §1.1 lesson 4 identifies Bertholet's `static for` as "the same
  construct as RFC-0092's comptime iteration" and as the best implementation of its stage 2.
  Its open question 4 asks whether the two are one feature.
- **Tuples.** RFC-0151 (draft) desugars `(A, B, C)` to the row `{ 0: A, 1: B, 2: C }`. If that
  lands, a loop over a row's fields is a loop over a tuple's elements, and RFC-0125's pack
  becomes a row operation rather than a separate calculus.

Designing the loop once, for rows, avoids three spellings.

---

## Prior art

| Language | Mechanism | Shape |
|---|---|---|
| Zig | `inline for (@typeInfo(T).Struct.fields) \|f\|` | comptime loop, field value by `@field(x, f.name)` |
| C++26 | static reflection (P2996), `template for` | `nonstatic_data_members_of`, splice `x.[:m:]` |
| D | `static foreach (i, _; x.tupleof)` | compile-time unrolled loop |
| Nim | `for name, value in fields(x)` | macro-time iterator |
| Julia | `@generated` + `fieldnames(T)` | code generation from field names |
| Rust | `#[derive]` proc macros; Bertholet's `static for` for packs | codegen; or unrolled loop |
| PureScript | `RowToList` + instances by induction | type-level list, no loop |
| Haskell | `GHC.Generics` (`:*:`, `M1`) | structural recursion over a representation type |
| Roc | auto-derived abilities (`Eq`, `Hash`, `Inspect`) | compiler-derived, no user loop |
| Go, Swift, Java | runtime reflection (`reflect`, `Mirror`) | dynamic; no static guarantee |

The unrolled loop (Zig, D, C++26, Rust's draft) is the common answer among languages with a
compile-time evaluator. Metel's RFC-0092/0132 already adopt Zig's execution model.

---

## Proposal (primary)

### D1: `comptime for` over a row's fields

```metel
comptime for field in fields(R) { body }
```

- `fields(R)` is a compile-time function returning the row's fields in a defined order (open
  question 3) as a sequence of compile-time values.
- The loop is **unrolled**: for a row of `n` fields the body is instantiated `n` times, once
  per field, in order. `comptime for` follows the family of `comptime let`, `comptime fun` and
  `comptime if` (RFC-0132), whose untaken branch is likewise "never type-checked or emitted".
- Each `field` has `name` (a compile-time string), `type` (a type value) and `index`.
- The sequence must be compile-time-known at the point of instantiation. Looping over a row
  that is still an abstract variable at the definition is legal; it is unrolled when `R` is
  instantiated.

`fields` is also applicable to a type (`fields(T)` for a record or struct `T`), so the loop
serves RFC-0093's derive functions unchanged.

### D2: Computed field access

```metel
self.[field.name]
```

reads the field of `self` whose label is the compile-time value `field.name`. Its type is
`field.type`. The index must be compile-time-known (a `field.name` of the enclosing
`comptime for`, or another compile-time string); anything else is an error. Reads only in the
first version; assignment through a computed access (`self.[name] := v`) and moves out of one
are open question 6.

### D3: The checking rule: once, against a symbolic field

A loop over an unknown row cannot be unrolled at the definition, so it cannot be checked by
unrolling. Re-checking each unrolled copy per concrete shape would be the template-style
behaviour RFC-0173 removes from generic bodies.

Instead the body is checked **once**, with `field` bound to a *symbolic* field: `field.name` is
an opaque compile-time string, `field.type` is a fresh opaque type `F`, and `self.[field.name]`
has type `F`. `F` is assumed to satisfy exactly the aspects the enclosing declaration requires
of every field (`where all R: Display` gives `F: Display`) and nothing else. A body that
uses more than that is rejected at the definition, with the error on the offending
expression.

Unrolling then happens at instantiation, after the check, as a mechanical expansion; it can
not fail on a type the symbolic check did not already cover. This is RFC-0173 D2 applied to a
row: a body may use only what its bounds entail.

Consequence: a `comptime for` whose body needs an aspect the declaration does not state is a
definition error, not a use-site error, and `all R: A` is what makes the loop usable at all.

### D4: Where it may appear

In any function body or method body, not only in `extend`. A `comptime for` in a derive
function (RFC-0093) loops over `typeinfo(T)`'s row the same way; there the output is
`emit`ted code rather than a value.

### D5: Scope

Specified here: the loop, `fields`, computed read access, the checking rule. Not specified
here: `typeinfo`'s shape (RFC-0092 §2), `emit` and `#derive` (RFC-0093), constructing a row
from per-field results (open question 7), packs (RFC-0125) and tuples (RFC-0151) beyond
"the same loop".

---

## Worked examples

### `Display` (the motivating case)

As in the summary. `where all R: Display` supplies `F: Display` for the single symbolic check;
at `{ x = 1, y = "a" }` the loop unrolls to two statements, each calling the right
`to_string`.

### `Eq` (illustrative; the aspect's method names are as RFC text, not checked here)

```metel
extend<row R> { ..R }: Eq where all R: Eq {
    fun eq(&self, other: &Self) -> boolean {
        comptime for field in fields(R) {
            if (self.[field.name] != other.[field.name]) { return false; }
        }
        true
    }
}
```

`comptime for` with an ordinary `return` inside is unrolled; the early exit is a runtime
branch, not a compile-time one. A `break` or `continue` that depends on a compile-time value
is open question 5.

### What it does not cover

`Clone` and `Default` need to *build* a record whose labels are compile-time values. Reading by
computed label is not enough; that needs a record literal with computed labels, or `emit`
(RFC-0093). Left to open question 7 and to RFC-0093.

---

## Alternatives

- **Compiler-derived impls only (Rust derive, Roc).** The right near-term step for a fixed set
  of aspects, and not mutually exclusive with this RFC: it is the implementation of #1337 and
  #1338 that does not need a loop. It cannot serve a user aspect.
- **A visitor with a generic method.** `aspect FieldVisitor<A> { fun visit<T: A>(&var self,
  name: String, value: &T); }` and an intrinsic `each_field(self, &var v)`. Needs no new syntax.
  It works today in the language's terms, but moves the loop body into a separate named type
  for every use, and the intrinsic is a one-off.
- **Type-level induction (PureScript `RowToList`, Haskell Generics).** Needs type-level lists,
  label-kinded generics and recursive impl resolution. RFC-0123 §4 set it aside and nothing here
  changes that.
- **Runtime reflection.** Loses the static guarantee that every field satisfies `A`, and costs
  at runtime. Rejected for the same reason RFC-0123 prefers the quantifier.
- **Check each unrolled copy per shape (C++ templates).** Simplest, and exactly what RFC-0173
  proposes to remove for generic bodies; it would re-introduce definition-site errors reported
  at the use.

---

## Open Questions

1. **Spelling of the loop.** `comptime for` (consistent with `comptime let/fun/if`) or
   `static for` (D, and the name RFC-0125 quotes from the Rust draft). Leaning `comptime for`.
2. **Spelling of computed access.** `self.[name]`, `self.(name)`, or a function `field(self,
   name)`. Leaning `self.[name]`; the bracket form cannot be confused with a literal label or
   a call.
3. **Field order.** Declaration order for a nominal record or struct; anonymous records are
   stored sorted by label, so a sorted order there. RFC-0092 §2 already notes reflection needs
   a stable order and open question 1 asks where the metadata lives. Needs a decision that
   covers a nominal record, an anonymous record and a tuple.
4. **Name type.** A `String`, or a `Symbol` type (RFC-0092's `TypeInfo` uses `Symbol`). The
   difference matters for `self.[field.name]` being checked against a closed label set.
5. **`break`/`continue` and early exit.** Allowed only when the condition is compile-time
   decidable, or banned in the first version. `return` inside the unrolled body is expected to
   work as an ordinary runtime early exit.
6. **Moves and writes.** Does `self.[field.name]` read by copy, by reference, or move out of a
   by-value `self`? A partial move out of a row has residual-type consequences (RFC-0137). Is
   assignment through a computed access in scope?
7. **Building a row from per-field results.** `Clone`, `Default` and deserialization need a
   record literal with computed labels (`{ [field.name] = v, .. }`) or `emit`. Specify here, or
   leave to RFC-0093.
8. **Visibility.** Does a loop in module `m` see the private fields of a nominal record from
   another module? A `record` has only public fields (RFC-0120), a `struct` may not.
9. **Packs and tuples.** Confirm that a pack loop (RFC-0125 stage 2, spelled `static for` in
   the Rust draft it cites) and a tuple row (RFC-0151) are the same construct as this one, and
   which RFC owns the spelling for a pack.
10. **Error reporting.** A failure inside an unrolled iteration must name the source location
    of the loop body, not the instantiation, as RFC-0092 open question 9 asks for comptime
    errors in general.
11. **Interaction with `comptime if`.** A `comptime if (field.type == i64)` inside the loop
    would let a body specialise per field type, which breaks the "only the declared bounds"
    check of D3 unless the branch is checked on both sides. Allowed, or deferred?

---

## Implementation Notes

- **Does not gate #1337/#1338.** Their near-term path is compiler-derived impls extending
  RFC-0096. This RFC is the general mechanism behind them and the answer for user aspects.
- **Depends on** RFC-0132 (the `comptime` execution model: `comptime fun`, `comptime if`) and
  on RFC-0173 for D3's rule. It cannot be implemented ahead of either, and RFC-0132's current
  slice (#726, static array sizes) does not include a loop.
- **Staging.** The loop and computed read access are the minimum. `emit`/`#derive` and row
  construction stay with RFC-0093.
- An ADR accompanies the implementation once accepted, recording the unrolling and the
  symbolic-field check.

---

## References

- RFC-0123 (Field-Wise Row Constraints): `where all R: A` and its §4 on why the quantifier is
  primitive.
- RFC-0125 (Variadic Generics), §1.1 lesson 4 and open question 4: the same loop for packs.
- RFC-0151 (Tuples as Numeric-Label Rows, draft): a tuple is a row.
- RFC-0092 §2 (`typeinfo`), RFC-0093 (`#derive`, `emit`), RFC-0132 (comptime execution model).
- RFC-0096 (auto-impl set): the closed list the near-term derive extends.
- RFC-0173: a body may use only what its declared bounds entail.
- metel-core#1337 (`Copy` for records), #1338 (`Display` for records), #1302.

---

## Decision

**Outcome:** *(pending)*
