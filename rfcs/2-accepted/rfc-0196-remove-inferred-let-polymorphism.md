---
id: rfc-0196
title: "Remove Inferred Let-Polymorphism"
date: '2026-10-30'
status: accepted
updated: '2026-10-30'
tracking: 'https://github.com/metel-lang/metel-core/issues/1710'
---

> **Status — under review (2026-10-30).** design drafted; tracked by metel-core#1710 (v0.15.0)

> **Prepared for acceptance (2026-10-30).** All five open questions are resolved. Acceptance follows RFC-0193. It no longer
> waits on RFC-0197 (generic closures), whose tracker moved out of v0.15.0 (2026-10-30); a polymorphic helper that captures
> state takes the state as a parameter until that RFC is taken up.
>
> **Revised (2026-10-30).** Review: adds the ownership-checking evidence (a generalized closure is rejected
> by `--move-check` where the monomorphic one passes), the module-level closure rule, a corrected backend
> note, the future-checks risk, a precise precedent, the rejected restrictions, and one open question.

> **Status — accepted (2026-10-30).** open questions resolved 2026-10-30; no longer waits on RFC-0197

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
- **Only pass-through and consume-once helpers survive ownership checking** (next section). The ergonomic
  benefit is therefore smaller than the unchecked examples suggest.
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
- **Ownership checking rejects what monomorphism accepts.** `let dup := |x| { (x, x) };` used only at `i64`
  runs, and `--move-check` rejects it with `T0019` (`x` moved): generalization makes `x` an unbounded `T`, which is
  non-`Copy` for every instantiation, and a closure cannot write `T: Copy` (GAP-FUNCTIONS-007). The same closure
  annotated `|x: i64|` passes, and so does `fun dup<T: Copy>`. With borrow checking on by default (RFC-0122), this
  is the normal behaviour, not an opt-in corner: an inferred-polymorphic closure is checked as a generic body
  that cannot state a bound.
- **Risk to future checks.** The borrow checker (RFC-0122), abstract regions (RFC-0159), effect rows (RFC-0140)
  and linear closures (RFC-0194) each quantify variables. An implicitly generalized closure would need a rule
  for each: is it polymorphic in its regions, its effect row, its multiplicity? This is a design risk, not a
  known failure. No mainstream language combines ownership checking with inferred let-polymorphism for closures.
