---
id: rfc-0196
title: "Remove Inferred Let-Polymorphism"
date: '2026-10-30'
status: under-review
updated: '2026-10-30'
tracking: 'https://github.com/metel-lang/metel-core/issues/1710'
---

> **Status — under review (2026-10-30).** design drafted; tracked by metel-core#1710 (v0.15.0)

## Summary

An unannotated `let`-bound closure has **one type**. Inference no longer turns its unresolved type
variables into type parameters, so `let id := |x| x;` used at `i64` and then at `boolean` is a type
error, as in Rust. Polymorphism in Metel is then always *written* or *already declared*:

- a type, bound or row parameter list on a `fun` (`fun id<T>(x: T) -> T`);
- a written open record (`|p: { x: i64, .. }| p.x`), whose `..` is the user's own row variable;
- a reference to an already-generic function (`let f := identity;`), which keeps the scheme its
  declaration wrote.

Together with RFC-0193 (named declarations write their signature), this removes inferred
polymorphism from the language: inference solves the types inside one body and never invents an
interface.

```metel
let id := |x| { x };
id(42);
id(true);
// error[T0001]: `id` has one type, `(i64) -> i64`, fixed by its first use; found `boolean`
//   help: to use it at several types, write a generic function:
//             fun id<T>(x: T) -> T { x }
```

This is a design draft. Nothing here is accepted, and the checker is unchanged until it is.

---

## Motivation

### What generalizes today

At a `let`, the checker quantifies free type variables for exactly two shapes
(`inference/declarations.rs`, the let-polymorphism branch): an unannotated **closure literal**, and
a **bare identifier naming an already-generic function** (metel-core#736, RFC-0138). Nothing else is
generalized: `let e := Vec::new();` and `let n := None;` stay monomorphic. Named functions with
unannotated parameters are generalized too; RFC-0193 removes that.

### What it buys

Measured against the fixtures and spec, not against real programs:

- **A local polymorphic helper without a type-parameter list**: `let id := |x| x;`, `|a, b| (b, a)`.
  Only **unconstrained** polymorphism is reachable, because a closure cannot name a bound or a row fact
  (GAP-FUNCTIONS-007), and it cannot recurse (GAP-FUNCTIONS-006).
- Every case has a `fun f<T>` spelling. Nothing is expressible *only* through generalization.
- The fixtures that exercise it are tests of the feature (`generics/52_let_polymorphism`,
  `limit_02_let_closure_mono`, `move_check/abstract_let_polymorphic_closure`, and two added for #1688).
  The standard library and the website showcases were not measured for use of this feature; the
  acceptance step below does.

### What it costs

- **Bugs.** #1688 (let-generalization against the wrong environment), #1691 (a generalized closure in
  a generic body: the move check meets a quantified variable in an abstract signature, `I0011`), and
  the I0010 family (a generic definition accepted whose reconstruction disagrees) all live where a
  closure is treated as a generic definition of its own. #1693 (a `many` closure owning a non-`Copy`
  capture in a generic body) is a separate gap that this RFC does not close.
