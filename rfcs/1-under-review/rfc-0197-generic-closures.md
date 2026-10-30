---
id: rfc-0197
title: "Generic Closures"
date: '2026-10-30'
status: under-review
updated: '2026-10-30'
tracking: 'https://github.com/metel-lang/metel-core/issues/1711'
---

> **Revived (2026-10-30).** RFC-0195 was reversed: a local `fun` does not capture, so a generic, bounded or
> row-fact helper that captures state has no spelling except a closure with a binder. That is this RFC. It was
> deferred earlier the same day on the opposite premise (that a capturing local `fun` covered the case).
> The binder order (binder first) is settled.

> **Status — under review (2026-10-30).** revived: RFC-0195 reversed (local functions do not capture); tracked by metel-core#1711 (v0.15.0)

## Summary

A closure literal may carry a **generic binder**: type parameters with bounds, a `where` clause,
and row parameters with row facts, written as a `fun` writes them. A closure can then name what
today only a `fun` can name.

```metel
let first_or := <T: Copy>|xs: [T], d: T| -> T { if (xs.len() == 0) { d } else { xs[0] } };
first_or([1, 2], 0);          // T = i64
first_or(["a"], "z");         // T = String

let add_host := <record R: !{ host }>|r: { ..R }| -> { ..R, host: String } {
    { ..r, host = "h" }
};
```

A generic closure also captures, which a local `fun` no longer does (RFC-0195):

```metel
var n := 0;
let bump := <T>[&var n] var |x: T| -> T { n += 1; x };
bump(1);
bump(true);                   // n counts both calls
```

The binder is the only way a closure becomes polymorphic by something other than a written open
record. It is the *written* counterpart of the inferred generalization that RFC-0196 removes: the
quantified variables are the ones the binder names, never ones inference invents.

This closes GAP-FUNCTIONS-007 (metel-core#1668) with the first of its two stated options (a binder
on a closure); the second, a documented decision to keep closures bound-free, is Alternative 1.

This is a design draft. Nothing here is accepted, and the grammar is unchanged until it is.

---

## Motivation

### What a closure cannot say

A closure has `[captures] once? var? |params| (-> ret)? { body }` and no generics list
(`closure_expr` in `grammar.pest`). It cannot declare a type parameter, a bound, a `where` clause
or a row fact (GAP-FUNCTIONS-007). The measured consequences:

- `let add_host := |r| { { ..r, host = "h" } };` is `T0012`: the absence of `host` is not provable.
  `fun add_host<record R: !{ host }>(r: { ..R }) -> { ..R, host: String }` states it.
- A function that needs `T: Copy`, or an associated-type bound, cannot be a closure.
- A closure cannot tie a written return annotation to a parameter's row, except inside a generic
  function, where it can use the enclosing `R`.

### Why it matters now

- **RFC-0193** makes every named declaration write its signature, and suggests a closure as the
  inferred alternative for a private helper. That suggestion is withheld for every function with a
  generics list, a bound, a `where` clause or a row-extending body (RFC-0193 section 2). A binder would
  widen it.
- **RFC-0196** removes inference-invented polymorphism from closures. After it, a closure is
  polymorphic only through a written open record. A polymorphic helper that needs a bound is a `fun`
  when it needs no state; one that also captures state has no spelling except this RFC, because a local
  `fun` does not capture (RFC-0195).
- **#1691 and #1693** show the move check failing on closures inside generic bodies. A written binder
  gives those analyses a declared set of quantified variables to work from.

### Precedent

Rust has no generic closures; its nearest tools are nested generic `fn` items (which cannot capture)
and `for<'a>` for lifetimes only. Swift has local generic functions but its closures cannot be
generic. Scala 3 added polymorphic function literals (`[T] => (x: T) => x`) for the same reason: a lambda that has to name
a type variable. Scala's binder precedes the parameters, as proposed here.

---

## 1. The rule

A closure literal may begin its parameter part with a generic binder, using the same grammar as a
function's `generic_params` and `where_clause`:

