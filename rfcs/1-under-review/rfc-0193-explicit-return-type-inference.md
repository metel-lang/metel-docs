---
id: rfc-0193
title: "Explicit Return-Type Inference"
date: '2026-10-29'
status: under-review
updated: '2026-10-29'
tracking: 'https://github.com/metel-lang/metel-core/issues/1665'
---

> **Status — under review (2026-10-29).** design drafted; tracked by metel-core#1665 (v0.15.0); two open questions (migration policy, spelling)

## Summary

An omitted return type means `()` for **every named declaration**: free functions, methods,
and aspect-method declarations. Inferring the return type from the body becomes something the
author writes, `-> auto`, and is allowed only where the signature is not part of an API:
private free functions and private methods.

```metel
fun double(x: i64) -> auto { x * 2 }              // private: inferred i64
fun log_all(items: [String]) { /* … */ }          // omitted: returns ()

extend Counter {
    fun doubled(self) -> auto { self.n * 2 }      // private method: inferred
    fun show(self) { println(self.n); }            // omitted: returns ()
}

public fun double(x: i64) { x * 2 }
// error[T0010]: `double` is public: write its return type; its body has type `i64`: add `-> i64`
```

Closures are unchanged: a closure has no signature to protect, so an omitted return type is
inferred. The rule for `public` declarations (`T0010`) is unchanged, with a better message.

Today the same spelling, an omitted return type, means three different things depending on the
declaration. This RFC makes it mean one thing and gives inference its own spelling. It amends
`spec.functions.named-function-declarations.dynamics-1` (which the implementation contradicts
today), RFC-0181 §1.1 (the advice on `T0032`), and adds a form to the return-type grammar.

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
difference is not a character but the kind of declaration the author happens to be writing.

### Why it is not simply "infer everywhere" or "infer nowhere"

- **Infer everywhere** (methods and aspect declarations too) cannot be done for an aspect-method
  declaration, which has no body, and for a `public` function conflicts with `T0010`'s reasons
  (below). It would also leave `functions.md` as wrong as it is now, in a different place.
- **Infer nowhere** works in Rust and Swift, which never infer a named function's signature, but
  it removes a feature the language uses where it matters most. If named declarations stopped
  inferring, 32 functions in 22 of about 1,460 fixtures and two documentation examples would need
  an annotation; none in the embedded standard library or the website showcases. Fifteen of the 32
  are helpers returning a tuple of closures or an inferred open row, where the written type is long
  or needs a generic parameter. Those are the cases inference serves. RFC-0181 §1.1 also relies on
  it: its answer to "how does a private factory return an anonymous record" is "omit the return
  type".

The measurement is a lower bound and covers the project's own corpus only.

### Why the marker is the fix

