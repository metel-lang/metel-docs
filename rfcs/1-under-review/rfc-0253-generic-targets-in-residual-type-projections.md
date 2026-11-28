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
   A generic base written without its argument list (`Box.{ .value }` for a generic `Box`)
   is an arity error; arguments are never inferred for a projection base (2026-11-28).
   `Self` is accepted as a base and denotes the enclosing impl's target *with its
   arguments*: inside `extend<T> Box<T>`, `Self.{ .value }` is `Box<T>.{ .value }`
   (2026-11-28).
   The base may use every generic argument kind accepted by its nominal declaration,
   including row arguments, subject to that declaration's kind and bound checks
   (language owner, 2026-11-25). A row argument uses RFC-0208's spelling, delivered in the
   same stage: the binder `<..R>`, used bare (`Session<R>.{ .id }`).
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
   hide inaccessible fields. Visibility is checked on the expanded type, after alias
   expansion, generic substitution and full-width normalization (language owner,
   2026-11-25 and 2026-11-28). Naming an alias outside its module is writing its
   expansion: if the expansion names a field private at that site, the use is `T0009`
   under `spec.modules.visibility.legality-3`, exactly as if the residual had been written
   out. An alias naming a private field therefore cannot expose that field in a public
   signature, including through another alias. An alias used as the base
   expands first: `Container<T>.{ .value }`, where `Container<T> := Box<T>`, names
   `Box<T>.{ .value }`. An imported alias resolves its target in its defining module,
   following RFC-0160 (language owner, 2026-11-25).
4. An empty projection such as `Box<T>.{}` is supported. An open residual tail
   (`Box<T>.{ .value, R }`) follows the existing residual-tail rule
   (`spec.types.generics.open-rows.legality-3`) unchanged, written with RFC-0208's binder;
   open question 3 states what the tail binds. This RFC adds no row-equation or
   disjointness rule.
5. Chained projection type syntax such as `Box<T>.{ .value, .label }.{ .value }` is
   outside this RFC's initial scope and is deferred to RFC-0150 (language owner,
   2026-11-25). Re-projecting an already narrowed value follows existing residual rules.
6. A generic residual projection may appear wherever a type is accepted, including
   parameter, return, field and alias positions, subject to the existing visibility,
   ownership and position-specific legality rules (language owner, 2026-11-25). An open
   tail stays parameter-only, as for a non-generic base.

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

**Visibility follows expansion (2026-11-28).** An alias that retains a private field is
legal to declare where the field is visible, but outside that module it is unusable,
because naming it writes its expansion:

```metel
// in Box's own module
struct Box<T> { pub value: T, pub label: String, secret: T }
type Inner<T> := Box<T>.{ .value, .secret };          // legal here: `secret` is visible
pub type Pub<T> := Box<T>.{ .value, .secret };        // warning: `pub` is pointless, no other
                                                      // module can name this type

// elsewhere
fun peek<T>(b: &Pub<T>) { }                           // T0009: expands to a residual naming the
                                                      // private field `secret`
fun shown<T>(b: &Box<T>.{ .value, .label }) { }       // OK: public fields only
```

The projection is deliberately not full-width (it leaves out `label`): a full-width
projection normalizes to `Box<T>` before the visibility check, names no field, and so is
usable anywhere. The warning on `Pub` is new, modelled on the pointless-`pub` field warning
(`spec.modules.visibility.legality-5`). Exposing private parts to other modules is opaque
views' job (RFC-0251), not an alias's.

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
- **RFC-0208 / RFC-0192:** a row argument in the base (`Session<R>.{ .id }`, binder
  `<..R>`) uses RFC-0208's spelling, delivered in the same stage (metel-core#1789, #2167).
  An open tail (`Box<T>.{ .value, R }`) follows the existing residual-tail rule (rule 4);
  this RFC adds no row-equation or disjointness rule.
- **RFC-0211 / RFC-0214 / RFC-0217:** aspect satisfaction of residuals and behavior gained
  on narrowing follow their own rules and open questions; an alias grants no aspect.
