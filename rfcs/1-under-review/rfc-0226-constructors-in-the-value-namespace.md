---
id: rfc-0226
title: "Explicit and inferred nominal construction"
date: '2026-11-11'
status: under-review
updated: '2026-11-11'
tracking: 'https://github.com/metel-lang/metel-core/issues/1944'
---

> **Status — under review (2026-11-11).** Review tracked by metel-core#1944.
> Revised after the language-owner discussion: explicit `new T(...)` and inferred
> `.(...)` replace the earlier constructor-binding proposal. Prototype evidence
> and interaction review remain required before acceptance.

## Summary

Nominal construction has two forms with the same argument rules:

```metel
let a := new Point(x = 1, y = 2);    // explicit target
let b: Point := .(x = 1, y = 2);     // expected target
let row := .{ .x = 1, .y = 2 };      // always an anonymous record
```

`new T(args)` resolves `T` in the type namespace. `.(args)` constructs the single
nominal type supplied by the expected type. Both explicitly request construction;
context never changes an anonymous `.{ ... }` literal into nominal construction.

Whole-row construction is explicit too: `new Point(..row)` supplies a record
binding, and `new Point(..{ .x = 1, .y = 2 })` supplies a literal row. Never
reinterpret an ordinary record-valued argument as the whole parameter row.

Bare zero-field struct/named-record construction is retired, as is implicit
construction through `T(...)`. Ordinary function calls keep `f(...)`.

This RFC remains under review. Release assignment lives in metel-core#1944's
milestone. The normative spec and interpreter remain unchanged until integration
and implementation through the project lifecycle.

## Motivation and current behaviour

RFC-0100 made construction a call while allowing a type and a function of one
name. The implementation can choose between them by argument binding:

```metel
struct Ticket { value: i64 }
fun Ticket(input: i64) -> i64 { input + 100 }
fun main() {
    println(Ticket(value = 1).value);
    println(Ticket(input = 1));
    println(Ticket(1));
}
```

The workspace's existing `metel-core/target/debug/metel` printed `1`, `101`,
`101` on 2026-11-11. The inspected
`pipeline/type_checking/construction/expressions.rs::function_takes_the_call`
uses argument binding to select between the function and constructor. This is
local-binary evidence, not a release-tag experiment.

The first revision reserved constructors in the value namespace. That removed
argument-dependent lookup but left construction visually identical to a call.
The language owner also found bare `Empty` unclear. The revised design makes the
operation explicit and offers a compact form that infers only its target type.
The [prior-art survey](../../architecture/reports/construction-syntax-prior-art-survey.md)
compares keyword, brace, associated-operation and ordinary-call alternatives.

## 1. Explicit construction

`new T(args)` is a construction expression. `new` is a reserved keyword; its
operand is a constructible nominal type path, optionally instantiated with type
arguments, rather than an arbitrary value expression. Generic construction uses
`new Pair::<i64>(1, 2)`, retaining the existing turbofish spelling. Aliases and
module qualification work: `new TicketAlias(value = 1)` and
`new model::Ticket(value = 1)`. Inside an impl, `new Self(...)` identifies its type.

Construction targets structs and named records. `new` specifies neither heap
allocation nor a fresh runtime identity; storage and ownership keep their rules.
It does not mean raw field initialisation: it invokes the canonical construction
operation, including validation when RFC-0114 supplies it.

The target resolves in the type namespace independently of arguments and expected
result types. A same-named value cannot capture it:

```metel
struct Ticket { value: i64 }
fun Ticket(input: i64) -> i64 { input + 100 }
let a := new Ticket(value = 1);  // construction
let b := Ticket(1);             // ordinary function call
```

The earlier proposal to reserve constructor names as values is withdrawn. Keep
existing type/value coexistence and import precedence. An ordinary failed call
never retries a same-spelled type constructor, and a failed `new` expression
never retries a value call. A type alias exposes a construction target, not a new
constructor value binding.

