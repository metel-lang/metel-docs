---
id: rfc-0253
title: "Generic Targets in Residual Type Projections"
date: '2026-11-25'
status: under-review
updated: '2026-11-26'
tracking: 'https://github.com/metel-lang/metel-core/issues/2194'
---

> **Status — under review (2026-11-25).** Scheduled for row visibility and named records design review

## Summary

Allow a residual type projection to name an instantiated generic nominal type, including
in a generic type alias. The following syntax is proposed, not implemented:

```metel
struct Box<T> { pub value: T, pub label: String }
type Value<T> := Box<T>.{ .value };
// Value<String> names Box<String>.{ .value }.
```

The residual retains the instantiated nominal brand and exactly the selected fields.
This draft addresses the generic-target limitation independently of whether RFC-0109
uses dedicated named views or transparent type aliases. It does not settle opaque views.

## Motivation

Existing transparent aliases can name residual types such as `type Empty := Pair.{};`
(RFC-0160). Current `record_projection_type` grammar accepts a `type_path` before
`.{ ... }`, but that path cannot carry generic arguments. Generic aliases themselves
exist, so an alias cannot currently express the corresponding residual of `Box<T>` by
writing `Box<T>.{ .value }`. A uniform projection type permits reusable generic
narrowed receiver signatures without a separate naming mechanism.

## Proposal

1. In a residual type position, accept an instantiated nominal path or a transparent
   alias that resolves to a nominal type as the projection base: `Box<T>.{ .value }`.
   Arbitrary type expressions and associated-type projections as bases are outside the
   initial scope (language owner, 2026-11-25). The base must resolve to a nominal type with the selected fields;
   missing or duplicate labels, wrong generic arity or kind, and unsatisfied bounds are
   errors. Field types are obtained after substituting the base's type arguments.
   The base may use every generic argument kind accepted by its nominal declaration,
   including row arguments, subject to that declaration's kind and bound checks
   (language owner, 2026-11-25). Proposed row-only binder syntax depends on RFC-0208.
2. The residual is the pair of the instantiated brand and the selected row. Thus
   `Box<String>.{ .value }` and `Box<i32>.{ .value }` are different instantiations, and
   an equally shaped residual of another brand is distinct. Full-width normalization,
   narrowing, ownership, visibility and aspect behavior follow the existing rules for
   residuals rather than introducing a new nominal type. A projection containing every
   field in the instantiated declaration normalizes to that instantiated nominal type.
   All fields count, including private fields; a public-only projection is not full-width
   when private fields remain (language owner, 2026-11-25).
3. A transparent alias substitutes its parameters into the entire projection base and
   expands to the resulting residual as RFC-0160 requires. Its own visibility does not
   hide inaccessible fields. Public signatures and field access remain subject to the
   normal visibility checks after alias expansion and generic substitution. An alias
   naming a private field cannot expose that field in a public signature, including
   through another alias (language owner, 2026-11-25). An alias used as the base
   expands first: `Container<T>.{ .value }`, where `Container<T> := Box<T>`, names
   `Box<T>.{ .value }`. An imported alias resolves its target in its defining module,
   following RFC-0160 (language owner, 2026-11-25).
4. An empty projection such as `Box<T>.{}` is supported. Open residual tails and row-only
   binders such as `Box<T>.{ .value, R }` are an interaction with RFC-0208, not a new
   row-equation or disjointness rule in this RFC.
5. Chained projection type syntax such as `Box<T>.{ .value, .label }.{ .value }` is
   outside this RFC's initial scope and is deferred to RFC-0150 (language owner,
   2026-11-25). Re-projecting an already narrowed value follows existing residual rules.
6. A generic residual projection may appear wherever a type is accepted, including
   parameter, return, field and alias positions, subject to the existing visibility,
   ownership and position-specific legality rules (language owner, 2026-11-25).

## Worked examples

```metel
struct Box<T> { pub value: T, pub label: String }
type Value<T> := Box<T>.{ .value };
type EmptyBox<T> := Box<T>.{};
fun use_value(v: &Value<String>) { /* v has Box<String>'s brand */ }
```