- **Order of checks.** Qualifier checks on closures (`once`, `var`, expected-type checks) had to be
  deferred until after solving, because the closure's type is not known until generalization has run
  (#1684, #1700).
- **An explanation burden.** `let id := |x| x` is polymorphic and `let v := Vec::new()` is not. The
  rule is a syntactic one (closure literal or generic-function reference), not a typing one.
- **A forward cost.** A monomorphizing backend (metel-core#288) would specialize one closure value's body
  per use type while sharing its environment. A monomorphic closure has one body and one environment.

### Precedent

Rust has no let-polymorphism for any value. A closure has one signature (a unique anonymous type
implementing `Fn*` once) and is inferred in a forward pass with expected types. Rust reaches the same
uses with generic `fn` items, which can be nested.

---

## 1. The rule

A `let` or `var` binding is **monomorphic** unless its initializer is one of the two forms below. The
type variables of an unannotated closure that are unresolved when the binding is checked are not
quantified: they stay variables of the enclosing function and are resolved by the binding's uses. A
use at a second, different type is the ordinary mismatch.

Generalization is kept, unchanged, for the two forms whose polymorphism is not invented by inference:

1. **A reference to an already-generic function** (`let f := identity;`). The scheme is the
   declaration's. This is metel-core#736 / RFC-0138 and is not touched.
2. **A closure whose written annotation names a row variable** (`|p: { x: i64, .. }| p.x`). Only the
   variables that the annotation itself introduced are quantified; the parameter and return types the
   closure infers are not. This is metel-core#1478.

So the test for quantification is **where the variable came from**: a written parameter, a written `..`,
or a generic declaration quantify; a type variable created by inference does not.

### Diagnostics

| situation | message |
|---|---|
| a monomorphic closure used at a second type | the mismatch, and `` `id` has one type, `(i64) -> i64`, fixed by its first use `` with the first use's span |
| as above, and the closure form is unconstrained | adds the written generic function (`fun id<T>(x: T) -> T { x }`), only when the closure does not capture (rule below) |
| a closure parameter nothing determines | unchanged (`unannotated_closure_param_nothing_determines_it`) |

The generic-function suggestion is made only for a closure that captures nothing. A capturing
polymorphic helper cannot be a module-level `fun`; its spelling is a local function with captures,
which is RFC-0195.

---

## 2. What does not change

- Explicit generics on `fun`, `struct`, `enum`, `aspect`, `extend`.
- Row polymorphism through `<record R>` parameters.
- Named functions: RFC-0193, a separate and compatible change.
- Closure semantics (captures, qualifiers, multiplicity), including their checks.
- Inference inside a body: literals, method calls and constraints still solve by unification.

---

## Alternatives Considered

1. **Status quo.** Keep generalizing closures. Keeps the convenience; keeps the cost. Each feature
   that touches closures (qualifiers, the move check, monomorphization) has to work with a generalized
   closure as well.
2. **Generalize capture-free closures only.** A closure with captures is the interaction surface of
   #1688 and #1693. Avoids those two but not #1691 (a capture-free `|y| y` in a generic body), and
   adds a rule that is itself an explanation burden.
3. **Remove all generalization, including references to generic functions and written open records.**
   The simplest statement ("a `let` is monomorphic"), at a cost: `let f := identity;` is pinned to its
   first use, and a closure cannot be row-polymorphic at all. Recommended against: neither is
   polymorphism invented by inference, and removing them gains nothing in the checker.
4. **Written generic closures instead** (`<T>|x: T| …`). Keeps the feature, makes it explicit. It
   is a larger feature (GAP-FUNCTIONS-007), brings back generalization inside generic bodies, and is
   compatible with this RFC as a later addition.

---

## Interactions

- **RFC-0193 (named declarations write their signature):** the pair removes inferred polymorphism. The
  closure suggestion in RFC-0193 section 2 already excludes generic functions, so every function it
  rewrites to a closure is monomorphic and unaffected.
- **RFC-0195 (local functions follow the closure capture rules):** the spelling of a polymorphic
  helper that captures state. Without it, such a helper has no form and the diagnostic above says so.
- **RFC-0138 (generic function references), metel-core#1478:** the two kept forms.
- **RFC-0050, RFC-0153, RFC-0157, RFC-0194:** closure rules are untouched; the closures they describe
  just have a single type.
- **Move check (`--move-check`):** #1691 stops being reproducible, since no `let`-bound closure is
  polymorphic; the abstract-body analysis loses a case it never supported.

---

## Migration

A closure used at two types becomes a generic `fun` (or two closures). The compiler knows the first use
and the conflicting one at the error and prints the generic function. Fixtures that test generalization
become tests of the new diagnostic or move to `fun f<T>`; the #1688 fixtures
(`v0_15_0_let_bound_closure_*`) are re-pointed at monomorphic closures. The number of affected fixtures
and documentation examples is not measured; see below.

---

## Open Questions

1. **Keep references to generic functions generalized?** Recommendation: yes (Alternative 3).
2. **Keep written open-record closures row-polymorphic?** Recommendation: yes.
3. **Order with RFC-0193 and RFC-0195.** RFC-0193 and this RFC are independent and could land in one
   release. A polymorphic helper that captures state needs RFC-0195; if that is rejected, this RFC
   removes a form that has no replacement for that case. Decide whether this RFC waits for RFC-0195's
   outcome.
4. **Hard cut or a window.** There is no warning channel (RFC-0187 notes the same). Recommendation: hard
   cut with the targeted diagnostic.

---

## Specification impact

Spec text lands only at `3-integrated`. `reference/spec/types.md`, *Type Inference* (GAP-TYPES-001):
"Hindley-Milner with let-polymorphism" becomes inference within a body with polymorphism only from
written or declared parameters, and "annotations are optional for all bindings" is narrowed together
with RFC-0193. `reference/spec/functions.md`: *Closures*, a rule that a closure has one type. No new
error code is proposed; the mismatch is `T0001`.

## Acceptance criteria for a prototype

- Instrument the checker: over the corpus (fixtures, spec, tutorial, standard library), count unannotated
  `let` closures whose generalized scheme is instantiated at two or more distinct types. This decides
  whether the migration is cheap.
- Turn off the closure-literal branch of the let-polymorphism code and list the failing fixtures.
- `let f := identity;` still works at several types; `|p: { x: i64, .. }| p.x` still accepts
  several shapes.
- The diagnostic above is produced for `id(42); id(true);`.
- #1691's repro no longer reaches `I0011`, and the #1688 shapes still pass as monomorphic closures.

## References

- `inference/declarations.rs`, the let-polymorphism branch (closure literal or generic-function reference).
- metel-core#736 (RFC-0138), #1478, #1684, #1688, #1691, #1693, #288.
- RFC-0193 (named declarations do not infer), RFC-0195 (local functions follow the closure capture
  rules), RFC-0187 (no warning channel), RFC-0138.
- GAP-FUNCTIONS-006, GAP-FUNCTIONS-007, GAP-TYPES-001.
- `reference/spec/types.md` (Type Inference); fixtures `generics/52_let_polymorphism`,
  `generics/102_generic_fn_reference_reused_at_multiple_types`, `move_check/abstract_let_polymorphic_closure`.

---

## Decision

**Outcome:** *(pending)*