```
closure_expr = { generic_params? capture_list? once_kw? var_kw? "|" param_list? "|"
                 ("->" type_expr)? where_clause? block }
```

1. **Quantification.** The variables the binder names are quantified over the closure: each use of
   the closure instantiates them afresh. Variables that inference creates for the closure's other
   parameters or return type are **not** quantified (RFC-0196). A closure with no binder and no
   written open record is monomorphic.
2. **Bounds and facts.** `T: Bound`, `T: !Bound`, `record R: !{ label }`, associated-type bindings,
   and `where` constraints mean what they mean on a `fun` (RFC-0121, RFC-0178, RFC-0186). The body
   is checked against the bounds, not against any one instantiation.
3. **Captures.** The capture list and the `once`/`var` qualifiers are unchanged and checked once, on the
   definition. A captured binding's type cannot mention a binder variable (the environment exists
   before any instantiation); a capture of an enclosing function's type parameter is allowed. A
   binder variable in the *type of a mutated capture* is the same error.
4. **Rank.** Quantification is rank-1, as for `let`-bound polymorphism today (`limit_01_rank1_fn_arg`).
   A generic closure is polymorphic where it is bound (`let f := <T>|…|`); passed as an argument it
   is instantiated at that call against the expected type; it cannot be stored in a field or a
   written function type as a still-polymorphic value.
5. **Call.** Type arguments are inferred. Explicit type arguments on a closure call are out of scope
   (RFC-0192 covers named record parameters).
6. **Evaluation.** One closure value, one environment, one body: instantiation is a typing
   operation. A monomorphizing backend specializes the body per instantiation and shares the
   environment (see Open Questions).

### Where the binder goes

The closure literal's prefix order is fixed (`[captures] once? var?`, legality-23), and a leading `<`
cannot otherwise start an expression, so every position is unambiguous. **The binder comes first,
before the capture list**, where a `fun` writes its generics (`fun name<T>(params)`):

```metel
<T>[&var n] once var |x: T| -> T { n += 1; x }
```

Both forms then read generics, captures, qualifiers, parameters.

### Diagnostics

| situation | message |
|---|---|
| a binder variable never used in a parameter or the return type | the unconstrained-variable error a `fun` gives |
| a capture whose type mentions a binder variable | "a capture is formed before the closure is instantiated; its type cannot mention `T`" |
| a bound the body needs and the binder lacks | as a `fun`: the missing-bound error naming the operation |
| `T0012` on a closure without a binder that extends a record | adds the binder (`<record R: !{ host }>`) as the fix |

---

## 2. What does not change

- Closures without a binder: monomorphic, except through a written open record (RFC-0196).
- Capture lists, qualifiers, multiplicity, `Copy` derivation, linearity (RFC-0050, RFC-0153, RFC-0157,
  RFC-0194).
- Recursion: a closure still cannot name itself (GAP-FUNCTIONS-006) until RFC-0198. A generic *and*
  recursive helper that needs no state is a `fun`.
- Written function types: no polymorphic function type is added (rank-1, rule 4).

---

## Alternatives Considered

1. **Keep closures bound-free (decide and document).** The other resolution GAP-FUNCTIONS-007 names.
   Smallest; a polymorphic helper with a bound is a `fun`, and one that captures state takes it as a
   parameter (RFC-0195 forbids capture on a `fun`). Costs the
   `T0012` row-extension case a closure spelling and leaves RFC-0193's closure suggestion narrow.
2. **Capturing local functions (RFC-0195 as first drafted).** Covers the capturing polymorphic helper, and
   recursion, with no new closure syntax. Rejected 2026-10-30 in favour of a `fun` that never captures: it
   needed a capture list on a declaration and a hoisting exception (RFC-0195 Alternative 1).
3. **Infer bounds from the body** (a closure that does `a + b` gets `T: Add`). Rejected: it invents an
   interface from a body, which is what RFC-0193 and RFC-0196 remove.
