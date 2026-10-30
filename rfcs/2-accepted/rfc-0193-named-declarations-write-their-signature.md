---
id: rfc-0193
title: "Named Declarations Write Their Signature"
date: '2026-10-29'
status: accepted
updated: '2026-10-30'
tracking: 'https://github.com/metel-lang/metel-core/issues/1665'
---

> **Status — under review (2026-10-29).** design drafted; tracked by metel-core#1665 (v0.15.0); migration policy resolved 2026-10-30

> **Prepared for acceptance (2026-10-30).** Open questions resolved (hard cut; the by-value reuse of the
> suggested closure was checked; independent of RFC-0196); acceptance criteria added.
>
> **Revised (2026-10-30).** Review: the rule now covers parameter types as well as the return type, so
> `named-function-declarations.legality-2` is amended (it was listed as unchanged); the cost of
> returning closures from named functions is stated; the closure suggestion records a value-semantics
> caveat; the transition recommendation is strengthened; two open questions were added and are now resolved.

> **Status — accepted (2026-10-30).** open questions resolved 2026-10-30

## Summary

A named declaration writes the type of each of its parameters and states its return type or
returns `()`. This holds for **every** named declaration: free functions (private or `public`),
methods, and aspect-method declarations. The checker never infers a named declaration's signature
from its body or from its callers. (This is Rust's rule for `fn` items.)

```metel
fun double(x: i64) -> i64 { x * 2 }          // written
fun log_all(items: [String]) { /* … */ }     // omitted: returns ()

fun triple(x: i64) { x * 3 }
// error[T0001]: `triple` has no return type, so it returns `()`, but its body evaluates to `i64`
//   help: write `-> i64`
//   help: or, if it is only used here, bind a closure, which infers its types:
//             let triple := |x: i64| { x * 3 };
```

Inference stays where there is no signature to protect: a **closure** infers its return type.
For a private free function that has no return type and a non-unit body, the compiler suggests
the closure form (when it applies, §2). Nothing is added to the grammar: there is no marker for
"infer this".

The other half is a guard on the module boundary: a function value that crosses it, as a
`public` function's parameter or return type, as a field of a `public` struct, or as any
future public binding, has a **written** function type (§3).

This amends `spec.functions.named-function-declarations.dynamics-1` (which the implementation
contradicts today), `named-function-declarations.legality-2` (which lets parameter and return-type
annotations be omitted), RFC-0181 §1.1 (the factory answer and the `T0032` advice), and the
visibility rules in `modules.md`.

---

## Motivation

### One spelling, three meanings

Measured on `develop` (metel-core#1544):

| position | omitted return type |
|---|---|
| private free function | inferred from the body: `fun f() { 1 }` returns `1` |
| closure | inferred |
| `public` free function | `T0010`: an explicit return type is required |
| method (inherent or in `extend`) | `()`: a non-unit body fails with `T0001: cannot unify i64 with ()` at the body |
| aspect-method declaration | `()` |
| `native` function | `()`; exempt from `T0010` (ADR-0039) |

The spec says "a function with no return annotation and no `return expr;` returns `()`"
(`dynamics-1`). That is true of methods and false of free functions, which infer. The method
diagnostic names the body expression, not the missing annotation, so the author has to work out
that the signature defaulted to `()`.

This is the hazard Scala 3 removed with procedure syntax: `def f() {}` and `def f() = {}` meant
different things by the presence of a character. Metel's version is worse, because the
difference is the kind of declaration the author happens to be writing.

### Why resolve it by removing inference from named declarations

- **A named declaration is an interface.** It is hoisted, callable before it appears, callable
  from other declarations that are checked independently, and importable. A signature that is read
  off the body means a body edit changes every caller's type, and a caller's error is reported
  against a body that is elsewhere. Rust never infers a named function's signature, for the same
  reasons (errors stay local, signatures stay stable).
- **The alternative of marking inference** (a keyword on the return type: Carbon `-> auto`,
  C++/D `auto`) keeps two ways to write a function and adds a word to say which. It is the more
  conservative fix, but it asks a reader to learn a third form of return type for something the
  language already has a place for: the closure.
- **The language already infers where it is cheap.** A closure's omitted return type is
  inferred, and so are its parameters. A private helper that wants everything inferred has a spelling.

### What it costs

Measured (metel-core#1544, 2026-10-22; a lower bound, project corpus only): 32 functions in 22 of
about 1,460 fixtures, two documentation examples, none in the embedded standard library or the
website showcases.

| group | functions | outcome |
|---|---|---|
| tests of inference itself | 7 | become tests of the new diagnostic |
| helpers returning a tuple of closures | 11 | rewritten as closures, or annotated |
| row-extension helpers (`add_host`) | 4 | annotated with a row parameter (a closure cannot carry the absence fact, §2) |
| negative-bound tests | 9 | annotated |
| false positive (`main` resolves to `!`) | 1 | none |

Parameter types (measured 2026-10-30, same corpus plus the spec and tutorial): 9 named
declarations in 8 files have an unannotated parameter: 6 files are tests of inference itself
(`named_function_inferred_signature`, `abstract_inferred_operand_*`, `limit_01`, `limit_03`), one is
a let-polymorphism test (`06_let_polymorphism`: `identity(x)` becomes `identity<T>(x: T) -> T`), and
one is a spec example (`types.md`, `add_inferred`). None is in the embedded standard library.

**Returning a closure now means writing its function type.** The 11 closure-returning helpers
above can no longer leave the type unwritten. A written function type carries its parameter and
return types and its `once`/`var` qualifiers, and is move-only (RFC-0166). There is no
`-> impl Callable` to avoid writing it: RFC-0161 (`dyn Callable`) is `1-under-review` and
RFC-0037's `-> impl Aspect` applies to aspects. A factory that returns a capturing closure with a
non-trivial type therefore has no unwritten form until RFC-0161 lands. This is a deliberate cost of
treating the signature as the interface, and it should be revisited when RFC-0161 is accepted.

### Cause of the split

A free function with an omitted return type gets a fresh type variable and is inferred in
dependency order; a method's signature is built with the unit type for the same omission, before
any body is checked (`inference/declarations.rs`, the function-signature and method paths;
`registry.rs`). After this RFC both paths read the same: absent means `()`. No dependency-ordered
inference is needed for methods, which is the largest piece of work the inference-for-everything
alternatives would have required.

---

## 1. The rule

A named declaration's return type is its written `-> T`, or `()` if there is none. This is the
rule for free functions, methods (inherent, and in an `extend`), aspect-method declarations and
the methods of an aspect `impl`. `native` functions are unchanged. The body is then checked against
that type exactly as against any written one: a body whose value is not `()` and a signature with
no `->` is an ordinary mismatch.

Private free functions no longer infer, and a named declaration writes every parameter's type
(the receiver `self` excepted). `named-function-declarations.legality-2` changes from "annotations
may be omitted when their types can be inferred from context" to the rule above; `public`
declarations already required both (`T0010`, `modules.md`), so this makes private declarations
match them. An unannotated parameter on a named declaration is `T0010`, as on a `public` one.
Closures keep omitting parameter types, below.

**Closures are unchanged.** A closure's parameter and return types are inferred within the declaration that
contains it (and fixed by their uses, RFC-0196), or taken from what is written. A closure has no signature to protect: it is a value, not a
name that other code is checked against.

### Diagnostics

| situation | message |
|---|---|
| no return type, body has type `T ≠ ()` | `` `get` has no return type, so it returns `()`, but its body evaluates to `i64` ``; help: write `-> i64` (omitted when the body's type has an unsolved part) |
| as above, and the closure form applies (§2) | adds the closure rewrite of the same declaration |
| a named declaration's parameter has no type | `T0010`, now for every named declaration and not only a `public` one; help: write the type, and if the parameter is used at several types make the function generic (`fun id<T>(x: T) -> T`). No closure is suggested: a closure has one type (RFC-0196) |
| `T0010` on a `public` declaration | unchanged; names the body's type where it can be computed |
| `T0010` and `T0032` where the type is an anonymous record | also point at a named `record` or a type alias (RFC-0160) as the short spelling |

---

## 2. The closure suggestion

When a **private free function** has no return type and a non-unit body, the compiler suggests
binding a closure instead, in the same help block as the written type. The suggestion is made only
when the rewrite keeps the program's meaning, which means the function must satisfy all of:

1. **It is private and a free function.** A method has a receiver and belongs to a type; a closure
   cannot replace it. A `public` declaration needs its type written (`T0010`).
2. **It has no generic parameter list, `where` clause or bounds.** A closure has no generics list, so
   it cannot name a type parameter, a bound or a row fact (GAP-FUNCTIONS-007; RFC-0197 proposes a binder, and the suggestion is revisited if it is accepted).
3. **It does not call itself, directly or through other functions.** A closure cannot refer to its
   own name inside its body (GAP-FUNCTIONS-006), so a recursive function must write its type.
4. **Every use follows the declaration.** Functions are hoisted and `let` bindings are not: a
   function declared after a call to it is fine, a `let`-bound closure used before its `let` is
   an undefined name (GAP-DECLARATIONS-004, RFC-0131).
5. **Its body does not extend a parameter's record.** A body such as `{ ..r, host = "h" }` needs
   the fact that `r` lacks `host`, which a function states with a row bound and a closure cannot;
   the closure form is rejected with `T0012` (GAP-FUNCTIONS-007). Such a function must write its type.

If any condition fails, the diagnostic gives the written type only. When they hold, it shows the
function rewritten with its own parameters and body, as in the Summary. The conditions are
syntactic and the checker does not type-check the rewrite, so the suggestion is advice, not a
guarantee: a body that depends on some other fact the signature carried can still be rejected as a
closure. The rewrite shows the parameter annotations the function wrote, so an error in the
rewrite points at the same code.

**Value semantics.** A closure is a value, not a hoisted item, but the suggestion only applies to a
module-level function, which captures nothing. The closure it produces is therefore capture-free and
`Copy` (`closures.legality-20`), and can be passed by value any number of times (checked 2026-10-30
under `--move-check`; a fixture is required, Open Question 2). A closure that owns a non-`Copy` capture
moves on its first by-value use, but the suggestion never produces one.

A closure bound at module level is private, as every top-level `let` is, and must be determined by its own
initializer (RFC-0196); the closure the suggestion produces writes its parameters, so it is. This is why the
suggestion is limited to private functions: it cannot be offered as a way to export a function
without writing its type.

---

## 3. Public function values are written

Nothing here makes it possible for an inferred type to cross a module boundary. The rule is
stated so that it keeps holding. Items 1 and 3 restate `T0010` and constrain a future RFC; item 2
(a targeted error for `public let`) is separable polish and can land on its own:

1. **In a public signature, a function type is written in full.** A `public fun` already annotates
   every parameter and its return type (`T0010`), and a function-typed parameter or return type
   is a written type with written parameter and return types. The same holds for the field of a
   `public struct`. The closure literal passed or
   returned through that type may infer its own return type; it is checked against the written
   one.
2. **There is no `public` closure binding.** `public` is valid on `struct`, `enum`, `fun` and
   `aspect` only, and a top-level `let` or `var` is module-private (`modules.md`, visibility). The
   attempt (`public let f := |x| x;`) is a parse error today; it becomes a targeted error:
   "top-level bindings are private; to export a function, write `public fun` with its parameter and
   return types".
3. **If a later RFC makes a closure binding exportable,** it must require the parameter types and
   return type written, by the same `T0010` rule as a `public fun`. A closure is never a way to
   avoid it, and this RFC's closure suggestion never produces one.

---

## 4. Interactions

- **RFC-0181 §1.1 (return-type advice).** The factory answer changes from "omit the return type"
  to: write the record in full, name an alias or `record` (RFC-0160), name a row parameter that
  comes from an argument, or (for a private function satisfying §2) bind a closure. The per-position
  `T0032` advice (metel-core#1484), which exists only because omission means different things,
  collapses to that one list.
- **Row-extension helpers.** `fun add_host<record R: !{ host }>(r: { ..R }) -> { ..R, host: String }`
  writes its type, with the row bound that makes the added label provable. The closure form
  `|r| { { ..r, host = "h" } }` is rejected today with `T0012`, which is why §2 condition 5
  withholds the suggestion for such a body.
- **RFC-0037 (return-position `impl Aspect`).** Unaffected; `-> impl Aspect` is a written type.
- **Unqualified variant constructors.** A named function body now always has an expected type, its
  written return type or `()`, so `Some { value = a }` resolves when the type is written. A
  closure with no annotation still has none and needs the qualified form.
- **RFC-0195 (local functions do not capture).** A local `fun` is a named declaration and writes its
  signature like any other, and it does not capture, so a closure that captures cannot be rewritten as one.
- **RFC-0198 (recursive closures).** Condition 3 (the function does not call itself) is revisited if it is accepted.
- **RFC-0196 (remove inferred let-polymorphism):** the pair removes inferred polymorphism. This RFC
  does not depend on it: the closure suggestion applies only to functions with no generics list and typed
  parameters, so the closure it produces is monomorphic whichever way RFC-0196 is decided.
- **RFC-0031 and `T0010`.** Unchanged: its three reasons (API stability, local errors, module
  independence) now cover all named declarations, not only exported ones.

---

## Migration

Every named, non-`native` declaration whose return type is currently inferred and is not `()`
needs its type written or becomes a closure. The compiler already knows the body's type when it
reports the mismatch, so the help line is the edit. Measured on a lower bound (the project corpus, spec and tutorial only): about 22 fixture files
for return types and 8 for parameter types, with two documentation examples and one spec example; none in the
standard library. Methods that relied on `()` are unaffected. The fixtures are counted once with RFC-0196: `typechecking/functions/06_let_polymorphism`
(a named function) is this RFC's, `generics/52_let_polymorphism` (a closure) is RFC-0196's, and one instrumented
pass over the corpus serves both. Both amend the `types.md` *Type Inference* section, so the spec rewrite is one
change. A function that was polymorphic by inference becomes `fun f<T>`, not a closure.

This lands as a hard cut (Open Questions, 1).

---

## Alternatives Considered

1. **Status quo, fix the text.** Change `dynamics-1` to describe the implementation. Rejected: it
   bakes in the split, and the method diagnostic is still wrong.
2. **Make methods infer.** One rule (omission infers) with no marker. Cannot apply to an
   aspect-method declaration, still needs dependency-ordered inference for methods, and leaves the
   Scala hazard.
3. **Mark inference with a keyword (`-> auto`, as in Carbon, C++14, D).** Resolves the
   inconsistency and keeps the feature, restricted to private functions and methods. Rejected on
   review: it adds a return-type form to learn when the closure already is the language's
   inferred function, and it keeps the methods work (dependency-ordered inference) that this
   design avoids.
4. **Only the form of the body decides (Kotlin `=`).** Metel's bodies are blocks, and a block with
   a tail value is ordinary. A separate expression-body syntax is a larger change.
5. **Allow a `public` closure binding with annotations required.** Adds a way to export a function
   other than `public fun`, with no use it enables that `public fun` lacks. Left to a later RFC
   (§3.3 states the constraint it would have to meet).
6. **Suggest closures for every private function.** Misleads for recursive, generic, row-bounded
   and used-before-declared functions (§2).

---

## Open Questions — resolved 2026-10-30

1. **Transition: hard cut or warning window?** *Resolved: hard cut.* The rewrite is mechanical and small
   (about 22 fixture files for return types, 8 for parameter types, none in the standard library), and
   v0.15.0 is already a language-visible release with other renames (`Perhaps` to `Option`). The project
   has no warning channel (RFC-0187 notes the same), so a "warning" would be an error with a suggested
   rewrite anyway. The help line is the edit.
2. **Does the closure suggestion survive by-value reuse?** *Resolved: yes, no sixth condition.* The suggestion
   applies only to a module-level function, which captures nothing; the closure it produces is capture-free and
   `Copy`. Checked under `--move-check`: a module-level `let triple := |x: i64| -> i64 { x * 3 }` passed by value
   to two calls and called directly all run. A closure with only `Copy` captures also reuses; only a closure
   owning a non-`Copy` capture moves, and the suggestion never produces one. A prototype fixture that
   passes a replaced helper to two calls is an acceptance criterion.
3. **Do closures keep generalizing?** *Resolved: independent of this RFC.* The suggestion is withheld for any
   function with a generics list, bounds or a `where` clause and requires typed parameters, so the closure it
   produces has no type variable to generalize. Whether closures keep generalizing is RFC-0196.

---

## Specification impact

Spec text lands only at `3-integrated`. `reference/spec/functions.md`: *Named Function
Declarations* (`dynamics-1` now correct; `legality-2` rewritten so a named declaration writes every
parameter's type and its return type, or returns `()`), *Closures* (inference unchanged; the known limit that a stand-alone closure
cannot name a row parameter in a written return annotation). `reference/spec/modules.md`
visibility: the targeted error for `public let`, and the written-function-type rule (§3).
`reference/spec/types.md`: *Type Inference* (GAP-TYPES-001) says "Hindley-Milner with let-polymorphism.
Annotations are optional for all bindings, including function parameters and return types"; it is
narrowed to local bindings, closure parameters and closure return types, with named declarations
written (RFC-0196 narrows the let-polymorphism half further). The open-rows text updates the `T0032`
advice. No new error code is proposed: an omitted return type is `T0001`, an omitted parameter type is
the existing `T0010`, now for every named declaration; the new messages are help text.

## Acceptance criteria for a prototype

- An unannotated parameter on a private free function, a method and an aspect-method declaration is `T0010`; a
  `public` one is unchanged.
- `fun triple(x: i64) { x * 3 }` reports the missing return type with the `-> i64` help and, when the five
  conditions hold, the closure rewrite; each condition that fails withholds the rewrite (one fixture per condition).
- A module-level closure produced by the rewrite is passed by value to two calls and called (Open Question 2).
- An unannotated parameter's `T0010` suggests the generic form and never a closure.
- `main` resolving to `!` is not reported (the one false positive in the measurement).
- The fixtures and documentation examples listed under *Migration* are rewritten first.

## Implementation notes

Implementation detail goes in an ADR at `3-integrated`. The constraints:

- Checker, parameters: an unannotated parameter on a named declaration is `T0010` at every declaration
  kind (today only `public` ones). The fresh-variable path that gives a private free function's
  unannotated parameters a type variable is removed with the return-type one; closures keep it.
- Checker: absent return type means the unit type at every declaration kind, in `registry.rs`, the
  function-signature path and the method path; the fresh-variable path for private free functions
  is removed. The function and method paths then share one rule.
- The help line needs the body's type at the mismatch; where it contains an unsolved variable the
  type is omitted rather than printed.
- The closure suggestion is syntactic over the declaration and its uses (conditions 1 to 5); it
  does not run the checker on the rewrite.
- The fixtures and documentation examples are rewritten before the check is on.

## References

- metel-core#1544: the issue, with prior-art and measurement comments.
- RFC-0181 (Anonymous open rows in return and function types) §1.1, metel-core#1484.
- RFC-0031 (Topological Per-Module Typechecking): the `T0010` rationale.
- RFC-0037 (Return-Position `impl Aspect`), RFC-0160 (type aliases), ADR-0039 (native bindings).
- GAP-FUNCTIONS-006 (a closure cannot call itself, metel-core#1667), GAP-FUNCTIONS-007 (a closure cannot
  name a type parameter, bound or row fact, metel-core#1668), GAP-DECLARATIONS-004 (`let` is not hoisted,
  RFC-0131): the existing limits that bound where the closure suggestion applies. None is changed here.

---

## Decision

**Outcome:** *(pending)*