- **Not a cost: the backend.** A quantified variable cannot occur in the type of anything a closure captures
  (the environment rule behind #1688), so the environment does not vary with the instantiation. A monomorphizing
  backend (metel-core#288) specializes the body and shares the environment, which is not hard. This RFC does
  not rest on it.

### Precedent

Rust has no let-polymorphism for any value. A closure has one signature (a unique anonymous type
implementing `Fn*` once) and is inferred in a forward pass with expected types. Rust reaches the same
uses with generic `fn` items, which can be nested. Swift's closures cannot be generic (its local functions
can), and Scala 3's polymorphic function literals name their type variable (`[T] => (x: T) => x`). The
ML family generalizes `let`-bound functions, and GHC turns that off (`MonoLocalBinds`) when GADTs or type
families are enabled, because it interacts badly with local constraints. The precedent splits along the
languages that have rich constraints or ownership and those that do not; it is evidence of risk, not proof.

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

### Module-level closures

A closure bound by a top-level `let` must be **fully determined by its own initializer**: its parameter and
return types are written or follow from its body. Otherwise the `let` is an error, "the type of `id` is not
determined by its initializer; annotate its parameters". Without this rule a module-level monomorphic closure
would take its type from whichever function the checker reaches first, a signature read off other
declarations, which RFC-0193 removes for named declarations. Today a top-level `let id := |x| x;` is
generalized and works at `i64` in one function and `boolean` in another; an unused one is accepted. Local
`let`s are unaffected: their inference never leaves the body that contains them. The closures RFC-0193
suggests in place of a function are annotated, so they satisfy the rule.

### Diagnostics

| situation | message |
|---|---|
| a monomorphic closure used at a second type | the mismatch, and `` `id` has one type, `(i64) -> i64`, fixed by its first use `` with the first use's span |
| as above, and the closure form is unconstrained | adds the written generic function (`fun id<T>(x: T) -> T { x }`), only when the closure does not capture (rule below) |
| a closure parameter nothing determines | unchanged (`unannotated_closure_param_nothing_determines_it`) |
| a top-level `let` closure whose type its initializer does not determine | the module-level message above, with the written parameters as the fix |

The generic-function suggestion is made only for a closure that captures nothing. A capturing
polymorphic helper cannot be a `fun` (a `fun` does not capture, RFC-0195); it takes the state it
captures as a parameter of a `fun<T>`, as in Rust. RFC-0197 (a generic binder on a closure) would
give it a closure spelling and is under review.

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
4. **Keep generalization and fix #1691.** Keeps the ergonomics for pass-through helpers. Rejected: the helper
   that duplicates a value is rejected under ownership checking with no way to state `T: Copy`, and each
   planned check (regions, effects, linearity) needs a rule for implicit generalization. See *What it costs*.
5. **Generalize only inside non-generic function bodies.** Avoids #1691 by cutting the case. Rejected: it is
   polymorphic here and not there, and it leaves the ownership-checking cost above.
6. **Written generic closures instead** (`<T>|x: T| …`). Keeps the feature, makes it explicit. It
   is a larger feature (GAP-FUNCTIONS-007), brings back generalization inside generic bodies, and is
   compatible with this RFC as a later addition.

---

## Interactions

- **RFC-0193 (named declarations write their signature):** the pair removes inferred polymorphism. The
  closure suggestion in RFC-0193 section 2 already excludes generic functions, so every function it
  rewrites to a closure is monomorphic and unaffected.
- **RFC-0197 (generic closures):** an optional ergonomic path, not a precondition. `<T: Copy>|x| (x, x)` would
  state the bound the move check needs on a closure; without it, `dup` is written `fun dup<T: Copy>(x: T) -> (T, T)`.
  A polymorphic helper that captures state would get a closure spelling; without it, the state is a parameter.
- **RFC-0195 (local functions do not capture):** a `fun` never captures, so a bounded or generic helper
  with no state is a `fun<T>` and one with state takes that state as a parameter.
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

## Open Questions — resolved 2026-10-30

1. **Keep references to generic functions generalized?** *Resolved: keep.* The polymorphism comes from the
   `<T>` the function's author wrote, not from inference, and it is already specified and implemented
   (`first-class-functions.legality-2`, RFC-0138, metel-core#736). Removing it would pin the alias to its
   first use and narrow an implemented RFC for no checker gain.
2. **Keep written open-record closures row-polymorphic?** *Resolved: keep.* The row variable is the user's
   own `..`, so it passes the test "only what is written quantifies", and it is the only way a closure
   accepts records of different shapes (metel-core#1478). The body is checked once and states no bound it
   cannot state, so it does not have the `dup` problem.
3. **When is this RFC accepted?** *Resolved (revised 2026-10-30): after RFC-0193, without waiting on RFC-0197.*
   A polymorphic helper that captures state is the one case with no closure spelling once inferred
   generalization is gone. Rust has neither generic closures nor recursive closures and takes the state as a
   parameter; so does Metel until RFC-0197 is taken up, which is a separate and lower-priority decision (its
   tracker moved to the Records and surface syntax theme). RFC-0195 is not a precondition.
4. **Which references count as an "already-generic function"?** *Resolved: exactly what the spec already
   allows; this RFC neither widens nor narrows it.* `first-class-functions.legality-2` admits a generic
   function bound with a bare unannotated `let`. Checked 2026-10-30: an imported generic function
   referenced as a value is `T0003` ("not yet a first-class value", RFC-0138), and an associated function
   (`let m := Box::make;`) is monomorphic. Extending first-class references to paths is RFC-0138's
   matter, not this RFC's.
5. **Hard cut or a window.** *Resolved: hard cut.* There is no warning channel (RFC-0187 notes the same), so a
   window would be an error with a different message. The diagnostic names the first use and prints the
   generic function, as RFC-0193 does for signatures.

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
- `let dup := |x| { (x, x) };` used at `i64` passes `--move-check` (monomorphic), and `let dup := |x| { (x, x) };` used at `i64` and `boolean` is the one-type mismatch.
- A top-level `let id := |x| x;` is the module-level error; `let id := |x: i64| x;` passes.
- #1691's repro no longer reaches `I0011`, and the #1688 shapes still pass as monomorphic closures.

## References

- `inference/declarations.rs`, the let-polymorphism branch (closure literal or generic-function reference).
- metel-core#736 (RFC-0138), #1478, #1684, #1688, #1691, #1693, #288.
- RFC-0193 (named declarations do not infer), RFC-0195 (local functions do not capture), RFC-0197 (generic
  closures), RFC-0187 (no warning channel), RFC-0138.
- GAP-FUNCTIONS-006, GAP-FUNCTIONS-007, GAP-TYPES-001.
- `reference/spec/types.md` (Type Inference); fixtures `generics/52_let_polymorphism`,
  `generics/102_generic_fn_reference_reused_at_multiple_types`, `move_check/abstract_let_polymorphic_closure`.

---

## Decision

**Outcome:** *(pending)*