`Value<String>` and `Box<String>.{ .value }` are interchangeable. A residual of a
second struct with the same `value` field does not become `Value<String>`. A type alias
naming a private field does not authorize an external caller to access that field or
permit a private field name in a public signature.

**Declaring a `pub` alias that retains a private field is a different operation from accessing that field, and only the
second is rejected** — an adversarial check against rule 3 and open question 4, whose wording ("a chain of aliases cannot
expose a private field in a public signature") is ambiguous between the two:

```metel
// in Box's own module
struct Box<T> { pub value: T, secret: T }
pub type Inner<T> := Box<T>.{ .value, secret };   // legal: written where `secret` is visible

// elsewhere
fun peek<T>(b: &Inner<T>) -> &T { &b.secret }     // error: `secret` is private to Box's module
```

`Inner<T>`'s declaration is legal because it is written inside `Box`'s module, where `secret` is visible — being `pub`
as a *type* does not change that, the same way a `pub` function may return a value whose fields stay private. Ordinary
residual field-access visibility (RFC-0109 `legality-8`) applies to `Inner<T>` exactly as it would to `Box<T>` directly,
because the alias is transparent (RFC-0160): this RFC adds no privacy rule on top of that one, it only confirms the
existing rule survives expansion.

## Alternatives

A dedicated generic `view Value<T> for Box<T> { value }` supplies a convenient name but
still needs a definition of the same instantiated residual. Another option is to keep
generic targets unsupported and require one alias per concrete instantiation; that is
not viable if the same grammar excludes generic arguments in the projection base.

## Interactions and limits

- **RFC-0109 / RFC-0160:** generic transparent view names and alias expansion. Narrowed
  receivers, automatic borrowing, and opaque views are independent and remain under
  review in RFC-0109, RFC-0251 and RFC-0252.
- **RFC-0137:** preserves the instantiated brand and full-width normalization. Partial
  moves, ownership and `Drop` are not modified.
- **RFC-0208 / RFC-0192:** row binders, open tails, row literals and explicit arguments
  require joint grammar and kind checking. This draft does not settle their syntax.
- **RFC-0211 / RFC-0214 / RFC-0217:** aspect satisfaction of residuals and behavior gained
  on narrowing follow their own rules and open questions; an alias grants no aspect.
- **RFC-0229:** single-field projection shorthand needs reconciliation with generic bases
  and associated-item path syntax.

## Open questions

1. The initial base is an instantiated nominal path or a transparent alias resolving to
   one; arbitrary type expressions and associated-type projections are out of scope
   (language owner, 2026-11-25). The grammar must resolve `Box<T>.{ ... }` without
   ambiguity with expression comparison and the proposed `Self.field` shorthand.
2. **Aliases as bases:** expand and substitute before projection, with definition-site
   name resolution for imported aliases (language owner, 2026-11-25). Nested aliases and
   interaction with inference still need integration checks.
3. **Argument kinds:** the base accepts every kind its nominal declaration accepts,
   including rows, with the existing kind and bound checks (language owner, 2026-11-25).
   Propagation through aliases and open residual tails across modules needs integration review.
4. **Privacy:** apply existing visibility rules after expansion and substitution; a
   chain of aliases cannot expose a private field in a public signature (language owner,
   2026-11-25). **Disambiguated:** this governs *access* to the field from outside the
   declaring module, not the alias *declaration* itself — a `pub` alias retaining a
   private field in its projected row is legal to declare wherever that field is visible
   (worked example above); only an external access to it is rejected. The implementing
   phases and diagnostics need integration review.
5. **Full width:** a projection of every declared field normalizes to the instantiated
   nominal type, including when some fields are private (language owner, 2026-11-25).
   Chained projection type syntax is deferred to RFC-0150; associated types and inference
   still need integration review.
6. Should generic transparent named views in RFC-0109 use aliases exclusively or retain
   dedicated sugar? That surface decision is separate from this residual-type capability.

## Decision

**Outcome:** *(pending)*