- **RFC-0229:** the single-field shorthand (`Box<T>.value`) is distinguished from this
  RFC's form by the token after the dot, `{` or an identifier, so this RFC leaves it free.
  Reconciling the shorthand with generic bases is RFC-0229's own work.
- **RFC-0243 / RFC-0254:** structural matching of a generic residual sees its present
  public fields (RFC-0243 open question 5), and `..Box<T>.{ .value }` extracts the same
  row (RFC-0254 section 1). A projection naming a private field does not widen either.

## Implementation notes

- **Grammar.** The projection base becomes a `named_type` (`type_path` with optional
  `<type_args>`). Factor it as one `named_type` followed by an optional projection suffix
  (closed or tailed), not as separate alternatives that each start with `named_type`:
  pest does not memoize, so re-parsing the base per alternative costs about 4^depth on
  nested generics (`A<B<C<…>>>`), where the current `type_path` base fails at `<` at once.
- **Residual identity.** `InferType::Residual { brand, fields }` carries no type arguments
  today. It gains the instantiation's arguments (and the brand's `NominalId`), so
  `Box<String>.{ .value }` and `Box<i32>.{ .value }` stay distinct. Two residuals unify by
  brand, then arguments positionally and invariantly, then equal field sets. Width
  narrowing (a `&Box<String>`, or a wider residual, passed where `&Box<T>.{ .value }` is
  expected, RFC-0137) unifies the arguments the same way and checks that the expected
  fields are a subset. Every residual carries its arguments, including those produced by
  move-narrowing (`spec.ownership.narrowing.legality-1`), not only written ones.
  Full-width normalization produces `Named(brand, args)`.
- **`Self`.** `resolve_record_projection_type` resolves `Self` to the bare struct name
  today (`conversions.rs`). It must resolve to the impl target with its arguments, or
  `Self.{ .value }` inside `extend<T> Box<T>` keeps an unsubstituted, argument-less
  residual (the #774 class of bug).
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
   (`Box<T>.value`) is told apart by the token after the dot (see Interactions). `Self`
   as a base is the impl target with its arguments, and a generic base without arguments
   is an arity error (rule 1).
2. **Resolved (language owner, 2026-11-25; nested aliases and inference 2026-11-28).**
   Expand and substitute before projection, with definition-site name resolution for
   imported aliases. Nested aliases need no new rule: RFC-0160 already expands
   recursively, rejects cycles, and resolves turbofish through the expansion. Inference
   treats a residual's type arguments like a nominal type's: they are part of its
   identity and unify positionally, so `fun f<T>(v: &Box<T>.{ .value })` called with a
   projection of a `Box<String>`, or with a whole `&Box<String>` through width narrowing,
   infers `T = String` (Implementation notes).
3. **Resolved (language owner, 2026-11-25; tails 2026-11-28).** The base accepts every
   kind its nominal declaration accepts, including rows, with the existing kind and bound
   checks. Through aliases, a row argument is substituted like any other argument. An open
   tail over a generic base (`Box<T>.{ .value, R }`) follows the existing rule
   (`spec.types.generics.open-rows.legality-3`) unchanged: it is accepted only as a
   parameter type and takes its argument whole. `R` binds the instantiated row's remaining
   *public* fields; binding a remainder never reveals a private field (RFC-0208 item 4).
   Private fields travel with the whole value but appear neither among the named fields
   nor in `R`.
4. **Resolved (language owner, 2026-11-25; phase 2026-11-28).** Apply existing visibility
   rules after expansion and substitution; a chain of aliases cannot expose a private
   field in a public signature. Decided 2026-11-28: visibility is checked on the expanded
   type, after substitution and full-width normalization. Declaring the alias is legal
   where its fields are visible; naming it where they are not is `T0009`, as if the
   residual were written out (worked example above). The checks are the existing
   `spec.modules.visibility.legality-3` and `legality-8`, with no new error code; a `pub`
   alias that no other module can name gets a new warning modelled on `legality-5`'s pointless-`pub` field warning.
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
