---
id: rfc-0023
title: "Type Ascription vs Turbofish — Call-Site Type Annotation Review"
date: '2026-05-23'
status: implemented
coverage:
  "1": { spec: "spec.types.type-ascription.legality-1" }
  "2.1": { spec: "spec.functions.turbofish.legality-1" }
  "2.2": { spec: "spec.functions.turbofish.legality-2" }
---

## Summary

Re-evaluate whether the type ascription operator (`:`) should remain in the language, and determine whether a turbofish-style call-site type parameter syntax (`f::<T>(args)`) is needed instead or alongside it. This RFC does not propose a decision — it documents the considerations so the question can be revisited once generics are in active use.

---

## Background

RFC-0021 introduced `:` as a type ascription operator in expression position. Its primary motivation was resolving inherently ambiguous expressions — empty array literals and `nope` — in positions where no binding annotation is available:

```metel
foo([] : String[]);                    // empty array in argument position
foo(nope : Perhaps<String>);           // nope in argument position
match flag { true => [] : Int[], ... } // empty literal in match arm
```

Since RFC-0021 was incorporated, two issues have been filed that address the inference gaps these examples actually expose:

- **#400** — `construct_match` does not propagate `expected_ty` into arm bodies, unlike `if`. Fix: thread `expected_ty` through `construct_match`.
- **#401** — `construct_call` does not propagate callee parameter types into argument construction. Fix: resolve callee type first, use param types as `expected_ty` for arguments.

Once both fixes land, the cases above no longer require ascription. The `let`-binding alternative becomes available in all remaining situations, though sometimes at the cost of a throwaway name or a block wrapper.

---

## The Narrowed Question

After #400 and #401 are resolved, type ascription shifts from *sometimes required* to *always optional*. It remains useful as a style tool — annotating an expression's type at the use site rather than on a binding — but it is no longer a necessity for correctness.

The question becomes: does the ergonomic benefit justify the operator's presence in the language?

---

## Turbofish

Rust's answer to call-site type annotation is turbofish: `::<T>` placed on the function name, before the argument list.

```rust
identity::<String>(x);
"42".parse::<i32>().unwrap();
iter.collect::<Vec<_>>();
```

Turbofish and ascription solve overlapping but different problems:

| | Ascription `expr : T` | Turbofish `f::<T>(args)` |
|---|---|---|
| Annotates | the result expression | the callee |
| Inference direction | result → type parameters | type parameters → result |
| Disambiguates arguments | yes, per-argument | yes, uniformly via type params |
| Disambiguates result | yes | only indirectly |

They are not equivalent. Consider a generic function with two independent type parameters:

```metel
fun zip<A, B>(a: A[], b: B[]) -> (A, B)[] { ... }

// Turbofish: one annotation covers both type parameters
zip::<Int, String>([], [])

// Ascription: must annotate each argument independently
zip([] : Int[], [] : String[])
```

In this case turbofish is more concise. But for a function that returns an ambiguous type and takes no ambiguous arguments, ascription on the result is cleaner:

```metel
fun empty<T>() -> T[] { [] }

empty() : String[]     // ascription — clean
empty::<String>()      // turbofish — also fine, slightly more syntactic weight
```

---

## Cases and Coverage