Every language that offers both uses a marker, or lets the form of the body decide:
Carbon `-> auto`, C++14 and D `auto`, Kotlin `fun f() = e`. Each restricts where inference may be
used, and the restrictions are about ordering (no forward declarations in Carbon; definition
before use in C++), which matches the cause in Metel (below). Public signatures stay explicit in
every one of them, by enforcement (Rust, Kotlin's explicit-API mode) or guidance (C++, Zig).

### Cause of the split

Confirmed in the typechecker: a free function with an omitted return type gets a fresh type
variable (`inference/declarations.rs`, the function-signature path) and is inferred in dependency
order; a method's signature is built with `InferType::unit()` for the same omission
(`inference/declarations.rs` method path, `registry.rs`), before any body is checked. Allowing
`-> auto` on a method therefore needs the same dependency-ordered inference free functions
already have. That is implementation cost, decided by the language rule in §2, not a reason for
the language rule to differ between the two.

---

## 1. The rule

### Omitted return type is `()`

For a free function, a method (inherent, or in an `extend`), and an aspect-method declaration, a
signature with no `->` returns `()`. A body whose value is not `()` is then an ordinary type
mismatch against `()`, with the improved message below. This makes
`spec.functions.named-function-declarations.dynamics-1` true as written. `native` functions are
unchanged.

### `-> auto`

`-> auto` asks the checker to infer the return type from the body:

```
return_type = { "->" ~ (auto_kw | type_expr) }
auto_kw     = { "auto" }          // contextual: only as the whole return type
```

- The inferred type is the type of the body, exactly as the omitted return type of a private
  free function infers today: the tail expression and every `return` unify to one type (several
  `return`s must agree), an anonymous record is inferred with its exact fields, and a diverging
  body is `!`.
- It is allowed on **private free functions** and **private methods** (inherent methods and
  methods of an `extend` that are not `public`).
- It is rejected, each with a message saying why, on:
  - a `public` declaration. The message states the inferred type so the fix is a copy-paste
    (`public fun double(x: i64) -> auto` is an error: write `-> i64`). Rust's E0121 does the same.
  - an aspect-method declaration (no body), and the methods of an aspect `impl`, whose signature
    is dictated by the aspect.
  - a closure. A closure already infers, so the form would only add a second spelling.
  - `native` functions (no body).
- `auto` is not a type: it is not accepted as a parameter type, a field type, or inside a type
  expression (`-> [auto]`, `-> (auto, i64)`), and it does not combine with `impl Aspect` returns
  (RFC-0037). It is a contextual word, reserved only as the entire return type after `->`; no
  declaration named `auto` exists in the standard library, the fixtures, or the documentation.

### Order and recursion

`-> auto` functions and methods are inferred as a group by their call dependencies, as private
free functions are today. Direct and mutual recursion between `-> auto` declarations keep
working as they do now for free functions: within its own body, a function's return type is a
single unsolved type. A cycle that cannot be solved is an error naming the cycle and the fix
(write the return type on one of them).

The ordering is a rule about the language: a method written `-> auto` is checked in the same
dependency order as a free function, whether or not the implementation currently does so. The
mechanism is an ADR.

### What does not change

- **`T0010`.** A `public` declaration annotates every parameter and its return type. Its three
  reasons stand: API stability (a body edit must not change a public signature), local errors, and
  module independence (RFC-0031: no cross-module inference, the family of TypeScript's
  `isolatedDeclarations`).
- **Closures.** An omitted return type is inferred. A stand-alone closure cannot name a row
  parameter in a written return annotation, because it has no generics list; this is recorded as a
  known limit. A closure inside a generic function uses the enclosing `R`, and a closure whose
  parameter is an anonymous open record generalizes, so the case that is missing is only the
  written annotation.
- **Parameter inference.** Omitted parameter types (`legality-2`) are a separate rule.
- **Aspect-impl return types.** Taking an impl method's return type from the aspect declaration
  (Scala 3 override inference) is independent and is not decided here.

### Diagnostics

| situation | message |
|---|---|
| a method or free function with no return type whose body has type `T ≠ ()` | `` `get` has no return type, so it returns `()`, but its body evaluates to `i64`; add `-> i64` `` (and `, or -> auto` when private) |
| `-> auto` on a public declaration | `T0010`: names the inferred type |
| `-> auto` on a closure, aspect declaration, aspect-impl method, or `native` | an error stating why and what to remove |
| `T0010` and `T0032` | when the type is a named record or has an alias (RFC-0160), the message points at it |
| `T0032` on a return type | one advice: write the record in full, name a row parameter that comes from an argument, or write `-> auto` (private only) |

---

## 2. Interactions

- **RFC-0181 §1.1.** The factory answer changes from "omit the return type" to "write
  `-> auto`". Its per-position advice (metel-core#1484), which exists only because omission means
  different things, collapses to the single row above.
- **RFC-0037 (return-position `impl Aspect`).** Unaffected: `-> impl Aspect` is a written type.
- **Unqualified variant constructors.** A body that needs an expected type (`Some { value = a }`
  with no annotation) has none under `-> auto`, so it must be qualified (`Option::Some`) or the
  return type written. This already holds for private free functions and closures; it is the same
  rule and now holds visibly.
- **RFC-0121, RFC-0186 (open rows).** `-> auto` returns the exact record a body builds, so row
  extension helpers (`add_host`) need no row parameter to be written.
- **Module checking order (RFC-0031).** Unchanged: `-> auto` is private, so no exported scheme
  depends on inference.

---

## Migration

A mechanical rewrite adds `-> auto` to every named, non-`native` declaration whose return type is
currently inferred and is not `()`. Measured: about 22 fixture files and two documentation
examples; none in the standard library. Because a private function whose body is `()` is
unaffected, the rewrite is exactly the set of functions and methods the new check would reject.
Methods that relied on `()` are unaffected.

Open question below: whether this lands as a hard cut or behind a warning.

---

## Alternatives Considered

1. **Status quo, fix the text.** Change `dynamics-1` to describe the implementation. Rejected: it
   bakes in the split, and the method diagnostic is still wrong.
2. **Make methods infer.** One rule (omission infers) with no marker. Removes the inconsistency
   but not the Scala hazard, cannot apply to aspect-method declarations, and still needs the
   dependency-ordering work, with nothing to show for it in the language.
3. **Remove inference from named declarations (Rust, Swift).** Cheap to carry out (tens of
   fixtures), and the most conservative reading of `T0010`'s reasoning. Rejected because the
   awkward cases are exactly where inference is used (tuples of closures, inferred rows), and
   RFC-0181's factory story depends on it.
4. **The form of the body decides (Kotlin `=`).** Metel's function bodies are blocks, and a
   block-bodied function with a tail value is ordinary. Giving expression bodies a separate
   syntax is a larger change than a marker.
5. **`-> _`.** `_` is Rust's local inference placeholder, which Rust rejects in signatures. Metel
   has no `_` type today (`unknown type `_``), and one would raise the placeholder questions
   (RFC-0192's out-of-scope note) for every position. `auto` is also what Carbon, C++ and D use.
6. **Allow `-> auto` on `public` declarations.** Rejected: it loses `T0010`'s API-stability and
   module-independence reasons for the sake of one word.
7. **Allow `-> auto` on closures (redundant).** Rejected: two spellings for the same thing, and the
   diagnostic would need to explain which to use.
8. **Forbid direct recursion (Carbon).** Free functions already allow it; forbidding it only for
   the marked form would be a regression for the code that exists.

---

## Open questions

1. **Transition: hard cut or warning window?** The rewrite is mechanical and small, and v0.15.0 is
   already a language-visible release with other renames (`Perhaps` to `Option`). A hard cut with
   a fix-it that prints `-> auto` is the simplest. A one-release warning (`omitted return type
   inferred; write -> auto`) costs a diagnostic and a second code path. Recommendation: hard cut.
2. **Spelling.** `auto` is chosen above. If review prefers a symbol, the main candidate is `_`
   (see Alternatives). The rest of the RFC does not depend on the spelling.

---

## Specification impact

Spec text lands only at `3-integrated`. `reference/spec/functions.md`: *Named Function
Declarations* (`dynamics-1` now correct; new legality rules for `-> auto`, its placements, and
the grouping/recursion rule), *Closures* (the known limit on row binders), and and any example in the
spec that omits a return type on a value-returning declaration. `reference/spec/modules.md` visibility
legality-2 gains the `-> auto` rejection. `reference/spec/types.md` (open rows) updates the
`T0032` advice. New diagnostics need codes; allocation belongs to the ADR.

## Implementation notes

Implementation detail goes in an ADR at `3-integrated`. The constraints:

- Grammar: `return_type` accepts the contextual `auto`; `fun.return_type` becomes a three-state
  value (absent, `auto`, written).
- Checker: absent means `()` at every declaration kind, in `registry.rs` and the method path; `auto`
  takes the fresh-variable path free functions use now. Method inference must join the
  dependency-ordered inference pass.
- The fixtures and documentation examples are rewritten by script before the check is turned on.

## References

- metel-core#1544: the issue, with prior-art and measurement comments.
- RFC-0181 (Anonymous open rows in return and function types) §1.1, metel-core#1484.
- RFC-0031 (Topological Per-Module Typechecking): the `T0010` rationale.
- RFC-0037 (Return-Position `impl Aspect`), RFC-0160 (type aliases), ADR-0039 (native bindings).
- RFC-0192: out-of-scope note on placeholder arguments.

---

## Decision

**Outcome:** *(pending)*