## 2. Inferred construction

`.(args)` is always a nominal-construction request. It means the same operation
as `new T(args)` once an independently known expected type supplies `T`:

```metel
struct Point { x: i64, y: i64 }
fun origin() -> Point { .(0, 0) }
fun consume(p: Point) { ... }
consume(.(x = 1, y = 2));

struct Segment { start: Point, end: Point }
let segment := new Segment(.(0, 0), .(10, 20));
```

Expected types may come from an annotation, declared return type or an already
selected callee/constructor parameter. Do not search nominal declarations by
field shape. Do not select between competing overloads using the fields of an
inferred-construction expression. If the target is not uniquely established
without inspecting this expression's constructor arguments, require `new T(...)`.
An abstract generic parameter without an established construction contract is not
a sufficient target. Generic construction capabilities remain separate work.

```metel
let unknown := .(x = 1, y = 2);    // error: target cannot be inferred
let row := .{ .x = 1, .y = 2 };    // anonymous structural record
let p: Point := .{ .x = 1, .y = 2 }; // no implicit nominal construction
```

Inference records the selected target and operation; typed-AST construction reads
that fact rather than making a second semantic decision. Existing expected-type
propagation must be prototyped before claiming the nested examples are supported.

## 3. Positional, keyword and record-valued arguments

Both construction forms retain RFC-0223's argument rules: positional arguments
bind in field declaration order and precede keyword arguments; keywords bind by
name; every parameter is supplied once. Arguments evaluate left to right as
written. No new defaults, partial application or constructor overloading is added.

```metel
let a := new Point(10, 20);
let b: Point := .(10, y = 20);
let c := new Point(y = 20, x = 10);
```

An anonymous record passed normally is one argument, even if its row happens to
match some construction target:

```metel
struct Sample { position: .{ .x: i64, .y: i64 }, weight: i64 }
let a := new Sample(.{ .x = 10, .y = 20 }, 5);
let b: Sample := .(position = .{ .x = 10, .y = 20 }, weight = 5);
```

The record initialises `position`; it is not unpacked into the parameter list.
There is no fallback that retries ordinary positional binding as whole-row binding.

## 4. Whole-row construction: `..r` and `..{ ... }`

A whole-row operand supplies exactly the construction parameter row, with the
same labels and corresponding field types under ordinary checking and generic
inference. It supplies every field, no extra fields, and satisfies the same
visibility requirements as explicit field arguments. Anonymous record field order
does not determine the binding: row labels do.

```metel
let fields := .{ .x = 10, .y = 20 };
let a := new Point(..fields);
let b: Point := .(..fields);
let c := new Point(..{ .x = 10, .y = 20 });
let d: Point := .(..{ .y = 20, .x = 10 });
```

`..r` accepts a plain record binding, as in RFC-0100's existing construction-spread
rule. `..{ ... }` is a dedicated whole-row literal argument with the same value
entries as an anonymous record literal (dotted labels, `=`, puns and existing
record-spread/update rules). It is not `..` followed by the `.{` opener.
The contiguous `..{` notation is used instead of `.. .{ ... }`; the latter is not
an alternative spelling. In generic type-argument position `..{ .x: i64 }` keeps
RFC-0180's literal-row meaning; constructor argument position uses value entries.

A whole-row operand must be the sole argument. Reject multiple whole-row operands
and mixtures such as `new Point(..fields, x = 5)`. To replace a field, explicitly
build an updated record using the existing record-update rules first, or use a
whole-row literal containing the update:

```metel
let p := new Point(..{ ..fields, .x = 5 });
```

The literal's own spread/update semantics are RFC-0191's, not a new constructor
argument-merging mechanism. Evaluate the binding operand or literal once, then
perform the same canonical construction as positional/keyword arguments. No
record-to-nominal coercion is added outside these explicitly marked expressions.