| Case | `let` binding | Ascription | Turbofish |
|---|---|---|---|
| Empty array in argument position (after #401) | not needed | not needed | not needed |
| Empty array in match arm (after #400) | block + let | `: T[]` | n/a |
| Ambiguous result of generic call | `let x: T[] = f()` | `f() : T[]` | `f::<T>()` |
| Two independent generic type params at call site | two `let` bindings | per-argument `: T` | `f::<A, B>(...)` |
| Restrict binding to less general type | `let x: T = expr` | `expr : T` | n/a |

The cell "not needed" in the first row reflects that after #401, inference flows from the callee into arguments, so no annotation is required.

---

## Alternatives

**A — Keep ascription, add turbofish for generics**

Both operators coexist. Ascription handles result-type annotation and single-argument disambiguation. Turbofish handles multi-parameter generic call sites. Largest surface area; most expressive.

**B — Keep ascription only**

Turbofish is not added. Generic call sites requiring explicit type parameters use per-argument ascription or intermediate `let` bindings. The `zip` case above requires two ascriptions instead of one turbofish call. This is the current state.

**C — Keep turbofish only, remove ascription**

Turbofish is added for generic calls. Ascription is removed. Cases that ascription covered but turbofish does not (result-type annotation, match arm disambiguation) fall back to `let` bindings. This is the minimal-surface-area option.

**D — Neither — rely on `let` bindings and inference**

Both operators are absent. All disambiguation is done via `let` bindings or improved inference. After #400 and #401, this covers most practical cases. The remaining gaps (complex generic calls, match arm disambiguation of non-trivial expressions) require hoisting bindings.

---

## Why This Is Deferred to v0.4

The right answer depends on real usage patterns with generics, which are not yet implemented. Specifically:

1. How often do generic call sites in practice require explicit type parameters beyond what inference can supply?
2. When they do, is per-argument ascription (option B) sufficiently ergonomic, or does the multi-parameter case arise frequently enough to justify turbofish (option A)?
3. Does the style value of ascription (annotating types inline at use sites) prove useful in practice, or do authors naturally reach for `let` annotations instead?

None of these questions can be answered credibly before v0.2 generics are implemented and used.

The cost of deferral: ascription remains in the language until this RFC resolves. If the eventual decision is to remove it (option C or D), that is a breaking change requiring a major-version bump or explicit deprecation cycle. This is acceptable given the pre-1.0 era.

---

## Decision

**Outcome:** Accepted — Option A: ascription and turbofish coexist.

Both operators are retained. Ascription (`expr : T`) handles result-type annotation and single-expression disambiguation. Turbofish (`f::<T>(args)`) handles multi-parameter generic call sites. The two operators address overlapping but distinct problems and the surface area cost is justified by their complementary coverage.

---

## References

- RFC-0021: Type Ascription Syntax (`rfc-0021-type-ascription.md`)
- Issue #400: propagate `expected_ty` into match arm bodies
- Issue #401: propagate callee param types into argument construction
- `docs/public/spec/types.md` § Type Ascription — current spec entry with known-limitation links

## Coverage Checklist (added 2026-08-19, not part of the original RFC)

Retroactive breakdown of this RFC's distinct, fixture-testable normative claims,
as headed sections for citation purposes only. The document above is
unchanged and remains the historical record. Deliberately excludes claims that
aren't independently observable from a program's behavior -- implementation
strategy, design rationale, or internal architecture discussion belongs in the
RFC's own prose, not here.

### 1. Type ascription constrains an expression without converting it

`expression : Type` is accepted only when the expression's inferred type unifies
with `Type`; it is a compile-time constraint and does not perform a runtime conversion.

**Turbofish supplies explicit generic call type arguments** — split into 2.1/2.2 below
(2026-08-21) rather than left as one claim, since a generic call may use
`name::<T, U>(arguments)` to supply its type arguments explicitly, including multiple
independent arguments, and the two halves below are independently wrong-able and, as it
turned out, independently *true*: 2.2's specific enforcement is not yet implemented
(metel-core#401), which one merged claim would have hidden behind 2.1's already-passing
fixture. (Not its own numbered section: a bare intro paragraph, not a claim of its own,
the same way this checklist's own opening paragraph isn't section "0".)

### 2.1 Turbofish pins each named type parameter, checked against its own bounds

`name::<T, U>(arguments)` pins each named type parameter to the given type;
a pinned type must satisfy that parameter's own bounds (e.g. `T: Display`).

### 2.2 A pinned type parameter's arguments must unify with it

The call's arguments must unify with their pinned types exactly as they would
with an inferred one -- a mismatched argument is rejected, not silently
accepted.
