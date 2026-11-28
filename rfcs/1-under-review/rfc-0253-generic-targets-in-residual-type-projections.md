---
id: rfc-0253
title: "Generic Targets in Residual Type Projections"
date: '2026-11-25'
status: under-review
updated: '2026-11-28'
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
  review in RFC-0109, RFC-0251 and RFC-0252. Whether generic named views keep dedicated
  `view` sugar or use aliases only is RFC-0109's decision (moved there 2026-11-28).
- **RFC-0137:** preserves the instantiated brand and full-width normalization. Partial
  moves, ownership and `Drop` are not modified.
- **RFC-0208 / RFC-0192:** a row argument in the base (`Session<..R>.{ .id }`) uses
  RFC-0208's binder, delivered in the same stage (metel-core#1789, #2167). An open tail
  (`Box<T>.{ .value, ..R }`) follows the existing residual-tail rule unchanged (see open
  question 3); this RFC adds no row-equation or disjointness rule.
- **RFC-0211 / RFC-0214 / RFC-0217:** aspect satisfaction of residuals and behavior gained
  on narrowing follow their own rules and open questions; an alias grants no aspect.
- **RFC-0229:** the single-field shorthand (`Box<T>.value`) is distinguished from this
  RFC's form by the token after the dot, `{` or an identifier, so this RFC leaves it free.
  Reconciling the shorthand with generic bases is RFC-0229's own work.
- **RFC-0243 / RFC-0254:** structural matching of a generic residual sees its present
  public fields (RFC-0243 open question 5), and `..Box<T>.{ .value }` extracts the same
  row (RFC-0254 section 1). A projection naming a private field does not widen either.

## Implementation notes

- **Grammar.** `record_projection_type` and `open_record_projection_type` take a
  `named_type` base (`type_path` with optional `<type_args>`) instead of a bare
  `type_path`.
- **Residual identity.** `InferType::Residual { brand, fields }` carries no type arguments
  today. It gains the instantiation's arguments (and the brand's `NominalId`), so
  `Box<String>.{ .value }` and `Box<i32>.{ .value }` stay distinct and unify by brand,
  then arguments positionally, then fields. Full-width normalization produces
  `Named(brand, args)`.
- **Resolution order.** Alias expansion and substitution run before the projection is
  resolved. Field lookup then uses the substituted field types, and the existing
  `projections::check` pass reports unknown types, labels and arity.

## Open questions

All resolved; none blocks acceptance.

1. **Resolved (language owner, 2026-11-25; grammar checked 2026-11-28).** The base is an
   instantiated nominal path or a transparent alias resolving to one; arbitrary type
   expressions and associated-type projections are out of scope. The grammar has no
   ambiguity to resolve. Types and expressions parse through separate rules, and the
   only places a type follows an expression, `as` and `:` ascription, already accept a
   projection type today (`x as Handle.{ .fd }`), so adding `<args>` to the base creates
   no new conflict with comparison. The single-field shorthand of RFC-0229
   (`Box<T>.value`) is told apart by the token after the dot (see Interactions).
2. **Resolved (language owner, 2026-11-25; nested aliases and inference 2026-11-28).**
   Expand and substitute before projection, with definition-site name resolution for
   imported aliases. Nested aliases need no new rule: RFC-0160 already expands
   recursively, rejects cycles, and resolves turbofish through the expansion. Inference
   treats a residual's type arguments like a nominal type's: they are part of its
   identity and unify positionally, so `fun f<T>(v: &Box<T>.{ .value })` called with a
   projection of a `Box<String>` infers `T = String`.
3. **Resolved (language owner, 2026-11-25; tails 2026-11-28).** The base accepts every
   kind its nominal declaration accepts, including rows, with the existing kind and bound
   checks. Through aliases, a row argument is substituted like any other argument. An open
   tail over a generic base (`Box<T>.{ .value, ..R }`) follows the existing rule
   (`spec.types.generics.open-rows.legality-3`) unchanged: it is accepted only as a
   parameter type, it takes its argument whole, and `R` binds the instantiated row's
   remaining fields abstractly. What the tail exposes across modules is RFC-0243's rule,
   not this RFC's: matching sees only public fields.
4. **Resolved (language owner, 2026-11-25; phase 2026-11-28).** Apply existing visibility
   rules after expansion and substitution; a chain of aliases cannot expose a private
   field in a public signature. This governs *access* to the field from outside the
   declaring module, not the alias *declaration* itself (worked example above). The
   check runs after expansion, in the existing visibility rules
   (`spec.modules.visibility.legality-3`, `legality-8`), with their existing diagnostics
   and no new error code.
5. **Resolved (language owner, 2026-11-25; 2026-11-28).** A projection of every declared
   field normalizes to the instantiated nominal type, including when some fields are
   private. Full width counts the declaration's fields, which do not depend on the type
   arguments, so it is decided before substitution. Associated types may appear as type
   arguments (`Box<I::Item>.{ .value }`) and substitute like any other argument; as a base
   they are out of scope (question 1). Chained projection type syntax is deferred to
   RFC-0150.

Former open question 6 (whether generic named views use aliases only or keep `view`
sugar) is a surface decision separate from this capability. It moved to RFC-0109 on
2026-11-28.

## Decision

**Outcome:** *(pending)*