```metel
struct Wrapper { position: .{ .x: i64, .y: i64 } }
new Wrapper(fields)                 // position receives one record value
new Wrapper(..fields)               // error: the whole row needs .position
new Wrapper(..{ .position = fields }) // accepted
```

Arbitrary expression operands after `..` (for example `..make_fields()`) are a
future extension, not included here. A dedicated literal is included in this
proposal; it deliberately extends RFC-0100's current plain-binding-only operand.

## 5. Empty types, variants and failure

Zero-field structs and named records require an explicit construction expression:

```metel
struct Empty {}
let a := new Empty();
let b: Empty := .();
let c := new Empty(..{});
let d: Empty := .(..{});
```

Bare `Empty` no longer implicitly constructs or becomes a first-class constructor
function. `Empty()` is an ordinary value call and constructs nothing implicitly;
if no callable value named `Empty` exists, suggest `new Empty()`. Type annotations
and ordinary reads/calls of same-spelled values remain valid.

Enum variants retain their existing qualified/unqualified bare and call forms.
This RFC introduces neither `new Enum::Variant(...)` nor contextual variant
selection: an expected enum type alone cannot identify a variant. Generalising
the marker to variants is a separate design question, not an implicit consequence.

Both explicit and inferred construction use the same result handling. Neither
inserts an implicit unwrap, catches failure or bypasses validation. RFC-0114's
`Construct`/fallibility model remains its own design; its current synthesised
infallible scope is not evidence of implemented custom constructor support.
Expected-target inference for fallible construction must be reconciled with that
RFC before extending the compact form to such constructors; it must not silently
infer a nominal target from an unrelated `Result` type.

## Interactions and migration

This proposal amends RFC-0100's public construction spelling and retains its
argument collection and exact-row contract. It retires RFC-0106's bare shorthand
for zero-field structs/named records. RFC-0111's enum-variant rules remain.
RFC-0225 owns anonymous record syntax; its literals stay structural. RFC-0114
owns canonical validation, fallibility and privileged minting. Ordinary function
overloads and type/value import coexistence keep their rules.

Before the grammar switch, classify calls using their old resolved identities.
Rewrite constructor calls `T(...)` to `new T(...)` and bare zero-field construction
to `new T()`, including aliases and qualified paths. Preserve ordinary function
calls and value reads even when names match types. Do not automatically choose
compact construction during migration. Inventory uses of `new` as an identifier
and migrate them before reserving the keyword.

Implement prototypes first; acceptance and spec integration precede product
implementation. Public docs, tutorials, active worked examples and changelog land
with implementation, followed by core's docs-pin update. No compiler behaviour is
changed merely by revising this RFC.

## Alternatives and decision

The earlier constructor-in-value-namespace design solved lookup but did not make
construction visibly distinct. Named brace construction and canonical associated
operations were researched; the language-owner discussion selected explicit
`new T(...)` paired with inferred `.(...)`. Enforced casing is unnecessary.

For record operands, implicit row unpacking based on argument shape is rejected:
it would give a normal record-valued positional argument two possible meanings.
Use `..r` or `..{ ... }` to state whole-row intent explicitly. General implicit
anonymous-record-to-nominal conversion is also outside this proposal.

**Current design direction (2026-11-11):** explicit/inferred nominal construction,
ordinary positional/keyword rules, explicit whole-row operands with `..{ ... }`
literal notation, and no implicit construction from bare names or ordinary calls.

**Remaining acceptance work:** parser prototypes for `new`, `.(...)` and literal
whole-row arguments; a resolved-call migration inventory; expected-type inference
checks (including nesting and overload rejection); exact-row, visibility and
single-evaluation fixtures; explicit interaction review with RFC-0225 and the
current scope of RFC-0114. These are evidence requirements, not completed checks.

**Lifecycle outcome:** Under review, tracked by metel-core#1944. No acceptance,
spec integration or implementation transition is claimed.