4. **A different position for the binder** (a leading `<T>[caps] …`, or after the parameters). Section 1 and
   Open Question 1.
5. **Higher-rank written function types** so a generic closure can be stored and passed polymorphically.
   Larger (RFC-0163's surface), out of scope; rule 4 keeps rank-1.

---

## Interactions

- **RFC-0196 (remove inferred let-polymorphism):** this is the written route to what it removes. Its
  test ("a variable quantifies if it came from something written") is exactly rule 1. They are independent;
  this RFC does not need RFC-0196, but is its natural complement.
- **RFC-0195 (local functions do not capture):** a `fun` is an item and never captures, so a generic or
  bounded helper that captures state is a generic closure. This RFC is the replacement it names.
- **RFC-0198 (recursive closures):** a generic closure cannot recurse without `let rec`.
- **RFC-0193:** a generic closure has a written signature in part (the binder) and inferred parameters in
  part. Closures stay exempt from RFC-0193's rule, which applies to named declarations.
- **RFC-0154 (pipe notation), RFC-0050 (capture lists), RFC-0121, RFC-0178, RFC-0186, RFC-0192:** syntax and
  row machinery reused unchanged.
- **Move check:** a closure with a binder inside a generic body is two nested generic definitions; this is
  #1691's shape. See acceptance criteria.

---

## Migration

Additive. No existing program changes meaning: a leading `<` after the qualifiers was a parse error.

---

## Open Questions

1. **Order against the capture list.** *Resolved (2026-10-30): binder first*, `<T>[caps] once var |…|`:
   generics, captures, qualifiers, parameters. A leading `<` cannot start an expression today, so the
   parse is unambiguous.
2. **Scope of the first version.** Type parameters and bounds first, row facts later? The `T0012`
   example needs row facts. Recommendation: include row facts; they are a bound on a row parameter and cost
   nothing extra to parse.
3. **Captures that mention binder variables** (rule 3): reject, as proposed, or allow a capture whose type is
   the enclosing function's parameter only. Recommendation: as proposed.
4. **Monomorphization.** One environment shared across instantiations of one body is the hard part of the
   backend (metel-core#288). Confirm it before acceptance.
5. **Should this land with RFC-0196?** RFC-0196 leaves a polymorphic helper that needs a bound as a `fun`;
   this RFC would give it a closure spelling. They can be accepted separately.

---

## Specification impact

Spec text lands only at `3-integrated`. `reference/spec/functions.md`: *Closures* legality-1 (the form)
and legality-23 (the order), a new legality rule for the binder, and the removal of GAP-FUNCTIONS-007.
`reference/spec/grammar.md` is generated from `grammar.pest`. `types.md` (open rows) gains the closure case.
Error codes: none proposed; a missing bound is the function error.

## Acceptance criteria for a prototype

- `first_or` and `add_host` above type-check and run; `add_host` without the binder is `T0012` with the binder named as the fix.
- A generic closure used at two types in the same body, and passed as an argument, instantiate separately.
- A binder variable in a capture's type is the stated error.
- The `bump` example above (the shape that is `I0010` as a local `fun`, metel-core#1708) type-checks and counts both calls.
- `--move-check` analyses a generic closure inside a generic function (the #1691 shape) without `I0011`.
- A closure without a binder is unchanged; the corpus passes with the grammar change.

## References

- GAP-FUNCTIONS-007 (metel-core#1668); GAP-FUNCTIONS-006.
- RFC-0193, RFC-0195, RFC-0196, RFC-0198, RFC-0154, RFC-0050, RFC-0121, RFC-0178, RFC-0186, RFC-0192, RFC-0163.
- metel-core#1544, #1691, #1693, #288.
- `grammar.pest` (`closure_expr`, `generic_params`, `where_clause`); `reference/spec/functions.md` (Closures, legality 1 and 23).
- Scala 3 polymorphic function literals.

---

## Decision

**Outcome:** *(pending)*
